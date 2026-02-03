# src/core/scenario.py
import json
import random
import os
import src.config as c
from src.entities.rickshaw import Rickshaw

class ScenarioManager:
    def __init__(self, city_graph, scenario_file="agent_scenario.json"):
        self.city = city_graph
        self.scenario_file = scenario_file
        self.scenario_configs = []
        self.path_history = {} # Persists across iterations involved in crashes

    def load_scenario(self):
        """
        Loads scenario from disk. Returns list of Rickshaw objects.
        """
        # Hard reset graph loads for determinism
        for u, v, data in self.city.G.edges(data=True):
            data['current_load'] = 0
            
        rickshaws = []
        try:
            with open(self.scenario_file, 'r') as f:
                self.scenario_configs = json.load(f)
                
            for config in self.scenario_configs:
                aid = config['id']
                history = self.path_history.get(aid, [])
                forced = config.get('forced_path', None)
                
                new_agent = Rickshaw(
                    aid, self.city,
                    start_node=config['start_node'],
                    initial_target=config['initial_target'],
                    initial_progress=config['initial_progress'],
                    dest_type=config['dest_type'],
                    dest_node=config['dest_node'],
                    dest_edge=config['dest_edge'],
                    dest_progress=config['dest_progress'],
                    speed_factor=config.get('speed_factor', 1.0),
                    forbidden_paths=history,
                    forced_path=forced
                )
                rickshaws.append(new_agent)
                
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error loading scenario file. Creating default.")
            self.scenario_configs = []
            rickshaws = self.set_agent_count(c.AGENT_COUNT, [])
            
        return rickshaws

    def save_scenario(self):
        try:
            with open(self.scenario_file, 'w') as f:
                json.dump(self.scenario_configs, f, indent=4)
        except Exception as e:
            print(f"Error saving scenario: {e}")

    def set_agent_count(self, target_count, current_rickshaws):
        """
        Adjusts the number of agents and updates configs. Returns new list of agents.
        """
        current_count = len(current_rickshaws)
        diff = target_count - current_count
        
        rickshaws = list(current_rickshaws)

        if diff > 0:
            all_edges = list(self.city.G.edges())
            
            for _ in range(diff):
                u, v = random.choice(all_edges)
                spawn_progress = random.uniform(0.05, 0.90)
                
                dtype, dnode, dedge, dprog = self._generate_new_destination_config(u)

                new_id = len(rickshaws)
                
                new_agent = Rickshaw(
                    new_id, self.city, 
                    start_node=u, initial_target=v, initial_progress=spawn_progress,
                    dest_type=dtype, dest_node=dnode, dest_edge=dedge, dest_progress=dprog,
                    forbidden_paths=[]
                )
                
                agent_config = {
                    "id": new_id,
                    "start_node": u,
                    "initial_target": v,
                    "initial_progress": spawn_progress,
                    "dest_type": dtype,
                    "dest_node": dnode,
                    "dest_edge": dedge,
                    "dest_progress": dprog,
                    "speed_factor": new_agent.speed_factor,
                    "forced_path": None
                }
                
                self.scenario_configs.append(agent_config)
                rickshaws.append(new_agent)

        elif diff < 0:
            to_remove = rickshaws[target_count:]
            # Clean up loads
            for agent in to_remove:
                if agent.current_edge:
                    u, v = agent.current_edge
                    if self.city.G.has_edge(u, v) and self.city.G[u][v]['current_load'] > 0:
                        self.city.G[u][v]['current_load'] -= 1
            
            rickshaws = rickshaws[:target_count]
            self.scenario_configs = self.scenario_configs[:target_count]

        self.save_scenario()
        return rickshaws

    def prepare_new_trip(self):
        """
        Updates scenario configs for a new position (trip start).
        Reset path history.
        """
        self.path_history = {}
        new_configs = []
        occupied_dests = set()

        for cfg in self.scenario_configs:
            prev_dest_type = cfg.get('dest_type', 'NODE')
            
            next_start_node = None
            next_initial_target = None
            next_initial_progress = 0.0

            if prev_dest_type == "NODE":
                next_start_node = cfg.get('dest_node', cfg['start_node'])
                next_initial_target = self._get_random_neighbor(next_start_node)
                next_initial_progress = 0.0
            
            elif prev_dest_type == "EDGE":
                edge = cfg.get('dest_edge')
                if edge:
                    next_start_node = edge[0]
                    next_initial_target = edge[1]
                    next_initial_progress = cfg.get('dest_progress', 0.5)
                else:
                    next_start_node = cfg['start_node']
                    next_initial_target = cfg['initial_target']
                    next_initial_progress = 0.0

            if not next_initial_target:
                next_initial_target = self._get_random_neighbor(next_start_node)

            dtype, dnode, dedge, dprog = self._generate_new_destination_config(
                    start_node=next_start_node, 
                    exclude_nodes=occupied_dests
            )
            
            if dtype == "NODE" and dnode: occupied_dests.add(dnode)

            new_cfg = {
                "id": cfg['id'],
                "start_node": next_start_node,
                "initial_target": next_initial_target,
                "initial_progress": next_initial_progress,
                "dest_type": dtype,
                "dest_node": dnode,
                "dest_edge": dedge,
                "dest_progress": dprog,
                "speed_factor": cfg.get('speed_factor', 1.0),
                "forced_path": None 
            }
            new_configs.append(new_cfg)
        
        self.scenario_configs = new_configs
        self.save_scenario()

    def update_configs_after_iteration(self, rickshaws):
        """
        Evolutionary Logic: punishes crashers, rewards safe agents.
        """
        for agent in rickshaws:
            # Find the config for this agent
            agent_config = next((c for c in self.scenario_configs if c['id'] == agent.id), None)
            if not agent_config: continue

            if agent.was_involved_in_crash:
                # PUNISHMENT
                # Add current path to forbidden history
                if agent.navigator.chosen_path:
                    if agent.id not in self.path_history:
                        self.path_history[agent.id] = []
                    self.path_history[agent.id].append(agent.navigator.chosen_path)
                
                # Clear forced path
                agent_config['forced_path'] = None
            
            else:
                # REWARD
                # Save the current successful path as 'forced_path'
                # Save the current successful path as 'forced_path'
                # Use accumulated_path to ensure the entire history is preserved for replay
                if agent.navigator.accumulated_path and len(agent.navigator.accumulated_path) > 0:
                    agent_config['forced_path'] = agent.navigator.accumulated_path

        self.save_scenario()

    def _get_random_neighbor(self, node):
        try:
            neighbors = list(self.city.G.neighbors(node))
            if neighbors: return random.choice(neighbors)
        except:
            pass
        return None

    def _generate_new_destination_config(self, start_node, exclude_nodes=None):
        if exclude_nodes is None: exclude_nodes = set()
        
        all_nodes = list(self.city.G.nodes())
        all_edges = list(self.city.G.edges())
        
        dest_type = "NODE" if random.random() < 0.25 else "EDGE"
        d_node = None
        d_edge = None
        d_prog = None

        if dest_type == "NODE":
            candidates = [n for n in all_nodes if n != start_node and n not in exclude_nodes]
            if candidates:
                d_node = random.choice(candidates)
            else:
                dest_type = "EDGE" 

        if dest_type == "EDGE":
            valid_edges = [e for e in all_edges if e[0] != start_node and e[1] != start_node]
            if valid_edges:
                d_edge = random.choice(valid_edges)
            else:
                d_edge = random.choice(all_edges)
            d_prog = random.uniform(0.2, 0.8)
            
        return dest_type, d_node, d_edge, d_prog

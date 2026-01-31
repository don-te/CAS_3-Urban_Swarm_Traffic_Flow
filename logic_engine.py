# logic_engine.py
import math
import random
import networkx as nx
import json
import os
import config as c
from city import CityGraph
from rickshaw import Rickshaw
from data_logger import DataLogger

class SimulationEngine:
    def __init__(self):
        self.city = CityGraph(rows=6, cols=6, block_size_meters=150)
        self.rickshaws = []
        
        self.scenario_file = "agent_scenario.json"
        self.scenario_configs = [] 
        
        self.path_history = {} 
        
        all_lats = [d['pos'][1] for n, d in self.city.G.nodes(data=True)]
        all_lons = [d['pos'][0] for n, d in self.city.G.nodes(data=True)]
        self.bounds = (min(all_lats), max(all_lats), min(all_lons), max(all_lons))
        
        self.collision_count = 0 
        self.collision_history = []
        
        # --- LOGGING COUNTERS ---
        self.current_iteration = 1
        self.current_position_id = 1 
        
        self.data_logger = DataLogger()

        if os.path.exists(self.scenario_file):
            print(f"Loading existing scenario from {self.scenario_file}")
            self.load_scenario_from_disk()
        else:
            print("No scenario file found. Creating new default scenario.")
            self.set_agent_count(c.AGENT_COUNT)

    def set_agent_count(self, target_count):
        current_count = len(self.rickshaws)
        diff = target_count - current_count

        if diff > 0:
            all_edges = list(self.city.G.edges())
            all_nodes = list(self.city.G.nodes())

            for _ in range(diff):
                u, v = random.choice(all_edges)
                spawn_progress = random.uniform(0.05, 0.90)
                
                dtype, dnode, dedge, dprog = self._generate_new_destination_config(u)

                new_id = len(self.rickshaws)
                
                # Note: No 'forced_path' for brand new agents
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
                    "forced_path": None # Initialize as None
                }
                
                self.scenario_configs.append(agent_config)
                self.rickshaws.append(new_agent)

        elif diff < 0:
            to_remove = self.rickshaws[target_count:]
            for agent in to_remove:
                if agent.current_edge:
                    u, v = agent.current_edge
                    if self.city.G.has_edge(u, v) and self.city.G[u][v]['current_load'] > 0:
                        self.city.G[u][v]['current_load'] -= 1
            
            self.rickshaws = self.rickshaws[:target_count]
            self.scenario_configs = self.scenario_configs[:target_count]

        self.save_scenario_to_disk()

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

    def save_scenario_to_disk(self):
        try:
            with open(self.scenario_file, 'w') as f:
                json.dump(self.scenario_configs, f, indent=4)
        except Exception as e:
            print(f"Error saving scenario: {e}")

    def load_scenario_from_disk(self):
        # --- FIX START: HARD RESET GRAPH LOADS ---
        # Instead of asking agents to leave edges, we wipe the map clean.
        # This guarantees Iteration 7 is mathematically identical to Iteration 6.
        for u, v, data in self.city.G.edges(data=True):
            data['current_load'] = 0
        # --- FIX END ---
        
        self.rickshaws = []
        try:
            with open(self.scenario_file, 'r') as f:
                self.scenario_configs = json.load(f)
            # ... rest of the loading logic ...
                
            for config in self.scenario_configs:
                aid = config['id']
                history = self.path_history.get(aid, [])
                forced = config.get('forced_path', None) # Load the successful path if it exists
                
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
                    forced_path=forced # Pass to agent
                )
                self.rickshaws.append(new_agent)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error loading scenario file. Resetting to empty.")
            self.scenario_configs = []
            self.set_agent_count(c.AGENT_COUNT)

    def reset_simulation(self):
        self.collision_count = 0
        self.collision_history = []
        self.current_iteration = 1
        self.current_position_id = 1 
        self.path_history = {} 
        print("--- SIMULATION RESET (Reloading from JSON) ---")
        self.load_scenario_from_disk()

    def update_positions(self):
        print(f"--- UPDATING POSITIONS (Starting new Trip) ---")
        
        self.path_history = {}
        self.current_position_id += 1 
        self.current_iteration = 1    
        
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
                "forced_path": None # New trip, so reset forced paths
            }
            new_configs.append(new_cfg)
        
        self.scenario_configs = new_configs
        self.save_scenario_to_disk()
        
        self.collision_count = 0
        self.load_scenario_from_disk()


    def trigger_next_iteration(self):
        # 1. Archive Stats
        record = f"Iter {self.current_iteration} Collisions: {self.collision_count}"
        self.collision_history.append(record)
        
        # Log Stats
        block_size = self.city.block_size
        agent_data_list = []
        for agent in self.rickshaws:
            dist_meters = agent.distance_travelled * block_size
            time_seconds = agent.travel_time
            agent_data_list.append([
                agent.id,
                round(dist_meters, 2),
                round(time_seconds, 2)
            ])
        self.data_logger.log_complex_iteration(
            pos_id=self.current_position_id,
            iter_id=self.current_iteration,
            collision_count=self.collision_count,
            agent_data_list=agent_data_list
        )
        
        print(f"--- NEXT ITERATION (Evolutionary Pathing) ---")
        
        # 2. EVOLUTIONARY LOGIC
        # We iterate over current active agents to see who crashed and who didn't.
        
        for agent in self.rickshaws:
            # Find the config for this agent
            agent_config = next((c for c in self.scenario_configs if c['id'] == agent.id), None)
            if not agent_config: continue

            if agent.was_involved_in_crash:
                # --- PUNISHMENT ---
                # 1. Add current path to forbidden history so they don't pick it again
                if agent.chosen_path:
                    if agent.id not in self.path_history:
                        self.path_history[agent.id] = []
                    self.path_history[agent.id].append(agent.chosen_path)
                
                # 2. Clear forced path so they recalculate
                agent_config['forced_path'] = None
                print(f"Agent {agent.id} CRASHED. Forcing new path next iter.")
            
            else:
                # --- REWARD ---
                # 1. Save the current successful path as 'forced_path'
                if agent.chosen_path and len(agent.chosen_path) > 0:
                    agent_config['forced_path'] = agent.chosen_path
                    # print(f"Agent {agent.id} SAFE. Keeping path.")

        # 3. Save Configs & Reload
        self.save_scenario_to_disk() # Write the 'forced_path' updates to JSON
        
        self.collision_count = 0
        self.current_iteration += 1
        self.load_scenario_from_disk() # Reloads agents; those with forced_path will use it.

    def _haversine_distance(self, pos1, pos2):
        lon1, lat1 = pos1[0], pos1[1]
        lon2, lat2 = pos2[0], pos2[1]
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c_val = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c_val

    def check_collisions(self):
        count = len(self.rickshaws)
        for i in range(count):
            for j in range(i + 1, count):
                a1 = self.rickshaws[i]
                a2 = self.rickshaws[j]
                
                if a1.is_crashed and a2.is_crashed: continue
                if a1.immunity_timer > 0 or a2.immunity_timer > 0: continue
                if a1.has_arrived or a2.has_arrived: continue
                
                if (a1.current_node == a2.target_node) and (a1.target_node == a2.current_node): continue
                if a1.target_node is None or a2.target_node is None: continue

                pos1 = a1.get_position()
                pos2 = a2.get_position()
                
                distance_meters = self._haversine_distance(pos1, pos2)
                
                if distance_meters < 2.5:
                    crash = False
                    if not a1.is_crashed:
                        a1.is_crashed = True
                        a1.was_involved_in_crash = True # <--- MARK AS CRASHED FOR ITERATION
                        a1.crash_timer = 5.0
                        crash = True
                    if not a2.is_crashed:
                        a2.is_crashed = True
                        a2.was_involved_in_crash = True # <--- MARK AS CRASHED FOR ITERATION
                        a2.crash_timer = 5.0
                        crash = True
                    if crash: self.collision_count += 1

    def update(self, dt):
        for agent in self.rickshaws:
            agent.move(dt, self.rickshaws)
        self.check_collisions()

# logic_engine.py
import math
import random
import networkx as nx
import json
import os
import config as c
from city import CityGraph
from rickshaw import Rickshaw

class SimulationEngine:
    def __init__(self):
        self.city = CityGraph(rows=6, cols=6, block_size_meters=150)
        self.rickshaws = []
        
        # --- JSON SCENARIO PERSISTENCE ---
        self.scenario_file = "agent_scenario.json"
        self.scenario_configs = [] 
        
        all_lats = [d['pos'][1] for n, d in self.city.G.nodes(data=True)]
        all_lons = [d['pos'][0] for n, d in self.city.G.nodes(data=True)]
        self.bounds = (min(all_lats), max(all_lats), min(all_lons), max(all_lons))
        
        self.collision_count = 0 
        self.collision_history = []
        self.current_iteration = 1
        
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
                
                # Use helper to pick dest
                dtype, dnode, dedge, dprog = self._generate_new_destination_config(u)

                new_id = len(self.rickshaws)
                new_agent = Rickshaw(
                    new_id, self.city, 
                    start_node=u, initial_target=v, initial_progress=spawn_progress,
                    dest_type=dtype, dest_node=dnode, dest_edge=dedge, dest_progress=dprog
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
                    "speed_factor": new_agent.speed_factor
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
        """Helper to pick a random destination (Node or Edge)."""
        if exclude_nodes is None: exclude_nodes = set()
        
        all_nodes = list(self.city.G.nodes())
        all_edges = list(self.city.G.edges())
        
        # 25% chance for precise Node destination, 75% for Edge destination
        dest_type = "NODE" if random.random() < 0.25 else "EDGE"
        d_node = None
        d_edge = None
        d_prog = None

        if dest_type == "NODE":
            # Don't pick start node or excluded nodes
            candidates = [n for n in all_nodes if n != start_node and n not in exclude_nodes]
            if candidates:
                d_node = random.choice(candidates)
            else:
                dest_type = "EDGE" # Fallback

        if dest_type == "EDGE":
            # Don't pick an edge that contains the start node (immediate U-turn or already there)
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
        # Clear existing load first
        for agent in self.rickshaws:
            if agent.current_edge:
                u, v = agent.current_edge
                if self.city.G.has_edge(u, v) and self.city.G[u][v]['current_load'] > 0:
                    self.city.G[u][v]['current_load'] -= 1
        
        self.rickshaws = []
        try:
            with open(self.scenario_file, 'r') as f:
                self.scenario_configs = json.load(f)
                
            for config in self.scenario_configs:
                new_agent = Rickshaw(
                    config['id'], self.city,
                    start_node=config['start_node'],
                    initial_target=config['initial_target'],
                    initial_progress=config['initial_progress'],
                    dest_type=config['dest_type'],
                    dest_node=config['dest_node'],
                    dest_edge=config['dest_edge'],
                    dest_progress=config['dest_progress'],
                    speed_factor=config.get('speed_factor', 1.0)
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
        print("--- SIMULATION RESET (Reloading from JSON) ---")
        self.load_scenario_from_disk()

    def trigger_next_iteration(self, path_constant=True):
        # 1. Archive Stats
        record = f"Iter {self.current_iteration} Collisions: {self.collision_count}"
        self.collision_history.append(record)
        
        # 2. Handle Continuous Path (CHAIN MODE)
        if not path_constant:
            print(f"--- CHAINING PATHS FOR ITERATION {self.current_iteration + 1} ---")
            new_configs = []
            occupied_dests = set()

            for cfg in self.scenario_configs:
                prev_dest_type = cfg.get('dest_type', 'NODE')
                
                # --- CALCULATE EXACT START POINT ---
                next_start_node = None
                next_initial_target = None
                next_initial_progress = 0.0

                if prev_dest_type == "NODE":
                    # Finished at a NODE
                    next_start_node = cfg.get('dest_node', cfg['start_node'])
                    # Needs to pick a new street to leave the intersection
                    next_initial_target = self._get_random_neighbor(next_start_node)
                    next_initial_progress = 0.0
                
                elif prev_dest_type == "EDGE":
                    # Finished MID-STREET
                    edge = cfg.get('dest_edge')
                    if edge:
                        # CORRECT FIX: Start exactly where they parked
                        next_start_node = edge[0]
                        next_initial_target = edge[1]
                        next_initial_progress = cfg.get('dest_progress', 0.5)
                    else:
                        # Fallback
                        next_start_node = cfg['start_node']
                        next_initial_target = cfg['initial_target']
                        next_initial_progress = 0.0

                # Validate Target (Safety Check)
                if not next_initial_target:
                    next_initial_target = self._get_random_neighbor(next_start_node)

                # --- GENERATE NEW DESTINATION ---
                # We start looking for a new destination from the 'next_start_node'
                dtype, dnode, dedge, dprog = self._generate_new_destination_config(
                     start_node=next_start_node, 
                     exclude_nodes=occupied_dests
                )
                
                if dtype == "NODE" and dnode: occupied_dests.add(dnode)

                new_cfg = {
                    "id": cfg['id'],
                    "start_node": next_start_node,
                    "initial_target": next_initial_target,
                    "initial_progress": next_initial_progress, # Preserves the "parking spot"
                    "dest_type": dtype,
                    "dest_node": dnode,
                    "dest_edge": dedge,
                    "dest_progress": dprog,
                    "speed_factor": cfg.get('speed_factor', 1.0)
                }
                new_configs.append(new_cfg)
            
            # Save chain
            self.scenario_configs = new_configs
            self.save_scenario_to_disk()

        # 3. Reload from Disk
        self.collision_count = 0
        self.current_iteration += 1
        print(f"--- STARTED ITERATION {self.current_iteration} ---")
        self.load_scenario_from_disk()

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
                        a1.crash_timer = 5.0
                        crash = True
                    if not a2.is_crashed:
                        a2.is_crashed = True
                        a2.crash_timer = 5.0
                        crash = True
                    if crash: self.collision_count += 1

    def update(self, dt):
        for agent in self.rickshaws:
            agent.move(dt, self.rickshaws)
        self.check_collisions()

# logic_engine.py
import math
import random
import networkx as nx
import json
import os
import config as c
from city import CityGraph
from rickshaw import Rickshaw
from traffic_control import TrafficManager

class SimulationEngine:
    def __init__(self):
        self.city = CityGraph(rows=6, cols=6, block_size_meters=150)
        self.traffic_manager = TrafficManager(self.city)
        self.rickshaws = []
        
        # --- JSON SCENARIO PERSISTENCE ---
        self.scenario_file = "agent_scenario.json"
        self.scenario_configs = [] # Local mirror of JSON data
        
        all_lats = [d['pos'][1] for n, d in self.city.G.nodes(data=True)]
        all_lons = [d['pos'][0] for n, d in self.city.G.nodes(data=True)]
        self.bounds = (min(all_lats), max(all_lats), min(all_lons), max(all_lons))
        
        self.collision_count = 0 
        self.collision_history = []
        self.current_iteration = 1
        
        # Initialize: Load from file if exists, else start default
        if os.path.exists(self.scenario_file):
            print(f"Loading existing scenario from {self.scenario_file}")
            self.load_scenario_from_disk()
        else:
            print("No scenario file found. Creating new default scenario.")
            self.set_agent_count(c.AGENT_COUNT)

    def set_agent_count(self, target_count):
        current_count = len(self.rickshaws)
        diff = target_count - current_count

        # --- ADDING AGENTS ---
        if diff > 0:
            all_edges = list(self.city.G.edges())
            all_nodes = list(self.city.G.nodes())

            for _ in range(diff):
                # 1. Generate Random Start
                u, v = random.choice(all_edges)
                spawn_progress = random.uniform(0.05, 0.90)
                
                # Init variables
                d_node = None
                d_edge = None
                d_prog = None
                
                # 2. Pick Destination
                if random.random() < 0.25:
                    dest_type = "NODE"
                    occupied = {a.final_dest_node for a in self.rickshaws if a.dest_type == "NODE" and a.final_dest_node}
                    candidates = [n for n in all_nodes if n != u and n not in occupied]
                    
                    if candidates:
                        d_node = random.choice(candidates)
                    else:
                        dest_type = "EDGE" # Fallback if no nodes available
                else:
                    dest_type = "EDGE"
                
                # 3. Handle EDGE Destination
                if dest_type == "EDGE":
                    valid_edges = [e for e in all_edges if e != (u, v)]
                    if valid_edges:
                        d_edge = random.choice(valid_edges)
                    else:
                        d_edge = (u, v)
                    d_prog = random.uniform(0.2, 0.8)

                # 4. Create the Agent (It will assign internal speed_factor)
                new_id = len(self.rickshaws)
                new_agent = Rickshaw(
                    new_id, self.city, 
                    start_node=u, initial_target=v, initial_progress=spawn_progress,
                    dest_type=dest_type, dest_node=d_node, dest_edge=d_edge, dest_progress=d_prog
                )
                
                # 5. Create Config Entry (Include Speed Factor!)
                agent_config = {
                    "id": new_id,
                    "start_node": u,
                    "initial_target": v,
                    "initial_progress": spawn_progress,
                    "dest_type": dest_type,
                    "dest_node": d_node,
                    "dest_edge": d_edge,
                    "dest_progress": d_prog,
                    "speed_factor": new_agent.speed_factor
                }
                
                self.scenario_configs.append(agent_config)
                self.rickshaws.append(new_agent)

        # --- REMOVING AGENTS ---
        elif diff < 0:
            # 1. Remove from Sim
            to_remove = self.rickshaws[target_count:]
            for agent in to_remove:
                # Remove load from roads
                if agent.current_edge:
                    u, v = agent.current_edge
                    if self.city.G.has_edge(u, v):
                        if self.city.G[u][v]['current_load'] > 0:
                            self.city.G[u][v]['current_load'] -= 1
            
            self.rickshaws = self.rickshaws[:target_count]
            
            # 2. Remove from Configs
            self.scenario_configs = self.scenario_configs[:target_count]

        # --- SAVE TO DISK ---
        self.save_scenario_to_disk()

    def save_scenario_to_disk(self):
        try:
            with open(self.scenario_file, 'w') as f:
                json.dump(self.scenario_configs, f, indent=4)
        except Exception as e:
            print(f"Error saving scenario: {e}")

    def load_scenario_from_disk(self):
        """
        Clears the board and respawns agents using the JSON file.
        """
        # 1. Clear existing load
        for agent in self.rickshaws:
            if agent.current_edge:
                u, v = agent.current_edge
                if self.city.G.has_edge(u, v) and self.city.G[u][v]['current_load'] > 0:
                    self.city.G[u][v]['current_load'] -= 1
        
        self.rickshaws = []
        
        # 2. Read File
        try:
            with open(self.scenario_file, 'r') as f:
                self.scenario_configs = json.load(f)
                
            # 3. Respawn Agents
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
                    speed_factor=config.get('speed_factor', 1.0) # Load persisted speed
                )
                self.rickshaws.append(new_agent)
                
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error loading scenario file. Resetting to empty.")
            self.scenario_configs = []
            self.set_agent_count(c.AGENT_COUNT)

    def reset_simulation(self):
        """Hard reset: Reloads from JSON."""
        self.collision_count = 0
        self.collision_history = []
        self.current_iteration = 1
        
        # Re-create traffic manager (Timers are still random per your request)
        self.traffic_manager = TrafficManager(self.city)
        
        print("--- SIMULATION RESET (Reloading from JSON) ---")
        self.load_scenario_from_disk()

    def trigger_next_iteration(self):
        # 1. Archive Stats
        record = f"Iter {self.current_iteration} Collisions: {self.collision_count}"
        self.collision_history.append(record)
        
        # 2. Reset Counter
        self.collision_count = 0
        self.current_iteration += 1
        
        # 3. RELOAD
        print(f"--- STARTED ITERATION {self.current_iteration} (Reloading from JSON) ---")
        self.load_scenario_from_disk()

    def toggle_traffic_lights(self):
        self.traffic_manager.toggle()

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
        self.traffic_manager.update(dt)
        for agent in self.rickshaws:
            agent.move(dt, self.rickshaws, self.traffic_manager)
        self.check_collisions()

import math
import random
import networkx as nx
import config as c
from city import CityGraph
from rickshaw import Rickshaw

class SimulationEngine:
    def __init__(self):
        self.city = CityGraph(rows=6, cols=6, block_size_meters=150)
        self.rickshaws = []
        
        all_lats = [d['pos'][1] for n, d in self.city.G.nodes(data=True)]
        all_lons = [d['pos'][0] for n, d in self.city.G.nodes(data=True)]
        self.bounds = (min(all_lats), max(all_lats), min(all_lons), max(all_lons))
        
        self.collision_count = 0 
        self.set_agent_count(c.AGENT_COUNT)

    def set_agent_count(self, target_count):
        current_count = len(self.rickshaws)
        diff = target_count - current_count

        if diff > 0:
            all_edges = list(self.city.G.edges())
            all_nodes = list(self.city.G.nodes())

            for _ in range(diff):
                placed = False
                for attempt in range(20):
                    u, v = random.choice(all_edges)
                    spawn_progress = random.uniform(0.05, 0.90)
                    
                    # Check overlap (simplified)
                    collision = False
                    for agent in self.rickshaws:
                        if agent.current_node == u and agent.target_node == v:
                            if abs(agent.progress - spawn_progress) < 0.15:
                                collision = True
                                break
                    
                    if not collision:
                        # --- MODIFIED: CHOOSE EDGE DESTINATION ---
                        # Pick a random edge that is NOT the current spawn edge
                        valid_dest_edges = [e for e in all_edges if e != (u, v)]
                        if not valid_dest_edges: valid_dest_edges = all_edges
                        
                        dest_edge = random.choice(valid_dest_edges)
                        dest_progress = random.uniform(0.2, 0.8) # Stop somewhere in the middle

                        new_id = len(self.rickshaws)
                        new_agent = Rickshaw(
                            new_id, 
                            self.city, 
                            start_node=u, 
                            final_dest_edge=dest_edge,      # Pass Edge
                            final_dest_progress=dest_progress, # Pass Progress
                            initial_target=v, 
                            initial_progress=spawn_progress
                        )
                        
                        self.rickshaws.append(new_agent)
                        placed = True
                        break 
                
                if not placed:
                    print(f"Warning: Grid saturation. Could not spawn agent {len(self.rickshaws)+1}.")

        elif diff < 0:
            self.rickshaws = self.rickshaws[:target_count]

    # ... Rest of the file (check_collisions, _haversine_distance, update) remains identical ...
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
                if a1.has_arrived or a2.has_arrived: continue # Parked cars safety
                
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

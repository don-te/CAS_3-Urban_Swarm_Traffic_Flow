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

    # logic_engine.py

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
                    
                    # Collision Check with existing agents
                    collision = False
                    for agent in self.rickshaws:
                        if agent.current_node == u and agent.target_node == v:
                            if abs(agent.progress - spawn_progress) < 0.15:
                                collision = True
                                break
                    
                    if not collision:
                        # --- MODIFICATION START ---
                        # Probability: 75% EDGE, 25% NODE
                        if random.random() < 0.25:
                            dest_type = "NODE"
                        else:
                            dest_type = "EDGE"
                        
                        d_node = None
                        d_edge = None
                        d_prog = None
                        
                        if dest_type == "NODE":
                            # Gather currently occupied destinations from existing rickshaws
                            occupied_destinations = {
                                agent.final_dest_node for agent in self.rickshaws 
                                if agent.dest_type == "NODE" and agent.final_dest_node
                            }
                            
                            # Filter: exclude spawn node 'u' AND occupied nodes
                            valid_nodes = [
                                n for n in all_nodes 
                                if n != u and n not in occupied_destinations
                            ]
                            
                            if valid_nodes:
                                d_node = random.choice(valid_nodes)
                            else:
                                # Fallback to Edge if grid is full
                                dest_type = "EDGE"

                        # Check again (is not elif because of potential fallback above)
                        if dest_type == "EDGE":
                            # Pick random edge != spawn edge
                            valid_edges = [e for e in all_edges if e != (u, v)]
                            if not valid_edges: valid_edges = all_edges
                            d_edge = random.choice(valid_edges)
                            d_prog = random.uniform(0.2, 0.8)
                        # --- MODIFICATION END ---

                        new_id = len(self.rickshaws)
                        new_agent = Rickshaw(
                            new_id, 
                            self.city, 
                            start_node=u,
                            dest_type=dest_type,
                            dest_node=d_node,
                            dest_edge=d_edge,
                            dest_progress=d_prog,
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
                if a1.has_arrived or a2.has_arrived: continue # Parked cars don't crash
                
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

# logic_engine.py
import math
import random  # <--- MAKE SURE THIS IS IMPORTED
import config as c
from city import CityGraph
from rickshaw import Rickshaw

class SimulationEngine:
    def __init__(self):
        self.city = CityGraph(rows=6, cols=6, block_size_meters=150)
        self.top_left_dest = "0-0" 
        
        self.rickshaws = []
        # Initial spawn using the new logic
        self.set_agent_count(c.AGENT_COUNT)
        
        self.collision_count = 0 
        
        all_lats = [d['pos'][1] for n, d in self.city.G.nodes(data=True)]
        all_lons = [d['pos'][0] for n, d in self.city.G.nodes(data=True)]
        self.bounds = (min(all_lats), max(all_lats), min(all_lons), max(all_lons))

    def set_agent_count(self, target_count):
        current_count = len(self.rickshaws)
        diff = target_count - current_count

        if diff > 0:
            # Get all possible streets (edges)
            all_edges = list(self.city.G.edges())
            
            for _ in range(diff):
                placed = False
                
                # Try up to 20 times to find a non-overlapping spot
                for attempt in range(20):
                    # 1. Pick a random street
                    u, v = random.choice(all_edges)
                    
                    # 2. Pick a random spot along the street (5% to 90%)
                    # We avoid 0.0 and 1.0 to keep intersections strictly clear
                    spawn_progress = random.uniform(0.05, 0.90)
                    
                    # 3. Check for collisions with existing agents
                    collision_detected = False
                    for agent in self.rickshaws:
                        # Only care if agent is on the EXACT same street (u->v)
                        if agent.current_node == u and agent.target_node == v:
                            # If distance between them is < 15% of road length (~20m)
                            if abs(agent.progress - spawn_progress) < 0.15:
                                collision_detected = True
                                break
                    
                    # 4. If safe, Spawn!
                    if not collision_detected:
                        new_id = len(self.rickshaws)
                        new_agent = Rickshaw(
                            new_id, 
                            self.city, 
                            start_node=u,               # Start of edge
                            initial_target=v,           # End of edge (defines direction)
                            initial_progress=spawn_progress, # Location on edge
                            final_dest=self.top_left_dest
                        )
                        self.rickshaws.append(new_agent)
                        placed = True
                        break # Break retry loop, move to next agent
                
                if not placed:
                    print(f"Warning: Could not find space for agent {len(self.rickshaws)+1}. Grid is full.")

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

                # Ignore arrived agents
                if (a1.target_node is None) or (a2.target_node is None): continue

                # Ignore traffic on opposite sides of the road (u->v vs v->u)
                if (a1.current_node == a2.target_node) and (a1.target_node == a2.current_node):
                    continue
                
                pos1 = a1.get_position()
                pos2 = a2.get_position()
                
                distance_meters = self._haversine_distance(pos1, pos2)
                
                if distance_meters < 2.5: # Slightly increased hit box
                    crash_event_occurred = False
                    if not a1.is_crashed:
                        a1.is_crashed = True
                        a1.crash_timer = 5.0
                        crash_event_occurred = True
                    if not a2.is_crashed:
                        a2.is_crashed = True
                        a2.crash_timer = 5.0
                        crash_event_occurred = True
                        
                    if crash_event_occurred:
                        self.collision_count += 1

    def update(self, dt):
        for agent in self.rickshaws:
            agent.move(dt, self.rickshaws)
        self.check_collisions()

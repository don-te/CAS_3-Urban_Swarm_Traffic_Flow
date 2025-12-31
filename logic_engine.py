# logic_engine.py
import math
import config as c
from city import CityGraph
from rickshaw import Rickshaw

class SimulationEngine:
    def __init__(self):
        self.city = CityGraph(rows=6, cols=6, block_size_meters=150)
        self.top_left_dest = "0-0" # Target Top-Left
        
        # --- PRE-CALCULATE SPAWN POINTS ---
        # Get all nodes and sort them to start from Bottom-Right (Max Row, Max Col)
        # This creates a "Snake" spawn pattern to prevent overlaps
        all_nodes = list(self.city.G.nodes())
        all_nodes.sort(key=lambda x: (int(x.split('-')[0]), int(x.split('-')[1])), reverse=True)
        self.spawn_points = all_nodes

        self.rickshaws = []
        self.set_agent_count(c.AGENT_COUNT)
        
        all_lats = [d['pos'][1] for n, d in self.city.G.nodes(data=True)]
        all_lons = [d['pos'][0] for n, d in self.city.G.nodes(data=True)]
        self.bounds = (min(all_lats), max(all_lats), min(all_lons), max(all_lons))

    def set_agent_count(self, target_count):
        current_count = len(self.rickshaws)
        diff = target_count - current_count

        if diff > 0:
            for _ in range(diff):
                new_id = len(self.rickshaws)
                
                # --- ASSIGN DETERMINISTIC SPAWN ---
                # Cycle through spawn points: 5-5, 5-4, 5-3...
                spawn_index = new_id % len(self.spawn_points)
                spawn_node = self.spawn_points[spawn_index]
                
                new_agent = Rickshaw(
                    new_id, 
                    self.city, 
                    start_node=spawn_node, 
                    final_dest=self.top_left_dest
                )
                self.rickshaws.append(new_agent)
                
        elif diff < 0:
            self.rickshaws = self.rickshaws[:target_count]

    def _haversine_distance(self, pos1, pos2):
        """
        Calculate the great-circle distance between two points on Earth.
        Returns distance in meters.
        """
        lon1, lat1 = pos1[0], pos1[1]
        lon2, lat2 = pos2[0], pos2[1]
        
        # Earth radius in meters
        R = 6371000
        
        # Convert to radians
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c_val = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = R * c_val
        return distance

    def check_collisions(self):
        """Checks distance between all agent pairs using proper geographic distance."""
        count = len(self.rickshaws)
        
        for i in range(count):
            for j in range(i + 1, count):
                a1 = self.rickshaws[i]
                a2 = self.rickshaws[j]
                
                # Skip if both are already crashed
                if a1.is_crashed and a2.is_crashed:
                    continue
                
                # --- IMMUNITY CHECK ---
                if a1.immunity_timer > 0 or a2.immunity_timer > 0:
                    continue

                # --- ARRIVAL SAFE ZONE (NEW FIX) ---
                # If either agent has reached their final destination, they are "parked" 
                # and should not cause collisions.
                a1_arrived = (a1.final_dest and a1.current_node == a1.final_dest)
                a2_arrived = (a2.final_dest and a2.current_node == a2.final_dest)
                
                if a1_arrived or a2_arrived:
                    continue
                
                # --- OPPOSITE DIRECTION SAFETY ---
                # Agents traveling in opposite directions on same road are in separate lanes
                if (a1.current_node == a2.target_node) and (a1.target_node == a2.current_node):
                    continue
                
                # --- CALCULATE ACTUAL DISTANCE ---
                # get_position() returns the OFFSET coordinates, ensuring lanes are respected
                pos1 = a1.get_position()
                pos2 = a2.get_position()
                
                distance_meters = self._haversine_distance(pos1, pos2)
                
                # Collision threshold: 2 meters
                if distance_meters < 2.0:
                    # --- CRASH TRIGGER ---
                    if not a1.is_crashed:
                        a1.is_crashed = True
                        a1.crash_timer = 5.0
                    
                    if not a2.is_crashed:
                        a2.is_crashed = True
                        a2.crash_timer = 5.0

    def update(self, dt):
        for agent in self.rickshaws:
            agent.move(dt, self.rickshaws)
            
        self.check_collisions()

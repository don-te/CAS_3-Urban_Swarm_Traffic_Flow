import math
import config as c
from city import CityGraph
from rickshaw import Rickshaw

class SimulationEngine:
    def __init__(self):
        self.city = CityGraph(rows=6, cols=6, block_size_meters=150)
        self.top_left_dest = f"{self.city.rows - 1}-0"
        
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
                new_agent = Rickshaw(new_id, self.city, final_dest=self.top_left_dest)
                self.rickshaws.append(new_agent)
        elif diff < 0:
            self.rickshaws = self.rickshaws[:target_count]

    def check_collisions(self):
        """Checks distance between all agent pairs."""
        count = len(self.rickshaws)
        # Nested loop to compare every pair once
        for i in range(count):
            for j in range(i + 1, count):
                a1 = self.rickshaws[i]
                a2 = self.rickshaws[j]
                
                if a1.is_crashed and a2.is_crashed:
                    continue

                # --- NEW LOGIC: SAFE PASSING ---
                # If agents are on the same road segment but opposite directions,
                # they are separated by the divider. Ignore collision.
                if (a1.current_node == a2.target_node) and (a1.target_node == a2.current_node):
                    continue
                # -------------------------------

                pos1 = a1.get_position()
                pos2 = a2.get_position()

                dx = pos1[0] - pos2[0]
                dy = pos1[1] - pos2[1]
                dist_sq = dx*dx + dy*dy
                
                if dist_sq < (c.COLLISION_DIST * c.COLLISION_DIST):
                    a1.is_crashed = True
                    a2.is_crashed = True

    def update(self, dt):
        for agent in self.rickshaws:
            agent.move(dt, self.rickshaws)
            
        self.check_collisions()

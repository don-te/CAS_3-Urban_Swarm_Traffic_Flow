# src/core/collision.py
import math
from src.utils.math_utils import haversine_distance

class CollisionSystem:
    def __init__(self):
        pass

    def check_collisions(self, agents):
        """
        Checks for collisions between agents.
        Returns the number of NEW collisions detected in this frame.
        """
        count = len(agents)
        new_collisions = 0
        
        for i in range(count):
            for j in range(i + 1, count):
                a1 = agents[i]
                a2 = agents[j]
                
                # Skip conditions
                if a1.is_crashed and a2.is_crashed: continue
                if a1.immunity_timer > 0 or a2.immunity_timer > 0: continue
                if a1.has_arrived or a2.has_arrived: continue
                
                # Traffic logic: Don't crash if essentially trading places or following strictly?
                # The original logic had this skip:
                if (a1.current_node == a2.target_node) and (a1.target_node == a2.current_node): continue
                if a1.target_node is None or a2.target_node is None: continue

                pos1 = a1.get_position()
                pos2 = a2.get_position()
                
                distance_meters = haversine_distance(pos1, pos2)
                
                # 2.5 meters crash radius
                if distance_meters < 2.5:
                    crash = False
                    if not a1.is_crashed:
                        a1.is_crashed = True
                        a1.was_involved_in_crash = True 
                        a1.crash_timer = 5.0
                        crash = True
                    if not a2.is_crashed:
                        a2.is_crashed = True
                        a2.was_involved_in_crash = True
                        a2.crash_timer = 5.0
                        crash = True
                    
                    if crash: 
                        new_collisions += 1
                        
        return new_collisions

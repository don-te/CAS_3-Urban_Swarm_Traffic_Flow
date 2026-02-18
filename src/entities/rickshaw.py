# src/entities/rickshaw.py
import random
import math 
import src.config as c
from src.entities.navigator import Navigator
from src.utils.math_utils import get_angle

class Rickshaw:
    def __init__(self, agent_id, city_graph, start_node=None, 
                 dest_type="NODE", dest_node=None, dest_edge=None, dest_progress=None, 
                 initial_target=None, initial_progress=0.0, speed_factor=None,
                 forbidden_paths=None, forced_path=None):
        self.id = agent_id
        self.city = city_graph
        self.G = city_graph.G
        
        # Start node fallback
        self.current_node = start_node if start_node else random.choice(list(self.G.nodes()))
        
        # Components
        self.navigator = Navigator(city_graph)
        self.navigator.set_forbidden_paths(forbidden_paths)
        self.navigator.set_forced_path(forced_path)

        # --- DESTINATION CONFIG ---
        self.dest_type = dest_type
        self.final_dest_node = dest_node 
        self.dest_edge = dest_edge
        self.dest_progress = dest_progress
        
        # Determine initial nav target
        self.nav_target_node = None
        if self.dest_type == "NODE":
            self.nav_target_node = self.final_dest_node
        else:
            self.nav_target_node = self.dest_edge[0] if self.dest_edge else None

        # Movement State
        self.target_node = initial_target
        self.progress = initial_progress
        self.current_edge = None 
        
        # --- METRICS ---
        self.distance_travelled = 0.0 
        self.travel_time = 0.0
        
        if self.target_node:
            self._enter_edge(self.current_node, self.target_node)
            # If we are part way through, we might need to set up the path
            # But usually initial connection is implied. 
            # We should probably run pathfinding if we have a target but no path yet?
            # For now, let's trust the logic engine setup.
        
        # State Flags
        self.is_crashed = False
        self.was_involved_in_crash = False 
        self.crash_timer = 0.0      
        self.immunity_timer = 2.0   
        self.has_arrived = False 
        self.reversing = False          
        self.blacklisted_edges = set() 
        
        # --- LOGGING DATA ---
        # Cache start position for logs (because get_position changes as we move)
        self.start_pos_coords = self.get_position()
        
        if speed_factor is not None:
            self.speed_factor = speed_factor
        else:
            self.speed_factor = random.choice([0.9, 1.0])

    def _enter_edge(self, u, v):
        if self.G.has_edge(u, v):
            self.G[u][v]['current_load'] += 1
            self.current_edge = (u, v)

    def _leave_edge(self):
        if self.current_edge:
            u, v = self.current_edge
            if self.G.has_edge(u, v):
                if self.G[u][v]['current_load'] > 0:
                    self.G[u][v]['current_load'] -= 1
            self.current_edge = None

    def _pick_new_destination(self, all_agents):
        # 1. Try to use forced path first (via Navigator)
        if self.navigator.forced_path:
             if self.navigator.find_path_to_node(self.current_node, None): 
                 # Path loaded from forced
                 if len(self.navigator.path) > 1 and self.navigator.path[0] == self.current_node:
                     self.target_node = self.navigator.path[1]
                     self.progress = 0.0
                     self._enter_edge(self.current_node, self.target_node)
                     return

        # 2. Standard Logic (New Dest)
        if not self.nav_target_node:
            if random.random() < 0.25:
                self.dest_type = "NODE"
            else:
                self.dest_type = "EDGE"
            
            all_nodes = list(self.G.nodes())

            if self.dest_type == "NODE":
                occupied_destinations = set()
                for agent in all_agents:
                    if agent.id != self.id and agent.dest_type == "NODE" and agent.final_dest_node:
                        occupied_destinations.add(agent.final_dest_node)

                candidates = [n for n in all_nodes if n != self.current_node and n not in occupied_destinations]
                if candidates:
                    self.final_dest_node = random.choice(candidates)
                    self.nav_target_node = self.final_dest_node
                else:
                    self.dest_type = "EDGE"
            
            if self.dest_type == "EDGE": 
                all_edges = list(self.G.edges())
                if all_edges:
                    self.dest_edge = random.choice(all_edges)
                    self.dest_progress = random.uniform(0.2, 0.8) 
                    self.nav_target_node = self.dest_edge[0]
                    self.final_dest_node = None # Clear node dest

        if not self.nav_target_node: return

        # 3. Calculate Path
        # Special case: Dest is Edge and we are at start of edge
        if self.dest_type == "EDGE" and self.current_node == self.nav_target_node:
             self.navigator.path = [self.current_node, self.dest_edge[1]]
             self.navigator.chosen_path = list(self.navigator.path)
        else:
             self.navigator.find_path_to_node(self.current_node, self.nav_target_node, self.blacklisted_edges)

        # Append dest edge end if needed
        if self.dest_type == "EDGE" and len(self.navigator.path) > 0:
            if self.navigator.path[-1] == self.dest_edge[0]:
                    self.navigator.path.append(self.dest_edge[1])

        # 4. Set Initial Target
        if len(self.navigator.path) > 1:
            self.target_node = self.navigator.path[1]
            self.progress = 0.0
            self._enter_edge(self.current_node, self.target_node)
        else:
            # We might be there already
            if self.dest_type == "NODE" and self.current_node == self.final_dest_node:
                self.has_arrived = True
            self.target_node = None


    def _detect_blockage(self, all_agents):
        if not self.target_node: return False
        for other in all_agents:
            if other.id == self.id: continue
            if other.current_node == self.current_node and other.target_node == self.target_node:
                if other.is_crashed and other.progress > self.progress:
                    return True
        return False

    def _get_agent_ahead(self, all_agents):
        closest_dist = 999.0
        target = None
        for other in all_agents:
            if other.id == self.id: continue
            if other.has_arrived: continue
            if (other.current_node == self.current_node and other.target_node == self.target_node):
                if other.progress > self.progress:
                    dist = other.progress - self.progress
                    if dist < closest_dist:
                        closest_dist = dist
                        target = other
        return target, closest_dist

    def move(self, dt, all_agents):
        if self.has_arrived: return
        self.travel_time += dt 

        # --- CRASH LOGIC ---
        if self.is_crashed:
            self.crash_timer -= dt
            if self.crash_timer <= 0:
                self.is_crashed = False
                self.crash_timer = 0.0
                self.immunity_timer = 2.0  
            else: 
                return 
        if self.immunity_timer > 0: self.immunity_timer -= dt

        # --- DECISION LOGIC ---
        if not self.target_node:
            if self.dest_type == "NODE" and self.current_node == self.final_dest_node:
                self.has_arrived = True
                return
            self._pick_new_destination(all_agents)
            if not self.target_node: return

        # Reversing Logic
        if not self.reversing and self.target_node:
             if self._detect_blockage(all_agents):
                self.reversing = True
                self.blacklisted_edges.add((self.current_node, self.target_node))

        # Edge Validity Check
        if not self.G.has_edge(self.current_node, self.target_node):
            self._leave_edge()
            self.target_node = None
            return

        # Speed Calculation
        edge_data = self.G[self.current_node][self.target_node]
        load = edge_data.get('current_load', 1)
        penalty_factor = 1.0 + (load * c.TRAFFIC_PENALTY)
        desired_speed = (c.RICKSHAW_SPEED_BASE * self.speed_factor) / penalty_factor

        # Car Following Logic
        stop_trigger = False
        if not self.reversing:
            agent_ahead, dist_ahead = self._get_agent_ahead(all_agents)
            if agent_ahead and dist_ahead < 0.06:
                stop_trigger = True

        # --- MOVEMENT EXECUTION ---
        if self.reversing:
            step_distance = (desired_speed * 0.8) * dt
            self.progress -= step_distance
            self.distance_travelled += step_distance 
            
            if self.progress <= 0.0:
                self.progress = 0.0
                self.reversing = False
                self._leave_edge()
                self.target_node = None 
                self.navigator.clear_path()
                self._pick_new_destination(all_agents)
        else:
            if stop_trigger:
                current_speed = 0.0
            else:
                current_speed = desired_speed
            
            step_distance = current_speed * dt
            self.progress += step_distance
            self.distance_travelled += step_distance
            
            # Destination Arrival (Edge Case)
            if self.dest_type == "EDGE":
                is_dest_edge = (self.current_node == self.dest_edge[0] and self.target_node == self.dest_edge[1])
                if is_dest_edge and self.progress >= self.dest_progress:
                    self.has_arrived = True
                    self.progress = self.dest_progress
                    self._leave_edge()
                    return

            # Node Arrival (Next Hop)
            if self.progress >= 1.0:
                self._leave_edge()
                self.current_node = self.target_node
                self.progress = 0.0
                
                # Check Final Arrival
                if self.dest_type == "NODE" and self.current_node == self.final_dest_node:
                    self.has_arrived = True
                    self.target_node = None
                    return

                # Advance Path
                self.navigator.advance_path()
                next_node = self.navigator.get_next_node()
                
                if next_node:
                    self.target_node = next_node
                    self._enter_edge(self.current_node, self.target_node)
                else:
                    self.target_node = None
                    self.navigator.clear_path()

    def get_position(self):
        # Delegate geometric logic or keep it here? 
        # For now, keep it here but use math_utils if needed. 
        # But wait, logic_engine uses this for collisions.
        start_pos = self.G.nodes[self.current_node]['pos']
        if not self.target_node: return start_pos
        end_pos = self.G.nodes[self.target_node]['pos']
        
        center_lon = start_pos[0] + (end_pos[0] - start_pos[0]) * self.progress
        center_lat = start_pos[1] + (end_pos[1] - start_pos[1]) * self.progress
        
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        
        dist = math.hypot(dx, dy)
        if dist == 0: return (center_lon, center_lat)
        
        ux = dx / dist
        uy = dy / dist
        perp_x = -uy
        perp_y = ux
        
        offset_lon = center_lon + (perp_x * c.LANE_OFFSET_DEG)
        offset_lat = center_lat + (perp_y * c.LANE_OFFSET_DEG)
        
        return (offset_lon, offset_lat)

    def get_visual_angle(self, start_screen, end_screen):
        return get_angle(start_screen, end_screen) + (math.pi if self.reversing else 0)

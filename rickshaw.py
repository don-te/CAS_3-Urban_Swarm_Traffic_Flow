# rickshaw.py
import networkx as nx
import random
import math 
import config as c

class Rickshaw:
    def __init__(self, agent_id, city_graph, start_node=None, 
                 dest_type="NODE", dest_node=None, dest_edge=None, dest_progress=None, 
                 initial_target=None, initial_progress=0.0, speed_factor=None):
        self.id = agent_id
        self.city = city_graph
        self.G = city_graph.G
        
        # Start node fallback
        self.current_node = start_node if start_node else random.choice(list(self.G.nodes()))
        
        # --- DESTINATION CONFIG ---
        self.dest_type = dest_type
        self.final_dest_node = dest_node 
        self.dest_edge = dest_edge
        self.dest_progress = dest_progress
        
        if self.dest_type == "NODE":
            self.nav_target_node = self.final_dest_node
        else:
            self.nav_target_node = self.dest_edge[0] if self.dest_edge else None

        # Movement State
        self.target_node = initial_target
        self.progress = initial_progress
        self.path = []
        self.current_edge = None 
        
        if self.target_node:
            self._enter_edge(self.current_node, self.target_node)
        
        # State Flags
        self.is_crashed = False
        self.crash_timer = 0.0      
        self.immunity_timer = 2.0   
        self.has_arrived = False 
        self.reversing = False          
        self.blacklisted_edges = set() 
        
        # --- SPEED PERSISTENCE ---
        # If loading from JSON, use the saved factor.
        # If new agent, pick a discrete random value (0.9 or 1.0).
        if speed_factor is not None:
            self.speed_factor = speed_factor
        else:
            self.speed_factor = random.choice([0.9, 1.0])

    def reset_state_for_next_iteration(self):
        self.has_arrived = False
        self.is_crashed = False
        self.crash_timer = 0.0
        self.reversing = False
        self.blacklisted_edges.clear()
        self.dest_type = None 
        self.final_dest_node = None
        self.dest_edge = None
        self.nav_target_node = None
        self.path = []

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

                candidates = [
                    n for n in all_nodes 
                    if n != self.current_node and n not in occupied_destinations
                ]
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

        if not self.nav_target_node: return

        try:
            if self.dest_type == "EDGE" and self.current_node == self.nav_target_node:
                self.path = [self.current_node, self.dest_edge[1]]
            else:
                original_weights = {}
                for u, v in self.blacklisted_edges:
                    if self.G.has_edge(u, v):
                        original_weights[(u, v)] = self.G[u][v]['weight']
                        self.G[u][v]['weight'] = 999999.0

                self.path = nx.shortest_path(self.G, self.current_node, self.nav_target_node, weight='weight')
                
                for (u, v), w in original_weights.items():
                    self.G[u][v]['weight'] = w

                if self.dest_type == "EDGE" and len(self.path) > 0:
                    if self.path[-1] == self.dest_edge[0]:
                         self.path.append(self.dest_edge[1])

            if len(self.path) > 1:
                self.target_node = self.path[1]
                self.progress = 0.0
                self._enter_edge(self.current_node, self.target_node)
            else:
                if self.dest_type == "NODE" and self.current_node == self.final_dest_node:
                    self.has_arrived = True
                self.target_node = None

        except (nx.NetworkXNoPath, nx.NodeNotFound):
            self.target_node = None

    def _detect_blockage(self, all_agents):
        # Only used for Reversing (Stuck behind a crash)
        if not self.target_node: return False
        for other in all_agents:
            if other.id == self.id: continue
            if other.current_node == self.current_node and other.target_node == self.target_node:
                # If the guy ahead is CRASHED and close
                if other.is_crashed and other.progress > self.progress:
                    return True
        return False

    def _get_agent_ahead(self, all_agents):
        """
        Scans for the closest agent directly in front on the same lane.
        Ignores agents that have already arrived (parked).
        """
        closest_dist = 999.0
        target = None
        
        for other in all_agents:
            if other.id == self.id: continue
            if other.has_arrived: continue  # Ignore parked agents
            
            # Must be on the same edge (Start -> End)
            if (other.current_node == self.current_node and 
                other.target_node == self.target_node):
                
                # Check if they are ahead of us
                if other.progress > self.progress:
                    dist = other.progress - self.progress
                    if dist < closest_dist:
                        closest_dist = dist
                        target = other
        return target, closest_dist

    def move(self, dt, all_agents, traffic_manager=None):
        if self.has_arrived: return
        
        # --- TIMERS ---
        if self.is_crashed:
            self.crash_timer -= dt
            if self.crash_timer <= 0:
                self.is_crashed = False
                self.crash_timer = 0.0
                self.immunity_timer = 2.0  
            else: return

        if self.immunity_timer > 0: self.immunity_timer -= dt

        # --- DESTINATION CHECK ---
        if not self.target_node:
            if self.dest_type == "NODE" and self.current_node == self.final_dest_node:
                self.has_arrived = True
                return
            self._pick_new_destination(all_agents)
            if not self.target_node: return

        # --- REVERSING LOGIC ---
        if not self.reversing and self.target_node:
             if self._detect_blockage(all_agents):
                self.reversing = True
                self.blacklisted_edges.add((self.current_node, self.target_node))

        if not self.G.has_edge(self.current_node, self.target_node):
            self._leave_edge()
            self.target_node = None
            return

        # --- TRAFFIC LOGIC START ---
        
        # 1. Base Speed Calculation
        edge_data = self.G[self.current_node][self.target_node]
        load = edge_data.get('current_load', 1)
        penalty_factor = 1.0 + (load * c.TRAFFIC_PENALTY)
        desired_speed = (c.RICKSHAW_SPEED_BASE * self.speed_factor) / penalty_factor

        stop_trigger = False

        # 2. Check Traffic Lights
        if traffic_manager and traffic_manager.active and not self.reversing:
            if self.progress > 0.85:
                signal = traffic_manager.get_signal(self.current_node, self.target_node)
                if signal == "RED":
                    stop_trigger = True
                elif signal == "YELLOW":
                    if self.progress < 0.90:
                        stop_trigger = True

        # 3. Check Queue/Gap Ahead (INTELLIGENT BRAKING)
        if not self.reversing:
            agent_ahead, dist_ahead = self._get_agent_ahead(all_agents)
            if agent_ahead:
                # 0.06 progress is roughly 9 meters (assuming 150m block)
                SAFE_GAP = 0.06 
                if dist_ahead < SAFE_GAP:
                    stop_trigger = True

        # --- APPLY MOVEMENT ---
        
        if self.reversing:
            self.progress -= (desired_speed * 0.8) * dt
            if self.progress <= 0.0:
                self.progress = 0.0
                self.reversing = False
                self._leave_edge()
                self.target_node = None 
                self.path = []
                self._pick_new_destination(all_agents)
        else:
            if stop_trigger:
                current_speed = 0.0
            else:
                current_speed = desired_speed
            
            self.progress += current_speed * dt
            
            # Hard Stop at light (Clamp progress)
            if traffic_manager and traffic_manager.active:
                signal = traffic_manager.get_signal(self.current_node, self.target_node)
                if signal == "RED" and self.progress > 0.92:
                    self.progress = 0.92

            # --- ARRIVAL CHECK: EDGE TYPE ---
            if self.dest_type == "EDGE":
                is_dest_edge = (self.current_node == self.dest_edge[0] and self.target_node == self.dest_edge[1])
                if is_dest_edge and self.progress >= self.dest_progress:
                    self.has_arrived = True
                    self.progress = self.dest_progress
                    self._leave_edge()
                    return

            # --- NODE TRANSITION ---
            if self.progress >= 1.0:
                self._leave_edge()
                self.current_node = self.target_node
                self.progress = 0.0
                
                if self.dest_type == "NODE" and self.current_node == self.final_dest_node:
                    self.has_arrived = True
                    self.target_node = None
                    return

                if len(self.path) > 1:
                    self.path.pop(0) 
                    if len(self.path) > 1:
                        self.target_node = self.path[1]
                        self._enter_edge(self.current_node, self.target_node)
                    else:
                        self.target_node = None
                        self.path = []
                else:
                    self.target_node = None
                    self.path = []

    def get_position(self):
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
        dx = end_screen[0] - start_screen[0]
        dy = -(end_screen[1] - start_screen[1]) 
        angle = math.atan2(dy, dx)
        if self.reversing:
            angle += math.pi 
        return angle

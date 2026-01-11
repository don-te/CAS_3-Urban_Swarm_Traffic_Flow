import networkx as nx
import random
import math 
import config as c

class Rickshaw:
    def __init__(self, agent_id, city_graph, start_node=None, final_dest_edge=None, final_dest_progress=None, initial_target=None, initial_progress=0.0):
        self.id = agent_id
        self.city = city_graph
        self.G = city_graph.G
        
        # Start node fallback
        self.current_node = start_node if start_node else random.choice(list(self.G.nodes()))
        
        # Current Motion
        self.target_node = initial_target
        self.progress = initial_progress
        
        # --- NEW DESTINATION LOGIC ---
        # Instead of just a node, we store the target edge and specific progress
        self.dest_edge = final_dest_edge  # Tuple (u, v)
        self.dest_progress = final_dest_progress # Float 0.0 - 1.0
        
        # Pathfinding target (This is the node we navigate TO to enter the edge)
        self.nav_target_node = self.dest_edge[0] if self.dest_edge else None

        self.path = []
        self.current_edge = None 
        
        if self.target_node:
            self._enter_edge(self.current_node, self.target_node)
        
        # --- CRASH & STATE FLAGS ---
        self.is_crashed = False
        self.crash_timer = 0.0      
        self.immunity_timer = 2.0   
        self.has_arrived = False 
        self.reversing = False          
        self.blacklisted_edges = set() 
        self.speed_factor = random.uniform(0.9, 1.1)

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
        """
        Picks a random edge in the map and a random progress point on it.
        """
        # 1. If we don't have a destination edge, pick a random one
        if not self.dest_edge:
            all_edges = list(self.G.edges())
            if not all_edges: return
            
            # Pick a random edge (u, v)
            self.dest_edge = random.choice(all_edges)
            
            # Pick a random point on that edge (e.g., 20% to 80% marks)
            self.dest_progress = random.uniform(0.2, 0.8)
            
            # The navigation target is the START node of that edge
            self.nav_target_node = self.dest_edge[0]

        # 2. Calculate Path to the START of the target edge
        try:
            # Handle edge case: If we are already AT the start of the target edge
            if self.current_node == self.nav_target_node:
                self.path = [self.current_node, self.dest_edge[1]]
            else:
                # Temporarily block blacklisted edges
                original_weights = {}
                for u, v in self.blacklisted_edges:
                    if self.G.has_edge(u, v):
                        original_weights[(u, v)] = self.G[u][v]['weight']
                        self.G[u][v]['weight'] = 999999.0

                # Path to the node that STARTS the specific edge
                self.path = nx.shortest_path(self.G, self.current_node, self.nav_target_node, weight='weight')
                
                # Restore weights
                for (u, v), w in original_weights.items():
                    self.G[u][v]['weight'] = w
            
            # Set initial movement
            if len(self.path) > 1:
                self.target_node = self.path[1]
                self.progress = 0.0
                self._enter_edge(self.current_node, self.target_node)
            elif len(self.path) == 1 and self.current_node == self.dest_edge[0]:
                # We are at the start node, next step is the target edge
                self.target_node = self.dest_edge[1]
                self.progress = 0.0
                self._enter_edge(self.current_node, self.target_node)
            else:
                self.target_node = None

        except (nx.NetworkXNoPath, nx.NodeNotFound):
            self.target_node = None

    def _detect_blockage(self, all_agents):
        if not self.target_node: return False
        for other in all_agents:
            if other.id == self.id: continue
            if other.current_node == self.current_node and other.target_node == self.target_node:
                if other.is_crashed and other.progress > self.progress:
                    return True
        return False

    def move(self, dt, all_agents):
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
            self._pick_new_destination(all_agents)
            if not self.target_node: return

        # --- MOVEMENT CALCULATION ---
        # ... (Existing blockage and reversing logic remains mostly the same) ...
        if not self.reversing and self.target_node:
             if self._detect_blockage(all_agents):
                self.reversing = True
                self.blacklisted_edges.add((self.current_node, self.target_node))

        if not self.G.has_edge(self.current_node, self.target_node):
            self._leave_edge()
            self.target_node = None
            return

        edge_data = self.G[self.current_node][self.target_node]
        load = edge_data.get('current_load', 1)
        penalty_factor = 1.0 + (load * c.TRAFFIC_PENALTY)
        current_speed = (c.RICKSHAW_SPEED_BASE * self.speed_factor) / penalty_factor
        
        if self.reversing:
            self.progress -= (current_speed * 0.8) * dt
            if self.progress <= 0.0:
                self.progress = 0.0
                self.reversing = False
                self._leave_edge()
                self.target_node = None 
                self.path = []
                self._pick_new_destination(all_agents)
        else:
            self.progress += current_speed * dt

            # --- NEW ARRIVAL CHECK ---
            # Check if we are on the specific Destination Edge
            is_dest_edge = (self.current_node == self.dest_edge[0] and self.target_node == self.dest_edge[1])
            
            if is_dest_edge and self.progress >= self.dest_progress:
                # We have arrived at the specific point!
                self.has_arrived = True
                self.progress = self.dest_progress # Snap to exact spot
                self._leave_edge() # Technically we "leave" traffic flow when parked
                return

            # Standard node transition
            if self.progress >= 1.0:
                self._leave_edge()
                self.current_node = self.target_node
                self.progress = 0.0
                
                # Advance path
                if len(self.path) > 2:
                    self.path.pop(0)
                    self.target_node = self.path[1]
                    self._enter_edge(self.current_node, self.target_node)
                elif len(self.path) == 2:
                    # We just finished the previous edge, now entering the FINAL edge (dest edge)
                    self.path.pop(0)
                    self.target_node = self.dest_edge[1] # Ensure we target the end of dest edge
                    self._enter_edge(self.current_node, self.target_node)
                else:
                    # Should be caught by is_dest_edge logic, but safety fallback
                    self.target_node = None
                    self.path = []

    # get_position and get_visual_angle remain exactly the same as original file
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
        if self.reversing: angle += math.pi 
        return angle

# rickshaw.py
import networkx as nx
import random
import math 
import config as c

class Rickshaw:
    # UPDATED INIT SIGNATURE
    def __init__(self, agent_id, city_graph, start_node=None, final_dest=None, initial_target=None, initial_progress=0.0):
        self.id = agent_id
        self.city = city_graph
        self.G = city_graph.G
        
        # If start_node is not provided, pick a random one
        self.current_node = start_node if start_node else random.choice(list(self.G.nodes()))
        
        # --- NEW: SUPPORT FOR EDGE SPAWNING ---
        self.target_node = initial_target
        self.progress = initial_progress
        self.destination_node = None
        self.final_dest = final_dest
        
        self.path = []
        self.current_edge = None 
        
        # If we spawn on an edge, register the load immediately
        if self.target_node:
            self._enter_edge(self.current_node, self.target_node)
        
        # --- CRASH LOGIC ---
        self.is_crashed = False
        self.crash_timer = 0.0      
        self.immunity_timer = 2.0   
        
        # Speed Variance
        self.speed_factor = random.uniform(0.9, 1.1)
        
        # Navigation
        self.reversing = False          
        self.blacklisted_edges = set() 

    # ... [Keep the rest of the file (move, get_position, etc.) exactly the same] ...

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

    def _pick_new_destination(self):
        try:
            target = self.final_dest if self.final_dest else random.choice(list(self.G.nodes()))
            if target == self.current_node:
                self.target_node = None
                return
            self.destination_node = target

            original_weights = {}
            for u, v in self.blacklisted_edges:
                if self.G.has_edge(u, v):
                    original_weights[(u, v)] = self.G[u][v]['weight']
                    self.G[u][v]['weight'] = 999999.0 

            try:
                self.path = nx.shortest_path(self.G, self.current_node, self.destination_node, weight='weight')
            finally:
                for (u, v), w in original_weights.items():
                    self.G[u][v]['weight'] = w
            
            if len(self.path) > 1:
                self.target_node = self.path[1]
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
        if self.is_crashed:
            self.crash_timer -= dt
            if self.crash_timer <= 0:
                self.is_crashed = False
                self.crash_timer = 0.0
                self.immunity_timer = 2.0  
            else:
                return 

        if self.immunity_timer > 0:
            self.immunity_timer -= dt

        if not self.reversing and self.target_node:
            if self._detect_blockage(all_agents):
                self.reversing = True
                self.blacklisted_edges.add((self.current_node, self.target_node))

        # --- MODIFIED: Handle case where we spawn without a path but WITH a target ---
        if not self.target_node:
            self._pick_new_destination()
            return

        if not self.G.has_edge(self.current_node, self.target_node):
            self._leave_edge()
            self.target_node = None
            return

        edge_data = self.G[self.current_node][self.target_node]
        load = edge_data.get('current_load', 1)
        penalty_factor = 1.0 + (load * c.TRAFFIC_PENALTY)
        
        base_speed = c.RICKSHAW_SPEED_BASE * self.speed_factor
        current_speed = base_speed / penalty_factor
        
        if self.reversing:
            self.progress -= (current_speed * 0.8) * dt
            if self.progress <= 0.0:
                self.progress = 0.0
                self.reversing = False
                self._leave_edge()
                self.target_node = None 
                self.path = []
                self._pick_new_destination()
        else:
            self.progress += current_speed * dt
            if self.progress >= 1.0:
                self._leave_edge()
                self.current_node = self.target_node
                self.progress = 0.0
                if len(self.path) > 2:
                    self.path.pop(0)
                    self.target_node = self.path[1]
                    self._enter_edge(self.current_node, self.target_node)
                else:
                    self.target_node = None
                    self.path = [] # Clear path so we pick a new random dest next frame

    def get_position(self):
        start_pos = self.G.nodes[self.current_node]['pos']
        
        if not self.target_node: 
            return start_pos
            
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
        import math
        dx = end_screen[0] - start_screen[0]
        dy = -(end_screen[1] - start_screen[1]) 
        angle = math.atan2(dy, dx)
        if self.reversing:
            angle += math.pi 
        return angle

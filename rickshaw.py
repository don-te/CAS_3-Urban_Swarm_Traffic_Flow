import networkx as nx
import random
import math 
import config as c

class Rickshaw:
    def __init__(self, agent_id, city_graph, start_node=None, final_dest=None, initial_target=None, initial_progress=0.0):
        self.id = agent_id
        self.city = city_graph
        self.G = city_graph.G
        
        # If start_node is not provided, pick a random one (Fallback)
        self.current_node = start_node if start_node else random.choice(list(self.G.nodes()))
        
        # --- EDGE SPAWNING SUPPORT ---
        self.target_node = initial_target
        self.progress = initial_progress
        
        # "final_dest" is the ultimate goal. "destination_node" is the current trip target.
        self.final_dest = final_dest
        self.destination_node = final_dest 
        
        self.path = []
        self.current_edge = None 
        
        # If we spawn on an edge, register the load immediately
        if self.target_node:
            self._enter_edge(self.current_node, self.target_node)
        
        # --- CRASH LOGIC ---
        self.is_crashed = False
        self.crash_timer = 0.0      
        self.immunity_timer = 2.0   
        
        # --- STATE FLAGS ---
        self.has_arrived = False 
        self.reversing = False          
        self.blacklisted_edges = set() 

        # Speed Variance
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
        Calculates a path to the destination.
        If no destination exists yet, picks a random unique one.
        """
        # 1. If we already have a fixed final destination, stick to it.
        if self.final_dest:
            self.destination_node = self.final_dest
        else:
            # Logic to pick a random unique destination if one wasn't assigned at spawn
            all_nodes = list(self.G.nodes())
            
            # Identify destinations currently claimed by OTHERS
            claimed_destinations = set()
            if all_agents:
                for agent in all_agents:
                    if agent.id != self.id and agent.destination_node:
                        claimed_destinations.add(agent.destination_node)

            # Filter valid candidates
            valid_candidates = []
            for n in all_nodes:
                if n == self.current_node: continue
                if n in claimed_destinations: continue
                valid_candidates.append(n)

            if valid_candidates:
                self.destination_node = random.choice(valid_candidates)
            else:
                # Fallback: just pick any node != current
                fallback = [n for n in all_nodes if n != self.current_node]
                if fallback: self.destination_node = random.choice(fallback)
                else: return # Map has only 1 node?

        # 2. Calculate Path
        try:
            # Temporarily block blacklisted edges
            original_weights = {}
            for u, v in self.blacklisted_edges:
                if self.G.has_edge(u, v):
                    original_weights[(u, v)] = self.G[u][v]['weight']
                    self.G[u][v]['weight'] = 999999.0 

            self.path = nx.shortest_path(self.G, self.current_node, self.destination_node, weight='weight')
            
            # Restore weights
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
        # --- 1. STOP IF ARRIVED ---
        if self.has_arrived:
            return

        # --- 2. HANDLE TIMERS ---
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

        # --- 3. DESTINATION CHECK ---
        if not self.target_node:
            # Check if we are at the destination
            if self.destination_node and self.current_node == self.destination_node:
                self.has_arrived = True
                return
            
            # If not, try to get a path
            self._pick_new_destination(all_agents)
            
            # If still no target (e.g. already at dest or calculation failed)
            if not self.target_node:
                if self.destination_node == self.current_node:
                    self.has_arrived = True
                return

        # --- 4. MOVEMENT LOGIC ---
        # Blockage Detection
        if not self.reversing and self.target_node:
            if self._detect_blockage(all_agents):
                self.reversing = True
                self.blacklisted_edges.add((self.current_node, self.target_node))

        # Edge Validation
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
                self._pick_new_destination(all_agents)
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
                    # End of path
                    self.target_node = None
                    self.path = []
                    # Next frame loop will catch the "Destination Check" and set has_arrived=True

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
        
        # Perpendicular Vector (Left Hand Rule)
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

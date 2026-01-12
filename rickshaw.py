import networkx as nx
import random
import math 
import config as c

class Rickshaw:
    def __init__(self, agent_id, city_graph, start_node=None, 
                 dest_type="NODE", dest_node=None, dest_edge=None, dest_progress=None, 
                 initial_target=None, initial_progress=0.0):
        self.id = agent_id
        self.city = city_graph
        self.G = city_graph.G
        
        # Start node fallback
        self.current_node = start_node if start_node else random.choice(list(self.G.nodes()))
        
        # --- DESTINATION CONFIG ---
        self.dest_type = dest_type  # "NODE" or "EDGE"
        
        # Mode A: Node Destination
        self.final_dest_node = dest_node 
        
        # Mode B: Edge Destination
        self.dest_edge = dest_edge        # Tuple (u, v)
        self.dest_progress = dest_progress # Float 0.0 - 1.0
        
        # Determine Navigation Target (The node A* calculates path to)
        if self.dest_type == "NODE":
            self.nav_target_node = self.final_dest_node
        else:
            # If Edge destination, we navigate to the START of that edge
            self.nav_target_node = self.dest_edge[0] if self.dest_edge else None

        # Movement State
        self.target_node = initial_target
        self.progress = initial_progress
        self.path = []
        self.current_edge = None 
        
        # Initial Edge Entry
        if self.target_node:
            self._enter_edge(self.current_node, self.target_node)
        
        # State Flags
        self.is_crashed = False
        self.crash_timer = 0.0      
        self.immunity_timer = 2.0   
        self.has_arrived = False 
        self.reversing = False          
        self.blacklisted_edges = set() 
        self.speed_factor = random.uniform(0.9, 1.1)

    def reset_state_for_next_iteration(self):
        """
        Called when the user clicks 'Next Iteration'.
        Keeps current position, but clears destination so a new one is picked.
        """
        self.has_arrived = False
        self.is_crashed = False
        self.crash_timer = 0.0
        self.reversing = False
        self.blacklisted_edges.clear()
        
        # Clear Destination info to trigger _pick_new_destination logic
        self.dest_type = None 
        self.final_dest_node = None
        self.dest_edge = None
        self.nav_target_node = None
        self.path = []
        
        # Note: We do NOT reset self.current_node or self.progress.
        # The agent starts exactly where they finished the previous trip.

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
        Picks a new destination (Node or Edge) and calculates the path.
        """
        # 1. Decide Destination if not set
        if not self.nav_target_node:
            # Probability Split: 25% Node, 75% Edge
            if random.random() < 0.25:
                self.dest_type = "NODE"
            else:
                self.dest_type = "EDGE"
            
            all_nodes = list(self.G.nodes())

            if self.dest_type == "NODE":
                # --- UNIQUE NODE CHECK ---
                # Gather destination nodes currently claimed by other agents
                occupied_destinations = set()
                for agent in all_agents:
                    if agent.id != self.id and agent.dest_type == "NODE" and agent.final_dest_node:
                        occupied_destinations.add(agent.final_dest_node)

                # Filter candidates: exclude current node AND occupied nodes
                candidates = [
                    n for n in all_nodes 
                    if n != self.current_node and n not in occupied_destinations
                ]

                if candidates:
                    self.final_dest_node = random.choice(candidates)
                    self.nav_target_node = self.final_dest_node
                else:
                    # If all nodes are taken, force fallback to EDGE
                    self.dest_type = "EDGE"
            
            if self.dest_type == "EDGE": 
                all_edges = list(self.G.edges())
                if all_edges:
                    self.dest_edge = random.choice(all_edges)
                    self.dest_progress = random.uniform(0.2, 0.8) 
                    self.nav_target_node = self.dest_edge[0]

        # 2. Calculate Path
        if not self.nav_target_node: return

        try:
            # Handle "Already at start of target edge" case
            if self.dest_type == "EDGE" and self.current_node == self.nav_target_node:
                self.path = [self.current_node, self.dest_edge[1]]
            else:
                # Standard A*
                original_weights = {}
                for u, v in self.blacklisted_edges:
                    if self.G.has_edge(u, v):
                        original_weights[(u, v)] = self.G[u][v]['weight']
                        self.G[u][v]['weight'] = 999999.0

                self.path = nx.shortest_path(self.G, self.current_node, self.nav_target_node, weight='weight')
                
                # Restore weights
                for (u, v), w in original_weights.items():
                    self.G[u][v]['weight'] = w

                # A* gets us to the START of the edge. We need to manually add the END of the edge
                if self.dest_type == "EDGE" and len(self.path) > 0:
                    if self.path[-1] == self.dest_edge[0]:
                         self.path.append(self.dest_edge[1])

            # Set Initial Move
            if len(self.path) > 1:
                self.target_node = self.path[1]
                self.progress = 0.0
                self._enter_edge(self.current_node, self.target_node)
            else:
                # Already at Node Destination
                if self.dest_type == "NODE" and self.current_node == self.final_dest_node:
                    self.has_arrived = True
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
        # If we don't have a target, pick one immediately
        if not self.target_node:
            # Immediate arrival check for NODE type (if just reset)
            if self.dest_type == "NODE" and self.current_node == self.final_dest_node:
                self.has_arrived = True
                return
            
            self._pick_new_destination(all_agents)
            if not self.target_node: return

        # --- MOVEMENT LOGIC ---
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

            # --- ARRIVAL CHECK: EDGE TYPE ---
            if self.dest_type == "EDGE":
                is_dest_edge = (self.current_node == self.dest_edge[0] and self.target_node == self.dest_edge[1])
                if is_dest_edge and self.progress >= self.dest_progress:
                    self.has_arrived = True
                    self.progress = self.dest_progress # Snap to exact spot
                    self._leave_edge() # Parked agents leave the traffic load
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

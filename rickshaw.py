import networkx as nx
import random
import config as c

class Rickshaw:
    def __init__(self, agent_id, city_graph, final_dest=None):
        self.id = agent_id
        self.city = city_graph
        self.G = city_graph.G
        
        # Position
        self.current_node = random.choice(list(self.G.nodes()))
        self.target_node = None
        self.destination_node = None
        
        # Navigation
        self.final_dest = final_dest
        self.path = []
        self.progress = 0.0
        
        # State tracking
        self.current_edge = None
        self.is_crashed = False  # <--- NEW STATE

    # [Keep _enter_edge, _leave_edge, _pick_new_destination as is...]
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
            if self.final_dest:
                if self.current_node == self.final_dest:
                    self.target_node = None
                    return
                self.destination_node = self.final_dest
            else:
                self.destination_node = random.choice(list(self.G.nodes()))

            self.path = nx.shortest_path(self.G, self.current_node, self.destination_node, weight='weight')
            
            if len(self.path) > 1:
                next_node = self.path[1]
                self.target_node = next_node
                self.progress = 0.0
                self._enter_edge(self.current_node, self.target_node)
            else:
                self.target_node = None
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            self.target_node = None

    def move(self, dt):
        # 1. STOP IF CRASHED
        if self.is_crashed:
            return

        # 2. If no target, find one
        if not self.target_node:
            self._pick_new_destination()
            return

        # [Keep rest of the move logic...]
        if not self.G.has_edge(self.current_node, self.target_node):
            self._leave_edge()
            self.target_node = None
            return

        edge_data = self.G[self.current_node][self.target_node]
        load = edge_data.get('current_load', 1) 
        
        penalty_factor = 1.0 + (load * c.TRAFFIC_PENALTY)
        current_speed = c.RICKSHAW_SPEED_BASE / penalty_factor
        
        self.progress += current_speed * dt

        if self.progress >= 1.0:
            self._leave_edge() 
            self.current_node = self.target_node
            self.progress = 0.0
            
            if len(self.path) > 2:
                self.path.pop(0) 
                next_node = self.path[1]
                self.target_node = next_node
                self._enter_edge(self.current_node, self.target_node)
            else:
                self.target_node = None
                self.path = []

    def get_position(self):
        node_pos = self.G.nodes[self.current_node]['pos']
        
        if not self.target_node: 
            return node_pos
            
        target_pos = self.G.nodes[self.target_node]['pos']
        
        lon = node_pos[0] + (target_pos[0] - node_pos[0]) * self.progress
        lat = node_pos[1] + (target_pos[1] - node_pos[1]) * self.progress
        return (lon, lat)

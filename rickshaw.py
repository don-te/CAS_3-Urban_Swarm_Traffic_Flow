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
        self.final_dest = final_dest  # The common destination
        self.path = []
        self.progress = 0.0
        
        # State tracking for Load Management
        self.current_edge = None 

    def _enter_edge(self, u, v):
        """Safely increments load on the new edge."""
        if self.G.has_edge(u, v):
            self.G[u][v]['current_load'] += 1
            self.current_edge = (u, v)

    def _leave_edge(self):
        """Safely decrements load on the previous edge."""
        if self.current_edge:
            u, v = self.current_edge
            if self.G.has_edge(u, v):
                if self.G[u][v]['current_load'] > 0:
                    self.G[u][v]['current_load'] -= 1
            self.current_edge = None

    def _pick_new_destination(self):
        """Calculates path to the destination."""
        try:
            # 1. Determine Destination
            if self.final_dest:
                # If we have a forced destination (Top Left)
                if self.current_node == self.final_dest:
                    # We have arrived; stop moving.
                    self.target_node = None
                    return
                self.destination_node = self.final_dest
            else:
                # Default random behavior
                self.destination_node = random.choice(list(self.G.nodes()))

            # 2. Calculate Shortest Path (Dijkstra)
            self.path = nx.shortest_path(self.G, self.current_node, self.destination_node, weight='weight')
            
            # 3. Set next step
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
        # 1. If no target, find one
        if not self.target_node:
            self._pick_new_destination()
            return

        # 2. Check if edge still exists (robustness)
        if not self.G.has_edge(self.current_node, self.target_node):
            self._leave_edge()
            self.target_node = None
            return

        # 3. Calculate Speed based on Traffic Load
        edge_data = self.G[self.current_node][self.target_node]
        load = edge_data.get('current_load', 1) 
        
        penalty_factor = 1.0 + (load * c.TRAFFIC_PENALTY)
        current_speed = c.RICKSHAW_SPEED_BASE / penalty_factor
        
        # 4. Advance
        self.progress += current_speed * dt

        # 5. Check Arrival
        if self.progress >= 1.0:
            self._leave_edge() 
            self.current_node = self.target_node
            self.progress = 0.0
            
            # Advance in path
            if len(self.path) > 2:
                self.path.pop(0) 
                next_node = self.path[1]
                self.target_node = next_node
                self._enter_edge(self.current_node, self.target_node)
            else:
                # End of path (Arrived at destination)
                self.target_node = None
                self.path = []

    def get_position(self):
        """Returns interpolated (lon, lat) for smooth rendering."""
        node_pos = self.G.nodes[self.current_node]['pos']
        
        if not self.target_node: 
            return node_pos
            
        target_pos = self.G.nodes[self.target_node]['pos']
        
        lon = node_pos[0] + (target_pos[0] - node_pos[0]) * self.progress
        lat = node_pos[1] + (target_pos[1] - node_pos[1]) * self.progress
        return (lon, lat)

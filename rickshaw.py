import networkx as nx
import random
import config as c

class Rickshaw:
    def __init__(self, agent_id, city_graph):
        self.id = agent_id
        self.city = city_graph
        self.G = city_graph.G
        self.current_node = random.choice(list(self.G.nodes()))
        self.target_node = None
        self.destination_node = None
        self.path = []
        self.progress = 0.0
        self.passenger = None
        self.money = 0
        self.state = "IDLE"

    def hunt(self, all_passengers):
        if self.passenger or not all_passengers: return
        
        # Greedy search for nearest passenger
        best_pax = None
        min_dist = float('inf')
        my_pos = self.city.G.nodes[self.current_node]['pos']
        
        for pax in all_passengers:
            pax_pos = self.city.G.nodes[pax.node]['pos']
            dist = (my_pos[0]-pax_pos[0])**2 + (my_pos[1]-pax_pos[1])**2
            if dist < min_dist:
                min_dist = dist
                best_pax = pax
        
        if best_pax:
            # FIX: Only recalculate if the destination is NEW
            if self.destination_node != best_pax.node:
                self.destination_node = best_pax.node
                self.state = "HUNTING"
                self._recalculate_path()

    def _recalculate_path(self):
        try:
            # Clean up load on the old edge if we are switching mid-journey
            if self.target_node and self.current_node != self.target_node:
                if self.G.has_edge(self.current_node, self.target_node):
                    self.G[self.current_node][self.target_node]['current_load'] -= 1
                    if self.G[self.current_node][self.target_node]['current_load'] < 0:
                        self.G[self.current_node][self.target_node]['current_load'] = 0
            
            if not self.destination_node:
                self.destination_node = random.choice(list(self.G.nodes()))
            
            # Calculate new path
            self.path = nx.shortest_path(self.G, self.current_node, self.destination_node, weight='weight')
            
            if len(self.path) > 1:
                self.target_node = self.path[1]
                self.progress = 0.0
                # Add load to the new edge we are taking
                self.G[self.current_node][self.target_node]['current_load'] += 1
            else:
                self.target_node = None
        except (nx.NetworkXNoPath, KeyError):
            # Fallback if pathfinding fails
            self.target_node = None

    def move(self, dt):
        if not self.target_node:
            # If idle or finished job, pick random
            if not self.destination_node or self.current_node == self.destination_node:
                 self.destination_node = random.choice(list(self.G.nodes()))
                 self._recalculate_path()
            return

        # Safety check for graph changes
        if not self.G.has_edge(self.current_node, self.target_node):
            self.target_node = None
            return
        
        # 1. Calculate Speed based on Traffic
        edge_data = self.G.get_edge_data(self.current_node, self.target_node)
        load = edge_data.get('current_load', 0)
        
        # Formula: Higher load = Lower speed
        current_speed = c.RICKSHAW_SPEED_BASE / (1 + load * c.TRAFFIC_PENALTY)
        
        # 2. Move
        self.progress += current_speed * dt
        
        # 3. Reach Next Node
        if self.progress >= 1.0:
            # Remove load from the edge we just finished
            if self.target_node:
                self.G[self.current_node][self.target_node]['current_load'] -= 1
            
            # Update Position
            self.current_node = self.target_node
            self.progress = 0.0
            
            # Pick next step in path
            if len(self.path) > 2:
                self.path.pop(0)
                self.target_node = self.path[1]
                # Add load to the next edge
                self.G[self.current_node][self.target_node]['current_load'] += 1
            else:
                self.target_node = None

    def get_position(self):
        if not self.target_node: return self.G.nodes[self.current_node]['pos']
        start = self.G.nodes[self.current_node]['pos']
        end = self.G.nodes[self.target_node]['pos']
        lon = start[0] + (end[0] - start[0]) * self.progress
        lat = start[1] + (end[1] - start[1]) * self.progress
        return (lon, lat)
# agents.py
import networkx as nx
import random
import config as c

class Passenger:
    def __init__(self, node_id, destination_id):
        self.node = node_id
        self.dest = destination_id
        self.spawn_time = 0

class Rickshaw:
    def __init__(self, agent_id, city_graph):
        self.id = agent_id
        self.city = city_graph
        self.G = city_graph.G
        
        # State
        self.current_node = random.choice(list(self.G.nodes()))
        self.target_node = None
        self.destination_node = None
        self.path = []
        self.progress = 0.0
        
        # "Snake" State
        self.passenger = None  # None or Passenger Object
        self.money = 0
        self.state = "IDLE"    # IDLE, HUNTING, DELIVERING

    def hunt(self, all_passengers):
        """Finds the nearest passenger if empty."""
        if self.passenger or not all_passengers:
            return

        # Simple Greedy Logic: Find closest passenger by grid distance
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
            self.destination_node = best_pax.node
            self.state = "HUNTING"
            self._recalculate_path()

    def _recalculate_path(self):
        try:
            # If no specific destination, pick random
            if not self.destination_node:
                self.destination_node = random.choice(list(self.G.nodes()))
                
            self.path = nx.shortest_path(self.G, self.current_node, self.destination_node, weight='weight')
            if len(self.path) > 1:
                self.target_node = self.path[1]
                self.progress = 0.0
            else:
                self.target_node = None
        except:
            self.target_node = None

    def move(self, dt):
        """
        Moves along the edge.
        dt: Delta time (seconds) to ensure smooth movement regardless of FPS.
        """
        if not self.target_node:
            # Reached Target (Pickup or Dropoff?)
            if self.state == "HUNTING" and self.current_node == self.destination_node:
                # Logic handled in main loop (Pickup)
                pass 
            elif self.state == "DELIVERING" and self.current_node == self.destination_node:
                # Logic handled in main loop (Dropoff)
                pass
            else:
                # Just wandering
                self.destination_node = random.choice(list(self.G.nodes()))
                self._recalculate_path()
            return

        # --- TRAFFIC LOGIC ---
        # Check load on the edge I am traversing
        edge_data = self.G.get_edge_data(self.current_node, self.target_node)
        load = edge_data.get('current_load', 0)
        
        # Formula: Speed = Base / (1 + Load * Penalty)
        current_speed = c.RICKSHAW_SPEED_BASE / (1 + load * c.TRAFFIC_PENALTY)
        
        # Advance
        self.progress += current_speed * dt
        
        if self.progress >= 1.0:
            # Arrived at next node
            # 1. Update Graph Load (Leaving Edge)
            if self.target_node:
                self.G[self.current_node][self.target_node]['current_load'] -= 1
            
            self.current_node = self.target_node
            self.progress = 0.0
            
            if len(self.path) > 2:
                self.path.pop(0)
                self.target_node = self.path[1]
                # 2. Update Graph Load (Entering Edge)
                self.G[self.current_node][self.target_node]['current_load'] += 1
            else:
                self.target_node = None

    def get_position(self):
        # ... (Same interpolation logic as before) ...
        if not self.target_node:
            return self.G.nodes[self.current_node]['pos']
        start = self.G.nodes[self.current_node]['pos']
        end = self.G.nodes[self.target_node]['pos']
        lon = start[0] + (end[0] - start[0]) * self.progress
        lat = start[1] + (end[1] - start[1]) * self.progress
        return (lon, lat)
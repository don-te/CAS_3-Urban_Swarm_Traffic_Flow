# traffic_control.py
import random
import config as c

class TrafficManager:
    def __init__(self, city_graph):
        self.city = city_graph
        self.active = False  # Toggled by UI
        self.intersections = {}  # Map node_id -> state
        self.cycle_timer = 0.0
        self.phase_duration = 6.0  # Seconds per green light
        self.yellow_duration = 2.0
        
        self._initialize_intersections()

    def _initialize_intersections(self):
        """
        Scans the graph to group incoming edges by orientation.
        """
        for node in self.city.G.nodes():
            # Find all edges ENTERING this node
            incoming = list(self.city.G.in_edges(node, data=True))
            if not incoming: continue

            # Group by street orientation (Vertical vs Horizontal)
            vert_edges = []
            horiz_edges = []

            for u, v, data in incoming:
                # The CityGraph tags edges as 'vertical' or 'horizontal'
                # Note: u is start, v is current node (intersection)
                edge_type = data.get('type', 'horizontal')
                if edge_type == 'vertical':
                    vert_edges.append(u)
                else:
                    horiz_edges.append(u)

            self.intersections[node] = {
                "vertical": vert_edges,
                "horizontal": horiz_edges,
                "phase": "V_GREEN", # V_GREEN, V_YELLOW, H_GREEN, H_YELLOW
                "timer": random.uniform(0, self.phase_duration) # Random start to desync lights
            }

    def toggle(self):
        self.active = not self.active
        print(f"Traffic Lights Active: {self.active}")

    def update(self, dt):
        if not self.active: return

        for node_id, data in self.intersections.items():
            data['timer'] -= dt
            
            if data['timer'] <= 0:
                # State Machine for Lights
                current = data['phase']
                
                if current == "V_GREEN":
                    data['phase'] = "V_YELLOW"
                    data['timer'] = self.yellow_duration
                elif current == "V_YELLOW":
                    data['phase'] = "H_GREEN"
                    data['timer'] = self.phase_duration
                elif current == "H_GREEN":
                    data['phase'] = "H_YELLOW"
                    data['timer'] = self.yellow_duration
                elif current == "H_YELLOW":
                    data['phase'] = "V_GREEN"
                    data['timer'] = self.phase_duration

    def get_signal(self, current_node, target_node):
        """
        Returns 'GREEN', 'YELLOW', or 'RED' for an agent traveling 
        FROM current_node TO target_node (intersection).
        """
        if not self.active: return "GREEN"
        
        # We are entering target_node. Check its state.
        if target_node not in self.intersections: return "GREEN"
        
        state = self.intersections[target_node]
        phase = state['phase']
        
        # Which group is the agent coming from?
        # We check if 'current_node' is in the vertical or horizontal incoming list
        is_vertical = current_node in state['vertical']
        
        if is_vertical:
            if phase == "V_GREEN": return "GREEN"
            if phase == "V_YELLOW": return "YELLOW"
            return "RED"
        else:
            if phase == "H_GREEN": return "GREEN"
            if phase == "H_YELLOW": return "YELLOW"
            return "RED"

# traffic_control.py
import random
import config as c

class TrafficManager:
    def __init__(self, city_graph):
        self.city = city_graph
        self.active = False
        self.mode = "TWO_WAY"  # Options: "TWO_WAY", "ONE_WAY"
        
        self.intersections = {} 
        self.cycle_timer = 0.0
        self.phase_duration = 6.0
        self.yellow_duration = 2.0
        
        self._initialize_intersections()

    def _initialize_intersections(self):
        for node in self.city.G.nodes():
            incoming = list(self.city.G.in_edges(node, data=True))
            if not incoming: continue

            # Parse Node ID "r-c" to integers
            curr_r, curr_c = map(int, node.split('-'))

            # Buckets for 4 directions
            # "North_Inc" means coming FROM North (moving South)
            groups = {
                "north_inc": [], # u.r > curr_r
                "south_inc": [], # u.r < curr_r
                "east_inc":  [], # u.c > curr_c
                "west_inc":  []  # u.c < curr_c
            }

            for u, v, data in incoming:
                u_r, u_c = map(int, u.split('-'))
                
                if u_r > curr_r: groups["north_inc"].append(u)
                elif u_r < curr_r: groups["south_inc"].append(u)
                elif u_c > curr_c: groups["east_inc"].append(u)
                elif u_c < curr_c: groups["west_inc"].append(u)

            self.intersections[node] = {
                "groups": groups,
                "phase": 0, # 0=N, 1=E, 2=S, 3=W (Clockwise)
                "state": "GREEN", # GREEN, YELLOW
                "timer": random.uniform(0, self.phase_duration)
            }

    def toggle_mode(self):
        if not self.active:
            self.active = True
            self.mode = "TWO_WAY"
            print("Traffic Lights: ON (2-Way)")
        elif self.mode == "TWO_WAY":
            self.mode = "ONE_WAY"
            print("Traffic Lights: ONE_WAY (4-Phase)")
        else:
            self.active = False
            self.mode = "TWO_WAY" # Reset
            print("Traffic Lights: OFF")

    def update(self, dt):
        if not self.active: return

        for node_id, data in self.intersections.items():
            data['timer'] -= dt
            
            if data['timer'] <= 0:
                # --- STATE MACHINE ---
                if data['state'] == "GREEN":
                    # Switch to Yellow
                    data['state'] = "YELLOW"
                    data['timer'] = self.yellow_duration
                else:
                    # Switch to Next Green Phase
                    data['state'] = "GREEN"
                    data['timer'] = self.phase_duration
                    
                    # Cycle Logic
                    current_phase = data['phase']
                    
                    if self.mode == "TWO_WAY":
                        # Toggle 0 (Vertical) <-> 1 (Horizontal)
                        # We map 0->N/S, 1->E/W
                        data['phase'] = 1 if current_phase == 0 else 0
                    else:
                        # Cycle 0->1->2->3 (N->E->S->W)
                        data['phase'] = (current_phase + 1) % 4

    def get_signal(self, current_node, target_node):
        if not self.active: return "GREEN"
        if target_node not in self.intersections: return "GREEN"
        
        data = self.intersections[target_node]
        phase = data['phase']
        state = data['state']
        groups = data['groups']

        # Determine allowed groups based on Phase & Mode
        allowed_groups = []
        
        if self.mode == "TWO_WAY":
            if phase == 0: # Vertical Phase
                allowed_groups = groups['north_inc'] + groups['south_inc']
            else:          # Horizontal Phase
                allowed_groups = groups['east_inc'] + groups['west_inc']
        else:
            # ONE_WAY Mode (4 Phases)
            if phase == 0: allowed_groups = groups['north_inc']
            elif phase == 1: allowed_groups = groups['east_inc']
            elif phase == 2: allowed_groups = groups['south_inc']
            elif phase == 3: allowed_groups = groups['west_inc']

        # Check if agent is in an allowed group
        if current_node in allowed_groups:
            if state == "GREEN": return "GREEN"
            if state == "YELLOW": return "YELLOW"
        
        return "RED"

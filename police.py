# police.py
import networkx as nx
import random
import config as c

class PoliceUnit:
    def __init__(self, agent_id, city_graph):
        self.id = agent_id
        self.city = city_graph
        self.G = city_graph.G
        
        self.current_node = random.choice(list(self.G.nodes()))
        self.target_node = None
        self.destination_node = None
        self.path = []
        self.progress = 0.0
        
        self.state = "PATROL"  # PATROL, PURSUIT
        self.target_agent = None

    def decide_move(self, agents):
        """
        Police AI: Patrol -> Speed Trap -> Pursue.
        Target agents who are 'Speeding' (moving efficiently on empty roads).
        """
        if self.state == "PATROL":
            # 1. Scan visible edges for speeders
            violator = self._scan_for_speeders(agents)
            
            if violator:
                print(f"Police {self.id}: Spotted Speeder {violator.id}!")
                self.target_agent = violator
                self.state = "PURSUIT"
                # Predict where they are going (intercept logic)
                self.destination_node = violator.target_node if violator.target_node else violator.current_node
                self._recalculate_path()
                return

            # 2. Random Patrol if no target
            if not self.target_node:
                self.destination_node = random.choice(list(self.G.nodes()))
                self._recalculate_path()

        elif self.state == "PURSUIT":
            # If target finished trip or got caught by someone else, give up
            if not self.target_agent or self.target_agent.state == "IDLE":
                self.state = "PATROL"
                self.target_agent = None
                return

            # Update pursuit target (Police Radio: "Suspect heading to...")
            current_target_loc = self.target_agent.current_node
            if self.destination_node != current_target_loc:
                self.destination_node = current_target_loc
                self._recalculate_path()

    def _scan_for_speeders(self, agents):
        """
        Checks for agents on the same street or neighbors.
        Violation Trigger: moving on a low-load street (Speeding).
        """
        # Get edges connected to current node
        visible_edges = list(self.G.edges(self.current_node))
        
        for agent in agents:
            # Is the agent active?
            if agent.state in ["HUNTING", "DELIVERING"] and agent.target_node:
                
                # Check if agent is on a visible edge
                is_visible = False
                if agent.current_node == self.current_node: is_visible = True
                for u, v in visible_edges:
                    if agent.current_node == v: is_visible = True
                
                if is_visible:
                    # CHECK SPEED (The new logic)
                    # Get load of the street the agent is on
                    try:
                        load = self.G[agent.current_node][agent.target_node]['current_load']
                        # Speeding Logic: Low Load (0 or 1 cars) = High Speed = Risk of Ticket
                        if load < 2: 
                            # 5% chance to get busted per tick if speeding
                            if random.random() < 0.05: 
                                return agent
                    except KeyError:
                        pass # Edge case where agent just switched nodes
        return None

    def _recalculate_path(self):
        try:
            if not self.destination_node: return
            self.path = nx.shortest_path(self.G, self.current_node, self.destination_node, weight='weight')
            if len(self.path) > 1:
                self.target_node = self.path[1]
                self.progress = 0.0
            else:
                self.target_node = None
        except:
            self.target_node = None

    def move(self, dt):
        if not self.target_node: return

        # Police always move at max speed (sirens on)
        speed = c.RICKSHAW_SPEED_BASE * 1.8
        self.progress += speed * dt
        
        if self.progress >= 1.0:
            self.current_node = self.target_node
            self.progress = 0.0
            if len(self.path) > 2:
                self.path.pop(0)
                self.target_node = self.path[1]
            else:
                self.target_node = None

    def enforce_law(self):
        """Capture logic: Must overlap physically."""
        if self.state == "PURSUIT" and self.target_agent:
            if (self.current_node == self.target_agent.current_node and 
                self.target_node == self.target_agent.target_node):
                
                # Proximity check
                if abs(self.progress - self.target_agent.progress) < 0.15:
                    print(f"Police {self.id}: Ticketed Agent {self.target_agent.id}!")
                    
                    # Penalty: Lose money, but KEEP passenger (it's a speeding ticket, not an impound)
                    self.target_agent.money -= 20 
                    if self.target_agent.money < 0: self.target_agent.money = 0
                    
                    # Reset Police
                    self.state = "PATROL"
                    self.target_agent = None

    def get_position(self):
        # Interpolation for smooth rendering
        if not self.target_node: return self.city.G.nodes[self.current_node]['pos']
        start = self.city.G.nodes[self.current_node]['pos']
        end = self.city.G.nodes[self.target_node]['pos']
        lon = start[0] + (end[0] - start[0]) * self.progress
        lat = start[1] + (end[1] - start[1]) * self.progress
        return (lon, lat)
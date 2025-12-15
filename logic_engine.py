import random
import statistics  # Added for variance calculation
from city import CityGraph
from rickshaw import Rickshaw
from police import PoliceUnit
from passenger import Passenger
import config as c

class SimulationEngine:
    def __init__(self):
        self.city = CityGraph(150) # Using new irregular city
        self.rickshaws = [Rickshaw(i, self.city) for i in range(12)]
        self.police = [PoliceUnit(991, self.city), PoliceUnit(992, self.city)]
        self.passengers = []
        
        # Metrics State
        self.system_efficiency = 100.0
        self.system_entropy = 0.0
        
        # Calculate bounds for renderer
        all_lats = [d['pos'][1] for n, d in self.city.G.nodes(data=True)]
        all_lons = [d['pos'][0] for n, d in self.city.G.nodes(data=True)]
        self.bounds = (min(all_lats), max(all_lats), min(all_lons), max(all_lons))

    def update(self, dt):
        """Advances the simulation by one step."""
        
        # 1. Spawn Passengers
        if random.random() < c.SPAWN_RATE:
            nodes = list(self.city.G.nodes())
            p1, p2 = random.sample(nodes, 2)
            self.passengers.append(Passenger(p1, p2))

        # 2. Update Police
        for cop in self.police:
            cop.decide_move(self.rickshaws)
            cop.move(dt)
            cop.enforce_law()

        # 3. Update Rickshaws
        for agent in self.rickshaws:
            if not agent.passenger:
                agent.hunt(self.passengers)
            
            # Pickup Logic
            if agent.state == "HUNTING" and agent.current_node == agent.destination_node and not agent.target_node:
                picked_up = None
                for i, p in enumerate(self.passengers):
                    if p.node == agent.current_node:
                        picked_up = p
                        break
                
                if picked_up:
                    self.passengers.remove(picked_up)
                    agent.passenger = picked_up
                    agent.state = "DELIVERING"
                    agent.destination_node = picked_up.dest
                    agent._recalculate_path()
                else:
                    agent.state = "IDLE"
                    agent.destination_node = None

            # Dropoff Logic
            if agent.state == "DELIVERING" and agent.current_node == agent.destination_node and not agent.target_node:
                agent.passenger = None
                agent.state = "IDLE"
                agent.money += 10
                agent.destination_node = None
            
            agent.move(dt)
            
        # 4. Update System Metrics
        self.calculate_metrics()

    def calculate_metrics(self):
        """Calculates Homeostatic Health (Efficiency) and Entropy (Disorder)."""
        
        # --- Metric A: System Efficiency (Speed vs Potential) ---
        total_speed_ratio = 0
        active_agents = 0
        
        for agent in self.rickshaws:
            if agent.target_node:
                # Replicate the speed formula from rickshaw.py to measure current efficiency
                edge_data = self.city.G.get_edge_data(agent.current_node, agent.target_node)
                load = edge_data.get('current_load', 0)
                
                # Speed = Base / (1 + Load * Penalty)
                current_speed = c.RICKSHAW_SPEED_BASE / (1 + load * c.TRAFFIC_PENALTY)
                ratio = current_speed / c.RICKSHAW_SPEED_BASE
                
                total_speed_ratio += ratio
                active_agents += 1
        
        if active_agents > 0:
            self.system_efficiency = (total_speed_ratio / active_agents) * 100
        else:
            self.system_efficiency = 100.0 # Perfect efficiency if no one is moving

        # --- Metric B: System Entropy (Load Variance) ---
        loads = []
        for u, v, data in self.city.G.edges(data=True):
            loads.append(data.get('current_load', 0))
            
        if loads:
            # Variance measures how "clumped" the traffic is
            self.system_entropy = statistics.variance(loads) if len(loads) > 1 else 0.0
import random
from city import CityGraph
from rickshaw import Rickshaw
from police import PoliceUnit
from passenger import Passenger
import config as c

class SimulationEngine:
    def __init__(self):
        self.city = CityGraph(6, 6, 150)
        self.rickshaws = [Rickshaw(i, self.city) for i in range(12)]
        self.police = [PoliceUnit(991, self.city), PoliceUnit(992, self.city)]
        self.passengers = []
        
        # Calculate bounds once for the renderer to use
        all_lats = [d['pos'][1] for n, d in self.city.G.nodes(data=True)]
        all_lons = [d['pos'][0] for n, d in self.city.G.nodes(data=True)]
        self.bounds = (min(all_lats), max(all_lats), min(all_lons), max(all_lons))

    def update(self, dt):
        """Advances the simulation by one step."""
        
        # 1. Spawn Passengers (Regulated by Spawn Rate)
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
            # A. Hunting Logic
            if not agent.passenger:
                agent.hunt(self.passengers)
            
            # B. Pickup Logic (Atomic Removal)
            # Check if agent is at the pickup node AND has an assigned target
            if agent.state == "HUNTING" and agent.current_node == agent.destination_node and not agent.target_node:
                
                # Find the specific passenger waiting at this node
                picked_up = None
                for i, p in enumerate(self.passengers):
                    if p.node == agent.current_node:
                        picked_up = p
                        break # Found one!
                
                if picked_up:
                    # CRITICAL: Remove from world list immediately
                    self.passengers.remove(picked_up)
                    
                    # Assign to agent
                    agent.passenger = picked_up
                    agent.state = "DELIVERING"
                    agent.destination_node = picked_up.dest
                    agent._recalculate_path()
                    # print(f"Agent {agent.id} picked up passenger. World Count: {len(self.passengers)}")
                else:
                    # If we arrived but the passenger is gone (stolen by another agent), go back to Idle
                    agent.state = "IDLE"
                    agent.destination_node = None

            # C. Dropoff Logic
            if agent.state == "DELIVERING" and agent.current_node == agent.destination_node and not agent.target_node:
                agent.passenger = None
                agent.state = "IDLE"
                agent.money += 10 # Economy: Successful delivery
                agent.destination_node = None
            
            agent.move(dt)
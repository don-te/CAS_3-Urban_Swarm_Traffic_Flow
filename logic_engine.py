from city import CityGraph
from rickshaw import Rickshaw

class SimulationEngine:
    def __init__(self):
        # Initialize City (6x6 Grid)
        self.city = CityGraph(rows=6, cols=6, block_size_meters=150)
        
        # --- DEFINE DESTINATION ---
        # Top Left = Max Row (North), Min Col (West)
        top_left_node_id = f"{self.city.rows - 1}-0"

        # Initialize Agents with the common destination
        self.rickshaws = [Rickshaw(i, self.city, final_dest=top_left_node_id) for i in range(20)]
        
        # Calculate bounds for the visualizer
        all_lats = [d['pos'][1] for n, d in self.city.G.nodes(data=True)]
        all_lons = [d['pos'][0] for n, d in self.city.G.nodes(data=True)]
        self.bounds = (min(all_lats), max(all_lats), min(all_lons), max(all_lons))

    def update(self, dt):
        """Advances the simulation by one step."""
        for agent in self.rickshaws:
            agent.move(dt)

# city_graph.py
import networkx as nx
import math

class CityGraph:
    def __init__(self, rows=5, cols=5, block_size_meters=100):
        self.rows = rows
        self.cols = cols
        self.block_size = block_size_meters
        # Initialize a directed graph (streets can be one-way)
        self.G = nx.DiGraph()
        self.build_grid()

    def build_grid(self):
        """Generates a Manhattan-style grid of two-way streets."""
        # Base coordinates (Approx. Indiranagar, Bangalore)
        base_lat = 12.9716
        base_lon = 77.6412
        
        # Convert meters to approx lat/lon degrees
        lat_step = (self.block_size / 111320)
        lon_step = (self.block_size / (40075000 * math.cos(math.radians(base_lat)) / 360))

        # 1. Create Nodes (Intersections)
        for r in range(self.rows):
            for c in range(self.cols):
                node_id = f"{r}-{c}"
                # Calculate real-world coordinates
                lat = base_lat + (r * lat_step)
                lon = base_lon + (c * lon_step)
                
                self.G.add_node(node_id, pos=(lon, lat), type="intersection")

        # 2. Create Edges (Streets)
        # We add edges both ways to simulate two-way traffic
        for r in range(self.rows):
            for c in range(self.cols):
                current = f"{r}-{c}"
                
                # Connect East/West
                if c < self.cols - 1:
                    neighbor = f"{r}-{c+1}"
                    self._add_two_way_street(current, neighbor, "horizontal")
                
                # Connect North/South
                if r < self.rows - 1:
                    neighbor = f"{r+1}-{c}"
                    self._add_two_way_street(current, neighbor, "vertical")

    def _add_two_way_street(self, u, v, orientation):
        """Adds a street with capacity and load attributes."""
        # Cost is length (1.0 block). 
        # Capacity is max vehicles (e.g., 10 per block).
        self.G.add_edge(u, v, weight=1.0, capacity=10, current_load=0, type=orientation)
        self.G.add_edge(v, u, weight=1.0, capacity=10, current_load=0, type=orientation)

    def get_plotting_data(self):
        """Export graph data for PyDeck visualization."""
        lines = []
        nodes = []

        # Extract Lines (Streets)
        for u, v, data in self.G.edges(data=True):
            start_pos = self.G.nodes[u]['pos'] # (lon, lat)
            end_pos = self.G.nodes[v]['pos']
            
            # Color logic: Grey = Empty, Red = Jammed (Placeholder for now)
            color = [100, 100, 100] 
            
            lines.append({
                "source": start_pos,
                "target": end_pos,
                "color": color,
                "width": 10  # Width in meters
            })

        # Extract Nodes (Intersections)
        for n, data in self.G.nodes(data=True):
            nodes.append({
                "pos": data['pos'],
                "id": n
            })

        return lines, nodes
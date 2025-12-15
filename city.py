# city.py
import networkx as nx
import math

class CityGraph:
    def __init__(self, block_size_meters=100):
        # We no longer need rows/cols for the whole map, just for coordinate scaling
        self.block_size = block_size_meters
        self.G = nx.DiGraph()
        self.build_irregular_city()

    def build_irregular_city(self):
        """
        Creates a 'Board Game' style map with two distinct zones 
        connected by a single bottleneck bridge to force congestion.
        """
        base_lat = 12.9716
        base_lon = 77.6412
        
        # Helper to get coords
        def get_pos(r, c):
            lat_step = (self.block_size / 111320)
            lon_step = (self.block_size / (40075000 * math.cos(math.radians(base_lat)) / 360))
            return (base_lon + (c * lon_step), base_lat + (r * lat_step))

        # --- 1. Define Nodes (The "Board Game" Spots) ---
        
        # Zone A: Residential (West) - A dense 3x3 Cluster
        # Rows 0-2, Cols 0-2
        west_nodes = []
        for r in range(3):
            for c in range(3):
                node_id = f"res-{r}-{c}"
                self.G.add_node(node_id, pos=get_pos(r, c), type="residential")
                west_nodes.append(node_id)

        # Zone B: Commercial (East) - A dense 3x3 Cluster
        # Shifted to Cols 6-8 (leaving a gap of 3 blocks for the bridge)
        east_nodes = []
        for r in range(3):
            for c in range(6, 9):
                node_id = f"com-{r}-{c}"
                self.G.add_node(node_id, pos=get_pos(r, c), type="commercial")
                east_nodes.append(node_id)

        # --- 2. Define Edges (The Connections) ---

        # Internal Streets for West Zone (Residential)
        for r in range(3):
            for c in range(3):
                curr = f"res-{r}-{c}"
                # Connect East
                if c < 2: self._add_two_way_street(curr, f"res-{r}-{c+1}")
                # Connect North
                if r < 2: self._add_two_way_street(curr, f"res-{r+1}-{c}")

        # Internal Streets for East Zone (Commercial)
        for r in range(3):
            for c in range(6, 9):
                curr = f"com-{r}-{c}"
                # Connect East
                if c < 8: self._add_two_way_street(curr, f"com-{r}-{c+1}")
                # Connect North
                if r < 2: self._add_two_way_street(curr, f"com-{r+1}-{c}")

        # --- 3. The Bottleneck (The Bridge) ---
        # Connects the middle of West (res-1-2) to middle of East (com-1-6)
        bridge_start = "res-1-2"
        bridge_end = "com-1-6"
        
        # High capacity but it's the ONLY way across.
        # We give it a higher 'weight' (cost) naturally because it's long, 
        # but agents HAVE to take it.
        self.G.add_edge(bridge_start, bridge_end, weight=3.0, capacity=20, current_load=0, type="bridge")
        self.G.add_edge(bridge_end, bridge_start, weight=3.0, capacity=20, current_load=0, type="bridge")

    def _add_two_way_street(self, u, v, weight=1.0):
        """Adds a standard street."""
        self.G.add_edge(u, v, weight=weight, capacity=10, current_load=0, type="street")
        self.G.add_edge(v, u, weight=weight, capacity=10, current_load=0, type="street")

    def get_plotting_data(self):
        """Export graph data for PyDeck (unchanged logic, adaptable to any graph)."""
        lines = []
        nodes = []

        for u, v, data in self.G.edges(data=True):
            start_pos = self.G.nodes[u]['pos'] 
            end_pos = self.G.nodes[v]['pos']
            
            # Color bridges differently (Cyan)
            color = [100, 100, 100]
            if data.get('type') == 'bridge':
                color = [0, 200, 255] 
            
            lines.append({
                "source": start_pos,
                "target": end_pos,
                "color": color,
                "width": 10
            })

        for n, data in self.G.nodes(data=True):
            nodes.append({
                "pos": data['pos'],
                "id": n
            })

        return lines, nodes
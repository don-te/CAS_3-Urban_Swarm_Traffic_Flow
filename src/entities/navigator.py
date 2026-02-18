# src/entities/navigator.py
import networkx as nx
import itertools
import random

class Navigator:
    def __init__(self, city_graph):
        self.city = city_graph
        self.G = city_graph.G
        self.path = []
        self.chosen_path = []
        self.accumulated_path = []
        self.forced_path = None
        self.forbidden_paths = []
        
    def set_forced_path(self, path):
        self.forced_path = path

    def set_forbidden_paths(self, paths):
        self.forbidden_paths = paths if paths else []

    def find_path_to_node(self, start_node, target_node, blacklisted_edges=None):
        """
        Calculates a path from start_node to target_node using NetworkX.
        Respects forced_path, forbidden_paths, and temporary blacklists (for reversing).
        """
        # 1. OPTIMIZATION: If we have a forced path, use it.
        if self.forced_path and len(self.forced_path) > 0:
            # check if start node matches to be safe
            if self.forced_path[0] == start_node:
                self.path = list(self.forced_path)
                self.chosen_path = list(self.forced_path)
                # If we are loading a forced path, that BECOMES our accumulated history for this run
                if not self.accumulated_path:
                    self.accumulated_path = list(self.forced_path)
                return True
            else:
                pass
                # print(f"DEBUG: Navigator IGNORED forced path. Start {start_node} != Forced[0] {self.forced_path[0]}")

        
        # 2. Standard Pathfinding
        try:
            # Temporarily apply blacklist (for reversing/stuck logic)
            original_weights = {}
            if blacklisted_edges:
                for u, v in blacklisted_edges:
                    if self.G.has_edge(u, v):
                        original_weights[(u, v)] = self.G[u][v]['weight']
                        self.G[u][v]['weight'] = 999999.0

            found_path = None
            try:
                # Logic to find paths that are NOT in forbidden_paths
                # We use shortest_simple_paths to find alternatives
                path_generator = nx.shortest_simple_paths(self.G, start_node, target_node, weight='weight')
                
                # Try top 10 shortest paths
                for candidate_path in itertools.islice(path_generator, 10):
                    if candidate_path not in self.forbidden_paths:
                        found_path = candidate_path
                        # print(f"Found new path: {found_path}")
                        break
                
                # Fallback if all top 10 are forbidden
                if found_path is None:
                    found_path = nx.shortest_path(self.G, start_node, target_node, weight='weight')
                
                
                self.path = found_path
                self.chosen_path = list(found_path)
                
                # Append to accumulated history (avoiding duplicate join node)
                if len(self.accumulated_path) > 0 and len(found_path) > 0:
                    if self.accumulated_path[-1] == found_path[0]:
                        self.accumulated_path.extend(found_path[1:])
                    else:
                        self.accumulated_path.extend(found_path)
                else:
                    self.accumulated_path.extend(found_path)
                    
                
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                self.path = []
                # print("No Path Found")

            # Restore weights
            for (u, v), w in original_weights.items():
                self.G[u][v]['weight'] = w
                
            return len(self.path) > 0

        except Exception as e:
            print(f"Nav Error: {e}")
            self.path = []
            return False

    def get_next_node(self):
        if len(self.path) > 1:
            return self.path[1]
        return None

    def advance_path(self):
        if len(self.path) > 0:
            self.path.pop(0)

    def clear_path(self):
        self.path = []

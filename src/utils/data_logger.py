# src/utils/data_logger.py
import csv
import os

class DataLogger:
    def __init__(self, filename="simulation_data.csv"):
        self.filename = filename
        
        # Initialize file with Header Row if it doesn't exist
        if not os.path.exists(self.filename):
            try:
                with open(self.filename, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    header = [
                        "Run_ID", "Agent_Count", "Agent_ID", 
                        "Start_Lat", "Start_Lon", "End_Lat", "End_Lon", 
                        "Total_Time", "Collision_Count", "Path_Sequence"
                    ]
                    writer.writerow(header)
            except IOError as e:
                print(f"Error initializing log file: {e}")

    def get_node_id(self, node_str):
        """
        Converts string coordinates (e.g., "1-2") into a unique integer ID.
        Formula: ID = (Row * 6) + Column
        """
        try:
            # node_str is expected to be "row-col"
            parts = node_str.split('-')
            row = int(parts[0])
            col = int(parts[1])
            return (row * 6) + col
        except (ValueError, IndexError):
            # Fallback or error handling if format isn't "r-c"
            print(f"Warning: Invalid node format '{node_str}'")
            return -1

    def _get_path_sequence_ids(self, agent):
        """
        Convert the agent's chosen_path (list of strings) into a list of integers.
        Return it as a string representation of the list (e.g., "[0, 1, 7]").
        """
        if not agent.navigator.chosen_path:
            return "[]"
        
        path_ids = []
        for node in agent.navigator.chosen_path:
            nid = self.get_node_id(str(node))
            path_ids.append(nid)
            
        return str(path_ids)

    def log_run(self, pos_id, iter_id, agents, city, collision_count):
        """
        Logs data for all agents in the current run iteration.
        """
        agent_count = len(agents)
        run_id = f"{agent_count}_{pos_id}_{iter_id}"
        
        data_rows = []
        
        for agent in agents:
            # extract Start_Lat, Start_Lon
            # We assume agent.start_pos_coords was set in __init__
            slat, slon = 0.0, 0.0
            if hasattr(agent, 'start_pos_coords') and agent.start_pos_coords:
                slon, slat = agent.start_pos_coords
            
            # extract End_Lat, End_Lon
            elat, elon = 0.0, 0.0
            
            # Case A: NODE Destination
            if agent.dest_type == "NODE" and agent.final_dest_node in city.G.nodes:
                end_pos = city.G.nodes[agent.final_dest_node]['pos']
                elon, elat = end_pos
            
            # Case B: EDGE Destination
            elif agent.dest_type == "EDGE" and agent.dest_edge:
                u, v = agent.dest_edge
                if u in city.G.nodes and v in city.G.nodes:
                    pos_u = city.G.nodes[u]['pos']
                    pos_v = city.G.nodes[v]['pos']
                    prog = agent.dest_progress if agent.dest_progress else 0.5
                    
                    # Interpolate
                    elon = pos_u[0] + (pos_v[0] - pos_u[0]) * prog
                    elat = pos_u[1] + (pos_v[1] - pos_u[1]) * prog
            
            # Total Time
            total_time = round(agent.travel_time, 2)
            
            # Path Sequence
            path_seq = self._get_path_sequence_ids(agent)
            
            row = [
                run_id,
                agent_count,
                agent.id,
                format(slat, '.6f'),
                format(slon, '.6f'),
                format(elat, '.6f'),
                format(elon, '.6f'),
                total_time,
                collision_count,
                path_seq
            ]
            data_rows.append(row)
            
        try:
            # Check if we need to write headers (file doesn't exist or is empty)
            write_header = not os.path.exists(self.filename) or os.stat(self.filename).st_size == 0
            
            with open(self.filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                if write_header:
                    header = [
                        "Run_ID", "Agent_Count", "Agent_ID", 
                        "Start_Lat", "Start_Lon", "End_Lat", "End_Lon", 
                        "Total_Time", "Collision_Count", "Path_Sequence"
                    ]
                    writer.writerow(header)
                writer.writerows(data_rows)
            print(f"Logged Run {run_id} with {agent_count} agents.")
        except IOError as e:
            print(f"Error appending data to log: {e}")

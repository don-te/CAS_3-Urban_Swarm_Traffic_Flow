import csv
import os

class DataLogger:
    def __init__(self, filename="simulation_data.csv"):
        self.filename = filename
        # We do NOT initialize headers here anymore because the format is a repeated block structure.
        # However, if we want to clear the file on start, we can:
        if not os.path.exists(self.filename):
             with open(self.filename, mode='w', newline='') as file:
                 pass # Create empty file

    def log_complex_iteration(self, pos_id, iter_id, collision_count, agent_data_list):
        """
        Logs a structured block of data for one iteration.
        agent_data_list: List of dictionaries or tuples [{'id': 1, 'dist': x, 'time': t}, ...]
        """
        try:
            with open(self.filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                
                # 1. Header Row: Pos : X | Iter : Y | Collisions: Z
                header_row = [f"Pos : {pos_id}", f"Iter : {iter_id}", f"Collisions: {collision_count}"]
                writer.writerow(header_row)
                
                # 2. Column Names
                col_names = ["agent_id", "Distance", "Time"]
                writer.writerow(col_names)
                
                # 3. Agent Data Rows
                for agent_data in agent_data_list:
                    # Expecting tuple/list: [id, dist, time]
                    writer.writerow(agent_data)
                
                # 4. Blank Line Separator
                writer.writerow([])
                
            print(f"Logged Block: Pos {pos_id} | Iter {iter_id}")
        except Exception as e:
            print(f"Error logging data: {e}")

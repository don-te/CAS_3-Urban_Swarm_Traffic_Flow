import csv
import os

class DataLogger:
    def __init__(self, filename="simulation_data.csv"):
        self.filename = filename
        self._initialize_csv()

    def _initialize_csv(self):
        """Creates the CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.filename):
            try:
                with open(self.filename, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    # Columns requested: Iteration, Number of Agents, Lights, Path Const, Collision Count
                    writer.writerow(["Iteration", "Number of Agents", "Lights", "Path Const", "Collision Count"])
                print(f"Created new log file: {self.filename}")
            except Exception as e:
                print(f"Error creating CSV: {e}")

    def log_iteration(self, iteration, agent_count, light_mode, path_const, collisions):
        """Appends a row of data to the CSV."""
        try:
            # Format Path Const as Yes/No
            path_str = "Yes" if path_const else "No"
            
            with open(self.filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([iteration, agent_count, light_mode, path_str, collisions])
                
            print(f"Data Logged: Iteration {iteration} | Collisions: {collisions}")
        except Exception as e:
            print(f"Error logging data: {e}")

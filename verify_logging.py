import sys
import os
import time

# Add current directory to path so imports work
sys.path.append(os.getcwd())

from src.core.engine import SimulationEngine

def verify_logging():
    print("Initializing Engine (creates file)...")
    engine = SimulationEngine()
    
    # 1. Simulate Deletion
    if os.path.exists("simulation_data.csv"):
        print("Deleting simulation_data.csv to test regeneration...")
        os.remove("simulation_data.csv")
    
    print("Simulating 5 ticks...")
    for _ in range(5):
        engine.update(0.1)
        
    # Trigger log - This should regenerate headers
    print("Triggering Log (should regenerate headers)...")
    engine.trigger_next_iteration()
    
    # Check file
    if os.path.exists("simulation_data.csv"):
        print("\n--- simulation_data.csv Content ---")
        with open("simulation_data.csv", "r") as f:
            content = f.read()
            print(content)
            if "Run_ID,Agent_Count" in content:
                print("\nSUCCESS: Headers found!")
            else:
                print("\nFAILURE: Headers MISSING!")
    else:
        print("Error: simulation_data.csv was not created.")

if __name__ == "__main__":
    verify_logging()

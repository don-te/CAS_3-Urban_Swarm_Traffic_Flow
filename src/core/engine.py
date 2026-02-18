# src/core/engine.py
import src.config as c
from src.world.city import CityGraph
from src.utils.data_logger import DataLogger
from src.core.scenario import ScenarioManager
from src.core.collision import CollisionSystem

class SimulationEngine:
    def __init__(self):
        self.city = CityGraph(rows=6, cols=6, block_size_meters=150)
        
        # --- SUB-SYSTEMS ---
        self.collision_system = CollisionSystem()
        self.data_logger = DataLogger()
        self.scenario_manager = ScenarioManager(self.city)
        
        # --- STATE ---
        self.rickshaws = []
        self.collision_count = 0 
        self.collision_history = []
        
        # Counters
        self.current_iteration = 1
        self.current_position_id = 1 
        
        all_lats = [d['pos'][1] for n, d in self.city.G.nodes(data=True)]
        all_lons = [d['pos'][0] for n, d in self.city.G.nodes(data=True)]
        self.bounds = (min(all_lats), max(all_lats), min(all_lons), max(all_lons))

        # Initial Load
        self._reload_agents()

    def _reload_agents(self):
        """Replaces current agents with those loaded from scenario manager."""
        self.rickshaws = self.scenario_manager.load_scenario()

    def set_agent_count(self, target_count):
        self.rickshaws = self.scenario_manager.set_agent_count(target_count, self.rickshaws)

    def reset_simulation(self):
        self.collision_count = 0
        self.collision_history = []
        self.current_iteration = 1
        self.current_position_id = 1 
        self.scenario_manager.path_history = {} 
        print("--- SIMULATION RESET ---")
        self._reload_agents()

    def update_positions(self):
        print(f"--- UPDATING POSITIONS (Starting new Trip) ---")
        self.current_position_id += 1 
        self.current_iteration = 1   
        
        self.scenario_manager.prepare_new_trip()
        self.collision_count = 0
        self._reload_agents()

    def trigger_next_iteration(self):
        # 1. Archive Stats
        record = f"Iter {self.current_iteration} Collisions: {self.collision_count}"
        self.collision_history.append(record)
        
        # Log Stats
        self.data_logger.log_run(
            pos_id=self.current_position_id,
            iter_id=self.current_iteration,
            agents=self.rickshaws,
            city=self.city,
            collision_count=self.collision_count
        )
        
        print(f"--- NEXT ITERATION (Evolutionary Pathing) ---")
        
        # 2. EVOLUTIONARY LOGIC (Delegated to ScenarioManager)
        self.scenario_manager.update_configs_after_iteration(self.rickshaws)
        
        # 3. Reload
        self.collision_count = 0
        self.current_iteration += 1
        self._reload_agents()

    def update(self, dt):
        for agent in self.rickshaws:
            agent.move(dt, self.rickshaws)
            
        new_collisions = self.collision_system.check_collisions(self.rickshaws)
        self.collision_count += new_collisions

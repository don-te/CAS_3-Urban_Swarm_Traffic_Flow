import pygame
import sys
import argparse
import src.config as c
from src.core.engine import SimulationEngine
from src.ui.visualizer import Visualizer

# --- AUTOMATION DRIVER ---
class AutomationDriver:
    def __init__(self, engine, iterations, pos_updates, n_start, n_end, step):
        self.engine = engine
        
        # Parameters
        self.target_iterations = iterations
        self.target_pos_updates = pos_updates
        self.n_start = n_start
        self.n_end = n_end
        self.step = step
        
        # State
        self.current_n = n_start
        self.pos_count = 0  # How many position updates done for this N
        self.iter_count = 0 # How many iterations done for this Pos
        
        # Initialization
        print(f"[AUTO] Starting with {self.current_n} agents.")
        self.engine.set_agent_count(self.current_n)
        self.engine.current_iteration = 1
        self.engine.current_position_id = 1
        
    def update(self):
        """
        Called every frame to check status and progress automation.
        """
        all_arrived = True
        for agent in self.engine.rickshaws:
            if not agent.has_arrived:
                all_arrived = False
                break
        
        if all_arrived:
            self._advance_step()

    def _advance_step(self):
        self.iter_count += 1
        print(f"[AUTO] Completed Iteration {self.iter_count}/{self.target_iterations} for Pos {self.pos_count+1}/{self.target_pos_updates} (Agents: {self.current_n})")

        if self.iter_count < self.target_iterations:
            self.engine.trigger_next_iteration()
        else:
            # --- FIX: Log the final iteration before moving on ---
            self.engine.finalize_iteration_stats()
            
            self.iter_count = 0 
            self.pos_count += 1
            
            if self.pos_count < self.target_pos_updates:
                print(f"[AUTO] Updating Positions ({self.pos_count}/{self.target_pos_updates})")
                self.engine.update_positions()
            else:
                self.pos_count = 0
                self.current_n += self.step
                
                if self.current_n <= self.n_end:
                    print(f"[AUTO] Increasing Agents to {self.current_n}")
                    self.engine.set_agent_count(self.current_n)
                    self.engine.update_positions() 
                else:
                    print("[AUTO] AUTOMATION SEQUENCE COMPLETE")
                    pygame.quit()
                    sys.exit()

# --- MAIN LOOP ---
def run_simulation(args):
    pygame.init()
    engine = SimulationEngine()
    vis = Visualizer(engine.bounds)
    clock = pygame.time.Clock()
    
    driver = AutomationDriver(
        engine, 
        args.iterations, 
        args.pos_updates, 
        args.n_start, 
        args.n_end, 
        args.step
    )
    
    running = True
    while running:
        raw_dt = clock.tick(c.FPS) / 1000.0
        FIXED_STEP = 1.0 / c.FPS
        
        if vis.is_paused:
            dt = 0
        else:
            dt = FIXED_STEP * vis.sim_speed
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                vis.handle_resize(event)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if event.key == pygame.K_SPACE: vis.toggle_pause()
            
            # --- CRITICAL: Handle UI Buttons ---
            # Even if automation is driving, we allow pausing/resetting or at least
            # processing the clicks so the window doesn't feel frozen.
            # We ignore the return values (next_iter, etc) because Driver controls that.
            # But we MUST call this so buttons update their hover state and don't block.
            vis.handle_ui_events(event)
        
        if dt > 0:
            driver.update()
            engine.update(dt)
            
        vis.draw(engine.city, engine.rickshaws, engine.collision_count, engine.collision_history)
        
        # Ensure the display updates! 
        # vis.draw() calls flip() at the end, so that is covered in Visualizer.
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Traffic Simulation Automation")
    parser.add_argument("--iterations", type=int, default=5, help="Iterations per position")
    parser.add_argument("--pos_updates", type=int, default=2, help="Position updates per agent count")
    parser.add_argument("--n_start", type=int, default=1, help="Start agent count")
    parser.add_argument("--n_end", type=int, default=10, help="End agent count")
    parser.add_argument("--step", type=int, default=2, help="Step size for agent count")
    
    args = parser.parse_args()
    run_simulation(args)

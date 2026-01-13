# main.py (Full Update)
import pygame
import sys
import config as c
from logic_engine import SimulationEngine
from visualizer import Visualizer

def main():
    engine = SimulationEngine()
    vis = Visualizer(engine.bounds)
    clock = pygame.time.Clock()
    
    running = True
    while running:
        raw_dt = clock.tick(c.FPS) / 1000.0
        
        if vis.is_paused:
            dt = 0
        else:
            dt = raw_dt * vis.sim_speed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.VIDEORESIZE:
                vis.handle_resize(event)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    vis.toggle_pause()

            # --- UPDATED UNPACKING ---
            new_agent_count, next_iter, toggle_lights, reset_triggered = vis.handle_ui_events(event)
            
            if reset_triggered:
                engine.reset_simulation()
            
            # Only set agent count if NOT resetting (prevents conflict)
            elif new_agent_count is not None:
                engine.set_agent_count(new_agent_count)
            
            if next_iter:
                engine.trigger_next_iteration()

            if toggle_lights:
                engine.toggle_traffic_lights()
        
        if dt > 0:
            engine.update(dt)
            
        vis.draw(engine.city, engine.rickshaws, engine.collision_count, engine.collision_history, engine.traffic_manager)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

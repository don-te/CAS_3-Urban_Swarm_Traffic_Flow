# main.py
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

            # --- UI EVENT UNPACKING ---
            new_agent_count, next_iter, toggle_lights, reset_triggered = vis.handle_ui_events(event)
            
            if reset_triggered:
                engine.reset_simulation()
            elif new_agent_count is not None:
                engine.set_agent_count(new_agent_count)
            
            if next_iter:
                # Pass the Path Constant flag from Visualizer to Engine
                engine.trigger_next_iteration(path_constant=vis.path_constant)

            if toggle_lights:
                engine.toggle_traffic_lights()
        
        if dt > 0:
            engine.update(dt)
            
        vis.draw(engine.city, engine.rickshaws, engine.collision_count, engine.collision_history, engine.traffic_manager)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

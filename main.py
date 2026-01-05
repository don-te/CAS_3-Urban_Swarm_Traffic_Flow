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

            new_agent_count = vis.handle_ui_events(event)
            if new_agent_count is not None:
                engine.set_agent_count(new_agent_count)
        
        if dt > 0:
            engine.update(dt)
            
        # --- PASS COLLISION COUNT HERE ---
        vis.draw(engine.city, engine.rickshaws, engine.collision_count)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

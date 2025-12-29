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
        dt = clock.tick(c.FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.VIDEORESIZE:
                vis.handle_resize(event)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

            # --- HANDLE SLIDER INPUT ---
            new_agent_count = vis.handle_ui_events(event)
            if new_agent_count is not None:
                # If the slider moved, update the engine
                engine.set_agent_count(new_agent_count)
        
        engine.update(dt)
        vis.draw(engine.city, engine.rickshaws)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

import pygame
import sys
import config as c
from logic_engine import SimulationEngine
from visualizer import Visualizer

def main():
    # 1. Setup Logic
    engine = SimulationEngine()
    
    # 2. Setup Display
    vis = Visualizer(engine.bounds)
    clock = pygame.time.Clock()
    
    running = True
    while running:
        dt = clock.tick(c.FPS) / 1000.0
        
        # Input Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle Window Resizing (Maximize/Drag)
            elif event.type == pygame.VIDEORESIZE:
                vis.handle_resize(event)

            # Optional: ESC to quit
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Update Logic
        engine.update(dt)
        
        # Draw Frame
        vis.draw(engine.city, engine.rickshaws)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

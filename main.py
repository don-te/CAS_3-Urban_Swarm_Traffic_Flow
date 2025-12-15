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
        
        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Update Logic
        engine.update(dt)

      
        # Draw Frame
        metrics = {
            "efficiency": engine.system_efficiency,
            "entropy": engine.system_entropy
        }
        vis.draw(engine.city, engine.rickshaws, engine.police, engine.passengers, metrics)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
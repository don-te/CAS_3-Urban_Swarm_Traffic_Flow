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
        # 1. Base Delta Time (Seconds)
        raw_dt = clock.tick(c.FPS) / 1000.0
        
        # 2. Apply Speed Multiplier from UI
        #    If paused, time does not pass for the engine.
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
                # Optional: Spacebar shortcut for Pause
                if event.key == pygame.K_SPACE:
                    vis.toggle_pause()

            # --- HANDLE UI INPUT ---
            # Returns new agent count if slider moved, else None
            new_agent_count = vis.handle_ui_events(event)
            
            if new_agent_count is not None:
                engine.set_agent_count(new_agent_count)
        
        # 3. Update Engine only if time is passing
        if dt > 0:
            engine.update(dt)
            
        vis.draw(engine.city, engine.rickshaws)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

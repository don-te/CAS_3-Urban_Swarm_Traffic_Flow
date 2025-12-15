import pygame
import config as c
from utils import map_coords_to_screen, draw_triangle, get_angle

class Visualizer:
    def __init__(self, bounds):
        pygame.init()
        self.screen = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        pygame.display.set_caption("Urban Swarm: Homeostasis Monitor")
        self.bounds = bounds 
        
        # Font for UI
        self.font = pygame.font.SysFont("monospace", 16, bold=True)

    def draw(self, city, rickshaws, police, passengers, metrics):
        """Now accepts a 'metrics' dict or object to display stats."""
        self.screen.fill((40, 40, 40)) 
        
        min_lat, max_lat, min_lon, max_lon = self.bounds

        # 1. Draw Roads
        for u, v, data in city.G.edges(data=True):
            load = data.get('current_load', 0)
            u_pos = city.G.nodes[u]['pos']
            v_pos = city.G.nodes[v]['pos']
            start = map_coords_to_screen(u_pos[1], u_pos[0], min_lat, max_lat, min_lon, max_lon)
            end = map_coords_to_screen(v_pos[1], v_pos[0], min_lat, max_lat, min_lon, max_lon)
            
            # Draw Bridge Distinctly
            is_bridge = data.get('type') == 'bridge'
            width = 12 if is_bridge else 6
            color = (60, 100, 120) if is_bridge else (70, 70, 70)
            
            if load > 2: color = c.COLOR_JAM

            pygame.draw.line(self.screen, color, start, end, width)

        # 2. Draw Intersections
        for n, data in city.G.nodes(data=True):
            pos = data['pos']
            s_pos = map_coords_to_screen(pos[1], pos[0], min_lat, max_lat, min_lon, max_lon)
            color = (70, 70, 70)
            size = 5
            if data.get('type') in ['residential', 'commercial']:
                color = (100, 100, 100)
                size = 8
            pygame.draw.circle(self.screen, color, s_pos, size)

        # 3. Draw Passengers
        for p in passengers:
            pos = city.G.nodes[p.node]['pos']
            s_pos = map_coords_to_screen(pos[1], pos[0], min_lat, max_lat, min_lon, max_lon)
            pygame.draw.circle(self.screen, c.COLOR_PASSENGER, s_pos, 6)

        # 4. Draw Rickshaws
        for agent in rickshaws:
            pos = agent.get_position()
            s_pos = map_coords_to_screen(pos[1], pos[0], min_lat, max_lat, min_lon, max_lon)
            angle = 0
            if agent.target_node:
                t_pos = city.G.nodes[agent.target_node]['pos']
                t_screen = map_coords_to_screen(t_pos[1], t_pos[0], min_lat, max_lat, min_lon, max_lon)
                angle = get_angle(s_pos, t_screen)
            
            color = c.COLOR_RICKSHAW_FULL if agent.passenger else c.COLOR_RICKSHAW_EMPTY
            draw_triangle(self.screen, color, s_pos, angle, 12)

        # 5. Draw Police
        for cop in police:
            pos = cop.get_position()
            s_pos = map_coords_to_screen(pos[1], pos[0], min_lat, max_lat, min_lon, max_lon)
            angle = 0
            if cop.target_node:
                t_pos = city.G.nodes[cop.target_node]['pos']
                t_screen = map_coords_to_screen(t_pos[1], t_pos[0], min_lat, max_lat, min_lon, max_lon)
                angle = get_angle(s_pos, t_screen)
            
            draw_triangle(self.screen, (255, 255, 255), s_pos, angle, 14)

        # 6. Draw HUD (Metrics)
        self._draw_hud(metrics)
        
        pygame.display.flip()

    def _draw_hud(self, metrics):
        """Displays System Efficiency and Entropy."""
        eff = metrics['efficiency']
        ent = metrics['entropy']
        
        # Color Logic
        eff_color = (0, 255, 0) if eff > 70 else (255, 165, 0) # Green -> Orange
        if eff < 40: eff_color = (255, 0, 0) # Red
        
        # Render Text
        t_eff = self.font.render(f"SYSTEM HEALTH: {eff:.1f}%", True, eff_color)
        t_ent = self.font.render(f"ENTROPY (VAR): {ent:.2f}", True, (200, 200, 200))
        t_note = self.font.render(f"Bottleneck Status: {'CRITICAL' if ent > 1.5 else 'STABLE'}", True, (200, 200, 200))

        # Blit
        self.screen.blit(t_eff, (20, 20))
        self.screen.blit(t_ent, (20, 45))
        self.screen.blit(t_note, (20, 70))
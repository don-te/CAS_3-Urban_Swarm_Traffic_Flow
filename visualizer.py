import pygame
import math
import config as c
from utils import map_coords_to_screen, draw_triangle, get_angle

class Visualizer:
    def __init__(self, bounds):
        pygame.init()
        # 1. Create the Main Window (Resizable)
        self.screen = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Urban Swarm: Fixed Aspect Ratio")
        
        # 2. Create the Fixed Simulation Surface (800x800)
        # We will draw the map on this, then paste it onto the main screen
        self.sim_surface = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        
        self.bounds = bounds # (min_lat, max_lat, min_lon, max_lon)

    def handle_resize(self, event):
        """Update the main window size when the user resizes/maximizes."""
        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

    def _get_perp_offset(self, start, end, magnitude):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0: return (0, 0)
        ux, uy = dx / length, dy / length
        return (uy * magnitude, -ux * magnitude)

    def draw(self, city, rickshaws):
        # A. Clear the Main Window (The blank space)
        # You can change this color to Black (0,0,0) or Dark Grey if you prefer
        self.screen.fill((20, 20, 20)) 

        # B. Clear the Simulation Surface
        self.sim_surface.fill(c.BG_COLOR)

        min_lat, max_lat, min_lon, max_lon = self.bounds

        # Helper to map coords to the FIXED sim_surface dimensions
        # Note: We pass fixed SCREEN_WIDTH/HEIGHT, not the window size
        def to_screen(lat, lon):
            return map_coords_to_screen(
                lat, lon, min_lat, max_lat, min_lon, max_lon, 
                c.SCREEN_WIDTH, c.SCREEN_HEIGHT
            )

        # --- LAYER 1: ROADS (Draw on sim_surface) ---
        for u, v, data in city.G.edges(data=True):
            u_pos = city.G.nodes[u]['pos']
            v_pos = city.G.nodes[v]['pos']
            s = to_screen(u_pos[1], u_pos[0])
            e = to_screen(v_pos[1], v_pos[0])
            
            pygame.draw.line(self.sim_surface, c.COLOR_ASPHALT, s, e, c.ROAD_WIDTH)
            pygame.draw.line(self.sim_surface, c.COLOR_DIVIDER, s, e, 1)

        # --- LAYER 2: LANES ---
        for u, v, data in city.G.edges(data=True):
            load = data.get('current_load', 0)
            u_pos = city.G.nodes[u]['pos']
            v_pos = city.G.nodes[v]['pos']
            s = to_screen(u_pos[1], u_pos[0])
            e = to_screen(v_pos[1], v_pos[0])
            
            ox, oy = self._get_perp_offset(s, e, c.LANE_OFFSET)
            start_off = (s[0] + ox, s[1] + oy)
            end_off = (e[0] + ox, e[1] + oy)
            
            color = (80, 80, 80)
            width = 2
            if load > 0:
                r = min(100 + (load * 40), 255)
                color = (r, 50, 50)
                width = 3
            pygame.draw.line(self.sim_surface, color, start_off, end_off, width)

        # --- LAYER 3: INTERSECTIONS ---
        for n, data in city.G.nodes(data=True):
            pos = data['pos']
            s_pos = to_screen(pos[1], pos[0])
            pygame.draw.circle(self.sim_surface, c.COLOR_ASPHALT, s_pos, int(c.ROAD_WIDTH/2))
            pygame.draw.circle(self.sim_surface, (80, 80, 80), s_pos, 4)

        # --- LAYER 4: AGENTS ---
        for agent in rickshaws:
            pos = agent.get_position()
            s_pos = to_screen(pos[1], pos[0])
            
            angle = 0
            offset_pos = s_pos
            if agent.target_node:
                t_pos = city.G.nodes[agent.target_node]['pos']
                t_screen = to_screen(t_pos[1], t_pos[0])
                angle = get_angle(s_pos, t_screen)
                ox, oy = self._get_perp_offset(s_pos, t_screen, c.LANE_OFFSET)
                offset_pos = (s_pos[0] + ox, s_pos[1] + oy)

            draw_triangle(self.sim_surface, c.COLOR_RICKSHAW_EMPTY, offset_pos, angle, 12)

        # C. BLIT TO MAIN SCREEN (Centering Logic)
        # Get current window size
        window_w, window_h = self.screen.get_size()
        
        # Calculate position to center the sim_surface
        x_pos = (window_w - c.SCREEN_WIDTH) // 2
        y_pos = (window_h - c.SCREEN_HEIGHT) // 2
        
        self.screen.blit(self.sim_surface, (x_pos, y_pos))

        pygame.display.flip()

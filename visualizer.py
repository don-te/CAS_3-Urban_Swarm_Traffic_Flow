import pygame
import math
import config as c
from utils import map_coords_to_screen, draw_triangle, get_angle
from ui import Slider

class Visualizer:
    def __init__(self, bounds):
        pygame.init()
        self.screen = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Urban Swarm")
        
        self.sim_surface = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        self.bounds = bounds
        
        # --- INIT SLIDER ---
        self.agent_slider = Slider(
            x=50, y=c.SCREEN_HEIGHT - 40, w=200, h=10,
            min_val=c.MIN_AGENTS, max_val=c.MAX_AGENTS, start_val=c.AGENT_COUNT,
            label="Agent Count"
        )

    def handle_resize(self, event):
        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

    def handle_ui_events(self, event):
        return self.agent_slider.handle_event(event)

    def _get_perp_offset(self, start, end, magnitude):
        """Calculates a left-hand perpendicular offset vector."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0: return (0, 0)
        ux, uy = dx / length, dy / length
        # Returns vector rotated 90 degrees to simulate Left Hand Traffic
        return (uy * magnitude, -ux * magnitude)

    def draw(self, city, rickshaws):
        self.screen.fill((20, 20, 20)) 
        self.sim_surface.fill(c.BG_COLOR)

        min_lat, max_lat, min_lon, max_lon = self.bounds
        def to_screen(lat, lon):
            return map_coords_to_screen(
                lat, lon, min_lat, max_lat, min_lon, max_lon, 
                c.SCREEN_WIDTH, c.SCREEN_HEIGHT
            )

        # --- LAYER 1: ROADS (Asphalt + Divider) ---
        for u, v, data in city.G.edges(data=True):
            u_pos = city.G.nodes[u]['pos']
            v_pos = city.G.nodes[v]['pos']
            s = to_screen(u_pos[1], u_pos[0])
            e = to_screen(v_pos[1], v_pos[0])
            pygame.draw.line(self.sim_surface, c.COLOR_ASPHALT, s, e, c.ROAD_WIDTH)
            pygame.draw.line(self.sim_surface, c.COLOR_DIVIDER, s, e, 1)

        # --- LAYER 2: LANE MARKINGS ---
        for u, v, data in city.G.edges(data=True):
            load = data.get('current_load', 0)
            u_pos = city.G.nodes[u]['pos']
            v_pos = city.G.nodes[v]['pos']
            s = to_screen(u_pos[1], u_pos[0])
            e = to_screen(v_pos[1], v_pos[0])
            
            # Apply offset to draw the visual lane line
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
            # 1. Get Base Screen Coordinates
            start_node_pos = city.G.nodes[agent.current_node]['pos']
            s_start = to_screen(start_node_pos[1], start_node_pos[0])

            final_screen_pos = s_start
            angle = 0

            if agent.target_node:
                end_node_pos = city.G.nodes[agent.target_node]['pos']
                s_end = to_screen(end_node_pos[1], end_node_pos[0])

                # 2. Interpolate Position along the CENTER line
                cx = s_start[0] + (s_end[0] - s_start[0]) * agent.progress
                cy = s_start[1] + (s_end[1] - s_start[1]) * agent.progress

                # 3. Apply LANE OFFSET (Pixel Space)
                # We reuse the exact same math used for drawing the lane lines
                ox, oy = self._get_perp_offset(s_start, s_end, c.LANE_OFFSET)
                
                final_screen_pos = (cx + ox, cy + oy)
                
                # 4. Calculate Visual Angle
                angle = agent.get_visual_angle(s_start, s_end)
            
            # Determine Color
            agent_color = c.COLOR_RICKSHAW_EMPTY
            if agent.is_crashed:
                agent_color = c.COLOR_JAM
            elif agent.reversing:
                agent_color = (255, 165, 0) # Orange
            
            draw_triangle(self.sim_surface, agent_color, final_screen_pos, angle, 12)

        # Blit Sim Surface
        window_w, window_h = self.screen.get_size()
        x_pos = (window_w - c.SCREEN_WIDTH) // 2
        y_pos = (window_h - c.SCREEN_HEIGHT) // 2
        self.screen.blit(self.sim_surface, (x_pos, y_pos))

        # --- DRAW UI ON TOP ---
        self.agent_slider.draw(self.screen)

        pygame.display.flip()


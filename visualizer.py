import pygame
import config as c
from utils import map_coords_to_screen, draw_triangle, get_angle

class Visualizer:
    def __init__(self, bounds):
        pygame.init()
        self.screen = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        pygame.display.set_caption("Urban Swarm: Modular")
        self.bounds = bounds # (min_lat, max_lat, min_lon, max_lon)

    def draw(self, city, rickshaws, police, passengers):
        self.screen.fill((40, 40, 40)) # Background
        
        min_lat, max_lat, min_lon, max_lon = self.bounds

        # 1. Draw Roads
        for u, v, data in city.G.edges(data=True):
            load = data.get('current_load', 0)
            u_pos = city.G.nodes[u]['pos']
            v_pos = city.G.nodes[v]['pos']
            start = map_coords_to_screen(u_pos[1], u_pos[0], min_lat, max_lat, min_lon, max_lon)
            end = map_coords_to_screen(v_pos[1], v_pos[0], min_lat, max_lat, min_lon, max_lon)
            
            # Road Base
            pygame.draw.line(self.screen, (70, 70, 70), start, end, 30)
            # Center Line
            pygame.draw.line(self.screen, (100, 100, 100), start, end, 2)
            # Jam Tint
            if load > 2:
                pygame.draw.line(self.screen, c.COLOR_JAM, start, end, 10)

        # 2. Draw Intersections
        for n, data in city.G.nodes(data=True):
            pos = data['pos']
            s_pos = map_coords_to_screen(pos[1], pos[0], min_lat, max_lat, min_lon, max_lon)
            pygame.draw.circle(self.screen, (70, 70, 70), s_pos, 15)

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
            
            color = (255, 255, 255)
            if cop.state == "PURSUIT" and (pygame.time.get_ticks() // 200) % 2 == 0:
                color = (255, 0, 0)
            draw_triangle(self.screen, color, s_pos, angle, 14)

        pygame.display.flip()
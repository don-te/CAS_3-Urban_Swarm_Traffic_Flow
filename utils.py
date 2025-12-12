# utils.py
import math
import pygame
import config as c

def map_coords_to_screen(lat, lon, min_lat, max_lat, min_lon, max_lon):
    """Converts GPS coordinates to Screen X,Y pixels."""
    if max_lon == min_lon: max_lon += 0.0001
    if max_lat == min_lat: max_lat += 0.0001
    x_pct = (lon - min_lon) / (max_lon - min_lon)
    y_pct = (lat - min_lat) / (max_lat - min_lat)
    screen_x = 50 + x_pct * (c.SCREEN_WIDTH - 100)
    screen_y = c.SCREEN_HEIGHT - (50 + y_pct * (c.SCREEN_HEIGHT - 100))
    return int(screen_x), int(screen_y)

def get_angle(start, end):
    dx = end[0] - start[0]
    dy = -(end[1] - start[1])
    return math.atan2(dy, dx)

def draw_triangle(surface, color, pos, angle, size=10):
    p1 = (pos[0] + size * math.cos(angle), pos[1] - size * math.sin(angle))
    p2 = (pos[0] + size*0.7 * math.cos(angle + 2.5), pos[1] - size*0.7 * math.sin(angle + 2.5))
    p3 = (pos[0] + size*0.7 * math.cos(angle - 2.5), pos[1] - size*0.7 * math.sin(angle - 2.5))
    pygame.draw.polygon(surface, color, [p1, p2, p3])
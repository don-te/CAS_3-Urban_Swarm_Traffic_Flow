# src/ui/drawing.py
import math
import pygame

def draw_triangle(surface, color, pos, angle, size=10):
    """Draws a rotated triangle at the given position."""
    p1 = (pos[0] + size * math.cos(angle), pos[1] - size * math.sin(angle))
    p2 = (pos[0] + size*0.7 * math.cos(angle + 2.5), pos[1] - size*0.7 * math.sin(angle + 2.5))
    p3 = (pos[0] + size*0.7 * math.cos(angle - 2.5), pos[1] - size*0.7 * math.sin(angle - 2.5))
    pygame.draw.polygon(surface, color, [p1, p2, p3])

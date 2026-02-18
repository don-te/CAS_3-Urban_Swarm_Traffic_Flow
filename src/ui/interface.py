# src/ui/interface.py
import pygame

class Button:
    def __init__(self, x, y, w, h, text, callback, color=(100, 100, 100), hover_color=(150, 150, 150)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.text_surf = self.font.render(text, True, (255, 255, 255))
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            self.current_color = self.hover_color if self.is_hovered else self.color
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.callback()
                return True
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, self.current_color, self.rect, border_radius=5)
        self.text_surf = self.font.render(self.text, True, (255, 255, 255))
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)
        surface.blit(self.text_surf, self.text_rect)


class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, start_val, label, is_float=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.label = label
        self.is_float = is_float
        
        self.handle_radius = 10
        self.dragging = False
        self.font = pygame.font.SysFont("Arial", 16)
        
    def get_handle_pos(self):
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        x = self.rect.x + ratio * self.rect.w
        return (int(x), self.rect.centery)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        hx, hy = self.get_handle_pos()
        handle_rect = pygame.Rect(hx - self.handle_radius, hy - self.handle_radius, self.handle_radius*2, self.handle_radius*2)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
             if handle_rect.collidepoint(mouse_pos) or self.rect.collidepoint(mouse_pos):
                 self.dragging = True
                 
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            
        if self.dragging and event.type == pygame.MOUSEMOTION:
            rel_x = mouse_pos[0] - self.rect.x
            ratio = max(0, min(1, rel_x / self.rect.w))
            new_val = self.min_val + ratio * (self.max_val - self.min_val)
            
            if not self.is_float:
                new_val = int(round(new_val))
            else:
                new_val = round(new_val, 2)
            
            self.val = new_val
            return self.val
        
        return None

    def draw(self, surface):
        # Label
        label_surf = self.font.render(f"{self.label}: {self.val}", True, (200, 200, 200))
        surface.blit(label_surf, (self.rect.x, self.rect.y - 25))
        
        # Track
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=2)
        
        # Handle
        hx, hy = self.get_handle_pos()
        pygame.draw.circle(surface, (200, 200, 200), (hx, hy), self.handle_radius)

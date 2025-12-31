import pygame

class Button:
    def __init__(self, x, y, w, h, text, callback, color=(100, 100, 100), hover_color=(150, 150, 150)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback  # Function to call when clicked
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.SysFont("Arial", 20, bold=True)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:
                self.callback()  # Trigger the action
                return True
        return False

    def draw(self, surface):
        # Draw Button Background
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, width=2, border_radius=8)
        
        # Draw Text
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, start_val, label="Value", is_float=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.label = label
        self.dragging = False
        self.is_float = is_float
        
        self.font = pygame.font.SysFont("Arial", 16)

    def handle_event(self, event):
        """Returns the new value if changed, else None."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                return self._update_val(event.pos[0])
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                return self._update_val(event.pos[0])
        
        return None

    def _update_val(self, mouse_x):
        rel_x = max(self.rect.x, min(mouse_x, self.rect.right))
        pct = (rel_x - self.rect.x) / self.rect.width
        
        raw_val = self.min_val + (self.max_val - self.min_val) * pct
        
        if self.is_float:
            self.val = round(raw_val, 1) # Keep 1 decimal place
        else:
            self.val = int(raw_val)
            
        return self.val

    def draw(self, surface):
        label_text = f"{self.label}: {self.val}"
        if self.is_float:
            label_text += "x"
            
        label_surf = self.font.render(label_text, True, (200, 200, 200))
        surface.blit(label_surf, (self.rect.x, self.rect.y - 20))
        
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=5)
        
        pct = (self.val - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.rect.x + (pct * self.rect.width)
        handle_rect = pygame.Rect(handle_x - 5, self.rect.y - 2, 10, self.rect.height + 4)
        
        pygame.draw.rect(surface, (0, 255, 128), handle_rect, border_radius=5)

import pygame

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, start_val, label="Value"):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.label = label
        self.dragging = False
        
        # Font for text
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
        # Clamp mouse position to slider width
        rel_x = max(self.rect.x, min(mouse_x, self.rect.right))
        
        # Calculate percentage (0.0 to 1.0)
        pct = (rel_x - self.rect.x) / self.rect.width
        
        # Map to value range
        self.val = int(self.min_val + (self.max_val - self.min_val) * pct)
        return self.val

    def draw(self, surface):
        # 1. Draw Label
        label_surf = self.font.render(f"{self.label}: {self.val}", True, (200, 200, 200))
        surface.blit(label_surf, (self.rect.x, self.rect.y - 20))
        
        # 2. Draw Track (Background)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, border_radius=5)
        
        # 3. Draw Handle
        # Calculate handle position
        pct = (self.val - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.rect.x + (pct * self.rect.width)
        handle_rect = pygame.Rect(handle_x - 5, self.rect.y - 2, 10, self.rect.height + 4)
        
        pygame.draw.rect(surface, (0, 255, 128), handle_rect, border_radius=5)

# src/ui/visualizer.py
import pygame
import math
import src.config as c
from src.utils.math_utils import map_coords_to_screen
from src.ui.drawing import draw_triangle
from src.ui.interface import Slider, Button

class Visualizer:
    def __init__(self, bounds):
        pygame.init()
        self.screen = pygame.display.set_mode((c.SCREEN_WIDTH + 300, c.SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Self-Organization in Multi-Agent Systems")
        
        self.sim_surface = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        self.bounds = bounds
        
        self.is_paused = True
        self.sim_speed = 1.0
        
        # UI Setup
        self.sidebar_width = 250
        panel_x = 25
        
        self.font_title = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_stats = pygame.font.SysFont("Arial", 18)
        self.font_small = pygame.font.SysFont("Arial", 18) 

        # --- UI ELEMENTS ---
        
        # Row 1: Start | Next Iter (Side by Side)
        self.play_btn = Button(
            x=panel_x, y=50, w=100, h=40,
            text="START", callback=self.toggle_pause,
            color=(60, 200, 60), hover_color=(80, 230, 80)
        )
        self.next_iter_btn = Button(
            x=panel_x + 110, y=50, w=100, h=40,
            text="NEXT ITER", callback=self._dummy_callback,
            color=(60, 100, 200), hover_color=(80, 120, 230)
        )

        # Row 2: Reset (Now Wide)
        self.reset_btn = Button(
            x=panel_x, y=100, w=210, h=40,
            text="RESET", callback=self._dummy_callback,
            color=(200, 60, 60), hover_color=(230, 80, 80)
        )

        # Row 3: Update Position (NEW BUTTON)
        self.update_pos_btn = Button(
            x=panel_x, y=150, w=210, h=35,
            text="UPDATE POSITION", callback=self._dummy_callback,
            color=(220, 140, 20), hover_color=(240, 160, 40)
        )

        # Sliders
        self.agent_slider = Slider(
            x=panel_x, y=260, w=200, h=10,
            min_val=c.MIN_AGENTS, max_val=c.MAX_AGENTS, start_val=c.AGENT_COUNT,
            label="Agent Count"
        )
        self.speed_slider = Slider(
            x=panel_x, y=330, w=200, h=10,
            min_val=0.1, max_val=5.0, start_val=1.0, 
            label="Sim Speed", is_float=True
        )

    def _dummy_callback(self):
        pass 

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.play_btn.text = "RESUME"
            self.play_btn.color = (60, 200, 60)
            self.play_btn.hover_color = (80, 230, 80)
        else:
            self.play_btn.text = "PAUSE"
            self.play_btn.color = (200, 60, 60)
            self.play_btn.hover_color = (230, 80, 80)

    def handle_resize(self, event):
        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

    def handle_ui_events(self, event):
        """
        Returns tuple: (new_agent_count, next_iter_triggered, reset_triggered, update_pos_triggered)
        """
        self.play_btn.handle_event(event)
        
        next_iter_triggered = False
        if self.next_iter_btn.handle_event(event):
            next_iter_triggered = True

        reset_triggered = False
        if self.reset_btn.handle_event(event):
            reset_triggered = True
            self.agent_slider.val = c.AGENT_COUNT
            self.is_paused = True
            self.play_btn.text = "START"
            self.play_btn.color = (60, 200, 60)

        update_pos_triggered = False
        if self.update_pos_btn.handle_event(event):
            update_pos_triggered = True

        new_speed = self.speed_slider.handle_event(event)
        if new_speed is not None: self.sim_speed = new_speed
        
        new_agent_count = self.agent_slider.handle_event(event)
        
        return new_agent_count, next_iter_triggered, reset_triggered, update_pos_triggered

    def _get_perp_offset(self, start, end, magnitude):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0: return (0, 0)
        ux, uy = dx / length, dy / length
        return (uy * magnitude, -ux * magnitude)

    def draw(self, city, rickshaws, total_collisions, history_list):
        self.screen.fill((20, 20, 20)) 
        self.sim_surface.fill(c.BG_COLOR)

        min_lat, max_lat, min_lon, max_lon = self.bounds
        def to_screen(lat, lon):
            return map_coords_to_screen(
                lat, lon, min_lat, max_lat, min_lon, max_lon, 
                c.SCREEN_WIDTH, c.SCREEN_HEIGHT
            )

        # Draw Roads
        for u, v, data in city.G.edges(data=True):
            u_pos = city.G.nodes[u]['pos']
            v_pos = city.G.nodes[v]['pos']
            s = to_screen(u_pos[1], u_pos[0])
            e = to_screen(v_pos[1], v_pos[0])
            pygame.draw.line(self.sim_surface, c.COLOR_ASPHALT, s, e, c.ROAD_WIDTH)
            pygame.draw.line(self.sim_surface, c.COLOR_DIVIDER, s, e, 1)

        # Draw Load
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

        # Draw Nodes
        for n, data in city.G.nodes(data=True):
            pos = data['pos']
            s_pos = to_screen(pos[1], pos[0])
            pygame.draw.circle(self.sim_surface, c.COLOR_ASPHALT, s_pos, int(c.ROAD_WIDTH/2))

        # Agents
        for agent in rickshaws:
            start_node_pos = city.G.nodes[agent.current_node]['pos']
            s_start = to_screen(start_node_pos[1], start_node_pos[0])
            final_screen_pos = s_start
            angle = 0
            
            if agent.target_node:
                end_node_pos = city.G.nodes[agent.target_node]['pos']
                s_end = to_screen(end_node_pos[1], end_node_pos[0])
                cx = s_start[0] + (s_end[0] - s_start[0]) * agent.progress
                cy = s_start[1] + (s_end[1] - s_start[1]) * agent.progress
                ox, oy = self._get_perp_offset(s_start, s_end, c.LANE_OFFSET)
                final_screen_pos = (cx + ox, cy + oy)
                angle = agent.get_visual_angle(s_start, s_end)
            
            agent_color = c.COLOR_RICKSHAW_EMPTY
            if agent.is_crashed: agent_color = c.COLOR_JAM
            elif agent.has_arrived: agent_color = (65, 105, 225)
            elif agent.reversing: agent_color = (255, 165, 0)
            
            draw_triangle(self.sim_surface, agent_color, final_screen_pos, angle, 12)

        # --- BLIT & UI ---
        window_w, window_h = self.screen.get_size()
        sim_x_pos = max(self.sidebar_width, (window_w - c.SCREEN_WIDTH) // 2)
        sim_y_pos = (window_h - c.SCREEN_HEIGHT) // 2
        self.screen.blit(self.sim_surface, (sim_x_pos, sim_y_pos))

        # Sidebar
        sidebar_rect = pygame.Rect(0, 0, self.sidebar_width, window_h)
        pygame.draw.rect(self.screen, (35, 35, 35), sidebar_rect)
        pygame.draw.line(self.screen, (60, 60, 60), (self.sidebar_width, 0), (self.sidebar_width, window_h), 2)
        
        title_surf = self.font_title.render("CONTROLS", True, (150, 150, 150))
        self.screen.blit(title_surf, (25, 15))

        self.play_btn.draw(self.screen)
        self.next_iter_btn.draw(self.screen)
        self.reset_btn.draw(self.screen)
        self.update_pos_btn.draw(self.screen) 
        
        self.agent_slider.draw(self.screen)
        self.speed_slider.draw(self.screen)
        
        # Stats
        pygame.draw.line(self.screen, (60, 60, 60), (20, 360), (self.sidebar_width - 20, 360), 1)
        stats_title = self.font_title.render("STATS", True, (150, 150, 150))
        self.screen.blit(stats_title, (25, 370))
        
        collision_surf = self.font_stats.render(f"Current Collisions: {total_collisions}", True, (255, 100, 100))
        self.screen.blit(collision_surf, (25, 400))

        # History
        y_hist = 440
        if history_list:
            hist_title = self.font_stats.render("History:", True, (200, 200, 200))
            self.screen.blit(hist_title, (25, y_hist))
            y_hist += 30 
            for entry in history_list[-15:]:
                entry_surf = self.font_small.render(entry, True, (150, 150, 150))
                self.screen.blit(entry_surf, (25, y_hist))
                y_hist += 25 

        pygame.display.flip()

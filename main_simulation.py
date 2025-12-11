# main_simulation.py
import pygame
import sys
import random
from city_graph import CityGraph
from agents import Rickshaw, Passenger
import config as c

# ... (Include the map_coords_to_screen function from previous turn) ...
def map_coords_to_screen(lat, lon, min_lat, max_lat, min_lon, max_lon):
    # Same helper function
    x_pct = (lon - min_lon) / (max_lon - min_lon)
    y_pct = (lat - min_lat) / (max_lat - min_lat)
    screen_x = 50 + x_pct * (c.SCREEN_WIDTH - 100)
    screen_y = c.SCREEN_HEIGHT - (50 + y_pct * (c.SCREEN_HEIGHT - 100))
    return int(screen_x), int(screen_y)

def main():
    pygame.init()
    screen = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
    pygame.display.set_caption("Urban Swarm: Phase 3 (Greed & Traffic)")
    clock = pygame.time.Clock()

    # Init
    city = CityGraph(6, 6, 150)
    agents = [Rickshaw(i, city) for i in range(15)]
    passengers = [] # List of active passengers

    # Map Bounds
    all_lats = [d['pos'][1] for n, d in city.G.nodes(data=True)]
    all_lons = [d['pos'][0] for n, d in city.G.nodes(data=True)]
    min_lat, max_lat, min_lon, max_lon = min(all_lats), max(all_lats), min(all_lons), max(all_lons)

    running = True
    while running:
        dt = clock.tick(c.FPS) / 1000.0 # Delta time in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- 1. GAME LOGIC ---
        
        # A. Spawn Passengers (Randomly)
        if random.random() < c.SPAWN_RATE:
            nodes = list(city.G.nodes())
            p1, p2 = random.sample(nodes, 2)
            passengers.append(Passenger(p1, p2))

        # B. Agent Decisions
        for agent in agents:
            # If idle, look for work
            if not agent.passenger:
                agent.hunt(passengers)
            
            # Check for Pickup
            if agent.state == "HUNTING" and agent.current_node == agent.destination_node and not agent.target_node:
                # Find the pax at this node
                for p in passengers:
                    if p.node == agent.current_node:
                        passengers.remove(p)
                        agent.passenger = p
                        agent.state = "DELIVERING"
                        agent.destination_node = p.dest
                        agent._recalculate_path()
                        break
            
            # Check for Delivery
            if agent.state == "DELIVERING" and agent.current_node == agent.destination_node and not agent.target_node:
                agent.passenger = None
                agent.state = "IDLE"
                agent.money += 10
                agent.destination_node = None # Will wander next tick

            agent.move(dt)

        # --- 2. DRAWING ---
        screen.fill(c.BG_COLOR)

        # Draw Streets (Color by Traffic Load)
        for u, v, data in city.G.edges(data=True):
            load = data.get('current_load', 0)
            u_pos = city.G.nodes[u]['pos']
            v_pos = city.G.nodes[v]['pos']
            start = map_coords_to_screen(u_pos[1], u_pos[0], min_lat, max_lat, min_lon, max_lon)
            end = map_coords_to_screen(v_pos[1], v_pos[0], min_lat, max_lat, min_lon, max_lon)
            
            # If load > 3, draw RED (Jam)
            color = c.COLOR_JAM if load > 2 else c.STREET_COLOR
            width = 8 if load > 2 else 4
            pygame.draw.line(screen, color, start, end, width)

        # Draw Nodes
        for n, data in city.G.nodes(data=True):
            pos = data['pos']
            s_pos = map_coords_to_screen(pos[1], pos[0], min_lat, max_lat, min_lon, max_lon)
            pygame.draw.circle(screen, c.NODE_COLOR, s_pos, 4)

        # Draw Passengers (Blue Dots)
        for p in passengers:
            pos = city.G.nodes[p.node]['pos']
            s_pos = map_coords_to_screen(pos[1], pos[0], min_lat, max_lat, min_lon, max_lon)
            pygame.draw.circle(screen, c.COLOR_PASSENGER, s_pos, 6)

        # Draw Agents
        for agent in agents:
            pos = agent.get_position()
            s_pos = map_coords_to_screen(pos[1], pos[0], min_lat, max_lat, min_lon, max_lon)
            
            # Color: Gold if Full, Green if Empty
            color = c.COLOR_RICKSHAW_FULL if agent.passenger else c.COLOR_RICKSHAW_EMPTY
            pygame.draw.circle(screen, color, s_pos, 8)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
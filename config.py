# config.py

# --- VISUALS ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
FPS = 60                   # Keep this high for smooth rendering
BG_COLOR = (20, 20, 20)
STREET_COLOR = (60, 60, 60)
NODE_COLOR = (100, 100, 100)

# --- AGENT COLORS ---
COLOR_RICKSHAW_EMPTY = (0, 255, 128)
COLOR_RICKSHAW_FULL = (255, 200, 0)
COLOR_PASSENGER = (0, 191, 255)
COLOR_JAM = (255, 50, 50)

# --- MECHANICS ---
# CHANGE THIS: Reduced from 1.0 to 0.2 for observation
RICKSHAW_SPEED_BASE = 0.2     

# Keep penalty the same to preserve the "Jam" dynamics relative to speed
TRAFFIC_PENALTY = 0.8         
SPAWN_RATE = 0.02

# --- DRONE SETTINGS ---
# CHANGE THIS: Scale drone speed down too (was 2.0, now 0.4)
DRONE_SPEED = 0.4             
DRONE_VISION_RADIUS = 150.0
DRONE_INTERCEPT_DIST = 10.0
FINE_DURATION = 3.0

# --- COLORS ---
COLOR_DRONE = (255, 255, 255)
COLOR_DRONE_VISION = (255, 255, 255)

# --- VISUALS ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
FPS = 60
BG_COLOR = (30, 30, 30)      # Darker Background to contrast Asphalt
STREET_COLOR = (60, 60, 60)
NODE_COLOR = (120, 120, 120)


# --- ROADS ---
COLOR_ASPHALT = (50, 50, 50)       # Dark Grey Road
COLOR_DIVIDER = (200, 200, 0)      # Yellow Center Line
LANE_OFFSET = 12.0                 # Pixels to shift left (Lane Center)
ROAD_WIDTH = 40                    # Total road width

# --- AGENT COLORS ---
COLOR_RICKSHAW_EMPTY = (0, 255, 128)  # Neon Green
COLOR_RICKSHAW_FULL = (255, 200, 0)   # Gold
COLOR_PASSENGER = (0, 191, 255)       # Blue
COLOR_JAM = (255, 50, 50)             # Red

# --- MECHANICS ---
RICKSHAW_SPEED_BASE = 1.0     
TRAFFIC_PENALTY = 0.8         
SPAWN_RATE = 0.02
# [Keep existing config...]

# --- MECHANICS ---
RICKSHAW_SPEED_BASE = 1.0     
TRAFFIC_PENALTY = 0.8         
SPAWN_RATE = 0.02
COLLISION_DIST = 0.00005      # Crash threshold
LANE_OFFSET_DEG = 0.000015    # <--- NEW: Real-world lane offset (approx 1.5m)

# --- SIMULATION SETTINGS ---
AGENT_COUNT = 20        # Default start
MIN_AGENTS = 0
MAX_AGENTS = 100

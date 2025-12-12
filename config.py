# config.py

# --- VISUALS ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
FPS = 60
BG_COLOR = (20, 20, 20)      # Dark Map
STREET_COLOR = (60, 60, 60)
NODE_COLOR = (100, 100, 100)

# --- AGENT COLORS ---
COLOR_RICKSHAW_EMPTY = (0, 255, 128)  # Neon Green (Available)
COLOR_RICKSHAW_FULL = (255, 200, 0)   # Gold (Earning Money)
COLOR_PASSENGER = (0, 191, 255)       # Blue (Waiting)
COLOR_JAM = (255, 50, 50)             # Red (Traffic Jam)

# --- MECHANICS ---
RICKSHAW_SPEED_BASE = 1.0     # Blocks per second (approx)
TRAFFIC_PENALTY = 0.8         # Speed reduction per car on the same street
SPAWN_RATE = 0.02             # Chance of passenger spawn per tick

# config.py (Append this to your existing file)

# --- DRONE SETTINGS ---
DRONE_SPEED = 2.0             # Twice as fast as rickshaws
DRONE_VISION_RADIUS = 150.0   # How far it can see chaos
DRONE_INTERCEPT_DIST = 10.0   # Distance to "catch" a rickshaw
FINE_DURATION = 3.0           # Seconds a rickshaw stays frozen after being caught

# --- COLORS ---
COLOR_DRONE = (255, 255, 255)         # White
COLOR_DRONE_VISION = (255, 255, 255)  # Faint white outline
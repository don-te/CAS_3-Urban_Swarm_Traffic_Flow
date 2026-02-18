# src/utils/math_utils.py
import math

def map_coords_to_screen(lat, lon, min_lat, max_lat, min_lon, max_lon, screen_w, screen_h):
    """
    Maps geographical coordinates (lat, lon) to screen coordinates (x, y).
    Adds padding to keep drawing within bounds.
    """
    if max_lon == min_lon: max_lon += 0.0001
    if max_lat == min_lat: max_lat += 0.0001
    x_pct = (lon - min_lon) / (max_lon - min_lon)
    y_pct = (lat - min_lat) / (max_lat - min_lat)
    
    # 50px padding
    screen_x = 50 + x_pct * (screen_w - 100)
    screen_y = screen_h - (50 + y_pct * (screen_h - 100))
    return int(screen_x), int(screen_y)

def get_angle(start, end):
    """Calculates angle between two points in radians."""
    dx = end[0] - start[0]
    dy = -(end[1] - start[1])
    return math.atan2(dy, dx)

def haversine_distance(pos1, pos2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    lon1, lat1 = pos1[0], pos1[1]
    lon2, lat2 = pos2[0], pos2[1]
    
    R = 6371000 # Radius of earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

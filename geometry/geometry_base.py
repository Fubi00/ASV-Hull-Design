# geometry/geometry_base.py

def generate_keel_profile(L, T, z1_factor, z2_factor, num_points):
    half_L = L / 2
    p0 = (0.0, -T)
    p1 = (0.25 * half_L, -T + (z1_factor * T))
    p2 = (0.75 * half_L, -T + (z2_factor * T))
    p3 = (half_L, 0.0)
    
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
        z = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
        points.append((x, z))
    return points

def generate_waterline(L, B_max, x1_factor, y1_factor, x2_factor, y2_factor, num_points):
    half_L = L / 2
    half_B = B_max / 2
    p0 = (0.0, half_B)
    p1 = (x1_factor * half_L, y1_factor * half_B)
    p2 = (x2_factor * half_L, y2_factor * half_B)
    p3 = (half_L, 0.0)
    
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
        y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
        points.append((x, y))
    return points

def generate_updated_station(y_wl, z_kjol, y1_factor, z1_factor, y2_factor, z2_factor, num_points):
    p0 = (0.0, z_kjol)
    p3 = (y_wl, 0.0)
    h_local = abs(z_kjol)
    
    p1 = (y1_factor * y_wl, z_kjol + (z1_factor * h_local))
    p2 = (y2_factor * y_wl, z_kjol + (z2_factor * h_local))
    
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        y = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
        z = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
        points.append((y, z))
    return points

def generate_complete_hull(config, num_stations=20, num_points_per_station=15):
    """Tar inn en konfigurasjons-ordbok (fra JSON) og lager skroget"""
    L = config['L']
    B_max = config['B_max']
    T = config['T']
    
    keel_profile = generate_keel_profile(L, T, config['z1_k'], config['z2_k'], num_stations)
    waterline = generate_waterline(L, B_max, config['x1_w'], config['y1_w'], config['x2_w'], config['y2_w'], num_stations)
    
    forebody_mesh = []
    for i in range(num_stations):
        x_local = waterline[i][0]
        y_wl = waterline[i][1]
        z_kjol = keel_profile[i][1]
        
        station_points = generate_updated_station(
            y_wl, z_kjol, 
            config['y1_s'], config['z1_s'], config['y2_s'], config['z2_s'], 
            num_points_per_station
        )
        forebody_mesh.append({'X': x_local, 'Points': station_points})
    
    aftbody_mesh = []
    for station in reversed(forebody_mesh[1:]):
        aftbody_mesh.append({'X': -station['X'], 'Points': station['Points'].copy()})
        
    return aftbody_mesh + forebody_mesh
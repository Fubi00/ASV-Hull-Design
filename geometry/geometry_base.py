# geometry/geometry_base.py
import numpy as np

def get_bezier_value(p0, p1, p2, p3, t):
    """Beregner ett enkelt punkt langs en kubisk Bézier-kurve for en gitt t."""
    return (1 - t)**3 * p0 + 3 * (1 - t)**2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3

def find_t_for_x(p0_x, p1_x, p2_x, p3_x, target_x, tol=1e-5):
    """
    Bruker binærsøk til å finne nøyaktig hvilken t-verdi som gir target_x.
    Dette fungerer fordi X(t) alltid er monotont stigende fra midtskip til baug.
    """
    low, high = 0.0, 1.0
    for _ in range(30): # Maks 30 iterasjoner gir ekstremt høy presisjon
        mid = (low + high) / 2.0
        x_val = get_bezier_value(p0_x, p1_x, p2_x, p3_x, mid)
        
        if abs(x_val - target_x) < tol:
            return mid
        if x_val < target_x:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0

def evaluate_waterline_at_x(x_target, L, B_max, config):
    """Finner nøyaktig halvbredde Y for en spesifikk X-posisjon."""
    half_L = L / 2
    half_B = B_max / 2
    
    p0_x, p0_y = 0.0, half_B
    p1_x, p1_y = config['x1_w'] * half_L, config['y1_w'] * half_B
    p2_x, p2_y = config['x2_w'] * half_L, config['y2_w'] * half_B
    p3_x, p3_y = half_L, 0.0
    
    t = find_t_for_x(p0_x, p1_x, p2_x, p3_x, x_target)
    return get_bezier_value(p0_y, p1_y, p2_y, p3_y, t)

def evaluate_keel_at_x(x_target, L, T, config):
    """Finner nøyaktig kjøldybde Z for en spesifikk X-posisjon."""
    half_L = L / 2
    
    p0_x, p0_z = 0.0, -T
    p1_x, p1_z = config['x1_k'] * half_L, -T + (config['z1_k'] * T)
    p2_x, p2_z = config['x2_k'] * half_L, -T + (config['z2_k'] * T)
    p3_x, p3_z = half_L, 0.0
    
    t = find_t_for_x(p0_x, p1_x, p2_x, p3_x, x_target)
    return get_bezier_value(p0_z, p1_z, p2_z, p3_z, t)

def generate_updated_station(y_wl, z_kjol, config, num_points):
    """Genererer (Y, Z) for et spant basert på lokal bredde og kjøldybde."""
    p0 = (0.0, z_kjol)
    p3 = (y_wl, 0.0)
    h_local = abs(z_kjol)
    
    p1 = (config['y1_s'] * y_wl, z_kjol + (config['z1_s'] * h_local))
    p2 = (config['y2_s'] * y_wl, z_kjol + (config['z2_s'] * h_local))
    
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        y = get_bezier_value(p0[0], p1[0], p2[0], p3[0], t)
        z = get_bezier_value(p0[1], p1[1], p2[1], p3[1], t)
        points.append((y, z))
    return points

def generate_complete_hull(config, num_stations=40, num_points_per_station=15):
    """
    Genererer et komplett, lineært strukturert 3D-skrog.
    Stasjonene er garantert jevnt fordelt langs X-aksen.
    """
    L = config['L']
    B_max = config['B_max']
    T = config['T']
    half_L = L / 2
    
    forebody_mesh = []
    
    # Lag en helt lineær fordeling av X-stasjoner fra midtskipet (0) til baugen (L/2)
    x_stations = np.linspace(0.0, half_L, num_stations)
    
    for x_local in x_stations:
        # Hvis vi er helt i baugtuppen, tvinger vi verdiene til null for å lukke skroget helt rent
        if abs(x_local - half_L) < 1e-5:
            y_wl = 0.0
            z_kjol = 0.0
        else:
            y_wl = evaluate_waterline_at_x(x_local, L, B_max, config)
            z_kjol = evaluate_keel_at_x(x_local, L, T, config)
            
        station_points = generate_updated_station(y_wl, z_kjol, config, num_points_per_station)
        forebody_mesh.append({'X': x_local, 'Points': station_points})
        
    # Speil forskipet for å lage akterskipet (X blir negativ)
    aftbody_mesh = []
    for station in reversed(forebody_mesh[1:]):
        aftbody_mesh.append({'X': -station['X'], 'Points': station['Points'].copy()})
        
    return aftbody_mesh + forebody_mesh
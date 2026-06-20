L = 1.4 # [m] Lengde på skrog
B_max = 0.4 # [m] Maks bredde på skroget

def calculate_bezier_point(p0, p1, p2, p3, t):
    """
    Beregner et enkelt X- eller Y-koordinat langs en kubisk Bézier-kurve.
    p0, p1, p2, p3 er verdiene (f.eks. X eller Y) for kontrollpunktene.
    t er parameteren mellom 0.0 og 1.0.
    """
    return (1 - t)**3 * p0 + 3 * (1 - t)**2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3

def generate_curve_points(p0, p1, p2, p3, num_points=20):
    """
    Genererer en liste med punkter langs kurven fra t=0 til t=1.
    """
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        point_value = calculate_bezier_point(p0, p1, p2, p3, t)
        points.append(point_value)
    return points

def generate_waterline(L, B_max, x1_factor, y1_factor, x2_factor, y2_factor, num_points=20):
    """
    Genererer en liste med (X, Y) koordinater for vannlinjen til forskipet.
    Factors er tall mellom 0 og 1 som algoritmen (Godzilla) kan justere.
    """
    half_L = L / 2
    half_B = B_max / 2
    
    # Definer kontrollpunktene basert på faktorer (0.0 til 1.0)
    p0 = (0.0, half_B)
    p1 = (x1_factor * half_L, y1_factor * half_B)
    p2 = (x2_factor * half_L, y2_factor * half_B)
    p3 = (half_L, 0.0)
    
    waterline_points = []
    
    for i in range(num_points):
        t = i / (num_points - 1)
        
        # Beregn X og Y uavhengig for parameteren t
        x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
        y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
        
        waterline_points.append((x, y))
        
    return waterline_points

def generate_station_profile(y_wl, T, y1_factor, z1_factor, y2_factor, z2_factor, num_points=15):
    """
    Genererer (Y, Z) punkter for en halvstasjon (ett spant på en side).
    y_wl: Bredden skroget har på dette spesifikke stedet (fra vannlinjekurven).
    T: Totalt dypgående (draft).
    Factors: Tall mellom 0.0 og 1.0 som styrer fyldigheten.
    """
    # P0: Kjølen (X=0 i lokal spant-akse, Z=-T)
    p0 = (0.0, -T)
    
    # P1 & P2: Kontrollpunkter, strengt begrenset innforbi y_wl
    p1 = (y1_factor * y_wl, -T + (z1_factor * T))
    p2 = (y2_factor * y_wl, -T + (z2_factor * T))
    
    # P3: Vannlinjen
    p3 = (y_wl, 0.0)
    
    station_points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        
        # Kubisk Bézier-formel for Y og Z
        y = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
        z = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
        
        station_points.append((y, z))
        
    return station_points
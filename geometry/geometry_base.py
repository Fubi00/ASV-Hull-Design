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

def generate_keel_profile(L, T, z1_factor=0.0, z2_factor=0.2, num_points=20):
    """
    Genererer (X, Z) koordinater for kjøllinjen fra midtskip til baug.
    z1_factor og z2_factor styrer hvor raskt kjølen svinger opp mot baugen.
    """
    half_L = L / 2
    
    # P0: Midtskipet (Båten er på sitt dypeste, Z = -T)
    p0 = (0.0, -T)
    # P1 & P2: Kontrollpunkter som optimalisatoren kan justere for å endre bunnprofilen
    p1 = (0.25 * half_L, -T + (z1_factor * T))
    p2 = (0.75 * half_L, -T + (z2_factor * T))
    # P3: Baugtuppen (Her treffer kjølen vannlinjen, Z = 0.0)
    p3 = (half_L, 0.0)
    
    keel_points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        
        x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
        z = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
        
        keel_points.append((x, z))
        
    return keel_points

def generate_updated_station(y_wl, z_kjol, y1_factor=0.5, z1_factor=0.0, y2_factor=1.0, z2_factor=0.5, num_points=15):
    """
    Genererer (Y, Z) for et spant, tilpasset lokal kjølhøyde (z_kjol) og bredde (y_wl).
    z1_factor og z2_factor styrer høydeposisjonen relativt mellom kjøl og vannlinje.
    """
    # P0: Start på den lokale kjølen (Senterlinje Y=0, Z=z_kjol)
    p0 = (0.0, z_kjol)
    
    # P3: Ende på vannlinjen (Y=y_wl, Z=0.0)
    p3 = (y_wl, 0.0)
    
    # Høyden på dette spesifikke spantet (avstanden fra kjøl til vannlinje)
    h_local = abs(z_kjol)
    
    # P1 & P2: Kontrollpunkter beskyttet mot å gå utenfor y_wl, 
    # og skalert etter det lokale spantets høyde
    p1 = (y1_factor * y_wl, z_kjol + (z1_factor * h_local))
    p2 = (y2_factor * y_wl, z_kjol + (z2_factor * h_local))
    
    station_points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        
        y = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
        z = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
        
        station_points.append((y, z))
        
    return station_points

def generate_3d_hull_mesh(L, B_max, T, num_stations=20, num_points_per_station=15):
    """
    Hovedfunksjon for å generere et strukturert 3D-punktnettverk for forskipet.
    """
    hull_mesh = [] # En liste som skal holde på alle stasjonene
    
    # 1. Definer master-kurvene (Vannlinje og Kjølprofil)
    # I en ferdig optimalisator vil faktorene under være variabler fra 'Godzilla'
    
    for i in range(num_stations):
        # Fordel stasjonene jevnt fra midtskipet (X=0) til baugen (X = L/2)
        x_local = (i / (num_stations - 1)) * (L / 2)
        
        # 2. FINN LOKAL BREDDE (Y_wl) FRA VANNLINJEKURVEN VED DENNE X
        # (For enkelhets skyld bruker vi en forenklet parabel her i eksempelet, 
        # men i koden din vil du løse Bézier-ligningen for x_local)
        y_wl = (B_max / 2) * (1 - (x_local / (L / 2))**2) 
        
        # 3. FINN LOKAL KJØLDYBDE (Z_kjol) FRA PROFILKURVEN VED DENNE X
        # Kjølen svinger oppover fra -T på midtskipet til 0 i baugen
        z_kjol = -T * (1 - (x_local / (L / 2))**2)
        
        # 4. GENERER SPANTET BASERT PÅ DE LOKALE VERDIENE
        # Her kaller vi den oppdaterte stasjonsfunksjonen
        station_points = generate_updated_station(y_wl, z_kjol, num_points_per_station)
        
        # Lagre stasjonen sammen med sin X-koordinat
        hull_mesh.append({'X': x_local, 'Points': station_points})
        
    return hull_mesh

def generate_complete_hull(L, B_max, T, num_stations=20, num_points_per_station=15):
    """
    Genererer et komplett, symmetrisk double-ender skrog (både for- og akterskip).
    Returnerer en liste med stasjoner sortert fra akter til forut.
    """
    # 1. Generer først rutenettet for forskipet (X fra 0 til L/2)
    # (Vi bruker loopen vi snakket om i sted)
    forebody_mesh = []
    
    # Vi henter master-kurvene for kjøl og vannlinje
    keel_profile = generate_keel_profile(L, T, num_points=num_stations)
    waterline = generate_waterline(L, B_max, 0.5, 1.0, 0.5, 0.5, num_points=num_stations)
    
    for i in range(num_stations):
        x_local = waterline[i][0]
        y_wl = waterline[i][1]
        z_kjol = keel_profile[i][1]
        
        station_points = generate_updated_station(y_wl, z_kjol, num_points=num_points_per_station)
        forebody_mesh.append({'X': x_local, 'Points': station_points})
    
    # 2. Generer akterskipet ved å speile forskipet
    aftbody_mesh = []
    
    # Vi looper baklengs gjennom forskipet (unntatt midtspantet på i=0 for å unngå duplikat)
    for station in reversed(forebody_mesh[1:]):
        x_aft = -station['X']  # Inverterer X-koordinaten
        
        # Punktene (Y, Z) forblir de samme siden skroget er symmetrisk om midtspantet
        aft_points = station['Points'].copy() 
        
        aftbody_mesh.append({'X': x_aft, 'Points': aft_points})
        
    # 3. Sveis sammen akterskipet og forskipet i riktig rekkefølge:
    # [Akterut --> Midtskip --> Forut]
    complete_hull_mesh = aftbody_mesh + forebody_mesh
    
    return complete_hull_mesh
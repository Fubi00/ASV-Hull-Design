import numpy as np

def calculate_michell_resistance(hull_mesh, speed, separation=0.0, is_multihull=False):
    """
    Beregner en tilnærming av bølgemotstand basert på Michells integral.
    hull_mesh: Matrisen fra geometry_base.
    speed: Hastighet i m/s.
    separation: Senter-til-senter avstand (Y) hvis katamaran/trimaran.
    """
    if speed <= 0.1:
        return 0.0
        
    g = 9.81
    rho = 1025.0 # Sjøvann tetthet
    
    num_stations = len(hull_mesh)
    num_waterlines = len(hull_mesh[0]['Points'])
    
    # Finn dX (avstanden mellom stasjonene)
    dx = abs(hull_mesh[1]['X'] - hull_mesh[0]['X'])
    
    # Integral-koeffisienter (I og J)
    I_sum = 0.0
    J_sum = 0.0
    
    # Forenklet numerisk integrasjon over skrogoverflaten
    for i in range(1, num_stations - 1):
        for j in range(num_waterlines):
            # Hent lokal dybde (Z) og breddeendring (dY)
            z = hull_mesh[i]['Points'][j][1]
            
            # Sentral differanse for den deriverte dY/dX
            dy_dx = (hull_mesh[i+1]['Points'][j][0] - hull_mesh[i-1]['Points'][j][0]) / (2 * dx)
            
            # Bølgetall-komponent (k) basert på hastighet
            k0 = g / (speed ** 2)
            
            # Bidrag til integranden (Froude-avhengig)
            weight = np.exp(k0 * z) * dy_dx * dx
            
            # Forenklet integrasjons-kjerne
            I_sum += weight * np.cos(k0 * hull_mesh[i]['X'])
            J_sum += weight * np.sin(k0 * hull_mesh[i]['X'])
            
    # Grunnleggende bølgemotstand for ett skrog
    R_w_single = (4 * rho * g**2 / (np.pi * speed**2)) * (I_sum**2 + J_sum**2) * 0.01 # Skaleringsfaktor for numerisk oppløsning
    
    # --- BØLGEINTERFERENS (Flerskrog-logikk) ---
    if is_multihull and separation > 0:
        # Interferensfaktor: Bølgene treffer hverandre basert på avstand (separation) og hastighet
        k0 = g / (speed ** 2)
        interference_factor = 1 + np.cos(2 * k0 * separation)
        return R_w_single * interference_factor * 2 # Ganger med 2 for to skrog + interferens
        
    return R_w_single

def calculate_viscous_resistance(hull_mesh, speed):
    """
    Beregner den viskøse motstanden (friksjon) basert på våt overflate og ITTC-57.
    """
    # Enkel estimering av våt overflate (Wetted Surface Area - WSA)
    # I et fullstendig system regner du dette nøyaktig ut fra mesh-firkantene
    wsa = 0.0
    dx = abs(hull_mesh[1]['X'] - hull_mesh[0]['X'])
    for station in hull_mesh:
        # Integrer buelengden av spantet under vann
        y_points = [p[0] for p in station['Points']]
        wsa += 2 * max(y_points) * dx # Forenklet anslag
        
    if speed <= 0.1:
        return 0.0
        
    rho = 1025.0
    nu = 1.188e-6 # Kinematisk viskositet for vann
    L = abs(hull_mesh[-1]['X'] - hull_mesh[0]['X'])
    
    # Reynolds nummer
    Rn = (speed * L) / nu
    # ITTC-1957 friksjonskoeffisient
    Cf = 0.075 / ((np.log10(Rn) - 2) ** 2)
    
    R_f = 0.5 * rho * (speed ** 2) * wsa * Cf
    return R_f
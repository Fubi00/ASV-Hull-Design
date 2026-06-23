import numpy as np

def calculate_michell_components(hull_mesh, speed, lambda_val):
    """
    Beregner de frie bølgekomponentene I og J for en gitt lambda-verdi.
    Dette er selve kjernen i Michells tynnskrogteori.
    """
    g = 9.81
    k0 = g / (speed ** 2)
    k = k0 * lambda_val ** 2  # Lokalt bølgetall for denne bølgevinkelen
    
    num_stations = len(hull_mesh)
    num_wl = len(hull_mesh[0]['Points'])
    
    I_sum = 0.0
    J_sum = 0.0
    
    # Gå gjennom skrogoverflaten stasjon for stasjon
    for i in range(1, num_stations - 1):
        x = hull_mesh[i]['X']
        
        # Finn dX (avstand mellom nabostasjoner)
        dx = abs(hull_mesh[i+1]['X'] - hull_mesh[i-1]['X']) / 2.0
        
        for j in range(1, num_wl):
            z = hull_mesh[i]['Points'][j][1]
            dz = abs(hull_mesh[i]['Points'][j][1] - hull_mesh[i]['Points'][j-1][1])
            
            # Sentraldifferanse for dY/dX (breddeendring langs skroget)
            dy_dx = (hull_mesh[i+1]['Points'][j][0] - hull_mesh[i-1]['Points'][j][0]) / (2.0 * dx)
            
            # Integrandens bidrag (dempes eksponensielt med dybden z)
            # Vi bruker lambda_val for å korrigere for vinkeleffekten av bølgen
            weight = np.exp(k * z / lambda_val) * dy_dx * dx * dz
            
            # Symmetrisk integrasjon om X-aksen
            I_sum += weight * np.cos(k * x / lambda_val)
            J_sum += weight * np.sin(k * x / lambda_val)
            
    return I_sum, J_sum

def get_total_wave_resistance(hull_mesh, speed, configurations=None):
    """
    Integrerer over lambda-spekteret for å finne total bølgemotstand (Rw).
    Støtter Monohull, Katamaran og Trimaran via konfigurasjonsfilen.
    """
    if speed <= 0.2:
        return 0.0
        
    g = 9.81
    rho = 1025.0
    
    # Standard konfigurasjon hvis ingenting er oppgitt (Monohull)
    if configurations is None:
        configurations = {'type': 'mono', 'separation': 0.0}
        
    # Numerisk integrasjon over lambda (fra 1.0 til 5.0 med 40 steg)
    lambda_steps = 40
    lambda_array = np.linspace(1.001, 5.0, lambda_steps)
    d_lambda = (5.0 - 1.001) / (lambda_steps - 1)
    
    total_integral = 0.0
    
    for lambda_val in lambda_array:
        I, J = calculate_michell_components(hull_mesh, speed, lambda_val)
        hull_wave_energy = I**2 + J**2
        
        # --- FLERSKROG / INTERFERENS LOGIKK ---
        interference = 1.0
        k0 = g / (speed ** 2)
        
        if configurations['type'] == 'katamaran':
            # Katamaran har to like skrog separert med avstand S
            s = configurations['separation']
            # Interferensfaktor basert på fasingen mellom de to skrogene
            interference = 2 * (1 + np.cos(2 * k0 * lambda_val * s))
            
        elif configurations['type'] == 'trimaran':
            # Forenklet trimaran: Hovedskrog + 2 sideskrog (antatt like for nå)
            s = configurations['separation']
            # Interferens mellom senterskrog og sideskrog
            interference = 1 + 4 * np.cos(k0 * lambda_val * s) + 4 * (np.cos(k0 * lambda_val * s)**2)
            
        # Michell integrasjonskjerne
        kernel = (lambda_val ** 2) / np.sqrt(lambda_val ** 2 - 1)
        total_integral += kernel * hull_wave_energy * interference * d_lambda
        
    R_w = (4.0 * rho * g**2 / (np.pi * speed**2)) * total_integral
    return max(0.0, R_w)
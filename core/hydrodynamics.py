import numpy as np

def calculate_hull_properties(hull_mesh, box_L=0.3, box_B=0.1, box_H=0.15):
    """
    Analyserer geometrimatrisen og beregner fysiske egenskaper:
    - Volum [m³] og Oppdrift [kg]
    - Våt overflate (WSA) [m²]
    - Batteriboks-klaring (True/False)
    """
    if not hull_mesh:
        return {'volume': 0.0, 'displacement': 0.0, 'wsa': 0.0, 'fits_battery': False}
        
    rho_water = 1025.0  # Tetthet for sjøvann [kg/m³]
    num_stations = len(hull_mesh)
    
    total_volume = 0.0
    total_wsa = 0.0
    
    # Lister for å lagre data per stasjon til batterisjekken
    station_x = []
    station_can_fit_box_section = []
    
    # Loop gjennom alle stasjonene for å integrere areal og overflate
    for i in range(num_stations):
        x = hull_mesh[i]['X']
        pts = hull_mesh[i]['Points']
        num_pts = len(pts)
        
        station_x.append(x)
        
        # 1. Beregn tverrsnittsareal (Half-section area) med trapesmetoden
        # pts er sortert fra kjøl (z = z_kjol) til vannlinje (z = 0)
        st_area = 0.0
        st_perimeter = 0.0
        
        for j in range(num_pts - 1):
            y1, z1 = pts[j][0], pts[j][1]
            y2, z2 = pts[j+1][0], pts[j+1][1]
            
            # Trapesformel for areal under kurven (Z-intervaller)
            st_area += 0.5 * (y1 + y2) * (z2 - z1)
            
            # Buelengde for våt overflate
            st_perimeter += np.sqrt((y2 - y1)**2 + (z2 - z1)**2)
            
        # Ganger med 2 for å få begge sider av skroget (Symmetrisk)
        actual_area = st_area * 2
        actual_perimeter = st_perimeter * 2
        
        # Lagre arealet på stasjonen for lengdeintegrasjon (Volum)
        hull_mesh[i]['Area'] = actual_area
        hull_mesh[i]['Perimeter'] = actual_perimeter
        
        # 2. BATTERIBOKS-SJEKK FOR DENNE STASJONEN
        # Sjekker om stasjonen er dyp nok, og om den er bred nok på boksens makshøyde
        z_kjol = pts[0][1]
        local_hull_height = abs(z_kjol)
        
        fits_locally = False
        if local_hull_height >= box_H:
            # Vi må finne ut hvor bredt skroget er ved dybden Z = -box_H
            # Vi interpolerer mellom punktene på spantet for å finne nøyaktig bredde
            z_target = -box_H
            y_at_z_target = 0.0
            
            for j in range(num_pts - 1):
                z_low, y_low = pts[j][1], pts[j][0]
                z_high, y_high = pts[j+1][1], pts[j+1][0]
                
                if z_low <= z_target <= z_high:
                    # Lineær interpolasjon
                    if abs(z_high - z_low) > 1e-5:
                        frac = (z_target - z_low) / (z_high - z_low)
                        y_at_z_target = y_low + frac * (y_high - y_low)
                    else:
                        y_at_z_target = y_low
                    break
            
            # For at boksen skal passe, må skrogbredden (2 * y) være større enn box_B
            if (y_at_z_target * 2) >= box_B:
                fits_locally = True
                
        station_can_fit_box_section.append(fits_locally)

    # 3. INTEGRER LANGS X FOR Å FINNE TOTALVOLUM OG WSA
    for i in range(num_stations - 1):
        dx = abs(hull_mesh[i+1]['X'] - hull_mesh[i]['X'])
        
        # Volumintegrasjon (Trapesmetoden langs X)
        total_volume += 0.5 * (hull_mesh[i]['Area'] + hull_mesh[i+1]['Area']) * dx
        # WSA-integrasjon
        total_wsa += 0.5 * (hull_mesh[i]['Perimeter'] + hull_mesh[i+1]['Perimeter']) * dx

    # 4. GLOBALT LENGDEKRAV FOR BATTERIBOKS
    # Vi må finne ut om det finnes et *sammenhengende* strekk langs X som er minst box_L langt
    fits_battery_global = False
    current_stretch = 0.0
    
    for i in range(num_stations - 1):
        if station_can_fit_box_section[i] and station_can_fit_box_section[i+1]:
            current_stretch += abs(station_x[i+1] - station_x[i])
            if current_stretch >= box_L:
                fits_battery_global = True
                break
        else:
            current_stretch = 0.0

    return {
        'volume': total_volume,
        'displacement': total_volume * rho_water,
        'wsa': total_wsa,
        'fits_battery': fits_battery_global
    }


def calculate_michell_components(hull_mesh, speed, lambda_val):
    """Beregner de frie bølgekomponentene I og J for en gitt lambda-verdi."""
    g = 9.81
    k = (g / (speed ** 2)) * lambda_val ** 2
    
    num_stations = len(hull_mesh)
    num_wl = len(hull_mesh[0]['Points'])
    
    I_sum = 0.0
    J_sum = 0.0
    
    for i in range(1, num_stations - 1):
        x = hull_mesh[i]['X']
        dx = abs(hull_mesh[i+1]['X'] - hull_mesh[i-1]['X']) / 2.0
        
        for j in range(1, num_wl):
            z = hull_mesh[i]['Points'][j][1]
            dz = abs(hull_mesh[i]['Points'][j][1] - hull_mesh[i]['Points'][j-1][1])
            
            dy_dx = (hull_mesh[i+1]['Points'][j][0] - hull_mesh[i-1]['Points'][j][0]) / (2.0 * dx)
            weight = np.exp(k * z / lambda_val) * dy_dx * dx * dz
            
            I_sum += weight * np.cos(k * x / lambda_val)
            J_sum += weight * np.sin(k * x / lambda_val)
            
    return I_sum, J_sum


def get_total_wave_resistance(hull_mesh, speed, config_global):
    """Beregner global og interferens-korrigert bølgemotstand."""
    if speed <= 0.2 or not hull_mesh:
        return 0.0
        
    g = 9.81
    rho = 1025.0
    
    num_hulls = config_global.get('num_hulls', 3)
    separation = config_global.get('separation', 0.6)
    stagger = config_global.get('stagger', 0.0)
    
    lambda_steps = 40
    lambda_array = np.linspace(1.001, 5.0, lambda_steps)
    d_lambda = (5.0 - 1.001) / (lambda_steps - 1)
    
    total_integral = 0.0
    
    for lambda_val in lambda_array:
        I, J = calculate_michell_components(hull_mesh, speed, lambda_val)
        hull_wave_energy = I**2 + J**2
        
        # --- AVANSERT INTERFERENS (Stagger og Separation integrert i fasen) ---
        k0 = g / (speed ** 2)
        k = k0 * lambda_val
        
        if num_hulls == 1:
            interference = 1.0
        elif num_hulls == 2:
            # Katamaran (To skrog, separasjon S, ingen stagger i seg selv)
            interference = 2 * (1 + np.cos(2 * k * lambda_val * separation))
        elif num_hulls == 3:
            # Trimaran med både Separasjon (Y) og Stagger (X-forskyvning av sideskrog)
            # Fasevinkel-endring basert på sideskrogenes posisjon relativt til hovedskroget
            phase_x = k * stagger
            phase_y = k * lambda_val * separation
            
            # Matematisk interferensfaktor for et symmetrisk trimaransetup
            interference = 1 + 4 * np.cos(phase_x) * np.cos(phase_y) + 4 * (np.cos(phase_y) ** 2)
            
        kernel = (lambda_val ** 2) / np.sqrt(lambda_val ** 2 - 1)
        total_integral += kernel * hull_wave_energy * interference * d_lambda
        
    R_w = (4.0 * rho * g**2 / (np.pi * speed**2)) * total_integral
    return max(0.0, R_w)


def calculate_viscous_resistance_exact(wsa, length, speed):
    """Beregner ren friksjonsmotstand basert på nøyaktig utregnet WSA og ITTC-57."""
    if speed <= 0.1 or wsa <= 0.0:
        return 0.0
        
    rho = 1025.0
    nu = 1.188e-6
    
    Rn = (speed * length) / nu
    Cf = 0.075 / ((np.log10(Rn) - 2) ** 2)
    
    return 0.5 * rho * (speed ** 2) * wsa * Cf
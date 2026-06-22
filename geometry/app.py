import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- HER LIMER DU INN GEOMETRIFUNKSJONENE VI LAGDE ISTED ---
# (generate_keel_profile, generate_waterline, generate_updated_station, generate_complete_hull)

def plot_hull_lines(hull_mesh):
    """
    Oppretter en GUI med 3 visninger: Topp (Vannlinjer), Side (Profil), Front (Spant)
    """
    # Opprett et "subplots"-oppsett med 1 rad og 3 kolonner
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("Ovenfra (Toppvisning)", "Fra Siden (Profil)", "Forfra/Akterfra (Spant)"),
        horizontal_spacing=0.08
    )

    # 1. TOPPVISNING (X vs Y) - Vi tegner linjene langs skroget
    # Vi henter ut "vannlinjene" ved å loope gjennom hvert punkt på stasjonene
    num_points_per_station = len(hull_mesh[0]['Points'])
    for p_idx in range(num_points_per_station):
        x_lines = [station['X'] for station in hull_mesh]
        y_lines = [station['Points'][p_idx][0] for station in hull_mesh]
        
        # Positiv side (Styrbord)
        fig.add_trace(go.Scatter(x=x_lines, y=y_lines, mode='lines', line=dict(color='blue', width=1), showlegend=False), row=1, col=1)
        # Negativ side (Babord) - speilet om senterlinjen
        fig.add_trace(go.Scatter(x=x_lines, y=[-y for y in y_lines], mode='lines', line=dict(color='blue', width=1), showlegend=False), row=1, col=1)

    # 2. SIDEVISNING (X vs Z) - Profil og kjøllinje
    for p_idx in range(num_points_per_station):
        x_lines = [station['X'] for station in hull_mesh]
        z_lines = [station['Points'][p_idx][1] for station in hull_mesh]
        fig.add_trace(go.Scatter(x=x_lines, y=z_lines, mode='lines', line=dict(color='green', width=1), showlegend=False), row=1, col=2)

    # 3. FRONTVISNING (Y vs Z) - Klassisk spantetegning
    for station in hull_mesh:
        y_points = [p[0] for p in station['Points']]
        z_points = [p[1] for p in station['Points']]
        
        # Høyre side av spantet
        fig.add_trace(go.Scatter(x=y_points, y=z_points, mode='lines', line=dict(color='red', width=1), showlegend=False), row=1, col=3)
        # Venstre side av spantet (speilet)
        fig.add_trace(go.Scatter(x=[-y for y in y_points], y=z_points, mode='lines', line=dict(color='red', width=1), showlegend=False), row=1, col=3)

    # Oppdater layout for fin visning
    fig.update_layout(
        title_text="ASV Skrogvisualisering - 2D Linjetegninger",
        height=500,
        width=1200,
        template="plotly_white"
    )
    
    # Sørg for at proporsjonene (aspect ratio) er like, så båten ikke ser strukket ut
    fig.update_yaxes(scaleanchor="x", scaleratio=1)

    fig.show()

# --- TEST AV SYSTEMET ---
if __name__ == "__main__":
    # Inputparamatere (Dette blir "input-feltene" dine)
    L_input = 2.0      # Lengde i meter
    B_input = 0.4      # Bredde i meter
    T_input = 0.15     # Dypgående i meter

    # Generer skroget basert på dine parametere
    mitt_skrog = generate_complete_hull(L=L_input, B_max=B_input, T=T_input)
    
    # Start den grafiske visningen
    plot_hull_lines(mitt_skrog)
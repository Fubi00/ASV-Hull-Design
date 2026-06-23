import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json

# Importer kjernefunksjonene dine
from geometry.geometry_base import generate_complete_hull
from core.hydrodynamics import calculate_hull_properties, get_total_wave_resistance, calculate_viscous_resistance_exact

st.set_page_config(layout="wide")
st.title("ASV Multidisciplinary Design Optimization Dashboard 🚢")
st.markdown("---")

# ==============================================================================
# 🎛️ 1. INNGANGSPARAMETERE & BEGRENSNINGER (TOPPEN AV APPEN)
# ==============================================================================
st.header("📋 1. Globale Krav & Begrensninger (Constraints)")

top_col1, top_col2, top_col3, top_col4 = st.columns(4)

with top_col1:
    st.subheader("Fartøy Globalt")
    num_hulls = st.selectbox("Antall skrog", [1, 2, 3], index=2) # Default Trimaran
    max_L_total = st.number_input("Maks lengde totalt [m]", 0.5, 10.0, 3.0, 0.1)
    max_B_total = st.number_input("Maks bredde totalt [m]", 0.2, 5.0, 1.5, 0.1)
    speed_knot = st.slider("Driftshastighet [Knop]", 1.0, 15.0, 5.0, 0.5)
    speed_ms = speed_knot * 0.5144
    
with top_col2:
    st.subheader("Vekt & Last")
    target_weight = st.number_input("Vekt som skal bæres [kg]", 1.0, 500.0, 25.0, 1.0)
    st.markdown("**Fordelingsområde for oppdrift**")
    weight_min_factor = st.number_input("Min faktor (f.eks. 0.90)", 0.5, 1.5, 0.90, 0.01)
    weight_max_factor = st.number_input("Maks faktor (f.eks. 0.95)", 0.5, 1.5, 0.95, 0.01)

with top_col3:
    st.subheader("Skrog Dimensjonsgrenser")
    min_L_main = st.number_input("Min lengde hovedskrog [m]", 0.2, 5.0, 1.5, 0.1)
    max_L_main = st.number_input("Maks lengde hovedskrog [m]", 0.2, 5.0, 2.5, 0.1)
    min_L_side = st.number_input("Min lengde sideskrog [m]", 0.0, 5.0, 0.5, 0.1) if num_hulls > 1 else 0.0
    max_L_side = st.number_input("Maks lengde sideskrog [m]", 0.0, 5.0, 1.5, 0.1) if num_hulls > 1 else 0.0

with top_col4:
    st.subheader("Interne Klaringer & Komponenter")
    min_B_internal = st.number_input("Minimum innvendig skrogbredde [m]", 0.02, 0.5, 0.08, 0.01)
    min_dist_hulls = st.number_input("Min avstand mellom skrog (motorplass) [m]", 0.0, 2.0, 0.4) if num_hulls > 1 else 0.0
    
    st.markdown("**🔋 Batteriboks-krav (L x B x H)**")
    box_L = st.number_input("Boks Lengde [m]", 0.05, 1.0, 0.3, 0.01)
    box_B = st.number_input("Boks Bredde [m]", 0.02, 0.5, 0.1, 0.01)
    box_H = st.number_input("Boks Høyde [m]", 0.02, 0.5, 0.15, 0.01)

with st.expander("🛠️ Manuell geometri-overstyring (For testing før optimalisering)"):
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.markdown("**Hovedskrog test-dimensjoner**")
        L_main_test = st.slider("Lengde Hoved", min_L_main, max_L_main, (min_L_main+max_L_main)/2)
        B_main_test = st.slider("Bredde Hoved", 0.05, 0.5, 0.25)
        T_main_test = st.slider("Dypgående Hoved", 0.02, 0.4, 0.12)
        x2_k_m = st.slider("Bauglengde kjøl (x2_k) - Øks-faktor", 0.0, 1.0, 0.9)
    with m_col2:
        st.markdown("**Sideskrog test-dimensjoner**")
        L_side_test = st.slider("Lengde Side", min_L_side, max_L_side, (min_L_side+max_L_side)/2) if num_hulls > 1 else 0.0
        B_side_test = st.slider("Bredde Side", 0.02, 0.4, 0.12) if num_hulls > 1 else 0.0
        T_side_test = st.slider("Dypgående Side", 0.01, 0.3, 0.06) if num_hulls > 1 else 0.0
        separation_test = st.slider("Separasjon (Y)", min_dist_hulls, max_B_total, 0.5) if num_hulls > 1 else 0.0
        stagger_test = st.slider("Stagger (X)", -max_L_total, max_L_total, -0.2) if num_hulls > 1 else 0.0

st.markdown("---")

# ==============================================================================
# 📐 DATA-PREPARERING & BEREGNINGER
# ==============================================================================
config_main = {
    'L': L_main_test, 'B_max': B_main_test, 'T': T_main_test,
    'x1_w': 0.5, 'y1_w': 1.0, 'x2_w': 0.5, 'y2_w': 0.5,
    'x1_k': 0.5, 'z1_k': 0.0, 'x2_k': x2_k_m, 'z2_k': 0.0,
    'y1_s': 0.5, 'z1_s': 0.0, 'y2_s': 1.0, 'z2_s': 0.5
}

config_side = {
    'L': L_side_test, 'B_max': B_side_test, 'T': T_side_test,
    'x1_w': 0.5, 'y1_w': 1.0, 'x2_w': 0.5, 'y2_w': 0.5,
    'x1_k': 0.5, 'z1_k': 0.0, 'x2_k': 0.5, 'z2_k': 0.2,
    'y1_s': 0.5, 'z1_s': 0.0, 'y2_s': 1.0, 'z2_s': 0.5
}

hull_mesh_main = generate_complete_hull(config_main, num_stations=40)
hull_mesh_side = generate_complete_hull(config_side, num_stations=40) if num_hulls > 1 else None

prop_main = calculate_hull_properties(hull_mesh_main, box_L, box_B, box_H)
prop_side = calculate_hull_properties(hull_mesh_side, box_L, box_B, box_H) if num_hulls > 1 else None

global_hydro_config = {'num_hulls': num_hulls, 'separation': separation_test, 'stagger': stagger_test if num_hulls > 1 else 0.0}
R_w_global = get_total_wave_resistance(hull_mesh_main, speed_ms, global_hydro_config)

R_f_main = calculate_viscous_resistance_exact(prop_main['wsa'], config_main['L'], speed_ms)
R_f_side = calculate_viscous_resistance_exact(prop_side['wsa'], config_side['L'], speed_ms) if num_hulls > 1 else 0.0

R_total_global = R_w_global + R_f_main + (R_f_side * (num_hulls - 1))


# ==============================================================================
# 📐 NY FUNKSJON FOR DET SPESIFISERTE 3x2 MATRISE-PLOTTET PER SKROG
# ==============================================================================
def create_vessel_3x2_subplot(mesh_data, props, R_f, name, is_main_hull=False):
    """
    Oppretter et perfekt opplinjet 3x2 plotnettverk for ett skrog:
    - (1,1): Data tekstfyll (Helt rent, uten akser)
    - (2,1): Frontvisning (Spant) -> Bredde vs Dybde
    - (1,2): Toppvisning (Vannlinjer, rowspan=2) -> Lengde vs Bredde
    - (3,1): Sidevisning (Profil, colspan=2) -> Lengde vs Dybde
    """
    # VIKTIG: Kun 4 titler fordi det bare er 4 aktive delplott!
    fig = make_subplots(
        rows=3, cols=2,
        specs=[
            [{"type": "scatter"}, {"type": "scatter", "rowspan": 2}],
            [{"type": "scatter"}, None],
            [{"type": "scatter", "colspan": 2}, None]
        ],
        subplot_titles=(
            f"📊 Data: {name}", 
            "Toppvisning (Vannlinjer)", 
            "Frontvisning (Spant)", 
            "Sidevisning (Profil)"
        ),
        horizontal_spacing=0.10,
        vertical_spacing=0.10
    )
    
    if mesh_data is None:
        return fig
        
    # --- 1. RAD 1, KOLONNE 1: RENT DATA-FELT ---
    battery_text = f"Batteriboks: {'✅ OK' if props['fits_battery'] else '❌ KRÆSJ'}" if is_main_hull else "Batteriboks: N/A"
    
    text_info = (
        f"<b>Oppdrift:</b> {props['displacement']:.1f} kg<br>"
        f"<b>Våt flate:</b> {props['wsa']:.2f} m²<br>"
        f"<b>Friksjon:</b> {R_f:.2f} N<br>"
        f"<b>{battery_text}</b>"
    )
    
    fig.add_annotation(
        dict(x=0.05, y=0.5, showarrow=False, text=text_info, 
             font=dict(size=14, color="black"),
             xref="x domain", yref="y domain", align="left")
    )
    
    # Fjern absolutt alt av akser, linjer og rammer fra dataruten så den blir helt hvit
    fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False, showline=False, row=1, col=1)
    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False, showline=False, row=1, col=1)

    num_points = len(mesh_data[0]['Points'])
    
    # --- 2. RAD 1 & 2, KOLONNE 2: TOPPVISNING (X vs Y) ---
    for p_idx in range(num_points):
        x_lines = [st_d['X'] for st_d in mesh_data]
        y_lines = [st_d['Points'][p_idx][0] for st_d in mesh_data]
        fig.add_trace(go.Scatter(x=x_lines, y=y_lines, mode='lines', line=dict(color='blue', width=1), showlegend=False), row=1, col=2)
        fig.add_trace(go.Scatter(x=x_lines, y=[-y for y in y_lines], mode='lines', line=dict(color='blue', width=1), showlegend=False), row=1, col=2)

    # --- 3. RAD 2, KOLONNE 1: FRONTVISNING (Y vs Z) ---
    for st_d in mesh_data:
        y_points = [p[0] for p in st_d['Points']]
        z_points = [p[1] for p in st_d['Points']]
        fig.add_trace(go.Scatter(x=y_points, y=z_points, mode='lines', line=dict(color='red', width=1), showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=[-y for y in y_points], y=z_points, mode='lines', line=dict(color='red', width=1), showlegend=False), row=2, col=1)
        
    # --- 4. RAD 3, KOLONNE 1 & 2: SIDEVISNING (X vs Z) ---
    for p_idx in range(num_points):
        x_lines = [st_d['X'] for st_d in mesh_data]
        z_lines = [st_d['Points'][p_idx][1] for st_d in mesh_data]
        fig.add_trace(go.Scatter(x=x_lines, y=z_lines, mode='lines', line=dict(color='green', width=1), showlegend=False), row=3, col=1)
        
    # ==============================================================================
    # 📐 MATEMATISK SYNKRONISERING AV AKSER OG PROPORSJONER
    # ==============================================================================
    # Sidevisningen (Axe 4) er master for fysiske proporsjoner (1:1 meter-skala på skjermen)
    fig.update_yaxes(scaleanchor="x4", scaleratio=1, row=3, col=1)
    
    # KRAV 1: Samme lengde (X) i Top og Side
    fig.update_xaxes(scaleanchor="x4", row=1, col=2)  # Låser Topp-X til Side-X
    
    # KRAV 2: Samme høyde/dybde (Z) i Side og Front
    fig.update_yaxes(scaleanchor="y4", row=2, col=1)  # Låser Front-Z (høyde) til Side-Z
    
    # KRAV 3: Samme bredde (Y) i Front og Topp
    fig.update_xaxes(scaleanchor="y2", row=2, col=1)  # Låser Front-X (bredde) til Topp-Y (bredde)

    # Forbann rutenett-skalering til å respektere låsingen vår
    fig.update_layout(height=650, template="plotly_white", margin=dict(l=15, r=15, t=40, b=15))
    
    return fig


# ==============================================================================
# 📊 2. GEOMETRISK ANALYSE (3 KOLONNER SIDE OM SIDE)
# ==============================================================================
st.header("📐 2. Geometrisk Analyse (3 x Skrogmatriser)")

skrog_col1, skrog_col2, skrog_col3 = st.columns(3)

with skrog_col1:
    st.subheader("Hovedskrog (Senter)")
    fig_main = create_vessel_3x2_subplot(hull_mesh_main, prop_main, R_f_main, "Hovedskrog", is_main_hull=True)
    st.plotly_chart(fig_main, use_container_width=True)

with skrog_col2:
    st.subheader("Sideskrog 1 (Styrbord)")
    if num_hulls > 1:
        fig_side1 = create_vessel_3x2_subplot(hull_mesh_side, prop_side, R_f_side, "Sideskrog STB", is_main_hull=False)
        st.plotly_chart(fig_side1, use_container_width=True)
    else:
        st.info("Deaktivert (Monohull)")

with skrog_col3:
    st.subheader("Sideskrog 2 (Babord)")
    if num_hulls > 2:
        fig_side2 = create_vessel_3x2_subplot(hull_mesh_side, prop_side, R_f_side, "Sideskrog BB", is_main_hull=False)
        st.plotly_chart(fig_side2, use_container_width=True)
    elif num_hulls == 2:
        st.info("Deaktivert (Katamaran)")
    else:
        st.info("Deaktivert (Monohull)")

st.markdown("---")


# ==============================================================================
# 🌐 3. GLOBAL VISNING (KUN TOPPVISNING STRUKTURERT)
# ==============================================================================
st.header("🌐 3. Global Visning (Hele Fartøyet i Posisjon)")

fig_global_top = go.Figure()

# 1. Plot hovedskrog i senter (Y=0)
x_m = [st_d['X'] for st_d in hull_mesh_main]
y_m = [st_d['Points'][-1][0] for st_d in hull_mesh_main]
fig_global_top.add_trace(go.Scatter(x=x_m, y=y_m, mode='lines', line=dict(color='blue', width=2), name="Hovedskrog"))
fig_global_top.add_trace(go.Scatter(x=x_m, y=[-y for y in y_m], mode='lines', line=dict(color='blue', width=2), showlegend=False))

# 2. Plot sideskrog med separation og stagger
if num_hulls > 1:
    x_s = [st_d['X'] + stagger_test for st_d in hull_mesh_side]
    y_s_kontur = [st_d['Points'][-1][0] for st_d in hull_mesh_side]
    
    # Styrbord sideskrog
    fig_global_top.add_trace(go.Scatter(x=x_s, y=[y + separation_test for y in y_s_kontur], mode='lines', line=dict(color='purple', width=1.5), name="Sideskrog STB"))
    fig_global_top.add_trace(go.Scatter(x=x_s, y=[-y + separation_test for y in y_s_kontur], mode='lines', line=dict(color='purple', width=1.5), showlegend=False))
    
    if num_hulls > 2:
        # Babord sideskrog
        fig_global_top.add_trace(go.Scatter(x=x_s, y=[y - separation_test for y in y_s_kontur], mode='lines', line=dict(color='purple', width=1.5), name="Sideskrog BB"))
        fig_global_top.add_trace(go.Scatter(x=x_s, y=[-y - separation_test for y in y_s_kontur], mode='lines', line=dict(color='purple', width=1.5), showlegend=False))
        
fig_global_top.update_layout(
    title="Overordnet Linje: Toppvisning (X vs Y)",
    template="plotly_white", 
    height=380,
    margin=dict(l=40, r=40, t=40, b=40)
)
fig_global_top.update_yaxes(scaleanchor="x", scaleratio=1)
st.plotly_chart(fig_global_top, use_container_width=True)

st.markdown("---")


# ==============================================================================
# ⚙️ 4. OPTIMALISERINGSKONTROLL & KJØRESTATUS (HELT I BUNNEN)
# ==============================================================================
st.header("⚙️ 4. Optimaliseringskontroll & Kjørestatus")

if 'optimizing' not in st.session_state:
    st.session_state.optimizing = False

opt_col1, opt_col2 = st.columns([1, 3])

with opt_col1:
    st.subheader("Kontroll")
    if not st.session_state.optimizing:
        if st.button("🚀 Start Optimalisering", type="primary", use_container_width=True):
            st.session_state.optimizing = True
            st.rerun()
    else:
        if st.button("🛑 STOPP Optimalisering", type="secondary", use_container_width=True):
            st.session_state.optimizing = False
            st.rerun()
            
    if st.session_state.optimizing:
        st.success("Kjører aktive søkesykluser...")
    else:
        st.info("Status: Klar")

with opt_col2:
    st.subheader("Live Telemetri")
    tele_col1, tele_col2, tele_col3 = st.columns(3)
    with tele_col1:
        st.metric(label="Total Motstand (R_tot)", value=f"{R_total_global:.2f} N")
    with tele_col2:
        st.write("**Mottatt Fordeling:**")
        st.write(f"🌊 Bølgemotstand global: {R_w_global:.2f} N")
        st.write(f"🧼 Viskøs hovedskrog: {R_f_main:.2f} N")
        if num_hulls > 1:
            st.write(f"🧼 Viskøs sideskrog (x{num_hulls-1}): {R_f_side * (num_hulls-1):.2f} N")
    with tele_col3:
        st.metric(label="Antall Sykluser", value="1 (Manuell modus)" if not st.session_state.optimizing else "Kjører...")

    st.markdown("---")
    st.subheader("🏆 Topp 10 Beste Skrogkonfigurasjoner")
    top_10_df = pd.DataFrame(columns=['Rank', 'Total Motstand [N]', 'L_Hoved [m]', 'L_Side [m]', 'Separasjon [m]', 'Stagger [m]', 'Batterisjekk'])
    st.dataframe(top_10_df, use_container_width=True, hide_index=True)
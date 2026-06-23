# main.py
import streamlit as st
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Importer geometrifunksjonene og hydrodynamikken
from geometry.geometry_base import generate_complete_hull
from core.hydrodynamics import get_total_wave_resistance, calculate_viscous_resistance

st.set_page_config(layout="wide")

# --- 📊 SIDEVINDU: RESULTATER OG DRIFTSPARAMETERE ---
st.sidebar.title("📊 Analyse & Hydrodynamikk")

# Hastighet og fartøytype
speed_knot = st.sidebar.slider("ASV Hastighet (Knop)", 1.0, 15.0, 6.0, 0.5)
speed_ms = speed_knot * 0.5144

hull_type = st.sidebar.selectbox("Fartøykonfigurasjon", ["Monohull", "Katamaran", "Trimaran"])

# Vis separasjonssmolder kun hvis det er flerskrog
if hull_type in ["Katamaran", "Trimaran"]:
    separation = st.sidebar.slider("Skrogseparasjon (Senter-Senter) [m]", 0.2, 2.0, 0.6)
else:
    separation = 0.0

st.sidebar.markdown("---")
# Container for live-resultater som oppdateres lenger ned
result_container = st.sidebar.empty()


# --- 🎛️ HOVEDOMRÅDE: 2x2 MODULÆRT DESIGN ---
st.title("ASV Konfigurator & Tynnskrog-analysator 🚢")

row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

# --- RAD 1, KOLONNE 1: HOVEDSKROG PARAMETERE ---
with row1_col1:
    st.subheader("📐 Modul 1: Hovedskrog Dimensjoner")
    L_m = st.number_input("Lengde (L) [m]", 0.5, 5.0, 2.0, 0.1, key="L_m")
    B_m = st.number_input("Maks Bredde (B_max) [m]", 0.1, 1.5, 0.3, 0.05, key="B_m")
    T_m = st.number_input("Dypgående (T) [m]", 0.05, 0.5, 0.15, 0.01, key="T_m")
    
    st.markdown("**Kjøl-kontroll (Øks-form)**")
    x1_k_m = st.slider("x1_k (Bunnlengde)", 0.0, 1.0, 0.5, key="x1_k_m")
    z1_k_m = st.slider("z1_k (Bunnhøyde)", 0.0, 1.0, 0.0, key="z1_k_m")
    x2_k_m = st.slider("x2_k (Bauglengde)", 0.0, 1.0, 0.9, key="x2_k_m")
    z2_k_m = st.slider("z2_k (Baughøyde)", 0.0, 1.0, 0.0, key="z2_k_m")

# --- RAD 1, KOLONNE 2: SIDESKROG PARAMETERE ---
with row1_col2:
    st.subheader("📐 Modul 2: Sideskrog Dimensjoner")
    if hull_type == "Monohull":
        st.info("Sideskrog er deaktivert i Monohull-modus.")
        L_s, B_s, T_s = 0.0, 0.0, 0.0
        x1_k_s, z1_k_s, x2_k_s, z2_k_s = 0.5, 0.0, 0.5, 0.2
    else:
        L_s = st.number_input("Lengde (L) [m]", 0.5, 5.0, 1.2, 0.1, key="L_s")
        B_s = st.number_input("Maks Bredde (B_max) [m]", 0.05, 1.0, 0.12, 0.02, key="B_s")
        T_s = st.number_input("Dypgående (T) [m]", 0.02, 0.5, 0.08, 0.01, key="T_s")
        
        st.markdown("**Kjøl-kontroll (Sideskrog)**")
        x1_k_s = st.slider("x1_k (Bunnlengde)", 0.0, 1.0, 0.5, key="x1_k_s")
        z1_k_s = st.slider("z1_k (Bunnhøyde)", 0.0, 1.0, 0.0, key="z1_k_s")
        x2_k_s = st.slider("x2_k (Bauglengde)", 0.0, 1.0, 0.5, key="x2_k_s")
        z2_k_s = st.slider("z2_k (Baughøyde)", 0.0, 1.0, 0.2, key="z2_k_s")

# --- PAKK KONFIGURASJONER ---
config_main = {
    'L': L_m, 'B_max': B_m, 'T': T_m,
    'x1_w': 0.5, 'y1_w': 1.0, 'x2_w': 0.5, 'y2_w': 0.5, # Standard vannlinje
    'x1_k': x1_k_m, 'z1_k': z1_k_m, 'x2_k': x2_k_m, 'z2_k': z2_k_m,
    'y1_s': 0.5, 'z1_s': 0.0, 'y2_s': 1.0, 'z2_s': 0.5  # Standard spant
}

config_side = {
    'L': L_s, 'B_max': B_s, 'T': T_s,
    'x1_w': 0.5, 'y1_w': 1.0, 'x2_w': 0.5, 'y2_w': 0.5,
    'x1_k': x1_k_s, 'z1_k': z1_k_s, 'x2_k': x2_k_s, 'z2_k': z2_k_s,
    'y1_s': 0.5, 'z1_s': 0.0, 'y2_s': 1.0, 'z2_s': 0.5
}

# --- GENERER 3D GEOMETRI (Med 40 stasjoner for høy oppløsning) ---
hull_mesh_main = generate_complete_hull(config_main, num_stations=40)
hull_mesh_side = generate_complete_hull(config_side, num_stations=40) if hull_type != "Monohull" else None

# --- BEREGN HYDRODYNAMISK MOTSTAND LIVE ---
hydro_config = {'type': hull_type.lower(), 'separation': separation}

# 1. Beregn for hovedskrog
R_w_main = get_total_wave_resistance(hull_mesh_main, speed_ms, hydro_config)
R_f_main = calculate_viscous_resistance(hull_mesh_main, speed_ms)

# 2. Legg til bidrag fra sideskrog om nødvendig
R_w_side, R_f_side = 0.0, 0.0
if hull_type != "Monohull":
    # Sideskrogene opplever ren singel-motstand i denne forenklingen, 
    # mens interferensen ligger i hovedskrog-beregningen over
    R_w_side = get_total_wave_resistance(hull_mesh_side, speed_ms, {'type': 'mono', 'separation': 0.0}) * 2
    R_f_side = calculate_viscous_resistance(hull_mesh_side, speed_ms) * 2

R_total = R_w_main + R_f_main + R_w_side + R_f_side

# --- OPPDATER RESULTATPANELET I SIDEBAR ---
with result_container.container():
    st.metric(label="Total Motstand (R_tot)", value=f"{R_total:.2f} N")
    st.subheader("Komponentoppdeling:")
    st.write(f"🌊 Bølgemotstand (Hoved): {R_w_main:.2f} N")
    st.write(f"🧼 Friksjonsmotstand (Hoved): {R_f_main:.2f} N")
    if hull_type != "Monohull":
        st.write(f"🌊 Bølgemotstand (Side x2): {R_w_side:.2f} N")
        st.write(f"🧼 Friksjonsmotstand (Side x2): {R_f_side:.2f} N")
    st.caption(f"Froude-nummer (Hoved): {speed_ms / (9.81 * L_m)**0.5:.3f}")


# --- RAD 2: DATAPLOT (VISUALISERING AV NETTVERKET) ---
def create_plotly_subplot(mesh_data, title):
    fig = make_subplots(rows=1, cols=3, subplot_titles=("Topp", "Side", "Front"))
    if mesh_data is None:
        return fig
    num_pts = len(mesh_data[0]['Points'])
    for p_idx in range(num_pts):
        x_l = [st_d['X'] for st_d in mesh_data]
        y_l = [st_d['Points'][p_idx][0] for st_d in mesh_data]
        z_l = [st_d['Points'][p_idx][1] for st_d in mesh_data]
        fig.add_trace(go.Scatter(x=x_l, y=y_l, mode='lines', line=dict(color='blue', width=1), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=x_l, y=[-y for y in y_l], mode='lines', line=dict(color='blue', width=1), showlegend=False), row=1, col=1)
        fig.add_trace(go.Scatter(x=x_l, y=z_l, mode='lines', line=dict(color='green', width=1), showlegend=False), row=1, col=2)
    for st_d in mesh_data:
        y_p = [p[0] for p in st_d['Points']]
        z_p = [p[1] for p in st_d['Points']]
        fig.add_trace(go.Scatter(x=y_p, y=z_p, mode='lines', line=dict(color='red', width=1), showlegend=False), row=1, col=3)
        fig.add_trace(go.Scatter(x=[-y for y in y_p], y=z_p, mode='lines', line=dict(color='red', width=1), showlegend=False), row=1, col=3)
    fig.update_layout(height=350, template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig

with row2_col1:
    st.plotly_chart(create_plotly_subplot(hull_mesh_main, "Hovedskrog"), use_container_width=True)

with row2_col2:
    if hull_type != "Monohull":
        st.plotly_chart(create_plotly_subplot(hull_mesh_side, "Sideskrog"), use_container_width=True)
    else:
        st.write("Ingen sideskrog å vise.")
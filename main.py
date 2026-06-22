# main.py
import streamlit as st
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from geometry.geometry_base import generate_complete_hull

st.set_page_config(layout="wide")
st.title("ASV Skrogdesign & Optimalisering 🚢")

# --- SIDEBAR: INPUT PARAMETERE ---
st.sidebar.header("Hoveddimensjoner")
L = st.sidebar.slider("Lengde (L)", 0.5, 5.0, 2.0, 0.1)
B_max = st.sidebar.slider("Bredde (B_max)", 0.1, 1.5, 0.4, 0.05)
T = st.sidebar.slider("Dypgående (T)", 0.05, 0.5, 0.15, 0.01)

st.sidebar.header("Bézier Kontrollfaktorer")
st.sidebar.subheader("Vannlinje (Ovenfra)")
x1_w = st.sidebar.slider("x1_w (Skulder posisjon)", 0.0, 1.0, 0.5)
y1_w = st.sidebar.slider("y1_w (Skulder bredde)", 0.0, 1.0, 1.0)
x2_w = st.sidebar.slider("x2_w (Baug form X)", 0.0, 1.0, 0.5)
y2_w = st.sidebar.slider("y2_w (Baug form Y)", 0.0, 1.0, 0.5)

# Pakk parametere inn i en konfigurasjon
config = {
    'L': L, 'B_max': B_max, 'T': T,
    'x1_w': x1_w, 'y1_w': y1_w, 'x2_w': x2_w, 'y2_w': y2_w,
    'z1_k': 0.0, 'z2_k': 0.2, # Fastlåst inntil videre
    'y1_s': 0.5, 'z1_s': 0.0, 'y2_s': 1.0, 'z2_s': 0.5 # Standard spant
}

# Lagre gjeldende til JSON (for integrasjon med de andre mappene dine senere)
if st.sidebar.button("Lagre til project_config.json"):
    with open('project_config.json', 'w') as f:
        json.dump(config, f, indent=4)
    st.sidebar.success("Konfigurasjon lagret!")

# --- HOVEDOMRÅDE: VISUALISERING ---
hull_mesh = generate_complete_hull(config)

fig = make_subplots(rows=1, cols=3, subplot_titles=("Topp (Vannlinjer)", "Side (Profil)", "Front (Spant)"))

num_points = len(hull_mesh[0]['Points'])
# Toppvisning
for p_idx in range(num_points):
    x_lines = [st['X'] for st in hull_mesh]
    y_lines = [st['Points'][p_idx][0] for st in hull_mesh]
    fig.add_trace(go.Scatter(x=x_lines, y=y_lines, mode='lines', line=dict(color='blue', width=1), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=x_lines, y=[-y for y in y_lines], mode='lines', line=dict(color='blue', width=1), showlegend=False), row=1, col=1)

# Sidevisning
for p_idx in range(num_points):
    x_lines = [st['X'] for st in hull_mesh]
    z_lines = [st['Points'][p_idx][1] for st in hull_mesh]
    fig.add_trace(go.Scatter(x=x_lines, y=z_lines, mode='lines', line=dict(color='green', width=1), showlegend=False), row=1, col=2)

# Frontvisning
for st_data in hull_mesh:
    y_points = [p[0] for p in st_data['Points']]
    z_points = [p[1] for p in st_data['Points']]
    fig.add_trace(go.Scatter(x=y_points, y=z_points, mode='lines', line=dict(color='red', width=1), showlegend=False), row=1, col=3)
    fig.add_trace(go.Scatter(x=[-y for y in y_points], y=z_points, mode='lines', line=dict(color='red', width=1), showlegend=False), row=1, col=3)

fig.update_layout(height=600, template="plotly_white")
fig.update_yaxes(scaleanchor="x", scaleratio=1)

st.plotly_chart(fig, use_container_width=True)
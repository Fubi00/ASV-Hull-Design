# main.py
import streamlit as st
import json
# ... (importer dine geometrifunksjoner her)
from core.hydrodynamics import calculate_michell_resistance, calculate_viscous_resistance

st.set_page_config(layout="wide")

# --- SIDEVINDU: MOTSTAND, INTERFERENS OG REVISJONSDATA ---
st.sidebar.title("📊 Analyse & Resultater")
speed_knot = st.sidebar.slider("ASV Hastighet (Knop)", 1.0, 15.0, 5.0, 0.5)
speed_ms = speed_knot * 0.5144

# Flerskrogskonfigurasjon
is_mono = st.sidebar.checkbox("Monohull (Enkeltskrog)", value=False)
separation = st.sidebar.slider("Skrogseparasjon (Senter-Senter) [m]", 0.2, 2.0, 0.6) if not is_mono else 0.0

st.sidebar.markdown("---")
# Her vil vi spytte ut resultatene live (vi beregner dem lenger ned i koden)
res_box = st.sidebar.empty()

# --- HOVEDOMRÅDE: 2x2 MODULÆRT DESIGN ---
st.title("ASV Konfigurator")

# Topp-rad i 2x2
row1_col1, row1_col2 = st.columns(2)
# Bunn-rad i 2x2
row2_col1, row2_col2 = st.columns(2)

with row1_col1:
    st.subheader("📐 Modul 1: Side x Front (Hovedskrog)")
    L_m = st.number_input("Lengde [m]", 0.5, 5.0, 2.0, 0.1, key="L_m")
    B_m = st.number_input("Bredde [m]", 0.1, 1.5, 0.4, 0.05, key="B_m")
    T_m = st.number_input("Dypgående [m]", 0.05, 0.5, 0.15, 0.01, key="T_m")

with row1_col2:
    st.subheader("📐 Modul 2: Side x Front (Sideskrog)")
    if is_mono:
        st.write("Skrudd av for Monohull")
        config_side = {'L': 0, 'B_max': 0, 'T': 0, 'x1_w':0.5, 'y1_w':1.0, 'x2_w':0.5, 'y2_w':0.5, 'z1_k':0, 'z2_k':0.2, 'y1_s':0.5, 'z1_s':0, 'y2_s':1, 'z2_s':0.5}
    else:
        L_s = st.number_input("Lengde [m]", 0.5, 5.0, 1.2, 0.1, key="L_s")
        B_s = st.number_input("Bredde [m]", 0.05, 1.0, 0.15, 0.05, key="B_s")
        T_s = st.number_input("Dypgående [m]", 0.02, 0.5, 0.08, 0.01, key="T_s")

# Definer fulle konfigurasjoner
config_main = {'L': L_m, 'B_max': B_m, 'T': T_m, 'x1_w':0.5, 'y1_w':1.0, 'x2_w':0.5, 'y2_w':0.5, 'z1_k':0, 'z2_k':0.2, 'y1_s':0.5, 'z1_s':0, 'y2_s':1, 'z2_s':0.5}
if not is_mono:
    config_side = {'L': L_s, 'B_max': B_s, 'T': T_s, 'x1_w':0.5, 'y1_w':1.0, 'x2_w':0.5, 'y2_w':0.5, 'z1_k':0, 'z2_k':0.2, 'y1_s':0.5, 'z1_s':0, 'y2_s':1, 'z2_s':0.5}

# Generer geometri
hull_main = generate_complete_hull(config_main)
hull_side = generate_complete_hull(config_side) if not is_mono else None

# --- BEREGN HYDRODYNAMIKK LIVE ---
R_w_main = calculate_michell_resistance(hull_main, speed_ms, separation, is_multihull=(not is_mono))
R_f_main = calculate_viscous_resistance(hull_main, speed_ms)
R_total = R_w_main + R_f_main

if not is_mono:
    R_w_side = calculate_michell_resistance(hull_side, speed_ms) # Ren singel motstand for amiene
    R_f_side = calculate_viscous_resistance(hull_side, speed_ms) * 2
    R_total += (R_w_side * 2) + R_f_side

# Oppdater sidepanelet med reelle tall
with res_box.container():
    st.metric(label="Total Motstand (R_total)", value=f"{R_total:.2f} N")
    st.write(f"🌊 Bølgemotstand: {R_w_main:.2f} N")
    st.write(f"🧼 Viskøs motstand: {R_f_main:.2f} N")
    st.caption("Iterasjons-sykluser: 1 (Manuell modus)")

# --- VIS GRAFIKK I DE NEDRE MODULENE ---
with row2_col1:
    st.subheader("📊 Dataplot: Hovedskrog Linjer")
    # Her setter du inn Plotly-koden (kun for hull_main) som vi brukte tidligere
    # fig_main = ...
    # st.plotly_chart(fig_main)

with row2_col2:
    st.subheader("📊 Dataplot: Sideskrog Linjer")
    if not is_mono:
        # Her setter du inn Plotly-koden (kun for hull_side)
        pass
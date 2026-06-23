# main.py

def create_2x2_subplot(mesh_data):
    """Genererer Data, Topp, Side og Front direkt fra en ekte skrogmatrise"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("📊 Beregnet Data (Se under)", "Toppvisning (Vannlinjer)", "Sidevisning (Profil)", "Frontvisning (Spant)"),
        horizontal_spacing=0.12,
        vertical_spacing=0.15
    )
    
    if mesh_data is None:
        return fig
        
    num_points = len(mesh_data[0]['Points'])
    
    # RAD 1, KOLONNE 1: SKAL VÆRE TOM i Plotly (Beregnet data skrives her via Streamlit-tekst)

    # 1. RAD 1, KOLONNE 2: TOPPVISNING (X vs Y) - NÅ FLYTTET HIT
    for p_idx in range(num_points):
        x_lines = [station['X'] for station in mesh_data]
        y_lines = [station['Points'][p_idx][0] for station in mesh_data]
        fig.add_trace(go.Scatter(x=x_lines, y=y_lines, mode='lines', line=dict(color='blue', width=1), showlegend=False), row=1, col=2)
        fig.add_trace(go.Scatter(x=x_lines, y=[-y for y in y_lines], mode='lines', line=dict(color='blue', width=1), showlegend=False), row=1, col=2)

    # 2. RAD 2, KOLONNE 1: SIDEVISNING (X vs Z)
    for p_idx in range(num_points):
        x_lines = [station['X'] for station in mesh_data]
        z_lines = [station['Points'][p_idx][1] for station in mesh_data]
        fig.add_trace(go.Scatter(x=x_lines, y=z_lines, mode='lines', line=dict(color='green', width=1), showlegend=False), row=2, col=1)
        
    # 3. RAD 2, KOLONNE 2: FRONTVISNING (Y vs Z)
    for station in mesh_data:
        y_points = [p[0] for p in station['Points']]
        z_points = [p[1] for p in station['Points']]
        fig.add_trace(go.Scatter(x=y_points, y=z_points, mode='lines', line=dict(color='red', width=1), showlegend=False), row=2, col=2)
        fig.add_trace(go.Scatter(x=[-y for y in y_points], y=z_points, mode='lines', line=dict(color='red', width=1), showlegend=False), row=2, col=2)
        
    fig.update_layout(height=450, template="plotly white", margin=dict(l=10, r=10, t=30, b=10))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, row=1, col=2)
    fig.update_yaxes(scaleanchor="x", scaleratio=1, row=2, col=1)
    fig.update_yaxes(scaleanchor="x", scaleratio=1, row=2, col=2)
    return fig


# ==============================================================================
# 📊 PRESENTASJON I KOLONNER (MED DATA ØVERST TIL VENSTRE)
# ==============================================================================
st.header("📐 2. Geometrisk Analyse (3 x 2x2 Skrogmatriser)")

skrog_col1, skrog_col2, skrog_col3 = st.columns(3)

# --- MATRISE 1: HOVEDSKROG ---
with skrog_col1:
    st.subheader("Hovedskrog (Senter)")
    
    # For å fylle Rad 1, Kolonne 1 (Data) visuelt, legger vi teksten her
    st.markdown("#### 📊 Data Hovedskrog")
    # st.write(f"Oppdrift: {vol_main * 1025:.2f} kg")
    # st.write(f"Bølgemotstand (Rw): {R_w_main:.2f} N")
    st.caption("Beregnede data vil vises her, øverst til venstre i matrisen.")
    
    # Plotly-diagrammet (hvor Topp nå er flyttet til øverst til høyre)
    # hull_mesh_main = generate_complete_hull(config_main, num_stations=40)
    # fig_main = create_2x2_subplot(hull_mesh_main)
    # st.plotly_chart(fig_main, use_container_width=True)
    st.caption("Matrise-plottene (Topp høyre, Side nede venstre, Front nede høyre)")

# --- MATRISE 2: SIDESKROG 1 (STYRBORD) ---
with skrog_col2:
    st.subheader("Sideskrog 1 (Styrbord)")
    if num_hulls > 1:
        st.markdown("#### 📊 Data Sideskrog 1")
        # st.write(f"Oppdrift: {vol_side1 * 1025:.2f} kg")
        
        # hull_mesh_side1 = generate_complete_hull(config_side1, num_stations=40)
        # fig_side1 = create_2x2_subplot(hull_mesh_side1)
        # st.plotly_chart(fig_side1, use_container_width=True)
    else:
        st.info("Deaktivert (Monohull)")

# --- MATRISE 3: SIDESKROG 2 (BABORD) ---
with skrog_col3:
    st.subheader("Sideskrog 2 (Babord)")
    if num_hulls > 2:
        st.markdown("#### 📊 Data Sideskrog 2")
        # st.write(f"Oppdrift: {vol_side2 * 1025:.2f} kg")
        
        # hull_mesh_side2 = generate_complete_hull(config_side2, num_stations=40)
        # fig_side2 = create_2x2_subplot(hull_mesh_side2)
        # st.plotly_chart(fig_side2, use_container_width=True)
    else:
        st.info("Deaktivert (Monohull/Katamaran)")
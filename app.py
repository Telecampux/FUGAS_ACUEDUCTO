import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

# Configuración de la página (Debe ser la primera instrucción de Streamlit)
st.set_page_config(
    page_title="IANC H2O Auditoría",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. INYECCIÓN DE METADATOS PWA (Opcional pero recomendado para el Manifest)
def add_pwa_headers():
    st.markdown(
        f"""
        <link rel="manifest" href="./static/manifest.json">
        <meta name="theme-color" content="#000000">
        """,
        unsafe_allow_html=True
    )

# 2. CARGA DE ESTILOS CSS PERSONALIZADOS
def local_css():
    st.markdown("""
        <style>
        .main { background-color: #f5f7f9; }
        .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        </style>
        """, unsafe_allow_html=True)

# 3. LÓGICA DE NAVEGACIÓN (Sidebar)
def main():
    add_pwa_headers()
    local_css()
    
    st.sidebar.image("https://via.placeholder.com/150", caption="IANC H2O Pro") # Reemplazar con logo real
    st.sidebar.title("Navegación")
    
    menu = ["Dashboard", "Simulación", "Mapa de Auditoría", "Reportes"]
    choice = st.sidebar.selectbox("Seleccione un módulo", menu)

    st.title(f"📊 Módulo: {choice}")
    st.divider()

    # 4. RUTEO DE MÓDULOS
    if choice == "Dashboard":
        render_dashboard()
    elif choice == "Simulación":
        render_simulation()
    elif choice == "Mapa de Auditoría":
        render_map()
    elif choice == "Reportes":
        st.info("Módulo de reportes en desarrollo.")

# --- DEFINICIÓN DE INTERFACES POR MÓDULO ---

def render_dashboard():
    col1, col2, col3 = st.columns(3)
    col1.metric("Eficiencia Hídrica", "85%", "+2%")
    col2.metric("Consumo Estimado", "1,200 m³", "-50 m³")
    col3.metric("Puntos Críticos", "4", "Estable")
    
    st.subheader("Resumen de Datos Recientes")
    # Aquí podrías cargar un dataframe de ejemplo o real
    df_placeholder = pd.DataFrame({'Mes': ['Ene', 'Feb', 'Mar'], 'Consumo': [400, 420, 380]})
    st.line_chart(df_placeholder.set_index('Mes'))

def render_simulation():
    st.subheader("Parámetros de Simulación")
    with st.form("sim_form"):
        flujo = st.slider("Flujo de entrada (L/s)", 0, 100, 50)
        presion = st.number_input("Presión de red (bar)", 1.0, 10.0, 3.5)
        submit = st.form_submit_button("Ejecutar Simulación")
        
        if submit:
            with st.spinner("Procesando modelos físicos..."):
                # Aquí llamarías a una función en ianc_h2o_pro/core/calculos.py
                st.success(f"Simulación completada para {flujo} L/s y {presion} bar.")

def render_map():
    st.subheader("Geolocalización de Auditoría")
    # Coordenadas iniciales (ejemplo)
    m = folium.Map(location=[4.6097, -74.0817], zoom_start=12)
    folium.Marker([4.6097, -74.0817], popup="Punto de Control Principal").add_to(m)
    st_folium(m, width=700, height=450)

if __name__ == "__main__":
    main()

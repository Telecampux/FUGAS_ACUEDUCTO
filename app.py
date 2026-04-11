import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Tablero IANC H2O", layout="wide")

st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader("Ing. Adolfo Barrera Vargas - Gestión de Sensores")

uploaded_file = st.file_uploader("Cargar Archivo Maestro (.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        df.columns = df.columns.str.strip().str.lower()
        
        # Asegurar datos numéricos
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df = df.dropna(subset=['latitud', 'longitud'])

        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Sensores", len(df))
        m2.metric("Municipio", str(df['municipio'].iloc[0]).capitalize())
        m3.metric("Presión Promedio", f"{df['presion_psi'].mean():.2f} PSI")

        st.markdown("---")

        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("### 📊 Detalle de Campo")
            st.table(df[['id_sensor', 'presion_psi', 'material', 'latitud', 'longitud']])

        with col2:
            st.write("### 🗺️ Mapa de Ubicación")
            # Centro en Villeta basado en sus datos
            centro_lat = df['latitud'].mean()
            centro_lon = df['longitud'].mean()
            
            # Crear mapa con parámetros de carga rápida
            m = folium.Map(
                location=[centro_lat, centro_lon], 
                zoom_start=16, 
                tiles="OpenStreetMap"
            )

            for _, row in df.iterrows():
                folium.Marker(
                    location=[row['latitud'], row['longitud']],
                    popup=f"Sensor: {row['id_sensor']}",
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)

            # ESTO ES LO MÁS IMPORTANTE: 
            # Forzamos el renderizado sin objetos de retorno para evitar bucles.
            st_folium(m, width=500, height=400, key="mapa_final", returned_objects=[])

    except Exception as e:
        st.error(f"Error en visualización: {e}")

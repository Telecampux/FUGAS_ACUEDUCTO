import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Configuración de página
st.set_page_config(page_title="Tablero IANC H2O", layout="wide")

st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader("Ing. Adolfo Barrera Vargas - Gestión de Sensores")

uploaded_file = st.file_uploader("Cargar Archivo Maestro (.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        # 1. Procesamiento de datos
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        df.columns = df.columns.str.strip().str.lower()
        
        # Asegurar que las coordenadas sean números
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df = df.dropna(subset=['latitud', 'longitud'])

        # 2. Métricas (Lo que ya le funciona)
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Sensores", len(df))
        col_m2.metric("Municipio", str(df['municipio'].iloc[0]).capitalize())
        col_m3.metric("Presión Promedio", f"{df['presion_psi'].mean():.2f} PSI")

        st.markdown("---")

        # 3. Visualización Forzada
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("### 📊 Detalle de Campo")
            # st.table es infalible, no se queda en blanco
            st.table(df[['id_sensor', 'presion_psi', 'material', 'latitud', 'longitud']].head(10))

        with col2:
            st.write("### 🗺️ Mapa de Ubicación")
            centro_lat = df['latitud'].mean()
            centro_lon = df['longitud'].mean()
            
            m = folium.Map(location=[centro_lat, centro_lon], zoom_start=15)

            for _, row in df.iterrows():
                folium.Marker(
                    location=[row['latitud'], row['longitud']],
                    popup=f"Sensor: {row['id_sensor']}",
                    tooltip=f"Presión: {row['presion_psi']} PSI"
                ).add_to(m)

            # Renderizado de alta compatibilidad con ID único
            st_folium(m, width=550, height=400, key="mapa_definitivo")

    except Exception as e:
        st.error(f"Error detectado: {e}")
else:
    st.info("Cargue el archivo CSV para activar el tablero.")

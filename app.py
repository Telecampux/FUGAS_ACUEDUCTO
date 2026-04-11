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
        # 1. Procesamiento de datos (Ya validado)
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        df.columns = df.columns.str.strip().str.lower()
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df = df.dropna(subset=['latitud', 'longitud'])

        # 2. Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Sensores", len(df))
        m2.metric("Municipio", str(df['municipio'].iloc[0]).capitalize())
        m3.metric("Presión Promedio", f"{df['presion_psi'].mean():.2f} PSI")

        st.divider()

        col1, col2 = st.columns([1, 1.2]) # Columna del mapa un poco más ancha
        
        with col1:
            st.write("### 📊 Detalle de Campo")
            st.table(df[['id_sensor', 'presion_psi', 'material', 'latitud', 'longitud']])

        with col2:
            st.write("### 🗺️ Mapa de Ubicación")
            # Centro del mapa en Villeta
            lat_centro = df['latitud'].mean()
            lon_centro = df['longitud'].mean()
            
            # Crear mapa base
            m = folium.Map(location=[lat_centro, lon_centro], zoom_start=16)

            # Agregar marcadores
            for _, row in df.iterrows():
                folium.Marker(
                    [row['latitud'], row['longitud']],
                    popup=f"Sensor: {row['id_sensor']}",
                    tooltip=f"Presión: {row['presion_psi']} PSI",
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)

            # RENDERIZADO FORZADO: Usamos una clave única y quitamos interactividad de retorno
            st_folium(m, width=600, height=450, key="mapa_final_ianc", returned_objects=[])

    except Exception as e:
        st.error(f"Error en visualización: {e}")
else:
    st.info("Cargue el archivo CSV para visualizar el tablero de control.")

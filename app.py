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
        # 1. Lectura forzada (Evita errores de tipos de datos)
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        df.columns = df.columns.str.strip().str.lower()
        
        # Convertir coordenadas a números flotantes sí o sí
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df = df.dropna(subset=['latitud', 'longitud'])

        # 2. Resumen de Métricas (Ya sabemos que esto funciona)
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Sensores", len(df))
        m2.metric("Municipio", str(df['municipio'].iloc[0]).capitalize())
        m3.metric("Presión Promedio", f"{df['presion_psi'].mean():.2f} PSI")

        st.divider()

        # 3. Visualización con contenedores explícitos
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("### 📊 Detalle de Campo")
            # Usamos st.table para forzar la visibilidad si st.dataframe falla
            st.write(df[['id_sensor', 'presion_psi', 'material']]) 

        with col2:
            st.write("### 🗺️ Mapa de Ubicación")
            centro_lat = df['latitud'].mean()
            centro_lon = df['longitud'].mean()
            
            # Crear mapa base con coordenadas de Villeta
            m = folium.Map(location=[centro_lat, centro_lon], zoom_start=15)

            for _, row in df.iterrows():
                folium.Marker(
                    location=[row['latitud'], row['longitud']],
                    popup=f"Sensor: {row['id_sensor']}\nPresión: {row['presion_psi']} PSI",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)

            # Renderizado estático para asegurar que aparezca en la nube
            st_folium(m, width=600, height=450, key="mapa_villeta")

    except Exception as e:
        st.error(f"Error visual: {e}")
else:
    st.info("Esperando archivo maestro de Villeta...")

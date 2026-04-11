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
        # 1. Lectura robusta
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        df.columns = df.columns.str.strip().str.lower()
        
        # 2. Limpieza de datos (Asegurar números)
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df = df.dropna(subset=['latitud', 'longitud'])

        # 3. Resumen de Auditoría (Cuadros de métricas)
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Sensores", len(df))
        m2.metric("Municipio", df['municipio'].iloc[0] if 'municipio' in df.columns else "N/A")
        m3.metric("Presión Promedio", f"{df['presion_psi'].mean():.2f} PSI" if 'presion_psi' in df.columns else "N/A")

        # 4. Layout: Tabla y Mapa
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("### 📊 Detalle de Campo")
            st.dataframe(df, height=400)

        with col2:
            st.write("### 🗺️ Mapa de Ubicación")
            # Crear mapa base
            centro_lat = df['latitud'].mean()
            centro_lon = df['longitud'].mean()
            
            m = folium.Map(location=[centro_lat, centro_lon], zoom_start=14, control_scale=True)

            # Añadir marcadores con información detallada
            for i, row in df.iterrows():
                info = f"""
                <b>Sensor:</b> {row.get('id_sensor', i)}<br>
                <b>Presión:</b> {row.get('presion_psi', 'N/A')} PSI<br>
                <b>Material:</b> {row.get('material', 'N/A')}
                """
                folium.Marker(
                    location=[row['latitud'], row['longitud']],
                    popup=folium.Popup(info, max_width=300),
                    tooltip=f"Sensor {row.get('id_sensor', i)}"
                ).add_to(m)

            # Renderizado de alta compatibilidad
            st_folium(m, width="100%", height=400, returned_objects=[])

    except Exception as e:
        st.error(f"Error al procesar el tablero: {e}")
else:
    st.info("Sistema listo. Por favor cargue el archivo de Villeta para visualizar los sensores.")

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. Títulos permanentes (Fuera del condicional para que no se "los coma")
st.set_page_config(page_title="Tablero IANC H2O", layout="wide")

st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader("Ing. Adolfo Barrera Vargas - Gestión de Sensores")

# 2. Módulo de carga
uploaded_file = st.file_uploader("Cargar Archivo Maestro de Campo (.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        # 3. Ejecución de cálculos (El cerebro del programa)
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        df.columns = df.columns.str.strip().str.lower()
        
        # Limpieza y conversión numérica
        df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
        df['presion_psi'] = pd.to_numeric(df['presion_psi'], errors='coerce')
        df = df.dropna(subset=['latitud', 'longitud'])

        # 4. Mostrar métricas de cálculo
        st.markdown("---")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Sensores", len(df))
        with col_b:
            mun = str(df['municipio'].iloc[0]).capitalize() if 'municipio' in df.columns else "N/A"
            st.metric("Municipio Detectado", mun)
        with col_c:
            promedio = df['presion_psi'].mean()
            st.metric("Presión Promedio", f"{promedio:.2f} PSI")

        # 5. Visualización del Tablero
        st.markdown("---")
        col1, col2 = st.columns([1, 1])

        with col1:
            st.write("### 📊 Detalle de Auditoría")
            st.table(df[['id_sensor', 'presion_psi', 'material', 'latitud', 'longitud']])

        with col2:
            st.write("### 🗺️ Mapa de Ubicación (Villeta)")
            # Crear el mapa de Folium que usted prefiere
            centro_lat = df['latitud'].mean()
            centro_lon = df['longitud'].mean()
            
            m = folium.Map(location=[centro_lat, centro_lon], zoom_start=15)

            for _, row in df.iterrows():
                folium.Marker(
                    location=[row['latitud'], row['longitud']],
                    popup=f"Sensor: {row['id_sensor']}\nPresión: {row['presion_psi']} PSI",
                    tooltip=f"ID: {row['id_sensor']}",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)

            # RENDERIZADO FINAL (Con llave de seguridad para que no falle en la web)
            st_folium(m, width=600, height=450, key="mapa_ianc_final", returned_objects=[])

    except Exception as e:
        st.error(f"Hubo un error al procesar los datos: {e}")
else:
    # Mensaje cuando no hay archivo
    st.info("Esperando archivo CSV para iniciar cálculos y generación de mapa.")

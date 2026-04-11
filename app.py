import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ==========================================
# 1. ENCABEZADOS FIJOS (Nunca desaparecen)
# ==========================================
st.set_page_config(page_title="Tablero IANC H2O", layout="wide")

st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader("Líder del Proyecto: ING. ADOLFO BARRERA VARGAS")
st.markdown("---")

# ==========================================
# 2. MENÚ LATERAL (El dashboard que se había perdido)
# ==========================================
st.sidebar.title("⚙️ Panel de Control")
modo_operacion = st.sidebar.radio(
    "Seleccione el origen de datos:",
    ["Datos Reales (Campo)", "Simulación (Prueba)"]
)

st.sidebar.markdown("---")

# ==========================================
# 3. LÓGICA DE CARGA (Depende del menú)
# ==========================================
df = None # Inicializamos la variable vacía

if modo_operacion == "Datos Reales (Campo)":
    st.sidebar.info("Modo de campo activo. Suba el archivo maestro.")
    uploaded_file = st.sidebar.file_uploader("Cargar Archivo (.csv)", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # Leer y limpiar datos
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
            df.columns = df.columns.str.strip().str.lower()
            df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
            df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
            df['presion_psi'] = pd.to_numeric(df['presion_psi'], errors='coerce')
            df = df.dropna(subset=['latitud', 'longitud'])
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

elif modo_operacion == "Simulación (Prueba)":
    st.sidebar.warning("Modo Simulación: Cargando datos sintéticos de Villeta.")
    # Generamos datos de prueba automáticamente si elige simulación
    datos_simulados = {
        'id_sensor': ['SIM-01', 'SIM-02', 'SIM-03'],
        'municipio': ['Villeta', 'Villeta', 'Villeta'],
        'presion_psi': [45.5, 50.2, 38.9],
        'material': ['PVC', 'HDPE', 'PVC'],
        'latitud': [5.0140, 5.0145, 5.0150],
        'longitud': [-74.4720, -74.4725, -74.4730]
    }
    df = pd.DataFrame(datos_simulados)

# ==========================================
# 4. CÁLCULOS Y VISUALIZACIÓN (Solo si hay datos)
# ==========================================
if df is not None and not df.empty:
    
    # --- MÓDULO DE CÁLCULOS ---
    st.write("### 🧮 Cálculos y Auditoría de Red")
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        st.metric("Sensores Activos", len(df))
    with col_m2:
        municipio = str(df['municipio'].iloc[0]).capitalize() if 'municipio' in df.columns else "N/A"
        st.metric("Sector Detectado", municipio)
    with col_m3:
        promedio_psi = df['presion_psi'].mean() if 'presion_psi' in df.columns else 0
        st.metric("Presión Promedio Red", f"{promedio_psi:.2f} PSI")

    st.markdown("---")

    # --- MÓDULO VISUAL (Tabla y Mapa) ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("### 📊 Registro Detallado")
        columnas_mostrar = [col for col in ['id_sensor', 'presion_psi', 'material', 'latitud', 'longitud'] if col in df.columns]
        st.dataframe(df[columnas_mostrar], use_container_width=True)

    with col2:
        st.write("### 🗺️ Georreferenciación")
        centro_lat = df['latitud'].mean()
        centro_lon = df['longitud'].mean()
        
        # El mapa de Folium configurado correctamente
        m = folium.Map(location=[centro_lat, centro_lon], zoom_start=15)

        for _, row in df.iterrows():
            id_sens = row.get('id_sensor', 'Desconocido')
            pres = row.get('presion_psi', 'N/A')
            folium.Marker(
                location=[row['latitud'], row['longitud']],
                popup=f"Sensor: {id_sens} | Presión: {pres} PSI",
                icon=folium.Icon(color='blue', icon='tint')
            ).add_to(m)

        # Carga del mapa sin bloqueo
        st_folium(m, width=500, height=400, key="mapa_final", returned_objects=[])

elif df is not None and df.empty:
    st.error("El archivo se cargó, pero no tiene coordenadas válidas.")
else:
    st.info("👈 Seleccione una opción en el menú lateral para iniciar.")

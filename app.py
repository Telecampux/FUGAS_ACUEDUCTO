import streamlit as st
import pandas as pd

# 1. Configuración Principal
st.set_page_config(page_title="Tablero IANC H2O", layout="wide")

st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader("Ing. Adolfo Barrera Vargas - Gestión de Sensores")
st.markdown("---")

# 2. Panel Lateral y Botón de Reinicio
st.sidebar.title("⚙️ Panel de Operación")

# BOTÓN DE REINICIO DE MEMORIA
if st.sidebar.button("🔄 Reiniciar Tablero / Limpiar Memoria"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

modo = st.sidebar.radio(
    "Seleccione el origen de la información:",
    ["1. Seleccione una opción...", "2. Simulación (Prueba rápida)", "3. Datos Reales (Subir CSV)"]
)

# 3. Inicializar tabla vacía
df = pd.DataFrame()

# ==========================================
# LÓGICA 1: SIMULACIÓN DIRECTA
# ==========================================
if modo == "2. Simulación (Prueba rápida)":
    st.sidebar.success("Modo Simulación Activo")
    # Creamos datos sintéticos obligatorios
    df = pd.DataFrame({
        'id_sensor': ['SIM-01', 'SIM-02', 'SIM-03', 'SIM-04'],
        'municipio': ['Villeta', 'Villeta', 'Villeta', 'Villeta'],
        'presion_psi': [45.5, 50.2, 38.9, 42.1],
        'material': ['PVC', 'HDPE', 'PVC', 'Hierro'],
        'lat': [5.0140, 5.0144, 5.0148, 5.0152],
        'lon': [-74.4720, -74.4723, -74.4726, -74.4729]
    })

# ==========================================
# LÓGICA 2: DATOS REALES
# ==========================================
elif modo == "3. Datos Reales (Subir CSV)":
    st.sidebar.info("Cargue su archivo de Villeta.")
    archivo = st.sidebar.file_uploader("Subir Archivo (.csv)", type=["csv"])
    
    if archivo:
        try:
            # Lectura y normalización forzada
            temp_df = pd.read_csv(archivo, sep=None, engine='python')
            temp_df.columns = temp_df.columns.str.strip().str.lower()
            
            # Renombramos a 'lat' y 'lon' para compatibilidad obligatoria
            if 'latitud' in temp_df.columns:
                temp_df = temp_df.rename(columns={'latitud': 'lat'})
            if 'longitud' in temp_df.columns:
                temp_df = temp_df.rename(columns={'longitud': 'lon'})
                
            temp_df['lat'] = pd.to_numeric(temp_df['lat'], errors='coerce')
            temp_df['lon'] = pd.to_numeric(temp_df['lon'], errors='coerce')
            
            # Guardamos solo si hay datos válidos
            df = temp_df.dropna(subset=['lat', 'lon'])
            
            if df.empty:
                st.error("El archivo se subió, pero no tiene coordenadas válidas.")
        except Exception as e:
            st.error(f"Error técnico al leer el archivo: {e}")

# ==========================================
# VISUALIZACIÓN (Se ejecuta automáticamente si 'df' tiene datos)
# ==========================================
if not df.empty:
    st.write("### 🧮 Cálculos de Auditoría")
    
    # Cuadros de cálculo matemáticos
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sensores Activos", len(df))
    
    mun = df['municipio'].iloc[0] if 'municipio' in df.columns else "Villeta"
    c2.metric("Municipio", str(mun).capitalize())
    
    if 'presion_psi' in df.columns:
        df['presion_psi'] = pd.to_numeric(df['presion_psi'], errors='coerce')
        c3.metric("Presión Promedio", f"{df['presion_psi'].mean():.2f} PSI")
    else:
        c3.metric("Presión Promedio", "No disp.")

    st.markdown("---")
    
    col_tabla, col_mapa = st.columns([1, 1])
    
    with col_tabla:
        st.write("### 📊 Datos Registrados")
        st.dataframe(df, use_container_width=True)
        
    with col_mapa:
        st.write("### 🗺️ Mapa Integrado")
        # El mapa nativo no sufre de bloqueos de navegador
        st.map(df, latitude='lat', longitude='lon', color='#0044ff', size=30)

elif modo == "1. Seleccione una opción...":
    st.info("👈 Utilice el panel izquierdo para seleccionar el modo de trabajo.")

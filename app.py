import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Tablero IANC H2O", layout="wide")

# --- ENCABEZADO ---
st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader("Ing. Adolfo Barrera Vargas - Gestión de Sensores")

# --- CARGA DE ARCHIVO ---
uploaded_file = st.file_uploader("Cargar Archivo Maestro de Campo (.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        # 1. Lectura de datos con detección de separador (coma o punto y coma)
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        
        # 2. Normalización de columnas a minúsculas
        df.columns = df.columns.str.strip().str.lower()
        
        # 3. Preparación técnica de coordenadas para el mapa nativo
        # Creamos columnas 'lat' y 'lon' que son las que Streamlit lee por defecto
        df['lat'] = pd.to_numeric(df['latitud'], errors='coerce')
        df['lon'] = pd.to_numeric(df['longitud'], errors='coerce')
        
        # Limpiamos registros que no tengan coordenadas válidas
        df = df.dropna(subset=['lat', 'lon'])

        # --- SECCIÓN DE MÉTRICAS ---
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        
        if not df.empty:
            m1.metric("Total Sensores", len(df))
            m2.metric("Municipio", str(df['municipio'].iloc[0]).capitalize() if 'municipio' in df.columns else "N/A")
            m3.metric("Presión Promedio", f"{df['presion_psi'].mean():.2f} PSI" if 'presion_psi' in df.columns else "0.00 PSI")

            st.markdown("---")

            # --- VISUALIZACIÓN EN DOS COLUMNAS ---
            col1, col2 = st.columns([1, 1.2])

            with col1:
                st.write("### 📊 Detalle de Auditoría")
                # Mostramos la tabla (st.table es la más confiable para visualizar)
                columnas_ver = [c for c in ['id_sensor', 'presion_psi', 'material', 'latitud', 'longitud'] if c in df.columns]
                st.table(df[columnas_ver])

            with col2:
                st.write("### 🗺️ Mapa de Ubicación Geográfica")
                # MAPA NATIVO: Ultra-confiable, no requiere iframes externos
                st.map(df, latitude='lat', longitude='lon', color='#FF0000', size=20)
        else:
            st.error("El archivo no contiene coordenadas válidas en las columnas 'latitud' y 'longitud'.")

    except Exception as e:
        st.error(f"Error crítico en el procesamiento: {e}")
else:
    st.info("🔌 Sistema a la espera de datos. Por favor cargue el archivo CSV para activar el tablero.")

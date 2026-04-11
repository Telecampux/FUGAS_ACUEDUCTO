import streamlit as st
import pandas as pd
import os
from pathlib import Path
import folium
from streamlit_folium import st_folium

# --- 1. LÓGICA DE DETECCIÓN DE DIRECTORIOS (REFORZADA) ---
# Usamos Path para manejar rutas de forma más limpia
BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "datos_simulacion"

def inicializar_sistema():
    """Verifica la carpeta de datos y lista archivos de ingeniería."""
    # Diagnóstico: Listar lo que ve el servidor para depuración profesional
    try:
        elementos_raiz = os.listdir(BASE_DIR)
    except Exception as e:
        return None, f"Error accediendo al directorio raíz: {e}"

    if not DATA_FOLDER.exists():
        return None, f"Carpeta 'datos_simulacion' no detectada en {BASE_DIR}. Contenido actual: {elementos_raiz}"
    
    # Filtro de archivos con list comprehension
    archivos = [f for f in os.listdir(DATA_FOLDER) if f.lower().endswith(('.csv', '.xlsx', '.xls'))]
    return archivos, None

def cargar_data(archivo_nombre):
    ruta = DATA_FOLDER / archivo_nombre
    if archivo_nombre.endswith('.csv'):
        return pd.read_csv(ruta)
    else:
        return pd.read_excel(ruta)

# --- 2. CONFIGURACIÓN DE LA INTERFAZ IANS H2O ---
st.set_page_config(page_title="IANS H2O - Localización de Fugas", layout="wide")

st.title("📍 Sistema de Localización de Fugas IANS H2O")
st.sidebar.header("Configuración del Sistema")
st.sidebar.info(f"Ruta base detectada: `{BASE_DIR}`")

# --- 3. EJECUCIÓN PRINCIPAL ---
archivos_disponibles, error_msg = inicializar_sistema()

if error_msg:
    st.error(f"❌ Error de Estructura")
    st.code(error_msg) # Mostramos el error técnico en un bloque de código
    st.warning("Asegúrate de que la carpeta esté en el repositorio con el nombre exacto 'datos_simulacion'.")
else:
    if not archivos_disponibles:
        st.warning(f"⚠️ Carpeta '{DATA_FOLDER.name}' vacía o sin archivos compatibles.")
    else:
        archivo_target = st.selectbox("Seleccione archivo de monitoreo:", archivos_disponibles)
        
        try:
            df = cargar_data(archivo_target)
            st.success(f"✅ Analizando: {archivo_target}")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("Métricas de Red")
                st.dataframe(df.describe(), use_container_width=True)
            
            with col2:
                st.subheader("Mapa de Presiones / Fugas")
                m = folium.Map(location=[4.6, -74.0], zoom_start=6)
                st_folium(m, width="100%", height=400)
                
        except Exception as e:
            st.error(f"Error al procesar los datos: {e}")

st.sidebar.markdown("---")
st.sidebar.write("Ing. Adolfo Barrera Vargas")

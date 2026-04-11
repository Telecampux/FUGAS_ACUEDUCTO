import streamlit as st
import pandas as pd
import os
import folium
from streamlit_folium import st_folium

# --- 1. LÓGICA DE DETECCIÓN DE DIRECTORIOS ---
# Obtenemos la ruta de la carpeta donde reside este archivo app.py
directorio_actual = os.path.dirname(os.path.abspath(__file__))
# Definimos la carpeta de datos relativa a la ubicación del script
DATA_FOLDER = os.path.join(directorio_actual, 'datos_simulacion')

def inicializar_sistema():
    """Verifica la carpeta de datos y lista archivos de ingeniería."""
    # Diagnóstico para el ingeniero: Ver qué carpetas existen en el servidor
    carpetas_visibles = [d for d in os.listdir(directorio_actual) if os.path.isdir(os.path.join(directorio_actual, d))]
    
    if not os.path.exists(DATA_FOLDER):
        return None, f"Carpeta 'datos_simulacion' no detectada. Carpetas encontradas: {carpetas_visibles}"
    
    archivos = [f for f in os.listdir(DATA_FOLDER) if f.endswith(('.csv', '.xlsx', '.xls'))]
    return archivos, None

def cargar_data(archivo_nombre):
    ruta = os.path.join(DATA_FOLDER, archivo_nombre)
    if archivo_nombre.endswith('.csv'):
        return pd.read_csv(ruta)
    else:
        return pd.read_excel(ruta)

# --- 2. CONFIGURACIÓN DE LA INTERFAZ IANS H2O ---
st.set_page_config(page_title="IANS H2O - Localización de Fugas", layout="wide")

st.title("📍 Sistema de Localización de Fugas IANS H2O")
st.sidebar.header("Configuración del Sistema")
st.sidebar.info(f"Ruta de ejecución: {directorio_actual}")

# --- 3. EJECUCIÓN PRINCIPAL ---
archivos_disponibles, error_msg = inicializar_sistema()

if error_msg:
    st.error(f"❌ Error de Estructura: {error_msg}")
    st.warning("Verifica que en tu GitHub la carpeta se llame exactamente 'datos_simulacion' (en minúsculas).")
else:
    if not archivos_disponibles:
        st.warning("⚠️ La carpeta existe pero no contiene archivos de datos (.csv o .xlsx).")
    else:
        archivo_target = st.selectbox("Seleccione archivo de monitoreo:", archivos_disponibles)
        
        try:
            df = cargar_data(archivo_target)
            st.success(f"✅ Analizando: {archivo_target}")
            
            # --- VISUALIZACIÓN TÉCNICA ---
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("Métricas de Red")
                st.write(df.describe())
            
            with col2:
                st.subheader("Mapa de Presiones / Fugas")
                # Mapa centrado (ajustar coordenadas según municipio)
                m = folium.Map(location=[4.6, -74.0], zoom_start=6)
                st_folium(m, width="100%", height=400)
                
        except Exception as e:
            st.error(f"Error al procesar los datos: {e}")

st.sidebar.markdown("---")
st.sidebar.write("Ing. Adolfo Barrera Vargas")

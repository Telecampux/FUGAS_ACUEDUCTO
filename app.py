import os
import streamlit as st
import pandas as pd
import json

# =================================================================
# 1. RUTA ESTÁTICA Y DIRECTA (SIN EXPLORADOR DE WINDOWS)
# =================================================================
# Escriba aquí el nombre exacto de la carpeta que creó. 
# Debe estar en el mismo lugar que este archivo app.py.
CARPETA_DATOS = "datos_simulacion" 

st.sidebar.header("📂 DATOS DEL SISTEMA")

# Verificación de seguridad directa
if not os.path.exists(CARPETA_DATOS):
    st.error(f"❌ La carpeta '{CARPETA_DATOS}' no existe en este directorio.")
    st.stop()

# =================================================================
# 2. LECTURA AUTOMÁTICA DE ARCHIVOS
# =================================================================
archivos_json = [f for f in os.listdir(CARPETA_DATOS) if f.endswith(('.geojson', '.json'))]
archivos_csv = [f for f in os.listdir(CARPETA_DATOS) if f.endswith('.csv')]

# --- Selector de Cartografía (Simulación) ---
if archivos_json:
    plano_sel = st.sidebar.selectbox("🗺️ Plano Cartográfico:", archivos_json)
    ruta_plano = os.path.join(CARPETA_DATOS, plano_sel)
    with open(ruta_plano, 'r', encoding='utf-8') as f:
        cartografia_activa = json.load(f)
else:
    st.sidebar.warning(f"⚠️ No hay archivos GeoJSON en '{CARPETA_DATOS}'")

# --- Selector de Auditoría (Lote/Producción) ---
if archivos_csv:
    csv_sel = st.sidebar.selectbox("📊 Matriz de Auditoría:", archivos_csv)
    ruta_csv = os.path.join(CARPETA_DATOS, csv_sel)
    df = pd.read_csv(ruta_csv)
else:
    st.sidebar.warning(f"⚠️ No hay archivos CSV en '{CARPETA_DATOS}'")

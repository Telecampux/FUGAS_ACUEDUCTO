import os
import pandas as pd
import json
import streamlit as st

# --- ANCLAJE DE DIRECTORIO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Definimos la carpeta con el nombre exacto que usted prefiere
FOLDER_SIM = os.path.join(BASE_DIR, "datos_simulacion")

# Aseguramos que la carpeta exista para evitar errores de ruta
if not os.path.exists(FOLDER_SIM):
    os.makedirs(FOLDER_SIM)

def obtener_archivos(extension):
    """Escanea la carpeta 'datos_simulacion' buscando archivos específicos."""
    return [f for f in os.listdir(FOLDER_SIM) if f.endswith(extension)]

# --- INTERFAZ DE CARGA DINÁMICA ---
st.sidebar.header("📂 BANCO DE DATOS")

# 1. Selector de Cartografía (GeoJSON)
planos_disponibles = obtener_archivos(".geojson") + obtener_archivos(".json")
if planos_disponibles:
    plano_sel = st.sidebar.selectbox("🗺️ Seleccionar Plano (Simulación):", planos_disponibles)
    with open(os.path.join(FOLDER_SIM, plano_sel), 'r') as f:
        cartografia_activa = json.load(f)
else:
    st.sidebar.info("💡 Suba archivos .geojson a /datos_simulacion")

# 2. Selector de Auditorías (CSV)
csv_disponibles = obtener_archivos(".csv")
if csv_disponibles:
    csv_sel = st.sidebar.selectbox("📊 Seleccionar CSV (Simulación):", csv_disponibles)
    df_simulacion = pd.read_csv(os.path.join(FOLDER_SIM, csv_sel))
else:
    st.sidebar.info("💡 Suba archivos .csv a /datos_simulacion")

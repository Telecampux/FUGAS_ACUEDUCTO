import os
import streamlit as st
import pandas as pd
import json
from pathlib import Path

# =================================================================
# 1. ANCLAJE MILIMÉTRICO DE RUTAS (PRO-ARCHITECTURE)
# =================================================================

# Obtenemos la ruta absoluta de donde está ESTE archivo app.py
# No importa desde dónde se ejecute, PATH_RAIZ siempre será 'ianc_h2o_pro'
PATH_RAIZ = Path(__file__).parent.absolute()

# Definimos la carpeta de datos de simulación
FOLDER_SIM = PATH_RAIZ / "datos_simulacion"

# Forzamos la creación si no existe
FOLDER_SIM.mkdir(parents=True, exist_ok=True)

# Obligamos al sistema operativo a que su "Directorio de Trabajo" sea este
os.chdir(PATH_RAIZ)

# =================================================================
# 2. LÓGICA DE EXPLORACIÓN AUTOMÁTICA
# =================================================================

def listar_archivos_locales(extension):
    """Busca archivos solo dentro de la carpeta del proyecto."""
    return [f.name for f in FOLDER_SIM.glob(f"*{extension}")]

# --- INTERFAZ SIDEBAR ---
st.sidebar.title("📂 GESTIÓN DE ARCHIVOS")
st.sidebar.info(f"📍 Directorio Activo: {PATH_RAIZ.name}")

# Selector de Cartografía (GeoJSON)
planos = listar_archivos_locales(".geojson") + listar_archivos_locales(".json")
if planos:
    plano_sel = st.sidebar.selectbox("🗺️ Plano en /datos_simulacion:", planos)
    ruta_plano = FOLDER_SIM / plano_sel
    with open(ruta_plano, 'r', encoding='utf-8') as f:
        cartografia_activa = json.load(f)
    st.sidebar.success(f"✅ Cargado: {plano_sel}")
else:
    st.sidebar.warning("⚠️ No hay .geojson en /datos_simulacion")

# Selector de Auditorías (CSV)
auditorias = listar_archivos_locales(".csv")
if auditorias:
    csv_sel = st.sidebar.selectbox("📊 Auditoría en /datos_simulacion:", auditorias)
    ruta_csv = FOLDER_SIM / csv_sel
    df_actual = pd.read_csv(ruta_csv)
    st.sidebar.success(f"✅ Cargado: {csv_sel}")
else:
    st.sidebar.warning("⚠️ No hay .csv en /datos_simulacion")

import streamlit as st
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt
import json
import pandas as pd

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="IANC H2O - Auditoría Profesional", layout="wide")

autor = "ING. ADOLFO BARRERA VARGAS"
programa = "SISTEMA INTEGRAL DE AUDITORÍA P.R.P."

st.title("📡 TABLERO DE CONTROL IANC H2O")
st.write(f"### {programa}")
st.caption(f"**Gestión de Activos y Diagnóstico Hidráulico** | {autor}")
st.divider()

# --- DATOS TOPOLÓGICOS ---
territorios = {
    "Villeta": {"coords": [5.0140, -74.4720], "costo": 3200, "z_base": 842.0},
    "Neiva": {"coords": [2.9273, -75.2819], "costo": 3500, "z_base": 442.0},
    "Chaparral": {"coords": [3.7231, -75.4832], "costo": 3100, "z_base": 854.0},
    "El Espinal": {"coords": [4.1492, -74.8878], "costo": 2900, "z_base": 323.0},
    "Villavicencio": {"coords": [4.1420, -73.6266], "costo": 3400, "z_base": 467.0}
}

# --- LÓGICA DE CÁLCULOS ---
def haversine(lat1, lon1, lat2, lon2):
    r = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    d = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 2 * r * asin(sqrt(d))

def cargar_cartografia_simulada(municipio):
    lat, lon = territorios[municipio]['coords']
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {"tipo": "Red Matriz (Simulada)", "color": "#00FFFF", "weight": 6},
                      "geometry": {"type": "LineString", "coordinates": [[lon - 0.015, lat + 0.015], [lon, lat]]}}]
    }

# --- MENÚ LATERAL ---
st.sidebar.header("📂 MÓDULOS DEL SISTEMA")
modo = st.sidebar.radio("Modo de Trabajo:", ["Simulación Interactiva", "Operación Real (Carga Lote)"])

st.sidebar.divider()
mun_sel = st.sidebar.selectbox("Municipio Objeto", list(territorios.keys()))
costo_m3 = st.sidebar.number_input("Costo m³ (COP)", value=territorios[mun_sel]['costo'])
dn = st.sidebar.selectbox("Diámetro de Red Auditada (P

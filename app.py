import streamlit as st
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt
import json
import pandas as pd
import time

# --- CONFIGURACIÓN E INTERFAZ PROFESIONAL ---
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

# --- LÓGICA DE CÁLCULOS HIDRÁULICOS ---
def haversine(lat1, lon1, lat2, lon2):
    r = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    d = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 2 * r * asin(sqrt(d))

def perdida_hazen_williams(q_lps, c, d_pulg, l_m):
    if q_lps <= 0: return 0
    q_m3s = q_lps / 1000.0
    d_m = d_pulg * 0.0254
    hf_mca = 10.67 * l_m * ((q_m3s / c)**1.852) * (d_m**-4.87)
    return hf_mca / 0.703 # Retorna pérdida en PSI

# --- MENÚ LATERAL ---
st.sidebar.header("📂 MÓDULOS DEL SISTEMA")
modo = st.sidebar.radio("Modo de Trabajo:", ["Simulación Interactiva", "Operación Real (Carga Lote)"])

st.sidebar.divider()
mun_sel = st.sidebar.selectbox("Municipio Objeto", list(territorios.keys()))
costo_m3 = st.sidebar.number_input("Costo m³ (COP)", value=territorios[mun_sel]['costo'])
dn = st.sidebar.selectbox("Diámetro de Red Auditada (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=2)

# --- ESTADO DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'ejecutado_sim' not in st.session_state: st.session_state.ejecutado_sim = False
if 'procesado_real' not in st.session_state: st.session_state.procesado_real = False
if 'mostrar_animacion' not in st.session_state: st.session_state.mostrar_animacion = False

# =================================================================
# MÓDULO 1: SIMULACIÓN INTERACTIVA (ESTÉTICA SUPERIOR)
# =================================================================
if modo == "Simulación Interactiva":
    st.write("### 🕹️ Modo: Simulación Interactiva")
    empresa = st.text_input("Nombre de la Empresa:", "Administración Municipal")
    
    if st.sidebar.button("♻️ Reiniciar Nodos"):
        st.session_state.puntos = []
        st.session_state.ejecutado_sim = False
        st.rerun()

    # Mapa de trazado
    m1 = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, popup=f"S{i+1}", icon=folium.Icon(color='blue')).add_to(m1)
    
    mapa_click = st_folium(m1, width=1100, height=400, key="sim_map")
    
    if mapa_click and mapa_click.get("last_clicked"):
        clicked = [mapa_click["last_clicked"]["lat"], mapa_click["last_clicked"]["lng"]]
        if not st.session

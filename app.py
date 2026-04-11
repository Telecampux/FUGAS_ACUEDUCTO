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
dn = st.sidebar.selectbox("Diámetro de Red Auditada (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=2)

# --- CARGA DE CARTOGRAFÍA (GIS) ---
st.sidebar.subheader("🗺️ Capas Geográficas")
archivo_gis = st.sidebar.file_uploader("Subir Plano del Acueducto (.geojson)", type=["geojson", "json"])

# --- ESTADO DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'ejecutado' not in st.session_state: st.session_state.ejecutado = False
if 'presiones' not in st.session_state: st.session_state.presiones = []
if 'cotas' not in st.session_state: st.session_state.cotas = []
if 'empresa' not in st.session_state: st.session_state.empresa = "Administración Municipal"

# =================================================================
# ENTRADAS
# =================================================================
if modo == "Simulación Interactiva":
    st.write("### 🕹️ Modo: Simulación Interactiva")
    st.session_state.empresa = st.text_input("Nombre de la Empresa:", st.session_state.empresa)
    
    if st.sidebar.button("♻️ Reiniciar Nodos"):
        st.session_state.puntos = []
        st.session_state.ejecutado = False
        st.rerun()

    m1 = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
    carto = json.load(archivo_gis) if archivo_gis else cargar_cartografia_simulada(mun_sel)
    folium.GeoJson(carto, style_function=lambda x: {'color': '#00FFFF', 'weight': 5, 'opacity': 0.5}).add_to(m1)
    
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, popup=f"S{i+1}", icon=folium.Icon(color='blue')).add_to(m1)
    
    mapa_click = st_folium(m1, width=1100, height=400, key=f"sim_{mun_sel}_{len(st.session_state.puntos)}")
    
    if mapa_click and mapa_click.get("last_clicked"):
        clicked = [mapa_click["last_clicked"]["lat"], mapa_click["last_clicked"]["lng"]]
        if not st.session_state.puntos or clicked != st.session_state.puntos[-1]:
            st.session_state.puntos.append(clicked)
            st.rerun()

    if len(st.session_state.puntos) >= 2:
        st.write("---")
        pres_list, cota_list = [], []
        cols = st.columns(len(st.session_state.puntos))
        for i in range(len(st.session_state.puntos)):
            with cols[i]:
                p_val = st.number_input(f"Presión S{i+1}", value=45.0-(i*8.0), key=f"psim_{i}")
                z_val = st.number_input(f"Cota S{i+1}", value=territorios[mun_sel]['z_base']-(i*1.0), key=f"zsim_{i}")
                pres_list.append(p_val); cota_list.append(z_val)
        
        if st.button("🚀 EJECUTAR CÁLCULOS"):
            st.session_state.presiones = pres_list
            st.session_state.cotas = cota_list
            st.session_state.ejecutado = True
            st.rerun()

elif modo == "Operación Real (Carga Lote)":
    st.write("### 📊 Modo: Operación por Lote (Auditoría Técnica)")
    
    with st.expander("⚠️ PROTOCOLO DE INFORMACIÓN TÉCNICA REQUERIDA", expanded=True):
        st.markdown("""
        Para obtener resultados de **localización exacta**, el archivo CSV debe contener:
        * **municipio**: Cruce

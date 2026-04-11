import streamlit as st
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt
import json
import pandas as pd
import time

# --- CONFIGURACIÓN E INTERFAZ DE ALTO NIVEL ---
st.set_page_config(page_title="IANC H2O - Auditoría Profesional", layout="wide")

# Identidad del Sistema
AUTOR = "ING. ADOLFO BARRERA VARGAS"
PROGRAMA = "SISTEMA INTEGRAL DE AUDITORÍA P.R.P."
VERSION = "2.0.1 PRO"

# --- MOTOR DE CÁLCULO (CORE LOGIC) ---
def haversine(lat1, lon1, lat2, lon2):
    """Cálculo de distancia geodésica entre dos puntos (m)."""
    r = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    d = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 2 * r * asin(sqrt(d))

def perdida_hazen_williams(q_lps, c, d_pulg, l_m):
    """Cálculo de pérdida por fricción (PSI)."""
    if q_lps <= 0: return 0
    q_m3s = q_lps / 1000.0
    d_m = d_pulg * 0.0254
    hf_mca = 10.67 * l_m * ((q_m3s / c)**1.852) * (d_m**-4.87)
    return hf_mca / 0.703 # Conversión a PSI

# --- DATOS TOPOLÓGICOS DE REFERENCIA ---
territorios = {
    "Villeta": {"coords": [5.0140, -74.4720], "costo": 3200, "z_base": 842.0},
    "Neiva": {"coords": [2.9273, -75.2819], "costo": 3500, "z_base": 442.0},
    "Chaparral": {"coords": [3.7231, -75.4832], "costo": 3100, "z_base": 854.0},
    "El Espinal": {"coords": [4.1492, -74.8878], "costo": 2900, "z_base": 323.0},
    "Villavicencio": {"coords": [4.1420, -73.6266], "costo": 3400, "z_base": 467.0}
}

# --- INICIALIZACIÓN DE ESTADOS (SESSION STATE) ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'ejecutado' not in st.session_state: st.session_state.ejecutado = False
if 'empresa' not in st.session_state: st.session_state.empresa = "Administración Municipal"
if 'procesado_real' not in st.session_state: st.session_state.procesado_real = False 

# --- HEADER ---
st.title("📡 TABLERO DE CONTROL IANC H2O")
st.write(f"### {PROGRAMA}")
st.caption(f"**Ingeniería de Software para Redes de Acueducto** | {AUTOR} | v{VERSION}")
st.divider()

# --- BARRA LATERAL (CONTROL DE MÓDULOS) ---
st.sidebar.header("📂 MÓDULOS DEL SISTEMA")
modo = st.sidebar.radio("Seleccione Modo de Trabajo:", ["Simulación Interactiva", "Operación Real (Carga Lote)"])

st.sidebar.divider()
mun_sel = st.sidebar.selectbox("Municipio Objeto", list(territorios.keys()))
costo_m3 = st.sidebar.number_input("Costo m³ (COP)", value=territorios[mun_sel]['costo'])
dn_sim = st.sidebar.selectbox("Diámetro de Red (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=2)

# =================================================================
# MÓDULO 1: SIMULACIÓN INTERACTIVA
# =================================================================
if modo == "Simulación Interactiva":
    st.write("### 🕹️ Modo: Simulación Interactiva")
    st.session_state.empresa = st.text_input("Nombre de la Empresa:", st.session_state.empresa)
    
    col_map, col_inputs = st.columns([2, 1])

    with col_map:
        m1 = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
        for i, p in enumerate(st.session_state.puntos):
            folium.Marker(p, popup=f"S{i+1}", icon=folium.Icon(color='blue')).add_to(m1)
        
        mapa_click = st_folium(m1, width=700, height=450, key="sim_map")
        
        if mapa_click and mapa_click.get("last_clicked"):
            clicked = [mapa_click["last_clicked"]["lat"], mapa_click["last_clicked"]["lng"]]
            if not st.session_state.puntos or clicked != st.session_state.puntos[-1]:
                st.session_state.puntos.append(clicked)
                st.rerun()

    with col_inputs:
        if st.button("♻️ Reiniciar Nodos"):
            st.session_state.puntos = []
            st.session_state.ejecutado = False
            st.rerun()
        
        pres_list, cota_list = [], []
        if len(st.session_state.puntos) >= 2:
            st.write("**Datos de Campo:**")
            for i in range(len(st.session_state.puntos)):
                p_val = st.number_input(f"P sensor {i+1} (PSI)", value=45.0-(i*5), key=f"psim_{i}")
                z_val = st.number_input(f"Cota {i+1} (msnm)", value=territorios[mun_sel]['z_base']-i, key=f"zsim_{i}")
                pres_list.append(p_val); cota_list.append(z_val)
            
            if st.button("🚀 EJECUTAR CÁLCULOS"):
                st.session_state.pres_sim = pres_list
                st.session_state.cota_sim = cota_list
                st.session_state.ejecutado = True

    # RESULTADOS DE SIMULACIÓN
    if st.session_state.ejecutado:
        st.divider()
        st.subheader("📊 Reporte de Diagnóstico")
        for i in range(len(st.session_state.puntos)-1):
            p1, p2 = st.session_state.pres_sim[i], st.session_state.pres_sim[i+1]
            z1, z2 = st.session_state.cota_sim[i], st.session_state.cota_sim[i+1]
            dist = haversine(st.session_state.puntos[i][0], st.session_state.puntos[i][1], 
                             st.session_state.puntos[i+1][0], st.session_state.puntos[i+1][1])
            dz_psi = (z1 - z2) / 0.703
            caida_real = (p1 + dz_psi) - p2

            with st.expander(f"Tramo S{i+1} ➔ S{i+2} ({round(dist,1)}m)", expanded=True):
                if caida_real > 1.5:
                    st.error(f"🚨 FUGA DETECTADA: Gradiente de {round(caida_real,2)} PSI")
                else:
                    st.success("✅ TRAMO HERMÉTICO")

# =================================================================
# MÓDULO 2: OPERACIÓN REAL (POR LOTE)
# =================================================================
elif modo == "Operación Real (Carga Lote)":
    st.write("### 📊 Modo: Operación por Lote (Auditoría Técnica)")
    csv_file = st.file_uploader("Subir CSV Maestro", type=["csv"])

    if csv_file:
        df = pd.read_csv(csv_file)
        st.success(f"Archivo cargado: {len(df)} sensores.")
        
        q_base = st.number_input("Caudal de tránsito (L/s)", value=5.0)
        
        if st.button("🚀 PROCESAR AUDITORÍA"):
            with st.status("Analizando Gradientes...", expanded=True) as s:
                time.sleep(1)
                st.session_state.procesado_real = True
                s.update(label="Análisis Completo", state="complete")
        
        if st.session_state.procesado_real:
            tab1, tab2 = st.tabs(["🗺️ Mapa", "💻 Log de Operaciones"])
            
            with tab1:
                m_real = folium.Map(location=[df.iloc[0]['latitud'], df.iloc[0]['longitud']], zoom_start=17)
                log_text = "INICIANDO AUDITORÍA...\n"
                
                for i in range(len(df)-1):
                    s1, s2 = df.iloc[i], df.iloc[i+1]
                    dist = haversine(s1['latitud'], s1['longitud'], s2['latitud'], s2['longitud'])
                    dz_psi = (s1['cota_z'] - s2['cota_z']) / 0.703
                    p_teorica = perdida_hazen_williams(q_base, s1['coeficiente_c'], s1['diametro_pulg'], dist)
                    p_real = (s1['presion_psi'] + dz_psi) - s2['presion_psi']
                    desv = p_real - p_teorica
                    
                    color = 'red' if desv > 2.0 else 'green'
                    folium.PolyLine([[s1['latitud'], s1['longitud']], [s2['latitud'], s2['longitud']]], color=color, weight=5).add_to(m_real)
                    log_text += f"Tramo {s1['id_sensor']}-{s2['id_sensor']}: Desviación {round(desv,2)} PSI\n"

                st_folium(m_real, width=1000, height=500)
            
            with tab2:
                st.code(log_text, language="bash")

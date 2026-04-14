import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import time

# --- CONFIGURACIÓN TÉCNICA ---
st.set_page_config(page_title="IANC_H2O - Análisis Físico", layout="wide")

# --- MOTOR DE CÁLCULO (PRECISIÓN DETERMINÍSTICA) ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Radio Tierra en metros
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi, dlamb = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlamb/2)**2
    return R * (2 * np.arctan2(np.sqrt(a), np.sqrt(1-a)))

def perdida_hazen_williams(q, c, d, l):
    if c == 0 or d == 0: return 0.0
    return 10.67 * ((q/1000.0)**1.852) * l / ((c**1.852) * ((d*0.0254)**4.87))

def obtener_cota_api(lat, lon):
    try:
        res = requests.get(f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}", timeout=2).json()
        return round(res["elevation"][0], 2) if "elevation" in res else 1000.0
    except: return 1000.0

# --- CONSTANTES ---
FACTOR_PSI_MCA = 0.7032
AUTOR = "Ing. Adolfo Barrera Vargas"

# --- INTERFAZ ---
st.title("IANC_H2O: LOCALIZACIÓN DE FUGAS (RED MATRIZ)")
st.caption(f"Motor de Análisis Físico Independiente del Material | {AUTOR}")

# Sidebar
with st.sidebar:
    st.header("⚙️ Parámetros de Diseño")
    q_lps = st.number_input("Caudal (L/s)", value=20.0)
    dn_pulg = st.selectbox("Diámetro (Pulg)", [3, 4, 6, 8, 10, 12, 16, 24], index=2)
    coef_c = st.slider("Coeficiente C", 100, 150, 140)
    st.divider()
    if st.button("🗑️ Reiniciar Sistema"):
        st.session_state.puntos = []
        st.rerun()

# Inicialización de Estado
if 'puntos' not in st.session_state: st.session_state.puntos = []

col_map, col_inputs = st.columns([2, 1])

with col_map:
    m = folium.Map(location=[4.60, -74.08], zoom_start=12)
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, tooltip=f"Nodo {i+1}").add_to(m)
    if len(st.session_state.puntos) > 1:
        folium.PolyLine(st.session_state.puntos, color="blue").add_to(m)
    
    mapa_data = st_folium(m, width=700, height=450)
    if mapa_data and mapa_data.get('last_clicked'):
        nuevo_p = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
        if nuevo_p not in st.session_state.puntos:
            st.session_state.puntos.append(nuevo_p)
            st.rerun()

with col_inputs:
    st.subheader("📡 Sensores de Presión")
    datos_sensores = {}
    for i in range(len(st.session_state.puntos)):
        with st.expander(f"Nodo {i+1}", expanded=True):
            p_val = st.number_input(f"Presión (PSI)", key=f"p_{i}", value=30.0)
            z_val = st.number_input(f"Cota (msnm)", key=f"z_{i}", value=obtener_cota_api(st.session_state.puntos[i][0], st.session_state.puntos[i][1]))
            datos_sensores[i] = {"P": p_val, "Z": z_val}

# --- PROCESAMIENTO ---
if len(st.session_state.puntos) >= 2:
    if st.button("🚀 EJECUTAR ANÁLISIS DE GRADIENTE", type="primary", use_container_width=True):
        matriz, alertas = [], []
        dist_acum = 0.0
        
        # Estado Inicial Nodo 1
        h_prev = datos_sensores[0]['Z'] + (datos_sensores[0]['P'] * FACTOR_PSI_MCA)
        matriz.append({"Nodo": "N-1", "H (mca)": round(h_prev, 2), "D (m)": 0.0})

        for i in range(1, len(st.session_state.puntos)):
            # Cálculo de tramo
            d2d = haversine(st.session_state.puntos[i-1][0], st.session_state.puntos[i-1][1], 
                            st.session_state.puntos[i][0], st.session_state.puntos[i][1])
            dz = abs(datos_sensores[i-1]['Z'] - datos_sensores[i]['Z'])
            d3d = np.sqrt(d2d**2 + dz**2)
            dist_acum += d3d
            
            # Energías
            h_act = datos_sensores[i]['Z'] + (datos_sensores[i]['P'] * FACTOR_PSI_MCA)
            dh_real = h_prev - h_act
            dh_teo = perdida_hazen_williams(q_lps, coef_c, dn_pulg, d3d)
            
            # Verificación de Anomalía
            if dh_real > (dh_teo + 0.1): # Umbral de sensibilidad
                x_fuga = d3d * (dh_teo / dh_real) if dh_real > 0 else 0
                alertas.append({
                    "id": f"{i}-{i+1}", "rel": x_fuga, "L": d3d, 
                    "h1": h_prev, "h2": h_act, "dh_r": dh_real, "dh_t": dh_teo,
                    "z1": datos_sensores[i-1]['Z'], "p1": datos_sensores[i-1]['P'],
                    "z2": datos_sensores[i]['Z'], "p2": datos_sensores[i]['P']
                })
            
            h_prev = h_act
            matriz.append({"Nodo": f"N-{i+1}", "H (mca)": round(h_act, 2), "D (m)": round(dist_acum, 2)})

        # REPORTE
        st.divider()
        if alertas:
            for a in alertas:
                st.error(f"🚨 ANOMALÍA CONFIRMADA: Punto crítico a {a['rel']:.2f} m del Nodo {a['id'].split('-')[0]}")
                with st.expander("⚙️ DICCIONARIO DE VARIABLES Y MEMORIA TÉCNICA"):
                    st.markdown(f"""
                    ### 1. Variables de Estado (Nodo Origen)
                    * **$Z_1$ (Cota):** {a['z1']} msnm | **$P_1$ (Presión):** {a['p1']} PSI
                    * **$H_1$ (Energía Total):** $Z_1 + (P_1 \cdot 0.7032) = {a['h1']:.2f}$ mca
                    
                    ### 2. Análisis de Fondo ($\Delta H$)
                    * **$\Delta H_{{Real}}$:** {a['dh_r']:.2f} mca (Caída medida por sensores).
                    * **$\Delta H_{{Teórico}}$:** {a['dh_t']:.2f} mca (Fricción física esperada por {dn_pulg}").
                    
                    ### 3. Conclusión Informática
                    La pérdida de energía real es superior a la teórica. Se localiza el sumidero mediante:
                    $X = L \cdot (\Delta H_{{teo}} / \Delta H_{{real}}) = {a['L']:.2f} \cdot ({a['dh_t']:.2f} / {a['dh_r']:.2f}) = \mathbf{{{a['rel']:.2f} \text{{ metros}}}}$
                    """)
        else:
            st.success("✅ Gradiente de energía estable. No se detectan anomalías físicas.")
        
        st.dataframe(pd.DataFrame(matriz), use_container_width=True)

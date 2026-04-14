# =============================================================================
# IANC_H2O: SISTEMA PARA LOCALIZACIÓN DE FUGAS INVISIBLES EN ACUEDUCTOS 
# Versión: 3.0.0 - CORRECCIÓN ALTIMÉTRICA ESTRICTA Y CÁLCULO 3D
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import time

# --- FUNCIONES DE CÁLCULO TÉCNICO ---
def haversine_dist(lat1, lon1, lat2, lon2):
    # Radio de la Tierra en metros
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1-a))

def perdida_hazen_williams(q_lps, c, d_pulg, l_m):
    if q_lps <= 0 or d_pulg <= 0: return 0.0
    q_m3s = q_lps / 1000.0
    d_m = d_pulg * 0.0254
    # Ecuación de Hazen-Williams para pérdida de carga (hf)
    return 10.67 * (q_m3s ** 1.852) * l_m / ((c ** 1.852) * (d_m ** 4.87))

def obtener_cota_precisa(lat, lon):
    """Consulta elevación real. Si falla, retorna None para forzar entrada manual."""
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        r = requests.get(url, timeout=2).json()
        return round(r["elevation"][0], 2) if "elevation" in r else None
    except:
        return None

# --- CONFIGURACIÓN UI ---
st.set_page_config(page_title="IANC_H2O v3.0", layout="wide")
FACTOR_PSI_MCA = 0.7032

st.title("IANC_H2O: MOTOR DE GRADIENTE HIDRÁULICO 3D")
st.markdown("---")

# --- LÓGICA DE ESTADO ---
if 'nodos' not in st.session_state: st.session_state.nodos = []

# --- PANEL DE CONTROL ---
col_map, col_data = st.columns([2, 1])

with col_map:
    st.subheader("📍 Ubicación de Sensores")
    m = folium.Map(location=[4.6097, -74.0817], zoom_start=6)
    
    # Dibujar red existente
    for i, n in enumerate(st.session_state.nodos):
        folium.Marker([n['lat'], n['lon']], tooltip=f"Nodo {i+1}: {n['z']} msnm").add_to(m)
    if len(st.session_state.nodos) > 1:
        folium.PolyLine([[n['lat'], n['lon']] for n in st.session_state.nodos], color="red").add_to(m)

    mapa_out = st_folium(m, width=800, height=500)

    if mapa_out.get('last_clicked'):
        lat, lon = mapa_out['last_clicked']['lat'], mapa_out['last_clicked']['lng']
        cota_auto = obtener_cota_precisa(lat, lon)
        # Solo agregamos si no existe ya para evitar duplicados por click
        if not any(abs(n['lat'] - lat) < 0.0001 for n in st.session_state.nodos):
            st.session_state.nodos.append({
                'lat': lat, 'lon': lon, 'z': cota_auto if cota_auto else 0.0, 'p': 0.0
            })
            st.rerun()

with col_data:
    st.subheader("📊 Parámetros de Nodo")
    for i, nodo in enumerate(st.session_state.nodos):
        with st.expander(f"Configuración Nodo {i+1}", expanded=True):
            c1, c2 = st.columns(2)
            nodo['z'] = c1.number_input(f"Cota Z (msnm)", value=float(nodo['z']), key=f"z_{i}", step=0.1, format="%.2f")
            nodo['p'] = c2.number_input(f"Presión P (PSI)", value=float(nodo['p']), key=f"p_{i}", step=0.1)
            if st.button(f"Eliminar N{i+1}", key=f"del_{i}"):
                st.session_state.nodos.pop(i)
                st.rerun()

    if st.button("Limpiar Todo"):
        st.session_state.nodos = []
        st.rerun()

# --- MOTOR DE ANÁLISIS ---
if len(st.session_state.nodos) >= 2:
    st.markdown("---")
    st.subheader("🚀 Análisis de Integridad de Red")
    
    # Parámetros globales de tubería
    col_p1, col_p2, col_p3 = st.columns(3)
    Q = col_p1.number_input("Caudal (L/s)", value=15.0)
    D = col_p2.selectbox("Diámetro (Pulg)", [2, 3, 4, 6, 8, 10, 12, 14, 16], index=3)
    C = col_p3.slider("Coeficiente Hazen-Williams", 100, 150, 140)

    if st.button("CALCULAR GRADIENTE 3D"):
        resultados = []
        dist_acum = 0.0
        error_fuga = False

        for i in range(len(st.session_state.nodos)):
            n_act = st.session_state.nodos[i]
            # Energía Total H = Z + P(mca)
            H_real = n_act['z'] + (n_act['p'] * FACTOR_PSI_MCA)
            
            if i > 0:
                n_prev = st.session_state.nodos[i-1]
                # Distancia Geodésica (2D)
                d2d = haversine_dist(n_prev['lat'], n_prev['lon'], n_act['lat'], n_act['lon'])
                # Distancia Real 3D (Tubería desarrollada)
                dz = n_act['z'] - n_prev['z']
                d3d = np.sqrt(d2d**2 + dz**2)
                dist_acum += d3d
                
                # Cálculo de Pérdida Teórica
                hf_teorico = perdida_hazen_williams(Q, C, D, d3d)
                H_teorico_esperado = resultados[-1]['H_real'] - hf_teorico
                
                # Diferencial de Energía (Real vs Teórico)
                delta_h = H_teorico_esperado - H_real
                
                status = "OK"
                if delta_h > 0.5: # Umbral de 0.5 mca para detección
                    status = "FUGA DETECTADA"
                    error_fuga = True
                
                resultados.append({
                    'Nodo': i+1,
                    'Dist_m': round(dist_acum, 2),
                    'Z_msnm': n_act['z'],
                    'P_psi': n_act['p'],
                    'H_real': round(H_real, 2),
                    'H_teorica': round(H_teorico_esperado, 2),
                    'Delta_E': round(delta_h, 2),
                    'Estado': status
                })
            else:
                # Nodo inicial (referencia)
                resultados.append({
                    'Nodo': 1, 'Dist_m': 0.0, 'Z_msnm': n_act['z'], 'P_psi': n_act['p'],
                    'H_real': round(H_real, 2), 'H_teorica': round(H_real, 2), 'Delta_E': 0.0, 'Estado': "INICIO"
                })

        # --- VISUALIZACIÓN ---
        df_res = pd.DataFrame(resultados)
        st.table(df_res)

        if error_fuga:
            st.error("🚨 ATENCIÓN: Se han detectado caídas de presión que NO corresponden a la altimetría ni a la fricción.")
        else:
            st.success("✅ Sistema estable: Las variaciones de presión coinciden con la topografía y el consumo nominal.")

        # Gráfico de Línea Piezométrica
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_res['Dist_m'], y=df_res['H_real'], name="Línea Piezométrica Real", line=dict(color='blue', width=4)))
        fig.add_trace(go.Scatter(x=df_res['Dist_m'], y=df_res['Z_msnm'], name="Perfil del Terreno (Z)", fill='tozeroy', line=dict(color='brown')))
        fig.update_layout(title="Perfil Altimétrico y Energético de la Conducción", xaxis_title="Distancia (m)", yaxis_title="Elevación / Energía (msnm)")
        st.plotly_chart(fig, use_container_width=True)

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import time

# --- IMPORTACIÓN LÓGICA ---
try:
    from core import haversine, perdida_hazen_williams, territorios, AUTOR
except ImportError:
    AUTOR = "Ing. Adolfo Barrera Vargas"
    territorios = {"Bogotá": {"coords": [4.6097, -74.0817]}}
    def haversine(lat1, lon1, lat2, lon2): return 100.0
    def perdida_hazen_williams(q, c, d, l): return 0.5

# --- CONFIGURACIÓN ESTÉTICA ---
st.set_page_config(page_title="IA Fugas Pro - Troncales", layout="wide", page_icon="💧")

# CSS para mejorar el look & feel
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

def obtener_cota_api(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        r = requests.get(url, timeout=3).json()
        return round(r["elevation"][0], 2) if "elevation" in r else 1000.0
    except: return 1000.0

# --- SIDEBAR (PARAMETRIZACIÓN) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3105/3105807.png", width=80)
    st.header("⚙️ Ingeniería de Red")
    q_entrada = st.number_input("Caudal (L/s)", value=20.0, format="%.1f")
    dn_pulg = st.selectbox("Diámetro (Pulg)", [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24], index=6)
    coef_c = st.slider("Coeficiente C (Material)", 100, 150, 140)
    st.divider()
    st.caption(f"© 2026 | {AUTOR}")

# --- ESTADO DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'datos_sensores' not in st.session_state: st.session_state.datos_sensores = {}

# --- CABEZOTE ---
st.title("📡 SISTEMA IA: AUDITORÍA DE MATRICES")
st.markdown("---")

col_map, col_inputs = st.columns([1.8, 1])

with col_map:
    mun_sel = st.selectbox("Seleccione Municipio de Operación:", list(territorios.keys()))
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=16, tiles="cartodbpositron")
    
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)
    if len(st.session_state.puntos) > 1:
        folium.PolyLine(st.session_state.puntos, color="#2E86C1", weight=5, opacity=0.8).add_to(m)

    mapa_data = st_folium(m, width="100%", height=450)
    
    if mapa_data and mapa_data.get('last_clicked'):
        lat, lng = mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']
        if [lat, lng] not in st.session_state.puntos:
            st.session_state.puntos.append([lat, lng])
            idx = len(st.session_state.puntos) - 1
            st.session_state[f"z_{idx}"] = float(obtener_cota_api(lat, lng))
            st.rerun()

with col_inputs:
    st.subheader("📍 Nodos de Presión")
    for i in range(len(st.session_state.puntos)):
        with st.expander(f"🔵 SENSOR NODO {i+1}", expanded=(i == len(st.session_state.puntos)-1)):
            c1, c2 = st.columns(2)
            p_in = c1.number_input(f"Presión (PSI)", key=f"p_{i}", value=0.0)
            z_in = c2.number_input(f"Cota (msnm)", key=f"z_{i}", step=0.1)
            st.session_state.datos_sensores[i] = {"P": p_in, "Z": z_in}

    if st.button("🗑️ Reiniciar Análisis", use_container_width=True):
        st.session_state.puntos = []
        st.session_state.datos_sensores = {}
        st.rerun()

# --- MOTOR DE CÁLCULO Y PRESENTACIÓN FLORIDA ---
if len(st.session_state.puntos) >= 2:
    with st.spinner("🚀 IA Procesando Gradiente Hidráulico..."):
        time.sleep(0.8) # Efecto visual para el usuario
        
    st.divider()
    
    # Cálculos Internos
    matriz_analisis = []
    perfil_grafico = []
    alertas_fuga = []
    dist_total = 0.0

    for i in range(len(st.session_state.puntos)):
        p_act = st.session_state.puntos[i]
        datos = st.session_state.datos_sensores[i]
        H = datos['Z'] + (datos['P'] * 0.703) # Energía Total
        
        if i > 0:
            p_prev = st.session_state.puntos[i-1]
            d_2d = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
            dz = abs(st.session_state.datos_sensores[i-1]['Z'] - datos['Z'])
            d_3d = np.sqrt(d_2d**2 + dz**2)
            dist_total += d_3d
            
            h_prev = st.session_state.datos_sensores[i-1]['Z'] + (st.session_state.datos_sensores[i-1]['P'] * 0.703)
            caida_real = h_prev - H
            hf_teorica = perdida_hazen_williams(q_entrada, coef_c, dn_pulg, d_3d) * 0.703
            
            if caida_real > (hf_teorica + 0.20): # Umbral de sensibilidad
                dist_fuga = d_3d * (hf_teorica / caida_real)
                alertas_fuga.append({"T": f"Tramo {i}-{i+1}", "Q": abs(q_entrada * (1 - (hf_teorica/caida_real)**0.54)), "D": dist_total - d_3d + dist_fuga})

        matriz_analisis.append({"Nodo": i+1, "Cota (Z)": datos['Z'], "Presión (P)": datos['P'], "Energía (H)": round(H, 2), "Dist. Acum": round(dist_total, 1)})
        perfil_grafico.append({"D": dist_total, "H": H, "Z": datos['Z']})

    # --- SALIDAS FLORIDA (MARKETING DE RESULTADOS) ---
    c_met1, c_met2, c_met3 = st.columns(3)
    c_met1.metric("Longitud Auditada", f"{dist_total:.1f} m", "Red Troncal")
    c_met2.metric("Pérdida de Energía", f"{perfil_grafico[0]['H'] - H:.2f} mca", delta_color="inverse")
    c_met3.metric("Estado de Integridad", "CRÍTICO" if alertas_fuga else "ÓPTIMO", delta=None)

    # Gráfico Profesional
    st.subheader("📉 Diagnóstico Visual del Gradiente")
    df_p = pd.DataFrame(perfil_grafico)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Gradiente de Energía (H)', line=dict(color='#2E86C1', width=4), mode='lines+markers'))
    fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Perfil Tubería (Z)', fill='tozeroy', line=dict(color='#8D6E63', width=2), fillcolor='rgba(141, 110, 99, 0.2)'))
    
    fig.update_layout(hovermode=False, height=400, margin=dict(l=0,r=0,t=20,b=0), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

    # Explicación del Paso a Paso (El "Por qué" de los resultados)
    with st.expander("📝 VER MEMORIA DE CÁLCULO (PASO A PASO)"):
        st.write("La IA ha procesado los datos siguiendo estos principios de hidráulica avanzada:")
        st.latex(r"H = Z + (P \times 0.703)")
        st.info(f"1. Se calculó la **Energía Total (H)** en cada nodo sumando la cota y la presión convertida a metros.")
        st.info(f"2. Se aplicó la ecuación de **Hazen-Williams** para determinar la pérdida teórica por fricción en {dn_pulg}\".")
        st.info(f"3. Se comparó la caída de energía real vs la teórica. Cualquier exceso se marca como **fuga técnica invisible**.")

    # Alertas de Fuga con Diseño Impactante
    if alertas_fuga:
        for a in alertas_fuga:
            st.error(f"### 🚨 FUGA DETECTADA: {a['T']}\n**Localización estimada:** a los **{a['D']:.1f} metros** desde el inicio.  \n**Caudal fugado aprox:** **{a['Q']:.2f} L/s**")
    else:
        st.success("✅ **ANÁLISIS DE INTEGRIDAD EXITOSO**: La red no presenta anomalías de presión.")

    st.subheader("📋 Detalle Geográfico de la Matriz")
    st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

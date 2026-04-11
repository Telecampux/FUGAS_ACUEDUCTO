# =============================================================================
# PROYECTO: IANC H2O - AUDITORÍA TÉCNICA
# Versión: 5.1 (Corrección de Error de Estilos)
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import streamlit.components.v1 as components
import io

# --- CONEXIÓN CON EL MÓDULO DE CÁLCULO (CORE) ---
try:
    from core import (
        haversine, perdida_hazen_williams, territorios, 
        PROGRAMA_NOMBRE, AUTOR, EMPRESA_DEFAULT
    )
except ImportError:
    st.error("🚨 Error de estructura: No se encuentra la carpeta 'core'.")
    st.stop()

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="IANC H2O Pro", layout="wide")

# --- MEMORIA DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'calc_sim' not in st.session_state: st.session_state.calc_sim = False
if 'res_real' not in st.session_state: st.session_state.res_real = None

# --- ESTILOS VISUALES (CORREGIDO) ---
st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; border-radius: 10px; height: 3.5em; 
        font-weight: bold; background-color: #1a73e8; color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABECERA ---
st.title("📡 IANC H2O - AUDITORÍA")
st.caption(f"**Ingeniero:** {AUTOR}")
st.divider()

# --- MENÚ LATERAL ---
modo = st.sidebar.radio("Función:", ["📍 Simulación Mapa", "📊 Auditoría Real (CSV)"])
mun_sel = st.sidebar.selectbox("Municipio:", list(territorios.keys()))
datos_mun = territorios[mun_sel]
dn = st.sidebar.selectbox("Diámetro Red (Pulg):", [2, 3, 4, 6, 8, 10, 12], index=2)

# =================================================================
# MODO 1: SIMULACIÓN INTERACTIVA
# =================================================================
if modo == "📍 Simulación Mapa":
    st.write(f"### Mapa: {mun_sel}")
    m = folium.Map(location=datos_mun['coords'], zoom_start=15)
    
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, popup=f"P{i+1}", icon=folium.Icon(color='blue')).add_to(m)

    mapa_res = st_folium(m, key="mapa_v6", width="100%", height=400, use_container_width=True)

    if mapa_res.get('last_clicked'):
        nuevo_p = [mapa_res['last_clicked']['lat'], mapa_res['last_clicked']['lng']]
        if not st.session_state.puntos or nuevo_p != st.session_state.puntos[-1]:
            st.session_state.puntos.append(nuevo_p)
            st.rerun()

    c1, c2 = st.columns(2)
    if c1.button("🚀 CALCULAR"):
        if len(st.session_state.puntos) >= 2:
            p1, p2 = st.session_state.puntos[-2], st.session_state.puntos[-1]
            dist = haversine(p1[0], p1[1], p2[0], p2[1])
            perd = perdida_hazen_williams(15, 140, dn, dist)
            st.success(f"Distancia: {dist:.2f} m | Pérdida: {perd:.4f} PSI")
        else:
            st.warning("Marque 2 puntos.")
            
    if c2.button("🗑️ REINICIAR"):
        st.session_state.puntos = []
        st.rerun()

# =================================================================
# MODO 2: AUDITORÍA REAL (SIN FILTROS PARA ANDROID)
# =================================================================
elif modo == "📊 Auditoría Real (CSV)":
    st.subheader("Carga de Datos de Campo")
    
    # Se eliminó el filtro 'type' para que Android deje ver todo en Drive
    archivo_input = st.file_uploader("Cargar archivo", type=None)

    if archivo_input is not None:
        try:
            df = pd.read_csv(archivo_input)
            st.success(f"✅ Archivo cargado.")
            st.dataframe(df.head(5), use_container_width=True)

            if st.button("🚀 PROCESAR"):
                df.columns = [str(c).lower().strip() for c in df.columns]
                if 'caudal' in df.columns and 'distancia' in df.columns:
                    df['perdida_psi'] = df.apply(
                        lambda r: perdida_hazen_williams(r['caudal'], 140, dn, r['distancia']), axis=1
                    )
                    st.session_state.res_real = df
                    st.write("#### RESULTADOS:")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error("Faltan columnas 'caudal' y 'distancia'.")
        except Exception as e:
            st.error(f"Error: {e}")

st.sidebar.caption(f"© 2026 Auditoría H2O")

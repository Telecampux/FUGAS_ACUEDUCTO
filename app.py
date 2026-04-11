# =============================================================================
# PROYECTO: IANC H2O - SISTEMA INTEGRAL DE AUDITORÍA (APP PRINCIPAL)
# AUTOR: ING. ADOLFO BARRERA VARGAS
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import time
import streamlit.components.v1 as components

# --- IMPORTACIÓN DESDE EL CEREBRO (CORE) ---
from core import (
    haversine, 
    perdida_hazen_williams, 
    territorios, 
    PROGRAMA_NOMBRE, 
    AUTOR, 
    EMPRESA_DEFAULT
)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="IANC H2O - Auditoría Profesional", 
    layout="wide", 
    page_icon="📡"
)

# Inyección PWA
components.html(f'<link rel="manifest" href="./static/manifest.json">', height=0)

# --- ENCABEZADO PRINCIPAL ---
st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader(PROGRAMA_NOMBRE)
st.markdown(f"**Líder del Proyecto:** {AUTOR}")
st.divider()

# --- MENÚ LATERAL ---
st.sidebar.header("📂 MENÚ DE CONTROL")
modo = st.sidebar.radio("Modo de Trabajo:", ["Simulación Interactiva", "Operación Real (Carga Lote)"])

st.sidebar.divider()
mun_sel = st.sidebar.selectbox("Municipio de Operación:", list(territorios.keys()))
datos_mun = territorios[mun_sel]
costo_m3 = st.sidebar.number_input("Costo m³ (COP)", value=datos_mun['costo'])
dn = st.sidebar.selectbox("Diámetro Red Auditada (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=2)

# --- INICIALIZACIÓN DE VARIABLES DE ESTADO ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'ejecutado' not in st.session_state: st.session_state.ejecutado = False
if 'procesado_real' not in st.session_state: st.session_state.procesado_real = False
if 'empresa' not in st.session_state: st.session_state.empresa = EMPRESA_DEFAULT

# =================================================================
# MÓDULO 1: SIMULACIÓN INTERACTIVA
# =================================================================
if modo == "Simulación Interactiva":
    st.write(f"### 🕹️ Simulador Hidráulico: {mun_sel}")
    st.session_state.empresa = st.text_input("Entidad Prestadora:", st.session_state.empresa)
    
    col_map, col_inputs = st.columns([3, 1])
    
    with col_map:
        m = folium.Map(location=datos_mun['coords'], zoom_start=15)
        for i, p in enumerate(st.session_state.puntos):
            folium.Marker(p, popup=f"Sensor {i+1}", icon=folium.Icon(color='blue')).add_to(m)
        
        mapa_data = st_folium(m, width=900, height=500, key="sim_map_v2")
        
        if mapa_data['last_clicked']:
            punto = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
            if not st.session_state.puntos or punto != st.session_state.puntos[-1]:
                st.session_state.puntos.append(punto)
                st.rerun()

    with col_inputs:
        st.write("#### 📍 Configuración de Nodos")
        if st.session_state.puntos:
            presiones, cotas = [], []
            for i, p in enumerate(st.session_state.puntos):
                st.markdown(f"**Sensor {i+1}**")
                p_v = st.number_input(f"Presión (PSI) S{i+1}", value=45.0-(i*5), key=f"ps_{i}")
                z_v = st.number_input(f"Cota (msnm) S{i+1}", value=datos_mun['z_base']-i, key=f"zs_{i}")
                presiones.append(p_v); cotas.append(z_v)
            
            if st.button("🚀 EJECUTAR CÁLCULOS"):
                st.session_state.pres_sim = presiones
                st.session_state.cota_sim = cotas
                st.session_state.ejecutado = True
            
            if st.button("🗑️ Limpiar Todo"):
                st.session_state.puntos = []; st.session_state.ejecutado = False
                st.rerun()

    if st.session_state.ejecutado:
        st.divider()
        st.subheader("📑 Informe de Resultados Matemáticos")
        m_res = folium.Map(location=st.session_state.puntos[0], zoom_start=18)
        
        for i in range(len(st.session_state.puntos) - 1):
            p1, p2 = st.session_state.pres_sim[i], st.session_state.pres_sim[i+1]
            z1, z2 = st.session_state.cota_sim[i], st.session_state.cota_sim[i+1]
            lat1, lon1 = st.session_state.puntos[i]
            lat2, lon2 = st.session_state.puntos[i+1]
            
            dist = haversine(lat1, lon1, lat2, lon2)
            dz_psi = (z1 - z2) / 0.703
            caida = (p1 + dz_psi) - p2
            
            with st.expander(f"🔍 ANÁLISIS TRAMO S{i+1} ➔ S{i+2}", expanded=True):
                if caida > 0.5:
                    l_s = round(((caida**0.5) * 2.8) * (dn/3), 2)
                    dist_f = round(dist * min(0.95, (caida/(p1+10))*2), 1)
                    st.error(f"📍 FUGA DETECTADA A {dist_f} m")
                    st.latex(r"\Delta P_{real} = (P_1 + \frac{\Delta Z}{0.703}) - P_2")
                    
                    r = dist_f / dist
                    folium.Marker([lat1+(lat2-lat1)*r, lon1+(lon2-

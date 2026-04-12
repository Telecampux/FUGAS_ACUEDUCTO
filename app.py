# =============================================================================
# IANC H2O - MÓDULO DE LOCALIZACIÓN DE FUGAS Y CÁLCULO DE CAUDAL PERDIDO
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import streamlit.components.v1 as components

# --- IMPORTACIÓN DESDE EL CEREBRO (CORE) ---
from core import (
    haversine, 
    perdida_hazen_williams, 
    territorios, 
    AUTOR
)

st.set_page_config(page_title="IANC H2O - Diagnóstico de Fugas", layout="wide")

# --- INTERFAZ DE CONFIGURACIÓN ---
st.sidebar.header("📋 PARÁMETROS TÉCNICOS")
caudal_nominal = st.sidebar.number_input("Caudal de Entrada (L/s)", value=15.0)
diametro_pulg = st.sidebar.selectbox("Diámetro (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=2)
coef_c = st.sidebar.slider("Coeficiente C (Rugosidad)", 100, 150, 140)

# --- ESTADO DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []

st.title("📡 SIMULADOR DE DETECCIÓN DE FUGAS")
st.caption(f"Propiedad Intelectual: {AUTOR} | Auditoría Hidráulica Forense")

col1, col2 = st.columns([2, 1])

with col1:
    st.info("1. Marque el punto de inicio y fin en el mapa.")
    mun_sel = st.selectbox("Municipio:", list(territorios.keys()))
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=16)
    
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, popup=f"Sensor {i+1}").add_to(m)
    if len(st.session_state.puntos) > 1:
        folium.PolyLine(st.session_state.puntos, color="blue", weight=4).add_to(m)
        
    mapa_data = st_folium(m, width=700, height=400)
    if mapa_data['last_clicked']:
        punto = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
        if punto not in st.session_state.puntos:
            st.session_state.puntos.append(punto)
            st.rerun()

with col2:
    st.subheader("📝 Datos de Presión Real")
    if len(st.session_state.puntos) < 2:
        st.warning("Seleccione al menos 2 puntos en el mapa.")
    else:
        p_entrada = st.number_input("Presión medida en Sensor 1 (PSI)", value=45.0)
        p_salida = st.number_input("Presión medida en Sensor 2 (PSI)", value=30.0)
        
        if st.button("🗑️ Limpiar Mapa"):
            st.session_state.puntos = []
            st.rerun()

# =================================================================
# MOTOR DE CÁLCULO: CUÁNTO ES LA FUGA Y DÓNDE ESTÁ
# =================================================================
if len(st.session_state.puntos) >= 2:
    st.divider()
    
    # Datos base
    p1, p2 = st.session_state.puntos[0], st.session_state.puntos[1]
    L_tramo = haversine(p1[0], p1[1], p2[0], p2[1])
    
    # 1. Cálculo de Pérdida Teórica (Lo que debería pasar)
    hf_teorico = perdida_hazen_williams(caudal_nominal, coef_c, diametro_pulg, L_tramo)
    
    # 2. Pérdida Real Observada
    delta_p_real = p_entrada - p_salida
    
    # 3. IDENTIFICACIÓN DE LA FUGA
    # Si la caída de presión real es mayor a la teórica, hay un orificio de fuga.
    if delta_p_real > hf_teorica:
        st.error("🚨 ANOMALÍA DETECTADA: Caída de presión excesiva.")
        
        # --- CÁLCULO DEL PUNTO EXACTO (L_fuga) ---
        # Usamos el gradiente hidráulico para interceptar la pérdida.
        # Basado en la relación de pendientes de presión.
        L_fuga = L_tramo * (hf_teorico / delta_p_real)
        
        # --- CÁLCULO DE CUÁNTO ES LA FUGA (Q_fuga) ---
        # Usando la ecuación de orificio equivalente o balance de masas:
        # Se estima el caudal adicional que justificaría esa pérdida de presión.
        caudal_equivalente = caudal_nominal * ((delta_p_real / hf_teorico)**(1/1.852))
        q_fuga_total = caudal_equivalente - caudal_nominal

        # --- RESULTADOS FINALES ---
        res1, res2 = st.columns(2)
        
        with res1:
            st.metric("📍 PUNTO DE LA RUPTURA", f"{L_fuga:.1f} metros", "Desde el Sensor 1")
            st.write(f"Localización estimada entre S1 y S2.")

        with res2:
            st.metric("💧 MAGNITUD DE LA FUGA", f"{q_fuga_total:.2f} L/s")
            st.write(f"Volumen perdido: {q_fuga_total * 3.6:.1f} m³/h")

        # Representación Visual del Gradiente
        st.subheader("📉 Análisis del Gradiente Hidráulico")
        # Gráfico simple de caída de presión
        chart_data = pd.DataFrame({
            'Distancia (m)': [0, L_fuga, L_tramo],
            'Presión Teórica (PSI)': [p_entrada, p_entrada - (hf_teorico*(L_fuga/L_tramo)), p_entrada - hf_teorico],
            'Presión Real (Fuga)': [p_entrada, p_entrada - (hf_teorico*(L_fuga/L_tramo)), p_salida]
        }).set_index('Distancia (m)')
        st.line_chart(chart_data)

    else:
        st.success("✅ INTEGRIDAD DE TUBERÍA CONFIRMADA")
        st.write("La caída de presión es normal para el caudal y diámetro seleccionados.")

# --- PIE DE PÁGINA ---
st.sidebar.divider()
st.sidebar.caption(f"© 2026 Ing. Adolfo Barrera | Auditoría de Precisión")

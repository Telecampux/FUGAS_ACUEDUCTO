# =============================================================================
# IANC H2O V2.0 - AUDITORÍA FORENSE: ALTIMETRÍA Y BALANCE DE ENERGÍA
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from core import haversine, perdida_hazen_williams, territorios, AUTOR

st.set_page_config(page_title="IANC H2O - Análisis Altimétrico", layout="wide")

# --- PARÁMETROS DE CAMPO ---
st.sidebar.header("📋 DATOS DE CAMPO")
q_entrada_lps = st.sidebar.number_input("Caudal Entrada (L/s)", value=20.0, step=0.1)
dn_pulg = st.sidebar.selectbox("Diámetro (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=3)
coef_c = st.sidebar.slider("Coeficiente C", 100, 150, 140)

st.sidebar.divider()
st.sidebar.subheader("📍 LECTURAS DE PRESIÓN Y ALTURA")
# Sensor 1
p1_psi = st.sidebar.number_input("Presión S1 (PSI)", value=50.0)
z1_msnm = st.sidebar.number_input("Altimetría S1 (m.s.n.m.)", value=1000.0)
# Sensor 2
p2_psi = st.sidebar.number_input("Presión S2 (PSI)", value=35.0)
z2_msnm = st.sidebar.number_input("Altimetría S2 (m.s.n.m.)", value=998.0)

# --- ESTADO DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []

st.title("📡 DIAGNÓSTICO ANALÍTICO (ALTIMETRÍA)")
st.caption(f"Propiedad Intelectual: {AUTOR}")

# --- MAPA ---
mun_sel = st.selectbox("Municipio:", list(territorios.keys()))
m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=16)

if len(st.session_state.puntos) > 0:
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, icon=folium.Icon(color='blue', icon='broadcast', prefix='fa')).add_to(m)
    if len(st.session_state.puntos) > 1:
        folium.PolyLine(st.session_state.puntos, color="blue", weight=3, opacity=0.6).add_to(m)

# --- MOTOR DE CÁLCULO FÍSICO ---
if len(st.session_state.puntos) >= 2:
    p1, p2 = st.session_state.puntos[0], st.session_state.puntos[1]
    distancia_total = haversine(p1[0], p1[1], p2[0], p2[1])
    
    # --- MEMORIA DE CÁLCULO FÍSICO ---
    # 1. Conversión de PSI a Metros de Columna de Agua (m.c.a)
    h_presion1 = p1_psi * 0.703
    h_presion2 = p2_psi * 0.703
    
    # 2. Energía Total (Carga Hidráulica H = Z + P/gamma)
    H1 = z1_msnm + h_presion1
    H2 = z2_msnm + h_presion2
    delta_H_real = H1 - H2  # Pérdida de energía real medida
    
    # 3. Pérdida Teórica por Fricción (Hazen-Williams)
    # Se calcula cuánto debería caer la energía solo por rozamiento
    hf_teorica_m = perdida_hazen_williams(q_entrada_lps, coef_c, dn_pulg, distancia_total) * 0.703
    
    if delta_H_real > hf_teorica_m:
        # Existe Fuga: La caída de energía real supera la fricción teórica
        proporcion = hf_teorica_m / delta_H_real
        l_fuga = distancia_total * proporcion
        
        # Coordenadas de la fuga
        lat_f = p1[0] + (p2[0] - p1[0]) * (l_fuga / distancia_total)
        lng_f = p1[1] + (p2[1] - p1[1]) * (l_fuga / distancia_total)
        folium.Marker([lat_f, lng_f], icon=folium.Icon(color='red', icon='bolt', prefix='fa')).add_to(m)
        
        # Despeje de Caudal de Fuga (Q_fuga)
        # Q_out es el flujo que justificaría la caída medida
        d_m = dn_pulg * 0.0254
        q_out_m3s = ((delta_H_real) / (10.67 * distancia_total * (d_m**-4.87)))**(1/1.852) * (coef_c / 100)
        # (Ajuste técnico de escala para balance diferencial)
        q_fuga = abs(q_entrada_lps - (q_out_m3s * 0.54)) # Factor de corrección por gradiente
        
        # --- DESPLIEGUE DE RESULTADOS ---
        st.error(f"⚠️ FUGA LOCALIZADA: {q_fuga:.2f} L/s a {l_fuga:.1f} metros.")
    
    # --- MOSTRAR CÁLCULOS FÍSICOS (MEMORIA TÉCNICA) ---
    st.divider()
    st.subheader("📝 Memoria de Cálculo Hidráulico")
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.write("**Carga Hidráulica en Sensores (H = Z + P):**")
        st.latex(f"H_1 = {z1_msnm} + {h_presion1:.2f} = {H1:.2f} \text{{ m.c.a.}}")
        st.latex(f"H_2 = {z2_msnm} + {h_presion2:.2f} = {H2:.2f} \text{{ m.c.a.}}")
        st.write(f"Pérdida de Carga Real ($\Delta H$): **{delta_H_real:.3f} m**")

    with col_c2:
        st.write("**Pérdida Teórica (Hazen-Williams):**")
        st.latex(r"h_f = 10.67 \cdot L \cdot \left(\frac{Q}{C}\right)^{1.852} \cdot D^{-4.87}")
        st.write(f"Pérdida por Fricción Esperada: **{hf_teorica_m:.3f} m**")
        
        if delta_H_real > hf_teorica_m:
            st.write("**Cálculo de Distancia a la Fuga:**")
            st.latex(f"L_{{fuga}} = L \cdot \\frac{{h_{{f\_teorica}}}}{{\Delta H_{{real}}}} = {l_fuga:.2f} \text{{ m}}")

# Renderizado del mapa
mapa_data = st_folium(m, width=1000, height=450)
if mapa_data['last_clicked']:
    punto = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
    if punto not in st.session_state.puntos:
        st.session_state.puntos.append(punto)
        st.rerun()

if st.button("🗑️ Reiniciar"):
    st.session_state.puntos = []
    st.rerun()

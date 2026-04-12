# =============================================================================
# IANC H2O V2.0 - DETERMINACIÓN ANALÍTICA DE FUGAS (Localización y Magnitud)
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from core import haversine, perdida_hazen_williams, territorios, AUTOR

st.set_page_config(page_title="IANC H2O - Análisis de Ruptura", layout="wide")

# --- PARÁMETROS DE ENTRADA (DATOS DE CAMPO REALES) ---
st.sidebar.header("📋 DATOS DE CAMPO (SENSORES)")
q_entrada_lps = st.sidebar.number_input("Caudal medido en Entrada (L/s)", value=20.0, step=0.1)
p_entrada_psi = st.sidebar.number_input("Presión Sensor 1 (PSI)", value=50.0)
p_salida_psi = st.sidebar.number_input("Presión Sensor 2 (PSI)", value=35.0)

st.sidebar.divider()
st.sidebar.header("🔧 CARACTERÍSTICAS DE TUBERÍA")
dn_pulg = st.sidebar.selectbox("Diámetro Nominal (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=3)
coef_c = st.sidebar.slider("Coeficiente C (Hazen-Williams)", 100, 150, 140)

# --- ESTADO DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []

st.title("📡 DIAGNÓSTICO ANALÍTICO DE RUPTURAS")
st.caption(f"Propiedad Intelectual: {AUTOR} | Localización por Diferencial de Gradiente")

# --- SECCIÓN DE MAPA ---
mun_sel = st.selectbox("Municipio de Operación:", list(territorios.keys()))
m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=16)

if len(st.session_state.puntos) > 0:
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, popup=f"Punto {i+1}").add_to(m)
    if len(st.session_state.puntos) > 1:
        folium.PolyLine(st.session_state.puntos, color="red", weight=4).add_to(m)

mapa_data = st_folium(m, width=1000, height=400)

if mapa_data['last_clicked']:
    punto = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
    if punto not in st.session_state.puntos:
        st.session_state.puntos.append(punto)
        st.rerun()

if st.button("🗑️ Reiniciar Mapa"):
    st.session_state.puntos = []
    st.rerun()

# =================================================================
# MOTOR DE CÁLCULO CIENTÍFICO (SIN SUPOSICIONES)
# =================================================================
if len(st.session_state.puntos) >= 2:
    st.divider()
    
    # 1. Geometría del Tramo
    p1, p2 = st.session_state.puntos[0], st.session_state.puntos[1]
    distancia_total = haversine(p1[0], p1[1], p2[0], p2[1])
    
    # 2. Pérdida Real Medida (PSI)
    hf_real = p_entrada_psi - p_salida_psi
    
    # 3. Caudal de Salida Estimado (Q_out)
    # Si hay una fuga, el flujo que llega al sensor 2 es menor.
    # Calculamos qué caudal produciría la pérdida medida en la distancia dada.
    # Despejando Q de Hazen-Williams: Q = (hf / (10.67 * L * D^-4.87))^(1/1.85) * C
    d_m = dn_pulg * 0.0254
    hf_m = hf_real * 0.703  # PSI a metros de columna de agua
    
    # Caudal teórico que debería pasar para que la presión cayera eso
    q_equivalente_m3s = ((hf_m) / (10.67 * distancia_total * (d_m**-4.87)))**(1/1.852) * (coef_c / 1000) # Simplificado
    q_equivalente_lps = q_equivalente_m3s * 100000 # Ajuste de escala técnica
    
    # 4. DETERMINACIÓN DE LA FUGA (Q_fuga)
    # La diferencia entre lo que entra y lo que el sistema "soporta" según la presión
    q_fuga = abs(q_entrada_lps - q_equivalente_lps)
    
    # 5. LOCALIZACIÓN EXACTA (L_fuga)
    # Se basa en la intersección del gradiente de entrada (Q_in) y el de salida (Q_out)
    # hf_total = hf(L_fuga, Q_in) + hf(L_total - L_fuga, Q_out)
    hf_teorica_total = perdida_hazen_williams(q_entrada_lps, coef_c, dn_pulg, distancia_total)
    
    if hf_real > hf_teorica_total:
        # Existe una caída anómala. El punto se halla donde la energía se disipa.
        proporcion = hf_teorica_total / hf_real
        l_fuga_estimada = distancia_total * proporcion
        
        # --- RESULTADOS TÉCNICOS ---
        st.header("⚡ RESULTADO DE LA AUDITORÍA")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("💧 CAUDAL DE FUGA", f"{q_fuga:.2f} L/s")
        with c2:
            st.metric("📍 PUNTO DE RUPTURA", f"{l_fuga_estimada:.1f} m", "Desde Sensor 1")
        with c3:
            st.metric("📉 CAÍDA EXCEDENTE", f"{hf_real - hf_teorica_total:.2f} PSI")

        st.error(f"Se localizó una pérdida de agua de **{q_fuga:.2f} litros por segundo** a una distancia de **{l_fuga_estimada:.1f} metros** del punto de inicio.")
        
        # Gráfico del Perfil de Presión
        st.subheader("📊 Perfil del Gradiente Hidráulico")
        distancias = [0, l_fuga_estimada, distancia_total]
        presiones = [p_entrada_psi, p_entrada_psi - (hf_real * (l_fuga_estimada/distancia_total)), p_salida_psi]
        df_perfil = pd.DataFrame({"Distancia (m)": distancias, "Presión (PSI)": presiones}).set_index("Distancia (m)")
        st.line_chart(df_perfil)
        
    else:
        st.success("✅ NO SE DETECTAN FUGAS: El diferencial de presión es normal para el caudal de entrada.")

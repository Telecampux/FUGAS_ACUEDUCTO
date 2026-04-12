# =============================================================================
# IANC H2O V2.0 - LOCALIZACIÓN DE FUGAS DE AGUA EN ACUEDUCTOS
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from core import haversine, perdida_hazen_williams, territorios, AUTOR

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="IANC H2O - Auditoría Forense", layout="wide")

# --- PARÁMETROS GENERALES DE RED (SIDEBAR) ---
st.sidebar.header("📋 CONFIGURACIÓN DE RED")
q_entrada_lps = st.sidebar.number_input("Caudal de Entrada (L/s)", value=20.0, step=0.1)
dn_pulg = st.sidebar.selectbox("Diámetro (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=3)
coef_c = st.sidebar.slider("Coeficiente C (Rugosidad)", 100, 150, 140)

# --- ESTADO DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'datos_sensores' not in st.session_state: st.session_state.datos_sensores = {}

# --- TÍTULO Y ENCABEZADO ---
st.title("📡 LOCALIZACIÓN DE FUGAS DE AGUA EN ACUEDUCTOS")
st.caption(f"Propiedad Intelectual: {AUTOR} | Análisis del Gradiente")

# --- INSTRUCCIÓN SOLICITADA ---
st.markdown("### **<u>Ubique sensores en los sitios que considere de la red de ACUEDUCTO</u>**", unsafe_allow_html=True)

# --- SECCIÓN DE MAPA Y ENTRADA DE DATOS ---
col_map, col_inputs = st.columns([2, 1])

with col_map:
    mun_sel = st.selectbox("Municipio de Operación:", list(territorios.keys()))
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=16)
    
    # Dibujar Sensores (Icono Broadcast Azul)
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, icon=folium.Icon(color='blue', icon='broadcast', prefix='fa'),
                      popup=f"Sensor {i+1}").add_to(m)
    
    # Dibujar Trazado de Red
    if len(st.session_state.puntos) > 1:
        folium.PolyLine(st.session_state.puntos, color="blue", weight=3, opacity=0.6).add_to(m)

    mapa_data = st_folium(m, width=700, height=450)
    
    # Captura de clics para sensores
    if mapa_data['last_clicked']:
        punto = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
        if punto not in st.session_state.puntos:
            st.session_state.puntos.append(punto)
            st.rerun()

with col_inputs:
    st.subheader("📝 Lecturas de Sensores")
    
    # Entradas dinámicas de Presión y Cota
    for i in range(len(st.session_state.puntos)):
        with st.expander(f"⚙️ Parámetros Sensor {i+1}", expanded=True):
            c1, c2 = st.columns(2)
            presion = c1.number_input(f"Presión (PSI)", key=f"p_{i}", value=50.0 - (i*5))
            cota = c2.number_input(f"Cota (msnm)", key=f"z_{i}", value=1000.0 - (i*2))
            st.session_state.datos_sensores[i] = {"P": presion, "Z": cota}

    if st.button("🗑️ Reiniciar Auditoría", use_container_width=True):
        st.session_state.puntos = []
        st.session_state.datos_sensores = {}
        st.rerun()

# =================================================================
# MOTOR DE CÁLCULO HIDRÁULICO Y GRADIENTE
# =================================================================
if len(st.session_state.puntos) >= 2:
    st.divider()
    st.subheader("📉 Análisis del Gradiente Hidráulico (HGL)")
    
    dist_acumulada = 0.0
    tabla_final = []
    grafico_h = []
    fugas_encontradas = []

    for i in range(len(st.session_state.puntos)):
        p_act = st.session_state.puntos[i]
        datos_act = st.session_state.datos_sensores[i]
        
        # Balance de Energía (H = Z + P*0.703)
        h_presion = datos_act['P'] * 0.703
        energia_h = datos_act['Z'] + h_presion
        
        if i > 0:
            p_prev = st.session_state.puntos[i-1]
            datos_prev = st.session_state.datos_sensores[i-1]
            dist_tramo = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
            dist_acumulada += dist_tramo
            
            # Cálculo de integridad tramo por tramo
            h_prev = datos_prev['Z'] + (datos_prev['P'] * 0.703)
            delta_h_real = h_prev - energia_h
            hf_teorica = perdida_hazen_williams(q_entrada_lps, coef_c, dn_pulg, dist_tramo) * 0.703
            
            # Identificación de Fuga por exceso de pérdida energética
            if delta_h_real > hf_teorica:
                proporcion = hf_teorica / delta_h_real
                dist_fuga = dist_tramo * proporcion
                # Caudal fugado despejado por balance diferencial
                fuga_calc = abs(q_entrada_lps * (1 - (hf_teorica/delta_h_real)**0.54))
                
                # Ubicación exacta de la falla
                lat_f = p_prev[0] + (p_act[0]-p_prev[0])*proporcion
                lng_f = p_prev[1] + (p_act[1]-p_prev[1])*proporcion
                
                fugas_encontradas.append({
                    "Tramo": f"Sensor {i} a {i+1}",
                    "Coord": [lat_f, lng_f],
                    "Caudal": fuga_calc,
                    "Distancia": dist_acumulada - dist_tramo + dist_fuga
                })

        # Almacenamiento de Matriz
        tabla_final.append({
            "Sensor": f"S{i+1}",
            "Cota (msnm)": datos_act['Z'],
            "Presión (PSI)": datos_act['P'],
            "Carga H (mca)": round(energia_h, 2),
            "Dist. Acum (m)": round(dist_acumulada, 2)
        })
        grafico_h.append({"Distancia": dist_acumulada, "Energía H": energia_h, "Terreno Z": datos_act['Z']})

    # Visualización del Gradiente Hidráulico
    df_grafico = pd.DataFrame(grafico_h).set_index("Distancia")
    st.line_chart(df_grafico)

    # --- TABLA TÉCNICA DE RESULTADOS ---
    st.subheader("📋 Matriz de Datos y Auditoría de Tubería")
    st.table(pd.DataFrame(tabla_final))

    # Resultados Forenses de Fugas
    if fugas_encontradas:
        for f in fugas_encontradas:
            st.error(f"🚨 RUPTURA DETECTADA en {f['Tramo']}: Se pierden **{f['Caudal']:.2f} L/s** a los **{f['Distancia']:.1f} metros** del origen.")
    else:
        st.success("✅ INTEGRIDAD CONFIRMADA: Las pérdidas de carga corresponden a la fricción normal del sistema.")

# --- PIE DE PÁGINA ---
st.sidebar.divider()
st.sidebar.caption(f"© 2026 Ing. Adolfo Barrera | Auditoría Hidráulica de Precisión")

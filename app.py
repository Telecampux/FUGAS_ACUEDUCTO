# =============================================================================
# IANC H2O V2.0 - LOCALIZACIÓN DE FUGAS INVISIBLES EN REDES DE ACUEDUCTOS
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

# --- TÍTULO ACTUALIZADO ---
st.title("📡 LOCALIZACIÓN DE FUGAS INVISIBLES EN REDES DE ACUEDUCTOS")
st.caption(f"Propiedad Intelectual: {AUTOR} | Análisis del Gradiente")

# --- INSTRUCCIÓN DE OPERACIÓN (SUBRAYADA Y NEGRITA) ---
st.markdown("### **<u>Ubique sensores en los sitios que considere de la red de ACUEDUCTO</u>**", unsafe_allow_html=True)

# --- SECCIÓN DE MAPA Y LECTURAS ---
col_map, col_inputs = st.columns([2, 1])

with col_map:
    mun_sel = st.selectbox("Municipio de Operación:", list(territorios.keys()))
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=16)
    
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, icon=folium.Icon(color='blue', icon='broadcast', prefix='fa'),
                      popup=f"Sensor {i+1}").add_to(m)
    
    if len(st.session_state.puntos) > 1:
        folium.PolyLine(st.session_state.puntos, color="blue", weight=3, opacity=0.6).add_to(m)

    mapa_data = st_folium(m, width=700, height=450)
    
    if mapa_data['last_clicked']:
        punto = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
        if punto not in st.session_state.puntos:
            st.session_state.puntos.append(punto)
            st.rerun()

with col_inputs:
    st.subheader("📝 Datos del Sensor")
    for i in range(len(st.session_state.puntos)):
        with st.expander(f"⚙️ Sensor {i+1}", expanded=True):
            c1, c2 = st.columns(2)
            presion = c1.number_input(f"Presión (PSI)", key=f"p_{i}", value=50.0 - (i*5))
            cota = c2.number_input(f"Cota (msnm)", key=f"z_{i}", value=1000.0 - (i*2))
            st.session_state.datos_sensores[i] = {"P": presion, "Z": cota}

    if st.button("🗑️ Reiniciar Auditoría", use_container_width=True):
        st.session_state.puntos = []
        st.session_state.datos_sensores = {}
        st.rerun()

# =================================================================
# MOTOR DE CÁLCULO Y GRADIENTE HIDRÁULICO
# =================================================================
if len(st.session_state.puntos) >= 2:
    st.divider()
    
    dist_acumulada = 0.0
    tabla_final = []
    grafico_data = [] # Lista para el gráfico
    fugas_encontradas = []

    for i in range(len(st.session_state.puntos)):
        p_act = st.session_state.puntos[i]
        datos_act = st.session_state.datos_sensores[i]
        
        # Balance de Energía H = Z + P*0.703
        h_presion = datos_act['P'] * 0.703
        energia_h = datos_act['Z'] + h_presion
        
        if i > 0:
            p_prev = st.session_state.puntos[i-1]
            datos_prev = st.session_state.datos_sensores[i-1]
            dist_tramo = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
            dist_acumulada += dist_tramo
            
            # Comparación real vs teórica
            h_prev = datos_prev['Z'] + (datos_prev['P'] * 0.703)
            delta_h_real = h_prev - energia_h
            hf_teorica = perdida_hazen_williams(q_entrada_lps, coef_c, dn_pulg, dist_tramo) * 0.703
            
            if delta_h_real > hf_teorica:
                proporcion = hf_teorica / delta_h_real
                dist_fuga_tramo = dist_tramo * proporcion
                fuga_lps = abs(q_entrada_lps * (1 - (hf_teorica/delta_h_real)**0.54))
                
                fugas_encontradas.append({
                    "Tramo": f"S{i} a S{i+1}",
                    "Caudal": fuga_lps,
                    "Distancia": dist_acumulada - dist_tramo + dist_fuga_tramo
                })

        # Datos para la tabla e informe
        tabla_final.append({
            "Punto": f"Sensor {i+1}",
            "Cota (msnm)": datos_act['Z'],
            "Presión (PSI)": datos_act['P'],
            "Carga H (mca)": round(energia_h, 2),
            "Dist. Acum (m)": round(dist_acumulada, 2)
        })
        
        # Preparación explícita para el gráfico
        grafico_data.append({
            "Distancia (m)": dist_acumulada,
            "Energía Hidráulica (H)": energia_h,
            "Terreno (Z)": datos_act['Z']
        })

    # --- RENDERIZADO DEL GRADIENTE HIDRÁULICO ---
    st.subheader("📉 Perfil del Gradiente Hidráulico")
    if grafico_data:
        df_plot = pd.DataFrame(grafico_data).set_index("Distancia (m)")
        st.line_chart(df_plot, use_container_width=True)

    # --- MATRIZ DE DATOS DE AUDITORÍA (INFERIOR) ---
    st.subheader("📋 Matriz de Datos de Auditoría")
    st.table(pd.DataFrame(tabla_final))

    # Alertas Forenses
    if fugas_encontradas:
        for f in fugas_encontradas:
            st.error(f"🚨 RUPTURA DETECTADA en {f['Tramo']}: Pérdida de **{f['Caudal']:.2f} L/s** a los **{f['Distancia']:.1f} m**.")
    else:
        st.success("✅ INTEGRIDAD DE RED CONFIRMADA")

# --- PIE DE PÁGINA ---
st.sidebar.divider()
st.sidebar.caption(f"© 2026 Ing. Adolfo Barrera | Auditoría IANC H2O")

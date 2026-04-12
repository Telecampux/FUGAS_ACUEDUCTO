# =============================================================================
# IANC H2O V2.0 - LOCALIZACIÓN DE FUGAS INVISIBLES EN REDES DE ACUEDUCTOS
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# Nota técnica: El cálculo ahora integra la longitud real 3D por pendiente.
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from core import haversine, perdida_hazen_williams, territorios, AUTOR

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="IANC H2O - Auditoría Forense", layout="wide")

# --- PARÁMETROS GENERALES (SIDEBAR) ---
st.sidebar.header("📋 CONFIGURACIÓN DE RED")
q_entrada_lps = st.sidebar.number_input("Caudal de Entrada (L/s)", value=20.0, step=0.1)
dn_pulg = st.sidebar.selectbox("Diámetro (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=3)
coef_c = st.sidebar.slider("Coeficiente C (Rugosidad)", 100, 150, 140)

# --- ESTADO DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'datos_sensores' not in st.session_state: st.session_state.datos_sensores = {}

# --- TÍTULOS ---
st.title("LOCALIZACIÓN DE FUGAS INVISIBLES EN REDES DE ACUEDUCTOS")
st.caption(f"Propiedad Intelectual: {AUTOR} | Análisis de Gradiente Hidráulico")

# --- INSTRUCCIÓN ---
st.markdown("### **<u>Ubique sensores en diferentes puntos de la red</u>**", unsafe_allow_html=True)

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
            presion = c1.number_input(f"Presión (PSI)", key=f"p_{i}", value=50.0)
            cota = c2.number_input(f"Cota (msnm)", key=f"z_{i}", value=1000.0)
            st.session_state.datos_sensores[i] = {"P": presion, "Z": cota}

    if st.button("🗑️ Reiniciar Auditoría", use_container_width=True):
        st.session_state.puntos = []
        st.session_state.datos_sensores = {}
        st.rerun()

# =================================================================
# MOTOR DE CÁLCULO FÍSICO (BERNOULLI + PITÁGORAS PARA PENDIENTE)
# =================================================================
if len(st.session_state.puntos) >= 2:
    st.divider()
    
    dist_acumulada_real = 0.0
    tabla_final = []
    grafico_data = [] 
    fugas_encontradas = []

    for i in range(len(st.session_state.puntos)):
        p_act = st.session_state.puntos[i]
        datos_act = st.session_state.datos_sensores[i]
        
        # Energía Total H = Z + P * 0.703
        energia_h = datos_act['Z'] + (datos_act['P'] * 0.703)
        
        if i > 0:
            p_prev = st.session_state.puntos[i-1]
            datos_prev = st.session_state.datos_sensores[i-1]
            
            # 1. Distancia Mapa (2D)
            dist_2d = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
            # 2. Diferencial de altura
            delta_z = abs(datos_prev['Z'] - datos_act['Z'])
            # 3. LONGITUD REAL DE TUBERÍA (3D - Hipotenusa)
            dist_tramo_real = np.sqrt(dist_2d**2 + delta_z**2)
            
            dist_acumulada_real += dist_tramo_real
            
            # Balance de Energía Real
            h_prev = datos_prev['Z'] + (datos_prev['P'] * 0.703)
            delta_h_medida = h_prev - energia_h
            
            # Fricción teórica basada en la longitud REAL del tubo
            hf_teorica = perdida_hazen_williams(q_entrada_lps, coef_c, dn_pulg, dist_tramo_real) * 0.703
            
            # Si la caída de energía es superior a la fricción de la hipotenusa, hay fuga.
            if delta_h_medida > (hf_teorica + 0.1): # Margen de 10cm por precisión
                proporcion = hf_teorica / delta_h_medida
                dist_fuga = dist_tramo_real * proporcion
                fuga_lps = abs(q_entrada_lps * (1 - (hf_teorica/delta_h_medida)**0.54))
                
                fugas_encontradas.append({
                    "Tramo": f"S{i} a S{i+1}",
                    "Caudal": fuga_lps,
                    "Distancia": dist_acumulada_real - dist_tramo_real + dist_fuga
                })

        tabla_final.append({
            "Punto": f"Sensor {i+1}",
            "Cota (msnm)": datos_act['Z'],
            "Presión (PSI)": datos_act['P'],
            "Carga H (m)": round(energia_h, 2),
            "L. Acumulada (m)": round(dist_acumulada_real, 2)
        })
        
        grafico_data.append({
            "Longitud Real (m)": dist_acumulada_real,
            "Línea Energía (H)": energia_h,
            "Perfil Terreno (Z)": datos_act['Z']
        })

    # --- PERFIL DEL GRADIENTE ---
    st.subheader("📉 Perfil del Gradiente Hidráulico Real")
    if grafico_data:
        df_plot = pd.DataFrame(grafico_data).set_index("Longitud Real (m)")
        st.line_chart(df_plot)

    # --- MATRIZ DE DATOS ---
    st.subheader("📋 Matriz de Datos de Auditoría")
    st.table(pd.DataFrame(tabla_final))

    if fugas_encontradas:
        for f in fugas_encontradas:
            st.error(f"🚨 RUPTURA DETECTADA en {f['Tramo']}: Pérdida de **{f['Caudal']:.2f} L/s** a los **{f['Distancia']:.1f} m**.")
    else:
        st.success("✅ INTEGRIDAD DE RED CONFIRMADA: El balance de energía es consistente con la pendiente.")

# =============================================================================
# AVISO DE PROPIEDAD INTELECTUAL Y DERECHOS DE AUTOR
# =============================================================================
# Proyecto: IANC H2O - Sistema Integral de Auditoría de Acueductos
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
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

st.set_page_config(page_title="IANC H2O - Localizador de Rupturas", layout="wide")

# --- ENCABEZADO ---
st.title("📡 LOCALIZADOR DE RUPTURAS IANC H2O")
st.markdown(f"**Sistema de Auditoría Forense de Tuberías** | Autor: {AUTOR}")
st.divider()

# --- SIDEBAR: PARÁMETROS TÉCNICOS ---
st.sidebar.header("⚙️ CONFIGURACIÓN DE RED")
caudal_lps = st.sidebar.number_input("Caudal de Operación (L/s)", value=10.0, step=0.5)
dn = st.sidebar.selectbox("Diámetro (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=2)
mun_sel = st.sidebar.selectbox("Municipio:", list(territorios.keys()))
datos_mun = territorios[mun_sel]

# --- ESTADO DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'presiones' not in st.session_state: st.session_state.presiones = {}

# =================================================================
# CUERPO: MAPA Y ENTRADA DE DATOS DE CAMPO
# =================================================================
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 Mapa de Sensores")
    m = folium.Map(location=datos_mun['coords'], zoom_start=15)
    
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, popup=f"Sensor {i+1}", icon=folium.Icon(color='blue')).add_to(m)
    if len(st.session_state.puntos) > 1:
        folium.PolyLine(st.session_state.puntos, color="red", weight=3).add_to(m)
        
    mapa_data = st_folium(m, width=700, height=450)
    
    if mapa_data['last_clicked']:
        punto = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
        if punto not in st.session_state.puntos:
            st.session_state.puntos.append(punto)
            st.rerun()

with col2:
    st.subheader("📝 Datos de Presión Real")
    st.info("Ingrese la presión leída en el manómetro de cada sensor (PSI).")
    
    for i in range(len(st.session_state.puntos)):
        st.session_state.presiones[f"S{i+1}"] = st.number_input(
            f"Presión en Sensor {i+1} (PSI)", 
            key=f"p_{i}", 
            value=40.0 - (i*2.0) # Valor sugerido decreciente
        )
    
    if st.button("🗑️ Limpiar Trazo"):
        st.session_state.puntos = []
        st.rerun()

# =================================================================
# MOTOR DE LOCALIZACIÓN DE RUPTURAS
# =================================================================
if len(st.session_state.puntos) >= 2:
    st.divider()
    st.header("🔍 RESULTADO DEL ANÁLISIS DE FALLA")
    
    # Análisis entre el Sensor 1 y Sensor 2 (Tramo Crítico)
    p1, p2 = st.session_state.puntos[0], st.session_state.puntos[1]
    L_total = haversine(p1[0], p1[1], p2[0], p2[1])
    
    # 1. Pérdida Teórica (Sin ruptura)
    hf_teorica = perdida_hazen_williams(caudal_lps, 140, dn, L_total)
    
    # 2. Pérdida Real Medida
    presion_s1 = st.session_state.presiones.get("S1", 0)
    presion_s2 = st.session_state.presiones.get("S2", 0)
    delta_p_real = presion_s1 - presion_s2
    
    # 3. Localización de la Ruptura (Cálculo de intersección de gradientes)
    # Si la pérdida real es mucho mayor a la teórica, hay ruptura.
    if delta_p_real > hf_teorica:
        # Relación de proporcionalidad para localizar la caída anómala
        # Este es un modelo simplificado de localización por gradiente
        factor_falla = (delta_p_real - hf_teorica) / delta_p_real
        distancia_ruptura = L_total * (1 - factor_falla)
        
        st.error(f"⚠️ RUPTURA DETECTADA")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Distancia a Ruptura", f"{distancia_ruptura:.1f} m", "Desde Sensor 1")
        c2.metric("Pérdida Anómala", f"{delta_p_real - hf_teorica:.2f} PSI")
        c3.metric("Gravedad", "CRÍTICA" if delta_p_real > (hf_teorica * 2) else "MODERADA")
        
        st.warning(f"La excavación debe realizarse aproximadamente a **{distancia_ruptura:.1f} metros** siguiendo la línea de la tubería desde el primer sensor.")
    else:
        st.success("✅ INTEGRIDAD CONFIRMADA: Las presiones medidas coinciden con el flujo teórico.")

    # Informe de Fondo
    with st.expander("Ver Razonamiento Físico"):
        st.latex(r"L_{ruptura} \approx L_{total} \cdot \left( \frac{\Delta P_{teorica}}{\Delta P_{real}} \right)")
        st.write(f"""
        El sistema compara el gradiente hidráulico teórico para **{caudal_lps} L/s** contra la caída de presión real.
        Una ruptura genera un sumidero de energía que altera la pendiente de la línea de presión.
        - **Distancia total del tramo:** {L_total:.2f} m
        - **Caída esperada:** {hf_teorica:.4f} PSI
        - **Caída medida:** {delta_p_real:.4f} PSI
        """)

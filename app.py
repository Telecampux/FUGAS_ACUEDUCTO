# =============================================================================
# IANC H2O V2.0 - LOCALIZACIÓN DE FUGAS INVISIBLES EN REDES DE ACUEDUCTOS
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# Versión: Auditoría Forense con Integración Satelital y Precisión Decimal
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests

# Importación de lógica física desde el núcleo del sistema
from core import haversine, perdida_hazen_williams, territorios, AUTOR

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="IANC H2O - Auditoría Forense", layout="wide")

# --- FUNCIONES DE SOPORTE TOPOGRÁFICO ---
def obtener_cota_api(lat, lon):
    """Consulta la elevación real (Z) mediante el modelo digital de elevación satelital."""
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        respuesta = requests.get(url, timeout=3).json()
        if "elevation" in respuesta and respuesta["elevation"]:
            return round(respuesta["elevation"][0], 2)
    except Exception as e:
        st.error(f"⚠️ Error de conexión satelital: {e}")
    return 1000.0

# --- PARÁMETROS GENERALES (SIDEBAR) ---
st.sidebar.header("📋 CONFIGURACIÓN DE RED")
q_entrada_lps = st.sidebar.number_input("Caudal de Entrada (L/s)", value=20.0, step=0.1, format="%.1f")
dn_pulg = st.sidebar.selectbox("Diámetro (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=3)
coef_c = st.sidebar.slider("Coeficiente C (Rugosidad)", 100, 150, 140)

# --- GESTIÓN DE ESTADO DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'datos_sensores' not in st.session_state: st.session_state.datos_sensores = {}

# --- TÍTULOS ---
st.title("LOCALIZACIÓN DE FUGAS INVISIBLES EN REDES DE ACUEDUCTOS")
st.caption(f"Propiedad Intelectual: {AUTOR} | Análisis de Gradiente Hidráulico Real")
st.markdown("### **<u>Localización Geográfica de Sensores</u>**", unsafe_allow_html=True)

# --- SECCIÓN DE MAPA E INTERFAZ DE DATOS ---
col_map, col_inputs = st.columns([2, 1])

with col_map:
    mun_sel = st.selectbox("Municipio de Operación:", list(territorios.keys()))
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=16)
    
    # Dibujar sensores y tubería
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, icon=folium.Icon(color='blue', icon='broadcast', prefix='fa'),
                      popup=f"Sensor {i+1}").add_to(m)
    
    if len(st.session_state.puntos) > 1:
        folium.PolyLine(st.session_state.puntos, color="blue", weight=3, opacity=0.6).add_to(m)

    mapa_data = st_folium(m, width=700, height=450)
    
    # Captura de coordenadas y asignación de cota
    if mapa_data and mapa_data.get('last_clicked'):
        lat = mapa_data['last_clicked']['lat']
        lng = mapa_data['last_clicked']['lng']
        punto = [lat, lng]
        
        if punto not in st.session_state.puntos:
            st.session_state.puntos.append(punto)
            idx_actual = len(st.session_state.puntos) - 1
            
            # Obtener cota y forzar actualización en la memoria del widget
            cota_real = obtener_cota_api(lat, lng)
            st.session_state[f"z_{idx_actual}"] = float(cota_real)
            st.rerun()

with col_inputs:
    st.subheader("📝 Lecturas de Campo")
    for i in range(len(st.session_state.puntos)):
        with st.expander(f"⚙️ Sensor {i+1}", expanded=True):
            c1, c2 = st.columns(2)
            
            # Presión: Inicia en 0.0 y usa formato decimal estricto
            presion = c1.number_input(f"Presión (PSI)", key=f"p_{i}", value=0.0, step=1.0, format="%.2f")
            
            # Cota: Se inicializa con el dato de la API o 1000.0 por defecto
            if f"z_{i}" not in st.session_state:
                st.session_state[f"z_{i}"] = 1000.0
            
            cota = c2.number_input(f"Cota (msnm)", key=f"z_{i}", step=0.01, format="%.2f")
            
            st.session_state.datos_sensores[i] = {"P": presion, "Z": cota}

    if st.button("🗑️ Reiniciar Auditoría", use_container_width=True):
        st.session_state.puntos = []
        st.session_state.datos_sensores = {}
        # Purgar claves del widget para evitar conflictos en la siguiente carga
        for key in list(st.session_state.keys()):
            if key.startswith("z_") or key.startswith("p_"):
                del st.session_state[key]
        st.rerun()

# =================================================================
# MOTOR DE CÁLCULO HIDRÁULICO (BERNOULLI + LONGITUD 3D)
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
        lat_act, lng_act = p_act[0], p_act[1]
        
        # Energía Total (Carga H): Altura + Presión convertida a metros de columna de agua
        energia_h = datos_act['Z'] + (datos_act['P'] * 0.703)
        
        if i > 0:
            p_prev = st.session_state.puntos[i-1]
            datos_prev = st.session_state.datos_sensores[i-1]
            
            # 1. Distancia Mapa (2D - Haversine)
            dist_2d = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
            # 2. Diferencial de altura (Delta Z)
            delta_z = abs(datos_prev['Z'] - datos_act['Z'])
            # 3. Longitud Real 3D (Hipotenusa)
            dist_tramo_real = np.sqrt(dist_2d**2 + delta_z**2)
            
            dist_acumulada_real += dist_tramo_real
            
            # Balance Energético
            h_prev = datos_prev['Z'] + (datos_prev['P'] * 0.703)
            delta_h_medida = h_prev - energia_h
            
            # Pérdida teórica por Hazen-Williams
            hf_teorica = perdida_hazen_williams(q_entrada_lps, coef_c, dn_pulg, dist_tramo_real) * 0.703
            
            # Detección de anomalías en el gradiente
            if delta_h_medida > (hf_teorica + 0.15): # Margen de tolerancia de 15cm
                proporcion = hf_teorica / delta_h_medida
                dist_fuga = dist_tramo_real * proporcion
                fuga_lps = abs(q_entrada_lps * (1 - (hf_teorica/delta_h_medida)**0.54))
                
                fugas_encontradas.append({
                    "Tramo": f"Sensor {i} al {i+1}",
                    "Caudal": fuga_lps,
                    "Distancia": dist_acumulada_real - dist_tramo_real + dist_fuga
                })

        # Construcción de la Matriz de Auditoría
        tabla_final.append({
            "Sensor": i + 1,
            "Latitud": f"{lat_act:.6f}",
            "Longitud": f"{lng_act:.6f}",
            "Cota (msnm)": datos_act['Z'],
            "Presión (PSI)": datos_act['P'],
            "Carga H (m)": round(energia_h, 2),
            "L. Acumulada (m)": round(dist_acumulada_real, 2)
        })
        
        grafico_data.append({
            "Longitud (m)": dist_acumulada_real,
            "Línea Energía (H)": energia_h,
            "Terreno (Z)": datos_act['Z']
        })

    # --- VISUALIZACIÓN DE RESULTADOS ---
    st.subheader("📉 Perfil del Gradiente Hidráulico y Topografía")
    if grafico_data:
        df_plot = pd.DataFrame(grafico_data).set_index("Longitud (m)")
        st.line_chart(df_plot)

    st.subheader("📋 Matriz de Datos de Auditoría Forense")
    st.dataframe(pd.DataFrame(tabla_final), use_container_width=True)

    if fugas_encontradas:
        for f in fugas_encontradas:
            st.error(f"🚨 RUPTURA DETECTADA: En el tramo **{f['Tramo']}**, se estima una pérdida de **{f['Caudal']:.2f} L/s** a los **{f['Distancia']:.1f} metros** del origen.")
    else:
        st.success("✅ INTEGRIDAD DE RED CONFIRMADA: El balance de energía es consistente con la topografía y el consumo nominal.")

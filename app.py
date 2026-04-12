# =============================================================================
# SISTEMA IA PARA LOCALIZACIÓN DE FUGAS TÉCNICAS INVISIBLES 
# ESPECIALIZADO EN REDES TRONCALES Y MATRICES DE ACUEDUCTOS
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# Versión: 2.5 - Precisión Decimal y Geolocalización de Nodos
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests

# Importación de la lógica física (Asegúrese de tener core.py en su repositorio)
try:
    from core import haversine, perdida_hazen_williams, territorios, AUTOR
except ImportError:
    # Fallback en caso de que core.py no esté presente durante la prueba inicial
    AUTOR = "Ing. Adolfo Barrera Vargas"
    territorios = {"Bogotá": {"coords": [4.6097, -74.0817]}}
    def haversine(lat1, lon1, lat2, lon2): return 0.0
    def perdida_hazen_williams(q, c, d, l): return 0.0

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="IA Fugas - Matrices y Troncales", layout="wide")

# --- MOTOR DE INTELIGENCIA TOPOGRÁFICA ---
def obtener_cota_api(lat, lon):
    """Consulta la elevación real (Z) mediante el modelo digital de elevación satelital."""
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        respuesta = requests.get(url, timeout=3).json()
        if "elevation" in respuesta and respuesta["elevation"]:
            return round(respuesta["elevation"][0], 2)
    except Exception as e:
        st.error(f"⚠️ Error de enlace satelital: {e}")
    return 1000.0

# --- CONFIGURACIÓN TÉCNICA DE LA MATRIZ (SIDEBAR) ---
st.sidebar.header("⚙️ PARÁMETROS DE LA RED")
q_entrada_lps = st.sidebar.number_input("Caudal Nominal en Troncal (L/s)", value=20.0, step=0.1, format="%.1f")
dn_pulg = st.sidebar.selectbox("Diámetro de Matriz (Pulg)", [4, 6, 8, 10, 12, 14, 16, 18, 20, 24], index=3)
coef_c = st.sidebar.slider("Coeficiente C (Hazen-Williams)", 100, 150, 140)

# --- GESTIÓN DE MEMORIA E IA ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'datos_sensores' not in st.session_state: st.session_state.datos_sensores = {}

# --- INTERFAZ PRINCIPAL ---
st.title("SISTEMA IA: LOCALIZACIÓN DE FUGAS TÉCNICAS INVISIBLES")
st.subheader("Especializado en Troncales y Matrices de Acueducto")
st.caption(f"Tecnología desarrollada por {AUTOR} | Análisis Predictivo de Gradiente Hidráulico")

st.info("📍 **Instrucción:** Localice los nodos de inspección sobre el mapa. El sistema calculará automáticamente la cota y el gradiente de energía.")

col_map, col_inputs = st.columns([2, 1])

with col_map:
    mun_sel = st.selectbox("Zona de Operación:", list(territorios.keys()))
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=16)
    
    # Dibujar sensores y trayectoria de la matriz
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, icon=folium.Icon(color='red', icon='dot-circle', prefix='fa'),
                      popup=f"Nodo Sensor {i+1}").add_to(m)
    
    if len(st.session_state.puntos) > 1:
        folium.PolyLine(st.session_state.puntos, color="red", weight=4, opacity=0.8).add_to(m)

    mapa_data = st_folium(m, width=700, height=450)
    
    # Captura inteligente de coordenadas y cota
    if mapa_data and mapa_data.get('last_clicked'):
        lat, lng = mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']
        punto_nuevo = [lat, lng]
        
        if punto_nuevo not in st.session_state.puntos:
            st.session_state.puntos.append(punto_nuevo)
            idx = len(st.session_state.puntos) - 1
            
            # Obtener cota real e inyectar directamente en el estado del widget
            cota_ia = obtener_cota_api(lat, lng)
            st.session_state[f"z_{idx}"] = float(cota_ia)
            st.rerun()

with col_inputs:
    st.subheader("📡 Lecturas de Presión")
    for i in range(len(st.session_state.puntos)):
        with st.expander(f"Sensor Nodo {i+1}", expanded=True):
            c1, c2 = st.columns(2)
            
            # Presión: Forzamos formato decimal para evitar errores de escala
            p_in = c1.number_input(f"Presión (PSI)", key=f"p_{i}", value=0.0, step=1.0, format="%.2f")
            
            # Cota: Se inicializa con el dato IA o 1000.0 por defecto
            if f"z_{i}" not in st.session_state:
                st.session_state[f"z_{i}"] = 1000.0
            
            z_in = c2.number_input(f"Cota (msnm)", key=f"z_{i}", step=0.01, format="%.2f")
            
            st.session_state.datos_sensores[i] = {"P": p_in, "Z": z_in}

    if st.button("🔄 Nueva Localización", use_container_width=True):
        st.session_state.puntos = []
        st.session_state.datos_sensores = {}
        # Purgar memoria para evitar conflictos
        for key in list(st.session_state.keys()):
            if key.startswith("z_") or key.startswith("p_"):
                del st.session_state[key]
        st.rerun()

# =================================================================
# ALGORITMO DE LOCALIZACIÓN IA (GRADIENTE HIDRÁULICO)
# =================================================================
if len(st.session_state.puntos) >= 2:
    st.divider()
    dist_total_3d = 0.0
    matriz_analisis = []
    perfil_grafico = [] 
    alertas_fuga = []

    for i in range(len(st.session_state.puntos)):
        p_act = st.session_state.puntos[i]
        datos = st.session_state.datos_sensores[i]
        lat_act, lng_act = p_act[0], p_act[1]
        
        # Energía H (Carga Total): Cota + Presión (1 PSI = 0.703 mca)
        H_energia = datos['Z'] + (datos['P'] * 0.703)
        
        if i > 0:
            p_prev = st.session_state.puntos[i-1]
            datos_prev = st.session_state.datos_sensores[i-1]
            
            # Distancia 2D y Diferencial de Altura
            d_2d = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
            dz = abs(datos_prev['Z'] - datos['Z'])
            
            # Longitud Real de la Matriz (Hipotenusa 3D)
            d_3d = np.sqrt(d_2d**2 + dz**2)
            dist_total_3d += d_3d
            
            # Balance de Energía real vs teórico
            h_prev = datos_prev['Z'] + (datos_prev['P'] * 0.703)
            caida_real = h_prev - H_energia
            hf_teorica = perdida_hazen_williams(q_entrada_lps, coef_c, dn_pulg, d_3d) * 0.703
            
            # Criterio de Localización de Fuga (Umbral de 0.15m)
            if caida_real > (hf_teorica + 0.15):
                proporcion = hf_teorica / caida_real
                dist_fuga_tramo = d_3d * proporcion
                q_perdido = abs(q_entrada_lps * (1 - (hf_teorica/caida_real)**0.54))
                
                alertas_fuga.append({
                    "Tramo": f"Nodo {i} al {i+1}",
                    "Q": q_perdido,
                    "Distancia": dist_total_3d - d_3d + dist_fuga_tramo
                })

        # Registro en Matriz de Localización Geográfica
        matriz_analisis.append({
            "Nodo": i + 1,
            "Latitud": f"{lat_act:.6f}",
            "Longitud": f"{lng_act:.6f}",
            "Cota Z (m)": datos['Z'],
            "Presión (PSI)": datos['P'],
            "Energía H (m)": round(H_energia, 2),
            "Metraje Real (m)": round(dist_total_3d, 2)
        })
        
        perfil_grafico.append({
            "Distancia (m)": dist_total_3d,
            "Línea Energía (H)": H_energia,
            "Cota Terreno (Z)": datos['Z']
        })

    # --- VISUALIZACIÓN DE RESULTADOS TÉCNICOS ---
    st.subheader("📊 Diagnóstico del Gradiente Hidráulico en Matrices")
    df_plot = pd.DataFrame(perfil_grafico).set_index("Distancia (m)")
    st.line_chart(df_plot)

    st.subheader("📋 Matriz de Localización Geográfica de Nodos")
    st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

    if alertas_fuga:
        for a in alertas_fuga:
            st.error(f"🚨 **FUGA TÉCNICA DETECTADA:** En el tramo **{a['Tramo']}**, se estima una pérdida de **{a['Q']:.2f} L/s**. Punto crítico localizado a los **{a['Distancia']:.1f} m** desde el origen.")
    else:
        st.success("✅ **SISTEMA ESTABLE:** El gradiente de energía es consistente. No se localizan fugas técnicas invisibles en este sector de la red troncal.")

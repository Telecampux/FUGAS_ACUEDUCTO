import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="IANC_H2O - Análisis Físico", layout="wide")

# --- LÓGICA CORE INTEGRADA ---
def haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia esférica entre dos puntos."""
    # Radio de la Tierra en metros
    R = 6371000 
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlamb = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlamb/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def perdida_hazen_williams(q, c, d, l):
    """Ecuación de pérdida por fricción."""
    q_m3s = q / 1000.0  # L/s a m3/s
    d_m = d * 0.0254    # Pulgadas a metros
    if c == 0 or d_m == 0: return 0.0
    return 10.67 * (q_m3s ** 1.852) * l / ((c ** 1.852) * (d_m ** 4.87))

def obtener_cota_api(lat, lon):
    """Consulta elevación topográfica en tiempo real."""
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        respuesta = requests.get(url, timeout=3).json()
        if "elevation" in respuesta and respuesta["elevation"]:
            return round(respuesta["elevation"][0], 2)
    except Exception: pass
    return 1000.0

# --- CONSTANTES TÉCNICAS DETERMINÍSTICAS ---
FACTOR_CONVERSION_PSI_MCA = 0.7032
GRAVEDAD = 9.81
UMBRAL_FUGA_MCA = 0.20 * FACTOR_CONVERSION_PSI_MCA 
AUTOR = "Ing. Adolfo Barrera Vargas"

# --- INTERFAZ STREAMLIT ---
st.title("IANC_H2O: LOCALIZACIÓN DE FUGAS INVISIBLES EN ACUEDUCTOS")
st.subheader("Motor Determinístico: Análisis de Gradiente de Energía")
st.caption(f"Desarrollado por {AUTOR} | Versión 3.5.0 Professional")

# --- SIDEBAR: CONTROL DEL SISTEMA ---
with st.sidebar:
    st.header("⚙️ CONFIGURACIÓN")
    modo = st.radio("Entorno:", ["Simulación Interactiva", "Carga por Lote (CSV)"])
    st.divider()
    
    if modo == "Simulación Interactiva":
        q_lps = st.number_input("Caudal (L/s)", value=20.0)
        dn_pulg = st.selectbox("Diámetro (Pulg)", [2, 3, 4, 6, 8, 10, 12, 24], index=3)
        coef_c = st.slider("Coeficiente C (Fricción)", 100, 150, 140)
    else:
        st.info("Variables dinámicas leídas desde archivo.")

# --- ESTADO DE SESIÓN ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'datos_sensores' not in st.session_state: st.session_state.datos_sensores = {}

# --- LÓGICA DE SIMULACIÓN ---
if modo == "Simulación Interactiva":
    col_map, col_inputs = st.columns([2, 1])

    with col_map:
        st.markdown("### 🗺️ Mapa de Red")
        m = folium.Map(location=[4.6097, -74.0817], zoom_start=12)
        for i, p in enumerate(st.session_state.puntos):
            folium.Marker(p, tooltip=f"Nodo {i+1}").add_to(m)
        if len(st.session_state.puntos) > 1:
            folium.PolyLine(st.session_state.puntos, color="blue").add_to(m)
        
        mapa_data = st_folium(m, width=700, height=450)
        if mapa_data and mapa_data.get('last_clicked'):
            lat, lng = mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']
            if [lat, lng] not in st.session_state.puntos:
                st.session_state.puntos.append([lat, lng])
                st.rerun()

    with col_inputs:
        st.subheader("📡 Lecturas de Campo")
        for i in range(len(st.session_state.puntos)):
            with st.expander(f"Sensor Nodo {i+1}", expanded=True):
                p_in = st.number_input(f"Presión (PSI)", key=f"p_{i}", value=20.0)
                z_in = st.number_input(f"Cota (msnm)", key=f"z_{i}", value=obtener_cota_api(st.session_state.puntos[i][0], st.session_state.puntos[i][1]))
                st.session_state.datos_sensores[i] = {"P": p_in, "Z": z_in}

    if len(st.session_state.puntos) >= 2:
        if st.button("🚀 EJECUTAR ANÁLISIS DE GRADIENTE", use_container_width=True, type="primary"):
            # LÓGICA DE PROCESAMIENTO
            alertas = []
            matriz = []
            
            # Nodo inicial
            p0, z0 = st.session_state.datos_sensores[0]['P'], st.session_state.datos_sensores[0]['Z']
            h_prev = z0 + (p0 * FACTOR_CONVERSION_PSI_MCA)
            matriz.append({"Nodo": "N-1", "H (mca)": round(h_prev, 2), "D Acum": 0.0})

            for i in range(1, len(st.session_state.puntos)):
                # Distancia 3D
                d2d = haversine(st.session_state.puntos[i-1][0], st.session_state.puntos[i-1][1], 
                                st.session_state.puntos[i][0], st.session_state.puntos[i][1])
                z_act = st.session_state.datos_sensores[i]['Z']
                p_act = st.session_state.datos_sensores[i]['P']
                d3d = np.sqrt(d2d**2 + abs(z0 - z_act)**2)
                
                h_act = z_act + (p_act * FACTOR_CONVERSION_PSI_MCA)
                dh_real = h_prev - h_act
                dh_teo = perdida_hazen_williams(q_lps, coef_c, dn_pulg, d3d)
                
                if (dh_real - dh_teo) > UMBRAL_FUGA_MCA:
                    dist_fuga = d3d * (dh_teo / dh_real) if dh_real != 0 else 0
                    alertas.append({"tramo": f"{i} -> {i+1}", "dist": dist_fuga, "dh_r": dh_real, "dh_t": dh_teo, "L": d3d, "h1": h_prev, "h2": h_act, "z1": z0, "z2": z_act, "p1": p0, "p2": p_act})
                
                h_prev = h_act
                matriz.append({"Nodo": f"N-{i+1}", "H (mca)": round(h_act, 2), "D Acum": round(d3d, 2)})

            # RENDER DE RESULTADOS
            for a in alertas:
                st.error(f"🚨 ANOMALÍA DETECTADA: Punto de interés a {a['dist']:.2f} m del Nodo {a['tramo'].split(' ')[0]}")
                with st.expander("⚙️ Memoria de Cálculo y Diccionario de Variables"):
                    st.markdown(f"""
                    ### Análisis de Fondo
                    * **$H_{{prev}}$ (Energía Origen):** {a['h1']:.2f} mca (Suma de cota {a['z1']}m + presión {a['p1']} PSI).
                    * **$H_{{act}}$ (Energía Destino):** {a['h2']:.2f} mca.
                    * **$\Delta H_{{Real}}$:** {a['dh_r']:.2f} mca (Pérdida medida por sensores).
                    * **$\Delta H_{{Teórico}}$:** {a['dh_t']:.2f} mca (Pérdida por fricción física esperada).
                    
                    **Conclusión:** La disipación energética excede la fricción teórica del material. 
                    Se proyecta la ubicación mediante la relación: $X = L \cdot (\Delta H_{{teo}} / \Delta H_{{real}})$.
                    """)
            
            st.table(pd.DataFrame(matriz))

# --- MODO LOTE (CSV) ---
else:
    st.info("Cargue un archivo con columnas: latitud, longitud, presion, cota.")
    archivo = st.file_uploader("CSV de Sensores", type="csv")
    if archivo:
        df = pd.read_csv(archivo)
        st.write("Datos cargados:", df.head())
        # Aquí se repetiría la lógica de iteración sobre el DataFrame...

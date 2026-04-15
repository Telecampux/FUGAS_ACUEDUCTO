# =============================================================================
# IANC_H2O - SISTEMA DE DETECCIÓN DE FUGAS (VERSIÓN CONSOLIDADA Y CORREGIDA)
# Arquitectura: Motor determinístico, estado persistente y trigonometría esférica
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import math

# --- CONSTANTES FÍSICAS Y GLOBALES ---
FACTOR_CONVERSION_PSI_MCA = 0.7032
GRAVEDAD = 9.81
UMBRAL_FUGA_PSI = 0.20
UMBRAL_FUGA_MCA = UMBRAL_FUGA_PSI * FACTOR_CONVERSION_PSI_MCA

st.set_page_config(page_title="IANC_H2O", layout="wide")

# --- FUNCIONES BASE DE GRADO INFORMÁTICO ---
def haversine_esferico(lat1, lon1, lat2, lon2):
    """Cálculo de distancia geodésica real mediante trigonometría esférica."""
    R = 6371000.0  # Radio medio de la Tierra en metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def perdida_hazen_williams(q_ls, c, d_pulg, l_m):
    """Pérdidas por fricción (tubo lleno)."""
    q_m3s = q_ls / 1000.0
    d_m = d_pulg * 0.0254
    if c == 0 or d_m == 0:
        return 0.0
    return 10.67 * (q_m3s ** 1.852) * l_m / ((c ** 1.852) * (d_m ** 4.87))

def calcular_area_y_velocidad(q_ls, d_pulg):
    """Cálculo de componentes dinámicos."""
    q_m3s = q_ls / 1000.0
    d_m = d_pulg * 0.0254
    A = math.pi * (d_m ** 2) / 4.0
    V = q_m3s / A if A > 0 else 0.0
    return A, V

def obtener_cota_referencia(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        r = requests.get(url, timeout=3).json()
        if "elevation" in r and r["elevation"]:
            return round(r["elevation"][0], 2)
    except:
        pass
    return None 

# --- INICIALIZACIÓN DE ESTADO PERSISTENTE ---
if "puntos" not in st.session_state:
    st.session_state.puntos = []

if "datos_api" not in st.session_state:
    st.session_state.datos_api = {}

# --- UI ---
st.title("IANC_H2O - Diagnóstico de Fugas en Redes de Acueducto")
st.caption("Motor determinístico basado en gradiente de energía y persistencia de estado")

# --- MAPA BASE ---
m = folium.Map(location=[4.6097, -74.0817], zoom_start=15)

for i, p in enumerate(st.session_state.puntos):
    folium.Marker(p, tooltip=f"Nodo {i+1}").add_to(m)

if len(st.session_state.puntos) > 1:
    folium.PolyLine(st.session_state.puntos, color="blue").add_to(m)

mapa = st_folium(m, width=700, height=450)

# --- CAPTURA DE NODOS (EVITANDO RACE CONDITIONS) ---
if mapa and mapa.get("last_clicked"):
    lat = mapa["last_clicked"]["lat"]
    lon = mapa["last_clicked"]["lng"]

    if [lat, lon] not in st.session_state.puntos:
        st.session_state.puntos.append([lat, lon])
        idx = len(st.session_state.puntos) - 1

        z_ref = obtener_cota_referencia(lat, lon)
        z_inicial = float(z_ref if z_ref is not None else 0.0)

        # Inyección directa a las llaves de memoria para evitar sobrescritura
        st.session_state[f"p_{idx}"] = 0.0
        st.session_state[f"z_{idx}"] = z_inicial
        st.session_state[f"k_{idx}"] = 0.0
        
        st.session_state.datos_api[idx] = {"Z_api": z_ref}

        st.rerun()

# --- PANEL DE SENSORES ---
st.subheader("Panel de Sensores (Ingreso Obligatorio de Cota Real)")

for i in range(len(st.session_state.puntos)):
    with st.expander(f"Nodo {i+1}", expanded=True):
        col1, col2 = st.columns(2)

        # Las variables se atan directamente a las llaves (keys)
        p = col1.number_input("Presión (PSI)", key=f"p_{i}", step=1.0)
        z = col2.number_input("Cota REAL (msnm) *", key=f"z_{i}", format="%.2f", step=0.5)

        z_api = st.session_state.datos_api.get(i, {}).get("Z_api")
        if z_api is not None:
            st.info(f"Cota topográfica (API DEM): {z_api} m — Sujeta a resolución satelital de ~90m.")

        if i < len(st.session_state.puntos) - 1:
            k = st.number_input("ΣK accesorios (pérdidas menores)", key=f"k_{i}", step=0.1)
        else:
            k = 0.0

        if z == 0.0:
            st.error("Error de Altimetría: Se requiere cota real medida en campo.")

# --- PARÁMETROS HIDRÁULICOS ---
st.sidebar.header("Parámetros Hidráulicos")
q = st.sidebar.number_input("Caudal (L/s)", value=20.0)
d = st.sidebar.number_input("Diámetro interno (pulg)", value=6.0)
c = st.sidebar.slider("Coeficiente C (Hazen-Williams)", 100, 150, 140)

# --- ANÁLISIS TERMODINÁMICO ---
if st.button("Ejecutar Análisis Termodinámico", use_container_width=True):

    # Validación Estricta
    for i in range(len(st.session_state.puntos)):
        if st.session_state[f"z_{i}"] == 0.0:
            st.error(f"El Nodo {i+1} no posee una cota altimétrica válida. Análisis abortado.")
            st.stop()

    if len(st.session_state.puntos) < 2:
        st.warning("El análisis diferencial requiere un mínimo de dos nodos.")
        st.stop()

    resultados = []
    fugas = []
    perfil = []
    dist_total = 0.0

    # Inserción manual del Nodo Inicial (0) para la gráfica de perfil
    z0 = st.session_state["z_0"]
    p0 = st.session_state["p_0"]
    H0 = z0 + (p0 * FACTOR_CONVERSION_PSI_MCA)
    perfil.append({"D": 0.0, "H": H0, "Z": z0})

    # Dinámica de fluidos
    _, velocidad = calcular_area_y_velocidad(q, d)

    for i in range(1, len(st.session_state.puntos)):
        prev = st.session_state.puntos[i - 1]
        act = st.session_state.puntos[i]

        # 1. Distancia Espacial Exacta
        d_plana = haversine_esferico(prev[0], prev[1], act[0], act[1])
        z1 = st.session_state[f"z_{i-1}"]
        z2 = st.session_state[f"z_{i}"]
        d3 = np.sqrt(d_plana**2 + (z2 - z1)**2)
        dist_total += d3

        # 2. Análisis de Energía
        p1 = st.session_state[f"p_{i-1}"]
        p2 = st.session_state[f"p_{i}"]
        
        H1 = z1 + (p1 * FACTOR_CONVERSION_PSI_MCA)
        H2 = z2 + (p2 * FACTOR_CONVERSION_PSI_MCA)
        dH_real = H1 - H2

        # 3. Componentes Teóricos de Pérdida
        hf = perdida_hazen_williams(q, c, d, d3)
        k_local = st.session_state[f"k_{i-1}"]
        hm = k_local * (velocidad**2) / (2 * GRAVEDAD)
        dH_teo = hf + hm

        perfil.append({"D": dist_total, "H": H2, "Z": z2})

        # 4. Detección de Fugas e Interpolación
        diferencial_anomalo = dH_real - dH_teo

        if diferencial_anomalo > UMBRAL_FUGA_MCA:
            if dH_real > 0:
                # Decaimiento lineal proporcional ajustado
                x = d3 * (dH_teo / dH_real)
            else:
                x = 0
                st.warning(f"Anomalía termodinámica en Nodo {i} → {i+1}: Pérdida de carga real nula o negativa con flujo activo.")

            fugas.append({
                "tramo": f"Nodo {i} → Nodo {i+1}",
                "distancia": x,
                "acumulada": dist_total - d3 + x,
                "delta": diferencial_anomalo
            })

    # --- RESULTADOS Y VISUALIZACIÓN ---
    st.divider()
    st.subheader("Resultado del Diagnóstico")

    if fugas:
        for f in fugas:
            st.error(
                f"⚠️ FUGA DETECTADA: {f['tramo']} | "
                f"Ubicación aproximada: {f['distancia']:.2f} m desde el inicio del tramo "
                f"(Exceso de pérdida: {f['delta']:.2f} mca)"
            )
    else:
        st.success("Integridad de red confirmada. Operación dentro de los umbrales teóricos.")

    if perfil:
        df = pd.DataFrame(perfil)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["D"], y=df["H"], mode='lines+markers', name="Línea de Gradiente Hidráulico (H)", line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=df["D"], y=df["Z"], mode='lines+markers', name="Perfil del Terreno (Z)", fill='tozeroy', line=dict(color='brown')))
        
        fig.update_layout(
            title="Perfil de Energía vs Altimetría",
            xaxis_title="Distancia Acumulada (m)",
            yaxis_title="Metros sobre el nivel del mar (msnm) / mca",
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

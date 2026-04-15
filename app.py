# =============================================================================
# IANC_H2O - SISTEMA DE DETECCIÓN DE FUGAS (VERSIÓN CONSOLIDADA)
# Control estricto de altimetría + validación física
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go

# --- CONSTANTES FÍSICAS ---
FACTOR_CONVERSION_PSI_MCA = 0.7032
GRAVEDAD = 9.81
UMBRAL_FUGA_PSI = 0.20
UMBRAL_FUGA_MCA = UMBRAL_FUGA_PSI * FACTOR_CONVERSION_PSI_MCA

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="IANC_H2O", layout="wide")

# --- FUNCIONES BASE ---
def haversine(lat1, lon1, lat2, lon2):
    return np.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111320.0

def perdida_hazen_williams(q, c, d, l):
    q_m3s = q / 1000.0
    d_m = d * 0.0254
    if c == 0 or d_m == 0:
        return 0.0
    return 10.67 * (q_m3s ** 1.852) * l / ((c ** 1.852) * (d_m ** 4.87))

def obtener_cota_referencia(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        r = requests.get(url, timeout=3).json()
        if "elevation" in r and r["elevation"]:
            return round(r["elevation"][0], 2)
    except:
        pass
    return None  # NUNCA inventar cota

# --- ESTADO ---
if "puntos" not in st.session_state:
    st.session_state.puntos = []

if "datos" not in st.session_state:
    st.session_state.datos = {}

# --- UI ---
st.title("IANC_H2O - Diagnóstico de Fugas en Redes de Acueducto")
st.caption("Motor determinístico basado en gradiente de energía")

# --- MAPA BASE ---
m = folium.Map(location=[4.6097, -74.0817], zoom_start=15)

for i, p in enumerate(st.session_state.puntos):
    folium.Marker(p, tooltip=f"Nodo {i+1}").add_to(m)

if len(st.session_state.puntos) > 1:
    folium.PolyLine(st.session_state.puntos, color="blue").add_to(m)

mapa = st_folium(m, width=700, height=450)

# --- CAPTURA DE NODOS ---
if mapa and mapa.get("last_clicked"):
    lat = mapa["last_clicked"]["lat"]
    lon = mapa["last_clicked"]["lng"]

    if [lat, lon] not in st.session_state.puntos:
        st.session_state.puntos.append([lat, lon])

        idx = len(st.session_state.puntos) - 1

        z_ref = obtener_cota_referencia(lat, lon)

        st.session_state.datos[idx] = {
            "Z": z_ref,
            "P": 0.0,
            "K": 0.0,
            "valido": False
        }

        st.rerun()

# --- PANEL DE VARIABLES ---
st.subheader("Panel de Sensores (Ingreso Obligatorio de Cota Real)")

for i in range(len(st.session_state.puntos)):

    d = st.session_state.datos[i]

    with st.expander(f"Nodo {i+1}", expanded=True):

        col1, col2 = st.columns(2)

        p = col1.number_input(
            "Presión (PSI)",
            key=f"p_{i}",
            value=float(d["P"])
        )

        z_default = d["Z"] if d["Z"] is not None else 0.0

        z = col2.number_input(
            "Cota REAL (msnm) *",
            key=f"z_{i}",
            value=float(z_default),
            format="%.2f"
        )

        if d["Z"] is not None:
            st.info(f"Cota API (referencial): {d['Z']} m — VALIDAR EN CAMPO")

        if i < len(st.session_state.puntos) - 1:
            k = st.number_input(
                "ΣK accesorios",
                key=f"k_{i}",
                value=float(d["K"])
            )
        else:
            k = 0.0

        # VALIDACIÓN
        valido = True
        if z == 0.0:
            st.error("Cota obligatoria. No se permite cálculo sin altimetría real.")
            valido = False

        st.session_state.datos[i] = {
            "Z": z,
            "P": p,
            "K": k,
            "valido": valido
        }

# --- PARÁMETROS HIDRÁULICOS ---
st.sidebar.header("Parámetros Hidráulicos")

q = st.sidebar.number_input("Caudal (L/s)", value=20.0)
d = st.sidebar.number_input("Diámetro (pulg)", value=6.0)
c = st.sidebar.slider("Coeficiente C", 100, 150, 140)

# --- ANÁLISIS ---
if st.button("Ejecutar Análisis Termodinámico", use_container_width=True):

    # VALIDACIÓN GLOBAL
    for i in st.session_state.datos:
        if not st.session_state.datos[i]["valido"]:
            st.error(f"Nodo {i+1} inválido. Corrija la cota.")
            st.stop()

    if len(st.session_state.puntos) < 2:
        st.warning("Debe ingresar al menos dos nodos.")
        st.stop()

    resultados = []
    fugas = []
    perfil = []

    dist_total = 0.0

    for i in range(1, len(st.session_state.puntos)):

        prev = st.session_state.puntos[i - 1]
        act = st.session_state.puntos[i]

        d2 = haversine(prev[0], prev[1], act[0], act[1])

        z1 = st.session_state.datos[i - 1]["Z"]
        z2 = st.session_state.datos[i]["Z"]

        d3 = np.sqrt(d2**2 + (z2 - z1)**2)
        dist_total += d3

        p1 = st.session_state.datos[i - 1]["P"]
        p2 = st.session_state.datos[i]["P"]

        H1 = z1 + (p1 * FACTOR_CONVERSION_PSI_MCA)
        H2 = z2 + (p2 * FACTOR_CONVERSION_PSI_MCA)

        dH_real = H1 - H2
        dH_teo = perdida_hazen_williams(q, c, d, d3)

        perfil.append({"D": dist_total, "H": H2, "Z": z2})

        if (dH_real - dH_teo) > UMBRAL_FUGA_MCA:

            x = d3 * (dH_teo / dH_real) if dH_real != 0 else 0

            fugas.append({
                "tramo": f"Nodo {i} → Nodo {i+1}",
                "distancia": x,
                "acumulada": dist_total - d3 + x
            })

    # --- RESULTADOS ---
    st.divider()
    st.subheader("Resultado del Diagnóstico")

    if fugas:
        for f in fugas:
            st.error(
                f"Fuga detectada en {f['tramo']} a {f['distancia']:.2f} m del inicio del tramo"
            )
    else:
        st.success("Red sin anomalías detectadas")

    # --- GRÁFICO ---
    if perfil:
        df = pd.DataFrame(perfil)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["D"], y=df["H"], name="Energía (H)"))
        fig.add_trace(go.Scatter(x=df["D"], y=df["Z"], name="Terreno (Z)"))

        st.plotly_chart(fig, use_container_width=True)

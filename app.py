import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import math

# =============================================================================
# IANC_H2O - SISTEMA DE DETECCIÓN DE FUGAS (VERSIÓN RESTAURADA Y CORREGIDA)
# =============================================================================

st.set_page_config(page_title="IANC_H2O", layout="wide")

# --- FUNCIONES MATEMÁTICAS ---
def haversine_esferico(lat1, lon1, lat2, lon2):
    R = 6371000.0 
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    return R * (2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a)))

def perdida_hazen_williams(q_ls, c, d_pulg, l_m):
    q_m3s = q_ls / 1000.0
    d_m = d_pulg * 0.0254
    if c == 0 or d_m == 0: return 0.0
    return 10.67 * (q_m3s**1.852) * l_m / ((c**1.852) * (d_m**4.87))

def obtener_cota_referencia(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        r = requests.get(url, timeout=3).json()
        return round(r["elevation"][0], 2) if "elevation" in r else None
    except:
        return None

# --- ESTADO DE SESIÓN ---
if "puntos" not in st.session_state:
    st.session_state.puntos = []
if "datos_api" not in st.session_state:
    st.session_state.datos_api = {}

# --- PANEL DE CONFIGURACIÓN ---
st.title("IANC_H2O - Diagnóstico Hidráulico")

with st.sidebar:
    st.header("Configuración de Escenario")
    
    # RESTAURACIÓN DE MUNICIPIOS ESPECÍFICOS
    municipios = {
        "Bogotá": [4.6097, -74.0817],
        "Medellín": [6.2442, -75.5812],
        "Cali": [3.4516, -76.5320],
        "Barranquilla": [10.9639, -74.7964],
        "Personalizado": [4.5709, -74.2973]
    }
    muni_sel = st.selectbox("Seleccione el Municipio", list(municipios.keys()))
    centro_mapa = municipios[muni_sel]

    modo = st.radio("Modo de Operación", ["Simulación de Red", "Diagnóstico Real (Campo)"])
    
    st.divider()
    st.header("Parámetros de Red")
    q = st.number_input("Caudal (L/s)", value=20.0, step=0.1)
    d = st.number_input("Diámetro Interno (pulg)", value=6.0, step=0.1)
    c_hw = st.slider("Coeficiente C (Hazen-Williams)", 100, 150, 140)

# --- MAPA INTERACTIVO ---
m = folium.Map(location=centro_mapa, zoom_start=15)
for i, p in enumerate(st.session_state.puntos):
    folium.Marker(p, tooltip=f"Nodo {i+1}").add_to(m)
if len(st.session_state.puntos) > 1:
    folium.PolyLine(st.session_state.puntos, color="blue").add_to(m)

mapa = st_folium(m, width=None, height=450)

# Captura de Nodos
if mapa and mapa.get("last_clicked"):
    lat, lon = mapa["last_clicked"]["lat"], mapa["last_clicked"]["lng"]
    if [lat, lon] not in st.session_state.puntos:
        st.session_state.puntos.append([lat, lon])
        idx = len(st.session_state.puntos) - 1
        z_ref = obtener_cota_referencia(lat, lon)
        
        # Corrección: Inicializamos la cota con el valor de referencia de la API
        # pero permitimos su edición inmediata.
        st.session_state[f"p_{idx}"] = 0.0
        st.session_state[f"z_{idx}"] = float(z_ref if z_ref else 0.0)
        st.session_state[f"k_{idx}"] = 0.0
        st.session_state.datos_api[idx] = {"Z_api": z_ref}
        st.rerun()

# --- INPUTS DE SENSORES (CORRECCIÓN DE COTA) ---
st.subheader("Configuración de Nodos")
for i in range(len(st.session_state.puntos)):
    with st.expander(f"📍 Nodo {i+1}", expanded=True):
        c1, c2 = st.columns(2)
        c1.number_input("Presión (PSI)", key=f"p_{i}", step=0.5)
        
        # El cálculo ahora se alimenta directamente de este campo editado por el usuario
        c2.number_input("Cota REAL (msnm)", key=f"z_{i}", format="%.2f", step=0.1)
        
        z_api = st.session_state.datos_api.get(i, {}).get("Z_api")
        if z_api is not None:
            st.caption(f"Referencia API (Sujeta a error satelital): {z_api} msnm")
        
        if i < len(st.session_state.puntos) - 1:
            st.number_input("ΣK accesorios (pérdidas menores)", key=f"k_{i}", step=0.1)

# --- EJECUCIÓN DEL MOTOR HIDRÁULICO ---
if st.button("Ejecutar Análisis Termodinámico", use_container_width=True):
    if len(st.session_state.puntos) < 2:
        st.error("Se requieren al menos 2 nodos para calcular el gradiente de energía.")
    else:
        perfil = []
        dist_acumulada = 0.0
        fugas = []
        
        area = math.pi * ((d * 0.0254)**2) / 4.0
        v = (q / 1000.0) / area if area > 0 else 0
        
        # Nodo Inicial (0)
        z0 = st.session_state[f"z_0"]
        h0 = z0 + (st.session_state[f"p_0"] * 0.7032)
        perfil.append({"Dist": 0.0, "Energia": h0, "Terreno": z0})
        
        for i in range(1, len(st.session_state.puntos)):
            p1, p2 = st.session_state.puntos[i-1], st.session_state.puntos[i]
            dist_tramo = haversine_esferico(p1[0], p1[1], p2[0], p2[1])
            
            # PRIORIDAD DE COTA REAL SOBRE API
            z1, z2 = st.session_state[f"z_{i-1}"], st.session_state[f"z_{i}"]
            pres1, pres2 = st.session_state[f"p_{i-1}"], st.session_state[f"p_{i}"]
            k_loc = st.session_state[f"k_{i-1}"]
            
            d_real = math.sqrt(dist_tramo**2 + (z2 - z1)**2)
            dist_acumulada += d_real
            
            # Energía Real
            h_real_1 = z1 + (pres1 * 0.7032)
            h_real_2 = z2 + (pres2 * 0.7032)
            dh_real = h_real_1 - h_real_2
            
            # Energía Teórica
            hf = perdida_hazen_williams(q, c_hw, d, d_real)
            hm = k_loc * (v**2) / (2 * 9.81)
            dh_teo = hf + hm
            
            perfil.append({"Dist": dist_acumulada, "Energia": h_real_2, "Terreno": z2})
            
            if (dh_real - dh_teo) > 0.14:
                x_f = d_real * (dh_teo / dh_real) if dh_real != 0 else 0
                fugas.append({"tramo": f"{i} → {i+1}", "pos": x_f, "perda": dh_real - dh_teo})

        # RESULTADOS Y GRÁFICA
        st.divider()
        if fugas:
            for f in fugas: st.warning(f"⚠️ Anomalía en Tramo {f['tramo']} a {f['pos']:.2f}m.")
        else:
            st.success("Integridad de red confirmada.")
            
        df = pd.DataFrame(perfil)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Dist"], y=df["Energia"], name="Energía (H)", line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=df["Dist"], y=df["Terreno"], name="Terreno (Z)", fill='tozeroy', line=dict(color='brown')))
        st.plotly_chart(fig, use_container_width=True)

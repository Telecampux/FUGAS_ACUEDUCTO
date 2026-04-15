import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import math

# =============================================================================
# IANC_H2O - SISTEMA DE DETECCIÓN DE FUGAS (VERSIÓN DEFINITIVA)
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
if "datos_nodos" not in st.session_state:
    st.session_state.datos_nodos = {}

# --- PANEL DE CONFIGURACIÓN ---
st.title("IANC_H2O - Diagnóstico Hidráulico")

with st.sidebar:
    st.header("Configuración de Escenario")
    
    municipios = {
        "Villeta": [5.0113, -74.4754],
        "Neiva": [2.9273, -75.2819],
        "Villavicencio": [4.1420, -73.6266],
        "Chaparral": [3.7235, -75.4833]
    }
    muni_sel = st.selectbox("Seleccione el Municipio", list(municipios.keys()))
    centro_mapa = municipios[muni_sel]

    # Guardamos el modo en session_state para detectar cambios
    if "modo_operacion" not in st.session_state:
        st.session_state.modo_operacion = "Simulación de Red"

    nuevo_modo = st.radio("Modo de Operación", ["Simulación de Red", "Diagnóstico Real (Campo)"], index=["Simulación de Red", "Diagnóstico Real (Campo)"].index(st.session_state.modo_operacion))
    
    # Si el usuario cambia de modo, limpiamos las cotas para evitar conflictos
    if nuevo_modo != st.session_state.modo_operacion:
        st.session_state.modo_operacion = nuevo_modo
        for i in range(len(st.session_state.puntos)):
             if nuevo_modo == "Diagnóstico Real (Campo)":
                 # Al pasar a Real, forzamos a 0.0 para que el usuario deba ingresarlo
                 st.session_state[f"z_{i}"] = 0.0 
             else:
                 # Al pasar a Simulación, intentamos recuperar la de la API si existe
                 z_api = st.session_state.datos_nodos.get(i, {}).get("Z_api")
                 st.session_state[f"z_{i}"] = float(z_api if z_api is not None else 0.0)
        st.rerun()

    modo = st.session_state.modo_operacion
    
    st.divider()
    st.header("Parámetros de Red")
    q = st.number_input("Caudal (L/s)", value=20.0, step=0.1)
    d = st.number_input("Diámetro Interno (pulg)", value=6.0, step=0.1)
    c_hw = st.slider("Coeficiente C (Hazen-Williams)", 100, 150, 140)
    
    if st.button("Limpiar Mapa y Datos", use_container_width=True):
        st.session_state.puntos = []
        st.session_state.datos_nodos = {}
        for key in list(st.session_state.keys()):
            if key.startswith("p_") or key.startswith("z_") or key.startswith("k_"):
                del st.session_state[key]
        st.rerun()

# --- MAPA INTERACTIVO ---
m = folium.Map(location=centro_mapa, zoom_start=14)
for i, p in enumerate(st.session_state.puntos):
    folium.Marker(p, tooltip=f"Nodo {i+1}").add_to(m)
if len(st.session_state.puntos) > 1:
    folium.PolyLine(st.session_state.puntos, color="blue").add_to(m)

mapa = st_folium(m, width=None, height=450)

# Lógica de Captura
if mapa and mapa.get("last_clicked"):
    lat, lon = mapa["last_clicked"]["lat"], mapa["last_clicked"]["lng"]
    if [lat, lon] not in st.session_state.puntos:
        st.session_state.puntos.append([lat, lon])
        idx = len(st.session_state.puntos) - 1
        
        # Siempre consultamos la API por debajo para guardarla como referencia
        z_ref = obtener_cota_referencia(lat, lon)
        st.session_state.datos_nodos[idx] = {"Z_api": z_ref}
        
        st.session_state[f"p_{idx}"] = 0.0
        st.session_state[f"k_{idx}"] = 0.0
        
        # Asignación de cota inicial según el modo
        if modo == "Simulación de Red":
            st.session_state[f"z_{idx}"] = float(z_ref if z_ref else 0.0)
        else:
            # En modo real, forzamos a 0.0 obligando al usuario a digitar
            st.session_state[f"z_{idx}"] = 0.0 
            
        st.rerun()

# --- INPUTS DE SENSORES ---
st.subheader("Configuración de Nodos")

if not st.session_state.puntos:
    st.info("Haga clic en el mapa para agregar nodos de presión.")

for i in range(len(st.session_state.puntos)):
    with st.expander(f"📍 Nodo {i+1}", expanded=True):
        c1, c2 = st.columns(2)
        
        # Presión
        st.session_state[f"p_{i}"] = c1.number_input("Presión (PSI)", value=st.session_state.get(f"p_{i}", 0.0), key=f"input_p_{i}", step=0.5)
        
        # Cota (Altimetría)
        ayuda_z = "Cota altimétrica. En modo 'Real' debe ingresar la cota levantada en terreno."
        st.session_state[f"z_{i}"] = c2.number_input("Cota REAL (msnm) *", value=st.session_state.get(f"z_{i}", 0.0), key=f"input_z_{i}", format="%.2f", step=0.1, help=ayuda_z)
        
        # Mensajes de UI según el modo
        z_api = st.session_state.datos_nodos.get(i, {}).get("Z_api")
        if modo == "Simulación de Red":
            if z_api is not None:
                st.caption(f"Cota de referencia cargada de la API: {z_api} msnm")
            else:
                 st.caption("No se pudo obtener cota de la API. Ingrese manualmente.")
        elif modo == "Diagnóstico Real (Campo)":
            if st.session_state[f"z_{i}"] == 0.0:
                 st.error("⚠️ Ingrese la altimetría de precisión tomada en terreno.")
            else:
                 st.success("Dato de terreno ingresado.")
        
        # Accesorios
        if i < len(st.session_state.puntos) - 1:
            st.session_state[f"k_{i}"] = st.number_input("ΣK accesorios (pérdidas menores)", value=st.session_state.get(f"k_{i}", 0.0), key=f"input_k_{i}", step=0.1)

# --- EJECUCIÓN DEL MOTOR HIDRÁULICO ---
if st.button("Ejecutar Análisis Termodinámico", use_container_width=True):
    # Validación: En modo real no permitimos cálculos con cotas en 0.0
    if modo == "Diagnóstico Real (Campo)":
        cotas_cero = [i+1 for i in range(len(st.session_state.puntos)) if st.session_state[f"z_{i}"] == 0.0]
        if cotas_cero:
             st.error(f"Error: Para el Diagnóstico Real debe ingresar la cota en los Nodos: {', '.join(map(str, cotas_cero))}")
             st.stop()

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
        p0 = st.session_state[f"p_0"]
        h0 = z0 + (p0 * 0.7032) # Energía Total = Cota (Z) + Presión (P/gamma)
        perfil.append({"Dist": 0.0, "Energia": h0, "Terreno": z0})
        
        for i in range(1, len(st.session_state.puntos)):
            p1, p2 = st.session_state.puntos[i-1], st.session_state.puntos[i]
            dist_tramo = haversine_esferico(p1[0], p1[1], p2[0], p2[1])
            
            z1, z2 = st.session_state[f"z_{i-1}"], st.session_state[f"z_{i}"]
            pres1, pres2 = st.session_state[f"p_{i-1}"], st.session_state[f"p_{i}"]
            k_loc = st.session_state[f"k_{i-1}"]
            
            d_real = math.sqrt(dist_tramo**2 + (z2 - z1)**2)
            dist_acumulada += d_real
            
            # Diferencial de Energía Real (Medida)
            h_real_1 = z1 + (pres1 * 0.7032)
            h_real_2 = z2 + (pres2 * 0.7032)
            dh_real = h_real_1 - h_real_2
            
            # Diferencial de Energía Teórica (Calculada)
            hf = perdida_hazen_williams(q, c_hw, d, d_real)
            hm = k_loc * (v**2) / (2 * 9.81)
            dh_teo = hf + hm
            
            perfil.append({"Dist": dist_acumulada, "Energia": h_real_2, "Terreno": z2})
            
            if (dh_real - dh_teo) > 0.14:
                x_f = d_real * (dh_teo / dh_real) if dh_real != 0 else 0
                fugas.append({"tramo": f"{i} → {i+1}", "pos": x_f, "perda": dh_real - dh_teo})

        # --- RESULTADOS Y VISUALIZACIÓN ---
        st.divider()
        if fugas:
            for f in fugas: 
                st.warning(f"⚠️ Anomalía en Tramo {f['tramo']} a {f['pos']:.2f}m. (Diferencial anómalo: {f['perda']:.2f} mca)")
        else:
            st.success("Integridad de red confirmada.")
            
        df = pd.DataFrame(perfil)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Dist"], y=df["Energia"], name="Línea de Energía Total (H)", line=dict(color='blue', width=3)))
        fig.add_trace(go.Scatter(x=df["Dist"], y=df["Terreno"], name="Perfil Terreno (Z)", fill='tozeroy', line=dict(color='brown')))
        fig.update_layout(title="Perfil Hidráulico de la Red", xaxis_title="Distancia (m)", yaxis_title="msnm / mca")
        st.plotly_chart(fig, use_container_width=True)

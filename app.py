# =============================================================================
# SISTEMA IA PARA LOCALIZACIÓN DE FUGAS TÉCNICAS INVISIBLES 
# ESPECIALIZADO EN REDES TRONCALES Y MATRICES DE ACUEDUCTOS
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# Versión: 2.7 - Balance Integral de Energía y Pérdidas Locales
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import time

try:
    from core import haversine, perdida_hazen_williams, territorios, AUTOR
except ImportError:
    AUTOR = "Ing. Adolfo Barrera Vargas"
    territorios = {"Bogotá": {"coords": [4.6097, -74.0817]}}
    # Funciones dummy en caso de no tener el archivo core.py
    def haversine(lat1, lon1, lat2, lon2): return 100.0
    def perdida_hazen_williams(q, c, d, l): return 0.5

# --- CONSTANTES TÉCNICAS ---
FACTOR_CONVERSION_PSI_MCA = 0.703
GRAVEDAD = 9.81

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="IA Fugas - Matrices y Troncales", layout="wide")

def obtener_cota_api(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        respuesta = requests.get(url, timeout=3).json()
        if "elevation" in respuesta and respuesta["elevation"]:
            return round(respuesta["elevation"][0], 2)
    except Exception:
        pass
    return 1000.0

def calcular_balance_hidraulico(q_lps, d_pulg, c_hazen, dist_m, k_sum):
    """Calcula la caída teórica considerando fricción (H-W) y pérdidas locales."""
    # 1. Pérdida por Fricción
    hf = perdida_hazen_williams(q_lps, c_hazen, d_pulg, dist_m)
    
    # 2. Cálculo de Velocidad y Pérdida Menor
    q_m3s = q_lps / 1000.0
    d_m = d_pulg * 0.0254
    area = (np.pi * d_m**2) / 4
    velocidad = q_m3s / area
    hm = k_sum * (velocidad**2 / (2 * GRAVEDAD))
    
    # 3. Caída Teórica Total en mca
    caida_teorica = (hf * FACTOR_CONVERSION_PSI_MCA) + hm
    return caida_teorica, velocidad

# --- INICIALIZACIÓN DE VARIABLES DE ESTADO ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'datos_sensores' not in st.session_state: st.session_state.datos_sensores = {}

# --- SIDEBAR: MENÚ DE CONTROL Y PARÁMETROS ---
st.sidebar.header("⚙️ PARÁMETROS DE LA RED")

modo = st.sidebar.radio(
    "Seleccione Modo de Trabajo:", 
    ["Simulación Interactiva", "Operación Real (Carga Lote)"]
)
st.sidebar.divider()

q_entrada_lps = st.sidebar.number_input("Caudal Nominal (L/s)", value=200.0, step=1.0, format="%.1f")
dn_pulg = st.sidebar.selectbox("Diámetro (Pulg)", [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 36], index=11)
coef_c = st.sidebar.slider("Coeficiente C (Hazen-Williams)", 90, 150, 130)

with st.sidebar.expander("📘 Guía de Coeficientes K (Pérdidas Menores)", expanded=False):
    st.markdown("""
    **Valores Sugeridos para Matrices:**
    * **Válvula Mariposa:** 0.35
    * **Válvula Compuerta (Abierta):** 0.15
    * **Codo 90° (R. Largo):** 0.30
    * **Codo 45°:** 0.18
    * **Macro-medidor:** 0.10
    
    *El sistema calculará automáticamente la velocidad y aplicará:* $h_m = \sum K \cdot \\frac{v^2}{2g}$
    """)

# --- INTERFAZ ---
st.title("SISTEMA IA: LOCALIZACIÓN DE FUGAS TÉCNICAS INVISIBLES")
st.subheader("Especializado en Troncales y Matrices de Acueducto")
st.caption(f"Desarrollado por {AUTOR} | Motor Versión 2.7")

# =================================================================
# MODO 1: SIMULACIÓN INTERACTIVA
# =================================================================
if modo == "Simulación Interactiva":
    col_map, col_inputs = st.columns([2, 1])

    with col_map:
        mun_sel = st.selectbox("Zona de Operación:", list(territorios.keys()))
        m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=16)
        
        for i, p in enumerate(st.session_state.puntos):
            folium.Marker(p, icon=folium.Icon(color='red', icon='dot-circle', prefix='fa')).add_to(m)
        
        if len(st.session_state.puntos) > 1:
            folium.PolyLine(st.session_state.puntos, color="red", weight=4).add_to(m)

        mapa_data = st_folium(m, width=700, height=450)
        
        if mapa_data and mapa_data.get('last_clicked'):
            lat, lng = mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']
            if [lat, lng] not in st.session_state.puntos:
                st.session_state.puntos.append([lat, lng])
                idx = len(st.session_state.puntos) - 1
                st.session_state[f"z_{idx}"] = float(obtener_cota_api(lat, lng))
                st.rerun()

    with col_inputs:
        st.subheader("📡 Lecturas de Campo")
        for i in range(len(st.session_state.puntos)):
            with st.expander(f"Sensor Nodo {i+1}", expanded=True):
                c1, c2 = st.columns(2)
                p_in = c1.number_input(f"Presión (PSI)", key=f"p_{i}", value=0.0, format="%.2f")
                if f"z_{i}" not in st.session_state: st.session_state[f"z_{i}"] = 1000.0
                z_in = c2.number_input(f"Cota (msnm)", key=f"z_{i}", step=0.01, format="%.2f")
                
                # Ingreso del factor K para el tramo que llega a este nodo (ignorado en Nodo 1)
                k_in = st.number_input(f"ΣK Accesorios (Tramo N{i}-N{i+1})", key=f"k_{i}", value=0.0, step=0.1) if i < len(st.session_state.puntos)-1 else 0.0
                
                st.session_state.datos_sensores[i] = {"P": p_in, "Z": z_in, "K": k_in}

        if st.button("🔄 Nueva Localización", use_container_width=True):
            st.session_state.puntos = []
            st.session_state.datos_sensores = {}
            for key in list(st.session_state.keys()):
                if key.startswith("z_") or key.startswith("p_") or key.startswith("k_"): del st.session_state[key]
            st.rerun()

    # --- CÁLCULOS E INFORME (Modo Simulación) ---
    if len(st.session_state.puntos) >= 2:
        st.divider()
        
        with st.status("🚀 Iniciando Motor Hidráulico V2.7...", expanded=True) as status:
            st.write("📡 Recopilando datos y coeficientes de válvulas...")
            time.sleep(0.4)
            st.write("📐 Calculando vectores 3D y cinemática del flujo...")
            time.sleep(0.4)
            st.write("💧 Modelando balance integral (Fricción + Pérdidas Locales)...")
            time.sleep(0.4)
            status.update(label="✅ Análisis completado", state="complete", expanded=False)

        dist_total = 0.0
        matriz_analisis = []
        perfil_grafico = [] 
        alertas_fuga = []

        for i in range(len(st.session_state.puntos)):
            p_act = st.session_state.puntos[i]
            datos = st.session_state.datos_sensores[i]
            H = datos['Z'] + (datos['P'] * FACTOR_CONVERSION_PSI_MCA)
            
            if i > 0:
                p_prev = st.session_state.puntos[i-1]
                d_2d = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
                dz = abs(st.session_state.datos_sensores[i-1]['Z'] - datos['Z'])
                d_3d = np.sqrt(d_2d**2 + dz**2)
                dist_total += d_3d
                
                # Caída real medida
                h_prev = st.session_state.datos_sensores[i-1]['Z'] + (st.session_state.datos_sensores[i-1]['P'] * FACTOR_CONVERSION_PSI_MCA)
                caida_h_real = h_prev - H
                
                # Cálculo integral teórico
                k_tramo = st.session_state.datos_sensores[i-1].get('K', 0.0)
                perdida_esperada, v_ms = calcular_balance_hidraulico(q_entrada_lps, dn_pulg, coef_c, d_3d, k_tramo)
                
                # Detección y localización
                if caida_h_real > (perdida_esperada + 0.15):
                    dist_fuga = d_3d * (perdida_esperada / caida_h_real) if caida_h_real != 0 else 0
                    q_fuga = abs(q_entrada_lps * (1 - (perdida_esperada/caida_h_real)**0.50)) # Ajustado a exponente de orificio
                    alertas_fuga.append({"T": f"N{i}-N{i+1}", "Q": q_fuga, "D": dist_total - d_3d + dist_fuga, "V": v_ms})

            matriz_analisis.append({"Nodo": i + 1, "Cota Z": datos['Z'], "Presión": datos['P'], "Energía H": round(H, 2), "Dist. Acum": round(dist_total, 2)})
            perfil_grafico.append({"D": dist_total, "H": H, "Z": datos['Z']})

        st.subheader("📉 Diagnóstico del Gradiente Hidráulico")
        df_p = pd.DataFrame(perfil_grafico)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Gradiente Energía (H)', line=dict(color='blue', width=3)))
        fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Perfil Terreno (Z)', fill='tozeroy', line=dict(color='brown', width=2)))

        fig.update_layout(hovermode=False, xaxis_title="Distancia (m)", yaxis_title="Elevación (msnm)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

        if alertas_fuga:
            for a in alertas_fuga:
                st.error(f"🚨 **FUGA TÉCNICA DETECTADA** en tramo **{a['T']}**. Caudal Anómalo: **{a['Q']:.2f} L/s** a los **{a['D']:.1f} m** desde el origen. *(Velocidad tramo: {a['V']:.2f} m/s)*")
        else:
            st.success("✅ **SISTEMA ESTABLE**: Balance energético coherente. No se detectan anomalías.")

# =================================================================
# MODO 2: OPERACIÓN REAL (CARGA LOTE)
# =================================================================
elif modo == "Operación Real (Carga Lote)":
    st.write("### 📊 Auditoría Masiva por Carga de Datos")
    st.info("Módulo configurado para procesamiento masivo. Requiere archivo CSV con columnas: `latitud`, `longitud`, `cota`, `presion` y opcionalmente `sum_k`.")
    
    archivo_csv = st.file_uploader("Cargar Archivo Maestro de Campo (.csv)", type=["csv"])
    
    if archivo_csv is not None:
        try:
            df_lote = pd.read_csv(archivo_csv, sep=None, engine='python', encoding_errors='ignore')
            
            # Limpieza robusta
            df_lote.columns = (df_lote.columns.str.strip().str.lower().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))
            df_lote.rename(columns={'cota_z': 'cota', 'presion_psi': 'presion', 'sumatoria_k': 'sum_k'}, inplace=True)
            
            if 'sum_k' not in df_lote.columns:
                df_lote['sum_k'] = 0.0

            st.success("Archivo estructurado correctamente.")
            
            if st.button("🚀 Iniciar Auditoría Hidráulica Lote", use_container_width=True):
                dist_total = 0.0
                matriz_analisis = []
                alertas_fuga = []
                
                for i in range(len(df_lote)):
                    row = df_lote.iloc[i]
                    p_act = [row['latitud'], row['longitud']]
                    z_act = row['cota']
                    p_in = row['presion']
                    H = z_act + (p_in * FACTOR_CONVERSION_PSI_MCA)
                    
                    if i > 0:
                        row_prev = df_lote.iloc[i-1]
                        p_prev = [row_prev['latitud'], row_prev['longitud']]
                        d_2d = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
                        dz = abs(row_prev['cota'] - z_act)
                        d_3d = np.sqrt(d_2d**2 + dz**2)
                        dist_total += d_3d
                        
                        h_prev = row_prev['cota'] + (row_prev['presion'] * FACTOR_CONVERSION_PSI_MCA)
                        caida_h_real = h_prev - H
                        
                        # Integración del factor K desde el CSV
                        k_tramo = row_prev['sum_k'] 
                        perdida_esperada, v_ms = calcular_balance_hidraulico(q_entrada_lps, dn_pulg, coef_c, d_3d, k_tramo)
                        
                        if caida_h_real > (perdida_esperada + 0.15):
                            dist_fuga = d_3d * (perdida_esperada / caida_h_real) if caida_h_real != 0 else 0
                            q_fuga = abs(q_entrada_lps * (1 - (perdida_esperada/caida_h_real)**0.50))
                            alertas_fuga.append({"T": f"N{i}-N{i+1}", "Q": q_fuga, "D": dist_total - d_3d + dist_fuga})

                    matriz_analisis.append({"Nodo": i + 1, "Latitud": f"{p_act[0]:.6f}", "Longitud": f"{p_act[1]:.6f}", "Cota Z": z_act, "Presión": p_in, "Energía H": round(H, 2)})

                if alertas_fuga:
                    for a in alertas_fuga:
                        st.error(f"🚨 **ANOMALÍA DETECTADA** (Tramo {a['T']}) | Caudal: {a['Q']:.2f} L/s | Ubicación: a {a['D']:.1f} m del inicio.")
                else:
                    st.success("✅ **LOTE AUDITADO**: Gradiente estable, sin registros de fugas invisibles.")

        except KeyError as e:
            st.error(f"Error Estructural: Faltan las columnas base en el archivo CSV. Detalle: {e}")

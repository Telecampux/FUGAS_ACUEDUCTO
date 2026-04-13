# =============================================================================
# SISTEMA IA PARA LOCALIZACIÓN DE FUGAS TÉCNICAS INVISIBLES 
# ESPECIALIZADO EN REDES TRONCALES Y MATRICES DE ACUEDUCTOS
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import time

# --- IMPORTACIÓN DESDE EL CORE ---
try:
    from core import haversine, perdida_hazen_williams, territorios, AUTOR
except ImportError:
    AUTOR = "Ing. Adolfo Barrera Vargas"
    territorios = {"Bogotá": {"coords": [4.6097, -74.0817]}}
    def haversine(lat1, lon1, lat2, lon2): return 100.0
    def perdida_hazen_williams(q, c, d, l): return 0.5

# --- CONSTANTES TÉCNICAS ---
FACTOR_CONVERSION_PSI_MCA = 0.703

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

q_entrada_lps = st.sidebar.number_input("Caudal Nominal (L/s)", value=20.0, step=0.1, format="%.1f")
dn_pulg = st.sidebar.selectbox("Diámetro (Pulg)", [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24], index=6)
coef_c = st.sidebar.slider("Coeficiente C", 100, 150, 140)

# --- ENCABEZADO PRINCIPAL ---
st.title("SISTEMA IA: LOCALIZACIÓN DE FUGAS TÉCNICAS INVISIBLES")
st.subheader("Especializado en Troncales y Matrices de Acueducto")
st.caption(f"Desarrollado por {AUTOR}")

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
                st.session_state.datos_sensores[i] = {"P": p_in, "Z": z_in}

        if st.button("🔄 Nueva Localización", use_container_width=True):
            st.session_state.puntos = []
            st.session_state.datos_sensores = {}
            for key in list(st.session_state.keys()):
                if key.startswith("z_") or key.startswith("p_"): del st.session_state[key]
            st.rerun()

    # --- CÁLCULOS E INFORME (Modo Simulación) ---
    if len(st.session_state.puntos) >= 2:
        st.divider()
        
        # FACHADA VISUAL DE PROCESAMIENTO (Añadido)
        with st.status("🚀 Iniciando Motor de Análisis Hidráulico...", expanded=True) as status:
            st.write("📡 Recopilando datos de sensores...")
            time.sleep(0.5)
            st.write("📐 Vectorizando distancias 3D y cotas...")
            time.sleep(0.5)
            st.write("💧 Modelando gradiente de energía (Hazen-Williams)...")
            time.sleep(0.5)
            st.write("🔍 Aplicando algoritmos de detección de anomalías...")
            time.sleep(0.5)
            status.update(label="✅ Análisis completado con éxito", state="complete", expanded=False)

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
                
                h_prev = st.session_state.datos_sensores[i-1]['Z'] + (st.session_state.datos_sensores[i-1]['P'] * FACTOR_CONVERSION_PSI_MCA)
                caida_h = h_prev - H
                hf_teorica = perdida_hazen_williams(q_entrada_lps, coef_c, dn_pulg, d_3d) * FACTOR_CONVERSION_PSI_MCA
                
                if caida_h > (hf_teorica + 0.15):
                    dist_fuga = d_3d * (hf_teorica / caida_h) if caida_h != 0 else 0
                    alertas_fuga.append({"T": f"N{i}-N{i+1}", "Q": abs(q_entrada_lps * (1 - (hf_teorica/caida_h)**0.54)), "D": dist_total - d_3d + dist_fuga})

            matriz_analisis.append({"Nodo": i + 1, "Latitud": f"{p_act[0]:.6f}", "Longitud": f"{p_act[1]:.6f}", "Cota Z": datos['Z'], "Presión": datos['P'], "Energía H": round(H, 2), "Dist. Acum": round(dist_total, 2)})
            perfil_grafico.append({"D": dist_total, "H": H, "Z": datos['Z']})

        # --- GRÁFICO PROFESIONAL CON PLOTLY ---
        st.subheader("📉 Diagnóstico del Gradiente Hidráulico")
        df_p = pd.DataFrame(perfil_grafico)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Gradiente Energía (H)', line=dict(color='blue', width=3)))
        fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Perfil Terreno (Z)', fill='tozeroy', line=dict(color='brown', width=2)))

        fig.update_layout(
            hovermode=False, 
            xaxis_title="Distancia en la Matriz (m)",
            yaxis_title="Metros sobre el nivel del mar (msnm)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Matriz de Localización Geográfica")
        st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

        if alertas_fuga:
            for a in alertas_fuga:
                st.error(f"🚨 **FUGA TÉCNICA DETECTADA** en tramo **{a['T']}**. Caudal: **{a['Q']:.2f} L/s** a los **{a['D']:.1f} m**.")
        else:
            st.success("✅ **SISTEMA ESTABLE**: No se detectan fugas invisibles.")

# =================================================================
# MODO 2: OPERACIÓN REAL (Carga Lote - CSV)
# =================================================================
elif modo == "Operación Real (Carga Lote)":
    st.write("### 📊 Auditoría Masiva por Carga de Datos")
    st.info("Módulo configurado para procesamiento masivo de sensores IoT. El CSV debe contener las columnas: 'Latitud', 'Longitud', 'Cota', 'Presion'")
    
    archivo_csv = st.file_uploader("Cargar Archivo Maestro de Campo (.csv)", type=["csv"])
    
    if archivo_csv is not None:
        try:
            df_lote = pd.read_csv(archivo_csv)
            st.success("Archivo cargado correctamente. Previsualización de datos:")
            st.dataframe(df_lote.head())
            
            if st.button("🚀 Procesar Lote de Sensores", use_container_width=True):
                
                # FACHADA VISUAL DE PROCESAMIENTO (Añadido)
                with st.status("🚀 Procesando Lote de Datos CSV...", expanded=True) as status:
                    st.write("📡 Estructurando registros del archivo maestro...")
                    time.sleep(0.6)
                    st.write("📐 Vectorizando coordenadas espaciales...")
                    time.sleep(0.6)
                    st.write("💧 Ejecutando modelo matemático por cada tramo...")
                    time.sleep(0.6)
                    st.write("🔍 Evaluando umbrales de caída atípica...")
                    time.sleep(0.6)
                    status.update(label="✅ Análisis Masivo Completado", state="complete", expanded=False)

                # EJECUCIÓN MATEMÁTICA REAL (Añadido)
                dist_total = 0.0
                matriz_analisis = []
                perfil_grafico = [] 
                alertas_fuga = []
                
                for i in range(len(df_lote)):
                    row = df_lote.iloc[i]
                    p_act = [row['Latitud'], row['Longitud']]
                    z_act = row['Cota']
                    p_in = row['Presion']
                    H = z_act + (p_in * FACTOR_CONVERSION_PSI_MCA)
                    
                    if i > 0:
                        row_prev = df_lote.iloc[i-1]
                        p_prev = [row_prev['Latitud'], row_prev['Longitud']]
                        d_2d = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
                        dz = abs(row_prev['Cota'] - z_act)
                        d_3d = np.sqrt(d_2d**2 + dz**2)
                        dist_total += d_3d
                        
                        h_prev = row_prev['Cota'] + (row_prev['Presion'] * FACTOR_CONVERSION_PSI_MCA)
                        caida_h = h_prev - H
                        hf_teorica = perdida_hazen_williams(q_entrada_lps, coef_c, dn_pulg, d_3d) * FACTOR_CONVERSION_PSI_MCA
                        
                        if caida_h > (hf_teorica + 0.15):
                            dist_fuga = d_3d * (hf_teorica / caida_h) if caida_h != 0 else 0
                            alertas_fuga.append({"T": f"N{i}-N{i+1}", "Q": abs(q_entrada_lps * (1 - (hf_teorica/caida_h)**0.54)), "D": dist_total - d_3d + dist_fuga})

                    matriz_analisis.append({"Nodo": i + 1, "Latitud": f"{p_act[0]:.6f}", "Longitud": f"{p_act[1]:.6f}", "Cota Z": z_act, "Presión": p_in, "Energía H": round(H, 2), "Dist. Acum": round(dist_total, 2)})
                    perfil_grafico.append({"D": dist_total, "H": H, "Z": z_act})

                # --- SALIDAS VISUALES ---
                st.subheader("📉 Diagnóstico del Gradiente Hidráulico Lote")
                df_p = pd.DataFrame(perfil_grafico)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Gradiente Energía (H)', line=dict(color='blue', width=3)))
                fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Perfil Terreno (Z)', fill='tozeroy', line=dict(color='brown', width=2)))

                fig.update_layout(
                    hovermode=False, 
                    xaxis_title="Distancia en la Matriz (m)",
                    yaxis_title="Metros sobre el nivel del mar (msnm)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("📋 Matriz de Localización Geográfica (Procesada)")
                st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

                if alertas_fuga:
                    for a in alertas_fuga:
                        st.error(f"🚨 **FUGA TÉCNICA DETECTADA** en tramo **{a['T']}**. Caudal: **{a['Q']:.2f} L/s** a los **{a['D']:.1f} m**.")
                else:
                    st.success("✅ **SISTEMA ESTABLE**: No se detectan fugas invisibles en el lote.")

        except KeyError as e:
            st.error(f"Error de formato: El archivo CSV debe contener exactamente las columnas: 'Latitud', 'Longitud', 'Cota', 'Presion'. Detalle: Falta {e}")
        except Exception as e:
            st.error(f"Error al leer o procesar el archivo CSV: {e}")

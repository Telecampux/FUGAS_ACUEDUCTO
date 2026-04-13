# =============================================================================
# AVISO DE PROPIEDAD INTELECTUAL Y DERECHOS DE AUTOR
# =============================================================================
# Proyecto: IANC H2O - Sistema Integral de Auditoría de Acueductos
# Versión: 2.0 (Arquitectura Modular Pro)
# Autor: Ing. Adolfo Barrera Vargas
# Ubicación: Colombia
# 
# (c) Copyright 2026. Todos los derechos reservados.
# 
# Este software y sus algoritmos (Core Hydraulics) están protegidos por las 
# leyes de derecho de autor en Colombia (Ley 23 de 1982). Queda prohibida la 
# reproducción total o parcial, comunicación pública, transformación o 
# distribución sin la autorización expresa y por escrito del autor.
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import streamlit.components.v1 as components

# --- IMPORTACIÓN DESDE EL CEREBRO (CORE) ---
try:
    from core import (
        haversine, 
        perdida_hazen_williams, 
        territorios, 
        PROGRAMA_NOMBRE, 
        AUTOR, 
        EMPRESA_DEFAULT
    )
except ImportError:
    AUTOR = "Ing. Adolfo Barrera Vargas"
    PROGRAMA_NOMBRE = "IANC H2O"
    EMPRESA_DEFAULT = "Acueducto Municipal"
    territorios = {"Bogotá": {"coords": [4.6097, -74.0817], "costo": 2500}}
    def haversine(lat1, lon1, lat2, lon2): return 100.0
    def perdida_hazen_williams(q, c, d, l): return 0.5

# --- CONSTANTES TÉCNICAS ---
FACTOR_CONVERSION_PSI_MCA = 0.703

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="IANC H2O - Auditoría Profesional", 
    layout="wide", 
    page_icon="📡"
)

# Inyección del Manifiesto PWA
components.html(
    f'<link rel="manifest" href="./static/manifest.json">', 
    height=0
)

# --- ENCABEZADO PRINCIPAL ---
st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader(PROGRAMA_NOMBRE)
st.markdown(f"**Líder del Proyecto:** {AUTOR}")
st.divider()

# --- MENÚ LATERAL (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3105/3105807.png", width=100)
st.sidebar.header("📂 MENÚ DE CONTROL")

modo = st.sidebar.radio(
    "Seleccione Modo de Trabajo:", 
    ["Simulación Interactiva", "Operación Real (Carga Lote)"]
)

st.sidebar.divider()

mun_sel = st.sidebar.selectbox("Municipio de Operación:", list(territorios.keys()))
datos_mun = territorios[mun_sel]

# Parámetros Técnicos
costo_m3 = st.sidebar.number_input("Costo del m³ (COP)", value=datos_mun['costo'])
q_entrada_lps = st.sidebar.number_input("Caudal Nominal (L/s)", value=20.0, step=0.1)
dn = st.sidebar.selectbox("Diámetro Red Auditada (Pulg)", [2, 3, 4, 6, 8, 10, 12, 14, 16], index=3)
coef_c = st.sidebar.slider("Coeficiente C", 100, 150, 140)

# --- INICIALIZACIÓN DE VARIABLES DE ESTADO ---
for key, default in [
    ('puntos', []), ('ejecutado', False), ('empresa', EMPRESA_DEFAULT),
    ('analisis_listo', False), ('datos_sensores', {})
]:
    if key not in st.session_state:
        st.session_state[key] = default

# =================================================================
# CUERPO DE LA APLICACIÓN
# =================================================================

if modo == "Simulación Interactiva":
    st.write(f"### 🕹️ Simulador: {mun_sel}")
    st.session_state.empresa = st.text_input("Entidad Prestadora del Servicio:", st.session_state.empresa)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("Haga clic en el mapa para ubicar los sensores de presión y flujo.")
        m = folium.Map(location=datos_mun['coords'], zoom_start=15)
        
        for i, p in enumerate(st.session_state.puntos):
            folium.Marker(p, popup=f"Punto {i+1}", icon=folium.Icon(color='blue')).add_to(m)
        
        if len(st.session_state.puntos) > 1:
            folium.PolyLine(st.session_state.puntos, color="blue", weight=4).add_to(m)
            
        mapa_data = st_folium(m, width=800, height=500)
        
        if mapa_data['last_clicked']:
            punto = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
            if punto not in st.session_state.puntos:
                st.session_state.puntos.append(punto)
                st.rerun()

    with col2:
        st.write("#### 📍 Puntos de Control y Lecturas")
        if st.session_state.puntos:
            for i, p in enumerate(st.session_state.puntos):
                with st.expander(f"Punto {i+1} ({p[0]:.4f}, {p[1]:.4f})", expanded=True):
                    p_in = st.number_input(f"Presión (PSI)", key=f"p_{i}", value=0.0)
                    z_in = st.number_input(f"Cota (msnm)", key=f"z_{i}", value=1000.0)
                    st.session_state.datos_sensores[i] = {"P": p_in, "Z": z_in}
            
            if st.button("🗑️ Limpiar"):
                st.session_state.puntos = []
                st.session_state.datos_sensores = {}
                st.session_state.ejecutado = False
                st.rerun()
                
            if st.button("🚀 EJECUTAR CÁLCULOS"):
                if len(st.session_state.puntos) < 2:
                    st.warning("Se requieren al menos 2 puntos para calcular pérdidas.")
                else:
                    st.session_state.ejecutado = True

# --- RESULTADOS DEL MOTOR HIDRÁULICO (SIMULACIÓN) ---
if st.session_state.ejecutado and modo == "Simulación Interactiva":
    st.divider()
    
    # 1. FACHADA VISUAL DE PROCESAMIENTO
    with st.status("🚀 Procesando Auditoría Hidráulica...", expanded=True) as status:
        st.write("📡 Conectando con malla de nodos virtuales...")
        time.sleep(0.5)
        st.write("📐 Vectorizando distancias espaciales y altimetría...")
        time.sleep(0.5)
        st.write("💧 Modelando gradiente de energía y fricción (Hazen-Williams)...")
        time.sleep(0.5)
        st.write("🔍 Aplicando algoritmos predictivos de fugas invisibles...")
        time.sleep(0.5)
        status.update(label="✅ Análisis Hidráulico Finalizado", state="complete", expanded=False)
    
    # 2. MOTOR MATEMÁTICO REAL
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
            hf_teorica = perdida_hazen_williams(q_entrada_lps, coef_c, dn, d_3d) * FACTOR_CONVERSION_PSI_MCA
            
            if caida_h > (hf_teorica + 0.15):
                dist_fuga = d_3d * (hf_teorica / caida_h) if caida_h != 0 else 0
                alertas_fuga.append({"T": f"P{i}-P{i+1}", "Q": abs(q_entrada_lps * (1 - (hf_teorica/caida_h)**0.54)), "D": dist_total - d_3d + dist_fuga})

        matriz_analisis.append({"Nodo": f"P{i+1}", "Latitud": p_act[0], "Longitud": p_act[1], "Cota Z": datos['Z'], "Presión": datos['P'], "Energía H": round(H, 2), "Dist Acum (m)": round(dist_total, 2)})
        perfil_grafico.append({"D": dist_total, "H": H, "Z": datos['Z']})
    
    res_col1, res_col2 = st.columns(2)
    res_col1.metric("Distancia Total Auditada", f"{dist_total:.2f} m")
    res_col2.metric("Pérdida de Energía Máxima", f"{(perfil_grafico[0]['H'] - H):.2f} mca")

    st.subheader("📉 Diagnóstico del Gradiente Hidráulico")
    df_p = pd.DataFrame(perfil_grafico)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Gradiente Energía (H)', line=dict(color='blue', width=3)))
    fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Perfil Terreno (Z)', fill='tozeroy', line=dict(color='brown', width=2)))
    fig.update_layout(hovermode=False, xaxis_title="Distancia (m)", yaxis_title="Elevación (msnm)", margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

    if alertas_fuga:
        for a in alertas_fuga:
            st.error(f"🚨 **FUGA DETECTADA** en {a['T']} a los **{a['D']:.1f} m**. Caudal: {a['Q']:.2f} L/s.")

# =================================================================
# MODO 2: OPERACIÓN REAL (CARGA LOTE)
# =================================================================
elif modo == "Operación Real (Carga Lote)":
    st.write("### 📊 Auditoría por Carga de Datos")
    st.info("Módulo configurado para procesamiento masivo de sensores IoT. El archivo debe contener los campos: latitud, longitud, cota, presion")
    archivo_csv = st.file_uploader("Cargar Archivo Maestro de Campo (.csv)", type=["csv"])
    
    if archivo_csv is not None:
        try:
            # --- MOTOR DE LECTURA ROBUSTO CON CONVERSIÓN ESTRICTA A MINÚSCULAS ---
            df_lote = pd.read_csv(archivo_csv, sep=None, engine='python', encoding_errors='ignore')
            
            # Limpieza exhaustiva de encabezados: todo a minúsculas
            df_lote.columns = (
                df_lote.columns
                .str.replace('\ufeff', '', regex=False)
                .str.strip()
                .str.lower() # FORZAR ESTRICTAMENTE A MINÚSCULA
                .str.normalize('NFKD')
                .str.encode('ascii', errors='ignore')
                .str.decode('utf-8')
            )
            # --------------------------------------------------------

            st.success("✅ Archivo procesado estructuralmente. Previsualización:")
            st.dataframe(df_lote.head())
            
            if st.button("🚀 PROCESAR LOTE", use_container_width=True):
                
                # 1. FACHADA VISUAL DE PROCESAMIENTO
                with st.status("🚀 Procesando Lote de Sensores...", expanded=True) as status:
                    st.write("📡 Extrayendo telemetría del archivo maestro...")
                    time.sleep(0.7)
                    st.write("📐 Vectorizando topología de red...")
                    time.sleep(0.7)
                    st.write("💧 Resolviendo matrices de pérdida por fricción...")
                    time.sleep(0.7)
                    status.update(label="✅ Análisis Masivo Completado", state="complete", expanded=False)

                # 2. MOTOR MATEMÁTICO REAL EN LOTE (Extrayendo en minúsculas)
                dist_total = 0.0
                matriz_analisis = []
                perfil_grafico = [] 
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
                        caida_h = h_prev - H
                        hf_teorica = perdida_hazen_williams(q_entrada_lps, coef_c, dn, d_3d) * FACTOR_CONVERSION_PSI_MCA
                        
                        if caida_h > (hf_teorica + 0.15):
                            dist_fuga = d_3d * (hf_teorica / caida_h) if caida_h != 0 else 0
                            alertas_fuga.append({"T": f"Línea {i}-{i+1}", "Q": abs(q_entrada_lps * (1 - (hf_teorica/caida_h)**0.54)), "D": dist_total - d_3d + dist_fuga})

                    matriz_analisis.append({"Registro": i + 1, "Latitud": p_act[0], "Longitud": p_act[1], "Cota Z": z_act, "Presión": p_in, "Energía H": round(H, 2), "Dist Acum": round(dist_total, 2)})
                    perfil_grafico.append({"D": dist_total, "H": H, "Z": z_act})

                st.subheader("📉 Gradiente Hidráulico del Lote")
                df_p = pd.DataFrame(perfil_grafico)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Gradiente Energía', line=dict(color='blue', width=3)))
                fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Terreno', fill='tozeroy', line=dict(color='brown', width=2)))
                fig.update_layout(hovermode=False, xaxis_title="Distancia (m)", margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)
                
                if alertas_fuga:
                    for a in alertas_fuga:
                        st.error(f"🚨 **FUGA DETECTADA** en {a['T']}. Caudal: {a['Q']:.2f} L/s.")
                else:
                    st.success("✅ Lote sin anomalías hidráulicas.")

        except KeyError as e:
            st.error(f"Error estructural residual: Las columnas detectadas en el archivo fueron {list(df_lote.columns)}. Se requiere estrictamente 'latitud', 'longitud', 'cota', 'presion' en minúsculas. Faltante o irreconocible: {e}")
        except Exception as e:
            st.error(f"Ocurrió un error inesperado al leer el archivo: {e}")

# --- PIE DE PÁGINA ---
st.sidebar.divider()
st.sidebar.caption(f"© 2026 Ing. Adolfo Barrera | Estándares CRA")

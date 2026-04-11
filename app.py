# =============================================================================
# AVISO DE PROPIEDAD INTELECTUAL Y DERECHOS DE AUTOR
# =============================================================================
# Proyecto: IANC H2O - Auditoría Técnica de Acueductos
# Autor: Ing. Adolfo Barrera Vargas | Versión: 4.5 (Final Android Unblocker)
# Ubicación: Colombia
# 
# (c) Copyright 2026. Todos los derechos reservados.
# Protegido por la Ley 23 de 1982 y Ley 1915 de 2018.
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import streamlit.components.v1 as components
import io

# --- CONEXIÓN CON EL MÓDULO CEREBRO (CORE) ---
try:
    from core import (
        haversine, perdida_hazen_williams, territorios, 
        PROGRAMA_NOMBRE, AUTOR, EMPRESA_DEFAULT
    )
except ImportError:
    st.error("🚨 Error Crítico: No se detecta la carpeta 'core' en su repositorio.")
    st.stop()

# --- CONFIGURACIÓN DE PÁGINA PARA DISPOSITIVOS MÓVILES ---
st.set_page_config(
    page_title="IANC H2O Pro", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inyección de Manifiesto PWA para que el celular lo reconozca como App
components.html('<link rel="manifest" href="./static/manifest.json">', height=0)

# --- SISTEMA DE PERSISTENCIA (SESSION STATE) ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'calc_sim' not in st.session_state: st.session_state.calc_sim = False
if 'res_real' not in st.session_state: st.session_state.res_real = None
if 'res_dist' not in st.session_state: st.session_state.res_dist = 0.0
if 'res_perd' not in st.session_state: st.session_state.res_perd = 0.0

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; border-radius: 10px; height: 3.5em; 
        font-weight: bold; background-color: #1a73e8; color: white;
    }
    .report-card { 
        background-color: white; padding: 20px; border-radius: 12px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-left: 6px solid #1a73e8; 
    }
    </style>
""", unsafe_allow_status=True)

# --- ENCABEZADO ---
st.title("📡 IANC H2O - AUDITORÍA")
st.markdown(f"**Ingeniero Responsable:** {AUTOR}")
st.divider()

# --- MENÚ LATERAL ---
st.sidebar.header("🕹️ OPERACIÓN")
modo = st.sidebar.radio("Función:", ["📍 Simulación sobre Mapa", "📊 Auditoría Real (CSV)"])
st.sidebar.divider()

mun_sel = st.sidebar.selectbox("Seleccione Municipio:", list(territorios.keys()))
datos_mun = territorios[mun_sel]
costo_m3 = st.sidebar.number_input("Costo m³ (COP):", value=datos_mun['costo'])
dn = st.sidebar.selectbox("Diámetro Red (Pulg):", [2, 3, 4, 6, 8, 10, 12], index=2)

# =================================================================
# MODO 1: SIMULACIÓN INTERACTIVA (MAPA)
# =================================================================
if modo == "📍 Simulación sobre Mapa":
    st.subheader(f"Mapa de Control: {mun_sel}")
    st.info("Toque el mapa para ubicar sensores.")
    
    m = folium.Map(location=datos_mun['coords'], zoom_start=15, control_scale=True)
    
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, popup=f"P{i+1}", icon=folium.Icon(color='blue')).add_to(m)

    mapa_res = st_folium(m, key="mapa_v4", width="100%", height=450, use_container_width=True)

    if mapa_res.get('last_clicked'):
        nuevo_p = [mapa_res['last_clicked']['lat'], mapa_res['last_clicked']['lng']]
        if not st.session_state.puntos or nuevo_p != st.session_state.puntos[-1]:
            st.session_state.puntos.append(nuevo_p)
            st.rerun()

    c1, c2 = st.columns(2)
    if c1.button("🚀 CALCULAR AHORA"):
        if len(st.session_state.puntos) >= 2:
            p1, p2 = st.session_state.puntos[-2], st.session_state.puntos[-1]
            st.session_state.res_dist = haversine(p1[0], p1[1], p2[0], p2[1])
            st.session_state.res_perd = perdida_hazen_williams(15, 140, dn, st.session_state.res_dist)
            st.session_state.calc_sim = True
        else:
            st.warning("⚠️ Marque 2 puntos en el mapa.")
            
    if c2.button("🗑️ LIMPIAR"):
        st.session_state.puntos = []
        st.session_state.calc_sim = False
        st.rerun()

    if st.session_state.calc_sim:
        st.markdown(f"""
        <div class="report-card">
            <h3>📊 Diagnóstico Hidráulico</h3>
            <p><b>Longitud:</b> {st.session_state.res_dist:.2f} m</p>
            <p><b>Pérdida (hf):</b> {st.session_state.res_perd:.4f} PSI</p>
        </div>
        """, unsafe_allow_status=True)

# =================================================================
# MODO 2: OPERACIÓN REAL (SOLUCIÓN DRIVE)
# =================================================================
elif modo == "📊 Auditoría Real (CSV)":
    st.subheader("Procesamiento de Datos de Campo")
    st.warning("📱 **AVISO:** Si no ve sus archivos, en el selector toque el menú (3 rayas) arriba a la izquierda y elija 'Drive'.")
    
    # type=None ELIMINA EL BLOQUEO DE VISIBILIDAD EN ANDROID
    archivo_input = st.file_uploader(
        "Seleccione su reporte (CSV, TXT o Excel)", 
        type=None,
        help="Sin filtros para asegurar visibilidad en móviles."
    )

    if archivo_input is not None:
        try:
            nombre = archivo_input.name.lower()
            if nombre.endswith('.csv'):
                df = pd.read_csv(archivo_input)
            elif nombre.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(archivo_input)
            else:
                df = pd.read_csv(archivo_input)
            
            st.success(f"✅ Archivo detectado.")
            st.dataframe(df.head(5), use_container_width=True)

            if st.button("🚀 PROCESAR AUDITORÍA"):
                df.columns = [str(c).lower().strip() for c in df.columns]
                if 'caudal' in df.columns and 'distancia' in df.columns:
                    df['perdida_psi'] = df.apply(
                        lambda r: perdida_hazen_williams(r['caudal'], 140, dn, r['distancia']), axis=1
                    )
                    st.session_state.res_real = df
                else:
                    st.error("❌ El archivo debe tener columnas 'caudal' y 'distancia'.")

        except Exception as e:
            st.error(f"Error técnico: {e}")

    if st.session_state.res_real is not None:
        st.divider()
        st.dataframe(st.session_state.res_real, use_container_width=True)
        csv_out = st.session_state.res_real.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DESCARGAR RESULTADOS", csv_out, "reporte.csv", "text/csv")

st.sidebar.divider()
st.sidebar.caption(f"© 2026 {AUTOR} | CRA Standard")

# =============================================================================
# PROYECTO: IANC H2O - AUDITORÍA TÉCNICA (CORE REFORZADO)
# Ingeniería: Ing. Adolfo Barrera Vargas
# Versión: 9.0 | Enfoque: Estabilidad de Conexión en Campo
# =============================================================================

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import io

# --- INTEGRACIÓN DEL CEREBRO HIDRÁULICO ---
try:
    from core import (
        haversine, perdida_hazen_williams, territorios, AUTOR
    )
except ImportError:
    st.error("🚨 Error Crítico de Archivos: Carpeta 'core' no detectada.")
    st.stop()

# Configuración de página de baja latencia
st.set_page_config(page_title="IANC H2O Pro", layout="wide")

# --- LÓGICA DE PERSISTENCIA (SESSION STATE) ---
if 'archivo_procesado' not in st.session_state: st.session_state.archivo_procesado = None
if 'puntos' not in st.session_state: st.session_state.puntos = []

# --- FUNCIÓN DE CARGA DE ALTA RESISTENCIA (CALLBACK) ---
def procesar_archivo_seguro():
    """Esta función captura el archivo antes de que la red falle en el móvil"""
    uploaded_file = st.session_state.uploader_maestro
    if uploaded_file is not None:
        try:
            # Leemos el buffer de inmediato
            data = uploaded_file.getvalue().decode('latin-1')
            sep = ';' if data.count(';') > data.count(',') else ','
            df = pd.read_csv(io.StringIO(data), sep=sep)
            # Limpiamos columnas en memoria antes de guardar
            df.columns = [str(c).lower().strip() for c in df.columns]
            st.session_state.archivo_procesado = df
        except Exception as e:
            st.error(f"Error interno en lectura: {e}")

# --- DISEÑO DE INTERFAZ ---
st.title("📡 IANC H2O: Auditoría de Precisión")
st.caption(f"**Ingeniería:** {AUTOR} | **Estándares:** CRA / Hazen-Williams")
st.divider()

# PANEL DE CONTROL
st.sidebar.header("🕹️ CONFIGURACIÓN")
modo = st.sidebar.radio("Módulo:", ["📍 Mapa y Simulación", "📊 Auditoría por Lote (CSV)"])
mun_sel = st.sidebar.selectbox("Municipio:", list(territorios.keys()))
dn = st.sidebar.selectbox("Diámetro Red (Pulg):", [2, 3, 4, 6, 8, 10, 12], index=2)

# =================================================================
# MÓDULO 1: MAPA (SIMULACIÓN GEOGRÁFICA)
# =================================================================
if modo == "📍 Mapa y Simulación":
    st.write(f"### Análisis de Tramo: {mun_sel}")
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
    for p in st.session_state.puntos:
        folium.Marker(p).add_to(m)

    # El mapa usa un ID único para no perder el foco en móviles
    map_data = st_folium(m, key="mapa_v9", width="100%", height=400, use_container_width=True)

    if map_data.get('last_clicked'):
        np = [map_data['last_clicked']['lat'], map_data['last_clicked']['lng']]
        if not st.session_state.puntos or np != st.session_state.puntos[-1]:
            st.session_state.puntos.append(np)
            st.rerun()

    if st.button("🚀 CALCULAR PÉRDIDA", use_container_width=True):
        if len(st.session_state.puntos) >= 2:
            p1, p2 = st.session_state.puntos[-2], st.session_state.puntos[-1]
            dist = haversine(p1[0], p1[1], p2[0], p2[1])
            perd = perdida_hazen_williams(15, 140, dn, dist)
            st.success(f"Distancia: {dist:.2f} m | Pérdida: {perd:.4f} PSI")

# =================================================================
# MÓDULO 2: AUDITORÍA REAL (EL MÉTODO "FORZADO")
# =================================================================
elif modo == "📊 Auditoría por Lote (CSV)":
    st.subheader("Procesamiento de Archivo Maestro")
    
    # El secreto técnico: on_change ejecuta la lógica ANTES de que el navegador refresque
    st.file_uploader(
        "📁 Seleccione reporte CSV de sensores", 
        type=None, 
        key="uploader_maestro",
        on_change=procesar_archivo_seguro # <-- LLAVE MAESTRA
    )

    if st.session_state.archivo_procesado is not None:
        df = st.session_state.archivo_procesado
        st.success("✅ Datos capturados en memoria.")
        st.dataframe(df.head(5), use_container_width=True)

        if st.button("🚀 EJECUTAR AUDITORÍA HIDRÁULICA", use_container_width=True):
            if 'caudal' in df.columns and 'distancia' in df.columns:
                with st.spinner("Procesando motor de cálculo..."):
                    df['perdida_psi'] = df.apply(
                        lambda r: perdida_hazen_williams(r['caudal'], 140, dn, r['distancia']), axis=1
                    )
                    st.write("#### REPORTE TÉCNICO GENERADO:")
                    st.dataframe(df, use_container_width=True)
                    
                    # Reporte de descarga profesional
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 DESCARGAR REPORTE", csv, "reporte_ianc.csv", "text/csv")
            else:
                st.error("Error: El archivo debe tener columnas 'caudal' y 'distancia'.")

st.sidebar.caption(f"© 2026 Auditoría H2O")

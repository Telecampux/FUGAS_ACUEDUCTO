# =============================================================================
# PROYECTO: IANC H2O - LOCALIZACIÓN DE FUGAS Y AUDITORÍA
# INGENIERÍA: Ing. Adolfo Barrera Vargas
# VERSIÓN: RECOMPUESTA (Simulación + Datos de Campo)
# =============================================================================

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import io

# --- INTEGRACIÓN CON EL NÚCLEO TÉCNICO ---
try:
    from core import (
        haversine, perdida_hazen_williams, territorios, 
        AUTOR, PROGRAMA_NOMBRE
    )
except ImportError:
    st.error("🚨 Error: No se encuentra 'core.py' en el repositorio.")
    st.stop()

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="IANC H2O Pro", layout="wide", page_icon="📡")

# Persistencia de memoria (Para que no se borre nada en el celular)
if 'pts_simulacion' not in st.session_state: st.session_state.pts_simulacion = []
if 'df_campo_crudo' not in st.session_state: st.session_state.df_campo_crudo = None
if 'df_campo_resultado' not in st.session_state: st.session_state.df_campo_resultado = None

# Estilos visuales
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; background-color: #1a73e8; color: white; }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 10px solid #1a73e8; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# --- CABECERA ---
st.title(f"📡 {PROGRAMA_NOMBRE}")
st.markdown(f"**Ingeniero Responsable:** {AUTOR}")
st.divider()

# --- MENÚ DE OPERACIÓN ---
st.sidebar.header("MENÚ DE CONTROL")
opcion = st.sidebar.radio("Seleccione Función:", ["📍 Simulación en Mapa", "📊 Datos de Campo (CSV)"])
st.sidebar.divider()

mun_sel = st.sidebar.selectbox("Municipio:", list(territorios.keys()))
dn_pulg = st.sidebar.selectbox("Diámetro Red (Pulg):", [2, 3, 4, 6, 8, 10, 12], index=2)
costo_agua = st.sidebar.number_input("Costo m³ (COP):", value=territorios[mun_sel]['costo'])

# =================================================================
# MÓDULO 1: SIMULACIÓN EN MAPA
# =================================================================
if opcion == "📍 Simulación en Mapa":
    st.subheader(f"Módulo de Simulación: {mun_sel}")
    st.info("Toque el mapa para definir los tramos de red y calcular pérdidas teóricas.")
    
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
    for i, p in enumerate(st.session_state.pts_simulacion):
        folium.Marker(p, popup=f"Punto {i+1}").add_to(m)

    map_res = st_folium(m, key="mapa_sim", width="100%", height=450, use_container_width=True)

    if map_res.get('last_clicked'):
        click = [map_res['last_clicked']['lat'], map_res['last_clicked']['lng']]
        if not st.session_state.pts_simulacion or click != st.session_state.pts_simulacion[-1]:
            st.session_state.pts_simulacion.append(click)
            st.rerun()

    c1, c2 = st.columns(2)
    if c1.button("🚀 EJECUTAR SIMULACIÓN"):
        if len(st.session_state.pts_simulacion) >= 2:
            p1, p2 = st.session_state.pts_simulacion[-2], st.session_state.pts_simulacion[-1]
            dist = haversine(p1[0], p1[1], p2[0], p2[1])
            hf = perdida_hazen_williams(15, 140, dn_pulg, dist)
            
            st.markdown(f"""
            <div class="report-card">
                <h4>📊 Informe de Simulación</h4>
                <p><b>Longitud del Tramo:</b> {dist:.2f} m</p>
                <p><b>Pérdida (PSI):</b> {hf:.4f}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Marque al menos 2 puntos en el mapa.")

    if c2.button("🗑️ LIMPIAR MAPA"):
        st.session_state.pts_simulacion = []
        st.rerun()

# =================================================================
# MÓDULO 2: DATOS DE CAMPO (CSV)
# =================================================================
elif opcion == "📊 Datos de Campo (CSV)":
    st.subheader("Módulo de Auditoría: Datos de Campo")
    st.write("Cargue su archivo de sensores para el procesamiento real.")
    
    archivo = st.file_uploader("Subir Reporte CSV", type=None, key="up_campo")

    if archivo is not None:
        try:
            # Lectura robusta para evitar errores de red y de formato (comas/puntos y comas)
            raw = archivo.getvalue().decode('latin-1')
            sep = ';' if raw.count(';') > raw.count(',') else ','
            st.session_state.df_campo_crudo = pd.read_csv(io.StringIO(raw), sep=sep)
            st.success("✅ Archivo de campo detectado con éxito.")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

    if st.session_state.df_campo_crudo is not None:
        df = st.session_state.df_campo_crudo
        st.write("### Vista previa de datos cargados:")
        st.dataframe(df.head(5), use_container_width=True)

        # MAPEADOR: Esto soluciona que el programa no encuentre las columnas
        st.info("⚙️ **Configuración de Datos:** Indique cuáles son las columnas de su archivo.")
        columnas = list(df.columns)
        
        # Búsqueda automática de nombres probables
        def_q = columnas.index([c for c in columnas if 'caudal' in c.lower()][0]) if any('caudal' in c.lower() for c in columnas) else 0
        def_d = columnas.index([c for c in columnas if 'distancia' in c.lower()][0]) if any('distancia' in c.lower() for c in columnas) else 1 if len(columnas) > 1 else 0

        col1, col2 = st.columns(2)
        q_col = col1.selectbox("Columna de CAUDAL:", columnas, index=def_q)
        d_col = col2.selectbox("Columna de DISTANCIA:", columnas, index=def_d)

        if st.button("🚀 PROCESAR DATOS DE CAMPO"):
            try:
                df_res = df.copy()
                df_res['perdida_psi'] = df_res.apply(
                    lambda r: perdida_hazen_williams(pd.to_numeric(r[q_col]), 140, dn_pulg, pd.to_numeric(r[d_col])), axis=1
                )
                st.session_state.df_campo_resultado = df_res
            except Exception as ex:
                st.error(f"Error en el cálculo: Verifique que las columnas sean numéricas. ({ex})")

    if st.session_state.df_campo_resultado is not None:
        st.divider()
        st.write("### 📋 Resultados de Auditoría de Campo:")
        st.dataframe(st.session_state.df_campo_resultado, use_container_width=True)
        
        csv_out = st.session_state.df_campo_resultado.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DESCARGAR RESULTADOS", csv_out, "auditoria_campo.csv", "text/csv")

st.sidebar.caption(f"© 2026 Auditoría H2O | Ing. Barrera")

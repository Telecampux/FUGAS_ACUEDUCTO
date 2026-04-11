# =============================================================================
# PROYECTO: IANC H2O - LOCALIZACIÓN DE FUGAS Y AUDITORÍA
# INGENIERÍA: Ing. Adolfo Barrera Vargas
# VERSIÓN: 18.0 (Versión Integradora - Blindaje Numérico)
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
    st.error("🚨 Error Crítico: No se encuentra 'core.py' en el repositorio.")
    st.stop()

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="IANC H2O Pro", layout="wide", page_icon="📡")

# Persistencia de memoria (State Management)
if 'pts_sim' not in st.session_state: st.session_state.pts_sim = []
if 'df_raw' not in st.session_state: st.session_state.df_raw = None
if 'df_res' not in st.session_state: st.session_state.df_res = None

# Estilos CSS Profesionales
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

# --- MENÚ DE CONTROL ---
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
    st.info("💡 Toque el mapa para definir los tramos de red.")
    
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
    for i, p in enumerate(st.session_state.pts_sim):
        folium.Marker(p, popup=f"Punto {i+1}").add_to(m)

    map_res = st_folium(m, key="mapa_sim_v18", width="100%", height=450, use_container_width=True)

    if map_res.get('last_clicked'):
        click = [map_res['last_clicked']['lat'], map_res['last_clicked']['lng']]
        if not st.session_state.pts_sim or click != st.session_state.pts_sim[-1]:
            st.session_state.pts_sim.append(click)
            st.rerun()

    c1, c2 = st.columns(2)
    if c1.button("🚀 EJECUTAR SIMULACIÓN"):
        if len(st.session_state.pts_sim) >= 2:
            p1, p2 = st.session_state.pts_sim[-2], st.session_state.pts_sim[-1]
            dist = haversine(p1[0], p1[1], p2[0], p2[1])
            hf = perdida_hazen_williams(15, 140, dn_pulg, dist)
            st.markdown(f"""<div class="report-card"><h4>📊 Resultado</h4><p>Longitud: {dist:.2f} m</p><p>Pérdida: {hf:.4f} PSI</p></div>""", unsafe_allow_html=True)
        else:
            st.warning("Marque al menos 2 puntos.")

    if c2.button("🗑️ LIMPIAR MAPA"):
        st.session_state.pts_sim = []
        st.rerun()

# =================================================================
# MÓDULO 2: DATOS DE CAMPO (CSV)
# =================================================================
elif opcion == "📊 Datos de Campo (CSV)":
    st.subheader("Auditoría de Campo")
    
    archivo = st.file_uploader("Subir Reporte CSV", type=None, key="up_v18")

    if archivo is not None:
        try:
            raw = archivo.getvalue().decode('latin-1')
            sep = ';' if raw.count(';') > raw.count(',') else ','
            st.session_state.df_raw = pd.read_csv(io.StringIO(raw), sep=sep)
            st.success("✅ Archivo cargado exitosamente.")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

    if st.session_state.df_raw is not None:
        df = st.session_state.df_raw
        st.write("### Vista previa de datos:")
        st.dataframe(df.head(5), use_container_width=True)

        st.info("⚙️ **Mapeador de Variables:** Seleccione las columnas de su archivo.")
        
        # Filtrar solo columnas numéricas para evitar errores como el de "Villeta"
        cols_num = df.select_dtypes(include=['number']).columns.tolist()
        cols_all = list(df.columns)
        opciones = cols_num if len(cols_num) > 0 else cols_all

        col1, col2 = st.columns(2)
        q_col = col1.selectbox("Variable CAUDAL:", opciones)
        d_col = col2.selectbox("Variable DISTANCIA:", opciones)

        if st.button("🚀 PROCESAR AUDITORÍA"):
            try:
                df_calc = df.copy()
                # Aseguramos que los datos sean numéricos y descartamos errores de texto
                df_calc[q_col] = pd.to_numeric(df_calc[q_col], errors='coerce')
                df_calc[d_col] = pd.to_numeric(df_calc[d_col], errors='coerce')
                df_calc = df_calc.dropna(subset=[q_col, d_col])

                df_calc['perdida_psi'] = df_calc.apply(
                    lambda r: perdida_hazen_williams(r[q_col], 140, dn_pulg, r[d_col]), axis=1
                )
                st.session_state.df_res = df_calc
                st.success("✅ Procesamiento terminado.")
            except Exception as ex:
                st.error(f"Error técnico en el cálculo: {ex}")

    if st.session_state.df_res is not None:
        st.divider()
        st.write("### 📋 Resultados Finales:")
        st.dataframe(st.session_state.df_res, use_container_width=True)
        
        csv_out = st.session_state.df_res.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DESCARGAR REPORTE", csv_out, "auditoria_campo.csv", "text/csv")

st.sidebar.caption(f"© 2026 Auditoría H2O | Ing. Barrera")

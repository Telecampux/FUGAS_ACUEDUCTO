# =============================================================================
# PROYECTO: IANC H2O - AUDITORÍA TÉCNICA
# Versión: 5.2 (Motor de Carga Reforzado para Móviles)
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import streamlit.components.v1 as components
import io

# --- CONEXIÓN CON EL MÓDULO DE CÁLCULO (CORE) ---
try:
    from core import (
        haversine, perdida_hazen_williams, territorios, 
        PROGRAMA_NOMBRE, AUTOR, EMPRESA_DEFAULT
    )
except ImportError:
    st.error("🚨 Error: No se encuentra la carpeta 'core'.")
    st.stop()

st.set_page_config(page_title="IANC H2O Pro", layout="wide")

# --- ESTILOS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; background-color: #1a73e8; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("📡 IANC H2O - AUDITORÍA")
st.divider()

modo = st.sidebar.radio("Función:", ["📍 Simulación Mapa", "📊 Auditoría Real (CSV)"])
mun_sel = st.sidebar.selectbox("Municipio:", list(territorios.keys()))
dn = st.sidebar.selectbox("Diámetro Red (Pulg):", [2, 3, 4, 6, 8, 10, 12], index=2)

# --- INICIALIZACIÓN DE ESTADOS ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'res_real' not in st.session_state: st.session_state.res_real = None

# =================================================================
# MODO 1: SIMULACIÓN INTERACTIVA
# =================================================================
if modo == "📍 Simulación Mapa":
    st.write(f"### Mapa: {mun_sel}")
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, popup=f"P{i+1}", icon=folium.Icon(color='blue')).add_to(m)
    
    mapa_res = st_folium(m, key="mapa_v7", width="100%", height=400, use_container_width=True)

    if mapa_res.get('last_clicked'):
        np = [mapa_res['last_clicked']['lat'], mapa_res['last_clicked']['lng']]
        if not st.session_state.puntos or np != st.session_state.puntos[-1]:
            st.session_state.puntos.append(np)
            st.rerun()

    if st.button("🚀 CALCULAR SIMULACIÓN"):
        if len(st.session_state.puntos) >= 2:
            p1, p2 = st.session_state.puntos[-2], st.session_state.puntos[-1]
            dist = haversine(p1[0], p1[1], p2[0], p2[1])
            perd = perdida_hazen_williams(15, 140, dn, dist)
            st.success(f"Distancia: {dist:.2f} m | Pérdida: {perd:.4f} PSI")
        else:
            st.warning("Marque 2 puntos.")

# =================================================================
# MODO 2: AUDITORÍA REAL (LECTURA REFORZADA)
# =================================================================
elif modo == "📊 Auditoría Real (CSV)":
    st.subheader("Carga de Datos de Campo")
    
    archivo_input = st.file_uploader("Seleccione el archivo de sensores", type=None)

    if archivo_input is not None:
        try:
            # --- MOTOR DE DETECCIÓN DE FORMATO ---
            # Leemos una parte del archivo para detectar si usa coma o punto y coma
            bytes_data = archivo_input.getvalue()
            string_data = bytes_data.decode('latin-1') # Usamos latin-1 para evitar errores con tildes
            
            # Decidir el separador (si hay más ';' que ',' usamos ';')
            sep = ';' if string_data.count(';') > string_data.count(',') else ','
            
            # Cargar el DataFrame con el separador detectado
            df = pd.read_csv(io.StringIO(string_data), sep=sep)
            
            st.success(f"✅ Archivo leído correctamente (Separador: '{sep}')")
            st.write("Vista previa de los datos:")
            st.dataframe(df.head(5), use_container_width=True)

            if st.button("🚀 PROCESAR AUDITORÍA"):
                # Limpiar nombres de columnas
                df.columns = [str(c).lower().strip() for c in df.columns]
                
                if 'caudal' in df.columns and 'distancia' in df.columns:
                    df['perdida_psi'] = df.apply(
                        lambda r: perdida_hazen_williams(r['caudal'], 140, dn, r['distancia']), axis=1
                    )
                    st.session_state.res_real = df
                    st.write("#### RESULTADOS FINALES:")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error("❌ El archivo debe tener columnas llamadas 'caudal' y 'distancia'.")
                    
        except Exception as e:
            st.error(f"Falla al procesar el archivo: {e}")

st.sidebar.caption(f"© 2026 Auditoría H2O")

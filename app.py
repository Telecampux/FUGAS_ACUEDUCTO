# =============================================================================
# PROYECTO: IANC H2O - AUDITORÍA TÉCNICA (VERSION RESISTENCIA)
# Versión: 6.0 | Autor: Ing. Adolfo Barrera Vargas
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import io

# --- CONEXIÓN CORE ---
try:
    from core import haversine, perdida_hazen_williams, territorios, AUTOR
except ImportError:
    st.error("Error: No se detecta la carpeta 'core'.")
    st.stop()

st.set_page_config(page_title="IANC H2O Pro", layout="wide")

# Estilos optimizados para evitar sobrecarga de red
st.markdown("<style>.stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #1a73e8; color: white; font-weight: bold; }</style>", unsafe_allow_html=True)

st.title("📡 IANC H2O - AUDITORÍA")
st.caption(f"Ingeniero: {AUTOR}")

# --- NAVEGACIÓN ---
modo = st.sidebar.radio("Función:", ["📍 Simulación Mapa", "📊 Auditoría Real"])
mun_sel = st.sidebar.selectbox("Municipio:", list(territorios.keys()))
dn = st.sidebar.selectbox("Diámetro Red (Pulg):", [2, 3, 4, 6, 8, 10, 12], index=2)

if 'puntos' not in st.session_state: st.session_state.puntos = []

# =================================================================
# MODO 1: SIMULACIÓN
# =================================================================
if modo == "📍 Simulación Mapa":
    st.write(f"### Mapa: {mun_sel}")
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p).add_to(m)
    
    mapa_res = st_folium(m, key="mapa_v10", width="100%", height=400, use_container_width=True)

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

# =================================================================
# MODO 2: AUDITORÍA REAL (CON PLAN B DE COPIA/PEGA)
# =================================================================
elif modo == "📊 Auditoría Real":
    st.subheader("Ingreso de Datos de Campo")
    
    # Creamos pestañas para dar opciones si falla la red
    tab1, tab2 = st.tabs(["📁 Subir Archivo CSV", "📝 Copiar/Pegar Datos"])

    df_a_procesar = None

    with tab1:
        archivo = st.file_uploader("Cargar CSV", type=None, key="up_v6")
        if archivo:
            try:
                # Lectura robusta con detección de separador
                data = archivo.getvalue().decode('latin-1')
                sep = ';' if data.count(';') > data.count(',') else ','
                df_a_procesar = pd.read_csv(io.StringIO(data), sep=sep)
                st.success("Archivo cargado por archivo.")
            except Exception as e:
                st.error("Error de red al subir. Use la pestaña 'Copiar/Pegar Datos'.")

    with tab2:
        st.write("Abra su archivo en el celular, copie los datos y péguelos abajo:")
        texto_pega = st.text_area("Pegue aquí el contenido del CSV", height=150, help="Debe incluir los encabezados: caudal, distancia")
        if texto_pega:
            try:
                sep_p = ';' if texto_pega.count(';') > texto_pega.count(',') else ','
                df_a_procesar = pd.read_csv(io.StringIO(texto_pega), sep=sep_p)
                st.success("Datos capturados desde texto.")
            except Exception as e:
                st.error("Formato de texto no reconocido.")

    # --- PROCESAMIENTO UNIFICADO ---
    if df_a_procesar is not None:
        st.dataframe(df_a_procesar.head(3), use_container_width=True)
        if st.button("🚀 EJECUTAR PROCESAMIENTO"):
            df_a_procesar.columns = [str(c).lower().strip() for c in df_a_procesar.columns]
            if 'caudal' in df_a_procesar.columns and 'distancia' in df_a_procesar.columns:
                df_a_procesar['perdida_psi'] = df_a_procesar.apply(
                    lambda r: perdida_hazen_williams(r['caudal'], 140, dn, r['distancia']), axis=1
                )
                st.write("#### RESULTADOS:")
                st.dataframe(df_a_procesar, use_container_width=True)
            else:
                st.error("El sistema requiere columnas: 'caudal' y 'distancia'.")

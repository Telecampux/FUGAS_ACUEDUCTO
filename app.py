# =============================================================================
# PROYECTO: IANC H2O - AUDITORÍA TÉCNICA
# Versión: 5.5 (Estabilidad de Red - Fix AxiosError)
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import io

# --- CONEXIÓN CON EL MÓDULO DE CÁLCULO (CORE) ---
try:
    from core import (
        haversine, perdida_hazen_williams, territorios, 
        PROGRAMA_NOMBRE, AUTOR
    )
except ImportError:
    st.error("🚨 Error: No se encuentra la carpeta 'core'.")
    st.stop()

# Configuración ligera para evitar caídas de red
st.set_page_config(page_title="IANC H2O Pro", layout="wide")

# Estilos básicos
st.markdown("""<style>.stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #1a73e8; color: white; }</style>""", unsafe_allow_html=True)

st.title("📡 IANC H2O - AUDITORÍA")

# --- NAVEGACIÓN ---
modo = st.sidebar.radio("Función:", ["📍 Simulación Mapa", "📊 Auditoría Real (CSV)"])
mun_sel = st.sidebar.selectbox("Municipio:", list(territorios.keys()))
dn = st.sidebar.selectbox("Diámetro Red (Pulg):", [2, 3, 4, 6, 8, 10, 12], index=2)

# Persistencia
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'df_final' not in st.session_state: st.session_state.df_final = None

# =================================================================
# MODO 1: SIMULACIÓN
# =================================================================
if modo == "📍 Simulación Mapa":
    st.write(f"### Mapa: {mun_sel}")
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, icon=folium.Icon(color='blue')).add_to(m)
    
    # Mapa con clave única para evitar refrescos de red
    mapa_res = st_folium(m, key="mapa_v8", width="100%", height=400, use_container_width=True)

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
# MODO 2: AUDITORÍA REAL (SOLUCIÓN AXIOS ERROR)
# =================================================================
elif modo == "📊 Auditoría Real (CSV)":
    st.subheader("Carga de Datos de Campo")
    
    # Usamos una clave única para el uploader para estabilizar la conexión
    archivo_input = st.file_uploader("Seleccione el archivo", type=None, key="uploader_estable")

    if archivo_input is not None:
        try:
            # LEER DATOS (Sin procesar nada todavía para no saturar la red)
            raw_data = archivo_input.getvalue()
            
            # Intentar detectar formato automáticamente
            content = raw_data.decode('latin-1')
            sep = ';' if content.count(';') > content.count(',') else ','
            
            df = pd.read_csv(io.StringIO(content), sep=sep)
            
            st.success("✅ Archivo cargado en memoria.")
            st.dataframe(df.head(3), use_container_width=True)

            if st.button("🚀 EJECUTAR PROCESAMIENTO"):
                with st.spinner("Calculando con el Core..."):
                    df.columns = [str(c).lower().strip() for c in df.columns]
                    if 'caudal' in df.columns and 'distancia' in df.columns:
                        df['perdida_psi'] = df.apply(
                            lambda r: perdida_hazen_williams(r['caudal'], 140, dn, r['distancia']), axis=1
                        )
                        st.session_state.df_final = df
                        st.write("#### RESULTADOS:")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.error("Faltan columnas 'caudal' o 'distancia'.")
                        
        except Exception as e:
            st.error("Error de lectura. Intente descargar el archivo al celular antes de subirlo.")
            st.info(f"Detalle técnico: {e}")

st.sidebar.caption(f"© 2026 Auditoría H2O")

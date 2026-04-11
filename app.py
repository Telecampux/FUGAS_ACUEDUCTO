# =============================================================================
# PROYECTO: IANC H2O - LOCALIZACIÓN DE FUGAS Y AUDITORÍA TÉCNICA
# INGENIERÍA: Ing. Adolfo Barrera Vargas
# VERSIÓN: 17.0 (Master Release - Ingeniería de Resiliencia)
# ESTÁNDARES: Hazen-Williams / Metodología IANC
# =============================================================================

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import io

# --- INTEGRACIÓN CON EL NÚCLEO TÉCNICO (CORE) ---
try:
    from core import (
        haversine, perdida_hazen_williams, territorios, 
        AUTOR, PROGRAMA_NOMBRE
    )
except ImportError:
    st.error("🚨 Error de Integridad: No se detecta el archivo 'core.py' en GitHub.")
    st.stop()

# --- CONFIGURACIÓN DE PLATAFORMA ---
st.set_page_config(
    page_title="IANC H2O Pro",
    layout="wide",
    page_icon="📡",
    initial_sidebar_state="expanded"
)

# --- PERSISTENCIA DE DATOS (SESSION STATE) ---
if 'puntos_mapa' not in st.session_state: st.session_state.puntos_mapa = []
if 'df_crudo' not in st.session_state: st.session_state.df_crudo = None
if 'df_resultado' not in st.session_state: st.session_state.df_resultado = None

# --- ESTILOS DE INGENIERÍA (CSS PROFESIONAL) ---
st.markdown("""
    <style>
    .main { background-color: #fdfdfd; }
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        font-weight: bold; background-color: #1a73e8; color: white;
        border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .report-card { 
        background-color: #ffffff; padding: 25px; border-radius: 12px; 
        border-left: 8px solid #1a73e8; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CABECERA ---
st.title(f"📡 {PROGRAMA_NOMBRE}")
st.markdown(f"**Líder de Proyecto:** Ing. {AUTOR}")
st.divider()

# --- PANEL DE CONTROL LATERAL ---
st.sidebar.header("⚙️ CONFIGURACIÓN")
modulo = st.sidebar.selectbox("Seleccione Módulo:", ["📍 Mapa Operativo", "📊 Auditoría por Lote"])
st.sidebar.divider()

mun_sel = st.sidebar.selectbox("Municipio de Trabajo:", list(territorios.keys()))
datos_mun = territorios[mun_sel]
dn_pulg = st.sidebar.selectbox("Diámetro Red (Pulg):", [2, 3, 4, 6, 8, 10, 12], index=2)
costo_m3 = st.sidebar.number_input("Costo m³ (COP):", value=datos_mun['costo'])

# =================================================================
# MÓDULO 1: MAPA OPERATIVO (GEORREFERENCIACIÓN)
# =================================================================
if modulo == "📍 Mapa Operativo":
    st.subheader(f"Análisis Espacial: {mun_sel}")
    st.info("💡 Marque los puntos en el mapa para calcular la pérdida del tramo.")
    
    m = folium.Map(location=datos_mun['coords'], zoom_start=15, control_scale=True)
    for i, p in enumerate(st.session_state.puntos_mapa):
        folium.Marker(p, popup=f"P{i+1}", icon=folium.Icon(color='blue')).add_to(m)

    map_data = st_folium(m, key="mapa_v17", width="100%", height=450, use_container_width=True)

    if map_data.get('last_clicked'):
        nuevo_click = [map_data['last_clicked']['lat'], map_data['last_clicked']['lng']]
        if not st.session_state.puntos_mapa or nuevo_click != st.session_state.puntos_mapa[-1]:
            st.session_state.puntos_mapa.append(nuevo_click)
            st.rerun()

    c1, c2 = st.columns(2)
    if c1.button("🚀 CALCULAR PÉRDIDAS"):
        if len(st.session_state.puntos_mapa) >= 2:
            p1, p2 = st.session_state.puntos_mapa[-2], st.session_state.puntos_mapa[-1]
            distancia_m = haversine(p1[0], p1[1], p2[0], p2[1])
            # Cálculo Hidráulico (Q=15 LPS, C=140)
            hf_psi = perdida_hazen_williams(15, 140, dn_pulg, distancia_m)
            
            st.markdown(f"""
            <div class="report-card">
                <h4>📊 Informe de Tramo</h4>
                <p><b>Longitud:</b> {distancia_m:.2f} m</p>
                <p><b>Pérdida (hf):</b> {hf_psi:.4f} PSI</p>
                <p><b>Costo Proyectado:</b> ${(distancia_m * costo_m3 / 10):,.0f} COP</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Seleccione al menos 2 puntos.")

    if c2.button("🗑️ REINICIAR"):
        st.session_state.puntos_mapa = []
        st.rerun()

# =================================================================
# MÓDULO 2: AUDITORÍA POR LOTE (MAPEADOR DINÁMICO)
# =================================================================
elif modulo == "📊 Auditoría por Lote":
    st.subheader("Auditoría Técnica de Sensores")
    
    # Carga de archivo con blindaje de red
    archivo = st.file_uploader("📁 Cargar reporte CSV", type=None)

    if archivo is not None:
        try:
            raw_bytes = archivo.getvalue()
            content = raw_bytes.decode('latin-1')
            sep = ';' if content.count(';') > content.count(',') else ','
            st.session_state.df_crudo = pd.read_csv(io.StringIO(content), sep=sep)
            st.success("✅ Archivo cargado.")
        except Exception as e:
            st.error(f"Error de red: {e}")

    if st.session_state.df_crudo is not None:
        df = st.session_state.df_crudo
        st.dataframe(df.head(5), use_container_width=True)

        st.info("⚙️ **Mapeo de Datos:** Seleccione las columnas de su archivo.")
        cols = list(df.columns)
        
        # Búsqueda inteligente de columnas
        def_q = cols.index([c for c in cols if 'caudal' in str(c).lower()][0]) if any('caudal' in str(c).lower() for c in cols) else 0
        def_d = cols.index([c for c in cols if 'distancia' in str(c).lower()][0]) if any('distancia' in str(c).lower() for c in cols) else 1 if len(cols) > 1 else 0

        c_q, c_d = st.columns(2)
        sel_q = c_q.selectbox("Columna Caudal:", cols, index=def_q)
        sel_d = c_d.selectbox("Columna Distancia:", cols, index=def_d)

        if st.button("🚀 EJECUTAR AUDITORÍA"):
            try:
                df_res = df.copy()
                df_res['perdida_psi'] = df_res.apply(
                    lambda r: perdida_hazen_williams(pd.to_numeric(r[sel_q]), 140, dn_pulg, pd.to_numeric(r[sel_d])), axis=1
                )
                st.session_state.df_resultado = df_res
            except Exception as ex:
                st.error(f"Error en datos: {ex}")

    if st.session_state.df_resultado is not None:
        st.divider()
        st.write("### Reporte Procesado:")
        st.dataframe(st.session_state.df_resultado, use_container_width=True)
        csv_final = st.session_state.df_resultado.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DESCARGAR RESULTADOS", csv_final, "auditoria_h2o.csv", "text/csv")

st.sidebar.divider()
st.sidebar.caption(f"© 2026 Auditoría H2O | Ing. Barrera")

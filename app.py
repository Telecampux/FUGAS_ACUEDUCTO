# =============================================================================
# PROYECTO: IANC H2O - LOCALIZACIÓN DE FUGAS Y AUDITORÍA
# INGENIERÍA: Ing. Adolfo Barrera Vargas
# VERSIÓN: RETORNO A LA ESENCIA (Directa y Automática)
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

# Persistencia de memoria
if 'puntos_sim' not in st.session_state: st.session_state.puntos_sim = []
if 'df_resultado' not in st.session_state: st.session_state.df_resultado = None

# Estilos visuales limpios
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; background-color: #1a73e8; color: white; }
    .report-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 8px solid #1a73e8; }
    </style>
""", unsafe_allow_html=True)

# --- CABECERA ---
st.title(f"📡 {PROGRAMA_NOMBRE}")
st.markdown(f"**Ingeniero Responsable:** {AUTOR}")
st.divider()

# --- MENÚ DE OPERACIÓN ---
st.sidebar.header("MENÚ DE CONTROL")
opcion = st.sidebar.radio("Módulo de Trabajo:", ["📍 Simulación en Mapa", "📊 Datos de Campo (Lotes)"])
st.sidebar.divider()

mun_sel = st.sidebar.selectbox("Municipio:", list(territorios.keys()))
dn_pulg = st.sidebar.selectbox("Diámetro Red (Pulg):", [2, 3, 4, 6, 8, 10, 12], index=2)

# =================================================================
# MÓDULO 1: SIMULACIÓN EN MAPA (MÉTODO DIRECTO)
# =================================================================
if opcion == "📍 Simulación en Mapa":
    st.subheader(f"Simulación de Tramos: {mun_sel}")
    st.info("Toque 2 puntos en el mapa para calcular la longitud y la pérdida.")
    
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
    for i, p in enumerate(st.session_state.puntos_sim):
        folium.Marker(p, popup=f"Punto {i+1}").add_to(m)

    mapa = st_folium(m, key="mapa_directo", width="100%", height=450, use_container_width=True)

    if mapa.get('last_clicked'):
        click = [mapa['last_clicked']['lat'], mapa['last_clicked']['lng']]
        if not st.session_state.puntos_sim or click != st.session_state.puntos_sim[-1]:
            st.session_state.puntos_sim.append(click)
            st.rerun()

    c1, c2 = st.columns(2)
    if c1.button("🚀 EJECUTAR SIMULACIÓN"):
        if len(st.session_state.puntos_sim) >= 2:
            p1, p2 = st.session_state.puntos_sim[-2], st.session_state.puntos_sim[-1]
            distancia = haversine(p1[0], p1[1], p2[0], p2[1])
            perdida = perdida_hazen_williams(15, 140, dn_pulg, distancia)
            
            st.markdown(f"""
            <div class="report-box">
                <h4>📊 Resultados del Tramo</h4>
                <p><b>Longitud calculada:</b> {distancia:.2f} metros</p>
                <p><b>Pérdida por fricción (hf):</b> {perdida:.4f} PSI</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Marque al menos 2 puntos en el mapa.")

    if c2.button("🗑️ LIMPIAR MAPA"):
        st.session_state.puntos_sim = []
        st.rerun()

# =================================================================
# MÓDULO 2: DATOS DE CAMPO POR LOTES (MÉTODO AUTOMÁTICO)
# =================================================================
elif opcion == "📊 Datos de Campo (Lotes)":
    st.subheader("Auditoría de Sensores en Lote")
    st.write("Sincronice su archivo CSV. El sistema detectará las variables automáticamente.")
    
    archivo = st.file_uploader("📁 Subir Archivo", type=None)

    if archivo is not None:
        try:
            # Lectura en memoria a prueba de errores
            raw = archivo.getvalue().decode('latin-1')
            sep = ';' if raw.count(';') > raw.count(',') else ','
            df = pd.read_csv(io.StringIO(raw), sep=sep)
            
            # Limpieza automática de columnas (minúsculas y sin espacios extra)
            df.columns = [str(c).lower().strip() for c in df.columns]

            if 'caudal' in df.columns and 'distancia' in df.columns:
                st.success("✅ Archivo válido. Variables 'caudal' y 'distancia' detectadas.")
                
                if st.button("🚀 EJECUTAR PROCESAMIENTO"):
                    with st.spinner("Calculando..."):
                        # Forzar conversión a números de forma invisible (ignora textos como "Villeta")
                        df['caudal'] = pd.to_numeric(df['caudal'], errors='coerce')
                        df['distancia'] = pd.to_numeric(df['distancia'], errors='coerce')
                        
                        # Quitar filas que hayan quedado vacías por ser texto
                        df = df.dropna(subset=['caudal', 'distancia'])
                        
                        # Cálculo matemático
                        df['perdida_psi'] = df.apply(
                            lambda r: perdida_hazen_williams(r['caudal'], 140, dn_pulg, r['distancia']), axis=1
                        )
                        st.session_state.df_resultado = df
            else:
                st.error("❌ El archivo no contiene las columnas 'caudal' y 'distancia'. Verifique su reporte.")

        except Exception as e:
            st.error(f"Error de lectura del archivo: {e}")

    # Mostrar Resultados directamente
    if st.session_state.df_resultado is not None:
        st.divider()
        st.write("### 📋 Tabla de Resultados:")
        st.dataframe(st.session_state.df_resultado, use_container_width=True)
        
        csv_out = st.session_state.df_resultado.to_csv(index=False).encode('utf-8')
        st.download_button("📥 DESCARGAR AUDITORÍA", csv_out, "auditoria_procesada.csv", "text/csv")

st.sidebar.caption(f"© 2026 Auditoría H2O | Ing. Barrera")

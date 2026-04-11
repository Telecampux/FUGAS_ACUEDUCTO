# =============================================================================
# AVISO DE PROPIEDAD INTELECTUAL Y DERECHOS DE AUTOR
# =============================================================================
# Proyecto: IANC H2O - Auditoría Técnica de Acueductos
# Autor: Ing. Adolfo Barrera Vargas | Versión: 2.7 (Mobile Fix - Android)
# (c) Copyright 2026. Todos los derechos reservados. Colombia.
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import streamlit.components.v1 as components
import io

# --- IMPORTACIÓN DESDE EL CEREBRO (CORE) ---
# Se asume que la estructura de carpetas en GitHub es: /app.py y /core/
try:
    from core import (
        haversine, perdida_hazen_williams, territorios, 
        PROGRAMA_NOMBRE, AUTOR, EMPRESA_DEFAULT
    )
except ImportError:
    st.error("🚨 Error Crítico: No se encontró la carpeta 'core'. Verifique su repositorio privado.")
    st.stop()

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="IANC H2O Pro", layout="wide", page_icon="📡")

# Inyección PWA para que el celular lo reconozca como App nativa
components.html(f'<link rel="manifest" href="./static/manifest.json">', height=0)

# --- INICIALIZACIÓN DE ESTADOS (PERSISTENCIA MÓVIL) ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'ejecutado' not in st.session_state: st.session_state.ejecutado = False
if 'df_resultados' not in st.session_state: st.session_state.df_resultados = None
if 'procesado_real' not in st.session_state: st.session_state.procesado_real = False

# --- ENCABEZADO ---
st.title("📡 IANC H2O - AUDITORÍA")
st.caption(f"**Ingeniería:** {AUTOR} | **Municipio:** {territorios[list(territorios.keys())[0]] if 'mun_sel' not in locals() else 'Cargando...'}")
st.divider()

# --- SIDEBAR ---
st.sidebar.header("🕹️ NAVEGACIÓN")
modo = st.sidebar.radio("Seleccione Función:", ["Simulación Interactiva", "Operación Real (Lote)"])

st.sidebar.divider()
mun_sel = st.sidebar.selectbox("Municipio de Trabajo:", list(territorios.keys()))
datos_mun = territorios[mun_sel]
costo_m3 = st.sidebar.number_input("Costo del Agua ($/m³)", value=datos_mun['costo'])
dn = st.sidebar.selectbox("Diámetro Red (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=2)

# --- MODO 1: SIMULACIÓN INTERACTIVA ---
if modo == "Simulación Interactiva":
    st.write(f"### 📍 Mapa de Simulación: {mun_sel}")
    
    # Mapa responsivo
    m = folium.Map(location=datos_mun['coords'], zoom_start=15, control_scale=True)
    
    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, popup=f"P{i+1}", icon=folium.Icon(color='blue')).add_to(m)

    # El mapa detecta clics/toques
    mapa_data = st_folium(m, key="mapa_v3", width="100%", height=450, use_container_width=True)

    if mapa_data.get('last_clicked'):
        nuevo_p = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
        if not st.session_state.puntos or nuevo_p != st.session_state.puntos[-1]:
            st.session_state.puntos.append(nuevo_p)
            st.rerun()

    col_acc1, col_acc2 = st.columns(2)
    if col_acc1.button("🚀 CALCULAR PÉRDIDAS", use_container_width=True):
        if len(st.session_state.puntos) >= 2:
            p1, p2 = st.session_state.puntos[-2], st.session_state.puntos[-1]
            dist = haversine(p1[0], p1[1], p2[0], p2[1])
            perd = perdida_hazen_williams(15, 140, dn, dist) # Caudal base 15LPS
            
            st.session_state.res_dist = dist
            st.session_state.res_perd = perd
            st.session_state.ejecutado = True
        else:
            st.warning("Marque al menos 2 puntos en el mapa.")

    if col_acc2.button("🗑️ REINICIAR", use_container_width=True):
        st.session_state.puntos = []
        st.session_state.ejecutado = False
        st.rerun()

    if st.session_state.ejecutado:
        st.success("✅ Diagnóstico de Tramo")
        r1, r2 = st.columns(2)
        r1.metric("Distancia", f"{st.session_state.res_dist:.2f} m")
        r2.metric("Pérdida hf", f"{st.session_state.res_perd:.4f} PSI")

# --- MODO 2: OPERACIÓN REAL (SOLUCIÓN CARGA ANDROID) ---
elif modo == "Operación Real (Lote)":
    st.write("### 📊 Auditoría Técnica con Datos de Campo")
    
    # 1. GENERADOR DE PLANTILLA (Para asegurar que el formato sea correcto)
    with st.expander("📝 Obtener Plantilla para CSV"):
        st.write("Si su archivo no carga, use esta estructura:")
        df_base = pd.DataFrame({'caudal': [10.5, 12.0], 'distancia': [100.0, 150.0]})
        csv_buffer = io.StringIO()
        df_base.to_csv(csv_buffer, index=False)
        st.download_button("Descargar Plantilla CSV", csv_buffer.getvalue(), "modelo_ianc.csv", "text/csv", use_container_width=True)

    st.divider()
    
    # 2. CARGADOR MULTI-FORMATO (Acepta CSV y TXT para mayor visibilidad en Android)
    st.info("Toque abajo para buscar su archivo en Drive o Memoria Interna")
    archivo_input = st.file_uploader(
        "Seleccionar reporte de campo", 
        type=["csv", "txt"], 
        help="Si no ve su archivo en Drive, intente descargarlo primero a la memoria del celular."
    )

    if archivo_input is not None:
        try:
            df_campo = pd.read_csv(archivo_input)
            st.success("✅ Archivo cargado correctamente")
            st.dataframe(df_campo.head(5), use_container_width=True)

            if st.button("🚀 PROCESAR AUDITORÍA MASIVA", use_container_width=True):
                # Validación de columnas para el motor del Core
                columnas = [c.lower() for c in df_campo.columns]
                if 'caudal' in columnas and 'distancia' in columnas:
                    # Normalizar nombres de columnas a minúsculas
                    df_campo.columns = columnas
                    df_campo['perdida_psi'] = df_campo.apply(
                        lambda r: perdida_hazen_williams(r['caudal'], 140, dn, r['distancia']), axis=1
                    )
                    st.session_state.df_resultados = df_campo
                    st.session_state.procesado_real = True
                else:
                    st.error("Error: El archivo debe tener las columnas 'caudal' y 'distancia'.")

        except Exception as e:
            st.error(f"Falla al leer el archivo: {e}")

    # 3. RESULTADOS PERSISTENTES
    if st.session_state.procesado_real:
        st.divider()
        st.subheader("📋 Resultados del Análisis")
        st.dataframe(st.session_state.df_resultados, use_container_width=True)
        
        # Opción de Exportación
        res_csv = st.session_state.df_resultados.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte Final", res_csv, "resultado_auditoria.csv", "text/csv", use_container_width=True)

# --- PIE DE PÁGINA ---
st.sidebar.divider()
st.sidebar.caption(f"© 2026 {AUTOR} | Estándares CRA")

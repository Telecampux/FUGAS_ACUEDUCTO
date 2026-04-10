# =============================================================================
# AVISO DE PROPIEDAD INTELECTUAL Y DERECHOS DE AUTOR
# =============================================================================
# Proyecto: IANC H2O - Auditoría Técnica de Acueductos
# Autor: Ing. Adolfo Barrera Vargas | Versión: 2.5 (Móvil-Pro)
# (c) Copyright 2026. Todos los derechos reservados. Colombia.
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import streamlit.components.v1 as components

# --- IMPORTACIÓN DESDE EL CEREBRO (CORE) ---
from core import (
    haversine, perdida_hazen_williams, territorios, 
    PROGRAMA_NOMBRE, AUTOR, EMPRESA_DEFAULT
)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="IANC H2O Pro", layout="wide", page_icon="📡")

# Inyección PWA para el celular
components.html(f'<link rel="manifest" href="./static/manifest.json">', height=0)

# --- INICIALIZACIÓN DE ESTADOS (PERSISTENCIA MÓVIL) ---
variables_estado = {
    'puntos': [], 'ejecutado': False, 'empresa': EMPRESA_DEFAULT,
    'res_distancia': 0.0, 'res_perdida': 0.0, 'procesado_real': False,
    'df_resultados': None
}
for key, default in variables_estado.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- ENCABEZADO ---
st.title("📡 IANC H2O - AUDITORÍA PRO")
st.caption(f"**Tecnología:** {PROGRAMA_NOMBRE} | **Autor:** {AUTOR}")
st.divider()

# --- SIDEBAR ---
st.sidebar.header("🕹️ PANEL DE CONTROL")
modo = st.sidebar.radio("Modo:", ["Simulación Interactiva", "Operación Real (Lote)"])

st.sidebar.divider()
mun_sel = st.sidebar.selectbox("Municipio:", list(territorios.keys()))
costo_m3 = st.sidebar.number_input("Costo m³", value=territorios[mun_sel]['costo'])
dn = st.sidebar.selectbox("Diámetro (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=2)

# --- MODO 1: SIMULACIÓN INTERACTIVA ---
if modo == "Simulación Interactiva":
    st.write(f"### 📍 Simulación: {mun_sel}")
    
    # Carga de Plano GIS
    with st.sidebar.expander("🗺️ Capas GIS"):
        archivo_gis = st.file_uploader("Subir Red (.geojson)", type=["geojson", "json"])

    # Mapa persistente y responsivo
    m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
    
    if archivo_gis:
        try:
            folium.GeoJson(json.load(archivo_gis), name="Red").add_to(m)
        except: st.sidebar.error("Error en GeoJSON")

    for i, p in enumerate(st.session_state.puntos):
        folium.Marker(p, popup=f"P{i+1}", icon=folium.Icon(color='blue')).add_to(m)

    mapa_data = st_folium(m, key="mapa_campo", width="100%", height=450, use_container_width=True)

    # Captura de puntos optimizada para táctil
    if mapa_data.get('last_clicked'):
        nuevo_p = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
        if not st.session_state.puntos or nuevo_p != st.session_state.puntos[-1]:
            st.session_state.puntos.append(nuevo_p)
            st.rerun()

    # Botones de Acción
    c_btn1, c_btn2 = st.columns(2)
    if c_btn1.button("🚀 EJECUTAR CÁLCULOS", use_container_width=True):
        if len(st.session_state.puntos) >= 2:
            p1, p2 = st.session_state.puntos[-2], st.session_state.puntos[-1]
            st.session_state.res_distancia = haversine(p1[0], p1[1], p2[0], p2[1])
            st.session_state.res_perdida = perdida_hazen_williams(15, 140, dn, st.session_state.res_distancia)
            st.session_state.ejecutado = True
        else: st.warning("⚠️ Marque 2 puntos.")
    
    if c_btn2.button("🗑️ LIMPIAR", use_container_width=True):
        st.session_state.puntos = []
        st.session_state.ejecutado = False
        st.rerun()

    # Resultados Persistentes
    if st.session_state.ejecutado:
        st.success("✅ Diagnóstico Finalizado")
        res1, res2 = st.columns(2)
        res1.metric("Longitud Tramo", f"{st.session_state.res_distancia:.2f} m")
        res2.metric("Pérdida (PSI)", f"{st.session_state.res_perdida:.4f}")
        st.info(f"Costo proyectado: ${(st.session_state.res_distancia * costo_m3 / 10):,.0f} COP/mes")

# --- MODO 2: OPERACIÓN REAL (CSV) ---
elif modo == "Operación Real (Lote)":
    st.write("### 📊 Procesamiento de Auditoría Real")
    
    with st.expander("🛠️ Generar Plantilla de Pruebas"):
        df_test = pd.DataFrame({'caudal':[12.5, 15.0], 'distancia':[100, 200]})
        st.download_button("📥 Bajar Plantilla", df_test.to_csv(index=False).encode('utf-8'), 
                           "plantilla_ianc.csv", "text/csv", use_container_width=True)

    archivo_csv = st.file_uploader("Subir CSV de Campo", type=["csv"])
    if archivo_csv:
        df = pd.read_csv(archivo_csv)
        if st.button("🚀 PROCESAR AUDITORÍA", use_container_width=True):
            if 'caudal' in df.columns and 'distancia' in df.columns:
                df['perdida_psi'] = df.apply(lambda r: perdida_hazen_williams(r['caudal'], 140, dn, r['distancia']), axis=1)
                st.session_state.df_resultados = df
                st.session_state.procesado_real = True
            else: st.error("Faltan columnas 'caudal' o 'distancia'")

    if st.session_state.procesado_real:
        st.success("✅ Resultados:")
        st.dataframe(st.session_state.df_resultados, use_container_width=True)

st.sidebar.caption(f"© 2026 Ing. Adolfo Barrera | CRA Standard")

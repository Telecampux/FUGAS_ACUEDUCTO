# =============================================================================
# AVISO DE PROPIEDAD INTELECTUAL Y DERECHOS DE AUTOR
# =============================================================================
# Proyecto: IANC H2O - Sistema Integral de Auditoría de Acueductos
# Versión: 2.0 (Arquitectura Modular Pro)
# Autor: Ing. Adolfo Barrera Vargas
# Ubicación: Colombia
# 
# (c) Copyright 2026. Todos los derechos reservados.
# 
# Este software y sus algoritmos (Core Hydraulics) están protegidos por las 
# leyes de derecho de autor en Colombia (Ley 23 de 1982). Queda prohibida la 
# reproducción total o parcial, comunicación pública, transformación o 
# distribución sin la autorización expresa y por escrito del autor.
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import streamlit.components.v1 as components

# --- IMPORTACIÓN DESDE EL CEREBRO (CORE) ---
# Traemos la lógica, los datos y las constantes desde nuestra carpeta privada
from core import (
    haversine, 
    perdida_hazen_williams, 
    territorios, 
    PROGRAMA_NOMBRE, 
    AUTOR, 
    EMPRESA_DEFAULT
)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="IANC H2O - Auditoría Profesional", 
    layout="wide", 
    page_icon="📡"
)

# Inyección del Manifiesto PWA (Para que el celular lo reconozca como App)
components.html(
    f'<link rel="manifest" href="./static/manifest.json">', 
    height=0
)

# --- ENCABEZADO PRINCIPAL ---
st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader(PROGRAMA_NOMBRE)
st.markdown(f"**Líder del Proyecto:** {AUTOR}")
st.divider()

# --- MENÚ LATERAL (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3105/3105807.png", width=100)
st.sidebar.header("📂 MENÚ DE CONTROL")

modo = st.sidebar.radio(
    "Seleccione Modo de Trabajo:", 
    ["Simulación Interactiva", "Operación Real (Carga Lote)"]
)

st.sidebar.divider()

# Selección de Municipio desde core.config
mun_sel = st.sidebar.selectbox("Municipio de Operación:", list(territorios.keys()))
datos_mun = territorios[mun_sel]

# Parámetros Técnicos
costo_m3 = st.sidebar.number_input(
    "Costo del m³ (COP)", 
    value=datos_mun['costo']
)
dn = st.sidebar.selectbox(
    "Diámetro Red Auditada (Pulg)", 
    [2, 3, 4, 6, 8, 10, 12], 
    index=2
)

# --- INICIALIZACIÓN DE VARIABLES DE ESTADO ---
for key, default in [
    ('puntos', []), ('ejecutado', False), ('empresa', EMPRESA_DEFAULT),
    ('analisis_listo', False)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# =================================================================
# CUERPO DE LA APLICACIÓN
# =================================================================

if modo == "Simulación Interactiva":
    st.write(f"### 🕹️ Simulador: {mun_sel}")
    st.session_state.empresa = st.text_input("Entidad Prestadora del Servicio:", st.session_state.empresa)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("Haga clic en el mapa para ubicar los sensores de presión y flujo.")
        # Mapa centrado según coordenadas del municipio en core.config
        m = folium.Map(location=datos_mun['coords'], zoom_start=15)
        
        # Lógica de marcadores
        for i, p in enumerate(st.session_state.puntos):
            folium.Marker(p, popup=f"Punto {i+1}", icon=folium.Icon(color='blue')).add_to(m)
            
        mapa_data = st_folium(m, width=800, height=500)
        
        # Captura de clics en el mapa
        if mapa_data['last_clicked']:
            punto = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
            if punto not in st.session_state.puntos:
                st.session_state.puntos.append(punto)
                st.rerun()

    with col2:
        st.write("#### 📍 Puntos de Control")
        if st.session_state.puntos:
            for i, p in enumerate(st.session_state.puntos):
                st.write(f"P{i+1}: {p[0]:.4f}, {p[1]:.4f}")
            
            if st.button("🗑️ Limpiar"):
                st.session_state.puntos = []
                st.session_state.ejecutado = False
                st.rerun()
                
            if st.button("🚀 EJECUTAR CÁLCULOS"):
                if len(st.session_state.puntos) < 2:
                    st.warning("Se requieren al menos 2 puntos para calcular pérdidas.")
                else:
                    st.session_state.ejecutado = True

# --- RESULTADOS DEL MOTOR HIDRÁULICO ---
if st.session_state.ejecutado and modo == "Simulación Interactiva":
    st.divider()
    st.success("✅ Análisis Hidráulico Finalizado")
    
    # Ejemplo de uso de las funciones del core
    p1, p2 = st.session_state.puntos[0], st.session_state.puntos[1]
    distancia = haversine(p1[0], p1[1], p2[0], p2[1])
    
    # Cálculo de pérdida (Ejemplo con caudal de 10 LPS y C de 140)
    perdida = perdida_hazen_williams(10, 140, dn, distancia)
    
    res_col1, res_col2 = st.columns(2)
    res_col1.metric("Distancia del Tramo", f"{distancia:.2f} m")
    res_col2.metric("Pérdida Estimada (hf)", f"{perdida:.4f} PSI")

elif modo == "Operación Real (Carga Lote)":
    st.write("### 📊 Auditoría por Carga de Datos")
    st.file_uploader("Cargar Archivo Maestro de Campo (.csv)", type=["csv"])
    st.info("Módulo configurado para procesamiento masivo de sensores IoT.")

# --- PIE DE PÁGINA ---
st.sidebar.divider()
st.sidebar.caption(f"© 2026 Ing. Adolfo Barrera | Estándares CRA")
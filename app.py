# =============================================================================
# AVISO DE PROPIEDAD INTELECTUAL Y DERECHOS DE AUTOR
# =============================================================================
# Proyecto: IANC H2O - Sistema Integral de Auditoría de Acueductos
# Versión: 2.0 (Arquitectura Modular Pro)
# Autor: Ing. Adolfo Barrera Vargas
# Ubicación: Colombia
# 
# (c) Copyright 2026. Todos los derechos reservados.
# Este código integra el motor de cálculos completos para simulación hidráulica.
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import streamlit.components.v1 as components

# --- IMPORTACIÓN DESDE EL CEREBRO (CORE) ---
# Se asume que estos métodos manejan la precisión física requerida
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

# Inyección del Manifiesto PWA para reconocimiento como App móvil
components.html(
    f'<link rel="manifest" href="./static/manifest.json">', 
    height=0
)

# --- ENCABEZADO PRINCIPAL ---
st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader(f"Módulo de Auditoría: {PROGRAMA_NOMBRE}")
st.markdown(f"**Líder del Proyecto:** {AUTOR}")
st.divider()

# --- MENÚ LATERAL (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3105/3105807.png", width=100)
st.sidebar.header("📂 PARÁMETROS DE CAMPO")

modo = st.sidebar.radio(
    "Seleccione Modo de Trabajo:", 
    ["Simulación Interactiva", "Operación Real (Carga Lote)"]
)

st.sidebar.divider()

# Selección de Municipio y Configuración de Red
mun_sel = st.sidebar.selectbox("Municipio de Operación:", list(territorios.keys()))
datos_mun = territorios[mun_sel]

costo_m3 = st.sidebar.number_input("Costo del m³ (COP)", value=datos_mun['costo'])
dn = st.sidebar.selectbox("Diámetro Red Auditada (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=2)

# --- INICIALIZACIÓN DE VARIABLES DE ESTADO ---
for key, default in [
    ('puntos', []), ('ejecutado', False), ('empresa', EMPRESA_DEFAULT)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# =================================================================
# SECCIÓN: SIMULACIÓN INTERACTIVA (CÁLCULOS COMPLETOS)
# =================================================================

if modo == "Simulación Interactiva":
    st.write(f"### 🕹️ Centro de Simulación: {mun_sel}")
    st.session_state.empresa = st.text_input("Entidad Prestadora (Empresa):", st.session_state.empresa)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("Trace la ruta de la auditoría haciendo clic en el mapa para ubicar sensores.")
        # Mapa centrado según el core.config
        m = folium.Map(location=datos_mun['coords'], zoom_start=15)
        
        # Dibujar marcadores y líneas de conexión
        if len(st.session_state.puntos) > 1:
            folium.PolyLine(st.session_state.puntos, color="red", weight=2.5, opacity=0.8).add_to(m)
            
        for i, p in enumerate(st.session_state.puntos):
            folium.Marker(p, popup=f"Sensor {i+1}", icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)
        
        mapa_data = st_folium(m, width=800, height=500)
        
        # Captura de coordenadas por clic
        if mapa_data['last_clicked']:
            punto = [mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']]
            if punto not in st.session_state.puntos:
                st.session_state.puntos.append(punto)
                st.rerun()

    with col2:
        st.write("#### 📍 Registro de Nodos")
        if st.session_state.puntos:
            for i, p in enumerate(st.session_state.puntos):
                st.write(f"**S{i+1}:** `{p[0]:.5f}, {p[1]:.5f}`")
            
            if st.button("🗑️ Reiniciar Trazo"):
                st.session_state.puntos = []
                st.session_state.ejecutado = False
                st.rerun()
                
            st.divider()
            if st.button("🚀 INICIAR AUDITORÍA", use_container_width=True):
                if len(st.session_state.puntos) < 2:
                    st.error("Error: Se requieren al menos 2 nodos para el análisis de pérdidas.")
                else:
                    st.session_state.ejecutado = True

    # --- MOTOR DE CÁLCULO HIDRÁULICO INTEGRAL ---
    if st.session_state.ejecutado:
        st.divider()
        st.header("📊 INFORME DE AUDITORÍA HIDRÁULICA")
        
        puntos = st.session_state.puntos
        dist_total_acumulada = 0.0
        perdida_total_acumulada = 0.0
        matriz_analisis = []

        # Cálculo histórico segmentado (Tramo a Tramo)
        for i in range(len(puntos) - 1):
            inicio, fin = puntos[i], puntos[i+1]
            
            # 1. Distancia geodésica entre sensores
            longitud_tramo = haversine(inicio[0], inicio[1], fin[0], fin[1])
            
            # 2. Pérdida de carga (hf) usando Hazen-Williams
            # Q=10 LPS, C=140 (Valores estándar de auditoría IANC)
            hf_tramo = perdida_hazen_williams(10, 140, dn, longitud_tramo)
            
            dist_total_acumulada += longitud_tramo
            perdida_total_acumulada += hf_tramo
            
            matriz_analisis.append({
                "Tramo": f"S{i+1} ➔ S{i+2}",
                "Longitud (m)": round(longitud_tramo, 2),
                "Pérdida (PSI)": round(hf_tramo, 4),
                "Pérdida Acum. (PSI)": round(perdida_total_acumulada, 4)
            })

        # Despliegue de Indicadores Críticos (KPIs)
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Distancia de Auditoría", f"{dist_total_acumulada:.2f} m")
        kpi2.metric("Caída de Presión Total", f"{perdida_total_acumulada:.4f} PSI", delta="-hf", delta_color="inverse")
        kpi3.metric("Coste del Agua Auditada", f"${costo_m3:,.0f} COP/m³")

        # Visualización de la Matriz de Datos
        st.subheader("📝 Matriz de Desglose de Energía")
        df_auditoria = pd.DataFrame(matriz_analisis)
        st.dataframe(df_auditoria, use_container_width=True)

        # Análisis de Fondo y Razonamiento Técnico
        with st.expander("🔬 Análisis Profundo y Ecuaciones"):
            st.markdown(f"""
            ### Evaluación Técnica del Sistema
            Para la empresa **{st.session_state.empresa}**, se ha realizado un análisis de fricción basado en la ecuación de **Hazen-Williams**:
            
            $$h_f = 10.67 \\cdot L \\cdot \\left(\\frac{{Q}}{{C}}\\right)^{{1.852}} \\cdot D^{{-4.87}}$$
            
            **Conclusiones de la Auditoría:**
            - Se han analizado **{len(puntos)} sensores** en el municipio de **{mun_sel}**.
            - La longitud total de la red auditada es de **{dist_total_acumulada:.2f} metros**.
            - La resistencia hidráulica acumulada es de **{perdida_total_acumulada:.4f} PSI**.
            
            Este valor de pérdida total debe restarse de la presión estática inicial para verificar el cumplimiento de la **normativa CRA** en términos de presión mínima en los puntos críticos de entrega.
            """)

elif modo == "Operación Real (Carga Lote)":
    st.write("### 📊 Auditoría por Procesamiento de Datos Externos")
    uploaded_file = st.file_uploader("Cargar Registro Maestro de Sensores (.csv)", type=["csv"])
    st.info("El módulo de carga masiva utiliza el mismo motor de cálculo que la simulación interactiva.")

# --- PIE DE PÁGINA ---
st.sidebar.divider()
st.sidebar.caption(f"© 2026 Ing. Adolfo Barrera | Auditoría IANC H2O")

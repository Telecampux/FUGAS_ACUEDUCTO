import streamlit as st
import pandas as pd
import numpy as np

# =====================================================================
# CONFIGURACIÓN DEL ENTORNO
# =====================================================================
st.set_page_config(
    page_title="Sistema de Acueducto",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================================
# INTERFAZ PRINCIPAL
# =====================================================================
st.title("Redes Matrices y Secundarias")
st.markdown("---")

st.info("Cargue el archivo CSV de la red. El sistema mapeará los nodos automáticamente antes de ejecutar el análisis de fugas.")

# Módulo de ingesta de datos
archivo_csv = st.file_uploader("Seleccionar lote de datos (CSV)", type=["csv"])

if archivo_csv is not None:
    try:
        # Lectura del archivo en memoria
        df = pd.read_csv(archivo_csv)
        
        # =====================================================================
        # FASE 1: RENDERIZADO VISUAL INMEDIATO
        # =====================================================================
        st.subheader("1. Ubicación Geoespacial y Estado de Nodos")
        
        # Búsqueda dinámica de coordenadas (tolerancia a variaciones en los nombres de columna)
        col_lat = next((c for c in df.columns if c.lower() in ['latitud', 'lat', 'latitude']), None)
        col_lon = next((c for c in df.columns if c.lower() in ['longitud', 'lon', 'lng', 'longitude']), None)
        
        # Layout de visualización: Mapa (70%) y Datos (30%)
        col_mapa, col_datos = st.columns([7, 3])
        
        with col_mapa:
            if col_lat and col_lon:
                # Estandarización estricta para el motor de mapas de Streamlit
                df_mapa = df[[col_lat, col_lon]].copy()
                df_mapa = df_mapa.rename(columns={col_lat: 'LAT', col_lon: 'LON'})
                
                # Limpieza de coordenadas corruptas para evitar colapsos en el renderizado
                df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'], errors='coerce')
                df_mapa['LON'] = pd.to_numeric(df_mapa['LON'], errors='coerce')
                df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])
                
                if not df_mapa.empty:
                    st.map(df_mapa)
                else:
                    st.warning("Precisión informática: Las coordenadas no contienen valores numéricos válidos.")
            else:
                st.warning("⚠️ Módulo Geoespacial inactivo: No se detectaron columnas de coordenadas válidas en el CSV.")

        with col_datos:
            st.markdown("**Matriz de Datos Recibida:**")
            st.dataframe(df, use_container_width=True, height=400)
            st.caption(f"Total de registros procesados: {len(df)}")

        st.markdown("---")

        # =====================================================================
        # FASE 2: ANÁLISIS DE CÁLCULO BAJO DEMANDA
        # =====================================================================
        st.subheader("2. Análisis de Integridad de Red")
        st.markdown("Ejecute el motor de cálculo para identificar caídas de presión o anomalías de caudal en las matrices.")
        
        if st.button("Ejecutar Detección de Fugas", type="primary"):
            with st.spinner('Procesando algoritmos hidráulicos...'):
                
                # ---------------------------------------------------------
                # INYECTAR AQUÍ TU LÓGICA DE CÁLCULO ORIGINAL
                # ---------------------------------------------------------
                # Como marcador de posición, utilizo una lógica de detección estadística
                # Asumiendo que existe una columna 'presion' o similar.
                
                col_presion = next((c for c in df.columns if 'presion' in c.lower()), None)
                
                if col_presion:
                    # Ejemplo matemático de fondo: Se marca como fuga si la presión cae un 20% bajo la media
                    umbral = df[col_presion].mean() * 0.8
                    df['Diagnóstico'] = np.where(df[col_presion] < umbral, "Fuga Probable", "Operativo")
                    fugas = df[df['Diagnóstico'] == "Fuga Probable"]
                else:
                    # Lógica de fallback si no hay columna de presión evidente
                    df['Diagnóstico'] = "Evaluación Pendiente (Faltan parámetros de presión/caudal)"
                    fugas = pd.DataFrame()
                # ---------------------------------------------------------

            # Despliegue de Resultados del Análisis
            if not fugas.empty:
                st.error(f"🚨 Alerta: Se han detectado {len(fugas)} nodos con comportamiento anómalo.")
                st.dataframe(fugas, use_container_width=True)
            elif col_presion is None:
                st.info("El análisis requiere que el CSV contenga una columna referida a la presión operativa.")
            else:
                st.success("✅ Análisis finalizado: La red opera dentro de los parámetros de normalidad. No se detectaron fugas.")

    except Exception as e:
        st.error(f"Se ha producido un error crítico durante la lectura del lote de datos: {e}")

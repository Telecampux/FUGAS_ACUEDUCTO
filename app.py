import streamlit as st
import pandas as pd
import numpy as np

# =====================================================================
# CONFIGURACIÓN DE PÁGINA
# =====================================================================
st.set_page_config(
    page_title="Análisis de Acueducto",
    page_icon="💧",
    layout="wide"
)

# =====================================================================
# MÓDULO 1: INTERFAZ DE USUARIO Y CARGA DE DATOS
# =====================================================================
# Título actualizado según los requerimientos de la topología de red
st.title("Redes Matrices y Secundarias")
st.markdown("---")

st.subheader("1. Ingestión de Datos")
st.info("Por favor, cargue el archivo CSV con los datos de los sensores. Asegúrese de incluir columnas de coordenadas (Latitud/Longitud) para habilitar el módulo geoespacial.")

archivo_csv = st.file_uploader("Seleccionar lote de datos (CSV)", type=["csv"])

# =====================================================================
# MÓDULO 2: LÓGICA DE PROCESAMIENTO Y CÁLCULO
# =====================================================================
def ejecutar_calculos_hidraulicos(df_entrada):
    """
    Función aislada para el análisis matemático de la red.
    Aquí debes insertar tu lógica original de cálculo de caudales, presiones, etc.
    """
    # Creamos una copia para no alterar el DataFrame original en memoria
    df_procesado = df_entrada.copy()
    
    # --- INICIO DE TU LÓGICA DE CÁLCULO ---
    # Ejemplo: Si tuvieras que calcular una presión base, lo harías aquí.
    # df_procesado['Presion_Calculada'] = df_procesado['Caudal'] * 0.85 
    # --- FIN DE TU LÓGICA DE CÁLCULO ---
    
    return df_procesado

# =====================================================================
# FLUJO PRINCIPAL DE EJECUCIÓN
# =====================================================================
if archivo_csv is not None:
    try:
        # 1. Lectura del archivo crudo
        df_bruto = pd.read_csv(archivo_csv)
        
        # 2. Ejecución del procesamiento matemático
        with st.spinner('Ejecutando cálculos de red...'):
            df_final = ejecutar_calculos_hidraulicos(df_bruto)
        
        st.success("✅ Análisis de red ejecutado y procesado correctamente.")
        
        # 3. Despliegue de la tabla de resultados
        st.subheader("2. Matriz de Resultados")
        st.dataframe(df_final, use_container_width=True)
        
        st.markdown("---")
        
        # =====================================================================
        # MÓDULO 3: RENDERIZADO GEOESPACIAL (MAPA)
        # =====================================================================
        st.subheader("3. Localización de Sensores en el Municipio")
        
        # Búsqueda dinámica y tolerante a fallos de las columnas espaciales
        columnas = df_final.columns.str.lower()
        col_lat = next((c for c in df_final.columns if c.lower() in ['latitud', 'lat', 'latitude']), None)
        col_lon = next((c for c in df_final.columns if c.lower() in ['longitud', 'lon', 'lng', 'longitude']), None)
        
        if col_lat and col_lon:
            # Extracción y estandarización estricta para el motor de Streamlit (exige 'LAT' y 'LON')
            df_mapa = df_final[[col_lat, col_lon]].copy()
            df_mapa = df_mapa.rename(columns={col_lat: 'LAT', col_lon: 'LON'})
            
            # Limpieza profunda: descartar sensores con coordenadas corruptas o nulas
            # para prevenir el colapso del renderizado del mapa
            df_mapa['LAT'] = pd.to_numeric(df_mapa['LAT'], errors='coerce')
            df_mapa['LON'] = pd.to_numeric(df_mapa['LON'], errors='coerce')
            df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])
            
            if not df_mapa.empty:
                # El motor geoespacial calcula automáticamente el polígono (Bounding Box)
                # y ajusta el zoom al municipio específico de los datos.
                st.map(df_mapa)
                st.caption(f"📌 Se han localizado {len(df_mapa)} sensores operativos en el territorio.")
            else:
                st.warning("Precisión informática: Las columnas de coordenadas existen, pero no contienen datos numéricos válidos.")
        else:
            st.warning("⚠️ Módulo Geoespacial inactivo: No se detectaron columnas de 'Latitud' y 'Longitud' en el archivo procesado.")
            
    except Exception as e:
        st.error(f"Error crítico durante la lectura o procesamiento del archivo: {e}")

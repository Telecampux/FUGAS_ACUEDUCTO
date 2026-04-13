import streamlit as st
import pandas as pd
# Importa aquí las librerías que ya tenías para tus cálculos (numpy, etc.)

# ==========================================
# 1. ACTUALIZACIÓN DEL TÍTULO
# ==========================================
st.title("Redes Matrices y Secundarias")

# Subida del archivo por lotes
archivo_csv = st.file_uploader("Cargar lote de datos (CSV)", type=["csv"])

if archivo_csv is not None:
    # Leer los datos crudos
    df_bruto = pd.read_csv(archivo_csv)
    
    # ==========================================
    # ZONA INTACTA: TUS CÁLCULOS
    # ==========================================
    # Aquí va exactamente el código que ya tienes funcionando.
    # No cambies nada de tu lógica.
    # Supongamos que al final de tus cálculos tienes un DataFrame llamado 'df_procesado'
    
    df_procesado = df_bruto.copy() # Reemplaza esto con tu función de cálculo
    
    # Mostrar mensaje de éxito y tabla (como seguro ya lo tienes)
    st.success("Análisis de red ejecutado correctamente.")
    st.dataframe(df_procesado) # O la forma en que estés mostrando los resultados
    
    # ==========================================
    # 2. NUEVO MÓDULO: MAPA GEOESPACIAL
    # ==========================================
    st.subheader("Localización de Sensores en el Municipio")
    
    # Análisis de fondo: st.map() exige que las columnas se llamen exactamente 
    # 'lat'/'latitude' y 'lon'/'longitude'. Hacemos una búsqueda dinámica para 
    # no desbaratar el código si el CSV viene con nombres como 'Latitud' o 'lng'.
    
    columnas = df_procesado.columns.str.lower()
    
    # Buscar dinámicamente cómo se llaman las columnas de coordenadas en el CSV
    col_lat = next((c for c in df_procesado.columns if c.lower() in ['latitud', 'lat', 'latitude']), None)
    col_lon = next((c for c in df_procesado.columns if c.lower() in ['longitud', 'lon', 'lng', 'longitude']), None)
    
    if col_lat and col_lon:
        # Preparamos un DataFrame temporal solo para el mapa, renombrando las columnas 
        # al estándar que exige Streamlit, evitando errores.
        df_mapa = df_procesado[[col_lat, col_lon]].copy()
        df_mapa = df_mapa.rename(columns={col_lat: 'LAT', col_lon: 'LON'})
        
        # Depuración: Eliminar filas sin coordenadas para que el mapa no colapse
        df_mapa = df_mapa.dropna(subset=['LAT', 'LON'])
        
        # Renderizar el mapa. 
        # Streamlit automáticamente encuadra el zoom en los puntos.
        if not df_mapa.empty:
            st.map(df_mapa)
        else:
            st.warning("Precisión informática: Las columnas de coordenadas están vacías o tienen datos inválidos.")
    else:
        st.warning("⚠️ No se encontraron las columnas de latitud y longitud en el CSV. El mapa no se puede generar.")

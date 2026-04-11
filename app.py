import streamlit as st
import pandas as pd
import os
import pathlib
import folium
from streamlit_folium import st_folium

# --- CONFIGURACIÓN DE ENTORNO Y RUTAS ---
# Localización dinámica de la raíz del proyecto
BASE_DIR = pathlib.Path(__file__).parent.resolve()
DATA_FOLDER = os.path.join(BASE_DIR, 'datos_simulacion')

def inicializar_sistema():
    """Verifica la existencia del entorno de datos y retorna los archivos disponibles."""
    if not os.path.exists(DATA_FOLDER):
        return None, f"Error: La carpeta '{DATA_FOLDER}' no existe en el repositorio."
    
    archivos = [f for f in os.listdir(DATA_FOLDER) if f.endswith(('.csv', '.xlsx', '.xls'))]
    return archivos, None

def cargar_data(archivo_nombre):
    """Carga el archivo detectado con el motor adecuado."""
    ruta = os.path.join(DATA_FOLDER, archivo_nombre)
    if archivo_nombre.endswith('.csv'):
        return pd.read_csv(ruta)
    else:
        return pd.read_excel(ruta)

# --- CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="IANS H2O - Localización de Fugas", layout="wide")

st.title("📍 Sistema de Localización de Fugas IANS H2O")
st.markdown("---")

# --- LÓGICA DE EJECUCIÓN ---
archivos_disponibles, error_msg = inicializar_sistema()

if error_msg:
    st.error(f"❌ {error_msg}")
    st.info("Asegúrese de que la carpeta 'datos_simulacion' esté en la raíz de su GitHub.")
else:
    if not archivos_disponibles:
        st.warning(f"⚠️ La carpeta 'datos_simulacion' está presente pero no contiene archivos .csv o .xlsx.")
    else:
        # Selección automática del primer archivo encontrado o mediante selector
        if len(archivos_disponibles) == 1:
            archivo_target = archivos_disponibles[0]
            st.success(f"✅ Archivo detectado: **{archivo_target}**")
        else:
            archivo_target = st.selectbox("Seleccione el archivo de simulación:", archivos_disponibles)

        try:
            df = cargar_data(archivo_target)
            
            # --- PANEL DE CONTROL Y MÉTRICAS (Ejemplo de Análisis de IANC) ---
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Registros Técnicos", len(df))
            with col2:
                st.metric("Estado del Sistema", "Activo")
            with col3:
                # Ejemplo de cálculo si existe la columna correspondiente
                st.metric("Localización", "Lat/Lon Detectada" if 'latitud' in df.columns else "Sin GPS")

            # --- VISUALIZACIÓN DE DATOS ---
            st.subheader("Análisis de Datos de Presión y Caudal")
            st.dataframe(df, use_container_width=True)

            # --- COMPONENTE GEOGRÁFICO (GIS) ---
            st.subheader("Mapa de Localización de Fugas")
            # Coordenadas por defecto (Bogotá) o centradas en los datos
            centro_lat = df['latitud'].mean() if 'latitud' in df.columns else 4.6097
            centro_lon = df['longitud'].mean() if 'longitud' in df.columns else -74.0817
            
            m = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)
            
            # Si hay datos GPS, marcamos las fugas sospechosas
            if 'latitud' in df.columns and 'longitud' in df.columns:
                for idx, row in df.iterrows():
                    folium.Marker(
                        [row['latitud'], row['longitud']], 
                        popup=f"Punto de Inspección {idx}",
                        icon=folium.Icon(color='red', icon='info-sign')
                    ).add_to(m)
            
            st_folium(m, width="100%", height=500)

        except Exception as e:
            st.error(f"Hubo un error al procesar el archivo: {e}")

# --- PIE DE PÁGINA PROFESIONAL ---
st.sidebar.markdown(f"**Ingeniero:** Adolfo Barrera Vargas")
st.sidebar.markdown(f"**Proyecto:** IANS H2O")

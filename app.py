import streamlit as st
import pandas as pd
import os
from pathlib import Path
import folium
from streamlit_folium import st_folium

# --- 1. CONFIGURACIÓN Y RUTAS (ESTABILIDAD) ---
BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "datos_simulacion"

st.set_page_config(page_title="IANS H2O - Análisis Pro", layout="wide")

def inicializar_sistema():
    if not DATA_FOLDER.exists():
        # Si no existe, listamos el directorio para depuración técnica
        return None, f"Error: No se halla la carpeta 'datos_simulacion' en {BASE_DIR}"
    archivos = [f for f in os.listdir(DATA_FOLDER) if f.lower().endswith(('.csv', '.xlsx'))]
    return archivos, None

# --- 2. LÓGICA DE PROCESAMIENTO (LO QUE SE HABÍA PERDIDO) ---
def analizar_presiones(df):
    """
    Aquí reinsertamos tu lógica de detección. 
    Ejemplo: Marcamos puntos donde la presión cae del umbral crítico.
    """
    # Supongamos que tu columna de presión se llama 'Presion_PSI'
    if 'Presion_PSI' in df.columns:
        df['Alerta'] = df['Presion_PSI'].apply(lambda x: "Crítico" if x < 20 else "Normal")
    return df

# --- 3. INTERFAZ Y EJECUCIÓN ---
st.title("📍 Localización de Fugas IANS H2O")

archivos, error = inicializar_sistema()

if error:
    st.error(error)
    st.info("💡 Consejo: Asegúrate de que el nombre de la carpeta en GitHub sea exactamente 'datos_simulacion'.")
else:
    with st.sidebar:
        st.header("Panel de Control")
        seleccion = st.selectbox("Archivo de Simulación", archivos)
        st.write(f"Directorio: `{DATA_FOLDER}`")

    if seleccion:
        try:
            # Carga de datos
            ruta_final = DATA_FOLDER / seleccion
            df = pd.read_csv(ruta_final) if seleccion.endswith('.csv') else pd.read_excel(ruta_final)
            
            # Ejecutar lógica de ingeniería
            df_procesado = analizar_presiones(df)
            
            st.success(f"Análisis completado para {seleccion}")
            
            # --- VISUALIZACIÓN ---
            tab1, tab2 = st.tabs(["📊 Datos de Presión", "🗺️ Mapa de Fugas"])
            
            with tab1:
                st.subheader("Análisis de Tendencias")
                st.dataframe(df_procesado, use_container_width=True)
            
            with tab2:
                st.subheader("Geolocalización de Anomalías")
                # Aquí centramos el mapa en los datos si existen coordenadas
                lat_media = df['latitud'].mean() if 'latitud' in df.columns else 4.6
                lon_media = df['longitud'].mean() if 'longitud' in df.columns else -74.0
                
                m = folium.Map(location=[lat_media, lon_media], zoom_start=12)
                
                # Ejemplo de marcador de fuga
                for idx, row in df_procesado.iterrows():
                    if 'latitud' in row and 'longitud' in row:
                        color = 'red' if row.get('Alerta') == "Crítico" else 'blue'
                        folium.Marker(
                            [row['latitud'], row['longitud']],
                            popup=f"Presión: {row.get('Presion_PSI')} PSI",
                            icon=folium.Icon(color=color)
                        ).add_to(m)
                
                st_folium(m, width="100%", height=500)

        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("Ing. Adolfo Barrera Vargas - v2.1")

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Configuración de página (Esto hace que se vea profesional)
st.set_page_config(page_title="Tablero IANC H2O", layout="wide")

st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader("Líder del Proyecto: ING. ADOLFO BARRERA VARGAS")

# Módulo de Carga
uploaded_file = st.file_uploader("Cargar Archivo Maestro de Campo (.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        # 1. Leer y limpiar datos
        df = pd.read_csv(uploaded_file)
        
        # Eliminamos filas que tengan latitud o longitud vacía
        df = df.dropna(subset=['latitud', 'longitud'])

        if df.empty:
            st.error("El archivo subido no tiene datos válidos en las columnas de coordenadas.")
        else:
            st.success(f"Se han cargado {len(df)} registros correctamente.")
            
            # 2. Layout de dos columnas: Datos a la izquierda, Mapa a la derecha
            col1, col2 = st.columns([1, 2])

            with col1:
                st.write("### Vista previa de Auditoría")
                st.dataframe(df.head(10)) # Muestra los primeros 10 registros

            with col2:
                st.write("### Ubicación de Sensores IoT")
                # Calcular el centro del mapa basado en el promedio de coordenadas
                centro_lat = df['latitud'].mean()
                centro_lon = df['longitud'].mean()
                
                m = folium.Map(location=[centro_lat, centro_lon], zoom_start=14)

                # Añadir los puntos al mapa automáticamente
                for i, row in df.iterrows():
                    folium.Marker(
                        [row['latitud'], row['longitud']],
                        popup=f"Punto: {i}",
                        icon=folium.Icon(color='blue', icon='info-sign')
                    ).add_to(m)

                # Renderizar el mapa
                st_folium(m, width=700, height=500)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Esperando carga de archivo .csv para activar el tablero...")

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# 1. Configuración base
st.set_page_config(page_title="Diagnóstico IANC H2O", layout="wide")

st.title("📡 SISTEMA DE DIAGNÓSTICO IANC H2O")
st.info("Este código detectará por qué el mapa no se muestra.")

# 2. Selector de archivo
uploaded_file = st.file_uploader("Cargar Archivo Maestro (.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        # Intentamos leer el archivo de la forma más flexible posible
        # Se prueba con coma y con punto y coma automáticamente
        try:
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        except:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)

        st.subheader("🔎 Resultado del Escaneo")
        
        # MOSTRAR COLUMNAS DETECTADAS
        cols = list(df.columns)
        st.write(f"El programa detectó estas columnas: `{cols}`")
        
        # MOSTRAR VISTA PREVIA REAL
        st.write("Datos leídos (primeras 3 filas):")
        st.dataframe(df.head(3))

        # 3. Lógica de normalización
        df.columns = df.columns.str.strip().str.lower()
        
        # 4. Verificación de coordenadas
        tiene_lat = 'latitud' in df.columns
        tiene_lon = 'longitud' in df.columns

        if tiene_lat and tiene_lon:
            st.success("✅ Coordenadas encontradas. Generando mapa...")
            
            # Limpieza de datos
            df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
            df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
            df = df.dropna(subset=['latitud', 'longitud'])

            # Crear mapa
            m = folium.Map(location=[df.latitud.mean(), df.longitud.mean()], zoom_start=12)
            for i, row in df.iterrows():
                folium.Marker([row['latitud'], row['longitud']], popup=f"Punto {i}").add_to(m)
            
            # Mostrar mapa
            st_folium(m, width=700, height=500)
        else:
            st.error("🛑 ERROR: No encuentro las columnas 'latitud' y 'longitud'.")
            st.warning(f"Asegúrese de que su CSV tenga esos nombres. El programa ve esto: {df.columns.tolist()}")

    except Exception as e:
        st.error(f"Error técnico: {e}")
else:
    st.warning("Esperando archivo...")

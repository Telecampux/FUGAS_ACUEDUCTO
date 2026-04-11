import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Tablero IANC H2O", layout="wide")

st.title("📡 TABLERO DE CONTROL IANC H2O")
st.subheader("Líder del Proyecto: ING. ADOLFO BARRERA VARGAS")

uploaded_file = st.file_uploader("Cargar Archivo Maestro de Campo (.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        # --- SOLUCIÓN DE FONDO: Autodetectar si es coma o punto y coma ---
        # Leemos las primeras líneas para saber qué usa el archivo
        content = uploaded_file.getvalue().decode('utf-8')
        separador = ';' if content.count(';') > content.count(',') else ','
        
        # Volvemos al inicio del archivo y leemos con el separador correcto
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=separador)
        
        # Limpieza de nombres de columnas
        df.columns = df.columns.str.strip().str.lower()

        # --- DIAGNÓSTICO VISUAL ---
        st.info(f"Sistema: Leyendo archivo con separador '{separador}'")
        
        if df.empty:
            st.error("El archivo se leyó pero no contiene datos.")
        else:
            # Verificamos si existen las columnas necesarias
            columnas_reales = list(df.columns)
            
            if 'latitud' in columnas_reales and 'longitud' in columnas_reales:
                df = df.dropna(subset=['latitud', 'longitud'])
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.write("### 📊 Datos de Auditoría")
                    st.dataframe(df)
                with col2:
                    st.write("### 🗺️ Mapa de Sensores")
                    centro_lat = pd.to_numeric(df['latitud']).mean()
                    centro_lon = pd.to_numeric(df['longitud']).mean()
                    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)
                    for i, row in df.iterrows():
                        folium.Marker([row['latitud'], row['longitud']], popup=f"Punto {i}").add_to(m)
                    st_folium(m, width="100%", height=450)
            else:
                st.error("🛑 COLUMNAS NO ENCONTRADAS")
                st.write("El archivo tiene estas columnas:", columnas_reales)
                st.write("Pero el programa necesita: **latitud** y **longitud**")
                # Mostramos lo que el programa "ve" para entender el error
                st.write("Muestra de datos crudos detectados:", df.head(3))

    except Exception as e:
        st.error(f"Error al procesar: {e}")

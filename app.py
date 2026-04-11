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
        # Intentamos leer el archivo
        df = pd.read_csv(uploaded_file)
        
        # 1. Advertencia de limpieza de nombres
        df.columns = df.columns.str.strip().str.lower()
        
        # 2. VALIDACIÓN CRÍTICA: ¿Existen las columnas?
        tiene_lat = 'latitud' in df.columns
        tiene_lon = 'longitud' in df.columns

        if not tiene_lat or not tiene_lon:
            st.error("🛑 ERROR DE FORMATO DETECTADO")
            st.warning(f"El programa busca 'latitud' y 'longitud', pero encontró: {list(df.columns)}")
            st.info("💡 Por favor, renombre las columnas de su archivo CSV para que coincidan.")
        
        else:
            # 3. VALIDACIÓN DE DATOS VACÍOS
            antes = len(df)
            df = df.dropna(subset=['latitud', 'longitud'])
            despues = len(df)

            if despues == 0:
                st.error("❌ ARCHIVO VACÍO: Todas las filas tienen coordenadas nulas o mal escritas.")
            else:
                if antes > despues:
                    st.warning(f"⚠️ Se omitieron {antes - despues} filas por falta de coordenadas.")

                st.success(f"✅ Procesando {despues} sensores IoT.")

                # Visualización
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.write("### 📊 Datos de Auditoría")
                    st.dataframe(df)

                with col2:
                    st.write("### 🗺️ Ubicación Geográfica")
                    m = folium.Map(location=[df.latitud.mean(), df.longitud.mean()], zoom_start=13)
                    for i, row in df.iterrows():
                        folium.Marker([row['latitud'], row['longitud']], popup=f"ID: {i}").add_to(m)
                    st_folium(m, width="100%", height=450)

    except Exception as e:
        st.error(f"💥 Error inesperado al leer el archivo: {e}")
else:
    st.info("📥 Por favor, cargue el archivo .csv para iniciar la auditoría.")

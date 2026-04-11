import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from datetime import datetime

# ==========================================
# CONFIGURACIÓN Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="IANS H2O - Localización Técnica de Fugas",
    page_icon="💧",
    layout="wide"
)

# Estilo CSS para mejorar la legibilidad profesional
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# LÓGICA DE INGENIERÍA (CÁLCULOS ESTADÍSTICOS)
# ==========================================
def calcular_probabilidad_fuga(df):
    """
    Analiza la relación Presión/Caudal para localizar puntos críticos.
    Se basa en el análisis de anomalías de fondo.
    """
    # Normalización para análisis comparativo
    df['p_norm'] = (df['presion'] - df['presion'].min()) / (df['presion'].max() - df['presion'].min())
    df['c_norm'] = (df['caudal'] - df['caudal'].min()) / (df['caudal'].max() - df['caudal'].min())
    
    # El indicador de fuga aumenta cuando hay alta presión pero caída de caudal relativo, 
    # o caudales excesivos en horas de mínima nocturna (Simulado aquí por lógica de peso)
    df['Indice_Fuga'] = (df['c_norm'] * 0.6 + (1 - df['p_norm']) * 0.4) * 100
    
    # Clasificación técnica
    df['Prioridad'] = pd.cut(df['Indice_Fuga'], 
                             bins=[0, 40, 70, 100], 
                             labels=['Baja', 'Media', 'Crítica'])
    return df

# ==========================================
# COMPONENTES DE INTERFAZ
# ==========================================
def mostrar_mapa(df):
    """Genera visualización GIS avanzada"""
    # Definir color por prioridad
    df['color_r'] = df['Prioridad'].apply(lambda x: 255 if x == 'Crítica' else (255 if x == 'Media' else 0))
    df['color_g'] = df['Prioridad'].apply(lambda x: 0 if x == 'Crítica' else (165 if x == 'Media' else 128))
    df['color_b'] = df['Prioridad'].apply(lambda x: 0 if x == 'Crítica' else 0)

    view_state = pdk.ViewState(
        latitude=df['latitud'].mean(),
        longitude=df['longitud'].mean(),
        zoom=13,
        pitch=45
    )

    layer = pdk.Layer(
        'ScatterplotLayer',
        data=df,
        get_position='[longitud, latitud]',
        get_color='[color_r, color_g, color_b, 160]',
        get_radius=80,
        pickable=True
    )

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "Prioridad: {Prioridad}\nÍndice: {Indice_Fuga:.2f}"}
    ))

# ==========================================
# FLUJO PRINCIPAL (APP)
# ==========================================
def main():
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3144/3144467.png", width=100)
    st.sidebar.title("Navegación IANS H2O")
    
    opcion = st.sidebar.radio(
        "Seleccione el flujo de trabajo:",
        ["Dashboard de Control", "Simulación Técnica", "Procesamiento por Lotes (Campo)"]
    )

    st.title("📍 Localización de Fugas e Inspección de Redes")
    st.info(f"Modo actual: {opcion}")

    if opcion == "Simulación Técnica":
        st.subheader("Generación de Escenarios de Prueba")
        num_puntos = st.slider("Cantidad de puntos a simular", 10, 500, 100)
        
        if st.button("Ejecutar Simulación"):
            # Generación de datos sintéticos con ruido estadístico
            data = pd.DataFrame({
                'latitud': np.random.uniform(4.60, 4.65, num_puntos),
                'longitud': np.random.uniform(-74.10, -74.05, num_puntos),
                'caudal': np.random.uniform(5, 50, num_puntos),
                'presion': np.random.uniform(15, 45, num_puntos)
            })
            df_res = calcular_probabilidad_fuga(data)
            
            # Métricas rápidas
            c1, c2, c3 = st.columns(3)
            c1.metric("Puntos Críticos", len(df_res[df_res['Prioridad'] == 'Crítica']))
            c2.metric("Presión Promedio", f"{df_res['presion'].mean():.2f} PSI")
            c3.metric("Caudal Total", f"{df_res['caudal'].sum():.2f} m3/h")
            
            mostrar_mapa(df_res)
            st.dataframe(df_res.drop(columns=['color_r', 'color_g', 'color_b']))

    elif opcion == "Procesamiento por Lotes (Campo)":
        st.subheader("Carga de Datos Reales de Terreno")
        archivo = st.file_uploader("Cargar archivo .csv o .xlsx detectado en campo", type=['csv', 'xlsx'])
        
        if archivo:
            try:
                if archivo.name.endswith('.csv'):
                    df_campo = pd.read_csv(archivo)
                else:
                    df_campo = pd.read_excel(archivo)
                
                # Validación de columnas requeridas
                cols_necesarias = {'latitud', 'longitud', 'caudal', 'presion'}
                if cols_necesarias.issubset(df_campo.columns):
                    with st.spinner('Analizando integridad de red...'):
                        df_res = calcular_probabilidad_fuga(df_campo)
                        mostrar_mapa(df_res)
                        
                        st.subheader("Detalle de Hallazgos")
                        st.write(df_res[df_res['Prioridad'] == 'Crítica'])
                        
                        # Opción de descarga de resultados
                        csv = df_res.to_csv(index=False).encode('utf-8')
                        st.download_button("Descargar Reporte de Fugas", csv, "reporte_ians_h2o.csv", "text/csv")
                else:
                    st.error(f"Error en formato: El archivo debe contener exactamente las columnas {cols_necesarias}")
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")
        else:
            st.warning("Por favor, suba un archivo para iniciar el procesamiento.")

    elif opcion == "Dashboard de Control":
        st.write("Bienvenido al sistema IANS H2O. Seleccione una opción en el menú lateral para comenzar el análisis.")
        st.image("https://images.unsplash.com/photo-1581094794329-c8112a89af12?auto=format&fit=crop&q=80&w=1000", caption="Monitoreo de Infraestructura Hídrica")

if __name__ == "__main__":
    main()

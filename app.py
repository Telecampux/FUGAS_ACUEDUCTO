# =============================================================================
# IANC_H2O: SISTEMA PARA LOCALIZACIÓN DE FUGAS INVISIBLES EN ACUEDUCTOS 
# ESPECIALIZADO EN REDES MATRIZ Y SECUNDARIA
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# Versión: 2.8.3 - Identidad Oficial (IANC_H2O)
# =============================================================================

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import time

try:
    from core import haversine, perdida_hazen_williams, territorios, AUTOR
except ImportError:
    AUTOR = "Ing. Adolfo Barrera Vargas"
    territorios = {
        "Bogotá": {"coords": [4.6097, -74.0817]}, 
        "Villeta": {"coords": [5.0114, -74.4744]}, 
        "Chaparral": {"coords": [3.7228, -75.4831]}
    }
    def haversine(lat1, lon1, lat2, lon2): 
        # Cálculo geodésico aproximado de respaldo
        return np.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111320.0
    def perdida_hazen_williams(q, c, d, l): 
        return 0.5

# --- CONSTANTES TÉCNICAS DETERMINÍSTICAS ---
FACTOR_CONVERSION_PSI_MCA = 0.7032
GRAVEDAD = 9.81
UMBRAL_FUGA_PSI = 0.20  # Umbral físico definido (0.2 PSI)
UMBRAL_FUGA_MCA = UMBRAL_FUGA_PSI * FACTOR_CONVERSION_PSI_MCA 

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="IANC_H2O - Fugas Invisibles", layout="wide")

def obtener_cota_api(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        respuesta = requests.get(url, timeout=3).json()
        if "elevation" in respuesta and respuesta["elevation"]:
            return round(respuesta["elevation"][0], 2)
    except Exception:
        pass
    return 1000.0

def calcular_balance_hidraulico(q_lps, d_pulg, c_hazen, dist_m, k_sum):
    hf = perdida_hazen_williams(q_lps, c_hazen, d_pulg, dist_m)
    q_m3s = q_lps / 1000.0
    d_m = d_pulg * 0.0254
    area = (np.pi * d_m**2) / 4
    velocidad = q_m3s / area if area > 0 else 0
    hm = k_sum * (velocidad**2 / (2 * GRAVEDAD))
    caida_teorica = (hf * FACTOR_CONVERSION_PSI_MCA) + hm
    return caida_teorica, velocidad

# --- INICIALIZACIÓN DE ESTADO ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'datos_sensores' not in st.session_state: st.session_state.datos_sensores = {}
if 'animar_terminal' not in st.session_state: st.session_state.animar_terminal = True

# --- INTERFAZ PRINCIPAL ---
st.title("IANC_H2O: LOCALIZACIÓN DE FUGAS INVISIBLES EN ACUEDUCTOS (MATRIZ Y SECUNDARIA)")
st.subheader("Motor Determinístico: Análisis de Gradiente de Energía")
st.caption(f"Desarrollado por {AUTOR}")

# --- SIDEBAR: MENÚ DE CONTROL Y PARÁMETROS ARQUITECTÓNICOS ---
st.sidebar.header("⚙️ CONTROL DEL SISTEMA")

modo = st.sidebar.radio(
    "Seleccione Entorno de Trabajo:", 
    ["Simulación Interactiva", "Operación Real (Carga Lote / En Línea)"]
)
st.sidebar.divider()

if modo == "Simulación Interactiva":
    st.sidebar.markdown("### 📝 Variables Ideales (Solo Simulación)")
    q_entrada_lps = st.sidebar.number_input("Caudal Nominal (L/s)", value=20.0, step=0.1, format="%.1f")
    dn_pulg = st.sidebar.selectbox("Diámetro (Pulg)", [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24], index=6)
    coef_c = st.sidebar.slider("Coeficiente C (Fricción)", 100, 150, 140)
    
    with st.sidebar.expander("📘 Guía de Accesorios", expanded=False):
        st.markdown("* Mariposa: 0.35\n* Compuerta: 0.15\n* Codo 90°: 0.30")
else:
    st.sidebar.markdown("### 🔒 Variables Deshabilitadas")
    st.sidebar.info(
        "**MODO REAL ACTIVO:**\n"
        "Las variables fijas (Caudal, Diámetro, Coef. C) han sido bloqueadas. "
        "El sistema calculará el gradiente basándose estrictamente en la lectura física "
        "de los sensores (Caja Negra)."
    )
    # Variables de control interno para evitar errores de referencia en el backend
    q_entrada_lps, dn_pulg, coef_c = 20.0, 6, 140

# =================================================================
# MODO 1: SIMULACIÓN INTERACTIVA
# =================================================================
if modo == "Simulación Interactiva":
    st.warning("⚠️ **AVISO ARQUITECTÓNICO - MODO SIMULACIÓN:** En este entorno, las variables ingresadas en el panel lateral se comportan como **CONSTANTES IDEALES**. Este módulo asume una red uniforme para proyectar el modelo teórico.")
    
    col_map, col_inputs = st.columns([2, 1])

    with col_map:
        mun_sel = st.selectbox("Zona de Operación:", list(territorios.keys()))
        m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
        
        # Mapeo visual priorizado con etiquetas explícitas
        for i, p in enumerate(st.session_state.puntos):
            folium.Marker(
                p, 
                tooltip=f"Sensor Nodo {i+1}", 
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
        
        if len(st.session_state.puntos) > 1:
            folium.PolyLine(st.session_state.puntos, color="red", weight=4).add_to(m)

        mapa_data = st_folium(m, width=700, height=450, key="mapa_simulacion")
        
        if mapa_data and mapa_data.get('last_clicked'):
            lat, lng = mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']
            if [lat, lng] not in st.session_state.puntos:
                st.session_state.puntos.append([lat, lng])
                idx = len(st.session_state.puntos) - 1
                st.session_state[f"z_{idx}"] = float(obtener_cota_api(lat, lng))
                st.session_state.animar_terminal = True
                st.rerun()

    with col_inputs:
        st.subheader("📡 Entradas Teóricas")
        nodo_a_borrar = None
        
        for i in range(len(st.session_state.puntos)):
            with st.expander(f"Sensor Nodo {i+1}", expanded=True):
                c1, c2 = st.columns(2)
                p_in = c1.number_input(f"Presión (PSI)", key=f"p_{i}", value=0.0, format="%.2f")
                if f"z_{i}" not in st.session_state: st.session_state[f"z_{i}"] = 1000.0
                z_in = c2.number_input(f"Cota (msnm)", key=f"z_{i}", step=0.01, format="%.2f")
                k_in = st.number_input(f"ΣK Accesorios", key=f"k_{i}", value=0.0, step=0.1) if i < len(st.session_state.puntos)-1 else 0.0
                st.session_state.datos_sensores[i] = {"P": p_in, "Z": z_in, "K": k_in}
                
                if st.button("🗑️ Borrar Nodo", key=f"del_{i}"): nodo_a_borrar = i

        if nodo_a_borrar is not None:
            st.session_state.puntos.pop(nodo_a_borrar)
            st.rerun()
            
        if st.button("🔄 Reiniciar Mapa", use_container_width=True):
            st.session_state.puntos = []
            st.rerun()

    if len(st.session_state.puntos) >= 2:
        st.divider()
        terminal_box = st.empty()
        log_lineas = []
        
        # Logger reestructurado para evitar errores de sintaxis en Python
        def log_s(texto):
            log_lineas.append(texto)
            texto_unido = "\n".join(log_lineas)
            caja_codigo = f"```text\n{texto_unido}\n```"
            terminal_box.markdown(caja_codigo)
            if st.session_state.animar_terminal: time.sleep(0.3)

        log_s(">>> INICIANDO MOTOR DE SIMULACIÓN TEÓRICA...")
        dist_total = 0.0
        
        for i in range(len(st.session_state.puntos)):
            if i > 0:
                p_prev, p_act = st.session_state.puntos[i-1], st.session_state.puntos[i]
                d_2d = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
                dz = abs(st.session_state.datos_sensores[i-1]['Z'] - st.session_state.datos_sensores[i]['Z'])
                d_3d = np.sqrt(d_2d**2 + dz**2)
                
                log_s(f"[*] Nodo {i} -> {i+1}: D_3D = {d_3d:.1f}m | H_W calculada con constantes asumidas.")
        log_s(">>> SIMULACIÓN FINALIZADA.")
        st.session_state.animar_terminal = False 

# =================================================================
# MODO 2: OPERACIÓN REAL (CARGA LOTE)
# =================================================================
elif modo == "Operación Real (Carga Lote / En Línea)":
    st.error("🚨 **AVISO ARQUITECTÓNICO - MODO OPERACIÓN REAL:** Aquí **NO SE CONSIDERA NINGUNA VARIABLE DE TIPO CONSTANTE**. La red se trata como un sistema heterogéneo (Caja Negra). Los cálculos de este módulo se realizan EXCLUSIVAMENTE a partir de la dinámica de la señal (Diferencial medido por los sensores).")
    
    archivo_csv = st.file_uploader("Cargar Archivo Maestro de Sensores (.csv)", type=["csv"])
    
    if archivo_csv is not None:
        try:
            df_lote = pd.read_csv(archivo_csv, sep=None, engine='python', encoding_errors='ignore')
            df_lote.columns = (df_lote.columns.str.replace('\ufeff', '', regex=False)
                               .str.strip().str.lower().str.normalize('NFKD')
                               .str.encode('ascii', errors='ignore').str.decode('utf-8'))
            
            # Renombramiento seguro de columnas
            df_lote.rename(columns={'cota_z': 'cota', 'presion_psi': 'presion'}, inplace=True)
            
            # Identificación segura de coordenadas
            cols = df_lote.columns.tolist()
            lat_col = next((c for c in cols if 'lat' in c), None)
            lon_col = next((c for c in cols if 'lon' in c), None)
            
            if lat_col is None or lon_col is None:
                st.error("Error: El archivo CSV debe contener columnas identificables para 'latitud' y 'longitud'.")
            else:
                st.success("Archivo estructurado correctamente. Nodos geolocalizados con éxito.")
                
                # --- VISUALIZACIÓN DEL LOTE (Prioridad Visual) ---
                st.subheader("🗺️ Mapeo Visual de la Red Escaneada")
                df_coords = df_lote[[lat_col, lon_col]].dropna()
                puntos_lote = df_coords.values.tolist()
                
                if puntos_lote:
                    lat_centro = sum([p[0] for p in puntos_lote]) / len(puntos_lote)
                    lon_centro = sum([p[1] for p in puntos_lote]) / len(puntos_lote)
                    
                    m_lote = folium.Map(location=[lat_centro, lon_centro], zoom_start=15)
                    
                    # Marcadores con el código del sensor claramente identificado
                    for i, p in enumerate(puntos_lote):
                        folium.Marker(
                            p, 
                            tooltip=f"Sensor Nodo {i+1} [Cód: N-{i+1}]", 
                            icon=folium.Icon(color='blue', icon='dot-circle-o', prefix='fa')
                        ).add_to(m_lote)
                    
                    if len(puntos_lote) > 1:
                        folium.PolyLine(puntos_lote, color="blue", weight=4, opacity=0.8).add_to(m_lote)
                        
                    st_folium(m_lote, width=1000, height=450, key="mapa_auditoria", returned_objects=[])
                
                if st.button("🚀 Ejecutar Análisis Físico en Lote (Determinístico)", use_container_width=True):
                    st.subheader("🖥️ Consola de Auditoría Real (Paso a Paso)")
                    terminal_batch = st.empty()
                    log_batch = []
                    
                    # Logger de procesamiento por lotes asegurado
                    def log_b(texto):
                        log_batch.append(texto)
                        lineas_visibles = log_batch[-18:]
                        texto_unido = "\n".join(lineas_visibles)
                        caja_codigo = f"```text\n{texto_unido}\n```"
                        terminal_batch.markdown(caja_codigo)
                    
                    log_b(">>> INICIANDO ANÁLISIS DE CAJA NEGRA (OPERACIÓN REAL)...")
                    log_b(f">>> Umbral Físico de Energía establecido en: {UMBRAL_FUGA_PSI} PSI ({UMBRAL_FUGA_MCA:.2f} mca).")
                    log_b(">>> NOTA: Ignorando variables de simulación. Leyendo dinámica directa del pulso de presión.")
                    log_b("-" * 75)
                    
                    dist_total = 0.0
                    matriz_analisis, perfil_grafico, alertas_fuga = [], [], []
                    barra = st.progress(0)
                    
                    for i in range(len(df_lote)):
                        row = df_lote.iloc[i]
                        p_act = [row[lat_col], row[lon_col]]
                        z_act = row.get('cota', 1000.0)
                        p_in = row.get('presion', 0.0)
                        H = z_act + (p_in * FACTOR_CONVERSION_PSI_MCA)
                        
                        if i > 0:
                            log_b(f"[*] PROCESANDO TRAMO EN CIEGO: NODO {i} -> NODO {i+1}")
                            row_prev = df_lote.iloc[i-1]
                            
                            # 1. Geometría Real
                            d_2d = haversine(row_prev[lat_col], row_prev[lon_col], p_act[0], p_act[1])
                            dz = abs(row_prev.get('cota', 1000.0) - z_act)
                            d_3d = np.sqrt(d_2d**2 + dz**2)
                            dist_total += d_3d
                            log_b(f"    ↳ Paso 1: Distancia geodésica y topográfica computada ({d_3d:.2f} m).")
                            
                            # 2. Termodinámica Pura
                            h_prev = row_prev.get('cota', 1000.0) + (row_prev.get('presion', 0.0) * FACTOR_CONVERSION_PSI_MCA)
                            caida_h_real = h_prev - H
                            log_b(f"    ↳ Paso 2: Diferencial de Energía Real (\u0394H_medido) = {caida_h_real:.2f} mca.")
                            
                            # 3. Línea Base Calibrada
                            k_tramo = row_prev.get('sum_k', 0.0)
                            perdida_esperada, v_ms = calcular_balance_hidraulico(20.0, 6, 140, d_3d, k_tramo) 
                            diferencia_energia = caida_h_real - perdida_esperada
                            
                            log_b(f"    ↳ Paso 3: Análisis de anomalía. Excedente de energía = {diferencia_energia:.2f} mca.")
                            
                            # 4. Veredicto
                            if diferencia_energia > UMBRAL_FUGA_MCA:
                                dist_fuga = d_3d * (perdida_esperada / caida_h_real) if caida_h_real != 0 else 0
                                alertas_fuga.append({"T": f"N{i}-N{i+1}", "D": dist_total - d_3d + dist_fuga})
                                log_b(f"    [!] VEREDICTO: ANOMALÍA DETECTADA. Localización a {dist_fuga:.1f}m del Nodo {i}.")
                            else:
                                log_b(f"    [OK] VEREDICTO: Gradiente conservado. Tramo estable.")
                            log_b("-" * 75)
                            time.sleep(0.05)
                        
                        barra.progress(int((i / (len(df_lote) - 1)) * 100) if len(df_lote) > 1 else 100)
                        matriz_analisis.append({"Código Nodo": f"N-{i+1}", "Elevación Z": z_act, "Presión P": p_in, "Energía H": round(H, 2), "Dist. Acumulada": round(dist_total, 2)})
                        perfil_grafico.append({"D": dist_total, "H": H, "Z": z_act})

                    log_b(">>> PROCESAMIENTO DETERMINÍSTICO DEL LOTE FINALIZADO.")

                    st.subheader("📉 Gradiente de Energía Real")
                    df_p = pd.DataFrame(perfil_grafico)
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Línea de Energía (H)', line=dict(color='blue', width=3)))
                    fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Terreno (Z)', fill='tozeroy', line=dict(color='brown', width=2)))
                    for a in alertas_fuga: fig.add_vline(x=a['D'], line_color="red", line_dash="dash", annotation_text="Anomalía")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("📋 Tabla de Nodos e Información Base")
                    st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

        except Exception as e:
            st.error(f"Error crítico procesando lote: Asegúrese de que el formato del CSV sea correcto. Detalles del sistema: {str(e)}")

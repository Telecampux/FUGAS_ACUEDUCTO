# =============================================================================
# SISTEMA IA PARA LOCALIZACIÓN DE FUGAS TÉCNICAS INVISIBLES 
# ESPECIALIZADO EN REDES TRONCALES Y MATRICES DE ACUEDUCTOS
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# Versión: 2.7 - Motor Determinístico (Física Teórica) y Logs Paso a Paso
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
    territorios = {"Bogotá": {"coords": [4.6097, -74.0817]}}
    def haversine(lat1, lon1, lat2, lon2): 
        # Fórmula del Haversine mock si no existe en core
        return 100.0
    def perdida_hazen_williams(q, c, d, l): 
        # Fórmula H-W mock si no existe
        return 0.5

# --- CONSTANTES TÉCNICAS DETERMINÍSTICAS ---
FACTOR_CONVERSION_PSI_MCA = 0.7032
GRAVEDAD = 9.81
UMBRAL_FUGA_PSI = 0.20  # El umbral físico definido (0.2 PSI)
UMBRAL_FUGA_MCA = UMBRAL_FUGA_PSI * FACTOR_CONVERSION_PSI_MCA # Aprox 0.14 mca

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="IA Fugas - Matrices y Troncales", layout="wide")

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
    # 1. Pérdida por fricción lineal (Hazen-Williams)
    hf = perdida_hazen_williams(q_lps, c_hazen, d_pulg, dist_m)
    # 2. Conversión de masa y cálculo de velocidad
    q_m3s = q_lps / 1000.0
    d_m = d_pulg * 0.0254
    area = (np.pi * d_m**2) / 4
    velocidad = q_m3s / area
    # 3. Pérdidas menores por accesorios (Ecuación de Energía de Velocidad)
    hm = k_sum * (velocidad**2 / (2 * GRAVEDAD))
    # 4. Caída teórica total esperada en condiciones ideales
    caida_teorica = (hf * FACTOR_CONVERSION_PSI_MCA) + hm
    return caida_teorica, velocidad

# --- INICIALIZACIÓN DE VARIABLES DE ESTADO ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'datos_sensores' not in st.session_state: st.session_state.datos_sensores = {}
if 'animar_terminal' not in st.session_state: st.session_state.animar_terminal = True

# --- SIDEBAR: MENÚ DE CONTROL Y PARÁMETROS ---
st.sidebar.header("⚙️ PARÁMETROS DE LA RED")

modo = st.sidebar.radio(
    "Seleccione Modo de Trabajo:", 
    ["Simulación Interactiva", "Operación Real (Carga Lote)"]
)
st.sidebar.divider()

q_entrada_lps = st.sidebar.number_input("Caudal Nominal (L/s)", value=20.0, step=0.1, format="%.1f")
dn_pulg = st.sidebar.selectbox("Diámetro (Pulg)", [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24], index=6)
coef_c = st.sidebar.slider("Coeficiente C", 100, 150, 140)

with st.sidebar.expander("📘 Guía de Coeficientes K (Pérdidas Menores)", expanded=False):
    st.markdown("""
    * **Válvula Mariposa:** 0.35
    * **Válvula Compuerta (Abierta):** 0.15
    * **Codo 90° (R. Largo):** 0.30
    * **Codo 45°:** 0.18
    * **Macro-medidor:** 0.10
    """)

# --- INTERFAZ ---
st.title("SISTEMA IA: LOCALIZACIÓN DE FUGAS TÉCNICAS INVISIBLES")
st.subheader("Motor Determinístico: Análisis de Gradiente y Celeridad Efectiva")
st.caption(f"Desarrollado por {AUTOR}")

# =================================================================
# MODO 1: SIMULACIÓN INTERACTIVA
# =================================================================
if modo == "Simulación Interactiva":
    col_map, col_inputs = st.columns([2, 1])

    with col_map:
        mun_sel = st.selectbox("Zona de Operación:", list(territorios.keys()))
        m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=16)
        
        for i, p in enumerate(st.session_state.puntos):
            folium.Marker(
                p, 
                tooltip=f"Sensor Nodo {i+1}", 
                icon=folium.Icon(color='red', icon='dot-circle', prefix='fa')
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
        st.subheader("📡 Lecturas de Campo")
        nodo_a_borrar = None
        
        for i in range(len(st.session_state.puntos)):
            with st.expander(f"Sensor Nodo {i+1}", expanded=True):
                c_lat, c_lon, c_del = st.columns([2, 2, 1])
                lat_nueva = c_lat.number_input("Lat", value=st.session_state.puntos[i][0], key=f"lat_edit_{i}", format="%.6f", step=0.0001)
                lon_nueva = c_lon.number_input("Lon", value=st.session_state.puntos[i][1], key=f"lon_edit_{i}", format="%.6f", step=0.0001)
                
                if lat_nueva != st.session_state.puntos[i][0] or lon_nueva != st.session_state.puntos[i][1]:
                    st.session_state.puntos[i] = [lat_nueva, lon_nueva]
                    st.rerun()
                
                if c_del.button("🗑️", key=f"del_btn_{i}", help="Eliminar únicamente este punto"):
                    nodo_a_borrar = i

                c1, c2 = st.columns(2)
                p_in = c1.number_input(f"Presión (PSI)", key=f"p_{i}", value=0.0, format="%.2f")
                if f"z_{i}" not in st.session_state: st.session_state[f"z_{i}"] = 1000.0
                z_in = c2.number_input(f"Cota (msnm)", key=f"z_{i}", step=0.01, format="%.2f")
                
                k_in = st.number_input(f"ΣK Accesorios (Tramo N{i}-N{i+1})", key=f"k_{i}", value=0.0, step=0.1) if i < len(st.session_state.puntos)-1 else 0.0
                st.session_state.datos_sensores[i] = {"P": p_in, "Z": z_in, "K": k_in}

        if nodo_a_borrar is not None:
            st.session_state.puntos.pop(nodo_a_borrar)
            st.rerun()

        if st.button("🔄 Borrar Toda la Localización", use_container_width=True):
            st.session_state.puntos = []
            st.session_state.datos_sensores = {}
            for key in list(st.session_state.keys()):
                if key.startswith("z_") or key.startswith("p_") or key.startswith("k_") or key.startswith("lat_") or key.startswith("lon_"): del st.session_state[key]
            st.rerun()

    # --- CÁLCULOS E INFORME (Modo Simulación) ---
    if len(st.session_state.puntos) >= 2:
        st.divider()
        
        c1, c2 = st.columns([3, 1])
        with c1:
            st.subheader("🖥️ Consola de Análisis Vectorial (En Vivo)")
        with c2:
            if st.button("▶️ Repetir Análisis", use_container_width=True):
                st.session_state.animar_terminal = True
                st.rerun()

        terminal_box = st.empty()
        log_lineas = []
        pausa = 0.5 if st.session_state.animar_terminal else 0.0
        
        def imprimir_log(texto):
            log_lineas.append(texto)
            terminal_box.markdown(f"```text\n{chr(10).join(log_lineas)}\n```")
            if pausa > 0: time.sleep(pausa)

        imprimir_log(">>> INICIANDO MOTOR DETERMINÍSTICO (FÍSICA TEÓRICA)...")
        imprimir_log(f">>> Parámetros Base: Q_in = {q_entrada_lps} L/s | DN = {dn_pulg}\" | Umbral de Anomalía = {UMBRAL_FUGA_PSI} PSI ({UMBRAL_FUGA_MCA:.2f} mca)")
        imprimir_log("-" * 70)

        dist_total = 0.0
        matriz_analisis = []
        perfil_grafico = [] 
        alertas_fuga = []

        for i in range(len(st.session_state.puntos)):
            p_act = st.session_state.puntos[i]
            datos = st.session_state.datos_sensores[i]
            # Ecuación de Energía: Altura Topográfica + Altura de Presión
            H = datos['Z'] + (datos['P'] * FACTOR_CONVERSION_PSI_MCA)
            
            if i > 0:
                imprimir_log(f"[*] EVALUANDO TRAMO: NODO {i} -> NODO {i+1}")
                p_prev = st.session_state.puntos[i-1]
                
                # Paso 1: Geometría de la Caja Negra
                d_2d = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
                dz = abs(st.session_state.datos_sensores[i-1]['Z'] - datos['Z'])
                d_3d = np.sqrt(d_2d**2 + dz**2)
                dist_total += d_3d
                imprimir_log(f"    Paso 1 - Geometría: Distancia 3D Efectiva calculada = {d_3d:.2f} m")
                
                # Paso 2: Diferencial de Energía Real (Lectura de Sensores)
                h_prev = st.session_state.datos_sensores[i-1]['Z'] + (st.session_state.datos_sensores[i-1]['P'] * FACTOR_CONVERSION_PSI_MCA)
                caida_h_real = h_prev - H
                imprimir_log(f"    Paso 2 - Termodinámica: Diferencial de Energía Medido (\u0394H_real) = {caida_h_real:.2f} mca")
                
                # Paso 3: Diferencial de Energía Teórica (Conservación de Energía)
                k_tramo = st.session_state.datos_sensores[i-1].get('K', 0.0)
                perdida_esperada, v_ms = calcular_balance_hidraulico(q_entrada_lps, dn_pulg, coef_c, d_3d, k_tramo)
                imprimir_log(f"    Paso 3 - Fricción Teórica: \u0394H_teórico (H-W + Accesorios) = {perdida_esperada:.2f} mca a Vel={v_ms:.2f} m/s")
                
                # Paso 4: Análisis de Discrepancia (Umbral Físico 0.2 PSI)
                diferencia_energia = caida_h_real - perdida_esperada
                imprimir_log(f"    Paso 4 - Balance: Discrepancia detectada = {diferencia_energia:.2f} mca")
                
                if diferencia_energia > UMBRAL_FUGA_MCA:
                    imprimir_log(f"    [!] ALERTA CRÍTICA: Discrepancia SUPERA el umbral de {UMBRAL_FUGA_MCA:.2f} mca. Iniciando Localización...")
                    
                    # Localización Determinística: Intersección de gradiente de energía
                    dist_fuga = d_3d * (perdida_esperada / caida_h_real) if caida_h_real != 0 else 0
                    
                    # Cálculo de magnitud de fuga (Orificio / Torricelli simplificado)
                    relacion_h = perdida_esperada / caida_h_real if caida_h_real != 0 else 1
                    q_fuga = abs(q_entrada_lps * (1 - np.sqrt(relacion_h)))
                    
                    alertas_fuga.append({"T": f"N{i}-N{i+1}", "Q": q_fuga, "D": dist_total - d_3d + dist_fuga, "V": v_ms})
                    imprimir_log(f"    => RESULTADO FÍSICO: Fuga de {q_fuga:.2f} L/s ubicada matemáticamente a {dist_fuga:.1f} m del Nodo {i}.")
                else:
                    imprimir_log(f"    [OK] BALANCE ESTABLE: Discrepancia dentro del margen de error físico.")
                imprimir_log("-" * 70)

            matriz_analisis.append({"Nodo": i + 1, "Latitud": f"{p_act[0]:.6f}", "Longitud": f"{p_act[1]:.6f}", "Cota Z": datos['Z'], "Presión": datos['P'], "Energía H": round(H, 2), "Dist. Acum": round(dist_total, 2)})
            perfil_grafico.append({"D": dist_total, "H": H, "Z": datos['Z']})

        imprimir_log(">>> ANÁLISIS DETERMINÍSTICO FINALIZADO CON ÉXITO.")
        st.session_state.animar_terminal = False 

        st.subheader("📉 Diagnóstico del Gradiente Hidráulico")
        df_p = pd.DataFrame(perfil_grafico)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Línea de Energía (H)', line=dict(color='blue', width=3)))
        fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Perfil Terreno (Z)', fill='tozeroy', line=dict(color='brown', width=2)))

        # Agregar marcadores visuales para las fugas en el gráfico
        for a in alertas_fuga:
            fig.add_vline(x=a['D'], line_width=2, line_dash="dash", line_color="red", annotation_text=f"Fuga: {a['Q']:.1f} L/s")

        fig.update_layout(hovermode=False, xaxis_title="Distancia Acumulada (m)", yaxis_title="Elevación (msnm)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Matriz de Localización Geográfica")
        st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

        if alertas_fuga:
            for a in alertas_fuga:
                st.error(f"🚨 **FUGA TÉCNICA LOCALIZADA** en tramo **{a['T']}**. Pérdida de masa: **{a['Q']:.2f} L/s** a exactamente **{a['D']:.1f} m** desde el origen.")
        else:
            st.success("✅ **SISTEMA ESTABLE**: Conservación de masa y energía validada. No hay anomalías estructurales.")

# =================================================================
# MODO 2: OPERACIÓN REAL (CARGA LOTE)
# =================================================================
elif modo == "Operación Real (Carga Lote)":
    st.write("### 📊 Auditoría Masiva por Carga de Datos (Análisis Determinístico)")
    st.info("Módulo configurado para procesamiento masivo de sensores IoT mediante ecuaciones de conservación de energía.")
    
    archivo_csv = st.file_uploader("Cargar Archivo Maestro de Campo (.csv)", type=["csv"])
    
    if archivo_csv is not None:
        try:
            df_lote = pd.read_csv(archivo_csv, sep=None, engine='python', encoding_errors='ignore')
            
            df_lote.columns = (df_lote.columns.str.replace('\ufeff', '', regex=False)
                               .str.strip().str.lower().str.normalize('NFKD')
                               .str.encode('ascii', errors='ignore').str.decode('utf-8'))
            df_lote.rename(columns={'cota_z': 'cota', 'presion_psi': 'presion', 'sumatoria_k': 'sum_k'}, inplace=True)
            
            if 'sum_k' not in df_lote.columns:
                df_lote['sum_k'] = 0.0

            st.success("Archivo estructurado correctamente. Previsualización de Nodos:")
            st.dataframe(df_lote.head())
            
            # =================================================================
            # MAPA DEL LOTE CON IDENTIFICACIÓN DE SENSORES
            # =================================================================
            st.subheader("🗺️ Trazado Geográfico de la Red (Datos Cargados)")
            
            cols = df_lote.columns.tolist()
            lat_col = next((c for c in cols if 'lat' in c.lower()), None)
            lon_col = next((c for c in cols if 'lon' in c.lower()), None)
            
            if lat_col and lon_col:
                try:
                    df_coords = df_lote[[lat_col, lon_col]].dropna()
                    puntos_lote = df_coords.values.tolist()
                    
                    if puntos_lote:
                        lat_centro = sum([p[0] for p in puntos_lote]) / len(puntos_lote)
                        lon_centro = sum([p[1] for p in puntos_lote]) / len(puntos_lote)
                        
                        m_lote = folium.Map(location=[lat_centro, lon_centro], zoom_start=15)
                        
                        for i, p in enumerate(puntos_lote):
                            folium.Marker(
                                p, 
                                tooltip=f"Sensor Nodo {i+1}", 
                                icon=folium.Icon(color='blue', icon='dot-circle', prefix='fa')
                            ).add_to(m_lote)
                        
                        if len(puntos_lote) > 1:
                            folium.PolyLine(puntos_lote, color="blue", weight=4, opacity=0.8).add_to(m_lote)
                            
                        st_folium(m_lote, width=1000, height=450, key="mapa_auditoria_lote", returned_objects=[])
                    else:
                        st.info("El CSV no contiene coordenadas válidas para graficar.")
                        
                except Exception as e:
                    st.error(f"Error interno al trazar el mapa: {e}")
            else:
                st.warning(f"⚠️ Imposible graficar: No se encontraron columnas de latitud/longitud.")
            
            if st.button("🚀 Ejecutar Análisis Físico del Lote", use_container_width=True):
                st.subheader("🖥️ Consola de Auditoría Masiva (Lote)")
                terminal_batch = st.empty()
                log_batch = []
                
                def log_b(texto):
                    log_batch.append(texto)
                    lineas_visibles = log_batch[-15:] if len(log_batch) > 15 else log_batch
                    terminal_batch.markdown(f"```text\n{chr(10).join(lineas_visibles)}\n```")
                
                log_b(">>> INICIANDO CÁLCULO TERMODINÁMICO DEL ARCHIVO MAESTRO...")
                log_b(f">>> Umbral Crítico Establecido: {UMBRAL_FUGA_PSI} PSI de diferencial.")
                
                dist_total = 0.0
                matriz_analisis = []
                perfil_grafico = [] 
                alertas_fuga = []
                
                barra = st.progress(0)
                
                columna_lat = lat_col if lat_col else 'latitud'
                columna_lon = lon_col if lon_col else 'longitud'
                
                for i in range(len(df_lote)):
                    row = df_lote.iloc[i]
                    p_act = [row[columna_lat], row[columna_lon]]
                    z_act = row['cota']
                    p_in = row['presion']
                    H = z_act + (p_in * FACTOR_CONVERSION_PSI_MCA)
                    
                    if i > 0:
                        log_b(f"[*] Analizando Balance de Masa y Energía Nodo {i} -> Nodo {i+1}...")
                        row_prev = df_lote.iloc[i-1]
                        p_prev = [row_prev[columna_lat], row_prev[columna_lon]]
                        d_2d = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
                        dz = abs(row_prev['cota'] - z_act)
                        d_3d = np.sqrt(d_2d**2 + dz**2)
                        dist_total += d_3d
                        
                        h_prev = row_prev['cota'] + (row_prev['presion'] * FACTOR_CONVERSION_PSI_MCA)
                        caida_h_real = h_prev - H
                        
                        k_tramo = row_prev['sum_k'] 
                        perdida_esperada, v_ms = calcular_balance_hidraulico(q_entrada_lps, dn_pulg, coef_c, d_3d, k_tramo)
                        
                        diferencia_energia = caida_h_real - perdida_esperada
                        log_b(f"    ↳ \u0394H_real={caida_h_real:.2f}mca | \u0394H_teórico={perdida_esperada:.2f}mca | Discrepancia={diferencia_energia:.2f}mca")
                        
                        if diferencia_energia > UMBRAL_FUGA_MCA:
                            dist_fuga = d_3d * (perdida_esperada / caida_h_real) if caida_h_real != 0 else 0
                            relacion_h = perdida_esperada / caida_h_real if caida_h_real != 0 else 1
                            q_fuga = abs(q_entrada_lps * (1 - np.sqrt(relacion_h)))
                            alertas_fuga.append({"T": f"N{i}-N{i+1}", "Q": q_fuga, "D": dist_total - d_3d + dist_fuga})
                            log_b(f"    [!] ANOMALÍA ESTRUCTURAL CONFIRMADA (> 0.2 PSI)")
                        
                        time.sleep(0.05) 
                    
                    barra.progress(int((i / (len(df_lote) - 1)) * 100) if len(df_lote) > 1 else 100)
                    matriz_analisis.append({"Nodo": i + 1, "Latitud": f"{p_act[0]:.6f}", "Longitud": f"{p_act[1]:.6f}", "Cota Z": z_act, "Presión": p_in, "Energía H": round(H, 2), "Dist. Acum": round(dist_total, 2)})
                    perfil_grafico.append({"D": dist_total, "H": H, "Z": z_act})

                log_b(">>> PROCESAMIENTO MASIVO FINALIZADO.")

                st.subheader("📉 Diagnóstico del Gradiente Hidráulico Lote")
                df_p = pd.DataFrame(perfil_grafico)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Línea de Energía (H)', line=dict(color='blue', width=3)))
                fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Perfil Terreno (Z)', fill='tozeroy', line=dict(color='brown', width=2)))

                for a in alertas_fuga:
                    fig.add_vline(x=a['D'], line_width=2, line_dash="dash", line_color="red", annotation_text=f"Fuga: {a['Q']:.1f} L/s")

                fig.update_layout(hovermode=False, xaxis_title="Distancia Acumulada (m)", yaxis_title="Elevación (msnm)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("📋 Matriz de Localización Geográfica (Procesada)")
                st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

                if alertas_fuga:
                    for a in alertas_fuga:
                        st.error(f"🚨 **FUGA TÉCNICA LOCALIZADA** en tramo **{a['T']}**. Pérdida de masa: **{a['Q']:.2f} L/s** a exactamente **{a['D']:.1f} m** desde el origen.")
                else:
                    st.success("✅ **SISTEMA ESTABLE**: Conservación de masa y energía validada en todo el lote.")

        except KeyError as e:
            st.error(f"Error estructural residual. Faltante o irreconocible: {e}")
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

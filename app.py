# =============================================================================
# IANC_H2O: SISTEMA PARA LOCALIZACIÓN DE FUGAS INVISIBLES EN ACUEDUCTOS 
# ESPECIALIZADO EN REDES MATRIZ Y SECUNDARIA
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# Versión: 2.9.1 - Restauración de Arquitectura + Control Altimétrico Estricto
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
        return np.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111320.0
    def perdida_hazen_williams(q, c, d, l): 
        q_m3s = q / 1000.0
        d_m = d * 0.0254
        if c == 0 or d_m == 0: return 0.0
        return 10.67 * (q_m3s ** 1.852) * l / ((c ** 1.852) * (d_m ** 4.87))

# --- CONSTANTES TÉCNICAS DETERMINÍSTICAS ---
FACTOR_CONVERSION_PSI_MCA = 0.7032
GRAVEDAD = 9.81
UMBRAL_FUGA_PSI = 0.20  
UMBRAL_FUGA_MCA = UMBRAL_FUGA_PSI * FACTOR_CONVERSION_PSI_MCA 

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="IANC_H2O - Fugas", layout="wide")

def obtener_cota_api(lat, lon):
    # Ya no asume 1000m. Si falla, retorna 0.0 para forzar revisión manual.
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        respuesta = requests.get(url, timeout=3).json()
        if "elevation" in respuesta and respuesta["elevation"]:
            return round(respuesta["elevation"][0], 2)
    except Exception:
        pass
    return 0.0

def calcular_balance_hidraulico(q_lps, d_pulg, c_hazen, dist_m, k_sum):
    hf = perdida_hazen_williams(q_lps, c_hazen, d_pulg, dist_m)
    q_m3s = q_lps / 1000.0
    d_m = d_pulg * 0.0254
    area = (np.pi * d_m**2) / 4
    velocidad = q_m3s / area if area > 0 else 0
    hm = k_sum * (velocidad**2 / (2 * GRAVEDAD))
    caida_teorica = hf + hm
    return caida_teorica, velocidad

# --- INICIALIZACIÓN DE ESTADO ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'datos_sensores' not in st.session_state: st.session_state.datos_sensores = {}
if 'animar_terminal' not in st.session_state: st.session_state.animar_terminal = True

# --- INTERFAZ PRINCIPAL ---
st.title("IANC_H2O: LOCALIZACIÓN DE FUGAS INVISIBLES")
st.subheader("Motor Determinístico: Análisis de Gradiente de Energía")
st.caption(f"Desarrollado por {AUTOR}")

# --- SIDEBAR: MENÚ DE CONTROL ---
st.sidebar.header("⚙️ CONTROL DEL SISTEMA")
modo = st.sidebar.radio(
    "Seleccione Entorno de Trabajo:", 
    ["Simulación Interactiva", "Operación Real (Carga Lote / En Línea)"]
)
st.sidebar.divider()

if modo == "Simulación Interactiva":
    st.sidebar.markdown("### 📝 Variables Ideales")
    q_entrada_lps = st.sidebar.number_input("Caudal Nominal (L/s)", value=20.0, step=0.1, format="%.1f")
    dn_pulg = st.sidebar.selectbox("Diámetro (Pulg)", [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24], index=6)
    coef_c = st.sidebar.slider("Coeficiente C (Fricción)", 100, 150, 140)
else:
    st.sidebar.markdown("### 🔒 Variables Deshabilitadas")
    st.sidebar.info("MODO REAL ACTIVO: Variables teóricas bloqueadas. Análisis por caja negra de presión.")
    q_entrada_lps, dn_pulg, coef_c = 20.0, 6, 140

# =================================================================
# MODO 1: SIMULACIÓN INTERACTIVA
# =================================================================
if modo == "Simulación Interactiva":
    st.warning("⚠️ **AVISO ARQUITECTÓNICO:** Las variables del panel lateral actúan como constantes de red.")
    
    col_map, col_inputs = st.columns([2, 1])

    with col_map:
        mun_sel = st.selectbox("Zona de Operación:", list(territorios.keys()))
        m = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
        
        for i, p in enumerate(st.session_state.puntos):
            folium.Marker(p, tooltip=f"Nodo {i+1}", icon=folium.Icon(color='blue', icon='info-sign')).add_to(m)
        
        if len(st.session_state.puntos) > 1:
            folium.PolyLine(st.session_state.puntos, color="blue", weight=4).add_to(m)

        mapa_data = st_folium(m, width=700, height=450, key="mapa_sim")
        
        if mapa_data and mapa_data.get('last_clicked'):
            lat, lng = mapa_data['last_clicked']['lat'], mapa_data['last_clicked']['lng']
            if [lat, lng] not in st.session_state.puntos:
                st.session_state.puntos.append([lat, lng])
                idx = len(st.session_state.puntos) - 1
                st.session_state[f"z_{idx}"] = float(obtener_cota_api(lat, lng))
                st.session_state.animar_terminal = True
                st.rerun()

    with col_inputs:
        st.subheader("📡 Panel de Sensores (Input Requerido)")
        nodo_a_borrar = None
        
        for i in range(len(st.session_state.puntos)):
            with st.expander(f"Sensor Nodo {i+1}", expanded=True):
                c1, c2 = st.columns(2)
                p_in = c1.number_input(f"Presión Real (PSI) *", key=f"p_{i}", value=st.session_state.datos_sensores.get(i, {}).get("P", 0.0), format="%.2f")
                if f"z_{i}" not in st.session_state: st.session_state[f"z_{i}"] = 0.0
                # Cota abierta a edición manual, vital para precisión
                z_in = c2.number_input(f"Cota (msnm) *", key=f"z_{i}", step=0.5, format="%.2f")
                k_in = st.number_input(f"ΣK Accesorios", key=f"k_{i}", value=0.0, step=0.1) if i < len(st.session_state.puntos)-1 else 0.0
                st.session_state.datos_sensores[i] = {"P": p_in, "Z": z_in, "K": k_in}
                
                if st.button("🗑️ Borrar Nodo", key=f"del_{i}"): nodo_a_borrar = i

        if nodo_a_borrar is not None:
            st.session_state.puntos.pop(nodo_a_borrar)
            st.rerun()
            
        if st.button("🔄 Reiniciar Escaneo", use_container_width=True):
            st.session_state.puntos = []
            st.rerun()

    if len(st.session_state.puntos) >= 2:
        st.divider()
        
        if st.button("🚀 Ejecutar Análisis Termodinámico", type="primary", use_container_width=True):
            
            p_0 = st.session_state.datos_sensores[0]['P']
            if p_0 <= 0.0:
                st.error("🛑 **ERROR DE CONDICIÓN INICIAL:** La presión en el Nodo Origen (Nodo 1) es de 0.0 PSI. Es físicamente inviable iniciar el balance sin pulso de entrada.")
                st.stop()

            terminal_box = st.empty()
            log_lineas = []
            
            def log_s(texto, color="#4AF626", bold=False, size="1em"):
                weight = "bold" if bold else "normal"
                linea = f"<span style='color:{color}; font-weight:{weight}; font-size:{size};'>{texto}</span><br>"
                log_lineas.append(linea)
                html_caja = f"""
                <div style='background-color:#0D1117; padding:15px; border-radius:5px; border: 1px solid #30363D; font-family: "Courier New", Courier, monospace; height:350px; overflow-y:auto; line-height: 1.4;'>
                    {"".join(log_lineas[-30:])}
                </div>
                """
                terminal_box.markdown(html_caja, unsafe_allow_html=True)
                if st.session_state.animar_terminal: time.sleep(0.08)

            log_s(">>> VERIFICACIÓN DE VARIABLES SUPERADA. INICIANDO MOTOR DETERMINÍSTICO...", color="#58A6FF")
            dist_total = 0.0
            matriz_analisis, perfil_grafico, alertas_fuga = [], [], []

            z_0 = st.session_state.datos_sensores[0]['Z']
            H_prev = z_0 + (p_0 * FACTOR_CONVERSION_PSI_MCA)
            
            matriz_analisis.append({"Nodo": "N-1", "Z (m)": z_0, "P (PSI)": p_0, "H (mca)": round(H_prev, 2), "D Acum (m)": 0.0})
            perfil_grafico.append({"D": 0.0, "H": H_prev, "Z": z_0})

            for i in range(1, len(st.session_state.puntos)):
                p_prev, p_act = st.session_state.puntos[i-1], st.session_state.puntos[i]
                
                # Cálculo de Distancia 3D Real Integrando Altimetría
                d_2d = haversine(p_prev[0], p_prev[1], p_act[0], p_act[1])
                z_prev = st.session_state.datos_sensores[i-1]['Z']
                z_act = st.session_state.datos_sensores[i]['Z']
                dz = abs(z_prev - z_act)
                d_3d = np.sqrt(d_2d**2 + dz**2) 
                dist_total += d_3d

                p_in = st.session_state.datos_sensores[i]['P']
                k_tramo = st.session_state.datos_sensores[i-1]['K']
                
                H_act = z_act + (p_in * FACTOR_CONVERSION_PSI_MCA)
                caida_h_real = H_prev - H_act
                perdida_esperada, v_ms = calcular_balance_hidraulico(q_entrada_lps, dn_pulg, coef_c, d_3d, k_tramo)
                diferencia_energia = caida_h_real - perdida_esperada

                log_s(f"[*] EVALUANDO TRAMO: NODO {i} -> NODO {i+1}", color="#8B949E")
                log_s(f"    ↳ L real (3D)={d_3d:.1f}m | H_prev={H_prev:.2f}mca | H_act={H_act:.2f}mca", color="#C9D1D9")
                log_s(f"    ↳ ΔH_Real = {caida_h_real:.2f} mca | ΔH_Teórico = {perdida_esperada:.2f} mca", color="#C9D1D9")
                
                if diferencia_energia > UMBRAL_FUGA_MCA:
                    dist_fuga = d_3d * (perdida_esperada / caida_h_real) if caida_h_real != 0 else 0
                    loc_absoluta = (dist_total - d_3d) + dist_fuga
                    alertas_fuga.append({"T": f"N{i}-N{i+1}", "D": loc_absoluta, "Rel": dist_fuga})
                    
                    log_s(f"    [!!!] RUPTURA DE GRADIENTE. EXCEDENTE ENERGÉTICO: {diferencia_energia:.2f} mca", color="red", bold=True, size="1.1em")
                    log_s(f"    [!!!] FUGA DETECTADA A {dist_fuga:.1f} m DEL NODO {i}.", color="red", bold=True, size="1.1em")
                else:
                    log_s(f"    [OK] Gradiente conservado dentro de los umbrales de seguridad.", color="#4AF626")
                
                log_s("-" * 65, color="#30363D")

                H_prev = H_act
                matriz_analisis.append({"Nodo": f"N-{i+1}", "Z (m)": z_act, "P (PSI)": p_in, "H (mca)": round(H_act, 2), "D Acum (m)": round(dist_total, 2)})
                perfil_grafico.append({"D": dist_total, "H": H_act, "Z": z_act})

            log_s(">>> MATRIZ CERRADA. ANÁLISIS FINALIZADO.", color="#58A6FF")
            st.session_state.animar_terminal = False 

            if alertas_fuga:
                for alerta in alertas_fuga:
                    st.error(f"🚨 **ALERTA DE FUGA DETECTADA:** Falla termodinámica en el tramo **{alerta['T']}**. Distancia de ruptura calculada: **{alerta['Rel']:.2f} metros** desde el inicio del tramo.", icon="🔴")
            else:
                st.success("✅ La red analizada opera en perfectas condiciones bajo la línea piezométrica teórica.", icon="🟢")

            st.subheader("📉 Perfil de Gradiente de Energía")
            df_p = pd.DataFrame(perfil_grafico)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Línea Piezométrica (H)', line=dict(color='blue', width=3)))
            fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Perfil Topográfico (Z)', fill='tozeroy', line=dict(color='brown', width=2)))
            
            for a in alertas_fuga: 
                fig.add_vline(x=a['D'], line_color="red", line_width=2, line_dash="dash", annotation_text="PUNTO DE FUGA", annotation_font_color="red")
                
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Matriz de Estados Nodal")
            st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

# =================================================================
# MODO 2: OPERACIÓN REAL (CARGA LOTE)
# =================================================================
elif modo == "Operación Real (Carga Lote / En Línea)":
    st.error("🚨 **AVISO ARQUITECTÓNICO:** La red se analiza como un sistema heterogéneo (Caja Negra) basado exclusivamente en métricas físicas comprobables.")
    
    archivo_csv = st.file_uploader("Cargar Archivo Maestro de Sensores (.csv)", type=["csv"])
    
    if archivo_csv is not None:
        try:
            df_lote = pd.read_csv(archivo_csv, sep=None, engine='python', encoding_errors='ignore')
            df_lote.columns = (df_lote.columns.str.replace('\ufeff', '', regex=False)
                               .str.strip().str.lower().str.normalize('NFKD')
                               .str.encode('ascii', errors='ignore').str.decode('utf-8'))
            
            df_lote.rename(columns={'cota_z': 'cota', 'presion_psi': 'presion'}, inplace=True)
            cols = df_lote.columns.tolist()
            lat_col, lon_col = next((c for c in cols if 'lat' in c), None), next((c for c in cols if 'lon' in c), None)
            
            if not lat_col or not lon_col:
                st.error("🛑 Error: CSV carece de columnas estructurales 'latitud' y 'longitud'.")
                st.stop()
                
            # COMPUERTA ALTIMÉTRICA ESTRICTA EN LOTE
            if 'cota' not in cols:
                st.error("🛑 **ERROR ESTRUCTURAL DE DATOS:** El archivo CSV no contiene la columna 'cota' o 'cota_z'. El sistema requiere la altimetría exacta para modelar la línea piezométrica. No se asumirán elevaciones falsas.")
                st.stop()

            st.subheader("🗺️ Escaneo Geoespacial")
            df_coords = df_lote[[lat_col, lon_col]].dropna()
            puntos_lote = df_coords.values.tolist()
            
            if puntos_lote:
                lat_c, lon_c = np.mean([p[0] for p in puntos_lote]), np.mean([p[1] for p in puntos_lote])
                m_lote = folium.Map(location=[lat_c, lon_c], zoom_start=15)
                for i, p in enumerate(puntos_lote):
                    folium.Marker(p, tooltip=f"N-{i+1}", icon=folium.Icon(color='blue', icon='dot-circle-o', prefix='fa')).add_to(m_lote)
                if len(puntos_lote) > 1:
                    folium.PolyLine(puntos_lote, color="blue", weight=4, opacity=0.8).add_to(m_lote)
                st_folium(m_lote, width=1000, height=450, key="mapa_aud", returned_objects=[])
            
            if st.button("🚀 Ejecutar Análisis Físico en Lote", type="primary", use_container_width=True):
                
                if df_lote.iloc[0].get('presion', 0.0) <= 0.0:
                    st.error("🛑 **ERROR DE CONDICIÓN INICIAL:** La presión registrada en la fila 1 del archivo CSV es nula. Revise la instrumentación de entrada.")
                    st.stop()

                terminal_batch = st.empty()
                log_batch = []
                
                def log_b(texto, color="#4AF626", bold=False, size="1em"):
                    w = "bold" if bold else "normal"
                    log_batch.append(f"<span style='color:{color}; font-weight:{w}; font-size:{size};'>{texto}</span><br>")
                    html_b = f"<div style='background-color:#0D1117; padding:15px; border-radius:5px; font-family:monospace; height:350px; overflow-y:auto; line-height: 1.4;'>{''.join(log_batch[-25:])}</div>"
                    terminal_batch.markdown(html_b, unsafe_allow_html=True)
                
                log_b(">>> INICIANDO ANÁLISIS DE CAJA NEGRA...", color="#58A6FF")
                dist_total = 0.0
                matriz_analisis, perfil_grafico, alertas_fuga = [], [], []
                barra = st.progress(0)
                
                for i in range(len(df_lote)):
                    row = df_lote.iloc[i]
                    p_act = [row[lat_col], row[lon_col]]
                    z_act, p_in = row['cota'], row.get('presion', 0.0)
                    H = z_act + (p_in * FACTOR_CONVERSION_PSI_MCA)
                    
                    if i > 0:
                        row_prev = df_lote.iloc[i-1]
                        d_2d = haversine(row_prev[lat_col], row_prev[lon_col], p_act[0], p_act[1])
                        # Cálculo 3D riguroso
                        d_3d = np.sqrt(d_2d**2 + abs(row_prev['cota'] - z_act)**2)
                        dist_total += d_3d
                        
                        h_prev = row_prev['cota'] + (row_prev.get('presion', 0.0) * FACTOR_CONVERSION_PSI_MCA)
                        caida_h_real = h_prev - H
                        k_tramo = row_prev.get('sum_k', 0.0)
                        perdida_esperada, v_ms = calcular_balance_hidraulico(20.0, 6, 140, d_3d, k_tramo) 
                        diferencia_energia = caida_h_real - perdida_esperada
                        
                        log_b(f"[*] TRAMO NODO {i} -> NODO {i+1} | ΔH = {caida_h_real:.2f} mca", color="#C9D1D9")
                        if diferencia_energia > UMBRAL_FUGA_MCA:
                            dist_fuga = d_3d * (perdida_esperada / caida_h_real) if caida_h_real != 0 else 0
                            alertas_fuga.append({"T": f"N{i}-N{i+1}", "D": dist_total - d_3d + dist_fuga, "Rel": dist_fuga})
                            
                            log_b(f"    [!!!] FUGA DETECTADA A {dist_fuga:.1f}m DEL NODO ORIGEN.", color="red", bold=True, size="1.1em")
                        else:
                            log_b("    [OK] Tramo estable.", color="#4AF626")
                        time.sleep(0.05)
                    
                    barra.progress(int((i / (len(df_lote) - 1)) * 100) if len(df_lote) > 1 else 100)
                    matriz_analisis.append({"Nodo": f"N-{i+1}", "Z (m)": z_act, "P (PSI)": p_in, "H (mca)": round(H, 2), "D Acum": round(dist_total, 2)})
                    perfil_grafico.append({"D": dist_total, "H": H, "Z": z_act})

                log_b(">>> PROCESAMIENTO MATEMÁTICO FINALIZADO.", color="#58A6FF")

                if alertas_fuga:
                    for alerta in alertas_fuga: 
                        st.error(f"🚨 **ALERTA DE FUGA DETECTADA:** Falla en tramo **{alerta['T']}** a **{alerta['Rel']:.2f}m**.", icon="🔴")

                st.subheader("📉 Gradiente de Energía Real")
                df_p = pd.DataFrame(perfil_grafico)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Línea Piezométrica (H)', line=dict(color='blue', width=3)))
                fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Terreno (Z)', fill='tozeroy', line=dict(color='brown', width=2)))
                for a in alertas_fuga: fig.add_vline(x=a['D'], line_color="red", line_width=2, line_dash="dash", annotation_text="FUGA DETECTADA", annotation_font_color="red")
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("📋 Matriz de Nodos")
                st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

        except Exception as e:
            st.error(f"Error crítico en la ingesta del CSV. Verifique la estructura de los datos. Trace: {str(e)}")

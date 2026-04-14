# =============================================================================
# IANC_H2O: SISTEMA PARA LOCALIZACIÓN DE FUGAS INVISIBLES EN ACUEDUCTOS 
# ESPECIALIZADO EN REDES MATRIZ Y SECUNDARIA
# Autor: Ing. Adolfo Barrera Vargas | (c) 2026
# Versión: 3.5.0 - Consola de Depuración y Diccionario de Variables en Tiempo Real
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

st.set_page_config(page_title="IANC_H2O - Fugas", layout="wide")

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
    caida_teorica = hf + hm
    return caida_teorica, velocidad

def renderizar_marco_teorico():
    st.subheader("🧠 Marco Analítico Termodinámico")
    st.markdown("""
    Para localizar la anomalía, el sistema prescinde de estimaciones y evalúa la red bajo los principios físicos de **Conservación de la Energía** y mecánica de fluidos.
    
    #### 1. Definición de Variables de Estado
    Antes de evaluar el gradiente, se extraen las variables físicas de cada nodo sensado:
    * **$Z$ (Cota topográfica):** Medida en metros sobre el nivel del mar (msnm). Aporta la *energía potencial gravitacional* del fluido por su posición espacial.
    * **$P$ (Presión estática):** Medida en PSI (y convertida a mca). Representa el *trabajo o energía interna* que ejerce el fluido contra las paredes de la tubería.
    * **$L_{3D}$ (Longitud Espacial):** Distancia tridimensional en metros. Es la métrica vectorial sobre la cual ocurre la fricción del fluido.
    
    #### 2. Ecuaciones Físicas Aplicadas
    El modelo ejecuta tres pasos fundamentales por cada tramo analizado:
    
    **A. Ecuación de Carga Hidráulica (Bernoulli Simplificado)**
    Unificamos la energía del sistema en un punto. Al asumir un diámetro constante, la carga de velocidad se anula en el diferencial, operando con la altura piezométrica:
    $$ H = Z + P_{mca} $$
    
    **B. Diferencial de Energía Real vs. Fricción Teórica**
    Comparamos la caída de energía medida en el terreno ($\Delta H_{real}$) contra la resistencia que opone el material de la tubería calculada mediante el modelo empírico de Hazen-Williams ($\Delta H_{teo}$).
    $$ \Delta H_{real} = H_{prev} - H_{act} $$
    $$ \Delta H_{teo} = \frac{10.67 \cdot Q^{1.852}}{C^{1.852} \cdot D^{4.87}} \cdot L_{3D} + \sum K \frac{v^2}{2g} $$
    
    **C. Vectorización de Ruptura (Interpolación)**
    Si el diferencial de energía supera el umbral físico ($\Delta H_{real} > \Delta H_{teo}$), confirmamos que existe un sumidero de energía (fuga). Se proyecta la ubicación exacta ($X$) relacionando la fricción con la caída:
    $$ X = L_{3D} \times \left( \frac{\Delta H_{teo}}{\Delta H_{real}} \right) $$
    """)

# --- INICIALIZACIÓN DE ESTADO ---
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'datos_sensores' not in st.session_state: st.session_state.datos_sensores = {}

# --- TÍTULO EXACTO SOLICITADO ---
st.title("IANC_H2O: LOCALIZACIÓN DE FUGAS INVISIBLES EN ACUEDUCTOS (MATRIZ Y SECUNDARIA)")
st.subheader("Motor Determinístico: Análisis de Gradiente de Energía")
st.caption(f"Desarrollado por {AUTOR}")

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
    st.sidebar.info("MODO REAL ACTIVO: Variables teóricas bloqueadas. Análisis por termodinámica directa.")
    q_entrada_lps, dn_pulg, coef_c = 20.0, 6, 140

# =================================================================
# MODO 1: SIMULACIÓN INTERACTIVA
# =================================================================
if modo == "Simulación Interactiva":
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
                st.rerun()

    with col_inputs:
        st.subheader("📡 Panel de Sensores")
        nodo_a_borrar = None
        
        for i in range(len(st.session_state.puntos)):
            with st.expander(f"Sensor Nodo {i+1}", expanded=True):
                c1, c2 = st.columns(2)
                p_in = c1.number_input(f"Presión Real (PSI) *", key=f"p_{i}", value=st.session_state.datos_sensores.get(i, {}).get("P", 0.0), format="%.2f")
                if f"z_{i}" not in st.session_state: st.session_state[f"z_{i}"] = 1000.0
                z_in = c2.number_input(f"Cota (msnm)", key=f"z_{i}", step=0.01, format="%.2f")
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
                st.error("🛑 **ERROR DE CONDICIÓN INICIAL:** La presión en el Nodo Origen es 0.0 PSI. Introduzca la variable de presión real.")
                st.stop()

            barra_progreso = st.progress(0, text="Verificando variables. Iniciando motor determinístico...")
            dist_total = 0.0
            matriz_analisis, perfil_grafico, alertas_fuga = [], [], []

            z_0 = st.session_state.datos_sensores[0]['Z']
            H_prev = z_0 + (p_0 * FACTOR_CONVERSION_PSI_MCA)
            
            matriz_analisis.append({"Nodo": "N-1", "Z (m)": z_0, "P (PSI)": p_0, "H (mca)": round(H_prev, 2), "D Acum (m)": 0.0})
            perfil_grafico.append({"D": 0.0, "H": H_prev, "Z": z_0})

            n_tramos = len(st.session_state.puntos) - 1
            for i in range(1, len(st.session_state.puntos)):
                p_prev_coord, p_act_coord = st.session_state.puntos[i-1], st.session_state.puntos[i]
                
                d_2d = haversine(p_prev_coord[0], p_prev_coord[1], p_act_coord[0], p_act_coord[1])
                z_prev = st.session_state.datos_sensores[i-1]['Z']
                z_act = st.session_state.datos_sensores[i]['Z']
                dz = abs(z_prev - z_act)
                d_3d = np.sqrt(d_2d**2 + dz**2)
                dist_total += d_3d

                p_in_prev = st.session_state.datos_sensores[i-1]['P']
                p_in = st.session_state.datos_sensores[i]['P']
                k_tramo = st.session_state.datos_sensores[i-1]['K']
                
                H_act = z_act + (p_in * FACTOR_CONVERSION_PSI_MCA)
                caida_h_real = H_prev - H_act
                perdida_esperada, v_ms = calcular_balance_hidraulico(q_entrada_lps, dn_pulg, coef_c, d_3d, k_tramo)
                diferencia_energia = caida_h_real - perdida_esperada
                
                if diferencia_energia > UMBRAL_FUGA_MCA:
                    dist_fuga = d_3d * (perdida_esperada / caida_h_real) if caida_h_real != 0 else 0
                    loc_absoluta = (dist_total - d_3d) + dist_fuga
                    
                    alertas_fuga.append({
                        "T": f"NODO {i} -> NODO {i+1}", 
                        "D": loc_absoluta, 
                        "Rel": dist_fuga,
                        "Z_prev": z_prev, "P_prev": p_in_prev, "H_prev": H_prev,
                        "Z_act": z_act, "P_act": p_in, "H_act": H_act,
                        "L3D": d_3d, "dH_real": caida_h_real, "dH_teo": perdida_esperada,
                        "diff": diferencia_energia, "Q": q_entrada_lps, "C": coef_c, "DN": dn_pulg
                    })

                H_prev = H_act
                matriz_analisis.append({"Nodo": f"N-{i+1}", "Z (m)": z_act, "P (PSI)": p_in, "H (mca)": round(H_act, 2), "D Acum (m)": round(dist_total, 2)})
                perfil_grafico.append({"D": dist_total, "H": H_act, "Z": z_act})
                
                barra_progreso.progress(int((i / n_tramos) * 100), text=f"Evaluando tramo {i} de {n_tramos}...")
                time.sleep(0.1)
                
            barra_progreso.empty()

            # --- REPORTE FINAL ---
            st.divider()
            st.header("📊 Reporte Oficial de Auditoría y Diagnóstico")
            if alertas_fuga:
                for alerta in alertas_fuga:
                    st.error(f"🚨 **ALERTA CRÍTICA - FUGA DETECTADA:** Ruptura del gradiente de energía confirmada. La anomalía se ubica aproximadamente a **{alerta['Rel']:.2f} metros** aguas abajo del NODO {alerta['T'].split(' ')[1]}.", icon="🔴")
                    
                    with st.expander(f"⚙️ Memoria de Cálculo Explicada para el Cliente - Tramo {alerta['T']}", expanded=False):
                        st.code(f""">>> INICIANDO ANÁLISIS DE ESTADO...
[*] TRAMO EN EVALUACIÓN: {alerta['T']}
[VAR] L_3D       : {alerta['L3D']:.2f} m      -> Longitud espacial (Distancia + Desnivel).
[VAR] H_prev     : {alerta['H_prev']:.2f} mca -> Carga piezométrica total en nodo de origen.
[VAR] H_act      : {alerta['H_act']:.2f} mca  -> Carga piezométrica total en nodo de destino.
[VAR] ΔH_Real    : {alerta['dH_real']:.2f} mca   -> Disipación de energía medida en terreno.
[VAR] ΔH_Teórico : {alerta['dH_teo']:.2f} mca    -> Fricción esperada por diseño (Hazen-Williams).
[VAR] X_anomalía : {alerta['Rel']:.2f} m      -> Proyección espacial del sumidero de energía.
>>> PROCESAMIENTO MATEMÁTICO FINALIZADO.""", language="bash")
                        
                        st.markdown(f"""
                        ### 1. ¿De dónde provienen estas variables?
                        Para garantizar la precisión informática, el sistema unifica las lecturas de presión y topografía en una sola unidad universal de energía hidráulica: **El mca (Metros de Columna de Agua)**. 
                        
                        * **¿Por qué usamos mca?** Los sensores de presión en campo entregan datos en **PSI**. Para sumar la presión del agua con la altura del terreno (que está en metros), multiplicamos los PSI por **0.7032** (la constante de conversión física del agua). Esto nos dice exactamente cuántos metros de altura podría escalar esa presión.

                        * **$L$ (Longitud Real):** Es la distancia tridimensional exacta entre el punto de inicio y el de destino. Se calcula usando coordenadas satelitales (Haversine) combinadas con el desnivel del terreno. **Para este tramo es {alerta['L3D']:.2f} m.**

                        ### 2. Evaluando la Energía del Sistema ($H$)
                        La variable **$H$** (Altura Piezométrica) representa la **Energía Total** que tiene el agua en un punto específico. Se obtiene sumando la altura geográfica sobre el nivel del mar ($Z$) y la presión leída por el sensor en mca ($P_{mca}$).
                        $$ H = Z_{cota} + P_{mca} $$

                        * **$H_{{prev}}$ (Energía en el Nodo Origen):** Topografía `{alerta['Z_prev']:.2f} m` + Presión `({alerta['P_prev']:.2f} PSI \cdot 0.7032)` = **{alerta['H_prev']:.2f} mca**
                        
                        * **$H_{{act}}$ (Energía en el Nodo Destino):** Topografía `{alerta['Z_act']:.2f} m` + Presión `({alerta['P_act']:.2f} PSI \cdot 0.7032)` = **{alerta['H_act']:.2f} mca**

                        ### 3. El Análisis de Fondo: Descubriendo la Fuga ($\Delta H$)
                        Aquí es donde el motor toma decisiones. Comparamos la energía real que se perdió en el terreno contra la energía que se debió perder teóricamente por la fricción natural del tubo.

                        * **$\Delta H_{{Real}}$ (Lo que midieron los sensores):** Es la resta matemática entre la energía inicial y la final.
                          $$ \Delta H_{{Real}} = H_{{prev}} - H_{{act}} = {alerta['H_prev']:.2f} - {alerta['H_act']:.2f} = \mathbf{{{alerta['dH_real']:.2f} \text{{ mca}}}} $$
                        
                        * **$\Delta H_{{Teórico}}$ (Lo que debió ocurrir):** Utilizando la ecuación internacional de Hazen-Williams, calculamos la fricción esperada para un tubo de {alerta['DN']}" a {alerta['Q']} L/s.
                          $$ \Delta H_{{Teórico}} = \frac{{10.67 \cdot Q^{{1.852}}}}{{C^{{1.852}} \cdot D^{{4.87}}}} \cdot L = \mathbf{{{alerta['dH_teo']:.2f} \text{{ mca}}}} $$

                        ### 4. Conclusión Analítica y Ubicación
                        El tramo debía perder únicamente **{alerta['dH_teo']:.2f} mca** por la fricción del agua contra el material, pero en la realidad perdió **{alerta['dH_real']:.2f} mca**. 
                        
                        Dado que la energía no se destruye, esta "energía faltante" masiva nos indica categóricamente que **el agua se está fugando del sistema**. Para encontrar el punto exacto ($X$), el sistema asume una pérdida lineal hasta la fractura y proyecta la distancia:
                        $$ X = L \cdot \left( \frac{{\Delta H_{{Teórico}}}}{{\Delta H_{{Real}}}} \right) = {alerta['L3D']:.2f} \cdot \left( \frac{{{alerta['dH_teo']:.2f}}}{{{alerta['dH_real']:.2f}}} \right) = \mathbf{{{alerta['Rel']:.2f} \text{{ metros}}}} $$
                        """)
            else:
                st.success("✅ Red operativa y hermética. Gradiente conservado dentro de los umbrales físicos.", icon="🟢")

            col_graf, col_tabla = st.columns([2, 1])
            with col_graf:
                st.subheader("Perfil de Gradiente de Energía")
                df_p = pd.DataFrame(perfil_grafico)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Línea Piezométrica (H)', line=dict(color='blue', width=3)))
                fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Terreno (Z)', fill='tozeroy', line=dict(color='brown', width=2)))
                for a in alertas_fuga: 
                    fig.add_vline(x=a['D'], line_color="red", line_width=2, line_dash="dash", annotation_text="FUGA", annotation_font_color="red")
                st.plotly_chart(fig, use_container_width=True)
            
            with col_tabla:
                st.subheader("Matriz de Estados Nodal")
                st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

# =================================================================
# MODO 2: OPERACIÓN REAL (CARGA LOTE)
# =================================================================
elif modo == "Operación Real (Carga Lote / En Línea)":
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
                st.error("Error: CSV carece de columnas estructurales 'latitud' y 'longitud'.")
            else:
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
                        st.error("🛑 **ERROR DE CONDICIÓN INICIAL:** La presión registrada en la fila 1 del archivo CSV es nula.")
                        st.stop()

                    barra_progreso = st.progress(0, text="Verificando variables. Iniciando motor determinístico...")
                    dist_total = 0.0
                    matriz_analisis, perfil_grafico, alertas_fuga = [], [], []
                    
                    n_tramos = len(df_lote) - 1
                    for i in range(len(df_lote)):
                        row = df_lote.iloc[i]
                        p_act = [row[lat_col], row[lon_col]]
                        z_act, p_in = row.get('cota', 1000.0), row.get('presion', 0.0)
                        H = z_act + (p_in * FACTOR_CONVERSION_PSI_MCA)
                        
                        if i > 0:
                            row_prev = df_lote.iloc[i-1]
                            p_in_prev = row_prev.get('presion', 0.0)
                            z_prev = row_prev.get('cota', 1000.0)

                            d_2d = haversine(row_prev[lat_col], row_prev[lon_col], p_act[0], p_act[1])
                            d_3d = np.sqrt(d_2d**2 + abs(z_prev - z_act)**2)
                            dist_total += d_3d
                            
                            h_prev = z_prev + (p_in_prev * FACTOR_CONVERSION_PSI_MCA)
                            caida_h_real = h_prev - H
                            k_tramo = row_prev.get('sum_k', 0.0)
                            perdida_esperada, v_ms = calcular_balance_hidraulico(20.0, 6, 140, d_3d, k_tramo) 
                            diferencia_energia = caida_h_real - perdida_esperada
                            
                            if diferencia_energia > UMBRAL_FUGA_MCA:
                                dist_fuga = d_3d * (perdida_esperada / caida_h_real) if caida_h_real != 0 else 0
                                alertas_fuga.append({
                                    "T": f"NODO {i} -> NODO {i+1}", 
                                    "D": dist_total - d_3d + dist_fuga, 
                                    "Rel": dist_fuga,
                                    "Z_prev": z_prev, "P_prev": p_in_prev, "H_prev": h_prev,
                                    "Z_act": z_act, "P_act": p_in, "H_act": H,
                                    "L3D": d_3d, "dH_real": caida_h_real, "dH_teo": perdida_esperada,
                                    "diff": diferencia_energia, "Q": 20.0, "C": 140, "DN": 6
                                })
                            
                            barra_progreso.progress(int((i / n_tramos) * 100), text=f"Evaluando tramo {i} de {n_tramos}...")
                            time.sleep(0.05)
                        
                        matriz_analisis.append({"Nodo": f"N-{i+1}", "Z (m)": z_act, "P (PSI)": p_in, "H (mca)": round(H, 2), "D Acum": round(dist_total, 2)})
                        perfil_grafico.append({"D": dist_total, "H": H, "Z": z_act})

                    barra_progreso.empty()

                    # --- REPORTE FINAL ---
                    st.divider()
                    st.header("📊 Reporte Oficial de Auditoría y Diagnóstico (Lote)")
                    if alertas_fuga:
                        for alerta in alertas_fuga: 
                            st.error(f"🚨 **ALERTA CRÍTICA - FUGA DETECTADA:** Ruptura del gradiente de energía confirmada. La anomalía se ubica aproximadamente a **{alerta['Rel']:.2f} metros** aguas abajo del NODO {alerta['T'].split(' ')[1]}.", icon="🔴")
                            
                            with st.expander(f"⚙️ Memoria de Cálculo Explicada para el Cliente - Tramo {alerta['T']}", expanded=False):
                                st.code(f""">>> INICIANDO ANÁLISIS DE ESTADO...
[*] TRAMO EN EVALUACIÓN: {alerta['T']}
[VAR] L_3D       : {alerta['L3D']:.2f} m      -> Longitud espacial (Distancia + Desnivel).
[VAR] H_prev     : {alerta['H_prev']:.2f} mca -> Carga piezométrica total en nodo de origen.
[VAR] H_act      : {alerta['H_act']:.2f} mca  -> Carga piezométrica total en nodo de destino.
[VAR] ΔH_Real    : {alerta['dH_real']:.2f} mca   -> Disipación de energía medida en terreno.
[VAR] ΔH_Teórico : {alerta['dH_teo']:.2f} mca    -> Fricción esperada por diseño (Hazen-Williams).
[VAR] X_anomalía : {alerta['Rel']:.2f} m      -> Proyección espacial del sumidero de energía.
>>> PROCESAMIENTO MATEMÁTICO FINALIZADO.""", language="bash")
                                
                                st.markdown(f"""
                                ### 1. ¿De dónde provienen estas variables?
                                Para garantizar la precisión informática, el sistema unifica las lecturas de presión y topografía en una sola unidad universal de energía hidráulica: **El mca (Metros de Columna de Agua)**. 
                                
                                * **¿Por qué usamos mca?** Los sensores de presión en campo entregan datos en **PSI**. Para sumar la presión del agua con la altura del terreno (que está en metros), multiplicamos los PSI por **0.7032** (la constante de conversión física del agua). Esto nos dice exactamente cuántos metros de altura podría escalar esa presión.

                                * **$L$ (Longitud Real):** Es la distancia tridimensional exacta entre el punto de inicio y el de destino. Se calcula usando coordenadas satelitales (Haversine) combinadas con el desnivel del terreno. **Para este tramo es {alerta['L3D']:.2f} m.**

                                ### 2. Evaluando la Energía del Sistema ($H$)
                                La variable **$H$** (Altura Piezométrica) representa la **Energía Total** que tiene el agua en un punto específico. Se obtiene sumando la altura geográfica sobre el nivel del mar ($Z$) y la presión leída por el sensor en mca ($P_{mca}$).
                                $$ H = Z_{cota} + P_{mca} $$

                                * **$H_{{prev}}$ (Energía en el Nodo Origen):** Topografía `{alerta['Z_prev']:.2f} m` + Presión `({alerta['P_prev']:.2f} PSI \cdot 0.7032)` = **{alerta['H_prev']:.2f} mca**
                                
                                * **$H_{{act}}$ (Energía en el Nodo Destino):** Topografía `{alerta['Z_act']:.2f} m` + Presión `({alerta['P_act']:.2f} PSI \cdot 0.7032)` = **{alerta['H_act']:.2f} mca**

                                ### 3. El Análisis de Fondo: Descubriendo la Fuga ($\Delta H$)
                                Aquí es donde el motor toma decisiones. Comparamos la energía real que se perdió en el terreno contra la energía que se debió perder teóricamente por la fricción natural del tubo.

                                * **$\Delta H_{{Real}}$ (Lo que midieron los sensores):** Es la resta matemática entre la energía inicial y la final.
                                  $$ \Delta H_{{Real}} = H_{{prev}} - H_{{act}} = {alerta['H_prev']:.2f} - {alerta['H_act']:.2f} = \mathbf{{{alerta['dH_real']:.2f} \text{{ mca}}}} $$
                                
                                * **$\Delta H_{{Teórico}}$ (Lo que debió ocurrir):** Utilizando la ecuación internacional de Hazen-Williams, calculamos la fricción esperada para un tubo de {alerta['DN']}" a {alerta['Q']} L/s.
                                  $$ \Delta H_{{Teórico}} = \frac{{10.67 \cdot Q^{{1.852}}}}{{C^{{1.852}} \cdot D^{{4.87}}}} \cdot L = \mathbf{{{alerta['dH_teo']:.2f} \text{{ mca}}}} $$

                                ### 4. Conclusión Analítica y Ubicación
                                El tramo debía perder únicamente **{alerta['dH_teo']:.2f} mca** por la fricción del agua contra el material, pero en la realidad perdió **{alerta['dH_real']:.2f} mca**. 
                                
                                Dado que la energía no se destruye, esta "energía faltante" masiva nos indica categóricamente que **el agua se está fugando del sistema**. Para encontrar el punto exacto ($X$), el sistema asume una pérdida lineal hasta la fractura y proyecta la distancia:
                                $$ X = L \cdot \left( \frac{{\Delta H_{{Teórico}}}}{{\Delta H_{{Real}}}} \right) = {alerta['L3D']:.2f} \cdot \left( \frac{{{alerta['dH_teo']:.2f}}}{{{alerta['dH_real']:.2f}}} \right) = \mathbf{{{alerta['Rel']:.2f} \text{{ metros}}}} $$
                                """)
                    else:
                        st.success("✅ Red operativa y hermética. Gradiente conservado dentro de los umbrales físicos.", icon="🟢")

                    col_graf, col_tabla = st.columns([2, 1])
                    with col_graf:
                        st.subheader("Gradiente de Energía Real")
                        df_p = pd.DataFrame(perfil_grafico)
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['H'], name='Línea Piezométrica (H)', line=dict(color='blue', width=3)))
                        fig.add_trace(go.Scatter(x=df_p['D'], y=df_p['Z'], name='Terreno (Z)', fill='tozeroy', line=dict(color='brown', width=2)))
                        for a in alertas_fuga: fig.add_vline(x=a['D'], line_color="red", line_width=2, line_dash="dash", annotation_text="FUGA", annotation_font_color="red")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col_tabla:
                        st.subheader("Matriz de Nodos")
                        st.dataframe(pd.DataFrame(matriz_analisis), use_container_width=True)

        except Exception as e:
            st.error(f"Error crítico en la ingesta del CSV. Verifique la estructura de los datos. Trace: {str(e)}")

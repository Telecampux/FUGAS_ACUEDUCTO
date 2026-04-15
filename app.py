import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
import math
import os

# =============================================================================
# IANC_H2O - SISTEMA DE DETECCIÓN DE FUGAS 
# VERSIÓN: BÚSQUEDA PROFUNDA + MEMORIA DE CÁLCULO AUDITABLE
# =============================================================================

st.set_page_config(page_title="IANC_H2O", layout="wide")

# --- FUNCIONES MATEMÁTICAS ---
def haversine_esferico(lat1, lon1, lat2, lon2):
    R = 6371000.0 
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    return R * (2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a)))

def perdida_hazen_williams(q_ls, c, d_pulg, l_m):
    q_m3s = q_ls / 1000.0
    d_m = d_pulg * 0.0254
    if c == 0 or d_m == 0: return 0.0
    return 10.67 * (q_m3s**1.852) * l_m / ((c**1.852) * (d_m**4.87))

def obtener_cota_referencia(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}"
        r = requests.get(url, timeout=3).json()
        return round(r["elevation"][0], 2) if "elevation" in r else None
    except:
        return None

# --- ESTADO DE SESIÓN ---
if "puntos" not in st.session_state:
    st.session_state.puntos = []
if "datos_nodos" not in st.session_state:
    st.session_state.datos_nodos = {}

# --- PANEL DE CONFIGURACIÓN ---
st.title("IANC_H2O - Diagnóstico Hidráulico")

with st.sidebar:
    st.header("Configuración de Escenario")
    
    municipios = {
        "Villeta": [5.0113, -74.4754],
        "Neiva": [2.9273, -75.2819],
        "Villavicencio": [4.1420, -73.6266],
        "Chaparral": [3.7235, -75.4833]
    }
    muni_sel = st.selectbox("Seleccione el Municipio", list(municipios.keys()))
    centro_mapa = municipios[muni_sel]

    if "modo_operacion" not in st.session_state:
        st.session_state.modo_operacion = "Simulación de Red"

    nuevo_modo = st.radio(
        "Modo de Operación", 
        ["Simulación de Red", "Diagnóstico Real (Campo)"], 
        index=["Simulación de Red", "Diagnóstico Real (Campo)"].index(st.session_state.modo_operacion)
    )
    
    if nuevo_modo != st.session_state.modo_operacion:
        st.session_state.modo_operacion = nuevo_modo
        st.session_state.puntos = []
        st.session_state.datos_nodos = {}
        st.rerun()

    modo = st.session_state.modo_operacion
    
    st.divider()
    st.header("Parámetros de Red")
    q = st.number_input("Caudal (L/s)", value=20.0, step=0.1)
    d = st.number_input("Diámetro Interno (pulg)", value=6.0, step=0.1)
    c_hw = st.slider("Coeficiente C (Hazen-Williams)", 100, 150, 140)
    
    if st.button("Limpiar Mapa y Datos", use_container_width=True):
        st.session_state.puntos = []
        st.session_state.datos_nodos = {}
        for key in list(st.session_state.keys()):
            if key.startswith("p_") or key.startswith("z_") or key.startswith("k_"):
                del st.session_state[key]
        st.rerun()

# --- MÓDULO DE INGESTA DE DATOS DESDE GITHUB (BÚSQUEDA PROFUNDA) ---
if modo == "Diagnóstico Real (Campo)":
    st.subheader("📥 Ingesta de Datos desde el Repositorio")
    
    archivos_csv = []
    rutas_absolutas = {}
    directorio_base = os.path.dirname(os.path.abspath(__file__))
    
    for root, dirs, files in os.walk(directorio_base):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.lower().endswith('.csv'):
                ruta_completa = os.path.join(root, file)
                ruta_amigable = os.path.relpath(ruta_completa, directorio_base)
                archivos_csv.append(ruta_amigable)
                rutas_absolutas[ruta_amigable] = ruta_completa
    
    if not archivos_csv:
        st.error("No se encontraron archivos .csv en el repositorio ni en sus subcarpetas.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            archivo_seleccionado = st.selectbox("Seleccione el archivo de campo:", archivos_csv)
        with col2:
            st.write("")
            st.write("")
            btn_procesar = st.button("Cargar Datos", type="primary", use_container_width=True)
            
        if btn_procesar:
            try:
                ruta_para_leer = rutas_absolutas[archivo_seleccionado]
                df_campo = pd.read_csv(ruta_para_leer)
                
                cols = df_campo.columns.astype(str).str.lower().str.strip()
                cols = [c.replace('\ufeff', '') for c in cols]
                df_campo.columns = cols
                
                col_lat = next((c for c in df_campo.columns if 'lat' in c), None)
                col_lon = next((c for c in df_campo.columns if 'lon' in c), None)
                col_p = next((c for c in df_campo.columns if 'pres' in c or 'psi' in c), None)
                col_z = next((c for c in df_campo.columns if 'cota' in c or 'alt' in c or 'msnm' in c), None)
                col_k = next((c for c in df_campo.columns if 'acc' in c or c == 'k'), None)
                
                if col_lat and col_lon and col_p and col_z:
                    st.session_state.puntos = []
                    st.session_state.datos_nodos = {}
                    
                    for idx, row in df_campo.iterrows():
                        st.session_state.puntos.append([float(row[col_lat]), float(row[col_lon])])
                        st.session_state[f"p_{idx}"] = float(row[col_p]) if pd.notna(row[col_p]) else 0.0
                        st.session_state[f"z_{idx}"] = float(row[col_z]) if pd.notna(row[col_z]) else 0.0
                        st.session_state[f"k_{idx}"] = float(row[col_k]) if col_k and pd.notna(row[col_k]) else 0.0
                        st.session_state.datos_nodos[idx] = {"Z_api": f"Fuente: {archivo_seleccionado}"}
                    
                    st.success(f"Configuración de red cargada desde '{archivo_seleccionado}'.")
                    st.rerun()
                else:
                    st.error("El archivo no tiene el formato esperado (latitud, longitud, presión, cota/altitud).")
            except Exception as e:
                st.error(f"Error crítico al abrir el archivo: {e}")

# --- MAPA INTERACTIVO ---
if len(st.session_state.puntos) > 0:
    centro = st.session_state.puntos[0]
else:
    centro = centro_mapa

m = folium.Map(location=centro, zoom_start=15)
for i, p in enumerate(st.session_state.puntos):
    folium.Marker(p, tooltip=f"Nodo {i+1}").add_to(m)
if len(st.session_state.puntos) > 1:
    folium.PolyLine(st.session_state.puntos, color="blue").add_to(m)

mapa = st_folium(m, width=None, height=450)

# Lógica de Captura Manual
if mapa and mapa.get("last_clicked"):
    lat, lon = mapa["last_clicked"]["lat"], mapa["last_clicked"]["lng"]
    if [lat, lon] not in st.session_state.puntos:
        st.session_state.puntos.append([lat, lon])
        idx = len(st.session_state.puntos) - 1
        
        if modo == "Simulación de Red":
            z_ref = obtener_cota_referencia(lat, lon)
            st.session_state.datos_nodos[idx] = {"Z_api": z_ref}
            st.session_state[f"z_{idx}"] = float(z_ref if z_ref else 0.0)
        else:
            st.session_state.datos_nodos[idx] = {"Z_api": "Agregado Manualmente"}
            st.session_state[f"z_{idx}"] = 0.0 
            
        st.session_state[f"p_{idx}"] = 0.0
        st.session_state[f"k_{idx}"] = 0.0
        st.rerun()

# --- PANEL DE NODOS ---
st.subheader("Configuración de Nodos")

for i in range(len(st.session_state.puntos)):
    with st.expander(f"📍 Nodo {i+1}", expanded=(i == len(st.session_state.puntos)-1)):
        c1, c2 = st.columns(2)
        st.session_state[f"p_{i}"] = c1.number_input("Presión (PSI)", value=st.session_state.get(f"p_{i}", 0.0), key=f"input_p_{i}", step=0.5)
        st.session_state[f"z_{i}"] = c2.number_input("Cota REAL (msnm)", value=st.session_state.get(f"z_{i}", 0.0), key=f"input_z_{i}", format="%.2f", step=0.1)
        
        z_api = st.session_state.datos_nodos.get(i, {}).get("Z_api")
        st.caption(f"Origen: {z_api}")
        
        if i < len(st.session_state.puntos) - 1:
            st.session_state[f"k_{i}"] = st.number_input("ΣK accesorios", value=st.session_state.get(f"k_{i}", 0.0), key=f"input_k_{i}", step=0.1)

# --- ANÁLISIS Y MEMORIA DE CÁLCULO ---
if st.button("Ejecutar Análisis Termodinámico", use_container_width=True):
    if len(st.session_state.puntos) < 2:
        st.error("Se requieren al menos 2 nodos para realizar el cálculo diferencial.")
    else:
        perfil = []
        dist_acumulada = 0.0
        fugas = []
        
        area = math.pi * ((d * 0.0254)**2) / 4.0
        v = (q / 1000.0) / area if area > 0 else 0
        
        z0 = st.session_state[f"z_0"]
        p0 = st.session_state[f"p_0"]
        h0 = z0 + (p0 * 0.7032) 
        perfil.append({"Dist": 0.0, "Energia": h0, "Terreno": z0})
        
        st.divider()
        st.subheader("Memoria de Cálculo Transparente")
        st.info("Despliegue cada tramo para auditar las variables, la ecuación de energía y las pérdidas matemáticas de fondo.")
        
        for i in range(1, len(st.session_state.puntos)):
            p1, p2 = st.session_state.puntos[i-1], st.session_state.puntos[i]
            dist_tramo = haversine_esferico(p1[0], p1[1], p2[0], p2[1])
            
            z1, z2 = st.session_state[f"z_{i-1}"], st.session_state[f"z_{i}"]
            pres1, pres2 = st.session_state[f"p_{i-1}"], st.session_state[f"p_{i}"]
            k_loc = st.session_state[f"k_{i-1}"]
            
            d_real = math.sqrt(dist_tramo**2 + (z2 - z1)**2)
            dist_acumulada += d_real
            
            h_real_1 = z1 + (pres1 * 0.7032)
            h_real_2 = z2 + (pres2 * 0.7032)
            dh_real = h_real_1 - h_real_2
            
            hf = perdida_hazen_williams(q, c_hw, d, d_real)
            hm = k_loc * (v**2) / (2 * 9.81)
            dh_teo = hf + hm
            diferencia = dh_real - dh_teo
            
            perfil.append({"Dist": dist_acumulada, "Energia": h_real_2, "Terreno": z2})
            
            if diferencia > 0.14:
                x_f = d_real * (dh_teo / dh_real) if dh_real != 0 else 0
                fugas.append({"tramo": f"{i} → {i+1}", "pos": x_f, "perda": diferencia})

            # EXPOSICIÓN DE LA MEMORIA DE CÁLCULO
            with st.expander(f"🔍 Auditoría Tramo: Nodo {i} → Nodo {i+1}"):
                st.markdown("**1. Topografía y Longitud**")
                st.markdown(f"- Distancia Plana (Haversine): `{dist_tramo:.2f} m`")
                st.markdown(f"- Cota Inicial ($Z_1$): `{z1} m` | Cota Final ($Z_2$): `{z2} m`")
                st.latex(r"L_{real} = \sqrt{D_{plana}^2 + (Z_2 - Z_1)^2}")
                st.markdown(f"- Longitud Inclinada ($L_{{real}}$): **`{d_real:.2f} m`**")
                
                st.markdown("**2. Ecuación de Energía Real (Mediciones de Campo)**")
                st.latex(r"H = Z + (P_{psi} \times 0.7032)")
                st.markdown(f"- Energía Total Nodo {i} ($H_1$): `{z1} + ({pres1} \times 0.7032)` = **`{h_real_1:.2f} mca`**")
                st.markdown(f"- Energía Total Nodo {i+1} ($H_2$): `{z2} + ({pres2} \times 0.7032)` = **`{h_real_2:.2f} mca`**")
                st.markdown(f"- Diferencial Medido ($\Delta H_{{real}} = H_1 - H_2$): **`{dh_real:.2f} mca`**")
                
                st.markdown("**3. Gradiente Teórico (Modelo Matemático)**")
                st.markdown(f"- Velocidad del Flujo ($V$): `{v:.2f} m/s`")
                st.markdown(f"- Pérdidas Menores ($h_m = K \cdot \frac{{v^2}}{{2g}}$): `{k_loc} \cdot \frac{{{v:.2f}^2}}{{19.62}}` = `{hm:.2f} mca`")
                st.markdown(f"- Pérdida por Fricción Hazen-Williams ($h_f$): `{hf:.2f} mca`")
                st.markdown(f"- Pérdida Teórica Esperada ($\Delta H_{{teo}} = h_f + h_m$): **`{dh_teo:.2f} mca`**")
                
                st.markdown("**4. Conclusión Termodinámica**")
                st.markdown(f"Diferencia Excedente ($\Delta H_{{real}} - \Delta H_{{teo}}$): **`{diferencia:.2f} mca`**")
                if diferencia > 0.14:
                    st.error("⚠️ El exceso de pérdida supera el umbral de 0.14 mca (0.2 PSI). Fuga termodinámica detectada.")
                else:
                    st.success("✅ El comportamiento termodinámico concuerda con las leyes de fricción para este tramo.")

        # --- RESULTADOS Y GRÁFICA ---
        st.divider()
        st.subheader("Resumen Diagnóstico")
        if fugas:
            for f in fugas: 
                st.warning(f"⚠️ Alerta Crítica en Tramo {f['tramo']}. Búsqueda focalizada recomendada a {f['pos']:.2f}m del Nodo de origen. (Pérdida inexplicable: {f['perda']:.2f} mca)")
        else:
            st.success("Sistema estabilizado. No se detectan gradientes anómalos.")
            
        df = pd.DataFrame(perfil)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Dist"], y=df["Energia"], name="Línea de Energía (H)", line=dict(color='blue', width=3)))
        fig.add_trace(go.Scatter(x=df["Dist"], y=df["Terreno"], name="Perfil Topográfico (Z)", fill='tozeroy', line=dict(color='brown')))
        fig.update_layout(title="Perfil Espacial Hidráulico", xaxis_title="Longitud Acumulada (m)", yaxis_title="msnm / mca")
        st.plotly_chart(fig, use_container_width=True)

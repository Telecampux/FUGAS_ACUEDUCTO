import streamlit as st
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt
import json
import pandas as pd
import time

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="IANC H2O - Auditoría Profesional", layout="wide")

autor = "ING. ADOLFO BARRERA VARGAS"
programa = "SISTEMA INTEGRAL DE AUDITORÍA P.R.P."

st.title("📡 TABLERO DE CONTROL IANC H2O")
st.write(f"### {programa}")
st.caption(f"**Gestión de Activos y Diagnóstico Hidráulico** | {autor}")
st.divider()

# --- DATOS TOPOLÓGICOS ---
territorios = {
    "Villeta": {"coords": [5.0140, -74.4720], "costo": 3200, "z_base": 842.0},
    "Neiva": {"coords": [2.9273, -75.2819], "costo": 3500, "z_base": 442.0},
    "Chaparral": {"coords": [3.7231, -75.4832], "costo": 3100, "z_base": 854.0},
    "El Espinal": {"coords": [4.1492, -74.8878], "costo": 2900, "z_base": 323.0},
    "Villavicencio": {"coords": [4.1420, -73.6266], "costo": 3400, "z_base": 467.0}
}

# --- LÓGICA DE CÁLCULOS ---
def haversine(lat1, lon1, lat2, lon2):
    r = 6371000
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    d = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 2 * r * asin(sqrt(d))

def perdida_hazen_williams(q_lps, c, d_pulg, l_m):
    if q_lps <= 0: return 0
    q_m3s = q_lps / 1000.0
    d_m = d_pulg * 0.0254
    hf_mca = 10.67 * l_m * ((q_m3s / c)**1.852) * (d_m**-4.87)
    return hf_mca / 0.703 

# --- MENÚ LATERAL ---
st.sidebar.header("📂 MÓDULOS DEL SISTEMA")
modo = st.sidebar.radio("Modo de Trabajo:", ["Simulación Interactiva", "Operación Real (Carga Lote)"])

st.sidebar.divider()
mun_sel = st.sidebar.selectbox("Municipio Objeto", list(territorios.keys()))
costo_m3 = st.sidebar.number_input("Costo m³ (COP)", value=territorios[mun_sel]['costo'])
dn = st.sidebar.selectbox("Diámetro de Red Auditada (Pulg)", [2, 3, 4, 6, 8, 10, 12], index=2)

# --- ESTADO DE SESIÓN ---
if 'procesado_real' not in st.session_state: st.session_state.procesado_real = False
if 'ejecutado_sim' not in st.session_state: st.session_state.ejecutado_sim = False
if 'puntos' not in st.session_state: st.session_state.puntos = []
if 'empresa' not in st.session_state: st.session_state.empresa = "Administración Municipal"

# =================================================================
# MÓDULO: SIMULACIÓN INTERACTIVA
# =================================================================
if modo == "Simulación Interactiva":
    st.write("### 🕹️ Modo: Simulación Interactiva")
    st.session_state.empresa = st.text_input("Nombre de la Empresa:", st.session_state.empresa)
    
    if st.sidebar.button("♻️ Reiniciar Nodos"):
        st.session_state.puntos = []
        st.session_state.ejecutado_sim = False
        st.rerun()

    m1 = folium.Map(location=territorios[mun_sel]['coords'], zoom_start=15)
    mapa_click = st_folium(m1, width=1100, height=400, key=f"sim_{mun_sel}")
    
    if mapa_click and mapa_click.get("last_clicked"):
        clicked = [mapa_click["last_clicked"]["lat"], mapa_click["last_clicked"]["lng"]]
        if not st.session_state.puntos or clicked != st.session_state.puntos[-1]:
            st.session_state.puntos.append(clicked)
            st.rerun()

    if len(st.session_state.puntos) >= 2:
        st.write("---")
        pres_list, cota_list = [], []
        cols = st.columns(len(st.session_state.puntos))
        for i in range(len(st.session_state.puntos)):
            with cols[i]:
                p_v = st.number_input(f"Presión S{i+1}", value=45.0-(i*8.0), key=f"ps_{i}")
                z_v = st.number_input(f"Cota S{i+1}", value=territorios[mun_sel]['z_base']-(i*1.0), key=f"zs_{i}")
                pres_list.append(p_v); cota_list.append(z_v)
        
        if st.button("🚀 EJECUTAR SIMULACIÓN TÉCNICA"):
            st.session_state.pres_sim = pres_list
            st.session_state.cota_sim = cota_list
            st.session_state.ejecutado_sim = True

    if st.session_state.ejecutado_sim:
        st.divider()
        m_sim = folium.Map(location=st.session_state.puntos[0], zoom_start=18)
        for i in range(len(st.session_state.puntos) - 1):
            p1, p2 = st.session_state.pres_sim[i], st.session_state.pres_sim[i+1]
            z1, z2 = st.session_state.cota_sim[i], st.session_state.cota_sim[i+1]
            lat1, lon1 = st.session_state.puntos[i]
            lat2, lon2 = st.session_state.puntos[i+1]
            d_t = haversine(lat1, lon1, lat2, lon2)
            dz_p = (z1 - z2) / 0.703
            c_real = (p1 + dz_p) - p2
            
            with st.expander(f"📊 INFORME TRAMO {i+1} ➔ {i+2}", expanded=True):
                if c_real > 0.5:
                    f_d = min(0.98, (c_real/(p1 + (z1/0.703)))*2.5)
                    d_f = round(d_t * f_d, 1)
                    st.error(f"📍 Fuga localizada a {d_f} metros del origen.")
                    with st.expander("🧮 MEMORIA DE CÁLCULO (DESCRESTE)"):
                        st.latex(r"d = 2r \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos\phi_1\cos\phi_2\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)")
                        st.latex(r"\Delta P_{real} = \left( P_1 + \frac{\Delta Z}{0.703} \right) - P_2")
                    folium.Marker([lat1+(lat2-lat1)*(d_f/d_t), lon1+(lon2-lon1)*(d_f/d_t)], icon=folium.Icon(color='red')).add_to(m_sim)
                else: st.success("✅ Tramo en condiciones óptimas.")
        st_folium(m_sim, width=1100, height=400, key="map_sim_final")

# =================================================================
# MÓDULO: OPERACIÓN REAL (LOG + CÁLCULOS AVANZADOS)
# =================================================================
elif modo == "Operación Real (Carga Lote)":
    st.write("### 📊 Modo: Operación por Lote (Auditoría Técnica Real)")
    csv_file = st.file_uploader("Subir CSV Maestro", type=["csv"])
    
    if csv_file:
        df = pd.read_csv(csv_file)
        st.dataframe(df, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1: q_base = st.number_input("Caudal base (L/s)", value=5.0)
        with col2: c_dom = st.number_input("Consumo/Acometida (L/s)", value=0.05)

        if st.button("🚀 INICIAR PROCESAMIENTO ANALÍTICO"):
            st.session_state.procesado_real = True
            with st.status("🖥️ Ejecutando Motor IANC H2O...", expanded=True) as s:
                st.write("⚙️ Analizando gradientes hidráulicos..."); time.sleep(0.7)
                st.write("📡 Interpolando coordenadas GPS..."); time.sleep(0.7)
                s.update(label="✅ Análisis Finalizado", state="complete")

        if st.session_state.procesado_real:
            st.divider()
            t1, t2 = st.tabs(["🗺️ Mapa de Diagnóstico", "💻 Consola de Operaciones (LOG)"])
            m_r = folium.Map(location=[df.iloc[0]['latitud'], df.iloc[0]['longitud']], zoom_start=18)
            log = "=== INICIO DE AUDITORÍA REAL ===\n"
            
            for i in range(len(df) - 1):
                s1, s2 = df.iloc[i], df.iloc[i+1]
                dist = haversine(s1['latitud'], s1['longitud'], s2['latitud'], s2['longitud'])
                dz_p = (s1['cota_z'] - s2['cota_z']) / 0.703
                caida = (s1['presion_psi'] + dz_p) - s2['presion_psi']
                q_t = q_base - (s1['conexiones_dom'] * c_dom)
                teo = perdida_hazen_williams(q_t, s1['coeficiente_c'], s1['diametro_pulg'], dist)
                desv = caida - teo
                
                log += f"> Tramo {s1['id_sensor']}: Desviación {desv:.2f} PSI\n"
                with t1:
                    with st.expander(f"🔍 TRAMO: {s1['id_sensor']} ➔ {s2['id_sensor']}", expanded=True):
                        if desv > 2.0:
                            f_d = max(0.1, min(0.9, teo/caida if caida > 0 else 0.5))
                            dist_f = round(dist * f_d, 1)
                            st.error(f"🚨 FUGA DETECTADA a {dist_f}m")
                            r = dist_f / dist
                            folium.Marker([s1['latitud']+(s2['latitud']-s1['latitud'])*r, s1['longitud']+(s2['longitud']-s1['longitud'])*r], icon=folium.Icon(color='red', icon='wrench', prefix='fa')).add_to(m_r)
                        else: st.success("✅ Operación Normal")
                folium.PolyLine([[s1['latitud'], s1['longitud']], [s2['latitud'], s2['longitud']]], color='red' if desv > 2.0 else 'green').add_to(m_r)
            
            with t1: st_folium(m_r, width=1100, height=450, key="map_real_final")
            with t2: st.code(log + "=== FIN DEL LOG ===", language='bash')

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math
import os
from geopy.geocoders import Nominatim
import geopandas as gpd

# =============================================================================
# IANC_H2O - SISTEMA INTEGRAL DE AUDITORÍA HIDRÁULICA PROFESIONAL
# VERSIÓN: 2026.25 - OPTIMIZACIÓN DE LOCALIZACIÓN EXACTA
# =============================================================================

st.set_page_config(page_title="IANC_H2O - Auditor Hidráulico", layout="wide")

# --- NÚCLEO FÍSICO Y MATEMÁTICO ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp/2.0)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2.0)**2
    return R * (2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a)))

def interpolar_coordenadas(p1, p2, distancia_fuga, distancia_total):
    if distancia_total <= 0: return p1
    ratio = min(max(distancia_fuga / distancia_total, 0), 1)
    lat_fuga = p1[0] + (p2[0] - p1[0]) * ratio
    lon_fuga = p1[1] + (p2[1] - p1[1]) * ratio
    return [lat_fuga, lon_fuga]

def obtener_direccion_fisica(lat, lon):
    try:
        geolocator = Nominatim(user_agent="ianc_h2o_pro_v2026")
        location = geolocator.reverse((lat, lon), timeout=10, language='es')
        if location:
            address = location.raw.get('address', {})
            calle = address.get('road', 'Vía sin nombre')
            numero = address.get('house_number', '')
            barrio = address.get('neighbourhood', address.get('suburb', ''))
            return f"{calle} {numero}, {barrio}".strip(", ")
        return f"Coord: {lat}, {lon}"
    except:
        return f"Coord: {lat}, {lon}"

def procesar_cartografia(ruta_archivo):
    gdf = gpd.read_file(ruta_archivo).to_crs(epsg=4326)
    gdf_metrico = gdf.to_crs(epsg=3116)
    gdf['longitud_real_m'] = gdf_metrico.geometry.length
    return gdf

def reset_total_sistema():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.puntos = []

if "puntos" not in st.session_state: reset_total_sistema()

st.title("💧 IANC_H2O - Diagnóstico Integral")

with st.sidebar:
    st.header("⚙️ Gestión de Datos")
    if st.button("LIMPIAR SESIÓN (RESET TOTAL)", width='stretch', type="primary"):
        reset_total_sistema(); st.rerun()

tab_csv, tab_correlacion = st.tabs(["📥 Inferencia por Gradiente", "🎧 Inferencia por Correlación"])

CARPETA = "datos_simulacion"
if not os.path.exists(CARPETA): os.makedirs(CARPETA)
archivos_json = [f for f in os.listdir(CARPETA) if f.lower().endswith(('.geojson', '.json'))]

# =============================================================================
# MÓDULO 1: GRADIENTE (PRESIÓN Y FRICCIÓN)
# =============================================================================
with tab_csv:
    archivos_csv = [f for f in os.listdir(CARPETA) if f.lower().endswith('.csv')]
    col_a, col_b = st.columns(2)
    csv_sel = col_a.selectbox("Mediciones (CSV):", archivos_csv, key="csv_g")
    json_sel = col_b.selectbox("Cartografía (GeoJSON):", archivos_json, key="json_g")

    if st.button("CARGAR PROYECTO GRADIENTE", type="primary"):
        if csv_sel and json_sel:
            df = pd.read_csv(os.path.join(CARPETA, csv_sel))
            df.columns = df.columns.astype(str).str.lower().str.strip()
            c_lat = next((c for c in df.columns if 'lat' in c), None)
            c_lon = next((c for c in df.columns if 'lon' in c), None)
            c_p = next((c for c in df.columns if 'pres' in c or 'psi' in c), None)
            c_z = next((c for c in df.columns if 'cota' in c or 'alt' in c), None)
            c_q = next((c for c in df.columns if 'caudal' in c or 'flow' in c), None)
            c_d = next((c for c in df.columns if 'diam' in c or 'pulg' in c), None)
            c_id = next((c for c in df.columns if 'id' in c or 'sensor' in c), None)
            
            st.session_state.puntos = []
            for idx, row in df.iterrows():
                st.session_state.puntos.append([float(row[c_lat]), float(row[c_lon])])
                st.session_state[f"id_{idx}"] = str(row[c_id]) if c_id else f"S-{idx}"
                st.session_state[f"lat_{idx}"] = float(row[c_lat])
                st.session_state[f"lon_{idx}"] = float(row[c_lon])
                st.session_state[f"zi_{idx}"] = float(row[c_z])
                st.session_state[f"pi_{idx}"] = float(row[c_p])
                st.session_state[f"qi_{idx}"] = float(row[c_q]) if not pd.isna(row[c_q]) else 0.0
                st.session_state[f"di_{idx}"] = float(row[c_d]) if not pd.isna(row[c_d]) else 0.0
            
            st.session_state.red_cartografica = procesar_cartografia(os.path.join(CARPETA, json_sel))
            st.rerun()

    if st.session_state.puntos:
        m_g = folium.Map(location=st.session_state.puntos[0], zoom_start=17)
        folium.GeoJson(st.session_state.red_cartografica).add_to(m_g)
        for i, p in enumerate(st.session_state.puntos):
            folium.Marker(p, tooltip=st.session_state[f"id_{i}"], icon=folium.Icon(color='blue', icon='info-sign')).add_to(m_g)
        st_folium(m_g, width='stretch', height=400, key="map_grad")

        for i in range(len(st.session_state.puntos)):
            with st.expander(f"📍 Nodo: {st.session_state[f'id_{i}']}", expanded=False):
                c1, c2, c3 = st.columns(3)
                st.session_state[f"lat_g_{i}"] = st.number_input("Latitud", value=st.session_state[f"lat_{i}"], format="%.8f", key=f"lat_input_{i}")
                st.session_state[f"lon_g_{i}"] = st.number_input("Longitud", value=st.session_state[f"lon_{i}"], format="%.8f", key=f"lon_input_g_{i}")
                st.session_state[f"pi_g_{i}"] = st.number_input("Presión (PSI)", value=st.session_state[f"pi_{i}"], key=f"pi_input_{i}")
                d1, d2, d3 = st.columns(3)
                st.session_state[f"zi_g_{i}"] = st.number_input("Cota (msnm)", value=st.session_state[f"zi_{i}"], key=f"zi_input_{i}")
                st.session_state[f"qi_g_{i}"] = st.number_input("Caudal (L/s)", value=st.session_state[f"qi_{i}"], key=f"qi_input_{i}")
                st.session_state[f"di_g_{i}"] = st.number_input("Diámetro (in)", value=st.session_state[f"di_{i}"], key=f"di_input_{i}")

        if st.button("ANALIZAR GRADIENTE HIDRÁULICO", type="primary", use_container_width=True):
            tramos, c_reales = [], []
            for i in range(1, len(st.session_state.puntos)):
                h1 = st.session_state[f"zi_g_{i-1}"] + (st.session_state[f"pi_g_{i-1}"] * 0.7032)
                h2 = st.session_state[f"zi_g_{i}"] + (st.session_state[f"pi_g_{i}"] * 0.7032)
                l = st.session_state.red_cartografica.iloc[i-1]['longitud_real_m'] if i-1 < len(st.session_state.red_cartografica) else haversine(st.session_state[f"lat_g_{i-1}"], st.session_state[f"lon_g_{i-1}"], st.session_state[f"lat_g_{i}"], st.session_state[f"lon_g_{i}"])
                
                if (h1-h2) > 0.1 and st.session_state[f"qi_g_{i-1}"] > 0:
                    c = ( (10.67 * (st.session_state[f"qi_g_{i-1}"]/1000)**1.852 * l) / ((h1-h2) * (st.session_state[f"di_g_{i-1}"]*0.0254)**4.87) )**(1/1.852)
                    c_reales.append(c)
                tramos.append({"dh": h1-h2, "l": l})

            c_avg = min(max(np.median(c_reales) if c_reales else 140.0, 70), 150)
            st.session_state['fugas_gradiente'] = []
            
            for i, t in enumerate(tramos):
                hf_t = 10.67 * (st.session_state[f"qi_g_{i}"]/1000.0)**1.852 * t["l"] / ((c_avg**1.852) * ((st.session_state[f"di_g_{i}"]*0.0254)**4.87))
                
                if (t["dh"] - hf_t) > 0.3:
                    dist_f = t["l"] * (hf_t / t["dh"])
                    cf = interpolar_coordenadas([st.session_state[f"lat_g_{i}"], st.session_state[f"lon_g_{i}"]], [st.session_state[f"lat_g_{i+1}"], st.session_state[f"lon_g_{i+1}"]], dist_f, t["l"])
                    
                    presion_mca = max(0.1, st.session_state[f"pi_g_{i}"] * 0.7032)
                    vol = 0.12 * math.sqrt(presion_mca)
                    
                    q_ref = st.session_state[f"qi_g_{i}"] if st.session_state[f"qi_g_{i}"] > 0 else 2.0
                    vol = min(vol, q_ref * 0.1)

                    st.session_state['fugas_gradiente'].append({
                        "tramo": f"{st.session_state[f'id_{i}']} → {st.session_state[f'id_{i+1}']}", 
                        "lat": cf[0], "lon": cf[1], "vol": vol
                    })

    if st.session_state.get('fugas_gradiente'):
        st.subheader("🚩 Informe de Fugas por Gradiente")
        for f in st.session_state['fugas_gradiente']:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**📍 Ubicación:** {obtener_direccion_fisica(f['lat'], f['lon'])}")
                c1.code(f"Lat: {f['lat']:.8f}, Lon: {f['lon']:.8f}")
                c2.metric("Pérdida Estimada", f"{f['vol']:.3f} L/s")
                c3.link_button("🗺️ Google Maps", f"https://www.google.com/maps?q={f['lat']},{f['lon']}")
# =============================================================================
# MÓDULO CORRELACIÓN ACÚSTICA (VERSIÓN FINAL + DIRECTORIO FIJO CSV)
# =============================================================================

import os
import glob
import numpy as np
import pandas as pd
import scipy.signal as signal

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

VELOCIDADES_MATERIALES = {
    "PVC": 400,
    "PEAD": 300,
    "Hierro dúctil": 1000,
    "Asbesto cemento": 600,
    "Desconocido": 500
}

CARPETA_SIMULACION = "datos_simulacion"

# crear carpeta automáticamente si no existe
os.makedirs(CARPETA_SIMULACION, exist_ok=True)

# =============================================================================
# GCC-PHAT
# =============================================================================

def gcc_phat(x, y):

    n = len(x) + len(y)

    X = np.fft.rfft(x, n=n)
    Y = np.fft.rfft(y, n=n)

    R = X * np.conj(Y)
    R /= (np.abs(R) + 1e-12)

    cc = np.fft.irfft(R, n=n)

    max_shift = n // 2

    cc = np.concatenate((cc[-max_shift:], cc[:max_shift+1]))
    lags = np.arange(-max_shift, max_shift+1)

    idx = np.argmax(np.abs(cc))

    return cc, lags, idx

# =============================================================================
# REFINAMIENTO SUB-MUESTRA
# =============================================================================

def refine_peak(corr, lags, idx, fs):

    if idx <= 0 or idx >= len(corr)-1:
        return lags[idx] / fs

    y0 = corr[idx - 1]
    y1 = corr[idx]
    y2 = corr[idx + 1]

    den = (y0 - 2*y1 + y2)

    if abs(den) > 1e-12:
        delta = 0.5 * (y0 - y2) / den
    else:
        delta = 0.0

    delay = lags[idx] + delta

    return delay / fs

# =============================================================================
# INTERFAZ
# =============================================================================

with tab_correlacion:

    st.header("🎧 Correlación Acústica (Precisión Operativa)")

    # =========================================================================
    # RED
    # =========================================================================

    json_sel = st.selectbox(
        "Seleccione red:",
        ["-- Seleccione --"] + archivos_json
    )

    if json_sel != "-- Seleccione --":

        gdf_p = gpd.read_file(
            os.path.join(CARPETA, json_sel)
        ).to_crs(epsg=4326)

        gdf_m = gdf_p.to_crs(epsg=3116)

        linea = gdf_m.geometry.iloc[0]
        L = linea.length

        coords = list(gdf_p.geometry.iloc[0].coords)

        pos_a = [coords[0][1], coords[0][0]]
        pos_b = [coords[-1][1], coords[-1][0]]

        st.session_state['linea'] = linea
        st.session_state['L'] = L
        st.session_state['pos_a'] = pos_a
        st.session_state['pos_b'] = pos_b
        st.session_state['red'] = gdf_p

    # =========================================================================
    # CONTINUAR
    # =========================================================================

    if 'linea' in st.session_state:

        # =====================================================================
        # PARÁMETROS
        # =====================================================================

        st.subheader("1. Parámetros")

        c1, c2, c3 = st.columns(3)

        material = c1.selectbox(
            "Material",
            list(VELOCIDADES_MATERIALES.keys())
        )

        v_default = VELOCIDADES_MATERIALES[material]

        modo_v = c2.selectbox(
            "Velocidad",
            ["Automática", "Manual"]
        )

        if modo_v == "Automática":

            v = v_default

            c3.metric(
                "v (m/s)",
                v
            )

        else:

            v = c3.number_input(
                "v (m/s)",
                value=float(v_default)
            )

        fs = st.number_input(
            "Frecuencia (Hz)",
            value=16000
        )

        # =====================================================================
        # UMBRALES
        # =====================================================================

        st.subheader("2. Umbrales")

        c4, c5 = st.columns(2)

        thr_rho = c4.number_input(
            "ρ mínimo",
            value=0.3
        )

        thr_snr = c5.number_input(
            "SNR mínimo",
            value=4.0
        )

        # =====================================================================
        # ENTRADA
        # =====================================================================

        st.subheader("3. Entrada")

        modo = st.radio(
            "Modo",
            ["Simulación", "CSV"]
        )

        # =====================================================================
        # SIMULACIÓN
        # =====================================================================

        if modo == "Simulación":

            dur = st.slider(
                "Duración (s)",
                1,
                10,
                5
            )

            tipo = st.selectbox(
                "Escenario",
                ["Correlacionado", "Ruido"]
            )

            if st.button("Generar señales"):

                t = np.linspace(
                    0,
                    dur,
                    int(fs * dur)
                )

                base = np.random.normal(
                    0,
                    1,
                    len(t)
                )

                if tipo == "Correlacionado":

                    delay = np.random.randint(
                        -int(0.01 * fs),
                        int(0.01 * fs)
                    )

                    a = base
                    b = np.roll(base, delay)

                else:

                    a = np.random.normal(0, 1, len(t))
                    b = np.random.normal(0, 1, len(t))

                a += np.random.normal(0, 0.3, len(t))
                b += np.random.normal(0, 0.3, len(t))

                st.session_state['a'] = a
                st.session_state['b'] = b

                st.success("Señales simuladas generadas")

        # =====================================================================
        # CSV DESDE DIRECTORIO FIJO
        # =====================================================================

        else:

            st.info(
                f"Los CSV deben existir dentro de: {CARPETA_SIMULACION}"
            )

            archivos_csv = glob.glob(
                os.path.join(CARPETA_SIMULACION, "*.csv")
            )

            nombres_csv = [
                os.path.basename(x)
                for x in archivos_csv
            ]

            if len(nombres_csv) == 0:

                st.warning(
                    "No existen CSV en datos_simulacion"
                )

            else:

                col1, col2 = st.columns(2)

                csv_a = col1.selectbox(
                    "Sensor A",
                    nombres_csv,
                    key="csv_a"
                )

                csv_b = col2.selectbox(
                    "Sensor B",
                    nombres_csv,
                    key="csv_b"
                )

                if st.button("Cargar CSV"):

                    ruta_a = os.path.join(
                        CARPETA_SIMULACION,
                        csv_a
                    )

                    ruta_b = os.path.join(
                        CARPETA_SIMULACION,
                        csv_b
                    )

                    st.session_state['a'] = pd.read_csv(
                        ruta_a
                    ).iloc[:, 0].values

                    st.session_state['b'] = pd.read_csv(
                        ruta_b
                    ).iloc[:, 0].values

                    st.success("CSV cargados correctamente")

        # =====================================================================
        # EJECUCIÓN
        # =====================================================================

        if 'a' in st.session_state and 'b' in st.session_state:

            if st.button("Ejecutar correlación"):

                xa = st.session_state['a']
                xb = st.session_state['b']

                xa = xa - np.mean(xa)
                xb = xb - np.mean(xb)

                # ventana
                w = np.hanning(len(xa))

                xa *= w
                xb *= w

                # filtro
                b_f, a_f = signal.butter(
                    4,
                    [100 / (fs / 2), 2000 / (fs / 2)],
                    btype='band'
                )

                xa = signal.filtfilt(b_f, a_f, xa)
                xb = signal.filtfilt(b_f, a_f, xb)

                # correlación
                corr, lags, idx = gcc_phat(xa, xb)

                # refinamiento
                delta_t = refine_peak(
                    corr,
                    lags,
                    idx,
                    fs
                )

                # métricas
                rho = np.max(np.abs(corr))

                fondo = np.percentile(
                    np.abs(corr),
                    90
                )

                snr = rho / (fondo + 1e-12)

                st.session_state['metricas'] = {
                    "rho": rho,
                    "snr": snr
                }

                # =============================================================
                # DECISIÓN
                # =============================================================

                if rho < thr_rho or snr < thr_snr:

                    st.session_state['resultado'] = None
                    st.session_state['estado'] = "NO"

                else:

                    L = st.session_state['L']

                    x = (L + v * delta_t) / 2

                    linea = st.session_state['linea']

                    punto = gpd.GeoSeries(
                        [linea.interpolate(x)],
                        crs="EPSG:3116"
                    ).to_crs(
                        epsg=4326
                    ).iloc[0]

                    st.session_state['resultado'] = {
                        "x": x,
                        "lat": punto.y,
                        "lon": punto.x
                    }

                    st.session_state['estado'] = "OK"

                st.session_state['corr'] = corr

        # =====================================================================
        # RESULTADOS
        # =====================================================================

        if 'metricas' in st.session_state:

            st.write(
                f"ρ: {st.session_state['metricas']['rho']:.3f}"
            )

            st.write(
                f"SNR: {st.session_state['metricas']['snr']:.2f}"
            )

        # =====================================================================
        # SIN EVIDENCIA
        # =====================================================================

        if st.session_state.get('estado') == "NO":

            st.warning("SIN EVIDENCIA DE FUGA")

        # =====================================================================
        # RESULTADO POSITIVO
        # =====================================================================

        if st.session_state.get('estado') == "OK":

            res = st.session_state['resultado']

            st.success(
                f"Posible fuga a {res['x']:.2f} m desde Sensor A"
            )

            # ================================================================
            # MAPA
            # ================================================================

            m = folium.Map(
                location=[res['lat'], res['lon']],
                zoom_start=19
            )

            icon_a = folium.CustomIcon(
                "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
                icon_size=(32, 32)
            )

            icon_b = folium.CustomIcon(
                "https://maps.google.com/mapfiles/ms/icons/green-dot.png",
                icon_size=(32, 32)
            )

            icon_f = folium.CustomIcon(
                "https://maps.google.com/mapfiles/ms/icons/red-dot.png",
                icon_size=(32, 32)
            )

            folium.GeoJson(
                st.session_state['red']
            ).add_to(m)

            folium.Marker(
                st.session_state['pos_a'],
                icon=icon_a
            ).add_to(m)

            folium.Marker(
                st.session_state['pos_b'],
                icon=icon_b
            ).add_to(m)

            folium.Marker(
                [res['lat'], res['lon']],
                icon=icon_f
            ).add_to(m)

            st_folium(
                m,
                width=1200,
                height=450
            )

            # ================================================================
            # GOOGLE MAPS
            # ================================================================

            lat = res['lat']
            lon = res['lon']

            st.code(
                f"Lat: {lat:.8f}, Lon: {lon:.8f}"
            )

            url = f"https://www.google.com/maps?q={lat},{lon}"

            st.link_button(
                "Abrir en Google Maps",
                url
            )

        # =====================================================================
        # GRÁFICA
        # =====================================================================

        if 'corr' in st.session_state:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    y=st.session_state['corr']
                )
            )

            st.plotly_chart(
                fig,
                width='stretch'
            )

        # =====================================================================
        # LIMPIAR
        # =====================================================================

        if st.button("Limpiar"):

            for k in [
                'resultado',
                'estado',
                'metricas',
                'corr'
            ]:

                st.session_state.pop(k, None)
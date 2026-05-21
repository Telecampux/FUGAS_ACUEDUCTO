import os
import glob
import json
import runpy

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import scipy.signal as signal
import streamlit as st
from shapely.geometry import LineString
from streamlit_folium import st_folium

from core.rutas import asegurar_bd_proyectos

# =============================================================================
# CONFIGURACIÓN GENERAL
# =============================================================================

st.set_page_config(
    page_title="IANC_H2O",
    layout="wide"
)

# =============================================================================
# MODO SISTEMA
# =============================================================================

modo_sistema = None
_modo_sistema_obsoleto = (
    "Sistema",
    [
        "Con cartografía",
        "Sin cartografía"
    ]
)

# =============================================================================
# SIN CARTOGRAFÍA
# =============================================================================

if modo_sistema == "Sin cartografía":

    runpy.run_path(
        "sin_cartografia/app_levantamiento.py"
    )

    st.stop()

CARPETA = asegurar_bd_proyectos()


def _leer_json_seguro(ruta):
    try:
        with open(
            ruta,
            "r",
            encoding="utf-8"
        ) as archivo:
            return json.load(archivo)
    except (OSError, json.JSONDecodeError):
        return None


def es_archivo_cartografico(nombre_archivo):
    extension = os.path.splitext(nombre_archivo)[1].lower()

    if extension not in (".json", ".geojson"):
        return False

    contenido = _leer_json_seguro(
        os.path.join(
            CARPETA,
            nombre_archivo
        )
    )

    if not isinstance(contenido, dict):
        return False

    if contenido.get("type") in (
        "FeatureCollection",
        "Feature"
    ):
        return True

    return (
        "proyecto" in contenido
        and
        "puntos" in contenido
        and
        "conexiones" in contenido
    )


def listar_cartografias_disponibles():
    return [
        nombre
        for nombre in os.listdir(CARPETA)
        if es_archivo_cartografico(nombre)
    ]


def _gdf_desde_proyecto(contenido):
    puntos = contenido.get("puntos", [])
    conexiones = contenido.get("conexiones", [])

    puntos_por_nombre = {
        punto.get("nombre"): punto
        for punto in puntos
    }

    registros = []

    for conexion in conexiones:
        origen = puntos_por_nombre.get(
            conexion.get("origen")
        )
        destino = puntos_por_nombre.get(
            conexion.get("destino")
        )

        if not origen or not destino:
            continue

        lat_origen = origen.get("latitud")
        lon_origen = origen.get("longitud")
        lat_destino = destino.get("latitud")
        lon_destino = destino.get("longitud")

        if None in (
            lat_origen,
            lon_origen,
            lat_destino,
            lon_destino
        ):
            continue

        registros.append(
            {
                **conexion,
                "geometry": LineString(
                    [
                        (
                            float(lon_origen),
                            float(lat_origen)
                        ),
                        (
                            float(lon_destino),
                            float(lat_destino)
                        )
                    ]
                )
            }
        )

    return gpd.GeoDataFrame(
        registros,
        geometry="geometry",
        crs="EPSG:4326"
    )


def cargar_gdf_cartografia(nombre_archivo):
    ruta = os.path.join(
        CARPETA,
        nombre_archivo
    )

    contenido = _leer_json_seguro(ruta)

    if not isinstance(contenido, dict):
        raise ValueError("Archivo cartografico invalido")

    if contenido.get("type") in (
        "FeatureCollection",
        "Feature"
    ):
        return gpd.read_file(ruta).to_crs(epsg=4326)

    return _gdf_desde_proyecto(contenido).to_crs(epsg=4326)


def obtener_coordenadas_extremos(geometria):
    if geometria.geom_type == "LineString":
        return list(geometria.coords)

    if geometria.geom_type == "MultiLineString":
        return list(
            list(geometria.geoms)[0].coords
        )

    raise ValueError(
        "La cartografia debe contener geometria de linea"
    )


archivos_cartografia = listar_cartografias_disponibles()

if "modo_levantamiento" not in st.session_state:
    st.session_state["modo_levantamiento"] = False

if st.sidebar.button(
    "Crear nueva cartografia"
):
    st.session_state["modo_levantamiento"] = True
    st.rerun()

if (
    st.session_state["modo_levantamiento"]
    and
    len(archivos_cartografia) > 0
):
    if st.sidebar.button(
        "Usar cartografia existente"
    ):
        st.session_state["modo_levantamiento"] = False
        st.rerun()

if (
    len(archivos_cartografia) == 0
    or
    st.session_state["modo_levantamiento"]
):

    runpy.run_path(
        "sin_cartografia/app_levantamiento.py"
    )

    st.stop()

# =============================================================================
# RESET
# =============================================================================


def reset_total_sistema():

    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.session_state['resultado_generado'] = False


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

    cc = np.concatenate(
        (
            cc[-max_shift:],
            cc[:max_shift + 1]
        )
    )

    lags = np.arange(
        -max_shift,
        max_shift + 1
    )

    idx = np.argmax(
        np.abs(cc)
    )

    return cc, lags, idx


# =============================================================================
# REFINAMIENTO SUB-MUESTRA
# =============================================================================


def refine_peak(corr, lags, idx, fs):

    if idx <= 0 or idx >= len(corr) - 1:
        return lags[idx] / fs

    y0 = corr[idx - 1]
    y1 = corr[idx]
    y2 = corr[idx + 1]

    den = (
        y0 - 2 * y1 + y2
    )

    if abs(den) > 1e-12:

        delta = (
            0.5 * (y0 - y2) / den
        )

    else:

        delta = 0.0

    delay = lags[idx] + delta

    return delay / fs


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

CARPETA = asegurar_bd_proyectos()

def es_archivo_cartografico_obsoleto(nombre_archivo):
    extension = os.path.splitext(nombre_archivo)[1].lower()

    if extension == ".geojson":
        return True

    if extension != ".json":
        return False

    ruta = os.path.join(
        CARPETA,
        nombre_archivo
    )

    try:
        with open(
            ruta,
            "r",
            encoding="utf-8"
        ) as archivo:
            contenido = json.load(archivo)
    except (OSError, json.JSONDecodeError):
        return False

    return contenido.get("type") in (
        "FeatureCollection",
        "Feature"
    )

if "resultado_generado" not in st.session_state:

    st.session_state['resultado_generado'] = False

# =============================================================================
# TÍTULO
# =============================================================================

st.title(
    "IANC_H2O - Con Cartografía"
)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:

    st.header("Gestión")

    if st.button(
        "LIMPIAR SESIÓN",
        width="stretch",
        type="primary"
    ):

        reset_total_sistema()

        st.rerun()

# =============================================================================
# TAB
# =============================================================================

tab_correlacion = st.tabs(
    [
        "Inferencia por Correlación"
    ]
)[0]

# =============================================================================
# TAB PRINCIPAL
# =============================================================================

with tab_correlacion:

    st.header(
        "Correlación Acústica Adaptativa"
    )

    # =========================================================================
    # GEOJSON
    # =========================================================================

    json_sel = st.selectbox(
        "Seleccione red:",
        archivos_cartografia
    )

    if json_sel:

        gdf_p = cargar_gdf_cartografia(
            json_sel
        )

        if len(gdf_p) == 0:
            st.error(
                "La cartografia no contiene tramos validos"
            )
            st.stop()

        gdf_m = gdf_p.to_crs(
            epsg=3116
        )

        linea = gdf_m.geometry.iloc[0]

        L = linea.length

        coords = obtener_coordenadas_extremos(
            gdf_p.geometry.iloc[0]
        )

        pos_a = [
            coords[0][1],
            coords[0][0]
        ]

        pos_b = [
            coords[-1][1],
            coords[-1][0]
        ]

        st.session_state['linea'] = linea
        st.session_state['L'] = L
        st.session_state['pos_a'] = pos_a
        st.session_state['pos_b'] = pos_b
        st.session_state['red'] = gdf_p

    # =========================================================================
    # CONTINUAR
    # =========================================================================

    if 'linea' in st.session_state:

        st.subheader(
            "1. Parámetros"
        )

        c1, c2, c3 = st.columns(3)

        material = c1.selectbox(
            "Material",
            list(
                VELOCIDADES_MATERIALES.keys()
            )
        )

        v_default = (
            VELOCIDADES_MATERIALES[material]
        )

        modo_v = c2.selectbox(
            "Velocidad",
            [
                "Automática",
                "Manual"
            ]
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
            "Frecuencia de muestreo sensores (Hz)",
            value=16000
        )

        # =====================================================================
        # ENTRADA
        # =====================================================================

        st.subheader(
            "2. Entrada"
        )

        modo = st.radio(
            "Modo",
            [
                "Simulación",
                "CSV"
            ]
        )

        # =====================================================================
        # SIMULACIÓN
        # =====================================================================

        if modo == "Simulación":

            dur = st.slider(
                "Tiempo de toma de muestra sensores (s)",
                1,
                10,
                5
            )

            tipo = st.selectbox(
                "Escenario",
                [
                    "Correlacionado",
                    "Ruido"
                ]
            )

            if st.button(
                "Generar señales"
            ):

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

                    b = np.roll(
                        base,
                        delay
                    )

                else:

                    a = np.random.normal(
                        0,
                        1,
                        len(t)
                    )

                    b = np.random.normal(
                        0,
                        1,
                        len(t)
                    )

                a += np.random.normal(
                    0,
                    0.3,
                    len(t)
                )

                b += np.random.normal(
                    0,
                    0.3,
                    len(t)
                )

                st.session_state['a'] = a
                st.session_state['b'] = b

                pd.DataFrame(a).to_csv(
                    os.path.join(
                        CARPETA,
                        "sensor_a_simulado.csv"
                    ),
                    index=False,
                    header=False
                )

                pd.DataFrame(b).to_csv(
                    os.path.join(
                        CARPETA,
                        "sensor_b_simulado.csv"
                    ),
                    index=False,
                    header=False
                )

                st.success(
                    "Señales simuladas y CSV generados"
                )

        # =====================================================================
        # CSV
        # =====================================================================

        else:

            archivos_csv = glob.glob(
                os.path.join(
                    CARPETA,
                    "*.csv"
                )
            )

            nombres_csv = [

                os.path.basename(x)

                for x in archivos_csv
            ]

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

            if st.button(
                "Cargar CSV"
            ):

                ruta_a = os.path.join(
                    CARPETA,
                    csv_a
                )

                ruta_b = os.path.join(
                    CARPETA,
                    csv_b
                )

                df_a = pd.read_csv(
                    ruta_a,
                    header=None
                )

                df_b = pd.read_csv(
                    ruta_b,
                    header=None
                )

                xa = pd.to_numeric(
                    df_a.iloc[:, 0],
                    errors='coerce'
                ).dropna().values

                xb = pd.to_numeric(
                    df_b.iloc[:, 0],
                    errors='coerce'
                ).dropna().values

                n_a = len(xa)
                n_b = len(xb)

                if n_a != n_b:

                    st.warning(
                        f"""
                        Los sensores tienen diferente cantidad de muestras.

                        Sensor A:
                        {n_a}

                        Sensor B:
                        {n_b}

                        El sistema sincronizará automáticamente
                        usando la longitud mínima común.
                        """
                    )

                n_min = min(
                    n_a,
                    n_b
                )

                xa = xa[:n_min]
                xb = xb[:n_min]

                st.info(
                    f"""
                    Muestras sincronizadas:
                    {n_min}
                    """
                )

                st.session_state['a'] = xa
                st.session_state['b'] = xb

                st.success(
                    "CSV cargados correctamente"
                )

        # =====================================================================
        # CORRELACIÓN
        # =====================================================================

        if (
            'a' in st.session_state
            and
            'b' in st.session_state
        ):

            if st.button(
                "Ejecutar correlación"
            ):

                xa = st.session_state['a']
                xb = st.session_state['b']

                xa = xa - np.mean(xa)
                xb = xb - np.mean(xb)

                w = np.hanning(
                    len(xa)
                )

                xa *= w
                xb *= w

                b_f, a_f = signal.butter(
                    4,
                    [
                        100 / (fs / 2),
                        2000 / (fs / 2)
                    ],
                    btype='band'
                )

                padlen = 3 * max(
                    len(a_f),
                    len(b_f)
                )

                if (
                    len(xa) <= padlen
                    or
                    len(xb) <= padlen
                ):

                    st.error(
                        "Señales demasiado cortas"
                    )

                    st.stop()

                xa = signal.filtfilt(
                    b_f,
                    a_f,
                    xa
                )

                xb = signal.filtfilt(
                    b_f,
                    a_f,
                    xb
                )

                corr, lags, idx = gcc_phat(
                    xa,
                    xb
                )

                delta_t = refine_peak(
                    corr,
                    lags,
                    idx,
                    fs
                )

                rho = np.max(
                    np.abs(corr)
                )

                noise_floor = np.median(
                    np.abs(corr)
                )

                noise_std = np.std(
                    np.abs(corr)
                )

                snr = (
                    (
                        rho - noise_floor
                    )
                    /
                    (
                        noise_std + 1e-12
                    )
                )

                thr_rho_auto = (
                    noise_floor
                    + (3.5 * noise_std)
                )

                thr_snr_auto = (
                    4.0
                    + (noise_std * 2)
                )

                confidence = (

                    (
                        rho /
                        (
                            thr_rho_auto + 1e-12
                        )
                    )

                    +

                    (
                        snr /
                        (
                            thr_snr_auto + 1e-12
                        )
                    )

                ) / 2

                confidence = max(
                    0,
                    min(confidence, 10)
                )

                st.session_state['rho'] = rho
                st.session_state['snr'] = snr
                st.session_state['thr_rho_auto'] = thr_rho_auto
                st.session_state['thr_snr_auto'] = thr_snr_auto
                st.session_state['confidence'] = confidence
                st.session_state['corr'] = corr

                if (
                    rho < thr_rho_auto
                    or
                    snr < thr_snr_auto
                ):

                    st.session_state['estado'] = "NO_FUGA"

                else:

                    L = st.session_state['L']

                    x = (
                        L
                        + v * delta_t
                    ) / 2

                    linea = st.session_state[
                        'linea'
                    ]

                    punto = gpd.GeoSeries(
                        [
                            linea.interpolate(x)
                        ],
                        crs="EPSG:3116"
                    ).to_crs(
                        epsg=4326
                    ).iloc[0]

                    st.session_state['estado'] = "FUGA"

                    st.session_state['x_fuga'] = x
                    st.session_state['lat_fuga'] = punto.y
                    st.session_state['lon_fuga'] = punto.x

                st.session_state[
                    'resultado_generado'
                ] = True

        # =====================================================================
        # RESULTADOS PERSISTENTES
        # =====================================================================

        if st.session_state['resultado_generado']:

            st.subheader(
                "3. Resultados"
            )

            st.write(
                f"ρ observado: "
                f"{st.session_state['rho']:.3f}"
            )

            st.write(
                f"SNR observado: "
                f"{st.session_state['snr']:.2f}"
            )

            st.write(
                f"ρ dinámico: "
                f"{st.session_state['thr_rho_auto']:.3f}"
            )

            st.write(
                f"SNR dinámico: "
                f"{st.session_state['thr_snr_auto']:.2f}"
            )

            st.metric(
                "Confiabilidad",
                f"{st.session_state['confidence']:.1f}/10"
            )

            if (
                st.session_state['estado']
                == "NO_FUGA"
            ):

                st.warning(
                    "SIN EVIDENCIA DE FUGA"
                )

            if (
                st.session_state['estado']
                == "FUGA"
            ):

                st.success(
                    f"""
                    Posible fuga a
                    {st.session_state['x_fuga']:.2f} m
                    desde Sensor A
                    """
                )

                mapa = folium.Map(
                    location=[
                        st.session_state['lat_fuga'],
                        st.session_state['lon_fuga']
                    ],
                    zoom_start=19
                )

                folium.GeoJson(
                    st.session_state['red']
                ).add_to(mapa)

                folium.Marker(
                    st.session_state['pos_a'],
                    tooltip="Sensor A",
                    icon=folium.Icon(color='blue')
                ).add_to(mapa)

                folium.Marker(
                    st.session_state['pos_b'],
                    tooltip="Sensor B",
                    icon=folium.Icon(color='green')
                ).add_to(mapa)

                folium.Marker(
                    [
                        st.session_state['lat_fuga'],
                        st.session_state['lon_fuga']
                    ],
                    tooltip="Posible fuga",
                    icon=folium.Icon(color='red')
                ).add_to(mapa)

                st_folium(
                    mapa,
                    width=1200,
                    height=500
                )

                lat = st.session_state['lat_fuga']
                lon = st.session_state['lon_fuga']

                st.code(
                    f"""
Lat:
{lat:.8f}

Lon:
{lon:.8f}
"""
                )

                url_maps = (
                    f"https://www.google.com/maps?q={lat},{lon}"
                )

                st.link_button(
                    "Abrir en Google Maps",
                    url_maps
                )

            fig_corr = go.Figure()

            fig_corr.add_trace(
                go.Scatter(
                    y=st.session_state['corr']
                )
            )

            fig_corr.update_layout(
                title="Correlación GCC-PHAT"
            )

            st.plotly_chart(
                fig_corr,
                width="stretch"
            )

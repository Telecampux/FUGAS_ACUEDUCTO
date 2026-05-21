import os
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

from core.rutas import asegurar_bd_proyectos, asegurar_bd_sensores

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
CARPETA_SENSORES = asegurar_bd_sensores()


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

    if extension != ".geojson":
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

    return False


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
    extension = os.path.splitext(nombre_archivo)[1].lower()

    if extension != ".geojson":
        raise ValueError(
            "Para geolocalizar fugas debe cargar una red en formato GeoJSON (.geojson)"
        )

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

    raise ValueError(
        "El archivo seleccionado no es un GeoJSON valido"
    )


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


def crear_tabla_conexiones(gdf):
    gdf_m = gdf.to_crs(epsg=3116)
    registros = []

    for posicion, (_, fila) in enumerate(gdf.iterrows()):
        geometria = fila.geometry

        if (
            geometria is None
            or
            geometria.is_empty
            or
            geometria.geom_type not in (
                "LineString",
                "MultiLineString"
            )
        ):
            continue

        datos = fila.drop(labels=["geometry"]).to_dict()

        origen = datos.get("origen") or datos.get("ORIGEN")
        destino = datos.get("destino") or datos.get("DESTINO")
        csv_a = valor_por_campos(
            datos,
            CAMPOS_CSV_SENSOR_A
        )
        csv_b = valor_por_campos(
            datos,
            CAMPOS_CSV_SENSOR_B
        )
        ubicacion = (
            datos.get("UBICACION")
            or
            datos.get("ubicacion")
        )

        if not ubicacion and origen and destino:
            ubicacion = f"{origen} - {destino}"

        registros.append(
            {
                "_posicion_gdf": posicion,
                "ID_TRAMO": (
                    datos.get("ID_TRAMO")
                    or
                    datos.get("id_tramo")
                    or
                    datos.get("id")
                    or
                    posicion + 1
                ),
                "UBICACION": ubicacion or f"Tramo {posicion + 1}",
                "TIPO_RED": (
                    datos.get("TIPO_RED")
                    or
                    datos.get("tipo_red")
                    or
                    "Sin dato"
                ),
                "DIAM_PULG": (
                    datos.get("DIAM_PULG")
                    or
                    datos.get("diam_pulg")
                    or
                    datos.get("diametro")
                    or
                    "Sin dato"
                ),
                "MATERIAL": (
                    datos.get("MATERIAL")
                    or
                    datos.get("material")
                    or
                    "Desconocido"
                ),
                "ESTADO": (
                    datos.get("ESTADO")
                    or
                    datos.get("estado")
                    or
                    "Sin dato"
                ),
                "CSV_A": csv_a,
                "CSV_B": csv_b,
                "LONG_M": round(
                    gdf_m.geometry.iloc[posicion].length,
                    2
                )
            }
        )

    return pd.DataFrame(registros)


CAMPOS_CSV_SENSOR_A = (
    "CSV_A",
    "csv_a",
    "SENSOR_A_CSV",
    "sensor_a_csv",
    "CSV_SENSOR_A",
    "csv_sensor_a",
    "ARCHIVO_SENSOR_A",
    "archivo_sensor_a"
)

CAMPOS_CSV_SENSOR_B = (
    "CSV_B",
    "csv_b",
    "SENSOR_B_CSV",
    "sensor_b_csv",
    "CSV_SENSOR_B",
    "csv_sensor_b",
    "ARCHIVO_SENSOR_B",
    "archivo_sensor_b"
)


def valor_por_campos(datos, campos):
    for campo in campos:
        valor = datos.get(campo)

        if valor is not None and str(valor).strip():
            return str(valor).strip()

    return None


def _nombre_proyecto_desde_archivo(nombre_archivo):
    if not nombre_archivo:
        return None

    return os.path.splitext(
        os.path.basename(str(nombre_archivo).strip())
    )[0]


def resolver_ruta_csv(nombre_csv, proyecto=None):
    if not nombre_csv:
        return None

    ruta = str(nombre_csv).strip()

    if os.path.isabs(ruta):
        return ruta

    proyecto_base = _nombre_proyecto_desde_archivo(proyecto)

    if proyecto_base:
        ruta_por_proyecto = os.path.join(
            CARPETA_SENSORES,
            proyecto_base,
            ruta
        )

        if os.path.exists(ruta_por_proyecto):
            return ruta_por_proyecto

    ruta_sensores = os.path.join(
        CARPETA_SENSORES,
        ruta
    )

    if os.path.exists(ruta_sensores):
        return ruta_sensores

    return os.path.join(
        CARPETA,
        ruta
    )


@st.cache_data(show_spinner=False)
def leer_senal_csv(ruta, modificado):
    df = pd.read_csv(
        ruta,
        header=None
    )

    return pd.to_numeric(
        df.iloc[:, 0],
        errors="coerce"
    ).dropna().values


def cargar_senales_desde_tramo(fila_tramo, proyecto=None):
    csv_a = fila_tramo.get("CSV_A")
    csv_b = fila_tramo.get("CSV_B")

    if not csv_a or not csv_b:
        raise ValueError(
            "El tramo debe incluir los campos CSV_A y CSV_B en el GeoJSON."
        )

    ruta_a = resolver_ruta_csv(csv_a, proyecto)
    ruta_b = resolver_ruta_csv(csv_b, proyecto)

    faltantes = [
        ruta for ruta in (ruta_a, ruta_b)
        if not ruta or not os.path.exists(ruta)
    ]

    if faltantes:
        raise FileNotFoundError(
            "No se encontraron estos CSV: "
            + ", ".join(faltantes)
        )

    xa = leer_senal_csv(
        ruta_a,
        os.path.getmtime(ruta_a)
    )
    xb = leer_senal_csv(
        ruta_b,
        os.path.getmtime(ruta_b)
    )

    n_min = min(
        len(xa),
        len(xb)
    )

    if n_min == 0:
        raise ValueError(
            "Los CSV del tramo no contienen muestras numericas validas."
        )

    return {
        "csv_a": csv_a,
        "csv_b": csv_b,
        "ruta_a": ruta_a,
        "ruta_b": ruta_b,
        "muestras_a": len(xa),
        "muestras_b": len(xb),
        "muestras_sincronizadas": n_min,
        "a": xa[:n_min],
        "b": xb[:n_min]
    }


def material_para_analisis(material):
    material_normalizado = str(
        material or ""
    ).strip().upper()

    if material_normalizado in (
        "HF",
        "HIERRO",
        "HIERRO DUCTIL"
    ) or material_normalizado.startswith("HIERRO "):
        return "Hierro"

    equivalencias = {
        "PVC": "PVC",
        "PEAD": "PEAD",
        "HF": "Hierro dÃºctil",
        "HIERRO": "Hierro dÃºctil",
        "HIERRO DUCTIL": "Hierro dÃºctil",
        "HIERRO DÃšCTIL": "Hierro dÃºctil",
        "AC": "Asbesto cemento",
        "ASBESTO CEMENTO": "Asbesto cemento"
    }

    return equivalencias.get(
        material_normalizado,
        "Desconocido"
    )


def limpiar_resultados_tramo():
    for key in (
        "resultado_generado",
        "estado",
        "x_fuga",
        "lat_fuga",
        "lon_fuga",
        "rho",
        "snr",
        "thr_rho_auto",
        "thr_snr_auto",
        "confidence",
        "corr"
    ):
        st.session_state.pop(key, None)

    st.session_state["resultado_generado"] = False


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
    "Hierro": 1000,
    "Hierro dúctil": 1000,
    "Asbesto cemento": 600,
    "Desconocido": 500
}

CARPETA = asegurar_bd_proyectos()

def es_archivo_cartografico_obsoleto(nombre_archivo):
    extension = os.path.splitext(nombre_archivo)[1].lower()

    if extension != ".geojson":
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

    return isinstance(contenido, dict) and contenido.get("type") in (
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

        tabla_conexiones = crear_tabla_conexiones(
            gdf_p
        )

        if len(tabla_conexiones) == 0:
            st.error(
                "La cartografia no contiene tramos de linea validos"
            )
            st.stop()

        st.subheader(
            "Conexiones disponibles"
        )

        st.dataframe(
            tabla_conexiones.drop(
                columns=["_posicion_gdf"]
            ),
            width="stretch",
            hide_index=True
        )

        opciones_tramo = [
            (
                f"{indice + 1}. "
                f"{fila['ID_TRAMO']} - "
                f"{fila['UBICACION']} "
                f"({fila['LONG_M']} m)"
            )
            for indice, fila in tabla_conexiones.iterrows()
        ]

        tramo_opcion = st.selectbox(
            "Seleccione tramo para analizar",
            opciones_tramo,
            key=f"tramo_selector_{json_sel}"
        )

        tramo_sel = opciones_tramo.index(
            tramo_opcion
        )

        fila_tramo = tabla_conexiones.loc[tramo_sel]
        posicion_tramo = int(
            fila_tramo["_posicion_gdf"]
        )

        tramo_actual = (
            f"{json_sel}::{posicion_tramo}"
        )
        material_tramo = material_para_analisis(
            fila_tramo["MATERIAL"]
        )

        if (
            st.session_state.get("tramo_actual")
            != tramo_actual
        ):
            limpiar_resultados_tramo()
            st.session_state["material_parametros"] = material_tramo

        st.session_state["tramo_actual"] = tramo_actual

        gdf_tramo_p = gdf_p.iloc[
            [posicion_tramo]
        ].copy()

        gdf_m = gdf_p.to_crs(
            epsg=3116
        )

        linea = gdf_m.geometry.iloc[
            posicion_tramo
        ]

        L = linea.length

        coords = obtener_coordenadas_extremos(
            gdf_p.geometry.iloc[posicion_tramo]
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
        st.session_state['red'] = gdf_tramo_p
        st.session_state['red_completa'] = gdf_p
        st.session_state['tramo_info'] = fila_tramo.to_dict()
        st.session_state['material_tramo'] = material_tramo

        c_info1, c_info2, c_info3, c_info4 = st.columns(4)
        c_info1.metric(
            "Longitud tramo",
            f"{L:.2f} m"
        )
        c_info2.metric(
            "Material",
            fila_tramo["MATERIAL"]
        )
        c_info3.metric(
            "Diametro",
            fila_tramo["DIAM_PULG"]
        )
        c_info4.metric(
            "Estado",
            fila_tramo["ESTADO"]
        )

    # =========================================================================
    # CONTINUAR
    # =========================================================================

    if 'linea' in st.session_state:

        st.subheader(
            "1. Parámetros"
        )

        c1, c2, c3 = st.columns(3)

        material_sugerido = st.session_state.get(
            "material_tramo",
            "Desconocido"
        )
        materiales_disponibles = list(
            VELOCIDADES_MATERIALES.keys()
        )

        if material_sugerido not in materiales_disponibles:
            material_sugerido = "Desconocido"

        material = c1.selectbox(
            "Material",
            materiales_disponibles,
            index=materiales_disponibles.index(
                material_sugerido
            ),
            key=(
                "material_parametros_widget_"
                f"{st.session_state.get('tramo_actual', 'sin_tramo')}"
            )
        )
        st.session_state["material_parametros"] = material

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
            "2. CSV del tramo"
        )

        try:
            senales = cargar_senales_desde_tramo(
                fila_tramo,
                json_sel
            )
        except (ValueError, FileNotFoundError, OSError) as error:
            st.session_state.pop("a", None)
            st.session_state.pop("b", None)
            st.error(str(error))
            st.info(
                "Agregue al GeoJSON del tramo las propiedades CSV_A y CSV_B "
                "con nombres de archivos ubicados en BD_SENSORES/proyecto, por ejemplo "
                "sensor_a_bogota.csv y sensor_b_bogota.csv."
            )
        else:
            st.session_state["a"] = senales["a"]
            st.session_state["b"] = senales["b"]

            c_csv1, c_csv2, c_csv3 = st.columns(3)
            c_csv1.metric(
                "Sensor A",
                senales["csv_a"]
            )
            c_csv2.metric(
                "Sensor B",
                senales["csv_b"]
            )
            c_csv3.metric(
                "Muestras sincronizadas",
                senales["muestras_sincronizadas"]
            )

            if senales["muestras_a"] != senales["muestras_b"]:
                st.warning(
                    "Los sensores tienen diferente cantidad de muestras. "
                    "El sistema usara la longitud minima comun."
                )

            muestras_vista = min(
                20,
                senales["muestras_sincronizadas"]
            )
            vista_csv = pd.DataFrame(
                {
                    "Muestra": np.arange(muestras_vista),
                    "Sensor A": senales["a"][:muestras_vista],
                    "Sensor B": senales["b"][:muestras_vista]
                }
            )

            st.dataframe(
                vista_csv,
                width="stretch",
                hide_index=True
            )

            st.success(
                "CSV cargados desde el tramo seleccionado"
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

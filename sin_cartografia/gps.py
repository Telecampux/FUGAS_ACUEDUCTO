# cartografia/gps.py

import streamlit as st

from datetime import datetime


def inicializar_gps():

    if "gps_historial" not in st.session_state:

        st.session_state["gps_historial"] = []


def registrar_coordenada_gps():

    inicializar_gps()

    st.subheader(
        "📡 Captura GPS"
    )

    nombre = st.text_input(
        "Nombre referencia"
    )

    latitud = st.number_input(
        "Latitud GPS",
        format="%.6f"
    )

    longitud = st.number_input(
        "Longitud GPS",
        format="%.6f"
    )

    precision = st.number_input(
        "Precisión estimada (m)",
        min_value=0.0,
        value=5.0
    )

    observacion = st.text_area(
        "Observación"
    )

    if st.button(
        "Registrar coordenada"
    ):

        registro = {

            "fecha": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "nombre": nombre,

            "latitud": latitud,

            "longitud": longitud,

            "precision": precision,

            "observacion": observacion

        }

        st.session_state[
            "gps_historial"
        ].append(registro)

        st.success(
            "Coordenada GPS registrada"
        )

    st.dataframe(

        st.session_state[
            "gps_historial"
        ],

        width='stretch'

    )


def obtener_ultima_coordenada():

    historial = st.session_state.get(
        "gps_historial",
        []
    )

    if len(historial) == 0:

        return None

    return historial[-1]


def asociar_gps_a_punto():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    historial = st.session_state.get(
        "gps_historial",
        []
    )

    if len(puntos) == 0:

        st.warning(
            "No existen puntos registrados"
        )

        return

    if len(historial) == 0:

        st.warning(
            "No existen coordenadas GPS"
        )

        return

    nombres = [

        p["nombre"]
        for p in puntos

    ]

    punto = st.selectbox(
        "Punto cartográfico",
        nombres
    )

    coordenada = obtener_ultima_coordenada()

    st.write(
        coordenada
    )

    if st.button(
        "Asociar GPS"
    ):

        for p in puntos:

            if p["nombre"] == punto:

                p["latitud"] = coordenada[
                    "latitud"
                ]

                p["longitud"] = coordenada[
                    "longitud"
                ]

        st.success(
            "GPS asociado correctamente"
        )
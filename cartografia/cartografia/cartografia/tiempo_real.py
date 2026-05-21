# cartografia/tiempo_real.py

import time
import random

import streamlit as st
import pandas as pd


def inicializar_stream():

    if "stream_tiempo_real" not in st.session_state:

        st.session_state[
            "stream_tiempo_real"
        ] = []


def generar_muestra_sensor():

    return {

        "timestamp": time.strftime(
            "%H:%M:%S"
        ),

        "amplitud": round(

            random.uniform(
                0.1,
                5.0
            ),

            3

        ),

        "snr": round(

            random.uniform(
                5,
                40
            ),

            2

        ),

        "correlacion": round(

            random.uniform(
                0,
                1
            ),

            3

        )

    }


def ejecutar_stream_tiempo_real():

    inicializar_stream()

    st.header(
        "📡 Monitoreo tiempo real"
    )

    sensores = st.session_state.get(
        "sensores_geo",
        []
    )

    if len(sensores) == 0:

        st.warning(
            "No existen sensores registrados"
        )

        return

    nombres = [

        s["sensor"]
        for s in sensores

    ]

    sensor = st.selectbox(
        "Sensor",
        nombres
    )

    actualizar = st.toggle(
        "Activar streaming"
    )

    placeholder_metricas = st.empty()

    placeholder_tabla = st.empty()

    if actualizar:

        for _ in range(30):

            muestra = generar_muestra_sensor()

            muestra["sensor"] = sensor

            st.session_state[
                "stream_tiempo_real"
            ].append(muestra)

            historial = st.session_state[
                "stream_tiempo_real"
            ][-20:]

            df = pd.DataFrame(
                historial
            )

            with placeholder_metricas.container():

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Amplitud",
                        muestra["amplitud"]
                    )

                with col2:

                    st.metric(
                        "SNR",
                        muestra["snr"]
                    )

                with col3:

                    st.metric(
                        "Correlación",
                        muestra["correlacion"]
                    )

            placeholder_tabla.dataframe(
                df,
                width='stretch'
            )

            time.sleep(1)

    else:

        historial = st.session_state.get(
            "stream_tiempo_real",
            []
        )

        if len(historial) > 0:

            df = pd.DataFrame(
                historial
            )

            st.dataframe(
                df,
                width='stretch'
            )
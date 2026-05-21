# cartografia/historico.py

import streamlit as st

from datetime import datetime
from copy import deepcopy


def inicializar_historico():

    if "historico_cartografia" not in st.session_state:

        st.session_state[
            "historico_cartografia"
        ] = []


def crear_snapshot():

    inicializar_historico()

    snapshot = {

        "fecha": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "puntos_red": deepcopy(

            st.session_state.get(
                "puntos_red",
                []
            )

        ),

        "conexiones_red": deepcopy(

            st.session_state.get(
                "conexiones_red",
                []
            )

        ),

        "sectores_red": deepcopy(

            st.session_state.get(
                "sectores_red",
                []
            )

        ),

        "sensores_geo": deepcopy(

            st.session_state.get(
                "sensores_geo",
                []
            )

        ),

        "inspecciones_red": deepcopy(

            st.session_state.get(
                "inspecciones_red",
                []
            )

        ),

        "alertas_red": deepcopy(

            st.session_state.get(
                "alertas_red",
                []
            )

        )

    }

    st.session_state[
        "historico_cartografia"
    ].append(snapshot)

    st.success(
        "Snapshot histórico creado"
    )


def visualizar_historico():

    inicializar_historico()

    historico = st.session_state.get(
        "historico_cartografia",
        []
    )

    st.subheader(
        "🕓 Histórico cartográfico"
    )

    if len(historico) == 0:

        st.info(
            "No existen snapshots"
        )

        return

    resumen = []

    for indice, snapshot in enumerate(historico):

        resumen.append(

            {

                "id": indice,

                "fecha": snapshot["fecha"],

                "puntos":

                len(
                    snapshot["puntos_red"]
                ),

                "conexiones":

                len(
                    snapshot["conexiones_red"]
                ),

                "sectores":

                len(
                    snapshot["sectores_red"]
                ),

                "sensores":

                len(
                    snapshot["sensores_geo"]
                ),

                "alertas":

                len(
                    snapshot["alertas_red"]
                )

            }

        )

    st.dataframe(
        resumen,
        width='stretch'
    )


def restaurar_snapshot():

    inicializar_historico()

    historico = st.session_state.get(
        "historico_cartografia",
        []
    )

    if len(historico) == 0:

        st.warning(
            "No existen snapshots"
        )

        return

    opciones = [

        f"{i} - {h['fecha']}"

        for i, h in enumerate(historico)

    ]

    seleccion = st.selectbox(
        "Seleccionar snapshot",
        opciones
    )

    indice = int(
        seleccion.split("-")[0].strip()
    )

    if st.button(
        "Restaurar snapshot"
    ):

        snapshot = historico[indice]

        st.session_state[
            "puntos_red"
        ] = snapshot["puntos_red"]

        st.session_state[
            "conexiones_red"
        ] = snapshot["conexiones_red"]

        st.session_state[
            "sectores_red"
        ] = snapshot["sectores_red"]

        st.session_state[
            "sensores_geo"
        ] = snapshot["sensores_geo"]

        st.session_state[
            "inspecciones_red"
        ] = snapshot["inspecciones_red"]

        st.session_state[
            "alertas_red"
        ] = snapshot["alertas_red"]

        st.success(
            "Snapshot restaurado"
        )
# cartografia/inspeccion.py

import streamlit as st
from datetime import datetime


TIPOS_EVENTO = [

    "Fuga probable",
    "Ruido anómalo",
    "Vibración",
    "Golpe de ariete",
    "Válvula defectuosa",
    "Inspección visual",
    "Otro"

]


def registrar_inspeccion():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    if len(puntos) == 0:

        st.warning(
            "No existen puntos registrados"
        )

        return

    if "inspecciones_red" not in st.session_state:

        st.session_state["inspecciones_red"] = []

    nombres = [

        p["nombre"]
        for p in puntos

    ]

    st.subheader(
        "🛠️ Registro de inspecciones"
    )

    punto = st.selectbox(
        "Punto inspeccionado",
        nombres
    )

    tipo_evento = st.selectbox(
        "Tipo evento",
        TIPOS_EVENTO
    )

    severidad = st.slider(
        "Severidad",
        1,
        10,
        5
    )

    observaciones = st.text_area(
        "Observaciones"
    )

    inspector = st.text_input(
        "Inspector"
    )

    if st.button(
        "Registrar inspección"
    ):

        inspeccion = {

            "fecha": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "punto": punto,

            "evento": tipo_evento,

            "severidad": severidad,

            "observaciones": observaciones,

            "inspector": inspector

        }

        st.session_state["inspecciones_red"].append(
            inspeccion
        )

        st.success(
            "Inspección registrada"
        )

    st.dataframe(

        st.session_state["inspecciones_red"],

        width='stretch'

    )
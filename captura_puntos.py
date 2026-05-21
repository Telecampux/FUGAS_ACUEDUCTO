# cartografia/captura_puntos.py

import streamlit as st


TIPOS_PUNTO = [

    "Hidrante",
    "Valvula",
    "Tanque",
    "Bomba",
    "Sensor",
    "Caja",
    "Empalme",
    "Otro"

]


def inicializar_estado():

    if "puntos_red" not in st.session_state:

        st.session_state["puntos_red"] = []


def registrar_punto():

    inicializar_estado()

    st.subheader(
        "Registro de puntos"
    )

    nombre = st.text_input(
        "Nombre del punto"
    )

    tipo = st.selectbox(
        "Tipo",
        TIPOS_PUNTO
    )

    latitud = st.number_input(
        "Latitud",
        format="%.6f"
    )

    longitud = st.number_input(
        "Longitud",
        format="%.6f"
    )

    descripcion = st.text_area(
        "Observaciones"
    )

    if st.button(
        "Agregar punto"
    ):

        punto = {

            "nombre": nombre,

            "tipo": tipo,

            "latitud": latitud,

            "longitud": longitud,

            "descripcion": descripcion

        }

        st.session_state[
            "puntos_red"
        ].append(punto)

        st.success(
            "Punto agregado correctamente"
        )

    st.dataframe(

        st.session_state[
            "puntos_red"
        ],

        width='stretch'

    )
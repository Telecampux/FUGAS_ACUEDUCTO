# cartografia/alertas.py

import streamlit as st

from datetime import datetime


NIVELES_ALERTA = [

    "Baja",
    "Media",
    "Alta",
    "Crítica"

]


TIPOS_ALERTA = [

    "Fuga probable",
    "Sensor desconectado",
    "Ruido anómalo",
    "Presión irregular",
    "Golpe de ariete",
    "Nodo aislado",
    "Otro"

]


def inicializar_alertas():

    if "alertas_red" not in st.session_state:

        st.session_state["alertas_red"] = []


def registrar_alerta():

    inicializar_alertas()

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    nombres = [

        p["nombre"]
        for p in puntos

    ]

    st.subheader(
        "🚨 Registro de alertas"
    )

    punto = st.selectbox(
        "Punto asociado",
        nombres
    )

    tipo = st.selectbox(
        "Tipo alerta",
        TIPOS_ALERTA
    )

    nivel = st.selectbox(
        "Nivel criticidad",
        NIVELES_ALERTA
    )

    descripcion = st.text_area(
        "Descripción"
    )

    responsable = st.text_input(
        "Responsable"
    )

    if st.button(
        "Registrar alerta"
    ):

        alerta = {

            "fecha": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "punto": punto,

            "tipo": tipo,

            "nivel": nivel,

            "descripcion": descripcion,

            "responsable": responsable,

            "estado": "Activa"

        }

        st.session_state[
            "alertas_red"
        ].append(alerta)

        st.success(
            "Alerta registrada"
        )

    st.dataframe(

        st.session_state[
            "alertas_red"
        ],

        width='stretch'

    )


def cerrar_alerta():

    inicializar_alertas()

    alertas = st.session_state.get(
        "alertas_red",
        []
    )

    if len(alertas) == 0:

        st.info(
            "No existen alertas"
        )

        return

    opciones = [

        f"{i} - {a['tipo']} - {a['punto']}"

        for i, a in enumerate(alertas)

        if a["estado"] == "Activa"

    ]

    if len(opciones) == 0:

        st.success(
            "No existen alertas activas"
        )

        return

    seleccion = st.selectbox(
        "Seleccionar alerta",
        opciones
    )

    indice = int(
        seleccion.split("-")[0].strip()
    )

    if st.button(
        "Cerrar alerta"
    ):

        st.session_state[
            "alertas_red"
        ][indice]["estado"] = "Cerrada"

        st.success(
            "Alerta cerrada"
        )


def dashboard_alertas():

    inicializar_alertas()

    alertas = st.session_state.get(
        "alertas_red",
        []
    )

    st.subheader(
        "📊 Estado alertas"
    )

    activas = [

        a for a in alertas
        if a["estado"] == "Activa"

    ]

    cerradas = [

        a for a in alertas
        if a["estado"] == "Cerrada"

    ]

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Alertas activas",
            len(activas)
        )

    with col2:

        st.metric(
            "Alertas cerradas",
            len(cerradas)
        )

    if len(alertas) > 0:

        st.dataframe(
            alertas,
            width='stretch'
        )
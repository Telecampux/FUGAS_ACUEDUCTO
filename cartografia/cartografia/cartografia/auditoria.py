# cartografia/auditoria.py

import streamlit as st

from datetime import datetime


def inicializar_auditoria():

    if "auditoria_cartografia" not in st.session_state:

        st.session_state["auditoria_cartografia"] = []


def registrar_evento(

    accion,
    elemento,
    descripcion

):

    inicializar_auditoria()

    evento = {

        "fecha": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "accion": accion,

        "elemento": elemento,

        "descripcion": descripcion

    }

    st.session_state[
        "auditoria_cartografia"
    ].append(evento)


def visualizar_auditoria():

    inicializar_auditoria()

    st.subheader(
        "📋 Auditoría cartográfica"
    )

    registros = st.session_state.get(
        "auditoria_cartografia",
        []
    )

    if len(registros) == 0:

        st.info(
            "No existen eventos registrados"
        )

        return

    st.dataframe(
        registros,
        width='stretch'
    )


def limpiar_auditoria():

    st.session_state[
        "auditoria_cartografia"
    ] = []

    st.success(
        "Auditoría eliminada"
    )
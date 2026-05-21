# cartografia/sectorizacion.py

import streamlit as st


def crear_sector(

    nombre_sector,
    puntos_sector

):

    sectores = st.session_state.get(
        "sectores_red",
        []
    )

    sector = {

        "nombre": nombre_sector,

        "puntos": puntos_sector

    }

    sectores.append(
        sector
    )

    st.session_state["sectores_red"] = sectores


def obtener_sectores():

    return st.session_state.get(
        "sectores_red",
        []
    )


def visualizar_sectorizacion():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    if len(puntos) == 0:

        st.warning(
            "No existen puntos registrados"
        )

        return

    if "sectores_red" not in st.session_state:

        st.session_state["sectores_red"] = []

    nombres_puntos = [

        p["nombre"]
        for p in puntos

    ]

    st.subheader(
        "🧩 Sectorización operacional"
    )

    nombre_sector = st.text_input(
        "Nombre del sector"
    )

    puntos_sector = st.multiselect(

        "Seleccionar puntos",

        nombres_puntos

    )

    if st.button(
        "Crear sector"
    ):

        crear_sector(

            nombre_sector,
            puntos_sector

        )

        st.success(
            "Sector creado correctamente"
        )

    sectores = obtener_sectores()

    if len(sectores) > 0:

        st.markdown(
            "### Sectores registrados"
        )

        st.dataframe(
            sectores,
            width='stretch'
        )
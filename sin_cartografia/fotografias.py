# cartografia/fotografias.py

import streamlit as st

from datetime import datetime


def inicializar_fotografias():

    if "fotografias_red" not in st.session_state:

        st.session_state[
            "fotografias_red"
        ] = []


def registrar_fotografia():

    inicializar_fotografias()

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    if len(puntos) == 0:

        st.warning(
            "No existen puntos registrados"
        )

        return

    nombres = [

        p["nombre"]
        for p in puntos

    ]

    st.subheader(
        "📸 Registro fotográfico"
    )

    punto = st.selectbox(
        "Punto asociado",
        nombres
    )

    descripcion = st.text_area(
        "Descripción"
    )

    imagen = st.file_uploader(

        "Seleccionar imagen",

        type=[
            "jpg",
            "jpeg",
            "png"
        ]

    )

    autor = st.text_input(
        "Responsable"
    )

    if st.button(
        "Guardar fotografía"
    ):

        if imagen is None:

            st.warning(
                "Debe seleccionar una imagen"
            )

            return

        registro = {

            "fecha": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "punto": punto,

            "descripcion": descripcion,

            "nombre_archivo": imagen.name,

            "autor": autor

        }

        st.session_state[
            "fotografias_red"
        ].append(registro)

        st.success(
            "Fotografía registrada"
        )

        st.image(
            imagen,
            caption=imagen.name
        )

    if len(

        st.session_state[
            "fotografias_red"
        ]

    ) > 0:

        st.dataframe(

            st.session_state[
                "fotografias_red"
            ],

            width='stretch'

        )


def visualizar_galeria():

    inicializar_fotografias()

    registros = st.session_state.get(
        "fotografias_red",
        []
    )

    st.subheader(
        "🖼️ Galería fotográfica"
    )

    if len(registros) == 0:

        st.info(
            "No existen fotografías"
        )

        return

    st.dataframe(
        registros,
        width='stretch'
    )
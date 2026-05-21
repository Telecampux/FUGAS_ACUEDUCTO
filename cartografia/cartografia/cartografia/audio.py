# cartografia/audio.py

import streamlit as st

from datetime import datetime


TIPOS_AUDIO = [

    "Ruido fuga",
    "Ruido ambiental",
    "Vibración",
    "Golpe ariete",
    "Inspección",
    "Otro"

]


def inicializar_audio():

    if "audios_red" not in st.session_state:

        st.session_state[
            "audios_red"
        ] = []


def registrar_audio():

    inicializar_audio()

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
        "🎙️ Registro acústico"
    )

    punto = st.selectbox(
        "Punto asociado",
        nombres
    )

    tipo_audio = st.selectbox(
        "Tipo audio",
        TIPOS_AUDIO
    )

    descripcion = st.text_area(
        "Descripción"
    )

    audio = st.file_uploader(

        "Seleccionar audio",

        type=[
            "wav",
            "mp3",
            "ogg"
        ]

    )

    responsable = st.text_input(
        "Responsable"
    )

    if st.button(
        "Guardar audio"
    ):

        if audio is None:

            st.warning(
                "Debe seleccionar un archivo"
            )

            return

        registro = {

            "fecha": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "punto": punto,

            "tipo": tipo_audio,

            "descripcion": descripcion,

            "archivo": audio.name,

            "responsable": responsable

        }

        st.session_state[
            "audios_red"
        ].append(registro)

        st.success(
            "Audio registrado"
        )

        st.audio(audio)

    if len(

        st.session_state[
            "audios_red"
        ]

    ) > 0:

        st.dataframe(

            st.session_state[
                "audios_red"
            ],

            width='stretch'

        )


def visualizar_historial_audio():

    inicializar_audio()

    registros = st.session_state.get(
        "audios_red",
        []
    )

    st.subheader(
        "📚 Histórico acústico"
    )

    if len(registros) == 0:

        st.info(
            "No existen registros"
        )

        return

    st.dataframe(
        registros,
        width='stretch'
    )
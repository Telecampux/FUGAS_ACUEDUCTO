# cartografia/persistencia.py

import json
import os

import streamlit as st


DIRECTORIO_DATOS = "data"


def crear_directorio():

    if not os.path.exists(
        DIRECTORIO_DATOS
    ):

        os.makedirs(
            DIRECTORIO_DATOS
        )


def guardar_estado_cartografia():

    crear_directorio()

    estructura = {

        "puntos_red":

        st.session_state.get(
            "puntos_red",
            []
        ),

        "conexiones_red":

        st.session_state.get(
            "conexiones_red",
            []
        ),

        "sectores_red":

        st.session_state.get(
            "sectores_red",
            []
        ),

        "sensores_geo":

        st.session_state.get(
            "sensores_geo",
            []
        ),

        "inspecciones_red":

        st.session_state.get(
            "inspecciones_red",
            []
        )

    }

    ruta = os.path.join(

        DIRECTORIO_DATOS,

        "cartografia_operacional.json"

    )

    with open(

        ruta,

        "w",

        encoding="utf-8"

    ) as archivo:

        json.dump(

            estructura,

            archivo,

            indent=4,

            ensure_ascii=False

        )

    return ruta


def cargar_estado_cartografia():

    ruta = os.path.join(

        DIRECTORIO_DATOS,

        "cartografia_operacional.json"

    )

    if not os.path.exists(
        ruta
    ):

        return False

    with open(

        ruta,

        "r",

        encoding="utf-8"

    ) as archivo:

        estructura = json.load(
            archivo
        )

    for clave, valor in estructura.items():

        st.session_state[clave] = valor

    return True
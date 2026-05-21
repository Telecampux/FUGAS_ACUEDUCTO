# cartografia/sincronizacion.py

import json
import requests

import streamlit as st


API_URL = "http://127.0.0.1:8000/cartografia"


def enviar_cartografia_api():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    conexiones = st.session_state.get(
        "conexiones_red",
        []
    )

    sectores = st.session_state.get(
        "sectores_red",
        []
    )

    estructura = {

        "puntos": puntos,

        "conexiones": conexiones,

        "sectores": sectores

    }

    try:

        response = requests.post(

            API_URL,

            json=estructura,

            timeout=10

        )

        if response.status_code == 200:

            st.success(
                "Cartografía sincronizada"
            )

        else:

            st.error(
                f"Error API: {response.status_code}"
            )

    except Exception as error:

        st.error(
            f"Error sincronización: {error}"
        )


def exportar_respaldo_local():

    estructura = {

        "puntos":

        st.session_state.get(
            "puntos_red",
            []
        ),

        "conexiones":

        st.session_state.get(
            "conexiones_red",
            []
        ),

        "sectores":

        st.session_state.get(
            "sectores_red",
            []
        )

    }

    json_data = json.dumps(

        estructura,

        indent=4,

        ensure_ascii=False

    )

    st.download_button(

        label="Descargar respaldo",

        data=json_data,

        file_name="respaldo_cartografia.json",

        mime="application/json"

    )


def panel_sincronizacion():

    st.subheader(
        "🔄 Sincronización cartográfica"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Enviar API"
        ):

            enviar_cartografia_api()

    with col2:

        exportar_respaldo_local()
# cartografia/almacenamiento.py

import json
import streamlit as st


def guardar_cartografia():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    conexiones = st.session_state.get(
        "conexiones_red",
        []
    )

    estructura = {

        "puntos": puntos,
        "conexiones": conexiones

    }

    json_data = json.dumps(

        estructura,

        indent=4,
        ensure_ascii=False

    )

    st.subheader(
        "💾 Exportación cartográfica"
    )

    st.download_button(

        label="Descargar cartografía JSON",

        data=json_data,

        file_name="cartografia_operacional.json",

        mime="application/json"

    )

    st.code(
        json_data,
        language="json"
    )
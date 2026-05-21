# ============================================================
# ARCHIVO:
# cartografia/captura_puntos.py
# ============================================================

import streamlit as st

# ============================================================
# REGISTRO MANUAL DE PUNTOS
# ============================================================

def registrar_punto():

    st.markdown(
        "### Captura manual de puntos"
    )

    col1, col2 = st.columns(2)

    with col1:

        latitud = st.number_input(

            "Latitud",

            format="%.6f",

            key="latitud_punto"

        )

    with col2:

        longitud = st.number_input(

            "Longitud",

            format="%.6f",

            key="longitud_punto"

        )

    nombre = st.text_input(

        "Nombre del punto",

        key="nombre_punto"

    )

    if st.button(

        "Registrar punto"

    ):

        punto = {

            "nombre": nombre,

            "latitud": latitud,

            "longitud": longitud

        }

        if "puntos_capturados" not in st.session_state:

            st.session_state[
                "puntos_capturados"
            ] = []

        st.session_state[
            "puntos_capturados"
        ].append(
            punto
        )

        st.success(
            "Punto registrado correctamente"
        )

    # ========================================================
    # VISUALIZACION
    # ========================================================

    if (

        "puntos_capturados"
        in st.session_state

        and

        len(
            st.session_state[
                "puntos_capturados"
            ]
        ) > 0

    ):

        st.markdown(
            "### Puntos registrados"
        )

        st.dataframe(

            st.session_state[
                "puntos_capturados"
            ],

            width='stretch'

        )
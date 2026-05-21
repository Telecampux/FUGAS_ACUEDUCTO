# ============================================================
# ARCHIVO:
# cartografia/conexiones.py
# ============================================================

import streamlit as st

# ============================================================
# CONEXION ENTRE PUNTOS
# ============================================================

def conectar_puntos():

    st.markdown(
        "### Conexion de puntos"
    )

    if (

        "puntos_capturados"
        not in st.session_state

        or

        len(
            st.session_state[
                "puntos_capturados"
            ]
        ) < 2

    ):

        st.warning(
            "Debe registrar minimo dos puntos"
        )

        return None

    puntos = st.session_state[
        "puntos_capturados"
    ]

    nombres = [

        p["nombre"]

        for p in puntos

    ]

    col1, col2 = st.columns(2)

    with col1:

        origen = st.selectbox(

            "Punto origen",

            nombres,

            key="origen_conexion"

        )

    with col2:

        destino = st.selectbox(

            "Punto destino",

            nombres,

            key="destino_conexion"

        )

    if st.button(

        "Crear conexion"

    ):

        conexion = {

            "origen": origen,

            "destino": destino

        }

        if "conexiones" not in st.session_state:

            st.session_state[
                "conexiones"
            ] = []

        st.session_state[
            "conexiones"
        ].append(
            conexion
        )

        st.success(
            "Conexion creada correctamente"
        )

    # ========================================================
    # VISUALIZACION
    # ========================================================

    if (

        "conexiones"
        in st.session_state

        and

        len(
            st.session_state[
                "conexiones"
            ]
        ) > 0

    ):

        st.markdown(
            "### Conexiones registradas"
        )

        st.dataframe(

            st.session_state[
                "conexiones"
            ],

            width='stretch'

        )
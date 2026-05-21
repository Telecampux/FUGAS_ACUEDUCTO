# ============================================================
# ARCHIVO:
# cartografia/conexiones.py
# ============================================================

import streamlit as st

from sin_cartografia.captura.conexiones import (
    MATERIALES_TUBERIA,
    TIPOS_TUBERIA
)

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

            index=1,

            key="destino_conexion"

        )

    tipo_tuberia = st.selectbox(
        "Tipo de tuberia",
        TIPOS_TUBERIA,
        key="tipo_tuberia_conexion"
    )

    material = st.selectbox(
        "Material de tuberia",
        MATERIALES_TUBERIA,
        key="material_tuberia_conexion"
    )

    if st.button(

        "Crear conexion"

    ):

        conexion = {

            "origen": origen,

            "destino": destino,

            "material": material,

            "tipo_red": tipo_tuberia

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

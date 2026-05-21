# cartografia/validacion.py

import streamlit as st


def validar_red():

    errores = []

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    conexiones = st.session_state.get(
        "conexiones_red",
        []
    )

    # ============================================================
    # VALIDAR EXISTENCIA DE PUNTOS
    # ============================================================

    if len(puntos) == 0:

        errores.append(
            "No existen puntos registrados"
        )

    # ============================================================
    # VALIDAR CONEXIONES
    # ============================================================

    for conexion in conexiones:

        origen = conexion["origen"]

        destino = conexion["destino"]

        # --------------------------------------------------------
        # MISMO PUNTO
        # --------------------------------------------------------

        if origen == destino:

            errores.append(

                f"""
                Conexión inválida:
                {origen} conectado consigo mismo
                """

            )

        # --------------------------------------------------------
        # DISTANCIA
        # --------------------------------------------------------

        if conexion["distancia"] <= 0:

            errores.append(

                f"""
                Distancia inválida entre
                {origen} y {destino}
                """

            )

        # --------------------------------------------------------
        # DIÁMETRO
        # --------------------------------------------------------

        if conexion["diametro"] <= 0:

            errores.append(

                f"""
                Diámetro inválido entre
                {origen} y {destino}
                """

            )

    # ============================================================
    # VALIDAR DUPLICADOS
    # ============================================================

    nombres = [

        p["nombre"]
        for p in puntos

    ]

    if len(nombres) != len(set(nombres)):

        errores.append(
            "Existen nombres de puntos duplicados"
        )

    return errores
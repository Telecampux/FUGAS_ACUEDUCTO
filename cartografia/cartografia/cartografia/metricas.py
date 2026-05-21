# cartografia/metricas.py

import streamlit as st

from cartografia.topologia import (
    construir_grafo
)


def calcular_densidad_red():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    conexiones = st.session_state.get(
        "conexiones_red",
        []
    )

    total_puntos = len(puntos)

    if total_puntos == 0:

        return 0

    densidad = len(conexiones) / total_puntos

    return round(
        densidad,
        2
    )


def calcular_promedio_conectividad():

    grafo = construir_grafo()

    if len(grafo) == 0:

        return 0

    grados = [

        len(conexiones)
        for conexiones in grafo.values()

    ]

    promedio = sum(grados) / len(grados)

    return round(
        promedio,
        2
    )


def calcular_porcentaje_nodos_aislados():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    grafo = construir_grafo()

    if len(puntos) == 0:

        return 0

    aislados = 0

    for punto in puntos:

        nombre = punto["nombre"]

        if nombre not in grafo:

            aislados += 1

            continue

        if len(grafo[nombre]) == 0:

            aislados += 1

    porcentaje = (

        aislados / len(puntos)

    ) * 100

    return round(
        porcentaje,
        2
    )


def calcular_indice_sectorizacion():

    sectores = st.session_state.get(
        "sectores_red",
        []
    )

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    if len(puntos) == 0:

        return 0

    puntos_sectorizados = 0

    for sector in sectores:

        puntos_sectorizados += len(
            sector["puntos"]
        )

    indice = (

        puntos_sectorizados / len(puntos)

    ) * 100

    return round(
        indice,
        2
    )
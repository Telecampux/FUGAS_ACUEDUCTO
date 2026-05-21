# cartografia/topologia.py

import streamlit as st


def construir_grafo():

    conexiones = st.session_state.get(
        "conexiones_red",
        []
    )

    grafo = {}

    for conexion in conexiones:

        origen = conexion["origen"]

        destino = conexion["destino"]

        if origen not in grafo:

            grafo[origen] = []

        if destino not in grafo:

            grafo[destino] = []

        grafo[origen].append(destino)

        grafo[destino].append(origen)

    return grafo


def obtener_nodos_aislados():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    grafo = construir_grafo()

    aislados = []

    for punto in puntos:

        nombre = punto["nombre"]

        if nombre not in grafo:

            aislados.append(nombre)

            continue

        if len(grafo[nombre]) == 0:

            aislados.append(nombre)

    return aislados


def calcular_grado_nodos():

    grafo = construir_grafo()

    grados = {}

    for nodo, conexiones in grafo.items():

        grados[nodo] = len(conexiones)

    return grados


def validar_conectividad():

    aislados = obtener_nodos_aislados()

    if len(aislados) == 0:

        return {

            "estado": True,

            "mensaje":
            "Todos los nodos tienen conectividad"

        }

    return {

        "estado": False,

        "mensaje":
        f"Nodos aislados encontrados: {aislados}"

    }
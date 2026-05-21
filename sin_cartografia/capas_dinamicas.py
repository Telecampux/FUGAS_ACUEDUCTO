# cartografia/capas_dinamicas.py

import streamlit as st
import folium

from streamlit_folium import st_folium

from cartografia.capas import (
    agregar_capa_puntos,
    agregar_capa_conexiones
)


def visualizar_capas_dinamicas():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    conexiones = st.session_state.get(
        "conexiones_red",
        []
    )

    sensores = st.session_state.get(
        "sensores_geo",
        []
    )

    alertas = st.session_state.get(
        "alertas_red",
        []
    )

    if len(puntos) == 0:

        st.warning(
            "No existen puntos registrados"
        )

        return

    st.subheader(
        "🗺️ Capas dinámicas"
    )

    mostrar_puntos = st.checkbox(
        "Mostrar puntos",
        value=True
    )

    mostrar_conexiones = st.checkbox(
        "Mostrar conexiones",
        value=True
    )

    mostrar_sensores = st.checkbox(
        "Mostrar sensores",
        value=True
    )

    mostrar_alertas = st.checkbox(
        "Mostrar alertas",
        value=True
    )

    # ============================================================
    # MAPA BASE
    # ============================================================

    lat_media = sum(

        p["latitud"]
        for p in puntos

    ) / len(puntos)

    lon_media = sum(

        p["longitud"]
        for p in puntos

    ) / len(puntos)

    mapa = folium.Map(

        location=[
            lat_media,
            lon_media
        ],

        zoom_start=16

    )

    # ============================================================
    # CAPA PUNTOS
    # ============================================================

    if mostrar_puntos:

        agregar_capa_puntos(
            mapa,
            puntos
        )

    # ============================================================
    # CAPA CONEXIONES
    # ============================================================

    if mostrar_conexiones:

        agregar_capa_conexiones(

            mapa,
            puntos,
            conexiones

        )

    # ============================================================
    # CAPA SENSORES
    # ============================================================

    if mostrar_sensores:

        for sensor in sensores:

            punto = next(

                p for p in puntos
                if p["nombre"] == sensor["punto"]

            )

            folium.CircleMarker(

                [

                    punto["latitud"],
                    punto["longitud"]

                ],

                radius=8,

                tooltip=f"""

                Sensor:
                {sensor['sensor']}

                """,

                color="orange",

                fill=True

            ).add_to(mapa)

    # ============================================================
    # CAPA ALERTAS
    # ============================================================

    if mostrar_alertas:

        for alerta in alertas:

            if alerta["estado"] != "Activa":

                continue

            punto = next(

                p for p in puntos
                if p["nombre"] == alerta["punto"]

            )

            folium.Circle(

                [

                    punto["latitud"],
                    punto["longitud"]

                ],

                radius=20,

                tooltip=f"""

                ALERTA:
                {alerta['tipo']}

                """,

                color="red",

                fill=True

            ).add_to(mapa)

    # ============================================================
    # MOSTRAR
    # ============================================================

    st_folium(

        mapa,

        width='stretch',

        height=700

    )
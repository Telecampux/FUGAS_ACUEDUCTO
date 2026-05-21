# cartografia/mapa.py

import streamlit as st
import folium

from streamlit_folium import st_folium


def visualizar_mapa():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    if len(puntos) == 0:

        st.info(
            "No existen puntos registrados"
        )

        return

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
    # MARCADORES
    # ============================================================

    for punto in puntos:

        popup_texto = f"""

        <b>{punto['nombre']}</b><br>
        Tipo: {punto['tipo']}<br>
        {punto['descripcion']}

        """

        folium.Marker(

            [
                punto["latitud"],
                punto["longitud"]
            ],

            popup=popup_texto

        ).add_to(mapa)

    # ============================================================
    # CONEXIONES
    # ============================================================

    conexiones = st.session_state.get(
        "conexiones_red",
        []
    )

    for conexion in conexiones:

        origen = next(

            p for p in puntos
            if p["nombre"] == conexion["origen"]

        )

        destino = next(

            p for p in puntos
            if p["nombre"] == conexion["destino"]

        )

        folium.PolyLine(

            [

                [
                    origen["latitud"],
                    origen["longitud"]
                ],

                [
                    destino["latitud"],
                    destino["longitud"]
                ]

            ],

            tooltip=f"""

            Material: {conexion['material']}
            | Distancia: {conexion['distancia']} m

            """

        ).add_to(mapa)

    # ============================================================
    # MOSTRAR MAPA
    # ============================================================

    st_folium(

        mapa,

        width='stretch',
        height=600

    )
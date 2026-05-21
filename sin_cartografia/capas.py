# cartografia/capas.py

import streamlit as st
import folium


TIPOS_COLORES = {

    "Hidrante": "red",
    "Válvula": "blue",
    "Tanque": "green",
    "Bomba": "purple",
    "Sensor": "orange",
    "Caja": "cadetblue",
    "Empalme": "darkred",
    "Otro": "gray"

}


def agregar_capa_puntos(

    mapa,
    puntos

):

    for punto in puntos:

        color = TIPOS_COLORES.get(
            punto["tipo"],
            "gray"
        )

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

            popup=popup_texto,

            icon=folium.Icon(
                color=color
            )

        ).add_to(mapa)


def agregar_capa_conexiones(

    mapa,
    puntos,
    conexiones

):

    for conexion in conexiones:

        origen = next(

            p for p in puntos
            if p["nombre"] == conexion["origen"]

        )

        destino = next(

            p for p in puntos
            if p["nombre"] == conexion["destino"]

        )

        tooltip_texto = f"""

        Material: {conexion['material']}
        | Distancia: {conexion['distancia']} m
        | Diámetro: {conexion['diametro']} mm

        """

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

            tooltip=tooltip_texto,

            weight=4

        ).add_to(mapa)
import folium
import streamlit as st

from streamlit_folium import st_folium


def visualizar_mapa(
    puntos,
    conexiones
):

    puntos_con_gps = [
        p for p in puntos
        if p.get("gps")
    ]

    if puntos_con_gps:
        centro = [
            sum(p["gps"]["lat"] for p in puntos_con_gps) / len(puntos_con_gps),
            sum(p["gps"]["lon"] for p in puntos_con_gps) / len(puntos_con_gps)
        ]
    else:
        centro = [4.60971, -74.08175]
        st.info("Aun no hay nodos con GPS para centrar el mapa")

    mapa = folium.Map(
        location=centro,
        zoom_start=15
    )

    for punto in puntos:

        gps = punto.get("gps")

        if gps is None:
            continue

        lat = gps["lat"]
        lon = gps["lon"]

        nombre = punto.get(
            "nombre",
            "Nodo"
        )

        tipo = punto.get(
            "tipo",
            "Sin tipo"
        )

        ubicacion = " | ".join(
            valor for valor in [
                gps.get("municipio"),
                gps.get("departamento"),
                gps.get("pais")
            ]
            if valor
        )

        popup = f"{nombre} | {tipo}"

        if ubicacion:
            popup = f"{popup} | {ubicacion}"

        folium.Marker(
            [lat, lon],
            tooltip=nombre,
            popup=popup,
            icon=folium.Icon(color="blue")
        ).add_to(mapa)

    for conexion in conexiones:

        origen_nombre = conexion.get("origen")
        destino_nombre = conexion.get("destino")

        origen = next(
            (
                p for p in puntos
                if p["nombre"] == origen_nombre
            ),
            None
        )

        destino = next(
            (
                p for p in puntos
                if p["nombre"] == destino_nombre
            ),
            None
        )

        if origen is None or destino is None:
            continue

        gps_o = origen.get("gps")
        gps_d = destino.get("gps")

        if gps_o is None or gps_d is None:
            continue

        folium.PolyLine(
            [
                [
                    gps_o["lat"],
                    gps_o["lon"]
                ],
                [
                    gps_d["lat"],
                    gps_d["lon"]
                ]
            ],
            color="red",
            weight=3
        ).add_to(mapa)

    st_folium(
        mapa,
        width=1200,
        height=600
    )

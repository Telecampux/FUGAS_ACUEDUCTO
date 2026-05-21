# cartografia/geojson_avanzado.py

import json

import streamlit as st


def exportar_geojson_avanzado():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    conexiones = st.session_state.get(
        "conexiones_red",
        []
    )

    features = []

    # ============================================================
    # FEATURES PUNTOS
    # ============================================================

    for punto in puntos:

        feature = {

            "type": "Feature",

            "geometry": {

                "type": "Point",

                "coordinates": [

                    punto["longitud"],
                    punto["latitud"]

                ]

            },

            "properties": {

                "nombre": punto["nombre"],

                "tipo": punto["tipo"],

                "descripcion": punto[
                    "descripcion"
                ]

            }

        }

        features.append(
            feature
        )

    # ============================================================
    # FEATURES CONEXIONES
    # ============================================================

    for conexion in conexiones:

        origen = next(

            p for p in puntos
            if p["nombre"] == conexion["origen"]

        )

        destino = next(

            p for p in puntos
            if p["nombre"] == conexion["destino"]

        )

        feature = {

            "type": "Feature",

            "geometry": {

                "type": "LineString",

                "coordinates": [

                    [

                        origen["longitud"],
                        origen["latitud"]

                    ],

                    [

                        destino["longitud"],
                        destino["latitud"]

                    ]

                ]

            },

            "properties": {

                "origen": conexion["origen"],

                "destino": conexion["destino"],

                "material": conexion[
                    "material"
                ],

                "diametro": conexion[
                    "diametro"
                ],

                "distancia": conexion[
                    "distancia"
                ]

            }

        }

        features.append(
            feature
        )

    # ============================================================
    # GEOJSON FINAL
    # ============================================================

    geojson = {

        "type": "FeatureCollection",

        "features": features

    }

    geojson_data = json.dumps(

        geojson,

        indent=4,

        ensure_ascii=False

    )

    st.subheader(
        "🌎 Exportación GeoJSON avanzada"
    )

    st.download_button(

        label="Descargar GeoJSON avanzado",

        data=geojson_data,

        file_name="cartografia_avanzada.geojson",

        mime="application/geo+json"

    )

    st.code(
        geojson_data,
        language="json"
    )
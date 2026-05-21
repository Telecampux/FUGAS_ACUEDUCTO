# cartografia/exportacion.py

import json
import streamlit as st


def exportar_geojson():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    features = []

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
                "descripcion": punto["descripcion"]

            }

        }

        features.append(
            feature
        )

    geojson = {

        "type": "FeatureCollection",

        "features": features

    }

    geojson_data = json.dumps(

        geojson,

        indent=4,
        ensure_ascii=False

    )

    st.download_button(

        label="Descargar GeoJSON",

        data=geojson_data,

        file_name="cartografia.geojson",

        mime="application/geo+json"

    )

    st.code(
        geojson_data,
        language="json"
    )
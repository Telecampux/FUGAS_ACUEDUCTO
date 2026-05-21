# cartografia/shapefile.py

import os
import zipfile
import tempfile

import shapefile

import streamlit as st


def exportar_shapefile():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    conexiones = st.session_state.get(
        "conexiones_red",
        []
    )

    if len(puntos) == 0:

        st.warning(
            "No existen puntos registrados"
        )

        return

    st.subheader(
        "🗂️ Exportación Shapefile"
    )

    with tempfile.TemporaryDirectory() as temp_dir:

        # ========================================================
        # SHAPE PUNTOS
        # ========================================================

        ruta_puntos = os.path.join(
            temp_dir,
            "puntos"
        )

        shp_puntos = shapefile.Writer(
            ruta_puntos
        )

        shp_puntos.field(
            "nombre",
            "C"
        )

        shp_puntos.field(
            "tipo",
            "C"
        )

        for punto in puntos:

            shp_puntos.point(

                punto["longitud"],
                punto["latitud"]

            )

            shp_puntos.record(

                punto["nombre"],
                punto["tipo"]

            )

        shp_puntos.close()

        # ========================================================
        # SHAPE CONEXIONES
        # ========================================================

        ruta_conexiones = os.path.join(
            temp_dir,
            "conexiones"
        )

        shp_conexiones = shapefile.Writer(
            ruta_conexiones,
            shapeType=shapefile.POLYLINE
        )

        shp_conexiones.field(
            "material",
            "C"
        )

        shp_conexiones.field(
            "diametro",
            "N"
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

            shp_conexiones.line(

                [[

                    [

                        origen["longitud"],
                        origen["latitud"]

                    ],

                    [

                        destino["longitud"],
                        destino["latitud"]

                    ]

                ]]

            )

            shp_conexiones.record(

                conexion["material"],

                conexion["diametro"]

            )

        shp_conexiones.close()

        # ========================================================
        # ZIP FINAL
        # ========================================================

        ruta_zip = os.path.join(
            temp_dir,
            "cartografia_shapefile.zip"
        )

        with zipfile.ZipFile(

            ruta_zip,

            "w",

            zipfile.ZIP_DEFLATED

        ) as zipf:

            for archivo in os.listdir(
                temp_dir
            ):

                if archivo.endswith(

                    (
                        ".shp",
                        ".shx",
                        ".dbf"
                    )

                ):

                    zipf.write(

                        os.path.join(
                            temp_dir,
                            archivo
                        ),

                        archivo

                    )

        with open(

            ruta_zip,

            "rb"

        ) as archivo_zip:

            st.download_button(

                label="Descargar Shapefile",

                data=archivo_zip,

                file_name="cartografia_shapefile.zip",

                mime="application/zip"

            )
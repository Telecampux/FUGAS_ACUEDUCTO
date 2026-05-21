# cartografia/postgis.py

import streamlit as st

import psycopg2


def conectar_postgis(

    host,
    puerto,
    base_datos,
    usuario,
    password

):

    conexion = psycopg2.connect(

        host=host,

        port=puerto,

        dbname=base_datos,

        user=usuario,

        password=password

    )

    return conexion


def crear_tablas_postgis(

    conexion

):

    cursor = conexion.cursor()

    # ============================================================
    # EXTENSIÓN POSTGIS
    # ============================================================

    cursor.execute(

        """
        CREATE EXTENSION IF NOT EXISTS postgis;
        """

    )

    # ============================================================
    # TABLA PUNTOS
    # ============================================================

    cursor.execute(

        """
        CREATE TABLE IF NOT EXISTS puntos_red (

            id SERIAL PRIMARY KEY,

            nombre TEXT,

            tipo TEXT,

            descripcion TEXT,

            geom GEOMETRY(Point, 4326)

        );
        """

    )

    # ============================================================
    # TABLA CONEXIONES
    # ============================================================

    cursor.execute(

        """
        CREATE TABLE IF NOT EXISTS conexiones_red (

            id SERIAL PRIMARY KEY,

            origen TEXT,

            destino TEXT,

            material TEXT,

            diametro NUMERIC,

            distancia NUMERIC,

            geom GEOMETRY(LineString, 4326)

        );
        """

    )

    conexion.commit()

    cursor.close()


def exportar_postgis(

    conexion

):

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    conexiones = st.session_state.get(
        "conexiones_red",
        []
    )

    cursor = conexion.cursor()

    # ============================================================
    # INSERTAR PUNTOS
    # ============================================================

    for punto in puntos:

        cursor.execute(

            """
            INSERT INTO puntos_red (

                nombre,
                tipo,
                descripcion,
                geom

            )

            VALUES (

                %s,
                %s,
                %s,

                ST_SetSRID(
                    ST_MakePoint(%s, %s),
                    4326
                )

            );
            """,

            (

                punto["nombre"],

                punto["tipo"],

                punto["descripcion"],

                punto["longitud"],

                punto["latitud"]

            )

        )

    # ============================================================
    # INSERTAR CONEXIONES
    # ============================================================

    for conexion_item in conexiones:

        origen = next(

            p for p in puntos
            if p["nombre"]
            == conexion_item["origen"]

        )

        destino = next(

            p for p in puntos
            if p["nombre"]
            == conexion_item["destino"]

        )

        cursor.execute(

            """
            INSERT INTO conexiones_red (

                origen,
                destino,
                material,
                diametro,
                distancia,
                geom

            )

            VALUES (

                %s,
                %s,
                %s,
                %s,
                %s,

                ST_SetSRID(

                    ST_MakeLine(

                        ST_MakePoint(%s, %s),

                        ST_MakePoint(%s, %s)

                    ),

                    4326

                )

            );
            """,

            (

                conexion_item["origen"],

                conexion_item["destino"],

                conexion_item["material"],

                conexion_item["diametro"],

                conexion_item["distancia"],

                origen["longitud"],

                origen["latitud"],

                destino["longitud"],

                destino["latitud"]

            )

        )

    conexion.commit()

    cursor.close()

    st.success(
        "Datos exportados a PostGIS"
    )


def interfaz_postgis():

    st.subheader(
        "🗄️ Integración PostGIS"
    )

    host = st.text_input(
        "Host",
        value="localhost"
    )

    puerto = st.number_input(
        "Puerto",
        value=5432
    )

    base_datos = st.text_input(
        "Base datos"
    )

    usuario = st.text_input(
        "Usuario"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button(
        "Conectar PostGIS"
    ):

        try:

            conexion = conectar_postgis(

                host,
                puerto,
                base_datos,
                usuario,
                password

            )

            crear_tablas_postgis(
                conexion
            )

            exportar_postgis(
                conexion
            )

            conexion.close()

        except Exception as error:

            st.error(
                f"Error PostGIS: {error}"
            )
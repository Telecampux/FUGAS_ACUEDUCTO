# cartografia/correlacion_geo.py

import streamlit as st

from cartografia.utilidades import (
    calcular_distancia_haversine,
    buscar_punto_por_nombre
)


VELOCIDADES_REFERENCIA = {

    "PVC": 350,
    "PEAD": 300,
    "Hierro dúctil": 1000,
    "Acero": 1200,
    "Asbesto cemento": 700,
    "Desconocido": 500

}


def calcular_tiempo_propagacion(

    distancia,
    velocidad

):

    if velocidad <= 0:

        return 0

    return round(
        distancia / velocidad,
        6
    )


def ejecutar_correlacion_geografica():

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

    if len(sensores) < 2:

        st.warning(
            "Debe registrar mínimo dos sensores"
        )

        return

    st.header(
        "🎧🌎 Correlación Geográfica"
    )

    nombres = [

        s["sensor"]
        for s in sensores

    ]

    sensor_1 = st.selectbox(
        "Sensor A",
        nombres
    )

    sensor_2 = st.selectbox(
        "Sensor B",
        nombres,
        index=1
    )

    s1 = next(

        s for s in sensores
        if s["sensor"] == sensor_1

    )

    s2 = next(

        s for s in sensores
        if s["sensor"] == sensor_2

    )

    punto_1 = buscar_punto_por_nombre(

        puntos,
        s1["punto"]

    )

    punto_2 = buscar_punto_por_nombre(

        puntos,
        s2["punto"]

    )

    distancia = calcular_distancia_haversine(

        punto_1["latitud"],
        punto_1["longitud"],

        punto_2["latitud"],
        punto_2["longitud"]

    )

    # ============================================================
    # MATERIAL ESTIMADO
    # ============================================================

    material = "Desconocido"

    for conexion in conexiones:

        if (

            conexion["origen"]
            == punto_1["nombre"]

            and

            conexion["destino"]
            == punto_2["nombre"]

        ):

            material = conexion["material"]

            break

    velocidad = VELOCIDADES_REFERENCIA.get(
        material,
        500
    )

    tiempo = calcular_tiempo_propagacion(

        distancia,
        velocidad

    )

    # ============================================================
    # RESULTADOS
    # ============================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Distancia (m)",
            round(distancia, 2)
        )

    with col2:

        st.metric(
            "Velocidad acústica (m/s)",
            velocidad
        )

    with col3:

        st.metric(
            "Tiempo propagación (s)",
            tiempo
        )

    st.subheader(
        "📑 Evaluación"
    )

    if distancia > 500:

        st.warning(
            """
            Distancia elevada para
            correlación confiable.
            """
        )

    else:

        st.success(
            """
            Distancia razonable para
            correlación acústica.
            """
        )

    st.write(

        {

            "sensor_a": sensor_1,
            "sensor_b": sensor_2,
            "material": material,
            "distancia": distancia,
            "velocidad": velocidad,
            "tiempo": tiempo

        }

    )
# cartografia/sensores_geo.py

import streamlit as st

from cartografia.utilidades import (
    calcular_distancia_haversine,
    buscar_punto_por_nombre
)


def registrar_sensor_geografico():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    if len(puntos) == 0:

        st.warning(
            "No existen puntos cartográficos"
        )

        return

    if "sensores_geo" not in st.session_state:

        st.session_state["sensores_geo"] = []

    nombres = [

        p["nombre"]
        for p in puntos

    ]

    st.subheader(
        "🎧 Registro geográfico sensores"
    )

    nombre_sensor = st.text_input(
        "Nombre sensor"
    )

    punto_asociado = st.selectbox(
        "Punto asociado",
        nombres
    )

    tipo_sensor = st.selectbox(

        "Tipo sensor",

        [
            "Piezoeléctrico",
            "Acelerómetro",
            "Micrófono contacto",
            "Otro"
        ]

    )

    frecuencia = st.number_input(
        "Frecuencia muestreo (Hz)",
        min_value=1
    )

    if st.button(
        "Registrar sensor"
    ):

        sensor = {

            "sensor": nombre_sensor,

            "punto": punto_asociado,

            "tipo": tipo_sensor,

            "frecuencia": frecuencia

        }

        st.session_state["sensores_geo"].append(
            sensor
        )

        st.success(
            "Sensor registrado"
        )

    st.dataframe(

        st.session_state["sensores_geo"],

        width='stretch'

    )


def calcular_distancia_sensores():

    sensores = st.session_state.get(
        "sensores_geo",
        []
    )

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    if len(sensores) < 2:

        st.warning(
            "Debe existir mínimo dos sensores"
        )

        return

    nombres = [

        s["sensor"]
        for s in sensores

    ]

    sensor_1 = st.selectbox(
        "Sensor 1",
        nombres
    )

    sensor_2 = st.selectbox(
        "Sensor 2",
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

    st.metric(
        "Distancia sensores (m)",
        round(distancia, 2)
    )
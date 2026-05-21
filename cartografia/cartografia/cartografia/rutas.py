# cartografia/rutas.py

import streamlit as st

from cartografia.utilidades import (
    calcular_distancia_haversine,
    buscar_punto_por_nombre
)


def calcular_ruta_simple():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    if len(puntos) < 2:

        st.warning(
            "Debe existir mínimo dos puntos"
        )

        return

    nombres = [

        p["nombre"]
        for p in puntos

    ]

    st.subheader(
        "🛣️ Cálculo ruta operacional"
    )

    origen_nombre = st.selectbox(
        "Punto origen",
        nombres
    )

    destino_nombre = st.selectbox(
        "Punto destino",
        nombres,
        index=1
    )

    origen = buscar_punto_por_nombre(

        puntos,
        origen_nombre

    )

    destino = buscar_punto_por_nombre(

        puntos,
        destino_nombre

    )

    distancia = calcular_distancia_haversine(

        origen["latitud"],
        origen["longitud"],

        destino["latitud"],
        destino["longitud"]

    )

    tiempo_estimado = distancia / 1.2

    st.metric(
        "Distancia estimada (m)",
        round(distancia, 2)
    )

    st.metric(
        "Tiempo caminando (min)",
        round(tiempo_estimado / 60, 2)
    )

    st.write(

        {

            "origen": origen_nombre,
            "destino": destino_nombre,
            "distancia_metros": round(
                distancia,
                2
            ),
            "tiempo_minutos": round(
                tiempo_estimado / 60,
                2
            )

        }

    )


def generar_recorrido_inspeccion():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    if len(puntos) == 0:

        st.warning(
            "No existen puntos"
        )

        return

    st.subheader(
        "📍 Recorrido inspección"
    )

    seleccionados = st.multiselect(

        "Seleccionar puntos",

        [

            p["nombre"]
            for p in puntos

        ]

    )

    if len(seleccionados) < 2:

        st.info(
            "Seleccione mínimo dos puntos"
        )

        return

    recorrido = []

    distancia_total = 0

    for i in range(

        len(seleccionados) - 1

    ):

        punto_1 = buscar_punto_por_nombre(

            puntos,
            seleccionados[i]

        )

        punto_2 = buscar_punto_por_nombre(

            puntos,
            seleccionados[i + 1]

        )

        distancia = calcular_distancia_haversine(

            punto_1["latitud"],
            punto_1["longitud"],

            punto_2["latitud"],
            punto_2["longitud"]

        )

        distancia_total += distancia

        recorrido.append(

            {

                "desde": seleccionados[i],

                "hasta": seleccionados[i + 1],

                "distancia_m": round(
                    distancia,
                    2
                )

            }

        )

    st.dataframe(
        recorrido,
        width='stretch'
    )

    st.metric(
        "Distancia total recorrido (m)",
        round(distancia_total, 2)
    )
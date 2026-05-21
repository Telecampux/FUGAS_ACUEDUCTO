# cartografia/inferencia.py

import streamlit as st

from cartografia.metricas import (
    calcular_densidad_red,
    calcular_promedio_conectividad,
    calcular_porcentaje_nodos_aislados
)


def inferir_estado_red():

    densidad = calcular_densidad_red()

    conectividad = (
        calcular_promedio_conectividad()
    )

    aislados = (
        calcular_porcentaje_nodos_aislados()
    )

    score = 0

    # ============================================================
    # DENSIDAD
    # ============================================================

    if densidad >= 1:

        score += 40

    elif densidad >= 0.5:

        score += 25

    else:

        score += 10

    # ============================================================
    # CONECTIVIDAD
    # ============================================================

    if conectividad >= 2:

        score += 40

    elif conectividad >= 1:

        score += 25

    else:

        score += 10

    # ============================================================
    # AISLADOS
    # ============================================================

    if aislados <= 5:

        score += 20

    elif aislados <= 20:

        score += 10

    else:

        score += 0

    # ============================================================
    # CLASIFICACIÓN
    # ============================================================

    if score >= 80:

        estado = "Óptimo"

    elif score >= 60:

        estado = "Aceptable"

    elif score >= 40:

        estado = "Deficiente"

    else:

        estado = "Crítico"

    return {

        "score": score,

        "estado": estado,

        "densidad": densidad,

        "conectividad": conectividad,

        "aislados": aislados

    }


def panel_inferencia():

    st.header(
        "🧠 Inferencia operacional"
    )

    resultado = inferir_estado_red()

    # ============================================================
    # SCORE
    # ============================================================

    st.metric(
        "Score operacional",
        resultado["score"]
    )

    st.metric(
        "Estado red",
        resultado["estado"]
    )

    # ============================================================
    # MÉTRICAS
    # ============================================================

    st.subheader(
        "📊 Variables evaluadas"
    )

    st.write(

        {

            "densidad":
            resultado["densidad"],

            "conectividad":
            resultado["conectividad"],

            "aislados":
            resultado["aislados"]

        }

    )

    # ============================================================
    # INTERPRETACIÓN
    # ============================================================

    st.subheader(
        "📑 Interpretación"
    )

    estado = resultado["estado"]

    if estado == "Óptimo":

        st.success(
            """
            La red presenta una
            estructura operacional robusta.
            """
        )

    elif estado == "Aceptable":

        st.info(
            """
            La red presenta condiciones
            aceptables con oportunidades
            de mejora.
            """
        )

    elif estado == "Deficiente":

        st.warning(
            """
            Existen problemas relevantes
            en la estructura operacional.
            """
        )

    else:

        st.error(
            """
            La red presenta condiciones
            críticas de estructuración.
            """
        )
# cartografia/diagnostico.py

import streamlit as st

from cartografia.metricas import (
    calcular_densidad_red,
    calcular_promedio_conectividad,
    calcular_porcentaje_nodos_aislados,
    calcular_indice_sectorizacion
)


def ejecutar_diagnostico_cartografico():

    st.header(
        "🧠 Diagnóstico Cartográfico"
    )

    densidad = calcular_densidad_red()

    conectividad = calcular_promedio_conectividad()

    porcentaje_aislados = (
        calcular_porcentaje_nodos_aislados()
    )

    sectorizacion = (
        calcular_indice_sectorizacion()
    )

    # ============================================================
    # MÉTRICAS
    # ============================================================

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Densidad red",
            densidad
        )

        st.metric(
            "Conectividad promedio",
            conectividad
        )

    with col2:

        st.metric(
            "% nodos aislados",
            porcentaje_aislados
        )

        st.metric(
            "% sectorización",
            sectorizacion
        )

    # ============================================================
    # EVALUACIÓN
    # ============================================================

    st.subheader(
        "📑 Evaluación técnica"
    )

    # ------------------------------------------------------------
    # DENSIDAD
    # ------------------------------------------------------------

    if densidad < 0.5:

        st.warning(
            """
            Baja densidad de conexiones.
            La red aún está poco estructurada.
            """
        )

    else:

        st.success(
            """
            Densidad de red aceptable.
            """
        )

    # ------------------------------------------------------------
    # CONECTIVIDAD
    # ------------------------------------------------------------

    if conectividad < 1:

        st.warning(
            """
            Baja conectividad operacional.
            """
        )

    else:

        st.success(
            """
            Conectividad operacional adecuada.
            """
        )

    # ------------------------------------------------------------
    # NODOS AISLADOS
    # ------------------------------------------------------------

    if porcentaje_aislados > 20:

        st.error(
            """
            Existen demasiados nodos aislados.
            """
        )

    else:

        st.success(
            """
            Nivel aceptable de conectividad.
            """
        )

    # ------------------------------------------------------------
    # SECTORIZACIÓN
    # ------------------------------------------------------------

    if sectorizacion < 50:

        st.warning(
            """
            Baja cobertura de sectorización.
            """
        )

    else:

        st.success(
            """
            Sectorización operacional adecuada.
            """
        )

    # ============================================================
    # RECOMENDACIONES
    # ============================================================

    st.subheader(
        "🛠️ Recomendaciones"
    )

    recomendaciones = []

    if densidad < 0.5:

        recomendaciones.append(
            "- Incrementar conexiones registradas."
        )

    if porcentaje_aislados > 20:

        recomendaciones.append(
            "- Revisar nodos aislados."
        )

    if sectorizacion < 50:

        recomendaciones.append(
            "- Definir sectores hidráulicos."
        )

    if len(recomendaciones) == 0:

        recomendaciones.append(
            "- La red presenta condiciones aceptables."
        )

    for recomendacion in recomendaciones:

        st.write(recomendacion)
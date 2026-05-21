# cartografia/reportes.py

import streamlit as st

from cartografia.geometria import (
    calcular_longitud_total,
    calcular_centro_red,
    obtener_limites_red
)


def generar_reporte_cartografico():

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

    # ============================================================
    # MÉTRICAS
    # ============================================================

    total_puntos = len(puntos)

    total_conexiones = len(conexiones)

    longitud_total = calcular_longitud_total(

        puntos,
        conexiones

    )

    centro = calcular_centro_red(
        puntos
    )

    limites = obtener_limites_red(
        puntos
    )

    # ============================================================
    # VISUALIZACIÓN
    # ============================================================

    st.subheader(
        "📊 Reporte cartográfico"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Puntos",
            total_puntos
        )

    with col2:

        st.metric(
            "Conexiones",
            total_conexiones
        )

    with col3:

        st.metric(
            "Longitud estimada (m)",
            round(longitud_total, 2)
        )

    # ============================================================
    # CENTRO GEOGRÁFICO
    # ============================================================

    st.markdown(
        "### 🌎 Centro aproximado de la red"
    )

    st.write(

        {
            "latitud": round(
                centro["latitud"],
                6
            ),

            "longitud": round(
                centro["longitud"],
                6
            )
        }

    )

    # ============================================================
    # LÍMITES
    # ============================================================

    st.markdown(
        "### 📐 Límites geográficos"
    )

    st.write(limites)

    # ============================================================
    # TABLA PUNTOS
    # ============================================================

    st.markdown(
        "### 📍 Puntos registrados"
    )

    st.dataframe(
        puntos,
        width='stretch'
    )

    # ============================================================
    # TABLA CONEXIONES
    # ============================================================

    st.markdown(
        "### 🔗 Conexiones registradas"
    )

    st.dataframe(
        conexiones,
        width='stretch'
    )
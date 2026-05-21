# cartografia/dashboard.py

import streamlit as st

from cartografia.topologia import (
    calcular_grado_nodos,
    obtener_nodos_aislados
)

from cartografia.geometria import (
    calcular_longitud_total
)


def mostrar_dashboard_cartografico():

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

    inspecciones = st.session_state.get(
        "inspecciones_red",
        []
    )

    sectores = st.session_state.get(
        "sectores_red",
        []
    )

    st.header(
        "📊 Dashboard Cartográfico"
    )

    # ============================================================
    # MÉTRICAS PRINCIPALES
    # ============================================================

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.metric(
            "Puntos",
            len(puntos)
        )

    with col2:

        st.metric(
            "Conexiones",
            len(conexiones)
        )

    with col3:

        st.metric(
            "Sensores",
            len(sensores)
        )

    with col4:

        st.metric(
            "Inspecciones",
            len(inspecciones)
        )

    with col5:

        st.metric(
            "Sectores",
            len(sectores)
        )

    # ============================================================
    # LONGITUD TOTAL
    # ============================================================

    longitud_total = calcular_longitud_total(

        puntos,
        conexiones

    )

    st.metric(
        "Longitud total estimada (m)",
        round(longitud_total, 2)
    )

    # ============================================================
    # NODOS AISLADOS
    # ============================================================

    aislados = obtener_nodos_aislados()

    st.subheader(
        "⚠️ Nodos aislados"
    )

    if len(aislados) == 0:

        st.success(
            "No existen nodos aislados"
        )

    else:

        st.warning(aislados)

    # ============================================================
    # GRADO NODOS
    # ============================================================

    grados = calcular_grado_nodos()

    st.subheader(
        "🔗 Conectividad nodos"
    )

    st.dataframe(

        [

            {
                "nodo": nodo,
                "grado": grado
            }

            for nodo, grado
            in grados.items()

        ],

        width='stretch'

    )

    # ============================================================
    # INSPECCIONES
    # ============================================================

    if len(inspecciones) > 0:

        st.subheader(
            "🛠️ Historial inspecciones"
        )

        st.dataframe(
            inspecciones,
            width='stretch'
        )
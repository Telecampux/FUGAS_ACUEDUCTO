# cartografia/integracion.py

import streamlit as st

from cartografia.cartografia import (
    ejecutar_cartografia
)

from cartografia.dashboard import (
    mostrar_dashboard_cartografico
)

from cartografia.reportes import (
    generar_reporte_cartografico
)

from cartografia.sectorizacion import (
    visualizar_sectorizacion
)

from cartografia.sensores_geo import (
    registrar_sensor_geografico,
    calcular_distancia_sensores
)

from cartografia.inspeccion import (
    registrar_inspeccion
)


def ejecutar_modulo_cartografia():

    st.title(
        "🗺️ Sistema Cartográfico Operacional"
    )

    tabs = st.tabs(

        [

            "🗺️ Cartografía",
            "🧩 Sectores",
            "🎧 Sensores",
            "🛠️ Inspecciones",
            "📊 Dashboard",
            "📑 Reportes"

        ]

    )

    # ============================================================
    # TAB CARTOGRAFÍA
    # ============================================================

    with tabs[0]:

        ejecutar_cartografia()

    # ============================================================
    # TAB SECTORES
    # ============================================================

    with tabs[1]:

        visualizar_sectorizacion()

    # ============================================================
    # TAB SENSORES
    # ============================================================

    with tabs[2]:

        registrar_sensor_geografico()

        st.divider()

        calcular_distancia_sensores()

    # ============================================================
    # TAB INSPECCIONES
    # ============================================================

    with tabs[3]:

        registrar_inspeccion()

    # ============================================================
    # TAB DASHBOARD
    # ============================================================

    with tabs[4]:

        mostrar_dashboard_cartografico()

    # ============================================================
    # TAB REPORTES
    # ============================================================

    with tabs[5]:

        generar_reporte_cartografico()
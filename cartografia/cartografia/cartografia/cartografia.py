# cartografia/cartografia.py

import streamlit as st

from cartografia.captura_puntos import registrar_punto
from cartografia.conexiones import conectar_puntos
from cartografia.mapa import visualizar_mapa
from cartografia.almacenamiento import guardar_cartografia
from cartografia.validacion import validar_red


def ejecutar_cartografia():

    st.header(
        "🗺️ Construcción de Cartografía Operacional"
    )

    tabs = st.tabs(
        [
            "📍 Registro puntos",
            "🔗 Conexiones",
            "🗺️ Visualización",
            "✅ Validación",
            "💾 Guardar"
        ]
    )

    with tabs[0]:

        registrar_punto()

    with tabs[1]:

        conectar_puntos()

    with tabs[2]:

        visualizar_mapa()

    with tabs[3]:

        errores = validar_red()

        if len(errores) == 0:

            st.success(
                "Red validada correctamente"
            )

        else:

            for error in errores:

                st.error(error)

    with tabs[4]:

        guardar_cartografia()
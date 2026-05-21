# ==============================================================
# modules/resultados.py
# VISUALIZACIÓN RESULTADOS
# ==============================================================

import streamlit as st
import pandas as pd
import folium
import plotly.graph_objects as go

from streamlit_folium import st_folium

from modules.interpretacion import (
    interpretar_resultados
)

# ==============================================================
# ESCALAS CUALITATIVAS
# ==============================================================

def nivel_rho(valor):

    if valor < 0.20:
        return "MUY BAJO"

    elif valor < 0.40:
        return "BAJO"

    elif valor < 0.70:
        return "MEDIO"

    elif valor < 0.90:
        return "ALTO"

    else:
        return "MUY ALTO"


def nivel_snr(valor):

    if valor < 2:
        return "MUY BAJO"

    elif valor < 5:
        return "BAJO"

    elif valor < 20:
        return "MEDIO"

    elif valor < 100:
        return "ALTO"

    else:
        return "MUY ALTO"


def nivel_confianza(valor):

    if valor < 2:
        return "MUY BAJA"

    elif valor < 4:
        return "BAJA"

    elif valor < 7:
        return "MEDIA"

    elif valor < 9:
        return "ALTA"

    else:
        return "MUY ALTA"


# ==============================================================
# ALERTAS
# ==============================================================

def mostrar_alerta(diagnostico):

    nivel = diagnostico.get(
        "nivel",
        "info"
    )

    descripcion = diagnostico.get(
        "descripcion",
        "Sin descripción"
    )

    estado = diagnostico.get(
        "estado",
        ""
    )

    mensaje = f"{estado}: {descripcion}"

    if nivel == "success":

        st.success(mensaje)

    elif nivel == "warning":

        st.warning(mensaje)

    elif nivel == "error":

        st.error(mensaje)

    else:

        st.info(mensaje)


# ==============================================================
# FUNCIÓN PRINCIPAL
# ==============================================================

def mostrar_resultados():

    st.write("ENTRANDO A RESULTADOS")

    # ==========================================================
    # VALORES DEMO TEMPORALES
    # ==============================================================

    rho_obs = st.session_state.get(
        "rho_observado",
        0.82
    )

    snr_obs = st.session_state.get(
        "snr_observado",
        18.5
    )

    rho_dyn = st.session_state.get(
        "rho_dinamico",
        0.77
    )

    snr_dyn = st.session_state.get(
        "snr_dinamico",
        14.2
    )

    confidence = st.session_state.get(
        "confidence",
        8.4
    )

    estado = st.session_state.get(
        "estado",
        "NO_FUGA"
    )

    corr = st.session_state.get(
        "corr",
        [0, 1, 2, 3, 5, 3, 2, 1, 0]
    )

    # ==========================================================
    # TÍTULO
    # ==============================================================

    st.header(
        "Resultados de Correlación"
    )

    # ==========================================================
    # TABLA
    # ==============================================================

    st.subheader(
        "Resultados Técnicos"
    )

    tabla_resultados = pd.DataFrame(

        [

            {
                "Especificación":
                "ρ observado",

                "Resultado":
                f"{rho_obs:.3f}",

                "Nivel":
                nivel_rho(rho_obs)
            },

            {
                "Especificación":
                "SNR observado",

                "Resultado":
                f"{snr_obs:.2f}",

                "Nivel":
                nivel_snr(snr_obs)
            },

            {
                "Especificación":
                "Confiabilidad",

                "Resultado":
                f"{confidence:.1f}/10",

                "Nivel":
                nivel_confianza(confidence)
            },

            {
                "Especificación":
                "ρ dinámico",

                "Resultado":
                f"{rho_dyn:.3f}",

                "Nivel":
                nivel_rho(rho_dyn)
            },

            {
                "Especificación":
                "SNR dinámico",

                "Resultado":
                f"{snr_dyn:.2f}",

                "Nivel":
                nivel_snr(snr_dyn)
            }

        ]

    )

    st.table(tabla_resultados)

    st.divider()

    # ==========================================================
    # INTERPRETACIÓN
    # ==============================================================

    try:

        diagnostico = interpretar_resultados(

            {
                "rho_observado": rho_obs,
                "snr_observado": snr_obs,
                "rho_dinamico": rho_dyn,
                "snr_dinamico": snr_dyn
            }

        )

        st.subheader(
            "Diagnóstico Semántico"
        )

        mostrar_alerta(
            diagnostico["rho_observado"]
        )

        mostrar_alerta(
            diagnostico["snr_observado"]
        )

        mostrar_alerta(
            diagnostico["rho_dinamico"]
        )

        mostrar_alerta(
            diagnostico["snr_dinamico"]
        )

        st.divider()

        st.subheader(
            "Conclusión Global"
        )

        mostrar_alerta(
            diagnostico[
                "conclusion_global"
            ]
        )

    except Exception as e:

        st.error(
            f"ERROR INTERPRETACIÓN: {e}"
        )

    st.divider()

    # ==========================================================
    # ESTADO
    # ==============================================================

    if estado == "NO_FUGA":

        st.warning(
            "SIN EVIDENCIA DE FUGA"
        )

    else:

        st.success(
            "POSIBLE FUGA DETECTADA"
        )

    # ==========================================================
    # GRÁFICA
    # ==============================================================

    if corr is not None and len(corr) > 0:

        st.subheader(
            "Correlación GCC-PHAT"
        )

        fig_corr = go.Figure()

        fig_corr.add_trace(

            go.Scatter(

                y=corr,

                mode='lines',

                name='GCC-PHAT'

            )

        )

        fig_corr.update_layout(

            title="Respuesta GCC-PHAT",

            xaxis_title="Lag",

            yaxis_title="Correlación",

            template="plotly_white"

        )

        st.plotly_chart(

            fig_corr,

            use_container_width=True

        )

    st.success(
        "RESULTADOS RENDERIZADOS"
    )
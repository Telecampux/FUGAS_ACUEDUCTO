# cartografia/prediccion_fugas.py

import streamlit as st

import numpy as np

from sklearn.linear_model import LogisticRegression


def construir_dataset_fugas():

    alertas = st.session_state.get(
        "alertas_red",
        []
    )

    inspecciones = st.session_state.get(
        "inspecciones_red",
        []
    )

    dataset_x = []
    dataset_y = []

    # ============================================================
    # ALERTAS
    # ============================================================

    for alerta in alertas:

        nivel = {

            "Baja": 1,
            "Media": 2,
            "Alta": 3,
            "Crítica": 4

        }.get(
            alerta["nivel"],
            1
        )

        tipo = alerta["tipo"]

        tipo_valor = (

            1
            if "Fuga" in tipo
            else 0

        )

        dataset_x.append(

            [

                nivel,
                tipo_valor

            ]

        )

        dataset_y.append(
            1
        )

    # ============================================================
    # INSPECCIONES
    # ============================================================

    for inspeccion in inspecciones:

        severidad = inspeccion[
            "severidad"
        ]

        dataset_x.append(

            [

                severidad,
                0

            ]

        )

        dataset_y.append(
            0
        )

    return (

        np.array(dataset_x),

        np.array(dataset_y)

    )


def entrenar_modelo_fugas():

    x, y = construir_dataset_fugas()

    if len(x) < 5:

        return None

    modelo = LogisticRegression()

    modelo.fit(x, y)

    return modelo


def ejecutar_prediccion_fugas():

    st.header(
        "💧 Predicción de fugas"
    )

    modelo = entrenar_modelo_fugas()

    if modelo is None:

        st.warning(
            """
            Datos insuficientes para
            entrenamiento predictivo.
            """
        )

        return

    st.subheader(
        "📊 Evaluación operacional"
    )

    severidad = st.slider(
        "Severidad operacional",
        1,
        10,
        5
    )

    tipo_fuga = st.selectbox(

        "Evento asociado",

        [

            "Sin fuga",
            "Fuga probable"

        ]

    )

    tipo_valor = (

        1
        if tipo_fuga == "Fuga probable"
        else 0

    )

    datos = np.array(

        [

            [

                severidad,
                tipo_valor

            ]

        ]

    )

    probabilidad = modelo.predict_proba(
        datos
    )[0][1]

    porcentaje = round(
        probabilidad * 100,
        2
    )

    st.metric(
        "Probabilidad fuga (%)",
        porcentaje
    )

    # ============================================================
    # INTERPRETACIÓN
    # ============================================================

    if porcentaje >= 80:

        st.error(
            """
            Alta probabilidad de fuga.
            """
        )

    elif porcentaje >= 50:

        st.warning(
            """
            Probabilidad moderada de fuga.
            """
        )

    else:

        st.success(
            """
            Baja probabilidad de fuga.
            """
        )

    st.write(

        {

            "severidad": severidad,

            "evento": tipo_fuga,

            "probabilidad":
            porcentaje

        }

    )
# cartografia/machine_learning.py

import streamlit as st

import numpy as np

from sklearn.ensemble import IsolationForest

from sklearn.preprocessing import StandardScaler


def generar_dataset_operacional():

    alertas = st.session_state.get(
        "alertas_red",
        []
    )

    inspecciones = st.session_state.get(
        "inspecciones_red",
        []
    )

    dataset = []

    # ============================================================
    # ALERTAS
    # ============================================================

    for alerta in alertas:

        nivel = alerta["nivel"]

        severidad = {

            "Baja": 1,
            "Media": 2,
            "Alta": 3,
            "Crítica": 4

        }.get(
            nivel,
            1
        )

        dataset.append(

            [

                severidad,
                1

            ]

        )

    # ============================================================
    # INSPECCIONES
    # ============================================================

    for inspeccion in inspecciones:

        dataset.append(

            [

                inspeccion["severidad"],
                0

            ]

        )

    return np.array(dataset)


def entrenar_modelo_anomalias():

    dataset = generar_dataset_operacional()

    if len(dataset) < 5:

        return None, None

    scaler = StandardScaler()

    datos = scaler.fit_transform(
        dataset
    )

    modelo = IsolationForest(

        contamination=0.2,

        random_state=42

    )

    modelo.fit(datos)

    return modelo, scaler


def ejecutar_deteccion_anomalias():

    st.header(
        "🤖 Machine Learning Operacional"
    )

    modelo, scaler = entrenar_modelo_anomalias()

    if modelo is None:

        st.warning(
            """
            Datos insuficientes para
            entrenar modelo.
            """
        )

        return

    dataset = generar_dataset_operacional()

    datos = scaler.transform(
        dataset
    )

    predicciones = modelo.predict(
        datos
    )

    resultados = []

    for i, prediccion in enumerate(
        predicciones
    ):

        estado = (

            "Anómalo"
            if prediccion == -1
            else "Normal"

        )

        resultados.append(

            {

                "registro": i,

                "estado": estado

            }

        )

    st.subheader(
        "📊 Detección anomalías"
    )

    st.dataframe(
        resultados,
        width='stretch'
    )

    anomalias = [

        r for r in resultados
        if r["estado"] == "Anómalo"

    ]

    st.metric(
        "Eventos anómalos",
        len(anomalias)
    )

    if len(anomalias) > 0:

        st.warning(
            """
            El modelo detectó posibles
            comportamientos anómalos.
            """
        )

    else:

        st.success(
            """
            No se detectaron anomalías
            relevantes.
            """
        )
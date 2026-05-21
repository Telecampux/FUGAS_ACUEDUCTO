import os
import glob

import numpy as np
import pandas as pd
import streamlit as st

from core.rutas import asegurar_bd_sensores

# =============================================================================
# CARPETA
# =============================================================================

CARPETA = asegurar_bd_sensores()

# =============================================================================
# GENERACIÓN / CARGA SEÑALES
# =============================================================================

def generar_senales():

    st.subheader(
        "Entrada señales acústicas"
    )

    # =========================================================================
    # MATERIAL
    # =========================================================================

    materiales = {

        "PVC": 400,
        "PEAD": 300,
        "Hierro dúctil": 1000,
        "Asbesto cemento": 600,
        "Desconocido": 500
    }

    c1, c2, c3 = st.columns(3)

    material = c1.selectbox(
        "Material",
        list(materiales.keys())
    )

    v_default = materiales[material]

    modo_v = c2.selectbox(
        "Velocidad acústica",
        [
            "Automática",
            "Manual"
        ]
    )

    if modo_v == "Automática":

        v = v_default

        c3.metric(
            "v (m/s)",
            v
        )

    else:

        v = c3.number_input(
            "v (m/s)",
            value=float(v_default)
        )

    st.session_state['v'] = v

    # =========================================================================
    # FRECUENCIA
    # =========================================================================

    fs = st.number_input(
        "Frecuencia muestreo (Hz)",
        value=16000
    )

    st.session_state['fs'] = fs

    # =========================================================================
    # MODO
    # =========================================================================

    modo = st.radio(
        "Modo entrada",
        [
            "Simulación",
            "CSV"
        ]
    )

    # =========================================================================
    # SIMULACIÓN
    # =========================================================================

    if modo == "Simulación":

        dur = st.slider(
            "Duración señal (s)",
            1,
            10,
            5
        )

        tipo = st.selectbox(
            "Escenario",
            [
                "Correlacionado",
                "Ruido"
            ]
        )

        if st.button(
            "Generar señales"
        ):

            try:

                t = np.linspace(
                    0,
                    dur,
                    int(fs * dur)
                )

                base = np.random.normal(
                    0,
                    1,
                    len(t)
                )

                if tipo == "Correlacionado":

                    delay = np.random.randint(
                        -int(0.01 * fs),
                        int(0.01 * fs)
                    )

                    a = base

                    b = np.roll(
                        base,
                        delay
                    )

                else:

                    a = np.random.normal(
                        0,
                        1,
                        len(t)
                    )

                    b = np.random.normal(
                        0,
                        1,
                        len(t)
                    )

                # ============================================================
                # RUIDO
                # ============================================================

                a += np.random.normal(
                    0,
                    0.3,
                    len(t)
                )

                b += np.random.normal(
                    0,
                    0.3,
                    len(t)
                )

                # ============================================================
                # SESSION
                # ============================================================

                st.session_state['a'] = a
                st.session_state['b'] = b

                # ============================================================
                # CSV
                # ============================================================

                pd.DataFrame(a).to_csv(

                    os.path.join(
                        CARPETA,
                        "sensor_a_simulado.csv"
                    ),

                    index=False,
                    header=False
                )

                pd.DataFrame(b).to_csv(

                    os.path.join(
                        CARPETA,
                        "sensor_b_simulado.csv"
                    ),

                    index=False,
                    header=False
                )

                st.success(
                    "Señales simuladas correctamente"
                )

            except Exception as e:

                st.error(
                    f"Error simulación: {e}"
                )

    # =========================================================================
    # CSV
    # =========================================================================

    else:

        archivos_csv = glob.glob(
            os.path.join(
                CARPETA,
                "**",
                "*.csv"
            ),
            recursive=True
        )

        nombres_csv = [

            os.path.relpath(x, CARPETA)

            for x in archivos_csv
        ]

        if len(nombres_csv) == 0:

            st.warning(
                "No existen archivos CSV"
            )

            return

        c1, c2 = st.columns(2)

        csv_a = c1.selectbox(
            "Sensor A",
            nombres_csv,
            key="csv_a"
        )

        csv_b = c2.selectbox(
            "Sensor B",
            nombres_csv,
            key="csv_b"
        )

        if st.button(
            "Cargar CSV"
        ):

            try:

                ruta_a = os.path.join(
                    CARPETA,
                    csv_a
                )

                ruta_b = os.path.join(
                    CARPETA,
                    csv_b
                )

                # ============================================================
                # LECTURA
                # ============================================================

                df_a = pd.read_csv(
                    ruta_a,
                    header=None
                )

                df_b = pd.read_csv(
                    ruta_b,
                    header=None
                )

                xa = pd.to_numeric(
                    df_a.iloc[:, 0],
                    errors='coerce'
                ).dropna().values

                xb = pd.to_numeric(
                    df_b.iloc[:, 0],
                    errors='coerce'
                ).dropna().values

                # ============================================================
                # LONGITUD
                # ============================================================

                n_a = len(xa)
                n_b = len(xb)

                if n_a != n_b:

                    st.warning(
                        f"""
                        Cantidad de muestras diferente

                        Sensor A:
                        {n_a}

                        Sensor B:
                        {n_b}
                        """
                    )

                n_min = min(
                    n_a,
                    n_b
                )

                xa = xa[:n_min]
                xb = xb[:n_min]

                # ============================================================
                # SESSION
                # ============================================================

                st.session_state['a'] = xa
                st.session_state['b'] = xb

                st.success(
                    f"""
                    CSV cargados correctamente

                    Muestras sincronizadas:
                    {n_min}
                    """
                )

            except Exception as e:

                st.error(
                    f"Error cargando CSV: {e}"
                )

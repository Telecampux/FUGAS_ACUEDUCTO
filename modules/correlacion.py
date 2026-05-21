# ==============================================================
# modules/correlacion.py
# CORRELACION GCC-PHAT
# ==============================================================

import numpy as np
import scipy.signal as signal
import geopandas as gpd
import streamlit as st


# ==============================================================
# GCC-PHAT
# ==============================================================

def gcc_phat(
    x,
    y
):

    n = len(x) + len(y)

    X = np.fft.rfft(
        x,
        n=n
    )

    Y = np.fft.rfft(
        y,
        n=n
    )

    R = X * np.conj(Y)

    # ==========================================================
    # PHAT
    # ==============================================================

    R /= (
        np.abs(R) + 1e-12
    )

    cc = np.fft.irfft(
        R,
        n=n
    )

    max_shift = n // 2

    cc = np.concatenate(
        (
            cc[-max_shift:],
            cc[:max_shift + 1]
        )
    )

    lags = np.arange(
        -max_shift,
        max_shift + 1
    )

    idx = np.argmax(
        np.abs(cc)
    )

    return (
        cc,
        lags,
        idx
    )


# ==============================================================
# REFINAMIENTO SUBMUESTRA
# ==============================================================

def refine_peak(
    corr,
    lags,
    idx,
    fs
):

    if (
        idx <= 0
        or
        idx >= len(corr) - 1
    ):

        return lags[idx] / fs

    y0 = corr[idx - 1]
    y1 = corr[idx]
    y2 = corr[idx + 1]

    den = (
        y0
        - 2 * y1
        + y2
    )

    if abs(den) > 1e-12:

        delta = (
            0.5
            *
            (y0 - y2)
            /
            den
        )

    else:

        delta = 0.0

    delay = lags[idx] + delta

    return delay / fs


# ==============================================================
# FILTRADO
# ==============================================================

def filtrar_senal(
    x,
    fs
):

    b_f, a_f = signal.butter(
        4,
        [
            100 / (fs / 2),
            2000 / (fs / 2)
        ],
        btype='band'
    )

    padlen = 3 * max(
        len(a_f),
        len(b_f)
    )

    if len(x) <= padlen:

        raise ValueError(
            "Señal demasiado corta"
        )

    return signal.filtfilt(
        b_f,
        a_f,
        x
    )


# ==============================================================
# FUNCION PRINCIPAL
# ==============================================================

def ejecutar_correlacion():

    # ==========================================================
    # VALIDACION
    # ==============================================================

    if (

        "a" not in st.session_state

        or

        "b" not in st.session_state

    ):

        st.error(
            "No existen señales cargadas."
        )

        return

    # ==========================================================
    # CAPTURA
    # ==============================================================

    xa = np.array(
        st.session_state["a"]
    )

    xb = np.array(
        st.session_state["b"]
    )

    fs = st.session_state.get(
        "fs",
        16000
    )

    v = st.session_state.get(
        "v",
        500
    )

    # ==========================================================
    # VALIDACION
    # ==============================================================

    if len(xa) != len(xb):

        st.error(
            "Las señales tienen distinta longitud."
        )

        return

    if len(xa) == 0:

        st.error(
            "Las señales están vacías."
        )

        return

    try:

        # ======================================================
        # NORMALIZACION
        # ======================================================

        xa = xa - np.mean(xa)
        xb = xb - np.mean(xb)

        # ======================================================
        # VENTANA HANN
        # ======================================================

        ventana = np.hanning(
            len(xa)
        )

        xa *= ventana
        xb *= ventana

        # ======================================================
        # FILTRADO
        # ======================================================

        xa = filtrar_senal(
            xa,
            fs
        )

        xb = filtrar_senal(
            xb,
            fs
        )

        # ======================================================
        # GCC-PHAT
        # ======================================================

        corr, lags, idx = gcc_phat(
            xa,
            xb
        )

        # ======================================================
        # DELAY
        # ======================================================

        delta_t = refine_peak(
            corr,
            lags,
            idx,
            fs
        )

        # ======================================================
        # METRICAS
        # ======================================================

        rho = np.max(
            np.abs(corr)
        )

        noise_floor = np.median(
            np.abs(corr)
        )

        noise_std = np.std(
            np.abs(corr)
        )

        snr = (

            (
                rho
                -
                noise_floor
            )

            /

            (
                noise_std
                + 1e-12
            )

        )

        # ======================================================
        # THRESHOLDS
        # ======================================================

        thr_rho_auto = (

            noise_floor
            +
            (
                3.5 * noise_std
            )

        )

        thr_snr_auto = (

            4.0
            +
            (
                noise_std * 2
            )

        )

        # ======================================================
        # CONFIANZA
        # ======================================================

        confidence = (

            (
                rho
                /
                (
                    thr_rho_auto
                    + 1e-12
                )
            )

            +

            (
                snr
                /
                (
                    thr_snr_auto
                    + 1e-12
                )
            )

        ) / 2

        confidence = max(
            0,
            min(confidence, 10)
        )

        # ======================================================
        # SESSION STATE
        # ======================================================

        st.session_state[
            "rho_observado"
        ] = float(rho)

        st.session_state[
            "snr_observado"
        ] = float(snr)

        st.session_state[
            "rho_dinamico"
        ] = float(thr_rho_auto)

        st.session_state[
            "snr_dinamico"
        ] = float(thr_snr_auto)

        st.session_state[
            "confidence"
        ] = float(confidence)

        st.session_state[
            "corr"
        ] = corr

        # ======================================================
        # DETECCION
        # ======================================================

        if (

            rho < thr_rho_auto
            or
            snr < thr_snr_auto

        ):

            st.session_state[
                "estado"
            ] = "NO_FUGA"

        else:

            # ==================================================
            # LOCALIZACION
            # ==================================================

            L = st.session_state["L"]

            x = (
                L
                +
                v * delta_t
            ) / 2

            linea = st.session_state[
                "linea"
            ]

            punto = gpd.GeoSeries(
                [
                    linea.interpolate(x)
                ],
                crs="EPSG:3116"
            ).to_crs(
                epsg=4326
            ).iloc[0]

            st.session_state[
                "estado"
            ] = "FUGA"

            st.session_state[
                "x_fuga"
            ] = x

            st.session_state[
                "lat_fuga"
            ] = punto.y

            st.session_state[
                "lon_fuga"
            ] = punto.x

        # ======================================================
        # BANDERA
        # ======================================================

        st.session_state[
            "resultado_generado"
        ] = True

        st.success(
            "Correlación GCC-PHAT ejecutada correctamente."
        )

    except Exception as e:

        st.error(
            f"Error correlación: {e}"
        )
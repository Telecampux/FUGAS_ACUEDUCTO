# ==============================================================
# modules/interpretacion.py
# Motor de interpretacion semantica de señales
# ==============================================================

from typing import Dict


# ==============================================================
# CLASIFICACION RHO OBSERVADO
# ==============================================================

def clasificar_rho_observado(
    valor: float
) -> Dict:

    if valor < 0.30:

        return {
            "estado": "MALA",
            "nivel": "error",
            "descripcion":
            "La correlacion entre señales es muy baja."
        }

    elif valor < 0.50:

        return {
            "estado": "DEBIL",
            "nivel": "warning",
            "descripcion":
            "La correlacion es debil y poco consistente."
        }

    elif valor < 0.70:

        return {
            "estado": "ACEPTABLE",
            "nivel": "info",
            "descripcion":
            "La correlacion es aceptable."
        }

    elif valor < 0.90:

        return {
            "estado": "ALTA",
            "nivel": "success",
            "descripcion":
            "La correlacion observada es buena y consistente."
        }

    else:

        return {
            "estado": "EXCELENTE",
            "nivel": "success",
            "descripcion":
            "La correlacion observada es excelente."
        }


# ==============================================================
# CLASIFICACION SNR LINEAL
# ==============================================================

def clasificar_snr_lineal(
    valor: float
) -> Dict:

    if valor < 1:

        return {
            "estado": "RUIDO_DOMINANTE",
            "nivel": "error",
            "descripcion":
            "La señal esta enterrada en el ruido."
        }

    elif valor < 5:

        return {
            "estado": "DEBIL",
            "nivel": "warning",
            "descripcion":
            "La señal util apenas supera el ruido."
        }

    elif valor < 20:

        return {
            "estado": "ACEPTABLE",
            "nivel": "info",
            "descripcion":
            "La señal es usable y detectable."
        }

    elif valor < 100:

        return {
            "estado": "FUERTE",
            "nivel": "success",
            "descripcion":
            "La señal util domina claramente sobre el ruido."
        }

    elif valor < 500:

        return {
            "estado": "MUY_FUERTE",
            "nivel": "success",
            "descripcion":
            "La señal util domina ampliamente sobre el ruido."
        }

    else:

        return {
            "estado": "EXTREMADAMENTE_DOMINANTE",
            "nivel": "success",
            "descripcion":
            "La señal es extremadamente dominante frente al ruido."
        }


# ==============================================================
# CLASIFICACION RHO DINAMICO
# ==============================================================

def clasificar_rho_dinamico(
    valor: float
) -> Dict:

    if valor < 0.10:

        return {
            "estado": "INESTABLE",
            "nivel": "error",
            "descripcion":
            "La estabilidad temporal de la señal es muy deficiente."
        }

    elif valor < 0.30:

        return {
            "estado": "MUY_BAJO",
            "nivel": "warning",
            "descripcion":
            "La estabilidad dinamica es baja."
        }

    elif valor < 0.50:

        return {
            "estado": "ACEPTABLE",
            "nivel": "info",
            "descripcion":
            "La estabilidad temporal es aceptable."
        }

    else:

        return {
            "estado": "ESTABLE",
            "nivel": "success",
            "descripcion":
            "La estabilidad dinamica es buena."
        }


# ==============================================================
# CLASIFICACION SNR DINAMICO
# ==============================================================

def clasificar_snr_dinamico(
    valor: float
) -> Dict:

    if valor < 3:

        return {
            "estado": "DEFICIENTE",
            "nivel": "error",
            "descripcion":
            "El ruido domina durante el analisis dinamico."
        }

    elif valor < 8:

        return {
            "estado": "MARGINAL",
            "nivel": "warning",
            "descripcion":
            "El ruido comienza a competir con la señal."
        }

    elif valor < 20:

        return {
            "estado": "BUENO",
            "nivel": "info",
            "descripcion":
            "La señal mantiene buena calidad dinamica."
        }

    else:

        return {
            "estado": "EXCELENTE",
            "nivel": "success",
            "descripcion":
            "La señal mantiene excelente calidad dinamica."
        }


# ==============================================================
# CONCLUSION GLOBAL
# ==============================================================

def generar_conclusion_global(
    rho_obs: float,
    snr_obs: float,
    rho_dyn: float,
    snr_dyn: float
) -> Dict:

    # ==========================================================
    # CASO ROBUSTO
    # ==========================================================

    if (

        rho_obs > 0.80
        and
        snr_obs > 20
        and
        rho_dyn > 0.50
        and
        snr_dyn > 8

    ):

        return {

            "estado": "ROBUSTA",

            "nivel": "success",

            "descripcion":
            (
                "La señal detectada presenta "
                "alta correlacion y buena "
                "estabilidad dinamica."
            )
        }

    # ==========================================================
    # CASO INESTABLE
    # ==========================================================

    elif (

        rho_obs > 0.70
        and
        snr_obs > 20
        and
        rho_dyn < 0.10

    ):

        return {

            "estado": "INESTABLE",

            "nivel": "warning",

            "descripcion":
            (
                "La señal observada es fuerte, "
                "pero presenta baja estabilidad "
                "temporal."
            )
        }

    # ==========================================================
    # CASO RUIDOSO
    # ==========================================================

    elif (

        snr_obs < 5
        or
        snr_dyn < 3

    ):

        return {

            "estado": "RUIDOSA",

            "nivel": "error",

            "descripcion":
            (
                "El ruido afecta significativamente "
                "la deteccion."
            )
        }

    # ==========================================================
    # CASO INTERMEDIO
    # ==========================================================

    else:

        return {

            "estado": "MODERADA",

            "nivel": "info",

            "descripcion":
            (
                "La señal presenta comportamiento "
                "intermedio y requiere validacion "
                "adicional."
            )
        }


# ==============================================================
# MOTOR PRINCIPAL
# ==============================================================

def interpretar_resultados(
    resultado: Dict
) -> Dict:

    rho_obs = resultado.get(
        "rho_observado",
        0
    )

    snr_obs = resultado.get(
        "snr_observado",
        0
    )

    rho_dyn = resultado.get(
        "rho_dinamico",
        0
    )

    snr_dyn = resultado.get(
        "snr_dinamico",
        0
    )

    diagnostico = {

        "rho_observado":

            clasificar_rho_observado(
                rho_obs
            ),

        "snr_observado":

            clasificar_snr_lineal(
                snr_obs
            ),

        "rho_dinamico":

            clasificar_rho_dinamico(
                rho_dyn
            ),

        "snr_dinamico":

            clasificar_snr_dinamico(
                snr_dyn
            ),

        "conclusion_global":

            generar_conclusion_global(

                rho_obs,
                snr_obs,
                rho_dyn,
                snr_dyn

            )

    }

    return diagnostico
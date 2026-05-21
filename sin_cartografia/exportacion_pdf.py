# cartografia/exportacion_pdf.py

import io

import streamlit as st

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors

from reportlab.lib.styles import (
    getSampleStyleSheet
)

from reportlab.lib.pagesizes import letter


def generar_pdf_cartografia():

    puntos = st.session_state.get(
        "puntos_red",
        []
    )

    conexiones = st.session_state.get(
        "conexiones_red",
        []
    )

    alertas = st.session_state.get(
        "alertas_red",
        []
    )

    buffer = io.BytesIO()

    documento = SimpleDocTemplate(

        buffer,

        pagesize=letter

    )

    estilos = getSampleStyleSheet()

    elementos = []

    # ============================================================
    # TÍTULO
    # ============================================================

    titulo = Paragraph(

        "Reporte Cartográfico Operacional",

        estilos["Title"]

    )

    elementos.append(titulo)

    elementos.append(
        Spacer(1, 20)
    )

    # ============================================================
    # RESUMEN
    # ============================================================

    resumen = [

        [

            "Elemento",
            "Cantidad"

        ],

        [

            "Puntos",
            len(puntos)

        ],

        [

            "Conexiones",
            len(conexiones)

        ],

        [

            "Alertas",
            len(alertas)

        ]

    ]

    tabla_resumen = Table(
        resumen
    )

    tabla_resumen.setStyle(

        TableStyle(

            [

                (

                    "BACKGROUND",

                    (0, 0),

                    (-1, 0),

                    colors.grey

                ),

                (

                    "TEXTCOLOR",

                    (0, 0),

                    (-1, 0),

                    colors.whitesmoke

                ),

                (

                    "GRID",

                    (0, 0),

                    (-1, -1),

                    1,

                    colors.black

                )

            ]

        )

    )

    elementos.append(
        tabla_resumen
    )

    elementos.append(
        Spacer(1, 20)
    )

    # ============================================================
    # PUNTOS
    # ============================================================

    elementos.append(

        Paragraph(

            "Puntos registrados",

            estilos["Heading2"]

        )

    )

    datos_puntos = [

        [

            "Nombre",
            "Tipo",
            "Latitud",
            "Longitud"

        ]

    ]

    for punto in puntos:

        datos_puntos.append(

            [

                punto["nombre"],

                punto["tipo"],

                str(punto["latitud"]),

                str(punto["longitud"])

            ]

        )

    tabla_puntos = Table(
        datos_puntos
    )

    tabla_puntos.setStyle(

        TableStyle(

            [

                (

                    "GRID",

                    (0, 0),

                    (-1, -1),

                    1,

                    colors.black

                )

            ]

        )

    )

    elementos.append(
        tabla_puntos
    )

    elementos.append(
        Spacer(1, 20)
    )

    # ============================================================
    # ALERTAS
    # ============================================================

    if len(alertas) > 0:

        elementos.append(

            Paragraph(

                "Alertas registradas",

                estilos["Heading2"]

            )

        )

        datos_alertas = [

            [

                "Fecha",
                "Punto",
                "Tipo",
                "Nivel",
                "Estado"

            ]

        ]

        for alerta in alertas:

            datos_alertas.append(

                [

                    alerta["fecha"],

                    alerta["punto"],

                    alerta["tipo"],

                    alerta["nivel"],

                    alerta["estado"]

                ]

            )

        tabla_alertas = Table(
            datos_alertas
        )

        tabla_alertas.setStyle(

            TableStyle(

                [

                    (

                        "GRID",

                        (0, 0),

                        (-1, -1),

                        1,

                        colors.black

                    )

                ]

            )

        )

        elementos.append(
            tabla_alertas
        )

    # ============================================================
    # GENERAR PDF
    # ============================================================

    documento.build(
        elementos
    )

    pdf = buffer.getvalue()

    buffer.close()

    st.download_button(

        label="📄 Descargar PDF",

        data=pdf,

        file_name="reporte_cartografico.pdf",

        mime="application/pdf"

    )
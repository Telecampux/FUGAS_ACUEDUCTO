import flet as ft

def main(page: ft.Page):

    page.title = "Sistema GCC-PHAT"

    titulo = ft.Text(

        "Sistema de Correlación",

        size=30,

        weight="bold"

    )

    resultado = ft.Text(
        "Esperando procesamiento..."
    )

    def procesar(e):

        resultado.value = (
            "Confiabilidad: MUY ALTA"
        )

        page.update()

    boton = ft.ElevatedButton(

        "Procesar",

        on_click=procesar

    )

    page.add(

        titulo,

        boton,

        resultado

    )

ft.app(target=main)
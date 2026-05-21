import os


RAIZ_PROYECTO = os.path.dirname(os.path.dirname(__file__))
CARPETA_BD_PROYECTOS = os.path.join(RAIZ_PROYECTO, "BD_PROYECTOS")
CARPETA_BD_SENSORES = os.path.join(RAIZ_PROYECTO, "BD_SENSORES")


def asegurar_bd_proyectos():
    os.makedirs(
        CARPETA_BD_PROYECTOS,
        exist_ok=True
    )

    return CARPETA_BD_PROYECTOS


def asegurar_bd_sensores():
    os.makedirs(
        CARPETA_BD_SENSORES,
        exist_ok=True
    )

    return CARPETA_BD_SENSORES

# cartografia/utilidades.py

from math import radians
from math import sin
from math import cos
from math import sqrt
from math import atan2


def calcular_distancia_haversine(

    lat1,
    lon1,
    lat2,
    lon2

):

    radio_tierra = 6371000

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (

        sin(delta_lat / 2) ** 2

        +

        cos(lat1)
        *
        cos(lat2)
        *
        sin(delta_lon / 2) ** 2

    )

    c = 2 * atan2(

        sqrt(a),
        sqrt(1 - a)

    )

    distancia = radio_tierra * c

    return round(
        distancia,
        2
    )


def buscar_punto_por_nombre(

    puntos,
    nombre

):

    for punto in puntos:

        if punto["nombre"] == nombre:

            return punto

    return None


def validar_coordenadas(

    latitud,
    longitud

):

    if latitud < -90 or latitud > 90:

        return False

    if longitud < -180 or longitud > 180:

        return False

    return True
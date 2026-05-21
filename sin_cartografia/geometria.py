# cartografia/geometria.py

from cartografia.utilidades import (
    calcular_distancia_haversine
)


def calcular_longitud_total(

    puntos,
    conexiones

):

    longitud_total = 0

    for conexion in conexiones:

        origen = next(

            p for p in puntos
            if p["nombre"] == conexion["origen"]

        )

        destino = next(

            p for p in puntos
            if p["nombre"] == conexion["destino"]

        )

        distancia = calcular_distancia_haversine(

            origen["latitud"],
            origen["longitud"],

            destino["latitud"],
            destino["longitud"]

        )

        longitud_total += distancia

    return round(
        longitud_total,
        2
    )


def calcular_centro_red(

    puntos

):

    if len(puntos) == 0:

        return None

    latitudes = [

        p["latitud"]
        for p in puntos

    ]

    longitudes = [

        p["longitud"]
        for p in puntos

    ]

    centro = {

        "latitud": sum(latitudes) / len(latitudes),

        "longitud": sum(longitudes) / len(longitudes)

    }

    return centro


def obtener_limites_red(

    puntos

):

    if len(puntos) == 0:

        return None

    latitudes = [

        p["latitud"]
        for p in puntos

    ]

    longitudes = [

        p["longitud"]
        for p in puntos

    ]

    limites = {

        "lat_min": min(latitudes),
        "lat_max": max(latitudes),

        "lon_min": min(longitudes),
        "lon_max": max(longitudes)

    }

    return limites
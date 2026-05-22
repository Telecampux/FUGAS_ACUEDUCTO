# =============================================================================
# EXPORTACION GEOJSON - SIN CARTOGRAFIA
# =============================================================================

import json
import os
import unicodedata

from core.rutas import asegurar_bd_proyectos

CARPETA_PROYECTOS = asegurar_bd_proyectos()


def _numero(valor):
    if valor is None:
        return None

    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _diametro_pulgadas(conexion):
    diametro = _numero(conexion.get("diametro"))

    if diametro is None:
        return None

    unidad = str(
        conexion.get("unidad_diametro", "pulgadas")
    ).strip().lower()

    if unidad in ("pulg", "pulgada", "pulgadas", "in", "inch", "inches"):
        return diametro

    return round(diametro / 25.4, 2)


def _material_geojson(material):
    material_normalizado = str(
        material or ""
    ).strip().upper()
    material_normalizado = unicodedata.normalize(
        "NFKD",
        material_normalizado
    ).encode(
        "ascii",
        "ignore"
    ).decode("ascii")

    equivalencias = {
        "HIERRO": "HF",
        "HIERRO DUCTIL": "HF",
        "ASBESTO CEMENTO": "AC",
        "PEAD": "PEAD",
        "PVC": "PVC",
        "ACERO": "ACERO"
    }

    return equivalencias.get(
        material_normalizado,
        material_normalizado or None
    )


def construir_geojson(
    puntos,
    conexiones,
    nombre="levantamiento"
):

    features = []

    puntos_por_nombre = {
        punto.get("nombre"): punto
        for punto in puntos
    }

    for indice, conexion in enumerate(
        conexiones,
        start=1
    ):

        origen = puntos_por_nombre.get(conexion.get("origen"))
        destino = puntos_por_nombre.get(conexion.get("destino"))

        if origen is None or destino is None:
            continue

        gps_origen = origen.get("gps")
        gps_destino = destino.get("gps")

        if gps_origen is None or gps_destino is None:
            continue

        lon_origen = _numero(gps_origen.get("lon"))
        lat_origen = _numero(gps_origen.get("lat"))
        lon_destino = _numero(gps_destino.get("lon"))
        lat_destino = _numero(gps_destino.get("lat"))

        if None in (
            lon_origen,
            lat_origen,
            lon_destino,
            lat_destino
        ):
            continue

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "ID_TRAMO": indice,
                    "UBICACION": (
                        f"{conexion.get('origen')} - "
                        f"{conexion.get('destino')}"
                    ),
                    "TIPO_RED": conexion.get(
                        "tipo_red",
                        "DISTRIBUCION"
                    ),
                    "DIAM_PULG": _diametro_pulgadas(conexion),
                    "MATERIAL": _material_geojson(
                        conexion.get("material")
                    ),
                    "ESTADO": conexion.get(
                        "estado",
                        "OPERATIVO"
                    ),
                    "CSV_A": conexion.get("CSV_A")
                    or conexion.get("csv_a")
                    or conexion.get("sensor_a_csv"),
                    "CSV_B": conexion.get("CSV_B")
                    or conexion.get("csv_b")
                    or conexion.get("sensor_b_csv")
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [lon_origen, lat_origen],
                        [lon_destino, lat_destino]
                    ]
                }
            }
        )

    return {
        "type": "FeatureCollection",
        "name": nombre,
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "features": features
    }


def exportar_geojson(
    puntos,
    conexiones,
    nombre="levantamiento",
    guardar_en_simulacion=False
):

    geojson = construir_geojson(
        puntos=puntos,
        conexiones=conexiones,
        nombre=nombre
    )

    if not geojson["features"]:
        raise ValueError(
            "No hay conexiones con GPS valido para exportar GeoJSON"
        )

    ruta = os.path.join(
        CARPETA_PROYECTOS,
        f"{nombre}.geojson"
    )

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            geojson,
            archivo,
            ensure_ascii=False,
            indent=4
        )

    rutas = {
        "BD_PROYECTOS": ruta
    }

    return rutas

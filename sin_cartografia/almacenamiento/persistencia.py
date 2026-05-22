import json
import os

import streamlit as st

from core.rutas import asegurar_bd_proyectos

CARPETA_PROYECTOS = asegurar_bd_proyectos()
EXTENSIONES_PROYECTO = (".json", ".geojson")


def guardar_proyecto(
    puntos,
    conexiones,
    proyecto
):

    if proyecto is None:

        st.error(
            "No existe proyecto activo"
        )

        return None

    nombre = str(proyecto.get("nombre", "")).strip()

    if not nombre:

        st.error(
            "El proyecto debe tener nombre"
        )

        return None

    ruta = os.path.join(
        CARPETA_PROYECTOS,
        f"{nombre}.json"
    )

    data = {
        "proyecto": proyecto,
        "puntos": puntos,
        "conexiones": conexiones
    }

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            data,
            archivo,
            ensure_ascii=False,
            indent=4
        )

    return ruta


def cargar_proyecto(
    archivo
):

    contenido = json.load(
        archivo
    )

    contenido = normalizar_contenido_proyecto(
        contenido,
        getattr(archivo, "name", None)
    )

    aplicar_contenido_proyecto(
        contenido
    )

    return contenido


def normalizar_contenido_proyecto(contenido, nombre_archivo=None):
    if "proyecto" in contenido:
        return contenido

    if contenido.get("type") in (
        "FeatureCollection",
        "Feature"
    ):
        return convertir_geojson_a_proyecto(
            contenido,
            nombre_archivo
        )

    return contenido


def _nombre_base(nombre_archivo, defecto="proyecto_geojson"):
    if not nombre_archivo:
        return defecto

    return os.path.splitext(
        os.path.basename(nombre_archivo)
    )[0] or defecto


def _coordenada_clave(coordenada):
    lon = coordenada[0]
    lat = coordenada[1]

    return f"{float(lon):.8f},{float(lat):.8f}"


def _crear_punto_desde_coordenada(coordenada, indice):
    lon = float(coordenada[0])
    lat = float(coordenada[1])

    gps = {
        "lat": lat,
        "lon": lon
    }

    return {
        "nombre": f"NODO_{indice}",
        "tipo": "Nodo GIS",
        "descripcion": "Generado desde GeoJSON",
        "gps": gps,
        "latitud": lat,
        "longitud": lon,
        "altimetria": None
    }


def _coordenadas_linea(geometria):
    tipo = geometria.get("type")
    coordenadas = geometria.get("coordinates") or []

    if tipo == "LineString":
        return coordenadas

    if tipo == "MultiLineString" and coordenadas:
        return coordenadas[0]

    return []


def convertir_geojson_a_proyecto(contenido, nombre_archivo=None):
    nombre = contenido.get("name") or _nombre_base(nombre_archivo)
    features = contenido.get("features", [])

    if contenido.get("type") == "Feature":
        features = [contenido]

    puntos = []
    puntos_por_coordenada = {}
    conexiones = []

    def obtener_punto(coordenada):
        clave = _coordenada_clave(coordenada)

        if clave not in puntos_por_coordenada:
            punto = _crear_punto_desde_coordenada(
                coordenada,
                len(puntos) + 1
            )
            puntos_por_coordenada[clave] = punto
            puntos.append(punto)

        return puntos_por_coordenada[clave]

    for indice, feature in enumerate(features, start=1):
        geometria = feature.get("geometry") or {}
        coordenadas = _coordenadas_linea(geometria)

        if len(coordenadas) < 2:
            continue

        origen = obtener_punto(coordenadas[0])
        destino = obtener_punto(coordenadas[-1])
        propiedades = feature.get("properties") or {}

        conexiones.append(
            {
                "origen": origen.get("nombre"),
                "destino": destino.get("nombre"),
                "distancia": propiedades.get("DISTANCIA")
                or propiedades.get("distancia")
                or 0.0,
                "diametro": propiedades.get("DIAM_PULG")
                or propiedades.get("diam_pulg")
                or propiedades.get("diametro")
                or propiedades.get("DIAMETRO")
                or 0.0,
                "unidad_diametro": "pulgadas"
                if (
                    propiedades.get("DIAM_PULG")
                    or propiedades.get("diam_pulg")
                )
                else propiedades.get("unidad_diametro", "pulgadas"),
                "material": propiedades.get("MATERIAL")
                or propiedades.get("material")
                or "",
                "tipo_red": propiedades.get("TIPO_RED")
                or propiedades.get("tipo_red"),
                "estado": propiedades.get("ESTADO")
                or propiedades.get("estado"),
                "descripcion": propiedades.get("UBICACION")
                or propiedades.get("descripcion")
                or f"Tramo {indice}"
            }
        )

    proyecto = {
        "nombre": nombre,
        "municipio": "",
        "operador": "",
        "descripcion": "Proyecto cargado desde GeoJSON",
        "fuente": "GeoJSON"
    }

    if puntos:
        primer_gps = puntos[0].get("gps")
        proyecto.update(
            {
                "gps": primer_gps,
                "latitud": primer_gps.get("lat"),
                "longitud": primer_gps.get("lon")
            }
        )

    return {
        "proyecto": proyecto,
        "puntos": puntos,
        "conexiones": conexiones
    }


def aplicar_contenido_proyecto(contenido):
    st.session_state["proyecto"] = contenido.get(
        "proyecto",
        {}
    )

    st.session_state["gps_proyecto"] = st.session_state["proyecto"].get(
        "gps"
    )

    st.session_state["puntos"] = contenido.get(
        "puntos",
        []
    )

    st.session_state["conexiones"] = contenido.get(
        "conexiones",
        []
    )


def listar_proyectos_guardados():
    archivos = []

    for nombre_archivo in os.listdir(CARPETA_PROYECTOS):
        if not nombre_archivo.lower().endswith(EXTENSIONES_PROYECTO):
            continue

        ruta = os.path.join(
            CARPETA_PROYECTOS,
            nombre_archivo
        )

        try:
            with open(
                ruta,
                "r",
                encoding="utf-8"
            ) as archivo:
                contenido = json.load(archivo)
        except (OSError, json.JSONDecodeError):
            continue

        contenido = normalizar_contenido_proyecto(
            contenido,
            nombre_archivo
        )

        if "proyecto" in contenido:
            archivos.append(nombre_archivo)

    return sorted(archivos)


def cargar_proyecto_guardado(nombre_archivo):
    ruta = os.path.join(
        CARPETA_PROYECTOS,
        nombre_archivo
    )

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:
        contenido = json.load(
            archivo
        )

    contenido = normalizar_contenido_proyecto(
        contenido,
        nombre_archivo
    )

    aplicar_contenido_proyecto(
        contenido
    )

    return contenido


def eliminar_archivo_proyecto(
    proyecto
):
    if not proyecto:
        return None

    nombre = str(proyecto.get("nombre", "")).strip()

    if not nombre:
        return None

    ruta = os.path.join(
        CARPETA_PROYECTOS,
        f"{nombre}.json"
    )

    if os.path.exists(ruta):
        os.remove(ruta)
        return ruta

    return None


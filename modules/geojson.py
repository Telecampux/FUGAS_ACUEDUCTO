import os
import json
import geopandas as gpd
import streamlit as st

from core.rutas import asegurar_bd_proyectos

# =============================================================================
# CARPETA
# =============================================================================

CARPETA = asegurar_bd_proyectos()

# =============================================================================
# CARGA RED GIS
# =============================================================================

def cargar_red_gis():
    def es_archivo_cartografico(nombre_archivo):
        extension = os.path.splitext(nombre_archivo)[1].lower()

        if extension == ".geojson":
            return True

        if extension != ".json":
            return False

        try:
            with open(
                os.path.join(CARPETA, nombre_archivo),
                "r",
                encoding="utf-8"
            ) as archivo:
                contenido = json.load(archivo)
        except (OSError, json.JSONDecodeError):
            return False

        return contenido.get("type") in (
            "FeatureCollection",
            "Feature"
        )

    archivos_json = [

        f for f in os.listdir(CARPETA)

        if es_archivo_cartografico(f)
    ]

    if len(archivos_json) == 0:

        st.warning(
            "No existen archivos GeoJSON en BD_PROYECTOS"
        )

        return

    json_sel = st.selectbox(
        "Seleccione red",
        ["-- Seleccione --"] + archivos_json
    )

    if json_sel == "-- Seleccione --":

        return

    try:

        # =====================================================================
        # LECTURA
        # =====================================================================

        gdf_p = gpd.read_file(
            os.path.join(
                CARPETA,
                json_sel
            )
        ).to_crs(
            epsg=4326
        )

        # =====================================================================
        # VALIDACIÓN
        # =====================================================================

        if len(gdf_p) == 0:

            st.error(
                "GeoJSON vacío"
            )

            return

        geom = gdf_p.geometry.iloc[0]

        if geom.geom_type not in [
            "LineString",
            "MultiLineString"
        ]:

            st.error(
                "El GeoJSON debe contener líneas"
            )

            return

        # =====================================================================
        # CRS MÉTRICO
        # =====================================================================

        gdf_m = gdf_p.to_crs(
            epsg=3116
        )

        linea = gdf_m.geometry.iloc[0]

        # =====================================================================
        # LONGITUD
        # =====================================================================

        L = linea.length

        # =====================================================================
        # COORDENADAS
        # =====================================================================

        if geom.geom_type == "LineString":

            coords = list(
                gdf_p.geometry.iloc[0].coords
            )

        else:

            coords = list(
                list(
                    gdf_p.geometry.iloc[0].geoms
                )[0].coords
            )

        pos_a = [
            coords[0][1],
            coords[0][0]
        ]

        pos_b = [
            coords[-1][1],
            coords[-1][0]
        ]

        # =====================================================================
        # SESSION STATE
        # =====================================================================

        st.session_state['linea'] = linea
        st.session_state['L'] = L
        st.session_state['red'] = gdf_p
        st.session_state['pos_a'] = pos_a
        st.session_state['pos_b'] = pos_b
        st.session_state['modo_mapa'] = 'GIS'

        # =====================================================================
        # INFO
        # =====================================================================

        st.success(
            "Red GIS cargada correctamente"
        )

        st.info(
            f"Longitud red: {L:.2f} m"
        )

    except Exception as e:

        st.error(
            f"Error cargando GeoJSON: {e}"
        )

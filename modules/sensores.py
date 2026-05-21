import streamlit as st
import geopandas as gpd
import folium

from shapely.geometry import LineString
from streamlit_folium import st_folium

# =============================================================================
# REGISTRO MANUAL SENSORES
# =============================================================================

def registrar_sensores_manual():

    st.subheader(
        "Registro sensores GPS"
    )

    st.write(
        "Ingrese coordenadas aproximadas de los sensores."
    )

    # =========================================================================
    # COLUMNAS
    # =========================================================================

    c1, c2 = st.columns(2)

    # =========================================================================
    # SENSOR A
    # =========================================================================

    with c1:

        st.markdown(
            "### Sensor A"
        )

        lat_a = st.number_input(
            "Latitud A",
            value=4.60971000,
            format="%.8f"
        )

        lon_a = st.number_input(
            "Longitud A",
            value=-74.08175000,
            format="%.8f"
        )

    # =========================================================================
    # SENSOR B
    # =========================================================================

    with c2:

        st.markdown(
            "### Sensor B"
        )

        lat_b = st.number_input(
            "Latitud B",
            value=4.61050000,
            format="%.8f"
        )

        lon_b = st.number_input(
            "Longitud B",
            value=-74.08250000,
            format="%.8f"
        )

    # =========================================================================
    # DISTANCIA
    # =========================================================================

    distancia = st.number_input(
        "Distancia aproximada entre sensores (m)",
        value=100.0,
        min_value=1.0
    )

    # =========================================================================
    # BOTÓN
    # =========================================================================

    if st.button(
        "Registrar sensores"
    ):

        try:

            # ================================================================
            # GEOMETRÍA
            # ================================================================

            linea_simple = LineString(
                [
                    (lon_a, lat_a),
                    (lon_b, lat_b)
                ]
            )

            gdf_linea = gpd.GeoDataFrame(
                geometry=[linea_simple],
                crs="EPSG:4326"
            )

            linea_m = gdf_linea.to_crs(
                epsg=3116
            ).geometry.iloc[0]

            # ================================================================
            # SESSION STATE
            # ================================================================

            st.session_state['linea'] = linea_m

            st.session_state['L'] = distancia

            st.session_state['red'] = gdf_linea

            st.session_state['pos_a'] = [
                lat_a,
                lon_a
            ]

            st.session_state['pos_b'] = [
                lat_b,
                lon_b
            ]

            st.session_state['modo_mapa'] = 'AUTONOMO'

            # ================================================================
            # CONFIRMACIÓN
            # ================================================================

            st.success(
                "Sensores registrados correctamente"
            )

            st.info(
                f"""
                Distancia operacional:
                {distancia:.2f} m
                """
            )

            # ================================================================
            # MAPA
            # ================================================================

            mapa = folium.Map(

                location=[
                    (lat_a + lat_b) / 2,
                    (lon_a + lon_b) / 2
                ],

                zoom_start=18
            )

            # ================================================================
            # LÍNEA
            # ================================================================

            folium.GeoJson(
                gdf_linea
            ).add_to(mapa)

            # ================================================================
            # SENSOR A
            # ================================================================

            folium.Marker(

                [lat_a, lon_a],

                tooltip="Sensor A",

                icon=folium.Icon(
                    color='blue'
                )

            ).add_to(mapa)

            # ================================================================
            # SENSOR B
            # ================================================================

            folium.Marker(

                [lat_b, lon_b],

                tooltip="Sensor B",

                icon=folium.Icon(
                    color='green'
                )

            ).add_to(mapa)

            # ================================================================
            # MAPA STREAMLIT
            # ================================================================

            st_folium(
                mapa,
                width=1200,
                height=450
            )

        except Exception as e:

            st.error(
                f"Error registrando sensores: {e}"
            )
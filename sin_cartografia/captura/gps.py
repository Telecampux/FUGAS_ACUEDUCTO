# =============================================================================
# GPS REAL - SIN CARTOGRAFIA
# =============================================================================

import streamlit as st
from streamlit_js_eval import streamlit_js_eval


GPS_TIMEOUT_MS = 20000


def calcular_altimetria(altitud):
    if altitud is None:
        return None

    return round(float(altitud), 2)


def obtener_gps(component_key="gps_real"):
    js = f"""
    new Promise((resolve) => {{
        if (!navigator.geolocation) {{
            resolve({{
                error: {{
                    code: 0,
                    message: "El navegador no soporta geolocalizacion"
                }}
            }});
            return;
        }}

        navigator.geolocation.getCurrentPosition(
            async (position) => {{
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                let ubicacion = null;
                let altimetria = position.coords.altitude;

                try {{
                    const url = (
                        "https://nominatim.openstreetmap.org/reverse" +
                        `?format=jsonv2&lat=${{lat}}&lon=${{lon}}` +
                        "&zoom=10&addressdetails=1&accept-language=es"
                    );
                    const response = await fetch(url);

                    if (response.ok) {{
                        const data = await response.json();
                        const address = data.address || {{}};

                        ubicacion = {{
                            municipio: (
                                address.city ||
                                address.town ||
                                address.village ||
                                address.municipality ||
                                address.county ||
                                null
                            ),
                            departamento: (
                                address.state ||
                                address.region ||
                                address.state_district ||
                                null
                            ),
                            pais: address.country || null,
                            direccion: data.display_name || null,
                            estado: "OK"
                        }};
                    }} else {{
                        ubicacion = {{
                            estado: `No se pudo consultar municipio/departamento/pais (${{response.status}})`
                        }};
                    }}
                }} catch (error) {{
                    ubicacion = {{
                        estado: "No se pudo consultar municipio/departamento/pais"
                    }};
                }}

                if (altimetria === null || altimetria === undefined) {{
                    try {{
                        const elevationUrl = (
                            "https://api.open-meteo.com/v1/elevation" +
                            `?latitude=${{lat}}&longitude=${{lon}}`
                        );
                        const elevationResponse = await fetch(elevationUrl);

                        if (elevationResponse.ok) {{
                            const elevationData = await elevationResponse.json();
                            const elevation = elevationData.elevation || [];

                            if (elevation.length > 0 && elevation[0] !== null) {{
                                altimetria = elevation[0];
                            }}
                        }}
                    }} catch (error) {{
                        altimetria = null;
                    }}
                }}

                resolve({{
                    coords: {{
                        latitude: lat,
                        longitude: lon,
                        altitude: position.coords.altitude,
                        altimetria: altimetria,
                        accuracy: position.coords.accuracy,
                        altitudeAccuracy: position.coords.altitudeAccuracy,
                        heading: position.coords.heading,
                        speed: position.coords.speed
                    }},
                    ubicacion: ubicacion,
                    timestamp: position.timestamp
                }});
            }},
            (error) => {{
                resolve({{
                    error: {{
                        code: error.code,
                        message: error.message
                    }}
                }});
            }},
            {{
                enableHighAccuracy: true,
                timeout: {GPS_TIMEOUT_MS},
                maximumAge: 0
            }}
        );
    }})
    """

    respuesta = streamlit_js_eval(
        js_expressions=js,
        key=component_key
    )

    if not respuesta:
        st.session_state["gps_estado"] = "Esperando respuesta del GPS real"
        return None

    error = respuesta.get("error")

    if error:
        st.session_state["gps_estado"] = traducir_error_gps(error)
        return None

    coords = respuesta.get("coords", {})
    lat = coords.get("latitude")
    lon = coords.get("longitude")

    if lat is None or lon is None:
        st.session_state["gps_estado"] = "El GPS no entrego latitud y longitud"
        return None

    st.session_state["gps_estado"] = "GPS real obtenido"
    ubicacion = respuesta.get("ubicacion") or {}

    return normalizar_gps(
        lat=lat,
        lon=lon,
        alt=coords.get("altitude"),
        altimetria=coords.get("altimetria"),
        precision=coords.get("accuracy"),
        estado="GPS_REAL",
        timestamp=respuesta.get("timestamp"),
        municipio=ubicacion.get("municipio"),
        departamento=ubicacion.get("departamento"),
        pais=ubicacion.get("pais"),
        direccion=ubicacion.get("direccion"),
        ubicacion_estado=ubicacion.get("estado")
    )


def traducir_error_gps(error):
    codigo = error.get("code")
    mensaje = error.get("message", "")

    if codigo == 1:
        return "Permiso de ubicacion denegado. Active la ubicacion para este sitio en el navegador."

    if codigo == 2:
        return "Ubicacion no disponible. Active GPS/datos del dispositivo y acerquese a cielo abierto."

    if codigo == 3:
        return "Tiempo agotado obteniendo GPS real. Intente nuevamente."

    if mensaje:
        return f"GPS real no disponible: {mensaje}"

    return "GPS real no disponible"


def normalizar_gps(
    lat,
    lon,
    alt=None,
    altimetria=None,
    precision=None,
    estado="GPS_REAL",
    timestamp=None,
    municipio=None,
    departamento=None,
    pais=None,
    direccion=None,
    ubicacion_estado=None
):
    lat = float(lat)
    lon = float(lon)
    altimetria = (
        calcular_altimetria(altimetria)
        if altimetria is not None
        else calcular_altimetria(alt)
    )

    if lat < -90 or lat > 90:
        raise ValueError("La latitud debe estar entre -90 y 90")

    if lon < -180 or lon > 180:
        raise ValueError("La longitud debe estar entre -180 y 180")

    return {
        "lat": lat,
        "lon": lon,
        "alt": None if alt is None else float(alt),
        "altimetria": altimetria,
        "altitud": altimetria,
        "precision": None if precision is None else float(precision),
        "estado": estado,
        "timestamp": timestamp,
        "municipio": municipio,
        "departamento": departamento,
        "pais": pais,
        "direccion": direccion,
        "ubicacion_estado": ubicacion_estado
    }


def mostrar_gps(component_key="gps_real_info"):
    gps = obtener_gps(component_key=component_key)

    st.subheader(
        "Informacion GPS"
    )

    if gps is None:
        st.warning(
            st.session_state.get(
                "gps_estado",
                "Autorice la ubicacion del navegador para obtener GPS real."
            )
        )
        return None

    c1, c2 = st.columns(2)

    c1.metric(
        "Latitud",
        gps["lat"]
    )

    c2.metric(
        "Longitud",
        gps["lon"]
    )

    c3, c4 = st.columns(2)

    c3.metric(
        "Altimetria",
        gps["altimetria"] if gps.get("altimetria") is not None else "N/D"
    )

    c4.metric(
        "Precision",
        f"{gps['precision']} m" if gps["precision"] is not None else "N/D"
    )

    st.success(
        f"Estado GPS: {gps['estado']}"
    )

    st.write(
        {
            "municipio": gps.get("municipio"),
            "departamento": gps.get("departamento"),
            "pais": gps.get("pais"),
            "ubicacion_estado": gps.get("ubicacion_estado")
        }
    )

    return gps

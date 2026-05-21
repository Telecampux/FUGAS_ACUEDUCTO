import streamlit as st

from sin_cartografia.captura.gps import obtener_gps

from sin_cartografia.captura.captura_puntos import (
    registrar_punto
)

from sin_cartografia.captura.conexiones import (
    MATERIALES_TUBERIA,
    TIPOS_TUBERIA,
    registrar_conexion
)

from sin_cartografia.validacion.topologia import (
    validar_topologia
)

from sin_cartografia.almacenamiento.persistencia import (
    guardar_proyecto,
    cargar_proyecto
)

from sin_cartografia.mapas.mapa import (
    visualizar_mapa
)

from sin_cartografia.exportacion.geojson import (
    exportar_geojson
)

# =============================================================================
# CONFIGURACIÓN GENERAL
# =============================================================================

st.set_page_config(
    page_title="IANC_H2O - Levantamiento",
    layout="wide"
)

# =============================================================================
# ESTADO GLOBAL
# =============================================================================


def inicializar_estado():

    estados = {
        "puntos": [],
        "conexiones": [],
        "proyecto": None,
        "gps": None,
        "errores": [],
        "modo": "SIN_CARTOGRAFIA"
    }

    for clave, valor in estados.items():

        if clave not in st.session_state:

            st.session_state[clave] = valor


inicializar_estado()

# =============================================================================
# TÍTULO
# =============================================================================

st.title(
    "IANC_H2O - Sin Cartografía"
)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:

    st.header(
        "Levantamiento"
    )

    menu = st.radio(
        "Módulos",
        [
            "Proyecto",
            "Captura GPS",
            "Registro Nodos",
            "Conexiones",
            "Mapa",
            "Validación",
            "Exportación"
        ]
    )

# =============================================================================
# PROYECTO
# =============================================================================

if menu == "Proyecto":

    st.header(
        "Proyecto de Levantamiento"
    )

    nombre = st.text_input(
        "Nombre proyecto"
    )

    municipio = st.text_input(
        "Municipio"
    )

    operador = st.text_input(
        "Operador"
    )

    descripcion = st.text_area(
        "Descripción"
    )

    if st.button(
        "Crear proyecto"
    ):

        st.session_state["proyecto"] = {
            "nombre": nombre,
            "municipio": municipio,
            "operador": operador,
            "descripcion": descripcion
        }

        st.success(
            "Proyecto creado"
        )

    st.divider()

    archivo = st.file_uploader(
        "Cargar proyecto",
        type=["json"]
    )

    if archivo is not None:

        cargar_proyecto(
            archivo
        )

        st.success(
            "Proyecto cargado"
        )

# =============================================================================
# GPS
# =============================================================================

if menu == "Captura GPS":

    st.header(
        "Captura GPS"
    )

    if st.button(
        "Obtener ubicación"
    ):

        gps = obtener_gps()

        st.session_state["gps"] = gps

    if st.session_state["gps"]:

        st.json(
            st.session_state["gps"]
        )

# =============================================================================
# NODOS
# =============================================================================

if menu == "Registro Nodos":

    st.header(
        "Registro de Nodos"
    )

    tipo = st.selectbox(
        "Tipo",
        [
            "Valvula",
            "Hidrante",
            "Empalme",
            "Sensor",
            "Tanque",
            "Acometida",
            "Final Linea"
        ]
    )

    nombre = st.text_input(
        "Nombre nodo"
    )

    descripcion = st.text_area(
        "Descripción"
    )

    foto = st.file_uploader(
        "Fotografía",
        type=[
            "jpg",
            "jpeg",
            "png"
        ]
    )

    gps_actual = st.session_state.get(
        "gps"
    )

    if gps_actual:

        st.info(
            f"""
            Lat:
            {gps_actual['lat']}

            Lon:
            {gps_actual['lon']}
            """
        )

    if st.button(
        "Registrar nodo"
    ):

        nodo = registrar_punto(
            nombre=nombre,
            tipo=tipo,
            descripcion=descripcion,
            gps=gps_actual,
            foto=foto
        )

        st.session_state["puntos"].append(
            nodo
        )

        st.success(
            "Nodo registrado"
        )

    st.divider()

    st.subheader(
        "Nodos registrados"
    )

    st.dataframe(
        st.session_state["puntos"],
        width="stretch"
    )

# =============================================================================
# CONEXIONES
# =============================================================================

if menu == "Conexiones":

    st.header(
        "Conexiones"
    )

    puntos = st.session_state["puntos"]

    nombres = [

        p["nombre"]

        for p in puntos
    ]

    if len(nombres) >= 2:

        origen = st.selectbox(
            "Origen",
            nombres,
            key="origen"
        )

        destino = st.selectbox(
            "Destino",
            nombres,
            index=1,
            key="destino"
        )

        distancia = st.number_input(
            "Distancia (m)",
            min_value=0.0,
            key="conexion_distancia"
        )

        diametro = st.number_input(
            "Diámetro (mm)",
            min_value=0.0,
            key="conexion_diametro"
        )

        material = st.selectbox(
            "Material",
            MATERIALES_TUBERIA,
            key="conexion_material"
        )

        tipo_tuberia = st.selectbox(
            "Tipo de tuberia",
            TIPOS_TUBERIA,
            key="conexion_tipo_tuberia"
        )

        if st.button(
            "Registrar conexión"
        ):

            try:
                conexion = registrar_conexion(
                    origen=origen,
                    destino=destino,
                    distancia=distancia,
                    diametro=diametro,
                    material=material,
                    tipo_red=tipo_tuberia
                )
            except ValueError as error:
                st.error(str(error))
                conexion = None

            if conexion is not None:
                st.session_state["conexiones"].append(
                    conexion
                )

                st.success(
                    "Conexión registrada"
                )

    else:

        st.warning(
            "Debe existir mínimo dos nodos"
        )

    st.divider()

    st.subheader(
        "Conexiones registradas"
    )

    st.dataframe(
        st.session_state["conexiones"],
        width="stretch"
    )

# =============================================================================
# MAPA
# =============================================================================

if menu == "Mapa":

    st.header(
        "Visualización Cartográfica"
    )

    visualizar_mapa(
        puntos=st.session_state["puntos"],
        conexiones=st.session_state["conexiones"]
    )

# =============================================================================
# VALIDACIÓN
# =============================================================================

if menu == "Validación":

    st.header(
        "Validación Topológica"
    )

    errores = validar_topologia(
        puntos=st.session_state["puntos"],
        conexiones=st.session_state["conexiones"]
    )

    st.session_state["errores"] = errores

    if len(errores) == 0:

        st.success(
            "Red válida"
        )

    else:

        for error in errores:

            st.error(
                error
            )

# =============================================================================
# EXPORTACIÓN
# =============================================================================

if menu == "Exportación":

    st.header(
        "Exportación"
    )

    col1, col2 = st.columns(2)

    if col1.button(
        "Guardar proyecto"
    ):

        guardar_proyecto(
            puntos=st.session_state["puntos"],
            conexiones=st.session_state["conexiones"],
            proyecto=st.session_state["proyecto"]
        )

        st.success(
            "Proyecto guardado"
        )

    if col2.button(
        "Exportar GeoJSON"
    ):

        try:
            rutas = exportar_geojson(
                puntos=st.session_state["puntos"],
                conexiones=st.session_state["conexiones"],
                nombre=st.session_state["proyecto"].get(
                    "nombre",
                    "levantamiento"
                )
            )

            st.success(
                "GeoJSON exportado en BD_PROYECTOS"
            )
            st.write(
                rutas
            )

        except ValueError as error:
            st.error(str(error))

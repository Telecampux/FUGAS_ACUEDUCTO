import streamlit as st

import json

from sin_cartografia.captura.gps import obtener_gps, calcular_altimetria
from sin_cartografia.captura.captura_puntos import mostrar_formulario_nodo
from sin_cartografia.captura.conexiones import (
    MATERIALES_TUBERIA,
    TIPOS_TUBERIA,
    registrar_conexion
)
from sin_cartografia.validacion.topologia import validar_topologia
from sin_cartografia.almacenamiento.persistencia import (
    guardar_proyecto,
    cargar_proyecto,
    eliminar_archivo_proyecto,
    listar_proyectos_guardados,
    cargar_proyecto_guardado
)
from sin_cartografia.mapas.mapa import visualizar_mapa
from sin_cartografia.exportacion.geojson import exportar_geojson

# =============================================================================
# CONFIGURACION GENERAL
# =============================================================================

if __name__ == "__main__":
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
        "gps_nodo": None,
        "gps_proyecto": None,
        "gps_historial": [],
        "solicitar_gps_proyecto": False,
        "solicitar_gps_nodo": False,
        "gps_proyecto_intento": 0,
        "gps_nodo_intento": 0,
        "gps_estado": None,
        "errores": [],
        "modo": "SIN_CARTOGRAFIA"
    }

    for clave, valor in estados.items():

        if clave not in st.session_state:

            st.session_state[clave] = valor


inicializar_estado()


def administrar_proyecto():
    proyecto = st.session_state.get("proyecto")

    if not proyecto:
        return

    st.divider()

    st.subheader(
        "Ver, modificar o eliminar proyecto"
    )

    st.json(proyecto)

    nuevo_nombre = st.text_input(
        "Nombre proyecto actual",
        value=proyecto.get("nombre", ""),
        key="editar_proyecto_nombre"
    )

    nuevo_municipio = st.text_input(
        "Municipio proyecto actual",
        value=proyecto.get("municipio", ""),
        key="editar_proyecto_municipio"
    )

    nuevo_operador = st.text_input(
        "Operador proyecto actual",
        value=proyecto.get("operador", ""),
        key="editar_proyecto_operador"
    )

    nueva_descripcion = st.text_area(
        "Descripcion proyecto actual",
        value=proyecto.get("descripcion", ""),
        key="editar_proyecto_descripcion"
    )

    reemplazar_gps = st.checkbox(
        "Reemplazar GPS con la ultima lectura capturada para este proyecto",
        key="editar_proyecto_reemplazar_gps"
    )

    col1, col2 = st.columns(2)

    if col1.button(
        "Guardar cambios proyecto"
    ):
        nombre_limpio = nuevo_nombre.strip()

        if not nombre_limpio:
            st.error("El nombre del proyecto es obligatorio")
        else:
            gps = proyecto.get("gps")

            if reemplazar_gps:
                gps = st.session_state.get("gps_proyecto")

                if gps is None:
                    st.error("Debe capturar un GPS antes de reemplazarlo")
                    return

            st.session_state["proyecto"] = {
                **proyecto,
                "nombre": nombre_limpio,
                "municipio": nuevo_municipio,
                "operador": nuevo_operador,
                "descripcion": nueva_descripcion,
                "gps": gps,
                "latitud": gps.get("lat") if gps else None,
                "longitud": gps.get("lon") if gps else None,
                "municipio_gps": gps.get("municipio") if gps else None,
                "departamento_gps": gps.get("departamento") if gps else None,
                "pais_gps": gps.get("pais") if gps else None,
                "direccion_gps": gps.get("direccion") if gps else None
            }

            st.success("Proyecto actualizado")

    confirmar_eliminar = st.checkbox(
        "Confirmar eliminacion del proyecto activo, nodos y conexiones",
        key="confirmar_eliminar_proyecto"
    )

    if col2.button(
        "Eliminar proyecto",
        disabled=not confirmar_eliminar
    ):
        ruta_eliminada = eliminar_archivo_proyecto(
            proyecto
        )

        st.session_state["proyecto"] = None
        st.session_state["puntos"] = []
        st.session_state["conexiones"] = []
        st.session_state["gps_proyecto"] = None
        st.session_state["gps_nodo"] = None

        if ruta_eliminada:
            st.success(f"Proyecto eliminado: {ruta_eliminada}")
        else:
            st.success("Proyecto eliminado de la sesion")

        st.rerun()


def administrar_conexiones(nombres):
    conexiones = st.session_state["conexiones"]

    if not conexiones:
        return

    if len(nombres) < 2:
        st.warning(
            "No hay nodos suficientes para modificar conexiones existentes"
        )
        return

    st.subheader(
        "Ver, modificar o eliminar conexion"
    )

    opciones = [
        f"{indice + 1}. {conexion.get('origen')} -> {conexion.get('destino')}"
        for indice, conexion in enumerate(conexiones)
    ]

    seleccion = st.selectbox(
        "Conexion",
        opciones,
        key="editar_conexion"
    )

    indice = opciones.index(seleccion)
    conexion = conexiones[indice]

    st.json(conexion)

    origen_actual = conexion.get("origen")
    destino_actual = conexion.get("destino")

    origen_index = nombres.index(origen_actual) if origen_actual in nombres else 0
    destino_index = nombres.index(destino_actual) if destino_actual in nombres else 0

    nuevo_origen = st.selectbox(
        "Origen conexion",
        nombres,
        index=origen_index,
        key=f"editar_conexion_origen_{indice}"
    )

    nuevo_destino = st.selectbox(
        "Destino conexion",
        nombres,
        index=destino_index,
        key=f"editar_conexion_destino_{indice}"
    )

    nueva_distancia = st.number_input(
        "Distancia conexion (m)",
        min_value=0.0,
        value=float(conexion.get("distancia", 0.0)),
        key=f"editar_conexion_distancia_{indice}"
    )

    nuevo_diametro = st.number_input(
        "Diametro conexion (mm)",
        min_value=0.0,
        value=float(conexion.get("diametro", 0.0)),
        key=f"editar_conexion_diametro_{indice}"
    )

    materiales = list(MATERIALES_TUBERIA)

    material_actual = conexion.get("material", materiales[0])

    if material_actual not in materiales:
        materiales.append(material_actual)

    nuevo_material = st.selectbox(
        "Material conexion",
        materiales,
        index=materiales.index(material_actual),
        key=f"editar_conexion_material_{indice}"
    )

    tipos_tuberia = list(TIPOS_TUBERIA)
    tipo_tuberia_actual = conexion.get("tipo_red", tipos_tuberia[0])

    if tipo_tuberia_actual not in tipos_tuberia:
        tipos_tuberia.append(tipo_tuberia_actual)

    nuevo_tipo_tuberia = st.selectbox(
        "Tipo de tuberia",
        tipos_tuberia,
        index=tipos_tuberia.index(tipo_tuberia_actual),
        key=f"editar_conexion_tipo_tuberia_{indice}"
    )

    col1, col2 = st.columns(2)

    if col1.button(
        "Guardar cambios conexion",
        key=f"guardar_cambios_conexion_{indice}"
    ):
        try:
            conexiones[indice] = registrar_conexion(
                origen=nuevo_origen,
                destino=nuevo_destino,
                distancia=nueva_distancia,
                diametro=nuevo_diametro,
                material=nuevo_material,
                tipo_red=nuevo_tipo_tuberia
            )

            st.success("Conexion actualizada")

        except ValueError as error:
            st.error(str(error))

    confirmar_eliminar = st.checkbox(
        "Confirmar eliminacion de esta conexion",
        key=f"confirmar_eliminar_conexion_{indice}"
    )

    if col2.button(
        "Eliminar conexion",
        key=f"eliminar_conexion_{indice}",
        disabled=not confirmar_eliminar
    ):
        conexiones.pop(indice)
        st.success("Conexion eliminada")
        st.rerun()


def solicitar_gps_proyecto():
    st.session_state["solicitar_gps_proyecto"] = True
    st.session_state["gps_proyecto"] = None
    st.session_state["gps_proyecto_intento"] += 1


def mostrar_captura_gps_proyecto():
    if st.session_state["solicitar_gps_proyecto"]:
        gps = obtener_gps(
            component_key=f"gps_proyecto_real_{st.session_state['gps_proyecto_intento']}"
        )

        if gps:
            st.session_state["gps"] = gps
            st.session_state["gps_proyecto"] = gps
            st.session_state["gps_historial"].append(gps)
            st.session_state["solicitar_gps_proyecto"] = False
            st.success("GPS real obtenido para este proyecto")
        else:
            st.warning(
                st.session_state.get(
                    "gps_estado",
                    "Autorice la ubicacion del navegador y espere la lectura GPS real."
                )
            )

    gps_proyecto = st.session_state.get("gps_proyecto")

    if gps_proyecto:
        st.info(
            f"Lat: {gps_proyecto['lat']} | Lon: {gps_proyecto['lon']} | Precision: {gps_proyecto.get('precision', 'N/D')} m"
        )

        ubicacion = {
            "municipio": gps_proyecto.get("municipio"),
            "departamento": gps_proyecto.get("departamento"),
            "pais": gps_proyecto.get("pais"),
            "direccion": gps_proyecto.get("direccion"),
            "altimetria": valor_altimetria_gps(gps_proyecto)
        }

        if any(ubicacion.values()):
            st.write(ubicacion)

        if gps_proyecto.get("ubicacion_estado") not in (None, "OK"):
            st.warning(
                gps_proyecto.get("ubicacion_estado")
            )
    else:
        st.warning(
            "Cargando GPS real del proyecto. Autorice la ubicacion del navegador."
        )

    return gps_proyecto


def valor_gps(gps, clave):
    if not gps:
        return ""

    valor = gps.get(clave)

    if valor is None:
        return ""

    return str(valor)


def valor_altimetria_gps(gps):
    if not gps:
        return ""

    altimetria = gps.get("altimetria")

    if altimetria is None:
        altimetria = calcular_altimetria(gps.get("alt"))

    if altimetria is None:
        return ""

    return str(altimetria)


def mostrar_datos_gps_proyecto(gps, prefijo):
    st.text_input(
        "Municipio GPS",
        value=valor_gps(gps, "municipio"),
        disabled=True
    )

    st.text_input(
        "Departamento GPS",
        value=valor_gps(gps, "departamento"),
        disabled=True
    )

    st.text_input(
        "Pais GPS",
        value=valor_gps(gps, "pais"),
        disabled=True
    )

    st.text_input(
        "Altimetria GPS",
        value=valor_altimetria_gps(gps) or "N/D",
        disabled=True
    )


def construir_datos_proyecto(nombre, operador, descripcion, gps, proyecto=None):
    datos = {
        "nombre": nombre.strip(),
        "municipio": gps.get("municipio"),
        "departamento": gps.get("departamento"),
        "pais": gps.get("pais"),
        "operador": operador.strip(),
        "descripcion": descripcion.strip(),
        "gps": gps,
        "latitud": gps["lat"],
        "longitud": gps["lon"],
        "altimetria": calcular_altimetria(
            gps.get("altimetria") if gps.get("altimetria") is not None else gps.get("alt")
        ),
        "altitud": calcular_altimetria(
            gps.get("altimetria") if gps.get("altimetria") is not None else gps.get("alt")
        ),
        "municipio_gps": gps.get("municipio"),
        "departamento_gps": gps.get("departamento"),
        "pais_gps": gps.get("pais"),
        "direccion_gps": gps.get("direccion")
    }

    if proyecto:
        return {
            **proyecto,
            **datos
        }

    return datos


def cargar_proyecto_desde_archivo(key):
    archivo = st.file_uploader(
        "Cargar proyecto existente",
        type=["json", "geojson"],
        key=key
    )

    if archivo is not None:
        cargar_proyecto(
            archivo
        )

        st.success(
            "Proyecto cargado"
        )

        return True

    return False


def texto_contiene_filtro(registro, filtro):
    if not filtro:
        return True

    texto = json.dumps(
        registro,
        ensure_ascii=False
    ).lower()

    return filtro.lower() in texto


def mostrar_tabla_consulta(titulo, registros, filtro, columnas):
    st.subheader(
        titulo
    )

    if not registros:
        st.info(
            "No hay registros para consultar."
        )
        return

    filtrados = [
        registro for registro in registros
        if texto_contiene_filtro(
            registro,
            filtro
        )
    ]

    if not filtrados:
        st.warning(
            "No hay registros que coincidan con la busqueda."
        )
        return

    vista = []

    for indice, registro in enumerate(filtrados):
        fila = {
            "#": indice + 1
        }

        for columna in columnas:
            fila[columna] = registro.get(
                columna
            )

        vista.append(
            fila
        )

    st.dataframe(
        vista,
        width="stretch"
    )

    opciones = []

    for indice, registro in enumerate(filtrados):
        etiqueta = registro.get("nombre")

        if not etiqueta:
            origen = registro.get("origen") or ""
            destino = registro.get("destino") or ""
            etiqueta = f"{origen} -> {destino}".strip()

        opciones.append(
            f"{indice + 1}. {etiqueta or 'Sin nombre'}"
        )

    seleccion = st.selectbox(
        f"Detalle {titulo.lower()}",
        opciones,
        key=f"consulta_detalle_{titulo}"
    )

    st.json(
        filtrados[opciones.index(seleccion)]
    )


def consultar_proyecto_cargado():
    st.subheader(
        "Cargar proyecto para consulta"
    )

    proyectos_guardados = listar_proyectos_guardados()

    if proyectos_guardados:
        nombre_archivo = st.selectbox(
            "Proyecto guardado",
            proyectos_guardados,
            key="consulta_proyecto_guardado"
        )

        if st.button(
            "Cargar proyecto guardado",
            key="consulta_cargar_proyecto_guardado"
        ):
            cargar_proyecto_guardado(
                nombre_archivo
            )

            st.success(
                "Proyecto cargado para consulta"
            )
    else:
        st.info(
            "No hay proyectos guardados en BD_PROYECTOS."
        )

    cargar_proyecto_desde_archivo(
        key="consulta_proyecto_archivo"
    )

    proyecto = st.session_state.get("proyecto")
    puntos = st.session_state.get(
        "puntos",
        []
    )
    conexiones = st.session_state.get(
        "conexiones",
        []
    )

    if not proyecto:
        st.warning(
            "Cargue un proyecto para consultar sus datos."
        )
        return

    st.divider()
    st.subheader(
        "Resumen del proyecto cargado"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Proyecto",
        proyecto.get("nombre", "Sin nombre")
    )
    col2.metric(
        "Nodos",
        len(puntos)
    )
    col3.metric(
        "Conexiones",
        len(conexiones)
    )

    filtro = st.text_input(
        "Buscar en nodos, conexiones o JSON completo",
        key="consulta_filtro"
    )

    tab_proyecto, tab_nodos, tab_conexiones, tab_json = st.tabs(
        [
            "Proyecto",
            "Nodos",
            "Conexiones",
            "JSON completo"
        ]
    )

    with tab_proyecto:
        st.json(
            proyecto
        )

    with tab_nodos:
        mostrar_tabla_consulta(
            "Nodos",
            puntos,
            filtro,
            [
                "nombre",
                "tipo",
                "descripcion",
                "latitud",
                "longitud",
                "altimetria"
            ]
        )

    with tab_conexiones:
        mostrar_tabla_consulta(
            "Conexiones",
            conexiones,
            filtro,
            [
                "origen",
                "destino",
                "distancia",
                "diametro",
                "material",
                "tipo_red"
            ]
        )

    with tab_json:
        st.json(
            {
                "proyecto": proyecto,
                "puntos": puntos,
                "conexiones": conexiones
            }
        )


def datos_proyecto_validos(nombre, operador, descripcion, gps):
    return all(
        [
            nombre.strip(),
            operador.strip(),
            descripcion.strip(),
            gps is not None
        ]
    )

# =============================================================================
# TITULO
# =============================================================================

st.title(
    "IANC_H2O - Sin Cartografia"
)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:

    st.header(
        "Levantamiento"
    )

    menu = st.radio(
        "Modulos",
        [
            "Proyecto",
            "Registro Nodos",
            "Conexiones",
            "Mapa",
            "Validacion",
            "Exportacion"
        ]
    )

# =============================================================================
# PROYECTO
# =============================================================================

if menu == "Proyecto":

    st.header(
        "Proyecto de Levantamiento"
    )

    accion_proyecto = st.radio(
        "Gestion de proyecto",
        [
            "PROYECTO NUEVO",
            "CONSULTAR PROYECTO CARGADO",
            "MODIFICAR PROYECTO EXISTENTE",
            "ELIMINAR PROYECTO EXISTENTE"
        ],
        horizontal=True,
        label_visibility="collapsed"
    )

    if accion_proyecto == "PROYECTO NUEVO":
        if (
            st.session_state.get("gps_proyecto") is None
            and not st.session_state.get("solicitar_gps_proyecto")
        ):
            solicitar_gps_proyecto()

        st.subheader(
            "Identificar GPS para este proyecto"
        )

        if st.button(
            "Actualizar GPS real de este proyecto",
            key="nuevo_proyecto_actualizar_gps"
        ):
            solicitar_gps_proyecto()

        gps_proyecto = mostrar_captura_gps_proyecto()
        mostrar_datos_gps_proyecto(
            gps_proyecto,
            prefijo="nuevo_proyecto"
        )

        nombre = st.text_input(
            "Nombre proyecto",
            key="nuevo_proyecto_nombre"
        )

        operador = st.text_input(
            "Operador",
            key="nuevo_proyecto_operador"
        )

        descripcion = st.text_area(
            "Descripcion",
            key="nuevo_proyecto_descripcion"
        )

        formulario_valido = datos_proyecto_validos(
            nombre,
            operador,
            descripcion,
            gps_proyecto
        )

        if not formulario_valido:
            st.warning(
                "Complete nombre, operador, descripcion y GPS para registrar el proyecto."
            )

        if st.button(
            "Registrar proyecto",
            disabled=not formulario_valido,
            key="registrar_proyecto_nuevo"
        ):
            st.session_state["proyecto"] = construir_datos_proyecto(
                nombre=nombre,
                operador=operador,
                descripcion=descripcion,
                gps=gps_proyecto
            )

            st.success(
                "Proyecto registrado con GPS real"
            )

    elif accion_proyecto == "CONSULTAR PROYECTO CARGADO":
        consultar_proyecto_cargado()

    elif accion_proyecto == "MODIFICAR PROYECTO EXISTENTE":
        if st.session_state.get("proyecto") is None:
            cargar_proyecto_desde_archivo(
                key="modificar_proyecto_cargar"
            )

        proyecto = st.session_state.get("proyecto")

        if proyecto is None:
            st.warning(
                "Cargue un proyecto existente para modificarlo."
            )
        else:
            st.json(proyecto)

            st.subheader(
                "Identificar GPS para este proyecto"
            )

            nombre = st.text_input(
                "Nombre proyecto",
                value=proyecto.get("nombre", ""),
                key="modificar_proyecto_nombre"
            )

            operador = st.text_input(
                "Operador",
                value=proyecto.get("operador", ""),
                key="modificar_proyecto_operador"
            )

            descripcion = st.text_area(
                "Descripcion",
                value=proyecto.get("descripcion", ""),
                key="modificar_proyecto_descripcion"
            )

            reemplazar_gps = st.checkbox(
                "Reemplazar GPS con una nueva lectura",
                key="modificar_proyecto_reemplazar_gps"
            )

            if reemplazar_gps:
                if st.button(
                    "Actualizar GPS real de este proyecto",
                    key="modificar_proyecto_actualizar_gps"
                ):
                    solicitar_gps_proyecto()

                gps_proyecto = mostrar_captura_gps_proyecto()
            else:
                gps_proyecto = proyecto.get("gps")

                if gps_proyecto:
                    st.info(
                        f"GPS actual - Lat: {gps_proyecto['lat']} | Lon: {gps_proyecto['lon']}"
                    )
                else:
                    st.warning(
                        "El proyecto no tiene GPS guardado. Active el reemplazo GPS para capturarlo."
                    )

            mostrar_datos_gps_proyecto(
                gps_proyecto,
                prefijo="modificar_proyecto"
            )

            formulario_valido = datos_proyecto_validos(
                nombre,
                operador,
                descripcion,
                gps_proyecto
            )

            if not formulario_valido:
                st.warning(
                    "Complete nombre, operador, descripcion y GPS para guardar el proyecto."
                )

            if st.button(
                "Registrar cambios del proyecto",
                disabled=not formulario_valido,
                key="registrar_cambios_proyecto"
            ):
                st.session_state["proyecto"] = construir_datos_proyecto(
                    nombre=nombre,
                    operador=operador,
                    descripcion=descripcion,
                    gps=gps_proyecto,
                    proyecto=proyecto
                )

                st.success(
                    "Proyecto actualizado"
                )

    elif accion_proyecto == "ELIMINAR PROYECTO EXISTENTE":
        if st.session_state.get("proyecto") is None:
            cargar_proyecto_desde_archivo(
                key="eliminar_proyecto_cargar"
            )

        proyecto = st.session_state.get("proyecto")

        if proyecto is None:
            st.warning(
                "Cargue un proyecto existente para eliminarlo."
            )
        else:
            st.json(proyecto)

            confirmar_eliminar = st.checkbox(
                "Confirmar eliminacion del proyecto activo, nodos y conexiones",
                key="eliminar_proyecto_confirmar"
            )

            if st.button(
                "Eliminar proyecto existente",
                disabled=not confirmar_eliminar,
                key="eliminar_proyecto_existente"
            ):
                ruta_eliminada = eliminar_archivo_proyecto(
                    proyecto
                )

                st.session_state["proyecto"] = None
                st.session_state["puntos"] = []
                st.session_state["conexiones"] = []
                st.session_state["gps_proyecto"] = None
                st.session_state["gps_nodo"] = None

                if ruta_eliminada:
                    st.success(f"Proyecto eliminado: {ruta_eliminada}")
                else:
                    st.success("Proyecto eliminado de la sesion")

                st.rerun()

# =============================================================================
# NODOS
# =============================================================================

if menu == "Registro Nodos":

    st.header(
        "Registro de Nodos"
    )

    st.subheader(
        "Identificar GPS para este nodo"
    )

    mostrar_formulario_nodo()

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
            "Diametro (mm)",
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
            "Registrar conexion",
            key="registrar_conexion"
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

                st.session_state["conexiones"].append(
                    conexion
                )

                st.success(
                    "Conexion registrada"
                )

            except ValueError as error:

                st.error(
                    str(error)
                )

    else:

        st.warning(
            "Debe existir minimo dos nodos"
        )

    st.divider()

    st.subheader(
        "Conexiones registradas"
    )

    st.dataframe(
        st.session_state["conexiones"],
        width="stretch"
    )

    administrar_conexiones(nombres)

# =============================================================================
# MAPA
# =============================================================================

if menu == "Mapa":

    st.header(
        "Visualizacion Cartografica"
    )

    visualizar_mapa(
        puntos=st.session_state["puntos"],
        conexiones=st.session_state["conexiones"]
    )

# =============================================================================
# VALIDACION
# =============================================================================

if menu == "Validacion":

    st.header(
        "Validacion Topologica"
    )

    errores = validar_topologia(
        puntos=st.session_state["puntos"],
        conexiones=st.session_state["conexiones"]
    )

    st.session_state["errores"] = errores

    if len(errores) == 0:

        st.success(
            "Red valida"
        )

    else:

        for error in errores:

            st.error(
                error
            )

# =============================================================================
# EXPORTACION
# =============================================================================

if menu == "Exportacion":

    st.header(
        "Exportacion"
    )

    col1, col2 = st.columns(2)

    if col1.button(
        "Guardar proyecto"
    ):

        ruta = guardar_proyecto(
            puntos=st.session_state["puntos"],
            conexiones=st.session_state["conexiones"],
            proyecto=st.session_state["proyecto"]
        )

        if ruta:
            st.success(
                f"Proyecto guardado: {ruta}"
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





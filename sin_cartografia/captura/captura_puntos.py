# ============================================================
# ARCHIVO:
# cartografia/captura_puntos.py
# ============================================================

import streamlit as st

from sin_cartografia.captura.gps import obtener_gps, calcular_altimetria


TIPOS_NODO = [
    "Valvula",
    "Hidrante",
    "Empalme",
    "Sensor",
    "Tanque",
    "Acometida",
    "Final Linea"
]

# ============================================================
# REGISTRO MANUAL DE PUNTOS
# ============================================================

def registrar_punto(
    nombre=None,
    tipo=None,
    descripcion="",
    gps=None,
    foto=None
):
    if nombre is not None or tipo is not None or gps is not None:
        return construir_punto(
            nombre=nombre,
            tipo=tipo,
            descripcion=descripcion,
            gps=gps,
            foto=foto
        )

    return mostrar_formulario_nodo()


def construir_punto(
    nombre,
    tipo,
    descripcion="",
    gps=None,
    foto=None
):
    if not nombre or not str(nombre).strip():
        raise ValueError("El nombre del nodo es obligatorio")

    if gps is None:
        raise ValueError("Debe cargar o ingresar una ubicacion GPS")

    lat = gps.get("lat")
    lon = gps.get("lon")

    if lat is None or lon is None:
        raise ValueError("La ubicacion GPS debe incluir latitud y longitud")

    foto_nombre = getattr(foto, "name", None)

    return {
        "nombre": str(nombre).strip(),
        "tipo": tipo,
        "descripcion": descripcion,
        "gps": {
            "lat": float(lat),
            "lon": float(lon),
            "alt": gps.get("alt"),
            "altimetria": calcular_altimetria(
                gps.get("altimetria") if gps.get("altimetria") is not None else gps.get("alt")
            ),
            "precision": gps.get("precision"),
            "estado": gps.get("estado", "OK"),
            "municipio": gps.get("municipio"),
            "departamento": gps.get("departamento"),
            "pais": gps.get("pais"),
            "direccion": gps.get("direccion"),
            "ubicacion_estado": gps.get("ubicacion_estado")
        },
        "latitud": float(lat),
        "longitud": float(lon),
        "altimetria": calcular_altimetria(
            gps.get("altimetria") if gps.get("altimetria") is not None else gps.get("alt")
        ),
        "altitud": calcular_altimetria(
            gps.get("altimetria") if gps.get("altimetria") is not None else gps.get("alt")
        ),
        "municipio": gps.get("municipio"),
        "departamento": gps.get("departamento"),
        "pais": gps.get("pais"),
        "direccion": gps.get("direccion"),
        "foto": foto_nombre
    }


def inicializar_estado_formulario_nodo():
    estados = {
        "gps_nodo": None,
        "gps_historial": [],
        "solicitar_gps_nodo": False,
        "gps_nodo_intento": 0,
        "gps_estado": None,
        "puntos": []
    }

    for clave, valor in estados.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor


def solicitar_gps_nodo():
    st.session_state["solicitar_gps_nodo"] = True
    st.session_state["gps_nodo"] = None
    st.session_state["gps_nodo_intento"] += 1


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


def mostrar_datos_gps_nodo(gps):
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


def mostrar_formulario_nodo(mostrar_tabla=True):
    inicializar_estado_formulario_nodo()

    tipo = st.selectbox(
        "Tipo",
        TIPOS_NODO
    )

    nombre = st.text_input(
        "Nombre nodo"
    )

    descripcion = st.text_area(
        "Descripcion"
    )

    foto = st.file_uploader(
        "Fotografia",
        type=[
            "jpg",
            "jpeg",
            "png"
        ]
    )

    if (
        st.session_state.get("gps_nodo") is None
        and not st.session_state.get("solicitar_gps_nodo")
    ):
        solicitar_gps_nodo()

    st.caption(
        "El GPS real se carga automaticamente para cada nodo."
    )

    if st.button(
        "Actualizar GPS real de este nodo"
    ):
        solicitar_gps_nodo()

    if st.session_state["solicitar_gps_nodo"]:
        gps = obtener_gps(
            component_key=f"gps_nodo_real_{st.session_state['gps_nodo_intento']}"
        )

        if gps:
            st.session_state["gps"] = gps
            st.session_state["gps_nodo"] = gps
            st.session_state["gps_historial"].append(gps)
            st.session_state["solicitar_gps_nodo"] = False
            st.success("GPS real obtenido para este nodo")
        else:
            st.warning(
                st.session_state.get(
                    "gps_estado",
                    "Autorice la ubicacion del navegador y espere la lectura GPS real."
                )
            )

    gps_actual = st.session_state.get(
        "gps_nodo"
    )

    if gps_actual:
        st.info(
            f"Lat: {gps_actual['lat']} | Lon: {gps_actual['lon']} | Precision: {gps_actual.get('precision', 'N/D')} m"
        )
        mostrar_datos_gps_nodo(gps_actual)

        if gps_actual.get("ubicacion_estado") not in (None, "OK"):
            st.warning(
                gps_actual.get("ubicacion_estado")
            )
    else:
        st.warning(
            "Cargando GPS real del nodo. Autorice la ubicacion del navegador."
        )

    if st.button(
        "Registrar nodo"
    ):
        try:
            nombre_limpio = nombre.strip()

            if any(
                p.get("nombre") == nombre_limpio
                for p in st.session_state["puntos"]
            ):
                raise ValueError("Ya existe un nodo con ese nombre")

            nodo = construir_punto(
                nombre=nombre_limpio,
                tipo=tipo,
                descripcion=descripcion,
                gps=gps_actual,
                foto=foto
            )

            st.session_state["puntos"].append(
                nodo
            )

            st.session_state["gps_nodo"] = None
            solicitar_gps_nodo()

            st.success(
                "Nodo registrado. Se cargara automaticamente el GPS del siguiente nodo."
            )

        except ValueError as error:
            st.error(
                str(error)
            )

    if mostrar_tabla:
        st.divider()

        st.subheader(
            "Nodos registrados"
        )

        st.dataframe(
            st.session_state["puntos"],
            width="stretch"
        )

        administrar_nodos()


def administrar_nodos():
    puntos = st.session_state["puntos"]

    if not puntos:
        return

    st.subheader(
        "Ver, modificar o eliminar nodo"
    )

    opciones = [
        f"{indice + 1}. {punto.get('nombre', 'Sin nombre')}"
        for indice, punto in enumerate(puntos)
    ]

    seleccion = st.selectbox(
        "Nodo",
        opciones,
        key="editar_nodo"
    )

    indice = opciones.index(seleccion)
    nodo = puntos[indice]
    gps_actual = st.session_state.get("gps_nodo")

    st.json(nodo)

    nombre_actual = nodo.get("nombre", "")
    tipo_actual = nodo.get("tipo", TIPOS_NODO[0])

    if tipo_actual not in TIPOS_NODO:
        TIPOS_NODO.append(tipo_actual)

    nuevo_nombre = st.text_input(
        "Nombre nodo",
        value=nombre_actual,
        key=f"editar_nodo_nombre_{indice}"
    )

    nuevo_tipo = st.selectbox(
        "Tipo nodo",
        TIPOS_NODO,
        index=TIPOS_NODO.index(tipo_actual),
        key=f"editar_nodo_tipo_{indice}"
    )

    nueva_descripcion = st.text_area(
        "Descripcion nodo",
        value=nodo.get("descripcion", ""),
        key=f"editar_nodo_descripcion_{indice}"
    )

    reemplazar_gps = st.checkbox(
        "Reemplazar GPS con la ultima lectura capturada en este formulario",
        key=f"editar_nodo_reemplazar_gps_{indice}"
    )

    col1, col2 = st.columns(2)

    if col1.button(
        "Guardar cambios nodo",
        key=f"guardar_cambios_nodo_{indice}"
    ):
        try:
            nombre_limpio = nuevo_nombre.strip()

            if not nombre_limpio:
                raise ValueError("El nombre del nodo es obligatorio")

            if any(
                i != indice and p.get("nombre") == nombre_limpio
                for i, p in enumerate(puntos)
            ):
                raise ValueError("Ya existe un nodo con ese nombre")

            gps = nodo.get("gps")

            if reemplazar_gps:
                if gps_actual is None:
                    raise ValueError("Debe capturar un GPS antes de reemplazarlo")

                gps = gps_actual

            nodo_actualizado = construir_punto(
                nombre=nombre_limpio,
                tipo=nuevo_tipo,
                descripcion=nueva_descripcion,
                gps=gps,
                foto=None
            )

            nodo_actualizado["foto"] = nodo.get("foto")
            puntos[indice] = nodo_actualizado

            if nombre_limpio != nombre_actual:
                for conexion in st.session_state.get("conexiones", []):
                    if conexion.get("origen") == nombre_actual:
                        conexion["origen"] = nombre_limpio

                    if conexion.get("destino") == nombre_actual:
                        conexion["destino"] = nombre_limpio

            st.success("Nodo actualizado")

        except ValueError as error:
            st.error(str(error))

    confirmar_eliminar = st.checkbox(
        "Confirmar eliminacion de este nodo y sus conexiones",
        key=f"confirmar_eliminar_nodo_{indice}"
    )

    if col2.button(
        "Eliminar nodo",
        key=f"eliminar_nodo_{indice}",
        disabled=not confirmar_eliminar
    ):
        nombre_eliminado = nodo.get("nombre")

        st.session_state["puntos"].pop(indice)
        st.session_state["conexiones"] = [
            conexion for conexion in st.session_state.get("conexiones", [])
            if (
                conexion.get("origen") != nombre_eliminado
                and conexion.get("destino") != nombre_eliminado
            )
        ]

        st.success("Nodo eliminado")
        st.rerun()

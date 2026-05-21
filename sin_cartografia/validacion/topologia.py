# =============================================================================
# VALIDACION TOPOLOGIA - SIN CARTOGRAFIA
# =============================================================================


def validar_topologia(
    puntos,
    conexiones
):

    errores = []

    nombres_nodos = [
        p["nombre"]
        for p in puntos
    ]

    for punto in puntos:

        gps = punto.get("gps")

        if gps is None:

            errores.append(
                f"Nodo sin GPS: {punto.get('nombre', 'Sin nombre')}"
            )
            continue

        if gps.get("lat") is None or gps.get("lon") is None:

            errores.append(
                f"Nodo con GPS incompleto: {punto.get('nombre', 'Sin nombre')}"
            )

    for conexion in conexiones:

        origen = conexion["origen"]
        destino = conexion["destino"]

        if origen not in nombres_nodos:

            errores.append(
                f"Nodo origen inexistente: {origen}"
            )

        if destino not in nombres_nodos:

            errores.append(
                f"Nodo destino inexistente: {destino}"
            )

        if origen == destino:

            errores.append(
                f"Conexion invalida: {origen}"
            )

    if len(nombres_nodos) != len(set(nombres_nodos)):

        errores.append(
            "Existen nodos duplicados"
        )

    return errores

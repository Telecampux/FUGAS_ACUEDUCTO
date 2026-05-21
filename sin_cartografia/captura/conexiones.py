# =============================================================================
# CONEXIONES - SIN CARTOGRAFÍA
# =============================================================================


def registrar_conexion(
    origen,
    destino,
    distancia,
    diametro,
    material
):
    if not origen or not destino:
        raise ValueError("Debe seleccionar nodo origen y nodo destino")

    if origen == destino:
        raise ValueError("El origen y el destino deben ser nodos diferentes")

    if distancia <= 0:
        raise ValueError("La distancia debe ser mayor que cero")

    if diametro <= 0:
        raise ValueError("El diametro debe ser mayor que cero")

    conexion = {

        "origen": origen,
        "destino": destino,

        "distancia": distancia,

        "diametro": diametro,

        "material": material
    }

    return conexion

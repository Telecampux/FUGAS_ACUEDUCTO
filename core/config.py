# --- IDENTIDAD DEL SISTEMA ---
PROGRAMA_NOMBRE = "SISTEMA INTEGRAL DE AUDITORÍA P.R.P."
AUTOR = "ING. ADOLFO BARRERA VARGAS"
EMPRESA_DEFAULT = "Administración Municipal"

# --- DATOS TOPOLÓGICOS (MUNICIPIOS) ---
territorios = {
    "Villeta": {"coords": [5.0140, -74.4720], "costo": 3200, "z_base": 842.0},
    "Neiva": {"coords": [2.9273, -75.2819], "costo": 3500, "z_base": 442.0},
    "Chaparral": {"coords": [3.7231, -75.4832], "costo": 3100, "z_base": 854.0},
    "El Espinal": {"coords": [4.1492, -74.8878], "costo": 2900, "z_base": 323.0},
    "Villavicencio": {"coords": [4.1420, -73.6266], "costo": 3400, "z_base": 467.0}
}

# --- CONSTANTES TÉCNICAS ---
GRAVEDAD = 9.81
PRESION_ATM_ESTANDAR = 14.7  # PSI
COEFICIENTE_DESCARGA_FUGA = 0.6  # Para Torricelli
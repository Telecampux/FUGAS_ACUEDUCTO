# cartografia/config.py

MAPA_ZOOM_INICIAL = 16

MAPA_ESTILO = "OpenStreetMap"

COORDENADAS_BOGOTA = {

    "latitud": 4.7110,
    "longitud": -74.0721

}

TIPOS_PUNTO = [

    "Hidrante",
    "Válvula",
    "Tanque",
    "Bomba",
    "Sensor",
    "Caja",
    "Empalme",
    "Otro"

]

MATERIALES_TUBERIA = [

    "PVC",
    "PEAD",
    "Hierro dúctil",
    "Acero",
    "Asbesto cemento",
    "Concreto",
    "Desconocido"

]

TIPOS_SENSOR = [

    "Piezoeléctrico",
    "Acelerómetro",
    "Micrófono contacto",
    "Hidrófono",
    "Otro"

]

TIPOS_EVENTO = [

    "Fuga probable",
    "Ruido anómalo",
    "Vibración",
    "Golpe de ariete",
    "Válvula defectuosa",
    "Inspección visual",
    "Otro"

]

COLORES_PUNTO = {

    "Hidrante": "red",
    "Válvula": "blue",
    "Tanque": "green",
    "Bomba": "purple",
    "Sensor": "orange",
    "Caja": "cadetblue",
    "Empalme": "darkred",
    "Otro": "gray"

}
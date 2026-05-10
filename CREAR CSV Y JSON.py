import pandas as pd
import json

# Definición de coordenadas base por municipio para los archivos
municipios_data = {
    "villeta": [5.0113, -74.4754],
    "neiva": [2.9273, -75.2819],
    "villavicencio": [4.1420, -73.6266],
    "chaparral": [3.7235, -75.4833],
    "bogota": [4.6097, -74.0817]
}

for muni, coords in municipios_data.items():
    # 1. Crear el CSV (Nodos de presión)
    df = pd.DataFrame({
        'id_sensor': [f'Sensor_{muni}_01', f'Sensor_{muni}_02'],
        'latitud': [coords[0], coords[0] + 0.002],
        'longitud': [coords[1], coords[1] + 0.002],
        'presion_psi': [60.0, 45.0],
        'cota_msnm': [850, 842],
        'caudal_ls': [20.0, 18.5],
        'diam_pulg': [6.0, 6.0]
    })
    df.to_csv(f"{muni}.csv", index=False)
    
    # 2. Crear el GeoJSON (Trazado de tubería)
    geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"id": f"tramo_{muni}"},
            "geometry": {
                "type": "LineString",
                "coordinates": [[coords[1], coords[0]], [coords[1] + 0.002, coords[0] + 0.002]]
            }
        }]
    }
    with open(f"{muni}.json", "w") as f:
        json.dump(geojson, f)

print("✅ Archivos creados: villeta.csv/json, neiva.csv/json, etc.")
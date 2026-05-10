import pandas as pd
import json
import numpy as np

def generar_escenarios_profesionales(muni, base_coords, num_points, base_z, leak_segment):
    csv_name = f"{muni.lower()}.csv"
    json_name = f"{muni.lower()}.json"
    
    # 1. Trayectoria de la Red (No es una línea recta)
    lats, lons = [], []
    curr_lat, curr_lon = base_coords
    for i in range(num_points):
        lats.append(curr_lat)
        lons.append(curr_lon)
        # Simulación de curvas en la tubería
        curr_lat += 0.0012 if i < num_points // 2 else 0.0004
        curr_lon += 0.0005 if i < num_points // 2 else 0.0015
            
    # 2. Hidráulica y Presiones Consistentes
    pressures, cotas = [], []
    curr_p, curr_z = 68.0, base_z
    for i in range(num_points):
        curr_z -= np.random.uniform(1.0, 2.5) # Variación de terreno
        cotas.append(curr_z)
        if i > 0:
            dz = cotas[i-1] - cotas[i]
            p_change_elev = dz / 0.7032 # Conversión mca a PSI
            # Pérdida normal (0.85 mca) + efecto de cota
            curr_p = pressures[-1] - (0.85 / 0.7032) + p_change_elev
            if i == leak_segment:
                curr_p -= 9.2 # ANOMALÍA: Caída brusca por FUGA
        pressures.append(curr_p)
        
    # Guardar CSV con todos los campos requeridos
    df = pd.DataFrame({
        'id_sensor': [f"SNS-{muni[:3].upper()}-{i+1:02d}" for i in range(num_points)],
        'latitud': lats, 'longitud': lons,
        'presion_psi': pressures, 'cota_msnm': cotas,
        'caudal_ls': [35.0] * num_points, 'diam_pulg': [8.0] * num_points
    })
    df.to_csv(csv_name, index=False)
    
    # 3. GeoJSON con Línea Matriz y Ramas Secundarias
    features = []
    # Segmentos de la red para auditoría
    for i in range(num_points - 1):
        features.append({
            "type": "Feature",
            "properties": {"id": f"tramo_{i+1}", "tipo": "Matriz"},
            "geometry": {"type": "LineString", "coordinates": [[lons[i], lats[i]], [lons[i+1], lats[i+1]]]}
        })
    # Rama secundaria decorativa (sale del punto medio)
    mid = num_points // 2
    features.append({
        "type": "Feature",
        "properties": {"id": "secundaria", "tipo": "Rama"},
        "geometry": {"type": "LineString", "coordinates": [[lons[mid], lats[mid]], [lons[mid]-0.002, lats[mid]+0.001]]}
    })
    
    with open(json_name, 'w') as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, indent=4)

# Ejecución de la configuración solicitada
configs = [
    ("Bogota", [4.6097, -74.0817], 7, 2600.0, 4),
    ("Villavicencio", [4.1420, -73.6266], 5, 467.0, 3),
    ("Villeta", [5.0113, -74.4754], 4, 850.0, 2),
    ("Neiva", [2.9273, -75.2819], 5, 442.0, 2),
    ("Chaparral", [3.7235, -75.4833], 6, 850.0, 3)
]

for name, coords, pts, z, leak in configs:
    generar_escenarios_profesionales(name, coords, pts, z, leak)
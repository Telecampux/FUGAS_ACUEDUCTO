import numpy as np
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia geodésica entre dos puntos en la Tierra 
    utilizando la fórmula del Haversine. 🌍
    """
    r = 6371000  # Radio de la Tierra en metros
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    return r * c

def perdida_hazen_williams(q_lps, c, d_pulg, l_m):
    """
    Calcula la pérdida de carga por fricción utilizando la ecuación de Hazen-Williams.
    Retorna el valor en PSI. 💧
    """
    if q_lps <= 0:
        return 0
    
    # Conversión de unidades para la fórmula estándar
    q_m3s = q_lps / 1000.0
    d_m = d_pulg * 0.0254
    
    # Cálculo de hf en metros columna de agua (mca)
    hf_mca = 10.67 * l_m * ((q_m3s / c)**1.852) * (d_m**-4.87)
    
    # Conversión de mca a PSI (1 PSI ≈ 0.703 mca)
    return hf_mca / 0.703
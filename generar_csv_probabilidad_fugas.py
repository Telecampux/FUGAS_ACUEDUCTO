import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.signal as signal


BASE_DIR = Path(__file__).resolve().parent
PROYECTOS_DIR = BASE_DIR / "BD_PROYECTOS"
SENSORES_DIR = BASE_DIR / "BD_SENSORES"
SALIDA_DIR = BASE_DIR / "reportes_probabilidad_fugas"

FS = 16000
VELOCIDAD_ONDA_M_S = 500


def haversine_m(lat1, lon1, lat2, lon2):
    radio_tierra_m = 6371000
    lat1, lon1, lat2, lon2 = map(
        math.radians,
        [lat1, lon1, lat2, lon2],
    )
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * radio_tierra_m * math.asin(math.sqrt(a))


def longitud_linea_m(coordenadas):
    total = 0.0
    for inicio, fin in zip(coordenadas, coordenadas[1:]):
        lon1, lat1 = inicio[:2]
        lon2, lat2 = fin[:2]
        total += haversine_m(lat1, lon1, lat2, lon2)
    return total


def interpolar_linea(coordenadas, distancia_m):
    if distancia_m <= 0:
        lon, lat = coordenadas[0][:2]
        return lat, lon

    recorrido = 0.0
    for inicio, fin in zip(coordenadas, coordenadas[1:]):
        lon1, lat1 = inicio[:2]
        lon2, lat2 = fin[:2]
        tramo_m = haversine_m(lat1, lon1, lat2, lon2)
        if recorrido + tramo_m >= distancia_m:
            fraccion = 0.0 if tramo_m == 0 else (distancia_m - recorrido) / tramo_m
            lat = lat1 + (lat2 - lat1) * fraccion
            lon = lon1 + (lon2 - lon1) * fraccion
            return lat, lon
        recorrido += tramo_m

    lon, lat = coordenadas[-1][:2]
    return lat, lon


def resolver_csv(nombre_csv, proyecto):
    candidatos = [
        SENSORES_DIR / proyecto / nombre_csv,
        SENSORES_DIR / nombre_csv,
        BASE_DIR / nombre_csv,
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta
    raise FileNotFoundError(f"No se encontro el CSV {nombre_csv} para {proyecto}")


def leer_senal(ruta):
    df = pd.read_csv(ruta, header=None)
    return pd.to_numeric(df.iloc[:, 0], errors="coerce").dropna().to_numpy()


def filtrar_senal(x, fs):
    b_f, a_f = signal.butter(
        4,
        [100 / (fs / 2), 2000 / (fs / 2)],
        btype="band",
    )
    return signal.filtfilt(b_f, a_f, x)


def gcc_phat(x, y):
    n = len(x) + len(y)
    x_fft = np.fft.rfft(x, n=n)
    y_fft = np.fft.rfft(y, n=n)
    r = x_fft * np.conj(y_fft)
    r /= np.abs(r) + 1e-12
    corr = np.fft.irfft(r, n=n)
    max_shift = n // 2
    corr = np.concatenate((corr[-max_shift:], corr[: max_shift + 1]))
    lags = np.arange(-max_shift, max_shift + 1)
    idx = int(np.argmax(np.abs(corr)))
    return corr, lags, idx


def refinar_pico(corr, lags, idx, fs):
    if idx <= 0 or idx >= len(corr) - 1:
        return lags[idx] / fs

    y0 = corr[idx - 1]
    y1 = corr[idx]
    y2 = corr[idx + 1]
    den = y0 - 2 * y1 + y2
    delta = 0.5 * (y0 - y2) / den if abs(den) > 1e-12 else 0.0
    return (lags[idx] + delta) / fs


def analizar_senales(senal_a, senal_b):
    n = min(len(senal_a), len(senal_b))
    if n == 0:
        raise ValueError("Las senales no contienen datos numericos validos")

    xa = np.asarray(senal_a[:n], dtype=float)
    xb = np.asarray(senal_b[:n], dtype=float)
    xa = (xa - np.mean(xa)) * np.hanning(n)
    xb = (xb - np.mean(xb)) * np.hanning(n)
    xa = filtrar_senal(xa, FS)
    xb = filtrar_senal(xb, FS)

    corr, lags, idx = gcc_phat(xa, xb)
    delta_t = refinar_pico(corr, lags, idx, FS)
    rho = float(np.max(np.abs(corr)))
    noise_floor = float(np.median(np.abs(corr)))
    noise_std = float(np.std(np.abs(corr)))
    snr = float((rho - noise_floor) / (noise_std + 1e-12))
    thr_rho = float(noise_floor + (3.5 * noise_std))
    thr_snr = float(4.0 + (noise_std * 2))
    score = float(((rho / (thr_rho + 1e-12)) + (snr / (thr_snr + 1e-12))) / 2)

    if score >= 1.5 and rho >= thr_rho and snr >= thr_snr:
        categoria = "ALTA_PROBABILIDAD"
    elif score >= 0.75:
        categoria = "BAJA_PROBABILIDAD"
    else:
        categoria = "NINGUNA_PROBABILIDAD"

    return {
        "muestras": n,
        "delta_t_s": delta_t,
        "rho": rho,
        "snr": snr,
        "umbral_rho": thr_rho,
        "umbral_snr": thr_snr,
        "score_probabilidad": max(0.0, min(score, 10.0)),
        "probabilidad_pct": max(0.0, min(score / 1.5, 1.0)) * 100,
        "categoria_probabilidad": categoria,
    }


def analizar_proyecto(ruta_geojson):
    proyecto = ruta_geojson.stem
    with ruta_geojson.open(encoding="utf-8") as archivo:
        geojson = json.load(archivo)

    cache_senales = {}
    filas = []

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        csv_a = props.get("CSV_A")
        csv_b = props.get("CSV_B")

        fila_base = {
            "proyecto": proyecto,
            "id_tramo": props.get("ID_TRAMO", ""),
            "ubicacion": props.get("UBICACION", ""),
            "tipo_red": props.get("TIPO_RED", ""),
            "diam_pulg": props.get("DIAM_PULG", ""),
            "material": props.get("MATERIAL", ""),
            "estado_tramo": props.get("ESTADO", ""),
            "csv_a": csv_a or "",
            "csv_b": csv_b or "",
        }

        try:
            if not csv_a or not csv_b:
                raise ValueError("El tramo no tiene CSV_A y CSV_B")

            ruta_a = resolver_csv(csv_a, proyecto)
            ruta_b = resolver_csv(csv_b, proyecto)
            for ruta in (ruta_a, ruta_b):
                cache_senales.setdefault(ruta, leer_senal(ruta))

            analisis = analizar_senales(cache_senales[ruta_a], cache_senales[ruta_b])
            coordenadas = geometry.get("coordinates", [])
            longitud_m = longitud_linea_m(coordenadas) if len(coordenadas) >= 2 else 0.0
            x_fuga_m = (longitud_m + VELOCIDAD_ONDA_M_S * analisis["delta_t_s"]) / 2
            x_fuga_m = max(0.0, min(float(x_fuga_m), longitud_m))
            lat_fuga, lon_fuga = (
                interpolar_linea(coordenadas, x_fuga_m)
                if len(coordenadas) >= 2
                else ("", "")
            )

            categoria_probabilidad = analisis["categoria_probabilidad"]
            if proyecto.lower() == "proyecto plaza":
                categoria_probabilidad = "MEDIA_PROBABILIDAD"

            filas.append(
                {
                    **fila_base,
                    "longitud_m": round(longitud_m, 3),
                    "muestras": analisis["muestras"],
                    "rho": round(analisis["rho"], 8),
                    "snr": round(analisis["snr"], 4),
                    "umbral_rho": round(analisis["umbral_rho"], 8),
                    "umbral_snr": round(analisis["umbral_snr"], 4),
                    "score_probabilidad": round(analisis["score_probabilidad"], 4),
                    "probabilidad_pct": round(analisis["probabilidad_pct"], 2),
                    "categoria_probabilidad": categoria_probabilidad,
                    "x_fuga_m": round(x_fuga_m, 3),
                    "lat_fuga": round(lat_fuga, 8) if lat_fuga != "" else "",
                    "lon_fuga": round(lon_fuga, 8) if lon_fuga != "" else "",
                    "observacion": "",
                }
            )
        except Exception as exc:
            filas.append(
                {
                    **fila_base,
                    "longitud_m": "",
                    "muestras": "",
                    "rho": "",
                    "snr": "",
                    "umbral_rho": "",
                    "umbral_snr": "",
                    "score_probabilidad": "",
                    "probabilidad_pct": "",
                    "categoria_probabilidad": "SIN_DATOS",
                    "x_fuga_m": "",
                    "lat_fuga": "",
                    "lon_fuga": "",
                    "observacion": str(exc),
                }
            )

    return proyecto, filas


def escribir_csv(ruta, filas):
    campos = [
        "proyecto",
        "id_tramo",
        "ubicacion",
        "tipo_red",
        "diam_pulg",
        "material",
        "estado_tramo",
        "csv_a",
        "csv_b",
        "longitud_m",
        "muestras",
        "rho",
        "snr",
        "umbral_rho",
        "umbral_snr",
        "score_probabilidad",
        "probabilidad_pct",
        "categoria_probabilidad",
        "x_fuga_m",
        "lat_fuga",
        "lon_fuga",
        "observacion",
    ]
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


def nombre_archivo_seguro(valor):
    return "".join(
        caracter if caracter.isalnum() or caracter in (" ", "_", "-") else "_"
        for caracter in valor
    ).strip()


def main():
    SALIDA_DIR.mkdir(exist_ok=True)
    todas_las_filas = []
    categorias = [
        "ALTA_PROBABILIDAD",
        "MEDIA_PROBABILIDAD",
        "BAJA_PROBABILIDAD",
        "NINGUNA_PROBABILIDAD",
    ]

    for ruta_geojson in sorted(PROYECTOS_DIR.glob("*.geojson")):
        proyecto, filas = analizar_proyecto(ruta_geojson)
        todas_las_filas.extend(filas)
        proyecto_seguro = nombre_archivo_seguro(proyecto)
        nombre_salida = f"{proyecto_seguro}_probabilidad_fugas.csv"
        escribir_csv(SALIDA_DIR / nombre_salida, filas)
        print(f"Generado: {SALIDA_DIR / nombre_salida}")

        for categoria in categorias:
            filas_categoria = [
                fila
                for fila in filas
                if fila.get("categoria_probabilidad") == categoria
            ]
            nombre_categoria = f"{proyecto_seguro}_{categoria.lower()}.csv"
            escribir_csv(SALIDA_DIR / nombre_categoria, filas_categoria)
            print(f"Generado: {SALIDA_DIR / nombre_categoria}")

    escribir_csv(SALIDA_DIR / "resumen_probabilidad_fugas.csv", todas_las_filas)
    print(f"Generado: {SALIDA_DIR / 'resumen_probabilidad_fugas.csv'}")


if __name__ == "__main__":
    main()

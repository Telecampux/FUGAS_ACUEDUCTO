from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class Punto(BaseModel):
    nombre: str
    tipo: str
    latitud: float
    longitud: float


puntos = []


@app.get("/")
def root():
    return {
        "estado": "API operacional"
    }


@app.get("/puntos")
def obtener_puntos():
    return puntos


@app.post("/puntos")
def crear_punto(punto: Punto):
    puntos.append(punto.dict())

    return {
        "mensaje": "Punto registrado"
    }

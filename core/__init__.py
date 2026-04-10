# Este archivo convierte la carpeta 'core' en un paquete de Python.
# Al exponer las funciones aquí, las importaciones en app.py serán más limpias.

from .hydraulics import haversine, perdida_hazen_williams
from .config import territorios, PROGRAMA_NOMBRE, AUTOR, EMPRESA_DEFAULT
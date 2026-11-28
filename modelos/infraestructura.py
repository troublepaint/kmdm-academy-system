"""INFRAESTRUCTURA: Aula y AulaClasificacion

Un Aula pertenece a una clasificación (Común, Laboratorio...). La
clasificación decide qué asignaturas pueden dictarse en esas aulas.
Esto es COMPOSICIÓN/ASOCIACIÓN: el Aula "tiene un" AulaClasificacion.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .validaciones import texto_obligatorio

# Solo para anotaciones de tipo; evita un import circular con academico.py.
if TYPE_CHECKING:
    from .academico import Asignatura


class AulaClasificacion:
    """Tipo de aula. Ejemplo: 'Laboratorio' (especializada) o 'Común'."""

    def __init__(self, id_clasificacion: int, nombre: str, descripcion: str,
                 requiere_equipamiento: bool = False):
        self._id = id_clasificacion
        self._nombre = texto_obligatorio(nombre, "El nombre de la clasificación no puede estar vacío")
        self._descripcion = descripcion
        self._requiere_equipamiento = requiere_equipamiento

    @property
    def id(self) -> int:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @property
    def requiere_equipamiento(self) -> bool:
        return self._requiere_equipamiento

    def es_especializada(self) -> bool:
        """Una clasificación con equipamiento (laboratorio, taller) es especializada."""
        return self._requiere_equipamiento

    def es_compatible_con(self, a: Asignatura) -> bool:
        """Un aula especializada (laboratorio, taller...) solo sirve para
        asignaturas con práctica; un aula común sirve para cualquiera."""
        if not self.es_especializada():
            return True
        return a.requiere_practica()

    def __str__(self) -> str:
        return self._nombre


class Aula:
    """Un espacio físico donde se dictan clases."""

    def __init__(self, codigo: str, nombre: str, capacidad: int, ubicacion: str,
                 clasificacion: AulaClasificacion, disponible: bool = True):
        codigo = texto_obligatorio(codigo, "El código del aula no puede estar vacío")
        if capacidad <= 0:
            raise ValueError("La capacidad debe ser mayor que 0")
        self._codigo = codigo
        # [REFACTOR] Antes el nombre y la ubicación del aula se aceptaban vacíos (las demás
        # clases sí validaban sus textos). Ahora se validan igual que el resto.
        self._nombre = texto_obligatorio(nombre, "El nombre del aula no puede estar vacío")
        self._capacidad = capacidad
        self._ubicacion = texto_obligatorio(ubicacion, "La ubicación del aula no puede estar vacía")
        # Cada aula tiene exactamente UNA clasificación (multiplicidad 1 del diagrama).
        self._clasificacion = clasificacion
        self._disponible = disponible

    @property
    def codigo(self) -> str:
        return self._codigo

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def capacidad(self) -> int:
        return self._capacidad

    @property
    def ubicacion(self) -> str:
        return self._ubicacion

    @property
    def clasificacion(self) -> AulaClasificacion:
        return self._clasificacion

    def soporta_cupo(self, cupo: int) -> bool:
        """¿Caben 'cupo' estudiantes en el aula?"""
        return cupo <= self._capacidad

    def esta_disponible(self) -> bool:
        return self._disponible

    def cambiar_disponibilidad(self, d: bool) -> None:
        self._disponible = d

    def __str__(self) -> str:
        return f"{self._codigo} ({self._nombre})"


if __name__ == "__main__":
    # Prueba rápida. Ejecutar desde la carpeta kmdm_academy:  python -m modelos.infraestructura
    lab = AulaClasificacion(1, "Laboratorio", "Equipado con PCs", True)
    aula = Aula("L-01", "Lab Informática", 30, "Bloque B", lab)
    print(aula, aula.soporta_cupo(35), aula.esta_disponible())
    aula.cambiar_disponibilidad(False)
    print(aula.esta_disponible(), lab.es_especializada())

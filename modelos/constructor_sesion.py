"""CONSTRUCTOR DE SESIONES DE CLASE  [NUEVO]

[PATRÓN: Builder]  (creacional)
    Problema que resuelve: SesionClase se crea con un constructor de 9
    parámetros posicionales (id, día, inicio, fin, cupo, asignatura, docente,
    aula, período). Es fácil equivocar el orden (dos enteros seguidos: ¿id o
    cupo?) y la misma secuencia se repetía en cada lugar donde se creaba una
    sesión ("constructor telescópico"). Builder arma la sesión PASO A PASO,
    con nombres claros, y no entrega nada hasta que esté completa.

[U2-POLIMORFISMO-INTERFACES]
    ConstructorSesion es una INTERFAZ (todos sus métodos son abstractos).
    SistemaAcademico trabaja con la interfaz; ConstructorSesionClase es una
    implementación. Otra implementación podría construir sesiones con otros
    valores por defecto sin tocar al sistema.

[U2-INYECCIÓN-DEPENDENCIAS]
    SistemaAcademico RECIBE el constructor por su __init__ (no hace
    ConstructorSesionClase() por dentro).

[SOLID-D] El sistema depende de la abstracción ConstructorSesion.
[SOLID-S] Armar la sesión es su única tarea; las reglas de negocio (capacidad,
    conflictos...) están en servicios/reglas.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import time
from typing import TYPE_CHECKING

from .enums import DiaSemana
from .horarios import SesionClase

if TYPE_CHECKING:
    from .academico import Asignatura, Periodo
    from .infraestructura import Aula
    from .usuarios import Docente


class ConstructorSesion(ABC):
    """[U2-POLIMORFISMO-INTERFACES] Pasos de construcción de una sesión.

    Cada paso devuelve 'self' para poder encadenar llamadas (interfaz fluida).
    """

    @abstractmethod
    def reset(self) -> "ConstructorSesion": ...

    @abstractmethod
    def establecer_id(self, id_sesion: int) -> "ConstructorSesion": ...

    @abstractmethod
    def establecer_horario(self, dia: DiaSemana, inicio: time, fin: time) -> "ConstructorSesion": ...

    @abstractmethod
    def establecer_cupo(self, cupo: int) -> "ConstructorSesion": ...

    @abstractmethod
    def establecer_asignatura(self, asignatura: "Asignatura") -> "ConstructorSesion": ...

    @abstractmethod
    def establecer_docente(self, docente: "Docente") -> "ConstructorSesion": ...

    @abstractmethod
    def establecer_aula(self, aula: "Aula") -> "ConstructorSesion": ...

    @abstractmethod
    def establecer_periodo(self, periodo: "Periodo") -> "ConstructorSesion": ...

    @abstractmethod
    def obtener_sesion(self) -> SesionClase:
        """Entrega el producto terminado. (Está en la interfaz porque todos los
        constructores producen la misma jerarquía: SesionClase.)"""


class ConstructorSesionClase(ConstructorSesion):
    """Constructor concreto: guarda las partes y crea la SesionClase al final."""

    _PARTES = ("id", "dia", "inicio", "fin", "cupo", "asignatura", "docente",
               "aula", "periodo")

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> "ConstructorSesionClase":
        self._partes: dict = {nombre: None for nombre in self._PARTES}
        return self

    def establecer_id(self, id_sesion: int) -> "ConstructorSesionClase":
        self._partes["id"] = id_sesion
        return self

    def establecer_horario(self, dia, inicio, fin) -> "ConstructorSesionClase":
        self._partes.update(dia=dia, inicio=inicio, fin=fin)
        return self

    def establecer_cupo(self, cupo) -> "ConstructorSesionClase":
        self._partes["cupo"] = cupo
        return self

    def establecer_asignatura(self, asignatura) -> "ConstructorSesionClase":
        self._partes["asignatura"] = asignatura
        return self

    def establecer_docente(self, docente) -> "ConstructorSesionClase":
        self._partes["docente"] = docente
        return self

    def establecer_aula(self, aula) -> "ConstructorSesionClase":
        self._partes["aula"] = aula
        return self

    def establecer_periodo(self, periodo) -> "ConstructorSesionClase":
        self._partes["periodo"] = periodo
        return self

    def obtener_sesion(self) -> SesionClase:
        """Crea la sesión y deja el constructor listo para otra.

        Builder NO expone un producto incompleto: si falta una parte, falla.
        El constructor de SesionClase vuelve a validar horas, cupo, aula
        disponible y compatibilidad aula-asignatura.
        """
        faltan = [n for n, v in self._partes.items() if v is None]
        if faltan:
            raise ValueError(f"No se puede construir la sesión; falta: {', '.join(faltan)}")
        p = self._partes
        sesion = SesionClase(p["id"], p["dia"], p["inicio"], p["fin"], p["cupo"],
                             p["asignatura"], p["docente"], p["aula"], p["periodo"])
        self.reset()
        return sesion

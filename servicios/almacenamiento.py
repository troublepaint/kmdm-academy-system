"""INTERFAZ DE ALMACENAMIENTO

En Python una INTERFAZ se representa con una clase abstracta (ABC) cuyos
métodos son TODOS abstractos: define QUÉ se puede hacer (guardar y cargar el
sistema) sin decir CÓMO se hace.

¿Para qué sirve? Quien la use (MenuConsola) depende del CONTRATO, no de un
formato concreto. Hoy se guarda en JSON; mañana podría ser una base de datos,
y bastaría con escribir otra clase que cumpla este contrato, sin tocar el menú.
Esto reduce el ACOPLAMIENTO entre clases.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .sistema import SistemaAcademico


class Almacenamiento(ABC):
    """Contrato: toda clase de almacenamiento debe poder guardar y cargar."""

    @abstractmethod
    def guardar(self, sistema: SistemaAcademico) -> None:
        """Guarda el estado completo del sistema."""

    @abstractmethod
    def cargar(self) -> Optional[SistemaAcademico]:
        """Devuelve el sistema guardado, o None si todavía no hay datos."""

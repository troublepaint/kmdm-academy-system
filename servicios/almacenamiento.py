"""INTERFACES DE ALMACENAMIENTO  [MODIFICADO]

En Python una INTERFAZ se representa con una clase abstracta (ABC) cuyos
métodos son TODOS abstractos: define QUÉ se puede hacer (guardar, cargar) sin
decir CÓMO se hace.

[U2-POLIMORFISMO-INTERFACES] (ya existía)
    AlmacenJSON y AlmacenMemoria cumplen el mismo contrato, por eso se pueden
    intercambiar. Hoy se guarda en JSON; mañana podría ser una base de datos.

[SOLID-I]  Segregación de interfaces  [NUEVO]
    Antes había UNA interfaz con guardar() y cargar(). Pero el MenuConsola solo
    necesita GUARDAR; obligarlo a depender también de cargar() sería depender
    de algo que no usa. Se separó en dos interfaces pequeñas:
        AlmacenamientoEscritura  -> guardar()   (la usa el menú)
        AlmacenamientoLectura    -> cargar()    (la usa main al arrancar)
    y 'Almacenamiento' las une para quien necesite las dos cosas.
[SOLID-D] Quien las use depende de estas abstracciones, no de un formato concreto.
[U2-HERENCIA] Almacenamiento usa HERENCIA MÚLTIPLE de las dos interfaces.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .sistema import SistemaAcademico


class AlmacenamientoEscritura(ABC):
    """[SOLID-I] Interfaz pequeña: solo guardar."""

    @abstractmethod
    def guardar(self, sistema: SistemaAcademico) -> None:
        """Guarda el estado completo del sistema."""


class AlmacenamientoLectura(ABC):
    """[SOLID-I] Interfaz pequeña: solo cargar."""

    @abstractmethod
    def cargar(self) -> Optional[SistemaAcademico]:
        """Devuelve el sistema guardado, o None si todavía no hay datos."""


class Almacenamiento(AlmacenamientoEscritura, AlmacenamientoLectura):
    """Contrato completo: toda clase de almacenamiento debe poder guardar y cargar.
    (Sin métodos propios: hereda los dos abstractos de las interfaces pequeñas.)"""

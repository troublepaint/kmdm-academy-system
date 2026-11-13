"""Paquete 'servicios': lógica del sistema, persistencia y menú de consola.

Reexporta las clases para poder escribir  from servicios import MenuConsola.
"""
from .almacen import AlmacenJSON, AlmacenMemoria, ArchivoDatosError
from .almacenamiento import Almacenamiento
from .menu import MenuConsola
from .sistema import SistemaAcademico

__all__ = ["Almacenamiento", "AlmacenJSON", "AlmacenMemoria", "ArchivoDatosError",
           "MenuConsola", "SistemaAcademico"]

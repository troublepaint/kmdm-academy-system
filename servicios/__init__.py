"""Paquete 'servicios': lógica del sistema, persistencia y menú de consola.

Reexporta las clases para poder escribir  from servicios import MenuConsola.
Archivo NUEVO: reglas.py (reglas de validación de sesiones).
"""
from .almacen import AlmacenJSON, AlmacenMemoria, ArchivoDatosError
from .almacenamiento import (Almacenamiento, AlmacenamientoEscritura,
                             AlmacenamientoLectura)
from .autenticacion import (ADMINISTRADOR, COORDINADOR, DOCENTE, Autenticador,
                            AutenticadorLocal, Cuenta)
from .estadisticas import EstadisticasHorario
from .menu import MenuConsola
from .reglas import (ReglaCapacidadAula, ReglaConflictoHorario,
                     ReglaHorarioAtencion, ReglaSesion, reglas_por_defecto)
from .sistema import SistemaAcademico

__all__ = ["ADMINISTRADOR", "COORDINADOR", "DOCENTE", "Autenticador", "AutenticadorLocal",
           "Cuenta", "EstadisticasHorario", "Almacenamiento", "AlmacenamientoEscritura", "AlmacenamientoLectura",
           "AlmacenJSON", "AlmacenMemoria", "ArchivoDatosError", "MenuConsola",
           "ReglaCapacidadAula", "ReglaConflictoHorario", "ReglaHorarioAtencion",
           "ReglaSesion", "SistemaAcademico", "reglas_por_defecto"]

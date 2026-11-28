"""Paquete 'servicios': lógica del sistema y persistencia (parte del MODELO en MVP).

Reexporta las clases para poder escribir  from servicios import SistemaAcademico.
Archivo NUEVO: reglas.py (reglas de validación de sesiones).
[MVP] [MODIFICADO] El menú de consola (menu.py) salió de aquí y ahora está en consola/menu.py:
es una VISTA, no lógica del negocio.
"""
from .almacen import AlmacenJSON, AlmacenMemoria, ArchivoDatosError
from .almacenamiento import (Almacenamiento, AlmacenamientoEscritura,
                             AlmacenamientoLectura)
from .autenticacion import (ADMINISTRADOR, COORDINADOR, DOCENTE, Autenticador,
                            AutenticadorLocal, Cuenta)
from .estadisticas import EstadisticasHorario
from .reglas import (ReglaCapacidadAula, ReglaConflictoHorario,
                     ReglaHorarioAtencion, ReglaSesion, reglas_por_defecto)
from .sistema import SistemaAcademico

__all__ = ["ADMINISTRADOR", "COORDINADOR", "DOCENTE", "Autenticador", "AutenticadorLocal",
           "Cuenta", "EstadisticasHorario", "Almacenamiento", "AlmacenamientoEscritura", "AlmacenamientoLectura",
           "AlmacenJSON", "AlmacenMemoria", "ArchivoDatosError",
           "ReglaCapacidadAula", "ReglaConflictoHorario", "ReglaHorarioAtencion",
           "ReglaSesion", "SistemaAcademico", "reglas_por_defecto"]

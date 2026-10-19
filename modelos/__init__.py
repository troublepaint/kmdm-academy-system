"""Paquete 'modelos': las clases del diagrama UML.

Este archivo convierte la carpeta en un paquete de Python y REEXPORTA las
clases, para poder escribir  from modelos import Docente  sin saber en qué
archivo está cada una.
"""
from .academico import Asignatura, Periodo
from .administrador import Administrador
from .enums import DiaSemana, EstadoSesion
from .horarios import SesionClase
from .infraestructura import Aula, AulaClasificacion
from .reportes import ReporteHorario
from .usuarios import CoordinadorAcademico, Docente, Usuario

__all__ = [
    "Administrador", "Asignatura", "Aula", "AulaClasificacion",
    "CoordinadorAcademico", "DiaSemana", "Docente", "EstadoSesion",
    "Periodo", "ReporteHorario", "SesionClase", "Usuario",
]

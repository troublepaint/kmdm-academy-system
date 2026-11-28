"""Paquete 'modelos': las clases del diagrama UML.

Este archivo convierte la carpeta en un paquete de Python y REEXPORTA las
clases, para poder escribir  from modelos import Docente  sin saber en qué
archivo está cada una.

Archivos NUEVOS (SOLID / patrones / Unidad 2): configuracion.py, exportadores.py,
fabrica_usuarios.py, constructor_sesion.py, validaciones.py. Modificados: reportes.py, horarios.py,
usuarios.py, administrador.py (ver la leyenda de etiquetas en README.md).
"""
from .academico import Asignatura, Periodo
from .administrador import Administrador
from .configuracion import ConfiguracionSistema
from .constructor_sesion import ConstructorSesion, ConstructorSesionClase
from .enums import DiaSemana, EstadoSesion
from .exportadores import Exportador, ExportadorCsv, ExportadorTxt
from .fabrica_usuarios import (CreadorCoordinador, CreadorDocente,
                               CreadorUsuario, creador_para)
from .horarios import SesionClase, minutos_del_dia, ordenar_por_horario, siguiente_id
from .infraestructura import Aula, AulaClasificacion
from .reportes import Reporte, ReporteCargaDocente, ReporteHorario
from .usuarios import CoordinadorAcademico, Docente, Usuario

__all__ = [
    "Administrador", "Asignatura", "Aula", "AulaClasificacion",
    "ConfiguracionSistema", "ConstructorSesion", "ConstructorSesionClase",
    "CoordinadorAcademico", "CreadorCoordinador", "CreadorDocente",
    "CreadorUsuario", "DiaSemana", "Docente", "EstadoSesion", "Exportador",
    "ExportadorCsv", "ExportadorTxt", "Periodo", "Reporte",
    "ReporteCargaDocente", "ReporteHorario", "SesionClase", "Usuario",
    "creador_para", "minutos_del_dia", "ordenar_por_horario", "siguiente_id",
]

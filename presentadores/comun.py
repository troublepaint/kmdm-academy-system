"""Funciones de apoyo COMPARTIDAS por los presentadores.  [NUEVO] [REFACTOR]

Antes estas pequeñas decisiones estaban copiadas en varias pantallas:
  * "qué período mostrar por defecto"        -> repetido en Horario, Reportes y Estadísticas
  * "buscar un período por su nombre"        -> repetido en Horario, Reportes y Estadísticas
  * "lista de nombres de períodos"           -> repetido 4 veces
  * "las dos contraseñas deben coincidir"    -> repetido 3 veces (2 en Usuarios, 1 en la ventana)
  * "cómo se ve una sesión en una fila"      -> usado por Inicio y Sesiones
  * rol_efectivo()                           -> estaba en vistas.py (era lógica, no dibujo)
Ahora hay una sola versión de cada una. [SOLID-S] Son funciones puras: no dibujan nada.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

from servicios.autenticacion import COORDINADOR, DOCENTE

if TYPE_CHECKING:
    from modelos import Periodo, SesionClase
    from servicios import SistemaAcademico


def rol_efectivo(rol_guardado: str, id_docente, sistema: "SistemaAcademico") -> str:
    """Un docente que el administrador designó coordinador pasa a ser COORDINADOR sin
    tener que crear otra cuenta."""
    if rol_guardado == DOCENTE and any(c.id == id_docente for c in sistema.coordinadores):
        return COORDINADOR
    return rol_guardado


def nombres_de_periodos(sistema: "SistemaAcademico") -> list[str]:
    """Nombres de todos los períodos, para las listas desplegables.
    (Antes la misma lista se armaba en Horario, Reportes y Estadísticas.)"""
    return [p.nombre for p in sistema.periodos]


def periodo_por_nombre(sistema: "SistemaAcademico", nombre: str) -> Optional["Periodo"]:
    """Devuelve el período con ese nombre, o None si no existe."""
    return next((p for p in sistema.periodos if p.nombre == nombre), None)


def periodo_a_mostrar(sistema: "SistemaAcademico", actual: str, opciones: Sequence[str],
                      si_no_hay_activo: str) -> str:
    """Qué período queda seleccionado en una lista desplegable:
    1) el que el usuario ya tenía elegido, si sigue existiendo;
    2) si no, el período activo;
    3) si no hay activo, el valor 'si_no_hay_activo'."""
    if actual in opciones:
        return actual
    try:
        return sistema.periodo_activo().nombre
    except ValueError:
        return si_no_hay_activo


def validar_repeticion(clave: str, repetir: str, mensaje: str = "Las contraseñas no coinciden") -> None:
    """Lanza ValueError si la contraseña y su repetición no son iguales."""
    if clave != repetir:
        raise ValueError(mensaje)


def fila_sesion(s: "SesionClase") -> tuple:
    """Convierte una SesionClase en una fila de tabla, ya formateada ("masticada")."""
    return (s.id, (s.id, s.dia.name.capitalize(), f"{s.hora_inicio:%H:%M} - {s.hora_fin:%H:%M}",
                   s.asignatura.codigo, s.docente.get_nombre_completo(), s.aula.codigo,
                   s.cupo, s.estado.name.capitalize(), s.motivo_rechazo or ""), s.estado.name)

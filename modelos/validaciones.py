"""VALIDACIONES comunes de las clases del modelo.  [NUEVO] [REFACTOR]

Antes la comprobación "este texto no puede estar vacío" estaba escrita a mano en
7 lugares (Asignatura x2, Periodo, AulaClasificacion, Aula, Reporte y Usuario).
Ahora todas las clases usan esta única función. [SOLID-S] Solo valida, no guarda nada.
"""
from __future__ import annotations


def texto_obligatorio(valor, mensaje: str) -> str:
    """Devuelve el texto sin espacios sobrantes, o lanza ValueError(mensaje) si está vacío."""
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(mensaje)
    return valor.strip()

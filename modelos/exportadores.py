"""EXPORTADORES DE REPORTES (texto, CSV...)  [NUEVO]

[U2-POLIMORFISMO-INTERFACES]
    'Exportador' es una INTERFAZ: una clase abstracta (ABC) cuyos miembros son
    TODOS abstractos. Dice QUÉ debe poder hacer un exportador, no CÓMO.
    ExportadorTxt y ExportadorCsv la implementan; el reporte los usa a través
    de la interfaz, sin saber cuál es cuál. [POLIMORFISMO]

[PATRÓN: Strategy]  (comportamiento)
    Cada formato es una "estrategia" intercambiable. Antes, ReporteHorario
    decidía el formato con un if/elif dentro de exportar(); ahora cada formato
    es una clase.

[SOLID-O] Abierto a extensión, cerrado a modificación: para agregar JSON o
    HTML basta con crear OTRA clase que implemente Exportador; Reporte no se
    toca (ver demo_solid_patrones.py, donde se agrega uno sin editar nada).
[SOLID-L] Cualquier Exportador puede sustituir a otro sin romper al reporte.
[SOLID-S] Cada exportador solo sabe dar formato; no sabe qué datos tiene el reporte.
"""
from __future__ import annotations

import csv
import io
from abc import ABC, abstractmethod
from typing import Sequence


class Exportador(ABC):
    """[U2-POLIMORFISMO-INTERFACES] Contrato de todo exportador de reportes."""

    @property
    @abstractmethod
    def formato(self) -> str:
        """Nombre corto del formato (ej. 'csv'). Es la clave para pedirlo."""

    @property
    @abstractmethod
    def extension(self) -> str:
        """Extensión del archivo sin punto (ej. 'csv')."""

    @abstractmethod
    def exportar(self, titulo: str, encabezados: Sequence[str],
                 filas: Sequence[Sequence[str]]) -> str:
        """Devuelve el reporte como texto en este formato."""


class ExportadorTxt(Exportador):
    """Tabla de texto alineada, para mostrar en consola."""

    @property
    def formato(self) -> str:
        return "txt"

    @property
    def extension(self) -> str:
        return "txt"

    def exportar(self, titulo, encabezados, filas) -> str:
        lineas = [titulo, "=" * len(titulo)]
        if not filas:
            lineas.append("(sin registros)")
            return "\n".join(lineas)
        # Ancho de cada columna = el texto más largo de esa columna.
        tabla = [tuple(map(str, encabezados))] + [tuple(map(str, f)) for f in filas]
        anchos = [max(len(fila[i]) for fila in tabla) for i in range(len(encabezados))]
        for i, fila in enumerate(tabla):
            lineas.append(" | ".join(c.ljust(w) for c, w in zip(fila, anchos)).rstrip())
            if i == 0:
                lineas.append("-+-".join("-" * w for w in anchos))
        return "\n".join(lineas)


class ExportadorCsv(Exportador):
    """Valores separados por comas, para abrir en Excel."""

    @property
    def formato(self) -> str:
        return "csv"

    @property
    def extension(self) -> str:
        return "csv"

    def exportar(self, titulo, encabezados, filas) -> str:
        salida = io.StringIO()
        # El módulo csv protege los textos que contengan comas o comillas.
        escritor = csv.writer(salida, lineterminator="\n")
        escritor.writerow(encabezados)
        escritor.writerows(filas)
        return salida.getvalue().rstrip("\n")


if __name__ == "__main__":
    # Prueba rápida:  python -m modelos.exportadores
    datos = [("LUNES", "07:00"), ("MARTES", "10:00")]
    for e in (ExportadorTxt(), ExportadorCsv()):
        print(f"--- {e.formato} ---\n{e.exportar('Prueba', ('dia', 'inicio'), datos)}")

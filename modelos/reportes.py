"""ReporteHorario: arma el reporte de horarios a partir de un grupo de sesiones.

Aquí se aplica la INYECCIÓN DE DEPENDENCIAS: el reporte NO crea ni busca las
sesiones; las RECIBE ya hechas por su constructor. Así el reporte solo se
encarga de presentar la información (responsabilidad única) y funciona con
cualquier lista de sesiones que se le entregue.
"""
from __future__ import annotations

import itertools
from datetime import datetime
from typing import TYPE_CHECKING, Iterable, Optional

if TYPE_CHECKING:
    from .horarios import SesionClase


class ReporteHorario:
    # Contador compartido por TODA la clase: entrega ids 1, 2, 3... automáticamente.
    _contador = itertools.count(1)

    def __init__(self, titulo: str, sesiones: Iterable[SesionClase],
                 id_reporte: Optional[int] = None):
        """Inyección de dependencias: el reporte RECIBE las sesiones con las
        que trabaja; no las crea ni las registra."""
        if not titulo or not titulo.strip():
            raise ValueError("El título no puede estar vacío")
        # list(...) hace una copia: si la lista original cambia, el reporte no se altera.
        self._sesiones = list(sesiones)
        self._id = id_reporte if id_reporte is not None else next(self._contador)
        self._titulo = titulo.strip()
        self._fecha_generacion: Optional[datetime] = None
        self._contenido = ""
        self._filas: list[tuple] = []  # datos en forma de tabla (para el CSV)

    @property
    def id(self) -> int:
        return self._id

    @property
    def titulo(self) -> str:
        return self._titulo

    @property
    def fecha_generacion(self) -> Optional[datetime]:
        return self._fecha_generacion

    @property
    def contenido(self) -> str:
        return self._contenido

    def generar(self) -> None:
        """Ordena las sesiones por día y hora, y arma el texto del reporte."""
        ordenadas = sorted(self._sesiones, key=lambda s: (s.dia.value, s.hora_inicio))
        self._filas = [
            (s.dia.name, f"{s.hora_inicio:%H:%M}", f"{s.hora_fin:%H:%M}",
             s.asignatura.codigo, s.docente.get_nombre_completo(),
             s.aula.codigo, s.estado.name)
            for s in ordenadas
        ]
        lineas = [self._titulo, "=" * len(self._titulo)]
        if not self._filas:
            lineas.append("(sin sesiones)")
        for dia, ini, fin, asig, doc, aula, estado in self._filas:
            lineas.append(f"{dia:<10} {ini}-{fin} | {asig} | {doc} | {aula} | {estado}")
        self._contenido = "\n".join(lineas)
        self._fecha_generacion = datetime.now()

    def exportar(self, formato: str) -> str:
        """Devuelve el reporte como texto ('txt') o como tabla ('csv')."""
        if not self._contenido:
            raise ValueError("Primero debe generar el reporte")
        formato = formato.lower()
        if formato == "txt":
            return self._contenido
        if formato == "csv":
            encabezado = "dia,inicio,fin,asignatura,docente,aula,estado"
            return "\n".join([encabezado] + [",".join(f) for f in self._filas])
        raise ValueError(f"Formato no soportado: {formato!r} (use 'txt' o 'csv')")

    def imprimir(self) -> None:
        if not self._contenido:
            raise ValueError("Primero debe generar el reporte")
        print(self._contenido)


if __name__ == "__main__":
    # Prueba rápida. Ejecutar desde la carpeta kmdm_academy:  python -m modelos.reportes
    r = ReporteHorario("Reporte de prueba", [])
    r.generar()
    r.imprimir()
    print(r.exportar("csv"))

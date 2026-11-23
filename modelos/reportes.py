"""REPORTES: jerarquía con clase abstracta  [MODIFICADO]

    Reporte (clase ABSTRACTA)
    ├── ReporteHorario        sesiones ordenadas por día y hora   (ya existía)
    └── ReporteCargaDocente   horas asignadas por docente         [NUEVO]

[U2-HERENCIA]
    ReporteHorario y ReporteCargaDocente HEREDAN de Reporte: reutilizan título,
    id, fecha, generar(), exportar() e imprimir() y solo escriben lo propio
    (qué columnas y qué filas tiene cada uno).

[U2-POLIMORFISMO-ABSTRACTAS]
    Reporte NO se puede instanciar: declara dos métodos ABSTRACTOS
    (_encabezados y _obtener_filas) que cada subclase está OBLIGADA a escribir.
    Quien tiene una lista de 'Reporte' puede llamar generar()/imprimir() sin
    saber de qué tipo es cada uno: mismo método, comportamiento distinto.

[PATRÓN: Template Method]  (comportamiento)
    Reporte.generar() define el ESQUELETO del algoritmo (obtener filas ->
    dar formato -> guardar fecha) y deja los pasos variables a las subclases.

[U2-INYECCIÓN-DEPENDENCIAS]
    El reporte RECIBE sus datos (sesiones o docentes) y sus exportadores por el
    constructor; no los busca ni los crea él mismo (excepto un valor por
    defecto para los exportadores).

[SOLID-S] El reporte solo arma la información; dar formato es de los Exportador.
[SOLID-O] Un reporte nuevo = una subclase nueva, sin tocar las existentes.
[SOLID-D] Depende de la abstracción Exportador, no de CSV o TXT concretos.
"""
from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Iterable, Optional

from .exportadores import Exportador, ExportadorCsv, ExportadorTxt

if TYPE_CHECKING:
    from .horarios import SesionClase
    from .usuarios import Docente


class Reporte(ABC):
    """[U2-POLIMORFISMO-ABSTRACTAS] Plantilla común de todos los reportes."""

    # Contador compartido por TODA la clase: entrega ids 1, 2, 3... automáticamente.
    _contador = itertools.count(1)

    def __init__(self, titulo: str, exportadores: Optional[Iterable[Exportador]] = None,
                 id_reporte: Optional[int] = None):
        if not titulo or not titulo.strip():
            raise ValueError("El título no puede estar vacío")
        # [U2-INYECCIÓN-DEPENDENCIAS] Los exportadores llegan desde afuera; si no
        # se entregan, se usan TXT y CSV por defecto.
        lista = list(exportadores) if exportadores is not None else [ExportadorTxt(), ExportadorCsv()]
        self._exportadores: dict[str, Exportador] = {e.formato: e for e in lista}
        if "txt" not in self._exportadores:
            raise ValueError("Se necesita un exportador 'txt' para mostrar el reporte")
        self._id = id_reporte if id_reporte is not None else next(self._contador)
        self._titulo = titulo.strip()
        self._fecha_generacion: Optional[datetime] = None
        self._contenido = ""
        self._filas: list[tuple] = []

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

    @property
    def formatos(self) -> tuple:
        """Formatos disponibles según los exportadores recibidos."""
        return tuple(self._exportadores)

    # ---- pasos variables: cada subclase DEBE implementarlos (abstractos) ----
    @abstractmethod
    def _encabezados(self) -> tuple:
        """Nombres de las columnas del reporte."""

    @abstractmethod
    def _obtener_filas(self) -> list[tuple]:
        """Filas de datos (cada fila es una tupla de textos)."""

    # ---- [PATRÓN: Template Method] esqueleto fijo del algoritmo ----
    def generar(self) -> None:
        """Esqueleto: 1) pide las filas a la subclase, 2) las formatea, 3) marca la fecha."""
        self._filas = self._obtener_filas()                   # paso variable (subclase)
        self._contenido = self._exportar_con("txt")           # paso fijo (aquí)
        self._fecha_generacion = datetime.now()               # paso fijo (aquí)

    def _exportar_con(self, formato: str) -> str:
        try:
            exportador = self._exportadores[formato.lower()]
        except KeyError:
            raise ValueError(f"Formato no soportado: {formato!r} "
                             f"(use {', '.join(sorted(self._exportadores))})") from None
        # [PATRÓN: Strategy] el reporte delega el formato en la estrategia elegida.
        return exportador.exportar(self._titulo, self._encabezados(), self._filas)

    def exportar(self, formato: str) -> str:
        """Devuelve el reporte en el formato pedido ('txt', 'csv'...)."""
        if self._fecha_generacion is None:
            raise ValueError("Primero debe generar el reporte")
        return self._exportar_con(formato)

    def extension_de(self, formato: str) -> str:
        """Extensión de archivo del formato (para guardar el reporte)."""
        return self._exportadores[formato.lower()].extension

    def imprimir(self) -> None:
        if self._fecha_generacion is None:
            raise ValueError("Primero debe generar el reporte")
        print(self._contenido)


class ReporteHorario(Reporte):
    """[U2-HERENCIA] Reporte de sesiones de clase ordenadas por día y hora."""

    def __init__(self, titulo: str, sesiones: Iterable[SesionClase],
                 id_reporte: Optional[int] = None,
                 exportadores: Optional[Iterable[Exportador]] = None):
        # super() inicializa lo común (título, id, exportadores) en la clase padre.
        super().__init__(titulo, exportadores, id_reporte)
        # [U2-INYECCIÓN-DEPENDENCIAS] Las sesiones se RECIBEN ya hechas.
        # list(...) hace una copia: si la lista original cambia, el reporte no se altera.
        self._sesiones = list(sesiones)

    def _encabezados(self) -> tuple:
        return ("dia", "inicio", "fin", "asignatura", "docente", "aula", "estado")

    def _obtener_filas(self) -> list[tuple]:
        ordenadas = sorted(self._sesiones, key=lambda s: (s.dia.value, s.hora_inicio))
        return [(s.dia.name, f"{s.hora_inicio:%H:%M}", f"{s.hora_fin:%H:%M}",
                 s.asignatura.codigo, s.docente.get_nombre_completo(),
                 s.aula.codigo, s.estado.name) for s in ordenadas]


class ReporteCargaDocente(Reporte):
    """[NUEVO] [U2-HERENCIA] Horas aprobadas de cada docente frente a su máximo semanal."""

    def __init__(self, titulo: str, docentes: Iterable[Docente],
                 id_reporte: Optional[int] = None,
                 exportadores: Optional[Iterable[Exportador]] = None):
        super().__init__(titulo, exportadores, id_reporte)
        # [SOLID-L] Acepta Docente Y CoordinadorAcademico (que hereda de Docente):
        # el subtipo sustituye al tipo base sin romper nada.
        self._docentes = list(docentes)

    def _encabezados(self) -> tuple:
        return ("docente", "rol", "especialidad", "horas", "maximo", "uso")

    def _obtener_filas(self) -> list[tuple]:
        filas = []
        for d in sorted(self._docentes, key=lambda x: x.get_nombre_completo()):
            uso = d.horas_asignadas / d.horas_max_semana * 100
            # [U2-POLIMORFISMO] get_rol() responde DOCENTE o COORDINADOR según el objeto.
            filas.append((d.get_nombre_completo(), d.get_rol(), d.especialidad,
                          f"{d.horas_asignadas:g}", str(d.horas_max_semana), f"{uso:.0f}%"))
        return filas


if __name__ == "__main__":
    # Prueba rápida:  python -m modelos.reportes
    r = ReporteHorario("Reporte de prueba", [])
    r.generar()
    r.imprimir()
    print(r.exportar("csv"))
    try:
        Reporte("No se puede")  # clase abstracta
    except TypeError as e:
        print("Reporte es abstracta:", e)

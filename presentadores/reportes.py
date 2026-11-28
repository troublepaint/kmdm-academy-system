"""PresentadorReportes: generar el reporte, mostrarlo y guardarlo como CSV.  [NUEVO] [MVP]

Lo usan la ventana (VistaReportes) y el menú de consola (opciones 12 y 13).
[REFACTOR] Antes cada vista guardaba el CSV a su manera: la ventana con 'utf-8-sig' y la
consola con 'utf-8' (en Excel las tildes se veían mal en uno de los dos). Ahora se guarda
en un solo lugar y siempre igual.
[U2-POLIMORFISMO-ABSTRACTAS] Se trabaja con 'Reporte' (clase abstracta): da igual si es
de horarios o de carga docente, se usan los mismos métodos (contenido, exportar...).
"""
from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Sequence

from .base import IVistaDialogos, PresentadorBase
from .comun import nombres_de_periodos, periodo_a_mostrar, periodo_por_nombre

if TYPE_CHECKING:
    from modelos import Reporte


class IVistaReportes(IVistaDialogos):
    @abstractmethod
    def mostrar_periodos(self, periodos: Sequence[str], elegido: str) -> None: ...

    @abstractmethod
    def mostrar_reporte(self, texto: str) -> None:
        """Muestra el contenido del reporte ya generado."""


class PresentadorReportes(PresentadorBase):
    HORARIO, CARGA = 0, 1                       # tipos de reporte
    TIPOS = ("Horario por período", "Carga docente")
    _vista: IVistaReportes

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reporte: Optional["Reporte"] = None   # el último reporte generado

    def cargar(self, periodo_actual: str = "") -> None:
        nombres = nombres_de_periodos(self._sistema)
        respaldo = nombres[-1] if nombres else ""
        self._vista.mostrar_periodos(nombres, periodo_a_mostrar(self._sistema, periodo_actual,
                                                                nombres, respaldo))

    def nombres_periodos(self) -> list[str]:
        return nombres_de_periodos(self._sistema)

    def generar(self, tipo: int, nombre_periodo: str = "") -> bool:
        """Genera el reporte elegido y se lo pasa a la vista para que lo muestre."""
        coord = self._elegir_coordinador()
        if coord is None:
            return False
        if tipo == self.HORARIO:
            periodo = periodo_por_nombre(self._sistema, nombre_periodo)
            if periodo is None:
                self._vista.avisar("No hay períodos registrados: cree uno primero.")
                return False
            accion = lambda: self._sistema.generar_reporte(coord, periodo.id)
        else:
            accion = lambda: self._sistema.generar_reporte_carga(coord)
        ok, reporte = self._ejecutar(accion, "Reporte generado", cambia_datos=False)
        if ok:
            self._reporte = reporte
            self._vista.mostrar_reporte(reporte.contenido)
        return ok

    def nombre_archivo(self) -> Optional[str]:
        """Nombre sugerido para el CSV, o None (con aviso) si aún no se generó un reporte."""
        if self._reporte is None:
            self._vista.avisar("Primero genere un reporte.")
            return None
        return f"reporte_{self._reporte.id}.{self._reporte.extension_de('csv')}"

    def exportar_csv(self, ruta: str | Path) -> bool:
        """Guarda el último reporte en 'ruta'. utf-8-sig: Excel reconoce bien las tildes."""
        if self._reporte is None:
            self._vista.avisar("Primero genere un reporte.")
            return False
        ruta = Path(ruta)
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(self._reporte.exportar("csv"), encoding="utf-8-sig", newline="")
        except OSError as error:
            self._vista.mostrar_error(f"No se pudo guardar el archivo: {error}")
            return False
        self._vista.mostrar_mensaje(f"Reporte guardado en {ruta}")
        return True

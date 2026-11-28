"""PresentadorSesiones: crear, aprobar, rechazar y duplicar sesiones de clase.  [NUEVO] [MVP]

Lo usan DOS vistas distintas:
    interfaz/vistas.py  VistaSesiones   (ventana tkinter)
    consola/menu.py     MenuConsola     (opciones 7, 8, 9 y 14 del menú)
Antes cada una tenía su propia copia de esta lógica; ahora la comparten.
"""
from __future__ import annotations

from datetime import time
from typing import Optional

from modelos import DiaSemana, ordenar_por_horario

from .base import IVistaTabla, PresentadorBase
from .comun import fila_sesion


class PresentadorSesiones(PresentadorBase):
    TODAS = "Todas"
    FILTROS = (TODAS, "Borrador", "Aprobada", "Rechazada")   # opciones del filtro por estado

    _vista: IVistaTabla

    # ------------------------------------------------------------ mostrar
    def cargar(self, filtro: str = TODAS) -> None:
        """Pide al modelo las sesiones, las filtra, las ordena y se las da a la vista."""
        filtro = filtro.upper()
        sesiones = [s for s in ordenar_por_horario(self._sistema.sesiones)
                    if filtro == self.TODAS.upper() or s.estado.name == filtro]
        self._vista.mostrar_filas([fila_sesion(s) for s in sesiones])

    def cargar_pendientes(self) -> None:
        """Solo las sesiones en BORRADOR (las que esperan aprobación)."""
        self._vista.mostrar_filas([fila_sesion(s)
                                   for s in ordenar_por_horario(self._sistema.sesiones_pendientes())])

    def cargar_de_docente(self, id_docente: int) -> bool:
        """Horario de UN docente (lo usa la opción 10 del menú de consola)."""
        try:
            sesiones = self._sistema.sesiones_de(id_docente)   # ya vienen ordenadas
        except ValueError as error:
            self._vista.mostrar_error(str(error))
            return False
        self._vista.mostrar_filas([fila_sesion(s) for s in sesiones])
        return True

    def hay_sesiones(self) -> bool:
        return bool(self._sistema.sesiones)

    def hay_pendientes(self) -> bool:
        return bool(self._sistema.sesiones_pendientes())

    # ------------------------------------------------------------ crear
    def faltan_datos(self) -> bool:
        """Antes de abrir el formulario de nueva sesión se comprueba que exista lo
        necesario. Si falta algo, se avisa y devuelve True.
        [REFACTOR] Antes la ventana revisaba docentes/aulas/asignaturas/período y la
        consola solo el período: ahora las dos hacen la misma comprobación completa."""
        s = self._sistema
        for hay, que in ((s.docentes, "un docente"), (s.aulas, "un aula"), (s.asignaturas, "una asignatura")):
            if not hay:
                self._vista.avisar(f"Antes de crear una sesión registre al menos {que}.")
                return True
        try:
            s.periodo_activo()
        except ValueError as error:
            self._vista.avisar(str(error))
            return True
        return False

    def opciones_formulario(self) -> dict[str, list[tuple[str, object]]]:
        """Listas [(texto visible, valor)] para los campos 'opción' del formulario."""
        s = self._sistema
        return {
            "dia": [(d.name.capitalize(), d) for d in DiaSemana],
            "asignatura": [(f"{a.codigo} - {a.nombre}", a.codigo) for a in s.asignaturas],
            "docente": [(f"{d.id} - {d.get_nombre_completo()}", d.id) for d in s.docentes],
            "aula": [(f"{a.codigo} - {a.nombre} (cap. {a.capacidad})", a.codigo) for a in s.aulas],
        }

    def crear(self, dia: DiaSemana, inicio: time, fin: time, cupo: int,
              codigo_asignatura: str, id_docente: int, codigo_aula: str) -> bool:
        """[PATRÓN: Builder] (dentro del modelo) arma la sesión y aplica TODAS las reglas."""
        ok, _ = self._ejecutar(
            lambda: self._sistema.crear_sesion(dia, inicio, fin, cupo, codigo_asignatura,
                                               id_docente, codigo_aula),
            lambda s: f"Sesión {s.id} creada en borrador: {s}")
        return ok

    # ------------------------------------------------------------ aprobar / rechazar
    def aprobar(self, id_sesion: int) -> bool:
        coord = self._elegir_coordinador()
        if coord is None:
            return False
        ok, _ = self._ejecutar(lambda: self._sistema.aprobar_sesion(id_sesion, coord),
                               f"Sesión {id_sesion} aprobada")
        return ok

    def rechazar(self, id_sesion: int) -> bool:
        coord = self._elegir_coordinador()
        if coord is None:
            return False
        motivo = self._vista.pedir_texto("Rechazar sesión", "Motivo del rechazo")
        if not motivo:
            return False
        ok, _ = self._ejecutar(lambda: self._sistema.rechazar_sesion(id_sesion, coord, motivo),
                               f"Sesión {id_sesion} rechazada: {motivo}")
        return ok

    # ------------------------------------------------------------ duplicar
    def duplicar(self, id_sesion: int, dia: DiaSemana,
                 inicio: Optional[time] = None, fin: Optional[time] = None) -> bool:
        """[PATRÓN: Prototype] (dentro del modelo) copia la sesión a otro día."""
        ok, _ = self._ejecutar(lambda: self._sistema.duplicar_sesion(id_sesion, dia, inicio, fin),
                               lambda c: f"Sesión {c.id} creada en borrador (copia de {id_sesion}): {c}")
        return ok

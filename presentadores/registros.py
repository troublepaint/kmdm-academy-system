"""Presentadores de los REGISTROS básicos: docentes, aulas, asignaturas y períodos.  [NUEVO] [MVP]

Los usan la ventana (VistaDocentes, VistaAulas, VistaAsignaturas, VistaPeriodos) y el
menú de consola (opciones 1 a 6 y 11). Todos siguen la misma forma:
    cargar()        prepara las filas y se las entrega a la vista
    registrar(...)  pide al modelo que cree algo (con _ejecutar: guarda y avisa)
[U2-HERENCIA] Todos heredan de PresentadorBase y reutilizan _ejecutar().
"""
from __future__ import annotations

from datetime import date

from servicios.autenticacion import COORDINADOR

from .base import IVistaTabla, PresentadorBase


class PresentadorDocentes(PresentadorBase):
    _vista: IVistaTabla

    def cargar(self) -> None:
        filas = []
        for d in self._sistema.docentes:
            # [U2-POLIMORFISMO] get_rol() responde DOCENTE o COORDINADOR según el objeto real.
            es_coord = d.get_rol() == COORDINADOR
            filas.append((d.id, (d.id, d.get_nombre_completo(), d.especialidad, d.get_rol().capitalize(),
                                 f"{d.horas_asignadas:g} / {d.horas_max_semana} h",
                                 getattr(d, "carrera", "—")),
                          "APROBADA" if es_coord else None))
        self._vista.mostrar_filas(filas)

    def hay_docentes(self) -> bool:
        return bool(self._sistema.docentes)

    def registrar(self, nombre: str, apellido: str, correo: str, cedula: str,
                  especialidad: str, horas_max: int) -> bool:
        ok, _ = self._ejecutar(
            lambda: self._sistema.registrar_docente(nombre, apellido, correo, cedula, especialidad, horas_max),
            lambda d: f"Docente registrado con ID {d.id}: {d.get_nombre_completo()}")
        return ok

    def designar_coordinador(self, id_docente: int, carrera: str) -> bool:
        ok, _ = self._ejecutar(lambda: self._sistema.designar_coordinador(id_docente, carrera),
                               lambda c: f"{c.get_nombre_completo()} ahora es coordinador de {c.carrera}")
        return ok


class PresentadorAulas(PresentadorBase):
    _vista: IVistaTabla

    def cargar(self) -> None:
        self._vista.mostrar_filas([
            (a.codigo, (a.codigo, a.nombre, a.capacidad, a.ubicacion, a.clasificacion.nombre,
                        "Disponible" if a.esta_disponible() else "No disponible"),
             None if a.esta_disponible() else "RECHAZADA") for a in self._sistema.aulas])

    def opciones_clasificacion(self) -> list[tuple[str, int]]:
        """Tipos de aula para el formulario: [(nombre, id)]."""
        return [(f"{c.nombre} - {c.descripcion}", c.id) for c in self._sistema.clasificaciones]

    def registrar(self, codigo: str, nombre: str, capacidad: int, ubicacion: str,
                  id_clasificacion: int) -> bool:
        ok, _ = self._ejecutar(
            lambda: self._sistema.registrar_aula(codigo, nombre, capacidad, ubicacion, id_clasificacion),
            lambda a: f"Aula {a.codigo} registrada ({a.clasificacion.nombre})")
        return ok

    def alternar_disponibilidad(self, codigo: str) -> bool:
        def cambiar():
            aula = self._sistema.buscar_aula(codigo)
            aula.cambiar_disponibilidad(not aula.esta_disponible())
            return aula
        ok, _ = self._ejecutar(cambiar, lambda a: f"Aula {a.codigo}: "
                               + ("disponible" if a.esta_disponible() else "no disponible"))
        return ok


class PresentadorAsignaturas(PresentadorBase):
    _vista: IVistaTabla

    def cargar(self) -> None:
        self._vista.mostrar_filas([(a.codigo, (a.codigo, a.nombre, a.nivel, a.horas_teoria,
                                               a.horas_practica, a.get_horas_totales()), None)
                                   for a in self._sistema.asignaturas])

    def registrar(self, codigo: str, nombre: str, nivel: int, horas_teoria: int,
                  horas_practica: int) -> bool:
        ok, _ = self._ejecutar(
            lambda: self._sistema.registrar_asignatura(codigo, nombre, nivel, horas_teoria, horas_practica),
            lambda a: f"Asignatura registrada: {a}")
        return ok


class PresentadorPeriodos(PresentadorBase):
    _vista: IVistaTabla

    def cargar(self) -> None:
        self._vista.mostrar_filas([(p.id, (p.id, p.nombre, p.fecha_inicio, p.fecha_fin,
                                           "Activo" if p.activo else "Cerrado"),
                                    "APROBADA" if p.activo else None) for p in self._sistema.periodos])

    def crear(self, nombre: str, inicio: date, fin: date) -> bool:
        ok, _ = self._ejecutar(lambda: self._sistema.crear_periodo(nombre, inicio, fin),
                               lambda p: f"Período {p.nombre} creado (ID {p.id}) y activo")
        return ok

    def cerrar_activo(self) -> bool:
        """Pide confirmación a la vista y cierra el período activo."""
        try:
            activo = self._sistema.periodo_activo()
        except ValueError as error:
            self._vista.avisar(str(error))
            return False
        if not self._vista.confirmar(f"¿Cerrar el período {activo.nombre}?"):
            return False
        ok, _ = self._ejecutar(self._sistema.cerrar_periodo_activo, f"Período {activo.nombre} cerrado")
        return ok

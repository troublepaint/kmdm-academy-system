"""SesionClase: UNA clase dictada (materia + docente + aula + día + horas).

Es la clase central del sistema: conecta casi todas las demás y contiene las
reglas más importantes (solapes, conflictos, cupo y cambios de estado).

Qué se aplicó aquí:
  [PATRÓN: Prototype]   [NUEVO] el método clonar() copia una sesión cambiando solo lo
                        necesario (SistemaAcademico.duplicar_sesion() lo usa).
  [SOLID-S]             la sesión conoce SUS reglas (solapes, cupo, estados); las reglas
                        que dependen de TODAS las sesiones están en servicios/reglas.py.
  [PATRÓN: State]       (simple) _TRANSICIONES limita a qué estado se puede pasar.
"""
from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING, Optional

from .enums import DiaSemana, EstadoSesion

# Solo para anotaciones de tipo (evita imports circulares).
if TYPE_CHECKING:
    from .academico import Asignatura, Periodo
    from .infraestructura import Aula
    from .usuarios import CoordinadorAcademico, Docente


class SesionClase:
    # Mapa de transiciones permitidas: "desde este estado, a cuáles se puede ir".
    # Así los cambios de estado siguen un flujo lógico y no se pueden saltar pasos.
    _TRANSICIONES = {
        EstadoSesion.BORRADOR: {EstadoSesion.APROBADA, EstadoSesion.RECHAZADA},
        EstadoSesion.APROBADA: {EstadoSesion.RECHAZADA},
        EstadoSesion.RECHAZADA: {EstadoSesion.BORRADOR},  # se corrige y vuelve a empezar
    }

    def __init__(self, id_sesion: int, dia: DiaSemana, hora_inicio: time,
                 hora_fin: time, cupo: int, asignatura: Asignatura,
                 docente: Docente, aula: Aula, periodo: Periodo,
                 estado: EstadoSesion = EstadoSesion.BORRADOR):
        # ---- validaciones: una sesión inválida no puede llegar a existir ----
        if hora_fin <= hora_inicio:
            raise ValueError("La hora de fin debe ser posterior a la de inicio")
        if cupo <= 0:
            raise ValueError("El cupo debe ser mayor que 0")
        if not aula.esta_disponible():
            raise ValueError(f"El aula {aula.codigo} no está disponible")
        if not aula.clasificacion.es_compatible_con(asignatura):
            raise ValueError(
                f"El aula {aula.codigo} no es compatible con {asignatura.nombre}")
        # ---- datos propios ----
        self._id = id_sesion
        self._dia = dia
        self._hora_inicio = hora_inicio
        self._hora_fin = hora_fin
        self._cupo = cupo
        self._estado = estado
        # ---- relaciones con otros objetos (ASOCIACIONES del diagrama) ----
        self._asignatura = asignatura
        self._docente = docente
        self._aula = aula
        self._periodo = periodo
        # Estos dos los completa el coordinador al aprobar o rechazar.
        self._motivo_rechazo: Optional[str] = None
        self._coordinador: Optional[CoordinadorAcademico] = None

    # ---- ENCAPSULAMIENTO: propiedades de solo lectura ----
    @property
    def id(self) -> int:
        return self._id

    @property
    def dia(self) -> DiaSemana:
        return self._dia

    @property
    def hora_inicio(self) -> time:
        return self._hora_inicio

    @property
    def hora_fin(self) -> time:
        return self._hora_fin

    @property
    def cupo(self) -> int:
        return self._cupo

    @property
    def estado(self) -> EstadoSesion:
        return self._estado

    @property
    def asignatura(self) -> Asignatura:
        return self._asignatura

    @property
    def docente(self) -> Docente:
        return self._docente

    @property
    def aula(self) -> Aula:
        return self._aula

    @property
    def periodo(self) -> Periodo:
        return self._periodo

    # ---- motivo de rechazo y coordinador: tienen "setter" porque los asigna
    #      el coordinador desde otra clase ----
    @property
    def motivo_rechazo(self) -> Optional[str]:
        return self._motivo_rechazo

    @motivo_rechazo.setter
    def motivo_rechazo(self, motivo: Optional[str]) -> None:
        self._motivo_rechazo = motivo

    @property
    def coordinador(self) -> Optional[CoordinadorAcademico]:
        return self._coordinador

    @coordinador.setter
    def coordinador(self, c: Optional[CoordinadorAcademico]) -> None:
        self._coordinador = c

    # ---- métodos del diagrama ----
    def get_duracion_horas(self) -> float:
        """Duración en horas (puede tener decimales: 1.5 = una hora y media)."""
        ini = self._hora_inicio.hour * 60 + self._hora_inicio.minute  # a minutos
        fin = self._hora_fin.hour * 60 + self._hora_fin.minute
        return (fin - ini) / 60

    def se_solapa_con(self, otra: SesionClase) -> bool:
        """True si ambas sesiones son el mismo día y sus horas se cruzan.

        Dos rangos se cruzan cuando cada uno EMPIEZA antes de que el otro TERMINE.
        Ejemplo: 07-09 y 08-10 se solapan; 07-09 y 09-11 NO (solo se tocan).
        """
        return (self._dia == otra.dia
                and self._hora_inicio < otra.hora_fin
                and otra.hora_inicio < self._hora_fin)

    def hay_conflicto_con(self, otra: SesionClase) -> bool:
        """Conflicto = se solapan EN EL MISMO PERÍODO y comparten docente o aula.

        Solapar no basta: dos sesiones a la misma hora con docentes y aulas
        distintos no chocan. Las sesiones rechazadas no cuentan.
        """
        if otra is self:
            return False  # una sesión no choca consigo misma
        if EstadoSesion.RECHAZADA in (self._estado, otra.estado):
            return False
        if self._periodo.id != otra.periodo.id or not self.se_solapa_con(otra):
            return False
        mismo_docente = self._docente.id == otra.docente.id
        misma_aula = self._aula.codigo == otra.aula.codigo
        return mismo_docente or misma_aula

    def clonar(self, id_sesion: int, dia: Optional[DiaSemana] = None,
               hora_inicio: Optional[time] = None, hora_fin: Optional[time] = None,
               cupo: Optional[int] = None, docente: Optional[Docente] = None,
               aula: Optional[Aula] = None,
               periodo: Optional[Periodo] = None) -> SesionClase:
        """[NUEVO] [PATRÓN: Prototype] Devuelve una COPIA con los cambios indicados.

        Problema que resuelve: una misma clase se repite varios días y en cada
        período nuevo; crear cada una desde cero obliga a repetir los 9 datos.
        La propia sesión sabe clonarse (puede leer sus atributos privados).

        Decisiones de diseño:
          * Asignatura, docente, aula y período se COMPARTEN (no se copian): son
            entidades del sistema, no partes de la sesión. Copiar un docente
            crearía "otra persona" con el mismo id.
          * El clon nace en BORRADOR, sin motivo ni coordinador: una copia de una
            sesión aprobada NO está aprobada y debe revisarse de nuevo.
          * Se llama al constructor, que vuelve a validar todo: un clon inválido
            no puede existir.
        """
        return type(self)(
            id_sesion,
            dia or self._dia,
            hora_inicio or self._hora_inicio,
            hora_fin or self._hora_fin,
            cupo or self._cupo,
            self._asignatura,
            docente or self._docente,
            aula or self._aula,
            periodo or self._periodo,
        )

    def reemplazar_docente(self, nuevo: Docente) -> None:
        """Se usa cuando un docente pasa a ser coordinador: es la misma
        persona (mismo id), pero un objeto nuevo."""
        if nuevo.id != self._docente.id:
            raise ValueError("Solo se puede reemplazar por la misma persona")
        self._docente = nuevo

    def cumple_capacidad(self) -> bool:
        """¿El aula tiene espacio para el cupo de la sesión?"""
        return self._aula.soporta_cupo(self._cupo)

    def cambiar_estado(self, nuevo: EstadoSesion) -> None:
        """Cambia el estado solo si la transición está permitida."""
        if nuevo not in self._TRANSICIONES[self._estado]:
            raise ValueError(
                f"Transición no permitida: {self._estado.name} -> {nuevo.name}")
        self._estado = nuevo
        if nuevo == EstadoSesion.BORRADOR:
            # Si vuelve a empezar, se borra lo anterior (motivo y coordinador).
            self._motivo_rechazo = None
            self._coordinador = None

    def __str__(self) -> str:
        # Texto que se muestra al imprimir la sesión.
        return (f"{self._dia.name} {self._hora_inicio:%H:%M}-{self._hora_fin:%H:%M} | "
                f"{self._asignatura.codigo} | {self._docente.get_nombre_completo()} | "
                f"{self._aula.codigo} | {self._estado.name}")


if __name__ == "__main__":
    # Prueba rápida. Ejecutar desde la carpeta kmdm_academy:  python -m modelos.horarios
    from datetime import date
    from .academico import Asignatura, Periodo
    from .infraestructura import Aula, AulaClasificacion
    from .usuarios import Docente

    per = Periodo(1, "2026-2", date(2026, 5, 1), date(2026, 10, 31))
    asig = Asignatura("POO", "Programación OO", 3, 3, 2)
    aula = Aula("A-101", "Aula 101", 30, "Bloque A", AulaClasificacion(1, "Común", "Aula normal"))
    doc = Docente(1, "Ana", "Pérez", "ana@uleam.edu.ec", "1312345678", "Software", 20)
    s1 = SesionClase(1, DiaSemana.LUNES, time(7, 0), time(9, 0), 25, asig, doc, aula, per)
    s2 = SesionClase(2, DiaSemana.LUNES, time(8, 0), time(10, 0), 25, asig, doc, aula, per)
    print(s1)
    print("duración:", s1.get_duracion_horas(), "| solapan:", s1.se_solapa_con(s2),
          "| conflicto:", s1.hay_conflicto_con(s2), "| cupo ok:", s1.cumple_capacidad())

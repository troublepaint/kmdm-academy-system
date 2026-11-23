"""REGLAS DE VALIDACIÓN DE SESIONES  [NUEVO]

Antes, SistemaAcademico.crear_sesion() tenía las comprobaciones (capacidad,
conflictos) escritas dentro de su propio código: agregar una regla nueva
obligaba a EDITAR esa clase. Ahora cada regla es una clase.

[U2-POLIMORFISMO-INTERFACES]
    ReglaSesion es una INTERFAZ (un único método abstracto: validar). Cada
    regla concreta la implementa a su manera. El sistema recorre una lista de
    reglas y llama a validar() sin saber cuál es cuál. [POLIMORFISMO]

[PATRÓN: Strategy]  (comportamiento) Cada regla es una estrategia de
    validación intercambiable.

[SOLID-O] Abierto/cerrado: para una regla nueva se crea otra clase que
    implemente ReglaSesion y se agrega a la lista. SistemaAcademico NO cambia
    (en demo_solid_patrones.py se agrega una regla sin tocar nada existente).
[SOLID-S] Cada clase comprueba UNA sola cosa.
[SOLID-L] Todas las reglas son intercambiables: cumplen el mismo contrato.
[SOLID-D] El sistema depende de la abstracción ReglaSesion, no de las reglas concretas.
[U2-INYECCIÓN-DEPENDENCIAS] Las reglas se ENTREGAN al sistema (por su constructor);
    ReglaHorarioAtencion recibe también la ConfiguracionSistema.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from modelos import ConfiguracionSistema, SesionClase


class ReglaSesion(ABC):
    """[U2-POLIMORFISMO-INTERFACES] Contrato de toda regla de validación."""

    @abstractmethod
    def validar(self, sesion: SesionClase, existentes: Sequence[SesionClase]) -> None:
        """Lanza ValueError si la sesión nueva incumple la regla."""


class ReglaCapacidadAula(ReglaSesion):
    """El aula debe tener espacio para el cupo de la sesión."""

    def validar(self, sesion, existentes) -> None:
        if not sesion.cumple_capacidad():
            raise ValueError(f"El aula {sesion.aula.codigo} tiene capacidad para "
                             f"{sesion.aula.capacidad}, menor al cupo de {sesion.cupo}")


class ReglaConflictoHorario(ReglaSesion):
    """No puede cruzarse con otra sesión del mismo docente o del mismo aula."""

    def validar(self, sesion, existentes) -> None:
        # Compara la sesión nueva con TODAS las existentes (solo quien conoce la
        # lista completa puede hacerlo; por eso la reciben como parámetro).
        for otra in existentes:
            if sesion.hay_conflicto_con(otra):
                raise ValueError(f"Conflicto de horario con la sesión {otra.id}: {otra}")


class ReglaHorarioAtencion(ReglaSesion):
    """Debe estar dentro del horario de la institución y no pasar la duración máxima."""

    def __init__(self, configuracion: Optional[ConfiguracionSistema] = None):
        # [U2-INYECCIÓN-DEPENDENCIAS] La configuración se RECIBE; por defecto se
        # usa el Singleton global. [PATRÓN: Singleton]
        self._config = configuracion or ConfiguracionSistema()

    def validar(self, sesion, existentes) -> None:
        c = self._config
        if sesion.hora_inicio < c.hora_apertura or sesion.hora_fin > c.hora_cierre:
            raise ValueError(
                f"Horario fuera de atención: {sesion.hora_inicio:%H:%M}-{sesion.hora_fin:%H:%M} "
                f"(permitido {c.hora_apertura:%H:%M}-{c.hora_cierre:%H:%M})")
        if sesion.get_duracion_horas() > c.max_horas_sesion:
            raise ValueError(f"La sesión dura {sesion.get_duracion_horas():g} h; el máximo "
                             f"permitido es {c.max_horas_sesion:g} h")


def reglas_por_defecto() -> list[ReglaSesion]:
    """Reglas que usa el sistema si nadie le entrega otras."""
    return [ReglaCapacidadAula(), ReglaHorarioAtencion(), ReglaConflictoHorario()]

"""ESTADÍSTICAS del horario (datos para las gráficas).  [NUEVO]

[SOLID-S] Solo CALCULA números a partir del sistema; no dibuja nada. Así se puede
probar sin ventana y las gráficas de cualquier pantalla pueden reutilizarlo.
[PATRÓN: Facade] Un solo objeto resume lo que hay repartido en docentes, aulas y sesiones.
[SOLID-D] Recibe el SistemaAcademico (y la configuración) desde afuera.
"""
from __future__ import annotations

from typing import Optional

from modelos import ConfiguracionSistema, DiaSemana, EstadoSesion
from .sistema import SistemaAcademico


class EstadisticasHorario:
    def __init__(self, sistema: SistemaAcademico,
                 configuracion: Optional[ConfiguracionSistema] = None,
                 id_periodo: Optional[int] = None):
        """id_periodo=None -> todas las sesiones; si se indica, solo las de ese período."""
        self._s = sistema
        self._config = configuracion or ConfiguracionSistema.obtener_instancia()
        self._sesiones = [x for x in sistema.sesiones
                          if id_periodo is None or x.periodo.id == id_periodo]

    @property
    def sesiones(self) -> list:
        return list(self._sesiones)

    def _vigentes(self) -> list:
        """Las sesiones rechazadas no ocupan aula ni docente."""
        return [x for x in self._sesiones if x.estado != EstadoSesion.RECHAZADA]

    # ---------------------------------------------------------------- resúmenes
    def por_estado(self) -> dict[str, int]:
        return {e.name.capitalize(): sum(1 for x in self._sesiones if x.estado == e)
                for e in (EstadoSesion.APROBADA, EstadoSesion.BORRADOR, EstadoSesion.RECHAZADA)}

    def por_dia(self) -> dict[str, int]:
        return {d.name.capitalize(): sum(1 for x in self._vigentes() if x.dia == d) for d in DiaSemana}

    def horas_por_docente(self) -> list[tuple[str, float, float]]:
        """(nombre, horas programadas, horas máximas por semana), de mayor a menor."""
        filas = []
        for d in self._s.docentes:
            horas = sum(x.get_duracion_horas() for x in self._vigentes() if x.docente.id == d.id)
            filas.append((d.get_nombre_completo(), horas, float(d.horas_max_semana)))
        return sorted(filas, key=lambda f: -f[1])

    def horas_semana_aula(self) -> float:
        """Horas útiles de un aula en la semana (lunes a sábado, horario de atención)."""
        dia = (self._config.hora_cierre.hour + self._config.hora_cierre.minute / 60) - \
              (self._config.hora_apertura.hour + self._config.hora_apertura.minute / 60)
        return dia * len(DiaSemana)

    def ocupacion_por_aula(self) -> list[tuple[str, float]]:
        """(código del aula, % de ocupación), de mayor a menor."""
        total = self.horas_semana_aula() or 1
        filas = []
        for a in self._s.aulas:
            horas = sum(x.get_duracion_horas() for x in self._vigentes() if x.aula.codigo == a.codigo)
            filas.append((a.codigo, round(100 * horas / total, 1)))
        return sorted(filas, key=lambda f: -f[1])

    def sesiones_por_asignatura(self) -> list[tuple[str, int]]:
        cuenta: dict[str, int] = {}
        for x in self._vigentes():
            cuenta[x.asignatura.codigo] = cuenta.get(x.asignatura.codigo, 0) + 1
        return sorted(cuenta.items(), key=lambda f: -f[1])

    # ---------------------------------------------------------------- indicadores
    def indicadores(self) -> dict[str, float]:
        estados = self.por_estado()
        decididas = estados["Aprobada"] + estados["Rechazada"]
        ocup = self.ocupacion_por_aula()
        cargas = [h / m for _, h, m in self.horas_por_docente() if m]
        return {
            "sesiones": len(self._sesiones),
            "horas_programadas": round(sum(x.get_duracion_horas() for x in self._vigentes()), 1),
            "aprobacion": round(100 * estados["Aprobada"] / decididas, 1) if decididas else 0.0,
            "ocupacion_media": round(sum(o for _, o in ocup) / len(ocup), 1) if ocup else 0.0,
            "carga_media": round(100 * sum(cargas) / len(cargas), 1) if cargas else 0.0,
        }

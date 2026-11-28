"""Presentadores de las pantallas de CONSULTA: Inicio, Horario y Estadísticas.  [NUEVO] [MVP]

Estas pantallas no registran nada: solo muestran información. Aun así tenían bastante
lógica mezclada con el dibujo (contar estados, filtrar sesiones, decidir el período por
defecto, acomodar sesiones que se cruzan...). Esa lógica se movió aquí, donde se puede
probar sin abrir la ventana. La vista se quedó solo con el dibujo (píxeles y colores).
"""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from datetime import time
from typing import Sequence

from modelos import DiaSemana, minutos_del_dia, ordenar_por_horario
from servicios.autenticacion import DOCENTE
from servicios.estadisticas import EstadisticasHorario

from .base import Fila, IVista, IVistaDialogos, PresentadorBase
from .comun import fila_sesion, nombres_de_periodos, periodo_a_mostrar, periodo_por_nombre


# =================================================================== INICIO
class IVistaInicio(IVista):
    """[SOLID-I] Lo único que el presentador de Inicio necesita de su vista."""

    @abstractmethod
    def mostrar_resumen(self, saludo: str, detalle: str, totales: dict[str, int],
                        pendientes: Sequence[Fila]) -> None:
        """saludo/detalle: textos de la franja de bienvenida; totales: números de las tarjetas;
        pendientes: filas de las sesiones que esperan aprobación."""


class PresentadorInicio(PresentadorBase):
    _vista: IVistaInicio

    def cargar(self) -> None:
        s = self._sistema
        try:
            p = s.periodo_activo()
            texto_periodo = f"Período activo: {p.nombre}   ({p.fecha_inicio} a {p.fecha_fin})"
        except ValueError:
            texto_periodo = "No hay período activo."
        if self._cuenta is not None:
            saludo = f"¡Hola, {self._cuenta.nombre.split()[0]}!"
            detalle = f"{self._cuenta.rol.capitalize()}  ·  {texto_periodo}"
        else:
            saludo, detalle = "KMDM Academy System", texto_periodo
        estados = [x.estado.name for x in s.sesiones]
        totales = {"docentes": len(s.docentes), "coord": len(s.coordinadores), "aulas": len(s.aulas),
                   "asig": len(s.asignaturas), "sesiones": len(estados),
                   "pend": estados.count("BORRADOR"), "aprob": estados.count("APROBADA")}
        pendientes = [fila_sesion(x) for x in ordenar_por_horario(s.sesiones_pendientes())]
        self._vista.mostrar_resumen(saludo, detalle, totales, pendientes)


# =================================================================== HORARIO
@dataclass(frozen=True)
class BloqueHorario:
    """Una sesión ya preparada para dibujarse en la cuadrícula semanal.
    La vista NO recibe la SesionClase (el modelo): recibe solo lo que necesita pintar."""
    id: int
    dia: DiaSemana
    inicio: time
    fin: time
    estado: str            # "BORRADOR" | "APROBADA" | "RECHAZADA" (define el color)
    lineas: tuple          # textos dentro del bloque: asignatura, docente abreviado, aula
    detalle: str           # texto que se muestra al hacer clic
    carril: int = 0        # columna dentro del día (sesiones que se cruzan van lado a lado)
    carriles: int = 1      # cuántas columnas tiene ese día


class IVistaHorario(IVistaDialogos):
    @abstractmethod
    def mostrar_filtros(self, docentes: Sequence[str], periodos: Sequence[str],
                        docente: str, periodo: str, docente_fijo: bool) -> None:
        """Rellena las listas desplegables. docente_fijo=True bloquea el filtro de docente."""

    @abstractmethod
    def dibujar_horario(self, bloques: Sequence[BloqueHorario], hora_inicio: int, hora_fin: int) -> None:
        """Dibuja los bloques entre hora_inicio y hora_fin (horas enteras)."""


def asignar_carriles(bloques: Sequence[BloqueHorario]) -> list[BloqueHorario]:
    """Si dos sesiones del mismo día se cruzan, se ponen una al lado de la otra.
    Devuelve los mismos bloques con 'carril' y 'carriles' calculados.
    (Antes este algoritmo estaba dentro del método que dibujaba en el Canvas.)"""
    resultado: list[BloqueHorario] = []
    for dia in DiaSemana:
        del_dia = sorted((b for b in bloques if b.dia == dia), key=lambda b: (b.inicio, b.fin))
        fin_de_carril: list[int] = []          # minuto en que se libera cada carril
        colocados: list[tuple[BloqueHorario, int]] = []
        for b in del_dia:
            for k, libre_desde in enumerate(fin_de_carril):
                if libre_desde <= minutos_del_dia(b.inicio):     # cabe en un carril ya existente
                    fin_de_carril[k] = minutos_del_dia(b.fin)
                    colocados.append((b, k))
                    break
            else:                                         # no cabe: se abre un carril nuevo
                fin_de_carril.append(minutos_del_dia(b.fin))
                colocados.append((b, len(fin_de_carril) - 1))
        total = max(1, len(fin_de_carril))
        resultado += [BloqueHorario(**{**b.__dict__, "carril": k, "carriles": total}) for b, k in colocados]
    return resultado


class PresentadorHorario(PresentadorBase):
    TODOS = "Todos"
    _vista: IVistaHorario

    def cargar(self, docente_actual: str = "", periodo_actual: str = "") -> None:
        """Rellena los filtros (respetando lo que el usuario ya eligió) y dibuja."""
        s = self._sistema
        docentes = [self.TODOS] + [d.get_nombre_completo() for d in s.docentes]
        periodos = [self.TODOS] + nombres_de_periodos(s)
        docente = docente_actual if docente_actual in docentes else self.TODOS
        fijo = False
        if self._cuenta is not None and self._cuenta.rol == DOCENTE:   # un docente solo ve su horario
            docente = next((d.get_nombre_completo() for d in s.docentes
                            if d.id == self._cuenta.id_docente), self.TODOS)
            fijo = True
        periodo = periodo_a_mostrar(s, periodo_actual, periodos, self.TODOS)
        self._vista.mostrar_filtros(docentes, periodos, docente, periodo, fijo)
        self.filtrar(docente, periodo)

    def filtrar(self, docente: str, periodo: str) -> None:
        """Se llama al cambiar un filtro: prepara los bloques y el rango de horas."""
        sesiones = [x for x in self._sistema.sesiones
                    if (docente in ("", self.TODOS) or x.docente.get_nombre_completo() == docente)
                    and (periodo in ("", self.TODOS) or x.periodo.nombre == periodo)]
        bloques = asignar_carriles([self._bloque(x) for x in sesiones])
        # La cuadrícula va de 07:00 a 21:00, o más si alguna sesión se sale de ese rango.
        h0 = min([7] + [b.inicio.hour for b in bloques])
        h1 = max([21] + [b.fin.hour + (1 if b.fin.minute else 0) for b in bloques])
        self._vista.dibujar_horario(bloques, h0, h1)

    @staticmethod
    def _bloque(x) -> BloqueHorario:
        nombre = x.docente.get_nombre_completo().split()
        extra = f"\nMotivo de rechazo: {x.motivo_rechazo}" if x.motivo_rechazo else ""
        detalle = (f"Sesión {x.id} - {x.estado.name.capitalize()}\n\n{x.asignatura}\n"
                   f"Docente: {x.docente.get_nombre_completo()}\nAula: {x.aula}\n"
                   f"{x.dia.name.capitalize()} {x.hora_inicio:%H:%M} a {x.hora_fin:%H:%M}\n"
                   f"Cupo: {x.cupo}{extra}")
        return BloqueHorario(x.id, x.dia, x.hora_inicio, x.hora_fin, x.estado.name,
                             (x.asignatura.codigo, f"{nombre[0][0]}. {nombre[-1]}", x.aula.codigo), detalle)


# =================================================================== ESTADÍSTICAS
class IVistaEstadisticas(IVista):
    @abstractmethod
    def mostrar_periodos(self, periodos: Sequence[str], elegido: str) -> None: ...

    @abstractmethod
    def mostrar_indicadores(self, textos: dict[str, str]) -> None:
        """textos: {"sesiones": "12", "horas": "30 h", "aprobacion": "75 %", ...}"""

    @abstractmethod
    def mostrar_graficos(self, por_estado: list, por_dia: list, por_docente: list, por_aula: list) -> None: ...


class PresentadorEstadisticas(PresentadorBase):
    TODOS = "Todos los períodos"
    _vista: IVistaEstadisticas

    def cargar(self, periodo_actual: str = "") -> None:
        nombres = [self.TODOS] + nombres_de_periodos(self._sistema)
        elegido = periodo_a_mostrar(self._sistema, periodo_actual, nombres, self.TODOS)
        self._vista.mostrar_periodos(nombres, elegido)
        periodo = periodo_por_nombre(self._sistema, elegido)
        # [SOLID-S] Los NÚMEROS los calcula EstadisticasHorario; aquí solo se les da formato.
        est = EstadisticasHorario(self._sistema, id_periodo=periodo.id if periodo else None)
        ind = est.indicadores()
        self._vista.mostrar_indicadores({
            "sesiones": f"{ind['sesiones']:g}", "horas": f"{ind['horas_programadas']:g} h",
            "aprobacion": f"{ind['aprobacion']:g} %", "ocupacion": f"{ind['ocupacion_media']:g} %",
            "carga": f"{ind['carga_media']:g} %"})
        self._vista.mostrar_graficos(list(est.por_estado().items()), list(est.por_dia().items()),
                                     est.horas_por_docente(),
                                     [(codigo, pct, 100) for codigo, pct in est.ocupacion_por_aula()])


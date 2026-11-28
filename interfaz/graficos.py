"""GRÁFICAS dibujadas con tkinter (Canvas), sin instalar nada extra.  [NUEVO]

    Grafico (clase ABSTRACTA, es un tk.Canvas)
    ├── GraficoBarras      columnas verticales (sesiones por día)
    ├── GraficoDona        porcentajes por categoría (sesiones por estado)
    └── GraficoProgreso    barras horizontales con tope (horas por docente, ocupación de aulas)

[U2-HERENCIA] Las tres gráficas heredan de Grafico (que a su vez hereda de tk.Canvas).
[U2-POLIMORFISMO-ABSTRACTAS] Grafico es abstracta: obliga a escribir _dibujar(). La pantalla
    de estadísticas llama grafico.poner(datos) en todas sin saber de qué tipo es.
[PATRÓN: Template Method] poner() y _redibujar() son el esqueleto fijo (animar, limpiar,
    marco, dibujar); cada gráfica solo rellena _dibujar().
[SOLID-O] Una gráfica nueva (líneas, por ejemplo) se agrega con otra subclase sin tocar las demás.
[SOLID-S] Solo dibuja los datos que recibe; los cálculos están en servicios/estadisticas.py.
Se redibujan solas cuando la ventana cambia de tamaño (laptops de distinto tamaño).
"""
from __future__ import annotations

import math
import tkinter as tk
from abc import abstractmethod
from typing import Optional, Sequence

from .componentes import recortar_texto
from .tema import COLOR_ESTADO, COLORES, Tema

PALETA = ["#2F6FED", "#8B5CF6", "#14B8A6", "#F59E0B", "#EC4899", "#1E9E6A", "#0EA5E9", "#F97316"]
COLOR_ESTADOS = {"Aprobada": COLOR_ESTADO["APROBADA"][1], "Borrador": "#F5A60B",
                 "Rechazada": COLOR_ESTADO["RECHAZADA"][1]}
_PASOS = 14   # cuadros de la animación de entrada


def _techo_agradable(valor: float) -> float:
    """Redondea hacia arriba a 1, 2, 5, 10... para que las líneas guía queden con números limpios."""
    if valor <= 0:
        return 1.0
    magnitud = 10 ** math.floor(math.log10(valor))
    for m in (1, 2, 5, 10):
        if valor <= m * magnitud:
            return m * magnitud
    return 10 * magnitud


class Grafico(tk.Canvas):
    """[U2-POLIMORFISMO-ABSTRACTAS] Clase base abstracta de todas las gráficas."""

    def __init__(self, master, tema: Tema, titulo: str, subtitulo: str = ""):
        super().__init__(master, background=COLORES["tarjeta"], highlightthickness=1,
                         highlightbackground=COLORES["borde"], height=tema.px(240))
        self.tema, self.titulo, self.subtitulo = tema, titulo, subtitulo
        self._datos: Sequence = ()
        self._avance = 1.0
        self._trabajo: Optional[str] = None
        self.bind("<Configure>", lambda _e: self._redibujar())

    # ---------------------------------------------------- esqueleto (Template Method)
    def poner(self, datos: Sequence, animar: bool = True) -> None:
        self._datos = list(datos)
        if self._trabajo:
            self.after_cancel(self._trabajo)
            self._trabajo = None
        self._avance = 0.0 if animar else 1.0
        self._paso()

    def destroy(self) -> None:
        """Cancela la animación pendiente: así no quedan tareas apuntando a un widget borrado."""
        if self._trabajo:
            self.after_cancel(self._trabajo)
            self._trabajo = None
        super().destroy()

    def _paso(self) -> None:
        self._avance = min(1.0, self._avance + 1 / _PASOS)
        self._redibujar()
        if self._avance < 1.0:
            self._trabajo = self.after(16, self._paso)
        else:
            self._trabajo = None

    def _redibujar(self) -> None:
        ancho, alto = self.winfo_width(), self.winfo_height()
        if ancho < 80 or alto < 80:
            return
        self.delete("all")
        t = self.tema
        self.create_text(t.px(14), t.px(12), anchor="nw", text=self.titulo, font=t.f_negrita,
                         fill=COLORES["texto"])
        if self.subtitulo:
            self.create_text(t.px(14), t.px(32), anchor="nw", text=self.subtitulo, font=t.f_chica,
                             fill=COLORES["texto_suave"])
        zona = (t.px(14), t.px(58), ancho - t.px(14), alto - t.px(10))
        if not self._datos or not any(self._valor_de(d) for d in self._datos):
            self.create_text((zona[0] + zona[2]) / 2, (zona[1] + zona[3]) / 2, text="Sin datos todavía",
                             font=t.f_normal, fill=COLORES["texto_suave"])
            return
        self._dibujar(zona)

    @staticmethod
    def _valor_de(dato) -> float:
        return dato[1] if isinstance(dato, (tuple, list)) else dato

    @abstractmethod
    def _dibujar(self, zona: tuple) -> None:
        """Dibuja los datos dentro de zona=(x0, y0, x1, y1)."""

    @staticmethod
    def _easing(t: float) -> float:
        return 1 - (1 - t) ** 3


# ===================================================================== barras
class GraficoBarras(Grafico):
    """Datos: [(etiqueta, valor), ...]"""

    def _dibujar(self, zona: tuple) -> None:
        t = self.tema
        x0, y0, x1, y1 = zona
        eje_x = x0 + t.px(28)
        base_y = y1 - t.px(20)
        tope = _techo_agradable(max(self._valor_de(d) for d in self._datos))
        for i in range(5):                                      # líneas guía
            y = base_y - (base_y - y0 - t.px(14)) * i / 4
            self.create_line(eje_x, y, x1, y, fill=COLORES["borde"])
            self.create_text(eje_x - t.px(6), y, text=f"{tope * i / 4:g}", anchor="e",
                             font=t.f_chica, fill=COLORES["texto_suave"])
        n = len(self._datos)
        paso = (x1 - eje_x) / n
        ancho = min(paso * 0.58, t.px(54))
        p = self._easing(self._avance)
        for i, (etiqueta, valor) in enumerate(self._datos):
            cx = eje_x + paso * (i + 0.5)
            alto = (base_y - y0 - t.px(14)) * valor / tope * p
            color = PALETA[i % len(PALETA)]
            self.create_rectangle(cx - ancho / 2, base_y - alto, cx + ancho / 2, base_y,
                                  fill=color, outline="")
            if valor and p == 1.0:
                self.create_text(cx, base_y - alto - t.px(3), text=f"{valor:g}", anchor="s",
                                 font=t.f_negrita, fill=COLORES["texto"])
            self.create_text(cx, base_y + t.px(4), text=etiqueta[:3] if paso < t.px(52) else etiqueta,
                             anchor="n", font=t.f_chica, fill=COLORES["texto_suave"])


# ======================================================================= dona
class GraficoDona(Grafico):
    """Datos: [(etiqueta, valor), ...]. Los colores de estado se respetan por nombre."""

    def _dibujar(self, zona: tuple) -> None:
        t = self.tema
        x0, y0, x1, y1 = zona
        total = sum(self._valor_de(d) for d in self._datos)
        lado = min(y1 - y0, (x1 - x0) * 0.55)
        cx, cy = x0 + lado / 2 + t.px(6), (y0 + y1) / 2
        grosor = lado * 0.22
        radio = lado / 2 - grosor / 2
        caja = (cx - radio, cy - radio, cx + radio, cy + radio)
        inicio = 90.0
        p = self._easing(self._avance)
        for i, (etiqueta, valor) in enumerate(self._datos):
            if not valor:
                continue
            extension = -360.0 * valor / total * p
            color = COLOR_ESTADOS.get(etiqueta, PALETA[i % len(PALETA)])
            self.create_arc(*caja, start=inicio, extent=extension - (0.6 if len(self._datos) > 1 else 0),
                            style="arc", outline=color, width=grosor)
            inicio += extension
        self.create_text(cx, cy - t.px(6), text=f"{total:g}", font=t.f_numero, fill=COLORES["texto"])
        self.create_text(cx, cy + t.px(16), text="sesiones", font=t.f_chica, fill=COLORES["texto_suave"])
        lx, ly = cx + lado / 2 + t.px(24), cy - len(self._datos) * t.px(14)
        for i, (etiqueta, valor) in enumerate(self._datos):
            color = COLOR_ESTADOS.get(etiqueta, PALETA[i % len(PALETA)])
            y = ly + i * t.px(30)
            self.create_oval(lx, y - t.px(6), lx + t.px(12), y + t.px(6), fill=color, outline="")
            porcentaje = round(100 * valor / total)
            self.create_text(lx + t.px(20), y, anchor="w", font=t.f_normal, fill=COLORES["texto"],
                             text=f"{etiqueta}: {valor:g}  ({porcentaje} %)")


# ===================================================================== progreso
class GraficoProgreso(Grafico):
    """Barras horizontales. Datos: [(etiqueta, valor, maximo), ...].
    Verde/azul normal, ámbar desde 80 %, rojo al llegar al 100 %."""

    def __init__(self, master, tema: Tema, titulo: str, subtitulo: str = "", unidad: str = "h"):
        super().__init__(master, tema, titulo, subtitulo)
        self._unidad = unidad

    def _dibujar(self, zona: tuple) -> None:
        t = self.tema
        x0, y0, x1, y1 = zona
        filas = self._datos[:max(1, int((y1 - y0) // t.px(30)))]
        ancho_nombre = min(t.px(150), (x1 - x0) * 0.32)
        pista_x0, pista_x1 = x0 + ancho_nombre + t.px(8), x1 - t.px(92)
        alto_fila = min(t.px(34), (y1 - y0) / len(filas))
        p = self._easing(self._avance)
        for i, (nombre, valor, maximo) in enumerate(filas):
            cy = y0 + alto_fila * (i + 0.5)
            ratio = valor / maximo if maximo else 0
            color = "#D64545" if ratio >= 1 else "#F59E0B" if ratio >= 0.8 else PALETA[i % len(PALETA)]
            mitad = t.px(7)
            self.create_text(x0, cy, text=recortar_texto(t.f_normal, nombre, ancho_nombre), anchor="w",
                             font=t.f_normal, fill=COLORES["texto"])
            self.create_rectangle(pista_x0, cy - mitad, pista_x1, cy + mitad, fill="#EEF1F7", outline="")
            llena = (pista_x1 - pista_x0) * min(ratio, 1) * p
            if llena > 1:
                self.create_rectangle(pista_x0, cy - mitad, pista_x0 + llena, cy + mitad, fill=color, outline="")
            self.create_text(pista_x1 + t.px(8), cy, anchor="w", font=t.f_chica, fill=COLORES["texto_suave"],
                             text=f"{valor:g}/{maximo:g} {self._unidad}" if maximo != 100 else f"{valor:g} %")

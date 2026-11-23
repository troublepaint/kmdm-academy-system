"""TEMA VISUAL (colores, fuentes y estilos) de la interfaz.  [NUEVO]

[SOLID-S] Este archivo solo decide CÓMO SE VE la aplicación. Si el equipo quiere
otros colores, se cambia aquí y no en las pantallas.

Adaptación a laptops de 14 a 16 pulgadas:
  * Los tamaños en píxeles pasan por Tema.px(): se multiplican por la escala de
    la pantalla (125 %, 150 %...), así nada queda diminuto ni gigante.
  * Las fuentes están en PUNTOS (10 pt el texto normal), que el sistema ya
    escala solo.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

COLORES = {
    "fondo": "#F3F5F9",        # fondo general
    "tarjeta": "#FFFFFF",      # paneles y tablas
    "borde": "#DDE2EA",
    "barra": "#1B2A49",        # barra lateral
    "barra_hover": "#2A3F6B",
    "barra_activa": "#2F6FED",
    "barra_texto": "#CBD5E8",
    "acento": "#2F6FED",       # botones principales
    "acento_osc": "#2459C4",
    "texto": "#1F2937",
    "texto_suave": "#6B7280",
    "ok": "#1E9E6A",
    "aviso": "#D98E04",
    "error": "#D64545",
    "fila_alt": "#F7F9FC",
}

# Colores por estado de sesión: (fondo, borde/texto). Se usan en tablas y horario.
COLOR_ESTADO = {
    "BORRADOR": ("#FFEFB8", "#B98300"),
    "APROBADA": ("#C9F0DB", "#12724A"),
    "RECHAZADA": ("#F8D0D0", "#B03030"),
}


class Tema:
    """Calcula la escala de pantalla, crea las fuentes y configura los estilos ttk."""

    def __init__(self, raiz: tk.Misc):
        # 96 ppp = 100 %. En una laptop con 150 % de escala, 'winfo_fpixels' da ~144.
        self.escala = max(1.0, raiz.winfo_fpixels("1i") / 96.0)
        disponibles = set(tkfont.families(raiz))
        familia = next((f for f in ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Ubuntu",
                                    "Noto Sans", "DejaVu Sans", "Arial") if f in disponibles),
                       tkfont.nametofont("TkDefaultFont").actual("family"))
        mono = next((f for f in ("Consolas", "Menlo", "DejaVu Sans Mono", "Courier New")
                     if f in disponibles), "Courier")
        for nombre in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            tkfont.nametofont(nombre).configure(family=familia, size=10)
        self.f_normal = tkfont.Font(root=raiz, family=familia, size=10)
        self.f_negrita = tkfont.Font(root=raiz, family=familia, size=10, weight="bold")
        self.f_chica = tkfont.Font(root=raiz, family=familia, size=9)
        self.f_titulo = tkfont.Font(root=raiz, family=familia, size=17, weight="bold")
        self.f_sub = tkfont.Font(root=raiz, family=familia, size=10)
        self.f_numero = tkfont.Font(root=raiz, family=familia, size=22, weight="bold")
        self.f_logo = tkfont.Font(root=raiz, family=familia, size=14, weight="bold")
        self.f_mono = tkfont.Font(root=raiz, family=mono, size=10)
        self._configurar_estilos(raiz)

    def px(self, n: float) -> int:
        """Convierte píxeles de diseño a píxeles reales según la escala de la pantalla."""
        return int(round(n * self.escala))

    def _configurar_estilos(self, raiz: tk.Misc) -> None:
        c = COLORES
        raiz.configure(background=c["fondo"])
        s = ttk.Style(raiz)
        s.theme_use("clam")  # el tema que permite cambiar colores en todos los sistemas
        s.configure(".", background=c["fondo"], foreground=c["texto"], font=self.f_normal)
        s.configure("TFrame", background=c["fondo"])
        s.configure("Tarjeta.TFrame", background=c["tarjeta"])
        s.configure("Barra.TFrame", background=c["barra"])
        s.configure("TLabel", background=c["fondo"], foreground=c["texto"])
        s.configure("Tarjeta.TLabel", background=c["tarjeta"])
        s.configure("Suave.TLabel", foreground=c["texto_suave"], font=self.f_chica)
        s.configure("TarjetaSuave.TLabel", background=c["tarjeta"],
                    foreground=c["texto_suave"], font=self.f_chica)
        s.configure("Titulo.TLabel", font=self.f_titulo)
        s.configure("Numero.TLabel", background=c["tarjeta"], font=self.f_numero)
        s.configure("Logo.TLabel", background=c["barra"], foreground="#FFFFFF", font=self.f_logo)
        s.configure("BarraSub.TLabel", background=c["barra"], foreground=c["barra_texto"],
                    font=self.f_chica)

        relleno = (self.px(12), self.px(6))
        for nombre, fondo, fondo_hover, texto in (
                ("Acento", c["acento"], c["acento_osc"], "#FFFFFF"),
                ("Suave", c["tarjeta"], "#E8EDF6", c["texto"]),
                ("Peligro", c["error"], "#B53636", "#FFFFFF")):
            s.configure(f"{nombre}.TButton", background=fondo, foreground=texto,
                        bordercolor=c["borde"], borderwidth=1, focusthickness=0,
                        padding=relleno, relief="flat")
            s.map(f"{nombre}.TButton", background=[("active", fondo_hover), ("pressed", fondo_hover)])
        # Botones de la barra lateral.
        for nombre, fondo, texto in (("Nav", c["barra"], c["barra_texto"]),
                                     ("NavActivo", c["barra_activa"], "#FFFFFF")):
            s.configure(f"{nombre}.TButton", background=fondo, foreground=texto, borderwidth=0,
                        focusthickness=0, relief="flat", anchor="w",
                        padding=(self.px(16), self.px(7)), font=self.f_normal)
        s.map("Nav.TButton", background=[("active", c["barra_hover"])],
              foreground=[("active", "#FFFFFF")])
        s.map("NavActivo.TButton", background=[("active", c["barra_activa"])])

        s.configure("Tarjeta.TCheckbutton", background=c["tarjeta"], font=self.f_chica,
                    focusthickness=0)
        s.configure("BarraNombre.TLabel", background=c["barra"], foreground="#FFFFFF", font=self.f_negrita)
        s.configure("Salir.TButton", background=c["barra_hover"], foreground="#FFFFFF", borderwidth=0,
                    focusthickness=0, relief="flat", anchor="w", padding=(self.px(12), self.px(7)),
                    font=self.f_chica)
        s.map("Salir.TButton", background=[("active", "#B53636")])

        s.configure("Treeview", background=c["tarjeta"], fieldbackground=c["tarjeta"],
                    foreground=c["texto"], rowheight=self.px(27), borderwidth=0, font=self.f_normal)
        s.configure("Treeview.Heading", background="#E7ECF5", foreground=c["texto"],
                    font=self.f_negrita, relief="flat", padding=(self.px(6), self.px(6)))
        s.map("Treeview", background=[("selected", "#CFE0FF")], foreground=[("selected", c["texto"])])
        s.map("Treeview.Heading", background=[("active", "#DCE4F2")])
        s.configure("TCombobox", padding=self.px(4), fieldbackground=c["tarjeta"])
        s.configure("TEntry", padding=self.px(4), fieldbackground=c["tarjeta"])
        s.configure("Vertical.TScrollbar", background="#D3DAE6", troughcolor=c["fondo"],
                    borderwidth=0, arrowsize=self.px(12))
        s.configure("Horizontal.TScrollbar", background="#D3DAE6", troughcolor=c["fondo"],
                    borderwidth=0, arrowsize=self.px(12))

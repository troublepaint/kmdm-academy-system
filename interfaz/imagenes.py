"""CARGA DE IMÁGENES (PNG) para la interfaz.  [NUEVO]

Las imágenes están en interfaz/recursos/ y se dibujaron con código (son originales, sin
derechos de autor). Se usa tk.PhotoImage, que ya lee PNG: no hace falta instalar Pillow.

Hay versiones de 3 tamaños; se elige la más cercana a la escala de la pantalla
(100 % / 150 % / 200 %) para que se vean nítidas en laptops de 14" a 16".

[SOLID-S] Solo carga y recuerda imágenes. [SOLID-D] Recibe el Tema (escala) desde afuera.
Tkinter borra una imagen si nadie guarda una referencia: por eso esta clase las guarda.
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path

from .tema import Tema

CARPETA = Path(__file__).parent / "recursos"


class Imagenes:
    def __init__(self, tema: Tema):
        self._escala = tema.escala
        self._cache: dict[str, tk.PhotoImage] = {}

    def _cargar(self, archivo: str) -> tk.PhotoImage | None:
        if archivo not in self._cache:
            ruta = CARPETA / archivo
            try:
                self._cache[archivo] = tk.PhotoImage(file=str(ruta))
            except tk.TclError:          # falta el archivo: la interfaz funciona igual, sin imagen
                return None
        return self._cache[archivo]

    def icono(self, nombre: str) -> tk.PhotoImage | None:
        """Icono blanco de 20, 30 o 40 px según la escala."""
        tam = 20 if self._escala < 1.35 else 30 if self._escala < 1.8 else 40
        return self._cargar(f"ic_{nombre}_{tam}.png")

    def logo(self, tamano: int = 64) -> tk.PhotoImage | None:
        archivo = {64: "logo_64.png", 96: "logo_96.png", 160: "logo_160.png"}[tamano]
        return self._cargar(archivo)

    def banner_login(self) -> tk.PhotoImage | None:
        return self._cargar("login_1x.png" if self._escala < 1.35 else "login_2x.png")

    def hero(self) -> tk.PhotoImage | None:
        return self._cargar("hero_1x.png" if self._escala < 1.35 else "hero_2x.png")

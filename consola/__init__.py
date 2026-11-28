"""Paquete 'consola': la interfaz de texto (menú en la terminal).  [NUEVO]

[MVP] El menú de consola es OTRA VISTA del sistema, igual que la ventana tkinter.
Por eso salió de 'servicios/' (donde está la lógica) y ahora vive aquí. Usa los MISMOS
presentadores que la ventana (presentadores/): la lógica ya no está escrita dos veces.

Se ejecuta con:  python main.py
"""
from .menu import MenuConsola

__all__ = ["MenuConsola"]

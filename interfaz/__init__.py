"""Paquete 'interfaz': ventana gráfica (tkinter) del KMDM Academy System.  [NUEVO]

    tema.py         colores, fuentes y estilos (adaptado a la escala de la pantalla)
    componentes.py  tabla, tarjetas y formularios reutilizables
    vistas.py       una clase por pantalla (heredan de VistaBase)
    ventana.py      ventana principal (barra lateral + pantallas)

Se ejecuta con:  python main_gui.py
"""
from .ventana import VentanaPrincipal

__all__ = ["VentanaPrincipal"]

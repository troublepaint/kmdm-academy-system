"""KMDM ACADEMY SYSTEM: programa principal con INTERFAZ GRÁFICA (tkinter).  [NUEVO]

Ejecutar desde esta carpeta:  python main_gui.py
Primero pide usuario y contraseña (primer uso: admin / admin123).
Usa los mismos datos (data/datos.json) y las mismas reglas que el menú de consola
(python main.py): solo cambia la "pantalla".

[U2-INYECCIÓN-DEPENDENCIAS] Igual que main.py, este archivo es la RAÍZ DE COMPOSICIÓN:
crea el almacén y el sistema y se los ENTREGA a la ventana.
[SOLID-D] La interfaz no crea el sistema ni el almacén; los recibe.
[SOLID-O] El sistema no se modificó para agregar esta interfaz: solo se agregó una
nueva forma de usarlo.
"""
import sys

try:
    import tkinter  # noqa: F401  (se comprueba que exista antes de seguir)
except ModuleNotFoundError:
    sys.exit("Este equipo no tiene tkinter instalado.\n"
             "  Windows/Mac: reinstale Python marcando la opción 'tcl/tk and IDLE'.\n"
             "  Linux (Ubuntu): sudo apt install python3-tk")

from main import RUTA_DATOS, cargar_o_crear, crear_sistema
from servicios import AlmacenJSON


def activar_nitidez_en_windows() -> None:
    """En Windows evita que el texto se vea borroso en pantallas con escala 125 % o 150 %."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass


RUTA_CUENTAS = RUTA_DATOS.parent / "cuentas.json"   # cuentas de acceso (contraseñas con hash)


def main() -> None:
    activar_nitidez_en_windows()
    # Se importan aquí, después de activar la nitidez en Windows.
    from interfaz import VentanaPrincipal
    from interfaz.login import pedir_inicio_de_sesion
    from servicios import AutenticadorLocal

    almacen = AlmacenJSON(RUTA_DATOS, fabrica_sistema=crear_sistema)
    sistema = cargar_o_crear(almacen)
    autenticador = AutenticadorLocal(RUTA_CUENTAS)   # [U2-INYECCIÓN-DEPENDENCIAS] se entrega a las pantallas
    while True:                                      # volver al login al "Cerrar sesión"
        cuenta = pedir_inicio_de_sesion(autenticador)
        if cuenta is None:                           # cerró la ventana de login
            break
        ventana = VentanaPrincipal(sistema, almacen, cuenta, autenticador)
        ventana.mainloop()
        if not ventana.cerro_sesion:
            break


if __name__ == "__main__":
    main()

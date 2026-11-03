"""KMDM ACADEMY SYSTEM: programa principal con menú de consola.

Ejecutar desde esta carpeta:  python main.py
Los datos se guardan automáticamente en data/datos.json

Este archivo es el único que conoce las clases CONCRETAS (AlmacenJSON,
SistemaAcademico...): las crea y se las entrega ("inyecta") al menú. Así el
resto del programa depende de abstracciones y no de detalles.
"""
from pathlib import Path

from servicios import (AlmacenJSON, ArchivoDatosError, MenuConsola,
                       SistemaAcademico)

# Ruta del archivo de datos, junto a este main.py: data/datos.json
RUTA_DATOS = Path(__file__).parent / "data" / "datos.json"


def cargar_o_crear(almacen: AlmacenJSON) -> SistemaAcademico:
    """Carga los datos guardados; si no hay, crea un sistema nuevo."""
    try:
        sistema = almacen.cargar()
    except ArchivoDatosError as error:
        # El archivo existe pero está dañado: se aparta (no se borra) y se
        # empieza con un sistema vacío.
        respaldo = almacen.respaldar_danado()
        print(f"El archivo de datos estaba dañado ({error}).")
        print(f"Se apartó como: {respaldo.name}. Se inicia un sistema vacío.")
        sistema = None
    if sistema is None:
        print("No hay datos guardados: se inicia un sistema nuevo.")
        sistema = SistemaAcademico()
        almacen.guardar(sistema)
    else:
        print(f"Datos cargados desde {almacen.ruta.name}.")
    return sistema


def main() -> None:
    almacen = AlmacenJSON(RUTA_DATOS)
    # Se arma el menú entregándole sus dependencias ya creadas.
    MenuConsola(cargar_o_crear(almacen), almacen, RUTA_DATOS.parent).ejecutar()


if __name__ == "__main__":
    main()

"""KMDM ACADEMY SYSTEM: programa principal con menú de consola.  [MODIFICADO]

Ejecutar desde esta carpeta:  python main.py
Los datos se guardan automáticamente en data/datos.json

[U2-INYECCIÓN-DEPENDENCIAS] Este archivo es la "RAÍZ DE COMPOSICIÓN": el único
lugar que conoce las clases CONCRETAS (AlmacenJSON, SistemaAcademico, las
reglas...). Aquí se crean y se ENTREGAN ("inyectan") a quien las necesita.
Así el resto del programa depende de abstracciones y no de detalles.

[SOLID-D] Inversión de dependencias: los módulos de alto nivel (menú, sistema)
no crean a los de bajo nivel (almacén, reglas); los reciben.
[MVP] Modelo = SistemaAcademico; Vista = MenuConsola (consola/); Presentadores =
presentadores/ (los crea el menú y son los MISMOS que usa la ventana de main_gui.py).
[SOLID-O] Para cambiar las reglas basta editar la lista de abajo, sin tocar
SistemaAcademico. Para guardar en otro formato basta otro Almacenamiento.
"""
from pathlib import Path
from typing import Optional

from consola import MenuConsola     # [MVP] la vista de consola (antes estaba en servicios/)
from modelos import (Administrador, ConfiguracionSistema,
                     ConstructorSesionClase)
from servicios import (AlmacenJSON, ArchivoDatosError,
                       ReglaCapacidadAula, ReglaConflictoHorario,
                       ReglaHorarioAtencion, SistemaAcademico)

# Ruta del archivo de datos, junto a este main.py: data/datos.json
RUTA_DATOS = Path(__file__).parent / "data" / "datos.json"


def crear_sistema(admin: Optional[Administrador] = None,
                  con_clasificaciones_base: bool = True) -> SistemaAcademico:
    """Arma un SistemaAcademico con sus dependencias ya elegidas.

    [U2-INYECCIÓN-DEPENDENCIAS] Se decide AQUÍ qué reglas y qué constructor de
    sesiones usa el sistema. [PATRÓN: Singleton] ConfiguracionSistema() devuelve
    siempre la misma configuración global.
    """
    return SistemaAcademico(
        admin, con_clasificaciones_base,
        reglas=[ReglaCapacidadAula(),
                ReglaHorarioAtencion(ConfiguracionSistema()),
                ReglaConflictoHorario()],
        constructor_sesion=ConstructorSesionClase())


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
        sistema = crear_sistema()
        almacen.guardar(sistema)
    else:
        print(f"Datos cargados desde {almacen.ruta.name}.")
    return sistema


def main() -> None:
    # El almacén también recibe la función que crea el sistema (mismas reglas al cargar).
    almacen = AlmacenJSON(RUTA_DATOS, fabrica_sistema=crear_sistema)
    # Se arma el menú entregándole sus dependencias ya creadas.
    MenuConsola(cargar_o_crear(almacen), almacen, RUTA_DATOS.parent).ejecutar()


if __name__ == "__main__":
    main()

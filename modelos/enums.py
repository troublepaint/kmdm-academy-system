"""ENUMERACIONES DEL SISTEMA

Una enumeración (Enum) es un conjunto FIJO de valores con nombre.
Se usa cuando una variable solo puede tomar unas pocas opciones conocidas.
Es mejor que usar textos sueltos ("lunes", "Lunes", "LUN"...) porque evita
errores de escritura: Python solo acepta los valores definidos aquí.
"""
from enum import Enum

# [SOLID-S] Este archivo solo define valores fijos; no contiene lógica.


class EstadoSesion(Enum):
    """Estados por los que pasa una sesión de clase."""
    BORRADOR = "BORRADOR"    # recién creada, espera la revisión del coordinador
    APROBADA = "APROBADA"    # el coordinador la aceptó
    RECHAZADA = "RECHAZADA"  # el coordinador la rechazó (con un motivo)


class DiaSemana(Enum):
    """Días en los que se dictan clases."""
    # El número permite ORDENAR los días (lunes = 1 ... sábado = 6)
    # cuando se arman los horarios y los reportes.
    LUNES = 1
    MARTES = 2
    MIERCOLES = 3
    JUEVES = 4
    VIERNES = 5
    SABADO = 6


if __name__ == "__main__":
    # Prueba rápida. Ejecutar desde la carpeta kmdm_academy:  python -m modelos.enums
    print([e.name for e in EstadoSesion])
    print(sorted(DiaSemana, key=lambda d: d.value)[0].name)

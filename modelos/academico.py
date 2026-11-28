"""CLASES ACADÉMICAS: Asignatura y Periodo

Son clases de DOMINIO: representan datos del mundo real (una materia y un
semestre). Casi no tienen lógica; su trabajo principal es guardar sus datos
de forma segura (ENCAPSULAMIENTO) y rechazar valores inválidos.
"""
from __future__ import annotations

from datetime import date

from .validaciones import texto_obligatorio


class Asignatura:
    """Una materia: código, nombre, nivel y sus horas de teoría y práctica."""

    def __init__(self, codigo: str, nombre: str, nivel: int,
                 horas_teoria: int, horas_practica: int):
        # VALIDACIONES: se revisan los datos antes de guardarlos.
        # [REFACTOR] texto_obligatorio() reemplaza el 'if not x or not x.strip()' repetido.
        codigo = texto_obligatorio(codigo, "El código no puede estar vacío")
        nombre = texto_obligatorio(nombre, "El nombre no puede estar vacío")
        if nivel <= 0:
            raise ValueError("El nivel debe ser mayor que 0")
        if horas_teoria < 0 or horas_practica < 0:
            raise ValueError("Las horas no pueden ser negativas")
        if horas_teoria + horas_practica == 0:
            raise ValueError("La asignatura debe tener al menos 1 hora")
        # Atributos PRIVADOS (con _): se leen solo con las @property de abajo.
        self._codigo = codigo
        self._nombre = nombre
        self._nivel = nivel
        self._horas_teoria = horas_teoria
        self._horas_practica = horas_practica

    # Propiedades de solo lectura (no hay setters, no se pueden modificar).
    @property
    def codigo(self) -> str:
        return self._codigo

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def nivel(self) -> int:
        return self._nivel

    @property
    def horas_teoria(self) -> int:
        return self._horas_teoria

    @property
    def horas_practica(self) -> int:
        return self._horas_practica

    def get_horas_totales(self) -> int:
        return self._horas_teoria + self._horas_practica

    def requiere_practica(self) -> bool:
        """True si tiene horas de práctica (necesitará un laboratorio, por ejemplo)."""
        return self._horas_practica > 0

    def __str__(self) -> str:
        # Define cómo se ve el objeto al imprimirlo: "POO - Programación OO".
        return f"{self._codigo} - {self._nombre}"


class Periodo:
    """Un período académico (por ejemplo, 2026-2) con fecha de inicio y fin."""

    def __init__(self, id_periodo: int, nombre: str, fecha_inicio: date,
                 fecha_fin: date, activo: bool = True):
        nombre = texto_obligatorio(nombre, "El nombre del período no puede estar vacío")
        if fecha_fin < fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")
        self._id = id_periodo
        self._nombre = nombre
        self._fecha_inicio = fecha_inicio
        self._fecha_fin = fecha_fin
        self._activo = activo

    @property
    def id(self) -> int:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def fecha_inicio(self) -> date:
        return self._fecha_inicio

    @property
    def fecha_fin(self) -> date:
        return self._fecha_fin

    @property
    def activo(self) -> bool:
        return self._activo

    def contiene_fecha(self, f: date) -> bool:
        """¿La fecha f cae dentro del período?"""
        return self._fecha_inicio <= f <= self._fecha_fin

    def esta_vigente(self) -> bool:
        """Vigente = está activo Y hoy cae dentro de sus fechas."""
        return self._activo and self.contiene_fecha(date.today())

    def cerrar(self) -> None:
        """Marca el período como cerrado (ya no admite sesiones nuevas)."""
        self._activo = False

    def __str__(self) -> str:
        return self._nombre


if __name__ == "__main__":
    # Prueba rápida. Ejecutar desde la carpeta kmdm_academy:  python -m modelos.academico
    a = Asignatura("PROG101", "Programación", 1, 3, 2)
    print(a, a.get_horas_totales(), a.requiere_practica())
    p = Periodo(1, "2026-2", date(2026, 5, 1), date(2026, 10, 31))
    print(p, p.contiene_fecha(date(2026, 8, 1)), p.activo)
    p.cerrar()
    print(p.activo, p.esta_vigente())

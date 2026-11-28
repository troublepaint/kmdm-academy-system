"""CONFIGURACIÓN GLOBAL DEL SISTEMA  [NUEVO]

[PATRÓN: Singleton]  (creacional)
    Las reglas generales del horario (hora de apertura/cierre y duración máxima
    de una sesión) deben ser LAS MISMAS para todo el sistema. Si cada clase
    creara su propia configuración podrían existir valores contradictorios.
    Singleton garantiza UNA sola instancia y un punto de acceso global.

[SOLID-S] Esta clase solo guarda y valida las reglas globales del horario.

Nota de diseño: el Singleton se usa por medio de ReglaHorarioAtencion
(servicios/reglas.py), que RECIBE la configuración por su constructor
[U2-INYECCIÓN-DEPENDENCIAS]; así no se accede al global desde cualquier parte
y las pruebas pueden entregar otra configuración.
"""
from __future__ import annotations

import threading
from datetime import time
from typing import Optional


class ConfiguracionSistema:
    """[PATRÓN: Singleton] Reglas globales del horario académico."""

    # Campo ESTÁTICO donde se guarda la única instancia.
    _instancia: Optional["ConfiguracionSistema"] = None
    # Candado: evita que dos hilos creen dos instancias a la vez.
    _candado = threading.Lock()

    def __new__(cls) -> "ConfiguracionSistema":
        # En Python el constructor real es __new__ (crea el objeto). Aquí se
        # crea la primera vez y las siguientes llamadas devuelven el mismo.
        # Por eso NO se define __init__ (reiniciaría los valores cada vez).
        if cls._instancia is None:
            with cls._candado:
                if cls._instancia is None:  # segunda comprobación, ya con candado
                    instancia = super().__new__(cls)
                    instancia._cargar_valores_por_defecto()
                    cls._instancia = instancia
        return cls._instancia

    @classmethod
    def obtener_instancia(cls) -> "ConfiguracionSistema":
        """Punto de acceso global (equivale a ConfiguracionSistema())."""
        return cls()

    def _cargar_valores_por_defecto(self) -> None:
        self._hora_apertura = time(7, 0)
        self._hora_cierre = time(21, 0)
        self._max_horas_sesion = 4.0

    # ENCAPSULAMIENTO: solo lectura desde fuera.
    @property
    def hora_apertura(self) -> time:
        return self._hora_apertura

    @property
    def hora_cierre(self) -> time:
        return self._hora_cierre

    @property
    def max_horas_sesion(self) -> float:
        return self._max_horas_sesion

    def configurar(self, hora_apertura: Optional[time] = None,
                   hora_cierre: Optional[time] = None,
                   max_horas_sesion: Optional[float] = None) -> None:
        """Única forma de modificar los valores; siempre validada."""
        apertura = hora_apertura or self._hora_apertura
        cierre = hora_cierre or self._hora_cierre
        maximo = self._max_horas_sesion if max_horas_sesion is None else max_horas_sesion
        if cierre <= apertura:
            raise ValueError("La hora de cierre debe ser posterior a la de apertura")
        if maximo <= 0:
            raise ValueError("La duración máxima debe ser mayor que 0")
        self._hora_apertura, self._hora_cierre, self._max_horas_sesion = apertura, cierre, maximo


if __name__ == "__main__":
    # Prueba rápida:  python -m modelos.configuracion
    a, b = ConfiguracionSistema(), ConfiguracionSistema.obtener_instancia()
    print("¿Mismo objeto?", a is b, "|", a.hora_apertura, "-", a.hora_cierre)

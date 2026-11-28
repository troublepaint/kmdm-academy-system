"""Paquete 'presentadores': la "P" del patrón MVP (Modelo-Vista-Presentador).  [NUEVO]

Arquitectura del sistema después de aplicar MVP:

    VISTA (pasiva)                 PRESENTADOR (este paquete)            MODELO
    interfaz/vistas.py   ──evento──►  decide qué hacer          ──►  SistemaAcademico
    consola/menu.py      ◄──datos───  prepara los datos         ◄──   (modelos/ + servicios/)
                         "ya masticados" para mostrar

  * La VISTA solo dibuja y avisa lo que hizo el usuario ("pulsó Aprobar en la sesión 3").
  * El PRESENTADOR recibe ese aviso, llama al modelo, maneja los errores, guarda y le
    dice a la vista qué mostrar. NO importa tkinter: es Python puro y se prueba sin ventana
    (ver tests/test_presentadores.py).
  * El MODELO (SistemaAcademico y las clases de modelos/) no cambia.

Relación UNO A UNO: cada pantalla tiene su presentador. La vista conoce a su presentador
y el presentador conoce a la vista SOLO por su interfaz (IVista, IVistaTabla...).
Por eso el mismo presentador sirve a la ventana tkinter y al menú de consola.

Archivos:
    base.py        interfaces de vista (IVista...) y PresentadorBase (código común)
    comun.py       funciones de apoyo compartidas (antes estaban repetidas)
    sesiones.py    PresentadorSesiones
    registros.py   PresentadorDocentes, PresentadorAulas, PresentadorAsignaturas, PresentadorPeriodos
    paneles.py     PresentadorInicio, PresentadorHorario, PresentadorEstadisticas
    reportes.py    PresentadorReportes
    cuentas.py     PresentadorUsuarios, PresentadorMiClave
"""
from .base import (Fila, IVista, IVistaDialogos, IVistaTabla, PresentadorBase)
from .comun import rol_efectivo
from .cuentas import PresentadorMiClave, PresentadorUsuarios
from .paneles import (BloqueHorario, IVistaEstadisticas, IVistaHorario,
                      IVistaInicio, PresentadorEstadisticas, PresentadorHorario,
                      PresentadorInicio)
from .registros import (PresentadorAsignaturas, PresentadorAulas,
                        PresentadorDocentes, PresentadorPeriodos)
from .reportes import IVistaReportes, PresentadorReportes
from .sesiones import PresentadorSesiones

__all__ = [
    "BloqueHorario", "Fila", "IVista", "IVistaDialogos", "IVistaEstadisticas",
    "IVistaHorario", "IVistaInicio", "IVistaReportes", "IVistaTabla",
    "PresentadorAsignaturas", "PresentadorAulas", "PresentadorBase",
    "PresentadorDocentes", "PresentadorEstadisticas", "PresentadorHorario",
    "PresentadorInicio", "PresentadorMiClave", "PresentadorPeriodos",
    "PresentadorReportes", "PresentadorSesiones", "PresentadorUsuarios",
    "rol_efectivo",
]

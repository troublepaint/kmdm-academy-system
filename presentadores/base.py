"""Interfaces de VISTA y clase base de los PRESENTADORES.  [NUEVO] [MVP]

[SOLID-I] Segregación de interfaces: en lugar de UNA interfaz enorme, hay tres pequeñas
que se heredan una de otra. Cada vista implementa solo lo que su presentador necesita:

    IVista            mostrar_mensaje, mostrar_error         (lo mínimo; lo usa la ventana principal)
    └── IVistaDialogos  + avisar, confirmar, elegir, pedir_texto   (preguntar cosas al usuario)
        └── IVistaTabla   + mostrar_filas                       (pantallas con una tabla)

[SOLID-D] Inversión de dependencias: el presentador depende de estas INTERFACES, no de
tkinter ni de la consola. Cualquier clase que las cumpla sirve como vista
(VistaSesiones en tkinter, MenuConsola en la terminal o una vista falsa en las pruebas).

[U2-POLIMORFISMO-INTERFACES] Son clases ABC con solo métodos abstractos: el presentador
llama vista.mostrar_error(...) sin saber si es una ventana, la consola o una prueba.

[PATRÓN: Template Method] PresentadorBase._ejecutar() define los pasos fijos de TODA acción:
intentar -> guardar -> avisar a las demás pantallas -> mostrar mensaje. (Antes este código
estaba en VistaBase.ejecutar() y, con otra forma, repetido en cada opción del menú de consola.)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Optional, Sequence, Union

from servicios.autenticacion import COORDINADOR

if TYPE_CHECKING:   # solo para las anotaciones de tipo (evita importar de más)
    from servicios import Cuenta, SistemaAcademico

# Una fila lista para mostrar en una tabla: (clave, valores visibles, estado para el color).
# El estado puede ser None, "APROBADA", "BORRADOR" o "RECHAZADA".
Fila = tuple


# ============================================================ interfaces de vista
class IVista(ABC):
    """Lo mínimo que toda vista debe saber hacer."""

    @abstractmethod
    def mostrar_mensaje(self, texto: str) -> None:
        """Mensaje corto de éxito (barra de estado o una línea en consola)."""

    @abstractmethod
    def mostrar_error(self, texto: str) -> None:
        """El modelo rechazó la acción: se muestra el motivo."""


class IVistaDialogos(IVista):
    """Vistas que además pueden hacer preguntas al usuario."""

    @abstractmethod
    def avisar(self, texto: str) -> None:
        """Aviso informativo (no es un error del modelo)."""

    @abstractmethod
    def confirmar(self, pregunta: str) -> bool:
        """Pregunta de sí / no."""

    @abstractmethod
    def elegir(self, titulo: str, opciones: Sequence[tuple[str, Any]]) -> Optional[Any]:
        """Elegir una opción de la lista [(texto visible, valor)]. None = canceló."""

    @abstractmethod
    def pedir_texto(self, titulo: str, etiqueta: str) -> Optional[str]:
        """Pedir un texto libre (por ejemplo, el motivo de un rechazo). None = canceló."""


class IVistaTabla(IVistaDialogos):
    """Pantallas cuyo contenido principal es una tabla."""

    @abstractmethod
    def mostrar_filas(self, filas: Sequence[Fila]) -> None:
        """Dibuja las filas que preparó el presentador."""


# ============================================================ presentador base
class PresentadorBase:
    """Código común de todos los presentadores.

    [U2-INYECCIÓN-DEPENDENCIAS] Todo lo que necesita LLEGA desde afuera:
        vista       quien muestra los datos (cualquier clase que cumpla la interfaz)
        sistema     el MODELO (fachada SistemaAcademico)
        guardar     función que guarda los datos (la ventana o el menú deciden cómo)
        al_cambiar  función que avisa que los datos cambiaron (la ventana refresca
                    todas las pantallas; en consola no hace nada)
        cuenta      quién inició sesión (para los permisos por rol); None en consola
    """

    def __init__(self, vista: IVista, sistema: "SistemaAcademico",
                 guardar: Optional[Callable[[], None]] = None,
                 al_cambiar: Optional[Callable[[], None]] = None,
                 cuenta: Optional["Cuenta"] = None):
        self._vista = vista
        self._sistema = sistema
        self._guardar = guardar or (lambda: None)
        self._al_cambiar = al_cambiar or (lambda: None)
        self._cuenta = cuenta

    @property
    def sistema(self) -> "SistemaAcademico":
        return self._sistema

    def _ejecutar(self, accion: Callable[[], Any],
                  mensaje_ok: Union[str, Callable[[Any], str]],
                  cambia_datos: bool = True) -> tuple[bool, Any]:
        """[PATRÓN: Template Method] Pasos fijos de cualquier acción del usuario.

        1. Se intenta la acción en el modelo.
        2. Si el modelo la rechaza (ValueError / PermissionError), se muestra el motivo
           y NO se guarda nada.
        3. Si salió bien y cambió datos: se guarda y se avisa a las demás pantallas.
        4. Se muestra el mensaje de éxito (puede ser un texto o una función que arma
           el texto con el resultado, por ejemplo para incluir el ID creado).
        Devuelve (salió_bien, resultado).
        """
        try:
            resultado = accion()
        except (ValueError, PermissionError) as error:
            self._vista.mostrar_error(str(error))
            return False, None
        if cambia_datos:
            self._guardar()
            self._al_cambiar()
        texto = mensaje_ok(resultado) if callable(mensaje_ok) else mensaje_ok
        self._vista.mostrar_mensaje(texto)
        return True, resultado

    def _elegir_coordinador(self) -> Optional[int]:
        """Decide QUÉ coordinador realiza una acción (aprobar, rechazar, generar reporte).

        [REFACTOR] Esta misma lógica estaba escrita dos veces: en la interfaz gráfica
        (VistaBase._elegir_coordinador) y en el menú (MenuConsola._elegir_coordinador).
        Ahora vive solo aquí y la usan las dos vistas.
            * Si inició sesión un coordinador, actúa siempre como él mismo.
            * Si no hay coordinadores, se avisa.
            * Si hay uno solo, se usa sin preguntar; si hay varios, se pregunta.
        """
        if self._cuenta is not None and self._cuenta.rol == COORDINADOR:
            return self._cuenta.id_docente
        coordinadores = self._sistema.coordinadores
        vista: IVistaDialogos = self._vista   # type: ignore[assignment]
        if not coordinadores:
            vista.avisar("No hay coordinadores. Primero designe uno (pantalla Docentes).")
            return None
        if len(coordinadores) == 1:
            return coordinadores[0].id
        return vista.elegir("¿Qué coordinador realiza la acción?",
                            [(f"{c.get_nombre_completo()} ({c.carrera})", c.id) for c in coordinadores])

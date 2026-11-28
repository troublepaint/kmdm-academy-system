"""Presentadores de las CUENTAS de acceso.  [NUEVO] [MVP]

    PresentadorUsuarios  pantalla "Usuarios y accesos" (solo el administrador)
    PresentadorMiClave   botón "Mi contraseña" de la barra lateral (cualquier usuario)

[SOLID-D] Dependen de la interfaz Autenticador, no de cómo se guardan las cuentas.
[REFACTOR] La comprobación "las dos contraseñas deben coincidir" estaba copiada tres veces
(crear cuenta, restablecer clave y cambiar mi clave); ahora todas usan validar_repeticion().
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from servicios.autenticacion import ADMINISTRADOR, DOCENTE, AutenticadorLocal

from .base import IVista, IVistaTabla, PresentadorBase
from .comun import rol_efectivo, validar_repeticion

if TYPE_CHECKING:
    from servicios import Autenticador, Cuenta, SistemaAcademico


class PresentadorUsuarios(PresentadorBase):
    _vista: IVistaTabla

    def __init__(self, vista: IVistaTabla, sistema: "SistemaAcademico",
                 autenticador: Optional["Autenticador"], **kwargs):
        super().__init__(vista, sistema, **kwargs)
        self._auth = autenticador

    def _local(self, avisar: bool = True) -> Optional[AutenticadorLocal]:
        """Administrar cuentas solo es posible con AutenticadorLocal (tiene la lista de usuarios)."""
        if isinstance(self._auth, AutenticadorLocal):
            return self._auth
        if avisar:
            self._vista.avisar("Este autenticador no permite administrar cuentas desde la interfaz.")
        return None

    def cargar(self) -> None:
        a = self._local(avisar=False)
        if a is None:
            return
        self._vista.mostrar_filas([
            (c["usuario"], (c["usuario"], c["nombre"],
                            rol_efectivo(c["rol"], c["id_docente"], self._sistema).capitalize(),
                            c["id_docente"] if c["id_docente"] is not None else "—"),
             "APROBADA" if c["rol"] == ADMINISTRADOR else None) for c in a.usuarios()])

    def puede_crear(self) -> bool:
        """Comprueba antes de abrir el formulario (y avisa el motivo si no se puede)."""
        if self._local() is None:
            return False
        if not self._sistema.docentes:
            self._vista.avisar("Primero registre docentes en la pantalla Docentes.")
            return False
        return True

    def opciones_docentes(self) -> list[tuple[str, int]]:
        return [(f"{d.id} - {d.get_nombre_completo()}", d.id) for d in self._sistema.docentes]

    def crear_cuenta_docente(self, id_docente: int, clave: str, repetir: str) -> bool:
        a = self._local()
        if a is None:
            return False

        def crear():
            validar_repeticion(clave, repetir)
            d = self._sistema.buscar_docente(id_docente)
            a.crear_cuenta(d.correo, clave, DOCENTE, d.id, d.get_nombre_completo())
        # Las cuentas se guardan en su propio archivo (lo hace el autenticador):
        # por eso cambia_datos=False (no hay que guardar el sistema académico).
        ok, _ = self._ejecutar(crear, "Cuenta creada: el usuario es el correo del docente",
                               cambia_datos=False)
        self.cargar()
        return ok

    def restablecer_clave(self, usuario: str, clave: str, repetir: str) -> bool:
        a = self._local()
        if a is None:
            return False

        def cambiar():
            validar_repeticion(clave, repetir)
            a.restablecer_clave(usuario, clave)
        ok, _ = self._ejecutar(cambiar, "Contraseña actualizada", cambia_datos=False)
        return ok

    def eliminar_cuenta(self, usuario: str) -> bool:
        a = self._local()
        if a is None:
            return False
        if self._cuenta is not None and usuario == self._cuenta.usuario:
            self._vista.avisar("No puede eliminar la cuenta con la que inició sesión.")
            return False
        if not self._vista.confirmar(f"¿Eliminar la cuenta {usuario}?"):
            return False
        ok, _ = self._ejecutar(lambda: a.eliminar_cuenta(usuario), "Cuenta eliminada", cambia_datos=False)
        self.cargar()
        return ok


class PresentadorMiClave:
    """Cambiar la contraseña propia. Solo necesita una IVista mínima (mensaje y error):
    [SOLID-I] la ventana principal no tiene que implementar tablas ni diálogos para esto."""

    def __init__(self, vista: IVista, autenticador: "Autenticador", cuenta: "Cuenta"):
        self._vista, self._auth, self._cuenta = vista, autenticador, cuenta

    def cambiar(self, actual: str, nueva: str, repetir: str) -> bool:
        try:
            validar_repeticion(nueva, repetir, "Las contraseñas nuevas no coinciden")
            self._auth.cambiar_clave(self._cuenta.usuario, actual, nueva)
        except ValueError as error:
            self._vista.mostrar_error(str(error))
            return False
        self._vista.mostrar_mensaje("Contraseña actualizada")
        return True

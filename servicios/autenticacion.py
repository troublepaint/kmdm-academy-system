"""INICIO DE SESIÓN: cuentas, contraseñas seguras y roles.  [NUEVO]

    Autenticador (INTERFAZ)
    └── AutenticadorLocal      guarda las cuentas en un archivo JSON

Las contraseñas NUNCA se guardan en texto plano: se guarda una "sal" aleatoria y el
resultado de PBKDF2-HMAC-SHA256 (200 000 vueltas). Para comprobar una clave se vuelve a
calcular el hash y se compara en tiempo constante (hmac.compare_digest).

El archivo de cuentas es independiente de data/datos.json: los datos académicos no se
tocan y el sistema sigue funcionando sin login (menú de consola).

[SOLID-S] Esta clase solo sabe de cuentas y claves; no sabe nada de pantallas ni de horarios.
[SOLID-D] La interfaz gráfica depende de la interfaz Autenticador, no de AutenticadorLocal.
[SOLID-O] Se puede escribir otro Autenticador (por ejemplo contra una base de datos o LDAP)
          sin cambiar la ventana de login.
[U2-POLIMORFISMO-INTERFACES] Autenticador es una interfaz (solo métodos abstractos).
[U2-INYECCIÓN-DEPENDENCIAS] AutenticadorLocal recibe la ruta del archivo; la pantalla de
          login recibe el Autenticador ya creado (main_gui.py).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ADMINISTRADOR = "ADMINISTRADOR"
COORDINADOR = "COORDINADOR"
DOCENTE = "DOCENTE"

USUARIO_INICIAL = "admin"
CLAVE_INICIAL = "admin123"
_VUELTAS = 200_000
_MIN_CLAVE = 6


@dataclass(frozen=True)
class Cuenta:
    """Quién inició sesión. 'id_docente' es None para el administrador."""
    usuario: str
    nombre: str
    rol: str
    id_docente: Optional[int] = None


class Autenticador(ABC):
    """[U2-POLIMORFISMO-INTERFACES] Interfaz: lo único que la ventana necesita saber."""

    @abstractmethod
    def iniciar_sesion(self, usuario: str, clave: str) -> Cuenta:
        """Devuelve la Cuenta o lanza ValueError con un mensaje claro."""

    @abstractmethod
    def cambiar_clave(self, usuario: str, clave_actual: str, clave_nueva: str) -> None:
        """Cambia la contraseña (ValueError si algo no es válido)."""


def _hash(clave: str, sal: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal, _VUELTAS).hex()


def validar_clave_nueva(clave: str) -> None:
    if len(clave) < _MIN_CLAVE:
        raise ValueError(f"La contraseña debe tener al menos {_MIN_CLAVE} caracteres")


class AutenticadorLocal(Autenticador):
    """Cuentas guardadas en un archivo JSON. Si el archivo no existe, crea la cuenta
    inicial admin / admin123 (se recomienda cambiarla en la pantalla Usuarios)."""

    def __init__(self, ruta: str | Path):
        self._ruta = Path(ruta)
        self._cuentas: dict[str, dict] = {}
        if self._ruta.exists():
            try:
                self._cuentas = json.loads(self._ruta.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                raise ValueError(f"El archivo de cuentas está dañado: {error}") from error
        if not self._cuentas:
            self.crear_cuenta(USUARIO_INICIAL, CLAVE_INICIAL, ADMINISTRADOR, nombre="Administrador")

    # ------------------------------------------------------------- consultas
    @staticmethod
    def _clave_usuario(usuario: str) -> str:
        return usuario.strip().lower()

    def usuarios(self) -> list[dict]:
        """Lista pública (sin hashes) para mostrarla en la pantalla Usuarios."""
        return [{"usuario": u, "nombre": d["nombre"], "rol": d["rol"], "id_docente": d.get("id_docente")}
                for u, d in sorted(self._cuentas.items())]

    def existe(self, usuario: str) -> bool:
        return self._clave_usuario(usuario) in self._cuentas

    def con_clave_inicial(self) -> bool:
        """True si admin todavía usa la contraseña de fábrica (la ventana avisa)."""
        d = self._cuentas.get(USUARIO_INICIAL)
        return bool(d) and hmac.compare_digest(
            _hash(CLAVE_INICIAL, bytes.fromhex(d["sal"])), d["hash"])

    # ------------------------------------------------------------- escritura
    def crear_cuenta(self, usuario: str, clave: str, rol: str, id_docente: Optional[int] = None,
                     nombre: str = "") -> None:
        u = self._clave_usuario(usuario)
        if not u:
            raise ValueError("El usuario no puede estar vacío")
        if u in self._cuentas:
            raise ValueError(f"Ya existe una cuenta con el usuario '{u}'")
        validar_clave_nueva(clave)
        sal = secrets.token_bytes(16)
        self._cuentas[u] = {"sal": sal.hex(), "hash": _hash(clave, sal), "rol": rol,
                            "id_docente": id_docente, "nombre": nombre or u}
        self._guardar()

    def restablecer_clave(self, usuario: str, clave_nueva: str) -> None:
        """Uso del administrador: pone una clave nueva sin pedir la anterior."""
        u = self._clave_usuario(usuario)
        if u not in self._cuentas:
            raise ValueError("La cuenta no existe")
        validar_clave_nueva(clave_nueva)
        sal = secrets.token_bytes(16)
        self._cuentas[u].update(sal=sal.hex(), hash=_hash(clave_nueva, sal))
        self._guardar()

    def eliminar_cuenta(self, usuario: str) -> None:
        u = self._clave_usuario(usuario)
        if u not in self._cuentas:
            raise ValueError("La cuenta no existe")
        admins = [x for x, d in self._cuentas.items() if d["rol"] == ADMINISTRADOR]
        if self._cuentas[u]["rol"] == ADMINISTRADOR and len(admins) == 1:
            raise ValueError("No se puede eliminar al único administrador")
        del self._cuentas[u]
        self._guardar()

    # --------------------------------------------------- Autenticador (interfaz)
    def iniciar_sesion(self, usuario: str, clave: str) -> Cuenta:
        u = self._clave_usuario(usuario)
        d = self._cuentas.get(u)
        # Mismo mensaje si el usuario no existe o la clave falla: no revela cuál fue.
        sal = bytes.fromhex(d["sal"]) if d else b"0" * 16
        coincide = hmac.compare_digest(_hash(clave, sal), d["hash"] if d else "x")
        if not d or not coincide:
            raise ValueError("Usuario o contraseña incorrectos")
        return Cuenta(u, d["nombre"], d["rol"], d.get("id_docente"))

    def cambiar_clave(self, usuario: str, clave_actual: str, clave_nueva: str) -> None:
        self.iniciar_sesion(usuario, clave_actual)   # valida la actual
        self.restablecer_clave(usuario, clave_nueva)

    # ---------------------------------------------------------------- archivo
    def _guardar(self) -> None:
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = self._ruta.with_suffix(".tmp")
        temporal.write_text(json.dumps(self._cuentas, indent=2, ensure_ascii=False), encoding="utf-8")
        temporal.replace(self._ruta)   # reemplazo atómico: nunca queda el archivo a medias

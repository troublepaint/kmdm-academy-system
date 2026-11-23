"""FÁBRICA DE USUARIOS (Docente / CoordinadorAcademico)  [NUEVO]

[PATRÓN: Factory Method]  (creacional)
    Problema que resuelve: AlmacenJSON decidía qué clase crear con un
    if/else según el rol guardado ("si es COORDINADOR crea un
    CoordinadorAcademico, si no, un Docente"). Cada rol nuevo obligaba a
    editar ese if. Con Factory Method cada rol tiene su propio CREADOR.

    Participantes:
      Producto            -> Usuario (clase abstracta que ya existía)
      Productos concretos -> Docente, CoordinadorAcademico
      Creador             -> CreadorUsuario (declara el método fábrica)
      Creadores concretos -> CreadorDocente, CreadorCoordinador

[U2-POLIMORFISMO-ABSTRACTAS]
    CreadorUsuario es una clase abstracta con un método abstracto
    (crear_usuario) y un método ya escrito (registrar) que sirve para TODOS
    los creadores sin saber qué clase de usuario devuelven.

[SOLID-O] Un rol nuevo (ej. Decano) = una subclase de CreadorUsuario + una
    línea en CREADORES_POR_ROL. No se toca AlmacenJSON ni SistemaAcademico.
[SOLID-S] Toda la creación de usuarios (y sus datos obligatorios) vive aquí.
[SOLID-D] Quien crea usuarios depende de CreadorUsuario (abstracción), no de
    las clases Docente o CoordinadorAcademico.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .administrador import Administrador
from .usuarios import CoordinadorAcademico, Docente, Usuario


class CreadorUsuario(ABC):
    """[PATRÓN: Factory Method] Creador: declara el método fábrica."""

    @abstractmethod
    def crear_usuario(self, datos: dict) -> Usuario:
        """MÉTODO FÁBRICA: cada creador concreto devuelve su tipo de Usuario.
        El tipo de retorno es la clase base común (Usuario)."""

    def registrar(self, admin: Administrador, datos: dict) -> Usuario:
        """Lógica común: crea el usuario y lo registra en el administrador.
        (La creación NO es la responsabilidad principal del creador: aquí está
        el trabajo real, que funciona con cualquier tipo de Usuario.)"""
        usuario = self.crear_usuario(datos)
        admin.registrar_usuario(usuario)
        return usuario

    @staticmethod
    def _exigir(datos: dict, *claves: str) -> None:
        faltan = [c for c in claves if c not in datos]
        if faltan:
            raise ValueError(f"Faltan datos obligatorios: {', '.join(faltan)}")


class CreadorDocente(CreadorUsuario):
    """Creador concreto: produce objetos Docente."""

    def crear_usuario(self, datos: dict) -> Docente:
        self._exigir(datos, "id", "nombre", "apellido", "correo", "cedula",
                     "especialidad", "horas_max_semana")
        return Docente(datos["id"], datos["nombre"], datos["apellido"],
                       datos["correo"], datos["cedula"], datos["especialidad"],
                       datos["horas_max_semana"])


class CreadorCoordinador(CreadorUsuario):
    """Creador concreto: produce objetos CoordinadorAcademico."""

    def crear_usuario(self, datos: dict) -> CoordinadorAcademico:
        self._exigir(datos, "id", "nombre", "apellido", "correo", "cedula",
                     "especialidad", "horas_max_semana", "carrera")
        return CoordinadorAcademico(
            datos["id"], datos["nombre"], datos["apellido"], datos["correo"],
            datos["cedula"], datos["especialidad"], datos["horas_max_semana"],
            datos["carrera"])


# Registro rol -> creador. Reemplaza al if/else. [SOLID-O] Se extiende sin editar código.
CREADORES_POR_ROL: dict[str, CreadorUsuario] = {
    "DOCENTE": CreadorDocente(),
    "COORDINADOR": CreadorCoordinador(),
}


def creador_para(rol: str) -> CreadorUsuario:
    """Devuelve el creador del rol indicado (DOCENTE, COORDINADOR...)."""
    try:
        return CREADORES_POR_ROL[rol.upper()]
    except KeyError:
        raise ValueError(f"No hay un creador registrado para el rol {rol!r}") from None


if __name__ == "__main__":
    # Prueba rápida:  python -m modelos.fabrica_usuarios
    adm = Administrador(100, "Root", "Admin", "admin@uleam.edu.ec", "ADM-001")
    fila = {"id": 1, "nombre": "Ana", "apellido": "Pérez", "correo": "ana@uleam.edu.ec",
            "cedula": "1312345678", "especialidad": "Software", "horas_max_semana": 20}
    u = creador_para("DOCENTE").registrar(adm, fila)
    print(type(u).__name__, u.get_rol())

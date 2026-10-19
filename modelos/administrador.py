"""Administrador: gestiona los registros generales del sistema.

Hereda de Usuario (HERENCIA SIMPLE) y es hermano de Docente: ambos son
usuarios, pero con funciones distintas. Un administrador NO es docente.

Como el diagrama no tiene una clase "repositorio", el administrador guarda
los registros (usuarios, períodos, aulas, asignaturas) en listas privadas.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from .academico import Asignatura, Periodo
from .infraestructura import Aula
from .usuarios import CoordinadorAcademico, Docente, Usuario


class Administrador(Usuario):
    def __init__(self, id_usuario: int, nombre: str, apellido: str, correo: str,
                 codigo_admin: str, fecha_ingreso: Optional[date] = None):
        super().__init__(id_usuario, nombre, apellido, correo)  # datos de Usuario
        self._codigo_admin = self._validar_texto(codigo_admin, "codigo_admin")
        self._fecha_ingreso = fecha_ingreso or date.today()
        # Listas PRIVADAS: nadie desde fuera puede agregar o quitar elementos
        # directamente; solo a través de los métodos registrar_* de abajo.
        self._usuarios: list[Usuario] = []
        self._periodos: list[Periodo] = []
        self._aulas: list[Aula] = []
        self._asignaturas: list[Asignatura] = []

    @property
    def codigo_admin(self) -> str:
        return self._codigo_admin

    @property
    def fecha_ingreso(self) -> date:
        return self._fecha_ingreso

    # Se devuelven COPIAS en forma de tupla (inmutables): se puede consultar
    # la lista, pero no modificarla desde fuera. [ENCAPSULAMIENTO]
    @property
    def usuarios(self) -> tuple:
        return tuple(self._usuarios)

    @property
    def periodos(self) -> tuple:
        return tuple(self._periodos)

    @property
    def aulas(self) -> tuple:
        return tuple(self._aulas)

    @property
    def asignaturas(self) -> tuple:
        return tuple(self._asignaturas)

    # ---- métodos del diagrama ----
    def registrar_usuario(self, u: Usuario) -> None:
        """Agrega un docente o coordinador, evitando duplicados."""
        if not isinstance(u, Usuario):
            raise TypeError("Solo se pueden registrar objetos Usuario")
        if isinstance(u, Administrador):
            raise ValueError("El sistema tiene un único administrador")
        if any(x.id == u.id for x in self._usuarios):
            raise ValueError(f"Ya existe un usuario con id {u.id}")
        if any(x.correo.lower() == u.correo.lower() for x in self._usuarios):
            raise ValueError(f"Ya existe un usuario con el correo {u.correo}")
        self._usuarios.append(u)

    def designar_coordinador(self, d: Docente, carrera: str) -> CoordinadorAcademico:
        """Convierte a un docente registrado en coordinador.

        Un objeto no puede cambiar de clase una vez creado. Por eso se crea un
        CoordinadorAcademico NUEVO con los mismos datos del docente y se
        reemplaza al docente en el registro.
        """
        if isinstance(d, CoordinadorAcademico):
            raise ValueError(f"{d.get_nombre_completo()} ya es coordinador")
        if d not in self._usuarios:
            raise ValueError("El docente debe estar registrado antes de designarlo")
        coord = CoordinadorAcademico(
            d.id, d.nombre, d.apellido, d.correo, d.cedula, d.especialidad,
            d.horas_max_semana, carrera, horas_asignadas=d.horas_asignadas)
        self._usuarios[self._usuarios.index(d)] = coord  # reemplazo en la lista
        return coord

    def registrar_periodo(self, p: Periodo) -> None:
        """Agrega un período. Solo puede haber UNO activo a la vez."""
        if not isinstance(p, Periodo):
            raise TypeError("Se esperaba un objeto Periodo")
        if any(x.id == p.id for x in self._periodos):
            raise ValueError(f"Ya existe un período con id {p.id}")
        if p.activo and any(x.activo for x in self._periodos):
            raise ValueError("Ya hay un período activo; ciérrelo antes de crear otro")
        self._periodos.append(p)

    def crear_periodo(self, nombre: str, inicio: date, fin: date) -> Periodo:
        """Crea un período nuevo con id automático y lo registra."""
        nuevo_id = max((p.id for p in self._periodos), default=0) + 1
        periodo = Periodo(nuevo_id, nombre, inicio, fin)
        self.registrar_periodo(periodo)
        return periodo

    def registrar_aula(self, a: Aula) -> None:
        if not isinstance(a, Aula):
            raise TypeError("Se esperaba un objeto Aula")
        if any(x.codigo == a.codigo for x in self._aulas):
            raise ValueError(f"Ya existe un aula con código {a.codigo}")
        self._aulas.append(a)

    def registrar_asignatura(self, a: Asignatura) -> None:
        if not isinstance(a, Asignatura):
            raise TypeError("Se esperaba un objeto Asignatura")
        if any(x.codigo == a.codigo for x in self._asignaturas):
            raise ValueError(f"Ya existe una asignatura con código {a.codigo}")
        self._asignaturas.append(a)

    def get_rol(self) -> str:
        # Tercera versión de get_rol en la jerarquía. [POLIMORFISMO]
        return "ADMINISTRADOR"


if __name__ == "__main__":
    # Prueba rápida. Ejecutar desde la carpeta kmdm_academy:  python -m modelos.administrador
    adm = Administrador(100, "Root", "Admin", "admin@uleam.edu.ec", "ADM-001")
    d = Docente(1, "Ana", "Pérez", "ana@uleam.edu.ec", "1312345678", "Software", 20)
    adm.registrar_usuario(d)
    c = adm.designar_coordinador(d, "Software")
    print(adm.get_rol(), "->", c.get_rol(), c.carrera, [u.get_rol() for u in adm.usuarios])
    p = adm.crear_periodo("2026-2", date(2026, 5, 1), date(2026, 10, 31))
    print(p)

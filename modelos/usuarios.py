"""JERARQUÍA DE USUARIOS

    Usuario (clase ABSTRACTA)
    ├── Docente
    │   └── CoordinadorAcademico        <- herencia MULTINIVEL (3 niveles)
    └── Administrador (está en administrador.py)

Conceptos de POO que se demuestran aquí:
  * ABSTRACCIÓN y CLASE ABSTRACTA : Usuario no se puede crear directamente.
  * ENCAPSULAMIENTO               : atributos privados (_x) + @property.
  * HERENCIA SIMPLE               : Docente hereda de Usuario.
  * HERENCIA MULTINIVEL           : CoordinadorAcademico hereda de Docente,
                                    que a su vez hereda de Usuario.
  * POLIMORFISMO                  : get_rol() devuelve algo distinto en cada clase.

Etiquetas de esta entrega (ver README.md):
  [U2-HERENCIA]                 Usuario -> Docente -> CoordinadorAcademico (3 niveles).
  [U2-POLIMORFISMO-ABSTRACTAS]  Usuario es abstracta y get_rol() es abstracto.
  [SOLID-L]                     un CoordinadorAcademico puede usarse donde se pida un
                                Docente (ver ReporteCargaDocente y demo_solid_patrones.py).
  [SOLID-S]                     cada clase tiene sus propios datos y reglas.
  [PATRÓN: Factory Method]      los usuarios se crean con modelos/fabrica_usuarios.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterable

from .enums import EstadoSesion
from .reportes import ReporteCargaDocente, ReporteHorario
from .validaciones import texto_obligatorio

# Estos imports se usan SOLO para las anotaciones de tipo. Se ponen dentro de
# "TYPE_CHECKING" para evitar imports circulares (A importa B y B importa A).
if TYPE_CHECKING:
    from .academico import Periodo
    from .horarios import SesionClase


class Usuario(ABC):
    """Clase abstracta: es la plantilla común de todos los usuarios.

    Hereda de ABC, por eso NO se puede hacer Usuario(...) directamente:
    solo se pueden crear objetos de sus subclases concretas.

    [U2-POLIMORFISMO-ABSTRACTAS] Clase abstracta: mezcla métodos ya escritos
    (get_nombre_completo...) con uno ABSTRACTO (get_rol) que obliga a cada
    subclase a escribir su versión.
    """

    def __init__(self, id_usuario: int, nombre: str, apellido: str, correo: str):
        # El guion bajo (_) indica que el atributo es PRIVADO: desde fuera de
        # la clase no se debe tocar directamente. [ENCAPSULAMIENTO]
        self._id = id_usuario
        # Se valida ANTES de guardar: nunca queda un dato inválido en el objeto.
        self._nombre = self._validar_texto(nombre, "nombre")
        self._apellido = self._validar_texto(apellido, "apellido")
        self._correo = self._validar_correo(correo)

    # ---- validaciones reutilizables (las heredan todas las subclases) ----
    @staticmethod
    def _validar_texto(valor: str, campo: str) -> str:
        """Rechaza textos vacíos y quita espacios sobrantes (usa la validación común)."""
        return texto_obligatorio(valor, f"El campo '{campo}' no puede estar vacío")

    @staticmethod
    def _validar_correo(correo: str) -> str:
        """Validación simple: debe tener '@' y un punto después del '@'."""
        if not isinstance(correo, str) or "@" not in correo or "." not in correo.split("@")[-1]:
            raise ValueError(f"Correo inválido: {correo!r}")
        return correo.strip()

    # ---- ENCAPSULAMIENTO: acceso de SOLO LECTURA ----
    # @property permite escribir usuario.nombre (sin paréntesis) para LEER el
    # dato, pero como no hay "setter" no se puede modificar desde fuera.
    @property
    def id(self) -> int:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def apellido(self) -> str:
        return self._apellido

    @property
    def correo(self) -> str:
        return self._correo

    # ---- métodos del diagrama ----
    def get_nombre_completo(self) -> str:
        return f"{self._nombre} {self._apellido}"

    def actualizar_correo(self, nuevo: str) -> None:
        # Única forma de CAMBIAR el correo, y siempre pasa por la validación.
        self._correo = self._validar_correo(nuevo)

    @abstractmethod
    def get_rol(self) -> str:
        """Método ABSTRACTO: aquí no tiene cuerpo.

        Obliga a cada subclase concreta a escribir su propia versión.
        Es la base del POLIMORFISMO: mismo método, resultado distinto.
        """


class Docente(Usuario):
    """HERENCIA SIMPLE: un Docente ES un Usuario.

    Reutiliza id, nombre, apellido, correo y sus validaciones, y agrega lo
    propio del docente: cédula, especialidad y control de horas.

    [U2-HERENCIA] Herencia simple: Docente reutiliza todo Usuario con super().
    """

    def __init__(self, id_usuario: int, nombre: str, apellido: str, correo: str,
                 cedula: str, especialidad: str, horas_max_semana: int,
                 horas_asignadas: float = 0):
        # super() llama al constructor de la clase padre (Usuario) para que
        # guarde los datos comunes. Aquí solo se agrega lo nuevo.
        super().__init__(id_usuario, nombre, apellido, correo)
        self._cedula = self._validar_texto(cedula, "cedula")
        self._especialidad = self._validar_texto(especialidad, "especialidad")
        if horas_max_semana <= 0:
            raise ValueError("horas_max_semana debe ser mayor que 0")
        if not 0 <= horas_asignadas <= horas_max_semana:
            raise ValueError("horas_asignadas fuera de rango")
        self._horas_max_semana = horas_max_semana
        self._horas_asignadas = horas_asignadas

    @property
    def cedula(self) -> str:
        return self._cedula

    @property
    def especialidad(self) -> str:
        return self._especialidad

    @property
    def horas_max_semana(self) -> int:
        return self._horas_max_semana

    @property
    def horas_asignadas(self) -> float:
        return self._horas_asignadas

    def tiene_capacidad(self, horas: float) -> bool:
        """¿Puede tomar 'horas' más sin pasar su máximo semanal?"""
        return self._horas_asignadas + horas <= self._horas_max_semana

    def asignar_horas(self, horas: float) -> None:
        """Suma horas a su carga. Falla si no tiene capacidad."""
        if horas <= 0:
            raise ValueError("Las horas a asignar deben ser mayores que 0")
        if not self.tiene_capacidad(horas):
            raise ValueError(
                f"{self.get_nombre_completo()} no tiene capacidad para {horas} h más")
        self._horas_asignadas += horas

    def liberar_horas(self, horas: float) -> None:
        """Resta horas de su carga (cuando se rechaza una sesión aprobada)."""
        if horas <= 0:
            raise ValueError("Las horas a liberar deben ser mayores que 0")
        if horas > self._horas_asignadas:
            raise ValueError("No se pueden liberar más horas de las asignadas")
        self._horas_asignadas -= horas

    def get_rol(self) -> str:
        # Implementa el método abstracto de Usuario. [POLIMORFISMO]
        return "DOCENTE"


class CoordinadorAcademico(Docente):
    """HERENCIA MULTINIVEL: Usuario -> Docente -> CoordinadorAcademico.

    Un coordinador ES un docente (puede dar clases) y además tiene permisos
    para aprobar o rechazar sesiones y generar reportes. Por eso hereda de
    Docente y no de Usuario directamente.

    [U2-HERENCIA] Tercer nivel de la jerarquía (herencia multinivel).
    [SOLID-L] Principio de sustitución de Liskov: el coordinador NO cambia las
    reglas de Docente (mismos métodos, mismas condiciones); solo AGREGA
    aprobar/rechazar/reportes. Por eso se puede usar donde se espera un Docente.
    """

    def __init__(self, id_usuario: int, nombre: str, apellido: str, correo: str,
                 cedula: str, especialidad: str, horas_max_semana: int,
                 carrera: str, horas_asignadas: float = 0):
        # Le pasa a Docente todo lo que Docente ya sabe guardar.
        super().__init__(id_usuario, nombre, apellido, correo, cedula,
                         especialidad, horas_max_semana, horas_asignadas)
        self._carrera = self._validar_texto(carrera, "carrera")

    @property
    def carrera(self) -> str:
        return self._carrera

    def aprobar_sesion(self, s: SesionClase) -> None:
        """Aprueba una sesión en BORRADOR, aplicando las reglas del sistema."""
        # Regla 1: nadie puede aprobar su propio horario (conflicto de interés).
        if s.docente is self or s.docente.id == self.id:
            raise PermissionError("El coordinador no puede aprobar sus propias sesiones")
        # Regla 2: solo se aprueba lo que está pendiente.
        if s.estado != EstadoSesion.BORRADOR:
            raise ValueError(f"Solo se aprueban sesiones en BORRADOR (estado: {s.estado.name})")
        # Regla 3: se asignan las horas al docente ANTES de cambiar el estado.
        # Si no tiene capacidad, lanza error y la sesión queda intacta.
        s.docente.asignar_horas(s.get_duracion_horas())
        s.cambiar_estado(EstadoSesion.APROBADA)
        s.coordinador = self  # queda registrado quién la aprobó

    def rechazar_sesion(self, s: SesionClase, motivo: str) -> None:
        """Rechaza una sesión y guarda el motivo."""
        if not motivo or not motivo.strip():
            raise ValueError("Debe indicar el motivo del rechazo")
        estaba_aprobada = s.estado == EstadoSesion.APROBADA
        s.cambiar_estado(EstadoSesion.RECHAZADA)  # esta línea valida la transición
        if estaba_aprobada:
            # Si ya estaba aprobada, sus horas ya se habían asignado: se devuelven.
            s.docente.liberar_horas(s.get_duracion_horas())
        s.motivo_rechazo = motivo.strip()
        s.coordinador = self

    def generar_reporte(self, p: Periodo, sesiones: list[SesionClase]) -> ReporteHorario:
        """Crea el reporte de horarios de un período.

        Nota: el diagrama solo tenía (p: Periodo); se agregó 'sesiones' porque
        ninguna clase guarda la lista completa de sesiones.
        """
        del_periodo = [s for s in sesiones if s.periodo.id == p.id]
        # INYECCIÓN DE DEPENDENCIAS: las sesiones se le ENTREGAN al reporte
        # por el constructor; el reporte no las busca ni las crea él mismo.
        reporte = ReporteHorario(f"Horario {self._carrera} - {p.nombre}", del_periodo)
        reporte.generar()
        return reporte

    def generar_reporte_carga(self, docentes: Iterable[Docente]) -> ReporteCargaDocente:
        """[NUEVO] Reporte de horas aprobadas de cada docente.

        [U2-INYECCIÓN-DEPENDENCIAS] Los docentes se ENTREGAN por parámetro.
        [U2-POLIMORFISMO-ABSTRACTAS] Devuelve otro tipo de Reporte (hermano de
        ReporteHorario): ambos se usan igual desde fuera.
        """
        reporte = ReporteCargaDocente(f"Carga docente - {self._carrera}", docentes)
        reporte.generar()
        return reporte

    def get_rol(self) -> str:
        # SOBRESCRIBE el get_rol de Docente. [POLIMORFISMO]
        return "COORDINADOR"


if __name__ == "__main__":
    # Prueba rápida. Ejecutar desde la carpeta kmdm_academy:  python -m modelos.usuarios
    d = Docente(1, "Ana", "Pérez", "ana@uleam.edu.ec", "1312345678", "Software", 20)
    c = CoordinadorAcademico(2, "Luis", "Mora", "luis@uleam.edu.ec", "1398765432",
                             "Redes", 20, "Software")
    d.asignar_horas(4)
    print(d.get_nombre_completo(), d.get_rol(), d.horas_asignadas, d.tiene_capacidad(17))
    print(c.get_nombre_completo(), c.get_rol(), c.carrera, isinstance(c, Docente))
    try:
        Usuario(3, "X", "Y", "x@y.com")
    except TypeError as e:
        print("Usuario es abstracta:", e)

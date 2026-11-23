"""SistemaAcademico: la LÓGICA que une todas las clases.  [MODIFICADO]

Cada clase de modelos/ sabe hacer lo suyo (una Sesion detecta conflictos, un
Coordinador aprueba...), pero alguien tiene que COORDINARLAS: guardar la lista
de sesiones, buscar objetos por ID, comprobar que exista un período activo...
Eso es lo que hace esta clase.

NO pide datos ni imprime nada (eso es del menú) y NO sabe de archivos (eso es
del almacén).

Qué se aplicó aquí (busca las etiquetas en el código):
  [PATRÓN: Facade]            esta clase es la "puerta única" del sistema: el menú
                              no necesita conocer a las demás clases.
  [PATRÓN: Builder]           crear_sesion() arma la sesión con un ConstructorSesion.
  [PATRÓN: Prototype]         duplicar_sesion() clona una sesión existente.
  [PATRÓN: Factory Method]    registrar_docente() crea el usuario con un CreadorUsuario.
  [U2-INYECCIÓN-DEPENDENCIAS] las reglas y el constructor se RECIBEN en __init__.
  [SOLID-S/O/D]               las validaciones salieron a servicios/reglas.py.
"""
from __future__ import annotations

from datetime import date, time
from typing import Optional, Sequence

from modelos import (Administrador, Asignatura, Aula, AulaClasificacion,
                     ConstructorSesion, ConstructorSesionClase,
                     CoordinadorAcademico, DiaSemana, Docente, Periodo,
                     Reporte, SesionClase, creador_para)

from .reglas import ReglaSesion, reglas_por_defecto


class SistemaAcademico:
    def __init__(self, admin: Optional[Administrador] = None,
                 con_clasificaciones_base: bool = True,
                 reglas: Optional[Sequence[ReglaSesion]] = None,
                 constructor_sesion: Optional[ConstructorSesion] = None):
        # [U2-INYECCIÓN-DEPENDENCIAS] Las dependencias (administrador, reglas y
        # constructor de sesiones) LLEGAN desde afuera. Si no se entregan, se usan
        # valores por defecto. Antes las comprobaciones estaban escritas aquí dentro.
        # [SOLID-D] Se depende de las abstracciones ReglaSesion y ConstructorSesion.
        self._admin = admin or Administrador(
            0, "Administrador", "Sistema", "admin@kmdm.edu.ec", "ADM-001")
        self._reglas: list[ReglaSesion] = (
            list(reglas) if reglas is not None else reglas_por_defecto())
        self._constructor_sesion: ConstructorSesion = (
            constructor_sesion if constructor_sesion is not None else ConstructorSesionClase())
        self._clasificaciones: list[AulaClasificacion] = []
        if con_clasificaciones_base:
            # Dos tipos de aula listos para usar desde el primer arranque.
            self._clasificaciones = [
                AulaClasificacion(1, "Común", "Aulas de clases teóricas"),
                AulaClasificacion(2, "Laboratorio", "Aulas equipadas para práctica", True),
            ]
        # Aquí viven TODAS las sesiones (ninguna otra clase las guarda).
        self._sesiones: list[SesionClase] = []

    # ---------- acceso de solo lectura (devuelven tuplas = copias inmutables) ----------
    @property
    def administrador(self) -> Administrador:
        return self._admin

    @property
    def docentes(self) -> tuple:
        """Docentes y coordinadores (un coordinador también es docente)."""
        return self._admin.usuarios

    @property
    def coordinadores(self) -> tuple:
        # Se filtra con get_rol() en lugar de isinstance: así se aprovecha el
        # POLIMORFISMO (cada objeto dice quién es).
        return tuple(u for u in self._admin.usuarios if u.get_rol() == "COORDINADOR")

    @property
    def aulas(self) -> tuple:
        return self._admin.aulas

    @property
    def asignaturas(self) -> tuple:
        return self._admin.asignaturas

    @property
    def periodos(self) -> tuple:
        return self._admin.periodos

    @property
    def clasificaciones(self) -> tuple:
        return tuple(self._clasificaciones)

    @property
    def sesiones(self) -> tuple:
        return tuple(self._sesiones)

    # ---------- búsquedas: permiten al usuario decir "docente 2" o "aula A-101" ----------
    def buscar_docente(self, id_docente: int) -> Docente:
        for u in self._admin.usuarios:
            if u.id == id_docente:
                return u
        raise ValueError(f"No existe un docente con ID {id_docente}")

    def buscar_coordinador(self, id_coordinador: int) -> CoordinadorAcademico:
        d = self.buscar_docente(id_coordinador)
        if d.get_rol() != "COORDINADOR":
            raise ValueError(f"{d.get_nombre_completo()} no es coordinador")
        return d

    def buscar_aula(self, codigo: str) -> Aula:
        # .lower() hace que "a-101" y "A-101" se consideren el mismo código.
        for a in self._admin.aulas:
            if a.codigo.lower() == codigo.strip().lower():
                return a
        raise ValueError(f"No existe un aula con código {codigo!r}")

    def buscar_asignatura(self, codigo: str) -> Asignatura:
        for a in self._admin.asignaturas:
            if a.codigo.lower() == codigo.strip().lower():
                return a
        raise ValueError(f"No existe una asignatura con código {codigo!r}")

    def buscar_periodo(self, id_periodo: int) -> Periodo:
        for p in self._admin.periodos:
            if p.id == id_periodo:
                return p
        raise ValueError(f"No existe un período con ID {id_periodo}")

    def buscar_clasificacion(self, id_clasificacion: int) -> AulaClasificacion:
        for c in self._clasificaciones:
            if c.id == id_clasificacion:
                return c
        raise ValueError(f"No existe una clasificación con ID {id_clasificacion}")

    def buscar_sesion(self, id_sesion: int) -> SesionClase:
        for s in self._sesiones:
            if s.id == id_sesion:
                return s
        raise ValueError(f"No existe una sesión con ID {id_sesion}")

    def periodo_activo(self) -> Periodo:
        for p in self._admin.periodos:
            if p.activo:
                return p
        raise ValueError("No hay un período activo. Cree uno primero")

    # ---------- operaciones del administrador (delegan en él lo que le corresponde) ----------
    def registrar_docente(self, nombre: str, apellido: str, correo: str, cedula: str,
                          especialidad: str, horas_max_semana: int) -> Docente:
        # ID automático: el mayor existente + 1.
        nuevo_id = max((u.id for u in self._admin.usuarios), default=0) + 1
        datos = {"id": nuevo_id, "nombre": nombre, "apellido": apellido,
                 "correo": correo, "cedula": cedula, "especialidad": especialidad,
                 "horas_max_semana": horas_max_semana}
        # [PATRÓN: Factory Method] El creador del rol DOCENTE decide qué clase
        # instanciar y registra al usuario; aquí ya no se escribe Docente(...).
        return creador_para("DOCENTE").registrar(self._admin, datos)

    def designar_coordinador(self, id_docente: int, carrera: str) -> CoordinadorAcademico:
        docente = self.buscar_docente(id_docente)
        coord = self._admin.designar_coordinador(docente, carrera)
        # El docente "viejo" fue reemplazado por un objeto nuevo: las sesiones que
        # apuntaban al viejo se actualizan para apuntar al coordinador.
        for s in self._sesiones:
            if s.docente is docente:
                s.reemplazar_docente(coord)
        return coord

    def crear_periodo(self, nombre: str, inicio: date, fin: date) -> Periodo:
        return self._admin.crear_periodo(nombre, inicio, fin)

    def cerrar_periodo_activo(self) -> Periodo:
        periodo = self.periodo_activo()
        periodo.cerrar()
        return periodo

    def agregar_clasificacion(self, c: AulaClasificacion) -> None:
        if any(x.id == c.id for x in self._clasificaciones):
            raise ValueError(f"Ya existe una clasificación con ID {c.id}")
        self._clasificaciones.append(c)

    def registrar_aula(self, codigo: str, nombre: str, capacidad: int,
                       ubicacion: str, id_clasificacion: int) -> Aula:
        aula = Aula(codigo, nombre, capacidad, ubicacion,
                    self.buscar_clasificacion(id_clasificacion))
        self._admin.registrar_aula(aula)
        return aula

    def registrar_asignatura(self, codigo: str, nombre: str, nivel: int,
                             horas_teoria: int, horas_practica: int) -> Asignatura:
        asignatura = Asignatura(codigo, nombre, nivel, horas_teoria, horas_practica)
        self._admin.registrar_asignatura(asignatura)
        return asignatura

    # ---------- sesiones ----------
    def crear_sesion(self, dia: DiaSemana, inicio: time, fin: time, cupo: int,
                     codigo_asignatura: str, id_docente: int, codigo_aula: str) -> SesionClase:
        """Crea una sesión en BORRADOR aplicando TODAS las reglas del sistema."""
        periodo = self.periodo_activo()          # debe existir un período abierto
        asignatura = self.buscar_asignatura(codigo_asignatura)
        docente = self.buscar_docente(id_docente)
        aula = self.buscar_aula(codigo_aula)
        nuevo_id = max((s.id for s in self._sesiones), default=0) + 1
        # [PATRÓN: Builder] La sesión se arma paso a paso con nombres claros, en
        # lugar de un constructor de 9 parámetros posicionales. obtener_sesion()
        # valida horas, cupo, disponibilidad y compatibilidad aula-asignatura.
        sesion = (self._constructor_sesion.reset()
                  .establecer_id(nuevo_id)
                  .establecer_horario(dia, inicio, fin)
                  .establecer_cupo(cupo)
                  .establecer_asignatura(asignatura)
                  .establecer_docente(docente)
                  .establecer_aula(aula)
                  .establecer_periodo(periodo)
                  .obtener_sesion())
        self._validar_nueva(sesion)
        self._sesiones.append(sesion)
        return sesion

    def duplicar_sesion(self, id_sesion: int, dia: DiaSemana,
                        inicio: Optional[time] = None,
                        fin: Optional[time] = None) -> SesionClase:
        """[NUEVO] Copia una sesión existente a otro día (y opcionalmente otras horas).

        [PATRÓN: Prototype] La sesión original actúa como prototipo: se CLONA con
        clonar() y solo se cambia lo necesario, en lugar de pedir otra vez los 9
        datos. El clon nace en BORRADOR (una copia de una sesión aprobada NO está
        aprobada) y se crea en el período ACTIVO.
        """
        original = self.buscar_sesion(id_sesion)
        nuevo_id = max((s.id for s in self._sesiones), default=0) + 1
        clon = original.clonar(nuevo_id, dia=dia, hora_inicio=inicio, hora_fin=fin,
                               periodo=self.periodo_activo())
        self._validar_nueva(clon)   # el clon pasa por las MISMAS reglas que una sesión nueva
        self._sesiones.append(clon)
        return clon

    def _validar_nueva(self, sesion: SesionClase) -> None:
        """Aplica todas las reglas inyectadas. [U2-POLIMORFISMO-INTERFACES]

        Se llama a validar() en cada regla sin saber de qué clase es: cada una
        responde a su manera. [SOLID-O] Una regla nueva no obliga a editar este método.
        """
        for regla in self._reglas:
            regla.validar(sesion, self._sesiones)

    def restaurar_sesion(self, sesion: SesionClase) -> None:
        """Agrega una sesión ya validada (se usa al cargar desde archivo)."""
        self._sesiones.append(sesion)

    def aprobar_sesion(self, id_sesion: int, id_coordinador: int) -> SesionClase:
        sesion = self.buscar_sesion(id_sesion)
        # La regla de aprobar vive en CoordinadorAcademico; aquí solo se delega.
        self.buscar_coordinador(id_coordinador).aprobar_sesion(sesion)
        return sesion

    def rechazar_sesion(self, id_sesion: int, id_coordinador: int, motivo: str) -> SesionClase:
        sesion = self.buscar_sesion(id_sesion)
        self.buscar_coordinador(id_coordinador).rechazar_sesion(sesion, motivo)
        return sesion

    def sesiones_de(self, id_docente: int) -> list[SesionClase]:
        """Sesiones de un docente, ordenadas por día y hora."""
        docente = self.buscar_docente(id_docente)
        propias = [s for s in self._sesiones if s.docente.id == docente.id]
        return sorted(propias, key=lambda s: (s.dia.value, s.hora_inicio))

    def sesiones_pendientes(self) -> list[SesionClase]:
        return [s for s in self._sesiones if s.estado.name == "BORRADOR"]

    # ---------- reportes ----------
    # [U2-POLIMORFISMO-ABSTRACTAS] Ambos métodos devuelven un 'Reporte' (clase
    # abstracta); quien los llama los trata igual aunque sean de tipos distintos.
    def generar_reporte(self, id_coordinador: int, id_periodo: int) -> Reporte:
        coord = self.buscar_coordinador(id_coordinador)
        return coord.generar_reporte(self.buscar_periodo(id_periodo), list(self._sesiones))

    def generar_reporte_carga(self, id_coordinador: int) -> Reporte:
        """[NUEVO] Reporte de horas aprobadas de cada docente."""
        coord = self.buscar_coordinador(id_coordinador)
        return coord.generar_reporte_carga(self.docentes)

"""MENÚ DE CONSOLA: solo pide datos y muestra resultados.

Aquí NO se decide ninguna regla del negocio: eso lo hace SistemaAcademico.
Aquí NO se sabe cómo se guardan los datos: eso lo hace el Almacenamiento.
Esta clase únicamente interactúa con el usuario (RESPONSABILIDAD ÚNICA).

Etiquetas de esta entrega (ver README.md):
  [SOLID-S]                    solo pide datos y muestra resultados.
  [SOLID-I]                    depende de AlmacenamientoEscritura (solo guardar).
  [SOLID-D] [U2-INYECCIÓN-DEPENDENCIAS]  recibe sistema y almacén ya creados.
  [U2-POLIMORFISMO-ABSTRACTAS] _mostrar_reporte() sirve para CUALQUIER Reporte.
  [PATRÓN: Prototype]          opción 14 (duplicar sesión).
"""
from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path

from modelos import DiaSemana, Reporte

from .almacenamiento import AlmacenamientoEscritura
from .sistema import SistemaAcademico


# ------------------------------------------------------------------ entrada
# Funciones que piden un dato y REPITEN la pregunta hasta que sea válido.
# Así el usuario no puede ingresar vacíos, letras donde van números, horas
# mal escritas, etc.
def leer_texto(mensaje: str) -> str:
    while True:
        valor = input(f"{mensaje}: ").strip()
        if valor:
            return valor
        print("  El campo no puede estar vacío.")


def leer_entero(mensaje: str, minimo: int = 1) -> int:
    while True:
        try:
            valor = int(input(f"{mensaje}: ").strip())
        except ValueError:  # no escribió un número
            print("  Ingrese un número entero.")
            continue
        if valor < minimo:
            print(f"  El valor debe ser al menos {minimo}.")
            continue
        return valor


def leer_hora(mensaje: str) -> time:
    while True:
        texto = input(f"{mensaje} (HH:MM): ").strip()
        try:
            return datetime.strptime(texto, "%H:%M").time()  # valida el formato
        except ValueError:
            print("  Formato inválido. Ejemplo: 07:30")


def leer_fecha(mensaje: str) -> date:
    while True:
        texto = input(f"{mensaje} (AAAA-MM-DD): ").strip()
        try:
            return date.fromisoformat(texto)
        except ValueError:
            print("  Formato inválido. Ejemplo: 2026-05-01")


def leer_si_no(mensaje: str) -> bool:
    while True:
        r = input(f"{mensaje} (s/n): ").strip().lower()
        if r in ("s", "si", "sí"):
            return True
        if r in ("n", "no"):
            return False
        print("  Responda 's' o 'n'.")


def leer_dia() -> DiaSemana:
    """Muestra los días numerados y devuelve el elegido."""
    dias = list(DiaSemana)
    for i, d in enumerate(dias, start=1):
        print(f"  {i}. {d.name.capitalize()}")
    while True:
        n = leer_entero("Día de la semana (número)")
        if n <= len(dias):
            return dias[n - 1]
        print(f"  Elija un número entre 1 y {len(dias)}.")


# --------------------------------------------------------------------- menú
class MenuConsola:
    def __init__(self, sistema: SistemaAcademico, almacen: AlmacenamientoEscritura,
                 carpeta_reportes: Path):
        # [U2-INYECCIÓN-DEPENDENCIAS] el menú RECIBE el sistema y el almacén ya
        # creados; no los crea él. Además 'almacen' es del tipo de la INTERFAZ:
        # funciona con cualquier clase que cumpla el contrato.
        # [SOLID-I] El tipo es AlmacenamientoEscritura (solo guardar): el menú no
        # depende de cargar(), que no usa. [SOLID-D] Depende de una abstracción.
        self._sistema = sistema
        self._almacen = almacen
        self._carpeta_reportes = Path(carpeta_reportes)
        # Diccionario: número de opción -> (texto del menú, método que se ejecuta).
        # Agregar una opción nueva es agregar una línea aquí.
        self._opciones = {
            "1": ("Registrar docente", self._registrar_docente),
            "2": ("Designar coordinador académico", self._designar_coordinador),
            "3": ("Crear período académico", self._crear_periodo),
            "4": ("Cerrar período activo", self._cerrar_periodo),
            "5": ("Registrar aula", self._registrar_aula),
            "6": ("Registrar asignatura", self._registrar_asignatura),
            "7": ("Crear sesión de clase", self._crear_sesion),
            "8": ("Aprobar o rechazar sesión", self._resolver_sesion),
            "9": ("Listar sesiones", self._listar_sesiones),
            "10": ("Ver horario de un docente", self._horario_docente),
            "11": ("Ver docentes, aulas, asignaturas y períodos", self._ver_registros),
            "12": ("Generar reporte de horarios", self._generar_reporte),
            # [NUEVO] Opciones 13 y 14: una opción nueva = una línea aquí. [SOLID-O]
            "13": ("Generar reporte de carga docente", self._generar_reporte_carga),
            "14": ("Duplicar una sesión a otro día", self._duplicar_sesion),
        }

    def ejecutar(self) -> None:
        """Bucle principal: muestra el menú y ejecuta la opción elegida."""
        while True:
            self._mostrar_menu()
            eleccion = input("Seleccione una opción: ").strip()
            if eleccion == "0":
                print("Datos guardados. ¡Hasta luego!")
                return
            opcion = self._opciones.get(eleccion)
            if opcion is None:
                print("\n  Opción inválida.")
                continue
            print(f"\n--- {opcion[0]} ---")
            try:
                opcion[1]()  # ejecuta el método asociado a la opción
            except (ValueError, PermissionError) as error:
                # Las reglas del sistema avisan con errores; aquí se muestran
                # como un mensaje y el programa sigue funcionando.
                print(f"\n  ✗ Error: {error}")

    def _mostrar_menu(self) -> None:
        print("\n" + "=" * 50)
        print("   KMDM ACADEMY SYSTEM - Gestor de horarios")
        print("=" * 50)
        for clave, (texto, _) in self._opciones.items():
            print(f"  {clave:>2}. {texto}")
        print("   0. Salir")

    def _guardar(self) -> None:
        """Se llama después de cada cambio: así los datos nunca se pierden."""
        self._almacen.guardar(self._sistema)

    # ------------------------------------------------------------- acciones
    # Todas siguen el mismo patrón: pedir datos -> llamar al sistema ->
    # guardar -> mostrar el resultado.
    def _registrar_docente(self) -> None:
        docente = self._sistema.registrar_docente(
            leer_texto("Nombre"), leer_texto("Apellido"), leer_texto("Correo"),
            leer_texto("Cédula"), leer_texto("Especialidad"),
            leer_entero("Horas máximas por semana"))
        self._guardar()
        print(f"\n  ✓ Docente registrado con ID {docente.id}: {docente.get_nombre_completo()}")

    def _designar_coordinador(self) -> None:
        self._imprimir_docentes()
        coord = self._sistema.designar_coordinador(
            leer_entero("ID del docente a designar"), leer_texto("Carrera que coordinará"))
        self._guardar()
        print(f"\n  ✓ {coord.get_nombre_completo()} ahora es coordinador de {coord.carrera}")

    def _crear_periodo(self) -> None:
        periodo = self._sistema.crear_periodo(
            leer_texto("Nombre del período (ej. 2026-2)"),
            leer_fecha("Fecha de inicio"), leer_fecha("Fecha de fin"))
        self._guardar()
        print(f"\n  ✓ Período {periodo.nombre} creado (ID {periodo.id}) y activo")

    def _cerrar_periodo(self) -> None:
        periodo = self._sistema.periodo_activo()
        if leer_si_no(f"¿Cerrar el período {periodo.nombre}?"):
            self._sistema.cerrar_periodo_activo()
            self._guardar()
            print(f"\n  ✓ Período {periodo.nombre} cerrado")

    def _registrar_aula(self) -> None:
        codigo = leer_texto("Código del aula (ej. A-101)")
        nombre = leer_texto("Nombre")
        capacidad = leer_entero("Capacidad (estudiantes)")
        ubicacion = leer_texto("Ubicación")
        print("Clasificaciones:")
        for c in self._sistema.clasificaciones:
            print(f"  {c.id}. {c.nombre} - {c.descripcion}")
        aula = self._sistema.registrar_aula(
            codigo, nombre, capacidad, ubicacion, leer_entero("ID de la clasificación"))
        self._guardar()
        print(f"\n  ✓ Aula {aula.codigo} registrada ({aula.clasificacion.nombre})")

    def _registrar_asignatura(self) -> None:
        asignatura = self._sistema.registrar_asignatura(
            leer_texto("Código (ej. POO)"), leer_texto("Nombre"), leer_entero("Nivel"),
            leer_entero("Horas de teoría", 0), leer_entero("Horas de práctica", 0))
        self._guardar()
        print(f"\n  ✓ Asignatura registrada: {asignatura}")

    def _crear_sesion(self) -> None:
        self._sistema.periodo_activo()  # falla pronto si no hay período, antes de pedir datos
        # Se muestran los registros disponibles para que el usuario elija bien.
        self._imprimir_docentes()
        self._imprimir_aulas()
        self._imprimir_asignaturas()
        dia = leer_dia()
        sesion = self._sistema.crear_sesion(
            dia, leer_hora("Hora de inicio"), leer_hora("Hora de fin"),
            leer_entero("Cupo de estudiantes"), leer_texto("Código de la asignatura"),
            leer_entero("ID del docente"), leer_texto("Código del aula"))
        self._guardar()
        print(f"\n  ✓ Sesión {sesion.id} creada en BORRADOR: {sesion}")

    def _resolver_sesion(self) -> None:
        pendientes = self._sistema.sesiones_pendientes()
        if not pendientes:
            print("  No hay sesiones pendientes (en BORRADOR).")
            return
        for s in pendientes:
            print(f"  [{s.id}] {s}")
        id_sesion = leer_entero("ID de la sesión")
        id_coord = self._elegir_coordinador()
        if leer_si_no("¿Aprobar la sesión? (n = rechazarla)"):
            sesion = self._sistema.aprobar_sesion(id_sesion, id_coord)
            print(f"\n  ✓ Sesión {sesion.id} APROBADA")
        else:
            sesion = self._sistema.rechazar_sesion(
                id_sesion, id_coord, leer_texto("Motivo del rechazo"))
            print(f"\n  ✓ Sesión {sesion.id} RECHAZADA: {sesion.motivo_rechazo}")
        self._guardar()

    def _listar_sesiones(self) -> None:
        sesiones = sorted(self._sistema.sesiones, key=lambda s: (s.dia.value, s.hora_inicio))
        if not sesiones:
            print("  No hay sesiones registradas.")
        for s in sesiones:
            extra = f"  (motivo: {s.motivo_rechazo})" if s.motivo_rechazo else ""
            print(f"  [{s.id}] {s}{extra}")

    def _horario_docente(self) -> None:
        self._imprimir_docentes()
        docente = self._sistema.buscar_docente(leer_entero("ID del docente"))
        sesiones = self._sistema.sesiones_de(docente.id)
        print(f"\nHorario de {docente.get_nombre_completo()} "
              f"({docente.horas_asignadas}/{docente.horas_max_semana} h aprobadas)")
        if not sesiones:
            print("  Sin sesiones registradas.")
        for s in sesiones:
            print(f"  [{s.id}] {s}")

    def _ver_registros(self) -> None:
        print("DOCENTES")
        self._imprimir_docentes()
        print("\nAULAS")
        self._imprimir_aulas()
        print("\nASIGNATURAS")
        self._imprimir_asignaturas()
        print("\nPERÍODOS")
        if not self._sistema.periodos:
            print("  (sin registros)")
        for p in self._sistema.periodos:
            estado = "ACTIVO" if p.activo else "cerrado"
            print(f"  {p.id}. {p.nombre} ({p.fecha_inicio} a {p.fecha_fin}) - {estado}")

    def _generar_reporte(self) -> None:
        id_coord = self._elegir_coordinador()
        periodos = self._sistema.periodos
        if not periodos:
            raise ValueError("No hay períodos registrados")
        if len(periodos) == 1:
            id_periodo = periodos[0].id  # si hay uno solo, no se pregunta
        else:
            for p in periodos:
                print(f"  {p.id}. {p.nombre}")
            id_periodo = leer_entero("ID del período")
        self._mostrar_reporte(self._sistema.generar_reporte(id_coord, id_periodo))

    def _generar_reporte_carga(self) -> None:
        """[NUEVO] Otro tipo de reporte; se muestra con el MISMO código de arriba."""
        self._mostrar_reporte(self._sistema.generar_reporte_carga(self._elegir_coordinador()))

    def _mostrar_reporte(self, reporte: Reporte) -> None:
        """[U2-POLIMORFISMO-ABSTRACTAS] Recibe un 'Reporte' (clase abstracta) y no
        sabe si es de horarios o de carga docente: imprimir() y exportar() se
        comportan según el objeto real. [SOLID-O] Un reporte nuevo no cambia esto."""
        print()
        reporte.imprimir()
        if leer_si_no("\n¿Guardar el reporte como archivo CSV?"):
            self._carpeta_reportes.mkdir(parents=True, exist_ok=True)
            ruta = self._carpeta_reportes / f"reporte_{reporte.id}.{reporte.extension_de('csv')}"
            ruta.write_text(reporte.exportar("csv"), encoding="utf-8")
            print(f"  ✓ Guardado en {ruta}")

    def _duplicar_sesion(self) -> None:
        """[NUEVO] [PATRÓN: Prototype] Copia una sesión a otro día sin volver a
        escribir sus datos."""
        sesiones = sorted(self._sistema.sesiones, key=lambda s: (s.dia.value, s.hora_inicio))
        if not sesiones:
            print("  No hay sesiones para duplicar.")
            return
        for s in sesiones:
            print(f"  [{s.id}] {s}")
        id_sesion = leer_entero("ID de la sesión a duplicar")
        dia = leer_dia()
        inicio = fin = None
        if leer_si_no("¿Cambiar también las horas?"):
            inicio, fin = leer_hora("Hora de inicio"), leer_hora("Hora de fin")
        clon = self._sistema.duplicar_sesion(id_sesion, dia, inicio, fin)
        self._guardar()
        print(f"\n  ✓ Sesión {clon.id} creada en BORRADOR (copia de {id_sesion}): {clon}")

    # ------------------------------------------------------------- ayudas
    def _elegir_coordinador(self) -> int:
        """Si hay un solo coordinador lo usa; si hay varios, pregunta cuál."""
        coordinadores = self._sistema.coordinadores
        if not coordinadores:
            raise ValueError("No hay coordinadores. Designe uno primero (opción 2)")
        if len(coordinadores) == 1:
            c = coordinadores[0]
            print(f"  Coordinador: {c.get_nombre_completo()} ({c.carrera})")
            return c.id
        for c in coordinadores:
            print(f"  {c.id}. {c.get_nombre_completo()} ({c.carrera})")
        return leer_entero("ID del coordinador")

    def _imprimir_docentes(self) -> None:
        if not self._sistema.docentes:
            print("  (sin docentes registrados)")
        for d in self._sistema.docentes:
            # get_rol() muestra DOCENTE o COORDINADOR según el objeto. [POLIMORFISMO]
            print(f"  {d.id}. {d.get_nombre_completo()} - {d.especialidad} "
                  f"[{d.get_rol()}] {d.horas_asignadas}/{d.horas_max_semana} h")

    def _imprimir_aulas(self) -> None:
        if not self._sistema.aulas:
            print("  (sin aulas registradas)")
        for a in self._sistema.aulas:
            print(f"  {a.codigo} - {a.nombre}, cap. {a.capacidad} ({a.clasificacion.nombre})")

    def _imprimir_asignaturas(self) -> None:
        if not self._sistema.asignaturas:
            print("  (sin asignaturas registradas)")
        for a in self._sistema.asignaturas:
            print(f"  {a.codigo} - {a.nombre} (teoría {a.horas_teoria} h, "
                  f"práctica {a.horas_practica} h)")

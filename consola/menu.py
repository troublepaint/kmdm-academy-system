"""MENÚ DE CONSOLA: una VISTA de texto del patrón MVP.  [MODIFICADO: antes estaba en servicios/menu.py]

[MVP] Esta clase es una vista PASIVA, igual que las pantallas de tkinter:
  * Pide datos al usuario (input) y los entrega al PRESENTADOR correspondiente.
  * El presentador llama al modelo, maneja los errores, guarda y le devuelve a esta
    vista lo que hay que mostrar (mostrar_filas, mostrar_mensaje, mostrar_error...).
  * Aquí NO se decide ninguna regla del negocio y NO se llama a SistemaAcademico.

[REFACTOR] ¿Qué código repetido se eliminó?
  * Elegir coordinador, ordenar sesiones, validar que existan datos antes de crear una
    sesión, guardar después de cada cambio, mostrar el reporte y exportarlo a CSV: todo
    eso estaba escrito aquí Y en la interfaz gráfica. Ahora lo hacen los presentadores.
  * _imprimir_docentes / _imprimir_aulas / _imprimir_asignaturas y el listado de sesiones
    se reemplazaron por UN solo método: mostrar_filas() (el presentador prepara las filas).
  * leer_dia() se reemplazó por elegir(), que sirve para cualquier lista de opciones.

[U2-POLIMORFISMO-INTERFACES] MenuConsola IMPLEMENTA las interfaces IVistaTabla e
    IVistaReportes: los presentadores la usan igual que a una ventana, sin saberlo.
[SOLID-S] Solo pide datos y muestra resultados.
[SOLID-I] Depende de AlmacenamientoEscritura (solo guardar).
[SOLID-D] [U2-INYECCIÓN-DEPENDENCIAS] Recibe sistema y almacén ya creados (main.py).
[SOLID-O] Agregar una opción nueva = agregar una línea al diccionario de opciones.
[PATRÓN: Prototype] opción 14 (duplicar sesión).
"""
from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Optional, Sequence

from presentadores import (Fila, IVistaReportes, IVistaTabla, PresentadorAsignaturas,
                           PresentadorAulas, PresentadorDocentes, PresentadorPeriodos,
                           PresentadorReportes, PresentadorSesiones)
from servicios import AlmacenamientoEscritura, SistemaAcademico


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


def leer_entero(mensaje: str, minimo: int = 1, maximo: Optional[int] = None) -> int:
    while True:
        try:
            valor = int(input(f"{mensaje}: ").strip())
        except ValueError:  # no escribió un número
            print("  Ingrese un número entero.")
            continue
        if valor < minimo or (maximo is not None and valor > maximo):
            print(f"  El valor debe estar entre {minimo} y {maximo}." if maximo is not None
                  else f"  El valor debe ser al menos {minimo}.")
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


# --------------------------------------------------------------------- menú
class MenuConsola(IVistaTabla, IVistaReportes):
    def __init__(self, sistema: SistemaAcademico, almacen: AlmacenamientoEscritura,
                 carpeta_reportes: Path):
        # [U2-INYECCIÓN-DEPENDENCIAS] el menú RECIBE el sistema y el almacén ya
        # creados; no los crea él. 'almacen' es del tipo de la INTERFAZ
        # AlmacenamientoEscritura [SOLID-I]: el menú solo necesita guardar.
        self._carpeta_reportes = Path(carpeta_reportes)
        # [MVP] Un presentador por cada grupo de opciones. La vista que reciben es
        # ESTE menú (self): los presentadores no saben que están en una consola.
        deps = {"guardar": lambda: almacen.guardar(sistema)}   # se guarda después de cada cambio
        self._docentes = PresentadorDocentes(self, sistema, **deps)
        self._aulas = PresentadorAulas(self, sistema, **deps)
        self._asignaturas = PresentadorAsignaturas(self, sistema, **deps)
        self._periodos = PresentadorPeriodos(self, sistema, **deps)
        self._sesiones = PresentadorSesiones(self, sistema, **deps)
        self._reportes = PresentadorReportes(self, sistema, **deps)
        # Diccionario: número de opción -> (texto del menú, método que se ejecuta).
        # Agregar una opción nueva es agregar una línea aquí. [SOLID-O]
        self._opciones = {
            "1": ("Registrar docente", self._registrar_docente),
            "2": ("Designar coordinador académico", self._designar_coordinador),
            "3": ("Crear período académico", self._crear_periodo),
            "4": ("Cerrar período activo", self._periodos.cerrar_activo),
            "5": ("Registrar aula", self._registrar_aula),
            "6": ("Registrar asignatura", self._registrar_asignatura),
            "7": ("Crear sesión de clase", self._crear_sesion),
            "8": ("Aprobar o rechazar sesión", self._resolver_sesion),
            "9": ("Listar sesiones", self._sesiones.cargar),
            "10": ("Ver horario de un docente", self._horario_docente),
            "11": ("Ver docentes, aulas, asignaturas y períodos", self._ver_registros),
            "12": ("Generar reporte de horarios", self._generar_reporte),
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
                # Red de seguridad: los presentadores ya muestran los errores del
                # modelo, pero si algo se escapa el programa sigue funcionando.
                self.mostrar_error(str(error))

    def _mostrar_menu(self) -> None:
        print("\n" + "=" * 50)
        print("   KMDM ACADEMY SYSTEM - Gestor de horarios")
        print("=" * 50)
        for clave, (texto, _) in self._opciones.items():
            print(f"  {clave:>2}. {texto}")
        print("   0. Salir")

    # ============================================================ IVista... (lo que piden los presentadores)
    def mostrar_mensaje(self, texto: str) -> None:
        print(f"\n  ✓ {texto}")

    def mostrar_error(self, texto: str) -> None:
        print(f"\n  ✗ Error: {texto}")

    def avisar(self, texto: str) -> None:
        print(f"  ! {texto}")

    def confirmar(self, pregunta: str) -> bool:
        return leer_si_no(pregunta)

    def elegir(self, titulo: str, opciones: Sequence[tuple[str, Any]]) -> Optional[Any]:
        """Muestra las opciones numeradas y devuelve el VALOR de la elegida."""
        if not opciones:
            return None
        print(f"{titulo}")
        for i, (texto, _) in enumerate(opciones, start=1):
            print(f"  {i}. {texto}")
        n = leer_entero("Número", 1, len(opciones))
        return opciones[n - 1][1]

    def pedir_texto(self, titulo: str, etiqueta: str) -> Optional[str]:
        return leer_texto(etiqueta)

    def mostrar_filas(self, filas: Sequence[Fila]) -> None:
        """Las mismas filas que ve la tabla de la ventana, pero como texto."""
        if not filas:
            print("  (sin registros)")
        for _clave, valores, _estado in filas:
            print("  " + " | ".join(str(v) for v in valores if v not in ("", None)))

    def mostrar_periodos(self, periodos: Sequence[str], elegido: str) -> None:
        for nombre in periodos:
            print(f"  - {nombre}{'  (seleccionado)' if nombre == elegido else ''}")

    def mostrar_reporte(self, texto: str) -> None:
        print()
        print(texto)

    # ============================================================ opciones del menú
    # Todas siguen el mismo patrón: pedir datos -> entregarlos al presentador.
    # Guardar y mostrar el resultado lo hace el presentador.
    def _registrar_docente(self) -> None:
        self._docentes.registrar(
            leer_texto("Nombre"), leer_texto("Apellido"), leer_texto("Correo"),
            leer_texto("Cédula"), leer_texto("Especialidad"),
            leer_entero("Horas máximas por semana"))

    def _designar_coordinador(self) -> None:
        self._docentes.cargar()                       # muestra la lista de docentes
        if self._docentes.hay_docentes():
            self._docentes.designar_coordinador(leer_entero("ID del docente a designar"),
                                                leer_texto("Carrera que coordinará"))

    def _crear_periodo(self) -> None:
        self._periodos.crear(leer_texto("Nombre del período (ej. 2026-2)"),
                             leer_fecha("Fecha de inicio"), leer_fecha("Fecha de fin"))

    def _registrar_aula(self) -> None:
        codigo = leer_texto("Código del aula (ej. A-101)")
        nombre = leer_texto("Nombre")
        capacidad = leer_entero("Capacidad (estudiantes)")
        ubicacion = leer_texto("Ubicación")
        tipo = self.elegir("Tipo de aula:", self._aulas.opciones_clasificacion())
        self._aulas.registrar(codigo, nombre, capacidad, ubicacion, tipo)

    def _registrar_asignatura(self) -> None:
        self._asignaturas.registrar(
            leer_texto("Código (ej. POO)"), leer_texto("Nombre"), leer_entero("Nivel"),
            leer_entero("Horas de teoría", 0), leer_entero("Horas de práctica", 0))

    def _crear_sesion(self) -> None:
        if self._sesiones.faltan_datos():   # avisa ANTES de pedir datos (misma regla que la ventana)
            return
        op = self._sesiones.opciones_formulario()
        dia = self.elegir("Día de la semana:", op["dia"])
        inicio, fin = leer_hora("Hora de inicio"), leer_hora("Hora de fin")
        cupo = leer_entero("Cupo de estudiantes")
        asignatura = self.elegir("Asignatura:", op["asignatura"])
        docente = self.elegir("Docente:", op["docente"])
        aula = self.elegir("Aula:", op["aula"])
        self._sesiones.crear(dia, inicio, fin, cupo, asignatura, docente, aula)

    def _resolver_sesion(self) -> None:
        if not self._sesiones.hay_pendientes():
            print("  No hay sesiones pendientes (en BORRADOR).")
            return
        self._sesiones.cargar_pendientes()
        id_sesion = leer_entero("ID de la sesión")
        if leer_si_no("¿Aprobar la sesión? (n = rechazarla)"):
            self._sesiones.aprobar(id_sesion)
        else:
            self._sesiones.rechazar(id_sesion)        # el presentador pide el motivo

    def _horario_docente(self) -> None:
        self._docentes.cargar()
        if self._docentes.hay_docentes():
            self._sesiones.cargar_de_docente(leer_entero("ID del docente"))

    def _ver_registros(self) -> None:
        for titulo, presentador in (("DOCENTES", self._docentes), ("AULAS", self._aulas),
                                    ("ASIGNATURAS", self._asignaturas), ("PERÍODOS", self._periodos)):
            print(f"\n{titulo}")
            presentador.cargar()   # [U2-POLIMORFISMO] mismo mensaje, cada uno arma sus filas

    def _generar_reporte(self) -> None:
        nombres = self._reportes.nombres_periodos()
        if len(nombres) > 1:      # si hay uno solo (o ninguno), no se pregunta
            nombre = self.elegir("Período:", [(n, n) for n in nombres])
        else:
            nombre = nombres[0] if nombres else ""
        if self._reportes.generar(PresentadorReportes.HORARIO, nombre):
            self._ofrecer_csv()

    def _generar_reporte_carga(self) -> None:
        """Otro tipo de reporte; se muestra y se exporta con el MISMO código."""
        if self._reportes.generar(PresentadorReportes.CARGA):
            self._ofrecer_csv()

    def _ofrecer_csv(self) -> None:
        if leer_si_no("\n¿Guardar el reporte como archivo CSV?"):
            nombre = self._reportes.nombre_archivo()
            if nombre:
                self._reportes.exportar_csv(self._carpeta_reportes / nombre)

    def _duplicar_sesion(self) -> None:
        """[PATRÓN: Prototype] Copia una sesión a otro día sin volver a escribir sus datos."""
        if not self._sesiones.hay_sesiones():
            print("  No hay sesiones para duplicar.")
            return
        self._sesiones.cargar()
        id_sesion = leer_entero("ID de la sesión a duplicar")
        dia = self.elegir("Nuevo día:", self._sesiones.opciones_formulario()["dia"])
        inicio = fin = None
        if leer_si_no("¿Cambiar también las horas?"):
            inicio, fin = leer_hora("Hora de inicio"), leer_hora("Hora de fin")
        self._sesiones.duplicar(id_sesion, dia, inicio, fin)

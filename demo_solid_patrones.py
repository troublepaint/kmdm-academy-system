"""DEMOSTRACIÓN de SOLID, patrones de diseño y temas de la Unidad 2.  [NUEVO]

Ejecutar desde esta carpeta:  python demo_solid_patrones.py

No usa menú ni archivos. Cada bloque dice qué se está demostrando y muestra
casos válidos e inválidos (marcados con [bloqueado]).
"""
from __future__ import annotations

from datetime import date, time

from main import crear_sistema
from modelos import (ConfiguracionSistema, CoordinadorAcademico, DiaSemana,
                     Docente, Exportador, ExportadorCsv, ExportadorTxt, Reporte, ReporteCargaDocente,
                     ReporteHorario, SesionClase, Usuario, creador_para)
from servicios import (AlmacenJSON, AlmacenMemoria, Almacenamiento,
                       AlmacenamientoEscritura, ReglaSesion, SistemaAcademico)


def titulo(t: str) -> None:
    print(f"\n{'=' * 72}\n{t}\n{'=' * 72}")


def intentar(descripcion: str, accion) -> None:
    """Ejecuta 'accion' y muestra el error esperado (casos inválidos)."""
    try:
        accion()
    except (ValueError, TypeError, PermissionError) as e:
        print(f"  [bloqueado] {descripcion}: {e}")
    else:
        raise AssertionError(f"Debía fallar: {descripcion}")


# ---------------------------------------------------------------------------
# [SOLID-O] Extensiones escritas AQUÍ, sin editar ni una línea del sistema:
# ---------------------------------------------------------------------------
class ReglaMaxSesionesPorDia(ReglaSesion):
    """Regla NUEVA: un docente no puede tener más de N sesiones el mismo día.
    [U2-POLIMORFISMO-INTERFACES] implementa la interfaz ReglaSesion."""

    def __init__(self, maximo: int):
        self._maximo = maximo

    def validar(self, sesion, existentes) -> None:
        del_dia = [s for s in existentes
                   if s.docente.id == sesion.docente.id and s.dia == sesion.dia
                   and s.periodo.id == sesion.periodo.id]
        if len(del_dia) >= self._maximo:
            raise ValueError(f"{sesion.docente.get_nombre_completo()} ya tiene "
                             f"el máximo de {self._maximo} sesión(es) el {sesion.dia.name}")


class ExportadorMarkdown(Exportador):
    """Formato NUEVO de exportación. [U2-POLIMORFISMO-INTERFACES] [PATRÓN: Strategy]"""

    @property
    def formato(self) -> str:
        return "md"

    @property
    def extension(self) -> str:
        return "md"

    def exportar(self, titulo, encabezados, filas) -> str:
        lineas = [f"# {titulo}", "", "| " + " | ".join(encabezados) + " |",
                  "|" + "---|" * len(encabezados)]
        lineas += ["| " + " | ".join(map(str, f)) + " |" for f in filas]
        return "\n".join(lineas)


def main() -> None:
    # ------------------------------------------------------------------ preparación
    sistema = crear_sistema()
    admin = sistema.administrador
    periodo = sistema.crear_periodo("2026-2", date(2026, 5, 1), date(2026, 10, 31))

    # ----------------------------------------------------- PATRÓN: Factory Method
    titulo("PATRÓN Factory Method - creación de usuarios por rol (sin if/else)")
    filas = [
        {"tipo": "DOCENTE", "id": 1, "nombre": "Ana", "apellido": "Pérez",
         "correo": "ana@uleam.edu.ec", "cedula": "1312345678",
         "especialidad": "Software", "horas_max_semana": 20},
        {"tipo": "COORDINADOR", "id": 2, "nombre": "Luis", "apellido": "Mora",
         "correo": "luis@uleam.edu.ec", "cedula": "1398765432",
         "especialidad": "Redes", "horas_max_semana": 12, "carrera": "Software"},
    ]
    for fila in filas:
        u = creador_para(fila["tipo"]).registrar(admin, fila)
        print(f"  {u.get_nombre_completo():<10} -> {type(u).__name__} ({u.get_rol()})")
    ana, luis = sistema.buscar_docente(1), sistema.buscar_docente(2)
    intentar("rol sin creador", lambda: creador_para("DECANO"))

    sistema.registrar_aula("A-101", "Aula 101", 35, "Bloque A", 1)
    sistema.registrar_aula("L-01", "Lab Informática", 25, "Bloque B", 2)
    sistema.registrar_asignatura("POO", "Programación Orientada a Objetos", 3, 3, 2)
    sistema.registrar_asignatura("RED", "Redes I", 3, 4, 0)

    # --------------------------------------------------------- PATRÓN: Builder
    titulo("PATRÓN Builder - SistemaAcademico.crear_sesion() arma la sesión paso a paso")
    s1 = sistema.crear_sesion(DiaSemana.LUNES, time(7, 0), time(9, 0), 30, "POO", 1, "A-101")
    s2 = sistema.crear_sesion(DiaSemana.MARTES, time(10, 0), time(12, 0), 20, "POO", 1, "L-01")
    print("  ", s1, "\n  ", s2)

    # ------------------------------------------------- PATRÓN: Singleton + SOLID-S/O
    titulo("PATRÓN Singleton + reglas (SOLID-O / U2 interfaces)")
    cfg_a, cfg_b = ConfiguracionSistema(), ConfiguracionSistema.obtener_instancia()
    print("  ¿Misma configuración global?", cfg_a is cfg_b)
    intentar("clase a las 05:00 (ReglaHorarioAtencion)", lambda: sistema.crear_sesion(
        DiaSemana.JUEVES, time(5, 0), time(7, 0), 20, "POO", 1, "A-101"))
    intentar("conflicto del mismo docente", lambda: sistema.crear_sesion(
        DiaSemana.LUNES, time(8, 0), time(10, 0), 20, "POO", 1, "A-101"))
    intentar("aula pequeña (ReglaCapacidadAula)", lambda: sistema.crear_sesion(
        DiaSemana.VIERNES, time(7, 0), time(9, 0), 60, "POO", 1, "A-101"))
    intentar("práctica en aula incompatible (valida SesionClase)", lambda: sistema.crear_sesion(
        DiaSemana.VIERNES, time(7, 0), time(9, 0), 20, "RED", 1, "L-01"))

    titulo("SOLID-O - regla NUEVA agregada sin editar SistemaAcademico")
    # [U2-INYECCIÓN-DEPENDENCIAS] Se entrega SOLO la regla nueva al sistema.
    sistema_estricto = SistemaAcademico(
        reglas=[ReglaMaxSesionesPorDia(1)], con_clasificaciones_base=True)
    sistema_estricto.crear_periodo("2026-2", date(2026, 5, 1), date(2026, 10, 31))
    sistema_estricto.registrar_docente("Ana", "Pérez", "ana@uleam.edu.ec", "1312345678", "Software", 20)
    sistema_estricto.registrar_aula("A-101", "Aula 101", 35, "Bloque A", 1)
    sistema_estricto.registrar_asignatura("POO", "POO", 3, 3, 2)
    sistema_estricto.crear_sesion(DiaSemana.LUNES, time(7, 0), time(9, 0), 20, "POO", 1, "A-101")
    intentar("2.ª sesión el mismo día (regla nueva)", lambda: sistema_estricto.crear_sesion(
        DiaSemana.LUNES, time(10, 0), time(12, 0), 20, "POO", 1, "A-101"))

    # ------------------------------------------------------- PATRÓN: Prototype
    titulo("PATRÓN Prototype - duplicar_sesion() clona sesiones")
    luis.aprobar_sesion(s1)
    c1 = sistema.duplicar_sesion(s1.id, DiaSemana.MIERCOLES)
    c2 = sistema.duplicar_sesion(s1.id, DiaSemana.VIERNES, time(9, 0), time(11, 0))
    print("  original:", s1.estado.name, "| copias:", c1.estado.name, c2.estado.name)
    assert c1.estado.name == "BORRADOR" and c1.docente is s1.docente
    intentar("duplicar sobre un conflicto", lambda: sistema.duplicar_sesion(s1.id, DiaSemana.LUNES))

    # --------------------------------- U2: herencia, clases abstractas, SOLID-L
    titulo("U2 HERENCIA + CLASES ABSTRACTAS + SOLID-L (Liskov)")
    intentar("instanciar la clase abstracta Usuario", lambda: Usuario(9, "X", "Y", "x@y.com"))
    intentar("instanciar la clase abstracta Reporte", lambda: Reporte("x"))
    print("  ¿Luis es Docente?", isinstance(luis, Docente),
          "| ¿es CoordinadorAcademico?", isinstance(luis, CoordinadorAcademico))

    def horas_libres(d: Docente) -> float:
        # Pide un Docente y funciona con un Coordinador sin cambios. [SOLID-L]
        return d.horas_max_semana - d.horas_asignadas

    print("  Horas libres (Docente / Coordinador):", horas_libres(ana), horas_libres(luis))

    # ------------------------------------------ U2: polimorfismo con reportes
    titulo("U2 POLIMORFISMO con clase abstracta - lista de 'Reporte'")
    reportes: list[Reporte] = [luis.generar_reporte(periodo, list(sistema.sesiones)),
                               luis.generar_reporte_carga(sistema.docentes)]
    for r in reportes:  # mismo código para dos tipos de reporte
        print(f"\n[{type(r).__name__}]")
        r.imprimir()

    # ----------------------------- U2: polimorfismo con interfaces (exportadores)
    titulo("U2 POLIMORFISMO con interfaces + Strategy - exportadores intercambiables")
    reporte = ReporteHorario("Horario Software", sistema.sesiones,
                             exportadores=[ExportadorTxt(), ExportadorCsv(), ExportadorMarkdown()])
    reporte.generar()
    print("  Formatos disponibles:", reporte.formatos)
    print(reporte.exportar("md"))
    intentar("formato inexistente", lambda: reporte.exportar("pdf"))

    # ---------------------------- U2: inyección de dependencias + SOLID-I/D
    titulo("U2 INYECCIÓN DE DEPENDENCIAS + SOLID-I/D - almacenes intercambiables")
    for almacen in (AlmacenMemoria(),):
        almacen.guardar(sistema)
        print(f"  {type(almacen).__name__} es Almacenamiento:", isinstance(almacen, Almacenamiento),
              "| es AlmacenamientoEscritura:", isinstance(almacen, AlmacenamientoEscritura))
    print("  ¿Recupera el mismo sistema?", almacen.cargar() is sistema)
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as carpeta:
        json_ = AlmacenJSON(Path(carpeta) / "datos.json", fabrica_sistema=crear_sistema)
        json_.guardar(sistema)
        recargado = json_.cargar()
        print("  JSON -> sesiones guardadas/recargadas:",
              len(sistema.sesiones), "/", len(recargado.sesiones),
              "| roles:", [u.get_rol() for u in recargado.docentes])
        assert len(recargado.sesiones) == len(sistema.sesiones)

    print("\nTodo correcto: SOLID, patrones y Unidad 2 demostrados.")


if __name__ == "__main__":
    main()

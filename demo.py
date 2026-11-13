"""Demostración con datos FIJOS del KMDM Academy System (sin menú ni archivos).

Ejecutar desde esta carpeta:  python demo.py

Sirve para ver de un vistazo cómo trabajan juntas las clases del diagrama:
el administrador prepara el sistema, se proponen sesiones, el coordinador
las revisa y se genera el reporte.
"""
from datetime import date, time

from modelos import (Administrador, Asignatura, Aula, AulaClasificacion,
                     DiaSemana, Docente, EstadoSesion, SesionClase)


def main() -> None:
    # 1. El administrador prepara el sistema ---------------------------------
    admin = Administrador(100, "Root", "Admin", "admin@uleam.edu.ec", "ADM-001")
    periodo = admin.crear_periodo("2026-2", date(2026, 5, 1), date(2026, 10, 31))

    ana = Docente(1, "Ana", "Pérez", "ana@uleam.edu.ec", "1312345678", "Software", 20)
    luis = Docente(2, "Luis", "Mora", "luis@uleam.edu.ec", "1398765432", "Redes", 12)
    admin.registrar_usuario(ana)
    admin.registrar_usuario(luis)
    # Luis pasa a ser coordinador (se crea un objeto CoordinadorAcademico nuevo).
    coord = admin.designar_coordinador(luis, "Software")
    print(f"{coord.get_nombre_completo()} es {coord.get_rol()} de {coord.carrera}")

    comun = AulaClasificacion(1, "Común", "Aula de clases teóricas")
    lab = AulaClasificacion(2, "Laboratorio", "Equipado con computadores", True)
    a101 = Aula("A-101", "Aula 101", 35, "Bloque A", comun)
    l01 = Aula("L-01", "Lab Informática", 25, "Bloque B", lab)
    admin.registrar_aula(a101)
    admin.registrar_aula(l01)

    poo = Asignatura("POO", "Programación Orientada a Objetos", 3, 3, 2)
    redes = Asignatura("RED", "Redes I", 3, 4, 0)
    admin.registrar_asignatura(poo)
    admin.registrar_asignatura(redes)

    # 2. Se proponen sesiones (quedan en BORRADOR) ---------------------------
    s1 = SesionClase(1, DiaSemana.LUNES, time(7, 0), time(9, 0), 30, poo, ana, a101, periodo)
    s2 = SesionClase(2, DiaSemana.LUNES, time(8, 0), time(10, 0), 25, poo, ana, l01, periodo)
    s3 = SesionClase(3, DiaSemana.MARTES, time(10, 0), time(12, 0), 30, redes, coord, a101, periodo)
    sesiones = [s1, s2, s3]

    # s1 y s2 son del mismo docente y se cruzan en horario: hay conflicto.
    print("\n¿s1 y s2 se solapan?     ", s1.se_solapa_con(s2))
    print("¿s1 y s2 tienen conflicto?", s1.hay_conflicto_con(s2), "(mismo docente)")
    print("¿s2 cumple capacidad?     ", s2.cumple_capacidad())

    # 3. El coordinador revisa ------------------------------------------------
    coord.aprobar_sesion(s1)
    coord.rechazar_sesion(s2, "Choca con otra sesión de la misma docente")
    try:
        coord.aprobar_sesion(s3)  # s3 es del propio coordinador: no se permite
    except PermissionError as e:
        print("\nBloqueado:", e)
    print(f"\ns1: {s1.estado.name} | s2: {s2.estado.name} ({s2.motivo_rechazo}) | "
          f"s3: {s3.estado.name}")
    print(f"Horas de Ana: {ana.horas_asignadas}/{ana.horas_max_semana}")

    # 4. Reporte ----------------------------------------------------------------
    reporte = coord.generar_reporte(periodo, sesiones)
    print()
    reporte.imprimir()
    print("\n--- CSV ---")
    print(reporte.exportar("csv"))
    assert s1.estado == EstadoSesion.APROBADA  # comprobación automática final


if __name__ == "__main__":
    main()

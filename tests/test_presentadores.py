"""PRUEBAS de los presentadores SIN abrir ninguna ventana.  [NUEVO] [MVP]

Esta es la ventaja principal de MVP: como el presentador no depende de tkinter, se le
entrega una VISTA FALSA que solo anota lo que el presentador le pide mostrar, y luego se
revisa esa anotación.

Ejecutar desde la carpeta kmdm_academy:
    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # para importar los paquetes

from main import crear_sistema                                    # noqa: E402
from modelos import DiaSemana                                     # noqa: E402
from presentadores import (IVistaHorario, IVistaReportes, IVistaTabla,  # noqa: E402
                           PresentadorDocentes, PresentadorHorario, PresentadorPeriodos,
                           PresentadorReportes, PresentadorSesiones)
from presentadores.comun import periodo_a_mostrar, validar_repeticion   # noqa: E402
from presentadores.paneles import BloqueHorario, asignar_carriles      # noqa: E402


class VistaFalsa(IVistaTabla, IVistaReportes, IVistaHorario):
    """[U2-POLIMORFISMO-INTERFACES] Cumple las interfaces de vista, pero en lugar de dibujar
    guarda todo en listas. 'respuestas' simula lo que contestaría el usuario."""

    def __init__(self, confirmar=True, elegir=None, texto="Motivo de prueba"):
        self.mensajes, self.errores, self.avisos, self.filas, self.reportes = [], [], [], [], []
        self.bloques = []
        self._confirmar, self._elegir, self._texto = confirmar, elegir, texto

    def mostrar_mensaje(self, texto): self.mensajes.append(texto)
    def mostrar_error(self, texto): self.errores.append(texto)
    def avisar(self, texto): self.avisos.append(texto)
    def confirmar(self, pregunta): return self._confirmar
    def elegir(self, titulo, opciones): return self._elegir if self._elegir is not None else opciones[0][1]
    def pedir_texto(self, titulo, etiqueta): return self._texto
    def mostrar_filas(self, filas): self.filas = list(filas)
    def mostrar_periodos(self, periodos, elegido): self.periodo_elegido = elegido
    def mostrar_reporte(self, texto): self.reportes.append(texto)
    def mostrar_filtros(self, docentes, periodos, docente, periodo, docente_fijo): self.filtros = (docente, periodo)
    def dibujar_horario(self, bloques, hora_inicio, hora_fin): self.bloques, self.horas = list(bloques), (hora_inicio, hora_fin)


def sistema_con_datos():
    """Un sistema con 1 período, 2 docentes (uno coordinador), 1 aula y 1 asignatura."""
    s = crear_sistema()
    s.crear_periodo("2026-2", date(2026, 5, 1), date(2026, 10, 31))
    ana = s.registrar_docente("Ana", "Pérez", "ana@uleam.edu.ec", "1312345678", "Software", 20)
    luis = s.registrar_docente("Luis", "Mora", "luis@uleam.edu.ec", "1398765432", "Redes", 20)
    s.designar_coordinador(luis.id, "Software")
    s.registrar_aula("A-101", "Aula 101", 30, "Bloque A", 1)
    s.registrar_asignatura("POO", "Programación OO", 3, 3, 2)
    return s, ana


class PruebasSesiones(unittest.TestCase):
    def setUp(self):
        self.sistema, self.ana = sistema_con_datos()
        self.vista = VistaFalsa()
        self.guardados = []
        self.p = PresentadorSesiones(self.vista, self.sistema, guardar=lambda: self.guardados.append(1))

    def crear(self, inicio=time(7), fin=time(9)):
        return self.p.crear(DiaSemana.LUNES, inicio, fin, 25, "POO", self.ana.id, "A-101")

    def test_crear_sesion_guarda_y_avisa(self):
        self.assertTrue(self.crear())
        self.assertEqual(len(self.guardados), 1)              # se guardó una vez
        self.assertIn("creada en borrador", self.vista.mensajes[-1])

    def test_conflicto_muestra_error_y_no_guarda(self):
        self.crear()
        self.assertFalse(self.crear(time(8), time(10)))       # se cruza con la anterior
        self.assertEqual(len(self.vista.errores), 1)
        self.assertEqual(len(self.guardados), 1)              # el segundo intento NO se guardó

    def test_aprobar_usa_el_unico_coordinador(self):
        self.crear()
        self.assertTrue(self.p.aprobar(1))
        self.p.cargar("Aprobada")
        self.assertEqual(len(self.vista.filas), 1)

    def test_rechazar_pide_motivo_a_la_vista(self):
        self.crear()
        self.assertTrue(self.p.rechazar(1))
        self.p.cargar("Rechazada")
        self.assertIn("Motivo de prueba", self.vista.filas[0][1])

    def test_faltan_datos_sin_periodo(self):
        self.sistema.cerrar_periodo_activo()
        self.assertTrue(self.p.faltan_datos())
        self.assertTrue(self.vista.avisos)

    def test_filas_ordenadas_por_dia_y_hora(self):
        self.p.crear(DiaSemana.MARTES, time(7), time(9), 25, "POO", self.ana.id, "A-101")
        self.crear(time(10), time(12))
        self.p.cargar()
        self.assertEqual([f[1][1] for f in self.vista.filas], ["Lunes", "Martes"])


class PruebasRegistros(unittest.TestCase):
    def test_registrar_docente_muestra_el_id(self):
        s, _ = sistema_con_datos()
        vista = VistaFalsa()
        PresentadorDocentes(vista, s).registrar("Eva", "Ruiz", "eva@x.ec", "1300000000", "BD", 10)
        self.assertIn("ID 3", vista.mensajes[-1])

    def test_cerrar_periodo_respeta_la_confirmacion(self):
        s, _ = sistema_con_datos()
        self.assertFalse(PresentadorPeriodos(VistaFalsa(confirmar=False), s).cerrar_activo())
        self.assertEqual(s.periodo_activo().nombre, "2026-2")     # sigue abierto
        self.assertTrue(PresentadorPeriodos(VistaFalsa(confirmar=True), s).cerrar_activo())


class PruebasReportes(unittest.TestCase):
    def test_generar_y_exportar_csv(self):
        s, ana = sistema_con_datos()
        PresentadorSesiones(VistaFalsa(), s).crear(DiaSemana.LUNES, time(7), time(9), 25, "POO", ana.id, "A-101")
        vista = VistaFalsa()
        p = PresentadorReportes(vista, s)
        self.assertIsNone(p.nombre_archivo())                     # aún no hay reporte: avisa
        self.assertTrue(p.generar(PresentadorReportes.HORARIO, "2026-2"))
        self.assertIn("POO", vista.reportes[-1])
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / p.nombre_archivo()
            self.assertTrue(p.exportar_csv(ruta))
            self.assertIn("POO", ruta.read_text(encoding="utf-8-sig"))


class PruebasHorario(unittest.TestCase):
    def test_sesiones_que_se_cruzan_van_en_carriles_distintos(self):
        b = lambda i, h0, h1: BloqueHorario(i, DiaSemana.LUNES, time(h0), time(h1), "BORRADOR", (), "")
        carriles = {x.id: (x.carril, x.carriles) for x in asignar_carriles([b(1, 7, 9), b(2, 8, 10), b(3, 9, 11)])}
        self.assertEqual(carriles, {1: (0, 2), 2: (1, 2), 3: (0, 2)})

    def test_filtrar_por_docente(self):
        s, ana = sistema_con_datos()
        PresentadorSesiones(VistaFalsa(), s).crear(DiaSemana.LUNES, time(7), time(9), 25, "POO", ana.id, "A-101")
        vista = VistaFalsa()
        p = PresentadorHorario(vista, s)
        p.cargar()
        self.assertEqual(len(vista.bloques), 1)
        p.filtrar("Luis Mora", PresentadorHorario.TODOS)
        self.assertEqual(vista.bloques, [])


class PruebasFuncionesComunes(unittest.TestCase):
    def test_validar_repeticion(self):
        validar_repeticion("abc123", "abc123")
        with self.assertRaises(ValueError):
            validar_repeticion("abc123", "otra")

    def test_periodo_a_mostrar(self):
        s, _ = sistema_con_datos()
        self.assertEqual(periodo_a_mostrar(s, "", ["Todos", "2026-2"], "Todos"), "2026-2")  # el activo
        self.assertEqual(periodo_a_mostrar(s, "Todos", ["Todos", "2026-2"], "Todos"), "Todos")  # lo elegido


if __name__ == "__main__":
    unittest.main()

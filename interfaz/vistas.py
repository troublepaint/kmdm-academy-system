"""PANTALLAS (vistas) de la interfaz gráfica.  [NUEVO]

    VistaBase (clase ABSTRACTA)
    ├── VistaInicio        panel con totales y sesiones pendientes
    ├── VistaDocentes      registrar docentes y designar coordinadores
    ├── VistaAulas         registrar aulas y activar/desactivar
    ├── VistaAsignaturas   registrar asignaturas
    ├── VistaPeriodos      crear y cerrar períodos
    ├── VistaSesiones      crear, aprobar, rechazar y duplicar sesiones
    ├── VistaHorario       cuadrícula semanal (lunes a sábado) por colores
    └── VistaReportes      reporte de horario / carga docente y exportar CSV

[U2-HERENCIA] Todas las pantallas HEREDAN de VistaBase y reutilizan su
    encabezado, el manejo de errores y el guardado.
[U2-POLIMORFISMO-ABSTRACTAS] VistaBase es abstracta: obliga a cada pantalla a
    escribir _construir() (cómo se dibuja) y actualizar() (cómo se refresca).
    La ventana principal llama vista.actualizar() sin saber de qué pantalla es.
[PATRÓN: Template Method] VistaBase.__init__ define el esqueleto (encabezado ->
    _construir -> actualizar) y ejecutar() el de cada acción (intentar -> guardar
    -> refrescar todo -> avisar); las pantallas rellenan los pasos variables.
[U2-INYECCIÓN-DEPENDENCIAS] Cada pantalla RECIBE un Contexto (sistema, tema y
    funciones de guardar/navegar); no crea ni busca nada por su cuenta.
[PATRÓN: Facade] La interfaz solo habla con SistemaAcademico, nunca con las reglas
    internas. [SOLID-D] Depende de esa abstracción de alto nivel.
[SOLID-S] Las pantallas solo muestran datos y piden datos; TODAS las reglas
    (conflictos, capacidad, horario...) siguen en el sistema y se muestran como avisos.
"""
from __future__ import annotations

import tkinter as tk
from abc import ABC, abstractmethod
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional

from modelos import DiaSemana, Reporte
from servicios import (ADMINISTRADOR, COORDINADOR, DOCENTE, Autenticador, AutenticadorLocal,
                       Cuenta, EstadisticasHorario, SistemaAcademico)

from .componentes import Campo, Encabezado, Hero, Tabla, TarjetaDato, pedir_datos
from .graficos import GraficoBarras, GraficoDona, GraficoProgreso
from .imagenes import Imagenes
from .tema import COLOR_ESTADO, COLORES, Tema


@dataclass
class Contexto:
    """[U2-INYECCIÓN-DEPENDENCIAS] Todo lo que una pantalla necesita, entregado desde afuera."""
    sistema: SistemaAcademico
    tema: Tema
    guardar: Callable[[], None]
    notificar_cambio: Callable[[], None]   # refresca TODAS las pantallas
    mensaje: Callable[[str], None]         # texto de la barra inferior
    navegar: Callable[[str], None]         # cambia de pantalla por su clave
    cuenta: Cuenta = None                  # [NUEVO] quién inició sesión (rol y docente)
    imagenes: Imagenes = None              # [NUEVO] imágenes PNG ya cargadas
    autenticador: Autenticador = None      # [NUEVO] para crear cuentas y cambiar claves


# =================================================================== clase base
class VistaBase(ttk.Frame, ABC):
    """[U2-POLIMORFISMO-ABSTRACTAS] Plantilla común de todas las pantallas."""

    clave = ""
    titulo = ""
    subtitulo = ""
    icono = ""                                       # [NUEVO] nombre del icono de la barra lateral
    roles = (ADMINISTRADOR, COORDINADOR, DOCENTE)    # [NUEVO] quién puede ver esta pantalla

    def __init__(self, master, ctx: Contexto):
        t = ctx.tema
        super().__init__(master, padding=(t.px(22), t.px(16), t.px(22), t.px(12)))
        self.ctx = ctx
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        # [PATRÓN: Template Method] esqueleto fijo: encabezado -> _construir -> actualizar
        self.encabezado = Encabezado(self, t, self.titulo, self.subtitulo)
        self.encabezado.grid(row=0, column=0, sticky="ew", pady=(0, t.px(12)))
        self.cuerpo = ttk.Frame(self)
        self.cuerpo.grid(row=1, column=0, sticky="nsew")
        self.cuerpo.columnconfigure(0, weight=1)
        self.cuerpo.rowconfigure(0, weight=1)
        self._construir()
        self.actualizar()

    @abstractmethod
    def _construir(self) -> None:
        """Crea los widgets (se llama una sola vez)."""

    @abstractmethod
    def actualizar(self) -> None:
        """Vuelve a leer el sistema y redibuja los datos."""

    # ------------------------------------------------------------ ayudas comunes
    @property
    def sistema(self) -> SistemaAcademico:
        return self.ctx.sistema

    def _pedir(self, titulo: str, campos, aceptar: str = "Guardar") -> Optional[dict]:
        return pedir_datos(self, self.ctx.tema, titulo, campos, aceptar)

    def ejecutar(self, accion: Callable[[], object], mensaje_ok: str,
                 cambia_datos: bool = True) -> tuple:
        """[PATRÓN: Template Method] Pasos fijos de toda acción: intentar -> guardar ->
        refrescar -> avisar. Si el sistema rechaza algo (ValueError/PermissionError),
        se muestra el motivo en una ventana y NADA se guarda."""
        try:
            resultado = accion()
        except (ValueError, PermissionError) as error:
            messagebox.showerror("No se pudo completar", str(error), parent=self)
            return False, None
        if cambia_datos:
            self.ctx.guardar()
            self.ctx.notificar_cambio()
        self.ctx.mensaje(mensaje_ok)
        return True, resultado

    def _avisar(self, texto: str, titulo: str = "Atención") -> None:
        messagebox.showinfo(titulo, texto, parent=self)

    def _seleccion_de(self, tabla: Tabla, que: str) -> Optional[str]:
        elegido = tabla.seleccion()
        if elegido is None:
            self._avisar(f"Seleccione {que} en la tabla.")
        return elegido

    def _elegir_coordinador(self) -> Optional[int]:
        """Si hay un solo coordinador lo usa; si hay varios, pregunta cuál."""
        cuenta = self.ctx.cuenta
        if cuenta is not None and cuenta.rol == COORDINADOR:
            return cuenta.id_docente           # un coordinador actúa siempre como él mismo
        coordinadores = self.sistema.coordinadores
        if not coordinadores:
            self._avisar("No hay coordinadores. Primero designe uno en la pantalla Docentes.")
            return None
        if len(coordinadores) == 1:
            return coordinadores[0].id
        datos = self._pedir("¿Qué coordinador realiza la acción?", [
            Campo("id", "Coordinador", "opcion",
                  [(f"{c.get_nombre_completo()} ({c.carrera})", c.id) for c in coordinadores])],
            "Continuar")
        return datos["id"] if datos else None


def _fila_sesion(s) -> tuple:
    """Convierte una SesionClase en una fila de tabla (coloreada por su estado)."""
    return (s.id, (s.id, s.dia.name.capitalize(), f"{s.hora_inicio:%H:%M} - {s.hora_fin:%H:%M}",
                   s.asignatura.codigo, s.docente.get_nombre_completo(), s.aula.codigo,
                   s.cupo, s.estado.name.capitalize(), s.motivo_rechazo or ""), s.estado.name)


def _ordenar(sesiones):
    return sorted(sesiones, key=lambda s: (s.dia.value, s.hora_inicio))


COLUMNAS_SESION = [("id", "ID", 45, "center"), ("dia", "Día", 85, "w"),
                   ("horario", "Horario", 115, "center"), ("asig", "Asignatura", 100, "w"),
                   ("docente", "Docente", 160, "w"), ("aula", "Aula", 70, "w"),
                   ("cupo", "Cupo", 50, "center"), ("estado", "Estado", 90, "center"),
                   ("motivo", "Motivo de rechazo", 190, "w")]


# ====================================================================== inicio
class VistaInicio(VistaBase):
    clave, titulo = "inicio", "Inicio"
    subtitulo = "Resumen del sistema"
    icono = "inicio"

    def _construir(self) -> None:
        t, img = self.ctx.tema, self.ctx.imagenes
        self.cuerpo.rowconfigure(0, weight=0)
        self.cuerpo.rowconfigure(3, weight=1)
        # [NUEVO] Franja de bienvenida con imagen en lugar del encabezado simple.
        self.encabezado.grid_remove()
        self._hero = Hero(self, t, img.hero() if img else None)
        self._hero.grid(row=0, column=0, sticky="ew", pady=(0, t.px(12)))
        self._periodo = ttk.Label(self.cuerpo, font=t.f_negrita)   # (solo guarda el texto; el Hero lo muestra)
        self._rejilla = ttk.Frame(self.cuerpo)
        self._rejilla.grid(row=1, column=0, sticky="ew")
        ic = (lambda n: img.icono(n)) if img else (lambda n: None)
        self._tarjetas = {
            "docentes": TarjetaDato(self._rejilla, t, "Docentes", COLORES["acento"], ic("docentes")),
            "coord": TarjetaDato(self._rejilla, t, "Coordinadores", "#7A4FE0", ic("usuarios")),
            "aulas": TarjetaDato(self._rejilla, t, "Aulas", "#13A3B8", ic("aulas")),
            "asig": TarjetaDato(self._rejilla, t, "Asignaturas", "#E07A2F", ic("asignaturas")),
            "sesiones": TarjetaDato(self._rejilla, t, "Sesiones totales", "#5B6B84", ic("sesiones")),
            "pend": TarjetaDato(self._rejilla, t, "Pendientes", "#E8A200", ic("periodos")),
            "aprob": TarjetaDato(self._rejilla, t, "Aprobadas", COLORES["ok"], ic("horario")),
        }
        self._columnas = 0
        self._rejilla.bind("<Configure>", self._reacomodar)
        cab = ttk.Frame(self.cuerpo)
        cab.grid(row=2, column=0, sticky="ew", pady=(t.px(14), t.px(6)))
        cab.columnconfigure(0, weight=1)
        ttk.Label(cab, text="Sesiones pendientes de aprobación", font=t.f_negrita).grid(row=0, column=0, sticky="w")
        if self.ctx.cuenta is None or self.ctx.cuenta.rol != DOCENTE:
            ttk.Button(cab, text="Ir a Sesiones", style="Suave.TButton",
                       command=lambda: self.ctx.navegar("sesiones")).grid(row=0, column=1)
        self._tabla = Tabla(self.cuerpo, t, [c for c in COLUMNAS_SESION if c[0] != "motivo" and c[0] != "estado"])
        self._tabla.grid(row=3, column=0, sticky="nsew")

    def _reacomodar(self, _evento=None) -> None:
        """Las tarjetas se acomodan en 2 a 7 columnas según el ancho (laptops chicas o grandes)."""
        t = self.ctx.tema
        columnas = max(2, min(7, self._rejilla.winfo_width() // t.px(190)))
        if columnas == self._columnas:
            return
        self._columnas = columnas
        for i in range(7):   # las columnas sin usar no deben entrar al grupo 'uniform'
            self._rejilla.columnconfigure(i, weight=1 if i < columnas else 0,
                                          uniform="k" if i < columnas else "", minsize=0)
        for i, tarjeta in enumerate(self._tarjetas.values()):
            tarjeta.grid(row=i // columnas, column=i % columnas, sticky="nsew",
                         padx=t.px(4), pady=t.px(4))

    def actualizar(self) -> None:
        s = self.sistema
        try:
            p = s.periodo_activo()
            texto = f"Período activo: {p.nombre}   ({p.fecha_inicio} a {p.fecha_fin})"
        except ValueError:
            texto = "No hay período activo."
        self._periodo.configure(text=texto)
        cuenta = self.ctx.cuenta
        if cuenta is not None:
            self._hero.poner(f"¡Hola, {cuenta.nombre.split()[0]}!",
                             f"{cuenta.rol.capitalize()}  ·  {texto}")
        estados = [x.estado.name for x in s.sesiones]
        valores = {"docentes": len(s.docentes), "coord": len(s.coordinadores), "aulas": len(s.aulas),
                   "asig": len(s.asignaturas), "sesiones": len(estados),
                   "pend": estados.count("BORRADOR"), "aprob": estados.count("APROBADA")}
        for clave, valor in valores.items():
            self._tarjetas[clave].poner(valor)
        self._tabla.cargar([_fila_sesion(x) for x in _ordenar(s.sesiones_pendientes())])


# =================================================================== docentes
class VistaDocentes(VistaBase):
    clave, titulo = "docentes", "Docentes"
    subtitulo = "Registro de docentes y coordinadores académicos"
    icono = "docentes"
    roles = (ADMINISTRADOR,)

    def _construir(self) -> None:
        self.encabezado.agregar_boton("Designar coordinador", self._designar)
        self.encabezado.agregar_boton("+ Nuevo docente", self._nuevo, "Acento.TButton")
        self._tabla = Tabla(self.cuerpo, self.ctx.tema, [
            ("id", "ID", 45, "center"), ("nombre", "Docente", 190, "w"),
            ("esp", "Especialidad", 150, "w"), ("rol", "Rol", 110, "center"),
            ("horas", "Horas aprobadas", 120, "center"), ("carrera", "Carrera", 130, "w")])
        self._tabla.grid(row=0, column=0, sticky="nsew")

    def actualizar(self) -> None:
        filas = []
        for d in self.sistema.docentes:
            # [U2-POLIMORFISMO] get_rol() responde DOCENTE o COORDINADOR según el objeto real.
            filas.append((d.id, (d.id, d.get_nombre_completo(), d.especialidad, d.get_rol().capitalize(),
                                 f"{d.horas_asignadas:g} / {d.horas_max_semana} h",
                                 getattr(d, "carrera", "—")),
                          "APROBADA" if d.get_rol() == "COORDINADOR" else None))
        self._tabla.cargar(filas)

    def _nuevo(self) -> None:
        datos = self._pedir("Nuevo docente", [
            Campo("nombre", "Nombre"), Campo("apellido", "Apellido"), Campo("correo", "Correo"),
            Campo("cedula", "Cédula"), Campo("esp", "Especialidad"),
            Campo("horas", "Horas máximas por semana", "entero", inicial="20")])
        if datos:
            self.ejecutar(lambda: self.sistema.registrar_docente(
                datos["nombre"], datos["apellido"], datos["correo"], datos["cedula"],
                datos["esp"], datos["horas"]), "Docente registrado")

    def _designar(self) -> None:
        elegido = self._seleccion_de(self._tabla, "un docente")
        if elegido is None:
            return
        datos = self._pedir("Designar coordinador", [Campo("carrera", "Carrera que coordinará")], "Designar")
        if datos:
            self.ejecutar(lambda: self.sistema.designar_coordinador(int(elegido), datos["carrera"]),
                          "Coordinador designado")


# ====================================================================== aulas
class VistaAulas(VistaBase):
    clave, titulo = "aulas", "Aulas"
    subtitulo = "Espacios donde se dictan las clases"
    icono = "aulas"
    roles = (ADMINISTRADOR,)

    def _construir(self) -> None:
        self.encabezado.agregar_boton("Activar / desactivar", self._alternar)
        self.encabezado.agregar_boton("+ Nueva aula", self._nueva, "Acento.TButton")
        self._tabla = Tabla(self.cuerpo, self.ctx.tema, [
            ("cod", "Código", 80, "w"), ("nombre", "Nombre", 170, "w"), ("cap", "Capacidad", 80, "center"),
            ("ubic", "Ubicación", 130, "w"), ("tipo", "Tipo", 110, "w"), ("disp", "Estado", 100, "center")])
        self._tabla.grid(row=0, column=0, sticky="nsew")

    def actualizar(self) -> None:
        self._tabla.cargar([
            (a.codigo, (a.codigo, a.nombre, a.capacidad, a.ubicacion, a.clasificacion.nombre,
                        "Disponible" if a.esta_disponible() else "No disponible"),
             None if a.esta_disponible() else "RECHAZADA") for a in self.sistema.aulas])

    def _nueva(self) -> None:
        datos = self._pedir("Nueva aula", [
            Campo("codigo", "Código (ej. A-101)"), Campo("nombre", "Nombre"),
            Campo("cap", "Capacidad (estudiantes)", "entero"), Campo("ubic", "Ubicación"),
            Campo("clas", "Tipo de aula", "opcion",
                  [(c.nombre, c.id) for c in self.sistema.clasificaciones])])
        if datos:
            self.ejecutar(lambda: self.sistema.registrar_aula(
                datos["codigo"], datos["nombre"], datos["cap"], datos["ubic"], datos["clas"]),
                "Aula registrada")

    def _alternar(self) -> None:
        elegido = self._seleccion_de(self._tabla, "un aula")
        if elegido is None:
            return

        def cambiar():
            aula = self.sistema.buscar_aula(elegido)
            aula.cambiar_disponibilidad(not aula.esta_disponible())
        self.ejecutar(cambiar, "Disponibilidad del aula actualizada")


# =============================================================== asignaturas
class VistaAsignaturas(VistaBase):
    clave, titulo = "asignaturas", "Asignaturas"
    subtitulo = "Materias con sus horas de teoría y práctica"
    icono = "asignaturas"
    roles = (ADMINISTRADOR,)

    def _construir(self) -> None:
        self.encabezado.agregar_boton("+ Nueva asignatura", self._nueva, "Acento.TButton")
        self._tabla = Tabla(self.cuerpo, self.ctx.tema, [
            ("cod", "Código", 80, "w"), ("nombre", "Nombre", 240, "w"), ("nivel", "Nivel", 60, "center"),
            ("teo", "H. teoría", 80, "center"), ("pra", "H. práctica", 80, "center"),
            ("tot", "Total", 70, "center")])
        self._tabla.grid(row=0, column=0, sticky="nsew")

    def actualizar(self) -> None:
        self._tabla.cargar([(a.codigo, (a.codigo, a.nombre, a.nivel, a.horas_teoria,
                                        a.horas_practica, a.get_horas_totales()), None)
                            for a in self.sistema.asignaturas])

    def _nueva(self) -> None:
        datos = self._pedir("Nueva asignatura", [
            Campo("cod", "Código (ej. POO)"), Campo("nombre", "Nombre"), Campo("nivel", "Nivel", "entero"),
            Campo("teo", "Horas de teoría", "entero", minimo=0, inicial="3"),
            Campo("pra", "Horas de práctica", "entero", minimo=0, inicial="0")])
        if datos:
            self.ejecutar(lambda: self.sistema.registrar_asignatura(
                datos["cod"], datos["nombre"], datos["nivel"], datos["teo"], datos["pra"]),
                "Asignatura registrada")


# ================================================================== períodos
class VistaPeriodos(VistaBase):
    clave, titulo = "periodos", "Períodos"
    subtitulo = "Solo puede haber un período académico activo a la vez"
    icono = "periodos"
    roles = (ADMINISTRADOR,)

    def _construir(self) -> None:
        self.encabezado.agregar_boton("Cerrar período activo", self._cerrar)
        self.encabezado.agregar_boton("+ Nuevo período", self._nuevo, "Acento.TButton")
        self._tabla = Tabla(self.cuerpo, self.ctx.tema, [
            ("id", "ID", 45, "center"), ("nombre", "Nombre", 160, "w"), ("ini", "Inicio", 110, "center"),
            ("fin", "Fin", 110, "center"), ("estado", "Estado", 100, "center")])
        self._tabla.grid(row=0, column=0, sticky="nsew")

    def actualizar(self) -> None:
        self._tabla.cargar([(p.id, (p.id, p.nombre, p.fecha_inicio, p.fecha_fin,
                                    "Activo" if p.activo else "Cerrado"),
                             "APROBADA" if p.activo else None) for p in self.sistema.periodos])

    def _nuevo(self) -> None:
        datos = self._pedir("Nuevo período académico", [
            Campo("nombre", "Nombre (ej. 2026-2)"), Campo("ini", "Fecha de inicio (AAAA-MM-DD)", "fecha"),
            Campo("fin", "Fecha de fin (AAAA-MM-DD)", "fecha")])
        if datos:
            self.ejecutar(lambda: self.sistema.crear_periodo(datos["nombre"], datos["ini"], datos["fin"]),
                          "Período creado")

    def _cerrar(self) -> None:
        try:
            activo = self.sistema.periodo_activo()
        except ValueError as e:
            self._avisar(str(e))
            return
        if messagebox.askyesno("Cerrar período", f"¿Cerrar el período {activo.nombre}?", parent=self):
            self.ejecutar(self.sistema.cerrar_periodo_activo, f"Período {activo.nombre} cerrado")


# =================================================================== sesiones
class VistaSesiones(VistaBase):
    clave, titulo = "sesiones", "Sesiones de clase"
    subtitulo = "Cree sesiones en borrador y el coordinador las aprueba o rechaza"
    icono = "sesiones"
    roles = (ADMINISTRADOR, COORDINADOR)
    TODAS = "Todas"

    def _construir(self) -> None:
        t = self.ctx.tema
        self.encabezado.agregar_boton("Duplicar", self._duplicar)
        self.encabezado.agregar_boton("Rechazar", self._rechazar)
        self.encabezado.agregar_boton("Aprobar", self._aprobar)
        self.encabezado.agregar_boton("+ Nueva sesión", self._nueva, "Acento.TButton")
        self.cuerpo.rowconfigure(0, weight=0)
        self.cuerpo.rowconfigure(1, weight=1)
        filtro = ttk.Frame(self.cuerpo)
        filtro.grid(row=0, column=0, sticky="w", pady=(0, t.px(8)))
        ttk.Label(filtro, text="Estado:").pack(side="left", padx=(0, t.px(6)))
        self._estado = ttk.Combobox(filtro, state="readonly", width=14,
                                    values=[self.TODAS, "Borrador", "Aprobada", "Rechazada"])
        self._estado.current(0)
        self._estado.pack(side="left")
        self._estado.bind("<<ComboboxSelected>>", lambda _e: self.actualizar())
        self._tabla = Tabla(self.cuerpo, t, COLUMNAS_SESION)
        self._tabla.grid(row=1, column=0, sticky="nsew")

    def actualizar(self) -> None:
        filtro = self._estado.get().upper()
        sesiones = [s for s in _ordenar(self.sistema.sesiones)
                    if filtro == self.TODAS.upper() or s.estado.name == filtro]
        self._tabla.cargar([_fila_sesion(s) for s in sesiones])

    def _faltan_datos(self) -> bool:
        s = self.sistema
        for hay, aviso in ((s.docentes, "docente"), (s.aulas, "aula"), (s.asignaturas, "asignatura")):
            if not hay:
                self._avisar(f"Antes de crear una sesión registre al menos una {aviso}.")
                return True
        try:
            s.periodo_activo()
        except ValueError as e:
            self._avisar(str(e))
            return True
        return False

    def _nueva(self) -> None:
        if self._faltan_datos():
            return
        s = self.sistema
        datos = self._pedir("Nueva sesión de clase", [
            Campo("dia", "Día", "opcion", [(d.name.capitalize(), d) for d in DiaSemana]),
            Campo("ini", "Hora de inicio (HH:MM)", "hora", inicial="07:00"),
            Campo("fin", "Hora de fin (HH:MM)", "hora", inicial="09:00"),
            Campo("cupo", "Cupo de estudiantes", "entero", inicial="30"),
            Campo("asig", "Asignatura", "opcion", [(f"{a.codigo} - {a.nombre}", a.codigo) for a in s.asignaturas]),
            Campo("doc", "Docente", "opcion", [(f"{d.id} - {d.get_nombre_completo()}", d.id) for d in s.docentes]),
            Campo("aula", "Aula", "opcion", [(f"{a.codigo} - {a.nombre} (cap. {a.capacidad})", a.codigo)
                                             for a in s.aulas])])
        if datos:
            self.ejecutar(lambda: s.crear_sesion(datos["dia"], datos["ini"], datos["fin"], datos["cupo"],
                                                 datos["asig"], datos["doc"], datos["aula"]),
                          "Sesión creada en borrador")

    def _aprobar(self) -> None:
        elegido = self._seleccion_de(self._tabla, "una sesión")
        coord = self._elegir_coordinador() if elegido is not None else None
        if elegido is not None and coord is not None:
            self.ejecutar(lambda: self.sistema.aprobar_sesion(int(elegido), coord),
                          f"Sesión {elegido} aprobada")

    def _rechazar(self) -> None:
        elegido = self._seleccion_de(self._tabla, "una sesión")
        if elegido is None:
            return
        coord = self._elegir_coordinador()
        if coord is None:
            return
        datos = self._pedir("Rechazar sesión", [Campo("motivo", "Motivo del rechazo")], "Rechazar")
        if datos:
            self.ejecutar(lambda: self.sistema.rechazar_sesion(int(elegido), coord, datos["motivo"]),
                          f"Sesión {elegido} rechazada")

    def _duplicar(self) -> None:
        """[PATRÓN: Prototype] Copia la sesión elegida a otro día sin volver a escribir sus datos."""
        elegido = self._seleccion_de(self._tabla, "la sesión a duplicar")
        if elegido is None:
            return
        datos = self._pedir("Duplicar sesión a otro día", [
            Campo("dia", "Nuevo día", "opcion", [(d.name.capitalize(), d) for d in DiaSemana]),
            Campo("ini", "Nueva hora de inicio (opcional)", "hora", opcional=True),
            Campo("fin", "Nueva hora de fin (opcional)", "hora", opcional=True)], "Duplicar")
        if datos:
            self.ejecutar(lambda: self.sistema.duplicar_sesion(int(elegido), datos["dia"],
                                                                datos["ini"], datos["fin"]),
                          "Sesión duplicada en borrador")


# =================================================================== horario
class VistaHorario(VistaBase):
    clave, titulo = "horario", "Horario semanal"
    subtitulo = "Cuadrícula de lunes a sábado; haga clic en un bloque para ver el detalle"
    icono = "horario"
    roles = (ADMINISTRADOR, COORDINADOR, DOCENTE)
    TODOS = "Todos"

    def _construir(self) -> None:
        t = self.ctx.tema
        self.cuerpo.rowconfigure(0, weight=0)
        self.cuerpo.rowconfigure(1, weight=1)
        barra = ttk.Frame(self.cuerpo)
        barra.grid(row=0, column=0, sticky="ew", pady=(0, t.px(8)))
        ttk.Label(barra, text="Docente:").pack(side="left", padx=(0, t.px(6)))
        self._docente = ttk.Combobox(barra, state="readonly", width=24)
        self._docente.pack(side="left", padx=(0, t.px(14)))
        ttk.Label(barra, text="Período:").pack(side="left", padx=(0, t.px(6)))
        self._periodo = ttk.Combobox(barra, state="readonly", width=12)
        self._periodo.pack(side="left")
        for combo in (self._docente, self._periodo):
            combo.bind("<<ComboboxSelected>>", lambda _e: self._dibujar())
        # Leyenda de colores (a la derecha).
        for estado in ("RECHAZADA", "APROBADA", "BORRADOR"):
            fondo, borde = COLOR_ESTADO[estado]
            tk.Label(barra, text=f" {estado.capitalize()} ", background=fondo, foreground=borde,
                     font=t.f_chica).pack(side="right", padx=(t.px(4), 0))
        self._lienzo = tk.Canvas(self.cuerpo, background=COLORES["fondo"], highlightthickness=0)
        self._lienzo.grid(row=1, column=0, sticky="nsew")
        self._lienzo.bind("<Configure>", lambda _e: self._dibujar())  # se redibuja al cambiar de tamaño

    def actualizar(self) -> None:
        docentes = [self.TODOS] + [d.get_nombre_completo() for d in self.sistema.docentes]
        periodos = [self.TODOS] + [p.nombre for p in self.sistema.periodos]
        actual_d, actual_p = self._docente.get(), self._periodo.get()
        self._docente.configure(values=docentes)
        self._periodo.configure(values=periodos)
        self._docente.set(actual_d if actual_d in docentes else self.TODOS)
        cuenta = self.ctx.cuenta
        if cuenta is not None and cuenta.rol == DOCENTE:    # [NUEVO] un docente solo ve su horario
            propio = next((d.get_nombre_completo() for d in self.sistema.docentes
                           if d.id == cuenta.id_docente), self.TODOS)
            self._docente.set(propio)
            self._docente.configure(state="disabled")
        if actual_p in periodos:
            self._periodo.set(actual_p)
        else:   # por defecto, el período activo
            try:
                self._periodo.set(self.sistema.periodo_activo().nombre)
            except ValueError:
                self._periodo.set(self.TODOS)
        self._dibujar()

    def _visibles(self):
        d, p = self._docente.get(), self._periodo.get()
        return [s for s in self.sistema.sesiones
                if (d in ("", self.TODOS) or s.docente.get_nombre_completo() == d)
                and (p in ("", self.TODOS) or s.periodo.nombre == p)]

    @staticmethod
    def _min(hora) -> int:
        return hora.hour * 60 + hora.minute

    @staticmethod
    def _recortar(fuente, texto: str, ancho: int) -> str:
        """Acorta el texto con '…' para que no se salga del bloque."""
        if fuente.measure(texto) <= ancho:
            return texto
        while texto and fuente.measure(texto + "…") > ancho:
            texto = texto[:-1]
        return texto + "…" if texto else ""

    def _dibujar(self) -> None:
        c, t = self._lienzo, self.ctx.tema
        c.delete("all")
        ancho, alto = c.winfo_width(), c.winfo_height()
        if ancho < 120 or alto < 120:
            return
        izq, sup, der, inf = t.px(52), t.px(28), t.px(4), t.px(4)
        sesiones = self._visibles()
        h0 = min([7] + [s.hora_inicio.hour for s in sesiones])
        h1 = max([21] + [s.hora_fin.hour + (1 if s.hora_fin.minute else 0) for s in sesiones])
        dias = list(DiaSemana)
        ancho_dia = (ancho - izq - der) / len(dias)
        alto_hora = (alto - sup - inf) / (h1 - h0)
        c.create_rectangle(izq, sup, ancho - der, alto - inf, fill=COLORES["tarjeta"], outline=COLORES["borde"])
        for h in range(h0, h1 + 1):                       # líneas y etiquetas de horas
            y = sup + (h - h0) * alto_hora
            c.create_line(izq, y, ancho - der, y, fill=COLORES["borde"])
            if h < h1 or True:
                c.create_text(izq - t.px(6), y, text=f"{h:02d}:00", anchor="e",
                              fill=COLORES["texto_suave"], font=t.f_chica)
        for i, d in enumerate(dias):                      # columnas y títulos de días
            x = izq + i * ancho_dia
            c.create_line(x, sup, x, alto - inf, fill=COLORES["borde"])
            c.create_text(x + ancho_dia / 2, sup / 2, text=d.name.capitalize(), font=t.f_negrita)
        linea = t.f_chica.metrics("linespace")
        for i, d in enumerate(dias):
            del_dia = sorted((s for s in sesiones if s.dia == d), key=lambda s: (s.hora_inicio, s.hora_fin))
            carriles: list[int] = []     # sesiones que se cruzan van una al lado de otra
            colocadas = []
            for s in del_dia:
                inicio = self._min(s.hora_inicio)
                for k, fin in enumerate(carriles):
                    if fin <= inicio:
                        carriles[k] = self._min(s.hora_fin)
                        colocadas.append((s, k))
                        break
                else:
                    carriles.append(self._min(s.hora_fin))
                    colocadas.append((s, len(carriles) - 1))
            n = max(1, len(carriles))
            ancho_bloque = (ancho_dia - 4) / n
            for s, k in colocadas:
                x0 = izq + i * ancho_dia + 2 + k * ancho_bloque
                y0 = sup + (self._min(s.hora_inicio) / 60 - h0) * alto_hora + 1
                y1 = sup + (self._min(s.hora_fin) / 60 - h0) * alto_hora - 1
                fondo, borde = COLOR_ESTADO[s.estado.name]
                etiqueta = f"s{s.id}"
                c.create_rectangle(x0, y0, x0 + ancho_bloque - 2, y1, fill=fondo, outline=borde,
                                   width=1, tags=(etiqueta,))
                nombre = s.docente.get_nombre_completo().split()
                lineas = [s.asignatura.codigo, f"{nombre[0][0]}. {nombre[-1]}", s.aula.codigo]
                caben = max(1, int((y1 - y0 - 4) // linea))
                texto = "\n".join(self._recortar(t.f_chica, l, int(ancho_bloque - t.px(10)))
                                  for l in lineas[:caben])
                c.create_text(x0 + t.px(4), y0 + t.px(3), anchor="nw", text=texto, fill=borde,
                              font=t.f_chica, tags=(etiqueta,))
                c.tag_bind(etiqueta, "<Button-1>", lambda _e, ses=s: self._detalle(ses))

    def _detalle(self, s) -> None:
        extra = f"\nMotivo de rechazo: {s.motivo_rechazo}" if s.motivo_rechazo else ""
        self._avisar(f"Sesión {s.id} - {s.estado.name.capitalize()}\n\n{s.asignatura}\n"
                     f"Docente: {s.docente.get_nombre_completo()}\nAula: {s.aula}\n"
                     f"{s.dia.name.capitalize()} {s.hora_inicio:%H:%M} a {s.hora_fin:%H:%M}\n"
                     f"Cupo: {s.cupo}{extra}", "Detalle de la sesión")


# =================================================================== reportes
class VistaReportes(VistaBase):
    clave, titulo = "reportes", "Reportes"
    subtitulo = "Genere un reporte, revíselo en pantalla y expórtelo a CSV"
    icono = "reportes"
    roles = (ADMINISTRADOR, COORDINADOR)

    def _construir(self) -> None:
        t = self.ctx.tema
        self.encabezado.agregar_boton("Exportar CSV", self._exportar)
        self.encabezado.agregar_boton("Generar reporte", self._generar, "Acento.TButton")
        self.cuerpo.rowconfigure(0, weight=0)
        self.cuerpo.rowconfigure(1, weight=1)
        barra = ttk.Frame(self.cuerpo)
        barra.grid(row=0, column=0, sticky="ew", pady=(0, t.px(8)))
        ttk.Label(barra, text="Tipo:").pack(side="left", padx=(0, t.px(6)))
        self._tipo = ttk.Combobox(barra, state="readonly", width=22,
                                  values=["Horario por período", "Carga docente"])
        self._tipo.current(0)
        self._tipo.pack(side="left", padx=(0, t.px(14)))
        ttk.Label(barra, text="Período:").pack(side="left", padx=(0, t.px(6)))
        self._periodo = ttk.Combobox(barra, state="readonly", width=14)
        self._periodo.pack(side="left")
        marco = ttk.Frame(self.cuerpo, style="Tarjeta.TFrame", borderwidth=1, relief="solid")
        marco.grid(row=1, column=0, sticky="nsew")
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(0, weight=1)
        self._texto = tk.Text(marco, wrap="none", font=t.f_mono, background=COLORES["tarjeta"],
                              borderwidth=0, padx=t.px(12), pady=t.px(10), state="disabled")
        vertical = ttk.Scrollbar(marco, orient="vertical", command=self._texto.yview)
        horizontal = ttk.Scrollbar(marco, orient="horizontal", command=self._texto.xview)
        self._texto.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self._texto.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self._reporte: Optional[Reporte] = None   # [U2-POLIMORFISMO-ABSTRACTAS] cualquier tipo de Reporte

    def actualizar(self) -> None:
        nombres = [p.nombre for p in self.sistema.periodos]
        actual = self._periodo.get()
        self._periodo.configure(values=nombres)
        if actual in nombres:
            self._periodo.set(actual)
        else:
            try:
                self._periodo.set(self.sistema.periodo_activo().nombre)
            except ValueError:
                self._periodo.set(nombres[-1] if nombres else "")

    def _mostrar(self, texto: str) -> None:
        self._texto.configure(state="normal")
        self._texto.delete("1.0", "end")
        self._texto.insert("1.0", texto)
        self._texto.configure(state="disabled")

    def _generar(self) -> None:
        coord = self._elegir_coordinador()
        if coord is None:
            return
        if self._tipo.current() == 0:
            periodo = next((p for p in self.sistema.periodos if p.nombre == self._periodo.get()), None)
            if periodo is None:
                self._avisar("No hay períodos registrados: cree uno en la pantalla Períodos.")
                return
            accion = lambda: self.sistema.generar_reporte(coord, periodo.id)
        else:
            accion = lambda: self.sistema.generar_reporte_carga(coord)
        ok, reporte = self.ejecutar(accion, "Reporte generado", cambia_datos=False)
        if ok:
            # [U2-POLIMORFISMO-ABSTRACTAS] Se usa 'contenido' sin saber qué tipo de Reporte es.
            self._reporte = reporte
            self._mostrar(reporte.contenido)

    def _exportar(self) -> None:
        if self._reporte is None:
            self._avisar("Primero genere un reporte.")
            return
        ruta = filedialog.asksaveasfilename(
            parent=self, title="Guardar reporte", defaultextension=".csv",
            initialfile=f"reporte_{self._reporte.id}.{self._reporte.extension_de('csv')}",
            filetypes=[("CSV (Excel)", "*.csv")])
        if ruta:
            # utf-8-sig: Excel reconoce bien las tildes.
            with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
                archivo.write(self._reporte.exportar("csv"))
            self.ctx.mensaje(f"Reporte guardado en {ruta}")


def rol_efectivo(rol_guardado: str, id_docente, sistema: SistemaAcademico) -> str:
    """Un docente que el administrador designó coordinador pasa a ser COORDINADOR sin
    tener que crear otra cuenta."""
    if rol_guardado == DOCENTE and any(c.id == id_docente for c in sistema.coordinadores):
        return COORDINADOR
    return rol_guardado


# ================================================================ estadísticas
class VistaEstadisticas(VistaBase):
    """[NUEVO] Gráficas e indicadores. Los números los calcula EstadisticasHorario;
    las gráficas (GraficoBarras, GraficoDona, GraficoProgreso) solo los dibujan."""
    clave, titulo = "estadisticas", "Estadísticas"
    subtitulo = "Resumen visual de la carga y la ocupación del horario"
    icono = "estadisticas"
    TODOS = "Todos los períodos"

    def _construir(self) -> None:
        t = self.ctx.tema
        for fila, peso in ((0, 0), (1, 0), (2, 1)):
            self.cuerpo.rowconfigure(fila, weight=peso)
        barra = ttk.Frame(self.cuerpo)
        barra.grid(row=0, column=0, sticky="w", pady=(0, t.px(8)))
        ttk.Label(barra, text="Período:").pack(side="left", padx=(0, t.px(6)))
        self._periodo = ttk.Combobox(barra, state="readonly", width=20)
        self._periodo.pack(side="left")
        self._periodo.bind("<<ComboboxSelected>>", lambda _e: self.actualizar())

        indicadores = ttk.Frame(self.cuerpo)
        indicadores.grid(row=1, column=0, sticky="ew", pady=(0, t.px(10)))
        self._numeros: dict[str, ttk.Label] = {}
        definicion = (("sesiones", "Sesiones", "#2F6FED"), ("horas", "Horas programadas", "#8B5CF6"),
                      ("aprobacion", "Aprobación", "#1E9E6A"), ("ocupacion", "Ocupación de aulas", "#14B8A6"),
                      ("carga", "Carga docente", "#F59E0B"))
        for i, (clave, etiqueta, color) in enumerate(definicion):
            indicadores.columnconfigure(i, weight=1, uniform="ind")
            tarjeta = ttk.Frame(indicadores, style="Tarjeta.TFrame", borderwidth=1, relief="solid")
            tarjeta.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else t.px(8), 0))
            tk.Frame(tarjeta, background=color, height=t.px(4)).pack(fill="x")
            numero = ttk.Label(tarjeta, text="0", style="Numero.TLabel", foreground=color)
            numero.pack(anchor="w", padx=t.px(12), pady=(t.px(4), 0))
            ttk.Label(tarjeta, text=etiqueta, style="TarjetaSuave.TLabel").pack(
                anchor="w", padx=t.px(12), pady=(0, t.px(6)))
            self._numeros[clave] = numero

        rejilla = ttk.Frame(self.cuerpo)
        rejilla.grid(row=2, column=0, sticky="nsew")
        for k in range(2):
            rejilla.columnconfigure(k, weight=1, uniform="g")
            rejilla.rowconfigure(k, weight=1, uniform="f")
        # [U2-POLIMORFISMO-ABSTRACTAS] las 4 son Grafico; se usan igual: grafico.poner(datos)
        self._g_estado = GraficoDona(rejilla, t, "Sesiones por estado", "Aprobadas, borradores y rechazadas")
        self._g_dia = GraficoBarras(rejilla, t, "Sesiones por día", "Sin contar las rechazadas")
        self._g_docente = GraficoProgreso(rejilla, t, "Carga de cada docente", "Horas programadas / máximo semanal")
        self._g_aula = GraficoProgreso(rejilla, t, "Ocupación de aulas", "% de las horas útiles de la semana")
        for k, g in enumerate((self._g_estado, self._g_dia, self._g_docente, self._g_aula)):
            g.configure(height=t.px(110))
            g.grid(row=k // 2, column=k % 2, sticky="nsew",
                   padx=(0 if k % 2 == 0 else t.px(5), t.px(5) if k % 2 == 0 else 0),
                   pady=(0 if k < 2 else t.px(5), t.px(5) if k < 2 else 0))

    def actualizar(self) -> None:
        nombres = [self.TODOS] + [p.nombre for p in self.sistema.periodos]
        actual = self._periodo.get()
        self._periodo.configure(values=nombres)
        if actual in nombres:
            self._periodo.set(actual)
        else:
            try:
                self._periodo.set(self.sistema.periodo_activo().nombre)
            except ValueError:
                self._periodo.set(self.TODOS)
        id_periodo = next((p.id for p in self.sistema.periodos if p.nombre == self._periodo.get()), None)
        est = EstadisticasHorario(self.sistema, id_periodo=id_periodo)
        ind = est.indicadores()
        self._numeros["sesiones"].configure(text=f"{ind['sesiones']:g}")
        self._numeros["horas"].configure(text=f"{ind['horas_programadas']:g} h")
        self._numeros["aprobacion"].configure(text=f"{ind['aprobacion']:g} %")
        self._numeros["ocupacion"].configure(text=f"{ind['ocupacion_media']:g} %")
        self._numeros["carga"].configure(text=f"{ind['carga_media']:g} %")
        animar = self.winfo_ismapped()
        self._g_estado.poner(list(est.por_estado().items()), animar)
        self._g_dia.poner(list(est.por_dia().items()), animar)
        self._g_docente.poner(est.horas_por_docente(), animar)
        self._g_aula.poner([(codigo, pct, 100) for codigo, pct in est.ocupacion_por_aula()], animar)


# ==================================================================== usuarios
class VistaUsuarios(VistaBase):
    """[NUEVO] Solo el administrador: crea cuentas de acceso para los docentes."""
    clave, titulo = "usuarios", "Usuarios y accesos"
    subtitulo = "Cuentas para iniciar sesión (el usuario de un docente es su correo)"
    icono = "usuarios"
    roles = (ADMINISTRADOR,)

    def _construir(self) -> None:
        self.encabezado.agregar_boton("Eliminar cuenta", self._eliminar)
        self.encabezado.agregar_boton("Restablecer contraseña", self._restablecer)
        self.encabezado.agregar_boton("+ Cuenta para docente", self._nueva, "Acento.TButton")
        self._tabla = Tabla(self.cuerpo, self.ctx.tema, [
            ("usuario", "Usuario", 230, "w"), ("nombre", "Nombre", 190, "w"),
            ("rol", "Rol", 120, "center"), ("doc", "Docente (ID)", 100, "center")])
        self._tabla.grid(row=0, column=0, sticky="nsew")

    def _auth(self) -> Optional[AutenticadorLocal]:
        a = self.ctx.autenticador
        if not isinstance(a, AutenticadorLocal):
            self._avisar("Este autenticador no permite administrar cuentas desde la interfaz.")
            return None
        return a

    def actualizar(self) -> None:
        a = self.ctx.autenticador
        if not isinstance(a, AutenticadorLocal):
            return
        self._tabla.cargar([(c["usuario"], (c["usuario"], c["nombre"],
                                            rol_efectivo(c["rol"], c["id_docente"], self.sistema).capitalize(),
                                            c["id_docente"] if c["id_docente"] is not None else "—"),
                             "APROBADA" if c["rol"] == ADMINISTRADOR else None) for c in a.usuarios()])

    def _nueva(self) -> None:
        a = self._auth()
        if a is None:
            return
        if not self.sistema.docentes:
            self._avisar("Primero registre docentes en la pantalla Docentes.")
            return
        datos = self._pedir("Crear cuenta para un docente", [
            Campo("doc", "Docente", "opcion", [(f"{d.id} - {d.get_nombre_completo()}", d.id)
                                                for d in self.sistema.docentes]),
            Campo("clave", "Contraseña (mín. 6)", "clave"), Campo("repetir", "Repetir contraseña", "clave")],
            "Crear cuenta")
        if not datos:
            return

        def crear():
            if datos["clave"] != datos["repetir"]:
                raise ValueError("Las contraseñas no coinciden")
            d = self.sistema.buscar_docente(datos["doc"])
            a.crear_cuenta(d.correo, datos["clave"], DOCENTE, d.id, d.get_nombre_completo())
        self.ejecutar(crear, "Cuenta creada: el usuario es el correo del docente", cambia_datos=False)
        self.actualizar()

    def _restablecer(self) -> None:
        a = self._auth()
        elegido = self._seleccion_de(self._tabla, "una cuenta") if a else None
        if elegido is None:
            return
        datos = self._pedir(f"Nueva contraseña para {elegido}", [
            Campo("clave", "Contraseña nueva (mín. 6)", "clave"), Campo("repetir", "Repetir", "clave")], "Cambiar")
        if not datos:
            return

        def cambiar():
            if datos["clave"] != datos["repetir"]:
                raise ValueError("Las contraseñas no coinciden")
            a.restablecer_clave(elegido, datos["clave"])
        self.ejecutar(cambiar, "Contraseña actualizada", cambia_datos=False)

    def _eliminar(self) -> None:
        a = self._auth()
        elegido = self._seleccion_de(self._tabla, "una cuenta") if a else None
        if elegido is None:
            return
        if self.ctx.cuenta and elegido == self.ctx.cuenta.usuario:
            self._avisar("No puede eliminar la cuenta con la que inició sesión.")
            return
        if messagebox.askyesno("Eliminar cuenta", f"¿Eliminar la cuenta {elegido}?", parent=self):
            self.ejecutar(lambda: a.eliminar_cuenta(elegido), "Cuenta eliminada", cambia_datos=False)
            self.actualizar()


# [SOLID-O] Para agregar una pantalla nueva: crear la clase y añadirla a esta lista.
VISTAS_POR_DEFECTO: tuple = (VistaInicio, VistaEstadisticas, VistaHorario, VistaSesiones, VistaDocentes,
                             VistaAulas, VistaAsignaturas, VistaPeriodos, VistaReportes, VistaUsuarios)

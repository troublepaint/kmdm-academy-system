"""PANTALLAS (vistas) de la interfaz gráfica.  [MODIFICADO: ahora son VISTAS PASIVAS de MVP]

    VistaBase (clase ABSTRACTA)
    ├── VistaInicio        panel con totales y sesiones pendientes
    ├── VistaEstadisticas  indicadores y gráficas
    ├── VistaHorario       cuadrícula semanal (lunes a sábado) por colores
    ├── VistaReportes      reporte de horario / carga docente y exportar CSV
    └── VistaConTabla      (base de las pantallas que muestran una tabla)
        ├── VistaSesiones      crear, aprobar, rechazar y duplicar sesiones
        ├── VistaDocentes      registrar docentes y designar coordinadores
        ├── VistaAulas         registrar aulas y activar/desactivar
        ├── VistaAsignaturas   registrar asignaturas
        ├── VistaPeriodos      crear y cerrar períodos
        └── VistaUsuarios      cuentas de acceso

[MVP] Cada pantalla tiene UN presentador (relación uno a uno, ver presentadores/):
    * La VISTA (este archivo) solo DIBUJA widgets y AVISA al presentador lo que hizo el
      usuario: "pulsó Aprobar con la sesión 3 seleccionada".
    * El PRESENTADOR decide: llama al modelo, maneja errores, guarda, y le devuelve a la
      vista los datos ya preparados (filas, textos, números) con métodos como
      mostrar_filas(), mostrar_error() o mostrar_mensaje().
    * La vista ya NO usa SistemaAcademico (el modelo) directamente: antes cada pantalla
      llamaba a self.sistema.xxx(); ahora solo habla con self.presentador.
  ¿Qué se ganó? La lógica que antes estaba aquí mezclada con tkinter (filtrar, validar,
  elegir coordinador, contar estados, acomodar el horario...) ahora se puede PROBAR sin
  abrir ninguna ventana (tests/test_presentadores.py) y se REUTILIZA en el menú de consola.

[U2-HERENCIA] Todas las pantallas HEREDAN de VistaBase y reutilizan su encabezado y la
    forma de mostrar mensajes, errores y preguntas.
[U2-POLIMORFISMO-ABSTRACTAS] VistaBase es abstracta: obliga a cada pantalla a escribir
    _crear_presentador(), _construir() y actualizar(). La ventana principal llama
    vista.actualizar() sin saber de qué pantalla es.
[U2-POLIMORFISMO-INTERFACES] Cada vista IMPLEMENTA la interfaz que su presentador espera
    (IVistaTabla, IVistaInicio, IVistaHorario...).
[PATRÓN: Template Method] VistaBase.__init__ define el esqueleto (encabezado ->
    presentador -> _construir -> actualizar); las pantallas rellenan los pasos.
    (El Template Method de las ACCIONES pasó a PresentadorBase._ejecutar.)
[U2-INYECCIÓN-DEPENDENCIAS] Cada pantalla RECIBE un Contexto (sistema, tema, funciones de
    guardar/navegar) y se lo entrega a su presentador; no crea ni busca nada por su cuenta.
[SOLID-S] Vista = dibujar; presentador = decidir; modelo = reglas del negocio.
"""
from __future__ import annotations

import tkinter as tk
from abc import abstractmethod
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Optional, Sequence

from modelos import DiaSemana, minutos_del_dia
from presentadores import (BloqueHorario, Fila, IVistaDialogos, IVistaEstadisticas,
                           IVistaHorario, IVistaInicio, IVistaReportes, IVistaTabla,
                           PresentadorAsignaturas, PresentadorAulas, PresentadorDocentes,
                           PresentadorEstadisticas, PresentadorHorario, PresentadorInicio,
                           PresentadorPeriodos, PresentadorReportes, PresentadorSesiones,
                           PresentadorUsuarios)
from servicios import (ADMINISTRADOR, COORDINADOR, DOCENTE, Autenticador, Cuenta,
                       SistemaAcademico)

from .componentes import (Campo, Encabezado, Hero, Tabla, TarjetaDato, llenar_combo,
                          pedir_datos, recortar_texto)
from .graficos import GraficoBarras, GraficoDona, GraficoProgreso
from .imagenes import Imagenes
from .tema import COLOR_ESTADO, COLORES, Tema


@dataclass
class Contexto:
    """[U2-INYECCIÓN-DEPENDENCIAS] Todo lo que una pantalla (y su presentador) necesita,
    entregado desde afuera por la ventana principal."""
    sistema: SistemaAcademico              # el MODELO: lo usa el presentador, no la vista
    tema: Tema
    guardar: Callable[[], None]
    notificar_cambio: Callable[[], None]   # refresca TODAS las pantallas
    mensaje: Callable[[str], None]         # texto de la barra inferior
    navegar: Callable[[str], None]         # cambia de pantalla por su clave
    cuenta: Cuenta = None                  # quién inició sesión (rol y docente)
    imagenes: Imagenes = None              # imágenes PNG ya cargadas
    autenticador: Autenticador = None      # para crear cuentas y cambiar claves


# =================================================================== clase base
class VistaBase(ttk.Frame, IVistaDialogos):
    """[U2-POLIMORFISMO-ABSTRACTAS] Plantilla común de todas las pantallas.

    Implementa, UNA sola vez para todas, los métodos de IVistaDialogos que usan los
    presentadores (mostrar_mensaje, mostrar_error, avisar, confirmar, elegir, pedir_texto).
    """

    clave = ""
    titulo = ""
    subtitulo = ""
    icono = ""                                       # nombre del icono de la barra lateral
    roles = (ADMINISTRADOR, COORDINADOR, DOCENTE)    # quién puede ver esta pantalla

    def __init__(self, master, ctx: Contexto):
        t = ctx.tema
        super().__init__(master, padding=(t.px(22), t.px(16), t.px(22), t.px(12)))
        self.ctx = ctx
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        # [PATRÓN: Template Method] esqueleto fijo: encabezado -> presentador -> _construir -> actualizar
        self.encabezado = Encabezado(self, t, self.titulo, self.subtitulo)
        self.encabezado.grid(row=0, column=0, sticky="ew", pady=(0, t.px(12)))
        self.cuerpo = ttk.Frame(self)
        self.cuerpo.grid(row=1, column=0, sticky="nsew")
        self.cuerpo.columnconfigure(0, weight=1)
        self.cuerpo.rowconfigure(0, weight=1)
        # [MVP] El presentador se crea ANTES de los widgets: _construir() puede pedirle
        # datos (por ejemplo, las opciones de un filtro).
        self.presentador = self._crear_presentador()
        self._construir()
        self.actualizar()

    # ------------------------------------------------------------ pasos que cada pantalla escribe
    @abstractmethod
    def _crear_presentador(self):
        """Crea el presentador de esta pantalla (relación uno a uno)."""

    @abstractmethod
    def _construir(self) -> None:
        """Crea los widgets (se llama una sola vez)."""

    @abstractmethod
    def actualizar(self) -> None:
        """Pide al presentador que vuelva a cargar los datos."""

    def _dependencias(self) -> dict:
        """Lo que todos los presentadores reciben además de la vista y el modelo."""
        return {"guardar": self.ctx.guardar, "al_cambiar": self.ctx.notificar_cambio,
                "cuenta": self.ctx.cuenta}

    # ------------------------------------------------------------ IVista / IVistaDialogos
    def mostrar_mensaje(self, texto: str) -> None:
        self.ctx.mensaje(texto)

    def mostrar_error(self, texto: str) -> None:
        messagebox.showerror("No se pudo completar", texto, parent=self)

    def avisar(self, texto: str, titulo: str = "Atención") -> None:
        messagebox.showinfo(titulo, texto, parent=self)

    def confirmar(self, pregunta: str) -> bool:
        return messagebox.askyesno(self.titulo or "Confirmar", pregunta, parent=self)

    def elegir(self, titulo: str, opciones: Sequence[tuple[str, Any]]) -> Optional[Any]:
        datos = self._pedir(titulo, [Campo("valor", "Opción", "opcion", list(opciones))], "Continuar")
        return datos["valor"] if datos else None

    def pedir_texto(self, titulo: str, etiqueta: str) -> Optional[str]:
        datos = self._pedir(titulo, [Campo("texto", etiqueta)], "Aceptar")
        return datos["texto"] if datos else None

    # ------------------------------------------------------------ ayudas de dibujo
    def _pedir(self, titulo: str, campos, aceptar: str = "Guardar") -> Optional[dict]:
        return pedir_datos(self, self.ctx.tema, titulo, campos, aceptar)

    def _seleccion_de(self, tabla: Tabla, que: str) -> Optional[str]:
        """Fila elegida en la tabla; si no hay, avisa. (Leer la selección es trabajo de la vista.)"""
        elegido = tabla.seleccion()
        if elegido is None:
            self.avisar(f"Seleccione {que} en la tabla.")
        return elegido


class VistaConTabla(VistaBase, IVistaTabla):
    """[REFACTOR] Base de las pantallas que muestran una tabla: así 'mostrar_filas'
    se escribe una sola vez en lugar de repetirse en seis pantallas."""

    _tabla: Tabla

    def mostrar_filas(self, filas: Sequence[Fila]) -> None:
        self._tabla.cargar(filas)


COLUMNAS_SESION = [("id", "ID", 45, "center"), ("dia", "Día", 85, "w"),
                   ("horario", "Horario", 115, "center"), ("asig", "Asignatura", 100, "w"),
                   ("docente", "Docente", 160, "w"), ("aula", "Aula", 70, "w"),
                   ("cupo", "Cupo", 50, "center"), ("estado", "Estado", 90, "center"),
                   ("motivo", "Motivo de rechazo", 190, "w")]


# ====================================================================== inicio
class VistaInicio(VistaBase, IVistaInicio):
    clave, titulo = "inicio", "Inicio"
    subtitulo = "Resumen del sistema"
    icono = "inicio"

    def _crear_presentador(self) -> PresentadorInicio:
        return PresentadorInicio(self, self.ctx.sistema, **self._dependencias())

    def _construir(self) -> None:
        t, img = self.ctx.tema, self.ctx.imagenes
        self.cuerpo.rowconfigure(0, weight=0)
        self.cuerpo.rowconfigure(3, weight=1)
        # Franja de bienvenida con imagen en lugar del encabezado simple.
        self.encabezado.grid_remove()
        self._hero = Hero(self, t, img.hero() if img else None)
        self._hero.grid(row=0, column=0, sticky="ew", pady=(0, t.px(12)))
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
        self._tabla = Tabla(self.cuerpo, t, [c for c in COLUMNAS_SESION if c[0] not in ("motivo", "estado")])
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
        self.presentador.cargar()

    # [MVP] El presentador entrega los textos y números ya calculados; aquí solo se pintan.
    def mostrar_resumen(self, saludo: str, detalle: str, totales: dict[str, int],
                        pendientes: Sequence[Fila]) -> None:
        self._hero.poner(saludo, detalle)
        for clave, valor in totales.items():
            self._tarjetas[clave].poner(valor)
        self._tabla.cargar(pendientes)


# =================================================================== docentes
class VistaDocentes(VistaConTabla):
    clave, titulo = "docentes", "Docentes"
    subtitulo = "Registro de docentes y coordinadores académicos"
    icono = "docentes"
    roles = (ADMINISTRADOR,)

    def _crear_presentador(self) -> PresentadorDocentes:
        return PresentadorDocentes(self, self.ctx.sistema, **self._dependencias())

    def _construir(self) -> None:
        self.encabezado.agregar_boton("Designar coordinador", self._designar)
        self.encabezado.agregar_boton("+ Nuevo docente", self._nuevo, "Acento.TButton")
        self._tabla = Tabla(self.cuerpo, self.ctx.tema, [
            ("id", "ID", 45, "center"), ("nombre", "Docente", 190, "w"),
            ("esp", "Especialidad", 150, "w"), ("rol", "Rol", 110, "center"),
            ("horas", "Horas aprobadas", 120, "center"), ("carrera", "Carrera", 130, "w")])
        self._tabla.grid(row=0, column=0, sticky="nsew")

    def actualizar(self) -> None:
        self.presentador.cargar()

    def _nuevo(self) -> None:
        datos = self._pedir("Nuevo docente", [
            Campo("nombre", "Nombre"), Campo("apellido", "Apellido"), Campo("correo", "Correo"),
            Campo("cedula", "Cédula"), Campo("esp", "Especialidad"),
            Campo("horas", "Horas máximas por semana", "entero", inicial="20")])
        if datos:
            self.presentador.registrar(datos["nombre"], datos["apellido"], datos["correo"],
                                       datos["cedula"], datos["esp"], datos["horas"])

    def _designar(self) -> None:
        elegido = self._seleccion_de(self._tabla, "un docente")
        if elegido is None:
            return
        datos = self._pedir("Designar coordinador", [Campo("carrera", "Carrera que coordinará")], "Designar")
        if datos:
            self.presentador.designar_coordinador(int(elegido), datos["carrera"])


# ====================================================================== aulas
class VistaAulas(VistaConTabla):
    clave, titulo = "aulas", "Aulas"
    subtitulo = "Espacios donde se dictan las clases"
    icono = "aulas"
    roles = (ADMINISTRADOR,)

    def _crear_presentador(self) -> PresentadorAulas:
        return PresentadorAulas(self, self.ctx.sistema, **self._dependencias())

    def _construir(self) -> None:
        self.encabezado.agregar_boton("Activar / desactivar", self._alternar)
        self.encabezado.agregar_boton("+ Nueva aula", self._nueva, "Acento.TButton")
        self._tabla = Tabla(self.cuerpo, self.ctx.tema, [
            ("cod", "Código", 80, "w"), ("nombre", "Nombre", 170, "w"), ("cap", "Capacidad", 80, "center"),
            ("ubic", "Ubicación", 130, "w"), ("tipo", "Tipo", 110, "w"), ("disp", "Estado", 100, "center")])
        self._tabla.grid(row=0, column=0, sticky="nsew")

    def actualizar(self) -> None:
        self.presentador.cargar()

    def _nueva(self) -> None:
        datos = self._pedir("Nueva aula", [
            Campo("codigo", "Código (ej. A-101)"), Campo("nombre", "Nombre"),
            Campo("cap", "Capacidad (estudiantes)", "entero"), Campo("ubic", "Ubicación"),
            Campo("clas", "Tipo de aula", "opcion", self.presentador.opciones_clasificacion())])
        if datos:
            self.presentador.registrar(datos["codigo"], datos["nombre"], datos["cap"],
                                       datos["ubic"], datos["clas"])

    def _alternar(self) -> None:
        elegido = self._seleccion_de(self._tabla, "un aula")
        if elegido is not None:
            self.presentador.alternar_disponibilidad(elegido)


# =============================================================== asignaturas
class VistaAsignaturas(VistaConTabla):
    clave, titulo = "asignaturas", "Asignaturas"
    subtitulo = "Materias con sus horas de teoría y práctica"
    icono = "asignaturas"
    roles = (ADMINISTRADOR,)

    def _crear_presentador(self) -> PresentadorAsignaturas:
        return PresentadorAsignaturas(self, self.ctx.sistema, **self._dependencias())

    def _construir(self) -> None:
        self.encabezado.agregar_boton("+ Nueva asignatura", self._nueva, "Acento.TButton")
        self._tabla = Tabla(self.cuerpo, self.ctx.tema, [
            ("cod", "Código", 80, "w"), ("nombre", "Nombre", 240, "w"), ("nivel", "Nivel", 60, "center"),
            ("teo", "H. teoría", 80, "center"), ("pra", "H. práctica", 80, "center"),
            ("tot", "Total", 70, "center")])
        self._tabla.grid(row=0, column=0, sticky="nsew")

    def actualizar(self) -> None:
        self.presentador.cargar()

    def _nueva(self) -> None:
        datos = self._pedir("Nueva asignatura", [
            Campo("cod", "Código (ej. POO)"), Campo("nombre", "Nombre"), Campo("nivel", "Nivel", "entero"),
            Campo("teo", "Horas de teoría", "entero", minimo=0, inicial="3"),
            Campo("pra", "Horas de práctica", "entero", minimo=0, inicial="0")])
        if datos:
            self.presentador.registrar(datos["cod"], datos["nombre"], datos["nivel"],
                                       datos["teo"], datos["pra"])


# ================================================================== períodos
class VistaPeriodos(VistaConTabla):
    clave, titulo = "periodos", "Períodos"
    subtitulo = "Solo puede haber un período académico activo a la vez"
    icono = "periodos"
    roles = (ADMINISTRADOR,)

    def _crear_presentador(self) -> PresentadorPeriodos:
        return PresentadorPeriodos(self, self.ctx.sistema, **self._dependencias())

    def _construir(self) -> None:
        self.encabezado.agregar_boton("Cerrar período activo", self.presentador.cerrar_activo)
        self.encabezado.agregar_boton("+ Nuevo período", self._nuevo, "Acento.TButton")
        self._tabla = Tabla(self.cuerpo, self.ctx.tema, [
            ("id", "ID", 45, "center"), ("nombre", "Nombre", 160, "w"), ("ini", "Inicio", 110, "center"),
            ("fin", "Fin", 110, "center"), ("estado", "Estado", 100, "center")])
        self._tabla.grid(row=0, column=0, sticky="nsew")

    def actualizar(self) -> None:
        self.presentador.cargar()

    def _nuevo(self) -> None:
        datos = self._pedir("Nuevo período académico", [
            Campo("nombre", "Nombre (ej. 2026-2)"), Campo("ini", "Fecha de inicio (AAAA-MM-DD)", "fecha"),
            Campo("fin", "Fecha de fin (AAAA-MM-DD)", "fecha")])
        if datos:
            self.presentador.crear(datos["nombre"], datos["ini"], datos["fin"])


# =================================================================== sesiones
class VistaSesiones(VistaConTabla):
    clave, titulo = "sesiones", "Sesiones de clase"
    subtitulo = "Cree sesiones en borrador y el coordinador las aprueba o rechaza"
    icono = "sesiones"
    roles = (ADMINISTRADOR, COORDINADOR)

    def _crear_presentador(self) -> PresentadorSesiones:
        return PresentadorSesiones(self, self.ctx.sistema, **self._dependencias())

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
                                    values=list(PresentadorSesiones.FILTROS))
        self._estado.current(0)
        self._estado.pack(side="left")
        self._estado.bind("<<ComboboxSelected>>", lambda _e: self.actualizar())
        self._tabla = Tabla(self.cuerpo, t, COLUMNAS_SESION)
        self._tabla.grid(row=1, column=0, sticky="nsew")

    def actualizar(self) -> None:
        self.presentador.cargar(self._estado.get())

    def _nueva(self) -> None:
        if self.presentador.faltan_datos():      # el presentador avisa qué falta
            return
        op = self.presentador.opciones_formulario()
        datos = self._pedir("Nueva sesión de clase", [
            Campo("dia", "Día", "opcion", op["dia"]),
            Campo("ini", "Hora de inicio (HH:MM)", "hora", inicial="07:00"),
            Campo("fin", "Hora de fin (HH:MM)", "hora", inicial="09:00"),
            Campo("cupo", "Cupo de estudiantes", "entero", inicial="30"),
            Campo("asig", "Asignatura", "opcion", op["asignatura"]),
            Campo("doc", "Docente", "opcion", op["docente"]),
            Campo("aula", "Aula", "opcion", op["aula"])])
        if datos:
            self.presentador.crear(datos["dia"], datos["ini"], datos["fin"], datos["cupo"],
                                   datos["asig"], datos["doc"], datos["aula"])

    def _aprobar(self) -> None:
        elegido = self._seleccion_de(self._tabla, "una sesión")
        if elegido is not None:
            self.presentador.aprobar(int(elegido))

    def _rechazar(self) -> None:
        elegido = self._seleccion_de(self._tabla, "una sesión")
        if elegido is not None:
            self.presentador.rechazar(int(elegido))   # el presentador pide el motivo

    def _duplicar(self) -> None:
        """[PATRÓN: Prototype] Copia la sesión elegida a otro día sin volver a escribir sus datos."""
        elegido = self._seleccion_de(self._tabla, "la sesión a duplicar")
        if elegido is None:
            return
        datos = self._pedir("Duplicar sesión a otro día", [
            Campo("dia", "Nuevo día", "opcion", self.presentador.opciones_formulario()["dia"]),
            Campo("ini", "Nueva hora de inicio (opcional)", "hora", opcional=True),
            Campo("fin", "Nueva hora de fin (opcional)", "hora", opcional=True)], "Duplicar")
        if datos:
            self.presentador.duplicar(int(elegido), datos["dia"], datos["ini"], datos["fin"])


# =================================================================== horario
class VistaHorario(VistaBase, IVistaHorario):
    clave, titulo = "horario", "Horario semanal"
    subtitulo = "Cuadrícula de lunes a sábado; haga clic en un bloque para ver el detalle"
    icono = "horario"
    roles = (ADMINISTRADOR, COORDINADOR, DOCENTE)

    def _crear_presentador(self) -> PresentadorHorario:
        return PresentadorHorario(self, self.ctx.sistema, **self._dependencias())

    def _construir(self) -> None:
        t = self.ctx.tema
        self._bloques: Sequence[BloqueHorario] = []   # lo último que mandó el presentador
        self._horas = (7, 21)
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
        for combo in (self._docente, self._periodo):   # al cambiar un filtro, decide el presentador
            combo.bind("<<ComboboxSelected>>",
                       lambda _e: self.presentador.filtrar(self._docente.get(), self._periodo.get()))
        # Leyenda de colores (a la derecha).
        for estado in ("RECHAZADA", "APROBADA", "BORRADOR"):
            fondo, borde = COLOR_ESTADO[estado]
            tk.Label(barra, text=f" {estado.capitalize()} ", background=fondo, foreground=borde,
                     font=t.f_chica).pack(side="right", padx=(t.px(4), 0))
        self._lienzo = tk.Canvas(self.cuerpo, background=COLORES["fondo"], highlightthickness=0)
        self._lienzo.grid(row=1, column=0, sticky="nsew")
        # Al cambiar de tamaño se vuelve a pintar lo mismo (no hace falta preguntar al presentador).
        self._lienzo.bind("<Configure>", lambda _e: self._pintar())

    def actualizar(self) -> None:
        self.presentador.cargar(self._docente.get(), self._periodo.get())

    # ------------------------------------------------------------ IVistaHorario
    def mostrar_filtros(self, docentes, periodos, docente: str, periodo: str, docente_fijo: bool) -> None:
        llenar_combo(self._docente, docentes, docente)
        llenar_combo(self._periodo, periodos, periodo)
        self._docente.configure(state="disabled" if docente_fijo else "readonly")

    def dibujar_horario(self, bloques: Sequence[BloqueHorario], hora_inicio: int, hora_fin: int) -> None:
        self._bloques, self._horas = bloques, (hora_inicio, hora_fin)
        self._pintar()

    # ------------------------------------------------------------ dibujo (solo píxeles)
    def _pintar(self) -> None:
        """Convierte días y horas en coordenadas del Canvas. Qué sesiones mostrar y en qué
        carril va cada una ya lo decidió el presentador (asignar_carriles)."""
        c, t = self._lienzo, self.ctx.tema
        c.delete("all")
        ancho, alto = c.winfo_width(), c.winfo_height()
        if ancho < 120 or alto < 120:
            return
        izq, sup, der, inf = t.px(52), t.px(28), t.px(4), t.px(4)
        h0, h1 = self._horas
        dias = list(DiaSemana)
        ancho_dia = (ancho - izq - der) / len(dias)
        alto_hora = (alto - sup - inf) / (h1 - h0)
        c.create_rectangle(izq, sup, ancho - der, alto - inf, fill=COLORES["tarjeta"], outline=COLORES["borde"])
        for h in range(h0, h1 + 1):                       # líneas y etiquetas de horas
            y = sup + (h - h0) * alto_hora
            c.create_line(izq, y, ancho - der, y, fill=COLORES["borde"])
            # [REFACTOR] Antes aquí había un  'if h < h1 or True:'  que siempre era verdadero.
            c.create_text(izq - t.px(6), y, text=f"{h:02d}:00", anchor="e",
                          fill=COLORES["texto_suave"], font=t.f_chica)
        for i, d in enumerate(dias):                      # columnas y títulos de días
            x = izq + i * ancho_dia
            c.create_line(x, sup, x, alto - inf, fill=COLORES["borde"])
            c.create_text(x + ancho_dia / 2, sup / 2, text=d.name.capitalize(), font=t.f_negrita)
        linea = t.f_chica.metrics("linespace")
        for b in self._bloques:
            i = dias.index(b.dia)
            ancho_bloque = (ancho_dia - 4) / b.carriles
            x0 = izq + i * ancho_dia + 2 + b.carril * ancho_bloque
            y0 = sup + (minutos_del_dia(b.inicio) / 60 - h0) * alto_hora + 1
            y1 = sup + (minutos_del_dia(b.fin) / 60 - h0) * alto_hora - 1
            fondo, borde = COLOR_ESTADO[b.estado]
            etiqueta = f"s{b.id}"
            c.create_rectangle(x0, y0, x0 + ancho_bloque - 2, y1, fill=fondo, outline=borde,
                               width=1, tags=(etiqueta,))
            caben = max(1, int((y1 - y0 - 4) // linea))
            texto = "\n".join(recortar_texto(t.f_chica, l, int(ancho_bloque - t.px(10)))
                              for l in b.lineas[:caben])
            c.create_text(x0 + t.px(4), y0 + t.px(3), anchor="nw", text=texto, fill=borde,
                          font=t.f_chica, tags=(etiqueta,))
            c.tag_bind(etiqueta, "<Button-1>", lambda _e, txt=b.detalle: self.avisar(txt, "Detalle de la sesión"))


# =================================================================== reportes
class VistaReportes(VistaBase, IVistaReportes):
    clave, titulo = "reportes", "Reportes"
    subtitulo = "Genere un reporte, revíselo en pantalla y expórtelo a CSV"
    icono = "reportes"
    roles = (ADMINISTRADOR, COORDINADOR)

    def _crear_presentador(self) -> PresentadorReportes:
        return PresentadorReportes(self, self.ctx.sistema, **self._dependencias())

    def _construir(self) -> None:
        t = self.ctx.tema
        self.encabezado.agregar_boton("Exportar CSV", self._exportar)
        self.encabezado.agregar_boton("Generar reporte", self._generar, "Acento.TButton")
        self.cuerpo.rowconfigure(0, weight=0)
        self.cuerpo.rowconfigure(1, weight=1)
        barra = ttk.Frame(self.cuerpo)
        barra.grid(row=0, column=0, sticky="ew", pady=(0, t.px(8)))
        ttk.Label(barra, text="Tipo:").pack(side="left", padx=(0, t.px(6)))
        self._tipo = ttk.Combobox(barra, state="readonly", width=22, values=list(PresentadorReportes.TIPOS))
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

    def actualizar(self) -> None:
        self.presentador.cargar(self._periodo.get())

    # ------------------------------------------------------------ IVistaReportes
    def mostrar_periodos(self, periodos, elegido: str) -> None:
        llenar_combo(self._periodo, periodos, elegido)

    def mostrar_reporte(self, texto: str) -> None:
        self._texto.configure(state="normal")
        self._texto.delete("1.0", "end")
        self._texto.insert("1.0", texto)
        self._texto.configure(state="disabled")

    # ------------------------------------------------------------ eventos
    def _generar(self) -> None:
        self.presentador.generar(self._tipo.current(), self._periodo.get())

    def _exportar(self) -> None:
        nombre = self.presentador.nombre_archivo()   # None si aún no hay reporte (ya avisó)
        if nombre is None:
            return
        # Elegir DÓNDE guardar es parte de la vista (un cuadro de diálogo de tkinter).
        ruta = filedialog.asksaveasfilename(parent=self, title="Guardar reporte", defaultextension=".csv",
                                            initialfile=nombre, filetypes=[("CSV (Excel)", "*.csv")])
        if ruta:
            self.presentador.exportar_csv(ruta)


# ================================================================ estadísticas
class VistaEstadisticas(VistaBase, IVistaEstadisticas):
    """Gráficas e indicadores. Los números los calcula EstadisticasHorario, el presentador
    les da formato y las gráficas (GraficoBarras, GraficoDona, GraficoProgreso) solo los dibujan."""
    clave, titulo = "estadisticas", "Estadísticas"
    subtitulo = "Resumen visual de la carga y la ocupación del horario"
    icono = "estadisticas"

    def _crear_presentador(self) -> PresentadorEstadisticas:
        return PresentadorEstadisticas(self, self.ctx.sistema, **self._dependencias())

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
        self.presentador.cargar(self._periodo.get())

    # ------------------------------------------------------------ IVistaEstadisticas
    def mostrar_periodos(self, periodos, elegido: str) -> None:
        llenar_combo(self._periodo, periodos, elegido)

    def mostrar_indicadores(self, textos: dict[str, str]) -> None:
        for clave, texto in textos.items():
            self._numeros[clave].configure(text=texto)

    def mostrar_graficos(self, por_estado, por_dia, por_docente, por_aula) -> None:
        animar = self.winfo_ismapped()      # solo se anima si la pantalla está a la vista
        self._g_estado.poner(por_estado, animar)
        self._g_dia.poner(por_dia, animar)
        self._g_docente.poner(por_docente, animar)
        self._g_aula.poner(por_aula, animar)


# ==================================================================== usuarios
class VistaUsuarios(VistaConTabla):
    """Solo el administrador: crea cuentas de acceso para los docentes."""
    clave, titulo = "usuarios", "Usuarios y accesos"
    subtitulo = "Cuentas para iniciar sesión (el usuario de un docente es su correo)"
    icono = "usuarios"
    roles = (ADMINISTRADOR,)

    def _crear_presentador(self) -> PresentadorUsuarios:
        return PresentadorUsuarios(self, self.ctx.sistema, self.ctx.autenticador, **self._dependencias())

    def _construir(self) -> None:
        self.encabezado.agregar_boton("Eliminar cuenta", self._eliminar)
        self.encabezado.agregar_boton("Restablecer contraseña", self._restablecer)
        self.encabezado.agregar_boton("+ Cuenta para docente", self._nueva, "Acento.TButton")
        self._tabla = Tabla(self.cuerpo, self.ctx.tema, [
            ("usuario", "Usuario", 230, "w"), ("nombre", "Nombre", 190, "w"),
            ("rol", "Rol", 120, "center"), ("doc", "Docente (ID)", 100, "center")])
        self._tabla.grid(row=0, column=0, sticky="nsew")

    def actualizar(self) -> None:
        self.presentador.cargar()

    def _nueva(self) -> None:
        if not self.presentador.puede_crear():
            return
        datos = self._pedir("Crear cuenta para un docente", [
            Campo("doc", "Docente", "opcion", self.presentador.opciones_docentes()),
            Campo("clave", "Contraseña (mín. 6)", "clave"), Campo("repetir", "Repetir contraseña", "clave")],
            "Crear cuenta")
        if datos:
            self.presentador.crear_cuenta_docente(datos["doc"], datos["clave"], datos["repetir"])

    def _restablecer(self) -> None:
        elegido = self._seleccion_de(self._tabla, "una cuenta")
        if elegido is None:
            return
        datos = self._pedir(f"Nueva contraseña para {elegido}", [
            Campo("clave", "Contraseña nueva (mín. 6)", "clave"), Campo("repetir", "Repetir", "clave")], "Cambiar")
        if datos:
            self.presentador.restablecer_clave(elegido, datos["clave"], datos["repetir"])

    def _eliminar(self) -> None:
        elegido = self._seleccion_de(self._tabla, "una cuenta")
        if elegido is not None:
            self.presentador.eliminar_cuenta(elegido)   # el presentador pide la confirmación


# [SOLID-O] Para agregar una pantalla nueva: crear la vista (y su presentador) y añadirla a esta lista.
VISTAS_POR_DEFECTO: tuple = (VistaInicio, VistaEstadisticas, VistaHorario, VistaSesiones, VistaDocentes,
                             VistaAulas, VistaAsignaturas, VistaPeriodos, VistaReportes, VistaUsuarios)

"""COMPONENTES REUTILIZABLES de la interfaz: tabla, tarjeta, encabezado y formularios.  [NUEVO]

[SOLID-S] Cada componente hace UNA cosa y no sabe nada del sistema académico
(no importa SistemaAcademico): solo dibuja y devuelve datos. Las pantallas
(vistas.py) los combinan.
[SOLID-O] Un formulario nuevo no requiere crear una clase de ventana: se
describe con una lista de objetos Campo y pedir_datos() lo dibuja.
"""
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from datetime import date, datetime
from tkinter import ttk
from typing import Any, Callable, Optional, Sequence

from .tema import COLOR_ESTADO, COLORES, Tema


# ============================================================ ayudas de texto
def recortar_texto(fuente, texto: str, ancho: float) -> str:
    """Acorta el texto con '…' para que quepa en 'ancho' píxeles.
    [REFACTOR] Antes estaba escrito dos veces: en el horario (vistas.py) y en las gráficas."""
    if fuente.measure(texto) <= ancho:
        return texto
    while texto and fuente.measure(texto + "…") > ancho:
        texto = texto[:-1]
    return texto + "…" if texto else ""


def llenar_combo(combo, valores, elegido: str) -> None:
    """Pone las opciones de una lista desplegable y deja marcada la elegida.
    [REFACTOR] Antes se repetía en Horario (2 veces), Reportes y Estadísticas."""
    combo.configure(values=list(valores))
    combo.set(elegido)


# ============================================================ encabezado de página
class Encabezado(ttk.Frame):
    """Título + subtítulo a la izquierda y una zona de botones a la derecha."""

    def __init__(self, master, tema: Tema, titulo: str, subtitulo: str = ""):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text=titulo, style="Titulo.TLabel").grid(row=0, column=0, sticky="w")
        if subtitulo:
            ttk.Label(self, text=subtitulo, style="Suave.TLabel").grid(row=1, column=0, sticky="w")
        self.acciones = ttk.Frame(self)
        self.acciones.grid(row=0, column=1, rowspan=2, sticky="e")

    def agregar_boton(self, texto: str, comando: Callable[[], None],
                      estilo: str = "Suave.TButton") -> ttk.Button:
        boton = ttk.Button(self.acciones, text=texto, command=comando, style=estilo)
        boton.pack(side="left", padx=(6, 0))
        return boton


# ======================================================================== tabla
class Tabla(ttk.Frame):
    """Tabla con barras de desplazamiento que aparecen solo cuando hacen falta.

    Las columnas se estiran con la ventana (stretch) y se pueden achicar hasta un
    mínimo: así la misma tabla sirve en una laptop de 14" y en un monitor grande.
    """

    def __init__(self, master, tema: Tema, columnas: Sequence[tuple]):
        """columnas: lista de (id, título, ancho_de_diseño, alineación)."""
        super().__init__(master, style="Tarjeta.TFrame", borderwidth=1, relief="solid")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._arbol = ttk.Treeview(self, columns=[c[0] for c in columnas],
                                   show="headings", selectmode="browse")
        for id_col, titulo, ancho, ancla in columnas:
            self._arbol.heading(id_col, text=titulo, anchor=ancla)
            self._arbol.column(id_col, width=tema.px(ancho), minwidth=tema.px(ancho * 0.55),
                               anchor=ancla, stretch=True)
        vertical = ttk.Scrollbar(self, orient="vertical", command=self._arbol.yview)
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self._arbol.xview)
        self._arbol.configure(yscrollcommand=lambda a, b: self._auto(vertical, a, b),
                              xscrollcommand=lambda a, b: self._auto(horizontal, a, b))
        self._arbol.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self._arbol.tag_configure("impar", background=COLORES["fila_alt"])
        for estado, (fondo, _) in COLOR_ESTADO.items():  # filas coloreadas por estado
            self._arbol.tag_configure(estado, background=fondo)

    @staticmethod
    def _auto(barra: ttk.Scrollbar, primero: str, ultimo: str) -> None:
        """Oculta la barra cuando todo el contenido ya cabe."""
        if float(primero) <= 0.0 and float(ultimo) >= 1.0:
            barra.grid_remove()
        else:
            barra.grid()
        barra.set(primero, ultimo)

    def cargar(self, filas: Sequence[tuple]) -> None:
        """filas: lista de (clave, valores, etiqueta_opcional). Conserva la selección."""
        anterior = self.seleccion()
        self._arbol.delete(*self._arbol.get_children())
        for i, (clave, valores, etiqueta) in enumerate(filas):
            self._arbol.insert("", "end", iid=str(clave), values=valores,
                               tags=(etiqueta if etiqueta else ("impar" if i % 2 else ""),))
        if anterior is not None and self._arbol.exists(anterior):
            self._arbol.selection_set(anterior)

    def seleccion(self) -> Optional[str]:
        elegidas = self._arbol.selection()
        return elegidas[0] if elegidas else None


# ===================================================================== tarjeta KPI
class TarjetaDato(ttk.Frame):
    """Tarjeta con un número grande, una etiqueta y un círculo de color con icono."""

    def __init__(self, master, tema: Tema, etiqueta: str, color: str = COLORES["acento"], icono=None):
        super().__init__(master, style="Tarjeta.TFrame", borderwidth=1, relief="solid")
        lado = tema.px(46)
        circulo = tk.Canvas(self, width=lado + tema.px(18), height=lado, highlightthickness=0,
                            background=COLORES["tarjeta"])
        circulo.pack(side="left", padx=(tema.px(10), 0), pady=tema.px(10))
        circulo.create_oval(tema.px(9), 0, tema.px(9) + lado, lado, fill=color, outline="")
        if icono is not None:   # [NUEVO] imagen PNG dentro del círculo
            circulo.create_image(tema.px(9) + lado / 2, lado / 2, image=icono)
        cuerpo = ttk.Frame(self, style="Tarjeta.TFrame", padding=(tema.px(4), tema.px(8), tema.px(10), tema.px(8)))
        cuerpo.pack(side="left", fill="both", expand=True)
        self._numero = ttk.Label(cuerpo, text="0", style="Numero.TLabel")
        self._numero.pack(anchor="w")
        ttk.Label(cuerpo, text=etiqueta, style="TarjetaSuave.TLabel").pack(anchor="w")

    def poner(self, valor) -> None:
        self._numero.configure(text=str(valor))


class Hero(tk.Canvas):
    """Franja de bienvenida con imagen de fondo y dos líneas de texto.  [NUEVO]
    El Canvas usa el color final de la imagen como fondo: en pantallas anchas la franja
    se continúa sin cortes."""

    def __init__(self, master, tema: Tema, imagen=None):
        alto = imagen.height() if imagen else tema.px(120)
        super().__init__(master, height=alto, highlightthickness=0, background="#7C3AED")
        self._tema = tema
        self._ancho_img = imagen.width() if imagen else 0
        self._img = self.create_image(0, 0, image=imagen, anchor="nw") if imagen else None
        self.bind("<Configure>", self._ajustar)
        self._t1 = self.create_text(tema.px(26), alto * 0.36, anchor="w", fill="white", font=tema.f_titulo)
        self._t2 = self.create_text(tema.px(26), alto * 0.68, anchor="w", fill="#E4E0FF", font=tema.f_sub)

    def _ajustar(self, evento) -> None:
        """Si la ventana es más angosta que la imagen se recorta el lado izquierdo (así el
        final del degradado siempre queda a la derecha); si es más ancha, el color continúa."""
        if self._img is None:
            return
        if evento.width <= self._ancho_img:
            self.itemconfigure(self._img, anchor="ne")
            self.coords(self._img, evento.width, 0)
        else:
            self.itemconfigure(self._img, anchor="nw")
            self.coords(self._img, 0, 0)

    def poner(self, titulo: str, subtitulo: str) -> None:
        self.itemconfigure(self._t1, text=titulo)
        self.itemconfigure(self._t2, text=subtitulo)


# ================================================================== formularios
@dataclass
class Campo:
    """Describe un dato que pide un formulario.

    tipo: 'texto' | 'entero' | 'fecha' | 'hora' | 'opcion' | 'clave' (se muestra con puntos)
    opciones: para 'opcion', lista de (texto_visible, valor_devuelto).
    """
    nombre: str
    etiqueta: str
    tipo: str = "texto"
    opciones: Sequence[tuple] = ()
    inicial: str = ""
    minimo: int = 1
    opcional: bool = False


class _Dialogo(tk.Toplevel):
    """Ventana modal que valida lo escrito y muestra el error SIN cerrarse."""

    def __init__(self, padre, tema: Tema, titulo: str, campos: Sequence[Campo], aceptar: str):
        super().__init__(padre)
        self.title(titulo)
        self.configure(background=COLORES["fondo"])
        self.resizable(False, False)
        self.transient(padre.winfo_toplevel())
        self.resultado: Optional[dict] = None
        self._campos = list(campos)
        self._widgets: list[Any] = []

        marco = ttk.Frame(self, padding=(tema.px(18), tema.px(14)))
        marco.pack(fill="both", expand=True)
        marco.columnconfigure(1, weight=1)
        ttk.Label(marco, text=titulo, font=tema.f_logo).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, tema.px(10)))
        for i, campo in enumerate(self._campos, start=1):
            ttk.Label(marco, text=campo.etiqueta).grid(
                row=i, column=0, sticky="w", padx=(0, tema.px(12)), pady=tema.px(4))
            if campo.tipo == "opcion":
                w = ttk.Combobox(marco, state="readonly", width=34,
                                 values=[t for t, _ in campo.opciones])
                if campo.opciones:
                    w.current(0)
            else:
                w = ttk.Entry(marco, width=36, show="•" if campo.tipo == "clave" else "")
                w.insert(0, campo.inicial)
            w.grid(row=i, column=1, sticky="ew", pady=tema.px(4))
            self._widgets.append(w)
        self._error = ttk.Label(marco, text="", foreground=COLORES["error"], wraplength=tema.px(380))
        self._error.grid(row=len(self._campos) + 1, column=0, columnspan=2, sticky="w", pady=(tema.px(6), 0))
        botones = ttk.Frame(marco)
        botones.grid(row=len(self._campos) + 2, column=0, columnspan=2, sticky="e", pady=(tema.px(10), 0))
        ttk.Button(botones, text="Cancelar", style="Suave.TButton", command=self.destroy).pack(side="left", padx=6)
        ttk.Button(botones, text=aceptar, style="Acento.TButton", command=self._aceptar).pack(side="left")

        self.bind("<Return>", lambda _e: self._aceptar())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.update_idletasks()
        x = padre.winfo_rootx() + (padre.winfo_width() - self.winfo_width()) // 2
        y = padre.winfo_rooty() + max(20, (padre.winfo_height() - self.winfo_height()) // 3)
        self.geometry(f"+{max(0, x)}+{max(0, y)}")
        if self._widgets:
            self._widgets[0].focus_set()
        self.after(50, self._tomar_foco)

    def _tomar_foco(self) -> None:
        try:
            self.grab_set()   # modal: bloquea la ventana de atrás hasta cerrar
        except tk.TclError:
            pass

    def _aceptar(self) -> None:
        try:
            datos = {c.nombre: self._leer(c, w) for c, w in zip(self._campos, self._widgets)}
        except ValueError as e:
            self._error.configure(text=str(e))
            return
        self.resultado = datos
        self.destroy()

    @staticmethod
    def _leer(campo: Campo, w) -> Any:
        if campo.tipo == "opcion":
            i = w.current()
            if i < 0:
                raise ValueError(f"{campo.etiqueta}: elija una opción")
            return campo.opciones[i][1]
        if campo.tipo == "clave":          # las contraseñas no se recortan ni se cambian
            if not w.get():
                raise ValueError(f"{campo.etiqueta}: complete este campo")
            return w.get()
        texto = w.get().strip()
        if not texto:
            if campo.opcional:
                return None
            raise ValueError(f"{campo.etiqueta}: complete este campo")
        if campo.tipo == "entero":
            try:
                valor = int(texto)
            except ValueError:
                raise ValueError(f"{campo.etiqueta}: debe ser un número entero") from None
            if valor < campo.minimo:
                raise ValueError(f"{campo.etiqueta}: debe ser al menos {campo.minimo}")
            return valor
        if campo.tipo == "fecha":
            try:
                return date.fromisoformat(texto)
            except ValueError:
                raise ValueError(f"{campo.etiqueta}: use el formato AAAA-MM-DD (2026-05-01)") from None
        if campo.tipo == "hora":
            try:
                return datetime.strptime(texto, "%H:%M").time()
            except ValueError:
                raise ValueError(f"{campo.etiqueta}: use el formato HH:MM (07:30)") from None
        return texto


def pedir_datos(padre, tema: Tema, titulo: str, campos: Sequence[Campo],
                aceptar: str = "Guardar") -> Optional[dict]:
    """Muestra el formulario y devuelve {nombre: valor}, o None si se cancela."""
    dialogo = _Dialogo(padre, tema, titulo, campos, aceptar)
    padre.wait_window(dialogo)
    return dialogo.resultado

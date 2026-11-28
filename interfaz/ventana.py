"""VENTANA PRINCIPAL: barra lateral + pantallas + barra de estado.  [NUEVO]

Diseño pensado para laptops de 14 a 16 pulgadas (y monitores mayores):
  * Tamaño inicial = 90 % del ancho y 86 % del alto de la pantalla, con un máximo.
  * Tamaño MÍNIMO para que nada se corte; si la pantalla es muy chica, aparecen
    barras de desplazamiento en las tablas.
  * Todo lo demás se estira con la ventana (grid con weight).
  * F11 alterna pantalla completa; Esc la termina; Ctrl+1...9 cambia de pantalla.

[NUEVO] Recibe la Cuenta que inició sesión y muestra SOLO las pantallas que su rol permite
(cada VistaBase declara sus 'roles'). La barra lateral tiene iconos, el usuario conectado,
"Mi contraseña" y "Cerrar sesión".

[U2-INYECCIÓN-DEPENDENCIAS] La ventana RECIBE el sistema y el almacén ya creados
    (los crea main_gui.py) y también la lista de pantallas.
[SOLID-I] El tipo del almacén es AlmacenamientoEscritura: la ventana solo necesita guardar.
[SOLID-D] Depende de abstracciones (VistaBase, AlmacenamientoEscritura), no de clases concretas.
[SOLID-O] Una pantalla nueva se añade en VISTAS_POR_DEFECTO sin editar esta clase.
[PATRÓN: Observer (simple)] Cuando una pantalla cambia datos llama a notificar_cambio
    y esta ventana avisa a TODAS las pantallas para que se refresquen.
[U2-POLIMORFISMO-ABSTRACTAS] Se llama a vista.actualizar() en cada pantalla sin
    conocer su tipo concreto.
[MVP] [MODIFICADO] La ventana también es una VISTA (implementa IVista) para el botón
    "Mi contraseña": la lógica de cambiar la clave está en PresentadorMiClave.
"""
from __future__ import annotations

import tkinter as tk
from dataclasses import replace
from tkinter import messagebox, ttk
from typing import Optional, Sequence

from presentadores import IVista, PresentadorMiClave, rol_efectivo
from servicios import (AlmacenamientoEscritura, Autenticador, Cuenta, SistemaAcademico)

from .componentes import Campo, pedir_datos
from .imagenes import Imagenes
from .tema import COLORES, Tema
from .vistas import VISTAS_POR_DEFECTO, Contexto, VistaBase


class VentanaPrincipal(tk.Tk, IVista):
    def __init__(self, sistema: SistemaAcademico, almacen: AlmacenamientoEscritura,
                 cuenta: Cuenta, autenticador: Autenticador,
                 vistas: Optional[Sequence[type]] = None):
        super().__init__()
        self.sistema = sistema
        self._almacen = almacen
        self._autenticador = autenticador
        self.cerro_sesion = False       # True si el usuario pulsó "Cerrar sesión" (vuelve al login)
        self.cuenta = replace(cuenta, rol=rol_efectivo(cuenta.rol, cuenta.id_docente, sistema))
        self.title("KMDM Academy System - Gestor de horarios")
        self.tema = Tema(self)
        self.imagenes = Imagenes(self.tema)
        self._ajustar_tamano()
        self._pantalla_completa = False
        self._temporizador = None

        # Estructura: [barra lateral | contenido] arriba y barra de estado abajo.
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._crear_barra_lateral()
        self._contenedor = ttk.Frame(self)
        self._contenedor.grid(row=0, column=1, sticky="nsew")
        self._contenedor.columnconfigure(0, weight=1)
        self._contenedor.rowconfigure(0, weight=1)
        self._crear_barra_estado()

        ctx = Contexto(sistema=sistema, tema=self.tema, guardar=self._guardar,
                       notificar_cambio=self.refrescar, mensaje=self._mensaje, navegar=self.mostrar,
                       cuenta=self.cuenta, imagenes=self.imagenes, autenticador=autenticador)
        self._vistas: dict[str, VistaBase] = {}
        self._botones: dict[str, ttk.Button] = {}
        for clase in (vistas or VISTAS_POR_DEFECTO):
            if self.cuenta.rol not in clase.roles:     # [NUEVO] permisos por rol
                continue
            vista = clase(self._contenedor, ctx)
            vista.grid(row=0, column=0, sticky="nsew")
            self._vistas[clase.clave] = vista
            self._agregar_boton_nav(clase.clave, clase.titulo, clase.icono)
        self._atajos()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.mostrar(next(iter(self._vistas)))
        self.refrescar()

    # ------------------------------------------------------------ tamaño y estructura
    def _ajustar_tamano(self) -> None:
        """Ventana proporcional a la pantalla: cabe en una laptop de 14" y no queda enorme."""
        t = self.tema
        ancho_pantalla, alto_pantalla = self.winfo_screenwidth(), self.winfo_screenheight()
        ancho = min(int(ancho_pantalla * 0.90), t.px(1280))
        alto = min(int(alto_pantalla * 0.86), t.px(760))
        self.minsize(min(t.px(940), ancho_pantalla - 40), min(t.px(580), alto_pantalla - 80))
        x = max(0, (ancho_pantalla - ancho) // 2)
        y = max(0, (alto_pantalla - alto) // 2 - t.px(20))
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _crear_barra_lateral(self) -> None:
        t = self.tema
        self._barra = ttk.Frame(self, style="Barra.TFrame", width=t.px(206))
        self._barra.grid(row=0, column=0, sticky="ns")
        self._barra.grid_propagate(False)
        cabecera = ttk.Frame(self._barra, style="Barra.TFrame")
        cabecera.pack(fill="x", padx=t.px(14), pady=(t.px(14), t.px(10)))
        logo = self.imagenes.logo(64)
        if logo:    # [NUEVO] logo del sistema
            ttk.Label(cabecera, image=logo, style="Logo.TLabel").pack(side="left", padx=(0, t.px(10)))
        textos = ttk.Frame(cabecera, style="Barra.TFrame")
        textos.pack(side="left")
        ttk.Label(textos, text="KMDM", style="Logo.TLabel").pack(anchor="w")
        ttk.Label(textos, text="Academy", style="BarraSub.TLabel").pack(anchor="w")
        self._zona_nav = ttk.Frame(self._barra, style="Barra.TFrame")
        self._zona_nav.pack(fill="x")

        # Parte de abajo: usuario conectado y sus acciones.
        usuario = ttk.Frame(self._barra, style="Barra.TFrame")
        usuario.pack(side="bottom", fill="x", padx=t.px(12), pady=(0, t.px(12)))
        ttk.Label(usuario, text=self.cuenta.nombre, style="BarraNombre.TLabel",
                  wraplength=t.px(176)).pack(anchor="w")
        ttk.Label(usuario, text=self.cuenta.rol.capitalize(), style="BarraSub.TLabel").pack(
            anchor="w", pady=(0, t.px(8)))
        for texto, icono, accion in (("  Mi contraseña", "candado", self._cambiar_mi_clave),
                                     ("  Cerrar sesión", "salir", self._cerrar_sesion)):
            ttk.Button(usuario, text=texto, image=self.imagenes.icono(icono), compound="left",
                       style="Salir.TButton", command=accion).pack(fill="x", pady=(0, t.px(4)))

    def _agregar_boton_nav(self, clave: str, texto: str, icono: str = "") -> None:
        boton = ttk.Button(self._zona_nav, text="  " + texto, style="Nav.TButton", compound="left",
                           image=self.imagenes.icono(icono) if icono else "",
                           command=lambda: self.mostrar(clave))
        boton.pack(fill="x")
        self._botones[clave] = boton

    def _crear_barra_estado(self) -> None:
        t = self.tema
        fondo = COLORES["cabecera"]
        barra = tk.Frame(self, background=fondo, height=t.px(26))
        barra.grid(row=1, column=0, columnspan=2, sticky="ew")
        self._estado = tk.Label(barra, text="Listo", background=fondo, foreground=COLORES["texto_suave"],
                                font=t.f_chica, anchor="w")
        self._estado.pack(side="left", padx=t.px(12), pady=t.px(3))
        tk.Label(barra, text="Los cambios se guardan automáticamente", background=fondo,
                 foreground=COLORES["texto_suave"], font=t.f_chica).pack(side="right", padx=t.px(12))

    def _atajos(self) -> None:
        self.bind("<F11>", lambda _e: self._alternar_pantalla_completa())
        self.bind("<Escape>", lambda _e: self._salir_pantalla_completa())
        for i, clave in enumerate(self._vistas, start=1):
            if i <= 9:
                self.bind(f"<Control-Key-{i}>", lambda _e, c=clave: self.mostrar(c))

    # ------------------------------------------------------------------ navegación
    def mostrar(self, clave: str) -> None:
        """Muestra la pantalla elegida y resalta su botón."""
        if clave not in self._vistas:      # el rol no tiene esa pantalla
            return
        self._vistas[clave].tkraise()
        for k, boton in self._botones.items():
            boton.configure(style="NavActivo.TButton" if k == clave else "Nav.TButton")
        self._vistas[clave].actualizar()

    def refrescar(self) -> None:
        """[PATRÓN: Observer (simple)] Todas las pantallas se actualizan tras un cambio."""
        for vista in self._vistas.values():
            vista.actualizar()   # [U2-POLIMORFISMO-ABSTRACTAS] mismo mensaje, distinta respuesta

    # ---------------------------------------------------------------- servicios
    def _mensaje(self, texto: str) -> None:
        self._estado.configure(text=texto)
        if self._temporizador:
            self.after_cancel(self._temporizador)
        self._temporizador = self.after(6000, lambda: self._estado.configure(text="Listo"))

    def _guardar(self) -> None:
        try:
            self._almacen.guardar(self.sistema)
        except OSError as error:
            messagebox.showerror("No se pudo guardar", f"No se pudieron guardar los datos:\n{error}", parent=self)

    def _alternar_pantalla_completa(self) -> None:
        self._pantalla_completa = not self._pantalla_completa
        self.attributes("-fullscreen", self._pantalla_completa)

    def _salir_pantalla_completa(self) -> None:
        if self._pantalla_completa:
            self._alternar_pantalla_completa()

    # ------------------------------------------------------------------ IVista
    # [MVP] Lo mínimo que PresentadorMiClave necesita de la ventana. [SOLID-I]
    def mostrar_mensaje(self, texto: str) -> None:
        self._mensaje(texto)

    def mostrar_error(self, texto: str) -> None:
        messagebox.showerror("No se pudo cambiar", texto, parent=self)

    def _cambiar_mi_clave(self) -> None:
        """La ventana solo muestra el formulario; validar y cambiar la clave lo hace el presentador."""
        datos = pedir_datos(self, self.tema, "Cambiar mi contraseña", [
            Campo("actual", "Contraseña actual", "clave"),
            Campo("nueva", "Contraseña nueva (mín. 6)", "clave"),
            Campo("repetir", "Repetir la nueva", "clave")], "Cambiar")
        if datos:
            PresentadorMiClave(self, self._autenticador, self.cuenta).cambiar(
                datos["actual"], datos["nueva"], datos["repetir"])

    def _cerrar_sesion(self) -> None:
        self.cerro_sesion = True
        self._cerrar()

    def _cerrar(self) -> None:
        self._guardar()
        self.destroy()

"""PANTALLA DE INICIO DE SESIÓN.  [NUEVO]

Muestra una ilustración a la izquierda y el formulario a la derecha. Si el usuario y la
contraseña son correctos, la ventana se cierra y main_gui.py abre el sistema con los
permisos del rol de esa cuenta (Administrador, Coordinador o Docente).

[U2-INYECCIÓN-DEPENDENCIAS] Recibe un Autenticador ya creado; no sabe dónde se guardan las cuentas.
[SOLID-D] Depende de la interfaz Autenticador, no de AutenticadorLocal.
[SOLID-S] Solo pide los datos y muestra el resultado; verificar claves es trabajo del Autenticador.
Seguridad: la clave se muestra con puntos, el mensaje de error es el mismo si falla el usuario
o la clave, y tras 5 intentos fallidos el botón se bloquea 20 segundos.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from servicios import Autenticador, AutenticadorLocal, Cuenta

from .imagenes import Imagenes
from .tema import COLORES, Tema

INTENTOS_MAXIMOS = 5
SEGUNDOS_BLOQUEO = 20


class VentanaLogin(tk.Tk):
    def __init__(self, autenticador: Autenticador):
        super().__init__()
        self.title("Iniciar sesión - KMDM Academy")
        self._auth = autenticador
        self.cuenta: Optional[Cuenta] = None
        self._fallos = 0
        self._bloqueo = 0
        self.tema = Tema(self)
        self.imagenes = Imagenes(self.tema)
        t = self.tema

        banner = self.imagenes.banner_login()
        ancho_b = banner.width() if banner else t.px(420)
        alto_b = banner.height() if banner else t.px(520)
        ancho_f = t.px(400)
        self.resizable(False, False)
        x = max(0, (self.winfo_screenwidth() - ancho_b - ancho_f) // 2)
        y = max(0, (self.winfo_screenheight() - alto_b) // 2 - t.px(20))
        self.geometry(f"{ancho_b + ancho_f}x{alto_b}+{x}+{y}")

        # ---- lado izquierdo: ilustración con el nombre del sistema
        izq = tk.Canvas(self, width=ancho_b, height=alto_b, highlightthickness=0,
                        background="#3B3FD0")
        izq.pack(side="left")
        if banner:
            izq.create_image(0, 0, image=banner, anchor="nw")
        logo = self.imagenes.logo(64 if t.escala < 1.35 else 96)
        if logo:
            izq.create_image(t.px(30), t.px(30), image=logo, anchor="nw")
        izq.create_text(t.px(30), t.px(110), anchor="nw", text="KMDM Academy", fill="white", font=t.f_titulo)
        izq.create_text(t.px(30), t.px(142), anchor="nw", fill="#DCE4FF", font=t.f_sub, width=ancho_b - t.px(60),
                        text="Gestión de horarios académicos:\nsesiones, aulas, docentes y reportes.")

        # ---- lado derecho: formulario
        der = ttk.Frame(self, style="Tarjeta.TFrame", padding=(t.px(38), t.px(30)))
        der.pack(side="left", fill="both", expand=True)
        centro = ttk.Frame(der, style="Tarjeta.TFrame")    # centrado vertical del formulario
        centro.place(relx=0, rely=0.5, anchor="w", relwidth=1)
        ttk.Label(centro, text="¡Bienvenido!", style="Tarjeta.TLabel", font=t.f_titulo).pack(anchor="w")
        ttk.Label(centro, text="Inicia sesión para continuar", style="TarjetaSuave.TLabel").pack(
            anchor="w", pady=(2, t.px(22)))

        ttk.Label(centro, text="Usuario", style="Tarjeta.TLabel", font=t.f_negrita).pack(anchor="w")
        self._usuario = ttk.Entry(centro, font=t.f_normal)
        self._usuario.pack(fill="x", pady=(t.px(4), t.px(12)), ipady=t.px(3))
        ttk.Label(centro, text="Contraseña", style="Tarjeta.TLabel", font=t.f_negrita).pack(anchor="w")
        self._clave = ttk.Entry(centro, show="•", font=t.f_normal)
        self._clave.pack(fill="x", pady=(t.px(4), t.px(6)), ipady=t.px(3))
        self._ver = tk.BooleanVar(value=False)
        ttk.Checkbutton(centro, text="Mostrar contraseña", variable=self._ver, command=self._alternar_ver,
                        style="Tarjeta.TCheckbutton").pack(anchor="w")

        self._error = ttk.Label(centro, text="", style="Tarjeta.TLabel", foreground=COLORES["error"],
                                wraplength=ancho_f - t.px(80))
        self._error.pack(anchor="w", pady=(t.px(10), t.px(4)))
        self._boton = ttk.Button(centro, text="Iniciar sesión", style="Acento.TButton", command=self._entrar)
        self._boton.pack(fill="x", ipady=t.px(4))
        if isinstance(autenticador, AutenticadorLocal) and autenticador.con_clave_inicial():
            ttk.Label(centro, style="TarjetaSuave.TLabel", wraplength=ancho_f - t.px(80), justify="left",
                      text="Primer uso: usuario  admin  y contraseña  admin123.\n"
                           "Cámbiala después en la pantalla Usuarios.").pack(anchor="w", pady=(t.px(18), 0))

        self.bind("<Return>", lambda _e: self._entrar())
        self.bind("<Escape>", lambda _e: self.destroy())
        self._usuario.focus_set()

    def _alternar_ver(self) -> None:
        self._clave.configure(show="" if self._ver.get() else "•")

    def _entrar(self) -> None:
        if self._bloqueo:
            return
        try:
            self.cuenta = self._auth.iniciar_sesion(self._usuario.get(), self._clave.get())
        except ValueError as error:
            self._fallos += 1
            self._clave.delete(0, "end")
            self._error.configure(text=str(error))
            if self._fallos >= INTENTOS_MAXIMOS:
                self._bloquear(SEGUNDOS_BLOQUEO)
            return
        self.destroy()

    def _bloquear(self, segundos: int) -> None:
        """Después de varios fallos se espera un momento (frena los intentos al azar)."""
        self._bloqueo = segundos
        self._boton.configure(state="disabled")
        self._cuenta_atras()

    def _cuenta_atras(self) -> None:
        if self._bloqueo <= 0:
            self._fallos = 0
            self._boton.configure(state="normal", text="Iniciar sesión")
            self._error.configure(text="")
            return
        self._error.configure(text=f"Demasiados intentos. Espera {self._bloqueo} s.")
        self._bloqueo -= 1
        self.after(1000, self._cuenta_atras)


def pedir_inicio_de_sesion(autenticador: Autenticador) -> Optional[Cuenta]:
    """Abre el login y devuelve la Cuenta, o None si se cerró la ventana sin entrar."""
    ventana = VentanaLogin(autenticador)
    ventana.mainloop()
    return ventana.cuenta

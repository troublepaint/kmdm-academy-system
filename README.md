# KMDM Academy System

Materia: Programacion Orientada a Objetos

Integrantes: 
Ronquillo Cruzatte Kerly Belén
Moreno Navarrete Marco Antonio
Chávez Merchán Mariuxi Magdalena
Muñoz Vásquez Dahiana
Bravo Rosado Yosvell Antonio

Gestor de horarios de clases en Python (POO), con menú de consola y guardado en JSON.

## Ejecutar (desde esta carpeta)

    python main_gui.py              # [NUEVO] interfaz gráfica con inicio de sesión (primer uso: admin / admin123)
    python main.py                  # programa con menú; guarda en data/datos.json
    python demo.py                  # demostración original, sin menú ni archivos
    python demo_solid_patrones.py   # demuestra SOLID, patrones y Unidad 2 (casos válidos e inválidos)
    python -m modelos.reportes      # prueba rápida de un módulo (sin ".py")
    python -m unittest discover -s tests -v   # [MVP] pruebas de los presentadores (sin abrir ventanas)

## Estructura

    main.py                  raíz de composición: crea y entrega ("inyecta") las dependencias
    main_gui.py              [NUEVO] raíz de composición de la interfaz gráfica
    interfaz/                VISTA gráfica (tkinter): tema, componentes, vistas (10 pantallas), ventana, login,
                             graficos (barras/dona/progreso), imagenes y recursos/ (PNG)
    consola/                 [MVP] VISTA de texto: menu.py (antes estaba en servicios/menu.py)
    presentadores/           [MVP] PRESENTADORES: un presentador por pantalla, sin tkinter
      base.py                interfaces de vista (IVista, IVistaDialogos, IVistaTabla) y PresentadorBase
      comun.py               funciones compartidas (antes estaban repetidas)
      sesiones.py  registros.py  paneles.py  reportes.py  cuentas.py
    tests/                   [MVP] test_presentadores.py: 13 pruebas con una vista falsa
    demo.py                  demostración de integración (original)
    demo_solid_patrones.py   [NUEVO] demostración de SOLID, patrones y Unidad 2
    modelos/                 clases del diagrama UML
      enums.py  usuarios.py  academico.py  infraestructura.py  horarios.py  administrador.py
      validaciones.py        [REFACTOR] validación común de textos obligatorios
      reportes.py            [MODIFICADO] jerarquía Reporte (abstracta) -> Horario / CargaDocente
      exportadores.py        [NUEVO] interfaz Exportador + TXT y CSV
      configuracion.py       [NUEVO] Singleton: reglas globales del horario
      fabrica_usuarios.py    [NUEVO] Factory Method: crea Docente / Coordinador
      constructor_sesion.py  [NUEVO] Builder: arma la SesionClase paso a paso
    servicios/               lógica y entrada/salida
      sistema.py             [MODIFICADO] reglas del negocio (SistemaAcademico)
      reglas.py              [NUEVO] interfaz ReglaSesion + 3 reglas
      almacenamiento.py      [MODIFICADO] interfaces segregadas (Escritura / Lectura)
      almacen.py             [MODIFICADO] AlmacenJSON y AlmacenMemoria
      autenticacion.py       [NUEVO] interfaz Autenticador + AutenticadorLocal (hash PBKDF2, roles)
      estadisticas.py        [NUEVO] cálculo de números para las gráficas
      archivos.py            [REFACTOR] escritura segura de JSON (datos y cuentas)
    data/datos.json          se crea al ejecutar (no se sube a Git)

## Arquitectura MVP (Modelo-Vista-Presentador)  [NUEVO]

    VISTA (pasiva)                       PRESENTADOR                        MODELO
    interfaz/vistas.py  (tkinter)  ─┐                                  SistemaAcademico
                                    ├─►  presentadores/   ──────────►  (servicios/ + modelos/)
    consola/menu.py     (terminal) ─┘    decide y prepara  ◄──────────
                        ◄──────────────  los datos

* **Modelo**: `SistemaAcademico` (fachada) y las clases de `modelos/`. No cambió.
* **Vista**: solo dibuja y avisa lo que hizo el usuario. Ya no llama a `SistemaAcademico`.
* **Presentador**: recibe el evento, llama al modelo, maneja errores, guarda y le dice a la
  vista qué mostrar (`mostrar_filas`, `mostrar_error`, `mostrar_mensaje`...). Es Python puro.
* Relación **uno a uno**: cada pantalla tiene su presentador. La vista conoce al presentador; el
  presentador conoce a la vista solo por su **interfaz** (`IVistaTabla`, `IVistaHorario`...).
* El **mismo presentador** sirve a la ventana y a la consola, y se prueba con una vista falsa
  (`tests/test_presentadores.py`).

| Pantalla | Vista (tkinter) | Presentador | También lo usa la consola |
|---|---|---|---|
| Inicio | `VistaInicio` | `PresentadorInicio` | |
| Estadísticas | `VistaEstadisticas` | `PresentadorEstadisticas` | |
| Horario | `VistaHorario` | `PresentadorHorario` | |
| Sesiones | `VistaSesiones` | `PresentadorSesiones` | opciones 7, 8, 9, 10, 14 |
| Docentes | `VistaDocentes` | `PresentadorDocentes` | opciones 1, 2, 11 |
| Aulas | `VistaAulas` | `PresentadorAulas` | opciones 5, 11 |
| Asignaturas | `VistaAsignaturas` | `PresentadorAsignaturas` | opciones 6, 11 |
| Períodos | `VistaPeriodos` | `PresentadorPeriodos` | opciones 3, 4, 11 |
| Reportes | `VistaReportes` | `PresentadorReportes` | opciones 12, 13 |
| Usuarios | `VistaUsuarios` | `PresentadorUsuarios` | |
| "Mi contraseña" | `VentanaPrincipal` | `PresentadorMiClave` | |

### Código duplicado que se eliminó (`[REFACTOR]` en los comentarios)

| Qué estaba repetido | Dónde estaba | Dónde quedó (una sola vez) |
|---|---|---|
| Ordenar sesiones por día y hora | 5 lugares: `sistema.py`, `reportes.py`, `menu.py` (2), `vistas.py` | `modelos/horarios.py: ordenar_por_horario()` |
| ID automático `max(id) + 1` | 4 lugares: `sistema.py` (3), `administrador.py` | `modelos/horarios.py: siguiente_id()` |
| Elegir el coordinador que actúa | `vistas.py` y `menu.py` | `PresentadorBase._elegir_coordinador()` |
| Intentar → guardar → refrescar → avisar | `VistaBase.ejecutar()` y cada opción de `menu.py` | `PresentadorBase._ejecutar()` |
| Comprobar que existan datos antes de crear una sesión | `vistas.py` (completo) y `menu.py` (solo el período) | `PresentadorSesiones.faltan_datos()` |
| Período seleccionado por defecto / buscar período por nombre | Horario, Reportes y Estadísticas | `presentadores/comun.py` |
| "Las contraseñas no coinciden" | 3 lugares (`vistas.py` 2, `ventana.py` 1) | `comun.validar_repeticion()` |
| Guardar el reporte en CSV | ventana (utf-8-sig) y consola (utf-8): **no eran iguales** | `PresentadorReportes.exportar_csv()` (siempre utf-8-sig) |
| Imprimir docentes / aulas / asignaturas / sesiones | 4 métodos `_imprimir_*` en `menu.py` | `MenuConsola.mostrar_filas()` (las filas las prepara el presentador) |
| `mostrar_filas` en 6 pantallas | `vistas.py` | `VistaConTabla` |
| "El texto no puede estar vacío" | 7 lugares del modelo (Asignatura, Periodo, Aula, AulaClasificacion, Reporte, Usuario) | `modelos/validaciones.py: texto_obligatorio()` |
| Pasar una hora a minutos (`hora * 60 + minuto`) | sesión, horario, estadísticas | `modelos/horarios.py: minutos_del_dia()` |
| "Primero debe generar el reporte" | `Reporte.exportar()` e `imprimir()` | `Reporte._exigir_generado()` |
| Bucle de búsqueda (`for ... if ... return ... raise`) | 8 métodos `buscar_*` de `SistemaAcademico` | `SistemaAcademico._buscar()` |
| Guardar JSON con archivo temporal | `AlmacenJSON` y `AutenticadorLocal` | `servicios/archivos.py: guardar_json_seguro()` |
| Crear sal + hash de la clave / "La cuenta no existe" | `AutenticadorLocal` (2 veces cada uno) | `_sal_y_hash()` y `_exigir_cuenta()` |
| Recortar texto con "…" | horario y gráficas | `componentes.recortar_texto()` |
| Llenar una lista desplegable | Horario (2), Reportes, Estadísticas | `componentes.llenar_combo()` |
| Lista de nombres de períodos | 4 presentadores | `comun.nombres_de_periodos()` |
| Color `#E7ECF5` escrito a mano | `ventana.py` (3) y `tema.py` | `COLORES["cabecera"]` |

### Código que no se usaba y se quitó

`AutenticadorLocal.existe()`, `EstadisticasHorario.sesiones` y `sesiones_por_asignatura()`,
`ConfiguracionSistema.restablecer()`, `Tabla.vaciar()` y el parámetro `al_doble_clic`, el estilo
de botón `Peligro`, el color `aviso` y un import sin usar en `demo_solid_patrones.py`.
Se **mantuvieron** métodos que no se llaman pero están en el diagrama de clases
(`actualizar_correo`, `esta_vigente`, `contiene_fecha`, `es_especializada`).

### Otras correcciones

* Horario: se quitó una condición inútil (`if h < h1 or True:`, siempre verdadera).
* `Aula` aceptaba nombre y ubicación vacíos (las demás clases validaban sus textos): ahora se validan.
* El login decía que la contraseña se cambia en "Usuarios"; en realidad es con el botón "Mi contraseña".

## Cómo encontrar lo aplicado: leyenda de etiquetas en los comentarios

Busca el texto de la etiqueta en el código (Ctrl+Shift+F en VS Code). `[NUEVO]` marca
lo agregado en esta entrega.

| Etiqueta | Qué significa | Dónde se aplicó |
|---|---|---|
| `[SOLID-S]` | Responsabilidad única | Reglas en `servicios/reglas.py` (una comprobación cada una); exportadores solo dan formato; vistas solo dibujan y presentadores solo deciden (MVP); `ConfiguracionSistema` solo guarda reglas globales |
| `[SOLID-O]` | Abierto/cerrado | Reglas nuevas, exportadores nuevos, reportes nuevos y roles nuevos se agregan SIN editar código existente (demostrado en `demo_solid_patrones.py`) |
| `[SOLID-L]` | Sustitución de Liskov | `CoordinadorAcademico` sustituye a `Docente` (`usuarios.py`, `ReporteCargaDocente`); los `Exportador` y `ReglaSesion` son intercambiables |
| `[SOLID-I]` | Segregación de interfaces | `almacenamiento.py`: `AlmacenamientoEscritura` y `AlmacenamientoLectura`; el menú solo depende de guardar; interfaces de vista pequeñas (`IVista` → `IVistaDialogos` → `IVistaTabla`) |
| `[SOLID-D]` | Inversión de dependencias | `SistemaAcademico` depende de `ReglaSesion` y `ConstructorSesion`; `Reporte` de `Exportador`; el menú de `AlmacenamientoEscritura`; los presentadores de las interfaces de vista, no de tkinter |
| `[U2-HERENCIA]` | Herencia | `Usuario → Docente → CoordinadorAcademico`, `Usuario → Administrador`, `Reporte → ReporteHorario / ReporteCargaDocente`, `Almacenamiento` (herencia múltiple de interfaces) |
| `[U2-POLIMORFISMO-ABSTRACTAS]` | Polimorfismo con clases abstractas | `Usuario.get_rol()`, `Reporte` (`_encabezados`, `_obtener_filas`), `CreadorUsuario.crear_usuario()`; `PresentadorReportes` trabaja con cualquier `Reporte` |
| `[U2-POLIMORFISMO-INTERFACES]` | Polimorfismo con interfaces | `Exportador`, `ReglaSesion`, `ConstructorSesion`, `Almacenamiento*`, interfaces de vista `IVista*` (clases ABC con solo métodos abstractos) |
| `[U2-INYECCIÓN-DEPENDENCIAS]` | Inyección de dependencias | `SistemaAcademico(reglas, constructor_sesion)`, `AlmacenJSON(fabrica_sistema)`, `MenuConsola(sistema, almacen)`, `Reporte(exportadores)`, `PresentadorX(vista, sistema, guardar, al_cambiar)`; `main.py` es la raíz de composición |
| `[PATRÓN: Singleton]` | Creacional | `ConfiguracionSistema` (usada por `ReglaHorarioAtencion`) |
| `[PATRÓN: Factory Method]` | Creacional | `fabrica_usuarios.py`; reemplaza el if/else de `AlmacenJSON` y crea docentes en `SistemaAcademico.registrar_docente` |
| `[PATRÓN: Builder]` | Creacional | `constructor_sesion.py`; usado en `SistemaAcademico.crear_sesion` |
| `[PATRÓN: Prototype]` | Creacional | `SesionClase.clonar()`; usado en `SistemaAcademico.duplicar_sesion` y la opción 14 del menú |
| `[PATRÓN: Strategy]` | Comportamiento | `Exportador` (formatos) y `ReglaSesion` (validaciones) |
| `[PATRÓN: Template Method]` | Comportamiento | `Reporte.generar()` define el esqueleto; las subclases rellenan los pasos; `PresentadorBase._ejecutar()` |
| `[PATRÓN: Facade]` | Estructural | `SistemaAcademico` es la puerta única que usan los presentadores |

### Patrón que se evaluó y NO se aplicó

**Abstract Factory**: el sistema no maneja *familias* de objetos relacionados con variantes
intercambiables; agregarlo sería complejidad sin un problema real que resolver.

### Cambio de comportamiento a tener en cuenta

Al crear una sesión ahora se valida el horario de atención (07:00 a 21:00) y una duración máxima
de 4 h (`ConfiguracionSistema`). Los valores se cambian con `ConfiguracionSistema().configurar(...)`
o quitando `ReglaHorarioAtencion` de la lista en `main.py`. Las sesiones ya guardadas se cargan
sin esa validación.

## Interfaz gráfica (tkinter)

`python main_gui.py` pide usuario y contraseña y abre el sistema según el rol de la cuenta.
Primer uso: **admin / admin123** (cámbiala con "Mi contraseña"). Las cuentas se guardan en
`data/cuentas.json` con la contraseña convertida a hash (PBKDF2-SHA256 con sal): nunca en texto plano.
Tras 5 intentos fallidos el botón se bloquea 20 segundos.

| Rol | Pantallas |
|---|---|
| Administrador | todas (incluye Usuarios y accesos para crear cuentas de docentes) |
| Coordinador | Inicio, Estadísticas, Horario, Sesiones (aprobar/rechazar), Reportes |
| Docente | Inicio, Estadísticas y su propio Horario |

El usuario de un docente es su correo. Un docente designado coordinador pasa a ser Coordinador sin crear otra cuenta.

Pantallas: Inicio (bienvenida con imagen e indicadores), **Estadísticas** (sesiones por estado, por día,
carga de cada docente y ocupación de aulas; filtro por período), Horario semanal, Sesiones, Docentes,
Aulas, Asignaturas, Períodos, Reportes (exporta CSV) y Usuarios. Atajos: F11 pantalla completa, Ctrl+1..9.

Adaptación a laptops de 14" a 16": la ventana mide ~90 % de la pantalla (máx. 1280x760), tiene tamaño
mínimo, fuentes e imágenes se escogen según la escala de la pantalla (100/150/200 %) y las gráficas se
redibujan al cambiar de tamaño. Las imágenes (`interfaz/recursos/`) son originales, dibujadas con código.
tkinter viene con Python (en Ubuntu: `sudo apt install python3-tk`).

| Etiqueta | Dónde |
|---|---|
| `[U2-HERENCIA]`, `[U2-POLIMORFISMO-ABSTRACTAS]` | `VistaBase` (pantallas) y `Grafico` (gráficas): clases abstractas |
| `[U2-POLIMORFISMO-INTERFACES]` | `Autenticador` (interfaz de login) |
| `[PATRÓN: Template Method]` | `VistaBase.__init__()`, `PresentadorBase._ejecutar()`, `Grafico.poner()/_redibujar()` |
| `[PATRÓN: Observer (simple)]` | `VentanaPrincipal.refrescar()` |
| `[PATRÓN: Facade]` | `EstadisticasHorario` |
| `[U2-INYECCIÓN-DEPENDENCIAS]` | `Contexto`, `VentanaPrincipal(sistema, almacen, cuenta, autenticador)`, `VentanaLogin(autenticador)`, `main_gui.py` |
| `[SOLID-S/O/D]` | cuentas, estadísticas y dibujo en clases separadas; nuevas pantallas/gráficas sin tocar las existentes |

Corrección incluida: `AlmacenJSON` ahora puede recargar sesiones cuyo aula fue desactivada después.

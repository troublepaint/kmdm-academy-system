# KMDM Academy System

Materia: Programacion Orientada a Objetos

Integrantes: 
Ronquillo Cruzatte Kerly Belén
Moreno Navarrete Marco Antonio
Chávez Merchán Mariuxi Magdalena
Muñoz Vásquez Dahiana

Gestor de horarios de clases en Python (POO), con menú de consola y guardado en JSON.

## Ejecutar (desde esta carpeta)

    python main_gui.py              # [NUEVO] interfaz gráfica con inicio de sesión (primer uso: admin / admin123)
    python main.py                  # programa con menú; guarda en data/datos.json
    python demo.py                  # demostración original, sin menú ni archivos
    python demo_solid_patrones.py   # demuestra SOLID, patrones y Unidad 2 (casos válidos e inválidos)
    python -m modelos.reportes      # prueba rápida de un módulo (sin ".py")

## Estructura

    main.py                  raíz de composición: crea y entrega ("inyecta") las dependencias
    main_gui.py              [NUEVO] raíz de composición de la interfaz gráfica
    interfaz/                [NUEVO] ventana tkinter: tema, componentes, vistas (10 pantallas), ventana, login,
                             graficos (barras/dona/progreso), imagenes y recursos/ (PNG)
    demo.py                  demostración de integración (original)
    demo_solid_patrones.py   [NUEVO] demostración de SOLID, patrones y Unidad 2
    modelos/                 clases del diagrama UML
      enums.py  usuarios.py  academico.py  infraestructura.py  horarios.py  administrador.py
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
      menu.py                [MODIFICADO] menú de consola (opciones 13 y 14 nuevas)
      autenticacion.py       [NUEVO] interfaz Autenticador + AutenticadorLocal (hash PBKDF2, roles)
      estadisticas.py        [NUEVO] cálculo de números para las gráficas
    data/datos.json          se crea al ejecutar (no se sube a Git)

## Cómo encontrar lo aplicado: leyenda de etiquetas en los comentarios

Busca el texto de la etiqueta en el código (Ctrl+Shift+F en VS Code). `[NUEVO]` marca
lo agregado en esta entrega.

| Etiqueta | Qué significa | Dónde se aplicó |
|---|---|---|
| `[SOLID-S]` | Responsabilidad única | Reglas en `servicios/reglas.py` (una comprobación cada una); exportadores solo dan formato; `MenuConsola` solo interactúa; `ConfiguracionSistema` solo guarda reglas globales |
| `[SOLID-O]` | Abierto/cerrado | Reglas nuevas, exportadores nuevos, reportes nuevos y roles nuevos se agregan SIN editar código existente (demostrado en `demo_solid_patrones.py`) |
| `[SOLID-L]` | Sustitución de Liskov | `CoordinadorAcademico` sustituye a `Docente` (`usuarios.py`, `ReporteCargaDocente`); los `Exportador` y `ReglaSesion` son intercambiables |
| `[SOLID-I]` | Segregación de interfaces | `almacenamiento.py`: `AlmacenamientoEscritura` y `AlmacenamientoLectura`; el menú solo depende de guardar |
| `[SOLID-D]` | Inversión de dependencias | `SistemaAcademico` depende de `ReglaSesion` y `ConstructorSesion`; `Reporte` de `Exportador`; el menú de `AlmacenamientoEscritura` |
| `[U2-HERENCIA]` | Herencia | `Usuario → Docente → CoordinadorAcademico`, `Usuario → Administrador`, `Reporte → ReporteHorario / ReporteCargaDocente`, `Almacenamiento` (herencia múltiple de interfaces) |
| `[U2-POLIMORFISMO-ABSTRACTAS]` | Polimorfismo con clases abstractas | `Usuario.get_rol()`, `Reporte` (`_encabezados`, `_obtener_filas`), `CreadorUsuario.crear_usuario()`; `MenuConsola._mostrar_reporte()` acepta cualquier `Reporte` |
| `[U2-POLIMORFISMO-INTERFACES]` | Polimorfismo con interfaces | `Exportador`, `ReglaSesion`, `ConstructorSesion`, `Almacenamiento*` (clases ABC con solo métodos abstractos) |
| `[U2-INYECCIÓN-DEPENDENCIAS]` | Inyección de dependencias | `SistemaAcademico(reglas, constructor_sesion)`, `AlmacenJSON(fabrica_sistema)`, `MenuConsola(sistema, almacen)`, `Reporte(exportadores)`; `main.py` es la raíz de composición |
| `[PATRÓN: Singleton]` | Creacional | `ConfiguracionSistema` (usada por `ReglaHorarioAtencion`) |
| `[PATRÓN: Factory Method]` | Creacional | `fabrica_usuarios.py`; reemplaza el if/else de `AlmacenJSON` y crea docentes en `SistemaAcademico.registrar_docente` |
| `[PATRÓN: Builder]` | Creacional | `constructor_sesion.py`; usado en `SistemaAcademico.crear_sesion` |
| `[PATRÓN: Prototype]` | Creacional | `SesionClase.clonar()`; usado en `SistemaAcademico.duplicar_sesion` y la opción 14 del menú |
| `[PATRÓN: Strategy]` | Comportamiento | `Exportador` (formatos) y `ReglaSesion` (validaciones) |
| `[PATRÓN: Template Method]` | Comportamiento | `Reporte.generar()` define el esqueleto; las subclases rellenan los pasos |
| `[PATRÓN: Facade]` | Estructural | `SistemaAcademico` es la puerta única que usa el menú |

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
| `[PATRÓN: Template Method]` | `VistaBase.__init__/ejecutar()`, `Grafico.poner()/_redibujar()` |
| `[PATRÓN: Observer (simple)]` | `VentanaPrincipal.refrescar()` |
| `[PATRÓN: Facade]` | `EstadisticasHorario` |
| `[U2-INYECCIÓN-DEPENDENCIAS]` | `Contexto`, `VentanaPrincipal(sistema, almacen, cuenta, autenticador)`, `VentanaLogin(autenticador)`, `main_gui.py` |
| `[SOLID-S/O/D]` | cuentas, estadísticas y dibujo en clases separadas; nuevas pantallas/gráficas sin tocar las existentes |

Corrección incluida: `AlmacenJSON` ahora puede recargar sesiones cuyo aula fue desactivada después.

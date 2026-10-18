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

    python main.py        # programa con menú; guarda en data/datos.json
    python demo.py        # demostración con datos fijos, sin menú ni archivos
    python -m modelos.horarios   # prueba rápida de un módulo (sin ".py")

## Estructura

    main.py              punto de entrada (carga datos y abre el menú)
    demo.py              demostración de integración
    modelos/             clases del diagrama UML
      enums.py  usuarios.py  academico.py  infraestructura.py
      horarios.py  reportes.py  administrador.py
    servicios/           lógica y entrada/salida
      sistema.py         reglas del negocio (SistemaAcademico)
      almacenamiento.py  interfaz Almacenamiento (guardar / cargar)
      almacen.py         AlmacenJSON y AlmacenMemoria (cumplen la interfaz)
      menu.py            menú de consola (MenuConsola)
    data/datos.json      se crea al ejecutar (no se sube a Git)

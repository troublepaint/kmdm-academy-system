"""PERSISTENCIA: guardar y cargar el sistema.

Contiene dos implementaciones de la interfaz Almacenamiento:
  * AlmacenJSON    -> guarda en un archivo .json (la que usa el programa).
  * AlmacenMemoria -> guarda solo en memoria (útil para pruebas).
Las dos cumplen el mismo contrato, por eso se pueden intercambiar.
[INTERFAZ + POLIMORFISMO]
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, time
from pathlib import Path
from typing import Optional

from modelos import (Administrador, Asignatura, Aula, AulaClasificacion,
                     CoordinadorAcademico, DiaSemana, Docente, EstadoSesion,
                     Periodo, SesionClase)

from .almacenamiento import Almacenamiento
from .sistema import SistemaAcademico


class ArchivoDatosError(Exception):
    """El archivo existe pero está dañado o es inconsistente."""


class AlmacenJSON(Almacenamiento):
    """Implementación de Almacenamiento que guarda en un archivo JSON.

    JSON es un formato de texto con claves y valores, fácil de leer y editar.
    Los objetos Python NO se pueden guardar tal cual: hay que convertirlos a
    diccionarios (guardar) y reconstruirlos después (cargar).
    """

    def __init__(self, ruta: Path):
        self._ruta = Path(ruta)

    @property
    def ruta(self) -> Path:
        return self._ruta

    # ------------------------------------------------------------ guardar
    def guardar(self, sistema: SistemaAcademico) -> None:
        datos = self._a_diccionario(sistema)
        self._ruta.parent.mkdir(parents=True, exist_ok=True)  # crea la carpeta data/
        # Se escribe primero en un archivo temporal y luego se reemplaza el
        # original. Si el programa se cierra a mitad de la escritura, el archivo
        # bueno no queda a medias.
        temporal = self._ruta.with_suffix(".tmp")
        temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        os.replace(temporal, self._ruta)

    @staticmethod
    def _a_diccionario(sistema: SistemaAcademico) -> dict:
        """Convierte el sistema completo en diccionarios y listas simples."""
        adm = sistema.administrador
        usuarios = []
        for u in sistema.docentes:
            fila = {"tipo": u.get_rol(), "id": u.id, "nombre": u.nombre,
                    "apellido": u.apellido, "correo": u.correo, "cedula": u.cedula,
                    "especialidad": u.especialidad,
                    "horas_max_semana": u.horas_max_semana}
            # Solo los coordinadores tienen 'carrera'; getattr devuelve None si no existe.
            carrera = getattr(u, "carrera", None)
            if carrera is not None:
                fila["carrera"] = carrera
            usuarios.append(fila)
        # Nota: NO se guardan las horas asignadas del docente. Se recalculan al
        # cargar a partir de las sesiones aprobadas, así nunca quedan inconsistentes.
        return {
            "administrador": {
                "id": adm.id, "nombre": adm.nombre, "apellido": adm.apellido,
                "correo": adm.correo, "codigo_admin": adm.codigo_admin,
                "fecha_ingreso": adm.fecha_ingreso.isoformat()},
            "clasificaciones": [
                {"id": c.id, "nombre": c.nombre, "descripcion": c.descripcion,
                 "requiere_equipamiento": c.requiere_equipamiento}
                for c in sistema.clasificaciones],
            "aulas": [
                {"codigo": a.codigo, "nombre": a.nombre, "capacidad": a.capacidad,
                 "ubicacion": a.ubicacion, "clasificacion_id": a.clasificacion.id,
                 "disponible": a.esta_disponible()} for a in sistema.aulas],
            "asignaturas": [
                {"codigo": a.codigo, "nombre": a.nombre, "nivel": a.nivel,
                 "horas_teoria": a.horas_teoria, "horas_practica": a.horas_practica}
                for a in sistema.asignaturas],
            "periodos": [
                {"id": p.id, "nombre": p.nombre,
                 "fecha_inicio": p.fecha_inicio.isoformat(),
                 "fecha_fin": p.fecha_fin.isoformat(), "activo": p.activo}
                for p in sistema.periodos],
            "usuarios": usuarios,
            # Las relaciones entre objetos se guardan como IDs (docente_id,
            # aula, periodo_id...), no como copias del objeto completo.
            "sesiones": [
                {"id": s.id, "dia": s.dia.name,
                 "hora_inicio": f"{s.hora_inicio:%H:%M}", "hora_fin": f"{s.hora_fin:%H:%M}",
                 "cupo": s.cupo, "asignatura": s.asignatura.codigo,
                 "docente_id": s.docente.id, "aula": s.aula.codigo,
                 "periodo_id": s.periodo.id, "estado": s.estado.name,
                 "motivo_rechazo": s.motivo_rechazo,
                 "coordinador_id": s.coordinador.id if s.coordinador else None}
                for s in sistema.sesiones],
        }

    # ------------------------------------------------------------- cargar
    def cargar(self) -> Optional[SistemaAcademico]:
        """Devuelve el sistema guardado, o None si todavía no hay archivo."""
        if not self._ruta.exists():
            return None
        try:
            datos = json.loads(self._ruta.read_text(encoding="utf-8"))
            return self._desde_diccionario(datos)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            # Cualquier problema al leer se convierte en un error propio y claro.
            raise ArchivoDatosError(f"{type(error).__name__}: {error}") from error

    @staticmethod
    def _desde_diccionario(d: dict) -> SistemaAcademico:
        """Reconstruye los objetos a partir de los diccionarios del JSON.

        El ORDEN importa: primero lo que no depende de nada (clasificaciones,
        aulas, asignaturas, períodos), luego los usuarios y al final las
        sesiones, que necesitan de todo lo anterior.
        """
        a = d["administrador"]
        admin = Administrador(a["id"], a["nombre"], a["apellido"], a["correo"],
                              a["codigo_admin"], date.fromisoformat(a["fecha_ingreso"]))
        sistema = SistemaAcademico(admin, con_clasificaciones_base=False)

        for c in d["clasificaciones"]:
            sistema.agregar_clasificacion(AulaClasificacion(
                c["id"], c["nombre"], c["descripcion"], c["requiere_equipamiento"]))
        for x in d["aulas"]:
            admin.registrar_aula(Aula(
                x["codigo"], x["nombre"], x["capacidad"], x["ubicacion"],
                sistema.buscar_clasificacion(x["clasificacion_id"]), x["disponible"]))
        for x in d["asignaturas"]:
            admin.registrar_asignatura(Asignatura(
                x["codigo"], x["nombre"], x["nivel"],
                x["horas_teoria"], x["horas_practica"]))
        for x in d["periodos"]:
            admin.registrar_periodo(Periodo(
                x["id"], x["nombre"], date.fromisoformat(x["fecha_inicio"]),
                date.fromisoformat(x["fecha_fin"]), x["activo"]))
        for x in d["usuarios"]:
            datos = (x["id"], x["nombre"], x["apellido"], x["correo"],
                     x["cedula"], x["especialidad"], x["horas_max_semana"])
            # Según el 'tipo' guardado, se crea la clase correcta. [POLIMORFISMO]
            if x["tipo"] == "COORDINADOR":
                admin.registrar_usuario(CoordinadorAcademico(*datos, x["carrera"]))
            else:
                admin.registrar_usuario(Docente(*datos))
        for x in d["sesiones"]:
            # Se vuelven a buscar los objetos reales a partir de los IDs guardados.
            sesion = SesionClase(
                x["id"], DiaSemana[x["dia"]], time.fromisoformat(x["hora_inicio"]),
                time.fromisoformat(x["hora_fin"]), x["cupo"],
                sistema.buscar_asignatura(x["asignatura"]),
                sistema.buscar_docente(x["docente_id"]),
                sistema.buscar_aula(x["aula"]),
                sistema.buscar_periodo(x["periodo_id"]),
                EstadoSesion[x["estado"]])
            sesion.motivo_rechazo = x["motivo_rechazo"]
            if x["coordinador_id"] is not None:
                sesion.coordinador = sistema.buscar_coordinador(x["coordinador_id"])
            sistema.restaurar_sesion(sesion)
            if sesion.estado == EstadoSesion.APROBADA:
                # Las horas del docente se recalculan, así nunca quedan inconsistentes.
                sesion.docente.asignar_horas(sesion.get_duracion_horas())
        return sistema

    def respaldar_danado(self) -> Path:
        """Aparta un archivo dañado (le cambia el nombre) para no sobrescribirlo."""
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = self._ruta.with_name(f"{self._ruta.stem}_danado_{marca}.json")
        os.replace(self._ruta, destino)
        return destino


class AlmacenMemoria(Almacenamiento):
    """Otra implementación del mismo contrato: guarda solo en memoria.
    Sirve para pruebas, porque no deja archivos en el disco."""

    def __init__(self) -> None:
        self._sistema: Optional[SistemaAcademico] = None

    def guardar(self, sistema: SistemaAcademico) -> None:
        self._sistema = sistema

    def cargar(self) -> Optional[SistemaAcademico]:
        return self._sistema

"""Escritura SEGURA de archivos JSON.  [NUEVO] [REFACTOR]

AlmacenJSON (datos.json) y AutenticadorLocal (cuentas.json) tenían escrito el mismo
procedimiento: crear la carpeta, escribir un archivo temporal y reemplazar el original.
Ahora los dos usan esta función. [SOLID-S] Solo sabe escribir archivos.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def guardar_json_seguro(ruta: Path, datos) -> None:
    """Guarda 'datos' como JSON en 'ruta' sin riesgo de dejar el archivo a medias.

    Se escribe primero en un archivo temporal y luego se reemplaza el original de una
    sola vez: si el programa se cierra a mitad de la escritura, el archivo bueno queda intacto.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)       # crea la carpeta data/ si no existe
    temporal = ruta.with_suffix(".tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporal, ruta)

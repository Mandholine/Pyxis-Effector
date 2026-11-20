# -*- coding: utf-8 -*-
"""Catalogo de nodos para la paleta del editor (el mismo manifiesto que usaba la interfaz web)."""
import json

from fastapi import APIRouter

router = APIRouter(prefix="/nodes", tags=["nodes"])
_cache = {}


def manifest() -> dict:
    if not _cache:
        import pyxis_core  # noqa: F401  (registra rutas del motor)
        import decorators
        import nodes_library  # noqa: F401  (registra los nodos de sistema)

        _cache["m"] = json.loads(decorators.get_manifest())
    return _cache["m"]


@router.get("/manifest")
def get_manifest():
    """`data_nodes`: {categoria: {nodo: [entradas]}} y `system_nodes`: {categoria: {nodo: {inputs, outputs, widgets...}}}."""
    return manifest()


@router.get("/categories")
def categories():
    m = manifest()
    out = {}
    for kind in ("data_nodes", "system_nodes"):
        for cat, nodes in m.get(kind, {}).items():
            out.setdefault(cat, []).extend(sorted(nodes))
    return {k: out[k] for k in sorted(out)}

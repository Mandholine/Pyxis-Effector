# -*- coding: utf-8 -*-
"""Cache del ultimo grafo ejecutado (uno por clave, normalmente el estilo): al volver a abrir el editor se recupera."""
import json
import os
import re
import time

from fastapi import APIRouter, HTTPException

from pyxis_core.infrastructure.engine.system.paths import get_user_data_dir

from ..schemas import CacheBody

router = APIRouter(prefix="/cache", tags=["cache"])


def _path(key: str) -> str:
    d = os.path.join(get_user_data_dir(), "cache")
    os.makedirs(d, exist_ok=True)
    slug = re.sub(r"[^\w\-]+", "_", key or "_all", flags=re.UNICODE).strip("_") or "_all"
    return os.path.join(d, "graph_%s.json" % slug[:80])


@router.get("/graph")
def get_graph(key: str = "_all"):
    p = _path(key)
    if not os.path.exists(p):
        raise HTTPException(404, "No hay un efecto en cache para esa clave")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


@router.put("/graph")
def put_graph(body: CacheBody):
    with open(_path(body.key), "w", encoding="utf-8") as fh:
        json.dump({"key": body.key, "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"), "graph": body.graph}, fh, ensure_ascii=False)
    return {"saved": body.key}


@router.delete("/graph")
def delete_graph(key: str = "_all"):
    p = _path(key)
    if os.path.exists(p):
        os.remove(p)
    return {"deleted": key}

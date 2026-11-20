# -*- coding: utf-8 -*-
"""Efectos en Python del usuario (`<workspace>/effects/*.py`): el modo «script» de Pyxis."""
import os
import re
from typing import List

from fastapi import APIRouter, HTTPException

from ..schemas import EffectBody, EffectCreateBody
from ..state import workspace_dir

router = APIRouter(prefix="/effects", tags=["effects"])
_NAME = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def _dir() -> str:
    d = os.path.join(workspace_dir(), "effects")
    os.makedirs(d, exist_ok=True)
    return d


def _path(name: str) -> str:
    if not _NAME.match(name):
        raise HTTPException(422, "Nombre invalido (letras, numeros, _ y -)")
    return os.path.join(_dir(), name + ".py")


@router.get("")
def list_effects() -> List[dict]:
    return [{"name": f[:-3], "size": os.path.getsize(os.path.join(_dir(), f))}
            for f in sorted(os.listdir(_dir())) if f.endswith(".py")]


@router.get("/{name}")
def read_effect(name: str):
    p = _path(name)
    if not os.path.exists(p):
        raise HTTPException(404, "Efecto no encontrado")
    with open(p, encoding="utf-8") as fh:
        return {"name": name, "path": p, "code": fh.read()}


@router.put("/{name}")
def write_effect(name: str, body: EffectBody):
    p = _path(name)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(body.code)
    return {"name": name, "path": p}


@router.post("", status_code=201)
def create_effect(body: EffectCreateBody):
    p = _path(body.name)
    if os.path.exists(p):
        raise HTTPException(409, "Ya existe un efecto con ese nombre")
    if body.library_name:
        from .fx import repo
        from pyxis_core.domain.services.ke_fxcodegen import fx_to_python

        fx = repo().get(body.library_name, body.library_kind)
        if fx is None:
            raise HTTPException(404, "Efecto de la libreria no encontrado")
        code = fx_to_python(fx, body.style or "Default", body.name)
    else:
        base = os.path.join(workspace_dir(), "effect_base.py")
        if not os.path.exists(base):
            raise HTTPException(500, "Falta effect_base.py en el workspace")
        with open(base, encoding="utf-8") as fh:
            code = fh.read()
        style = body.style
        rep = {"NAME": body.name, "STYLE": '"%s"' % style.replace("\\", "\\\\").replace('"', '\\"') if style else "None",
               "STYLE_TXT": style or "(todos)", "C1": '"&HFFFFFF&"', "C2": '"&HFFFFFF&"', "C3": '"&HA050FF&"'}
        code = re.sub(r"@(?P<k>[A-Z][A-Z0-9_]*)@", lambda m: rep.get(m.group("k"), m.group(0)), code)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(code)
    return {"name": body.name, "path": p}


@router.delete("/{name}")
def delete_effect(name: str):
    p = _path(name)
    if not os.path.exists(p):
        raise HTTPException(404, "Efecto no encontrado")
    os.remove(p)
    return {"deleted": name}

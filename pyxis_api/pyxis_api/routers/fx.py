# -*- coding: utf-8 -*-
"""Libreria de efectos de Kara Effector 3.6 (3.946 efectos) y su codigo Python generado."""
from typing import Optional

from fastapi import APIRouter, HTTPException

from pyxis_core.domain.services.ke_fxcodegen import fx_to_python, support_report
from pyxis_core.infrastructure.repositories import FxLibraryRepository

router = APIRouter(prefix="/fx", tags=["fx-library"])
_repo: Optional[FxLibraryRepository] = None


def repo() -> FxLibraryRepository:
    global _repo
    if _repo is None:
        _repo = FxLibraryRepository()
    return _repo


def _row(fx, with_status: bool) -> dict:
    row = {"kind": fx.kind, "kind_name": fx.kind_name, "name": fx.name, "template": fx.template}
    if with_status:
        rep = support_report(fx)
        row.update(supported=rep["supported"], missing=rep["missing"], notes=rep["notes"])
    return row


@router.get("/kinds")
def kinds():
    return [{"kind": k, "count": n} for k, n in repo().counts().items()]


@router.get("")
def list_fx(kind: Optional[str] = None, q: str = "", limit: int = 50, offset: int = 0,
            status: bool = False, only_supported: bool = False):
    """Efectos de la libreria; `status=true` anade si se ejecutan hoy y lo que les falta."""
    items = repo().search(q, kind, None)
    rows = [_row(f, status or only_supported) for f in items]
    if only_supported:
        rows = [r for r in rows if r["supported"]]
    return {"total": len(rows), "offset": offset, "items": rows[offset:offset + max(1, min(limit, 500))]}


@router.get("/{kind}/{name}/source")
def source(kind: str, name: str, style: Optional[str] = None):
    fx = repo().get(name, kind)
    if fx is None:
        raise HTTPException(404, "Efecto no encontrado")
    return {"kind": kind, "name": name, "code": fx_to_python(fx, style or "Default", name)}

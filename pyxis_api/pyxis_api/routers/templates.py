# -*- coding: utf-8 -*-
"""Biblioteca de plantillas (grafos guardados)."""
from fastapi import APIRouter, HTTPException

from pyxis_core import TemplateDTO

from ..schemas import TemplateBody
from ..state import state

router = APIRouter(prefix="/templates", tags=["templates"])


def _summary(t) -> dict:
    graph = (t.payload or {}).get("graph", t.payload or {})
    return {"id": t.id, "name": t.name, "category": t.category, "author": t.author, "comment": t.comment,
            "node_count": len(graph.get("nodes", [])) if isinstance(graph, dict) else 0}


@router.get("")
def list_templates():
    return [_summary(t) for t in state.core.templates_use_case.list_templates().templates]


@router.get("/{template_id}")
def get_template(template_id: str):
    t = state.core.templates_use_case.get_template(template_id)
    if t is None:
        raise HTTPException(404, "Plantilla no encontrada")
    return {**_summary(t), "graph": (t.payload or {}).get("graph", t.payload)}


@router.post("", status_code=201)
def save_template(body: TemplateBody):
    dto = TemplateDTO(id=body.id or "", name=body.name, comment=body.comment, author=body.author,
                      category=body.category, payload={"graph": body.graph})
    return {"id": state.core.templates_use_case.save_template(dto)}


@router.delete("/{template_id}")
def delete_template(template_id: str):
    if not state.core.templates_use_case.delete_template(template_id):
        raise HTTPException(404, "Plantilla no encontrada o no se puede eliminar")
    return {"deleted": template_id}

# -*- coding: utf-8 -*-
"""Sesion de Aegisub: el .ass activo, sus estilos y resolucion."""
import os

from fastapi import APIRouter, HTTPException

from ..schemas import ChoiceBody, SessionOpenBody
from ..state import state

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/open")
def open_session(body: SessionOpenBody):
    if not os.path.exists(body.ass_path):
        raise HTTPException(404, "No existe el archivo .ass")
    script = state.core.subtitle_repo.read_from_file(body.ass_path)
    state.session = {
        "ass_path": body.ass_path,
        "style": body.style,
        "choice": None,
        "styles": [{"name": n, "fontname": s.fontname, "fontsize": s.fontsize} for n, s in script.styles.items()],
        "lines_count": len(script.dialogues),
        "resolution": {"play_res_x": script.resolution.play_res_x, "play_res_y": script.resolution.play_res_y},
    }
    return state.session


@router.post("/choice")
def set_choice(body: ChoiceBody):
    """La app registra aqui lo elegido en su pantalla de inicio (`script` | `nodes`) y el estilo; el macro de Aegisub lo lee."""
    if body.mode not in ("script", "nodes"):
        raise HTTPException(422, "mode debe ser 'script' o 'nodes'")
    if not state.session:
        state.session = {}
    state.session["choice"] = {"mode": body.mode, "style": body.style}
    if body.style is not None:
        state.session["style"] = body.style
    return state.session["choice"]


@router.get("/choice")
def get_choice():
    return (state.session or {}).get("choice") or {"mode": None, "style": None}


@router.get("/info")
def info():
    if not state.session:
        raise HTTPException(404, "No hay sesion abierta")
    return state.session


@router.post("/shutdown")
def shutdown():
    """Apaga el daemon: primero un cierre limpio (SIGTERM) y, si una conexion abierta lo retiene, salida forzada."""
    import os as _os
    import signal
    import threading

    threading.Timer(0.2, lambda: _os.kill(_os.getpid(), signal.SIGTERM)).start()
    t = threading.Timer(2.5, lambda: _os._exit(0))
    t.daemon = True
    t.start()
    return {"status": "shutting_down"}

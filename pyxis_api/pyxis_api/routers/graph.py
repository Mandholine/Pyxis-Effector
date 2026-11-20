# -*- coding: utf-8 -*-
"""Validar y procesar grafos de nodos con pyxis-core; progreso y cancelacion por WebSocket."""
import asyncio
import os
import re
import tempfile
import threading
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from ..schemas import GraphBody, ProcessBody
from ..state import state

router = APIRouter(prefix="/graph", tags=["graph"])


def _filter_style(ass_path: str, style: str):
    """Copia temporal del .ass con solo las lineas `Dialogue:` de ese estilo. Devuelve (ruta, {n_filtrada: n_original});
    la numeracion cuenta solo lineas `Dialogue:` (es la que usa el macro de Aegisub al exportar)."""
    with open(ass_path, encoding="utf-8-sig") as fh:
        lines = fh.read().splitlines()
    out, mapping, orig, kept = [], {}, 0, 0
    for ln in lines:
        if ln.startswith("Dialogue:"):
            orig += 1
            fields = ln.split(",", 9)
            if len(fields) > 3 and fields[3].strip() == style:
                kept += 1
                mapping[kept] = orig
                out.append(ln)
        elif not ln.startswith("Comment:"):
            out.append(ln)
    fd, path = tempfile.mkstemp(suffix=".ass")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    return path, mapping


def _remap_used(text: str, mapping) -> str:
    def fix(m):
        nums = [str(mapping.get(int(n), int(n))) for n in re.findall(r"\d+", m.group(1))]
        return "#PYXIS_USED_IDX: " + ",".join(nums)
    return re.sub(r"#PYXIS_USED_IDX:\s*([\d,\s]*)", fix, text, count=1)


def _run(body: Dict[str, Any], progress=None) -> Dict[str, Any]:
    if not (body.get("ass_path") or body.get("ass_content")):
        raise HTTPException(422, "Indica ass_path o ass_content")
    ass_path, output_path, mapping, tmp_in, tmp_out = body.get("ass_path"), body.get("output_path"), None, None, None
    style = body.get("style")
    if style and ass_path:
        # solo las lineas de ese estilo; los indices usados se devuelven con la numeracion del archivo original
        ass_path, mapping = _filter_style(ass_path, style)
        tmp_in = ass_path
        if output_path:
            fd, tmp_out = tempfile.mkstemp(suffix=".ass")
            os.close(fd)
            output_path = tmp_out
    with state.lock:
        state.running = True
        try:
            res = state.core.process(
                body["graph"],
                ass_path=ass_path,
                ass_content=None if ass_path else body.get("ass_content"),
                output_path=output_path,
                default_audio_source=body.get("default_audio_source"),
                progress_callback=progress,
            )
        finally:
            state.running = False
            if tmp_in:
                try:
                    os.remove(tmp_in)
                except OSError:
                    pass
    out = res.to_dict()
    if mapping is not None:
        out["used_indices"] = [mapping.get(i, i) for i in out.get("used_indices", [])]
    if tmp_out:
        try:
            with open(tmp_out, encoding="utf-8") as fh:
                text = fh.read()
            with open(body["output_path"], "w", encoding="utf-8") as fh:
                fh.write(_remap_used(text, mapping or {}))
        finally:
            os.remove(tmp_out)
    out["output_path"] = body.get("output_path")
    if body.get("include_lines"):
        out["lines"] = res.lines
    return out


@router.post("/validate")
def validate(body: GraphBody):
    r = state.core.validate(body.graph)
    return {"valid": r.valid, "errors": r.errors, "warnings": r.warnings}


@router.post("/process")
async def process(body: ProcessBody):
    return await run_in_threadpool(_run, body.model_dump())


@router.post("/abort")
def abort():
    return {"status": "abort_requested" if state.abort() else "idle"}


@router.websocket("/ws/progress")
async def ws_progress(ws: WebSocket):
    """Flutter envia {"action":"start", "graph":..., "ass_path":...}; el daemon emite {"percent","phase"} y un evento final."""
    await ws.accept()
    loop = asyncio.get_running_loop()
    queue: "asyncio.Queue[Optional[dict]]" = asyncio.Queue()

    def on_progress(ev):
        loop.call_soon_threadsafe(queue.put_nowait, {"percent": ev.percent, "phase": ev.phase})

    try:
        while True:
            msg = await ws.receive_json()
            action = msg.get("action")
            if action == "abort":
                await ws.send_json({"status": "abort_requested" if state.abort() else "idle"})
                continue
            if action != "start":
                await ws.send_json({"error": "accion desconocida: %r" % action})
                continue
            result: Dict[str, Any] = {}

            def work():
                try:
                    result.update(_run(msg, on_progress))
                except HTTPException as e:
                    result.update({"success": False, "error": e.detail})
                except Exception as e:  # noqa: BLE001
                    result.update({"success": False, "error": str(e)})
                loop.call_soon_threadsafe(queue.put_nowait, None)

            threading.Thread(target=work, daemon=True).start()
            while True:
                item = await queue.get()
                if item is None:
                    break
                await ws.send_json(item)
            await ws.send_json({"percent": 100, "phase": "Done", **result})
    except WebSocketDisconnect:
        state.abort()

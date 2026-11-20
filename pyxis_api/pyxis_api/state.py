# -*- coding: utf-8 -*-
"""Estado compartido del daemon: fachada de pyxis-core, sesion activa y tarea de procesamiento en curso."""
from __future__ import annotations

import os
import threading
from typing import Any, Dict, Optional

import pyxis_core


def workspace_dir() -> str:
    """Carpeta de trabajo de los efectos en Python (`PYXIS_WORKSPACE`, por defecto ~/PyxisEffects)."""
    return os.environ.get("PYXIS_WORKSPACE") or os.path.join(os.path.expanduser("~"), "PyxisEffects")


class AppState:
    def __init__(self) -> None:
        self.core = pyxis_core.PyxisCore()
        self.session: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.running = False

    def abort(self) -> bool:
        if not self.running:
            return False
        self.core.process_graph_use_case.abort()
        return True


state = AppState()

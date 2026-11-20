# -*- coding: utf-8 -*-
# Libreria de efectos de Kara Effector 3.6 legacy (c) 2012-2020 Vict8r, Karalaura, NatsuoKE & Itachi Akatsuki.

"""Repositorio de la libreria de efectos: los de Kara Effector 3.6 (JSON incluido) + los del usuario (JSON)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, fields
from typing import Dict, List, Optional, Sequence

from ...domain.entities.fx_template import FX_KINDS, FxTemplate
from ...domain.repositories.i_fx_library_repository import IFxLibraryRepository
from ..engine.system import get_user_data_dir
from .lua_effector import parse_effects

BUILTIN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engine", "data", "effector36_fxlist.json")
_FIELDS = [f.name for f in fields(FxTemplate)]


def load_builtin(path: str = BUILTIN_FILE) -> List[FxTemplate]:
    """Efectos incluidos (generados desde Effector-3.6.lua con `tools/build_fxlist.py`)."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return [FxTemplate.from_sequence(row) for row in data["effects"]]


class FxLibraryRepository(IFxLibraryRepository):
    """Efectos de Kara Effector 3.6 (solo lectura) y efectos del usuario en `<datos de usuario>/fxlist.json`."""

    def __init__(self, user_file: Optional[str] = None, builtin: Optional[Sequence[FxTemplate]] = None):
        self.user_file = user_file or os.path.join(get_user_data_dir(), "fxlist.json")
        self._builtin: Optional[List[FxTemplate]] = None if builtin is None else list(builtin)
        self._index: Optional[Dict[tuple, FxTemplate]] = None

    # ---- lectura -------------------------------------------------------------------------
    def _builtin_list(self) -> List[FxTemplate]:
        if self._builtin is None:
            self._builtin = load_builtin()
        return self._builtin

    def _user(self) -> List[FxTemplate]:
        try:
            with open(self.user_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            return []
        return [FxTemplate(**{k: v for k, v in item.items() if k in _FIELDS}) for item in data]

    def all(self) -> List[FxTemplate]:
        user = self._user()
        taken = {(u.kind, u.name) for u in user}
        return [b for b in self._builtin_list() if (b.kind, b.name) not in taken] + user

    def by_kind(self, kind: str) -> List[FxTemplate]:
        return [fx for fx in self.all() if fx.kind == kind]

    def get(self, name: str, kind: Optional[str] = None) -> Optional[FxTemplate]:
        """Efecto por nombre (o nombre legible). El mismo nombre puede existir en varios tipos: indica `kind`
        (LIfx, LOfx...) para elegir; si no, se devuelve el primero (los del usuario tienen prioridad)."""
        for fx in reversed(self._user()):
            if name in (fx.name, fx.display_name) and kind in (None, fx.kind):
                return fx
        if self._index is None:
            self._index = {}
            for fx in self._builtin_list():
                for key in (fx.name, fx.display_name):
                    self._index.setdefault((key, fx.kind), fx)
                    self._index.setdefault((key, None), fx)
        return self._index.get((name, kind))

    def search(self, text: str = "", kind: Optional[str] = None, limit: Optional[int] = None) -> List[FxTemplate]:
        needle = text.strip().lower().replace(" ", "_")
        found = [fx for fx in self.all() if (kind is None or fx.kind == kind) and needle in fx.name.lower()]
        return found[:limit] if limit else found

    def counts(self) -> Dict[str, int]:
        return {kind: len(self.by_kind(kind)) for kind in FX_KINDS}

    # ---- escritura (solo efectos del usuario) ---------------------------------------------------
    def _write(self, items: List[FxTemplate]) -> None:
        os.makedirs(os.path.dirname(self.user_file) or ".", exist_ok=True)
        tmp = self.user_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump([asdict(i) for i in items], fh, ensure_ascii=False, indent=2)
        os.replace(tmp, self.user_file)

    def add(self, fx: FxTemplate) -> FxTemplate:
        if fx.kind not in FX_KINDS:
            raise ValueError("tipo desconocido %r (usa: %s)" % (fx.kind, ", ".join(FX_KINDS)))
        self._write([u for u in self._user() if (u.kind, u.name) != (fx.kind, fx.name)] + [fx])
        return fx

    def remove(self, name: str, kind: Optional[str] = None) -> bool:
        items = self._user()
        kept = [u for u in items if not (name in (u.name, u.display_name) and kind in (None, u.kind))]
        if len(kept) == len(items):
            return False
        self._write(kept)
        return True

    def import_lua(self, path: str) -> List[FxTemplate]:
        """Importa los efectos de un `Effector-3.6.lua` (o con su formato) como efectos del usuario."""
        with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            found = parse_effects(fh.read())
        for fx in found:
            self.add(fx)
        return found

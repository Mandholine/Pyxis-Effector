# -*- coding: utf-8 -*-
"""Regenera `effector36_fxlist.json` (los efectos incluidos) desde `Effector-3.6.lua`.

Uso:  python tools/build_fxlist.py /ruta/Effector-3.6.lua
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from pyxis_core.domain.entities.fx_template import FxTemplate  # noqa: E402
from pyxis_core.infrastructure.repositories.lua_effector import parse_effects  # noqa: E402
from dataclasses import fields  # noqa: E402

OUT = os.path.join(HERE, "..", "pyxis_core", "infrastructure", "engine", "data", "effector36_fxlist.json")


def main(path: str) -> int:
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        effects = parse_effects(fh.read())
    seen, unique = set(), []
    for fx in effects:
        key = (fx.kind, fx.name)          # el mismo nombre puede existir como lead-in, lead-out, etc.
        if key not in seen:
            seen.add(key)
            unique.append(fx)
    payload = {
        "source": "Effector-3.6.lua (Kara Effector 3.6 legacy, 2012-2020 Vict8r, Karalaura, NatsuoKE & Itachi Akatsuki)",
        "fields": [f.name for f in fields(FxTemplate)],
        "effects": [fx.to_sequence() for fx in unique],
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    print("%d efectos (%d repetidos exactos descartados) -> %s" % (len(unique), len(effects) - len(unique), os.path.abspath(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]) if len(sys.argv) > 1 else print(__doc__) or 1)

# -*- coding: utf-8 -*-
"""Genera `ke3_index.py`: indice (nombre -> linea) de las funciones de Effector-utils-lib-3.6.lua.

Uso:  python tools/build_utils_index.py /ruta/Effector-utils-lib-3.6.lua
"""
import os
import re
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pyxis_core", "domain", "services", "ke3_index.py")
HEADER = '''# -*- coding: utf-8 -*-
# GENERADO por tools/build_utils_index.py desde Effector-utils-lib-3.6.lua (Kara Effector 3.6 legacy,
# (c) 2012-2020 Vict8r, Karalaura, NatsuoKE & Itachi Akatsuki). No editar a mano.

"""Indice de las funciones de la libreria de utilidades de Kara Effector 3.6: nombre -> linea en el Lua original."""

UTILS_LIB_FILE = "Effector-utils-lib-3.6.lua"

UTILS_INDEX = {
'''


def main(path: str) -> int:
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        lines = fh.read().replace("\r\n", "\n").split("\n")
    found = {}
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("--"):
            continue
        m = re.match(r"function\s+([A-Za-z_]\w*(?:[.:]\w+)*)\s*\(", s) or \
            re.match(r"([A-Za-z_]\w*(?:\.\w+)+)\s*=\s*function\s*\(", s)
        if m:
            found.setdefault(m.group(1).replace(":", "."), i)
            continue
        m = re.match(r"([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*\.\w+)\s*$", s)   # alias: Rr = math.Rr
        if m:
            found.setdefault(m.group(1), i)
    body = "".join("    %r: %d,\n" % (k, v) for k, v in sorted(found.items(), key=lambda kv: kv[1]))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(HEADER + body + "}\n")
    print("%d funciones indexadas -> %s" % (len(found), os.path.abspath(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]) if len(sys.argv) > 1 else print(__doc__) or 1)

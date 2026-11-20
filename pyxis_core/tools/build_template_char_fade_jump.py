# -*- coding: utf-8 -*-
"""Genera la plantilla de nodos «Karaoke por caracter: entrada, salida y salto».

Equivale al efecto Python base del Pyxis Effect Studio para un estilo (3 capas por caracter):
  1) Entrada   - aparece antes de su silaba, escalonada por indice de silaba (retime `start2syl`).
  2) Salida    - desaparece despues de su silaba (retime `syl2end`).
  3) Mientras suena - salto, escala y rotaciones aleatorias que se relajan (retime `syl`).

Uso:  python tools/build_template_char_fade_jump.py            (escribe en engine/data/templates/)
Los nodos se instancian desde el catalogo del motor (`decorators.get_manifest()`), asi que siempre tienen las
ranuras correctas. Colores del ejemplo: relleno blanco, borde &H444447&, resalte rojo; se editan en los nodos Concatenate.
"""
import json
import os
import sys

import pyxis_core, decorators, nodes_library

MANIFEST = json.loads(decorators.get_manifest())["system_nodes"]


class G:
    def __init__(self):
        self.nodes, self.links, self.nid, self.lid = [], [], 0, 0
        self.x, self.y = 0, 0

    def node(self, ctype, name, pos, **props):
        spec = MANIFEST[ctype][name]
        self.nid += 1
        p = dict(spec["properties"]); p.update(props)
        n = {"id": self.nid, "type": "%s/%s" % (ctype, name), "pos": list(pos), "size": [230, 40 + 22 * max(len(spec["inputs"]), len(spec["outputs"]))],
             "flags": {}, "order": self.nid - 1, "mode": 0,
             "inputs": [{"name": i, "type": "loop" if "loop" in i.lower() else "data", "link": None} for i in spec["inputs"]],
             "outputs": [{"name": o, "type": "loop" if "loop" in o.lower() else "data", "links": []} for o in spec["outputs"]],
             "properties": p, "color": spec["color"]}
        self.nodes.append(n)
        return n

    def link(self, a, out_name, b, in_name):
        os_ = [o["name"] for o in a["outputs"]].index(out_name)
        is_ = [i["name"] for i in b["inputs"]].index(in_name)
        self.lid += 1
        kind = "loop" if "loop" in out_name.lower() else "data"
        self.links.append([self.lid, a["id"], os_, b["id"], is_, kind])
        a["outputs"][os_]["links"].append(self.lid)
        b["inputs"][is_]["link"] = self.lid

    def graph(self):
        return {"last_node_id": self.nid, "last_link_id": self.lid, "nodes": self.nodes, "links": self.links,
                "groups": [], "config": {}, "extra": {}, "version": 0.4}


PRIMARY, OUTLINE, SECONDARY = "&HFFFFFF&", "&H444447&", "&H0000FF&"
BASE = "\\3c%s\\1c%s\\bord2\\blur2\\shad0" % (OUTLINE, PRIMARY)


def layer(g, loop, title, queue, order, layer_no, phase, off_in, off_out, tags_parts, y):
    # queue_id vacio: el motor lo escribe en el campo Actor de las lineas y ahi no debe haber nada
    out = g.node("System", "Output", (900, y), apply_to="Style Lines", queue_id="", queue_order=str(order), origin_align=5)
    g.link(loop, "Loop", out, "Loop / Domain")
    ly = g.node("Basics", "Number", (420, y), value=str(layer_no))
    g.link(ly, "Number", out, "Layer")
    rt = g.node("Time", "Retime", (420, y + 70), phase=phase, offset_in=off_in, offset_out=off_out)
    g.link(rt, "Start Time", out, "Start Time")
    g.link(rt, "End Time", out, "End Time")
    cat = g.node("Basics", "Concatenate", (420, y + 230), separator="nil")
    cat["inputs"] = [{"name": "In%d" % i, "type": "data", "link": None} for i in range(1, len(tags_parts) + 1)]
    for i, part in enumerate(tags_parts, 1):
        cat["properties"]["In%d" % i] = part
    g.link(cat, "String", out, "Tags")
    return out


def build():
    g = G()
    loop = g.node("Loops", "Main Loop", (40, 360), iterator="char", blank_mode="no_blank")
    o1 = layer(g, loop, "Entrada", "1 Entrada", 1, 2, "start2syl", "-400 + 400 / char.syl.n * char.syl.i", "0",
               ["\\fad(500,0)" + BASE, "\\t(0,200,\\3c%s)" % PRIMARY, "\\t(200,300,\\3c%s)" % OUTLINE], 0)
    o2 = layer(g, loop, "Salida", "2 Salida", 2, 2, "syl2end", "0", "400 / char.syl.n * char.syl.i",
               ["\\fad(0,400)" + BASE, "\\t(200,300,\\3c%s)" % OUTLINE], 380)
    o3 = layer(g, loop, "Mientras suena", "3 Mientras suena", 3, 3, "syl", "0", "0",
               ["\\move(char.center,char.middle-15,char.center,char.middle)\\be1",
                "\\t(0,fx.dur/12,\\fscxR(130,160))", "\\fscyR(130,160)\\frzR(-30,30)\\fryR(-50,50)\\frxR(-20,20)\\1c%s\\3c%s" % (SECONDARY, OUTLINE),
                "\\t(0,fx.dur,\\frx0\\fry0\\frz0\\fscx100\\fscy100)"], 760)
    return g.graph()


TEMPLATE_ID = "20261120_char_fade_jump"
NAME = "Karaoke por caracter: entrada, salida y salto"
COMMENT = ("Tres capas por caracter: entrada (start2syl), salida (syl2end) y salto/rotacion aleatoria mientras suena (syl). "
           "Cambia los colores y tiempos en los nodos Retime y Concatenate.")


def template(graph=None):
    graph = graph or build()
    now = "2026-11-20T00:00:00-00:00"
    return {
        "schema_version": 1,
        "id": TEMPLATE_ID, "name": NAME, "comment": COMMENT, "author": "Pyxis", "category": "Karaoke",
        "created_at": now, "updated_at": now,
        "metadata": {"template_id": TEMPLATE_ID, "name": NAME, "comment": COMMENT, "author": "Pyxis", "created_at": now, "updated_at": now},
        "graph": graph,
    }


def main(out=None):
    # por defecto, la carpeta de datos del REPO (no la copia instalada en site-packages)
    repo_pkg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyxis_core")
    out = out or os.path.join(repo_pkg, "infrastructure", "engine", "data", "templates", "Karaoke_Char_Fade_Jump.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(template(), fh, indent=2, ensure_ascii=False)
    print("plantilla escrita:", out, "(%d nodos)" % len(build()["nodes"]))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)

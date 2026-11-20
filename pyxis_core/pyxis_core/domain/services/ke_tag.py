# -*- coding: utf-8 -*-
# Port de `ke.tag` (newkara_library.lua de Effector).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Tags ASS: listas, lectura (`array`), `default`, `inverse`, interpolacion y utilidades. Puro.

En el original estas funciones leian el estado global `ke.infofx.data` (linea/estilo actual);
aqui el estilo se pasa explicitamente (dict u objeto con color1..4, alpha1..4, spacing, outline,
shadow, scale_x, scale_y, fontsize, angle).

Pendiente: `ke.tag.dark` completo, `times` (retime de \\t), `move`, `oscill`, `set`, `glitter`
(dependen del motor de plantillas, que en Python ya cubre `string_evaluator`/`node_engine`),
y la interpolacion de tags con shapes (fase `ke.shape`).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence

from . import ke_alpha, ke_color, ke_math
from .ke_common import to_number

ANIMATED = ["\\1c", "\\2c", "\\3c", "\\4c", "\\c", "\\1a", "\\2a", "\\3a", "\\4a", "\\alpha",
            "\\fsp", "\\xbord", "\\ybord", "\\bord", "\\xshad", "\\yshad", "\\shad", "\\fscx", "\\fscy",
            "\\fs", "\\frx", "\\fry", "\\frz", "\\fr", "\\blur", "\\be", "\\fax", "\\fay", "\\clip", "\\iclip"]
UNANIMATED = ["\\n", "\\N", "\\h", "\\q", "\\a", "\\an", "\\i", "\\b", "\\u", "\\s", "\\fn", "\\fe", "\\k",
              "\\K", "\\kf", "\\ko", "\\r", "\\p", "\\pos", "\\move", "\\org", "\\fad", "\\fade", "\\t"]
FUNCTIONS = ["\\pos", "\\move", "\\org", "\\fad", "\\fade", "\\clip", "\\iclip", "\\t"]
DARK_IN = ["\\fscxy", "\\faxy", "\\frxyz", "\\frxy", "\\frxz", "\\fryz", "\\xybord", "\\xyshad", "\\bs",
           "\\13a", "\\14a", "\\34a", "\\134a", "\\13c", "\\14c", "\\34c", "\\134c"]
DARK_OUT = ["\\fscx%s\\fscy%s", "\\fax%s\\fay%s", "\\frx%s\\fry%s\\frz%s", "\\frx%s\\fry%s", "\\frx%s\\frz%s",
            "\\fry%s\\frz%s", "\\xbord%s\\ybord%s", "\\xshad%s\\yshad%s", "\\bord%s\\shad%s", "\\1a%s\\3a%s",
            "\\1a%s\\4a%s", "\\3a%s\\4a%s", "\\1a%s\\3a%s\\4a%s", "\\1c%s\\3c%s", "\\1c%s\\4c%s",
            "\\3c%s\\4c%s", "\\1c%s\\3c%s\\4c%s"]

_NAME = re.compile(r"\\(\d*[a-z]+)")
_VALUE = re.compile(r"-?[\d&]*[.\dHhA-Fa-f&]*")


def _num_str(v: Any) -> str:
    """Numero compacto para tags (5.0 -> 5, 1.2300 -> 1.23)."""
    if isinstance(v, float):
        v = round(v, 3)
        if v == int(v):
            v = int(v)
    return str(v)


def _style_get(style: Any, key: str, default: Any = 0):
    if style is None:
        return default
    return style.get(key, default) if isinstance(style, dict) else getattr(style, key, default)


def _balanced(text: str, start: int) -> int:
    """Indice del ')' que cierra el '(' en `start` (o len(text) si no cierra)."""
    depth = 0
    for i in range(start, len(text)):
        depth += (text[i] == "(") - (text[i] == ")")
        if depth == 0:
            return i
    return len(text) - 1


def tonumber(text: str, frame_dur: float, ratio: float) -> str:
    """ke.tag.tonumber: "10f" -> 10 * frame_dur ; "2r" -> 2 * ratio (numeros con sufijo f/r)."""
    return re.sub(r"(-?\d[.\d]*)([fr])", lambda m: str(float(m.group(1)) * (frame_dur if m.group(2) == "f" else ratio)), text)


def array(text: str) -> List[Dict[str, Any]]:
    """ke.tag.array: lee los tags de un bloque. Cada tag -> {"tag": "\\\\fscx", "val": "100"}.

    Un \\t -> {"tag": "\\\\t1", "val": [tags internos], "times": [t1, t2, accel], "tags": "\\\\1c&HFF&..."}.
    Los \\tag(...) guardan los parentesis en `val` ("(0,0)"), y \\tagR(...) conserva la R."""
    out: List[Dict[str, Any]] = []
    t_count = 0
    i = 0
    while i < len(text):
        m = _NAME.match(text, i) if text[i] == "\\" else None
        if not m:
            i += 1
            continue
        name, j = m.group(1), m.end()
        if j < len(text) and text[j] in "R(" and (text[j] == "(" or text[j:j + 2] == "R("):
            k = j + (1 if text[j] == "R" else 0)
            end = _balanced(text, k)
            val, i = text[j:end + 1], end + 1
        else:
            vm = _VALUE.match(text, j)
            val, i = vm.group(0), vm.end()
        if name == "t":
            t_count += 1
            inner = val[1:-1]
            cut = inner.find("\\")
            nums = [to_number(x.strip()) for x in (inner[:cut] if cut >= 0 else inner).split(",") if x.strip()]
            tags = inner[cut:] if cut >= 0 else ""
            t1, t2, acc = 0, None, 1
            if len(nums) == 1:
                acc = nums[0]
            elif len(nums) == 2:
                t1, t2 = nums
            elif len(nums) >= 3:
                t1, t2, acc = nums[:3]
            out.append({"tag": "\\t%d" % t_count, "val": array(tags), "times": [t1, t2, acc], "tags": tags})
        else:
            out.append({"tag": "\\" + name, "val": val})
    return out


def _iter_tags(items: Sequence[Dict[str, Any]]):
    for it in items:
        if it["tag"].startswith("\\t") and isinstance(it["val"], list):
            yield from _iter_tags(it["val"])
        else:
            yield it


def _dedupe_last(values: Sequence[str]) -> List[str]:
    """Quita repetidos conservando la ultima aparicion de cada tag."""
    seen, out = set(), []
    for v in reversed(values):
        key = re.match(r"\\[\d]*[a-z]+", v).group(0)
        if key not in seen:
            seen.add(key)
            out.append(v)
    return list(reversed(out))


def default(text: str, style: Any = None) -> str:
    """ke.tag.default: los valores por defecto (del estilo) de los tags animables presentes (incluso dentro de \\t)."""
    s = lambda k, d=0: _style_get(style, k, d)
    vals = {
        "\\1c": ("\\1c", s("color1", "&HFFFFFF&")), "\\2c": ("\\2c", s("color2", "&HFFFFFF&")),
        "\\3c": ("\\3c", s("color3", "&H000000&")), "\\4c": ("\\4c", s("color4", "&H000000&")),
        "\\c": ("\\1c", s("color1", "&HFFFFFF&")), "\\1a": ("\\1a", s("alpha1", "&H00&")),
        "\\2a": ("\\2a", s("alpha2", "&H00&")), "\\3a": ("\\3a", s("alpha3", "&H00&")),
        "\\4a": ("\\4a", s("alpha4", "&H00&")), "\\alpha": ("\\alpha", "&H00&"),
        "\\fsp": ("\\fsp", s("spacing")), "\\xbord": ("\\xbord", s("outline")), "\\ybord": ("\\ybord", s("outline")),
        "\\bord": ("\\bord", s("outline")), "\\xshad": ("\\xshad", s("shadow")), "\\yshad": ("\\yshad", s("shadow")),
        "\\shad": ("\\shad", s("shadow")), "\\fscx": ("\\fscx", s("scale_x", 100)), "\\fscy": ("\\fscy", s("scale_y", 100)),
        "\\fs": ("\\fs", s("fontsize")), "\\frx": ("\\frx", 0), "\\fry": ("\\fry", 0), "\\frz": ("\\frz", s("angle")),
        "\\fr": ("\\fr", s("angle")), "\\blur": ("\\blur", 0), "\\be": ("\\be", 0), "\\fax": ("\\fax", 0), "\\fay": ("\\fay", 0),
    }
    result = []
    for it in _iter_tags(array(text)):
        if it["tag"] in vals:
            tag, val = vals[it["tag"]]
            result.append("%s%s" % (tag, val))
    return "".join(_dedupe_last(result))


def inverse(text: str, style: Any = None) -> str:
    """ke.tag.inverse: el valor "opuesto" de cada tag animable (colores/alphas invertidos, numeros negados...)."""
    result = []
    for it in _iter_tags(array(text)):
        tag, val = it["tag"], it["val"]
        if tag not in ANIMATED or tag in ("\\clip", "\\iclip"):
            continue
        if isinstance(val, str) and re.fullmatch(r"&H[0-9A-Fa-f]{6}&", val):
            b, g, r = (255 - int(val[2 + k:4 + k], 16) for k in (0, 2, 4))
            inv = tag + ke_color.ass(r, g, b)
        elif isinstance(val, str) and re.fullmatch(r"&H[0-9A-Fa-f]{1,2}&", val):
            inv = tag + "&H%X&" % (255 - int(val[2:-1], 16))
        elif tag.startswith("\\b") or tag in ("\\xbord", "\\ybord"):
            inv = tag + "0"
        elif tag in ("\\fscx", "\\fscy"):
            inv = tag + str(_style_get(style, "scale_x" if tag == "\\fscx" else "scale_y", 100))
        elif tag in ("\\fs", "\\shad"):
            inv = tag + str(val)
        else:
            num = to_number(val)
            inv = tag + str(-num) if isinstance(num, (int, float)) else ""
        if inv:
            result.append(inv)
    return "".join(_dedupe_last(result))


def only(conditions, *exits):
    """ke.tag.only: devuelve la salida segun la condicion (o lista de condiciones)."""
    exits = list(exits[0]) if len(exits) == 1 and isinstance(exits[0], (list, tuple)) else list(exits)
    if isinstance(conditions, (list, tuple)):
        for i, c in enumerate(conditions):
            if c:
                return exits[i]
        if len(exits) > len(conditions):
            return exits[len(conditions)]
        return 0 if exits and isinstance(exits[-1], (int, float)) else ""
    if conditions:
        return exits[0]
    return exits[1] if len(exits) > 1 else (0 if exits and isinstance(exits[0], (int, float)) else "")


def clip(left: float, top: float, width: float, height: float, j: int = 1, loop: Sequence[int] = (1, 1),
         offset: float = 0) -> str:
    """ke.tag.clip: \\clip del rectangulo (j-esima celda de una rejilla loop[0] x loop[1]). `offset` = borde + sombra."""
    lw, lh = loop[0], (loop[1] if len(loop) > 1 else 1)
    left_x, top_y = left - offset, top - offset
    sw, sh = (width + 2 * offset) / lw, (height + 2 * offset) / lh
    cx1 = ke_math.round_(left_x + ((j - 1) % lw) * sw, 3)
    cx2 = ke_math.round_(left_x + ((j - 1) % lw + 1) * sw, 3)
    cy1 = ke_math.round_(top_y + (-(-j // lw) - 1) * sh, 3)
    cy2 = ke_math.round_(top_y + (-(-j // lw)) * sh, 3)
    return "\\clip(%s,%s,%s,%s)" % (cx1, cy1, cx2, cy2)


def expand_dark(text: str) -> str:
    """Parte pura de ke.tag.dark: expande los tags compuestos (\\fscxy150 -> \\fscx150\\fscy150, \\1c3c...)."""
    for tag, out in sorted(zip(DARK_IN, DARK_OUT), key=lambda p: -len(p[0])):
        n = out.count("%s")
        text = re.sub(re.escape(tag) + r"(\([^)]*\)|[^\\}()]*)",
                      lambda m, _o=out, _n=n: _o % ((m.group(1),) * _n), text)
    return text


def ipol(tags: Sequence[str], t: float = 0.5, accel=1) -> str:
    """ke.tag.ipol: interpola entre bloques de tags (numeros, colores y alphas; ver pendientes en el modulo)."""
    parsed = [array(expand_dark(v)) for v in tags]
    first = [it["tag"] for it in parsed[0]]
    for p in parsed[1:]:
        for it in p:
            if it["tag"] not in first:
                first.append(it["tag"])
    out = []
    for name in first:
        vals = [next((it["val"] for it in p if it["tag"] == name), None) for p in parsed]
        vals = [v for v in vals if v is not None]
        sample = vals[0]
        if isinstance(sample, str) and re.fullmatch(r"&H[0-9A-Fa-f]{6}&", sample):
            res = ke_color.ipol(vals, t, accel)
        elif isinstance(sample, str) and re.fullmatch(r"&H[0-9A-Fa-f]{2}&", sample):
            res = ke_alpha.ipol(vals, t, accel)
        else:
            nums = [to_number(v) for v in vals]
            res = ke_math.ipol(nums, t, accel) if len(nums) > 1 and all(isinstance(n, (int, float)) for n in nums) else vals[0]
        out.append("%s%s" % (name, _num_str(res)))
    return "".join(out)


def transform(t1: float, t2: float, tags: str, accel: Any = None) -> str:
    """Construye un `\\t`: transform(0, 200, "\\\\fscx120") -> "\\t(0,200,\\fscx120)" (con `accel`: "\\t(0,200,2,...)")."""
    t1, t2 = int(round(t1)), int(round(t2))
    if accel is None or accel == 1:
        return "\\t(%d,%d,%s)" % (t1, t2, tags)
    return "\\t(%d,%d,%s,%s)" % (t1, t2, _num_str(accel), tags)


def times(text: str, unit: Any, origin: float = 0) -> str:
    """ke.tag.times (retimettag): en cada `\\t(modo, t1, t2[, accel], tags)` sustituye el modo (syl, char, start2syl...)
    por los tiempos reales de `unit`, relativos a `origin` (inicio del efecto). Los `\\t` numericos no se tocan.

    Ej.: times("\\\\t(syl,0,0,\\\\fscx150)", syl, start) -> "\\\\t(0,430,\\\\fscx150)"."""
    from .ke_time import RETIME_MODES, retime

    text = wrap_bare_t(text)

    def fix(m: re.Match) -> str:
        head, tags = m.group(1), m.group(2)
        parts = [p.strip() for p in head.split(",") if p.strip()]
        if not parts or parts[0] not in RETIME_MODES:
            return m.group(0)
        mode, nums = parts[0], [to_number(p) for p in parts[1:]]
        t1 = nums[0] if len(nums) > 0 else 0
        t2 = nums[1] if len(nums) > 1 else 0
        a, b = retime(unit, mode, t1, t2, origin=origin)
        acc = nums[2] if len(nums) > 2 else None
        return transform(a, b, tags, acc)

    return re.sub(r"\\t\(\s*([^\\()]*?)\s*,?\s*(\\[^()]*(?:\([^()]*\)[^()]*)*)\)", fix, text)


def evaluate(text: str, env: Optional[Dict[str, Any]] = None) -> str:
    """Evalua las expresiones entre parentesis de los tags (`\\1c(colors[char.i])`, `\\frz(j * 15)`) con las
    variables de `env`. Los tags de funcion (\\pos, \\move, \\t, \\clip...) y los parentesis con solo numeros
    no se tocan; si una expresion falla se deja tal cual. Las listas se indexan desde 1 como en el original."""
    from .ke_lua import lua_expr

    env = dict(env or {})
    functions = {f.lstrip("\\") for f in FUNCTIONS}

    def repl(m: re.Match) -> str:
        name, expr = m.group(1), m.group(2)
        if name in functions or re.fullmatch(r"[\s\d.,\-+&H]*", expr):
            return m.group(0)
        try:
            value = eval(compile(lua_expr(expr), "<tag>", "eval"), {"__builtins__": __builtins__}, env)
        except Exception:  # noqa: BLE001 - se deja la expresion sin tocar
            return m.group(0)
        if isinstance(value, (list, tuple)):
            value = ",".join(_num_str(v) for v in value)
        return "\\%s%s" % (name, _num_str(value) if isinstance(value, (int, float)) else value)

    return re.sub(r"\\([A-Za-z0-9]+)\(([^()]*(?:\([^()]*\)[^()]*)*)\)", repl, text)


def movevc(shape: Any, posx: float, posy: float, dx: float = 0, dy: float = 0, time_i: float = 0, time_f: float = 0,
           iclip: bool = False) -> str:
    """ke4.tag.movevc: `\\clip(forma)\\movevc(x1,y1,x2,y2,t1,t2)` (tag de VSFilterMod que mueve un clip vectorial).

    La forma se lleva al origen y se centra en (posx, posy); (dx, dy) es el desplazamiento y (time_i, time_f) los
    tiempos. Con `iclip=True` devuelve `\\iclip` (ke4.tag.movevci). Sin movimiento (dx = dy = 0 y tiempos 0) devuelve
    solo el clip ya colocado, sin `\\movevc`, porque libass no lo soporta."""
    from . import ke_math
    from .ke_shape import Shape

    shp = (shape if isinstance(shape, Shape) else Shape(shape)).displace({"mode": "origin"})
    w, h = shp.width, shp.height
    r = lambda v: _num_str(ke_math.round_(v, 3))
    x1, y1 = posx - w / 2, posy - h / 2
    clip = "\\iclip" if iclip else "\\clip"
    if dx == 0 and dy == 0 and time_i == 0 and time_f == 0:
        # sin movimiento: \movevc es de VSFilterMod y libass lo ignora (el clip quedaria en la esquina 0,0);
        # se entrega la forma ya colocada en (x1, y1), que se ve igual en cualquier renderizador
        return "%s(%s)" % (clip, shp.displace({"x": x1, "y": y1}).code)
    return "%s(%s)\\movevc(%s,%s,%s,%s,%s,%s)" % (clip, shp.code, r(x1), r(y1), r(x1 + dx), r(y1 + dy), r(time_i), r(time_f))


def movevci(shape: Any, posx: float, posy: float, dx: float = 0, dy: float = 0, time_i: float = 0,
            time_f: float = 0) -> str:
    """ke4.tag.movevci: como `movevc` con \\iclip."""
    return movevc(shape, posx, posy, dx, dy, time_i, time_f, iclip=True)


def wrap_bare_t(text: str) -> str:
    """`\\t\\fr0\\fad(300,0)` -> `\\t(\\fr0)\\fad(300,0)`: un `\\t` sin parentesis no es ASS valido (el renderizador
    lo ignora y aplica el tag de golpe); aqui abarca los tags animables que le siguen, hasta el primero que no lo sea."""
    animatable = {f.lstrip("\\") for f in ANIMATED}
    out, i = [], 0
    for m in re.finditer(r"\\t(?=\\)", text):
        if m.start() < i:
            continue
        j, grabbed = m.end(), []
        while j < len(text) and text[j] == "\\":
            nm = _NAME.match(text, j)
            if not nm or nm.group(1) not in animatable:
                break
            k = nm.end()
            if k < len(text) and text[k] == "(":
                end = _balanced(text, k) + 1
            else:
                end = k + _VALUE.match(text, k).end() - k
            grabbed.append(text[j:end])
            j = end
        if grabbed:
            out.append(text[i:m.start()] + "\\t(" + "".join(grabbed) + ")")
            i = j
    out.append(text[i:])
    return "".join(out)


def _balanced_paren(text: str, start: int) -> int:
    """Indice del `)` que cierra el `(` en `start` (respeta cadenas); -1 si no cierra."""
    depth, quote, i = 0, None, start
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def clip_moves(text: str, env: Optional[Dict[str, Any]] = None) -> str:
    """Clips animados de Kara Effector: `\\clip(x1,y1,x2,y2)( {t1, t2, dx, dy[, accel]}, ... )` ->
    `\\clip(x1,y1,x2,y2)\\t(t1,t2,\\clip(x1+dx,y1+dy,x2+dx,y2+dy))...` (tambien `\\iclip`). La tabla se evalua con las
    variables de `env` (p. ej. `jump`, `fx.dur`). Si no se puede evaluar, el texto queda igual."""
    from .ke3 import LuaTable
    from .ke_lua import lua_expr

    out, i = [], 0
    for m in re.finditer(r"\\(i?clip)(?=\()", text):
        if m.start() < i:
            continue
        a = m.end()                                         # `(` del rectangulo
        b = _balanced_paren(text, a)
        if b < 0:
            continue
        j = b + 1
        while j < len(text) and text[j] == " ":
            j += 1
        if j >= len(text) or text[j] != "(":
            continue
        e = _balanced_paren(text, j)
        if e < 0:
            continue
        coor, moves = text[a + 1:b], text[j + 1:e]
        nums = re.findall(r"-?\d+[.\d]*", coor)
        if len(nums) < 4 or "m" in coor:
            continue
        try:
            table = eval(compile(lua_expr("{ %s }" % moves, shift_indices=False), "<clip>", "eval"),
                         {"__builtins__": __builtins__}, {**(env or {}), "lt": LuaTable})
            rows = [list(r.values()) if isinstance(r, dict) else list(r) for _, r in sorted(table.items())]
            x1, y1, x2, y2 = (float(n) for n in nums[:4])
            tag, built = m.group(1), []
            for r in rows:
                accel = r[4] if len(r) > 4 else 1
                built.append("\\t(%s,%s,%s%s(%s,%s,%s,%s))" % (
                    _num_str(r[0]), _num_str(r[1]), "" if accel == 1 else _num_str(accel) + ",", "\\" + tag,
                    _num_str(x1 + r[2]), _num_str(y1 + r[3]), _num_str(x2 + r[2]), _num_str(y2 + r[3])))
        except Exception:  # noqa: BLE001 - no se pudo evaluar: se deja el texto original
            continue
        out.append(text[i:j].rstrip(" ") + "".join(built))
        i = e + 1
    out.append(text[i:])
    return "".join(out)


def split_tags(text: str) -> List[str]:
    """Parte un bloque de tags en tags sueltos (cada `\\` en el nivel superior empieza uno; los parentesis, llaves y
    cadenas no se parten). Lo que sigue a un tag sin barra (p. ej. el `( 0, 100 )` tras un `\\t(...)`) queda en el."""
    out: List[str] = []
    cur: List[str] = []
    depth, quote, i = 0, None, 0
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch in "({":
            depth += 1
        elif ch in ")}":
            depth -= 1
        elif ch == "\\" and depth == 0 and cur:
            out.append("".join(cur))
            cur = []
        cur.append(ch)
        i += 1
    if cur:
        out.append("".join(cur))
    return out

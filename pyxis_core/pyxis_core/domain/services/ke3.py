# -*- coding: utf-8 -*-
# Port de la libreria de utilidades de Kara Effector 3.6 legacy (Effector-utils-lib-3.6.lua)
# (c) 2012-2020 Vict8r, Karalaura, NatsuoKE & Itachi Akatsuki.

"""`ke3`: las utilidades de Kara Effector 3.6 que ya estan en Python, con los nombres y firmas del original.

Cada funcion portada se comporta como la del Lua. Las que todavia no estan portadas NO existen "a medias": al usarlas
lanzan `NotImplementedError` indicando su linea en `Effector-utils-lib-3.6.lua`, y `coverage()` dice cuales faltan.

Estado de ejecucion: el original lee globales (`ratio`, `frame_dur`...). Aqui viven en `ENV`, que fija el motor
(p. ej. `pyxis_fx` al leer el script).
"""

from __future__ import annotations

import math as _pymath
from types import SimpleNamespace
from typing import Any, Callable, Dict, Iterable, List, Optional

from . import ke_math, ke_tag, ke_time
from .ke3_index import UTILS_INDEX

# Datos del script en ejecucion: ratio = xres / 1280, frame_dur en ms por frame (valores por defecto de Effector).
ENV = SimpleNamespace(xres=1280, yres=720, ratio=1.0, frame_dur=41.708)

# Contexto de la iteracion actual (lo que en Effector son globales: `fx`, `l`/`line`, la unidad y `j`). El codigo
# generado lo actualiza en cada vuelta con `bind(...)`; las utilidades que lo necesitan (tag.clip...) lo leen de aqui.
CTX = SimpleNamespace(fx=None, line=None, unit=None, j=1, tags_style="")


def bind(fx: Any, line: Any, unit: Any, j: int = 1) -> None:
    """Fija el contexto de la iteracion actual."""
    CTX.fx, CTX.line, CTX.unit, CTX.j = fx, line, unit, j


class _Namespace(object):
    """`math`, `tag`, `shape`...: las funciones portadas son atributos; el resto avisa donde esta el original."""

    def __init__(self, name: str, impls: Dict[str, Callable], consts: Optional[Dict[str, Any]] = None):
        self.__dict__["_name"] = name
        self.__dict__["_impls"] = dict(impls)
        self.__dict__.update(impls)
        self.__dict__.update(consts or {})      # valores (no funciones), p. ej. shape.circle

    def __getattr__(self, attr: str):
        key = "%s.%s" % (self.__dict__["_name"], attr)
        line = UTILS_INDEX.get(key)
        if line:
            raise NotImplementedError(
                "%s no esta portado todavia (Effector-utils-lib-3.6.lua, linea %d)" % (key, line))
        raise AttributeError("%s no existe en la libreria de Kara Effector 3.6" % key)

    def ported(self) -> List[str]:
        return sorted(self.__dict__["_impls"])


# ------------------------------------------------------------------------------------------ math ---


def _num(v: Any) -> Any:
    """Argumento que puede ser una funcion (el original admite `function() ... end`)."""
    return v() if callable(v) else v


def _scaled(v: Any, k: float) -> Any:
    v = _num(v)
    return None if v is None else v * k


def R(a: Any = None, b: Any = None, step: Any = None):
    """R(i, f, paso): entero al azar entre i y f (R(n) = 1..n; sin argumentos, decimal en [0, 1))."""
    a, b, step = _num(a), _num(b), _num(step)
    return ke_math.rand(a, b, 1 if step is None else step)


def _signed(v):
    return v * (-1) ** ke_math.rand(2)


def Rs(a=None, b=None, step=None):
    """Como R con signo al azar."""
    return _signed(R(a, b, step))


def Rr(a=None, b=None, step=None):
    """R escalado por `ratio` (resolucion del video / 1280); con un solo argumento, R(n * ratio)."""
    a, b = _num(a), _num(b)
    if a is None:
        return R()
    if b is None:
        return R(a * ENV.ratio)
    return R(a * ENV.ratio, b * ENV.ratio, step)


def Rsr(a=None, b=None, step=None):
    """R con `ratio` y signo al azar. (alias: Rrs)"""
    return _signed(R(a, b, step)) * ENV.ratio


def _decimal(k: int, ratio: bool, signed: bool) -> Callable:
    """Rd/Rc/Rm (1 decimal, 2, 3) con sus variantes: r = por ratio, s = con signo."""
    def fn(a=None, b=None, step=None):
        v = R(_scaled(a, k), _scaled(b, k), _scaled(step, k))
        if signed:
            return v * (1.0 / k) * (ENV.ratio if ratio else 1) * (-1) ** ke_math.rand(2)
        return v * (ENV.ratio if ratio else 1) / k
    return fn


def Re(table: Any = None):
    """Valor de un elemento al azar de la tabla (lista o diccionario)."""
    table = _num(table)
    values = list(table.values()) if isinstance(table, dict) else list(table if table is not None else [1])
    return values[R(len(values)) - 1]


_R_FAMILY: Dict[str, Callable] = {"R": R, "Rs": Rs, "Rr": Rr, "Rsr": Rsr, "Rrs": Rsr, "Re": Re}
for _suffix, _k in (("d", 10), ("c", 100), ("m", 1000)):
    _R_FAMILY["R" + _suffix] = _decimal(_k, False, False)
    _R_FAMILY["R" + _suffix + "r"] = _decimal(_k, True, False)
    _R_FAMILY["R" + _suffix + "s"] = _decimal(_k, False, True)
    _R_FAMILY["R" + _suffix + "rs"] = _decimal(_k, True, True)

math = _Namespace("math", {
    **{k: v for k, v in _R_FAMILY.items()},
    "round": ke_math.round_, "polar": ke_math.polar, "distance": ke_math.distance, "angle": ke_math.angle,
    "clamp": ke_math.clamp, "intersect": ke_math.intersect, "factk": ke_math.factorial,
})

# ------------------------------------------------------------------------------------------- tag ---


def _n(v: Any) -> str:
    """Numero como lo imprime `%s` en Lua: 5.0 -> 5, 2.5 -> 2.5."""
    return ke_tag._num_str(ke_math.round_(v, 2))


def _seq(t: Any) -> list:
    """Tabla de Lua (dict con indices desde 1, lista...) -> lista de Python."""
    if isinstance(t, dict):
        return [t[k] for k in sorted((k for k in t if isinstance(k, int)))]
    return list(t)


def only(conditions: Any, *exits: Any):
    """tag.only: devuelve la salida segun la condicion (acepta tablas de Lua)."""
    exits = list(_seq(exits[0])) if len(exits) == 1 and isinstance(exits[0], (dict, list, tuple)) else list(exits)
    if isinstance(conditions, (dict, list, tuple)):
        conditions = _seq(conditions)
    return ke_tag.only(conditions, *exits)


def clip(left_cx: Any = None, top_cy: Any = None, width_clip: Any = None, height_clip: Any = None,
         mode: Any = None, clip_move: Any = None) -> str:
    """tag.clip: `\\clip(x1,y1,x2,y2)` de la celda `j` de una rejilla `loop_h x loop_v` sobre el rectangulo dado
    (por defecto, el de la unidad actual). `mode` (13, 17, 31, 39, 71, 79, 93, 97) elige el orden de recorrido; el
    movimiento `clip_move` puede ser una tabla `{dx, dy, [dx2, dy2, ...], [{t1, t2}]}` (clips animados con \\t).

    Usa el contexto (`bind`): fx.loop_h/loop_v, fx.move_l1/t1, fx.dur, la unidad (ancho/alto), la linea (borde y
    sombra) y `j`. El movimiento dado como TEXTO con funciones de `shape` (`"shape.rmove(...)"`) no esta portado."""
    c = CTX
    if c.fx is None:
        raise RuntimeError("tag.clip necesita el contexto del efecto (ke3.bind)")
    fx, line, unit, j = c.fx, c.line, c.unit, c.j
    left_cx, top_cy, width_clip, height_clip, mode, clip_move = (_num(v) for v in (
        left_cx, top_cy, width_clip, height_clip, mode, clip_move))
    loop_w, loop_h = fx.loop_h, fx.loop_v
    offset = getattr(line, "outline", 0) + getattr(line, "shadow", 0)
    if isinstance(left_cx, str):                       # tag.clip("movimiento"): rectangulo de la unidad + movimiento
        clip_move, mode = left_cx, 79
        left_x, top_y = fx.move_l1 - offset, fx.move_t1 - offset
        clip_w, clip_h = unit.width + 2 * offset, unit.height + 2 * offset
    else:
        left_x = (fx.move_l1 if left_cx is None else left_cx) - offset
        top_y = (fx.move_t1 if top_cy is None else top_cy) - offset
        clip_w = (unit.width if not width_clip else width_clip) + 2 * offset
        clip_h = (unit.height if not height_clip else height_clip) + 2 * offset
        mode = mode or 79
    size_w, size_h = clip_w / loop_w, clip_h / loop_h
    if mode not in (13, 17, 31, 39, 71, 79, 93, 97):
        mode = 79
    ceil = _pymath.ceil
    cx1 = cx2 = cy1 = cy2 = 0.0
    if mode in (17, 71):
        cx1, cx2 = left_x + (ceil(j / loop_h) - 1) * size_w, left_x + ceil(j / loop_h) * size_w
    elif mode in (13, 79):
        cx1, cx2 = left_x + ((j - 1) % loop_w) * size_w, left_x + ((j - 1) % loop_w + 1) * size_w
    elif mode in (39, 93):
        cx1, cx2 = left_x + clip_w - ceil(j / loop_h) * size_w, left_x + clip_w - (ceil(j / loop_h) - 1) * size_w
    elif mode in (31, 97):
        cx1, cx2 = left_x + clip_w - ((j - 1) % loop_w + 1) * size_w, left_x + clip_w - ((j - 1) % loop_w) * size_w
    if mode in (79, 97):
        cy1, cy2 = top_y + (ceil(j / loop_w) - 1) * size_h, top_y + ceil(j / loop_w) * size_h
    elif mode in (71, 93):
        cy1, cy2 = top_y + ((j - 1) % loop_h) * size_h, top_y + ((j - 1) % loop_h + 1) * size_h
    elif mode in (13, 31):
        cy1, cy2 = top_y + clip_h - ceil(j / loop_w) * size_h, top_y + clip_h - (ceil(j / loop_w) - 1) * size_h
    elif mode in (17, 39):
        cy1, cy2 = top_y + clip_h - ((j - 1) % loop_h + 1) * size_h, top_y + clip_h - ((j - 1) % loop_h) * size_h
    if clip_move is None:
        return "\\clip(%s,%s,%s,%s)" % (_n(cx1), _n(cy1), _n(cx2), _n(cy2))
    if isinstance(clip_move, str):
        raise NotImplementedError(
            "tag.clip con movimiento dado como texto (funciones de shape como shape.rmove) no esta portado todavia "
            "(Effector-utils-lib-3.6.lua, linea 8470): %r" % clip_move)
    moves = _seq(clip_move)
    if len(moves) % 2 == 1:                            # el ultimo elemento es {tiempo_inicial, tiempo_final}
        last = _seq(moves.pop())
        time_i, time_f = last[0], last[1]
    else:
        time_i, time_f = 0, fx.dur
    time_dur = time_f - time_i
    out = "\\clip(%s,%s,%s,%s)" % (_n(cx1 + moves[0]), _n(cy1 + moves[1]), _n(cx2 + moves[0]), _n(cy2 + moves[1]))
    pairs = len(moves) // 2
    for i in range(2, pairs + 1):
        div = only(pairs == 1, 1, pairs - 1)
        out += "\\t(%s,%s,\\clip(%s,%s,%s,%s))" % (
            _n(time_i + (i - 2) * time_dur / div), _n(time_i + (i - 1) * time_dur / div),
            _n(cx1 + moves[2 * i - 2]), _n(cy1 + moves[2 * i - 1]),
            _n(cx2 + moves[2 * i - 2]), _n(cy2 + moves[2 * i - 1]))
    return out


tag = _Namespace("tag", {"only": only, "clip": clip})


def new_pos(posx: Any = None, posy: Any = None) -> str:
    """effector.new_pos: `\\pos(x,y)` (o `\\move` si el efecto tiene varias posiciones) relativo al punto base."""
    fx = CTX.fx
    posx = fx.pos_x if posx is None else posx
    posy = fx.pos_y if posy is None else posy
    x1 = ke_math.round_(posx + fx.move_x1 - fx.pos_x, 3)
    y1 = ke_math.round_(posy + fx.move_y1 - fx.pos_y, 3)
    if getattr(fx, "nmove", 1) >= 2:
        x2 = ke_math.round_(posx + fx.move_x2 - fx.pos_x, 3)
        y2 = ke_math.round_(posy + fx.move_y2 - fx.pos_y, 3)
        return "\\move(%s,%s,%s,%s%s)" % (_n3(x1), _n3(y1), _n3(x2), _n3(y2), getattr(fx, "tags_times", ""))
    return "\\pos(%s,%s)" % (_n3(x1), _n3(y1))


def _n3(v: Any) -> str:
    return ke_tag._num_str(ke_math.round_(v, 3))


def lmove(coor: Any, times: Any = None, times2: Any = None, accel: Any = 1) -> str:
    """shape.lmove: movimiento por tramos rectos entre las coordenadas dadas `{x1, y1, x2, y2, ...}`.

    `times` = `{t1, t2, t3, t4, ...}` (ms desde el inicio del efecto; un valor negativo cuenta desde el final y un 0
    tras la primera posicion vale fx.dur). Sin `times`, el tiempo se reparte segun la longitud de cada tramo (`times2`:
    duracion, o `{inicio, fin}`). Es el truco de Effector: el texto se mueve escalando un dibujo (`\\fscx\\fscy`), asi que
    devuelve `\\an7\\q2\\pos...\\fscx..\\fscy..\\t(...)\\p1}m 0 0 m 100 100 {\\p0\\r` (cierra y reabre el bloque de tags).
    Sin cambios de color en el texto, `tags_style` es vacio, como en Effector."""
    c = CTX
    if c.fx is None:
        raise RuntimeError("shape.lmove necesita el contexto del efecto (ke3.bind)")
    fx, line, unit = c.fx, c.line, c.unit
    coor, times, times2, accel = _num(coor), _num(times), _num(times2), _num(accel)
    accel = 1 if accel is None else accel
    coor = _seq(coor)
    off_x = off_y = 0
    if coor and isinstance(coor[0], (dict, list, tuple)):      # coordenadas relativas al punto de movimiento
        coor = _seq(coor[0])
        off_x, off_y = fx.move_x1, fx.move_y1
    if times is None:
        time_ini, time_dur = 0, fx.dur
        if times2 is not None:
            if isinstance(times2, (int, float)):
                time_dur = times2
            else:
                t2 = _seq(times2)
                time_ini = t2[0] if t2 else 0
                time_dur = (t2[1] if len(t2) > 1 else fx.dur) - time_ini
        n = len(coor) // 2
        segments = [ke_math.distance((coor[2 * i - 2], coor[2 * i - 1]), (coor[2 * i], coor[2 * i + 1])) for i in range(1, n)]
        total = sum(segments)
        partial = [0.0]
        for sg in segments:
            partial.append(partial[-1] + sg)
        tms = {0: time_ini}
        for i in range(1, len(coor) - 1):
            tms[i] = tms[i - 1] if i % 2 == 1 else ke_math.round_(time_ini + time_dur * partial[i // 2] / total, 2)
        tlist = [tms[i] for i in range(1, len(coor) - 1)]
    else:
        tlist = list(_seq(times))
    for i in range(len(tlist)):                                # 0 (tras la 1a posicion) = fx.dur; negativos desde el final
        if i > 0 and tlist[i] == 0:
            tlist[i] = fx.dur
        elif tlist[i] < 0:
            tlist[i] = fx.dur + tlist[i]
    w, h = unit.width, unit.height
    descent = getattr(line, "descent", 0)
    coorx = [ke_math.round_(coor[2 * i] - w / 2 + off_x, 2) for i in range(len(coor) // 2)]
    coory = [ke_math.round_(coor[2 * i + 1] + h / 2 - descent + off_y, 2) for i in range(len(coor) // 2)]
    tags1 = "\\fscx%s\\fscy%s" % (_n(coorx[0]), _n(coory[0]))
    for i in range(2, len(coorx) + 1):
        tags1 += "\\t(%s,%s,%s,\\fscx%s\\fscy%s)" % (_n(tlist[2 * (i - 1) - 2]), _n(tlist[2 * (i - 1) - 1]),
                                                       _n(accel), _n(coorx[i - 1]), _n(coory[i - 1]))
    tags2 = tags1 + "\\p1}m 0 0 m 100 100 {\\p0\\r" + getattr(c, "tags_style", "")
    import re as _re
    fsc = [float(m) for m in _re.findall(r"fscx?y?(-?\d+[.\d]*)", tags2)]
    sizex, sizey = fsc[0::2], fsc[1::2]
    min_x, min_y = min(sizex), min(sizey)
    if min_x >= 0:
        min_x = 0
    if 0 < min_y <= h:
        min_y = -min_y
    elif min_y >= 0:
        min_y = 0
    shifted = _re.sub(r"\\fscx(-?\d+[.\d]*)\\fscy(-?\d+[.\d]*)",
                      lambda m: "\\fscx%s\\fscy%s" % (_n(float(m.group(1)) - min_x), _n(float(m.group(2)) - min_y)), tags2)
    return "\\an7\\q2" + new_pos(min_x, min_y) + shifted




# ------------------------------------------------------------------------------------------ time ---
time = _Namespace("time", {
    "li": ke_time.time_li, "lo": ke_time.time_lo, "mid1": ke_time.time_mid1, "mid2": ke_time.time_mid2,
    "retime": ke_time.retime,
})

# Namespaces del original sin ninguna funcion portada todavia (cada una avisa su linea al usarla).
from . import ke_shape as _ke_shape  # noqa: E402
from .ke_shape_library import PREDEFINED as _SHAPES  # noqa: E402

# formas predefinidas (shape.circle, shape.rectangle, shape.cristal17...): la libreria nueva manda si coincide
from .ke3_shape import FUNCTIONS as _SHAPE_FUNCS  # noqa: E402

shape = _Namespace("shape", {"lmove": lmove, **_SHAPE_FUNCS}, {**_SHAPES, **{n.lower(): getattr(_ke_shape, n) for n in (
    "CIRCLE", "TRIANGLE", "RECTANGLE", "PIXEL", "HEART", "SHINE1T", "SHINE2T", "STAR", "SAKURA")}})
text = _Namespace("text", {})
color = _Namespace("color", {})
alpha = _Namespace("alpha", {})
string = _Namespace("string", {})
table = _Namespace("table", {})

NAMESPACES = {"math": math, "tag": tag, "time": time, "shape": shape, "text": text, "color": color,
              "alpha": alpha, "string": string, "table": table}

# Funciones globales del original (R, Rs, retime, time_li...) que el codigo generado puede usar directamente.
# (`retime(...)` en un campo tiene efectos laterales sobre la linea de efecto; el generador lo trata aparte.)
GLOBALS: Dict[str, Callable] = dict(_R_FAMILY)
globals().update(_R_FAMILY)      # ke3.R, ke3.Rs, ke3.Rrs...


def ported() -> List[str]:
    """Nombres portados (con su espacio): ["math.R", "tag.only", ...] + globales."""
    names = ["%s.%s" % (ns, fn) for ns, obj in NAMESPACES.items() for fn in obj.ported()]
    return sorted(names + sorted(GLOBALS))


def coverage(used: Iterable[str]) -> Dict[str, List[str]]:
    """Clasifica nombres usados por los efectos en portados / no portados / desconocidos."""
    have = set(ported())
    out: Dict[str, List[str]] = {"ported": [], "missing": [], "unknown": []}
    for name in sorted(set(used)):
        (out["ported"] if name in have else out["missing"] if name in UTILS_INDEX else out["unknown"]).append(name)
    return out


# Abreviaturas de funciones de math que usa el lenguaje de plantillas (sin, cos, ceil, pi...).
PI, LN = _pymath.pi, _pymath.log
sin, cos, tan, asin, acos, atan, atan2 = (_pymath.sin, _pymath.cos, _pymath.tan, _pymath.asin, _pymath.acos,
                                          _pymath.atan, _pymath.atan2)
ceil, floor, pi, sqrt = _pymath.ceil, _pymath.floor, _pymath.pi, _pymath.sqrt


# ----------------------------------------------------------------------- apoyo del codigo generado ---


class LuaTable(dict):
    """Tabla de Lua: acceso por punto a las claves de texto (`t.times`) y `None` (nil) si la clave no existe."""

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return self.get(name)

    def __setattr__(self, name: str, value: Any):
        self[name] = value

    def __missing__(self, key: Any):
        return None


def compose(align: Any, pos_x: Any, pos_y: Any, tags: str, extra: str = "") -> str:
    """Bloque de tags de la linea de efecto: `\\an` y `\\pos` por defecto, SALVO que `tags` traiga los suyos (en ASS solo
    cuenta el primero, y utilidades como shape.lmove ponen `\\an7\\pos(0,0)`). `extra` va al final (p. ej. `\\p1`)."""
    import re as _re
    head = ""
    if not _re.search(r"\\an\d", tags):
        head += "\\an%s" % align
    if not _re.search(r"\\(?:pos|move)\(", tags):
        head += "\\pos(%s,%s)" % (_n3(pos_x), _n3(pos_y))
    return "{%s%s%s}" % (head, tags, extra)


def cat(*parts: Any) -> str:
    """Une los valores de una lista de retornos (`a, b, c` de un campo) en un solo texto; None cuenta como vacio."""
    out = []
    for p in parts:
        if p is None:
            continue
        out.append(("%g" % p) if isinstance(p, float) else str(p))
    return "".join(out)


def tag_post(tags: str, unit: Any, start: float, env: Optional[Dict[str, Any]] = None) -> str:
    """Pasa los tags de un campo a ASS valido: clips animados `\\clip(...)( {...} )`, tags compuestos (\\fscxy, \\bs...) y
    modos de `\\t(syl, ...)`. `env` son las variables del efecto para evaluar las tablas de movimiento."""
    return ke_tag.times(ke_tag.expand_dark(ke_tag.clip_moves(tags, env)), unit, start)


def untranslated(field: str, text: str):
    """Campo del efecto que el generador no pudo traducir a Python: falla al usarse, con el texto original."""
    raise NotImplementedError("campo %s sin traducir a Python; texto original de Kara Effector: %s" % (field, text))

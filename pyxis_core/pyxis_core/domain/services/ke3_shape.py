# -*- coding: utf-8 -*-
# Port de las funciones `shape.*` de Effector-utils-lib-3.6.lua (Kara Effector 3.6 legacy,
# (c) 2012-2020 Vict8r, Karalaura, NatsuoKE & Itachi Akatsuki), sobre la clase `Shape`.

"""`ke3.shape`: size, displace, rotate, ratio, reflect, width, height, reverse, divide (y atajos de displace).

Reciben una shape (texto ASS o `Shape`) o una tabla de shapes (se aplican a cada una) y devuelven codigo ASS.
"""

from __future__ import annotations

import math
import re
from typing import Any, Callable, Dict, List, Optional

from . import ke_math
from .ke_point import Point
from .ke_shape import Shape


def _call(v: Any) -> Any:
    return v() if callable(v) else v


def _is_table(v: Any) -> bool:
    return isinstance(v, (dict, list, tuple))


def _items(t: Any) -> List:
    return [t[k] for k in sorted(k for k in t if isinstance(k, int))] if isinstance(t, dict) else list(t)


def _map(shape: Any, fn: Callable[[Any], Any]):
    """Aplica `fn` a cada shape de una tabla (conserva las claves) o a una sola."""
    if isinstance(shape, dict):
        from .ke3 import LuaTable
        return LuaTable({k: fn(v) for k, v in shape.items()})
    if isinstance(shape, (list, tuple)):
        return [fn(v) for v in shape]
    return fn(shape)


def _axis_expr(text: str, w: float, h: float) -> float:
    """Expresion de un eje como "2x + 5": `x` = ancho de la shape, `y` = alto (se evalua solo con aritmetica)."""
    s = re.sub(r"(\d)x", r"\1 * x", text)
    s = re.sub(r"(\d)y", r"\1 * y", s)
    s = re.sub(r"x", str(w), s)
    s = re.sub(r"y", str(h), s)
    if not re.fullmatch(r"[\d\s.+\-*/()eE]*", s):
        raise ValueError("expresion no valida: %r" % text)
    return eval(s, {"__builtins__": {}}, {})


def width(shape: Any, height: Any = None) -> float:
    return _map(shape, lambda s: Shape(s).width)


def height(shape: Any) -> float:
    return _map(shape, lambda s: Shape(s).height)


def reverse(shape: Any) -> str:
    """shape.reverse: invierte el sentido del trazado sin cambiar la forma."""
    return _map(shape, lambda s: Shape(s).inverse().code)


def ratio(shape: Any, rx: Any = None, ry: Any = None, mode: Any = None) -> str:
    """shape.ratio: escala por una proporcion (`rx`, `ry`: numero, `{tamano}` o `{puntos..., tamano}`)."""
    def one(s):
        r = lambda v: _items(v) if _is_table(v) else v
        return Shape(s).ratio(r(_call(rx)), r(_call(ry)), _call(mode) or None).code
    return _map(shape, one)


def size(shape: Any, size_x: Any = None, size_y: Any = None, mode: Any = None) -> str:
    """shape.size: cambia el tamano. `size_x`/`size_y`: pixeles, `{n}` (se suma al ancho/alto actual) o una expresion
    en texto con `x`/`y` ("2x"). Un 0 en un eje = proporcional al otro. `mode`: punto fijo al escalar (como en ratio)."""
    def one(s):
        shp = Shape(s)
        w, h = shp.width, shp.height
        sx, sy, md = _call(size_x), _call(size_y), _call(mode)
        szx = w if sx is None else sx
        szy = szx if sy is None else sy
        if _is_table(szx):
            szx = w + _items(szx)[0]
        if _is_table(szy):
            szy = h + _items(szy)[0]
        if isinstance(szx, str):
            szx = _axis_expr(szx, w, h)
        if isinstance(szy, str):
            szy = _axis_expr(szy, w, h)
        md = md or None
        if szx == 0:
            return shp.ratio(None, [szy], md).code
        if szy == 0:
            return shp.ratio([szx], None, md).code
        return shp.ratio(szx / w if w > 0 else 1, szy / h if h > 0 else 1, md).code
    return _map(shape, one)


def displace(shape: Any, dx: Any = 0, dy: Any = 0, mode: Any = None) -> str:
    """shape.displace: desplaza la shape. Atajos: `displace(s, "origin")` y `displace(s, "incenter")`.
    `mode`: "origin" (esquina en dx,dy), "center" (centro en dx,dy), "first" / "last" (primer/ultimo punto en dx,dy).
    `dx` puede ser un texto "m 20 20", una tabla `{angulo, radio}` (polar) o una expresion con x/y."""
    def one(s):
        shp = Shape(s)
        x, y, md = _call(dx), _call(dy), _call(mode)
        x = 0 if x is None else x
        y = 0 if y is None else y
        if isinstance(x, str) and re.search(r"-?\d+[.\d]* -?\d+[.\d]*", x):
            nums = re.findall(r"-?\d+[.\d]*", x)
            x, y = float(nums[0]), float(nums[1])
        if _is_table(x):
            a = _items(x)
            x, y = ke_math.polar(a[0], a[1])
        if isinstance(x, str) and x == "origin":
            x, y, md = 0, 0, "origin"
        elif isinstance(x, str) and x == "incenter":
            x, y, md = 0, 0, "center"
        w, h = shp.width, shp.height
        if isinstance(x, str):
            x = _axis_expr(x, w, h)
        if isinstance(y, str):
            y = _axis_expr(y, w, h)
        if md == "origin":
            x, y = x - shp.minx, y - shp.miny
        elif md == "center":
            x, y = x - shp.minx - 0.5 * w, y - shp.miny - 0.5 * h
        elif md == "first":
            p = shp.points()[0]
            x, y = x - p.x, y - p.y
        elif md == "last":
            p = shp.inverse().points()[0]
            x, y = x - p.x, y - p.y
        return (shp + (x, y)).code
    return _map(shape, one)


def origin(shape: Any) -> str:
    return displace(shape, 0, 0, "origin")


def incenter(shape: Any) -> str:
    return displace(shape, 0, 0, "center")


def centerpos(shape: Any, dx: Any = 0, dy: Any = 0) -> str:
    return displace(shape, dx, dy, "center")


def firstpos(shape: Any, dx: Any = 0, dy: Any = 0) -> str:
    return displace(shape, dx, dy, "first")


def rotate(shape: Any, angle: Any = 0, org_x: Any = None, org_y: Any = None) -> str:
    """shape.rotate: rota sobre el eje z respecto a (org_x, org_y) (por defecto el origen), "center" o "x y"."""
    def one(s):
        shp = Shape(s)
        ang = _call(angle)
        ang = _items(ang) if _is_table(ang) else (0 if ang is None else ang)
        cx = _call(org_x)
        if cx == "center":
            org: Any = "center"
        elif isinstance(cx, str) and re.search(r"-?\d+[.\d]* -?\d+[.\d]*", cx):
            nums = re.findall(r"-?\d+[.\d]*", cx)
            org = Point(float(nums[0]), float(nums[1]))
        else:
            org = Point(cx or 0, _call(org_y) or 0)
        return shp.rotate(ang, org).code
    return _map(shape, one)


def reflect(shape: Any, axis: Any = None, relative: Any = None) -> str:
    """shape.reflect: eje "y" (por defecto: x = rel - x), "x" (y = rel - y) u otro (diagonal). `relative` = 0 si no se da."""
    def one(s):
        shp = Shape(s)
        rel = _call(relative)
        if isinstance(rel, str):
            rel = _axis_expr(rel, shp.width, shp.height)
        rel = 0 if rel is None else rel
        ax = _call(axis)

        def filt(x, y):
            if ax == "x":
                return x, rel - y
            if ax == "y" or ax is None:
                return rel - x, y
            return -rel - x, -rel - y
        return shp.gsub(filt).code
    return _map(shape, one)


def divide(shape: Any, mark: Any = None):
    """shape.divide: tabla con las subformas; `mark` ("default", numero o `{x1, y1, x2, y2}`) antepone a cada una el
    marco que fija la caja."""
    from .ke3 import LuaTable

    def one(s):
        shp = Shape(s)
        m = ""
        mk = _call(mark)
        if mk == "default" or isinstance(mk, (int, float)) and not isinstance(mk, bool):
            m = "m %s %s m %s %s " % (_f(shp.maxx), _f(shp.maxy), _f(shp.minx), _f(shp.miny))
        elif _is_table(mk):
            a = _items(mk)
            m = "m %s %s m %s %s " % (_f(a[2]), _f(a[3]), _f(a[0]), _f(a[1]))
        return LuaTable({i: m + part.strip() + " " for i, part in enumerate(re.findall(r"m[^m]*", shp.code), 1)})
    if _is_table(shape):
        return LuaTable({i: one(s) for i, s in enumerate(_items(shape), 1)})
    return one(shape)


def _f(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else str(round(v, 3))


FUNCTIONS: Dict[str, Callable] = {
    "size": size, "displace": displace, "rotate": rotate, "ratio": ratio, "reflect": reflect, "width": width,
    "height": height, "reverse": reverse, "divide": divide, "origin": origin, "incenter": incenter,
    "centerpos": centerpos, "firstpos": firstpos,
}

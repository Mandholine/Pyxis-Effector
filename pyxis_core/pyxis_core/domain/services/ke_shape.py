# -*- coding: utf-8 -*-
# Port de `ke.shape` (newkara_library.lua de Effector).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Formas vectoriales ASS (dibujos \\p): analisis, transformaciones y deformaciones. Puro.

`Shape` guarda el codigo ASS canonico (cada comando repetido por segmento: "m 0 0 l 0 100 l 100 100 ...").
Las operaciones devuelven formas nuevas (no mutan). Las operaciones booleanas (union, diferencia...) viven en
`infrastructure/engine/geometry` porque dependen de pyclipper.

Los filtros de `gsub` reciben `(x, y, ctx)`; `ctx` expone las variables del original:
Cx, Cy (centro), Do/Dc (distancia al origen/centro), Ao/Ac (angulo al origen/centro), Pn (total de puntos),
Pk (indice del punto), Mx/My (posicion relativa 0..1 en la caja) y Mp (posicion relativa entre puntos).
"""

from __future__ import annotations

import inspect
import math
import random as _random
import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from . import ke_math
from .ke_common import EPSILON, ROUND_NUM, get_numbers
from .ke_point import Point, group as point_group, to_convex, to_shape as points_to_shape
from .ke_segment import Segment
from .ke_shape_ops import ShapeOps

# Formas predisenadas (ke.shape.circle, ...)
CIRCLE = "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 "
TRIANGLE = "m 50 0 l 0 86 l 100 86 l 50 0 "
RECTANGLE = "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0 "
PIXEL = "m 0 0 l 0 1 1 1 1 0 "
HEART = "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 106 b 75 71 100 68 100 40 b 100 16 68 0 50 25 "
SHINE1T = "m 0 0 l 47 50 l 0 100 l 50 53 l 100 100 l 53 50 l 100 0 l 50 47 m 42 50 b 42 61 58 61 58 50 b 58 39 42 39 42 50 "
SHINE2T = "m 0 0 l 45 50 l 0 100 l 50 55 l 100 100 l 55 50 l 100 0 l 50 45 m 40 50 b 40 64 60 64 60 50 b 60 36 40 36 40 50 "
TREBOL = ("m 1 99 l 4 106 b 21 99 44 83 53 56 b 51 73 40 88 56 98 b 72 106 80 90 77 82 b 85 86 100 82 100 69 "
          "b 100 58 87 52 64 54 b 52 55 51 50 68 48 b 85 46 94 40 95 29 b 96 18 80 10 70 19 b 70 0 40 0 40 21 "
          "b 40 33 47 37 50 43 b 54 50 52 54 47 47 b 39 38 31 26 19 27 b 0 29 0 49 13 53 b 0 58 3 80 19 79 "
          "b 39 78 40 62 51 55 b 42 79 23 92 1 99 ")
FEATHER = ("m 0 0 b 0 20 10 28 27 34 b 10 33 47 49 54 55 b 62 62 72 77 78 75 l 80 78 l 90 79 b 94 86 96 94 97 100 "
           "l 100 100 b 99 93 96 84 93 78 b 100 56 88 41 73 30 l 73 39 l 69 28 b 62 24 55 23 49 19 l 48 24 l 45 19 "
           "b 31 10 13 12 0 0 m 91 74 l 88 75 b 79 49 57 40 46 35 b 22 25 8 15 2 5 b 11 17 22 23 48 34 b 64 41 82 51 91 74 ")
BUBBLE = ("m 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 m 50 1 b 79 1 "
          "99 21 99 50 b 99 76 80 93 68 96 b 62 98 66 94 50 94 b 34 94 38 98 32 96 b 20 93 1 78 1 50 b 1 22 22 1 50 1 "
          "m 88 22 b 79 11 75 14 85 24 b 92 38 94 33 88 22 m 12 15 b 12 19 18 19 18 15 b 18 11 12 11 12 15 "
          "m 14 16 l 15 30 l 16 16 l 30 15 l 16 14 l 15 0 l 14 14 l 0 15 m 50 94 b 63 94 61 100 52 100 b 42 100 38 94 50 94 ")
STAR = "m 38 36 l 0 36 l 31 59 l 20 95 l 50 72 l 81 94 l 69 59 l 100 36 l 62 36 l 50 0 l 38 36 "
SAKURA = "m 50 40 l 35 0 b 10 10 0 32 0 61 b 0 88 15 117 50 130 b 85 117 100 88 100 61 b 100 32 90 10 65 0 l 50 40 "
TEST = "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0 m 20 20 l 80 20 l 80 80 l 20 80 l 20 20 m 40 40 l 40 60 l 60 60 l 60 40 l 40 40 "

_PAIR = re.compile(r"(-?\d[.\d]*)\s+(-?\d[.\d]*)")
_NUM = re.compile(r"-?\d[.\d]*")


def _fmt(v: float) -> str:
    v = round(float(v), ROUND_NUM)
    return str(int(v)) if v == int(v) else str(v)


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def assdraw(code: Any) -> str:
    """Normaliza codigo ASS (o un clip rectangular "x1,y1,x2,y2") al formato canonico de ASSDraw3."""
    if isinstance(code, Shape):
        return code.code
    code = str(code)
    rect = re.search(r"(-?\d[. \d]*),\s*(-?\d[. \d]*),\s*(-?\d[. \d]*),\s*(-?\d[. \d]*)", code)
    if rect:
        x1, y1, x2, y2 = (g.strip() for g in rect.groups())
        return "m %s %s l %s %s l %s %s l %s %s " % (x1, y1, x1, y2, x2, y2, x2, y1)
    m = re.search(r"m\s+-?\d[.\-\d blm]*", code)
    code = m.group(0) if m else code
    out: List[str] = []
    for letter, nums in re.findall(r"([mbl])\s+((?:-?\d[.\d]*\s*)+)", code):
        values = [float(n) for n in _NUM.findall(nums)]
        size = 6 if letter == "b" else 2
        for i in range(0, len(values) - size + 1, size):
            out.append("%s %s " % (letter, " ".join(_fmt(v) for v in values[i:i + size])))
    return "".join(out)


def tocode(points: Sequence[Point]) -> str:
    """Codigo ASS desde puntos (cada Point con su `t`)."""
    pts = list(points)
    code = "%s %s %s " % (pts[0].t or "m", _fmt(pts[0].x), _fmt(pts[0].y))
    for i in range(1, len(pts)):
        letter = "" if pts[i].t == pts[i - 1].t else (pts[i].t or "l")
        code += "%s %s %s " % (letter, _fmt(pts[i].x), _fmt(pts[i].y))
    return re.sub(r"\s+", " ", code)


class _Ctx:
    """Variables disponibles para los filtros de `Shape.gsub`."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


class Shape(ShapeOps):
    """ke.shape (objeto)."""

    def __init__(self, code: Any = ""):
        if isinstance(code, Shape):
            code = code.code
        elif isinstance(code, (list, tuple)) and code:
            first = code[0]
            if isinstance(first, Segment):
                code = _segments_code(code)
            elif isinstance(first, Point):
                code = tocode(code)
            elif isinstance(first, str):
                code = "".join(code)
        elif isinstance(code, (list, tuple)):
            code = ""
        self.code: str = assdraw(re.sub(r"c\s?", "", code))

    @classmethod
    def new(cls, code: Any) -> "Shape":
        return cls(code)

    def copy(self) -> "Shape":
        return Shape(self.code)

    def __repr__(self):
        return self.code

    __str__ = __repr__

    def __eq__(self, other):
        return isinstance(other, Shape) and self.code == other.code

    def __hash__(self):
        return hash(self.code)

    # ---- informacion -----------------------------------------------------------
    def _coords(self) -> List[Tuple[float, float]]:
        return [(float(x), float(y)) for x, y in _PAIR.findall(self.code)]

    @property
    def n(self) -> int:
        return len(self._coords())

    def _extent(self, idx: int, fn) -> float:
        c = self._coords()
        return fn(p[idx] for p in c) if c else 0

    @property
    def minx(self): return self._extent(0, min)

    @property
    def maxx(self): return self._extent(0, max)

    @property
    def miny(self): return self._extent(1, min)

    @property
    def maxy(self): return self._extent(1, max)

    @property
    def width(self): return self.maxx - self.minx

    @property
    def height(self): return self.maxy - self.miny

    @property
    def center(self): return self.minx + self.width / 2

    @property
    def middle(self): return self.miny + self.height / 2

    @property
    def radius(self): return ke_math.distance(self.width, self.height) / 2

    @property
    def centroid(self) -> Point: return Point(self.center, self.middle)

    @property
    def pnt(self) -> List[Point]: return self.points()

    @property
    def seg(self) -> List[Segment]: return self.segments()

    @property
    def len(self) -> float: return self.length()

    @property
    def isclosed(self) -> bool: return self.is_closed()

    def bounding(self) -> Tuple[float, float, float, float]:
        return self.minx, self.miny, self.maxx, self.maxy

    def box(self) -> Tuple[Point, Point, Point, Point]:
        """Puntos de la caja: izq-sup, izq-inf, der-inf, der-sup."""
        x0, y0, x1, y1 = self.bounding()
        return Point(x0, y0), Point(x0, y1), Point(x1, y1), Point(x1, y0)

    # ---- descomposicion ---------------------------------------------------------
    def points(self) -> List[Point]:
        out: List[Point] = []
        for t, nums in re.findall(r"([mbl])(\s+-?\d[. \-\d]*)", self.code):
            out += [Point(x, y, t) for x, y in _PAIR.findall(nums)]
        return out

    def parts(self) -> List[str]:
        """Cada subforma ("m ..." hasta el siguiente "m")."""
        return re.findall(r"m[^m]*", self.code)

    def subshapes(self) -> List["Shape"]:
        return [Shape(p) for p in self.parts()]

    def tract(self) -> List[str]:
        """Codigo de cada segmento (lineas/curvas con su punto de partida)."""
        tracts: List[str] = []
        for seg in re.findall(r"[mlb][^mlb]*", self.code):
            if tracts and "m" not in seg:
                prev = re.findall(r"-?\d[.\d]*\s+-?\d[.\d]*", tracts[-1])[-1]
                seg = prev + " " + seg
            tracts.append(seg)
        return tracts

    def segments(self) -> List[Segment]:
        out: List[Segment] = []
        for tr in self.tract():
            nums = get_numbers(tr)
            out.append(Segment(nums))
        return out

    def length(self) -> float:
        return ke_math.round_(sum(s.length() for s in self.segments()), ROUND_NUM)

    def get_points_coors(self) -> Dict[str, List[float]]:
        return point_group(self.points(), "coors")

    # ---- estado cerrado / orientacion ---------------------------------------------
    def is_closed(self) -> bool:
        for sub in self.subshapes():
            pts = sub.points()
            if pts and pts[0] != pts[-1]:
                return False
        return True

    def closed(self) -> "Shape":
        """Cierra cada subforma agregando su primer punto si hace falta."""
        out = ""
        for sub in self.subshapes():
            first = re.search(r"m (-?\d[.\d]* -?\d[.\d]* )", sub.code)
            last = re.search(r"(-?\d[.\d]* -?\d[.\d]* )$", sub.code)
            add = first.group(1) if first and (not last or first.group(1) != last.group(1)) else ""
            out += sub.code + (("l " + add) if add else "")
        return Shape(out)

    def unclosed(self) -> "Shape":
        out = ""
        for sub in self.subshapes():
            first = re.search(r"m (-?\d[.\d]* -?\d[.\d]* )", sub.code)
            last = re.search(r"(-?\d[.\d]* -?\d[.\d]* )$", sub.code)
            code = sub.code
            if first and last and first.group(1) == last.group(1):
                code = re.sub(r"-?\d[.\d]* -?\d[.\d]* $", "", code)
                code = re.sub(r"[lm] $", "", code)
            out += code
        return Shape(out)

    def area(self) -> float:
        """Area con signo (negativa = antihoraria en coordenadas ASS)."""
        total = 0.0
        for sub in self.subshapes():
            pnt = sub.points()
            n = len(pnt)
            s1 = sum(pnt[i].x * pnt[(i + 1) % n].y for i in range(n))
            s2 = sum(pnt[i].y * pnt[(i + 1) % n].x for i in range(n))
            total += (s1 - s2) / 2
        return ke_math.round_(total, ROUND_NUM)

    def is_clockwise(self) -> bool:
        return self.area() > 0

    def inverse(self) -> "Shape":
        """Invierte el recorrido de cada subforma (y su orden) sin cambiar su aspecto."""
        out = []
        for sub in self.subshapes():
            segs = sub.segments()
            if len(segs) < 2:
                out.append(sub.code)
                continue
            start = segs[-1].pts[-1]
            pts = [Point(start.x, start.y, "m")]
            for sg in reversed(segs[1:]):
                pts += [Point(p.x, p.y, sg.t) for p in list(reversed(sg.pts))[1:]]
            out.append(tocode(pts))
        return Shape("".join(reversed(out)))

    def clockwise(self) -> "Shape":
        return self.inverse() if self.area() <= 0 else self.copy()

    def unclockwise(self) -> "Shape":
        return self.inverse() if self.area() > 0 else self.copy()

    # ---- aritmetica y composicion -----------------------------------------------------
    def concat(self, other: Any) -> "Shape":
        return Shape(self.code + (other.code if isinstance(other, Shape) else str(other)))

    def __add__(self, xy: Any):
        if isinstance(xy, Shape):
            return self.concat(xy)
        dx, dy = (xy[0], xy[1] if len(xy) > 1 else 0) if isinstance(xy, (list, tuple)) else (xy or 0, 0)
        return self.gsub(lambda x, y: (x + dx, y + dy))

    def __sub__(self, xy: Any):
        dx, dy = ke_math.get_pair(xy, 0, 0)
        return self.gsub(lambda x, y: (x - dx, y - dy))

    def __mul__(self, xy: Any):
        rx, ry = ke_math.get_pair(xy, 1)
        return self.gsub(lambda x, y: (x * rx, y * ry))

    def __truediv__(self, xy: Any):
        rx, ry = ke_math.get_pair(xy, 1)
        return self.gsub(lambda x, y: (x / rx, y / ry))

    def repeat(self, n: int = 1) -> "Shape":
        return Shape(self.code * max(1, math.ceil(abs(n))))

    def delete_points(self, delete: Any = 0, initial: bool = False) -> "Shape":
        """Quita el punto (o el rango [a, b]) indicado; los indices negativos cuentan desde el final (1-based)."""
        pts = self.points()
        d1 = delete[0] if isinstance(delete, (list, tuple)) else delete
        d2 = delete[1] if isinstance(delete, (list, tuple)) and len(delete) > 1 else d1
        d1 = len(pts) + d1 + 1 if d1 < 0 else d1
        d2 = len(pts) + d2 + 1 if d2 < 0 else d2
        keep = [p for i, p in enumerate(pts, 1) if not d1 <= i <= d2]
        if initial and keep:
            keep[0].t = "m"
        return Shape(keep)

    # ---- transformacion de puntos ---------------------------------------------------------
    def gsub(self, filt: Callable) -> "Shape":
        """Aplica `filt(x, y[, ctx]) -> (x, y)` a cada punto del codigo."""
        try:
            wants_ctx = len(inspect.signature(filt).parameters) >= 3
        except (TypeError, ValueError):
            wants_ctx = False
        total = self.n
        cx, cy, minx, miny = self.center, self.middle, self.minx, self.miny
        width, height = self.width, self.height
        counter = {"k": 0}

        def repl(m: re.Match) -> str:
            counter["k"] += 1
            k = counter["k"]
            x, y = float(m.group(1)), float(m.group(2))
            ctx = _Ctx(Cx=cx, Cy=cy, Do=ke_math.distance(x, y), Dc=ke_math.distance((cx, cy), (x, y)),
                       Ao=ke_math.angle((0, 0), (x, y)), Ac=ke_math.angle((cx, cy), (x, y)), Pn=total, Pk=k,
                       Mx=_safe_div(y - miny, height), My=_safe_div(x - minx, width),
                       Mp=_safe_div(k - 1, total - 1), shape=self)
            nx, ny = filt(x, y, ctx) if wants_ctx else filt(x, y)
            return "%s %s" % (_fmt(nx), _fmt(ny))

        new = Shape.__new__(Shape)
        new.code = _PAIR.sub(repl, self.code)
        return new

    def round(self, n: int = 0) -> "Shape":
        new = Shape.__new__(Shape)
        new.code = _NUM.sub(lambda m: str(ke_math.round_(float(m.group(0)), n)), self.code)
        return new

    def redraw(self, tract: float = 2, section: str = "all") -> "Shape":
        """Divide los segmentos en tramos rectos de longitud `tract` (section: "all" | "line" | "bezier")."""
        t = "l" if section == "line" else ("b" if section == "bezier" else section)
        segs = self.segments()
        new = [(s.split(tract) if (t == "all" or s.t == t) else s) for s in segs]
        return Shape(_segments_code(new))

    def displace(self, move: Any = None) -> "Shape":
        """Desplaza la forma. move = numero | {x, y, mode: origin|center|polar|first|last|point, point}."""
        if isinstance(move, (int, float)):
            move = {"x": move}
        move = move or {"x": 0, "y": 0}
        dx, dy = move.get("x", 0) or 0, move.get("y", 0) or 0
        disp: Any = (dx, dy)
        mode = move.get("mode")
        if mode:
            pnt, n = self.points(), self.n
            idx = (move.get("point") or 1) - 1
            table = {
                "origin": (dx - self.minx, dy - self.miny),
                "center": (dx - self.minx - 0.5 * self.width, dy - self.miny - 0.5 * self.height),
                "polar": ke_math.polar(dx, dy),
                "first": (dx - pnt[0].x, dy - pnt[0].y),
                "last": (dx - pnt[-1].x, dy - pnt[-1].y),
                "point": (dx - pnt[idx].x, dy - pnt[idx].y),
            }
            disp = table.get(mode, disp)
        return self + disp

    def ratio(self, xratio: Any = None, yratio: Any = None, mode: Any = None) -> "Shape":
        """Escala la forma. xratio/yratio: numero, [tamano] o ([punto_a, punto_b], tamano). mode: posicion fija
        (1-9 o "first"/"last") hacia la que se mantiene la forma al escalar."""
        x0, y0, x1, y1 = self.bounding()
        wx, hy = self.width, self.height
        pnt, n = self.points(), self.n
        rx = xratio if isinstance(xratio, (int, float)) else (1 if xratio is None else None)
        if isinstance(xratio, (list, tuple)):
            rx = _safe_div((xratio[0] if xratio and xratio[0] is not None else wx), wx) or 1
            if len(xratio) == 2:
                ref = xratio[0] if xratio[0] is not None else [pnt[0], pnt[-1]]
                d = ke_math.distance(ref)
                rx = xratio[1] / d if d else _safe_div(xratio[1], wx)
        ry = yratio if isinstance(yratio, (int, float)) else rx
        if isinstance(yratio, (list, tuple)):
            ry = _safe_div(yratio[0], hy) or 1
            rx = ry if xratio is None else rx
        disp = (0, 0)
        if mode is not None:
            xpos = {1: x0 * (1 - rx), 2: self.center * (1 - rx), 3: x1 * (1 - rx),
                    "first": pnt[0].x * (1 - rx), "last": pnt[-1].x * (1 - rx)}
            ypos = {1: y1 * (1 - ry), 2: self.middle * (1 - ry), 3: y0 * (1 - ry),
                    "first": pnt[0].y * (1 - rx), "last": pnt[-1].y * (1 - rx)}
            if isinstance(mode, str):
                disp = (xpos[mode], ypos[mode])
            else:
                disp = (xpos[(mode - 1) % 3 + 1], ypos[math.ceil(mode / 3)])
        return self.gsub(lambda x, y: (x * rx, y * ry)) + disp

    def size(self, xsize: Any = None, ysize: Any = None, mode: Any = None) -> "Shape":
        """Cambia el tamano: numeros absolutos, o [delta] para anadir al ancho/alto actual; 0 = proporcional."""
        xsize = self.width if xsize is None else xsize
        ysize = xsize if ysize is None else ysize
        xrat = self.width + xsize[0] if isinstance(xsize, (list, tuple)) else xsize
        yrat = self.height + ysize[0] if isinstance(ysize, (list, tuple)) else ysize
        xr: Any = [xrat] if yrat == 0 else ((xrat / self.width if self.width > 0 else 1) if xrat != 0 else None)
        yr: Any = [yrat] if xrat == 0 else ((yrat / self.height if self.height > 0 else 1) if yrat != 0 else None)
        return self.ratio(xr, yr, mode)

    def rotate(self, angle: Any = 0, org: Any = None) -> "Shape":
        """Rota respecto a `org` (Point | (x, y) | "center" | indice de punto 1-based)."""
        pnt = self.points()
        if org == "center":
            org = Point(self.center, self.middle)
        elif isinstance(org, int) and not isinstance(org, bool):
            org = pnt[math.ceil(org) - 1] if 0 < org <= len(pnt) else Point(0, 0)
        org = Point(org) if org is not None else Point(0, 0)
        cx, cy = org.x, org.y
        ang = angle
        if isinstance(angle, (list, tuple)):
            ref = angle[0] if angle[0] is not None else [pnt[0], pnt[-1]]
            ang = (angle[1] if len(angle) > 1 else 0) - ke_math.angle(ref)

        def filt(x, y):
            a = ke_math.angle((cx, cy), (x, y))
            r = ke_math.distance((cx, cy), (x, y))
            delta = ang(x, y) if callable(ang) else ang
            return cx + ke_math.polar(a + delta, r, "x"), cy + ke_math.polar(a + delta, r, "y")

        return self.gsub(filt)

    def reflect(self, axis: Optional[str] = None, relative: Optional[float] = None) -> "Shape":
        """Reflexion respecto al eje "x", "y" (por defecto), o la diagonal (otro valor)."""
        relative = self.maxx if axis is None and relative is None else (relative or 0)
        axis = axis or "y"

        def filt(x, y):
            nx = x if axis == "x" else (relative - x if axis == "y" else -relative - x)
            ny = relative - y if axis == "x" else (y if axis == "y" else -relative - y)
            return nx, ny

        return self.gsub(filt)

    def oblique(self, pixels: Any = None, t: float = 1) -> "Shape":
        """Deforma la caja de la forma: pixels = numero | {x:[..4], y:[..4]} | "random"."""
        cx, cy = 0.4 * self.width, 0.4 * self.height
        pxs = cx if pixels is None else pixels
        fxbox = [(0, 0)] * 4
        if isinstance(pxs, (int, float)):
            fxbox = [(pxs, 0), (0, 0), (0, 0), (pxs, 0)]
        elif isinstance(pxs, dict):
            xs, ys = list(pxs.get("x", [0] * 4)) + [0] * 4, list(pxs.get("y", [0] * 4)) + [0] * 4
            fxbox = [(xs[i] or 0, ys[i] or 0) for i in range(4)]
        elif pxs == "random":
            fxbox = [(ke_math.rand(-cx, cx), ke_math.rand(-cy, cy)) for _ in range(4)]
        P0, P1, P2, P3 = (p + fxbox[i] for i, p in enumerate(self.box()))

        def filt(x, y, ctx):
            top, bottom = P0.ipol(ctx.My, P3), P1.ipol(ctx.My, P2)
            newp = top.ipol(ctx.Mx, bottom)
            return x + (newp.x - x) * t, y + (newp.y - y) * t

        return self.gsub(filt)

    def roundout(self, radius: Optional[float] = None, mode: str = "round") -> "Shape":
        """Redondea (mode="round") o achaflana (mode="bevel") las esquinas; radio negativo = hacia dentro."""
        negative = radius is not None and radius < 0
        radius = abs(12 if radius is None else radius)

        def get_t(p0, p1, p2, rad):
            d1, d2 = p0.distance(p1), p1.distance(p2)
            dmin = max(d1, d2) if min(d1, d2) == 0 else min(d1, d2)
            rad = 0.4 * dmin if rad > 0.4 * dmin else rad
            return _safe_div(rad, d1), _safe_div(rad, d2)

        result: List[Point] = []
        for sub in self.subshapes():
            pnt, n = sub.points(), sub.n
            closed = sub.is_closed()
            if closed and n > 2:
                _, t1 = get_t(pnt[n - 2], pnt[0], pnt[1], radius)
                result.append(pnt[0].ipol(t1, pnt[1]))
            else:
                result.append(pnt[0])
            for i, p in enumerate(pnt, 1):
                if p.t == "l":
                    if 1 < i <= n - (0 if closed else 1):
                        pnext = pnt[1] if i == n else pnt[i]
                        t0, t1 = get_t(pnt[i - 2], p, pnext, radius)
                        if mode == "bevel":
                            result += [Point(p.ipol(t0, pnt[i - 2]), t="l"), Point(p.ipol(t1, pnext), t="l")]
                        else:
                            p1, p2 = p.ipol(t0, pnt[i - 2]), p.ipol(0.42 * t0, pnt[i - 2])
                            p3, p4 = p.ipol(0.42 * t1, pnext), p.ipol(t1, pnext)
                            if negative:
                                p2, p3 = p2.reflect(p1, p4), p3.reflect(p1, p4)
                            p1.t = "l"
                            p2.t = p3.t = p4.t = "b"
                            result += [p1, p2, p3, p4]
                elif p.t != "m":
                    result.append(p)
            if not closed:
                result.append(pnt[-1])
        return Shape(result)

    def reduce(self) -> "Shape":
        """Quita los puntos colineales de las lineas rectas."""
        P = self.points()
        if len(P) < 3:
            return self.copy()
        keep = [P[0]]
        for i in range(1, len(P) - 1):
            collinear = (P[i].t == "l" and P[i + 1].t == "l"
                         and ke_math.equality(P[i - 1].angle(P[i]), P[i - 1].angle(P[i + 1]), 2))
            if not collinear:
                keep.append(P[i])
        keep.append(P[-1])
        return Shape(keep)

    def rand(self, rx: Any = 24, ry: Any = 24, step: float = 1, split: Any = None, section: str = "all",
             rng=_random, filt: Optional[Callable] = None) -> "Shape":
        """Mueve cada punto al azar (rx, ry: maximo o [min, max])."""
        shp = self.redraw(split, section) if split else self

        def default(x, y):
            prx = ke_math.rand(rx[0], rx[1], step, rng=rng) if isinstance(rx, (list, tuple)) else ke_math.rand(0, rx, step, rng=rng)
            pry = ke_math.rand(ry[0], ry[1], step, rng=rng) if isinstance(ry, (list, tuple)) else ke_math.rand(0, ry, step, rng=rng)
            return x + prx, y + pry

        return shp.gsub(filt or default)

    @classmethod
    def random(cls, n: int = 12, dx: float = 100, dy: float = 100, rng=_random) -> "Shape":
        """Forma aleatoria: envolvente convexa de `n` puntos al azar."""
        pts = Point(0, 0).rand({"n": n, "dx": dx, "dy": dy}, rng=rng)
        return cls(points_to_shape(to_convex(pts)))


def _segments_code(segs: Sequence[Segment]) -> str:
    """Codigo ASS de una lista de segmentos (cada uno aporta sus puntos salvo el de partida en l/b)."""
    pts: List[Point] = []
    for s in segs:
        body = s.pts if s.t == "m" else s.pts[1:]
        for p in body:
            pts.append(Point(p.x, p.y, s.t))
    return tocode(pts) if pts else ""


# --- API a nivel de modulo, como `ke.shape.*` del original ---
circle, triangle, rectangle, pixel, heart = CIRCLE, TRIANGLE, RECTANGLE, PIXEL, HEART
shine1t, shine2t, trebol, feather, bubble = SHINE1T, SHINE2T, TREBOL, FEATHER, BUBBLE
star, sakura, test = STAR, SAKURA, TEST


def new(code: Any = "") -> Shape:
    return Shape(code)


def pixels(code: Any):
    """Pixeles de una forma como objetos con atributos `.x`, `.y`, `.a` (ke.shape.pixels)."""
    from types import SimpleNamespace
    return [SimpleNamespace(**px) for px in Shape(code).pixels()]


# Resto de formas predefinidas (Kara Effector 3.6 / ke4.shape): flower*, cristal17, geometric10, pentagon... Las de
# arriba (librería nueva) tienen prioridad si el nombre coincide.
from .ke_shape_library import PREDEFINED as _PREDEFINED  # noqa: E402

globals().update({_k: _v for _k, _v in _PREDEFINED.items() if _k not in globals()})


def movevc(*args, **kwargs):
    """`shape.movevc(forma, 'tag', ancho, alto)` (firma de los listados) NO esta en effector-auto4.lua.

    Effector 4 solo define `tag.movevc(Shape, posx, posy, Dx, Dy, Time_i, Time_f)`: usa `ke.tag.movevc`."""
    raise NotImplementedError(
        "shape.movevc(forma, 'tag', ancho, alto) no existe en effector-auto4.lua; esa libreria solo define "
        "tag.movevc(Shape, posx, posy, Dx, Dy, Time_i, Time_f) -> usa ke.tag.movevc(...) con esos argumentos.")

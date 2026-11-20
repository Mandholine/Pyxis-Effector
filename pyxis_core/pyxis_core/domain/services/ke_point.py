# -*- coding: utf-8 -*-
# Port de `ke.shape.point` (newkara_library.lua de Effector).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Punto 2D (coordenadas ASSDraw: y crece hacia abajo) y operaciones sobre grupos de puntos. Puro.

`Point` es inmutable por convencion: las operaciones devuelven puntos nuevos. `t` es el tipo de
nodo del dibujo ASS ("m", "l", "b" o None).
"""

from __future__ import annotations

import math
import random as _random
import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from . import ke_math
from .ke_common import EPSILON, ROUND_NUM, get_numbers, round_half_up

_POINT_RE = re.compile(r"([blm])?\s*(-?\d[.\d]*)\s+(-?\d[.\d]*)")


def _r(v: float) -> float:
    return round_half_up(v, ROUND_NUM)


class Point:
    """ke.shape.point"""

    __slots__ = ("x", "y", "t", "z", "w")

    def __init__(self, x: Any = 0, y: Any = None, t: Optional[str] = None):
        if isinstance(x, Point):
            x, y, t = x.x, x.y, t or x.t
        elif isinstance(x, str) and y is not None:  # coordenadas como texto: Point("12", "5")
            x, y = float(x), float(y)
        elif isinstance(x, str):
            m = _POINT_RE.search(x)
            if m:
                t, x, y = m.group(1) or t, float(m.group(2)), float(m.group(3))
            else:
                x = 0
        elif isinstance(x, dict):
            x, y, t = x.get("x", x.get(1, 0)), x.get("y", x.get(2, 0)), x.get("t", t)
        elif isinstance(x, (list, tuple)):
            x, y, t = (list(x) + [0, 0])[0], (list(x) + [0, 0])[1], (x[2] if len(x) > 2 else t)
        self.x = _r(float(x or 0))
        self.y = _r(float(y or 0))
        self.t = t
        self.z = None
        self.w = None

    # ---- protocolo ---------------------------------------------------------
    @classmethod
    def new(cls, x: Any = 0, y: Any = None, t: Optional[str] = None) -> "Point":
        return cls(x, y, t)

    def copy(self) -> "Point":
        return Point(self.x, self.y, self.t)

    def __iter__(self):
        yield self.x
        yield self.y

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    def __len__(self):
        return 2

    def __repr__(self):
        return "(%s, %s)" % (_fmt(self.x), _fmt(self.y))

    def __str__(self):
        return "%s %s " % (_fmt(self.x), _fmt(self.y))

    def __hash__(self):
        return hash((round(self.x, 4), round(self.y, 4)))

    def __eq__(self, other):
        if not hasattr(other, "x"):
            return False
        return abs(self.x - other.x) <= EPSILON and abs(self.y - other.y) <= EPSILON

    def __lt__(self, other):
        return self.x < other.x or (self.x == other.x and self.y < other.y)

    def __le__(self, other):
        return self.x <= other.x and self.y <= other.y

    # ---- aritmetica --------------------------------------------------------
    def __neg__(self):
        return Point(-self.x, -self.y, self.t)

    def __add__(self, other):
        ax, ay = ke_math.get_pair(other, 0, 0)
        return Point(self.x + ax, self.y + ay, self.t)

    __radd__ = __add__

    def __sub__(self, other):
        sx, sy = ke_math.get_pair(other, 0, 0)
        return Point(self.x - sx, self.y - sy, self.t)

    def __rsub__(self, other):
        return Point(other) - self

    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            other = (other, other)
        dx, dy = ke_math.get_pair(other, 1)
        return Point(self.x / dx, self.y / dy, self.t)

    def __mul__(self, other):
        if isinstance(other, ke_math.Matrix):
            res = other * self
            p = Point(res[0], res[1], self.t)
            p.z = res[2] if len(res) > 2 else None
            p.w = res[3] if len(res) > 3 else None
            return p
        if isinstance(other, (int, float)):
            return Point(other * self.x, other * self.y, self.t)
        return self.x * other.x + self.y * other.y  # producto punto

    def __rmul__(self, other):
        return self.__mul__(other)

    # ---- medidas -----------------------------------------------------------
    def len2(self) -> float:
        return self.x * self.x + self.y * self.y

    def len(self) -> float:
        return math.sqrt(self.len2())

    def distance(self, other, *more) -> float:
        return ke_math.distance(self, other) if not more else ke_math.distance([self, other, *more])

    def middle(self, other: Any = None) -> "Point":
        return (self + (other if other is not None else Point(0, 0))) / 2

    def ortho(self) -> "Point":
        """Vector normal: (-y, x)."""
        return Point(-self.y, self.x)

    def cross(self, other) -> float:
        return self.x * other.y - self.y * other.x

    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y

    def clockwise(self, other, third) -> bool:
        return (other - self).cross(third - self) >= 0

    def collinear(self, other, third) -> bool:
        return abs((other - self).cross(third - self)) < EPSILON

    def angle(self, other=None, third=None) -> float:
        """Angulo del punto con el origen, o entre dos/tres puntos."""
        if other is None:
            return ke_math.angle(self)
        a1, a2 = ke_math.angle(self, other), ke_math.angle(other, third) if third is not None else 0
        ang = 180 - a1 + a2 if third is not None else a1
        return ang + 360 if ang < 0 else (ang - 360 if ang > 360 else ang)

    def bisector(self, other, third) -> float:
        a1, a2 = ke_math.angle(self, other), ke_math.angle(other, third)
        ang = 180 - a1 + a2
        ang = ang + 360 if ang < 0 else (ang - 360 if ang > 360 else ang)
        ang = a1 + 180 + ang / 2
        return ang + 360 if ang < 0 else (ang - 360 if ang > 360 else ang)

    # ---- relaciones con segmentos -----------------------------------------
    def inline(self, a, b):
        """Parametro t si el punto esta sobre la recta a-b; False si no."""
        a, b = Point(a), Point(b)
        ab, ap = b - a, self - a
        if abs(ap.cross(ab)) > EPSILON:
            return False
        return ap.dot(ab) / ab.len2()

    def intriangle(self, p1, p2, p3) -> bool:
        v1, v2 = p2 - p1, p3 - p1
        qp, dv = self - p1, v1.cross(v2)
        l, m = qp.cross(v2) / dv, v1.cross(qp) / dv
        if l <= 0 or m <= 0:
            return False
        return l + m < 1

    def intersect(self, p1, p2, p3) -> Optional["Point"]:
        """Interseccion de los segmentos (self-p1) y (p2-p3); None si no se cortan."""
        p0 = self
        det = (p0.x - p1.x) * (p2.y - p3.y) - (p0.y - p1.y) * (p2.x - p3.x)
        if det == 0:
            return None
        t = ((p0.x - p2.x) * (p2.y - p3.y) - (p0.y - p2.y) * (p2.x - p3.x)) / det
        u = -((p0.x - p1.x) * (p0.y - p2.y) - (p0.y - p1.y) * (p0.x - p2.x)) / det
        if -EPSILON <= t <= 1 + EPSILON and -EPSILON <= u <= 1 + EPSILON:
            return Point(p0.x + t * (p1.x - p0.x), p0.y + t * (p1.y - p0.y))
        return None

    def perpendicular(self, other, t: float = 0.5, distance: Any = 0) -> "Point":
        """Punto perpendicular al segmento self-other, a la fraccion `t`, separado `distance`
        (un numero, o [fraccion_de_longitud])."""
        if self == other:
            other = self.polar(self.angle() - 90, 32)
        vx, vy = other.x - self.x, other.y - self.y
        length = self.distance(other)
        d = distance[0] * length if isinstance(distance, (list, tuple)) else distance
        px, py = self.x + t * vx, self.y + t * vy
        return Point(px + d * (-vy / length), py + d * (vx / length), self.t)

    def polar(self, angle: float, radius: float, ptype: Optional[str] = None) -> "Point":
        x, y = ke_math.polar(angle, radius)
        return Point(self.x + x, self.y + y, ptype or self.t)

    def topolar(self, other=None) -> Tuple[float, float]:
        other = Point(other) if other is not None else Point(0, 0)
        return self.angle(other), self.distance(other)

    def ratio(self, rxy) -> "Point":
        rx, ry = ke_math.get_pair(rxy, 1)
        return Point(self.x * rx, self.y * ry, self.t)

    def rotate(self, angle: Any = 0, o: Any = None, axis: str = "z") -> "Point":
        o = Point(o) if o is not None else Point(0, 0)
        a = angle
        if isinstance(a, (list, tuple)):
            a = 360 - o.angle(self) + a[0]
        a = -math.radians(a)
        px, py = self.x - o.x, self.y - o.y
        if axis == "x":
            res = Point(px + o.x, math.cos(a) * py + o.y)
        elif axis == "y":
            res = Point(math.cos(a) * px + o.x, py + o.y)
        else:
            res = Point(math.cos(a) * px - math.sin(a) * py + o.x, math.sin(a) * px + math.cos(a) * py + o.y)
        res.t = self.t
        return res

    def distline(self, a, b) -> Tuple[float, float, "Point"]:
        """Distancia, angulo y pie de la perpendicular desde el punto a la recta a-b."""
        a, b = Point(a), Point(b)
        ab = b - a
        t = (self - a).dot(ab) / ab.len2()
        foot = Point(a.x + t * ab.x, a.y + t * ab.y)
        return ke_math.distance(self, foot), ke_math.angle(self, foot), foot

    def reflect(self, p1, p2=None) -> "Point":
        """Reflexion respecto a un punto (p1) o a la recta p1-p2."""
        p1 = Point(p1)
        if p2 is None or p1 == Point(p2):
            return p1 * 2 - self
        p2 = Point(p2)
        v, w = p2 - p1, self - p1
        t = (w.x * v.x + w.y * v.y) / (v.x ** 2 + v.y ** 2)
        aux = (v * t + p1) * 2 - self
        return Point(aux.x, aux.y, self.t)

    # ---- aleatorios e interpolacion ---------------------------------------
    def rand(self, configs: Optional[Dict[str, Any]] = None, rng=_random):
        """Punto(s) al azar alrededor del punto.

        configs: {dx, dy, step, sign} | {radius, step} | {other, rx, ry, step}; con `n` devuelve una lista
        (y `distance` exige una separacion minima entre ellos)."""
        cfg = dict(configs or {})
        st, sg = cfg.get("step", 1), cfg.get("sign", False)
        n = cfg.pop("n", None)
        if n:
            mind = cfg.pop("distance", 0) or 0
            if mind <= 0:
                return [self.rand(cfg, rng) for _ in range(n)]
            cell, found, grid = mind, [], {}

            def key(p):
                return math.floor(p.x / cell), math.floor(p.y / cell)

            def too_close(p):
                cx, cy = key(p)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for q in grid.get((cx + dx, cy + dy), ()):
                            if (q.x - p.x) ** 2 + (q.y - p.y) ** 2 < mind * mind:
                                return True
                return False

            for _ in range(n):
                for _ in range(100):
                    p = self.rand(cfg, rng)
                    if not too_close(p):
                        found.append(p)
                        grid.setdefault(key(p), []).append(p)
                        break
                else:
                    break
            return found
        if "radius" in cfg:
            radius = cfg["radius"]
            radius = (0, radius) if isinstance(radius, (int, float)) else radius
            return self.polar(ke_math.rand(0, 360, 0.2, rng=rng), ke_math.rand(radius[0], radius[1], rng=rng))
        if "other" in cfg:
            other = Point(cfg["other"])
            angle, radius = self.topolar(other)
            rx, ry = cfg.get("rx", 0.25) * radius, cfg.get("ry", 0.5) * radius
            a1 = angle + 180 * ke_math.rand(2, rng=rng)
            a2 = angle + 90 * (-1) ** ke_math.rand(2, rng=rng)
            p1 = ke_math.polar(a1, ke_math.rand(0, rx, st, rng=rng))
            p2 = ke_math.polar(a2, ke_math.rand(0, ry, st, rng=rng))
            return self.polar(angle, ke_math.rand(0, radius, st, rng=rng)) + p1 + p2
        dx, dy = cfg.get("dx", 256), cfg.get("dy", 256)
        rx = ke_math.rand(dx[0], dx[1], st, sg, rng=rng) if isinstance(dx, (list, tuple)) else ke_math.rand(0, dx, st, sg, rng=rng)
        ry = ke_math.rand(dy[0], dy[1], st, sg, rng=rng) if isinstance(dy, (list, tuple)) else ke_math.rand(0, dy, st, sg, rng=rng)
        return self + (rx, ry)

    def ipol(self, t: float = 0, other: Any = None, accel=1, curve: Optional[str] = None,
             n: Optional[int] = None, shape=None):
        """Interpola (curva de Bezier por Bernstein) entre el punto y `other` (punto o lista de puntos).

        curve: "curve+", "curve-", "curve+-", "curve-+" anade puntos de control curvos."""
        other = other if other is not None else Point(0, 0)
        pts: List[Point] = [self] + ([Point(p) for p in other] if _is_point_list(other) else [Point(other)])
        last = pts[-1]
        special = {
            "curve+": (0.35, 0.35), "curve-": (-0.35, -0.35), "curve+-": (0.35, -0.35), "curve-+": (-0.35, 0.35),
        }
        if curve in special:
            s1, s2 = special[curve]
            pts[1:1] = [self.perpendicular(last, 0.33, [s1]), self.perpendicular(last, 0.67, [s2])]
        bn = len(pts)

        def bern(i, n_, u):
            w = ke_math.normalize(u, accel, shape)
            return (math.factorial(n_) / (math.factorial(i) * math.factorial(n_ - i))) * (w ** i) * ((1 - w) ** (n_ - i))

        def at(u):
            x = sum(p.x * bern(i, bn - 1, u) for i, p in enumerate(pts))
            y = sum(p.y * bern(i, bn - 1, u) for i, p in enumerate(pts))
            return Point(x, y, self.t)

        if not n:
            return at(t)
        if n < 2:
            return self
        return [at(k / (n - 1)) for k in range(n)]


def _fmt(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else str(v)


def _is_point_list(obj: Any) -> bool:
    return isinstance(obj, (list, tuple)) and bool(obj) and all(isinstance(p, (Point, dict, list, tuple)) for p in obj)


# ----------------------------------------------------------- grupos de puntos ---


def group(points: Sequence[Point], what: str):
    """Informacion de un grupo de puntos: rank, bounding, n, centroid, convex, coors, lengths."""
    pts = list(points)
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    lengths = [pts[i].distance(pts[i - 1]) for i in range(1, len(pts))]
    info = {
        "rank": {"x": max(xs) - min(xs), "y": max(ys) - min(ys)},
        "bounding": [min(xs), min(ys), max(xs), max(ys)],
        "n": len(pts),
        "centroid": Point(sum(xs) / len(pts), sum(ys) / len(pts)),
        "convex": to_convex(pts),
        "coors": {"x": xs, "y": ys},
        "lengths": lengths,
        "total": sum(lengths),
    }
    return info.get(what, pts)


def sort_points(points: Sequence[Point], mode: Union[str, float, Callable] = "lefttop") -> List[Point]:
    """Rota la lista para que empiece en el punto elegido por `mode`:
    "minx|maxx|miny|maxy|lefttop|righttop|leftbottom|rightbottom", un angulo [0, 360) respecto al
    centroide, o una funcion(a, b) -> bool que decide si `a` es mejor que `b`."""
    pts = list(points)
    n = len(pts)
    sorts = {
        "minx": lambda a, b: a.x < b.x, "maxx": lambda a, b: a.x > b.x,
        "miny": lambda a, b: a.y < b.y, "maxy": lambda a, b: a.y > b.y,
        "lefttop": lambda a, b: a.y < b.y or (a.y == b.y and a.x < b.x),
        "righttop": lambda a, b: a.y < b.y or (a.y == b.y and a.x > b.x),
        "leftbottom": lambda a, b: a.y > b.y or (a.y == b.y and a.x < b.x),
        "rightbottom": lambda a, b: a.y > b.y or (a.y == b.y and a.x > b.x),
    }

    def best_index(better):
        idx = 0
        for i in range(1, n):
            if better(pts[i], pts[idx]):
                idx = i
        return idx

    if isinstance(mode, str):
        index = best_index(sorts.get(mode, lambda a, b: True))
    elif isinstance(mode, (int, float)):
        centroid = group(pts, "centroid")

        def diff(p):
            d = abs(centroid.angle(p) - mode)
            return min(d, 360 - d)

        index = min(range(n), key=lambda i: (diff(pts[i]), i))
    else:
        index = best_index(mode)
    return [pts[(index + i) % n] for i in range(n)]


def _cross3(o: Point, a: Point, b: Point) -> float:
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)


def to_convex(points: Sequence[Point]) -> List[Point]:
    """Envolvente convexa (cadena monotona de Andrew)."""
    pts = list(points)
    if len(pts) < 3:
        return pts
    pts.sort(key=lambda p: (p.x, p.y))
    uniques = [pts[0]]
    for p in pts[1:]:
        if not (abs(p.x - uniques[-1].x) < EPSILON and abs(p.y - uniques[-1].y) < EPSILON):
            uniques.append(p)
    pts = uniques
    if len(pts) < 3:
        return pts
    lower: List[Point] = []
    for p in pts:
        while len(lower) >= 2 and _cross3(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: List[Point] = []
    for p in reversed(pts):
        while len(upper) >= 2 and _cross3(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def to_shape(points: Sequence[Point]) -> str:
    """Codigo ASS "m x y l x y ..." de un grupo de puntos."""
    pts = list(points)
    out = "m %s %s l " % (_fmt(pts[0].x), _fmt(pts[0].y))
    return out + "".join("%s %s " % (_fmt(p.x), _fmt(p.y)) for p in pts[1:])


def triangulate(points: Sequence[Point], rectangle: Optional[Sequence[Point]] = None, as_shape: bool = False):
    """Triangulacion de Delaunay (Bowyer-Watson). Con `rectangle` (4 puntos) parte de ese rectangulo;
    si no, de un super-triangulo que luego se descarta. Devuelve triangulos (listas de 3 Point) o shapes."""

    def orient(a, b, c):
        return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)

    def in_circle(a, b, c, p):
        if orient(a, b, c) < 0:
            b, c = c, b
        ax, ay, bx, by, cx, cy = a.x - p.x, a.y - p.y, b.x - p.x, b.y - p.y, c.x - p.x, c.y - p.y
        det = ((ax * ax + ay * ay) * (bx * cy - cx * by) - (bx * bx + by * by) * (ax * cy - cx * ay)
               + (cx * cx + cy * cy) * (ax * by - bx * ay))
        return det > 0

    def key(p):
        return (p.x, p.y)

    def insert(triangles, p):
        bad = [t for t in triangles if in_circle(t[0], t[1], t[2], p)]
        counter: Dict[Tuple, List] = {}
        for t in bad:
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                k = tuple(sorted((key(a), key(b))))
                if k in counter:
                    counter[k][0] += 1
                else:
                    counter[k] = [1, a, b]
        kept = [t for t in triangles if not any(t is b for b in bad)]
        kept += [[e[1], e[2], p] for e in counter.values() if e[0] == 1]
        return kept

    pts = [Point(p) for p in points]
    if rectangle:
        r = [Point(p) for p in rectangle]
        triangles = [[r[0], r[1], r[2]], [r[0], r[2], r[3]]]
        for p in pts:
            triangles = insert(triangles, p)
    else:
        minx, maxx = min(p.x for p in pts), max(p.x for p in pts)
        miny, maxy = min(p.y for p in pts), max(p.y for p in pts)
        d = max(maxx - minx, maxy - miny) * 10 + 1
        s = [Point(minx - d, miny - d), Point(maxx + d * 2, miny - d), Point(minx - d, maxy + d * 2)]
        triangles = [list(s)]
        for p in pts:
            triangles = insert(triangles, p)
        triangles = [t for t in triangles if not any(v is sv for v in t for sv in s)]
    return [to_shape(t) for t in triangles] if as_shape else [list(t) for t in triangles]

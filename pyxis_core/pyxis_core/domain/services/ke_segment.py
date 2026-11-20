# -*- coding: utf-8 -*-
# Port de `ke.shape.segment` y `ke.shape.beziers` (newkara_library.lua de Effector).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Segmentos de dibujo ASS (m / l / b) y matematicas de curvas de Bezier. Puro.

Un `Segment` guarda su tipo `t` y sus puntos `pts`:
  "m" -> [p]                       (mover)
  "l" -> [p0, p1]                  (linea; con mas puntos es una polilinea)
  "b" -> [p0, p1, p2, p3]          (Bezier cubica; con 3n+1 puntos, una curva compuesta)
"""

from __future__ import annotations

import math
import random as _random
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from . import ke_math
from .ke_common import EPSILON, get_numbers
from .ke_point import Point


# ------------------------------------------------------------------ beziers ---


def _pts(bezier: Any) -> List[Point]:
    if isinstance(bezier, Segment):
        return list(bezier.pts)
    if isinstance(bezier, (list, tuple)) and bezier and isinstance(bezier[0], Point):
        return list(bezier)
    nums = get_numbers(bezier)
    return [Point(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]


def derivative(bezier: Any, t: Optional[float] = None):
    """Derivada de la curva: lista de vectores (sin `t`) o el vector en `t` (De Casteljau)."""
    pts = _pts(bezier)
    n = len(pts) - 1
    der = [(pts[i + 1] - pts[i]) * n for i in range(n)]
    if t is None:
        return der
    count = len(der)
    while count > 1:
        for i in range(count - 1):
            der[i] = der[i] * (1 - t) + der[i + 1] * t
        count -= 1
    return der[0]


def config(bezier: Any, t: float = 0) -> Tuple[Point, float]:
    """Punto de la curva en `t` y el angulo de su tangente (grados, coords ASSDraw)."""
    pts = _pts(bezier)
    work = [Point(p.x, p.y) for p in pts]
    count = len(work)
    while count > 1:
        for i in range(count - 1):
            work[i] = work[i] * (1 - t) + work[i + 1] * t
        count -= 1
    vec = derivative(pts, t)
    return work[0], math.degrees(math.atan2(-vec.y, vec.x))


def length(bezier: Any, t: float = 1, n: int = 8) -> float:
    """Longitud de la curva hasta `t` (Simpson con 2n intervalos sobre |B'|)."""
    pts = _pts(bezier)
    if len(pts) == 2:
        return ke_math.distance(pts[0], pts[1]) * t
    h = t / (2 * n)

    def speed(u: float) -> float:
        v = derivative(pts, u)
        return math.hypot(v.x, v.y)

    total = speed(0) + speed(t)
    total += 4 * sum(speed((2 * i - 1) * h) for i in range(1, n + 1))
    total += 2 * sum(speed(2 * i * h) for i in range(1, n))
    return (h / 3) * total


def length2t(bezier: Any, target: float) -> Optional[float]:
    """Parametro t cuya longitud acumulada es `target`; None si `target` supera la longitud total."""
    pts = _pts(bezier)
    if target > length(pts, 1):
        return None
    if len(pts) == 2:
        return target / ke_math.distance(pts[0], pts[1])
    t, i = 1.0, 1
    cur = length(pts, t)
    for _ in range(60):
        if ke_math.equality(target, cur, 5):
            break
        t += (1 if cur < target else -1) * (1 / (2 ** i))
        cur = length(pts, t)
        i += 1
    return t


def coefficients(bezier: Any) -> Tuple[List[float], List[float]]:
    """Coeficientes ascendentes de los polinomios x(t) e y(t) de la curva."""
    pts = _pts(bezier)
    n = len(pts) - 1
    cx, cy = [0.0] * (n + 1), [0.0] * (n + 1)

    def binom(a, k):
        if k > a:
            return 0
        r = 1
        for i in range(1, k + 1):
            r = r * (a - i + 1) / i
        return r

    for i in range(n + 1):
        for j in range(n - i + 1):
            k = i + j
            coeff = binom(n, i) * binom(n - i, j) * (1 if j % 2 == 0 else -1)
            cx[k] += pts[i].x * coeff
            cy[k] += pts[i].y * coeff
    return cx, cy


def inside(bezier: Any, p: Any) -> Union[float, bool]:
    """Parametro t si el punto `p` pertenece a la curva; False si no."""
    p = Point(p)
    cx, cy = coefficients(bezier)
    cx[0] -= p.x
    for t in ke_math.equation(cx, True):
        if ke_math.between(t, -1e-3, 1 + 1e-3):
            t = ke_math.clamp(t)
            if abs(ke_math.evaluate(cy, t) - p.y) < 1e-3:
                return t
    return False


def roots(bezier: Any) -> Tuple[List[float], List[float]]:
    """Raices (t en [0, 1]) de x(t) y de y(t)."""
    cx, cy = coefficients(bezier)
    keep = lambda rs: [v for v in rs if -EPSILON <= v <= 1 + EPSILON]
    return keep(ke_math.equation(cx, True)), keep(ke_math.equation(cy, True))


# ------------------------------------------------------------------ segmento ---


class Segment:
    """ke.shape.segment"""

    def __init__(self, seg: Any = None, t: Optional[str] = None, pts: Optional[Sequence[Point]] = None):
        if pts is not None:
            self.t, self.pts = t or "l", [Point(p) for p in pts]
            return
        if isinstance(seg, Segment):
            self.t, self.pts = seg.t, [p.copy() for p in seg.pts]
            return
        if isinstance(seg, (list, tuple)) and seg and isinstance(seg[0], Point):
            nums = [c for p in seg for c in (p.x, p.y)]
        else:
            nums = get_numbers(seg)
        self.t = t or ("m" if len(nums) == 2 else "l" if len(nums) == 4 else "b")
        self.pts = [Point(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]

    @classmethod
    def new(cls, seg: Any) -> "Segment":
        return cls(seg)

    def copy(self) -> "Segment":
        return Segment(self)

    # ---- acceso --------------------------------------------------------------
    @property
    def start(self) -> Point:
        return self.pts[0]

    @property
    def end(self) -> Point:
        return self.pts[-1]

    def numbers(self) -> List[float]:
        return [c for p in self.pts for c in (p.x, p.y)]

    def __repr__(self):
        return str(self)

    def __str__(self):
        if self.t == "m" or len(self.pts) < 2:
            return "m %s " % self.pts[0]
        return "m %s%s %s" % (self.pts[0], self.t, "".join(str(p) for p in self.pts[1:]))

    def __len__(self):
        return len(self.pts)

    def reversed(self) -> "Segment":
        return Segment(t=self.t, pts=list(reversed(self.pts)))

    # ---- medidas -------------------------------------------------------------
    def length(self) -> float:
        return 0 if self.t == "m" else length(self.pts)

    def bezier(self, t: float) -> Tuple[Point, float]:
        """Punto y angulo de la curva en `t` (un "m" devuelve su punto)."""
        if self.t == "m":
            return self.pts[0], 0
        return config(self.pts, t)

    def parameter(self, t: Any) -> Tuple[Point, float, float]:
        """Punto, angulo y `t` para un parametro t (o para una longitud `[longitud]`)."""
        if self.t == "m":
            return self.pts[0], 0, 0
        t = length2t(self.pts, t[0]) if isinstance(t, (list, tuple)) else float(t)
        point, angle = self.bezier(t)
        return point, angle, t

    def angle(self, other: Optional["Segment"] = None) -> float:
        if self.t == "m":
            return 0
        if other is not None:
            return self.pts[0].angle(self.pts[1], other.pts[1])
        return ke_math.angle(self.pts[0], self.pts[1])

    def bisector(self, other: "Segment") -> float:
        ang = self.angle() - 180 + 0.5 * self.angle(other)
        return ang + 360 if ang < 0 else (ang - 360 if ang > 360 else ang)

    def to_bezier(self) -> "Segment":
        if self.t != "l":
            return self.copy()
        p0, p3 = self.pts[0], self.pts[-1]
        return Segment(t="b", pts=[p0, Point(p0.x + 0.33 * (p3.x - p0.x), p0.y + 0.33 * (p3.y - p0.y)),
                                    Point(p0.x + 0.67 * (p3.x - p0.x), p0.y + 0.67 * (p3.y - p0.y)), p3])

    def inside(self, p: Any) -> Union[float, bool]:
        """t si el punto pertenece al segmento/curva; False si no."""
        p = Point(p)
        if self.t == "l":
            t = p.inline(self.pts[0], self.pts[1])
            return t if t is not False and ke_math.between(t, 0, 1) else False
        return inside(self.pts, p) if self.t == "b" else False

    # ---- transformaciones ------------------------------------------------------
    def move(self, dxy: Any) -> "Segment":
        dx, dy = ke_math.get_pair(dxy, 0, 0)
        return Segment(t=self.t, pts=[p + (dx, dy) for p in self.pts])

    def ratio(self, rxy: Any) -> "Segment":
        rx, ry = ke_math.get_pair(rxy, 1)
        return Segment(t=self.t, pts=[Point(p.x * rx, p.y * ry) for p in self.pts])

    def rotate(self, angle: float, o: Any = None) -> "Segment":
        """Rota respecto a `o` (punto; 0 = inicio, 1 = fin; por defecto el origen)."""
        org = self.pts[0] if o == 0 and not isinstance(o, Point) else (self.pts[-1] if o == 1 and not isinstance(o, Point) else o)
        return Segment(t=self.t, pts=[p.rotate(angle, org) for p in self.pts])

    def extend(self, ext_i: float = 0, ext_f: float = 0) -> "Segment":
        a = self.angle()
        pts = list(self.pts)
        pts[0], pts[-1] = pts[0].polar(a + 180, ext_i), pts[-1].polar(a, ext_f)
        return Segment(t=self.t, pts=pts)

    # ---- division ----------------------------------------------------------------
    def cut(self, t: Any, rng=_random):
        """Divide en `t` -> (izq, der, punto). Con dict {t:[..]|n:int|random:int|[a,b]} devuelve la curva
        compuesta con todos los cortes."""
        if isinstance(t, dict):
            ts: List[float] = []
            if "t" in t:  # fracciones absolutas ascendentes
                ts = list(t["t"]) if isinstance(t["t"], (list, tuple)) else [t["t"]]
            if "n" in t:
                ts = [i / t["n"] for i in range(1, t["n"])]
            if "random" in t:
                r = t["random"]
                tn = ke_math.rand(r[0], r[1], rng=rng) if isinstance(r, (list, tuple)) else r
                ts = sorted(ke_math.rand(0.05, 0.95, 0.001, rng=rng) for _ in range(tn - 1))
            ts = [x for x in ts if 0 < x < 1]
            if not ts:
                return self
            parts, cur, last = [], self, 0.0
            for x in ts:
                left, cur, _ = cur.cut((x - last) / (1 - last))
                parts.append(left)
                last = x
            parts.append(cur)
            joined = parts[0].copy()
            for part in parts[1:]:
                joined.pts += part.pts[1:]
            return joined
        if self.t == "m":
            return self
        pts = self.pts
        if self.t == "b" and len(pts) == 4:
            S = pts
            b0, b1, b2 = S[0] * (1 - t) + S[1] * t, S[1] * (1 - t) + S[2] * t, S[2] * (1 - t) + S[3] * t
            b3, b4 = b0 * (1 - t) + b1 * t, b1 * (1 - t) + b2 * t
            b5 = b3 * (1 - t) + b4 * t
            return (Segment(t="b", pts=[S[0], b0, b3, b5]), Segment(t="b", pts=[b5, b4, b2, S[3]]), Point(b5.x, b5.y))
        p0, p2 = pts[0], pts[-1]
        p1 = Point(p0.x + t * (p2.x - p0.x), p0.y + t * (p2.y - p0.y))
        return Segment(t="l", pts=[p0, p1]), Segment(t="l", pts=[p1, p2]), p1

    def split(self, split: Any = 2) -> "Segment":
        """Redibuja el segmento como lineas rectas de longitud `split` (o `[n_segmentos]`)."""
        segms = split[0] if isinstance(split, (list, tuple)) else None
        if self.t == "m":
            return self
        if self.t == "l":
            p0, p1 = self.pts[0], self.pts[-1]
            angle, total = p0.angle(p1), p0.distance(p1)
            step = total / segms if segms else total / max(1, ke_math.round_(total / split))
            n = max(1, ke_math.round_(total / step)) if step else 1
            return Segment(t="l", pts=[p0] + [p0.polar(angle, step * k) for k in range(1, n + 1)])
        total = self.length()
        step = total / segms if segms else split
        out, k = [self.pts[0]], 1
        while True:
            t = length2t(self.pts, k * step)
            if t is None or t > 1:
                out.append(self.bezier(1)[0])
                break
            out.append(self.bezier(t)[0])
            k += 1
        return Segment(t="l", pts=out)

    # ---- interseccion ---------------------------------------------------------------
    def intersect(self, other: Any, without_vertices: bool = False):
        """Interseccion con otro segmento: linea-linea -> (Point, t, u) o False; linea-curva -> lista de
        {"p", "t", "u"} (hasta 3) o False."""
        s1, s2 = Segment(self), Segment(other)
        if s1.t == "l" and s2.t == "l":
            den = (s1.pts[1].x - s1.pts[0].x) * (s2.pts[0].y - s2.pts[1].y) - (s2.pts[0].x - s2.pts[1].x) * (s1.pts[1].y - s1.pts[0].y)
            if den == 0:
                return False
            hit = ke_math.intersect(s1.numbers()[:4], s2.numbers()[:4])
            back = ke_math.intersect(s2.numbers()[:4], s1.numbers()[:4])
            if hit is None or back is None:
                return False
            x, y, t = hit
            s = back[2]
            a1, a2 = s1.angle(), s2.angle()
            if without_vertices:
                bad = t <= 0 or t >= 1 or s <= 0 or s >= 1
            else:
                bad = t < 0 or t > 1 or s < 0 or s > 1
            if bad or abs(a1 - a2) == 180 or a1 == a2:
                return False
            return Point(x, y), t, s
        if s1.t == "l" or s2.t == "l":
            seg, bez = (s1, s2) if s1.t == "l" else (s2, s1)
            poly = bez.split(1).pts
            result = []
            for i in range(1, len(poly)):
                hit = seg.intersect(Segment(t="l", pts=[poly[i - 1], poly[i]]))
                if hit:
                    result.append({"p": hit[0], "t": hit[1], "u": hit[2]})
                if len(result) == 3:
                    break
            return result or False
        return False

    def intax(self, other: Any) -> bool:
        """True si los segmentos son colineales y se solapan."""
        s1, s2 = Segment(self), Segment(other)
        a1, a2 = s1.angle(), s2.angle()
        p0, p1, q0, q1 = s1.pts[0], s1.pts[-1], s2.pts[0], s2.pts[-1]
        if ((p0 == q0 and abs(a1 - a2) == 180) or (p0 == q1 and a1 == a2)
                or (p1 == q1 and abs(a1 - a2) == 180) or (p1 == q0 and a1 == a2)):
            return False
        if s1.intersect(s2):
            return False
        x0, y0, x1, y1 = s1.numbers()[:4]
        x2, y2, x3, y3 = s2.numbers()[:4]
        if ((x0 > x2 and x0 > x3 and x1 > x2 and x1 > x3) or (x0 < x2 and x0 < x3 and x1 < x2 and x1 < x3)
                or (y0 > y2 and y0 > y3 and y1 > y2 and y1 > y3) or (y0 < y2 and y0 < y3 and y1 < y2 and y1 < y3)):
            return False
        return a1 == a2 or abs(a1 - a2) == 180

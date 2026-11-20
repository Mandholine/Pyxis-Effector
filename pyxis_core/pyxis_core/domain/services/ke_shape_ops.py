# -*- coding: utf-8 -*-
# Port de `ke.shape` (parte 2: operaciones y generadores) de newkara_library.lua de Effector.
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Operaciones de `Shape` (mezcla `ShapeOps`) y generadores de formas (multi1-8, polygon, banner, gear...).

`ShapeOps` se mezcla en `ke_shape.Shape`; por eso este modulo importa `Shape` de forma perezosa.
"""

from __future__ import annotations

import math
import random as _random
import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from . import ke_alpha, ke_color, ke_math, ke_segment
from .ke_common import EPSILON, ROUND_NUM
from .ke_point import Point, to_convex
from .ke_segment import Segment


def _S():
    from .ke_shape import Shape
    return Shape


def _f(v: float) -> str:
    v = round(float(v), ROUND_NUM)
    return str(int(v)) if v == int(v) else str(v)


def newlen_spread(items: Sequence[Any], n: int) -> List[Any]:
    """Reparte `n` elementos entre los `items` (ke.table "newlen" con {n}): ["a","b","c"], 5 -> a a b b c."""
    base, extra = divmod(n, len(items))
    out: List[Any] = []
    for i, it in enumerate(items):
        out += [it] * (base + (1 if i < extra else 0))
    return out


def length2seg(shape, length: float) -> Optional[Tuple[Segment, float]]:
    """Segmento de la forma que contiene la longitud acumulada `length` y la longitud local dentro de el."""
    segs = shape.segments()
    off = [0.0]
    for s in segs:
        off.append(off[-1] + s.length())
    length = off[-1] if abs(off[-1] - length) < 1 else length
    for i in range(1, len(segs)):
        if off[i] <= length <= off[i + 1]:
            return segs[i], length - off[i]
    return None


class ShapeOps:
    """Operaciones adicionales de `Shape` (herramientas, deformaciones y rasterizado)."""

    # ---- filtros -------------------------------------------------------------------------
    def filter(self, split: Optional[float] = None, *filters: Any):
        """Aplica uno o mas filtros: funciones (x, y[, ctx]) o formas/codigo (-> glue, o [forma, modo])."""
        S = _S()
        shp = self.redraw(split) if split and split > 0 else self
        flist = list(filters[0]) if len(filters) == 1 and isinstance(filters[0], list) and not callable(filters[0]) else list(filters)
        if not flist:
            flist = [lambda x, y: (x, y)]
        for f in flist:
            if isinstance(f, (str, S)) or (isinstance(f, (list, tuple)) and f):
                code, mode = (f[0], f[1] if len(f) > 1 else None) if isinstance(f, (list, tuple)) else (f, None)
                shp = shp.glue(code, mode)
            else:
                shp = shp.gsub(f)
        return shp.reduce()

    def filtergroup(self, filt: Callable):
        """Aplica `filt(i, n, subforma, forma) -> Shape` a cada subforma y las une."""
        S = _S()
        subs = self.subshapes()
        n = len(subs)
        return S("".join(filt(i, n, s, self).code for i, s in enumerate(subs, 1)))

    def glue(self, other: Any, mode: Any = 1, split: float = 2):
        """Hace que la forma adopte la curva de `other` (modo 1 centrado, 2 inicio, 3 fin, 4 justificado o funcion)."""
        S = _S()
        mode = 1 if mode is None else mode
        width = self.width
        shp = self.redraw(split)
        code = other.code if isinstance(other, S) else str(other)
        m = re.search(r"m\s+-?\d[.\-\d lb]*", code)
        path = S(m.group(0) if m else code).redraw(3)
        ratio = ke_math.round_(width / path.length(), ROUND_NUM) if path.length() else 1
        ident = lambda x, y: (x, y)
        if callable(mode):
            filt = mode
        elif path.length() < width:
            filt = ident
        elif mode == 1:
            filt = lambda x, y: ((1 - ratio) / 2 + ratio * x, y)
        elif mode == 2:
            filt = lambda x, y: (ratio * x, y)
        elif mode == 3:
            filt = lambda x, y: (1 - ratio + ratio * x, y)
        else:
            filt = ident
        pts = path._coords()
        segments: List[List[float]] = []
        total = 0.0
        for a, b in zip(pts, pts[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            dist = math.hypot(dx, dy)
            if dist > 0:
                segments.append([a[0], a[1], dx, dy, dist, 0.0, 0.0])
                total += dist
        if not segments:
            return shp
        curve = 0.0
        for seg in segments:
            seg[5] = curve / total
            curve += seg[4]
            seg[6] = curve / total
        x0, y0, x1, y1 = shp.bounding()
        if not x1 > x0:
            return shp

        def warp(x, y):
            px, py = (x - x0) / width, y - y1
            dx, dy = filt(px, py)
            px, py = max(0, min(dx, 1)), dy
            for sg in segments:
                if sg[5] <= px <= sg[6]:
                    pos = (px - sg[5]) / (sg[6] - sg[5])
                    ox, oy = -sg[3], sg[2]
                    curve_len = math.hypot(ox, oy)
                    ox, oy = (ox * py / curve_len, oy * py / curve_len) if curve_len else (0, 0)
                    return sg[0] + pos * sg[2] + ox, sg[1] + pos * sg[3] + oy
            return x, y

        return shp.gsub(warp)

    # ---- conversion y corte --------------------------------------------------------------------
    def to_line(self, tract: float = 5):
        return self.redraw(tract, "bezier")

    def to_bezier(self):
        S = _S()
        return S([s.to_bezier() if s.t == "l" else s for s in self.segments()])

    def cut(self, t: float = 0.5):
        """Corta la forma a la fraccion `t` del perimetro -> (forma, (punto, angulo, t)). t < 0 corta desde el final."""
        S = _S()
        if t < 0:
            s, info = self.inverse().cut(-t)
            return s.inverse(), info
        t = ke_math.clamp(t)
        if t == 1:
            return self.copy(), None
        segs = self.segments()
        lengths = [s.length() for s in segs]
        acc = [0.0]
        for ln in lengths:
            acc.append(acc[-1] + ln)
        target = t * self.length()
        k = len(segs) - 1
        for i in range(len(segs)):
            if target <= acc[i + 1]:
                k = i
                break
        newt = (target - acc[k]) / lengths[k] if lengths[k] > 0 else 0
        part = segs[k].cut(newt)
        left = part[0] if isinstance(part, tuple) else part
        new = segs[:k] + [left]
        return S(new), segs[k].parameter(newt)

    def parameter(self, t: Any = None, n: Optional[int] = None):
        """Punto y angulo en la fraccion `t` del perimetro (o `[longitud]`); con `n`, lista de n (punto, angulo)."""
        if n:
            n = math.ceil(abs(n))
            div = n if self.is_closed() else n - 1
            return [self.parameter(i / div if div else 0) for i in range(n)]
        length = t[0] if isinstance(t, (list, tuple)) else t * self.length()
        found = length2seg(self, length)
        if found is None:
            return self.points()[-1], 0
        seg, local = found
        nwt = ke_segment.length2t(seg, local)
        return ke_segment.config(seg, 1 if nwt is None else nwt)

    def getpoint(self, t: Any):
        return self.parameter(t)

    def get_parameter(self, p: Any) -> Optional[float]:
        """Fraccion del perimetro donde esta el punto `p` (si pertenece al contorno); None si no."""
        p = Point(p)
        closed = self.closed()
        perimeter = closed.length()
        accum = 0.0
        for sub in closed.unclosed().subshapes():
            pnt, n = sub.points(), sub.n
            for i in range(n):
                p1, p2 = pnt[i], pnt[0] if i == n - 1 else pnt[i + 1]
                seg = p1.distance(p2)
                if p == p1:
                    return accum / perimeter
                dist1 = p1.distance(p)
                if abs(dist1 + p.distance(p2) - seg) < EPSILON:
                    return (accum + dist1) / perimeter
                accum += seg
        return None

    # ---- contornos --------------------------------------------------------------------------------
    @staticmethod
    def _ends(pnt: List[Point]) -> Tuple[Point, Point]:
        n = len(pnt)
        if pnt[0] == pnt[-1]:
            return pnt[n - 2], pnt[1]
        return pnt[0].polar(pnt[1].angle(pnt[0]), 1), pnt[-1].polar(pnt[n - 2].angle(pnt[-1]), 1)

    def line(self, bord: Optional[float] = None, mode: str = "miter"):
        """Convierte el perimetro en una forma lineal de grosor `bord` (mode: miter | round | bevel)."""
        S = _S()
        bord = 0.5 * abs(bord) if bord else 4
        shp = self.reduce()
        rat, result = 0.115, ""
        for s in shp.subshapes():
            pnt, n = s.points(), s.n
            exterior: List[Point] = []
            interior: List[Point] = []
            first, last = self._ends(pnt)
            for k in range(n):
                p0 = first if k == 0 else pnt[k - 1]
                p1, p2 = pnt[k], last if k == n - 1 else pnt[k + 1]
                ang1, ang2 = p0.bisector(p1, p2), p0.angle(p1, p2)
                sin = math.sin(math.radians(ang1 - p1.angle(p0) - (0 if ang2 <= 300 else rat) * ang2))
                radius = abs(bord / sin) if abs(sin) > 1e-9 else abs(bord)
                if ang2 <= 300:
                    exterior.append(p1.polar(ang1, radius))
                    interior.append(p1.polar(ang1, -radius))
                else:
                    exterior.append(p1.polar(ang1 - rat * ang2, radius))
                    interior.append(p1.polar(ang1 - rat * ang2, -radius))
                    if k != n - 1:
                        exterior.append(p1.polar(ang1 + rat * ang2, radius))
                        interior.append(p1.polar(ang1 + rat * ang2, -radius))
            ext, inn = S(exterior), S(interior).inverse()
            ratio = 2.4 if mode == "round" else 1.8
            if mode != "miter":
                if s.is_clockwise():
                    inn = inn.roundout(ratio * bord, mode)
                else:
                    ext = ext.roundout(ratio * bord, mode)
            inner_code = inn.code if s.is_closed() else inn.code.replace("m", "l")
            result += ext.code + inner_code
        return S(result)

    def offset(self, bord: float = 6, mode: str = "miter"):
        if mode in ("round", "bevel"):
            return self.roundout(bord * 1.48, mode).line(bord)
        return self.line(bord)

    def expand(self, pixel: float = 4):
        """Expande la forma segun el sentido de su trazado."""
        S = _S()
        result = ""
        for s in self.reduce().subshapes():
            pnt, n = s.points(), s.n
            first, last = self._ends(pnt)
            path: List[Point] = []
            for k in range(n):
                p0 = first if k == 0 else pnt[k - 1]
                p1, p2 = pnt[k], last if k == n - 1 else pnt[k + 1]
                angle = p0.bisector(p1, p2)
                sin = math.sin(math.radians(angle - p1.angle(p0)))
                path.append(p1.polar(angle, pixel / sin if abs(sin) > 1e-9 else pixel))
            result += S(path).code
        return S(result)

    # ---- rasterizado -----------------------------------------------------------------------------------
    def pixels(self) -> List[Dict[str, Any]]:
        """Pixeles de la superficie: [{"a": alpha ASS, "x": ..., "y": ...}] (muestreo 8x8 por pixel)."""
        upscale = 8
        down = 1 / upscale
        shp = self.ratio(upscale)
        x1, y1, x2, y2 = shp.bounding()
        shift_x, shift_y = -(x1 - x1 % upscale), -(y1 - y1 % upscale)
        shp = shp.displace({"x": shift_x, "y": shift_y})
        width = math.ceil((x2 + shift_x) * down) * upscale
        height = math.ceil((y2 + shift_y) * down) * upscale
        img = [False] * (width * height)
        red = shp.redraw(upscale, "bezier")
        ymin, ymax = red.miny, red.maxy
        lines: List[Tuple[float, float, float, float]] = []
        last: Optional[Tuple[int, int]] = None
        for x, y in red._coords():
            x, y = ke_math.round_(x), ke_math.round_(y)
            if last and last[1] != y and not (last[1] < 0 and y < 0) and not (last[1] > height and y > height):
                lines.append((last[0], last[1], x - last[0], y - last[1]))
            last = (x, y)
        for y in range(max(math.floor(ymin), 0), min(math.ceil(ymax), height)):
            stops = []
            for lx, ly, vx, vy in lines:
                if vy != 0:
                    s = (y + 0.5 - ly) / vy
                    if 0 <= s <= 1:
                        stops.append((min(max(lx + s * vx, 0), width), 1 if vy > 0 else -1))
            if len(stops) > 1:
                stops.sort(key=lambda a: a[0])
                status = 0
                for i in range(len(stops) - 1):
                    status += stops[i][1]
                    if status != 0:
                        for x in range(math.ceil(stops[i][0] - 0.5), math.floor(stops[i + 1][0] + 0.5)):
                            if 0 <= x < width:
                                img[y * width + x] = True
        out = []
        for y in range(0, height - upscale + 1, upscale):
            for x in range(0, width - upscale + 1, upscale):
                opacity = 0
                for yy in range(upscale):
                    row = (y + yy) * width + x
                    opacity += 255 * sum(img[row:row + upscale])
                if opacity > 0:
                    out.append({"a": ke_alpha.ass(255 - opacity * down ** 2),
                                "x": (x - shift_x) * down + 1, "y": (y - shift_y) * down + 1})
        return out

    # ---- deformaciones -------------------------------------------------------------------------------------
    def tensor(self, inbox: Any = None, t: float = 1):
        """Deforma la forma para que su caja adopte la silueta de `inbox` (4 curvas Bezier)."""
        S = _S()
        sw, sh = self.width, self.height
        other = S(inbox) if inbox is not None else S("m 0 0 l 0 100 l 100 100 l 100 0 l 0 0 ").size(sw, sh)
        xbox = other.to_bezier().segments()[1:]
        xbox[2], xbox[3] = xbox[2].reversed(), xbox[3].reversed()
        sup, inf, izq, der = (xbox[3].pts, xbox[1].pts, xbox[0].pts, xbox[2].pts)
        ow, oh = other.width, other.height

        def filt(x, y, ctx):
            u, v = ctx.My, ctx.Mx
            pt, pb = sup[0].ipol(u, sup[1:]), inf[0].ipol(u, inf[1:])
            pl, pr = izq[0].ipol(v, izq[1:]), der[0].ipol(v, der[1:])
            vert, hori = pt.ipol(v, pb) * (sw / ow), pl.ipol(u, pr) * (sh / oh)
            return x + (hori.x - x) * t, y + (vert.y - y) * t

        return self.gsub(filt)

    def inbounding(self, angle: float = 0):
        """Punto (y distancia al centroide) donde el rayo con `angle` corta la caja envolvente."""
        box = list(self.box())
        c = self.centroid
        p = c.polar(angle, self.radius + 10)
        for i in range(4):
            hit = c.intersect(p, box[i], box[(i + 1) % 4])
            if hit:
                return hit, hit.distance(c)
        return None

    def inboundary(self, angle: float = 0):
        """Punto (y distancia) donde el rayo con `angle` corta el contorno de la primera subforma."""
        sub = self.subshapes()[0]
        c = sub.centroid
        pnt, n = sub.points(), sub.n
        p = c.polar(angle, sub.radius + 10)
        for i in range(n):
            hit = c.intersect(p, pnt[i], pnt[(i + 1) % n])
            if hit:
                return hit, hit.distance(c)
        return None

    def inconvex(self, angle: float = 0):
        """Punto (y distancia) donde el rayo con `angle` corta la envolvente convexa."""
        hull = to_convex(self.points())
        c = self.centroid
        p = c.polar(angle, self.radius + 10)
        n = len(hull)
        for i in range(n):
            hit = c.intersect(p, hull[i], hull[(i + 1) % n])
            if hit:
                return hit, hit.distance(c)
        return None

    def distort(self, other: Any, t: float = 1, source: str = "convex", target: str = "boundary"):
        """Deforma la forma hasta tomar la silueta de `other`."""
        S = _S()
        funcs = {"convex": lambda s, a: s.inconvex(a), "boundary": lambda s, a: s.inboundary(a)}
        original, other = self.copy(), S(other).reduce()
        shp = self.redraw(4)
        c = shp.centroid
        out: List[Point] = []
        for p in shp.points():
            angle, dis = c.topolar(p)
            r1 = (funcs[source](original, angle) or (None, None))[1]
            hit2 = funcs[target](other, angle) or funcs[target](other, -angle)
            r2 = hit2[1] if hit2 else None
            if not r1 or r2 is None:
                out.append(p)
                continue
            q = c.polar(angle, dis + (dis * r2 / r1 - dis) * t)
            q.t = p.t
            out.append(q)
        return S(out).reduce()

    def flexor(self, anycurve: Any, t: float = 1, axis: Optional[str] = None):
        """Estira la forma para que siga una curva."""
        S = _S()
        shp = self.rotate(-90) if axis == "y" else self
        h = shp.height
        curve, _ = S(anycurve).cut(t if t is not None else 1)

        def filt(x, y, ctx):
            p, a = curve.parameter(ctx.My)
            q = p.polar(a, h / 2 - y)
            return q.x, q.y

        split = ke_math.round_(shp.length() / (0.42 * (h + curve.length())), ROUND_NUM)
        return shp.redraw(split).gsub(filt)

    def inflated(self, t: float, split: float = 4, ratio: float = 1, mode: str = "circle"):
        """Infla la forma hacia un circulo o una elipse."""
        S = _S()
        shp = self.ratio(ratio).redraw(split)
        result: List[Point] = []
        for s in shp.subshapes():
            c, w, h = s.centroid, s.width, s.height
            diameter = math.sqrt((w * w + h * h) / 2)
            r1 = (diameter if mode == "circle" else w) * math.sqrt(2) / 2
            r2 = (diameter if mode == "circle" else h) * math.sqrt(2) / 2
            for p in s.points():
                dx, dy = p.x - c.x, p.y - c.y
                dist = math.hypot(dx, dy)
                if dist > EPSILON:
                    cs, sn = math.cos(math.atan2(dy, dx)), math.sin(math.atan2(dy, dx))
                    rad = (r1 * r2) / math.sqrt(r2 * r2 * cs * cs + r1 * r1 * sn * sn)
                    nd = dist * (1 - t) + rad * t
                    result.append(Point(c.x + dx / dist * nd, c.y + dy / dist * nd, p.t))
                else:
                    result.append(Point(p.x, p.y, p.t))
        return S(result)

    def matrix(self, m: Any):
        """Aplica una matriz (3x3 / 4x4) a todos los puntos."""
        S = _S()
        mat = m if isinstance(m, ke_math.Matrix) else ke_math.Matrix(m)
        return S("".join(S([p * mat for p in s.points()]).code for s in self.subshapes()))

    def to_clip(self, x: float, y: float, iclip: bool = False) -> str:
        """\\clip(...)/\\iclip(...) con la forma centrada en (x, y)."""
        return "\\%sclip(%s)" % ("i" if iclip else "", self.displace({"x": x, "y": y, "mode": "center"}).code)

    def divide(self) -> List[str]:
        """Cada subforma precedida de dos marcas que fijan la caja de toda la forma."""
        x1, y1, x2, y2 = self.bounding()
        mark = "m %s %s l %s %s m %s %s l %s %s " % (_f(x1), _f(y1), _f(x2), _f(y1), _f(x1), _f(y2), _f(x2), _f(y2))
        return [mark + s.code for s in self.subshapes()]

    def splitmove(self):
        """Parte los segmentos en y=0 (para animar con \\move)."""
        S = _S()
        out: List[Segment] = []
        for s in self.segments():
            if s.t == "m":
                out.append(s)
            elif s.t == "l":
                a, b = s.pts[0], s.pts[-1]
                if a.y * b.y < 0:
                    p = Point(a.x + (-a.y / (b.y - a.y)) * (b.x - a.x), 0)
                    out += [Segment(t="l", pts=[a, p]), Segment(t="l", pts=[p, b])]
                else:
                    out.append(s)
            else:
                _, yroots = ke_segment.roots(s)
                curve, ini, last = s, 0.0, None
                for t in yroots:
                    if t <= ini or t >= 1:
                        continue
                    c1, c2, _ = curve.cut((t - ini) / (1 - ini))
                    ini = t
                    out.append(c1)
                    curve = c2
                    last = c2
                out.append(last or s)
        return S(out)

    def insert(self, other: Any):
        """Iguala tipo y cantidad de segmentos de dos formas para poder interpolarlas -> (self, other)."""
        S = _S()
        a_parts, b_parts = self.parts(), S(other).parts()
        n = max(len(a_parts), len(b_parts))
        a_parts = newlen_spread(a_parts, n) if len(a_parts) < n else a_parts
        b_parts = newlen_spread(b_parts, n) if len(b_parts) < n else b_parts
        out_a, out_b = "", ""
        for pa, pb in zip(a_parts, b_parts):
            sa, sb = re.findall(r"[mlb][^mlb]*", pa), re.findall(r"[mlb][^mlb]*", pb)
            ma, mb = sa.pop(0), sb.pop(0)
            m = max(len(sa), len(sb))
            sa = newlen_spread(sa, m) if sa and len(sa) < m else sa
            sb = newlen_spread(sb, m) if sb and len(sb) < m else sb
            sa, sb = [ma] + sa, [mb] + sb
            for k in range(1, len(sa)):
                t1, t2 = re.match(r"[mbl]", sa[k]).group(0), re.match(r"[mbl]", sb[k]).group(0)
                if t1 == t2:
                    continue

                def as_bezier(prev: str, cur: str) -> str:
                    p0 = Point(*re.findall(r"-?\d[.\d]*", prev)[-2:])
                    p3 = Point(*re.findall(r"-?\d[.\d]*", cur)[-2:])
                    p1, p2 = p0.ipol(0.33, p3), p0.ipol(0.66, p3)
                    return "b %s %s %s %s %s %s " % (_f(p1.x), _f(p1.y), _f(p2.x), _f(p2.y), _f(p3.x), _f(p3.y))

                if t1 == "l":
                    sa[k] = as_bezier(sa[k - 1], sa[k])
                else:
                    sb[k] = as_bezier(sb[k - 1], sb[k])
            out_a += "".join(sa)
            out_b += "".join(sb)
        return S(out_a), S(out_b)

    def bars(self, tags: Any = None, vertical: bool = False, rng=_random) -> str:
        """Redibuja la forma como barras (cada una con sus tags) horizontales o verticales; devuelve codigo ASS."""
        S = _S()
        shp = self.redraw(4, "bezier")
        x0, y0, x1, y1 = shp.bounding()
        angle = ke_math.rand(360, rng=rng)
        if tags is None:
            tags = lambda i, n: "\\1c%s" % ke_color.hsv_to_rgb(angle + 90 * i / n)
        exteriors, holes = [], []
        for s in shp.subshapes():
            (holes if s.is_clockwise() else exteriors).append(s.points())

        def inside(p: Point, poly: List[Point]) -> bool:
            result, j = False, len(poly) - 1
            for i in range(len(poly)):
                pi, pj = poly[i], poly[j]
                if (pi.y > p.y) != (pj.y > p.y) and p.x < (pj.x - pi.x) * (p.y - pi.y) / ((pj.y - pi.y) + EPSILON) + pi.x:
                    result = not result
                j = i
            return result

        pixels = []
        for y in range(math.floor(y0), math.ceil(y1) + 1):
            for x in range(math.floor(x0), math.ceil(x1) + 1):
                p = Point(x + 0.5, y + 0.5)
                ec = sum(1 for e in exteriors if inside(p, e))
                if not ec:
                    continue
                hc = sum(1 for h in holes if inside(p, h))
                if (hc > 0 and (ec + hc) % 2 == 1) or hc == 0:
                    pixels.append((x, y))
        key = (lambda q: (q[0], q[1])) if vertical else (lambda q: (q[1], q[0]))
        pixels.sort(key=key)
        bars, current, ini, fin = [], None, None, None
        for x, y in pixels:
            fixed, axis = (x, y) if vertical else (y, x)
            if fixed != current or (fin is not None and axis != fin + 1):
                if ini is not None:
                    bars.append({"x": current if vertical else ini, "y": ini if vertical else current, "l": fin - ini + 1})
                current, ini = fixed, axis
            fin = axis
        if ini is not None and fin is not None:
            bars.append({"x": current if vertical else ini, "y": ini if vertical else current, "l": fin - ini + 1})
        groups: Dict[Any, List[Dict]] = {}
        for b in bars:
            groups.setdefault(b["x"] if vertical else b["y"], []).append(b)
        grouped = [groups[k] for k in sorted(groups)]
        n, out = len(grouped), []
        prev = {"x": x0 - 1, "y": y0 - 1}
        quad = lambda *v: " ".join(_f(c) for c in v) + " "
        for i, bar in enumerate(grouped, 1):
            code = "bars m %s %s l " % (_f(x0), _f(y0))
            nx = ny = None
            for b in bar:
                if vertical:
                    ny = b["y"] if ny is None else ny
                    nx = b["x"] - prev["x"] - 1
                    code += quad(nx, b["y"], nx + 1, b["y"], nx + 1, b["y"] + b["l"], nx, b["y"] + b["l"])
                else:
                    nx = b["x"] if nx is None else nx
                    ny = b["y"] - prev["y"] - 1
                    code += quad(b["x"], ny, b["x"], ny + 1, b["x"] + b["l"], ny + 1, b["x"] + b["l"], ny)
            code += quad(nx, y1, nx, ny) if vertical else quad(x1, ny, nx, ny)
            code = "{%s\\p1}" % (tags(i, n) if callable(tags) else tags) + code
            out.append(code + ("" if vertical else "{\\p0}\\N"))
            prev = bar[0]
        return "".join(out)


# ---------------------------------------------------------------------------- generadores ---


def ipol(shapes: Sequence[Any], t: float = 0.5, accel=1, shape=None, size: Optional[int] = None):
    """Interpola entre dos o mas formas (codigo ASS); con `size` devuelve esa cantidad de pasos."""
    S = _S()
    if size:
        return [ipol(shapes, i / (size - 1), accel, shape) for i in range(size)]
    t = ke_math.normalize(t if t is not None else 0.5, accel, shape)
    if t == 0:
        return S(shapes[0]).code
    n = len(shapes)
    seg = math.ceil(t * (n - 1))
    s1, s2 = S(shapes[seg - 1]).insert(shapes[seg])
    u = t * (n - 1) - (seg - 1)
    return S([a.ipol(u, b) for a, b in zip(s1.points(), s2.points())]).code


def array(shapes: Any, dx: float = 0, dy: float = 0, loop: Any = 1, mode: str = "array", alternated: bool = False,
          guide: Any = None, radius: float = 0, rng=_random):
    """Crea matrices de una o varias formas: mode = "array" (rejilla), "radial", "shape" (sobre una guia) o "random"."""
    S = _S()
    if isinstance(shapes, (list, tuple)) and shapes and not isinstance(shapes[0], (int, float)):
        shps = [S(s) for s in shapes]
    else:
        shps = [S(shapes)]
    n = len(shps)
    if mode == "random":
        rc = lambda a, b: ke_math.rand(a, b, 0.01, rng=rng)
        rs = lambda a, b=None: ke_math.rand(a, b, 0.01, True, rng=rng) if b is not None else ke_math.rand(a, None, 0.01, True, rng=rng)
        r1a, r1b, r1c, r2a, r2b, r2c, r6a = rc(10, 30), rc(10, 30), rc(10, 30), rs(30), rs(30), rs(30), rc(0, 20)
        r3a, r3b, r4a, r4b, r5a, r5b, r5c = rc(25, 45), rc(25, 45), rc(20, 40), rc(20, 40), rs(40), rs(40), rs(40)
        F = lambda *v: tuple(_f(x) for x in v)
        templates = [
            "m 0 0 l %s %s l %s %s l %s %s l %s %s l 50 0 " % F(r1a, r2a, r3a, r5a, r6a, r2b, r4a, r5b),
            "m 0 0 l %s %s l %s %s b %s %s %s %s %s %s l 50 0 " % F(r1a, r2a, r3a, r5a, r6a, r2b, r3b, r5b, r4a, r5c),
            "m 0 0 l %s %s b %s %s %s %s %s %s l %s %s l 50 0 " % F(r1a, r2a, r3a, r5a, r6a, r2b, r3b, r5b, r4a, r5c),
            "m 0 0 b %s %s %s %s %s %s l %s %s b %s %s %s %s 50 0 " % F(r1a, r2a, r3a, r5a, r6a, r2b, r4a, r5b, r1b, r2c, r4b, r5c),
            "m 0 0 b %s %s %s %s %s %s b %s %s %s %s %s %s l 50 0 " % F(r1a, r2a, r3a, r5a, r6a, r2b, r4a, r5b, r1b, r2c, r4b, r5c),
        ]
        shp1 = S(ke_math.rand(templates, rng=rng))
        shp2 = shp1.inverse().reflect("x").code.replace("m 50 0 ", "")
        shps = [S(shp1.code + shp2).ratio([ke_math.rand(36, 50, 0.01, rng=rng)])]
        mode, n = "radial", 1
    xmax = max(s.width for s in shps)
    ymax = max(s.height for s in shps)
    loopx = loop.get("x", 1) if isinstance(loop, dict) else loop
    loopy = loop.get("y", 1) if isinstance(loop, dict) else 1
    pick = lambda j, flag: shps[j].inverse() if flag else shps[j]
    result = ""
    if mode == "shape":
        confi = S(guide or "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 ").parameter(None, loopx)
        for i in range(loopx):
            j = i % n
            shp = pick(j, alternated and j % 2 == 1)
            pos, ang = confi[i][0], confi[i][1]
            result += shp.displace({"mode": "center"}).rotate(ang).displace({"x": pos.x, "y": pos.y}).code
    elif mode == "radial":
        for i in range(1, loopy + 1):
            for k in range(1, loopx + 1):
                j = (i + k - 2) % n
                shp = pick(j, alternated and (i + k) % 2 == 1)
                result += shp.displace({"mode": "center", "x": 0.5 * xmax + (i - 1) * (xmax + dx) + radius}).rotate((k - 1) * 360 / loopx).code
    else:
        for i in range(1, loopy + 1):
            for k in range(1, loopx + 1):
                j = (i + k - 2) % n
                shp = pick(j, alternated and (i + k) % 2 == 1)
                result += shp.displace({"mode": "center", "x": 0.5 * xmax + (k - 1) * (xmax + dx),
                                        "y": 0.5 * ymax + (i - 1) * (ymax + dy)}).code
    return S(result).displace({"mode": "origin"})


def multi1(size: float = 100, px: Any = 4):
    """Cuadrados concentricos. px: numero o lista (los numeros son franjas, los [n] separaciones)."""
    S = _S()
    px = [px] if isinstance(px, (int, float)) else list(px)
    px1 = px[0] if not isinstance(px[0], list) else px[0][0]
    shpw = px1
    shp = "m 0 0 l 0 %s l %s %s l %s 0 l 0 0 " % (_f(px1), _f(px1), _f(px1), _f(px1))
    i = 1
    while 2 * shpw < size and i < 10000:
        pxi = px[i % len(px)]
        shpw += pxi[0] if isinstance(pxi, list) else pxi
        if not isinstance(pxi, list):
            a = -shpw + px1
            d = a + pxi
            e = shpw - pxi
            pts = [(a, a), (a, shpw), (shpw, shpw), (shpw, a), (a, a), (d, d), (e, d), (e, e), (d, e), (d, d)]
            shp += "m %s %s " % (_f(pts[0][0]), _f(pts[0][1])) + "".join("l %s %s " % (_f(x), _f(y)) for x, y in pts[1:])
        i += 1
    return S(shp).displace({"mode": "origin"})


def multi2(width: float = 70, height: float = 50, pixel: Any = 6):
    """Diagonales dentro de un rectangulo."""
    S = _S()
    pixel = [pixel] if isinstance(pixel, (int, float)) else list(pixel)
    dim_x, dim_y = (height, width) if height > width else (width, height)
    i, dy = 1, pixel[0]
    shp = "m 0 0 l 0 %s l %s 0 l 0 0 l 0 0 " % (_f(pixel[0]), _f(pixel[0]))
    guard = 0
    while dy < dim_y and guard < 10000:
        guard += 1
        pxi = pixel[i % len(pixel)]
        dy += pxi[0] if isinstance(pxi, list) else pxi
        if not isinstance(pxi, list):
            shp += "m 0 %s l 0 %s l %s 0 l %s 0 l 0 %s " % (_f(dy - pxi), _f(dy), _f(dy), _f(dy - pxi), _f(dy - pxi))
        i += 1
    dx, shp_y = dy, dy
    while dx < dim_x and guard < 20000:
        guard += 1
        pxi = pixel[i % len(pixel)]
        dx += pxi[0] if isinstance(pxi, list) else pxi
        if not isinstance(pxi, list):
            shp += "m %s %s l %s %s l %s 0 l %s 0 l %s %s " % tuple(_f(v) for v in (
                dx - shp_y - pxi, shp_y, dx - shp_y, shp_y, dx, dx - pxi, dx - shp_y - pxi, shp_y))
        i += 1
    shp_x = 0
    while shp_x < shp_y and guard < 30000:
        guard += 1
        pxi = pixel[i % len(pixel)]
        shp_x += pxi[0] if isinstance(pxi, list) else pxi
        if not isinstance(pxi, list) and shp_x <= shp_y:
            shp += "m %s %s l %s %s l %s %s l %s %s l %s %s " % tuple(_f(v) for v in (
                dx - shp_y + shp_x - pxi, shp_y, dx - shp_y + shp_x, shp_y, dx, shp_x, dx, shp_x - pxi,
                dx - shp_y + shp_x - pxi, shp_y))
        i += 1
    out = S(shp)
    return out.rotate(-90).reflect() if height > width else out


def multi3(shape: Any = None, size: float = 100, bord: Any = 4):
    """Formas concentricas (circulos si no se da forma)."""
    S = _S()
    base = S(shape) if shape is not None else S("m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 ")
    bord = [bord] if isinstance(bord, (int, float)) else list(bord)
    smax = bord[0]
    shp = base.size(bord[0]).displace({"mode": "center"})
    i = 1
    while smax <= size and i < 10000:
        bi = bord[i % len(bord)]
        smax += 2 * (bi[0] if isinstance(bi, list) else bi)
        if not isinstance(bi, list):
            s1 = base.size(smax).displace({"mode": "center"})
            s2 = base.size(smax - 2 * bi).inverse().displace({"mode": "center"})
            shp = shp.concat(s1.code + s2.code.replace("m", "l", 1))
        i += 1
    return shp.displace({"mode": "origin"})


def multi4(size: float = 64, loop1: int = 6, loop2: int = 1, n: int = 25):
    """Poligono regular de `loop1` lados formado por franjas concentricas."""
    S = _S()
    loop1 = 3 if loop1 < 3 else loop1
    loop2 = 1 if loop2 <= 0 else loop2
    sizer = 2 * math.ceil(size / 2)
    px = ke_math.round_(0.5 * sizer / loop2)

    def ring(size40: float, loop40: int, px40: float) -> str:
        size40 = 2 * math.ceil(size40 / 2)
        px40 = size40 / 2 if px40 >= size40 / 2 else px40
        angle = 360 / loop40
        out = []
        for i in range(1, ke_math.round_(360 / angle) + 1):
            pts = [ke_math.polar(angle * i, size40 / 2 - px40), ke_math.polar(angle * i, size40 / 2),
                   ke_math.polar(angle * (i - 1), size40 / 2), ke_math.polar(angle * (i - 1), size40 / 2 - px40)]
            out.append("m %s %s l %s %s l %s %s l %s %s " % tuple(_f(c) for p in pts for c in p))
        return "".join(out)

    pn, shp, i = sizer / 2, "", 0
    while pn > 0 and i < n:
        shp += ring(pn * 2, loop1, px)
        pn -= px
        i += 1
    out = S(shp).displace({"mode": "origin"})
    if loop1 % 2 == 1:
        out = out.rotate(((-1) ** ((loop1 - 1) // 2)) * 90 / loop1).displace({"mode": "origin"})
    return out


def multi5(shapes: Any = None, width: float = 60, height: float = 50, dxy: Any = (0, 0)):
    """Matriz rectangular de formas desplazadas ciclicamente."""
    S = _S()
    shps = [S(s) for s in shapes] if isinstance(shapes, (list, tuple)) else [S(shapes or "m 0 0 l 0 8 8 8 8 0 ")]
    dxy = (dxy, 0) if isinstance(dxy, (int, float)) else dxy
    wmax, hmax = max(s.width for s in shps), max(s.height for s in shps)
    n = len(shps)
    rows = []
    for i in range(1, n + 1):
        row = ""
        for k in range(1, n + 1):
            row += shps[(k - i) % n].displace({"mode": "center"}).displace({"x": (k - 1) * wmax, "y": (i - n) * hmax}).code
        rows.append(row)
    shp = S("".join(rows)).displace({"mode": "origin"})
    lh, lv = math.ceil(width / (shp.width + dxy[0])), math.ceil(height / (shp.height + dxy[1]))
    return array(shp, dx=dxy[0], dy=dxy[1], loop={"x": lh, "y": lv})


def multi6(size: Any = 104, bord: Any = 4, length: float = 20):
    """Perimetro de un rectangulo formado por rectangulos individuales."""
    S = _S()
    xsize, ysize = (size[0], size[1]) if isinstance(size, (list, tuple)) else (size, size)
    spacex = bord[1] if isinstance(bord, (list, tuple)) else 0
    bord = bord[0] if isinstance(bord, (list, tuple)) else bord
    xloop, yloop = math.ceil((xsize - bord) / (length + spacex)), math.ceil((ysize - bord) / (length + spacex))
    xsize, ysize = xloop * (length + spacex) + bord - spacex, yloop * (length + spacex) + bord - spacex
    rect = S("m 0 100 l 100 100 l 100 0 l 0 0 ").size(length, bord)
    shp_h = array(rect, dx=spacex, loop={"x": xloop})
    shp_v = shp_h if yloop == xloop else array(rect, dx=spacex, loop={"x": yloop})
    parts = [
        shp_h.code,
        shp_v.rotate(-90).displace({"point": 4, "x": xsize + spacex, "y": 0, "mode": "point"}).code,
        shp_h.rotate(180).displace({"point": 4, "x": xsize + spacex, "y": ysize + spacex, "mode": "point"}).code,
        shp_v.rotate(90).displace({"point": 4, "x": 0, "y": ysize + spacex, "mode": "point"}).code,
    ]
    return S("".join(parts))


def multi7(part: int = 12, radius: Any = 50):
    """Perimetro circular formado por segmentos individuales."""
    S = _S()
    part = max(2, ke_math.round_(abs(part)))
    angle = 360 / part
    ang_b = angle * 0.295927
    ratio = 1 / math.cos(math.radians(ang_b))
    P = ke_math.polar
    shp = ""
    if isinstance(radius, (int, float)):
        for i in range(1, part + 1):
            pts = [P(angle * (i - 1), radius), P(angle * (i - 1) + ang_b, radius * ratio),
                   P(angle * i - ang_b, radius * ratio), P(angle * i, radius)]
            shp += "m 0 0 l %s %s b %s %s %s %s %s %s l 0 0 " % tuple(_f(c) for p in pts for c in p)
    else:
        for i in range(len(radius) - 1):
            for k in range(1, part + 1):
                r, R = radius[i], radius[i + 1]
                pts = [P(angle * (k - 1), R), P(angle * (k - 1) + ang_b, R * ratio), P(angle * k - ang_b, R * ratio),
                       P(angle * k, R), P(angle * k, r), P(angle * k - ang_b, r * ratio),
                       P(angle * (k - 1) + ang_b, r * ratio), P(angle * (k - 1), r), P(angle * (k - 1), R)]
                shp += "m %s %s b %s %s %s %s %s %s l %s %s b %s %s %s %s %s %s l %s %s " % tuple(_f(c) for p in pts for c in p)
    return S(shp).displace({"mode": "origin"})


def multi8(shape: Any = None, size1: Optional[float] = None, size2: Optional[float] = None, loop: int = 8):
    """Formas concentricas desde un tamano inicial a uno final."""
    S = _S()
    shp = S(shape or "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0 ").displace({"mode": "origin"})
    size1 = shp.width if size1 is None else size1
    size2 = shp.width / 2 if size2 is None else size2
    loop = max(2, abs(math.ceil(loop)))
    mx, mn = max(abs(math.ceil(size1)), abs(math.ceil(size2))), min(abs(math.ceil(size1)), abs(math.ceil(size2)))
    shp1 = shp.size(mx, 0)
    c = shp1.centroid
    return S("".join(shp1.size(mx - (mx - mn) * (i - 1) / (loop - 1), 0).displace({"x": c.x, "y": c.y, "mode": "center"}).code
                     for i in range(1, loop + 1)))


def fusion(shapes: Any, tags: Any = None, rng=_random) -> str:
    """Une varias formas en una sola linea de efecto (cada una con su bloque de tags)."""
    S = _S()
    items = [S(s) for s in shapes] if isinstance(shapes, (list, tuple)) else [S(shapes)]
    joined = S("".join(s.code for s in items))
    w, h = joined.width, joined.height
    pieces = [S(p) for p in joined.displace({"mode": "origin"}).divide()]
    n = len(pieces)
    if tags is None:
        tags = ["\\1c%s" % ke_color.random(None, 0.82, rng=rng) for _ in range(n)]
    for i in range(n, 0, -1):
        pieces[i - 1] = pieces[i - 1].displace({"x": 0.5 * w + (n - i) * w, "y": 0.5 * h, "mode": "center"})
        pieces[i - 1] = pieces[i - 1].displace({"x": -0.5 * n * w + 0.5 * w})
    return "".join("{%s}%s" % (tags[i % len(tags)], pieces[i].code) for i in range(n))


def trajectory(mode: str = "bezier", loop: Any = None, caliber1: Any = None, caliber2: Any = None, rng=_random):
    """Trayectorias aleatorias: "bezier" (fluida), "path" (en linea recta) o "line" (tramos rectos)."""
    S = _S()
    kw = {"rng": rng}
    if mode == "line":
        loop = 8 if loop is None else loop
        radius = 60 if caliber1 is None else caliber1
        loops = math.ceil(loop)
        angles = [ke_math.rand(36, **kw) * 10]
        for i in range(loops):
            angles.append(ke_math.rand(angles[i] + 110, angles[i] + 250, **kw))
        shp = "m 0 0 "
        for i in range(1, loops + 1):
            shp += "l %s %s " % tuple(_f(c) for c in ke_math.polar(angles[i], ke_math.rand(0.7 * radius, radius, **kw)))
        return S(shp)
    if mode == "path":
        length_t = 640 if caliber1 is None else caliber1
        ratio = 30 if caliber2 is None else caliber2
        length_c = length_t / (4 if loop is None else loop)
        n = ke_math.round_(length_t / length_c)
        sign = (-1) ** ke_math.rand(2, **kw)
        xray = Segment([-length_c, 0, n * length_c + length_c, 0])
        cix, ciy = ke_math.counter(2), ke_math.counter()
        pts: List[Point] = []
        for i in range(1, 2 * n + 1):
            x = length_c * (cix("N,n", 2) - 1) + ke_math.rand(0.35 * length_c, 0.65 * length_c, **kw) * sign ** i
            y = ratio * sign * (-1) ** ciy("N,n", 2) + ke_math.rand(1, 0.125 * ratio, 1, True, **kw)
            pts.append(Point(x, y))
        pts.append(Point(n * length_c + ke_math.rand(1, 0.125 * length_c, 1, True, **kw), 0))
        shp = "m 0 0 b "
        for i, p in enumerate(pts, 1):
            shp += str(p)
            if i < len(pts) - 2 and i % 2 == 0:
                hit = xray.intersect(Segment(t="l", pts=[pts[i - 1], pts[i]]))
                if hit:
                    shp += str(hit[0])
        return S(shp)
    loop = 8 if loop is None else loop
    dmin, dmax = (50 if caliber1 is None else caliber1), (120 if caliber2 is None else caliber2)
    pts = Point(0, 0).rand({"n": 2 * loop + 1, "dx": dmin, "dy": dmax, "sign": True}, rng=rng)
    shp = "m 0 0 b "
    for i, p in enumerate(pts, 1):
        shp += str(p)
        if i < len(pts) - 2 and i % 2 == 0:
            shp += str(Segment(t="l", pts=[pts[i - 1], pts[i]]).bezier(ke_math.rand(0.3, 0.7, 0.01, **kw))[0])
    return S(shp)


# --- graficos predefinidos (ke.shape.graph) ---


def polygon(n: Optional[int] = 6, radius: Any = 50, angle: Any = None, bord: Optional[float] = None):
    """Poligonos regulares (n=None -> circulo). radius/angle pueden ser listas (varios poligonos)."""
    S = _S()
    n = 6 if n is None else n
    n = abs(math.ceil(3 if n < 3 else n)) if n != math.inf else n
    radii = [radius] if isinstance(radius, (int, float)) else list(radius)
    angles = None if angle is None else ([angle] if isinstance(angle, (int, float)) else list(angle))

    def one(rad: float, ang: Optional[float]) -> str:
        if n == math.inf:
            poly = S("m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 ")
            poly = poly.size(2 * rad).rotate(-90, "center").displace({"mode": "center"})
        else:
            anglex, thetax = 360 / n, 90 * (n - 2) / n
            code = "".join("l %s %s " % tuple(_f(c) for c in ke_math.polar(anglex * i, rad)) for i in range(n + 1))
            code = code.replace("l", "m", 1)
            if n % 2 == 1:
                anglix = 90 - anglex * math.floor(90 / anglex)
                fakex = rad * math.sin(math.radians(thetax)) / math.sin(math.radians(180 - thetax - anglix))
                code = "m %s 0 " % _f(fakex)
                code += "".join("l %s %s " % tuple(_f(c) for c in ke_math.polar(anglix + anglex * i, rad)) for i in range(n))
                code += "l %s 0 " % _f(fakex)
            poly = S(code)
        if ang:
            poly = poly.cut(ang / 360)[0]
        if bord and isinstance(bord, (int, float)):
            poly = poly.line(bord)
        return poly.code

    return "".join(one(r, angles[i % len(angles)] if angles else None) for i, r in enumerate(radii))


_HEADS_START = {
    "[": "m 0 0 l 0 100 ", "]": "m 0 0 l 0 100 ", "<": "m 28.86 0 l 0 50 l 28.86 100 ", ">": "m 0 0 l 28.86 50 l 0 100 ",
    "/": "m 28.86 0 l 0 100 ", "\\": "m 0 0 l 28.86 100 ", "{": "m 27 0 l 15 12 15 35 0 50 15 65 15 88 27 100 ",
    "}": "m 0 0 l 12 12 12 35 27 50 12 65 12 88 0 100 ", "=": "m 0 0 l 0 32 32 32 32 68 0 68 0 100 ",
    "#": "m 0 0 l 0 20 20 20 20 40 0 40 0 60 20 60 20 80 0 80 0 100 ",
    "(": "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 ",
    ")": "m 0 0 b 17.591 9.974 28.88 28.447 28.88 50 b 28.88 71.553 17.591 90.026 0 100 ",
}
_HEADS_END = {
    "]": "m 0 100 l 0 0 ", "[": "m 0 100 l 0 0 ", "<": "m 0 100 l -28.86 50 l 0 0 ", ">": "m -28.86 100 l 0 50 l -28.86 0 ",
    "/": "m -28.86 100 l 0 0 ", "\\": "m 0 100 l -28.86 0 ", "}": "m 0 100 l 12 88 12 65 27 50 12 35 12 12 0 0 ",
    "{": "m 0 100 l -12 88 -12 65 -27 50 -12 35 -12 12 0 0 ", "=": "m 0 100 l 0 68 -32 68 -32 32 0 32 0 0 ",
    "#": "m 0 100 l 0 80 -20 80 -20 60 0 60 0 40 -20 40 -20 20 0 20 0 0 ",
    ")": "m -50 100 b -22 100 0 78 0 50 b 0 22 -22 0 -50 0 ",
    "(": "m 0 100 b -17.591 90.026 -28.88 71.553 -28.88 50 b -28.88 28.447 -17.591 9.974 0 0 ",
}


def banner(width: float = 200, height: float = 50, mode: Any = "[]", bord: Optional[float] = None):
    """Banners con extremos ("[", "]", "<", ">", "/", "\\", "{", "}", "=", "#", "(", ")") y borde opcional."""
    S = _S()
    mi = mode[0] if isinstance(mode, (str, list, tuple)) and len(mode) > 0 else "["
    mf = mode[1] if isinstance(mode, (str, list, tuple)) and len(mode) > 1 else "]"
    ini = S(_HEADS_START.get(mi, mi if len(mi) > 1 else "m 0 0 l 0 100 "))
    fin = S(_HEADS_END.get(mf, mf if len(mf) > 1 else "m 0 100 l 0 0 "))
    ini = ini.ratio(None, [height])
    fin = fin.ratio(None, [height]).displace({"x": width})
    shp = S(ini.code + fin.code.replace("m", "l")).to_line().closed()
    out = shp.line(bord).displace({"mode": "origin"}) if bord and isinstance(bord, (int, float)) else shp.displace({"mode": "origin"})
    return out


def gear(radius: float = 180, n: int = 8, dent: Optional[str] = None, double: bool = False, bord: Optional[float] = None):
    """Engranajes (dent: forma del diente, por defecto una recta)."""
    S = _S()

    def graph_gear(rad: float, count: int, tooth: Optional[str]):
        ratio, angle = 0.38, 360 / count
        arc1, arc2 = ratio * angle, 0.5 * (1 + ratio) * angle
        length = 2 * math.pi * rad * angle / 360
        t = S(tooth or "m 0 0 l 100 0 ").rotate([None, 0]).displace({"mode": "center"})
        height = t.height
        part1 = S("m 50 0 b 50 -28 28 -50 0 -50 ").size(rad).cut(arc1 / 90)[0]
        part2 = t.ratio([0.45 * length]).rotate(90 + arc2).displace(
            {"x": arc2, "y": rad + 0.45 * length - height / 5, "mode": "polar"})
        tooth_shape = S(part1.code + part2.code.replace("m", "l"))
        body = "".join(tooth_shape.rotate(angle * i).code for i in range(count))
        code = S(body).rotate(-arc2).code.replace("m", "l").replace("l", "m", 1)
        return S(code).closed()

    cir1 = S("m 0 -50 b -28 -50 -50 -28 -50 0 b -50 28 -28 50 0 50 b 28 50 50 28 50 0 b 50 -28 28 -50 0 -50 ")
    cir2 = cir1.inverse()
    add1 = cir2.size(1.8 * radius).concat(cir1.size(1.5 * radius))
    add2 = cir2.size(0.5 * radius)
    shp = graph_gear(radius, n, dent)
    if double:
        shp = shp.concat(graph_gear(0.7 * radius, n, dent).inverse())
        add1 = cir1.size(1.1 * radius).concat(cir2.size(0.9 * radius))
        add2 = cir1.size(0.5 * radius)
    result = shp.concat(add1).concat(add2)
    if bord and isinstance(bord, (int, float)):
        result = result.line(bord)
    return result.displace({"mode": "origin"})

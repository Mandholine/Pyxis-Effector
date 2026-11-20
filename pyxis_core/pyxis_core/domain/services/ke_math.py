# -*- coding: utf-8 -*-
# Port de `ke.math` (newkara_library.lua de Effector).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Matematica de efectos: aleatorios, angulos, interpolacion, ecuaciones y matrices.

Funciones puras (sin I/O). Los puntos son tuplas/listas `(x, y)` o `(x, y, z)`,
cadenas con coordenadas ("2 7 11 3") u objetos con atributos x/y.

`normalize(..., shape=...)` usa `ke_shape.Shape` (importado de forma perezosa).
"""

from __future__ import annotations

import cmath
import math
import random as _random
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

from .ke_common import (EPSILON, ROUND_MATRIX, ROUND_NUM, get_numbers, recurse,
                        round_half_up, to_number)

# ----------------------------------------------------------------- basicas ---


def round_(value, decimals=0):
    """ke.math.round: redondea (half-up); admite listas/dicts anidados."""
    if isinstance(value, (list, tuple, dict)):
        return recurse(round_, value, decimals)
    value = to_number(value, 0)
    if isinstance(value, (int, float)):
        return round_half_up(value, int(abs(to_number(decimals, 0))))
    return value


def clamp(num, low=0, high=1, cycle=False):
    """ke.math.clamp: restringe `num` a [low, high]; con cycle=True rebota (ping-pong)."""
    if isinstance(num, (list, tuple, dict)):
        return recurse(clamp, num, low, high, cycle)
    num = to_number(num, 0.5)
    low, high = to_number(low, 0), to_number(high, 1)
    c_min, c_max = min(low, high), max(low, high)
    if cycle:
        n = round_(num * 10000)
        lo, hi = round_(c_min * 10000), round_(c_max * 10000)
        return round_(sequence(n - lo, lo, hi, mode="ABA") / 10000, 3)
    return c_min if num < c_min else (c_max if num > c_max else num)


def equality(n1, n2, tolerance=5) -> bool:
    """Dos numeros son iguales si |n1 - n2| < 0.1^tolerance."""
    return abs(n1 - n2) < 0.1 ** tolerance


def between(num, n1, n2) -> bool:
    return min(n1, n2) <= num <= max(n1, n2)


def get_pair(val, defx=None, defy=None) -> Tuple[float, float]:
    nums = get_numbers(val)
    vx = nums[0] if len(nums) > 0 else (defx if defx is not None else 0)
    vy = nums[1] if len(nums) > 1 else (defy if defy is not None else (nums[0] if nums else 0))
    return vx, vy


def to_hex(num):
    """ke.math.to16: decimal -> hexadecimal (mayusculas)."""
    if isinstance(num, (list, tuple, dict)):
        return recurse(to_hex, num)
    return "%X" % round_(to_number(num, 0))


def factorial(n) -> int:
    n = abs(math.ceil(to_number(n, 0)))
    return math.factorial(int(n))


# --------------------------------------------------------------- aleatorios ---


def rand(num1=None, num2=None, step=1, sign=False, range_=None, rng=_random):
    """ke.math.rand: aleatorio.

    rand() -> [0,1) con 5 decimales; rand(n) -> entero 1..n; rand(a, b[, step]) -> a..b;
    rand([lista]) -> elemento al azar. `sign=True` multiplica por +-1.
    `range_=(rmin, rmax, porcentaje)` favorece ese sub-rango (ke.math.rand 5to parametro).
    """
    num1, num2, step = to_number(num1), to_number(num2), to_number(step, 1)
    if isinstance(num1, (list, tuple)):
        return num1[rand(len(num1), rng=rng) - 1]

    def fx(a=None, b=None):
        if a is None and b is None:
            return round_(rng.random(), 5)
        if b is None:
            if a == 0:
                return 0
            a, b = 1, a
        r1, r2 = round_(min(a, b)), round_(max(a, b))
        return rng.randint(r1, r2)

    if num1 is None:
        return fx()
    if num2 is None:
        return fx(num1)
    n1, n2 = min(num1, num2), max(num1, num2)
    step = 1 if step <= 0 else step
    if range_:
        rmin, rmax = range_[0], range_[1]
        percent = clamp(range_[2] if len(range_) > 2 else 100, 0, 100)
        lsize = rmin - n1 if rmin > n1 else 0
        rsize = n2 - rmax if rmax < n2 else 0
        if rand(0, 100, rng=rng) <= percent or lsize + rsize <= 0:
            return rand(rmin, rmax, step, sign, rng=rng)
        pick = rand(0, lsize + rsize, step, rng=rng)
        return (rand(n1, rmin - 1, step, sign, rng=rng) if pick <= lsize
                else rand(rmax + 1, n2, step, sign, rng=rng))
    result = n1 + fx(0, (n2 - n1) / step) * step
    result = n2 if result > n2 else result
    return result * (-1) ** rand(2, rng=rng) if sign else result


def counter(init=None, step=1) -> Callable:
    """ke.math.count: contador independiente. `c()` devuelve el siguiente valor;
    `c("ABA", A, B, C)` devuelve ese algoritmo de `sequence` en el valor actual."""
    s = to_number(step, 1)
    state = {"i": (to_number(init) - s) if init is not None else 0}

    def _next(mode=None, A=None, B=None, C=None):
        state["i"] += s
        return sequence(state["i"], A, B, C, mode=mode) if mode else state["i"]

    return _next


def sequence(i, A=1, B=1, C=1, mode: Optional[str] = None):
    """ke.math.i: secuencias numericas predefinidas para el contador `i`.

    Con `mode` ("ABA", "A,B", "+,-", ...) devuelve solo ese valor; sin `mode`, un dict con todos
    (los que no se puedan calcular, p. ej. por division entre 0, valen NaN como en Lua)."""
    i = to_number(i)
    A, B, C = to_number(A, 1), to_number(B, 1), to_number(C, 1)
    D, E = A - B + 1, B - A + 1
    f = math.floor

    def xt(v):
        return math.ceil(i / v)

    def aba():
        if A > B:
            return B + D - ((D - 1 - (D - 1) * xt(D - 1) + i) * (-1) ** (xt(D - 1) + 1)
                            + (D + 1) * (1 + (-1) ** xt(D - 1)) / 2)
        return (A + (E - 1 - (E - 1) * xt(E - 1) + i) * (-1) ** (xt(E - 1) + 1)
                + (E + 1) * (1 + (-1) ** xt(E - 1)) / 2 - 1)

    algorithms = {
        "+,-": lambda: (-1) ** (xt(A) + 1),                                            # (+,-) A veces cada uno
        "A,B": lambda: A + ((B - A) / 2) * (1 + (-1) ** xt(C)),                        # (A,B) C veces cada uno
        "mxA": lambda: A * xt(B),                                                      # multiplos de A, B veces
        "A>B": lambda: ((xt(C) - 1) % E + A) if A <= B else -1 * ((xt(C) - 1) % D - A),  # (A-->B) C veces
        "ABA": aba,                                                                    # (A-->B-->A)
        "ABB": lambda: A * f(1 / i) + B * (1 - f(1 / i)),                              # primero A, el resto B
        "ABC": lambda: A * f((C * xt(C) - i + 1) / C) + B * (1 - f((C * xt(C) - i + 1) / C)),
        "ACB": lambda: A * (1 - f((C - C * xt(C) + i) / C)) + B * f((C - C * xt(C) + i) / C),
        "N,n": lambda: f((i - 1) / A) + 1,                                             # naturales, A veces cada uno
    }

    def run(fn):
        try:
            v = fn()
        except (ZeroDivisionError, ValueError, OverflowError):
            return float("nan")
        return 0 if v == 0 else v

    if mode is not None:
        return run(algorithms[mode])
    return {k: run(fn) for k, fn in algorithms.items()}


# ----------------------------------------------------------------- geometria ---


class Point3(NamedTuple):
    x: float
    y: float
    z: float = 0


def angle(p1, p2=None, p3=None) -> float:
    """ke.math.angle: angulo (0-360) entre uno (y el origen), dos o tres puntos (coords ASSDraw)."""
    nums = get_numbers(p1, p2, p3)
    x1, y1 = nums[0], nums[1]
    x2 = nums[2] if len(nums) > 2 else None
    y2 = nums[3] if len(nums) > 3 else None
    x3 = nums[4] if len(nums) > 4 else None
    y3 = nums[5] if len(nums) > 5 else None
    if x2 is None:
        x2, y2, x1, y1 = x1, y1, 0, 0
    a1 = math.degrees(math.atan2(y1 - y2, x2 - x1))
    a2 = math.degrees(math.atan2(y2 - y3, x3 - x2)) if (x3 is not None and y3 is not None) else None
    a1 = a1 + 360 if a1 < 0 else a1
    a2 = (a2 + 360 if a2 < 0 else a2) if a2 is not None else None
    ang = 180 - a1 + a2 if a2 is not None else a1
    ang = ang + 360 if ang < 0 else (ang - 360 if ang > 360 else ang)
    return round_(ang, ROUND_NUM)


def polar(ang, radius, get: Optional[str] = None):
    """ke.math.polar: punto (x, y) a `ang` grados y `radius` del origen. get="x"|"y" devuelve una coordenada."""
    ang, radius = to_number(ang), to_number(radius)
    px = round_(radius * math.cos(math.radians(ang)), ROUND_NUM)
    py = round_(-radius * math.sin(math.radians(ang)), ROUND_NUM)
    if get == "x":
        return px
    if get == "y":
        return py
    return px, py


def distance(p1, p2=None) -> float:
    """ke.math.distance: entre dos puntos, o un punto y el origen. Con una lista de >2 puntos, longitud del trazado."""
    if isinstance(p1, (list, tuple)) and p2 is None and len(p1) > 2 and isinstance(p1[0], (list, tuple, dict)):
        return sum(distance(p1[k], p1[k + 1]) for k in range(len(p1) - 1))
    nums = get_numbers(p1, p2)
    if not nums:
        return 0
    x1, y1 = nums[0], nums[1] if len(nums) > 1 else 0
    x2 = nums[2] if len(nums) > 2 else 0
    y2 = nums[3] if len(nums) > 3 else 0
    return round_(((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5, ROUND_NUM)


def intersect(s1, s2):
    """ke.math.intersect: punto (x, y, t) donde se cortan las rectas de dos segmentos; None si son paralelas."""
    x1, y1, x2, y2, x3, y3, x4, y4 = get_numbers(s1, s2)[:8]
    if (x1 == x3 and y1 == y3) or (x1 == x4 and y1 == y4):
        return x1, y1, 0
    if (x2 == x3 and y2 == y3) or (x2 == x4 and y2 == y4):
        return x2, y2, 1
    den = (x2 - x1) * (y3 - y4) - (x3 - x4) * (y2 - y1)
    if den == 0:
        return None  # "parallels" en el original
    t = ((x3 - x1) * (y3 - y4) - (x3 - x4) * (y3 - y1)) / den
    return round_(x1 + t * (x2 - x1), ROUND_NUM), round_(y1 + t * (y2 - y1), ROUND_NUM), t


def circle(p1, p2, p3):
    """ke.math.circle: ((cx, cy), radio) del circulo por tres puntos; None si son colineales."""
    (ax, ay), (bx, by), (cx, cy) = [get_numbers(p)[:2] for p in (p1, p2, p3)]
    det = ax * (by - cy) + bx * (cy - ay) + cx * (ay - by)
    if abs(det) < EPSILON:
        return None
    d1, d2, d3 = ax * ax + ay * ay, bx * bx + by * by, cx * cx + cy * cy
    ux = (d1 * (by - cy) + d2 * (cy - ay) + d3 * (ay - by)) / (2 * det)
    uy = (d1 * (cx - bx) + d2 * (ax - cx) + d3 * (bx - ax)) / (2 * det)
    return (ux, uy), math.hypot(ux - ax, uy - ay)


def rotate(p, ang, axis="z"):
    """ke.math.rotate: rota un punto (x, y[, z]) sobre el eje x|y|z.

    Si `p` es una cadena de coordenadas ("m 0 0 l 10 5") rota cada par x y (eje z)."""
    import re
    if isinstance(p, str) and re.search(r"-?\d[.\d]*\s+-?\d[.\d]*", p):
        def sub(m):
            r = rotate((float(m.group(1)), float(m.group(2))), ang, axis)
            return "%s %s" % (_fmt(r.x), _fmt(r.y))
        return re.sub(r"(-?\d[.\d]*)\s+(-?\d[.\d]*)", sub, p)
    a = math.radians(to_number(ang, 0))
    nums = get_numbers(p)
    x, y, z = (nums + [0, 0, 0])[:3]
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return Point3(x, c * y - s * z, s * y + c * z)
    if axis == "y":
        return Point3(c * x + s * z, y, c * z - s * x)
    return Point3(c * x - s * y, s * x + c * y, z)


def _fmt(v: float) -> str:
    v = round(v, 3)
    return str(int(v)) if v == int(v) else str(v)


# ----------------------------------------------- normalizacion / interpolacion ---


def normalize(t, accel=1, shape=None):
    """ke.math.normalize: lleva `t` al rango [0, 1], aplicando `accel` (potencia o funcion)."""
    if isinstance(t, dict):
        shape = t.get("shape", shape)
        accel = t.get("accel", accel)
        t = t["t"]
    if isinstance(t, (list, tuple)):
        out, last = [], 0
        for ti in t:
            out.append((ti - last) / (1 - last))
            last = ti
        return [normalize(v, accel) for v in out]
    t = abs(to_number(t))
    if not 0 <= t <= 1:
        digits = len(str(t).split(".")[0])
        t = t / (10 ** digits)
    t = clamp(accel(t) if callable(accel) else t ** (accel if accel is not None else 1))
    if shape:
        # interpolacion por el valor "y" de una forma: t = |y| / alto, con y = punto de la forma en t
        from .ke_shape import Shape
        shp = shape if isinstance(shape, Shape) else Shape(shape)
        height = shp.height
        point, _ = shp.parameter(t)
        t = 0 if height == 0 else abs(point.y) / height
    return t


def ipol(values, t=0.5, accel=1, shape=None, size=None):
    """ke.math.ipol: interpolacion entre dos o mas numeros (o listas de numeros)."""
    if size:
        return [ipol(values, i / (size - 1), accel, shape) for i in range(size)]
    if isinstance(values, (int, float)):
        values = [0, values]
    if values and isinstance(values[0], (list, tuple)):
        return [ipol(list(col), t, accel, shape) for col in zip(*values)]
    t = normalize(t, accel, shape)
    if t == 0:
        return values[0]
    n = len(values)
    seg = math.ceil(t * (n - 1))
    ini, fin = values[seg - 1], values[seg]
    u = t * (n - 1) - (seg - 1)
    return round_(ini + u * (fin - ini), ROUND_NUM)


# ---------------------------------------------------------------- ecuaciones ---


def quadratic(c1, c2, c3) -> List[float]:
    d = c2 * c2 - 4 * c1 * c3
    if d > EPSILON:
        return [(-c2 - math.sqrt(d)) / (2 * c1), (-c2 + math.sqrt(d)) / (2 * c1)]
    return [(-c2) / (2 * c1)] if abs(d) <= EPSILON else []


def _cbrt(x: float) -> float:
    return x ** (1 / 3) if x >= 0 else -((-x) ** (1 / 3))


def cubic(c1, c2, c3, c4) -> List[float]:
    """Raices reales de c1*x^3 + c2*x^2 + c3*x + c4 (ordenadas, sin repetir)."""
    a = 1 / c1
    b, c, d = c2 * a, c3 * a, c4 * a
    offset = b / 3
    p = c - b * b / 3
    q = (2 * b ** 3) / 27 - (b * c) / 3 + d
    D = (q * q) / 4 + (p ** 3) / 27
    roots: List[float] = []
    if D > EPSILON:
        sD = math.sqrt(D)
        roots.append(_cbrt(-q / 2 + sD) + _cbrt(-q / 2 - sD) - offset)
    elif abs(D) <= EPSILON:
        u = _cbrt(-q / 2)
        roots += [2 * u - offset, -u - offset]
    else:
        phi = math.acos(max(-1, min(1, (-q / 2) / math.sqrt(-(p ** 3) / 27))))
        r = 2 * math.sqrt(-p / 3)
        roots += [r * math.cos((2 * math.pi * k + phi) / 3) - offset for k in range(3)]
    return sorted(set(roots))


def resolve(coefficients: Sequence[float]):
    """Resuelve ecuaciones lineales, cuadraticas y cubicas (coeficientes de mayor a menor grado)."""
    co = list(coefficients)
    while co and abs(co[0]) < EPSILON:
        co.pop(0)
    if len(co) > 1:
        if len(co) >= 4:
            return cubic(*co[:4])
        if len(co) == 3:
            return quadratic(*co)
        return [-co[1] / co[0]]
    return False


def equation(coefficients: Sequence[float], reals: bool = False):
    """ke.math.equation: raices de grado n (coeficientes ascendentes), metodo de Durand-Kerner."""
    cx = [complex(c) for c in coefficients]
    while len(cx) > 1 and abs(cx[-1]) < EPSILON:
        cx.pop()
    n = len(cx) - 1
    if n < 1:
        return []
    radius = max([1 + abs(cx[i] / cx[-1]) for i in range(n)] + [1])
    roots = [cmath.rect(radius, 2 * math.pi * i / n + 0.001 * rand()) for i in range(n)]

    def horner(z):
        p, dp = cx[-1], 0j
        for i in range(n - 1, -1, -1):
            dp = dp * z + p
            p = p * z + cx[i]
        return p, dp

    for _ in range(50):
        done = True
        for i in range(n):
            z = roots[i]
            p, dp = horner(z)
            newton = p / dp if dp != 0 else 0j
            s = sum(1 / (z - roots[j]) for j in range(n) if j != i and z != roots[j])
            corr = newton / (1 - newton * s)
            roots[i] = z - corr
            done = abs(corr) <= 1e-14
        if done:
            break
    out = [r.real if abs(r.imag) < EPSILON else r for r in roots]
    if reals:
        out = [r for r in out if isinstance(r, float)]
    return sorted(out, key=lambda c: (c.real if isinstance(c, complex) else c))


def evaluate(coefficients: Sequence[float], t: float) -> float:
    """Evalua el polinomio de coeficientes ascendentes en `t` (Horner)."""
    result = coefficients[-1]
    for c in reversed(coefficients[:-1]):
        result = result * t + c
    return result


def gauss(matrix: Sequence[Sequence[float]]):
    """Resuelve un sistema (n x n+1) por eliminacion gaussiana; None si es singular."""
    n = len(matrix)
    A = [list(map(float, row)) for row in matrix]
    for k in range(n):
        pivot_row = max(range(k, n), key=lambda i: abs(A[i][k]))
        if abs(A[pivot_row][k]) < EPSILON:
            return None
        A[k], A[pivot_row] = A[pivot_row], A[k]
        pivot = A[k][k]
        A[k] = [v / pivot for v in A[k]]
        for i in range(k + 1, n):
            factor = A[i][k]
            A[i] = [A[i][j] - factor * A[k][j] for j in range(n + 1)]
    sol = [0.0] * n
    for i in range(n - 1, -1, -1):
        sol[i] = A[i][n] - sum(A[i][j] * sol[j] for j in range(i + 1, n))
    return [round_(v, ROUND_MATRIX) for v in sol]


# ------------------------------------------------------------------- matrices ---


class Matrix:
    """ke.math.matrix: matriz cuadrada n x n (valor inmutable por convencion)."""

    def __init__(self, data: Sequence[Any]):
        nums = get_numbers(data) if not _is_rows(data) else None
        if nums is not None:
            n = math.ceil(math.sqrt(len(nums))) if nums else 0
            nums = list(nums) + [0] * (n * n - len(nums))
            rows = [nums[i * n:(i + 1) * n] for i in range(n)]
        else:
            rows = [list(r) for r in data]
        self.rows = [[round_(v, ROUND_MATRIX) for v in r] for r in rows]

    @property
    def n(self) -> int:
        return len(self.rows)

    @classmethod
    def identity(cls, n: int) -> "Matrix":
        n = math.ceil(n)
        return cls([[1 if i == j else 0 for j in range(n)] for i in range(n)])

    def to_array(self) -> List[float]:
        return [v for r in self.rows for v in r]

    def determinant(self) -> float:
        n = self.n
        if n == 1:
            return self.rows[0][0]
        det, sign = 0, 1
        for j in range(n):
            sub = Matrix([[self.rows[r][c] for c in range(n) if c != j] for r in range(1, n)])
            det += sign * self.rows[0][j] * sub.determinant()
            sign = -sign
        return det

    det = property(determinant)

    def inverse(self) -> Optional["Matrix"]:
        det = self.determinant()
        if abs(det) < EPSILON:
            return None
        n = self.n
        cof = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                c = 1
                if n > 1:
                    c = Matrix([[self.rows[r][k] for k in range(n) if k != j]
                                for r in range(n) if r != i]).determinant()
                cof[i][j] = -c if (i + j) % 2 == 1 else c
        return Matrix([[cof[j][i] / det for j in range(n)] for i in range(n)])

    def rotate(self, x: float = 0, y: float = 0, z: float = 0) -> "Matrix":
        sx, sy, sz = (math.sin(math.radians(a)) for a in (x, y, z))
        cx, cy, cz = (math.cos(math.radians(a)) for a in (x, y, z))
        rot = Matrix([cy * cz, -cx * sz + sx * sy * cz, sx * sz + cx * sy * cz,
                      cy * sz, cx * cz + sx * sy * sz, -sx * cz + cx * sy * sz,
                      -sy, sx * cy, cx * cy])
        return self * rot

    def __mul__(self, other):
        n = self.n
        if isinstance(other, (int, float)):
            return Matrix([[v * other for v in r] for r in self.rows])
        if isinstance(other, Matrix):
            return Matrix([[sum(self.rows[i][k] * other.rows[k][j] for k in range(n))
                            for j in range(n)] for i in range(n)])
        vals = get_numbers(other)  # matriz * punto -> vector
        return [sum(self.rows[i][j] * (vals[j] if j < len(vals) else 0) for j in range(n))
                for i in range(n)]

    __rmul__ = __mul__

    def __add__(self, other):
        o = other if isinstance(other, (int, float)) else None
        return Matrix([[v + (o if o is not None else other.rows[i][j]) for j, v in enumerate(r)]
                       for i, r in enumerate(self.rows)])

    def __sub__(self, other):
        o = other if isinstance(other, (int, float)) else None
        return Matrix([[v - (o if o is not None else other.rows[i][j]) for j, v in enumerate(r)]
                       for i, r in enumerate(self.rows)])

    def __neg__(self):
        return Matrix([[-v for v in r] for r in self.rows])

    def __eq__(self, other):
        return (isinstance(other, Matrix) and self.n == other.n and
                all(abs(a - b) < EPSILON for r1, r2 in zip(self.rows, other.rows) for a, b in zip(r1, r2)))

    def __repr__(self):
        return "matrix%dx%d(%s)" % (self.n, self.n, self.rows)


def _is_rows(data: Any) -> bool:
    return isinstance(data, (list, tuple)) and bool(data) and all(isinstance(r, (list, tuple)) for r in data)

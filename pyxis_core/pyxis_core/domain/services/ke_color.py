# -*- coding: utf-8 -*-
# Port de `ke.color` (newkara_library.lua de Effector).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Colores ASS (&HBBGGRR&): conversion RGB/HSV, aleatorios e interpolacion. Funciones puras.

Pendiente (depende del estado `ke.infofx`, fase siguiente): `ke.color.set`.
"""

from __future__ import annotations

import math
import re
from typing import List, Optional, Sequence

from . import ke_math
from .ke_common import round_half_up, to_number

_HEX6 = re.compile(r"(?:^|[^0-9A-Fa-f])([0-9A-Fa-f]{6})(?:[^0-9A-Fa-f]|$)")


def ass(R=255, G=255, B=255) -> str:
    """ke.color.ass: color en formato xy-vsfilter "&HBBGGRR&".

    Acepta (R, G, B) como numeros 0-255 (los valores fuera de rango rebotan, ping-pong),
    una tupla (R, G, B), "#RRGGBB" (HTML), "&HBBGGRR&" o "&HAABBGGRR" (de un estilo, se descarta el alfa).
    """
    R, G, B = to_number(R, 255), to_number(G, 255), to_number(B, 255)
    if isinstance(R, (list, tuple)):
        R, G, B = (list(R) + [255, 255])[:3]
    if isinstance(R, str):
        s = R.strip()
        m = re.fullmatch(r"#([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})", s)
        if m:  # HTML RGB -> ASS BGR
            return "&H%s%s%s&" % (m.group(3).upper(), m.group(2).upper(), m.group(1).upper())
        m = re.fullmatch(r"&?[Hh]?([0-9A-Fa-f]{8})&?", s)
        if m:  # de un estilo: &HAABBGGRR -> se descarta AA
            return "&H%s&" % m.group(1)[2:].upper()
        m = _HEX6.search(s)
        if m:
            return "&H%s&" % m.group(1).upper()
        raise ValueError("color invalido: %r" % R)
    if isinstance(R, (int, float)):
        def wrap(v):
            return int(ke_math.sequence(v + 1, 0, 255, mode="ABA"))
        return "&H%02X%02X%02X&" % (wrap(B), wrap(G), wrap(R))
    raise ValueError("color invalido: %r" % (R,))


def to_rgb(color: str = "&HFFFFFF&") -> List[int]:
    """ke.color.to_RGB: [R, G, B]."""
    c = ass(color or "&HFFFFFF&")
    b, g, r = c[2:4], c[4:6], c[6:8]
    return [int(r, 16), int(g, 16), int(b, 16)]


def to_hsv(color: str = "&HFFFFFF&") -> List[float]:
    """ke.color.to_HSV: [H (0-360), S (0-1), V (0-1)]."""
    r, g, b = to_rgb(color)
    r, g, b = r / 255 + 0.000001, g / 255, b / 255
    cmax, cmin = max(r, g, b), min(r, g, b)
    d = cmax - cmin
    if cmax == r:
        h = ke_math.round_(60 * (((g - b) / d) % 6), 3)
    elif cmax == g:
        h = ke_math.round_(60 * (((b - r) / d) + 2), 3)
    else:
        h = ke_math.round_(60 * (((r - g) / d) + 4), 3)
    return [h, ke_math.round_(d / cmax, 3), ke_math.round_(cmax, 3)]


def hsv_to_rgb(H=0, S=1, V=1) -> str:
    """ke.color.HSV_to_RGB: HSV (H 0-360, S y V 0-1) -> color ASS."""
    if isinstance(H, (list, tuple)):
        H, S, V = H[0], H[1], H[2]
    H, S, V = to_number(H, 0), to_number(S, 1), to_number(V, 1)
    H = ((H - 1) % 360 + 1) / 360 * 6
    S, V = ((1000 * S) % 1001) / 1000, ((1000 * V) % 1001) / 1000
    if S == 0 or V == 0:
        return "&HFFFFFF&" if S == 0 else "&H000000&"
    C = V * S
    M = V - C
    X = C * (1 - abs((H % 2) - 1))
    r = C if H < 1 else X if H < 2 else 0 if H < 4 else X if H < 5 else C
    g = X if H < 1 else C if H < 3 else X if H < 4 else 0
    b = 0 if H < 2 else X if H < 3 else C if H < 5 else X
    return ass(255 * (r + M), 255 * (g + M), 255 * (b + M))


def random(H=None, S=1, V=1, rng=None) -> str:
    """ke.color.random: color aleatorio. H/S/V pueden ser numero fijo o rango (a, b)."""
    kw = {"rng": rng} if rng is not None else {}
    S, V = to_number(S, 1) * 100, to_number(V, 1) * 100
    if H is None:
        H = ke_math.rand(360, **kw)
    if isinstance(H, (list, tuple)):
        H = ke_math.rand((H[0] - 1) % 360 + 1, (H[1] - 1) % 360 + 1, **kw)
    else:
        H = (H - 1) % 360 + 1

    def comp(v):
        if isinstance(v, (list, tuple)):
            return ke_math.rand(v[1] % 101, v[0] % 101, **kw) / 100
        return ke_math.sequence(v + 1, 0, 100, mode="ABA") / 100

    return hsv_to_rgb(H, comp(S), comp(V))


def ipol(colors: Sequence[str], t: float = 0.5, accel=1, shape=None, size: Optional[int] = None):
    """ke.color.ipol: interpolacion entre dos o mas colores."""
    if size:
        return [ipol(colors, i / (size - 1), accel, shape) for i in range(size)]
    t = ke_math.normalize(0.5 if t is None else t, accel, shape)
    if t == 0:
        return colors[0]
    n = len(colors)
    seg = math.ceil(t * (n - 1))
    c1, c2 = to_rgb(colors[seg - 1]), to_rgb(colors[seg])
    u = t * (n - 1) - (seg - 1)
    r, g, b = (ke_math.round_(a + (z - a) * u) for a, z in zip(c1, c2))
    return ass(r, g, b)

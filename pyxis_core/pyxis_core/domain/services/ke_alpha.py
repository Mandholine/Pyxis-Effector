# -*- coding: utf-8 -*-
# Port de `ke.alpha` (newkara_library.lua de Effector).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Transparencias ASS (&HXX&): formato, aleatorios e interpolacion. Funciones puras."""

from __future__ import annotations

import math
import re
from typing import Optional, Sequence, Union

from . import ke_math
from .ke_common import recurse, to_number


def ass(alpha=0, number: bool = False) -> Union[str, int]:
    """ke.alpha.ass: "&HXX&" (o el entero 0-255 con number=True).

    Acepta un numero (se toma modulo 256), "FF", "&HFF&", "#F0" o listas anidadas."""
    if isinstance(alpha, (list, tuple, dict)):
        return recurse(ass, alpha, number)
    alpha = to_number(alpha, 0)
    if isinstance(alpha, (int, float)):
        hx = "%X" % (math.ceil(alpha) % 256)
    else:
        m = re.search(r"([0-9A-Fa-f]{1,2})&?$", str(alpha).replace("&H", "").replace("#", ""))
        if not m:
            raise ValueError("alpha invalido: %r" % (alpha,))
        hx = m.group(1)
    hx = ("0" + hx if len(hx) == 1 else hx).upper()
    return int(hx, 16) if number else "&H%s&" % hx


def random(alpha1=0, alpha2=255, rng=None) -> str:
    """ke.alpha.random: alpha aleatorio entre dos valores."""
    kw = {"rng": rng} if rng is not None else {}
    a1, a2 = ass(alpha1, True), ass(alpha2, True)
    return ass(ke_math.rand(a2, a1, **kw))


def ipol(alphas: Sequence, t: float = 0.5, accel=1, shape=None, size: Optional[int] = None):
    """ke.alpha.ipol: interpolacion entre dos o mas alphas."""
    if size:
        return [ipol(alphas, i / (size - 1), accel, shape) for i in range(size)]
    t = ke_math.normalize(0.5 if t is None else t, accel, shape)
    if t == 0:
        return alphas[0]
    n = len(alphas)
    seg = math.ceil(t * (n - 1))
    a1, a2 = ass(alphas[seg - 1], True), ass(alphas[seg], True)
    u = t * (n - 1) - (seg - 1)
    return ass(a1 + u * (a2 - a1))

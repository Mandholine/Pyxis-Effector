# -*- coding: utf-8 -*-
# Pyxis Effector — Domain Services (port de la libreria `ke` de Effector)
#
# Portado de newkara_library.lua de Effector.
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved.
# Redistribution and use in source and binary forms, with or without modification, are
# permitted provided that the conditions of the original BSD-style notice are met
# (see luas-old/newkara_library.lua): the copyright notice must be retained, and the
# names of EFFECTOR, its author or contributors may not be used to endorse derived
# products without written permission. Provided "AS IS", without warranty.

"""Constantes y utilidades compartidas por los servicios `ke_*` (funciones puras)."""

from __future__ import annotations

import math
import re
from typing import Any, Callable, Iterable, List

ROUND_MATRIX = 6   # decimales para redondear valores en matrices
ROUND_NUM = 3      # decimales para redondear un valor numerico
EPSILON = 1e-6     # |valor| < EPSILON se considera 0

_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?|-?\.\d+")


def round_half_up(value: float, decimals: int = 0):
    """floor(x * 10^d + 0.5) / 10^d, igual que ke.math.round. Entero si decimals == 0."""
    decimals = int(abs(decimals))
    result = math.floor(value * (10 ** decimals) + 0.5) / (10 ** decimals)
    return int(result) if decimals == 0 else result


def recurse(fn: Callable, obj: Any, *args, **kwargs):
    """Aplica `fn` a cada elemento de listas/tuplas/dicts anidados (ke.table.recurse)."""
    if isinstance(obj, dict):
        return {k: recurse(fn, v, *args, **kwargs) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [recurse(fn, v, *args, **kwargs) for v in obj]
    return fn(obj, *args, **kwargs)


def _numbers_in_string(text: str) -> List[float]:
    out: List[float] = []
    for m in _NUM_RE.findall(text):
        f = float(m)
        out.append(int(f) if f.is_integer() and "." not in m else f)
    return out


def _numbers_in(v: Any) -> List[float]:
    if isinstance(v, bool) or v is None:
        return []
    if isinstance(v, (int, float)):
        return [v]
    if isinstance(v, str):
        return _numbers_in_string(v)
    if isinstance(v, dict):
        return [n for key in ("x", "y", "z") if key in v for n in _numbers_in(v[key])]
    if isinstance(v, Iterable):
        return [n for item in v for n in _numbers_in(item)]
    return [n for key in ("x", "y", "z") if hasattr(v, key) for n in _numbers_in(getattr(v, key))]


def get_numbers(*values: Any) -> List[float]:
    """Aplana numeros, cadenas ("7 8"), secuencias y objetos con x/y/z en una lista de numeros."""
    return [n for v in values for n in _numbers_in(v)]


def to_number(value: Any, default: Any = None):
    """Equivale a ke.math.__init para valores escalares: numero, cadena numerica o callable."""
    if callable(value):
        value = value()
    if value is None:
        return default
    if isinstance(value, str):
        try:
            f = float(value)
            return int(f) if f.is_integer() and "." not in value else f
        except ValueError:
            return value
    return value

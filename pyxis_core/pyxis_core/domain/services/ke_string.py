# -*- coding: utf-8 -*-
# Port de `ke.string` (newkara_library.lua de Effector).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Utilidades de cadenas para tags ASS. Funciones puras.

DIFERENCIA CON EL ORIGINAL: los patrones son expresiones regulares de Python (`re`), no
patrones de Lua. Los alias "number", "point", "color", "alpha" y "shape" siguen existiendo.
`toval`/`loadstr` (evaluacion de codigo Lua en tiempo de ejecucion) no se portan: la
evaluacion de expresiones la hace `pyxis_core...graph.string_evaluator`.
"""

from __future__ import annotations

import random as _random
import re
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from . import ke_math
from .ke_common import recurse

ALIASES: Dict[str, str] = {
    "number": r"-?\d[.\d]*",
    "point": r"-?\d[.\d]*\s+-?\d[.\d]*",
    "color": r"[&#Hh]*[0-9A-Fa-f]{6}&?",
    "alpha": r"&[Hh]?[0-9A-Fa-f]{2}&",
    "shape": r"m\s+-?\d[.\-\d mlb]*",
}

Pattern = Union[str, "re.Pattern[str]"]


def _pat(p: Pattern) -> "re.Pattern[str]":
    return p if isinstance(p, re.Pattern) else re.compile(ALIASES.get(p, p))


def _as_list(x) -> list:
    return list(x) if isinstance(x, (list, tuple)) else [x]


def count(text, captures: Union[Pattern, Sequence[Pattern]]) -> int:
    """ke.string.count: cuantas veces aparece cada captura (o alias) en la cadena."""
    if isinstance(text, (list, tuple, dict)):
        return recurse(count, text, captures)
    return sum(sum(1 for _ in _pat(c).finditer(text)) for c in _as_list(captures))


def array(text, captures: Union[None, Pattern, Sequence[Pattern]] = None) -> list:
    """ke.string.array: sin captura -> lista de caracteres; "chars" tambien; si no, las capturas.

    Con grupos en el patron, cada elemento es la tupla de grupos."""
    if isinstance(text, (list, tuple, dict)):
        return recurse(array, text, captures)
    if captures is None:
        return list(text)
    out: list = []
    for cap in _as_list(captures):
        if cap == "chars":
            out.extend(text)
            continue
        for m in _pat(cap).finditer(text):
            out.append(m.groups() if m.groups() else m.group(0))
    return out


def protect(text: str, captures: Union[Pattern, Sequence[Pattern]]) -> Tuple[str, List[str]]:
    """ke.string.protect: reemplaza las capturas por "<x>" para poder transformar el resto.

    Devuelve (texto_protegido, capturas_en_orden_de_aparicion). Restaurar con `unprotect`."""
    saved: List[str] = []
    for cap in _as_list(captures):
        text = _pat(cap).sub(lambda m: (saved.append(m.group(0)) or "\x00%d\x00" % (len(saved) - 1)), text)
    order = [int(i) for i in re.findall("\x00(\\d+)\x00", text)]
    text = re.sub("\x00\\d+\x00", "<x>", text)
    return text, [saved[i] for i in order]


def unprotect(text: str, saved: Sequence[str]) -> str:
    """Devuelve las capturas guardadas por `protect` a su lugar."""
    it = iter(saved)
    return re.sub(r"<x>", lambda m: next(it, ""), text)


def delete(text: str, captures: Union[Pattern, Sequence[Pattern]],
           except_: Iterable[int] = (), protect_: Union[None, Pattern, Sequence[Pattern]] = None) -> str:
    """ke.string.delete: borra las capturas, salvo las que ocupan las posiciones `except_` (1-based)."""
    saved: List[str] = []
    if protect_:
        text, saved = protect(text, protect_)
    keep = set(except_)
    for pat in _as_list(captures):
        counter = {"i": 0}

        def repl(m, _c=counter):
            _c["i"] += 1
            return m.group(0) if _c["i"] in keep else ""

        text = _pat(pat).sub(repl, text)
    return unprotect(text, saved) if protect_ else text


def change(text: str, captures: Union[Pattern, Sequence[Pattern]],
           filter_: Union[str, Callable, Sequence] = "", nochange: Union[int, Sequence[int]] = (),
           protect_: Union[None, Pattern, Sequence[Pattern]] = None) -> str:
    """ke.string.change: cambia (o borra) capturas. `filter_` es un texto, una funcion(*grupos)
    o una lista de ellos (uno por captura). `nochange` son posiciones 1-based (negativas desde el final)."""
    if isinstance(text, (list, tuple, dict)):
        return recurse(change, text, captures, filter_, nochange, protect_)
    saved: List[str] = []
    if protect_:
        text, saved = protect(text, protect_)
    skip = [nochange] if isinstance(nochange, int) else list(nochange)
    pats = [_pat(c) for c in _as_list(captures)]
    total = sum(sum(1 for _ in p.finditer(text)) for p in pats)
    skip = {v if v > 0 else total + v + 1 for v in skip}
    n = {"i": 0}

    for idx, pat in enumerate(pats):
        def repl(m, _idx=idx):
            n["i"] += 1
            if n["i"] in skip:
                return m.group(0)
            f = filter_[_idx] if isinstance(filter_, (list, tuple)) else filter_
            return str(f(*(m.groups() or (m.group(0),)))) if callable(f) else str(f)

        text = pat.sub(repl, text)
    return unprotect(text, saved) if protect_ else text


def parts(text: str, size: Union[int, Tuple[int, int]] = 3, rng=_random) -> List[str]:
    """ke.string.parts: parte el texto en trozos de `size` caracteres (o de tamano aleatorio (a, b))."""
    if isinstance(size, (int, float)):
        size = int(abs(size)) or 2
    else:
        size = (size[0] if size[0] > 0 else 1, size[1] if size[1] > 0 else 2)
    chars, out = list(text), []
    while chars:
        n = ke_math.rand(size[0], size[1], rng=rng) if isinstance(size, tuple) else size
        out.append("".join(chars[:n]))
        chars = chars[n:]
    return out


def disorder(text: str, rng=_random) -> str:
    """ke.string.disorder: mezcla los caracteres al azar."""
    chars = list(text)
    rng.shuffle(chars)
    return "".join(chars)


def index_variable(text: str) -> str:
    """ke.string.i: sustituye la variable `i` dentro de cada \\tag(...) por un contador consecutivo
    ("\\fr(-5i)\\frx(10 - i)" -> "\\fr(-5 * 0)\\frx(10 - 1)")."""
    counter = {"n": 0}
    var = re.compile(r"([+ \-*/^(\[{\d%])i(?=[+ \-*/^)\]}%\\]|$)")

    def per_tag(m):
        original = m.group(0)
        new = var.sub(lambda v: (v.group(1) + " * " + str(counter["n"])) if v.group(1).isdigit()
                      else v.group(1) + str(counter["n"]), original)
        if new != original:
            counter["n"] += 1
        return new

    return re.sub(r"\\\w+\([^()]*(?:\([^()]*\)[^()]*)*\)", per_tag, text)

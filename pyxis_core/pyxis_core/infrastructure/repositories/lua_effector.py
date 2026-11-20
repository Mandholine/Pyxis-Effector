# -*- coding: utf-8 -*-
# Lectura de los efectos de Kara Effector 3.6 (Effector-3.6.lua): llamadas `effector.create_fx( ... )`.

"""Parser de las definiciones `NOMBRE = effector.create_fx( "LIfx", "NOMBRE", ... )` del Lua original."""

from __future__ import annotations

import re
from typing import Any, Iterator, List, Tuple

from ...domain.entities.fx_template import FX_KINDS, FxTemplate

_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "\\": "\\", '"': '"', "'": "'", "a": "\a", "b": "\b", "f": "\f", "v": "\v"}
_DEF = re.compile(r"(?P<var>[A-Za-z_]\w*)\s*=\s*effector\.create_fx\s*\(")


def _unescape(raw: str) -> str:
    out, i = [], 0
    while i < len(raw):
        ch = raw[i]
        if ch != "\\" or i + 1 >= len(raw):
            out.append(ch)
            i += 1
            continue
        nxt = raw[i + 1]
        if nxt in _ESCAPES:
            out.append(_ESCAPES[nxt])
            i += 2
        elif nxt.isdigit():
            m = re.match(r"\d{1,3}", raw[i + 1:])
            out.append(chr(int(m.group(0))))
            i += 1 + len(m.group(0))
        else:
            out.append(nxt)
            i += 2
    return "".join(out)


def parse_args(text: str, start: int) -> Tuple[List[Any], int]:
    """Lee los argumentos de una llamada Lua desde el caracter siguiente a `(` hasta el `)` que la cierra.
    Valores: cadenas, numeros, true/false/nil. Devuelve (valores, indice tras el parentesis)."""
    i, values, n = start, [], len(text)
    while i < n:
        ch = text[i]
        if ch in " \t\r\n,":
            i += 1
        elif ch == ")":
            return values, i + 1
        elif ch in "\"'":
            j = i + 1
            while j < n and text[j] != ch:
                j += 2 if text[j] == "\\" else 1
            values.append(_unescape(text[i + 1:j]))
            i = j + 1
        else:
            m = re.match(r"-?\d+(?:\.\d+)?|true|false|nil", text[i:])
            if not m:
                raise ValueError("argumento Lua no soportado cerca de %r" % text[i:i + 30])
            tok = m.group(0)
            values.append({"true": True, "false": False, "nil": None}[tok] if tok in ("true", "false", "nil")
                          else (float(tok) if "." in tok else int(tok)))
            i += len(tok)
    raise ValueError("llamada Lua sin cerrar")


def iter_definitions(text: str) -> Iterator[Tuple[str, List[Any]]]:
    """(variable, argumentos) de cada `X = effector.create_fx( ... )` del texto (ignora comentarios `--`)."""
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            continue
        m = _DEF.match(stripped)
        if not m:
            continue
        try:
            args, _ = parse_args(stripped, m.end())
        except ValueError:
            continue
        yield m.group("var"), args


def parse_effects(text: str) -> List[FxTemplate]:
    """Todos los efectos de un `Effector-3.6.lua` (o de un archivo con el mismo formato)."""
    effects: List[FxTemplate] = []
    for _, args in iter_definitions(text):
        if len(args) >= 2 and args[0] in FX_KINDS:
            effects.append(FxTemplate.from_sequence(args))
    return effects

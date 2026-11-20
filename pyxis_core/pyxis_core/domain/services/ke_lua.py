# -*- coding: utf-8 -*-
# Utilidades para traducir las expresiones Lua del listado de efectos de Effector a Python.
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Traduccion minima Lua -> Python de las expresiones de los efectos de Kara Effector (puro)."""

from __future__ import annotations

import re
from typing import Callable, List

_RULES = [(r"~=", "!="), (r"\bnil\b", "None"), (r"\btrue\b", "True"), (r"\bfalse\b", "False"),
          (r"\s*\.\.\s*", " + "), (r"\^", "**"), (r"#(\w+)", r"len(\1)")]


def outside_strings(text: str, fn: Callable[[str], str]) -> str:
    """Aplica `fn` solo a los trozos de `text` que no estan dentro de comillas."""
    out: List[str] = []
    buf: List[str] = []
    quote = None
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and i + 1 < len(text):
                buf.append(text[i + 1])
                i += 1
            elif ch == quote:
                out.append("".join(buf))
                buf, quote = [], None
        elif ch in "\"'":
            out.append(fn("".join(buf)))
            buf, quote = [ch], ch
        else:
            buf.append(ch)
        i += 1
    out.append("".join(buf) if quote else fn("".join(buf)))
    return "".join(out)


def lua_expr(text: str, shift_indices: bool = True) -> str:
    """Expresion Lua -> Python (`~=`, nil, true/false, `..`, `^`, `#x`, `{a, b}`); no toca el contenido de cadenas.

    Con `shift_indices=True` (listas de Python) `lista[j]` pasa a `lista[j - 1]`; con False las tablas de Lua se
    convierten a diccionarios de indices desde 1 (ver `lua_tables`) y no se ajusta nada."""
    def tr(chunk: str) -> str:
        for pat, rep in _RULES:
            chunk = re.sub(pat, rep, chunk)
        if not shift_indices:
            return chunk
        chunk = chunk.replace("{", "[").replace("}", "]")
        # los indices de bucle de Lua empiezan en 1: lista[j] -> lista[j - 1]
        return re.sub(r"\[\s*(j|i|\w+\.i)\s*\]", r"[\1 - 1]", chunk)
    out = outside_strings(text, tr).strip()
    return out if shift_indices else lua_tables(out)


def _match_brace(text: str, start: int) -> int:
    """Indice de la `}` que cierra la `{` en `start` (respeta cadenas); -1 si no cierra."""
    depth, quote, i = 0, None, start
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\" and i + 1 < len(text):
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def lua_tables(text: str) -> str:
    """Convierte los constructores de tabla de Lua en `lt({...})` (`ke3.LuaTable`, indices desde 1 como en Lua):
    `{a, b}` -> `lt({1: a, 2: b})`;  `{[1] = x, times = y}` -> `lt({1: x, "times": y})`. Funciona con tablas anidadas."""
    out, i = [], 0
    while i < len(text):
        # saltar cadenas intactas
        if text[i] in "\"'":
            q, j = text[i], i + 1
            while j < len(text) and text[j] != q:
                j += 2 if text[j] == "\\" else 1
            out.append(text[i:j + 1])
            i = j + 1
        elif text[i] == "{":
            end = _match_brace(text, i)
            if end < 0:
                out.append(text[i:])
                break
            items, n = [], 0
            for raw in split_top(text[i + 1:end]):
                raw = raw.strip()
                if not raw:
                    continue
                m = re.match(r"\[\s*(.+?)\s*\]\s*=(?!=)\s*(.*)$", raw, re.S) or \
                    re.match(r"([A-Za-z_]\w*)\s*=(?!=)\s*(.*)$", raw, re.S)
                if m:
                    key = m.group(1)
                    key = key if raw.startswith("[") else '"%s"' % key
                    items.append("%s: %s" % (lua_tables(key), lua_tables(m.group(2))))
                else:
                    n += 1
                    items.append("%d: %s" % (n, lua_tables(raw)))
            out.append("lt({" + ", ".join(items) + "})")
            i = end + 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def expand_units(text: str, unit: str = "syl") -> str:
    """Atajos de Kara Effector (fuera de cadenas): `50li` -> `time_li(50)`, `50lo`, `50mid1`, `50mid2`;
    `10f` -> `(10 * frame_dur)` (frames a ms); `10r` -> `(10 * ratio)` (escala segun la resolucion)."""
    def tr(chunk: str) -> str:
        chunk = re.sub(r"(?<![\w.])(\d+(?:\.\d+)?)(li|lo|mid1|mid2)\b",
                       lambda m: "time_%s(%s)" % (m.group(2), m.group(1)), chunk)
        chunk = re.sub(r"(?<![\w.])(\d+(?:\.\d+)?)f\b", r"(\1 * frame_dur)", chunk)
        return re.sub(r"(?<![\w.])(\d+(?:\.\d+)?)r\b", r"(\1 * ratio)", chunk)
    return outside_strings(text, tr)


def split_statements(text: str) -> List[str]:
    """Parte un bloque de Lua en sentencias: por `;` o salto de linea en el nivel superior."""
    parts: List[str] = []
    cur: List[str] = []
    depth, quote, i = 0, None, 0
    while i < len(text):
        ch = text[i]
        if quote:
            cur.append(ch)
            if ch == "\\" and i + 1 < len(text):
                cur.append(text[i + 1])
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        else:
            depth += ch in "([{"
            depth -= ch in ")]}"
            if ch in ";\n" and depth == 0:
                parts.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        i += 1
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip() and not p.strip().startswith("--")]


def split_top(text: str, sep: str = ",") -> List[str]:
    """Parte por `sep` solo en el nivel superior (respeta parentesis, corchetes, llaves y cadenas)."""
    parts: List[str] = []
    cur: List[str] = []
    depth, quote, i = 0, None, 0
    while i < len(text):
        ch = text[i]
        if quote:
            cur.append(ch)
            if ch == "\\" and i + 1 < len(text):
                cur.append(text[i + 1])
                i += 1
            elif ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur.append(ch)
        else:
            depth += ch in "([{"
            depth -= ch in ")]}"
            if ch == sep and depth == 0:
                parts.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        i += 1
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts

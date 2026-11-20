# -*- coding: utf-8 -*-
# Port de `ke.time` (newkara_library.lua de Effector).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Conversion de tiempos (HMS / ms / frames) y retardos escalonados. Funciones puras.

En el original, `leadin/leadout/middle/loop` leian el estado global `ke.infofx.data`;
aqui reciben los indices explicitamente (i, n, j, maxj) y `frame_dur` (ms por frame).

"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Sequence, Union

from . import ke_math
from .ke_common import recurse, round_half_up, to_number

_HMS = re.compile(r"^(\d+):(\d+):(\d+)\.(\d+)$")
DEFAULT_FRAME_DUR = 1000 / 24  # ms por frame (23.976 fps ~ 41.7)


def hms_to_ms(hms):
    """ke.time.HMS_to_ms: "0:00:34.952" -> 34952 (admite listas anidadas y numeros)."""
    if isinstance(hms, (list, tuple, dict)):
        return recurse(hms_to_ms, hms)
    hms = to_number(hms, 0)
    if isinstance(hms, str):
        m = _HMS.match(hms)
        if not m:
            return hms
        h, mi, s, ms = m.groups()
        ms_val = int(ms) * (10 if len(ms) == 2 else 100 if len(ms) == 1 else 1)
        return int(h) * 3600000 + int(mi) * 60000 + int(s) * 1000 + ms_val
    return hms


def ms_to_hms(ms) -> str:
    """ke.time.ms_to_HMS: 34952 -> "0:00:34.952"."""
    if isinstance(ms, (list, tuple, dict)):
        return recurse(ms_to_hms, ms)
    t = ke_math.round_(to_number(ms, 0))
    h, t = divmod(t, 3600000)
    m, t = divmod(t, 60000)
    s, t = divmod(t, 1000)
    return "%d:%02d:%02d.%03d" % (h, m, s, t)


def time_to_frame(time, frame_dur: float = DEFAULT_FRAME_DUR):
    """ke.time.time_to_frame: cantidad de frames en un tiempo (ms o HMS)."""
    if isinstance(time, (list, tuple, dict)):
        return recurse(time_to_frame, time, frame_dur)
    ms = hms_to_ms(time) if isinstance(time, str) and _HMS.match(time) else to_number(time, 0)
    return math.ceil(ms / frame_dur)


def frame_to_ms(frames, frame_dur: float = DEFAULT_FRAME_DUR):
    if isinstance(frames, (list, tuple, dict)):
        return recurse(frame_to_ms, frames, frame_dur)
    return ke_math.round_(to_number(frames, 0) * frame_dur, 2)


def frame_to_hms(frames, frame_dur: float = DEFAULT_FRAME_DUR):
    if isinstance(frames, (list, tuple, dict)):
        return recurse(frame_to_hms, frames, frame_dur)
    return ms_to_hms(frame_to_ms(frames, frame_dur))


# ------------------------------------------------ retardos por indice de unidad ---


def leadin(i: int, delay: float = 40) -> float:
    """Entrada escalonada: cada unidad `i` (1..n) entra `delay` ms despues de la anterior."""
    return delay * (i - 1) - 200


def leadout(i: int, n: int, delay: float = 40) -> float:
    """Salida escalonada de las unidades i (1..n)."""
    return delay * (i - n - 1) + 200


def middle(i: int, n: int, delay: float = 30) -> float:
    """Desde el centro hacia los extremos."""
    return delay * (i - 1) - 200 if i <= (n + 1) / 2 else delay * (n - i + 0.5) - 200


def mid1(i: int, n: int, delay: float = 60) -> float:
    """ke4.time.mid1: extremos -> centro (equivale a `middle`)."""
    return delay * (i - 1) - 200 if i <= (n + 1) / 2 else delay * (n - i + 0.5) - 200


def mid2(i: int, n: int, delay: float = 60) -> float:
    """ke4.time.mid2: centro -> extremos."""
    return delay * (i - n - 1) - 200 if i >= (n + 1) / 2 else delay * (-i + 0.5) - 200


def loop(j: int, maxj: int, delay: float = 30, mode: str = "leadin") -> float:
    """Igual que leadin/leadout/middle pero sobre el indice de bucle j (1..maxj)."""
    if mode == "leadin":
        return delay * (j - 1) - 200
    if mode == "leadout":
        return delay * (j - maxj - 1) + 200
    if mode in ("middle", "mid1"):
        return mid1(j, maxj, delay)
    if mode == "mid2":
        return mid2(j, maxj, delay)
    return delay


def ipol(times, n: Optional[int] = None, accel=1, numbers: Optional[Sequence[float]] = None,
         points: Optional[Sequence[Any]] = None):
    """ke.time.ipol: reparte un intervalo en segmentos (con aceleracion).

    - times = ms final (0..t), [ini, fin] o [t1, t2, t3, ...] (HMS admitido).
    - n: cantidad de segmentos iguales.  - numbers: duraciones proporcionales a |delta| de esos valores.
    - points: lista de Point; la duracion de cada tramo es proporcional a su longitud.
    Devuelve una lista de [ini, fin] por cada grupo.
    """
    times = hms_to_ms(times)
    if isinstance(times, (int, float)):
        groups = [[0, times]]
    elif isinstance(times, (list, tuple)) and times and isinstance(times[0], (list, tuple)):
        return [list(t) for t in times]
    else:
        groups = [[times[k], times[k + 1]] for k in range(len(times) - 1)]
    result = []
    for t0, t1 in groups:
        dur = t1 - t0
        if points:
            from .ke_point import Point
            pts = [Point(p) for p in points]
            lengths = [pts[k].distance(pts[k - 1]) for k in range(1, len(pts))]
            total, acc, aux = sum(lengths), 0.0, [t0]
            for ln in lengths:
                acc += ln
                u = acc / total
                aux.append(t0 + dur * (accel(u) if callable(accel) else u ** accel))
            result.append([[aux[k], aux[k + 1]] for k in range(len(aux) - 1)])
        elif numbers:
            total = sum(abs(numbers[k] - numbers[k - 1]) for k in range(1, len(numbers)))
            acc, aux = 0, [t0]
            for k in range(1, len(numbers)):
                acc += abs(numbers[k] - numbers[k - 1])
                u = acc / total
                aux.append(t0 + dur * (accel(u) if callable(accel) else u ** accel))
            result.append([[aux[k], aux[k + 1]] for k in range(len(aux) - 1)])
        elif n:
            pts = ke_math.ipol([t0, t1], None, accel, None, n + 1)
            result.append([[pts[k], pts[k + 1]] for k in range(len(pts) - 1)])
        else:
            result.append([t0, t1])
    return result


# ----------------------------------------------------------------------------- retime ---
# Port de `retime` de Kara Effector 3.6 legacy (Effector-3.6.lua, (c) 2012-2020 Vict8r, Karalaura, NatsuoKE &
# Itachi Akatsuki). Los 39 modos y sus tiempos son los del original, incluidos los que terminan en el INICIO de la
# unidad (`postword`, `postchar`), tal como estan escritos alli.

RETIME_MODES = (
    "line", "preline", "postline", "word", "preword", "postword", "syl", "sylmodule", "presyl", "postsyl",
    "furi", "prefuri", "postfuri", "char", "prechar", "postchar", "start2word", "word2end", "start2syl", "syl2end",
    "start2furi", "furi2end", "start2char", "char2end", "linepct", "wordpct", "sylpct", "furipct", "charpct",
    "set", "abs", "fxpretime", "fxtime", "fxposttime", "fxpct", "startsyl2char", "startword2syl", "startword2char",
    "syl2endword", "char2endsyl", "char2endword",
)
_FURI_MODES = {"furi", "prefuri", "postfuri", "start2furi", "furi2end", "furipct"}


def retime(unit: Any, mode: str, add_start: Any = 0, add_end: Any = 0, *, fx: Optional[Sequence[float]] = None,
           j: int = 1, maxj: int = 1, origin: float = 0):
    """`retime(mode, add_start, add_end)` de Kara Effector: (inicio, fin) absolutos en ms de la linea de efecto.

    `unit` es una unidad de `ke_units.units` (palabra, silaba o caracter). `add_start`/`add_end` aceptan ms o "H:MM:SS.cc".
    Modos: ver `RETIME_MODES` (line, word, syl, char, start2syl, syl2end, char2endsyl, linepct, sylpct, set...).
    `fx=(inicio, fin)` es el tiempo de la linea de efecto para los modos fx* (por defecto, el de la linea);
    `j`/`maxj` los usa `sylmodule`; `origin` se resta al resultado (tiempos relativos al inicio del efecto).
    Un modo desconocido devuelve el tiempo de la linea (el "default" del original)."""
    a, b = to_number(hms_to_ms(add_start), 0) or 0, to_number(hms_to_ms(add_end), 0) or 0
    ls, le = unit.line.start_time, unit.line.end_time
    ld = le - ls
    ws, we = unit.word_start, unit.word_end
    ss, se = unit.syl_start, unit.syl_end
    cs = unit.char_start if getattr(unit, "char_start", None) is not None else ss
    ce = unit.char_end if getattr(unit, "char_end", None) is not None else se
    fs_, fe_ = (fx if fx is not None else (ls, le))
    fd = fe_ - fs_
    if mode in _FURI_MODES:
        furi_s, furi_e = getattr(unit, "furi_start", None), getattr(unit, "furi_end", None)
        if furi_s is None or furi_e is None:
            raise ValueError("retime(%r): la unidad no tiene furigana (furi_start/furi_end)" % mode)
    else:
        furi_s = furi_e = 0
    table = {
        "line": (ls + a, le + b), "preline": (ls + a, ls + b), "postline": (le + a, le + b),
        "word": (ws + a, we + b), "preword": (ws + a, ws + b), "postword": (we + a, ws + b),
        "syl": (ss + a, se + b),
        "sylmodule": (ss + a + (se - ss + a + b) * (j - 1) / maxj, ss + a + (se - ss + a + b) * j / maxj),
        "presyl": (ss + a, ss + b), "postsyl": (se + a, se + b),
        "furi": (furi_s + a, furi_e + b), "prefuri": (furi_s + a, furi_s + b), "postfuri": (furi_e + a, furi_e + b),
        "char": (cs + a, ce + b), "prechar": (cs + a, cs + b), "postchar": (ce + a, cs + b),
        "start2word": (ls + a, ws + b), "word2end": (we + a, le + b),
        "start2syl": (ls + a, ss + b), "syl2end": (se + a, le + b),
        "start2furi": (ls + a, furi_s + b), "furi2end": (furi_e + a, le + b),
        "start2char": (ls + a, cs + b), "char2end": (ce + a, le + b),
        "linepct": (ls + a * ld / 100, ls + b * ld / 100),
        "wordpct": (ws + a * (we - ws) / 100, ws + b * (we - ws) / 100),
        "sylpct": (ss + a * (se - ss) / 100, ss + b * (se - ss) / 100),
        "furipct": (furi_s + a * (furi_e - furi_s) / 100, furi_s + b * (furi_e - furi_s) / 100),
        "charpct": (cs + a * (ce - cs) / 100, cs + b * (ce - cs) / 100),
        "set": (a, b), "abs": (a, b),
        "fxpretime": (fs_ + a, fs_ + b), "fxtime": (fs_ + a, fe_ + b), "fxposttime": (fe_ + a, fe_ + b),
        "fxpct": (fs_ + a * fd / 100, fs_ + b * fd / 100),
        "startsyl2char": (ss + a, cs + b), "startword2syl": (ws + a, ss + b), "startword2char": (ws + a, cs + b),
        "syl2endword": (se + a, we + b), "char2endsyl": (ce + a, se + b), "char2endword": (ce + a, we + b),
    }
    start, end = table.get(mode, (ls, le))
    return int(round(start - origin)), int(round(end - origin))


# ---- atajos de Kara Effector: `50li` = time_li(50), `50lo`, `50mid1`, `50mid2` (usan el indice de la unidad) ---


def time_li(unit: Any, delay: Optional[float] = None, mode: Optional[str] = None) -> float:
    """time_li: entrada escalonada (suma el retardo por indice). mode "syl"/"word": relativo a esa unidad."""
    delay = 40 if delay is None else delay
    if mode == "syl":
        return unit.syl_start - unit.line.start_time + delay * (unit.si - 1) - 200
    if mode == "word":
        return unit.word_start - unit.line.start_time + delay * (unit.wi - 1) - 200
    return delay * (unit.i - 1) - 200


def time_lo(unit: Any, delay: Optional[float] = None, mode: Optional[str] = None) -> float:
    """time_lo: salida escalonada."""
    delay = 40 if delay is None else delay
    if mode == "syl":
        return unit.syl_end - unit.line.start_time + delay * (unit.si - unit.syln - 1) + 200
    if mode == "word":
        return unit.word_end - unit.line.start_time + delay * (unit.wi - unit.wn - 1) + 200
    return delay * (unit.i - unit.n - 1) + 200


def time_mid1(unit: Any, delay: Optional[float] = None) -> float:
    """time_mid1: de los extremos hacia el centro."""
    return mid1(unit.i, unit.n, 30 if delay is None else delay)


def time_mid2(unit: Any, delay: Optional[float] = None) -> float:
    """time_mid2: del centro hacia los extremos."""
    return mid2(unit.i, unit.n, 30 if delay is None else delay)

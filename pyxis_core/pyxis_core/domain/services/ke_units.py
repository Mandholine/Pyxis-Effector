# -*- coding: utf-8 -*-
# Port del modelo de plantillas de Effector (template line / word / syl / char).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Unidades de karaoke (palabra, silaba, caracter) con sus tiempos ya resueltos. Puro (duck-typing).

`line` es el objeto de linea de pyxis-core: `line.syls`, `line.words`, `line.start_time`... Los tiempos de
silaba/palabra son relativos al inicio de la linea; los de caracter, relativos a su silaba. `Unit` los convierte
todos a tiempos ABSOLUTOS (ms) para poder usar `ke_time.retime`.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Iterator, Optional


class Unit(object):
    """Una palabra, silaba o caracter con tiempos absolutos y la informacion de su contexto.

    abs_start / abs_end     tiempo absoluto de esta unidad            dur   su duracion
    syl_start / syl_end     tiempo absoluto de su silaba
    word_start / word_end   tiempo absoluto de su palabra
    char_start / char_end   tiempo absoluto del caracter (None si la unidad es silaba/palabra)
    si / syln               indice (1-based) y total de silabas        wi / wn   idem de palabras
    kind                    "char" | "syl" | "word"
    parent_syl/parent_word  la silaba y la palabra a las que pertenece (como `syl`/`word` dentro de una plantilla char)
    sylchar                 (solo caracteres) i, n y start_time/mid_time/end_time DENTRO de su silaba; como en Effector,
                            la duracion de la silaba se reparte a partes iguales entre sus caracteres visibles
    El resto de atributos (center, middle, left, text_stripped...) se delegan en el objeto de pyxis-core.
    """

    def __init__(self, obj: Any, line: Any, abs_start: float, abs_end: float, syl_start: float, syl_end: float,
                 si: int, syln: int, word_start: Optional[float] = None, word_end: Optional[float] = None,
                 wi: int = 1, wn: int = 1, kind: str = "char", parent_syl: Optional["Unit"] = None,
                 parent_word: Optional["Unit"] = None, sylchar: Any = None):
        char_unit = kind == "char"
        self.__dict__.update(
            _obj=obj, line=line, abs_start=abs_start, abs_end=abs_end, syl_start=syl_start, syl_end=syl_end,
            word_start=syl_start if word_start is None else word_start,
            word_end=syl_end if word_end is None else word_end,
            char_start=abs_start if char_unit else None, char_end=abs_end if char_unit else None,
            si=si, syln=syln, wi=wi, wn=wn, kind=kind, dur=abs_end - abs_start,
            # como en Effector: start_time/end_time relativos al INICIO DE LA LINEA (en pyxis-core, los de un
            # caracter son relativos a su silaba)
            start_time=abs_start - line.start_time, end_time=abs_end - line.start_time,
            duration=abs_end - abs_start, parent_syl=parent_syl, parent_word=parent_word, sylchar=sylchar)

    def __getattr__(self, name: str):
        return getattr(self.__dict__["_obj"], name)

    def __repr__(self):
        return "Unit(%s %s-%s)" % (self.kind, self.abs_start, self.abs_end)


def units(line: Any, kind: str = "char", noblank: bool = True) -> Iterator[Unit]:
    """Itera las palabras ("word"), silabas ("syl") o caracteres ("char") de la linea
    (equivale a `template word|syl|char [noblank]`)."""
    ls = line.start_time
    syls = line.syls
    words = list(getattr(line, "words", []) or [])
    syln, wn = len(syls), max(1, len(words))

    def word_times(idx: Any):
        if isinstance(idx, int) and 1 <= idx <= len(words):
            w = words[idx - 1]
            return ls + w.start_time, ls + w.end_time, idx
        return None, None, 1

    def word_unit(i: int) -> Optional[Unit]:
        if not (1 <= i <= len(words)):
            return None
        w = words[i - 1]
        a, b = ls + w.start_time, ls + w.end_time
        return Unit(w, line, a, b, a, b, 1, syln, a, b, i, wn, "word")

    if kind == "word":
        for i, w in enumerate(words, 1):
            if noblank and getattr(w, "is_blank", False):
                continue
            ws, we = ls + w.start_time, ls + w.end_time
            yield Unit(w, line, ws, we, ws, we, 1, syln, ws, we, i, wn, "word")
        return
    for si, syl in enumerate(syls, 1):
        ss, se = ls + syl.start_time, ls + syl.end_time
        ws, we, wi = word_times(getattr(syl, "word", None))
        pword = word_unit(wi)
        if kind == "syl":
            if noblank and getattr(syl, "is_blank", False):
                continue
            yield Unit(syl, line, ss, se, ss, se, si, syln, ws, we, wi, wn, "syl", parent_word=pword)
            continue
        psyl = Unit(syl, line, ss, se, ss, se, si, syln, ws, we, wi, wn, "syl", parent_word=pword)
        visible = [ch for ch in syl.chars if not ch.is_blank]
        n_vis, dur_syl, k = len(visible), se - ss, 0
        for ch in syl.chars:
            if ch.is_blank:
                if noblank:
                    continue
                a, b = ss + ch.start_time, ss + ch.end_time              # un espacio conserva su tiempo
                sc = SimpleNamespace(i=k, n=n_vis, start_time=ch.start_time, mid_time=(ch.start_time + ch.end_time) / 2,
                                     end_time=ch.end_time)
            else:
                k += 1
                rel_a, rel_b = dur_syl * (k - 1) / n_vis, dur_syl * k / n_vis      # reparto igual (Effector-3.6.lua)
                a, b = ss + rel_a, ss + rel_b
                sc = SimpleNamespace(i=k, n=n_vis, start_time=rel_a, mid_time=(rel_a + rel_b) / 2, end_time=rel_b)
            yield Unit(ch, line, a, b, ss, se, si, syln, ws, we, wi, wn, "char", parent_syl=psyl, parent_word=pword,
                       sylchar=sc)


class Fx(object):
    """El objeto `fx` de las expresiones de Kara Effector para una unidad: texto, posicion, medidas y estado.

    pos_x / pos_y: punto base del efecto (por defecto el centro de la unidad); pos_l/pos_r/pos_t/pos_b: sus bordes
    (como en Effector: pos_l = pos_x - ancho/2, pos_t = pos_y - alto/2). move_*1..4: posiciones del movimiento (sin
    "time move" valen las de pos). loop_v/loop_h/loop_3: bucles; start_time/end_time/dur: tiempo de la linea de efecto
    (los fija el codigo generado tras `retime`). El resto (`center`, `middle`, `left`, `width`, `i`, `n`...) se delega
    en la unidad."""

    def __init__(self, unit: Any, pos_x: Optional[float] = None, pos_y: Optional[float] = None):
        d = self.__dict__
        d["_u"] = unit
        px = unit.center if pos_x is None else pos_x
        py = unit.middle if pos_y is None else pos_y
        w, h = unit.width, unit.height
        d["pos_x"], d["pos_y"] = px, py
        d["x"], d["y"] = px, py
        d["pos_l"], d["pos_r"], d["pos_t"], d["pos_b"] = px - w / 2, px + w / 2, py - h / 2, py + h / 2
        d["text"] = getattr(unit, "text_stripped", "")
        d["loop_v"] = d["loop_h"] = d["loop_3"] = d["maxloop_fx"] = 1
        d["start_time"] = d["end_time"] = d["dur"] = 0
        for n in (1, 2, 3, 4):
            d["move_x%d" % n], d["move_y%d" % n] = px, py
            d["move_l%d" % n], d["move_r%d" % n] = px - w / 2, px + w / 2
            d["move_t%d" % n], d["move_b%d" % n] = py - h / 2, py + h / 2

    def __getattr__(self, name: str):
        return getattr(self.__dict__["_u"], name)

    def __setattr__(self, name: str, value: Any):
        self.__dict__[name] = value

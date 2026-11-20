# -*- coding: utf-8 -*-
# Port de `ke.shape.clipper` (newkara_library.lua de Effector).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver domain/services/ke_common.py.

"""Adaptador de `IShapeBooleanEngine` basado en pyclipper (sustituye al clipper.lua del original)."""

from __future__ import annotations

from typing import Any, List

from ..engine.geometry import clipper_engine as _ce
from ...domain.repositories.i_shape_boolean_engine import FILL_TYPES, OPERATIONS, IShapeBooleanEngine
from ...domain.services.ke_shape import Shape

SCALE_PATHS = 1000  # factor de escala de los poligonos (el clipper trabaja con enteros)


class ShapeBooleanAdapter(IShapeBooleanEngine):
    """Union, interseccion, diferencia y XOR de formas ASS (las curvas se aplanan a tramos de 2 px)."""

    def __init__(self, curve_step: float = 2):
        self._step = curve_step

    @staticmethod
    def _pyclipper():
        pc = getattr(_ce, "pyclipper", None)
        if pc is None:
            raise RuntimeError("pyclipper no esta instalado (pip install pyclipper)")
        return pc

    def to_paths(self, shape: Any) -> List[List[List[int]]]:
        """Subformas -> caminos de enteros (x, y escalados por SCALE_PATHS)."""
        shp = (shape if isinstance(shape, Shape) else Shape(shape)).redraw(self._step, "bezier")
        paths = []
        for sub in shp.subshapes():
            paths.append([[int(round(x * SCALE_PATHS)), int(round(y * SCALE_PATHS))] for x, y in sub._coords()])
        return paths

    @staticmethod
    def to_shape(paths: List[List[List[int]]]) -> Shape:
        codes = []
        for path in paths:
            if not path:
                continue
            pts = ["%s %s" % (_num(x / SCALE_PATHS), _num(y / SCALE_PATHS)) for x, y in path]
            codes.append("m " + pts[0] + " " + "".join("l %s " % p for p in pts[1:]))
        return Shape("".join(codes)).closed()

    def boolean(self, subject: Any, clip: Any, operation: str = "union", filltype: str = "evenodd") -> Shape:
        pc = self._pyclipper()
        op = {"intersection": pc.CT_INTERSECTION, "union": pc.CT_UNION,
              "difference": pc.CT_DIFFERENCE, "xor": pc.CT_XOR}[operation if operation in OPERATIONS else "union"]
        fill = {"evenodd": pc.PFT_EVENODD, "nonzero": pc.PFT_NONZERO, "positive": pc.PFT_POSITIVE,
                "negative": pc.PFT_NEGATIVE}[filltype if filltype in FILL_TYPES else "evenodd"]
        engine = pc.Pyclipper()
        engine.AddPaths(self.to_paths(subject), pc.PT_SUBJECT, True)
        engine.AddPaths(self.to_paths(clip), pc.PT_CLIP, True)
        return self.to_shape(engine.Execute(op, fill, fill))


def _num(v: float) -> str:
    v = round(v, 3)
    return str(int(v)) if v == int(v) else str(v)

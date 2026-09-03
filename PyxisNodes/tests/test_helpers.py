# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any question you can visit: https://discord.gg/rYsARc3fB9

"""Utilidades y fixtures compartidos para la suite de pruebas de Pyxis Nodes."""

import os
import sys
import unittest
from typing import Any, Dict, List, Optional

# Garantizar que PyxisNodes este en sys.path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PYXIS_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, ".."))
if _PYXIS_DIR not in sys.path:
    sys.path.insert(0, _PYXIS_DIR)

from models import PyxisLine, PyxisUnit


class PyxisTestCase(unittest.TestCase):
    """Clase base estandarizada para pruebas unitarias en Pyxis Node Engine."""

    def setUp(self):
        super().setUp()
        self.sample_line = self.create_sample_line(
            text="Hello Pyxis Karaoke",
            start_time=0,
            end_time=2000,
            style_name="Default"
        )
        self.sample_syl = self.create_sample_syl(
            text="Hello",
            dur=1000,
            start_time=0,
            end_time=1000,
            i=1,
            n=2,
            center=640.0,
            middle=360.0
        )
        self.sample_line.syls = [self.sample_syl]
        self.context = self.create_dummy_context(self.sample_line, self.sample_syl)

    @staticmethod
    def create_sample_line(
        text: str = "Test Line",
        start_time: int = 0,
        end_time: int = 5000,
        style_name: str = "Default",
        layer: int = 0,
        is_selected: bool = True
    ) -> PyxisLine:
        """Crea una instancia controlada de PyxisLine para pruebas."""
        line = PyxisLine()
        line.layer = layer
        line.start_time = start_time
        line.end_time = end_time
        line.style_name = style_name
        line.text = text
        line.is_selected = is_selected
        line.actor = ""
        line.effect = ""
        line.margin_l = 0
        line.margin_r = 0
        line.margin_v = 0
        line.syls = []
        return line

    @staticmethod
    def create_sample_syl(
        text: str = "Test",
        dur: int = 1000,
        start_time: int = 0,
        end_time: int = 1000,
        i: int = 1,
        n: int = 1,
        center: float = 640.0,
        middle: float = 360.0,
        left: float = 600.0,
        right: float = 680.0,
        top: float = 340.0,
        bottom: float = 380.0,
        width: float = 80.0,
        height: float = 40.0
    ) -> PyxisUnit:
        """Crea una instancia controlada de PyxisUnit para pruebas de silabas o palabras."""
        syl = PyxisUnit()
        syl.text = text
        syl.text_stripped = text
        syl.duration = dur
        syl.dur = dur
        syl.start_time = start_time
        syl.end_time = end_time
        syl.i = i
        syl.n = n
        syl.center = center
        syl.middle = middle
        syl.left = left
        syl.right = right
        syl.top = top
        syl.bottom = bottom
        syl.width = width
        syl.height = height
        syl.tag = "k"
        return syl

    @staticmethod
    def create_dummy_context(
        line: Optional[PyxisLine] = None,
        syl: Optional[PyxisUnit] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Genera un diccionario de contexto de evaluacion tipico de GraphEngine."""
        ctx: Dict[str, Any] = {
            "line": line,
            "syl": syl,
            "start_time": syl.start_time if syl else (line.start_time if line else 0.0),
            "end_time": syl.end_time if syl else (line.end_time if line else 1000.0),
            "duration": syl.dur if syl else 1000.0,
            "var_store": {},
            "res_x": 1280,
            "res_y": 720,
        }
        if extra:
            ctx.update(extra)
        return ctx

    def assertAssTagPresent(self, ass_string: str, tag_prefix: str, msg: Optional[str] = None):
        """Verifica que un tag ASS especifico (ej: '\\fscx', '\\pos') este presente en la cadena."""
        self.assertIn(tag_prefix, ass_string, msg or f"Tag '{tag_prefix}' no encontrado en: {ass_string}")

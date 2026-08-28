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

# tests/test_sys_var.py
"""Pruebas unitarias completas para el nodo maestro Sys Var de PyxisNodes."""

import unittest
from models import PyxisLine, PyxisUnit, StyleRef
from node_engine import GraphEngine, _eval_sys_var


class TestSysVarEval(unittest.TestCase):
    def setUp(self):
        self.engine = GraphEngine({"nodes": [], "links": []})
        
        # Simular línea y unidad activas
        self.line = PyxisLine()
        self.line.text_stripped = "Karaoke Test Line"
        self.line.raw_text = "{\\k50}Karaoke Test Line"
        self.line.start_time = 1000
        self.line.end_time = 5000
        self.line.duration = 4000
        self.line.style_name = "TitleStyle"
        
        # Simular estilos en la línea
        style_dict = {
            "Fontname": "Trebuchet MS",
            "Fontsize": "48",
            "PrimaryColour": "&H0000FFFF&", # Amarillo ASS
            "SecondaryColour": "&H000000FF&",
            "OutlineColour": "&H00000000&",
            "BackColour": "&H00000000&",
            "Outline": "3.5",
            "Shadow": "1.5"
        }
        self.line.styleref = StyleRef(style_dict)

        self.syl = PyxisUnit()
        self.syl.text_stripped = "Ka"
        self.syl.start_time = 1000
        self.syl.end_time = 1500
        self.syl.duration = 500
        self.syl.i = 1
        self.syl.n = 5
        self.syl.x = 240.0
        self.syl.y = 360.0
        self.syl.line = self.line

        self.context = {
            'active_unit': self.syl,
            'active_line': self.line,
            'syl': self.syl,
            'line': self.line,
            'fx_start_time': 1050,
            'fx_end_time': 1450,
            'fx_dur': 400,
            'fx_pos_x': 245.5,
            'fx_pos_y': 365.2,
            'frame_dur': 41.708,
            'ratio': 0.75,
            'module': 0.5,
            'res_x': 1920,
            'res_y': 1080
        }

    def test_eval_sys_var_line_and_alias_l(self):
        # Texto y tiempos
        self.assertEqual(_eval_sys_var("line.text", self.context), "Karaoke Test Line")
        self.assertEqual(_eval_sys_var("l.text", self.context), "Karaoke Test Line")
        self.assertEqual(_eval_sys_var("l.start_time", self.context), 1000)
        self.assertEqual(_eval_sys_var("l.end_time", self.context), 5000)
        self.assertEqual(_eval_sys_var("l.dur", self.context), 4000)
        self.assertEqual(_eval_sys_var("l.duration", self.context), 4000)
        self.assertEqual(_eval_sys_var("l.mid_time", self.context), 3000.0)
        self.assertEqual(_eval_sys_var("line.mid_time", self.context), 3000.0)

        # Estilo y propiedades
        self.assertEqual(_eval_sys_var("l.style", self.context), "TitleStyle")
        self.assertEqual(_eval_sys_var("line.style", self.context), "TitleStyle")
        self.assertEqual(_eval_sys_var("l.color1", self.context), "&H0000FFFF&")
        self.assertEqual(_eval_sys_var("l.outline", self.context), 3.5)
        self.assertEqual(_eval_sys_var("l.shadow", self.context), 1.5)

    def test_eval_sys_var_syl(self):
        self.assertEqual(_eval_sys_var("syl.text", self.context), "Ka")
        self.assertEqual(_eval_sys_var("syl.start_time", self.context), 1000)
        self.assertEqual(_eval_sys_var("syl.end_time", self.context), 1500)
        self.assertEqual(_eval_sys_var("syl.dur", self.context), 500)
        self.assertEqual(_eval_sys_var("syl.mid_time", self.context), 1250.0)

    def test_eval_sys_var_fx(self):
        self.assertEqual(_eval_sys_var("fx.start_time", self.context), 1050)
        self.assertEqual(_eval_sys_var("fx.end_time", self.context), 1450)
        self.assertEqual(_eval_sys_var("fx.dur", self.context), 400)
        self.assertEqual(_eval_sys_var("fx.pos_x", self.context), 245.5)
        self.assertEqual(_eval_sys_var("fx.pos_y", self.context), 365.2)

    def test_eval_sys_var_global_and_meta(self):
        self.assertEqual(_eval_sys_var("frame_dur", self.context), 41.708)
        self.assertEqual(_eval_sys_var("ratio", self.context), 0.75)
        self.assertEqual(_eval_sys_var("meta.res_x", self.context), 1920)
        self.assertEqual(_eval_sys_var("meta.res_y", self.context), 1080)

    def test_graph_engine_sys_var_evaluation(self):
        # Crear circuito de prueba GraphEngine con nodo Sys Var
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Variables/Sys Var",
                    "properties": { "var_name": "l.mid_time" }
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph_data)
        res = engine.evaluate_data_node(1, self.context)
        self.assertEqual(res, "3000.0")


if __name__ == '__main__':
    unittest.main()

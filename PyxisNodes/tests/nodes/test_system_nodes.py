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

"""Pruebas unitarias para nodos del sistema (Sys Var, Code Node, Dynamic Nodes y Registro)."""

import unittest
from decorators import NODE_REGISTRY
from models import PyxisLine, PyxisUnit, StyleRef
from node_engine import GraphEngine, _eval_sys_var
from nodes.code_nodes import execute_python_script, execute_lua_script, code_script_master


class TestSysVarEval(unittest.TestCase):
    """Pruebas del evaluador de variables de sistema (Sys Var)."""

    def setUp(self):
        self.engine = GraphEngine({"nodes": [], "links": []})
        self.line = PyxisLine()
        self.line.text_stripped = "Karaoke Test Line"
        self.line.raw_text = r"{\k50}Karaoke Test Line"
        self.line.start_time = 1000
        self.line.end_time = 5000
        self.line.duration = 4000
        self.line.style_name = "TitleStyle"

        style_dict = {
            "Fontname": "Trebuchet MS",
            "Fontsize": "48",
            "PrimaryColour": "&H0000FFFF&",
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
            "active_unit": self.syl,
            "syl": self.syl,
            "active_line": self.line,
            "line": self.line,
            "start_time": 1000,
            "end_time": 1500,
            "duration": 500,
            "fx_start_time": 1050,
            "fx_end_time": 1450,
            "fx_dur": 400,
            "fx_pos_x": 245.5,
            "fx_pos_y": 365.2,
            "i": 1,
            "n": 5
        }

    def test_syl_variables(self):
        self.assertEqual(_eval_sys_var("syl.i", self.context), 1)
        self.assertEqual(_eval_sys_var("syl.n", self.context), 5)
        self.assertEqual(_eval_sys_var("syl.dur", self.context), 500)
        self.assertEqual(_eval_sys_var("syl.text", self.context), "Ka")

    def test_line_variables(self):
        self.assertEqual(_eval_sys_var("line.duration", self.context), 4000)
        self.assertEqual(_eval_sys_var("line.style", self.context), "TitleStyle")

    def test_fx_variables(self):
        self.assertEqual(_eval_sys_var("fx.dur", self.context), 400)
        self.assertEqual(_eval_sys_var("fx.pos_x", self.context), 245.5)


class TestCodeNodes(unittest.TestCase):
    """Pruebas de ejecucion de scripts Python embebidos en el nodo Code."""

    def setUp(self):
        self.context = {
            "syl": type("Syl", (), {
                "i": 1,
                "n": 2,
                "text": "World",
                "text_stripped": "World",
                "duration": 500,
                "dur": 500,
                "start_time": 0,
                "end_time": 500,
                "x": 100.0,
                "y": 200.0,
                "center": 100.0,
                "middle": 200.0
            })(),
            "line": type("Line", (), {
                "layer": 0,
                "style_name": "Default",
                "text": "Hello World"
            })(),
            "rx": 1280,
            "ry": 720,
            "fd": 41.708
        }

    def test_python_script_execution_basic(self):
        script = "result = 'Hello ' + syl.text"
        res = execute_python_script(self.context, script, {})
        self.assertEqual(res, "Hello World")

    def test_python_print_and_single_expressions(self):
        res_print = execute_python_script(self.context, "print(syl.i)", {})
        self.assertEqual(res_print, "")

        res_expr = execute_python_script(self.context, "syl.x * 2", {})
        self.assertEqual(float(res_expr), 200.0)


class TestGhostNodeRegistry(unittest.TestCase):
    """Pruebas de integridad del registro global de nodos."""

    def test_registry_populated(self):
        self.assertGreater(len(NODE_REGISTRY), 20)

    def test_essential_categories_present(self):
        categories = {k.split("/")[0] for k in NODE_REGISTRY.keys() if "/" in k}
        for cat in ["Shape", "Text", "Time", "Functions", "Variables"]:
            self.assertIn(cat, categories, f"Categoria '{cat}' no encontrada en el registro")


if __name__ == "__main__":
    unittest.main()

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

"""Pruebas unitarias para MultiTag, alias l.width/l.height de line y objeto fx (fx.pos_x, fx.pos_y)."""

import unittest
from models import PyxisLine, PyxisUnit
from node_engine import GraphEngine, _eval_num_expr, FxContext
from nodes.tag_nodes import tag_master
from nodes.code_nodes import execute_python_script, execute_lua_script


class TestMultiTagEval(unittest.TestCase):

    def setUp(self):
        self.line = PyxisLine()
        self.line.width = 300.0
        self.line.height = 50.0
        self.line.center = 640.0
        self.line.middle = 360.0

        self.unit = PyxisUnit()
        self.unit.line = self.line
        self.unit.center = 640.0
        self.unit.middle = 360.0

        self.context = {
            'active_unit': self.unit,
            'line': self.line,
            'l': self.line,
            'fx_pos_x': 640.0,
            'fx_pos_y': 360.0
        }
        self.context['fx'] = FxContext(self.context)

    def test_eval_num_expr_with_fx_and_line(self):
        """Verifica la evaluación matemática de fx.pos_x-0.5*line.width y fx.pos_y-0.5*line.height."""
        res_x = _eval_num_expr('fx.pos_x-0.5*line.width', context=self.context)
        res_y = _eval_num_expr('fx.pos_y-0.5*line.height', context=self.context)
        self.assertEqual(res_x, 490.0)  # 640 - 150
        self.assertEqual(res_y, 335.0)  # 360 - 25

    def test_eval_num_expr_with_fx_and_l_alias(self):
        """Verifica la evaluación matemática de fx.pos_x-0.5*l.width y fx.pos_y-0.5*l.height."""
        res_x = _eval_num_expr('fx.pos_x-0.5*l.width', context=self.context)
        res_y = _eval_num_expr('fx.pos_y-0.5*l.height', context=self.context)
        self.assertEqual(res_x, 490.0)
        self.assertEqual(res_y, 335.0)

    def test_multitag_pos_evaluation(self):
        """Verifica que tag_master (MultiTag pos) evalúe expresiones complejas con line y l."""
        tag_line = tag_master(self.context, tag_type="pos", x="fx.pos_x-0.5*line.width", y="fx.pos_y-0.5*line.height")
        self.assertEqual(tag_line, r"\pos(490,335)")

        tag_l = tag_master(self.context, tag_type="pos", x="fx.pos_x-0.5*l.width", y="fx.pos_y-0.5*l.height")
        self.assertEqual(tag_l, r"\pos(490,335)")

    def test_code_nodes_python_and_lua(self):
        """Verifica execute_python_script y execute_lua_script con l y fx."""
        script_py = "result = str(fx.pos_x - 0.5 * l.width)"
        res_py = execute_python_script(self.context, script_py, {})
        self.assertEqual(res_py, "490.0")

        script_lua = "return tostring(fx.pos_x - 0.5 * l.width)"
        res_lua = execute_lua_script(self.context, script_lua, {})
        if "lupa" in res_lua:
            # Lupa es opcional en Python embebido
            pass
        else:
            self.assertEqual(res_lua, "490.0")

    def test_graph_engine_multitag_circuit(self):
        """Verifica el flujo completo en GraphEngine para MultiTag."""
        graph_data = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"iterador": "line", "noblank": "No Blank"}, "outputs": [{"name": "Loop", "links": [101]}]},
                {
                    "id": 2,
                    "type": "MultiTag",
                    "properties": {"tag_type": "pos", "x": "fx.pos_x-0.5*line.width", "y": "fx.pos_y-0.5*l.height"},
                    "inputs": [{"name": "Loop", "link": 101}],
                    "outputs": [{"name": "String", "links": [102]}]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 101},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": 102},
                        {"name": "Return", "link": None}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 2, 0, "Loop"],
                [102, 2, 0, 3, 4, "String"]
            ]
        }

        engine = GraphEngine(graph_data, 1280, 720, 41.708)
        dialogues = [{
            "raw": "Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Test Line",
            "metrics": {
                "h": 50, "d": 0, "e": 0, "sel": True, "rw": 300, "l": 490, "c": 640, "r": 790, "t": 335, "m": 360, "b": 385,
                "syl_lefts": [490], "syl_centers": [640], "syl_rights": [790], "syl_widths": [300],
                "syl_starts": [0], "syl_ends": [5000], "w": [300]
            }
        }]
        styles = {"Default": {}}

        lines = engine.process(dialogues, styles)
        self.assertTrue(len(lines) > 0)
        self.assertIn(r"\pos(575.56,", lines[0])


if __name__ == "__main__":
    unittest.main()

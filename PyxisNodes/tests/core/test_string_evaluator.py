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

"""Pruebas unitarias para evaluacion de plantillas de strings, interpolador de tags ASS y expresiones."""

import unittest
from node_engine import GraphEngine, _eval_num_expr
from string_evaluator import eval_string_template


class TestStringEvaluator(unittest.TestCase):
    """Pruebas para el evaluador de expresiones de texto y tags ASS."""

    def setUp(self):
        self.context = {
            "syl": type("Syl", (), {
                "center": 150.0,
                "middle": 70.0,
                "dur": 400.0,
                "i": 1,
                "n": 3
            })(),
            "line": type("Line", (), {
                "color1": "&HFFFFFF&",
                "dur": 2000.0
            })(),
            "fd": 40.0
        }

    def test_basic_arithmetic_expressions(self):
        res = _eval_num_expr("10 + 20 * 2", self.context)
        self.assertEqual(res, 50.0)

    def test_context_variable_expressions(self):
        res = _eval_num_expr("syl.center + 10", self.context)
        self.assertEqual(res, 160.0)

    def test_template_evaluation(self):
        raw = r"{\an5\pos(syl.center + 10, syl.middle)\fscxy(150)}"
        res = eval_string_template(raw, self.context)
        self.assertEqual(res, r"{\an5\pos(160, 70)\fscx150\fscy150}")

    def test_stochastic_tags(self):
        raw = r"\frzR(-30, 30)\1cR()"
        res = eval_string_template(raw, self.context)
        self.assertIn(r"\frz", res)
        self.assertIn(r"\1c&H", res)


class TestInterpolatorNode(unittest.TestCase):
    """Pruebas de interpolacion lineal y acelerada de tags ASS numericos y alfa."""

    def test_interpolator_alpha_tags(self):
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Interpolator",
                    "properties": {
                        "iterador": "5",
                        "total": "9",
                        "accel": "1.0",
                        "v1": "&H00&",
                        "v2": "&HFF&"
                    },
                    "inputs": [
                        {"name": "Iterador"},
                        {"name": "Total"},
                        {"name": "Accel"},
                        {"name": "v1", "value": "&H00&"},
                        {"name": "v2", "value": "&HFF&"}
                    ]
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {})
        self.assertEqual(res, "&H80&")

    def test_interpolator_numeric_tags(self):
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Interpolator",
                    "properties": {
                        "iterador": "5",
                        "total": "9",
                        "accel": "1.0",
                        "v1": "100",
                        "v2": "200"
                    },
                    "inputs": [
                        {"name": "Iterador"},
                        {"name": "Total"},
                        {"name": "Accel"},
                        {"name": "v1", "value": "100"},
                        {"name": "v2", "value": "200"}
                    ]
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {})
        self.assertEqual(res, "150")


if __name__ == "__main__":
    unittest.main()

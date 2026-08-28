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

# PyxisNodes/tests/test_time_nodes_v098.py
"""Pruebas unitarias para la Etapa 1 de PyxisNodes v0.9.8: Nodos de Tiempo (Effector 2 ke.time)."""

import unittest
from models import PyxisUnit
from nodes.time_nodes import (
    time_lead_in, time_lead_out, time_middle_1, time_middle_2,
    time_loop_1, time_loop_2, time_ipol
)


def _make_test_unit(i, n, start_time, end_time, dur, text="A"):
    u = PyxisUnit()
    u.i, u.n = i, n
    u.start_time, u.end_time, u.dur = start_time, end_time, dur
    u.text, u.text_stripped = text, text
    return u


class TestTimeNodesStage1(unittest.TestCase):

    def setUp(self):
        self.unit1 = _make_test_unit(i=1, n=4, start_time=1000, end_time=2000, dur=1000, text="A")
        self.unit2 = _make_test_unit(i=2, n=4, start_time=1200, end_time=2200, dur=1000, text="B")
        self.unit3 = _make_test_unit(i=3, n=4, start_time=1400, end_time=2400, dur=1000, text="C")
        self.unit4 = _make_test_unit(i=4, n=4, start_time=1600, end_time=2600, dur=1000, text="D")

        self.ctx1 = {'active_unit': self.unit1, 'fx_i': 1, 'fx_n': 3, 'J': 1, 'maxJ': 2}
        self.ctx2 = {'active_unit': self.unit2, 'fx_i': 2, 'fx_n': 3, 'J': 2, 'maxJ': 2}
        self.ctx4 = {'active_unit': self.unit4, 'fx_i': 3, 'fx_n': 3, 'J': 2, 'maxJ': 2}

    def test_lead_in(self):
        # i = 1: 40 * (1 - 1) - 200 = -200
        self.assertEqual(time_lead_in(self.ctx1, delay=40), -200.0)
        # i = 2: 40 * (2 - 1) - 200 = -160
        self.assertEqual(time_lead_in(self.ctx2, delay=40), -160.0)
        # i = 4: 40 * (4 - 1) - 200 = -80
        self.assertEqual(time_lead_in(self.ctx4, delay=40), -80.0)

    def test_lead_out(self):
        # i = 1, n = 4: 40 * (1 - 4 - 1) + 200 = 40 * (-4) + 200 = 40
        self.assertEqual(time_lead_out(self.ctx1, delay=40), 40.0)
        # i = 4, n = 4: 40 * (4 - 4 - 1) + 200 = 40 * (-1) + 200 = 160
        self.assertEqual(time_lead_out(self.ctx4, delay=40), 160.0)

    def test_middle_1(self):
        # i = 1 <= 2.5: 30 * (1 - 1) - 200 = -200
        self.assertEqual(time_middle_1(self.ctx1, delay=30), -200.0)
        # i = 2 <= 2.5: 30 * (2 - 1) - 200 = -170
        self.assertEqual(time_middle_1(self.ctx2, delay=30), -170.0)
        # i = 4 > 2.5: 30 * (4 - 4 + 0.5) - 200 = 15 - 200 = -185
        self.assertEqual(time_middle_1(self.ctx4, delay=30), -185.0)

    def test_middle_2(self):
        # i = 1 < 2.5: 30 * (-1 + 0.5) - 200 = -15 - 200 = -215
        self.assertEqual(time_middle_2(self.ctx1, delay=30), -215.0)
        # i = 4 >= 2.5: 30 * (4 - 4 - 1) - 200 = -30 - 200 = -230
        self.assertEqual(time_middle_2(self.ctx4, delay=30), -230.0)

    def test_loop_1(self):
        # fx_i = 1, fx_n = 3, mode = leadin: 30 * (1 - 1) - 200 = -200
        self.assertEqual(time_loop_1(self.ctx1, delay=30, mode="leadin"), -200.0)
        # fx_i = 2, fx_n = 3, mode = leadin: 30 * (2 - 1) - 200 = -170
        self.assertEqual(time_loop_1(self.ctx2, delay=30, mode="leadin"), -170.0)
        # fx_i = 3, fx_n = 3, mode = leadout: 30 * (3 - 3 - 1) + 200 = 170
        self.assertEqual(time_loop_1(self.ctx4, delay=30, mode="leadout"), 170.0)

    def test_loop_2(self):
        # J = 1, maxJ = 2, mode = leadin: 30 * (1 - 1) - 200 = -200
        self.assertEqual(time_loop_2(self.ctx1, delay=30, mode="leadin"), -200.0)
        # J = 2, maxJ = 2, mode = leadin: 30 * (2 - 1) - 200 = -170
        self.assertEqual(time_loop_2(self.ctx2, delay=30, mode="leadin"), -170.0)

    def test_ipol(self):
        res = time_ipol(self.ctx1, dur=1000, points="0, 50, 100", accel=1.0)
        self.assertIn("[0.0, 500.0]", res)
        self.assertIn("[500.0, 1000.0]", res)

    def test_expression_evaluation(self):
        # Probar evaluación de expresiones en casillas de texto
        ctx = dict(self.ctx1)
        res = time_lead_in(ctx, delay="20 * 2")
        self.assertEqual(res, -200.0)

    def test_salida_expressions(self):
        from node_engine import _to_int_or_default
        ctx = dict(self.ctx1)
        ctx['start_time'] = 12500.0
        ctx['line_start_time'] = 12500.0
        ctx['line'] = self.unit1
        # Probar evaluación de start_time + time_lead_in(40) en Salida
        st = _to_int_or_default("start_time + time_lead_in(40)", 1000, context=ctx)
        self.assertEqual(st, 12300)

        # Probar evaluación con alias line_start_time
        st_alias = _to_int_or_default("line_start_time + time_lead_in(40)", 1000, context=ctx)
        self.assertEqual(st_alias, 12300)

    def test_variable_inputs_in_graph(self):
        from node_engine import GraphEngine
        graph_data = {
            "nodes": [
                {
                    "id": 1, "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl"},
                    "inputs": []
                },
                {
                    "id": 2, "type": "Variables/Define Vars",
                    "properties": {"variables": "mi_inicio = start_time + time_lead_in(40)\nmi_fin = end_time + time_lead_out(40)"},
                    "inputs": [{"name": "In", "link": 1}]
                },
                {
                    "id": 3, "type": "Variables/Get Var",
                    "properties": {"var_name": "mi_inicio"},
                    "inputs": []
                },
                {
                    "id": 4, "type": "Variables/Get Var",
                    "properties": {"var_name": "mi_fin"},
                    "inputs": []
                },
                {
                    "id": 5, "type": "System/Output",
                    "properties": {"apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 2},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": 3},
                        {"name": "End Time", "link": 4}
                    ]
                }
            ],
            "links": [
                [1, 1, 0, 2, 0, "bucle"],
                [2, 2, 0, 5, 0, "bucle"],
                [3, 3, 0, 5, 2, "data"],
                [4, 4, 0, 5, 3, "data"]
            ]
        }
        engine = GraphEngine(graph_data)
        raw_dialogue = "Dialogue: 0,0:00:10.00,0:00:15.00,Default,,0,0,0,,{\\k50}H"
        item = {"raw": raw_dialogue, "selected": True}
        lines = engine.process([item], {"Default": {}})
        self.assertGreater(len(lines), 0)
        # start_time = 10000 + (40*(1-1)-200) = 9800 -> 0:00:09.80
        # end_time (syl) = 10500 + (40*(1-1-1)+200) = 10500 + 160 = 10660 -> 0:00:10.66
        self.assertTrue("9.80" in str(lines[0]) or "9800" in str(lines[0]))
        self.assertTrue("10.66" in str(lines[0]) or "10660" in str(lines[0]))

    def test_implicit_variable_start_end_time_in_graph(self):
        from node_engine import GraphEngine
        graph_data = {
            "nodes": [
                {
                    "id": 1, "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl"},
                    "inputs": []
                },
                {
                    "id": 2, "type": "Variables/Define Vars",
                    "properties": {"variables": "start_time = line_start_time + time_lead_in(40)\nend_time = line_end_time + time_lead_out(40)"},
                    "inputs": [{"name": "In", "link": 1}]
                },
                {
                    "id": 3, "type": "System/Output",
                    "properties": {"apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 2},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None}
                    ]
                }
            ],
            "links": [
                [1, 1, 0, 2, 0, "bucle"],
                [2, 2, 0, 3, 0, "bucle"]
            ]
        }
        engine = GraphEngine(graph_data)
        raw_dialogue = "Dialogue: 0,0:00:10.00,0:00:15.00,Default,,0,0,0,,{\\k50}H"
        item = {"raw": raw_dialogue, "selected": True}
        lines = engine.process([item], {"Default": {}})
        self.assertGreater(len(lines), 0)
        # start_time = 10000 + (40*(1-1)-200) = 9800 -> 0:00:09.80
        # end_time = 15000 + (40*(1-1-1)+200) = 15000 + 160 = 15160 -> 0:00:15.16
        self.assertTrue("9.80" in str(lines[0]) or "9800" in str(lines[0]))
        self.assertTrue("15.16" in str(lines[0]) or "15160" in str(lines[0]))


if __name__ == '__main__':
    unittest.main()

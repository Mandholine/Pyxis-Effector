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

"""Unit tests for Loops category nodes (Main Loop, MaxLoop, Module)."""

import unittest
from decorators import NODE_REGISTRY, SYSTEM_NODE_DB
from models import PyxisLine, PyxisUnit
from node_engine import GraphEngine
from nodes.loop_nodes import main_loop_node, max_loop_node, module_node


class TestLoopNodesDirect(unittest.TestCase):
    """Direct execution tests for loop functions."""

    def setUp(self):
        self.line = PyxisLine()
        self.line.text_stripped = "Hello World"
        self.line.start_time = 1000
        self.line.end_time = 3000

        self.syl = PyxisUnit()
        self.syl.text_stripped = "Hello"
        self.syl.i = 2
        self.syl.n = 5
        self.syl.line = self.line

        self.context = {
            "active_unit": self.syl,
            "syl": self.syl,
            "active_line": self.line,
            "line": self.line,
            "i": 2,
            "n": 5,
            "j": 3,
            "maxj": 10
        }

    def test_main_loop_node(self):
        res = main_loop_node(self.context)
        self.assertEqual(res, "2")

    def test_max_loop_node(self):
        res = max_loop_node(self.context, var_name="j")
        self.assertEqual(res, "3")

    def test_module_node_basic(self):
        # i=1, N=5, m=0 -> (1-1+0)/(5-1) = 0/4 = 0
        res = module_node(self.context, in_i="1", in_n="5", in_m="0")
        self.assertEqual(res, "0")

        # i=5, N=5, m=0 -> (5-1+0)/(5-1) = 4/4 = 1
        res = module_node(self.context, in_i="5", in_n="5", in_m="0")
        self.assertEqual(res, "1")

        # i=3, N=5, m=0 -> (3-1+0)/(5-1) = 2/4 = 0.5
        res = module_node(self.context, in_i="3", in_n="5", in_m="0")
        self.assertEqual(res, "0.5")

    def test_module_node_single_total(self):
        # N=1 -> returns m
        res = module_node(self.context, in_i="1", in_n="1", in_m="0.25")
        self.assertEqual(res, "0.25")


class TestLoopNodesEngine(unittest.TestCase):
    """GraphEngine integration tests for Loops nodes."""

    def test_main_loop_slots(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"iterator": "syl", "blank_mode": "no_blank"}}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        syl = PyxisUnit()
        syl.i = 3
        syl.n = 8
        ctx = {"active_unit": syl}

        # Slot 1: Iterator (i)
        res_i = engine.evaluate_data_node(1, ctx, output_slot_index=1)
        self.assertEqual(res_i, "3")

        # Slot 2: Total (N)
        res_n = engine.evaluate_data_node(1, ctx, output_slot_index=2)
        self.assertEqual(res_n, "8")

    def test_max_loop_slots(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/MaxLoop", "properties": {"mode": "normal", "iterations": "5", "var_name": "k"}}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        ctx = {"k": 2, "k_max": 5}

        # Slot 1: Counter
        res_counter = engine.evaluate_data_node(1, ctx, output_slot_index=1)
        self.assertEqual(res_counter, "2")

        # Slot 2: Total
        res_total = engine.evaluate_data_node(1, ctx, output_slot_index=2)
        self.assertEqual(res_total, "5")

    def test_module_evaluation(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Module", "properties": {"iter": "2", "total": "5", "sub_m": "0"}}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        ctx = {}
        res = engine.evaluate_data_node(1, ctx)
        # (2-1)/(5-1) = 1/4 = 0.25
        self.assertEqual(res, "0.25")

    def test_main_loop_and_output_execution(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"iterator": "syl", "blank_mode": "no_blank"}},
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 101},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": 102}
                    ]
                },
                {"id": 3, "type": "Basics/String", "properties": {"value": "syl_out"}}
            ],
            "links": [
                [101, 1, 0, 2, 0, "loop"],
                [102, 3, 0, 2, 5, "data"]
            ]
        }
        dialogues = [
            {"raw": r"Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\k50}Ka{\k50}ra", "is_selected": True}
        ]
        styles = {"Default": {}}
        engine = GraphEngine(graph)
        res = engine.process_single(dialogues, styles)
        self.assertEqual(len(res), 2)
        self.assertIn("syl_out", res[0]["text"])

    def test_maxloop_multiple_lines_order_111222333(self):
        """Verifica que con varias líneas y loops de j devuelva 111222333 en vez de 123123123."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"iterator": "line", "blank_mode": "no_blank"}},
                {"id": 2, "type": "Loops/MaxLoop", "properties": {"mode": "normal", "iterations": "3", "var_name": "j"}, "inputs": [{"name": "Loop In", "link": 101}]},
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 102},
                        {"name": "Layer", "link": 103},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": None}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 2, 0, "loop"],
                [102, 2, 0, 3, 0, "loop"],
                [103, 2, 1, 3, 1, "data"]
            ]
        }
        dialogues = [
            {"raw": "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Line1", "is_selected": True},
            {"raw": "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Line2", "is_selected": True},
            {"raw": "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Line3", "is_selected": True}
        ]
        styles = {"Default": {}}
        engine = GraphEngine(graph)
        res = engine.process(dialogues, styles, use_multiprocessing=False)
        self.assertEqual(len(res), 9)
        # Verify 111 222 333 ordering
        self.assertIn("Line1", res[0])
        self.assertIn("Line1", res[1])
        self.assertIn("Line1", res[2])
        self.assertIn("Line2", res[3])
        self.assertIn("Line2", res[4])
        self.assertIn("Line2", res[5])
        self.assertIn("Line3", res[6])
        self.assertIn("Line3", res[7])
        self.assertIn("Line3", res[8])

    def test_maxloop_multiple_lines_order_111222333_multiprocessing(self):
        """Verifica que con varias líneas y loops en multiprocessing devuelva 111222333."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"iterator": "line", "blank_mode": "no_blank"}},
                {"id": 2, "type": "Loops/MaxLoop", "properties": {"mode": "normal", "iterations": "3", "var_name": "j"}, "inputs": [{"name": "Loop In", "link": 101}]},
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 102},
                        {"name": "Layer", "link": 103},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": None}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 2, 0, "loop"],
                [102, 2, 0, 3, 0, "loop"],
                [103, 2, 1, 3, 1, "data"]
            ]
        }
        dialogues = [
            {"raw": "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Line1", "is_selected": True},
            {"raw": "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Line2", "is_selected": True},
            {"raw": "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Line3", "is_selected": True}
        ]
        styles = {"Default": {}}
        engine = GraphEngine(graph)
        res = engine.process(dialogues, styles, use_multiprocessing=True)
        self.assertEqual(len(res), 9)
        self.assertIn("Line1", res[0])
        self.assertIn("Line1", res[1])
        self.assertIn("Line1", res[2])
        self.assertIn("Line2", res[3])
        self.assertIn("Line2", res[4])
        self.assertIn("Line2", res[5])
        self.assertIn("Line3", res[6])
        self.assertIn("Line3", res[7])
        self.assertIn("Line3", res[8])

    def test_registry_and_system_db(self):
        self.assertIn("Loops/Main Loop", NODE_REGISTRY)
        self.assertIn("Loops/MaxLoop", NODE_REGISTRY)
        self.assertIn("Loops/Module", NODE_REGISTRY)

        self.assertIn("Loops", SYSTEM_NODE_DB)
        loops_defs = SYSTEM_NODE_DB["Loops"]
        self.assertIn("Main Loop", loops_defs)
        self.assertIn("MaxLoop", loops_defs)
        self.assertIn("Module", loops_defs)


if __name__ == "__main__":
    unittest.main()

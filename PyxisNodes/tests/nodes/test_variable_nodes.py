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

"""Unit tests for Variables category nodes (Sys Var, Define Vars, Get Var, Memory)."""

import unittest
from decorators import NODE_REGISTRY, SYSTEM_NODE_DB
from models import PyxisLine, PyxisUnit, StyleRef
from node_engine import GraphEngine
from nodes.variable_nodes import sys_var_node, define_vars_node, get_var_node, memory_node


class TestVariableNodesDirect(unittest.TestCase):
    """Direct execution tests for variable nodes."""

    def setUp(self):
        self.line = PyxisLine()
        self.line.text_stripped = "Hello World"
        self.line.raw_text = r"{\k50}Hello {\k50}World"
        self.line.start_time = 1000
        self.line.end_time = 3000
        self.line.duration = 2000
        self.line.style_name = "Default"

        self.syl = PyxisUnit()
        self.syl.text_stripped = "Hello"
        self.syl.text = "Hello"
        self.syl.start_time = 1000
        self.syl.end_time = 2000
        self.syl.duration = 1000
        self.syl.dur = 1000
        self.syl.i = 1
        self.syl.n = 2
        self.syl.x = 150.0
        self.syl.y = 200.0
        self.syl.line = self.line

        self.context = {
            "active_unit": self.syl,
            "syl": self.syl,
            "active_line": self.line,
            "line": self.line,
            "start_time": 1000,
            "end_time": 2000,
            "duration": 1000,
            "fx_pos_x": 155.0,
            "fx_pos_y": 205.0,
            "i": 1,
            "n": 2,
            "custom_val": "pyxis_test",
            "j": 3
        }

    def test_sys_var_node(self):
        self.assertEqual(sys_var_node(self.context, "syl.text"), "Hello")
        self.assertEqual(sys_var_node(self.context, "syl.i"), 1)
        self.assertEqual(sys_var_node(self.context, "line.duration"), 2000)
        self.assertEqual(sys_var_node(self.context, "fx.pos_x"), 155.0)

    def test_define_vars_node(self):
        res = define_vars_node(self.context, in_val="pass_through", variables="my_var=10")
        self.assertEqual(res, "pass_through")

    def test_get_var_node(self):
        self.assertEqual(get_var_node(self.context, "custom_val"), "pyxis_test")
        self.assertEqual(get_var_node(self.context, "j"), 3)
        self.assertEqual(get_var_node(self.context, "non_existent"), "")

    def test_memory_node(self):
        ctx = {}
        # Remember value
        saved = memory_node(ctx, key_in="alpha", val_in="12345", mode="remember")
        self.assertEqual(saved, "12345")
        # Retrieve value
        loaded = memory_node(ctx, key_in="alpha", mode="retrieve")
        self.assertEqual(loaded, "12345")
        # Retrieve non-existing with default
        fallback = memory_node(ctx, key_in="beta", mode="retrieve", default="def_val")
        self.assertEqual(fallback, "def_val")


class TestVariableNodesEngine(unittest.TestCase):
    """GraphEngine integration tests for Variables nodes."""

    def test_sys_var_evaluation(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Variables/Sys Var", "properties": {"var_name": "syl.text"}}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        syl = PyxisUnit()
        syl.text_stripped = "EngineTest"
        ctx = {"active_unit": syl, "syl": syl}
        res = engine.evaluate_data_node(1, ctx)
        self.assertEqual(res, "EngineTest")

    def test_get_var_evaluation(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Variables/Get Var", "properties": {"var_name": "counter"}}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        ctx = {"counter": 42}
        res = engine.evaluate_data_node(1, ctx)
        self.assertEqual(res, 42)

    def test_memory_remember_and_recall_evaluation(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Variables/Memory", "properties": {"mode": "remember", "key": "stored_pos", "value": "500"}},
                {"id": 2, "type": "Variables/Memory", "properties": {"mode": "retrieve", "key": "stored_pos", "value": "default_pos"}}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        ctx = {}
        saved = engine.evaluate_data_node(1, ctx)
        self.assertEqual(saved, "500")
        loaded = engine.evaluate_data_node(2, ctx)
        self.assertEqual(loaded, "500")

    def test_registry_and_system_db(self):
        self.assertIn("Variables/Sys Var", NODE_REGISTRY)
        self.assertIn("Variables/Define Vars", NODE_REGISTRY)
        self.assertIn("Variables/Get Var", NODE_REGISTRY)
        self.assertIn("Variables/Memory", NODE_REGISTRY)

        self.assertIn("Variables", SYSTEM_NODE_DB)
        var_defs = SYSTEM_NODE_DB["Variables"]
        self.assertIn("Sys Var", var_defs)
        self.assertIn("Define Vars", var_defs)
        self.assertIn("Get Var", var_defs)
        self.assertIn("Memory", var_defs)


if __name__ == "__main__":
    unittest.main()

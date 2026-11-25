"""Unit tests for scoped random callsite isolation and sub-loop helper cache binding."""

import sys
import os
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from node_engine import GraphEngine
from string_evaluator import eval_pyxis_expr


class TestScopedRandomIsolation(unittest.TestCase):
    """Verifies independent random callsites per variable/bytecode and fresh sub-loop helpers."""

    def test_unscoped_multiple_r_calls_and_variable_reuse(self):
        """Each R() call in an expression evaluates independently, while a variable caches its sum."""
        ctx = {"bu_i": 1}
        # Evaluate Variable = R(1000) + R(1000) + R(1000) multiple times via Define Vars
        engine = GraphEngine({"nodes": [], "links": []})
        # Check that two R(100000) calls inside one expression are not identical by callsite collision
        vals = set()
        for _ in range(5):
            v1 = eval_pyxis_expr("R(1, 100000)", ctx)
            v2 = eval_pyxis_expr("R(1, 100000)", ctx)
            vals.add((v1, v2))
        self.assertTrue(any(a != b for a, b in vals))

        engine._apply_set_vars_to_context("Total = R(1, 100000) + R(1, 100000) + R(1, 100000)", ctx)
        first_read = eval_pyxis_expr("Total", ctx)
        second_read = eval_pyxis_expr("Total", ctx)
        self.assertEqual(first_read, second_read)

    def test_define_vars_distinct_variables_do_not_share_callsite(self):
        """Distinct variables using the same by.bu_i.Rs(...) expression get independent callsites."""
        engine = GraphEngine({"nodes": [], "links": []})
        line = type("L", (), {"i": 1})()
        pairs = set()
        for bu_i in range(1, 8):
            ctx = {"line": line, "active_unit": line, "bu_i": bu_i}
            engine._apply_set_vars_to_context("Origenx = by.bu_i.Rs(100000)\nOrigeny = by.bu_i.Rs(100000)", ctx, line)
            pairs.add((ctx["Origenx"], ctx["Origeny"]))
        self.assertTrue(any(x != y for x, y in pairs))

    def test_builder_re_evaluates_by_bu_i_when_define_vars_ran_before_builder(self):
        """Pre-populated _eval_helpers_cache from outer context must not flatten by.bu_i inside Builder."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Shape/Library", "properties": {"category": "shapes", "shape": "rectangle"}},
                {"id": 2, "type": "Shape/Slicer", "properties": {"mode": "grid", "out_mode": "shape", "loop_mode": "Shape", "cols": "3", "rows": "2"}},
                {"id": 3, "type": "Functions/Move Tag", "properties": {"mode": "shadtrick", "points": "Origenx, Origeny, 0.001, 0.001", "step_px": "500", "t1": "0", "t2": "1000"}},
                {"id": 4, "type": "Basics/Builder", "inputs": [{"name": "Tags", "link": 3}, {"name": "In1", "link": 2}], "properties": {"mode": "shape", "sub_mode": "splitter", "shape_split_mode": "subpaths", "inject_r": True}},
            ],
            "links": [
                [1, 1, 0, 2, 0, "data"],
                [2, 2, 0, 4, 1, "data"],
                [3, 3, 0, 4, 0, "data"],
            ],
        }
        engine = GraphEngine(graph)
        line = type("L", (), {
            "text": "Hi", "start_time": 0, "end_time": 2000,
            "center": 640, "middle": 360, "left": 600, "right": 680,
            "top": 340, "bottom": 380, "width": 80, "height": 40, "i": 1,
            "styleref": type("S", (), {"alignment": 5, "scale_x": 100, "scale_y": 100, "fontname": "Arial", "fontsize": 50, "outline": 2, "shadow": 0})(),
        })()
        vars_str = "Origenx = by.bu_i.Rs(10000)\nOrigeny = by.bu_i.Rs(10000)"
        ctx = {"line": line, "active_unit": line, "meta": {"res_x": 1280, "res_y": 720}, "_active_set_vars": [vars_str]}
        # Pre-run Define Vars on outer context (populates _eval_helpers_cache before Builder)
        engine._apply_set_vars_to_context(vars_str, ctx, line)
        out = engine.evaluate_data_node(4, ctx, 0)
        import re
        xshads = re.findall(r"\\xshad(-?\d+(?:\.\d+)?)", out)
        yshads = re.findall(r"\\yshad(-?\d+(?:\.\d+)?)", out)
        # Initial positions (every even index, since odd index is the target 0.001 in \t)
        init_x = xshads[0::2]
        init_y = yshads[0::2]
        self.assertGreaterEqual(len(set(init_x)), 2)
        self.assertGreaterEqual(len(set(init_y)), 2)
        self.assertNotEqual(init_x, init_y)


if __name__ == "__main__":
    unittest.main()

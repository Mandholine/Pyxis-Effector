"""
Unit tests for `Basics/Math` canonical 1:1 `ke.math` implementation (`math_nodes.py`)
and its integration with `GraphEngine` (`node_engine.py`) and decoupled helpers (`code_nodes.py`).
"""

import os
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from nodes.math_nodes import eval_math_node, KeMatrix
from nodes.code_nodes import (
    _pyxis_ease_in,
    _pyxis_ease_out,
    _pyxis_ease_in_out,
    _pyxis_cubic_in,
    _pyxis_cubic_out,
    _pyxis_elastic,
    _pyxis_bounce,
    _pyxis_back,
    _pyxis_sine_wave,
    _pyxis_square_wave,
    _pyxis_triangle_wave,
    _pyxis_sawtooth_wave,
)
from node_engine import GraphEngine


class TestBasicsMathKeMath(unittest.TestCase):
    """Exhaustive tests covering all operations of `Basics/Math` across 6 categories."""

    # ------------------------------------------------------------------
    # Category 0: basic (expandable multi-input arithmetic)
    # ------------------------------------------------------------------
    def test_basic_operations(self):
        self.assertEqual(eval_math_node(category="basic", operation="add"), 0.0)
        self.assertEqual(eval_math_node(category="basic", operation="add", in1="10", in2="20", In3="5"), 35.0)
        self.assertEqual(eval_math_node(category="basic", operation="sub", in1="20", in2="5", In3="3"), 12.0)
        self.assertEqual(eval_math_node(category="basic", operation="mul", in1="2", in2="3", In3="4"), 24.0)
        self.assertEqual(eval_math_node(category="basic", operation="div", in1="24", in2="3", In3="2"), 4.0)
        self.assertEqual(eval_math_node(category="basic", operation="div", in1="10", in2="0"), 0.0)
        self.assertEqual(eval_math_node(category="basic", operation="mod", in1="17", in2="5"), 2.0)
        self.assertEqual(eval_math_node(category="basic", operation="mod", in1="17", in2="0"), 0.0)
        self.assertEqual(eval_math_node(category="basic", operation="pow", in1="2", in2="3", In3="2"), 64.0)
        self.assertEqual(eval_math_node(category="basic", operation="min", in1="8", in2="3", In3="12"), 3.0)
        self.assertEqual(eval_math_node(category="basic", operation="max", in1="8", in2="3", In3="12"), 12.0)
        self.assertEqual(eval_math_node(category="basic", operation="avg", in1="10", in2="20", In3="30"), 20.0)

    def test_graph_engine_basic_expandable(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Basics/Number", "properties": {"value": "100"}, "outputs": [{"name": "Number"}]},
                {"id": 2, "type": "Basics/Number", "properties": {"value": "25"}, "outputs": [{"name": "Number"}]},
                {"id": 3, "type": "Basics/Number", "properties": {"value": "15"}, "outputs": [{"name": "Number"}]},
                {
                    "id": 4,
                    "type": "Basics/Math",
                    "properties": {"category": "basic", "operation": "add", "expandable": True, "in1": "0", "in2": "0", "In3": "0"},
                    "inputs": [
                        {"name": "In1", "property": "in1", "link": 1},
                        {"name": "In2", "property": "in2", "link": 2},
                        {"name": "In3", "property": "In3", "link": 3},
                    ],
                    "outputs": [{"name": "Out"}],
                },
            ],
            "links": [
                [1, 1, 0, 4, 0, "data"],
                [2, 2, 0, 4, 1, "data"],
                [3, 3, 0, 4, 2, "data"],
            ],
        }
        eng = GraphEngine(graph)
        self.assertEqual(eng.evaluate_data_node(4, {}, output_slot_index=0), "140")

    # ------------------------------------------------------------------
    # Category 1: numeric
    # ------------------------------------------------------------------
    def test_numeric_round(self):
        self.assertEqual(eval_math_node(category="numeric", operation="round", value="2.5", decimal="0"), 3.0)
        self.assertEqual(eval_math_node(category="numeric", operation="round", value="3.14159", decimal="2"), 3.14)
        self.assertEqual(
            eval_math_node(category="numeric", operation="round", value="1.6, 3.2, 8.7", decimal="0"),
            "2, 3, 9",
        )

    def test_numeric_clamp(self):
        self.assertEqual(eval_math_node(category="numeric", operation="clamp", num="3", min_val="5", max_val="10"), 5.0)
        self.assertEqual(eval_math_node(category="numeric", operation="clamp", num="12", min_val="10", max_val="5"), 10.0)
        self.assertEqual(
            eval_math_node(category="numeric", operation="clamp", num="3, 7, 12", min_val="5", max_val="10"),
            "5, 7, 10",
        )
        cycled = eval_math_node(category="numeric", operation="clamp", num="1.2", min_val="0", max_val="1", cycle=True)
        self.assertAlmostEqual(cycled, 0.8, places=3)

    def test_numeric_rand(self):
        v0 = eval_math_node(category="numeric", operation="rand", num1="", num2="")
        self.assertTrue(0.0 <= v0 <= 1.0)
        v1 = eval_math_node(category="numeric", operation="rand", num1="10", num2="20", step="2")
        self.assertTrue(10.0 <= v1 <= 20.0)
        self.assertEqual((v1 - 10.0) % 2.0, 0.0)
        v_list = eval_math_node(category="numeric", operation="rand", num1="10, 20, 30", num2="")
        self.assertIn(v_list, [10.0, 20.0, 30.0])
        v_rng = eval_math_node(category="numeric", operation="rand", num1="0", num2="100", step="1", range="20, 30, 100")
        self.assertTrue(20.0 <= v_rng <= 30.0)
        v_sign = eval_math_node(category="numeric", operation="rand", num1="5", num2="5", step="1", sign=True)
        self.assertIn(v_sign, [-5.0, 5.0])

    def test_numeric_factk_to16_equality_between(self):
        self.assertEqual(eval_math_node(category="numeric", operation="factk", n="5"), 120)
        self.assertEqual(eval_math_node(category="numeric", operation="factk", n="0"), 1)
        self.assertEqual(eval_math_node(category="numeric", operation="to16", num="255"), "FF")
        self.assertEqual(eval_math_node(category="numeric", operation="to16", num="255, 16, 12"), "FF, 10, C")
        self.assertTrue(eval_math_node(category="numeric", operation="equality", n1="1.000001", n2="1.0", tolerance="5"))
        self.assertFalse(eval_math_node(category="numeric", operation="equality", n1="1.01", n2="1.0", tolerance="5"))
        self.assertTrue(eval_math_node(category="numeric", operation="between", num="3", n1="5", n2="2"))
        self.assertFalse(eval_math_node(category="numeric", operation="between", num="6", n1="5", n2="2"))

    # ------------------------------------------------------------------
    # Category 2: sequence
    # ------------------------------------------------------------------
    def test_sequence_i_all_modes(self):
        self.assertEqual([eval_math_node(category="sequence", operation="i", counter=k, seq_mode="+,-", a=1) for k in range(1, 5)], [1.0, -1.0, 1.0, -1.0])
        self.assertEqual([eval_math_node(category="sequence", operation="i", counter=k, seq_mode="A,B", a=10, b=20, c=1) for k in range(1, 5)], [10.0, 20.0, 10.0, 20.0])
        self.assertEqual([eval_math_node(category="sequence", operation="i", counter=k, seq_mode="mxA", a=5, b=2) for k in range(1, 5)], [5.0, 5.0, 10.0, 10.0])
        self.assertEqual([eval_math_node(category="sequence", operation="i", counter=k, seq_mode="A>B", a=1, b=3, c=1) for k in range(1, 5)], [1.0, 2.0, 3.0, 1.0])
        self.assertEqual([eval_math_node(category="sequence", operation="i", counter=k, seq_mode="ABA", a=1, b=3) for k in range(1, 6)], [1.0, 2.0, 3.0, 2.0, 1.0])
        self.assertEqual([eval_math_node(category="sequence", operation="i", counter=k, seq_mode="ABB", a=5, b=9) for k in range(1, 4)], [5.0, 9.0, 9.0])
        self.assertEqual([eval_math_node(category="sequence", operation="i", counter=k, seq_mode="ABC", a=1, b=2, c=3) for k in range(1, 5)], [1.0, 2.0, 2.0, 1.0])
        self.assertEqual([eval_math_node(category="sequence", operation="i", counter=k, seq_mode="ACB", a=1, b=2, c=3) for k in range(1, 5)], [1.0, 1.0, 2.0, 1.0])
        self.assertEqual([eval_math_node(category="sequence", operation="i", counter=k, seq_mode="N,n", a=2) for k in range(1, 5)], [1.0, 1.0, 2.0, 2.0])

    def test_sequence_count_stateful(self):
        ctx = {}
        vals = [
            eval_math_node(ctx, node_id="cnt_1", category="sequence", operation="count", init="1", step="2", seq_mode="none")
            for _ in range(3)
        ]
        self.assertEqual(vals, [1.0, 3.0, 5.0])

    def test_sequence_normalize_and_ipol(self):
        self.assertAlmostEqual(eval_math_node(category="sequence", operation="normalize", t="0.5", accel="2"), 0.25, places=6)
        self.assertAlmostEqual(eval_math_node(category="sequence", operation="normalize", t="25", accel="1"), 0.25, places=6)
        shp_norm = eval_math_node(category="sequence", operation="normalize", t="0.5", accel="1", shape="m 0 0 l 0 100")
        self.assertAlmostEqual(shp_norm, 0.5, places=3)
        self.assertEqual(eval_math_node(category="sequence", operation="ipol", values="0, 30, 20", t="0.7"), 26.0)
        self.assertEqual(eval_math_node(category="sequence", operation="ipol", values="0, 100", t="0", size="3"), "0, 50, 100")

    # ------------------------------------------------------------------
    # Category 3: geometry
    # ------------------------------------------------------------------
    def test_geometry_angle_polar_distance(self):
        self.assertEqual(eval_math_node(category="geometry", operation="angle", p1="10, 0", p2=""), 0.0)
        self.assertEqual(eval_math_node(category="geometry", operation="angle", p1="0, 0", p2="0, -10"), 90.0)
        px, py = eval_math_node(category="geometry", operation="polar", angle="45", radius="10", get="xy")
        self.assertEqual(px, 7.071)
        self.assertEqual(py, -7.071)
        self.assertEqual(eval_math_node(category="geometry", operation="distance", p1="0, 0", p2="3, 4"), 5.0)
        self.assertEqual(eval_math_node(category="geometry", operation="distance", p1="m 0 0 l 3 0 3 4", p2=""), 7.0)

    def test_geometry_intersect_circle_rotate(self):
        ix, iy, t = eval_math_node(category="geometry", operation="intersect", s1="0 0 10 10", s2="0 10 10 0")
        self.assertEqual((ix, iy, t), (5.0, 5.0, 0.5))
        par = eval_math_node(category="geometry", operation="intersect", s1="0 0 10 0", s2="0 5 10 5")
        self.assertEqual(par[0], "parallels")

        cx, cy, rad = eval_math_node(category="geometry", operation="circle", p1="0, 0", p2="10, 0", p3="0, 10")
        self.assertEqual((cx, cy, rad), (5.0, 5.0, 7.071))
        col = eval_math_node(category="geometry", operation="circle", p1="0, 0", p2="5, 5", p3="10, 10")
        self.assertEqual(col[0], "collineals")

        out_pt, rx, ry, rz = eval_math_node(category="geometry", operation="rotate", p="10, 0, 0", angle="90", axis="z")
        self.assertEqual((rx, ry, rz), (0.0, 10.0, 0.0))
        self.assertEqual(out_pt, "0, 10, 0")
        rot_shp, _, _, _ = eval_math_node(category="geometry", operation="rotate", p="m 10 0 l 0 10", angle="90", axis="z")
        self.assertEqual(rot_shp, "m 0 10 l -10 0")

    # ------------------------------------------------------------------
    # Category 4: algebra
    # ------------------------------------------------------------------
    def test_algebra_solvers_and_evaluate(self):
        self.assertEqual(eval_math_node(category="algebra", operation="quadratic", c1="1", c2="-3", c3="2"), "1, 2")
        self.assertEqual(eval_math_node(category="algebra", operation="cubic", c1="1", c2="-3", c3="-9", c4="-5"), "-1, 5")
        self.assertEqual(eval_math_node(category="algebra", operation="resolve", coefficients="0, 1, -3, 2"), "1, 2")
        eq_roots = eval_math_node(category="algebra", operation="equation", coefficients="-5, -9, -3, 1", reals=True)
        self.assertIn("5", eq_roots)
        self.assertIn("-1", eq_roots)
        self.assertEqual(eval_math_node(category="algebra", operation="evaluate", coefficients="5, -7", t="2"), -9.0)
        self.assertEqual(eval_math_node(category="algebra", operation="gauss", matrix="5, -3, -1; 2, 1, 4"), "1, 2")
        self.assertEqual(eval_math_node(category="algebra", operation="gauss", matrix="1, 2, 3; 2, 4, 6"), "singular system")

    def test_algebra_matrix(self):
        out_id, det_id = eval_math_node(category="algebra", operation="matrix", matrix_op="identity", matrix_a="3")
        self.assertEqual(out_id, "1, 0, 0; 0, 1, 0; 0, 0, 1")
        self.assertEqual(det_id, 1.0)

        out_det, d_val = eval_math_node(category="algebra", operation="matrix", matrix_op="det", matrix_a="2, 3, 4, 1")
        self.assertEqual(out_det, -10.0)
        self.assertEqual(d_val, -10.0)

        out_inv, _ = eval_math_node(category="algebra", operation="matrix", matrix_op="inverse", matrix_a="2, 3, 4, 1")
        self.assertEqual(out_inv, "-0.1, 0.3; 0.4, -0.2")

        out_mul, _ = eval_math_node(category="algebra", operation="matrix", matrix_op="mul", matrix_a="1, 2, 3, 4", matrix_b="2")
        self.assertEqual(out_mul, "2, 4; 6, 8")

        out_eq, _ = eval_math_node(category="algebra", operation="matrix", matrix_op="eq", matrix_a="1, 2, 3, 4", matrix_b="1, 2, 3, 4")
        self.assertTrue(out_eq)

    # ------------------------------------------------------------------
    # Category 5: data
    # ------------------------------------------------------------------
    def test_data_getpair_getnumbers_format(self):
        self.assertEqual(eval_math_node(category="data", operation="getpair", val="7 8", defx="0", defy="0"), (7.0, 8.0))
        self.assertEqual(eval_math_node(category="data", operation="getpair", val="7", defx="0", defy=""), (7.0, 7.0))
        self.assertEqual(eval_math_node(category="data", operation="getnumbers", val="m 1 2 l -3.5 4"), "1, 2, -3.5, 4")
        self.assertEqual(eval_math_node(category="data", operation="format", fmt="pos(%d, %d)", values="10, 20"), "pos(10, 20)")

    # ------------------------------------------------------------------
    # GraphEngine multi-output & code_nodes decoupling
    # ------------------------------------------------------------------
    def test_graph_engine_multi_output_slots(self):
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Basics/Math",
                    "properties": {"category": "geometry", "operation": "polar", "angle": "45", "radius": "10", "get": "xy"},
                    "inputs": [
                        {"name": "Angle", "property": "angle", "link": None},
                        {"name": "Radius", "property": "radius", "link": None},
                    ],
                    "outputs": [{"name": "X"}, {"name": "Y"}],
                }
            ],
            "links": [],
        }
        eng = GraphEngine(graph)
        self.assertEqual(eng.evaluate_data_node(1, {}, output_slot_index=0), "7.071")
        self.assertEqual(eng.evaluate_data_node(1, {}, output_slot_index=1), "-7.071")

    def test_decoupled_code_nodes_helpers(self):
        self.assertAlmostEqual(_pyxis_ease_in(0.5), 0.25)
        self.assertAlmostEqual(_pyxis_ease_out(0.5), 0.75)
        self.assertAlmostEqual(_pyxis_ease_in_out(0.5), 0.5)
        self.assertAlmostEqual(_pyxis_cubic_in(0.5), 0.125)
        self.assertAlmostEqual(_pyxis_cubic_out(0.5), 0.875)
        self.assertEqual(_pyxis_elastic(0.0), 0.0)
        self.assertEqual(_pyxis_bounce(1.0), 1.0)
        self.assertAlmostEqual(_pyxis_back(1.0), 1.0)
        self.assertAlmostEqual(_pyxis_sine_wave(0.25, freq=1.0, amp=10.0, offset=5.0), 15.0)
        self.assertEqual(_pyxis_square_wave(0.25, freq=1.0, amp=2.0, offset=0.0), 2.0)
        self.assertAlmostEqual(_pyxis_triangle_wave(0.5, freq=1.0, amp=1.0, offset=0.0), -1.0)
        self.assertAlmostEqual(_pyxis_sawtooth_wave(0.5, freq=1.0, amp=1.0, offset=0.0), 0.0)


if __name__ == "__main__":
    unittest.main()

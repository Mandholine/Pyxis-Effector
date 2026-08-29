# tests/test_all_nodes_dynamic_eval.py
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from node_engine import GraphEngine
from nodes.math_nodes import eval_math_node, math_random_master
from nodes.time_nodes import time_lead_in, time_lead_out, time_ipol
from nodes.text_nodes import text_substring, eval_text_node
from nodes.tag_nodes import node_condicionador


class DummyLine:
    def __init__(self, left=100.0, right=300.0, width=200.0, height=40.0, center=200.0, middle=120.0, start_time=1000, end_time=3000, duration=2000):
        self.left = left
        self.right = right
        self.width = width
        self.height = height
        self.center = center
        self.middle = middle
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.dur = duration
        self.text = "Hello World"
        self.text_stripped = "Hello World"


class DummyUnit:
    def __init__(self, line, i=2, n=5, start_time=1200, end_time=1600, duration=400):
        self.line = line
        self.i = i
        self.n = n
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.dur = duration
        self.left = 120.0
        self.right = 160.0
        self.width = 40.0
        self.height = 30.0
        self.center = 140.0
        self.middle = 120.0
        self.text = "llo"
        self.text_stripped = "llo"


class TestAllNodesDynamicEval(unittest.TestCase):

    def setUp(self):
        self.engine = GraphEngine({"nodes": []})
        self.line = DummyLine()
        self.unit = DummyUnit(self.line)
        self.context = {
            'line': self.line,
            'active_line': self.line,
            'active_unit': self.unit,
            'syl': self.unit,
            'unit': self.unit,
            'char': self.unit,
            'start_time': self.unit.start_time,
            'end_time': self.unit.end_time,
            'duration': self.unit.duration,
            'i': self.unit.i,
            'n': self.unit.n,
        }
        self.engine.bind_active_unit(self.context, self.unit)

    def test_number_node_dynamic_expressions(self):
        # 1. Literal number
        node_lit = {"id": 1, "type": "Number", "properties": {"valor": "42"}}
        self.engine.nodes[1] = node_lit
        self.assertEqual(self.engine.evaluate_data_node(1, self.context), "42")

        # 2. Expression using line alias l
        node_expr = {"id": 2, "type": "Number", "properties": {"valor": "l.width + 50"}}
        self.engine.nodes[2] = node_expr
        self.assertEqual(self.engine.evaluate_data_node(2, self.context), "250")

        # 3. Expression using syl / unit
        node_syl = {"id": 3, "type": "Number", "properties": {"valor": "syl.duration / 2"}}
        self.engine.nodes[3] = node_syl
        self.assertEqual(self.engine.evaluate_data_node(3, self.context), "200")

        # 4. Expression using fx context
        node_fx = {"id": 4, "type": "Number", "properties": {"valor": "fx.pos_x + 10"}}
        self.engine.nodes[4] = node_fx
        self.assertEqual(self.engine.evaluate_data_node(4, self.context), "150")

    def test_math_node_dynamic_expressions(self):
        # Math Suma with A = l.left (100) and B = l.width (200) -> 300
        res = eval_math_node(self.context, categoria="Basico", operacion="Suma", A="l.left", B="l.width")
        self.assertEqual(float(res), 300.0)

        # Math Multiplicacion with A = syl.duration (400) and B = 0.5 -> 200
        res = eval_math_node(self.context, categoria="Basico", operacion="Multiplicacion", A="syl.duration", B="0.5")
        self.assertEqual(float(res), 200.0)

        # Math with fx.pos_x (140) and l.left (100)
        res = eval_math_node(self.context, categoria="Basico", operacion="Resta", A="fx.pos_x", B="l.left")
        self.assertEqual(float(res), 40.0)

    def test_multirandom_node_dynamic_expressions(self):
        # MultiRandom with Min = l.left (100) and Max = l.right (300)
        for _ in range(20):
            val = math_random_master(self.context, modo="R", min_val="l.left", max_val="l.right", step="1")
            self.assertTrue(100.0 <= float(val) <= 300.0, f"Random val {val} out of bounds [100, 300]")

        # MultiRandom with syl.duration / 4 (100) and syl.duration / 2 (200)
        for _ in range(20):
            val = math_random_master(self.context, modo="R", min_val="syl.duration / 4", max_val="syl.duration / 2", step="1")
            self.assertTrue(100.0 <= float(val) <= 200.0, f"Random val {val} out of bounds [100, 200]")

    def test_shape_slicer_dynamic_expressions(self):
        # Shape Slicer node with cols = l.width / 100 (2.0 -> 2), rows = 2, size_x = l.width / 10 (20.0)
        node_slicer = {
            "id": 10,
            "type": "Shape/Shape Slicer",
            "properties": {
                "shape": "m 0 0 l 200 0 l 200 100 l 0 100",
                "cols": "l.width / 100",   # 200 / 100 = 2
                "rows": "syl.i",           # 2
                "size_x": "l.width / 10",  # 20
                "size_y": "syl.height",    # 30
                "scale_x": "1.0",
                "scale_y": "1.0",
                "modo": "Rejilla 1D/2D",
                "out_mode": "Shape",
                "order": "79"
            }
        }
        self.engine.nodes[10] = node_slicer
        res_piece = self.engine.evaluate_data_node(10, self.context, output_slot_index=0)
        self.assertTrue(res_piece.startswith("m "), f"Expected vector shape, got {res_piece}")

        res_col = self.engine.evaluate_data_node(10, self.context, output_slot_index=3)
        res_row = self.engine.evaluate_data_node(10, self.context, output_slot_index=4)
        self.assertTrue(res_col.isdigit())
        self.assertTrue(res_row.isdigit())

    def test_time_nodes_dynamic_expressions(self):
        # Lead In with Delay = syl.duration / 10 (40) and Base = l.start_time (1000)
        # formula: round(base_val + delay_val * (i - 1.0) - 200.0, 3)
        # base = 1000, delay = 40, i = 2 -> 1000 + 40*(1) - 200 = 840
        res = time_lead_in(self.context, delay="syl.duration / 10", base="l.start_time")
        self.assertEqual(res, 840.0)

        # Time Ipol with Points = "0, syl.duration / 2, syl.duration" (0, 200, 400)
        res_ipol = time_ipol(self.context, dur="syl.duration", points="0, syl.duration / 2, syl.duration", accel="1.0")
        self.assertIn("[0.0, 200.0]", res_ipol)
        self.assertIn("[200.0, 400.0]", res_ipol)

    def test_text_substring_dynamic_expressions(self):
        # text_substring with Start = char.i - 1 (1) and Length = 3 on "Hello World" -> "ell"
        res = text_substring(self.context, text="Hello World", start="char.i - 1", length="3")
        self.assertEqual(res, "ell")

        # eval_text_node Subcadena
        res_eval = eval_text_node(self.context, operacion="Subcadena", Text="Hello World", Start="char.i - 1", Longitud="3")
        self.assertEqual(res_eval, "ell")

    def test_conditioner_dynamic_expressions(self):
        # Condition with l.width > 150 (200 > 150 -> True)
        res_true = node_condicionador(self.context, condicion="l.width > 150", si_verdadero="VERDADERO", si_falso="FALSO")
        self.assertEqual(res_true, "VERDADERO")

        # Condition with l.width < 50 (200 < 50 -> False)
        res_false = node_condicionador(self.context, condicion="l.width < 50", si_verdadero="VERDADERO", si_falso="FALSO")
        self.assertEqual(res_false, "FALSO")

        # Condition with char.i == 2 and fx.pos_x > 100 -> True
        res_fx = node_condicionador(self.context, condicion="char.i == 2 and fx.pos_x > 100", si_verdadero="OK", si_falso="FAIL")
        self.assertEqual(res_fx, "OK")


if __name__ == '__main__':
    unittest.main()

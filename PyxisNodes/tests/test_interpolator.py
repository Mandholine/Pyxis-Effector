# tests/test_interpolator.py
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from node_engine import GraphEngine


class TestInterpolator(unittest.TestCase):

    def test_interpolator_linear(self):
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Interpolator",
                    "properties": {
                        "iterador": "5",
                        "total": "9",
                        "accel": "1.0",
                        "v1": "0",
                        "v2": "100"
                    }
                }
            ]
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {})
        # i=5, N=9 -> t = (5-1)/(9-1) = 4/8 = 0.5 -> 0 + 100*0.5 = 50.0
        self.assertEqual(float(res), 50.0)

    def test_interpolator_acceleration_ease_in(self):
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Interpolator",
                    "properties": {
                        "iterador": "5",
                        "total": "9",
                        "accel": "2.0",
                        "v1": "0",
                        "v2": "100"
                    }
                }
            ]
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {})
        # t_base = 0.5. accel=2.0 -> t = 0.5^2 = 0.25 -> 25.0
        self.assertEqual(float(res), 25.0)

    def test_interpolator_deceleration_penner_ease_out(self):
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Interpolator",
                    "properties": {
                        "iterador": "5",
                        "total": "9",
                        "accel": "0.5",
                        "v1": "0",
                        "v2": "100"
                    }
                }
            ]
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {})
        # t_base = 0.5. accel=0.5 -> p = 1/0.5 = 2.0 -> t = 1 - (1 - 0.5)^2 = 1 - 0.25 = 0.75 -> 75.0
        self.assertEqual(float(res), 75.0)

    def test_interpolator_no_gaps_on_first_step(self):
        # Simular N=20 caracteres, paso i=2 (el segundo carácter) con accel=0.5
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Interpolator",
                    "properties": {
                        "iterador": "2",
                        "total": "20",
                        "accel": "0.5",
                        "v1": "0",
                        "v2": "100"
                    }
                }
            ]
        }
        engine = GraphEngine(graph)
        res = float(engine.evaluate_data_node(1, {}))
        # t_base = (2-1)/(20-1) = 1/19 approx 0.05263
        # Con Penner conjugada: t = 1 - (1 - 1/19)^2 = 1 - (18/19)^2 = 1 - 324/361 = 37/361 approx 0.10249 (10.25%)
        # En vez del 22.94% de la fórmula antigua que dejaba huecos
        self.assertAlmostEqual(res, 10.25, delta=0.1)

    def test_interpolator_boundaries(self):
        # i=1 -> t=0, res=0
        graph_start = {
            "nodes": [
                {"id": 1, "type": "Functions/Interpolator", "properties": {"iterador": "1", "total": "10", "accel": "0.5", "v1": "0", "v2": "100"}}
            ]
        }
        engine = GraphEngine(graph_start)
        self.assertEqual(float(engine.evaluate_data_node(1, {})), 0.0)

        # i=10 -> t=1, res=100
        graph_end = {
            "nodes": [
                {"id": 1, "type": "Functions/Interpolator", "properties": {"iterador": "10", "total": "10", "accel": "0.5", "v1": "0", "v2": "100"}}
            ]
        }
        engine = GraphEngine(graph_end)
        self.assertEqual(float(engine.evaluate_data_node(1, {})), 100.0)

    def test_interpolator_color(self):
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Interpolator",
                    "properties": {
                        "iterador": "5",
                        "total": "9",
                        "accel": "0.5",
                        "v1": "#000000",
                        "v2": "#FFFFFF"
                    }
                }
            ]
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {})
        # t = 0.75 -> 255 * 0.75 = 191 -> #BFBFBF
        self.assertIn("#BFBFBF", res.upper())

    def test_interpolator_ass_alpha_tags(self):
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Interpolator",
                    "properties": {
                        "iterador": "5",
                        "total": "9",
                        "accel": "1.0",
                        "v1": r"\alpha&H00&",
                        "v2": r"\alpha&HFF&"
                    }
                }
            ]
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {})
        # t = 0.5 -> 128 = 0x80
        self.assertEqual(res, r"\alpha&H80&")

    def test_interpolator_multitag_chain(self):
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Interpolator",
                    "properties": {
                        "iterador": "5",
                        "total": "9",
                        "accel": "1.0",
                        "v1": r"\1a&H00&\3a&H00&\4a&H00&",
                        "v2": r"\1a&HC8&\3a&HC8&\4a&HC8&"
                    }
                }
            ]
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {})
        # t = 0.5 -> 200 * 0.5 = 100 = 0x64
        self.assertEqual(res, r"\1a&H64&\3a&H64&\4a&H64&")

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
                        "v1": r"\fscx100\fscy100",
                        "v2": r"\fscx200\fscy300"
                    }
                }
            ]
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {})
        self.assertEqual(res, r"\fscx150\fscy200")


if __name__ == "__main__":
    unittest.main()

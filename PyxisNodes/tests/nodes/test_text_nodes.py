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

"""Pruebas unitarias para nodos de texto, trazado sobre rutas vectoriales y metricas tipograficas."""

import unittest
from ass_parser import KaraokeProcessor
from models import PyxisLine, PyxisUnit
from nodes.text_nodes import eval_text_node, text_to_shape_node, text_on_path_core, text_on_path_node
from nodes.shape_nodes import shape_circulo
from node_engine import GraphEngine


class TestUnifiedTextNode(unittest.TestCase):
    """Pruebas para el nodo maestro Text y manipulacion de cadenas."""

    def setUp(self):
        self.context = {
            'active_unit': type('Unit', (), {'text': r'{\pos(100,200)}Hola Mundo', 'text_stripped': 'Hola Mundo'})(),
            'active_line': type('Line', (), {'text': r'{\pos(100,200)}Hola Mundo', 'text_stripped': 'Hola Mundo'})()
        }

    def test_op_strip_tags(self):
        res = eval_text_node(self.context, operacion="Strip Tags", Texto=r"{\b1\pos(10,20)}Prueba\NText")
        self.assertEqual(res, "Prueba Text")

    def test_op_mayusculas(self):
        res = eval_text_node(self.context, operacion="Mayusculas", Texto="kara effector")
        self.assertEqual(res, "KARA EFFECTOR")

    def test_op_minusculas(self):
        res = eval_text_node(self.context, operacion="Minusculas", Texto="PYXIS NODES")
        self.assertEqual(res, "pyxis nodes")

    def test_op_reemplazar(self):
        res = eval_text_node(self.context, operacion="Reemplazar", Texto="Hola Mundo", Buscar="Mundo", Reemplazar="Pyxis")
        self.assertEqual(res, "Hola Pyxis")

    def test_op_subcadena(self):
        res = eval_text_node(self.context, operacion="Subcadena", Texto="Antigravity", Inicio=0, Longitud=4)
        self.assertEqual(res, "Anti")

    def test_op_longitud(self):
        res = eval_text_node(self.context, operacion="Longitud", Texto="PyxisNodes")
        self.assertEqual(res, "10")

    def test_op_contener_true(self):
        res = eval_text_node(self.context, operacion="Contener", Texto="Efecto Visual", Buscar="Efecto")
        self.assertEqual(res, "1")

    def test_op_contener_false(self):
        res = eval_text_node(self.context, operacion="Contener", Texto="Efecto Visual", Buscar="Audio")
        self.assertEqual(res, "0")

    def test_op_kana_romaji_hiragana(self):
        res = eval_text_node(self.context, operacion="Kana", Texto="sakura", Modo="Romaji a Hiragana")
        self.assertEqual(res, "さくら")

    def test_op_kana_romaji_katakana(self):
        res = eval_text_node(self.context, operacion="Kana", Texto="sakura", Modo="Romaji a Katakana")
        self.assertEqual(res, "サクラ")

    def test_graph_engine_text_node_evaluation(self):
        text_node = {
            "id": 1,
            "type": "Text",
            "properties": {"operacion": "Reemplazar"},
            "inputs": [
                {"name": "Text", "value": "Pyxis V1"},
                {"name": "Buscar", "value": "V1"},
                {"name": "Reemplazar Por", "value": "V2"}
            ]
        }
        graph_data = {"nodes": [text_node], "links": []}
        engine = GraphEngine(graph_data)
        res = engine.evaluate_data_node(1, {})
        self.assertEqual(res, "Pyxis V2")


class DummyUnit:
    def __init__(self, i=1, n=4, left=100.0, center=120.0, width=40.0, height=30.0, middle=50.0):
        self.i = i
        self.n = n
        self.left = left
        self.center = center
        self.width = width
        self.height = height
        self.middle = middle


class DummyLine:
    def __init__(self, left=100.0, width=160.0, center=180.0, middle=50.0, text="Test Line"):
        self.left = left
        self.width = width
        self.center = center
        self.middle = middle
        self.text = text
        self.raw_text = text


class TestTextOnPath(unittest.TestCase):
    """Pruebas para el nodo Text on Path (trazado tipografico sobre curvas vectoriales)."""

    def setUp(self):
        self.line = DummyLine()
        self.u1 = DummyUnit(1, 4, left=100.0, center=120.0, width=40.0)
        self.u2 = DummyUnit(2, 4, left=140.0, center=160.0, width=40.0)

    def test_straight_line_center_mode(self):
        line_shape = "m 0 0 l 400 0 "
        ctx = {'active_unit': self.u1, 'active_line': self.line}

        tag_out, pos_str, frz_str, x_val, y_val, total_len, target_dist = text_on_path_core(
            line_shape,
            context=ctx,
            mode="Center (Centrado)",
            offset=0.0
        )

        self.assertEqual(total_len, 400.0)
        self.assertEqual(target_dist, 140.0)
        self.assertEqual(x_val, 140.0)
        self.assertEqual(y_val, 0.0)
        self.assertEqual(frz_str, "\\frz0")
        self.assertTrue(pos_str.startswith("\\pos(140"))

    def test_straight_line_left_and_right_modes(self):
        line_shape = "m 0 0 l 400 0 "
        ctx = {'active_unit': self.u1, 'active_line': self.line}

        # Left mode
        tag_out, pos_str, frz_str, x_val, y_val, total_len, target_dist = text_on_path_core(
            line_shape, context=ctx, mode="Left (Izquierda)", offset=0.0
        )
        self.assertEqual(x_val, 20.0)
        self.assertEqual(target_dist, 20.0)

        # Right mode
        tag_out, pos_str, frz_str, x_val, y_val, total_len, target_dist = text_on_path_core(
            line_shape, context=ctx, mode="Right (Derecha)", offset=0.0
        )
        self.assertEqual(x_val, 260.0)
        self.assertEqual(target_dist, 260.0)

    def test_vertical_line_tangent_angle(self):
        vert_shape = "m 50 50 l 50 250 "
        ctx = {'active_unit': self.u1, 'active_line': self.line}

        tag_out, pos_str, frz_str, x_val, y_val, total_len, target_dist = text_on_path_core(
            vert_shape, context=ctx, mode="Left", offset=0.0
        )
        self.assertEqual(total_len, 200.0)
        self.assertEqual(x_val, 50.0)
        self.assertEqual(y_val, 70.0)
        self.assertEqual(frz_str, "\\frz-90")
        self.assertIn("\\frz-90", tag_out)


class TestRealWidthAndKerning(unittest.TestCase):
    """Pruebas de precision metrica y calculo de dimensiones tipograficas."""

    def _process(self, raw, style=None):
        proc = KaraokeProcessor(1280, 720, 41.708)
        if style is None:
            style = {"Fontname": "Arial", "Fontsize": "40", "MarginL": "10", "MarginR": "10", "MarginV": "30", "Alignment": "2"}
        return proc.process_line(raw, style)

    def test_line_width_calculated(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola"
        line = self._process(raw)
        self.assertIsNotNone(line)
        self.assertGreater(line.width, 0.0)

    def test_alignment_bottom_center(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola"
        line = self._process(raw)
        expected_center = 1280.0 / 2.0
        self.assertAlmostEqual(line.center, expected_center, delta=1.0)


if __name__ == "__main__":
    unittest.main()

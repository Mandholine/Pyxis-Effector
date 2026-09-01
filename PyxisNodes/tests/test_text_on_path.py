# -*- coding: utf-8 -*-
"""
Tests automatizados para el nodo Text on Path (Functions/Text on Path).
Verifica paridad con Effector 2 (ke.text.bezier), integración con Bezier Curve,
Shapes Library, modos de alineación, rotación tangencial y slots de salida.
"""

import pytest
import unittest
from nodes.text_nodes import text_on_path_core, text_on_path_node
from nodes.shape_nodes import shape_circulo
from node_engine import GraphEngine


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

    def setUp(self):
        self.line = DummyLine()
        self.u1 = DummyUnit(1, 4, left=100.0, center=120.0, width=40.0)
        self.u2 = DummyUnit(2, 4, left=140.0, center=160.0, width=40.0)
        self.u3 = DummyUnit(3, 4, left=180.0, center=200.0, width=40.0)
        self.u4 = DummyUnit(4, 4, left=220.0, center=240.0, width=40.0)

    def test_straight_line_center_mode(self):
        """Verifica alineación centrada sobre una recta horizontal."""
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
        """Verifica alineaciones izquierda y derecha."""
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
        """Verifica ángulo de rotación tangencial \\frz-90 en línea vertical descendente."""
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

    def test_extra_angle_offset(self):
        """Verifica aplicación de desfase angular adicional."""
        line_shape = "m 0 0 l 200 0 "
        ctx = {'active_unit': self.u1, 'active_line': self.line}

        tag_out, pos_str, frz_str, x_val, y_val, total_len, target_dist = text_on_path_core(
            line_shape, context=ctx, mode="Left", offset=0.0, extra_angle=45.0
        )
        self.assertEqual(frz_str, "\\frz45")
        self.assertIn("\\frz45", tag_out)

    def test_cubic_bezier_curve_distribution(self):
        """Verifica distribución de caracteres sobre curva Bézier cúbica."""
        curve = "m 0 0 b 100 200 300 200 400 0 "
        prev_x = -1.0

        for u in [self.u1, self.u2, self.u3, self.u4]:
            ctx = {'active_unit': u, 'active_line': self.line}
            tag_out, pos_str, frz_str, x_val, y_val, total_len, target_dist = text_on_path_core(
                curve, context=ctx, mode="Center", offset=0.0
            )
            self.assertGreater(x_val, prev_x)
            prev_x = x_val
            self.assertGreater(total_len, 400.0)

    def test_justified_mode(self):
        """Verifica modo Justificado automático por caracteres."""
        line_shape = "m 0 0 l 300 0 "

        # u1 (i=1, n=4) -> progress 0.0 -> target = 20
        ctx1 = {'active_unit': self.u1, 'active_line': self.line}
        _, _, _, x1, _, _, t1 = text_on_path_core(line_shape, context=ctx1, mode="Justified")

        # u4 (i=4, n=4) -> progress 1.0 -> target = (300 - 160)*1.0 + 140 = 280
        ctx4 = {'active_unit': self.u4, 'active_line': self.line}
        _, _, _, x4, _, _, t4 = text_on_path_core(line_shape, context=ctx4, mode="Justified")

        self.assertEqual(t1, 20.0)
        self.assertEqual(t4, 280.0)

    def test_node_engine_multi_slot_dispatch(self):
        """Verifica que el motor de evaluación entregue correctamente todos los slots."""
        node = {
            'id': 'top_node_1',
            'type': 'Functions/Text on Path',
            'properties': {
                'shape': 'm 0 0 l 500 0 ',
                'modo': 'Center (Centrado)',
                'offset': '0',
                'extra_angle': '15',
                'subdivs': '30'
            },
            'inputs': []
        }
        engine = GraphEngine({'nodes': [node]})
        ctx = {'active_unit': self.u1, 'active_line': self.line}

        # Slot 0: Tag Out
        out0 = engine.evaluate_data_node('top_node_1', ctx, output_slot_index=0)
        self.assertTrue(out0.startswith("\\pos("))
        self.assertIn("\\frz15", out0)

        # Slot 1: \pos Tag
        out1 = engine.evaluate_data_node('top_node_1', ctx, output_slot_index=1)
        self.assertTrue(out1.startswith("\\pos("))
        self.assertNotIn("\\frz", out1)

        # Slot 2: Angle (\frz)
        out2 = engine.evaluate_data_node('top_node_1', ctx, output_slot_index=2)
        self.assertEqual(out2, "\\frz15")

        # Slot 3: X
        out3 = engine.evaluate_data_node('top_node_1', ctx, output_slot_index=3)
        self.assertEqual(float(out3), 190.0)

        # Slot 4: Y
        out4 = engine.evaluate_data_node('top_node_1', ctx, output_slot_index=4)
        self.assertEqual(float(out4), 0.0)

        # Slot 5: Length
        out5 = engine.evaluate_data_node('top_node_1', ctx, output_slot_index=5)
        self.assertEqual(float(out5), 500.0)

    def test_shapes_library_integration(self):
        """Verifica integración directa con formas generadas por Shapes Library."""
        circle_shp = shape_circulo(None)
        self.assertTrue(circle_shp.startswith("m "))

        ctx = {'active_unit': self.u1, 'active_line': self.line}
        tag_out, pos_str, frz_str, x_val, y_val, total_len = text_on_path_node(
            context=ctx,
            shape=circle_shp,
            mode="Center",
            offset=0.0
        )
        self.assertGreater(total_len, 100.0)
        self.assertTrue(pos_str.startswith("\\pos("))


if __name__ == '__main__':
    unittest.main()

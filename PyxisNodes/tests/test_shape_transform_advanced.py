# tests/test_shape_transform_advanced.py
"""Pruebas unitarias para el nuevo nodo Shape Transform (Etapa 1: Inflate - Abombamiento/Esferificación Radial)."""

import unittest
import math
from models import PyxisLine, PyxisUnit
from nodes.shape_nodes import shape_transform, _shape_inflate
from node_engine import GraphEngine


class TestShapeTransformAdvanced(unittest.TestCase):

    def setUp(self):
        self.sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        self.rect = "m 0 0 l 200 0 l 200 100 l 0 100"
        self.context = {
            'active_unit': PyxisUnit(),
            'active_line': PyxisLine(),
            'fx_pos_x': 500.0,
            'fx_pos_y': 300.0
        }

    def test_inflate_basic_levels(self):
        """Verifica la deformación morfológica radial con diferentes niveles de t (0.0, 0.5, 1.0)."""
        # Con t=0.0 y anchor="original", el contorno no sufre alteración
        res_t0 = shape_transform(self.context, drawing=self.sq, mode="Inflate", t=0.0, anchor="original")
        self.assertIn("m 0 0", res_t0)

        # Con t=0.5, los lados del cuadrado se subdividen y abomban hacia afuera
        res_t05 = shape_transform(self.context, drawing=self.sq, mode="Inflate", t=0.5, anchor="center")
        self.assertTrue(res_t05.startswith("m "))
        self.assertIn("l ", res_t05)
        # El número de tokens aumenta debido a la subdivisión y curvado
        self.assertGreater(len(res_t05.split()), len(self.sq.split()))

        # Con t=1.0, alcanza la curvatura máxima de la circunferencia circunscrita
        res_t1 = shape_transform(self.context, drawing=self.sq, mode="Inflate", t=1.0, anchor="center")
        tokens_t1 = res_t1.split()
        self.assertGreater(len(tokens_t1), 20)

    def test_inflate_modes_circle_vs_ellipse(self):
        """Verifica la diferencia entre modo Circle (radio uniforme) y modo Ellipse (aspecto adaptado)."""
        res_circle = shape_transform(self.context, drawing=self.rect, mode="Inflate", t=1.0, inflate_mode="Circle", anchor="center")
        res_ellipse = shape_transform(self.context, drawing=self.rect, mode="Inflate", t=1.0, inflate_mode="Ellipse", anchor="center")

        self.assertNotEqual(res_circle, res_ellipse)
        self.assertTrue(res_circle.startswith("m "))
        self.assertTrue(res_ellipse.startswith("m "))

    def test_inflate_ratio_parameter(self):
        """Verifica que el parámetro ratio expanda proporcionalmente el eje X."""
        res_ratio1 = shape_transform(self.context, drawing=self.sq, mode="Inflate", t=0.8, ratio=1.0, anchor="center")
        res_ratio2 = shape_transform(self.context, drawing=self.sq, mode="Inflate", t=0.8, ratio=2.0, anchor="center")

        def get_max_x(shp):
            coords = []
            for tok in shp.split():
                try: coords.append(float(tok))
                except: pass
            return max(coords[0::2]) if coords else 0.0

        max_x1 = get_max_x(res_ratio1)
        max_x2 = get_max_x(res_ratio2)
        self.assertGreater(max_x2, max_x1)

    def test_inflate_anchor_modes(self):
        """Verifica el correcto anclaje: center, topleft, absolute, original."""
        res_center = shape_transform(self.context, drawing=self.sq, mode="Inflate", t=0.5, anchor="center")
        coords_c = [float(t) for t in res_center.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        xs_c = coords_c[0::2]
        ys_c = coords_c[1::2]
        self.assertAlmostEqual((min(xs_c) + max(xs_c)) / 2.0, 0.0, delta=1.0)
        self.assertAlmostEqual((min(ys_c) + max(ys_c)) / 2.0, 0.0, delta=1.0)

        res_topleft = shape_transform(self.context, drawing=self.sq, mode="Inflate", t=0.5, anchor="topleft")
        coords_tl = [float(t) for t in res_topleft.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        self.assertAlmostEqual(min(coords_tl[0::2]), 0.0, delta=0.5)
        self.assertAlmostEqual(min(coords_tl[1::2]), 0.0, delta=0.5)

        res_abs = shape_transform(self.context, drawing=self.sq, mode="Inflate", t=0.5, anchor="absolute")
        coords_abs = [float(t) for t in res_abs.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        self.assertAlmostEqual((min(coords_abs[0::2]) + max(coords_abs[0::2])) / 2.0, 500.0, delta=1.0)
        self.assertAlmostEqual((min(coords_abs[1::2]) + max(coords_abs[1::2])) / 2.0, 300.0, delta=1.0)

    def test_graph_engine_evaluation(self):
        """Verifica la integración y evaluación de Shape Transform en GraphEngine."""
        graph = {
            'nodes': [
                {
                    'id': 1,
                    'type': 'Shape/Shape Transform',
                    'properties': {
                        'shape': self.sq,
                        'mode': 'Inflate',
                        't': '0.75',
                        'ratio': '1.0',
                        'inflate_mode': 'Circle',
                        'anchor': 'center'
                    },
                    'inputs': []
                }
            ],
            'links': []
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        res = engine.evaluate_data_node(1, self.context, output_slot_index=0)
        self.assertIsInstance(res, str)
        self.assertTrue(res.startswith("m "))
        self.assertNotIn("[Err", res)

    def test_skew_x_and_y(self):
        """Verifica la deformación angular planar (Skew en X y Skew en Y)."""
        # Con angle_x=0 y angle_y=0, forma original sin alteración
        res_zero = shape_transform(self.context, drawing=self.sq, mode="Skew", angle_x=0, angle_y=0, anchor="original")
        self.assertIn("m 0 0", res_zero)

        # Skew X = 45° (tan(45°) = 1.0)
        # Un cuadrado [0..100, 0..100] centrado con anchor original desplaza x según y
        res_skew_x = shape_transform(self.context, drawing=self.sq, mode="Skew", angle_x=45, angle_y=0, anchor="center")
        self.assertTrue(res_skew_x.startswith("m "))
        self.assertIn("l ", res_skew_x)

        # Skew Y = 30°
        res_skew_y = shape_transform(self.context, drawing=self.sq, mode="Skew", angle_x=0, angle_y=30, anchor="center")
        self.assertTrue(res_skew_y.startswith("m "))

    def test_skew_anchors(self):
        """Verifica los modos de anclaje de Skew: center, topleft, absolute."""
        res_center = shape_transform(self.context, drawing=self.sq, mode="Skew", angle_x=30, angle_y=0, anchor="center")
        coords_c = [float(t) for t in res_center.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        xs_c = coords_c[0::2]
        ys_c = coords_c[1::2]
        self.assertAlmostEqual((min(xs_c) + max(xs_c)) / 2.0, 0.0, delta=1.0)
        self.assertAlmostEqual((min(ys_c) + max(ys_c)) / 2.0, 0.0, delta=1.0)

        res_topleft = shape_transform(self.context, drawing=self.sq, mode="Skew", angle_x=30, angle_y=0, anchor="topleft")
        coords_tl = [float(t) for t in res_topleft.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        self.assertAlmostEqual(min(coords_tl[0::2]), 0.0, delta=0.5)
        self.assertAlmostEqual(min(coords_tl[1::2]), 0.0, delta=0.5)

        res_abs = shape_transform(self.context, drawing=self.sq, mode="Skew", angle_x=30, angle_y=0, anchor="absolute")
        coords_abs = [float(t) for t in res_abs.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        self.assertAlmostEqual((min(coords_abs[0::2]) + max(coords_abs[0::2])) / 2.0, 500.0, delta=1.0)
        self.assertAlmostEqual((min(coords_abs[1::2]) + max(coords_abs[1::2])) / 2.0, 300.0, delta=1.0)

    def test_skew_graph_engine_evaluation(self):
        """Verifica la integración y evaluación de Skew en GraphEngine."""
        graph = {
            'nodes': [
                {
                    'id': 1,
                    'type': 'Shape/Shape Transform',
                    'properties': {
                        'shape': self.sq,
                        'mode': 'Skew',
                        'angle_x': '25',
                        'angle_y': '10',
                        'anchor': 'center'
                    },
                    'inputs': []
                }
            ],
            'links': []
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        res = engine.evaluate_data_node(1, self.context, output_slot_index=0)
        self.assertIsInstance(res, str)
        self.assertTrue(res.startswith("m "))
        self.assertNotIn("[Err", res)

    def test_round_corners_bezier(self):
        """Verifica el redondeo de esquinas con curvas Bézier cúbicas."""
        res_round = shape_transform(self.context, drawing=self.sq, mode="Round Corners", radius=20, corner_mode="Round", anchor="original")
        self.assertTrue(res_round.startswith("m "))
        # Debe contener comandos 'b' para las curvas en las esquinas
        self.assertIn(" b ", res_round)
        # El número de tokens debe ser mayor que el cuadrado base
        self.assertGreater(len(res_round.split()), len(self.sq.split()))

    def test_round_corners_bevel(self):
        """Verifica el chaflán/biselado de esquinas (Bevel con rectas 'l')."""
        res_bevel = shape_transform(self.context, drawing=self.sq, mode="Round Corners", radius=20, corner_mode="Bevel", anchor="original")
        self.assertTrue(res_bevel.startswith("m "))
        # Bevel corta las esquinas con segmentos rectos 'l' y no debe generar 'b'
        self.assertNotIn(" b ", res_bevel)
        self.assertIn(" l ", res_bevel)

    def test_round_corners_anchors(self):
        """Verifica los modos de anclaje de Round Corners: center, topleft, absolute."""
        res_center = shape_transform(self.context, drawing=self.sq, mode="Round Corners", radius=15, anchor="center")
        coords_c = [float(t) for t in res_center.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        xs_c = coords_c[0::2]
        ys_c = coords_c[1::2]
        self.assertAlmostEqual((min(xs_c) + max(xs_c)) / 2.0, 0.0, delta=1.0)
        self.assertAlmostEqual((min(ys_c) + max(ys_c)) / 2.0, 0.0, delta=1.0)

        res_topleft = shape_transform(self.context, drawing=self.sq, mode="Round Corners", radius=15, anchor="topleft")
        coords_tl = [float(t) for t in res_topleft.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        self.assertAlmostEqual(min(coords_tl[0::2]), 0.0, delta=0.5)
        self.assertAlmostEqual(min(coords_tl[1::2]), 0.0, delta=0.5)

        res_abs = shape_transform(self.context, drawing=self.sq, mode="Round Corners", radius=15, anchor="absolute")
        coords_abs = [float(t) for t in res_abs.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        self.assertAlmostEqual((min(coords_abs[0::2]) + max(coords_abs[0::2])) / 2.0, 500.0, delta=1.0)
        self.assertAlmostEqual((min(coords_abs[1::2]) + max(coords_abs[1::2])) / 2.0, 300.0, delta=1.0)

    def test_round_corners_graph_engine_evaluation(self):
        """Verifica la integración y evaluación de Round Corners en GraphEngine."""
        graph = {
            'nodes': [
                {
                    'id': 1,
                    'type': 'Shape/Shape Transform',
                    'properties': {
                        'shape': self.sq,
                        'mode': 'Round Corners',
                        'radius': '15',
                        'corner_mode': 'Round',
                        'anchor': 'center'
                    },
                    'inputs': []
                }
            ],
            'links': []
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        res = engine.evaluate_data_node(1, self.context, output_slot_index=0)
        self.assertIsInstance(res, str)
        self.assertTrue(res.startswith("m "))
        self.assertIn(" b ", res)
        self.assertNotIn("[Err", res)

    def test_flexor_arch_bend(self):
        """Verifica la deformación y curvado a lo largo de un arco paramétrico."""
        res_arch = shape_transform(self.context, drawing=self.rect, mode="Flexor", curve="45", bend_t=1.0, anchor="center")
        self.assertTrue(res_arch.startswith("m "))
        # Debe haber subdividido el contorno para curvar suavemente
        self.assertGreater(len(res_arch.split()), len(self.rect.split()))

    def test_flexor_guide_spline(self):
        """Verifica la deformación y seguimiento a lo largo de una curva directriz Bézier ASS."""
        guide = "m 0 0 b 50 -60 150 -60 200 0"
        res_guide = shape_transform(self.context, drawing=self.rect, mode="Flexor", curve=guide, bend_t=1.0, anchor="center")
        self.assertTrue(res_guide.startswith("m "))
        self.assertGreater(len(res_guide.split()), 30)

    def test_flexor_anchors(self):
        """Verifica los modos de anclaje de Flexor: center, topleft, absolute."""
        res_center = shape_transform(self.context, drawing=self.rect, mode="Flexor", curve="30", bend_t=1.0, anchor="center")
        coords_c = [float(t) for t in res_center.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        xs_c = coords_c[0::2]
        ys_c = coords_c[1::2]
        self.assertAlmostEqual((min(xs_c) + max(xs_c)) / 2.0, 0.0, delta=1.0)
        self.assertAlmostEqual((min(ys_c) + max(ys_c)) / 2.0, 0.0, delta=1.0)

        res_topleft = shape_transform(self.context, drawing=self.rect, mode="Flexor", curve="30", bend_t=1.0, anchor="topleft")
        coords_tl = [float(t) for t in res_topleft.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        self.assertAlmostEqual(min(coords_tl[0::2]), 0.0, delta=0.5)
        self.assertAlmostEqual(min(coords_tl[1::2]), 0.0, delta=0.5)

        res_abs = shape_transform(self.context, drawing=self.rect, mode="Flexor", curve="30", bend_t=1.0, anchor="absolute")
        coords_abs = [float(t) for t in res_abs.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        self.assertAlmostEqual((min(coords_abs[0::2]) + max(coords_abs[0::2])) / 2.0, 500.0, delta=1.0)
        self.assertAlmostEqual((min(coords_abs[1::2]) + max(coords_abs[1::2])) / 2.0, 300.0, delta=1.0)

    def test_flexor_graph_engine_evaluation(self):
        """Verifica la integración y evaluación de Flexor en GraphEngine."""
        graph = {
            'nodes': [
                {
                    'id': 1,
                    'type': 'Shape/Shape Transform',
                    'properties': {
                        'shape': self.rect,
                        'mode': 'Flexor',
                        'curve': '35',
                        'bend_t': '1.0',
                        'anchor': 'center'
                    },
                    'inputs': []
                }
            ],
            'links': []
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        res = engine.evaluate_data_node(1, self.context, output_slot_index=0)
        self.assertIsInstance(res, str)
        self.assertTrue(res.startswith("m "))
        self.assertNotIn("[Err", res)

    def test_distort_square_to_diamond(self):
        """Verifica la deformación polar morfológica hacia una forma objetivo (Distort)."""
        diamond = "m 50 0 l 100 50 l 50 100 l 0 50"
        # Con t=0.0, la forma se mantiene idéntica
        res_t0 = shape_transform(self.context, drawing=self.sq, mode="Distort", target_shape=diamond, t=0.0, anchor="original")
        self.assertIn("m 0 0", res_t0)

        # Con t=1.0, se deforma hacia el rombo objetivo con subdivisión adaptativa
        res_t1 = shape_transform(self.context, drawing=self.sq, mode="Distort", target_shape=diamond, t=1.0, anchor="center")
        self.assertTrue(res_t1.startswith("m "))
        self.assertGreater(len(res_t1.split()), len(self.sq.split()))

    def test_distort_anchors(self):
        """Verifica los modos de anclaje de Distort: center, topleft, absolute."""
        diamond = "m 50 0 l 100 50 l 50 100 l 0 50"
        res_center = shape_transform(self.context, drawing=self.sq, mode="Distort", target_shape=diamond, t=0.8, anchor="center")
        coords_c = [float(t) for t in res_center.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        xs_c = coords_c[0::2]
        ys_c = coords_c[1::2]
        self.assertAlmostEqual((min(xs_c) + max(xs_c)) / 2.0, 0.0, delta=1.0)
        self.assertAlmostEqual((min(ys_c) + max(ys_c)) / 2.0, 0.0, delta=1.0)

        res_topleft = shape_transform(self.context, drawing=self.sq, mode="Distort", target_shape=diamond, t=0.8, anchor="topleft")
        coords_tl = [float(t) for t in res_topleft.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        self.assertAlmostEqual(min(coords_tl[0::2]), 0.0, delta=0.5)
        self.assertAlmostEqual(min(coords_tl[1::2]), 0.0, delta=0.5)

        res_abs = shape_transform(self.context, drawing=self.sq, mode="Distort", target_shape=diamond, t=0.8, anchor="absolute")
        coords_abs = [float(t) for t in res_abs.split() if t.replace('-','',1).replace('.','',1).isdigit()]
        self.assertAlmostEqual((min(coords_abs[0::2]) + max(coords_abs[0::2])) / 2.0, 500.0, delta=1.0)
        self.assertAlmostEqual((min(coords_abs[1::2]) + max(coords_abs[1::2])) / 2.0, 300.0, delta=1.0)

    def test_distort_graph_engine_evaluation(self):
        """Verifica la integración y evaluación de Distort en GraphEngine."""
        diamond = "m 50 0 l 100 50 l 50 100 l 0 50"
        graph = {
            'nodes': [
                {
                    'id': 1,
                    'type': 'Shape/Shape Transform',
                    'properties': {
                        'shape': self.sq,
                        'mode': 'Distort',
                        'target_shape': diamond,
                        't': '0.75',
                        'anchor': 'center'
                    },
                    'inputs': []
                }
            ],
            'links': []
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        res = engine.evaluate_data_node(1, self.context, output_slot_index=0)
        self.assertIsInstance(res, str)
        self.assertTrue(res.startswith("m "))
        self.assertNotIn("[Err", res)


if __name__ == '__main__':
    unittest.main()

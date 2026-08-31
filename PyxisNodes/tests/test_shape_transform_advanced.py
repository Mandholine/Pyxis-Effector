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

        # Test con corner_mode = 'Bevel' (Bisel / Acabado chaflán)
        graph['nodes'][0]['properties']['corner_mode'] = 'Bevel'
        engine_bevel = GraphEngine(graph, 1280, 720, 41.7)
        res_bevel = engine_bevel.evaluate_data_node(1, self.context, output_slot_index=0)
        self.assertIsInstance(res_bevel, str)
        self.assertTrue(res_bevel.startswith("m "))
        self.assertNotIn(" b ", res_bevel)
        self.assertIn(" l ", res_bevel)

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

    def test_distort_with_bezier_target_and_cache(self):
        """Verifica la deformación morfométrica hacia un objetivo con curvas Bézier (corazón) y uso de caché de 2px."""
        heart = "m 50 20 b 50 0 100 0 100 40 b 100 70 50 100 50 100 b 50 100 0 70 0 40 b 0 0 50 0 50 20"
        from nodes.shape_nodes import _SHAPE_NORMALIZED_CACHE
        # Comprobar primera evaluación
        res1 = shape_transform(self.context, drawing=self.sq, mode="Distort", target_shape=heart, t=1.0, anchor="center")
        self.assertTrue(res1.startswith("m "))
        self.assertGreater(len(res1.split()), 20)
        # Comprobar que la forma objetivo se guardó en la caché con paso de 2px
        self.assertIn((heart, 2.0), _SHAPE_NORMALIZED_CACHE)

        # Comprobar segunda evaluación (hit de caché)
        res2 = shape_transform(self.context, drawing=self.sq, mode="Distort", target_shape=heart, t=0.5, anchor="center")
        self.assertTrue(res2.startswith("m "))

    def test_tensor_coons_patch(self):
        """Verifica la deformación bilineal Coons Patch (Tensor) respecto a una caja envolvente."""
        res_tensor = shape_transform(self.context, drawing=self.sq, mode="Tensor", target_box=self.rect, t=1.0, anchor="center")
        self.assertTrue(res_tensor.startswith("m "))
        self.assertNotIn("[Err", res_tensor)

    def test_round_corners_negative_radius_reflection(self):
        """Verifica el redondeo cóncavo con radio negativo usando reflexión especular."""
        res_neg = shape_transform(self.context, drawing=self.sq, mode="Round Corners", radius=-15.0, corner_mode="Round", anchor="center")
        self.assertTrue(res_neg.startswith("m "))
        self.assertIn(" b ", res_neg)

    def test_maxloop_iterator_slot_with_distort(self):
        """Verifica que MaxLoop propague correctamente el iterador dinámico a través de Loops/Module hacia Distort."""
        triangle = "m 50 0 l 0 86 l 100 86 l 50 0"
        star = "m 38 36 l 0 36 l 31 59 l 20 95 l 50 72 l 81 94 l 69 59 l 100 36 l 62 36 l 50 0 l 38 36"
        graph = {
            'nodes': [
                {'id': 1, 'type': 'Loops/Main Loop', 'properties': {'iterador': 'line'}, 'inputs': []},
                {'id': 2, 'type': 'Loops/MaxLoop', 'properties': {'modo': 'FBF', 'step_ms': '41.7', 'var_name': 'j'}, 'inputs': [{'link': 1}]},
                {'id': 3, 'type': 'Loops/Module', 'properties': {'iter': 'i', 'total': 'N'}, 'inputs': [{'link': 2}, {'link': 3}]},
                {'id': 4, 'type': 'Shape/Shape Transform', 'properties': {'shape': triangle, 'target_shape': star, 'mode': 'Distort', 'anchor': 'center'}, 'inputs': [{'link': None}, {'link': None}, {'link': 4}]},
                {'id': 5, 'type': 'System/Output', 'properties': {'apply_to': 'All Lines', 'origin_align': 5}, 'inputs': [{'link': 5}, None, None, None, None, {'link': 6}]}
            ],
            'links': [
                [1, 1, 0, 2, 0, 'bucle'],
                [2, 2, 1, 3, 0, 'data'],
                [3, 2, 2, 3, 1, 'data'],
                [4, 3, 0, 4, 2, 'data'],
                [5, 2, 0, 5, 0, 'bucle'],
                [6, 4, 0, 5, 5, 'data']
            ]
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        raw_line = 'Dialogue: 0,0:00:00.00,0:00:00.20,Default,,0,0,0,,{\\k20}Prueba'
        styles = {'Default': {'fontname': 'Arial', 'fontsize': 40}}
        engine.process_single([{'raw': raw_line}], styles)
        self.assertEqual(len(engine.all_generated_lines), 5)
        # El frame 0 es el triángulo inicial y el frame 4 es la estrella completa
        first_line = engine.all_generated_lines[0]['text']
        last_line = engine.all_generated_lines[-1]['text']
        self.assertNotEqual(first_line, last_line)

    def test_tensor_graph_engine_with_target_box(self):
        """Verifica la evaluación del modo Tensor en GraphEngine con la especificación de puertos de frontend."""
        box = "m 0 0 l 200 0 l 200 100 l 0 100"
        graph = {
            'nodes': [
                {'id': 1, 'type': 'Shape/Shape Transform', 'properties': {'shape': self.sq, 'target_box': box, 'mode': 'Tensor', 't': '1.0', 'anchor': 'center'}, 'inputs': []}
            ],
            'links': []
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        res = engine.evaluate_data_node(1, self.context, output_slot_index=0)
        self.assertTrue(res.startswith("m "))
        self.assertNotIn("[Err", res)

    def test_skew_with_t_interpolation(self):
        """Verifica que el modo Skew interpole los ángulos proporcionalmente con Factor (t)."""
        # Con t=0.0 -> sin inclinación
        res_t0 = shape_transform(self.context, drawing=self.sq, mode="Skew", angle_x=45, angle_y=0, t=0.0, anchor="original")
        self.assertIn("m 0 0", res_t0)

        # Con t=1.0 -> inclinación completa
        res_t1 = shape_transform(self.context, drawing=self.sq, mode="Skew", angle_x=45, angle_y=0, t=1.0, anchor="original")
        self.assertNotEqual(res_t0, res_t1)

    def test_round_corners_with_t_interpolation(self):
        """Verifica que el modo Round Corners interpole el radio con Factor (t)."""
        # Con t=0.0 -> radio 0 (sin redondeo)
        res_t0 = shape_transform(self.context, drawing=self.sq, mode="Round Corners", radius=20, t=0.0, corner_mode="Round", anchor="original")
        self.assertNotIn(" b ", res_t0)

        # Con t=1.0 -> radio 20 (esquinas redondeadas con Bézier 'b')
        res_t1 = shape_transform(self.context, drawing=self.sq, mode="Round Corners", radius=20, t=1.0, corner_mode="Round", anchor="original")
        self.assertIn(" b ", res_t1)


class DummyPathLine:
    def __init__(self, left=100.0, right=300.0, width=200.0, center=200.0, middle=50.0):
        self.left = left
        self.right = right
        self.width = width
        self.center = center
        self.middle = middle
        self.text = "Hello World"


class DummyPathChar:
    def __init__(self, left=100.0, width=20.0, center=110.0, i=1, n=5, line=None):
        self.left = left
        self.width = width
        self.center = center
        self.middle = 50.0
        self.i = i
        self.n = n
        self.line = line


class TestTextOnPath(unittest.TestCase):
    def setUp(self):
        from nodes.shape_nodes import text_on_path_core, text_on_path_node, NODE_REGISTRY
        self.text_on_path_core = text_on_path_core
        self.text_on_path_node = text_on_path_node
        self.NODE_REGISTRY = NODE_REGISTRY

        self.line = DummyPathLine(left=100.0, right=300.0, width=200.0, center=200.0, middle=50.0)
        self.char1 = DummyPathChar(left=100.0, width=20.0, center=110.0, i=1, n=5, line=self.line)
        self.char3 = DummyPathChar(left=180.0, width=40.0, center=200.0, i=3, n=5, line=self.line)
        self.char5 = DummyPathChar(left=280.0, width=20.0, center=290.0, i=5, n=5, line=self.line)
        self.context_c1 = {'active_line': self.line, 'active_unit': self.char1}
        self.context_c3 = {'active_line': self.line, 'active_unit': self.char3}
        self.context_c5 = {'active_line': self.line, 'active_unit': self.char5}

        # Trayectoria horizontal recta de 400px
        self.path_line = "m 0 100 l 400 100"
        # Trayectoria Bézier
        self.path_bezier = "m 0 100 b 100 0 300 200 400 100"

    def test_center_alignment(self):
        """En modo Center, el centro de la línea queda en el centro del trazo (L=400, centro=200)."""
        comb, pos, angle, x, y, tan = self.text_on_path_core(
            self.path_line, context=self.context_c3, mode="Center"
        )
        self.assertAlmostEqual(x, 200.0, delta=1.0)
        self.assertAlmostEqual(y, 100.0, delta=1.0)
        self.assertAlmostEqual(angle, 0.0, delta=1.0)
        self.assertIn("pos(200,100)", pos)

        comb1, pos1, _, x1, y1, _ = self.text_on_path_core(
            self.path_line, context=self.context_c1, mode="Center"
        )
        self.assertAlmostEqual(x1, 110.0, delta=1.0)

    def test_left_alignment(self):
        """En modo Left, el inicio de la línea queda en el inicio de la curva."""
        comb, pos, angle, x, y, _ = self.text_on_path_core(
            self.path_line, context=self.context_c1, mode="Left", offset=50.0
        )
        self.assertAlmostEqual(x, 60.0, delta=1.0)
        self.assertAlmostEqual(y, 100.0, delta=1.0)

    def test_right_alignment(self):
        """En modo Right, el final de la línea queda en el extremo de la curva."""
        comb, pos, angle, x, y, _ = self.text_on_path_core(
            self.path_line, context=self.context_c5, mode="Right", offset=0.0
        )
        self.assertAlmostEqual(x, 390.0, delta=1.0)

    def test_justified_alignment(self):
        """En modo Justified, los caracteres se distribuyen uniformemente."""
        _, _, _, x1, _, _ = self.text_on_path_core(self.path_line, context=self.context_c1, mode="Justified")
        self.assertAlmostEqual(x1, 0.0, delta=1.0)

        _, _, _, x3, _, _ = self.text_on_path_core(self.path_line, context=self.context_c3, mode="Justified")
        self.assertAlmostEqual(x3, 200.0, delta=1.0)

        _, _, _, x5, _, _ = self.text_on_path_core(self.path_line, context=self.context_c5, mode="Justified")
        self.assertAlmostEqual(x5, 400.0, delta=1.0)

    def test_normal_offset_and_angle_offset(self):
        """Verifica el desplazamiento perpendicular y la rotación adicional."""
        comb, pos, angle, x, y, tan = self.text_on_path_core(
            self.path_line, context=self.context_c3, mode="Center", normal_offset=25.0, angle_offset=15.0
        )
        self.assertAlmostEqual(x, 200.0, delta=1.0)
        self.assertAlmostEqual(y, 125.0, delta=1.0)
        self.assertAlmostEqual(angle, 15.0, delta=1.0)
        self.assertIn("\\frz15", comb)

    def test_bezier_tangent_and_rotation(self):
        """Verifica el muestreo de una trayectoria con curvas Bézier."""
        comb, pos, angle, x, y, tan = self.text_on_path_core(
            self.path_bezier, context=self.context_c3, mode="Center"
        )
        self.assertTrue(comb.startswith("\\pos("))
        self.assertIn("\\frz", comb)
        self.assertIsInstance(angle, float)

    def test_graphengine_evaluation_multislot(self):
        """Verifica la evaluación en GraphEngine a través de todos los slots de salida."""
        graph = {
            'nodes': [
                {
                    'id': 1,
                    'type': 'Functions/Text on Path',
                    'properties': {
                        'shape': self.path_line,
                        'modo': 'Center',
                        'offset': '10',
                        'normal_offset': '5',
                        'angle_offset': '0'
                    },
                    'inputs': []
                }
            ],
            'links': []
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)

        # Slot 0: Combined Tag
        tag = engine.evaluate_data_node(1, self.context_c3, output_slot_index=0)
        self.assertTrue(tag.startswith("\\pos("))
        self.assertIn("\\frz", tag)

        # Slot 1: \pos Tag
        pos = engine.evaluate_data_node(1, self.context_c3, output_slot_index=1)
        self.assertTrue(pos.startswith("\\pos("))
        self.assertNotIn("\\frz", pos)

        # Slot 2: Angle (\frz)
        frz = engine.evaluate_data_node(1, self.context_c3, output_slot_index=2)
        self.assertEqual(float(frz), 0.0)

        # Slot 3: X
        val_x = engine.evaluate_data_node(1, self.context_c3, output_slot_index=3)
        self.assertAlmostEqual(float(val_x), 210.0, delta=1.0)

        # Slot 4: Y
        val_y = engine.evaluate_data_node(1, self.context_c3, output_slot_index=4)
        self.assertAlmostEqual(float(val_y), 105.0, delta=1.0)

    def test_registry_aliases(self):
        """Verifica que el nodo esté registrado con sus diferentes nombres y alias."""
        self.assertIn("Functions/Text on Path", self.NODE_REGISTRY)
        self.assertIn("Text on Path", self.NODE_REGISTRY)
        self.assertIn("Texto en trazado", self.NODE_REGISTRY)


if __name__ == '__main__':
    unittest.main()

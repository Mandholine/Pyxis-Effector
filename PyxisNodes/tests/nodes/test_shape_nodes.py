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

"""Pruebas unitarias completas para nodos de formas vectoriales (Shape Nodes).

Incluye:
- Shapes Library (80 formas maestras y alias)
- Shape Slicer (los 22 motores de corte poligonal)
- Shape Walker (recorredor y segmentacion de curvas de Bezier y lineas)
- Transformaciones avanzadas (escalado, rotacion, pivote, deformaciones)
- Bordes concentricos y Clip Gradient
"""

import math
import unittest

from clipper_engine import ClipperEngine
from node_engine import GraphEngine
from nodes.shape_nodes import (
    eval_shapes_lib_node,
    RAW_PRESET_SHAPES,
    SHAPES_LIB_MAP,
    parse_assdraw_segments,
    shape_walker_core,
    shape_walker_node,
    shape_manipulator,
    shape_filter,
    shape_transform,
    shape_concentric_borders_node,
    clip_gradient_node
)

ALL_22_ENGINES = [
    "Rejilla 1D/2D",
    "hex",
    "tri",
    "dia",
    "ring",
    "ray",
    "quad",
    "bez",
    "jigsaw",
    "voronoi",
    "delaunay",
    "ashlar",
    "brick",
    "mondrian",
    "herringbone",
    "scallop",
    "web",
    "rhombille",
    "octagon",
    "kagome",
    "truchet",
    "circuit",
    "pattern"
]

TEST_SHAPE_SQUARE = "m 0 0 l 100 0 l 100 100 l 0 100"
TEST_SHAPE_COMPLEX = "m 0 0 l 200 0 l 200 50 l 50 50 l 50 150 l 200 150 l 200 200 l 0 200"


class TestShapesLibrary(unittest.TestCase):
    """Pruebas para la biblioteca de 80 formas vectoriales de Pyxis."""

    def setUp(self):
        self.context = {}

    def test_all_80_shapes_return_non_empty_ass_draw(self):
        self.assertGreaterEqual(len(RAW_PRESET_SHAPES), 80)
        for forma_key in RAW_PRESET_SHAPES.keys():
            with self.subTest(forma=forma_key):
                res = eval_shapes_lib_node(self.context, forma=forma_key)
                self.assertTrue(isinstance(res, str) and len(res) > 5, f"Fallo forma '{forma_key}'")
                self.assertTrue(res.startswith("m "), f"Forma '{forma_key}' no inicia con 'm '")

    def test_shortened_and_legacy_names(self):
        pairs = [
            ("Esq. Curva", "Esquinas Redondeadas"),
            ("Estrella 4", "Estrella de 4 Puntas"),
            ("Flecha Der.", "Flecha Derecha"),
            ("Globo Texto", "Burbuja de Dialogo"),
        ]
        for short_name, long_name in pairs:
            if short_name in SHAPES_LIB_MAP and long_name in SHAPES_LIB_MAP:
                res1 = eval_shapes_lib_node(self.context, forma=short_name)
                res2 = eval_shapes_lib_node(self.context, forma=long_name)
                self.assertEqual(res1, res2, f"Discrepancia entre alias '{short_name}' y '{long_name}'")


class TestShapeSlicer(unittest.TestCase):
    """Pruebas para el motor de segmentacion poligonal y los 22 algoritmos de corte."""

    def test_all_22_engines_direct_slicing(self):
        for engine in ALL_22_ENGINES:
            with self.subTest(engine=engine):
                pieces = ClipperEngine.slice_grid(
                    TEST_SHAPE_SQUARE,
                    engine_mode=engine,
                    cols=3,
                    rows=3,
                    size_x=20,
                    size_y=20,
                    accel_x=1.0,
                    accel_y=1.0,
                    order=79
                )
                self.assertGreater(len(pieces), 0, f"Motor '{engine}' no genero piezas.")
                for idx, p in enumerate(pieces):
                    code = p.get("code", "")
                    cx = p.get("cx")
                    cy = p.get("cy")
                    self.assertTrue(code and str(code).strip().startswith("m "), f"Pieza {idx} de {engine} invalida")
                    self.assertIsNotNone(cx)
                    self.assertIsNotNone(cy)
                    self.assertFalse(math.isnan(cx))
                    self.assertFalse(math.isnan(cy))

    def test_complex_non_convex_shape(self):
        for engine in ALL_22_ENGINES:
            with self.subTest(engine=engine):
                pieces = ClipperEngine.slice_grid(
                    TEST_SHAPE_COMPLEX,
                    engine_mode=engine,
                    cols=4,
                    rows=4,
                    size_x=25,
                    size_y=25,
                    overlap=1.0
                )
                self.assertGreater(len(pieces), 0, f"Fallo motor '{engine}' en silueta compleja")
                for p in pieces:
                    self.assertTrue(p.get("code", "").startswith("m "))

    def test_shape_slicer_graph_engine_evaluation(self):
        for engine in ALL_22_ENGINES:
            with self.subTest(engine=engine):
                node = {
                    "id": 101,
                    "type": "Shape/Shape Slicer",
                    "properties": {
                        "modo": engine,
                        "shape": TEST_SHAPE_SQUARE,
                        "Cols": 2,
                        "Rows": 2,
                        "Size X": 20,
                        "Size Y": 20,
                        "out_mode": "shape"
                    },
                    "inputs": []
                }
                engine_inst = GraphEngine({"nodes": [node], "links": []})
                ctx = {"j": 1}
                out_shape = engine_inst.evaluate_data_node(101, ctx)
                self.assertTrue(isinstance(out_shape, str) and out_shape.startswith("m "), f"Fallo evaluacion de {engine}")

    def test_spatial_sorting_radial(self):
        pieces = ClipperEngine.slice_grid(
            TEST_SHAPE_SQUARE,
            engine_mode="hex",
            size_x=15,
            order=5
        )
        self.assertGreaterEqual(len(pieces), 2)
        d_first = math.sqrt((pieces[0]["cx"] - 50)**2 + (pieces[0]["cy"] - 50)**2)
        d_last = math.sqrt((pieces[-1]["cx"] - 50)**2 + (pieces[-1]["cy"] - 50)**2)
        self.assertLessEqual(d_first, d_last + 1.0)


class TestShapeWalker(unittest.TestCase):
    """Pruebas del algoritmo de recorrido de trazados y recorte parametrico."""

    def test_parse_segments_line(self):
        shape = "m 0 0 l 100 0 l 100 50"
        contours = parse_assdraw_segments(shape)
        self.assertEqual(len(contours), 1)
        self.assertEqual(contours[0]['start'], (0.0, 0.0))
        self.assertEqual(len(contours[0]['segments']), 2)
        self.assertEqual(contours[0]['segments'][0]['type'], 'l')
        self.assertEqual(contours[0]['segments'][0]['p0'], (0.0, 0.0))
        self.assertEqual(contours[0]['segments'][0]['p1'], (100.0, 0.0))

    def test_parse_segments_bezier(self):
        shape = "m 0 0 b 25 50 75 50 100 0"
        contours = parse_assdraw_segments(shape)
        self.assertEqual(len(contours), 1)
        self.assertEqual(len(contours[0]['segments']), 1)
        b_seg = contours[0]['segments'][0]
        self.assertEqual(b_seg['type'], 'b')
        self.assertEqual(b_seg['p0'], (0.0, 0.0))
        self.assertEqual(b_seg['p1'], (25.0, 50.0))
        self.assertEqual(b_seg['p2'], (75.0, 50.0))
        self.assertEqual(b_seg['p3'], (100.0, 0.0))

    def test_line_cut_half(self):
        shape = "m 0 0 l 100 0"
        cut_shp, tx, ty, angle, cut_len, total_len = shape_walker_core(shape, progress=0.5, start_t=0.0)
        self.assertIn("m 0 0", cut_shp)
        self.assertIn("l 50", cut_shp)
        self.assertAlmostEqual(tx, 50.0, delta=0.1)
        self.assertAlmostEqual(ty, 0.0, delta=0.1)
        self.assertAlmostEqual(cut_len, 50.0, delta=0.1)
        self.assertAlmostEqual(total_len, 100.0, delta=0.1)

    def test_line_cut_window_trim(self):
        shape = "m 0 0 l 100 0"
        cut_shp, tx, ty, angle, cut_len, total_len = shape_walker_core(shape, progress=0.7, start_t=0.2)
        self.assertIn("m 20", cut_shp)
        self.assertIn("l 70", cut_shp)
        self.assertAlmostEqual(tx, 70.0, delta=0.1)
        self.assertAlmostEqual(ty, 0.0, delta=0.1)
        self.assertAlmostEqual(cut_len, 50.0, delta=0.1)

    def test_shape_walker_node_pure_shape_out(self):
        shape = "m 0 0 l 100 0"
        final_shp, pos_str, angle, cut_len, tip_x, tip_y = shape_walker_node(None, shape=shape, progress=0.5)
        self.assertTrue(final_shp.startswith("m "))
        self.assertNotIn("\\pos", final_shp)
        self.assertNotIn("{\\", final_shp)

    def test_shape_walker_node_unit_position_inheritance(self):
        class DummyUnit:
            center = 640.0
            middle = 360.0
        ctx = {"active_unit": DummyUnit()}
        shape = "m 0 0 l 100 0"
        final_shp, pos_str, angle, cut_len, tip_x, tip_y = shape_walker_node(ctx, shape=shape, progress=0.5)
        self.assertEqual(tip_x, 690.0)
        self.assertEqual(tip_y, 360.0)
        self.assertEqual(pos_str, "\\pos(690,360)")
        self.assertTrue(final_shp.startswith("m "))
        self.assertNotIn("\\pos", final_shp)

    def test_shape_walker_node_line_position_inheritance(self):
        class DummyLine:
            center = 500.0
            middle = 200.0
        ctx = {"active_line": DummyLine()}
        shape = "m 0 0 l 100 0"
        final_shp, pos_str, angle, cut_len, tip_x, tip_y = shape_walker_node(ctx, shape=shape, progress=0.5)
        self.assertEqual(tip_x, 550.0)
        self.assertEqual(tip_y, 200.0)
        self.assertEqual(pos_str, "\\pos(550,200)")

    def test_shape_walker_node_fx_override(self):
        class DummyUnit:
            center = 640.0
            middle = 360.0
        ctx = {"active_unit": DummyUnit(), "fx_pos_x": 100.0, "fx_pos_y": 50.0}
        shape = "m 0 0 l 100 0"
        final_shp, pos_str, angle, cut_len, tip_x, tip_y = shape_walker_node(ctx, shape=shape, progress=0.5)
        self.assertEqual(tip_x, 150.0)
        self.assertEqual(tip_y, 50.0)
        self.assertEqual(pos_str, "\\pos(150,50)")

    def test_shape_walker_node_no_context_fallback(self):
        shape = "m 0 0 l 100 0"
        final_shp, pos_str, angle, cut_len, tip_x, tip_y = shape_walker_node(None, shape=shape, progress=0.5)
        self.assertEqual(tip_x, 50.0)
        self.assertEqual(tip_y, 0.0)
        self.assertEqual(pos_str, "\\pos(50,0)")


class TestShapeTransformAdvanced(unittest.TestCase):
    """Pruebas de transformacion, rotacion, pivote y deformaciones."""

    def test_shape_manipulator_scale(self):
        shape = "m 0 0 l 100 0 l 100 100 l 0 100"
        transformed = shape_manipulator(None, drawing=shape, scale_x=2.0, scale_y=2.0, mode="origin")
        self.assertTrue(transformed.startswith("m 0 0"))
        self.assertIn("l 200 0", transformed)
        self.assertIn("l 200 200", transformed)

    def test_shape_manipulator_translation(self):
        shape = "m 0 0 l 10 0"
        transformed = shape_manipulator(None, drawing=shape, offset_x=50.0, offset_y=30.0, mode="origin")
        self.assertTrue(transformed.startswith("m 50 30"))
        self.assertIn("l 60 30", transformed)

    def test_shape_manipulator_redraw_densify(self):
        # Curva Bézier cúbica
        shape = "m 0 0 b 0 50 50 100 100 100"
        # Densificar con densidad positiva (subdivide manteniendo curvas 'b')
        redrawn = shape_manipulator(None, drawing=shape, op_mode="Redibujar", density=10.0)
        self.assertTrue(redrawn.startswith("m 0 0"))
        self.assertIn("b ", redrawn)
        # Debe haber múltiples 'b' por la subdivisión
        b_count = redrawn.count("b ")
        self.assertGreater(b_count, 1)

    def test_shape_manipulator_redraw_simplify(self):
        # Curva Bézier cúbica
        shape = "m 0 0 b 0 50 50 100 100 100"
        # Simplificar con densidad negativa (low-poly con rectas 'l')
        simplified = shape_manipulator(None, drawing=shape, op_mode="Redibujar", density=-25.0)
        self.assertTrue(simplified.startswith("m 0 0"))
        self.assertNotIn("b ", simplified)
        self.assertIn("l ", simplified)

    def test_shape_manipulator_rotate_3d(self):
        shape = "m -50 -50 l 50 -50 l 50 50 l -50 50"
        rotated = shape_manipulator(None, drawing=shape, op_mode="Giro 3D", angle_x=45.0, angle_y=30.0, angle_z=60.0)
        self.assertTrue(rotated.startswith("m "))
        self.assertIn("l ", rotated)
        tokens = rotated.split()
        self.assertEqual(len(tokens), 12)

    def test_shape_manipulator_rotate_3d_z_pure(self):
        shape = "m -50 -50 l 50 -50 l 50 50 l -50 50"
        # Giro puro en Z (90°) alrededor del centro (0,0)
        rotated = shape_manipulator(None, drawing=shape, op_mode="Giro 3D", angle_x=0.0, angle_y=0.0, angle_z=90.0)
        self.assertTrue(rotated.startswith("m 50 -50"))
        self.assertIn("l 50 50", rotated)
        self.assertIn("l -50 50", rotated)
        self.assertIn("l -50 -50", rotated)

    def test_shape_manipulator_reflect_y(self):
        shape = "m 10 10 l 20 10 l 20 30 l 10 30"
        # Reflejo en eje Y (horizontal, pivote en x=15)
        reflected = shape_manipulator(None, drawing=shape, op_mode="Reflejar", axis="y")
        self.assertTrue(reflected.startswith("m 20 10"))
        self.assertIn("l 10 10", reflected)
        self.assertIn("l 10 30", reflected)
        self.assertIn("l 20 30", reflected)

    def test_shape_manipulator_reflect_x(self):
        shape = "m 10 10 l 20 10 l 20 30 l 10 30"
        # Reflejo en eje X (vertical, pivote en y=20)
        reflected = shape_manipulator(None, drawing=shape, op_mode="Reflejar", axis="x")
        self.assertTrue(reflected.startswith("m 10 30"))
        self.assertIn("l 20 30", reflected)
        self.assertIn("l 20 10", reflected)
        self.assertIn("l 10 10", reflected)

    def test_shape_manipulator_reflect_offset(self):
        shape = "m 0 0 l 10 0"
        # Pivote en centro (x=5) + offset_x=10 => piv_x = 15 => m 0 -> 2*15 - 0 = 30; l 10 -> 2*15 - 10 = 20
        reflected = shape_manipulator(None, drawing=shape, op_mode="Reflejar", axis="y", offset_x=10.0)
        self.assertTrue(reflected.startswith("m 30 0"))
        self.assertIn("l 20 0", reflected)

    def test_shape_manipulator_scale_t(self):
        shape = "m 0 0 l 100 0 l 100 100 l 0 100"
        # t=0.0: escala 1.0 (tamaño original)
        res_t0 = shape_manipulator(None, drawing=shape, scale_x=2.0, scale_y=2.0, mode="origin", t=0.0)
        self.assertTrue(res_t0.startswith("m 0 0"))
        self.assertIn("l 100 0", res_t0)
        self.assertIn("l 100 100", res_t0)

        # t=0.5: escala 1.5
        res_t05 = shape_manipulator(None, drawing=shape, scale_x=2.0, scale_y=2.0, mode="origin", t=0.5)
        self.assertIn("l 150 0", res_t05)
        self.assertIn("l 150 150", res_t05)

        # t=1.0: escala 2.0
        res_t1 = shape_manipulator(None, drawing=shape, scale_x=2.0, scale_y=2.0, mode="origin", t=1.0)
        self.assertIn("l 200 0", res_t1)
        self.assertIn("l 200 200", res_t1)

    def test_shape_manipulator_position_t(self):
        shape = "m 0 0 l 10 0"
        res_t0 = shape_manipulator(None, drawing=shape, offset_x=100.0, offset_y=50.0, mode="origin", t=0.0)
        self.assertTrue(res_t0.startswith("m 0 0"))
        self.assertIn("l 10 0", res_t0)

        res_t05 = shape_manipulator(None, drawing=shape, offset_x=100.0, offset_y=50.0, mode="origin", t=0.5)
        self.assertTrue(res_t05.startswith("m 50 25"))
        self.assertIn("l 60 25", res_t05)

        res_t1 = shape_manipulator(None, drawing=shape, offset_x=100.0, offset_y=50.0, mode="origin", t=1.0)
        self.assertTrue(res_t1.startswith("m 100 50"))
        self.assertIn("l 110 50", res_t1)

    def test_shape_manipulator_border_t(self):
        shape = "m 0 0 l 100 0 l 100 100 l 0 100"
        # Con t=0.0 no debe haber offset de Clipper
        res_t0 = shape_manipulator(None, drawing=shape, op_mode="Bordes", offset_border=10.0, mode="origin", t=0.0)
        self.assertIn("m 0 0", res_t0)

        # Con t=1.0 aplica Clipper offset
        res_t1 = shape_manipulator(None, drawing=shape, op_mode="Bordes", offset_border=10.0, mode="origin", t=1.0)
        self.assertTrue(res_t1.startswith("m "))
        self.assertNotEqual(res_t0, res_t1)

    def test_shape_manipulator_rotate_3d_t(self):
        shape = "m -50 -50 l 50 -50 l 50 50 l -50 50"
        # t=0.0: sin rotación
        res_t0 = shape_manipulator(None, drawing=shape, op_mode="Giro 3D", angle_z=90.0, t=0.0)
        self.assertTrue(res_t0.startswith("m -50 -50"))

        # t=1.0: rotación completa 90° Z
        res_t1 = shape_manipulator(None, drawing=shape, op_mode="Giro 3D", angle_z=90.0, t=1.0)
        self.assertTrue(res_t1.startswith("m 50 -50"))

    def test_shape_manipulator_reflect_t(self):
        shape = "m 10 10 l 20 10 l 20 30 l 10 30"
        # t=0.0: forma original intacta
        res_t0 = shape_manipulator(None, drawing=shape, op_mode="Reflejar", axis="y", t=0.0)
        self.assertTrue(res_t0.startswith("m 10 10"))

        # t=0.5: colapsa en el eje de simetría x=15
        res_t05 = shape_manipulator(None, drawing=shape, op_mode="Reflejar", axis="y", t=0.5)
        self.assertTrue(res_t05.startswith("m 15 10"))

        # t=1.0: 100% reflejada
        res_t1 = shape_manipulator(None, drawing=shape, op_mode="Reflejar", axis="y", t=1.0)
        self.assertTrue(res_t1.startswith("m 20 10"))

    def test_shape_manipulator_redraw_t(self):
        shape = "m 0 0 b 0 50 50 100 100 100"
        # t=0.0: no subdivide
        res_t0 = shape_manipulator(None, drawing=shape, op_mode="Redibujar", density=10.0, t=0.0)
        self.assertEqual(res_t0.count("b "), 1)

        # t=1.0: subdivide múltiples veces
        res_t1 = shape_manipulator(None, drawing=shape, op_mode="Redibujar", density=10.0, t=1.0)
        self.assertGreater(res_t1.count("b "), 1)

    def test_shape_manipulator_node_engine_dispatch(self):
        # Probar evaluación por GraphEngine con t conectado o por propiedad
        node_def = {
            "id": 1,
            "type": "Shape/Shape Manipulator",
            "properties": {
                "shape": "m 0 0 l 100 0 l 100 100 l 0 100",
                "mode": "Escalar",
                "t": "0.5",
                "scale_x": "200",
                "scale_y": "200",
                "anchor": "origin"
            }
        }
        engine = GraphEngine({"nodes": [node_def], "links": []})
        res = engine.evaluate_data_node(1, context={})
        self.assertTrue(isinstance(res, str))
        self.assertIn("l 150 0", res)
        self.assertIn("l 150 150", res)

    def test_shape_transform_inflate(self):
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        res_t0 = shape_transform(None, drawing=sq, mode="Inflate", t=0.0, anchor="origin")
        self.assertIn("m 0 0", res_t0)
        res_t05 = shape_transform(None, drawing=sq, mode="Inflate", t=0.5, anchor="center")
        self.assertTrue(res_t05.startswith("m "))

    def test_shape_transform_skew_t(self):
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        # t=0.0: sin inclinación
        res_t0 = shape_transform(None, drawing=sq, mode="Skew", angle_x=45.0, angle_y=0.0, anchor="origin", t=0.0)
        self.assertTrue(res_t0.startswith("m 0 0"))
        self.assertIn("l 100 0", res_t0)
        self.assertIn("l 100 100", res_t0)

        # t=1.0: inclinación completa 45° (tan(45°)=1, x' = x + y*1 => para y=100, x' = 100 + 100 = 200)
        res_t1 = shape_transform(None, drawing=sq, mode="Skew", angle_x=45.0, angle_y=0.0, anchor="origin", t=1.0)
        self.assertIn("l 200 100", res_t1)
        self.assertIn("l 100 100", res_t1)

    def test_shape_transform_round_corners_t(self):
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        # t=0.0: esquinas intactas (mantenemos rectas 'l')
        res_t0 = shape_transform(None, drawing=sq, mode="Round Corners", radius=20.0, anchor="origin", t=0.0)
        self.assertNotIn("b ", res_t0)
        self.assertIn("l 100 0", res_t0)

        # t=1.0: esquinas redondeadas con arcos Bézier 'b'
        res_t1 = shape_transform(None, drawing=sq, mode="Round Corners", radius=20.0, anchor="origin", t=1.0)
        self.assertIn("b ", res_t1)

    def test_shape_transform_flexor_t(self):
        line_shp = "m 0 0 l 100 0"
        # t=0.0: forma recta sin doblar
        res_t0 = shape_transform(None, drawing=line_shp, mode="Flexor", curve="45", anchor="origin", t=0.0)
        self.assertTrue(res_t0.startswith("m 0 0"))

        # t=1.0: curvatura activa
        res_t1 = shape_transform(None, drawing=line_shp, mode="Flexor", curve="45", anchor="origin", t=1.0)
        self.assertTrue(res_t1.startswith("m "))
        self.assertNotEqual(res_t0, res_t1)

    def test_shape_transform_graph_engine_skew_and_corners(self):
        node_skew = {
            "id": 301,
            "type": "Shape/Shape Transform",
            "properties": {
                "shape": "m 0 0 l 100 0 l 100 100 l 0 100",
                "mode": "Skew",
                "t": "1.0",
                "angle_x": "45",
                "angle_y": "0",
                "anchor": "origin"
            }
        }
        engine = GraphEngine({"nodes": [node_skew], "links": []})
        out_skew = engine.evaluate_data_node(301, context={})
        self.assertTrue(isinstance(out_skew, str))
        self.assertIn("l 200 100", out_skew)

        node_round = {
            "id": 302,
            "type": "Shape/Shape Transform",
            "properties": {
                "shape": "m 0 0 l 100 0 l 100 100 l 0 100",
                "mode": "Round Corners",
                "t": "1.0",
                "radius": "20.0",
                "anchor": "origin"
            }
        }
        engine_round = GraphEngine({"nodes": [node_round], "links": []})
        out_round = engine_round.evaluate_data_node(302, context={})
        self.assertTrue(isinstance(out_round, str))
        self.assertIn("b ", out_round)

    def test_shape_transform_distort_basic(self):
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        tri = "m 0 0 l 100 0 l 50 100"
        res_t0 = shape_transform(None, drawing=sq, target_shape=tri, mode="Distort", t=0.0, anchor="origin")
        self.assertTrue(isinstance(res_t0, str) and res_t0.startswith("m "))
        res_t1 = shape_transform(None, drawing=sq, target_shape=tri, mode="Distort", t=1.0, anchor="origin")
        self.assertTrue(isinstance(res_t1, str) and res_t1.startswith("m "))

    def test_shape_transform_distort2_progression(self):
        shape_a = "m 0 0 l 100 0 l 100 100 l 0 100"
        shape_b = "m 0 0 l 100 0 l 50 100"
        shape_c = "m 0 0 l 100 50 l 0 100"

        # t = 0.0: debería coincidir con Distort(A -> B, t=0.0)
        res_t0 = shape_transform(None, drawing=shape_a, mid_shape=shape_b, target_shape=shape_c, mode="Distort2", t=0.0, anchor="origin")
        expected_t0 = shape_transform(None, drawing=shape_a, target_shape=shape_b, mode="Distort", t=0.0, anchor="origin")
        self.assertEqual(res_t0, expected_t0)

        # t = 0.5: fin del primer tramo, debería coincidir con Distort(A -> B, t=1.0)
        res_t05 = shape_transform(None, drawing=shape_a, mid_shape=shape_b, target_shape=shape_c, mode="Distort2", t=0.5, anchor="origin")
        expected_t05 = shape_transform(None, drawing=shape_a, target_shape=shape_b, mode="Distort", t=1.0, anchor="origin")
        self.assertEqual(res_t05, expected_t05)

        # t = 1.0: fin del segundo tramo, debería coincidir con Distort(B -> C, t=1.0)
        res_t1 = shape_transform(None, drawing=shape_a, mid_shape=shape_b, target_shape=shape_c, mode="Distort2", t=1.0, anchor="origin")
        expected_t1 = shape_transform(None, drawing=shape_b, target_shape=shape_c, mode="Distort", t=1.0, anchor="origin")
        self.assertEqual(res_t1, expected_t1)

        # Puntos intermedios t = 0.25 (A -> B al 50%) y t = 0.75 (B -> C al 50%)
        res_t025 = shape_transform(None, drawing=shape_a, mid_shape=shape_b, target_shape=shape_c, mode="Distort2", t=0.25, anchor="origin")
        expected_t025 = shape_transform(None, drawing=shape_a, target_shape=shape_b, mode="Distort", t=0.5, anchor="origin")
        self.assertEqual(res_t025, expected_t025)

        res_t075 = shape_transform(None, drawing=shape_a, mid_shape=shape_b, target_shape=shape_c, mode="Distort2", t=0.75, anchor="origin")
        expected_t075 = shape_transform(None, drawing=shape_b, target_shape=shape_c, mode="Distort", t=0.5, anchor="origin")
        self.assertEqual(res_t075, expected_t075)

    def test_shape_transform_distort2_graph_engine_evaluation(self):
        shape_a = "m 0 0 l 100 0 l 100 100 l 0 100"
        shape_b = "m 0 0 l 100 0 l 50 100"
        shape_c = "m 0 0 l 100 50 l 0 100"

        node = {
            "id": 201,
            "type": "Shape/Shape Transform",
            "properties": {
                "mode": "Distort2",
                "shape": shape_a,
                "mid_shape": shape_b,
                "target_shape": shape_c,
                "t": "0.5",
                "energy": "0.35",
                "step_px": "0",
                "anchor": "origin"
            },
            "inputs": []
        }
        engine_inst = GraphEngine({"nodes": [node], "links": []})
        ctx = {"j": 1}
        out_shape = engine_inst.evaluate_data_node(201, ctx)
        self.assertTrue(isinstance(out_shape, str) and out_shape.startswith("m "))
        expected = shape_transform(None, drawing=shape_a, target_shape=shape_b, mode="Distort", t=1.0, anchor="origin")
        self.assertEqual(out_shape, expected)

    def test_shape_transform_distort2_fallbacks(self):
        shape_a = "m 0 0 l 100 0 l 100 100 l 0 100"
        shape_c = "m 0 0 l 100 50 l 0 100"

        # Si no hay mid_shape, opera como Distort directo
        res = shape_transform(None, drawing=shape_a, mid_shape="", target_shape=shape_c, mode="Distort2", t=0.5, anchor="origin")
        expected = shape_transform(None, drawing=shape_a, target_shape=shape_c, mode="Distort", t=0.5, anchor="origin")
        self.assertEqual(res, expected)

    def test_shape_transform_distort2_polyline_step(self):
        shape_a = "m 0 0 l 100 0 l 100 100 l 0 100"
        shape_b = "m 0 0 l 100 0 l 50 100"
        shape_c = "m 0 0 l 100 50 l 0 100"

        res_poly = shape_transform(None, drawing=shape_a, mid_shape=shape_b, target_shape=shape_c, mode="Distort2", t=0.3, step_px=5.0, anchor="origin")
        self.assertTrue(isinstance(res_poly, str) and res_poly.startswith("m "))
        self.assertIn("l ", res_poly)


class TestConcentricBordersAndClip(unittest.TestCase):
    """Pruebas de generacion de bordes concentricos y gradientes de corte."""

    def test_concentric_borders_generation(self):
        shape = "m 0 0 l 100 0 l 100 100 l 0 100"
        ctx = {"start_time": 0, "end_time": 1000, "b_i": 2}
        res = shape_concentric_borders_node(ctx, shape=shape, loop_count=3, separation=4.0)
        self.assertIsNotNone(res)
        self.assertEqual(ctx.get("b_i"), 2)
        self.assertEqual(ctx.get("b_n"), 3)
        self.assertEqual(ctx.get("ring_i"), 2)
        self.assertEqual(ctx.get("ring_n"), 3)
        self.assertNotIn("j_max", ctx)


class TestShapeFilter(unittest.TestCase):
    """Pruebas unitarias completas para el nodo Shape Filter en sus 3 modos (Vértices, Grupo, Ruido)."""

    def test_shape_filter_vertices_math_and_t(self):
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        # Con t = 1.0, x -> x + 10, y -> y + 20
        res_t1 = shape_filter(None, drawing=sq, mode="Vértices", expr_x="x + 10", expr_y="y + 20", t=1.0)
        self.assertTrue(res_t1.startswith("m 10 20"))
        self.assertIn("l 110 20", res_t1)
        self.assertIn("l 110 120", res_t1)
        self.assertIn("l 10 120", res_t1)

        # Con t = 0.0, debe mantenerse idéntico a la forma base
        res_t0 = shape_filter(None, drawing=sq, mode="Vértices", expr_x="x + 50", expr_y="y + 50", t=0.0)
        self.assertTrue(res_t0.startswith("m 0 0"))
        self.assertIn("l 100 0", res_t0)
        self.assertIn("l 100 100", res_t0)
        self.assertIn("l 0 100", res_t0)

        # Con t = 0.5, interpolación al 50%
        res_t05 = shape_filter(None, drawing=sq, mode="Vértices", expr_x="x + 20", expr_y="y + 40", t=0.5)
        self.assertTrue(res_t05.startswith("m 10 20"))
        self.assertIn("l 110 20", res_t05)

    def test_shape_filter_vertices_env_vars(self):
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        # Usar mx, cy, sin
        res = shape_filter(None, drawing=sq, mode="Vértices", expr_x="x + 10 * sin(mx * pi)", expr_y="y + cy", t=1.0)
        self.assertTrue(res.startswith("m "))
        tokens = res.split()
        self.assertEqual(len(tokens), 12)

    def test_shape_filter_vertices_subdivs(self):
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        # Subdividir antes de filtrar con onda
        res = shape_filter(None, drawing=sq, mode="Vértices", expr_x="x + 5 * sin(mx * 2 * pi)", subdivs=20.0)
        tokens = res.split()
        self.assertGreater(len(tokens), 12)

    def test_shape_filter_group_rotation_and_offset(self):
        # Forma con 3 subcontornos
        multi = "m 0 0 l 10 0 l 10 10 l 0 10 m 20 0 l 30 0 l 30 10 l 20 10 m 40 0 l 50 0 l 50 10 l 40 10"
        res = shape_filter(None, drawing=multi, mode="Grupo", rot_step=45.0, offset_x=15.0, t=1.0, anchor="center")
        self.assertEqual(res.count("m "), 3)
        self.assertTrue(res.startswith("m "))

        # Modulación con t = 0.0 (las piezas no rotan ni se desplazan adicionalmente)
        res_t0 = shape_filter(None, drawing=multi, mode="Grupo", rot_step=90.0, offset_x=50.0, t=0.0, anchor="center")
        self.assertEqual(res_t0.count("m "), 3)

    def test_shape_filter_noise_deterministic(self):
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        # Misma semilla debe dar idéntico resultado
        res1 = shape_filter(None, drawing=sq, mode="Ruido", radius_x=10.0, radius_y=10.0, subdivs=0, seed=1234)
        res2 = shape_filter(None, drawing=sq, mode="Ruido", radius_x=10.0, radius_y=10.0, subdivs=0, seed=1234)
        self.assertEqual(res1, res2)

        # Semilla distinta debe dar resultado diferente
        res3 = shape_filter(None, drawing=sq, mode="Ruido", radius_x=10.0, radius_y=10.0, subdivs=0, seed=9999)
        self.assertNotEqual(res1, res3)

    def test_shape_filter_node_engine_dispatch(self):
        node_def = {
            "id": 1,
            "type": "Shape/Shape Filter",
            "properties": {
                "shape": "m 0 0 l 50 0 l 50 50 l 0 50",
                "mode": "Vértices",
                "expr_x": "x + 5",
                "expr_y": "y + 10",
                "t": "1.0",
                "subdivs": "0"
            }
        }
        engine = GraphEngine({"nodes": [node_def], "links": []})
        res = engine.evaluate_data_node(1, context={})
        self.assertTrue(isinstance(res, str))
        self.assertTrue(res.startswith("m 5 10"))

    def test_shape_multi_all_modes_direct(self):
        from nodes.shape_nodes import shape_multi

        # 1. Cuadros Concéntricos (multi1)
        res1 = shape_multi(None, mode="Cuadros Concéntricos", size=100.0, px="4", t=1.0)
        self.assertTrue(isinstance(res1, str))
        self.assertTrue(res1.startswith("m "))
        # Con patrón de huecos
        res1_pat = shape_multi(None, mode="Cuadros Concéntricos", size=100.0, px="8, {2}, 4, {3}", t=1.0)
        self.assertTrue(res1_pat.startswith("m "))

        # 2. Franjas Diagonales (multi2)
        res2 = shape_multi(None, mode="Franjas Diagonales", width=70.0, height=50.0, px="6", t=1.0)
        self.assertTrue(isinstance(res2, str))
        self.assertTrue(res2.startswith("m "))

        # 3. Anillos Concéntricos (multi3)
        res3 = shape_multi(None, drawing="m 0 0 l 100 0 l 100 100 l 0 100", mode="Anillos Concéntricos", size=100.0, bord="4", t=1.0)
        self.assertTrue(isinstance(res3, str))
        self.assertTrue(res3.startswith("m "))

        # 4. Mosaico Poligonal (multi4)
        res4 = shape_multi(None, mode="Mosaico Poligonal", size=64.0, sides=6, rings=1, n_layers=5, t=1.0)
        self.assertTrue(isinstance(res4, str))
        self.assertTrue(res4.startswith("m "))

        res4_rings = shape_multi(None, mode="Mosaico Poligonal", size=64.0, sides=6, rings=3, n_layers=3, separation=4.0, t=1.0)
        self.assertTrue(isinstance(res4_rings, str))
        self.assertTrue(res4_rings.startswith("m "))

        # 5. Mosaico Multi-Forma (multi5)
        res5 = shape_multi(None, drawing="m 0 0 l 10 0 l 10 10 l 0 10", mode="Mosaico Multi-Forma", width=60.0, height=50.0, dx=2.0, dy=2.0)
        self.assertTrue(isinstance(res5, str))
        self.assertTrue(res5.startswith("m "))

        # 6. Borde Segmentado (multi6)
        res6 = shape_multi(None, mode="Borde Segmentado", width=104.0, height=104.0, bord=4.0, space=2.0, length=20.0, t=1.0)
        self.assertTrue(isinstance(res6, str))
        self.assertTrue(res6.startswith("m "))

        res6_custom = shape_multi(None, drawing="Estrella", mode="Borde Segmentado", width=120.0, height=100.0, bord=10.0, space=4.0, length=15.0, t=1.0)
        self.assertTrue(isinstance(res6_custom, str))
        self.assertTrue(res6_custom.startswith("m "))

        # 7. Roseta Radial (multi7)
        res7_pie = shape_multi(None, mode="Roseta Radial", parts=12, r_out=50.0, r_in=0.0, t=1.0)
        self.assertTrue(isinstance(res7_pie, str))
        self.assertTrue(res7_pie.startswith("m "))
        self.assertIn("b ", res7_pie) # Debe contener curvas Bézier suaves

        res7_ring = shape_multi(None, mode="Roseta Radial", parts=12, r_out=50.0, r_in=20.0, t=1.0)
        self.assertTrue(isinstance(res7_ring, str))
        self.assertTrue(res7_ring.startswith("m "))

        # 8. Túnel / Cascada (multi8)
        res8 = shape_multi(None, drawing="m 0 0 l 100 0 l 100 100 l 0 100", mode="Túnel / Cascada", size1=100.0, size2=10.0, loop=5, t=1.0)
        self.assertTrue(isinstance(res8, str))
        self.assertTrue(res8.startswith("m "))

    def test_shape_multi_factor_t_progress(self):
        from nodes.shape_nodes import shape_multi

        # Roseta Radial con t=0.5 debe generar menos rebanadas que con t=1.0
        r_half = shape_multi(None, mode="Roseta Radial", parts=12, r_out=50.0, r_in=0.0, t=0.5)
        r_full = shape_multi(None, mode="Roseta Radial", parts=12, r_out=50.0, r_in=0.0, t=1.0)
        self.assertLess(len(r_half), len(r_full))

        # Borde Segmentado con t=0.25 vs t=1.0
        b_quarter = shape_multi(None, mode="Borde Segmentado", width=104.0, height=104.0, bord=4.0, length=20.0, t=0.25)
        b_full = shape_multi(None, mode="Borde Segmentado", width=104.0, height=104.0, bord=4.0, length=20.0, t=1.0)
        self.assertLess(len(b_quarter), len(b_full))

        # Túnel con t=0.5 vs t=1.0
        t_half = shape_multi(None, mode="Túnel / Cascada", size1=100.0, size2=10.0, loop=8, t=0.5)
        t_full = shape_multi(None, mode="Túnel / Cascada", size1=100.0, size2=10.0, loop=8, t=1.0)
        self.assertLess(len(t_half), len(t_full))

    def test_shape_multi_separation_and_overlap(self):
        from nodes.shape_nodes import shape_multi

        # Roseta Radial: con separación > 0 los vértices radiales se desplazan hacia afuera
        res_sep0 = shape_multi(None, mode="Roseta Radial", parts=4, r_out=50.0, r_in=0.0, separation=0.0, t=1.0)
        res_sep10 = shape_multi(None, mode="Roseta Radial", parts=4, r_out=50.0, r_in=0.0, separation=10.0, t=1.0)
        res_sep_neg = shape_multi(None, mode="Roseta Radial", parts=4, r_out=50.0, r_in=0.0, separation=-5.0, t=1.0)

        self.assertNotEqual(res_sep0, res_sep10)
        self.assertNotEqual(res_sep0, res_sep_neg)
        self.assertTrue(res_sep10.startswith("m "))
        self.assertTrue(res_sep_neg.startswith("m "))

        # Mosaico Poligonal con separación
        res_poly0 = shape_multi(None, mode="Mosaico Poligonal", size=64.0, sides=6, rings=1, n_layers=5, separation=0.0, t=1.0)
        res_poly5 = shape_multi(None, mode="Mosaico Poligonal", size=64.0, sides=6, rings=1, n_layers=5, separation=5.0, t=1.0)
        self.assertNotEqual(res_poly0, res_poly5)

        # Cuadros Concéntricos con separación
        res_sq0 = shape_multi(None, mode="Cuadros Concéntricos", size=100.0, px="4", separation=0.0, t=1.0)
        res_sq5 = shape_multi(None, mode="Cuadros Concéntricos", size=100.0, px="4", separation=5.0, t=1.0)
        self.assertNotEqual(res_sq0, res_sq5)

        # Túnel / Cascada con separación
        res_tun0 = shape_multi(None, drawing="m 0 0 l 100 0 l 100 100 l 0 100", mode="Túnel / Cascada", size1=100.0, size2=10.0, loop=5, separation=0.0, t=1.0)
        res_tun10 = shape_multi(None, drawing="m 0 0 l 100 0 l 100 100 l 0 100", mode="Túnel / Cascada", size1=100.0, size2=10.0, loop=5, separation=10.0, t=1.0)
        self.assertNotEqual(res_tun0, res_tun10)

    def test_shape_multi_diagonal_stripes_corner_coverage(self):
        from nodes.shape_nodes import shape_multi, _get_drawing_bbox

        # Franjas Diagonales con dimensiones no cuadradas (100x200) sin separación: caja exacta
        res_diag0 = shape_multi(None, mode="Franjas Diagonales", width=100.0, height=200.0, px="10", separation=0.0, t=1.0, anchor="origin")
        bbox0 = _get_drawing_bbox(res_diag0)
        self.assertEqual(bbox0, (0.0, 100.0, 0.0, 200.0))

        # Franjas Diagonales con separación (2.0): mantiene la caja exacta pero con huecos internos entre franjas
        res_diag2 = shape_multi(None, mode="Franjas Diagonales", width=100.0, height=200.0, px="10", separation=2.0, t=1.0, anchor="origin")
        bbox2 = _get_drawing_bbox(res_diag2)
        self.assertEqual(bbox2, (0.0, 100.0, 0.0, 200.0))

        # Franjas Diagonales horizontales (200x100)
        res_diag_h = shape_multi(None, mode="Franjas Diagonales", width=200.0, height=100.0, px="10", separation=2.0, t=1.0, anchor="origin")
        bbox_h = _get_drawing_bbox(res_diag_h)
        self.assertEqual(bbox_h, (0.0, 200.0, 0.0, 100.0))

        # Franjas Diagonales cuadradas (100x100)
        res_diag_sq = shape_multi(None, mode="Franjas Diagonales", width=100.0, height=100.0, px="10", separation=0.0, t=1.0, anchor="origin")
        bbox_sq = _get_drawing_bbox(res_diag_sq)
        self.assertEqual(bbox_sq, (0.0, 100.0, 0.0, 100.0))

    def test_shape_multi_node_engine_separation_inputs(self):
        # Roseta Radial con slot de separación conectado / propiedad
        node_def = {
            "id": 1,
            "type": "Shape/Shape Multi",
            "properties": {
                "mode": "Roseta Radial",
                "parts": "8",
                "r_out": "60.0",
                "r_in": "10.0",
                "separation": "15.0",
                "t": "1.0"
            }
        }
        engine = GraphEngine({"nodes": [node_def], "links": []})
        res = engine.evaluate_data_node(1, context={})
        self.assertTrue(isinstance(res, str) and res.startswith("m "))

        # Probar con link en input slot 3 (Separación)
        sep_node = {
            "id": 2,
            "type": "Functions/Number",
            "properties": {"value": "20.0"}
        }
        node_def_linked = {
            "id": 3,
            "type": "Shape/Shape Multi",
            "properties": {
                "mode": "Roseta Radial",
                "parts": "8",
                "r_out": "60.0",
                "r_in": "10.0",
                "t": "1.0"
            },
            "inputs": [{"name": "Separación", "link": 10}]
        }
        link = [10, 2, 0, 3, 3, "number"]
        engine2 = GraphEngine({"nodes": [sep_node, node_def_linked], "links": [link]})
        res2 = engine2.evaluate_data_node(3, context={})
        self.assertTrue(isinstance(res2, str) and res2.startswith("m "))

    def test_shape_multi_anchor_modes(self):
        from nodes.shape_nodes import shape_multi

        # 1. Cuadros Concéntricos: center vs origin vs zero con posición
        res_center = shape_multi(None, mode="Cuadros Concéntricos", size=100.0, px="4", separation=0.0, t=1.0, anchor="center")
        res_origin = shape_multi(None, mode="Cuadros Concéntricos", size=100.0, px="4", separation=0.0, t=1.0, anchor="origin")
        ctx = {"fx_pos_x": 200.0, "fx_pos_y": 150.0}
        res_zero = shape_multi(ctx, mode="Cuadros Concéntricos", size=100.0, px="4", separation=0.0, t=1.0, anchor="zero")

        self.assertTrue(res_center.startswith("m "))
        self.assertTrue(res_origin.startswith("m "))
        self.assertTrue(res_zero.startswith("m "))
        self.assertNotEqual(res_center, res_origin)
        self.assertNotEqual(res_center, res_zero)

        # 2. Túnel / Cascada: center vs origin
        res_tun_center = shape_multi(None, drawing="m 0 0 l 100 0 l 100 100 l 0 100", mode="Túnel / Cascada", size1=100.0, size2=10.0, loop=5, anchor="center")
        res_tun_origin = shape_multi(None, drawing="m 0 0 l 100 0 l 100 100 l 0 100", mode="Túnel / Cascada", size1=100.0, size2=10.0, loop=5, anchor="origin")
        self.assertTrue(res_tun_center.startswith("m "))
        self.assertTrue(res_tun_origin.startswith("m "))
        self.assertNotEqual(res_tun_center, res_tun_origin)

        # 3. Mosaico Multi-Forma con anchor
        res_multi_center = shape_multi(None, drawing="m 0 0 l 20 0 l 20 20 l 0 20", mode="Mosaico Multi-Forma", width=60.0, height=60.0, anchor="center")
        res_multi_origin = shape_multi(None, drawing="m 0 0 l 20 0 l 20 20 l 0 20", mode="Mosaico Multi-Forma", width=60.0, height=60.0, anchor="origin")
        self.assertTrue(res_multi_center.startswith("m "))
        self.assertTrue(res_multi_origin.startswith("m "))
        self.assertNotEqual(res_multi_center, res_multi_origin)

    def test_shape_multi_node_engine_anchor(self):
        # Evaluar Shape Multi con propiedad anchor="origin" vs "center"
        node_def_origin = {
            "id": 1,
            "type": "Shape/Shape Multi",
            "properties": {
                "mode": "Cuadros Concéntricos",
                "size": "100.0",
                "px": "4",
                "separation": "0.0",
                "t": "1.0",
                "anchor": "origin"
            }
        }
        engine_origin = GraphEngine({"nodes": [node_def_origin], "links": []})
        res_origin = engine_origin.evaluate_data_node(1, context={})

        node_def_center = {
            "id": 2,
            "type": "Shape/Shape Multi",
            "properties": {
                "mode": "Cuadros Concéntricos",
                "size": "100.0",
                "px": "4",
                "separation": "0.0",
                "t": "1.0",
                "anchor": "center"
            }
        }
        engine_center = GraphEngine({"nodes": [node_def_center], "links": []})
        res_center = engine_center.evaluate_data_node(2, context={})

        self.assertTrue(res_origin.startswith("m "))
        self.assertTrue(res_center.startswith("m "))
        self.assertNotEqual(res_origin, res_center)

    def test_shape_multi_node_engine_dispatch(self):
        # Probar evaluación por NodeEngine para cada uno de los 8 modos
        modes = [
            ("Cuadros Concéntricos", {"size": "100.0", "px": "4", "separation": "2.0", "t": "1.0", "anchor": "center"}),
            ("Franjas Diagonales", {"width": "70.0", "height": "50.0", "px": "6", "separation": "1.0", "t": "1.0", "anchor": "center"}),
            ("Anillos Concéntricos", {"shape": "circle", "size": "100.0", "bord": "4", "separation": "2.0", "t": "1.0", "anchor": "center"}),
            ("Mosaico Poligonal", {"size": "64.0", "sides": "6", "rings": "1", "n_layers": "5", "separation": "3.0", "t": "1.0", "anchor": "center"}),
            ("Mosaico Multi-Forma", {"shape": "rectangle", "width": "60.0", "height": "50.0", "dx": "0", "dy": "0", "anchor": "center"}),
            ("Borde Segmentado", {"width": "104.0", "height": "104.0", "bord": "4.0", "space": "0", "separation": "2.0", "length": "20.0", "t": "1.0", "anchor": "center"}),
            ("Roseta Radial", {"parts": "12", "r_out": "50.0", "r_in": "0.0", "separation": "4.0", "t": "1.0", "anchor": "center"}),
            ("Túnel / Cascada", {"shape": "rectangle", "size1": "100.0", "size2": "10.0", "loop": "6", "separation": "2.0", "t": "1.0", "anchor": "center"}),
        ]

        for idx, (m_name, props_dict) in enumerate(modes, start=1):
            props_all = {"mode": m_name}
            props_all.update(props_dict)
            node_def = {
                "id": idx,
                "type": "Shape/Shape Multi",
                "properties": props_all
            }
            engine = GraphEngine({"nodes": [node_def], "links": []})
            res = engine.evaluate_data_node(idx, context={})
            self.assertTrue(isinstance(res, str), f"Fallo en modo {m_name}")
    def test_shape_multi_concentric_rings_hollow(self):
        from nodes.shape_nodes import shape_multi, parse_assdraw_segments

        # Anillos concéntricos con círculos: verificar que los subcaminos interiores estén invertidos
        res = shape_multi(None, mode="Anillos Concéntricos", size=60.0, bord="3, 7", separation=0.0, t=1.0)
        self.assertTrue(isinstance(res, str))
        self.assertTrue(res.startswith("m "))
        # No debe haber comandos l que conecten entre sí los contornos circulares
        # Todos los subcaminos de círculos concéntricos deben iniciar con 'm'
        contours = parse_assdraw_segments(res)
        self.assertGreater(len(contours), 1)
        for c in contours:
            # Cada contorno de círculo debe estar cerrado y compuesto por curvas Bézier
            for s in c["segments"]:
                self.assertEqual(s["type"], "b")

    def test_shape_multi_concentric_rings_gap(self):
        from nodes.shape_nodes import shape_multi, parse_assdraw_segments

        # Anillos con centro vacío (gap inicial)
        res_gap = shape_multi(None, mode="Anillos Concéntricos", size=60.0, bord="{-4}, 4", separation=0.0, t=1.0)
        self.assertTrue(isinstance(res_gap, str))
        self.assertTrue(res_gap.startswith("m "))
    def test_shape_multi_segmented_border_custom_shape(self):
        from nodes.shape_nodes import shape_multi, parse_assdraw_segments

        # 1. Borde segmentado por defecto (rectángulo)
        res_rect = shape_multi(None, mode="Borde Segmentado", width=100.0, height=100.0, bord=4.0, space=5.0, length=20.0, t=1.0)
        self.assertTrue(isinstance(res_rect, str))
        self.assertTrue(res_rect.startswith("m "))

        # 2. Borde segmentado con forma personalizada (estrella / corazón / círculo)
        heart_shape = "m 50 20 b 50 10 35 0 20 0 b 0 0 0 30 0 30 b 0 60 50 90 50 90 b 50 90 100 60 100 30 b 100 30 100 0 80 0 b 65 0 50 10 50 20"
        res_heart = shape_multi(None, drawing=heart_shape, mode="Borde Segmentado", bord=4.0, space=5.0, length=15.0, t=1.0)
        self.assertTrue(isinstance(res_heart, str))
        self.assertTrue(res_heart.startswith("m "))
        contours = parse_assdraw_segments(res_heart)
        self.assertGreater(len(contours), 1, "Debe generar múltiples trazos/segmentos a lo largo del contorno")

        # 3. Factor t progresivo
        res_heart_half = shape_multi(None, drawing=heart_shape, mode="Borde Segmentado", bord=4.0, space=5.0, length=15.0, t=0.5)
        contours_half = parse_assdraw_segments(res_heart_half)
        self.assertLess(len(contours_half), len(contours), "t=0.5 debe generar menos segmentos que t=1.0")

    def test_shape_multi_tunnel_cascade_directions(self):
        from nodes.shape_nodes import shape_multi

        # 1. Dirección numérica (0° = arriba vs 90° = derecha vs 180° = abajo vs 270° = izquierda)
        res_up = shape_multi(None, drawing="m 0 0 l 20 0 l 20 20 l 0 20", mode="Túnel / Cascada", size1=50.0, size2=10.0, loop=4, separation=10.0, angle=0.0)
        res_right = shape_multi(None, drawing="m 0 0 l 20 0 l 20 20 l 0 20", mode="Túnel / Cascada", size1=50.0, size2=10.0, loop=4, separation=10.0, angle=90.0)
        res_down = shape_multi(None, drawing="m 0 0 l 20 0 l 20 20 l 0 20", mode="Túnel / Cascada", size1=50.0, size2=10.0, loop=4, separation=10.0, angle=180.0)
        res_left = shape_multi(None, drawing="m 0 0 l 20 0 l 20 20 l 0 20", mode="Túnel / Cascada", size1=50.0, size2=10.0, loop=4, separation=10.0, angle=270.0)

        self.assertTrue(res_up.startswith("m "))
        self.assertTrue(res_right.startswith("m "))
        self.assertTrue(res_down.startswith("m "))
        self.assertTrue(res_left.startswith("m "))
        self.assertNotEqual(res_up, res_right)
        self.assertNotEqual(res_up, res_down)
        self.assertNotEqual(res_right, res_left)

        # 2. Dirección textual por nombre ("arriba", "arriba-derecha", etc.)
        res_up_name = shape_multi(None, drawing="m 0 0 l 20 0 l 20 20 l 0 20", mode="Túnel / Cascada", size1=50.0, size2=10.0, loop=4, separation=10.0, angle="arriba")
        res_up_num = shape_multi(None, drawing="m 0 0 l 20 0 l 20 20 l 0 20", mode="Túnel / Cascada", size1=50.0, size2=10.0, loop=4, separation=10.0, angle=0.0)
        self.assertEqual(res_up_name, res_up_num)

        res_right_name = shape_multi(None, drawing="m 0 0 l 20 0 l 20 20 l 0 20", mode="Túnel / Cascada", size1=50.0, size2=10.0, loop=4, separation=10.0, angle="derecha")
        res_right_num = shape_multi(None, drawing="m 0 0 l 20 0 l 20 20 l 0 20", mode="Túnel / Cascada", size1=50.0, size2=10.0, loop=4, separation=10.0, angle=90.0)
        self.assertEqual(res_right_name, res_right_num)

    def test_shape_array_node_progress_t(self):
        from nodes.shape_nodes import shape_array_node, parse_assdraw_segments

        # 1. Grid en modo Shape (Monolítico) 5x3 = 15 partículas con t=1.0
        res_full, pos, px, py, ang, ai, total, col, row = shape_array_node(
            context={},
            mode="Grid",
            out_mode="Shape",
            cols=5,
            rows=3,
            t=1.0,
            order="79"
        )
        self.assertEqual(total, 15)
        segments_full = parse_assdraw_segments(res_full)
        self.assertEqual(len(segments_full), 15)

        # 2. t = 0.5 -> 50% de las 15 partículas = round(7.5) = 8 partículas
        res_half, _, _, _, _, _, _, _, _ = shape_array_node(
            context={},
            mode="Grid",
            out_mode="Shape",
            cols=5,
            rows=3,
            t=0.5,
            order="79"
        )
        segments_half = parse_assdraw_segments(res_half)
        self.assertEqual(len(segments_half), 8)

        # 3. t = 0.0 -> 0 partículas
        res_zero, _, _, _, _, _, _, _, _ = shape_array_node(
            context={},
            mode="Grid",
            out_mode="Shape",
            cols=5,
            rows=3,
            t=0.0,
            order="79"
        )
        self.assertEqual(res_zero, "")

        # 4. Modo Loops: las partículas con a_i <= visible_count tienen dibujo, y las que superan a_i > visible_count retornan ""
        # Con t=0.5 (8 visibles de 15)
        res_loop_5, _, _, _, _, ai5, tot5, _, _ = shape_array_node(
            context={"a_i": 5},
            mode="Grid",
            out_mode="Loops",
            cols=5,
            rows=3,
            t=0.5
        )
        self.assertTrue(res_loop_5.startswith("m "))

        res_loop_12, _, _, _, _, ai12, tot12, _, _ = shape_array_node(
            context={"a_i": 12},
            mode="Grid",
            out_mode="Loops",
            cols=5,
            rows=3,
            t=0.5
        )
        self.assertEqual(res_loop_12, "", "Partículas más allá del umbral t deben retornar dibujo vacío")

        # 5. Spiral en modo Shape con t=0.4 (de 20 partículas = 8 visibles)
        res_spiral_t, _, _, _, _, _, tot_sp, _, _ = shape_array_node(
            context={},
            mode="Spiral",
            out_mode="Shape",
            count=20,
            t=0.4
        )
        segments_spiral = parse_assdraw_segments(res_spiral_t)
        self.assertEqual(len(segments_spiral), 8)


if __name__ == "__main__":
    unittest.main()





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
    shape_manipulator,
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

    def test_shape_transform_inflate(self):
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        res_t0 = shape_transform(None, drawing=sq, mode="Inflate", t=0.0, anchor="origin")
        self.assertIn("m 0 0", res_t0)
        res_t05 = shape_transform(None, drawing=sq, mode="Inflate", t=0.5, anchor="center")
        self.assertTrue(res_t05.startswith("m "))


class TestConcentricBordersAndClip(unittest.TestCase):
    """Pruebas de generacion de bordes concentricos y gradientes de corte."""

    def test_concentric_borders_generation(self):
        shape = "m 0 0 l 100 0 l 100 100 l 0 100"
        ctx = {"start_time": 0, "end_time": 1000}
        res = shape_concentric_borders_node(ctx, shape=shape, loop_count=3, separation=4.0)
        self.assertIsNotNone(res)

    def test_clip_gradient_basic(self):
        ctx = {"start_time": 0, "end_time": 1000}
        res = clip_gradient_node(ctx, num_clips="4", angle="0")
        self.assertIsNotNone(res)


if __name__ == "__main__":
    unittest.main()

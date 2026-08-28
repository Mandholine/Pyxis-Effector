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

import os
import sys

_pyxis_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _pyxis_dir not in sys.path:
    sys.path.insert(0, _pyxis_dir)

import unittest
from nodes.tag_nodes import node_gradiente_color
from nodes.math_nodes import math_polar
from nodes.shape_nodes import shape_transform
from node_engine import GraphEngine

class AdvancedNodesTests(unittest.TestCase):
    def test_gradiente_color(self):
        ctx = {}
        # Test 2-stop gradient Red (#FF0000) to Blue (#0000FF)
        c_start = node_gradiente_color(ctx, prog=0.0, colors_str="#FF0000,#00FF00,#0000FF")
        c_mid = node_gradiente_color(ctx, prog=0.5, colors_str="#FF0000,#00FF00,#0000FF")
        c_end = node_gradiente_color(ctx, prog=1.0, colors_str="#FF0000,#00FF00,#0000FF")

        self.assertEqual(c_start, "&H0000FF&") # Red in ASS (&H0000FF&)
        self.assertEqual(c_mid, "&H00FF00&")   # Green in ASS (&H00FF00&)
        self.assertEqual(c_end, "&HFF0000&")   # Blue in ASS (&HFF0000&)

    def test_gradiente_color_expression(self):
        class DummyChar:
            i = 2
            n = 4
        ctx = {"char": DummyChar()}
        c_res = node_gradiente_color(ctx, prog="char.i / char.n", colors_str="#FF0000,#00FF00,#0000FF")
        self.assertEqual(c_res, "&H00FF00&")

    def test_math_polar(self):
        ctx = {}
        # Test 0 degrees (pointing right: dx=100, dy=0)
        pos_0 = math_polar(ctx, x=100, y=200, angle=0, radius=100)
        self.assertEqual(pos_0, "\\pos(200,200)")

        # Test 90 degrees (pointing down: dx=0, dy=100)
        pos_90 = math_polar(ctx, x=100, y=200, angle=90, radius=100)
        self.assertEqual(pos_90, "\\pos(100,300)")

    def test_polar_engine_slots(self):
        graph = {
            "last_node_id": 2,
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Polar to Cartesian",
                    "properties": {"x": "100", "y": "200", "angle": "0", "radius": "50"}
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        pos_tag = engine.evaluate_data_node(1, {}, output_slot_index=0)
        val_x = engine.evaluate_data_node(1, {}, output_slot_index=1)
        val_y = engine.evaluate_data_node(1, {}, output_slot_index=2)
        val_dx = engine.evaluate_data_node(1, {}, output_slot_index=3)

        self.assertEqual(pos_tag, "\\pos(150,200)")
        self.assertEqual(val_x, "150")
        self.assertEqual(val_y, "200")
        self.assertEqual(val_dx, "50")

    def test_polar_engine_expressions(self):
        class DummySyl:
            center = 500
            middle = 300
        graph = {
            "last_node_id": 1,
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Polar to Cartesian",
                    "properties": {"x": "syl.center", "y": "syl.middle", "angle": "j * 45", "radius": "45"}
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        ctx = {"syl": DummySyl(), "j": 2}
        pos_tag = engine.evaluate_data_node(1, ctx, output_slot_index=0)
        self.assertEqual(pos_tag, "\\pos(500,345)")

    def test_shape_transform(self):
        ctx = {"fx_pos_x": 500, "fx_pos_y": 300}
        square = "m 0 0 l 100 0 l 100 100 l 0 100 "

        # 1. Mode 'topleft': Scale 2x, offset +10, +10 -> top-left at (10, 10), corner at (210, 210)
        t_topleft = shape_transform(ctx, drawing=square, scale_x=2.0, scale_y=2.0, rot=0, offset_x=10, offset_y=10, mode="topleft")
        self.assertIn("m 10 10", t_topleft)
        self.assertIn("l 210 210", t_topleft)

        # 2. Mode 'center': Center at (0,0), scale 2x (box [-100..100, -100..100]) + offset (10, 10) -> [-90..110, -90..110]
        t_center = shape_transform(ctx, drawing=square, scale_x=2.0, scale_y=2.0, rot=0, offset_x=10, offset_y=10, mode="center")
        self.assertIn("m -90 -90", t_center)
        self.assertIn("l 110 110", t_center)

        # 3. Mode 'absolute': Bounding box centered and placed at (500+10, 300+10) = (510, 310) -> [-100+510 .. 100+510] = [410..610]
        t_abs = shape_transform(ctx, drawing=square, scale_x=2.0, scale_y=2.0, rot=0, offset_x=10, offset_y=10, mode="absolute")
        self.assertIn("m 410 210", t_abs)
        self.assertIn("l 610 410", t_abs)

    def test_trans_shape_engine(self):
        graph = {
            "last_node_id": 1,
            "nodes": [
                {
                    "id": 1,
                    "type": "Shape Transform",
                    "properties": {
                        "shape": "m 0 0 l 100 0 l 100 100 l 0 100",
                        "scale_x": "200",
                        "scale_y": "200",
                        "offset_x": "10",
                        "offset_y": "10",
                        "anchor": "topleft",
                        "mode": "Escalar"
                    }
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        res = engine.evaluate_data_node(1, {}, output_slot_index=0)
        self.assertIn("m 10 10", res)
        self.assertIn("l 210 210", res)

if __name__ == "__main__":
    unittest.main()

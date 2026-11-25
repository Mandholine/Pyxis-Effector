"""Unit tests for Functions/Move Tag shadtrick mode and simplified comma-list points."""

import sys
import os
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from nodes.tag_nodes import move_tag_node, _parse_points_input
from node_engine import GraphEngine


class TestMoveTagShadtrick(unittest.TestCase):
    """Test suite for Move Tag shadtrick mode and comma-separated coordinate parsing."""

    def test_parse_points_flat_comma_and_variables(self):
        """Parses flat comma-separated coordinates and evaluates context variables."""
        ctx = {
            "Origenx": 120.0,
            "Origeny": -40.0,
            "MidX": 50.0,
            "bu_i": 0,
        }
        pts = _parse_points_input("Origenx, Origeny, MidX, 10, 0.001, 0.001", step_px=500.0, context=ctx)
        self.assertEqual(len(pts), 3)
        self.assertAlmostEqual(pts[0][0], 120.0)
        self.assertAlmostEqual(pts[0][1], -40.0)
        self.assertAlmostEqual(pts[1][0], 50.0)
        self.assertAlmostEqual(pts[1][1], 10.0)
        self.assertAlmostEqual(pts[2][0], 0.001)
        self.assertAlmostEqual(pts[2][1], 0.001)

    def test_shadtrick_preserves_min_precision_and_avoids_shad_reset(self):
        """Emits \\1a&HFF&\\3a&HFF&\\ko0\\xshad...\\yshad... without \\shad, \\pos, \\fscx, or \\p1...\\p0."""
        res = move_tag_node(
            context={"Origenx": 80, "Origeny": -20},
            mode="shadtrick",
            points="Origenx, Origeny, 0.001, 0.001",
            step_px=500.0,
            t1=100,
            t2=1100,
            accel=1.0,
        )
        self.assertTrue(res.startswith("\\1a&HFF&\\3a&HFF&\\ko0\\xshad80\\yshad-20"))
        self.assertIn("\\t(100,1100,\\xshad0.001\\yshad0.001)", res)
        self.assertNotIn("\\shad0", res)
        self.assertNotIn("\\pos(", res)
        self.assertNotIn("\\fscx", res)
        self.assertNotIn("\\p1", res)
        self.assertNotIn("\\p0", res)

    def test_shadtrick_fallback_uses_min_shadow_when_points_empty(self):
        """Uses 0.001, 0.001 as static base shadow offset when points is omitted."""
        res = move_tag_node(
            context={},
            mode="shadtrick",
        )
        self.assertEqual(res, "\\1a&HFF&\\3a&HFF&\\ko0\\xshad0.001\\yshad0.001")

    def test_shadtrick_four_points_emits_three_direct_transforms(self):
        """4 waypoints (A, B, C, D) emit strictly 3 \\t(...) transforms without step_px subdivision."""
        res = move_tag_node(
            context={},
            mode="shadtrick",
            points="0, 0, 100, 0, 100, 100, 0.001, 100",
            step_px=1.0,
            t1=0,
            t2=900,
        )
        self.assertEqual(res.count("\\t("), 3)
        self.assertIn("\\xshad0\\yshad0", res)
        self.assertIn("\\xshad100\\yshad0)", res)
        self.assertIn("\\xshad100\\yshad100)", res)
        self.assertIn("\\xshad0.001\\yshad100)", res)

    def test_shadtrick_assdraw_with_tags_strips_tags_and_resamples(self):
        """ASSDraw paths with prepended {...} tags isolate geometry and resample by step_px."""
        res = move_tag_node(
            context={},
            mode="shadtrick",
            points="{\\1c&HFFFFFF&\\bord2}m 0 0 l 100 0",
            step_px=25.0,
            t1=0,
            t2=1000,
        )
        self.assertNotIn("\\1c", res)
        self.assertNotIn("\\bord2", res)
        self.assertEqual(res.count("\\t("), 4)
        self.assertIn("\\xshad25\\yshad0)", res)
        self.assertIn("\\xshad100\\yshad0)", res)

    def test_waypoints_accepts_flat_comma_list_and_variables(self):
        """Waypoints mode parses flat comma-separated coordinates and arithmetic expressions with variables."""
        res = move_tag_node(
            context={"Ox": 10, "Oy": 40},
            mode="waypoints",
            points="Ox + 50, Oy - 20, Ox + 150, Oy + 30",
            step_px=500.0,
            anchor="origin",
            t1=0,
            t2=1000,
        )
        self.assertIn("\\fscx60.00\\fscy20.00", res)
        self.assertIn("\\t(0,1000,\\fscx160.00\\fscy70.00)", res)

    def test_builder_shape_preserves_shadtrick_per_block(self):
        """Basics/Builder in shape mode preserves shadtrick tags inside each subpath block."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Shape/Library", "properties": {"category": "shapes", "shape": "rectangle"}},
                {"id": 2, "type": "Shape/Slicer", "properties": {"mode": "grid", "out_mode": "shape", "loop_mode": "Shape", "cols": "2", "rows": "1"}},
                {"id": 3, "type": "Functions/Move Tag", "properties": {"mode": "shadtrick", "points": "100 + bu_i*10, 50, 0.001, 0.001", "step_px": "500", "t1": "0", "t2": "1000"}},
                {"id": 4, "type": "Basics/Builder", "inputs": [{"name": "Tags", "link": 3}, {"name": "In1", "link": 2}], "properties": {"mode": "shape", "sub_mode": "splitter", "shape_split_mode": "subpaths", "inject_r": True}},
            ],
            "links": [
                [1, 1, 0, 2, 0, "data"],
                [2, 2, 0, 4, 1, "data"],
                [3, 3, 0, 4, 0, "data"],
            ],
        }
        engine = GraphEngine(graph)
        ctx = {
            "line": type("L", (), {
                "text": "Hi", "start_time": 0, "end_time": 2000,
                "center": 640, "middle": 360, "left": 600, "right": 680,
                "top": 340, "bottom": 380, "width": 80, "height": 40,
                "styleref": type("S", (), {"alignment": 5, "scale_x": 100, "scale_y": 100, "fontname": "Arial", "fontsize": 50, "outline": 2, "shadow": 0})(),
            })(),
            "meta": {"res_x": 1280, "res_y": 720},
        }
        out = engine.evaluate_data_node(4, ctx, 0)
        self.assertIn("\\1a&HFF&\\3a&HFF&\\ko0\\xshad110\\yshad50\\t(0,1000,\\xshad0.001\\yshad0.001)", out)
        self.assertIn("\\1a&HFF&\\3a&HFF&\\ko0\\xshad120\\yshad50\\t(0,1000,\\xshad0.001\\yshad0.001)", out)


if __name__ == "__main__":
    unittest.main()

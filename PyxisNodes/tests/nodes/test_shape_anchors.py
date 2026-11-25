"""Unit tests for Shape/piece anchor modes including relative2."""

import sys
import os
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from nodes.shape_nodes import resolve_piece_anchor


class TestPieceAnchorModes(unittest.TestCase):
    """Test suite for resolve_piece_anchor canonical anchor modes."""

    def test_relative_vs_relative2_org_behavior(self):
        """relative2 preserves raw relative geometry like relative, without injecting \\org."""
        raw = "m 10 20 l 30 20 l 30 40 l 10 40"
        ctx_rel = {}
        res_rel = resolve_piece_anchor(raw, piece_cx=20.0, piece_cy=30.0, parent_x=640.0, parent_y=360.0, anchor="relative", context=ctx_rel)
        self.assertEqual(res_rel["formatted_code"], raw)
        self.assertTrue(res_rel["has_org"])
        self.assertEqual((res_rel["org_x"], res_rel["org_y"]), (640.0, 360.0))

        ctx_rel2 = {}
        res_rel2 = resolve_piece_anchor(raw, piece_cx=20.0, piece_cy=30.0, parent_x=640.0, parent_y=360.0, anchor="relative2", context=ctx_rel2)
        self.assertEqual(res_rel2["formatted_code"], raw)
        self.assertFalse(res_rel2["has_org"])
        self.assertFalse(res_rel2["pos_overridden"])
        self.assertEqual((res_rel2["pos_x"], res_rel2["pos_y"]), (640.0, 360.0))
        self.assertFalse(ctx_rel2.get("has_org", False))


if __name__ == "__main__":
    unittest.main()

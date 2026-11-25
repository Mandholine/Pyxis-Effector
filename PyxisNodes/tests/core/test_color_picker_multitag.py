# -*- coding: utf-8 -*-
"""Unit tests for Basics/Color Picker and Basics/MultiTag routing in Pyxis Effector.

Validates that Color Picker resolves multi-slot outputs accurately when configured
with multiple colors, ensuring that each color output slot correctly matches
its corresponding swatch index without off-by-one errors.
"""

import os
import sys
import unittest

_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from node_engine import GraphEngine


class TestColorPickerMultiTagRouting(unittest.TestCase):
    """Test suite for Color Picker multi-swatch output resolution and MultiTag integration."""

    def setUp(self):
        self.engine = GraphEngine()

    def test_single_color_picker_outputs(self):
        """Verifies that a Color Picker with a single swatch outputs both the palette and the swatch."""
        node = {
            "id": 1,
            "type": "Basics/Color Picker",
            "properties": {
                "colors": ["#FF0000"],
                "formats": ["ASS"],
            },
            "inputs": [],
            "outputs": [{"name": "Color List"}, {"name": "Color 1"}],
        }
        self.engine.nodes = {1: node}
        self.engine.links_by_id = {}

        # Slot 0 should return palette list
        palette = self.engine.evaluate_data_node(1, {}, output_slot_index=0)
        self.assertEqual(palette, "&H0000FF&")

        # Slot 1 should return Color 1
        col1 = self.engine.evaluate_data_node(1, {}, output_slot_index=1)
        self.assertEqual(col1, "&H0000FF&")

    def test_multi_color_picker_individual_swatches(self):
        """Verifies that multiple swatches correctly map to output slots 1..N without off-by-one shifts."""
        node = {
            "id": 1,
            "type": "Basics/Color Picker",
            "properties": {
                "colors": ["#FF0000", "#00FF00", "#0000FF"],
                "formats": ["ASS", "ASS", "ASS"],
            },
            "inputs": [],
            "outputs": [
                {"name": "Color List"},
                {"name": "Color 1"},
                {"name": "Color 2"},
                {"name": "Color 3"},
            ],
        }
        self.engine.nodes = {1: node}
        self.engine.links_by_id = {}

        # Slot 0: Full palette list
        palette = self.engine.evaluate_data_node(1, {}, output_slot_index=0)
        self.assertEqual(palette, "&H0000FF&, &H00FF00&, &HFF0000&")

        # Slot 1: Color 1 (Red #FF0000 -> &H0000FF&)
        col1 = self.engine.evaluate_data_node(1, {}, output_slot_index=1)
        self.assertEqual(col1, "&H0000FF&")

        # Slot 2: Color 2 (Green #00FF00 -> &H00FF00&)
        col2 = self.engine.evaluate_data_node(1, {}, output_slot_index=2)
        self.assertEqual(col2, "&H00FF00&")

        # Slot 3: Color 3 (Blue #0000FF -> &HFF0000&)
        col3 = self.engine.evaluate_data_node(1, {}, output_slot_index=3)
        self.assertEqual(col3, "&HFF0000&")

    def test_multi_color_picker_connected_to_multitags(self):
        """Verifies that separate MultiTag nodes wired to distinct Color Picker slots receive correct colors."""
        color_node = {
            "id": 1,
            "type": "Basics/Color Picker",
            "properties": {
                "colors": ["#FF0000", "#0000FF"],
                "formats": ["ASS", "ASS"],
            },
            "inputs": [],
            "outputs": [{"name": "Color List"}, {"name": "Color 1"}, {"name": "Color 2"}],
        }
        tag_1c = {
            "id": 2,
            "type": "Basics/MultiTag",
            "properties": {"tag_type": "1c"},
            "inputs": [{"name": "value", "link": 101}],
            "outputs": [{"name": "Tag"}],
        }
        tag_3c = {
            "id": 3,
            "type": "Basics/MultiTag",
            "properties": {"tag_type": "3c"},
            "inputs": [{"name": "value", "link": 102}],
            "outputs": [{"name": "Tag"}],
        }

        self.engine.nodes = {1: color_node, 2: tag_1c, 3: tag_3c}
        # Link 101: Color Picker slot 1 (Color 1: Red) -> tag_1c
        # Link 102: Color Picker slot 2 (Color 2: Blue) -> tag_3c
        self.engine.links_by_id = {
            101: [101, 1, 1, 2, 0, "data"],
            102: [102, 1, 2, 3, 0, "data"],
        }

        res_1c = self.engine.evaluate_data_node(2, {}, 0)
        res_3c = self.engine.evaluate_data_node(3, {}, 0)

        # 1c should receive Color 1 (Red #FF0000 -> \1c&H0000FF&)
        self.assertEqual(res_1c, "\\1c&H0000FF&")
        # 3c should receive Color 2 (Blue #0000FF -> \3c&HFF0000&)
        self.assertEqual(res_3c, "\\3c&HFF0000&")


if __name__ == "__main__":
    unittest.main()

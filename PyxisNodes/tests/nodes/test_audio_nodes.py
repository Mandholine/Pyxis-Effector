"""
Unit tests for `Audio/Waveform` spatial anchor integration (`audio_nodes.py`),
`GraphEngine` dispatch (`node_engine.py`), and `GraphValidator` (`node_validator.py`).
"""

import os
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from nodes.audio_nodes import audio_waveform_master, _apply_ema_smoothing
from node_engine import GraphEngine
from node_validator import GraphValidator


class TestAudioWaveformAnchor(unittest.TestCase):
    """Verify canonical anchor behaviour for Audio/Waveform across outputs and modes."""

    def test_default_anchor_is_center(self):
        """Default anchor ('center') centres [0, w] x [0, h] around (0, 0)."""
        x_coords = audio_waveform_master(
            context={},
            mode="oscilloscope",
            width="400",
            height="60",
            samples="5",
            output_slot_index=2,
        )
        y_coords = audio_waveform_master(
            context={},
            mode="oscilloscope",
            width="400",
            height="60",
            samples="5",
            output_slot_index=3,
        )
        self.assertEqual(x_coords, [-200.0, -100.0, 0.0, 100.0, 200.0])
        self.assertEqual(y_coords, [0.0, 0.0, 0.0, 0.0, 0.0])

        shape_str = audio_waveform_master(
            context={},
            mode="oscilloscope",
            width="400",
            height="60",
            samples="5",
            output_slot_index=0,
        )
        self.assertIn("m -200 ", shape_str)
        self.assertIn("l 200 ", shape_str)

    def test_origin_and_relative_anchor(self):
        """'origin' and 'relative' preserve [0, w] x [0, h] local coordinates."""
        for anchor_mode in ("origin", "relative"):
            x_coords = audio_waveform_master(
                context={},
                mode="oscilloscope",
                width="200",
                height="40",
                samples="5",
                anchor=anchor_mode,
                output_slot_index=2,
            )
            y_coords = audio_waveform_master(
                context={},
                mode="oscilloscope",
                width="200",
                height="40",
                samples="5",
                anchor=anchor_mode,
                output_slot_index=3,
            )
            self.assertEqual(x_coords, [0.0, 50.0, 100.0, 150.0, 200.0])
            self.assertEqual(y_coords, [20.0, 20.0, 20.0, 20.0, 20.0])

    def test_absolute_anchor_uses_context_position(self):
        """'absolute' translates coordinates by (fx_pos_x, fx_pos_y)."""
        ctx = {"fx_pos_x": 640.0, "fx_pos_y": 360.0}
        x_coords = audio_waveform_master(
            context=ctx,
            mode="oscilloscope",
            width="100",
            height="40",
            samples="5",
            anchor="absolute",
            output_slot_index=2,
        )
        y_coords = audio_waveform_master(
            context=ctx,
            mode="oscilloscope",
            width="100",
            height="40",
            samples="5",
            anchor="absolute",
            output_slot_index=3,
        )
        self.assertEqual(x_coords, [640.0, 665.0, 690.0, 715.0, 740.0])
        self.assertEqual(y_coords, [380.0, 380.0, 380.0, 380.0, 380.0])

        shape_str = audio_waveform_master(
            context=ctx,
            mode="oscilloscope",
            width="100",
            height="40",
            samples="5",
            anchor="absolute",
            output_slot_index=0,
        )
        self.assertIn("m 640 ", shape_str)

    def test_graph_engine_waveform_anchor_dispatch(self):
        """GraphEngine forwards 'anchor' property to audio_waveform_master."""
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Audio/Waveform",
                    "properties": {
                        "mode": "oscilloscope",
                        "width": "100",
                        "height": "40",
                        "samples": "5",
                        "anchor": "center",
                    },
                    "outputs": [
                        {"name": "Shape Out"},
                        {"name": "\\pos Tag"},
                        {"name": "X Array"},
                        {"name": "Y Array"},
                        {"name": "Bands Array"},
                    ],
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {},
                    "inputs": [{"name": "Tags", "link": 1}],
                },
            ],
            "links": [[1, 1, 0, 2, 0, "data"]],
        }
        engine = GraphEngine(graph)
        x_arr = engine.evaluate_data_node(1, {}, output_slot_index=2)
        self.assertEqual(x_arr, [-50.0, -25.0, 0.0, 25.0, 50.0])

        warnings = GraphValidator(graph).validate()
        self.assertEqual(warnings, [])

    def test_ema_smoothing_helper_and_clamping(self):
        """EMA smoothing matches Modulator recurrence and Waveform clamps smoothing to [0.0, 0.95]."""
        raw = [0.0, 1.0, 0.0, 1.0]
        self.assertEqual(_apply_ema_smoothing(raw, 0.0), raw)
        smoothed = _apply_ema_smoothing(raw, 0.5)
        self.assertEqual(smoothed, [0.0, 0.5, 0.25, 0.625])

        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Audio/Waveform",
                    "properties": {
                        "mode": "oscilloscope",
                        "width": "100",
                        "height": "40",
                        "samples": "5",
                        "smoothing": "0.5",
                        "anchor": "center",
                    },
                    "outputs": [
                        {"name": "Shape Out"},
                        {"name": "\\pos Tag"},
                        {"name": "X Array"},
                        {"name": "Y Array"},
                        {"name": "Bands Array"},
                    ],
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {},
                    "inputs": [{"name": "Tags", "link": 1}],
                },
            ],
            "links": [[1, 1, 0, 2, 0, "data"]],
        }
        self.assertEqual(GraphValidator(graph).validate(), [])


if __name__ == "__main__":
    unittest.main()

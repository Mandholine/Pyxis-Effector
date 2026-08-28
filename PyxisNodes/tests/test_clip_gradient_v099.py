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

import unittest
import sys
import os

dev_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if dev_path not in sys.path:
    sys.path.insert(0, dev_path)

from nodes.shape_nodes import clip_gradient_node
from ass_parser import KaraokeProcessor
from node_engine import GraphEngine


class TestClipGradientV099(unittest.TestCase):
    def setUp(self):
        self.raw_line = r"Dialogue: 1,0:00:08.32,0:00:13.33,Default,,0,0,0,,{\k44}Ma{\k65}ry"
        self.styles = {
            "Default": {
                "Fontname": "Arial",
                "Fontsize": "48",
                "Bold": "0",
                "Italic": "0",
                "Alignment": "2",
                "MarginL": "10",
                "MarginR": "10",
                "MarginV": "10"
            }
        }
        self.proc = KaraokeProcessor(1280, 720, 10)
        self.line = self.proc.process_line(self.raw_line, self.styles["Default"], {"sel": True})
        self.syl = self.line.syls[0]

    def test_horizontal_rectangular_clip_0deg(self):
        """Ángulo 0° genera clips rectangulares nativos AABB \\clip(x1,y1,x2,y2)."""
        ctx = {'line': self.line, 'active_line': self.line, 'syl': self.syl, 'active_unit': self.syl, 'j': 1}
        tag, prog, idx, total = clip_gradient_node(ctx, num_clips="4", angle="0", padding="2", overlap="0.5", out_mode="Clip")
        
        self.assertTrue(tag.startswith(r"\clip("))
        self.assertFalse("m " in tag) # Debe ser rectangular puro, sin assdraw
        self.assertEqual(prog, 0.0)
        self.assertEqual(idx, 1)
        self.assertEqual(total, 4)

    def test_horizontal_rectangular_clip_180deg(self):
        """Ángulo 180° genera clips rectangulares nativos AABB \\clip(x1,y1,x2,y2) en sentido horizontal invertido."""
        ctx = {'line': self.line, 'active_line': self.line, 'syl': self.syl, 'active_unit': self.syl, 'j': 1}
        tag, prog, idx, total = clip_gradient_node(ctx, num_clips="4", angle="180", padding="2", overlap="0.5", out_mode="Clip")
        
        self.assertTrue(tag.startswith(r"\clip("))
        self.assertFalse("m " in tag)
        self.assertEqual(idx, 1)
        self.assertEqual(total, 4)

    def test_vertical_rectangular_clip_90deg(self):
        """Ángulo 90° genera clips rectangulares verticales nativos AABB \\clip(x1,y1,x2,y2)."""
        ctx = {'line': self.line, 'active_line': self.line, 'syl': self.syl, 'active_unit': self.syl, 'j': 4}
        tag, prog, idx, total = clip_gradient_node(ctx, num_clips="4", angle="90", padding="2", overlap="0.5", out_mode="Clip")
        
        self.assertTrue(tag.startswith(r"\clip("))
        self.assertFalse("m " in tag)
        self.assertEqual(prog, 1.0)
        self.assertEqual(idx, 4)
        self.assertEqual(total, 4)

    def test_vertical_rectangular_clip_270deg(self):
        """Ángulo 270° genera clips rectangulares verticales nativos AABB \\clip(x1,y1,x2,y2) en sentido vertical invertido."""
        ctx = {'line': self.line, 'active_line': self.line, 'syl': self.syl, 'active_unit': self.syl, 'j': 1}
        tag, prog, idx, total = clip_gradient_node(ctx, num_clips="4", angle="270", padding="2", overlap="0.5", out_mode="Clip")
        
        self.assertTrue(tag.startswith(r"\clip("))
        self.assertFalse("m " in tag)
        self.assertEqual(idx, 1)
        self.assertEqual(total, 4)

    def test_negative_angles_normalization(self):
        """Ángulos negativos (-90°, -180°, -270°) se normalizan y generan clips rectangulares AABB."""
        ctx = {'line': self.line, 'active_line': self.line, 'syl': self.syl, 'active_unit': self.syl, 'j': 1}
        
        # -90° equivale a 270° (Vertical rectangular)
        tag_neg90, _, _, _ = clip_gradient_node(ctx, num_clips="4", angle="-90", out_mode="Clip")
        self.assertTrue(tag_neg90.startswith(r"\clip("))
        self.assertFalse("m " in tag_neg90)

        # -180° equivale a 180° (Horizontal rectangular)
        tag_neg180, _, _, _ = clip_gradient_node(ctx, num_clips="4", angle="-180", out_mode="Clip")
        self.assertTrue(tag_neg180.startswith(r"\clip("))
        self.assertFalse("m " in tag_neg180)

        # -270° equivale a 90° (Vertical rectangular)
        tag_neg270, _, _, _ = clip_gradient_node(ctx, num_clips="4", angle="-270", out_mode="Clip")
        self.assertTrue(tag_neg270.startswith(r"\clip("))
        self.assertFalse("m " in tag_neg270)

    def test_iclip_and_forma_modes(self):
        """Prueba salida \\iclip(...) y salida ASSdraw puro 'm ...'."""
        ctx = {'line': self.line, 'active_line': self.line, 'syl': self.syl, 'active_unit': self.syl, 'j': 1}
        
        # Modo iClip
        tag_iclip, _, _, _ = clip_gradient_node(ctx, num_clips="3", angle="0", out_mode="iClip")
        self.assertTrue(tag_iclip.startswith(r"\iclip("))
        
        # Modo Forma: debe estar centrado alrededor de (0, 0)
        tag_forma, _, _, _ = clip_gradient_node(ctx, num_clips="3", angle="0", out_mode="Shape")
        self.assertTrue(tag_forma.startswith("m "))
        self.assertFalse(r"\clip" in tag_forma)
        # Verifica que las coordenadas x e y incluyan valores negativos alrededor de 0
        coords = [float(c) for c in tag_forma.replace("m", "").replace("l", "").split()]
        min_x = min(coords[0::2])
        max_x = max(coords[0::2])
        self.assertLess(min_x, 0.0) # b_left relativo es negativo (-w/2 - pad)
        self.assertGreater(max_x, -w_val if 'w_val' in locals() else -100.0)

    def test_order_inversion_and_progress(self):
        """Prueba inversión de orden."""
        ctx1 = {'line': self.line, 'active_line': self.line, 'syl': self.syl, 'active_unit': self.syl, 'j': 1}
        tag1, prog1, _, _ = clip_gradient_node(ctx1, num_clips="5", angle="0", order="Normal")
        
        ctx2 = {'line': self.line, 'active_line': self.line, 'syl': self.syl, 'active_unit': self.syl, 'j': 1}
        tag2, prog2, _, _ = clip_gradient_node(ctx2, num_clips="5", angle="0", order="Invertido")
        
        self.assertEqual(prog1, 0.0)
        self.assertEqual(prog2, 1.0) # El primer paso del invertido es la última franja
        self.assertNotEqual(tag1, tag2)

    def test_graph_engine_auto_loop_integration(self):
        """Verifica ejecución completa de Grafo con Main Loop SYL + Clip Gradient generando N sub-clips por sílaba."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"bucle": "SYL", "iterador": "syl", "noblank": "No Blank"}, "outputs": [{"name": "Loop", "type": "loop", "links": [101]}]},
                {"id": 2, "type": "Shape/Clip Gradient", "properties": {"num_clips": "3", "angle": "0", "padding": "4", "overlap": "0.5", "order": "Normal", "out_mode": "Clip"}, "outputs": [{"name": "Output", "type": "string", "links": [102]}, {"name": "Progress (0-1)", "type": "number", "links": [103]}, {"name": "Index", "type": "number", "links": []}, {"name": "Total", "type": "number", "links": []}]},
                {"id": 3, "type": "Functions/Color Gradient", "inputs": [{"name": "Progress (0-1)", "link": 103}], "properties": {"colors_str": "#FF0000,#0000FF"}, "outputs": [{"name": "ASS Color", "type": "string", "links": [104]}]},
                {"id": 4, "type": "MultiTag", "properties": {"tag": "\\1c", "modo": "1c"}, "inputs": [{"name": "Value", "link": 104}], "outputs": [{"name": "String", "type": "string", "links": [105]}]},
                {"id": 5, "type": "Concatenate", "properties": {"delimitador": ""}, "inputs": [{"name": "In1", "link": 105}, {"name": "In2", "link": 102}], "outputs": [{"name": "String", "type": "string", "links": [106]}]},
                {"id": 6, "type": "System/Output", "properties": {"apply_to": "Selected Lines"}, "inputs": [{"name": "Loop / Domain", "type": "loop", "link": 101}, {"name": "Layer", "link": 0}, {"name": "Start Time", "link": 0}, {"name": "End Time", "link": 0}, {"name": "Tags", "type": "string", "link": 106}, {"name": "Return", "type": "string", "link": 0}]}
            ],
            "links": [
                [101, 1, 0, 6, 0, "loop"],
                [102, 2, 0, 5, 1, "string"],
                [103, 2, 1, 3, 0, "number"],
                [104, 3, 0, 4, 0, "string"],
                [105, 4, 0, 5, 0, "string"],
                [106, 5, 0, 6, 4, "string"]
            ]
        }
        
        dialogues = [{"raw": self.raw_line, "metrics": {"sel": True}}]
        engine = GraphEngine(graph)
        lines = engine.process(dialogues, self.styles)
        
        # 2 sílabas ("Ma", "ry") x 3 franjas = 6 líneas generadas
        self.assertEqual(len(lines), 6)
        for l in lines:
            self.assertIn(r"\clip(", l)
            self.assertIn(r"\1c&H", l)


if __name__ == '__main__':
    unittest.main()

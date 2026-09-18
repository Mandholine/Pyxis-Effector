import unittest
import sys
import os

# Add parent path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ass_parser import KaraokeProcessor
from font_engine import FontEngine
from font_vector_engine import FontVectorEngine
from node_engine import GraphEngine

class TestASSParserDivisionModes(unittest.TestCase):
    def setUp(self):
        self.processor = KaraokeProcessor(1280, 720)
        self.style = {
            "Name": "Default",
            "Fontname": "Arial",
            "Fontsize": 65.0,
            "Bold": False,
            "Italic": False,
            "ScaleX": 100.0,
            "ScaleY": 100.0,
            "Spacing": 0.0,
            "Alignment": 5,
            "MarginL": 10,
            "MarginR": 10,
            "MarginV": 10
        }
        self.raw_karaoke = r"Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{\k10}i{\k10}t{\k10}s{\k10}u{\k10}k{\k10}a{\k10} {\k10}n{\k10}o{\k10} {\k10}a{\k10}s{\k10}a{\k10} {\k10}n{\k10}o{\k10} {\k10}n{\k10}i{\k10}o{\k10}i"
        self.raw_plain = r"Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,itsuka no asa no nioi"

    def test_char_mode_no_duplicate_spaces(self):
        """Verifica que el desglose de caracteres no duplique espacios en sílabas de karaoke."""
        line = self.processor.process_line(self.raw_karaoke, self.style)
        self.assertIsNotNone(line)
        # "itsuka no asa no nioi" tiene exactamente 21 caracteres
        self.assertEqual(len(line.chars), 21)
        full_text = "".join(c.text for c in line.chars)
        self.assertEqual(full_text, "itsuka no asa no nioi")

        # Verificar que no haya dos espacios consecutivos
        for i in range(len(line.chars) - 1):
            if line.chars[i].text.isspace():
                self.assertFalse(line.chars[i+1].text.isspace(), f"Espacio duplicado detectado en índice {i}")

    def test_char_mode_monotonic_layout(self):
        """Verifica que los caracteres avancen estrictamente hacia la derecha de forma no decreciente."""
        line = self.processor.process_line(self.raw_karaoke, self.style)
        prev_right = line.left
        for i, ch in enumerate(line.chars):
            self.assertGreaterEqual(ch.left, prev_right - 0.01, f"Carácter {i} '{ch.text}' solapa hacia la izquierda")
            self.assertAlmostEqual(ch.right, ch.left + ch.width, places=2)
            self.assertAlmostEqual(ch.center, ch.left + ch.width / 2.0, places=2)
            prev_right = ch.right

    def test_word_mode_distribution(self):
        """Verifica la correcta agrupación y métricas de palabras (word mode)."""
        line = self.processor.process_line(self.raw_karaoke, self.style)
        # Palabras esperadas: "itsuka", "no", "asa", "no", "nioi"
        expected_words = ["itsuka", "no", "asa", "no", "nioi"]
        self.assertEqual(len(line.words), 5)
        for w, exp in zip(line.words, expected_words):
            self.assertEqual(w.text_stripped, exp)
            self.assertGreater(w.width, 0)
            self.assertEqual(w.left, w.chars[0].left)
            self.assertEqual(w.right, w.chars[-1].right)
            self.assertAlmostEqual(w.center, w.left + w.width / 2.0, places=2)
            self.assertEqual(w.x, w.center)
            self.assertEqual(w.y, w.middle)

    def test_syl_mode_metrics(self):
        """Verifica que las sílabas tengan posiciones y dimensiones válidas."""
        line = self.processor.process_line(self.raw_karaoke, self.style)
        self.assertGreater(len(line.syls), 0)
        for syl in line.syls:
            self.assertAlmostEqual(syl.center, syl.left + syl.width / 2.0, places=2)
            self.assertEqual(syl.x, syl.center)
            self.assertEqual(syl.y, syl.middle)

    def test_font_vector_engine_single_char_quantization(self):
        """Verifica que FontVectorEngine cuantice caracteres individuales de forma coherente."""
        shape_single = FontVectorEngine.text_to_shape("a", font_name="Arial", font_size=65.0)
        self.assertTrue(shape_single.startswith("m ") or shape_single.startswith("m-") or " m " in shape_single)
        self.assertNotIn("NaN", shape_single)

    def test_node_engine_origin_align_reverted(self):
        """Verifica que node_engine no sobrescriba origin_align con un tag explicito \anX."""
        engine = GraphEngine({"nodes": []}, 1280, 720, 41.7)
        # Simular apply_defaults con \an7
        line = self.processor.process_line(self.raw_karaoke, self.style)
        ctx = {"line": line, "val_left": 100.0, "val_center": 200.0, "val_top": 50.0, "val_middle": 75.0}
        _, _, _, tags_out, _ = engine._apply_defaults(
            line, 0, 0, 5000, r"\an7\bord1", "test", context=ctx
        )
        self.assertIn(r"\an7", tags_out)
        self.assertIn(r"\pos(200,75)", tags_out)

if __name__ == '__main__':
    unittest.main()

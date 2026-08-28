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

# test_pyxis_karaskel_integration.py
"""Test de integración de KaraskelEngine con ASSParser y KaraokeProcessor en PyxisNodes."""

import unittest
import os
from ass_parser import ASSParser, KaraokeProcessor


class TestPyxisKaraskelIntegration(unittest.TestCase):

    def test_process_preview_base_line(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        preview_base_path = os.path.join(base_dir, "preview_base.ass")
        if not os.path.exists(preview_base_path):
            preview_base_path = os.path.join(os.path.dirname(base_dir), "preview_base.ass")
        
        self.assertTrue(os.path.exists(preview_base_path), f"File not found: {preview_base_path}")

        parse_res = ASSParser.read_file(preview_base_path)
        styles = parse_res.styles
        dialogues = parse_res.dialogues

        self.assertIn("Default", styles)
        self.assertGreater(len(dialogues), 0)

        kp = KaraokeProcessor(res_x=parse_res.res_x, res_y=parse_res.res_y)

        raw_line = dialogues[0]["raw"]
        style = styles["Default"]
        metrics = dialogues[0]["metrics"]

        line = kp.process_line(raw_line, style, metrics)

        self.assertIsNotNone(line)
        self.assertAlmostEqual(line.center, 500.0, delta=0.1)
        self.assertAlmostEqual(line.width, 598.33, delta=0.1)

        # Verificar estructuras jerárquicas creadas por KaraskelEngine en Python
        self.assertEqual(len(line.syls), 10)  # Lead-in (0) + 9 sílabas
        self.assertGreater(len(line.chars), 0)
        self.assertGreater(len(line.words), 0)

        # Verificar primer sílaba "Ma"
        syl1 = line.syls[1]
        self.assertEqual(syl1.text_stripped, "Ma")
        self.assertAlmostEqual(syl1.center, 241.25, delta=0.1)

        print("\n=== PyxisNodes KaraokeProcessor Integration SUCCESS ===")
        print(f"Line Center: {line.center:.2f}")
        print(f"Total Syllables: {len(line.syls)}")
        print(f"Total Chars: {len(line.chars)}")
        print(f"Total Words: {len(line.words)}")


if __name__ == "__main__":
    unittest.main()

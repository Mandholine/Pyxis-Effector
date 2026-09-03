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

"""Pruebas unitarias para el motor Karaskel y extraccion metrica de karaoke."""

import os
import unittest
from ass_parser import ASSParser, KaraokeProcessor
from karaskel_engine import KaraskelEngine, KaraskelMeta, KaraskelLine


class TestKaraskelEngine(unittest.TestCase):
    """Pruebas de preprocesamiento Karaskel, silabacion y calculo de metricas tipograficas."""

    def test_process_preview_base_file(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        preview_base_path = os.path.abspath(os.path.join(current_dir, "..", "..", "preview_base.ass"))
        if not os.path.exists(preview_base_path):
            self.skipTest(f"preview_base.ass no encontrado en: {preview_base_path}")

        parse_res = ASSParser.read_file(preview_base_path)
        self.assertIn("Default", parse_res.styles)
        self.assertGreater(len(parse_res.dialogues), 0)

        kp = KaraokeProcessor(res_x=parse_res.res_x, res_y=parse_res.res_y)
        raw_line = parse_res.dialogues[0]["raw"]
        style = parse_res.styles["Default"]
        metrics = parse_res.dialogues[0].get("metrics")

        line = kp.process_line(raw_line, style, metrics)
        self.assertIsNotNone(line)
        self.assertAlmostEqual(line.center, 500.0, delta=1.0)
        self.assertGreater(len(line.syls), 0)

    def test_karaskel_line_metrics_calculation(self):
        meta = KaraskelMeta(res_x=1280, res_y=720)
        styles = {
            "Default": {
                "Fontname": "Arial", "Fontsize": 40.0,
                "MarginL": 10, "MarginR": 10, "MarginV": 30,
                "Alignment": 2, "ScaleX": 100.0, "ScaleY": 100.0
            }
        }
        k_line = KaraskelLine(
            raw_text=r"{\k50}Hel{\k50}lo",
            start_time=1000,
            end_time=2000,
            style="Default",
            margin_l=10, margin_r=10, margin_t=30, margin_b=30
        )
        KaraskelEngine.preproc_line(meta, styles, k_line)
        self.assertGreater(k_line.width, 0.0)
        self.assertEqual(len(k_line.kara), 3)  # Lead-in (0) + 2 silabas


if __name__ == "__main__":
    unittest.main()

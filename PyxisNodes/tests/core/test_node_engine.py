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

"""Pruebas unitarias para el motor central de grafos (GraphEngine) y procesamiento de lineas."""

import unittest
from ass_parser import KaraokeProcessor
from models import PyxisLine, PyxisUnit
from node_engine import GraphEngine
from template_store import PYXIS_ENGINE_VERSION


class TestGraphEngineCore(unittest.TestCase):
    """Pruebas de inicializacion, memoria y evaluacion en GraphEngine."""

    def setUp(self):
        self.sample_line = PyxisLine()
        self.sample_line.layer = 0
        self.sample_line.start_time = 0
        self.sample_line.end_time = 2000
        self.sample_line.style_name = "Default"
        self.sample_line.text = "Hello Pyxis"
        self.sample_line.is_selected = True

        self.sample_syl = PyxisUnit()
        self.sample_syl.text = "Hello"
        self.sample_syl.text_stripped = "Hello"
        self.sample_syl.duration = 1000
        self.sample_syl.dur = 1000
        self.sample_syl.start_time = 0
        self.sample_syl.end_time = 1000
        self.sample_syl.i = 1
        self.sample_syl.n = 2
        self.sample_syl.center = 640.0
        self.sample_syl.middle = 360.0
        self.sample_line.syls = [self.sample_syl]

    def test_version_current(self):
        self.assertEqual(PYXIS_ENGINE_VERSION, "1.0.6")

    def test_remember_and_recall_memory(self):
        engine = GraphEngine({"nodes": [], "links": []})
        val = engine.remember("mi_pos_x", 450.5)
        self.assertEqual(val, 450.5)
        recalled = engine.recall("mi_pos_x", default=0.0)
        self.assertEqual(recalled, 450.5)
        default_val = engine.recall("clave_inexistente", default=123)
        self.assertEqual(default_val, 123)

    def test_simple_graph_pipeline(self):
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"base_unit": "line", "noblank": "No Blank"}
                },
                {
                    "id": 2,
                    "type": "String",
                    "properties": {"valor": "Processed Text"}
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [
                        {"name": "Loop", "type": "data", "link": 101},
                        {"name": "Capa", "type": 0, "link": None},
                        {"name": "Start", "type": 0, "link": None},
                        {"name": "End", "type": 0, "link": None},
                        {"name": "Tags", "type": 0, "link": None},
                        {"name": "Retorno", "type": "string", "link": 102}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 3, 0, "data"],
                [102, 2, 0, 3, 5, "string"]
            ]
        }
        styles = {
            'Default': {
                'Fontname': 'Arial', 'Fontsize': 40.0,
                'PrimaryColour': '&H00FFFFFF&', 'SecondaryColour': '&H000000FF&',
                'OutlineColour': '&H00000000&', 'BackColour': '&H00000000&',
                'ScaleX': 100.0, 'ScaleY': 100.0, 'Spacing': 0.0, 'Outline': 2.0,
                'Shadow': 0.0, 'Alignment': 5
            }
        }
        dialogues = [{'raw': 'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Hello', 'is_selected': True}]
        engine = GraphEngine(graph)
        engine.process_single(dialogues, styles, allow_fallback_select_all=True)
        self.assertGreater(len(engine.all_generated_lines), 0)


class TestPyxisAutonomousProcessing(unittest.TestCase):
    """Pruebas de procesamiento de lineas ASS mediante KaraokeProcessor y Karaskel."""

    def test_line_karaoke_syllables_extraction(self):
        kp = KaraokeProcessor(1280, 720, 41.708)
        raw = r"Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,{\k50}Hel{\k50}lo {\k100}World"
        style = {"Fontname": "Arial", "Fontsize": "40", "MarginL": "10", "MarginR": "10", "MarginV": "30", "Alignment": "2"}
        line = kp.process_line(raw, style)
        self.assertIsNotNone(line)
        self.assertEqual(line.start_time, 1000)
        self.assertEqual(line.end_time, 4000)
        self.assertGreater(len(line.syls), 0)


if __name__ == "__main__":
    unittest.main()

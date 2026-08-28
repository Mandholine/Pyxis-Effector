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
import unittest

# Ensure PyxisNodes package root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from node_engine import GraphEngine


class TestMultiprocessingEngine(unittest.TestCase):
    def setUp(self):
        # Construct a simple node graph: Main Loop -> Texto -> Salida
        self.graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"base_unit": "line", "noblank": "No Blank"}
                },
                {
                    "id": 2,
                    "type": "String/Texto",
                    "properties": {"text": "Test Line"}
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
                [101, 1, 0, 3, 0, "data"],   # Loop link to Salida slot 0
                [102, 2, 0, 3, 5, "string"]  # Return text link to Salida slot 5
            ]
        }

        self.styles = {
            "Default": {
                "fontname": "Arial",
                "fontsize": 20,
                "color1": "&H00FFFFFF&",
                "color2": "&H000000FF&",
                "color3": "&H00000000&",
                "color4": "&H00000000&",
                "bold": 0, "italic": 0, "underline": 0, "strikeout": 0,
                "scale_x": 100, "scale_y": 100, "spacing": 0, "angle": 0,
                "borderstyle": 1, "outline": 2, "shadow": 0, "align": 2,
                "margin_l": 10, "margin_r": 10, "margin_t": 10, "encoding": 1
            }
        }

        # Build 10 dialogue line items
        self.dialogue_items = []
        for i in range(1, 11):
            raw_line = f"Dialogue: 0,0:00:0{i}.00,0:00:0{i+1}.00,Default,NTP,0,0,0,,Line {i} Text"
            metrics = "h=20;d=4;e=0;sel=1;rw=100;l=100;c=150;r=200;t=50;m=60;b=70"
            self.dialogue_items.append({"raw": raw_line, "metrics": metrics})

    def test_single_vs_multiprocessing_identity(self):
        engine_single = GraphEngine(self.graph_data)
        out_single = engine_single.process(self.dialogue_items, self.styles, use_multiprocessing=False)

        engine_multi = GraphEngine(self.graph_data)
        out_multi = engine_multi.process(self.dialogue_items, self.styles, use_multiprocessing=True)

        self.assertEqual(len(out_single), len(out_multi), "Line count mismatch between single and multi process execution")
        self.assertEqual(out_single, out_multi, "Generated ASS lines differ between single and multi process execution")

    def test_multiprocessing_performance_and_cores(self):
        cpu_cores = os.cpu_count() or 1
        engine = GraphEngine(self.graph_data)
        res = engine.process(self.dialogue_items, self.styles, use_multiprocessing=True)
        self.assertTrue(len(res) > 0, "Multiprocessing returned empty results")
        print(f"\n[Test MP Engine] Executed successfully across {cpu_cores} CPU cores with {len(res)} output lines.")


if __name__ == "__main__":
    unittest.main()

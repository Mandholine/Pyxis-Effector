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

"""Pruebas unitarias para el motor de previsualizacion en tiempo real y conexion con nodos Salida."""

import unittest
from node_engine import GraphEngine


class TestPreviewSinglePort(unittest.TestCase):
    """Pruebas de generacion de preview y resolucion de puertos de salida."""

    def setUp(self):
        self.dialogues = [{
            'raw': r"Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\k50}Test{\k50}Line",
            'metrics': {'h': 20.0, 'd': 5.0, 'e': 0.0, 'sel': True, 'w': [40.0, 40.0]}
        }]
        self.styles = {
            "Default": {
                "Fontname": "Arial", "Fontsize": 40.0,
                "PrimaryColour": "&H00FFFFFF&", "SecondaryColour": "&H000000FF&",
                "OutlineColour": "&H00000000&", "BackColour": "&H00000000&",
                "ScaleX": 100.0, "ScaleY": 100.0, "Spacing": 0.0, "Outline": 2.0,
                "Shadow": 0.0, "Alignment": 5
            }
        }

    def test_default_output_id_matching(self):
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl"},
                    "outputs": [{"name": "Loop", "type": "bucle", "links": [101]}]
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 101},
                        {"name": "Layer", "type": "data", "link": None},
                        {"name": "Start Time", "type": "data", "link": None},
                        {"name": "End Time", "type": "data", "link": None},
                        {"name": "Tags", "type": "data", "link": None},
                        {"name": "Return", "type": "data", "link": None},
                        {"name": "Queue ID", "type": "data", "link": None},
                        {"name": "Queue Order", "type": "data", "link": None}
                    ],
                    "outputs": []
                }
            ],
            "links": [
                [101, 1, 0, 2, 0, "bucle"]
            ]
        }
        engine = GraphEngine(graph_data)
        engine.process_single(self.dialogues, self.styles, allow_fallback_select_all=True)
        self.assertGreaterEqual(len(engine.all_generated_lines), 1)


if __name__ == "__main__":
    unittest.main()

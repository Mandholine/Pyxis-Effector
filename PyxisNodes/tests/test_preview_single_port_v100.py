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

# PyxisNodes/tests/test_preview_single_port_v100.py
"""Pruebas unitarias para la refactorización a puerto único del nodo Previsualizador y resolución dinámica de salidas."""

import unittest
from node_engine import GraphEngine

class TestPreviewSinglePort(unittest.TestCase):

    def setUp(self):
        self.dialogues = [{
            'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k50}Test{\\k50}Line",
            'metrics': {'h': 20.0, 'd': 5.0, 'e': 0.0, 'sel': True, 'w': [40.0, 40.0]}
        }]
        self.styles = {"Default": {}}

    def test_default_output_id_matching(self):
        """Verifica que las salidas sin output_id explícito se clasifiquen como 'default' y coincidan con el previsualizador."""
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
                    "properties": {"apply_to": "All Lines"}, # Sin ID -> 'default'
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

        engine = GraphEngine(graph_data, 1000, 260, 41.7)
        engine.target_output_id = ["default"]
        lines = engine.process(self.dialogues, self.styles)
        self.assertGreater(len(lines), 0)

    def test_multiple_outputs_with_concatenar(self):
        """Verifica la resolución de múltiples salidas (default y con ID personalizado)."""
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl"},
                    "outputs": [{"name": "Loop", "type": "bucle", "links": [101, 102]}]
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines"}, # Sin ID -> 'default'
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
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines", "output_id": "capa2"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 102},
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
                [101, 1, 0, 2, 0, "bucle"],
                [102, 1, 0, 3, 0, "bucle"]
            ]
        }

        engine1 = GraphEngine(graph_data, 1000, 260, 41.7)
        engine1.target_output_id = ["default"]
        lines1 = engine1.process(self.dialogues, self.styles)
        self.assertGreater(len(lines1), 0)

        engine2 = GraphEngine(graph_data, 1000, 260, 41.7)
        engine2.target_output_id = ["default", "capa2"]
        lines2 = engine2.process(self.dialogues, self.styles)
        self.assertGreater(len(lines2), len(lines1))

    def test_numeric_leading_zero_matching(self):
        """Verifica que objetivos como '002' o '02' coincidan numéricamente con el nodo Salida id=2."""
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

        engine = GraphEngine(graph_data, 1000, 260, 41.7)
        engine.target_output_id = ["002"]
        lines = engine.process(self.dialogues, self.styles)
        self.assertGreater(len(lines), 0)

if __name__ == "__main__":
    unittest.main()

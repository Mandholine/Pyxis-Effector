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

import json
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from node_engine import GraphEngine

class TestSessionIntegrity(unittest.TestCase):
    def test_dynamic_nodes_graph_processing(self):
        """Verifica que un grafo con nodos dinámicos conectados (Tag Dinámico, Random, Memoria, Condicionador) procesa correctamente sin pérdida de datos."""
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
                    "type": "MultiTag",
                    "properties": {"tag_type": "pos", "X": "150", "Y": "250"},
                    "inputs": [
                        {"name": "X", "type": "data", "link": None},
                        {"name": "Y", "type": "data", "link": None}
                    ],
                    "outputs": [{"name": "String", "type": "data", "links": [102]}]
                },
                {
                    "id": 3,
                    "type": "Variables/Memory",
                    "properties": {"modo": "Remember (Guardar)", "clave": "test_var", "valor": "hello"},
                    "inputs": [
                        {"name": "Key", "type": "data", "link": None},
                        {"name": "Value", "type": "data", "link": None}
                    ],
                    "outputs": [{"name": "Data", "type": "data", "links": None}]
                },
                {
                    "id": 4,
                    "type": "MultiRandom",
                    "properties": {"modo": "R", "min": "10", "max": "50", "step": "1"},
                    "inputs": [
                        {"name": "Min", "type": "data", "link": None},
                        {"name": "Max", "type": "data", "link": None},
                        {"name": "Step", "type": "data", "link": None}
                    ],
                    "outputs": [{"name": "Data", "type": "data", "links": None}]
                },
                {
                    "id": 5,
                    "type": "Functions/Conditioner",
                    "properties": {"condicion": "True", "si_verdadero": "VERDADERO", "si_falso": "FALSO"},
                    "inputs": [
                        {"name": "Condition", "type": "data", "link": None},
                        {"name": "If True", "type": "data", "link": None},
                        {"name": "If False", "type": "data", "link": None}
                    ],
                    "outputs": [{"name": "String", "type": "data", "links": [103]}]
                },
                {
                    "id": 6,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 101},
                        {"name": "Layer", "type": "data", "link": None},
                        {"name": "Start Time", "type": "data", "link": None},
                        {"name": "End Time", "type": "data", "link": None},
                        {"name": "Tags", "type": "data", "link": 102},
                        {"name": "Return", "type": "data", "link": 103},
                        {"name": "Queue ID", "type": "data", "link": None},
                        {"name": "Queue Order", "type": "data", "link": None}
                    ],
                    "outputs": []
                }
            ],
            "links": [
                [101, 1, 0, 6, 0, "bucle"],
                [102, 2, 0, 6, 4, "data"],
                [103, 5, 0, 6, 5, "data"]
            ]
        }

        styles = {"Default": {}}
        dialogues = [{
            'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k50}Test{\\k50}Line",
            'metrics': {'h': 20.0, 'd': 5.0, 'e': 0.0, 'sel': True, 'w': [40.0, 40.0]}
        }]

        engine = GraphEngine(graph_data, 1280, 720, 41.708)
        lines = engine.process(dialogues, styles)
        self.assertTrue(len(lines) > 0, "El motor debe generar líneas")
        self.assertTrue(any("\\pos(150,250)" in l for l in lines), "Debe incluir el tag pos del Tag Dinámico")
        self.assertTrue(any("VERDADERO" in l for l in lines), "Debe incluir la salida del Condicionador")

if __name__ == "__main__":
    unittest.main()

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

# Ajustar path para incluir PyxisNodes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from node_engine import GraphEngine
from models import PyxisLine, PyxisUnit


class TestStage1Features(unittest.TestCase):
    def setUp(self):
        self.sample_line = PyxisLine()
        self.sample_line.layer = 0
        self.sample_line.start_time = 0
        self.sample_line.end_time = 2000
        self.sample_line.style_name = "Default"
        self.sample_line.text = "Hello Pyxis 0.9.6"
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

    def test_version_bump(self):
        from main import PYXIS_ENGINE_VERSION
        self.assertEqual(PYXIS_ENGINE_VERSION, "1.0.4")

    def test_remember_and_recall_memory(self):
        engine = GraphEngine({"nodes": [], "links": []})
        
        # Probar remember
        val = engine.remember("mi_pos_x", 450.5)
        self.assertEqual(val, 450.5)
        self.assertEqual(engine.memory.get("mi_pos_x"), 450.5)
        
        # Probar recall
        recalled = engine.recall("mi_pos_x")
        self.assertEqual(recalled, 450.5)
        
        # Probar recall con default
        default_val = engine.recall("clave_inexistente", "123")
        self.assertEqual(default_val, "123")

    def test_memoria_master_node_remember_mode(self):
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Variables/Memory",
                    "properties": {"modo": "Remember (Guardar)", "clave": "contador", "valor": "100"},
                    "inputs": [{"name": "Key"}, {"name": "Value"}]
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph_data)
        context = {"line": self.sample_line, "active_unit": self.sample_syl}
        engine.bind_active_unit(context, self.sample_syl)
        
        res = engine.evaluate_data_node(1, context)
        self.assertEqual(res, "100")
        self.assertEqual(engine.memory.get("contador"), "100")

    def test_memoria_master_node_recall_mode(self):
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Variables/Memory",
                    "properties": {"modo": "Recall (Recuperar)", "clave": "contador", "default": "0"},
                    "inputs": [{"name": "Key"}, {"name": "Default"}]
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph_data)
        context = {"line": self.sample_line, "active_unit": self.sample_syl}
        engine.bind_active_unit(context, self.sample_syl)
        
        # Inicialmente debe retornar default '0'
        res1 = engine.evaluate_data_node(1, context)
        self.assertEqual(res1, "0")
        
        # Guardar en memoria
        engine.remember("contador", "55")
        res2 = engine.evaluate_data_node(1, context)
        self.assertEqual(res2, "55")

    def test_fallback_input_properties_when_unconnected(self):
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "MultiTag",
                    "properties": {"tag_type": "pos", "x": "120", "y": "340"},
                    "inputs": [{"name": "x"}, {"name": "y"}]
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph_data)
        context = {"line": self.sample_line, "active_unit": self.sample_syl}
        engine.bind_active_unit(context, self.sample_syl)
        
        res = engine.evaluate_data_node(1, context)
        self.assertEqual(res, "\\pos(120,340)")

    def test_full_graph_remember_and_recall_integration(self):
        # Simular un grafo completo con Main Loop -> Salida, un nodo Remember y un nodo Recall conectado a Tags
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl"},
                    "outputs": [{"name": "Loop"}]
                },
                {
                    "id": 2,
                    "type": "Variables/Memory",
                    "properties": {"modo": "Remember (Guardar)", "clave": "pos_guardada", "valor": "\\pos(640,360)"},
                    "inputs": [{"name": "Key"}, {"name": "Value"}]
                },
                {
                    "id": 3,
                    "type": "Variables/Memory",
                    "properties": {"modo": "Recall (Recuperar)", "clave": "pos_guardada", "default": "\\pos(0,0)"},
                    "inputs": [{"name": "Key"}, {"name": "Default"}],
                    "outputs": [{"name": "Data"}]
                },
                {
                    "id": 4,
                    "type": "System/Output",
                    "properties": {"apply_to": "Sel. Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 101},
                        {"name": "Layer"}, {"name": "Start Time"}, {"name": "End Time"},
                        {"name": "Tags", "link": 102},
                        {"name": "Return"}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 4, 0], # Loop -> Salida (Bucle)
                [102, 3, 0, 4, 4]  # Recall -> Salida (Tags)
            ]
        }
        engine = GraphEngine(graph_data)
        styles = {"Default": {}}
        dialogue_items = [{
            "raw": "Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,{\\k100}Hello",
            "metrics": {"rw": 100, "h": 20, "sel": True}
        }]
        
        lines = engine.process(dialogue_items, styles)
        self.assertEqual(len(lines), 1)
        self.assertIn("\\pos(640,360)", lines[0])

    def test_salida_queue_properties_fallback(self):
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "line"},
                    "outputs": [{"name": "Loop"}]
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {"apply_to": "Sel. Lines", "queue_id": "CustomQ", "queue_order": "5"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 101},
                        {"name": "Layer"}, {"name": "Start Time"}, {"name": "End Time"},
                        {"name": "Tags"}, {"name": "Return"},
                        {"name": "Queue ID"}, {"name": "Queue Order"}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 2, 0]
            ]
        }
        engine = GraphEngine(graph_data)
        styles = {"Default": {}}
        dialogue_items = [{
            "raw": "Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,{\\k100}Hello World",
            "metrics": {"rw": 100, "h": 20, "sel": True}
        }]
        
        lines = engine.process(dialogue_items, styles)
        self.assertEqual(len(lines), 1)
        self.assertEqual(len(engine.all_generated_lines), 1)
        self.assertEqual(engine.all_generated_lines[0]['queue_id'], "CustomQ")
        self.assertEqual(engine.all_generated_lines[0]['actor'], "CustomQ")
        self.assertEqual(engine.all_generated_lines[0]['queue_order'], 5)
        self.assertIn("CustomQ", lines[0])

    def test_definir_vars_char_expression_evaluation(self):
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "char"},
                    "outputs": [{"name": "Loop", "type": "bucle"}]
                },
                {
                    "id": 2,
                    "type": "Bucles/Definir Vars",
                    "properties": {"variables": "my_idx = char.i\nmy_tot = char.n"},
                    "inputs": [{"name": "In (bucle)", "link": 1}],
                    "outputs": [{"name": "Out", "type": "bucle"}]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "Sel. Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 2},
                        {"name": "Layer"}, {"name": "Start Time"}, {"name": "End Time"},
                        {"name": "Tags"}, {"name": "Return"}
                    ]
                }
            ],
            "links": [
                [1, 1, 0, 2, 0],
                [2, 2, 0, 3, 0]
            ]
        }
        engine = GraphEngine(graph_data)
        styles = {"Default": {}}
        dialogue_items = [{
            "raw": "Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,{\\k100}AB",
            "metrics": {"rw": 100, "h": 20, "sel": True}
        }]
        
        lines = engine.process(dialogue_items, styles)
        self.assertEqual(len(engine.all_generated_lines), 2)
        self.assertIn("A", engine.all_generated_lines[0]['text'])
        self.assertIn("B", engine.all_generated_lines[1]['text'])


if __name__ == "__main__":
    unittest.main()


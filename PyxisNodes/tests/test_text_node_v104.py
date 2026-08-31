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

# PyxisNodes/tests/test_text_node_v104.py
"""Pruebas unitarias completas para el Nodo Maestro Text v1.0.5."""

import unittest
from nodes.text_nodes import eval_text_node, text_to_shape_node
from node_engine import GraphEngine

class TestUnifiedTextNode(unittest.TestCase):
    def setUp(self):
        self.context = {
            'active_unit': type('Unit', (), {'text': r'{\pos(100,200)}Hola Mundo', 'text_stripped': 'Hola Mundo'})(),
            'active_line': type('Line', (), {'text': r'{\pos(100,200)}Hola Mundo', 'text_stripped': 'Hola Mundo'})()
        }

    # 1. Strip Tags
    def test_op_strip_tags(self):
        res = eval_text_node(self.context, operacion="Strip Tags", Texto=r"{\b1\pos(10,20)}Prueba\NText")
        self.assertEqual(res, "Prueba Text")

    # 2. Mayusculas
    def test_op_mayusculas(self):
        res = eval_text_node(self.context, operacion="Mayusculas", Texto="kara effector")
        self.assertEqual(res, "KARA EFFECTOR")

    # 3. Minusculas
    def test_op_minusculas(self):
        res = eval_text_node(self.context, operacion="Minusculas", Texto="PYXIS NODES")
        self.assertEqual(res, "pyxis nodes")

    # 4. Reemplazar
    def test_op_reemplazar(self):
        res = eval_text_node(self.context, operacion="Reemplazar", Texto="Hola Mundo", Buscar="Mundo", Reemplazar="Pyxis")
        self.assertEqual(res, "Hola Pyxis")

    # 5. Subcadena
    def test_op_subcadena(self):
        res = eval_text_node(self.context, operacion="Subcadena", Texto="Antigravity", Inicio=0, Longitud=4)
        self.assertEqual(res, "Anti")

    # 6. Longitud
    def test_op_longitud(self):
        res = eval_text_node(self.context, operacion="Longitud", Texto="PyxisNodes")
        self.assertEqual(res, "10")

    # 7. Contener
    def test_op_contener_true(self):
        res = eval_text_node(self.context, operacion="Contener", Texto="Efecto Visual", Buscar="Efecto")
        self.assertEqual(res, "1")

    def test_op_contener_false(self):
        res = eval_text_node(self.context, operacion="Contener", Texto="Efecto Visual", Buscar="Audio")
        self.assertEqual(res, "0")

    # 8. Kana (Transliteración)
    def test_op_kana_romaji_hiragana(self):
        res = eval_text_node(self.context, operacion="Kana", Texto="sakura", Modo="Romaji a Hiragana")
        self.assertEqual(res, "さくら")

    def test_op_kana_romaji_katakana(self):
        res = eval_text_node(self.context, operacion="Kana", Texto="sakura", Modo="Romaji a Katakana")
        self.assertEqual(res, "サクラ")

    # Integración con GraphEngine
    def test_graph_engine_text_node_evaluation(self):
        text_node = {
            "id": 1,
            "type": "Text",
            "properties": {"operacion": "Reemplazar"},
            "inputs": [
                {"name": "Text", "value": "Pyxis V1"},
                {"name": "Buscar", "value": "V1"},
                {"name": "Reemplazar Por", "value": "V2"}
            ]
        }
        graph_data = {"nodes": [text_node], "links": []}
        engine = GraphEngine(graph_data)
        res = engine.evaluate_data_node(1, {})
        self.assertEqual(res, "Pyxis V2")


if __name__ == "__main__":
    unittest.main()

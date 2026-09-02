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
import json
import unittest
import sys
import tempfile

sys.path.insert(0, r"f:\Kara Effector\Node\Antigravity-PyxisNode\Versión en desarrollo\PyxisNodes")

from main import PyxisAPI

class TestSessionPersistenceIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.session_file = os.path.join(self.tmp_dir.name, "session_test.json")
        self.api = PyxisAPI("dummy.ass", "result.ass", self.session_file)

    def tearDown(self):
        self.tmp_dir.cleanup()
        
    def test_text_node_session_persistence(self):
        # Realistic session graph with Texto, Número, Concatenar, Shape Slicer, Interpolador, Definir Vars
        sample_graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Text",
                    "title": "Text",
                    "properties": {"valor": "Kanji / Romanization Test Text"},
                    "widgets_values": ["Kanji / Romanization Test Text"]
                },
                {
                    "id": 2,
                    "type": "Number",
                    "title": "Number",
                    "properties": {"valor": "123.45"},
                    "widgets_values": ["123.45"]
                },
                {
                    "id": 3,
                    "type": "Concatenate",
                    "title": "Concatenate",
                    "properties": {"In1": "Hello", "In2": "World", "separador": "Space"},
                    "widgets_values": ["Hello", "World"]
                },
                {
                    "id": 4,
                    "type": "Define Vars",
                    "title": "Define Vars",
                    "properties": {"variables": "x = 10\ny = 20\nname = 'Pyxis'"}
                },
                {
                    "id": 5,
                    "type": "Shape/Corte/Shape Slicer",
                    "title": "Shape Slicer [hex]",
                    "properties": {"modo": "hex", "Radius": "15", "Overlap": "2"}
                }
            ],
            "links": []
        }
        
        # Save session
        serialized_str = json.dumps(sample_graph)
        res = self.api.save_session(serialized_str)
        self.assertTrue(res)
        
        # Retrieve session
        loaded_str = self.api.get_session_graph()
        self.assertTrue(bool(loaded_str))
        loaded_graph = json.loads(loaded_str)
        
        # Check all nodes retained their exact properties
        texto_node = next(n for n in loaded_graph["nodes"] if n["id"] == 1)
        self.assertEqual(texto_node["properties"]["valor"], "Kanji / Romanization Test Text")
        
        num_node = next(n for n in loaded_graph["nodes"] if n["id"] == 2)
        self.assertEqual(num_node["properties"]["valor"], "123.45")
        
        concat_node = next(n for n in loaded_graph["nodes"] if n["id"] == 3)
        self.assertEqual(concat_node["properties"]["In1"], "Hello")
        self.assertEqual(concat_node["properties"]["separador"], "Space")
        
        vars_node = next(n for n in loaded_graph["nodes"] if n["id"] == 4)
        self.assertEqual(vars_node["properties"]["variables"], "x = 10\ny = 20\nname = 'Pyxis'")

        slicer_node = next(n for n in loaded_graph["nodes"] if n["id"] == 5)
        self.assertEqual(slicer_node["properties"]["Radius"], "15")

if __name__ == "__main__":
    unittest.main()

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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from node_engine import GraphEngine
from nodes.code_nodes import execute_python_script, execute_lua_script, code_script_master

class TestStage3CodeNode(unittest.TestCase):
    def setUp(self):
        self.context = {
            "syl": type("Syl", (), {
                "i": 1,
                "n": 2,
                "text": "World",
                "text_stripped": "World",
                "duration": 500,
                "dur": 500,
                "start_time": 0,
                "end_time": 500,
                "x": 100.0,
                "y": 200.0,
                "center": 100.0,
                "middle": 200.0
            })(),
            "line": type("Line", (), {
                "layer": 0,
                "style_name": "Default",
                "text": "Hello World"
            })(),
            "rx": 1280,
            "ry": 720,
            "fd": 41.708
        }

    def test_python_script_execution_basic(self):
        script = "result = 'Hello ' + syl.text"
        res = execute_python_script(self.context, script, {})
        self.assertEqual(res, "Hello World")

    def test_python_print_and_single_expressions(self):
        # 1. Test print statement does not crash with NoneType subscriptable error
        res_print = execute_python_script(self.context, "print(syl.i)", {})
        self.assertEqual(res_print, "")

        # 2. Test direct expression without result = ...
        res_expr = execute_python_script(self.context, "syl.i * 10", {})
        self.assertEqual(res_expr, "10")

        # 3. Test built-in functions
        res_builtins = execute_python_script(self.context, "result = ','.join([str(x) for x in range(3)])", {})
        self.assertEqual(res_builtins, "0,1,2")

    def test_python_script_execution_with_inputs(self):
        script = "result = str(in1) + ' - ' + str(in2)"
        inputs = {"In1": "ALPHA", "In2": "BETA"}
        res = execute_python_script(self.context, script, inputs)
        self.assertEqual(res, "ALPHA - BETA")

    def test_python_script_with_memory(self):
        memory_store = {}
        def remember(key, val):
            memory_store[key] = val
            return val
        def recall(key, default=None):
            return memory_store.get(key, default)

        ctx = dict(self.context)
        ctx["remember"] = remember
        ctx["recall"] = recall

        script = """
counter = recall('ctr', 0) + 1
remember('ctr', counter)
result = 'Counter: ' + str(counter)
"""
        res1 = execute_python_script(ctx, script, {})
        self.assertEqual(res1, "Counter: 1")

        res2 = execute_python_script(ctx, script, {})
        self.assertEqual(res2, "Counter: 2")

    def test_lua_script_execution_basic(self):
        try:
            import lupa
        except ImportError:
            self.skipTest("lupa no está disponible")

        script = "result = 'Lua ' .. syl.text"
        res = execute_lua_script(self.context, script, {})
        self.assertEqual(res, "Lua World")

    def test_code_script_master_dispatch(self):
        script = "result = 'Dispatch ' + str(in1)"
        res_py = code_script_master(self.context, script=script, lenguaje="Python", In1="Test")
        self.assertEqual(res_py, "Dispatch Test")

    def test_graph_engine_integration_with_code_node(self):
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
                    "type": "System/Script Code",
                    "properties": {
                        "lenguaje": "Python",
                        "script": "result = '\\\\pos(500,600)' if syl.i == 1 else '\\\\pos(700,800)'"
                    },
                    "inputs": [
                        {"name": "Flow In", "type": "bucle", "link": 101},
                        {"name": "In1", "type": "data", "link": None}
                    ],
                    "outputs": [
                        {"name": "Flow Out", "type": "bucle", "links": None},
                        {"name": "Result", "type": "data", "links": [102]}
                    ]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 101},
                        {"name": "Layer", "type": "data", "link": None},
                        {"name": "Start Time", "type": "data", "link": None},
                        {"name": "End Time", "type": "data", "link": None},
                        {"name": "Tags", "type": "data", "link": 102},
                        {"name": "Return", "type": "data", "link": None},
                        {"name": "Queue ID", "type": "data", "link": None},
                        {"name": "Queue Order", "type": "data", "link": None}
                    ],
                    "outputs": []
                }
            ],
            "links": [
                [101, 1, 0, 3, 0, "bucle"],
                [102, 2, 1, 3, 4, "data"]
            ]
        }

        styles = {"Default": {}}
        dialogues = [{
            'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k50}Test{\\k50}Line",
            'metrics': {'h': 20.0, 'd': 5.0, 'e': 0.0, 'sel': True, 'w': [40.0, 40.0]}
        }]

        engine = GraphEngine(graph_data, 1280, 720, 41.708)
        lines = engine.process(dialogues, styles)
        self.assertTrue(len(lines) > 0)
        self.assertTrue(any("\\pos(500,600)" in l for l in lines))

    def test_code_node_loop_flow_chaining(self):
        # Chain: Main Loop -> Código Script (Flujo In -> Flujo Out) -> Salida (Bucle / Dominio)
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl"},
                    "outputs": [{"name": "Loop", "type": "bucle", "links": [201]}]
                },
                {
                    "id": 2,
                    "type": "System/Script Code",
                    "properties": {
                        "lenguaje": "Python",
                        "script": "remember('loop_visited', recall('loop_visited', 0) + 1)\nresult = '\\\\an5'"
                    },
                    "inputs": [
                        {"name": "Flow In", "type": "bucle", "link": 201},
                        {"name": "In1", "type": "data", "link": None}
                    ],
                    "outputs": [
                        {"name": "Flow Out", "type": "bucle", "links": [202]},
                        {"name": "Result", "type": "data", "links": [203]}
                    ]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 202},
                        {"name": "Layer", "type": "data", "link": None},
                        {"name": "Start Time", "type": "data", "link": None},
                        {"name": "End Time", "type": "data", "link": None},
                        {"name": "Tags", "type": "data", "link": 203},
                        {"name": "Return", "type": "data", "link": None},
                        {"name": "Queue ID", "type": "data", "link": None},
                        {"name": "Queue Order", "type": "data", "link": None}
                    ],
                    "outputs": []
                }
            ],
            "links": [
                [201, 1, 0, 2, 0, "bucle"],
                [202, 2, 0, 3, 0, "bucle"],
                [203, 2, 1, 3, 4, "data"]
            ]
        }

        styles = {"Default": {}}
        dialogues = [{
            'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k50}Test{\\k50}Line",
            'metrics': {'h': 20.0, 'd': 5.0, 'e': 0.0, 'sel': True, 'w': [40.0, 40.0]}
        }]

        engine = GraphEngine(graph_data, 1280, 720, 41.708)
        lines = engine.process(dialogues, styles)
        self.assertEqual(len(lines), 2)
        self.assertTrue(all("\\an5" in l for l in lines))

    def test_syl_i_indexing_with_lead_in(self):
        # Karaoke line with lead in metrics:
        # syl 0 (empty lead in): ""
        # syl 1: "Ma" -> i=1
        # syl 2: "ry" -> i=2
        from ass_parser import KaraokeProcessor
        processor = KaraokeProcessor(1280, 720, 41.708)
        raw_dialogue = {
            'raw': "Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{\\k44}Ma{\\k65}ry",
            'metrics': {
                'rw': 100.0, 'h': 35.0, 'd': 0.0, 'e': 0.0, 'sel': True,
                'w': [20.0, 20.0, 20.0, 20.0],
                'syl_lefts': [0.0, 0.0, 40.0],
                'syl_centers': [0.0, 20.0, 60.0],
                'syl_rights': [0.0, 40.0, 80.0],
                'syl_widths': [0.0, 40.0, 40.0],
                'syl_starts': [0, 0, 440],
                'syl_ends': [0, 440, 1090]
            }
        }
        line = processor.process_line(raw_dialogue['raw'], {}, raw_dialogue['metrics'])
        visible_syls = [s for s in line.syls if s.text_stripped.strip()]
        self.assertEqual(len(visible_syls), 2)
        self.assertEqual(visible_syls[0].i, 1)
        self.assertEqual(visible_syls[1].i, 2)
        self.assertEqual(visible_syls[0].n, 2)

    def test_word_i_accessible_from_syl_loop(self):
        # Test full graph execution iterating on syl with script accessing word.i
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl"},
                    "outputs": [{"name": "Loop", "type": "bucle", "links": [301]}]
                },
                {
                    "id": 2,
                    "type": "System/Script Code",
                    "properties": {
                        "lenguaje": "Python",
                        "script": "result = f'{syl.text_stripped.strip()}:syl{syl.i}_word{word.i}'"
                    },
                    "inputs": [
                        {"name": "Flow In", "type": "bucle", "link": None},
                        {"name": "In1", "type": "data", "link": None}
                    ],
                    "outputs": [
                        {"name": "Flow Out", "type": "bucle", "links": None},
                        {"name": "Result", "type": "data", "links": [302]}
                    ]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 301},
                        {"name": "Layer", "type": "data", "link": None},
                        {"name": "Start Time", "type": "data", "link": None},
                        {"name": "End Time", "type": "data", "link": None},
                        {"name": "Tags", "type": "data", "link": None},
                        {"name": "Return", "type": "data", "link": 302},
                        {"name": "Queue ID", "type": "data", "link": None},
                        {"name": "Queue Order", "type": "data", "link": None}
                    ],
                    "outputs": []
                }
            ],
            "links": [
                [301, 1, 0, 3, 0, "bucle"],
                [302, 2, 1, 3, 5, "data"]
            ]
        }

        styles = {"Default": {}}
        dialogues = [{
            'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k50}Ma{\\k50}ry {\\k50}te{\\k50}nia",
            'metrics': {
                'rw': 200.0, 'h': 35.0, 'd': 0.0, 'e': 0.0, 'sel': True,
                'w': [20.0]*10
            }
        }]

        engine = GraphEngine(graph_data, 1280, 720, 41.708)
        lines = engine.process(dialogues, styles)
        self.assertEqual(len(lines), 4)
        # Line 0 ("Ma"): word 1
        self.assertTrue("Ma:syl1_word1" in lines[0])
        # Line 1 ("ry"): word 1
        self.assertTrue("ry:syl2_word1" in lines[1])
        # Line 2 ("te"): word 2
        self.assertTrue("te:syl3_word2" in lines[2])
        # Line 3 ("nia"): word 2
        self.assertTrue("nia:syl4_word2" in lines[3])

    def test_syl_with_space_inherits_first_word(self):
        # A syllable with space in the middle ('a la') belongs to 2 words ('a' and 'la')
        # It must inherit the identity of the FIRST word ('a', word.i = 1)
        from ass_parser import KaraokeProcessor
        processor = KaraokeProcessor(1280, 720, 41.708)
        raw_dialogue = {
            'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}a la {\\k50}playa",
            'metrics': {'rw': 200.0, 'h': 35.0, 'd': 0.0, 'e': 0.0, 'sel': True, 'w': [20.0]*12}
        }
        line = processor.process_line(raw_dialogue['raw'], {}, raw_dialogue['metrics'])
        self.assertEqual(len(line.words), 3)
        self.assertEqual(line.words[0].text, "a")
        self.assertEqual(line.words[1].text, "la")
        self.assertEqual(line.words[2].text, "playa")

        # Syllable 1 ('a la ') inherits word 1 ('a')
        syl1 = [s for s in line.syls if s.text_stripped][0]
        syl2 = [s for s in line.syls if s.text_stripped][1]
        self.assertEqual(syl1.word.i, 1)
        self.assertEqual(syl1.word.text, "a")

        # Syllable 2 ('playa') inherits word 3 ('playa')
        self.assertEqual(syl2.word.i, 3)
        self.assertEqual(syl2.word.text, "playa")

    def test_word_accessible_in_char_loop(self):
        # Test Main Loop iterating on 'char' with script using word.i
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "char"},
                    "outputs": [{"name": "Loop", "type": "bucle", "links": [401]}]
                },
                {
                    "id": 2,
                    "type": "System/Script Code",
                    "properties": {
                        "lenguaje": "Python",
                        "script": "result = f'{char.text}:w{word.i}'"
                    },
                    "inputs": [
                        {"name": "Flow In", "type": "bucle", "link": None},
                        {"name": "In1", "type": "data", "link": None}
                    ],
                    "outputs": [
                        {"name": "Flow Out", "type": "bucle", "links": None},
                        {"name": "Result", "type": "data", "links": [402]}
                    ]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 401},
                        {"name": "Layer", "type": "data", "link": None},
                        {"name": "Start Time", "type": "data", "link": None},
                        {"name": "End Time", "type": "data", "link": None},
                        {"name": "Tags", "type": "data", "link": None},
                        {"name": "Return", "type": "data", "link": 402},
                        {"name": "Queue ID", "type": "data", "link": None},
                        {"name": "Queue Order", "type": "data", "link": None}
                    ],
                    "outputs": []
                }
            ],
            "links": [
                [401, 1, 0, 3, 0, "bucle"],
                [402, 2, 1, 3, 5, "data"]
            ]
        }

        styles = {"Default": {}}
        dialogues = [{
            'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k50}Go {\\k50}Up",
            'metrics': {'rw': 100.0, 'h': 35.0, 'd': 0.0, 'e': 0.0, 'sel': True, 'w': [20.0]*5}
        }]

        engine = GraphEngine(graph_data, 1280, 720, 41.708)
        lines = engine.process(dialogues, styles)
        self.assertEqual(len(lines), 4) # 'G', 'o', 'U', 'p'
        self.assertTrue("G:w1" in lines[0])
        self.assertTrue("o:w1" in lines[1])
        self.assertTrue("U:w2" in lines[2])
        self.assertTrue("p:w2" in lines[3])

    def test_pyxis_api_code_templates_persistence(self):
        from main import PyxisAPI
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        try:
            api = PyxisAPI("dummy_temp.ass", "dummy_res.ass", "dummy_session.json")
            # Override template path to test directory
            api._get_code_templates_path = lambda: os.path.join(temp_dir, "test_templates.json")

            initial = api.get_code_templates()
            self.assertEqual(initial, {})

            sample_templates = {
                "user_tpl_1": {
                    "name": "Custom Sine Wave",
                    "lang": "Python",
                    "code": "result = '\\\\pos(100,200)'"
                }
            }
            saved = api.save_code_templates(sample_templates)
            self.assertTrue(saved)

            loaded = api.get_code_templates()
            self.assertEqual(loaded.get("user_tpl_1", {}).get("name"), "Custom Sine Wave")
            self.assertEqual(loaded.get("user_tpl_1", {}).get("lang"), "Python")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_salida_queue_id_and_order(self):
        # Test Salida nodes using inputs for queue_id and queue_order
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "line"},
                    "outputs": [{"name": "Loop", "type": "bucle", "links": [501]}]
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {
                        "apply_to": "All Lines"
                    },
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 501},
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
                [501, 1, 0, 2, 0, "bucle"]
            ]
        }

        styles = {"Default": {}}
        dialogues = [{
            'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k50}Test",
            'metrics': {'rw': 100.0, 'h': 35.0, 'd': 0.0, 'e': 0.0, 'sel': True, 'w': [20.0]*4}
        }]

        engine = GraphEngine(graph_data, 1280, 720, 41.708)
        lines = engine.process(dialogues, styles)
        self.assertEqual(len(lines), 1)
        self.assertIn("Test", lines[0])


if __name__ == "__main__":
    unittest.main()


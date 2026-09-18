import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from nodes.tag_nodes import node_animation
from models import StyleRef, PyxisLine, PyxisUnit


class TestAnimationNode(unittest.TestCase):

    def setUp(self):
        style_dict = {
            'fontname': 'Arial',
            'fontsize': 45.0,
            'color1': '&H00FFFFFF&',
            'color2': '&H000000FF&',
            'color3': '&H00000000&',
            'color4': '&H00000000&',
            'alpha1': '&H00&',
            'alpha2': '&H00&',
            'alpha3': '&H80&',
            'alpha4': '&HFF&',
            'scale_x': 100.0,
            'scale_y': 100.0,
            'spacing': 0.0,
            'outline': 3.0,
            'shadow': 1.5,
            'angle': 0.0
        }
        self.style = StyleRef(style_dict)
        self.line = PyxisLine()
        self.line.styleref = self.style
        self.line.duration = 1000.0
        self.line.start_time = 0.0
        self.line.end_time = 1000.0

        self.unit = PyxisUnit()
        self.unit.styleref = self.style
        self.unit.start_time = 0.0
        self.unit.end_time = 1000.0
        self.unit.duration = 1000.0

        self.context = {
            'active_line': self.line,
            'active_unit': self.unit,
            'styleref': self.style,
            'duration': 1000.0,
            'fx_dur': 1000.0,
            'start_time': 0.0,
            'end_time': 1000.0,
            'an_i': 1
        }

    def test_fbf_mode_shape_list(self):
        shapes = ["m 0 0 l 10 0 l 10 10 l 0 10", "m 0 0 l 20 0 l 20 20 l 0 20", "m 0 0 l 30 0 l 30 30 l 0 30"]
        self.context['an_i'] = 1
        res1 = node_animation(self.context, frames=shapes, mode="FBF", output_slot_index=0)
        self.assertEqual(res1, f"{{\\an7}}{shapes[0]}")

        self.context['an_i'] = 2
        res2 = node_animation(self.context, frames=shapes, mode="FBF", output_slot_index=0)
        self.assertEqual(res2, f"{{\\an7}}{shapes[1]}")

        # Test frame number slot
        frame_num = node_animation(self.context, frames=shapes, mode="FBF", output_slot_index=1)
        self.assertEqual(frame_num, 2)

        # Test frames list slot
        frames_list = node_animation(self.context, frames=shapes, mode="FBF", output_slot_index=2)
        self.assertEqual(len(frames_list), 3)

    def test_animation_canonical_lowercase(self):
        shapes = ["m 0 0 l 10 0", "m 0 0 l 20 0", "m 0 0 l 30 0"]
        self.context['an_i'] = 1
        res1 = node_animation(self.context, frames=shapes, mode="fbf", output_slot_index=0)
        self.assertEqual(res1, f"{{\\an7}}{shapes[0]}")

        # Alpha mode with lowercase "alpha"
        res_alpha = node_animation(
            self.context,
            frames=shapes,
            mode="alpha",
            step_ms=100.0,
            start_time=0.0,
            end_time=300.0,
            output_slot_index=0
        )
        self.assertIn(r"\alpha", res_alpha)

    def test_fbf_mode_lua_table_syntax(self):
        lua_input = '{"m 0 0 l 10 0", "m 0 0 l 20 0"}'
        self.context['an_i'] = 2
        res = node_animation(self.context, frames=lua_input, mode="FBF", output_slot_index=0)
        self.assertEqual(res, r"{\an7}m 0 0 l 20 0")

    def test_text_to_shape_conversion(self):
        text_input = '["A", "B"]'
        self.context['an_i'] = 1
        res = node_animation(self.context, frames=text_input, mode="FBF", output_slot_index=0)
        self.assertTrue(r"{\an7}" in res)
        self.assertTrue("m " in res or "m-" in res or "m0" in res)

    def test_alpha_mode_generation(self):
        shapes = ["m 0 0 l 10 0", "m 0 0 l 20 0"]
        self.context['an_i'] = 1
        # Slot 0: Shape with tags
        res_shape_tags = node_animation(
            self.context,
            frames=shapes,
            mode="Alpha",
            step_ms=100.0,
            start_time=0.0,
            end_time=400.0,
            alpha_tag=r"\alpha",
            output_slot_index=0
        )
        self.assertIn(r"\an7", res_shape_tags)
        self.assertIn(r"\alpha&HFF&", res_shape_tags)
        self.assertIn(r"\t(0,1,\alpha&H00&)", res_shape_tags)
        self.assertIn(r"\p1", res_shape_tags)
        self.assertIn("m 0 0 l 10 0", res_shape_tags)

        # Slot 1: Tags alone
        res_tags = node_animation(
            self.context,
            frames=shapes,
            mode="Alpha",
            step_ms=100.0,
            start_time=0.0,
            end_time=400.0,
            alpha_tag=r"\1a",
            output_slot_index=1
        )
        self.assertTrue(res_tags.startswith(r"\an7"))
        self.assertIn(r"\1a&HFF&", res_tags)
        self.assertIn(r"\t(0,1,\1a&H00&)", res_tags)
        self.assertNotIn(r"\p1", res_tags)

    def test_custom_var_name_iterators(self):
        shapes = ["m 0 0 l 10 0", "m 0 0 l 20 0", "m 0 0 l 30 0"]
        ctx = {'myiter_i': 3}
        node_animation(ctx, frames=shapes, mode="FBF", var_name="myiter", output_slot_index=0)
        self.assertEqual(ctx.get('myiter_n'), 3)
        self.assertEqual(ctx.get('myiter_i'), 3)
        self.assertEqual(ctx.get('maxloop'), 3)

    def test_context_variable_name_resolution(self):
        shapes = ["m 0 0 l 10 0", "m 0 0 l 20 0", "m 0 0 l 30 0"]
        self.context['Shapes1'] = shapes
        self.context['an_i'] = 2
        res = node_animation(self.context, frames="Shapes1", mode="FBF", output_slot_index=0)
        self.assertEqual(res, f"{{\\an7}}{shapes[1]}")

    def test_lua_table_object_resolution(self):
        class MockLuaTable:
            def __init__(self, items):
                self._items = items
            def values(self):
                return self._items

        mock_tbl = MockLuaTable(["m 0 0 l 10 0", "m 0 0 l 20 0"])
        self.context['ShapesLua'] = mock_tbl
        self.context['an_i'] = 1
        res = node_animation(self.context, frames="ShapesLua", mode="FBF", output_slot_index=0)
        self.assertEqual(res, r"{\an7}m 0 0 l 10 0")

    def test_graphengine_fbf_simulation(self):
        from node_engine import GraphEngine
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterator": "line", "blank_mode": "No Blank"}
                },
                {
                    "id": 2,
                    "type": "Functions/Animation",
                    "properties": {
                        "mode": "FBF",
                        "frames": '["m 0 0 l 10 0 10 10 0 10", "m 0 0 l 20 0 20 20 0 20", "m 0 0 l 30 0 30 30 0 30"]',
                        "step_ms": "50",
                        "var_name": "an"
                    }
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "inputs": [
                        {"name": "Loop / Domain", "link": 1},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": 2}
                    ],
                    "properties": {"apply_to": "Sel. Lines", "origin_align": 5}
                }
            ],
            "links": [
                [1, 1, 0, 3, 0, "loop"],
                [2, 2, 0, 3, 5, "data"]
            ]
        }

        dialogues = [{
            'raw': 'Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{\\k50}Test Line',
            'start_time': 0.0,
            'end_time': 5000.0,
            'duration': 5000.0,
            'text': 'Test Line',
            'raw_text': '{\\k50}Test Line',
            'style_name': 'Default',
            'is_selected': True
        }]
        styles = {'Default': {
            'fontname': 'Arial', 'fontsize': 45.0, 'color1': '&H00FFFFFF&',
            'color2': '&H000000FF&', 'color3': '&H00000000&', 'color4': '&H00000000&',
            'alpha1': '&H00&', 'alpha2': '&H00&', 'alpha3': '&H80&', 'alpha4': '&HFF&',
            'scale_x': 100.0, 'scale_y': 100.0, 'spacing': 0.0, 'outline': 3.0,
            'shadow': 1.5, 'angle': 0.0
        }}

        engine = GraphEngine(graph_data)
        lines = engine.process_single(dialogues, styles)

        self.assertEqual(len(lines), 100, "Should generate 100 frame lines across 5000ms duration (50ms step)")
        # First cycle
        self.assertIn("m 0 0 l 10 0 10 10 0 10", lines[0]['text'])
        self.assertIn("m 0 0 l 20 0 20 20 0 20", lines[1]['text'])
        self.assertIn("m 0 0 l 30 0 30 30 0 30", lines[2]['text'])
        # Second cycle (repeats like a GIF)
        self.assertIn("m 0 0 l 10 0 10 10 0 10", lines[3]['text'])
        self.assertIn("m 0 0 l 20 0 20 20 0 20", lines[4]['text'])
        self.assertIn("m 0 0 l 30 0 30 30 0 30", lines[5]['text'])
        # Timing check
        self.assertEqual(lines[0]['start_time'], 0.0)
        self.assertEqual(lines[0]['end_time'], 50.0)
        self.assertEqual(lines[1]['start_time'], 50.0)
        self.assertEqual(lines[1]['end_time'], 100.0)
        self.assertEqual(lines[2]['start_time'], 100.0)
        self.assertEqual(lines[2]['end_time'], 150.0)
        self.assertEqual(lines[3]['start_time'], 150.0)
        self.assertEqual(lines[3]['end_time'], 200.0)
        self.assertEqual(lines[99]['start_time'], 4950.0)
        self.assertEqual(lines[99]['end_time'], 5000.0)

    def test_exact_saved_template_with_lua_script(self):
        import json
        template_path = os.path.expandvars(r"%APPDATA%\PyxisNodes\templates\20260915_122253_Prueba_de_animation_8b62445b.json")
        if not os.path.exists(template_path):
            self.skipTest("Template not found on this machine")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)

        from node_engine import GraphEngine
        engine = GraphEngine(template_data.get('graph', {}))
        dialogues = [{
            'raw': 'Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{\\k50}Prueba Animation',
            'start_time': 0.0,
            'end_time': 5000.0,
            'duration': 5000.0,
            'text': 'Prueba Animation',
            'raw_text': '{\\k50}Prueba Animation',
            'style_name': 'Default',
            'is_selected': True
        }]
        styles = {'Default': {
            'fontname': 'Arial', 'fontsize': 45.0, 'color1': '&H00FFFFFF&',
            'color2': '&H000000FF&', 'color3': '&H00000000&', 'color4': '&H00000000&',
            'alpha1': '&H00&', 'alpha2': '&H00&', 'alpha3': '&H80&', 'alpha4': '&HFF&',
            'scale_x': 100.0, 'scale_y': 100.0, 'spacing': 0.0, 'outline': 3.0,
            'shadow': 1.5, 'angle': 0.0
        }}

        lines = engine.process_single(dialogues, styles)
        self.assertGreater(len(lines), 1, "Should generate multiple animation frames")
        first_line = lines[0]
        self.assertNotIn("Shapes1", first_line['text'], "Text must not contain literal variable name 'Shapes1'")
        self.assertTrue("m " in first_line['text'] or "\\p1" in first_line['text'], "Generated line must contain shape drawing")
        self.assertEqual(lines[0]['start_time'], 0.0)
        self.assertEqual(lines[0]['end_time'], 100.0)
        self.assertEqual(lines[1]['start_time'], 100.0)
        self.assertEqual(lines[1]['end_time'], 200.0)

    def test_graphengine_fbf_with_variable_names_list(self):
        from node_engine import GraphEngine
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterator": "line", "blank_mode": "No Blank"}
                },
                {
                    "id": 6,
                    "type": "System/Script Code",
                    "properties": {
                        "language": "Lua",
                        "script": 'F1 = "m 0 0 l 10 10"; F2 = "m 0 0 l 20 20"; F3 = "m 0 0 l 30 30"'
                    }
                },
                {
                    "id": 2,
                    "type": "Functions/Animation",
                    "properties": {
                        "mode": "FBF",
                        "frames": "F1, F2, F3",
                        "step_ms": "80",
                        "var_name": "an"
                    }
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "inputs": [
                        {"name": "Loop / Domain", "link": 2},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": 3}
                    ],
                    "properties": {"apply_to": "Sel. Lines", "origin_align": 5}
                }
            ],
            "links": [
                [1, 1, 0, 6, 0, "loop"],
                [2, 6, 0, 3, 0, "loop"],
                [3, 2, 0, 3, 5, "data"]
            ]
        }

        dialogues = [{
            'raw': 'Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{\\k100}Anim',
            'start_time': 0.0,
            'end_time': 1000.0,
            'duration': 1000.0,
            'text': 'Anim',
            'raw_text': '{\\k100}Anim',
            'style_name': 'Default',
            'is_selected': True
        }]
        styles = {'Default': {
            'fontname': 'Arial', 'fontsize': 45.0, 'color1': '&H00FFFFFF&',
            'color2': '&H000000FF&', 'color3': '&H00000000&', 'color4': '&H00000000&',
            'alpha1': '&H00&', 'alpha2': '&H00&', 'alpha3': '&H80&', 'alpha4': '&HFF&',
            'scale_x': 100.0, 'scale_y': 100.0, 'spacing': 0.0, 'outline': 3.0,
            'shadow': 1.5, 'angle': 0.0
        }}

        engine = GraphEngine(graph_data)
        lines = engine.process_single(dialogues, styles)

        self.assertEqual(len(lines), 13, "Should generate 13 frames (math.ceil(1000/80)) from list of variable names")
        # Repeating pattern F1, F2, F3, F1...
        self.assertIn("m 0 0 l 10 10", lines[0]['text'])
        self.assertIn("m 0 0 l 20 20", lines[1]['text'])
        self.assertIn("m 0 0 l 30 30", lines[2]['text'])
        self.assertIn("m 0 0 l 10 10", lines[3]['text'])
        self.assertIn("m 0 0 l 20 20", lines[4]['text'])
        self.assertIn("m 0 0 l 30 30", lines[5]['text'])
        self.assertEqual(lines[0]['start_time'], 0.0)
        self.assertEqual(lines[0]['end_time'], 80.0)
        self.assertEqual(lines[1]['start_time'], 80.0)
        self.assertEqual(lines[1]['end_time'], 160.0)
        self.assertEqual(lines[2]['start_time'], 160.0)
        self.assertEqual(lines[2]['end_time'], 240.0)
        self.assertEqual(lines[3]['start_time'], 240.0)
        self.assertEqual(lines[3]['end_time'], 320.0)

    def test_gif_continuous_looping_and_local_timing(self):
        from node_engine import GraphEngine
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterator": "line", "blank_mode": "No Blank"}
                },
                {
                    "id": 2,
                    "type": "Functions/Animation",
                    "properties": {
                        "mode": "FBF",
                        "frames": '["m 0 0 l 10 10", "m 0 0 l 20 20", "m 0 0 l 30 30", "m 0 0 l 40 40"]',
                        "step_ms": "100",
                        "start_time": "0",
                        "end_time": "fx.dur",
                        "var_name": "an"
                    }
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "inputs": [
                        {"name": "Loop / Domain", "link": 1},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": 2}
                    ],
                    "properties": {"apply_to": "Sel. Lines", "origin_align": 5}
                }
            ],
            "links": [
                [1, 1, 0, 3, 0, "loop"],
                [2, 2, 0, 3, 5, "data"]
            ]
        }

        dialogues = [{
            'raw': 'Dialogue: 0,0:00:02.00,0:00:03.20,Default,,0,0,0,,{\\k120}GIF Test',
            'start_time': 2000.0,
            'end_time': 3200.0,
            'duration': 1200.0,
            'text': 'GIF Test',
            'raw_text': '{\\k120}GIF Test',
            'style_name': 'Default',
            'is_selected': True
        }]
        styles = {'Default': {
            'fontname': 'Arial', 'fontsize': 45.0, 'color1': '&H00FFFFFF&',
            'color2': '&H000000FF&', 'color3': '&H00000000&', 'color4': '&H00000000&',
            'alpha1': '&H00&', 'alpha2': '&H00&', 'alpha3': '&H80&', 'alpha4': '&HFF&',
            'scale_x': 100.0, 'scale_y': 100.0, 'spacing': 0.0, 'outline': 3.0,
            'shadow': 1.5, 'angle': 0.0
        }}

        engine = GraphEngine(graph_data)
        lines = engine.process_single(dialogues, styles)

        # 1200ms duration / 100ms step = 12 total frames (3 full cycles of 4 frames)
        self.assertEqual(len(lines), 12)
        expected_shapes = ["m 0 0 l 10 10", "m 0 0 l 20 20", "m 0 0 l 30 30", "m 0 0 l 40 40"]
        for idx, line_item in enumerate(lines):
            exp_shape = expected_shapes[idx % 4]
            self.assertIn(exp_shape, line_item['text'], f"Frame {idx} should match GIF cycle shape {idx % 4}")
            exp_st = 2000.0 + idx * 100.0
            exp_et = exp_st + 100.0
            self.assertEqual(line_item['start_time'], exp_st, f"Frame {idx} start_time mismatch")
            self.assertEqual(line_item['end_time'], exp_et, f"Frame {idx} end_time mismatch")

    def test_graphengine_alpha_mode_simulation(self):
        from node_engine import GraphEngine
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterator": "line", "blank_mode": "No Blank"}
                },
                {
                    "id": 2,
                    "type": "Functions/Animation",
                    "properties": {
                        "mode": "Alpha",
                        "frames": '["m 0 0 l 10 0", "m 0 0 l 20 0"]',
                        "step_ms": "100",
                        "alpha_tag": "\\alpha",
                        "var_name": "an"
                    }
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "inputs": [
                        {"name": "Loop / Domain", "link": 1},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": 2}
                    ],
                    "properties": {"apply_to": "Sel. Lines", "origin_align": 5}
                }
            ],
            "links": [
                [1, 1, 0, 3, 0, "loop"],
                [2, 2, 0, 3, 5, "data"]
            ]
        }

        dialogues = [{
            'raw': 'Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{\\k100}Anim',
            'start_time': 0.0,
            'end_time': 1000.0,
            'duration': 1000.0,
            'text': 'Anim',
            'raw_text': '{\\k100}Anim',
            'style_name': 'Default',
            'is_selected': True
        }]
        styles = {'Default': {
            'fontname': 'Arial', 'fontsize': 45.0, 'color1': '&H00FFFFFF&',
            'color2': '&H000000FF&', 'color3': '&H00000000&', 'color4': '&H00000000&',
            'alpha1': '&H00&', 'alpha2': '&H00&', 'alpha3': '&H80&', 'alpha4': '&HFF&',
            'scale_x': 100.0, 'scale_y': 100.0, 'spacing': 0.0, 'outline': 3.0,
            'shadow': 1.5, 'angle': 0.0
        }}

        engine = GraphEngine(graph_data)
        lines = engine.process_single(dialogues, styles)

        self.assertEqual(len(lines), 2, "Alpha mode generates 1 line per frame covering full line duration with synchronized alpha")
        self.assertEqual(lines[0]['start_time'], 0.0)
        self.assertEqual(lines[0]['end_time'], 1000.0)
        self.assertEqual(lines[1]['start_time'], 0.0)
        self.assertEqual(lines[1]['end_time'], 1000.0)
        self.assertIn(r"\alpha&HFF&", lines[0]['text'])
        self.assertIn(r"\t(", lines[0]['text'])
        self.assertIn(r"\p1", lines[0]['text'])
    def test_animation_respects_salida_custom_timing_relative_to_effect(self):
        from node_engine import GraphEngine
        # In this graph, Salida receives custom Start Time (1000) and End Time (3000)
        # Original line is 0..5000 (duration 5000).
        # Animation has 2 frames with step_ms = 500, local start = 0, local end = fx.dur.
        # It must generate frames relative to effect (1000..3000):
        # Frame 1: 1000..1500 (shape 1)
        # Frame 2: 1500..2000 (shape 2)
        # Frame 3: 2000..2500 (shape 1, loop!)
        # Frame 4: 2500..3000 (shape 2, loop!)
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterator": "line", "blank_mode": "No Blank"}
                },
                {
                    "id": 2,
                    "type": "Functions/Animation",
                    "properties": {
                        "mode": "FBF",
                        "frames": '["m 0 0 l 10 10", "m 0 0 l 20 20"]',
                        "step_ms": "500",
                        "start_time": "0",
                        "end_time": "fx.dur",
                        "var_name": "an"
                    }
                },
                {
                    "id": 10,
                    "type": "Math/Math",
                    "properties": {"a": "1000", "b": "0", "op": "Add"}
                },
                {
                    "id": 11,
                    "type": "Math/Math",
                    "properties": {"a": "3000", "b": "0", "op": "Add"}
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "inputs": [
                        {"name": "Loop / Domain", "link": 1},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": 10},
                        {"name": "End Time", "link": 11},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": 2}
                    ],
                    "properties": {"apply_to": "Sel. Lines", "origin_align": 5}
                }
            ],
            "links": [
                [1, 1, 0, 3, 0, "loop"],
                [10, 10, 0, 3, 2, "data"],
                [11, 11, 0, 3, 3, "data"],
                [2, 2, 0, 3, 5, "data"]
            ]
        }

        dialogues = [{
            'raw': 'Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{\\k500}Test Salida Timing',
            'start_time': 0.0,
            'end_time': 5000.0,
            'duration': 5000.0,
            'text': 'Test Salida Timing',
            'raw_text': '{\\k500}Test Salida Timing',
            'style_name': 'Default',
            'is_selected': True
        }]
        styles = {'Default': {
            'fontname': 'Arial', 'fontsize': 45.0, 'color1': '&H00FFFFFF&',
            'color2': '&H000000FF&', 'color3': '&H00000000&', 'color4': '&H00000000&',
            'alpha1': '&H00&', 'alpha2': '&H00&', 'alpha3': '&H80&', 'alpha4': '&HFF&',
            'scale_x': 100.0, 'scale_y': 100.0, 'spacing': 0.0, 'outline': 3.0,
            'shadow': 1.5, 'angle': 0.0
        }}

        engine = GraphEngine(graph_data)
        lines = engine.process_single(dialogues, styles)

        self.assertEqual(len(lines), 4, "Should generate 4 frames across 1000..3000ms effect duration")
        self.assertEqual(lines[0]['start_time'], 1000.0)
        self.assertEqual(lines[0]['end_time'], 1500.0)
        self.assertIn("m 0 0 l 10 10", lines[0]['text'])

        self.assertEqual(lines[1]['start_time'], 1500.0)
        self.assertEqual(lines[1]['end_time'], 2000.0)
        self.assertIn("m 0 0 l 20 20", lines[1]['text'])

        self.assertEqual(lines[2]['start_time'], 2000.0)
        self.assertEqual(lines[2]['end_time'], 2500.0)
        self.assertIn("m 0 0 l 10 10", lines[2]['text'])

        self.assertEqual(lines[3]['start_time'], 2500.0)
        self.assertEqual(lines[3]['end_time'], 3000.0)
        self.assertIn("m 0 0 l 20 20", lines[3]['text'])


if __name__ == '__main__':
    unittest.main()


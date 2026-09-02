import unittest
import json
from node_engine import GraphEngine

class TestMaxLoopModuleMorph(unittest.TestCase):
    def test_maxloop_module_distortion(self):
        graph = {
            "last_node_id": 9,
            "last_link_id": 10,
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "line", "noblank": "No Blank (Ignorar Espacios)"},
                    "outputs": [{"name": "Loop", "type": "bucle", "links": [1], "slot_index": 0}]
                },
                {
                    "id": 2,
                    "type": "Loops/MaxLoop",
                    "properties": {"modo": "FBF", "start_time": "1000", "end_time": "1200", "step_ms": "50", "var_name": "j"},
                    "inputs": [{"name": "Loop In", "type": "bucle", "link": 1}],
                    "outputs": [
                        {"name": "Loop Out", "type": "bucle", "links": [2], "slot_index": 0},
                        {"name": "Iterator (j)", "type": "data", "links": [3], "slot_index": 1},
                        {"name": "Total (N)", "type": "data", "links": [4], "slot_index": 2}
                    ]
                },
                {
                    "id": 3,
                    "type": "Loops/Module",
                    "properties": {"iter": "i", "total": "N", "sub_m": "0"},
                    "inputs": [
                        {"name": "Iterator (i)", "type": "data", "link": 3},
                        {"name": "Total (N)", "type": "data", "link": 4},
                        {"name": "Sub-step (m)", "type": "data", "link": None}
                    ],
                    "outputs": [{"name": "Data", "type": "data", "links": [5], "slot_index": 0}]
                },
                {
                    "id": 4,
                    "type": "Functions/Text to Shape",
                    "properties": {"text": "A", "font_name": "Arial", "font_size": "40"},
                    "outputs": [{"name": "Shape Out", "type": "shape", "links": [6], "slot_index": 0}]
                },
                {
                    "id": 5,
                    "type": "Functions/Text to Shape",
                    "properties": {"text": "B", "font_name": "Arial", "font_size": "40"},
                    "outputs": [{"name": "Shape Out", "type": "shape", "links": [7], "slot_index": 0}]
                },
                {
                    "id": 6,
                    "type": "Shape/Shape Transform",
                    "properties": {"mode": "Distort", "t": "0.5"},
                    "inputs": [
                        {"name": "Shape / Texto", "type": "data", "link": 6},
                        {"name": "Target Shape", "type": "data", "link": 7},
                        {"name": "Factor (t)", "type": "data", "link": 5},
                        {"name": "Anchor", "type": "data", "link": None}
                    ],
                    "outputs": [{"name": "Shape", "type": "data", "links": [8], "slot_index": 0}]
                },
                {
                    "id": 7,
                    "type": "System/Output",
                    "properties": {"apply_to": "Sel. Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 2},
                        {"name": "Layer", "type": "data", "link": None},
                        {"name": "Start Time", "type": "data", "link": None},
                        {"name": "End Time", "type": "data", "link": None},
                        {"name": "Tags", "type": "data", "link": None},
                        {"name": "Return", "type": "data", "link": 8}
                    ],
                    "outputs": [{"name": "Preview", "type": "data", "links": []}]
                }
            ],
            "links": [
                [1, 1, 0, 2, 0, "bucle"],
                [2, 2, 0, 7, 0, "bucle"],
                [3, 2, 1, 3, 0, "data"],
                [4, 2, 2, 3, 1, "data"],
                [5, 3, 0, 6, 2, "data"],
                [6, 4, 0, 6, 0, "shape"],
                [7, 5, 0, 6, 1, "shape"],
                [8, 6, 0, 7, 5, "data"]
            ]
        }

        styles = {
            'Default': {
                'Fontname': 'Arial',
                'Fontsize': 40.0,
                'PrimaryColour': '&H00FFFFFF&',
                'SecondaryColour': '&H000000FF&',
                'OutlineColour': '&H00000000&',
                'BackColour': '&H00000000&',
                'ScaleX': 100.0,
                'ScaleY': 100.0,
                'Spacing': 0.0,
                'Outline': 2.0,
                'Shadow': 0.0,
                'Alignment': 5
            }
        }

        dialogue_items = [
            {
                'raw': 'Dialogue: 0,0:00:01.00,0:00:01.20,Default,,0,0,0,,{\\k20}A',
                'is_selected': True
            }
        ]

        engine = GraphEngine(graph)
        engine.process_single(dialogue_items, styles, allow_fallback_select_all=True)

        self.assertGreater(len(engine.all_generated_lines), 1)
        first_line = engine.all_generated_lines[0]['text']
        last_line = engine.all_generated_lines[-1]['text']
        self.assertNotEqual(first_line, last_line)

if __name__ == '__main__':
    unittest.main()

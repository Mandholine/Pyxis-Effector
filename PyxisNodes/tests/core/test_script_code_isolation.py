import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from node_engine import GraphEngine


class TestScriptCodeIsolation(unittest.TestCase):
    """Verifies strict branch isolation for System/Script Code across Output nodes."""

    def setUp(self):
        self.styles = {
            "Default": {
                "fontname": "Arial",
                "fontsize": 40.0,
                "bold": False,
                "italic": False,
                "underline": False,
                "strikeout": False,
                "scale_x": 100.0,
                "scale_y": 100.0,
                "spacing": 0.0,
                "angle": 0.0,
                "borderstyle": 1,
                "outline": 2.0,
                "shadow": 0.0,
                "align": 2,
                "margin_l": 30,
                "margin_r": 30,
                "margin_v": 30,
            }
        }
        self.dialogue_items = [
            {
                "raw": r"Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\k50}Hi",
                "is_selected": True,
                "i": 1,
            }
        ]

    def _make_output_node(self, node_id, loop_link_id, return_link_id=None, tags_link_id=None, queue_id=""):
        return {
            "id": node_id,
            "type": "System/Output",
            "properties": {
                "apply_to": "Selected Lines",
                "queue_id": queue_id,
                "queue_order": "",
                "origin_align": 5,
            },
            "inputs": [
                {"name": "Loop / Domain", "link": loop_link_id},
                {"name": "Layer", "link": None},
                {"name": "Start Time", "link": None},
                {"name": "End Time", "link": None},
                {"name": "Tags", "link": tags_link_id},
                {"name": "Return", "link": return_link_id},
                {"name": "Queue ID", "link": None},
                {"name": "Queue Order", "link": None},
            ],
            "outputs": [{"name": "Preview", "links": []}],
        }

    def test_two_script_nodes_remain_isolated_across_outputs_python(self):
        """Each Output branch must only see st, et, layer, and result from its own Script Code."""
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterator": "syl", "blank_mode": "no_blank", "preserve_tags": True},
                    "inputs": [],
                    "outputs": [{"name": "Loop", "links": [10, 20]}],
                },
                {
                    "id": 2,
                    "type": "System/Script Code",
                    "properties": {
                        "language": "Python",
                        "script": "st = 1100\net = 1500\nfx.layer = 1\nresult = r'\\c&H111111&'",
                        "inputs_count": 2,
                    },
                    "inputs": [
                        {"name": "Loop In", "link": 10},
                        {"name": "In1", "link": None},
                        {"name": "In2", "link": None},
                    ],
                    "outputs": [
                        {"name": "Loop Out", "links": [11]},
                        {"name": "Result", "links": []},
                    ],
                },
                {
                    "id": 3,
                    "type": "System/Script Code",
                    "properties": {
                        "language": "Python",
                        "script": "st = 2200\net = 2800\nfx.layer = 2\nresult = r'\\c&H222222&'",
                        "inputs_count": 2,
                    },
                    "inputs": [
                        {"name": "Loop In", "link": 20},
                        {"name": "In1", "link": None},
                        {"name": "In2", "link": None},
                    ],
                    "outputs": [
                        {"name": "Loop Out", "links": [21]},
                        {"name": "Result", "links": []},
                    ],
                },
                {
                    "id": 4,
                    "type": "System/Script Code",
                    "properties": {
                        "language": "Python",
                        "script": "st = 9999\net = 9999\nfx.layer = 9\nresult = r'\\c&H999999&'",
                        "inputs_count": 2,
                    },
                    "inputs": [
                        {"name": "Loop In", "link": None},
                        {"name": "In1", "link": None},
                        {"name": "In2", "link": None},
                    ],
                    "outputs": [
                        {"name": "Loop Out", "links": []},
                        {"name": "Result", "links": []},
                    ],
                },
                self._make_output_node(10, loop_link_id=11, queue_id="branch_a"),
                self._make_output_node(20, loop_link_id=21, queue_id="branch_b"),
            ],
            "links": [
                [10, 1, 0, 2, 0, "loop"],
                [11, 2, 0, 10, 0, "loop"],
                [20, 1, 0, 3, 0, "loop"],
                [21, 3, 0, 20, 0, "loop"],
            ],
        }

        engine = GraphEngine(graph_data, rx=1280, ry=720, fd=41.708333333333336)
        engine.process(self.dialogue_items, self.styles)
        lines = engine.all_generated_lines

        self.assertEqual(len(lines), 2)
        by_queue = {line["queue_id"]: line for line in lines}

        self.assertIn("branch_a", by_queue)
        self.assertEqual(by_queue["branch_a"]["start_time"], 1100.0)
        self.assertEqual(by_queue["branch_a"]["end_time"], 1500.0)
        self.assertEqual(by_queue["branch_a"]["layer"], 1)
        self.assertIn(r"\c&H111111&", by_queue["branch_a"]["text"])
        self.assertNotIn(r"\c&H222222&", by_queue["branch_a"]["text"])
        self.assertNotIn(r"\c&H999999&", by_queue["branch_a"]["text"])

        self.assertIn("branch_b", by_queue)
        self.assertEqual(by_queue["branch_b"]["start_time"], 2200.0)
        self.assertEqual(by_queue["branch_b"]["end_time"], 2800.0)
        self.assertEqual(by_queue["branch_b"]["layer"], 2)
        self.assertIn(r"\c&H222222&", by_queue["branch_b"]["text"])
        self.assertNotIn(r"\c&H111111&", by_queue["branch_b"]["text"])
        self.assertNotIn(r"\c&H999999&", by_queue["branch_b"]["text"])

    def test_data_port_script_result_does_not_leak_into_tags(self):
        """A Script Code wired only to Return must not inject its result into Output.Tags."""
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterator": "syl", "blank_mode": "no_blank", "preserve_tags": True},
                    "inputs": [],
                    "outputs": [{"name": "Loop", "links": [10]}],
                },
                {
                    "id": 2,
                    "type": "System/Script Code",
                    "properties": {
                        "language": "Python",
                        "script": r"result = r'{\c&H00FF00&}Custom'",
                        "inputs_count": 2,
                    },
                    "inputs": [
                        {"name": "Loop In", "link": None},
                        {"name": "In1", "link": None},
                        {"name": "In2", "link": None},
                    ],
                    "outputs": [
                        {"name": "Loop Out", "links": []},
                        {"name": "Result", "links": [11]},
                    ],
                },
                self._make_output_node(10, loop_link_id=10, return_link_id=11, queue_id="data_only"),
            ],
            "links": [
                [10, 1, 0, 10, 0, "loop"],
                [11, 2, 1, 10, 5, "string"],
            ],
        }

        engine = GraphEngine(graph_data, rx=1280, ry=720, fd=41.708333333333336)
        engine.process(self.dialogue_items, self.styles)
        lines = engine.all_generated_lines

        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["text"], r"{\an5\pos(640,700)\c&H00FF00&}Custom")
        self.assertEqual(lines[0]["text"].count(r"\c&H00FF00&"), 1)

    def test_two_script_nodes_remain_isolated_across_outputs_lua(self):
        """Lua Script Code branches must remain isolated per Output when lupa is available."""
        try:
            import lupa  # noqa: F401
        except ImportError:
            self.skipTest("lupa is not installed")

        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterator": "syl", "blank_mode": "no_blank", "preserve_tags": True},
                    "inputs": [],
                    "outputs": [{"name": "Loop", "links": [10, 20]}],
                },
                {
                    "id": 2,
                    "type": "System/Script Code",
                    "properties": {
                        "language": "Lua",
                        "script": "st = 1200\net = 1600\nfx.layer = 3\nresult = '\\\\c&HAAAAAA&'",
                        "inputs_count": 2,
                    },
                    "inputs": [
                        {"name": "Loop In", "link": 10},
                        {"name": "In1", "link": None},
                        {"name": "In2", "link": None},
                    ],
                    "outputs": [
                        {"name": "Loop Out", "links": [11]},
                        {"name": "Result", "links": []},
                    ],
                },
                {
                    "id": 3,
                    "type": "System/Script Code",
                    "properties": {
                        "language": "Lua",
                        "script": "st = 2400\net = 2900\nfx.layer = 4\nresult = '\\\\c&HBBBBBB&'",
                        "inputs_count": 2,
                    },
                    "inputs": [
                        {"name": "Loop In", "link": 20},
                        {"name": "In1", "link": None},
                        {"name": "In2", "link": None},
                    ],
                    "outputs": [
                        {"name": "Loop Out", "links": [21]},
                        {"name": "Result", "links": []},
                    ],
                },
                self._make_output_node(10, loop_link_id=11, queue_id="lua_a"),
                self._make_output_node(20, loop_link_id=21, queue_id="lua_b"),
            ],
            "links": [
                [10, 1, 0, 2, 0, "loop"],
                [11, 2, 0, 10, 0, "loop"],
                [20, 1, 0, 3, 0, "loop"],
                [21, 3, 0, 20, 0, "loop"],
            ],
        }

        engine = GraphEngine(graph_data, rx=1280, ry=720, fd=41.708333333333336)
        engine.process(self.dialogue_items, self.styles)
        lines = engine.all_generated_lines

        self.assertEqual(len(lines), 2)
        by_queue = {line["queue_id"]: line for line in lines}

        self.assertEqual(by_queue["lua_a"]["start_time"], 1200.0)
        self.assertEqual(by_queue["lua_a"]["end_time"], 1600.0)
        self.assertEqual(by_queue["lua_a"]["layer"], 3)
        self.assertIn(r"\c&HAAAAAA&", by_queue["lua_a"]["text"])
        self.assertNotIn(r"\c&HBBBBBB&", by_queue["lua_a"]["text"])

        self.assertEqual(by_queue["lua_b"]["start_time"], 2400.0)
        self.assertEqual(by_queue["lua_b"]["end_time"], 2900.0)
        self.assertEqual(by_queue["lua_b"]["layer"], 4)
        self.assertIn(r"\c&HBBBBBB&", by_queue["lua_b"]["text"])
        self.assertNotIn(r"\c&HAAAAAA&", by_queue["lua_b"]["text"])

    def test_dynamic_fx_timing_in_python_script(self):
        """Verifies fx.start_time, fx.end_time, and fx.dur update dynamically in Python Script Code."""
        from nodes.code_nodes import code_script_master

        ctx = {
            "fx_start_time": 1000.0,
            "fx_end_time": 1500.0,
            "fx_dur": 500.0,
            "start_time": 1000.0,
            "end_time": 1500.0,
            "st": 1000.0,
            "et": 1500.0,
            "dur": 500.0,
        }
        script = (
            "st = 1100\n"
            "et = 1950\n"
            "a = (int(fx.start_time), int(fx.end_time), int(fx.dur))\n"
            "fx.st = 1200\n"
            "fx.et = 2000\n"
            "b = (int(fx.start_time), int(fx.end_time), int(fx.dur))\n"
            "fx.dur = 350\n"
            "c = (int(fx.start_time), int(fx.end_time), int(fx.dur))\n"
            "result = f'{a}|{b}|{c}'"
        )
        res = code_script_master(ctx, script=script, language="Python")
        self.assertEqual(res, "(1100, 1950, 850)|(1200, 2000, 800)|(1200, 1550, 350)")

    def test_dynamic_fx_timing_in_lua_script(self):
        """Verifies fx.start_time, fx.end_time, and fx.dur update dynamically in Lua Script Code."""
        try:
            import lupa  # noqa: F401
        except ImportError:
            self.skipTest("lupa is not installed")

        from nodes.code_nodes import code_script_master

        ctx = {
            "fx_start_time": 1000.0,
            "fx_end_time": 1500.0,
            "fx_dur": 500.0,
            "start_time": 1000.0,
            "end_time": 1500.0,
            "st": 1000.0,
            "et": 1500.0,
            "dur": 500.0,
        }
        script = (
            "st = 1100\n"
            "et = 1950\n"
            "local a = string.format('%d,%d,%d', fx.start_time, fx.end_time, fx.dur)\n"
            "fx.st = 1200\n"
            "fx.et = 2000\n"
            "local b = string.format('%d,%d,%d', fx.start_time, fx.end_time, fx.dur)\n"
            "fx.dur = 350\n"
            "local c = string.format('%d,%d,%d', fx.start_time, fx.end_time, fx.dur)\n"
            "result = a .. '|' .. b .. '|' .. c"
        )
        res = code_script_master(ctx, script=script, language="Lua")
        self.assertEqual(res, "1100,1950,850|1200,2000,800|1200,1550,350")


if __name__ == "__main__":
    unittest.main()

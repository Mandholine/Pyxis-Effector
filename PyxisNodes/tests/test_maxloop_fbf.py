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

# tests/test_maxloop_fbf.py
"""Pruebas unitarias para el Modo FBF (Frame-by-Frame) en MaxLoop."""

import unittest
from node_engine import GraphEngine


class TestMaxLoopFBF(unittest.TestCase):

    def test_maxloop_fbf_41_7ms(self):
        """Verifica que MaxLoop en modo FBF divida la línea a 41.7ms e inyecte tiempos de frame automáticamente."""
        graph_data = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"iterador": "line", "noblank": "No Blank"}, "outputs": [{"name": "Loop", "links": [101]}]},
                {
                    "id": 2,
                    "type": "Loops/MaxLoop",
                    "properties": {"modo": "FBF", "step_ms": "41.7", "var_name": "j"},
                    "inputs": [{"name": "Loop In", "link": 101}],
                    "outputs": [{"name": "Loop Out", "links": [102]}]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 102},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": None}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 2, 0, "Loop"],
                [102, 2, 0, 3, 0, "Loop"]
            ]
        }

        engine = GraphEngine(graph_data, 1280, 720, 41.708)
        dialogues = [{
            "raw": "Dialogue: 0,0:00:00.00,0:00:00.20,Default,,0,0,0,,{\\k20}Test FBF",
            "metrics": {
                "h": 35, "d": 0, "e": 0, "sel": True, "rw": 100, "l": 50, "c": 100, "r": 150, "t": 50, "m": 65, "b": 80,
                "syl_lefts": [50], "syl_centers": [100], "syl_rights": [150], "syl_widths": [100],
                "syl_starts": [0], "syl_ends": [200], "w": [100]
            }
        }]
        styles = {"Default": {}}

        lines = engine.process(dialogues, styles)
        # 200 ms / 41.7 ms = ceil(4.79) = 5 frames
        self.assertEqual(len(lines), 5)
        self.assertTrue("0:00:00.00" in lines[0] or ",0," in lines[0])

    def test_maxloop_fbf_83_4ms_two_frames(self):
        """Verifica que MaxLoop en modo FBF con paso de 83.4ms genere fotogramas cada 2 frames."""
        graph_data = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"iterador": "line", "noblank": "No Blank"}, "outputs": [{"name": "Loop", "links": [101]}]},
                {
                    "id": 2,
                    "type": "Loops/MaxLoop",
                    "properties": {"modo": "FBF", "step_ms": "83.4", "var_name": "j"},
                    "inputs": [{"name": "Loop In", "link": 101}],
                    "outputs": [{"name": "Loop Out", "links": [102]}]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 102},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": None}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 2, 0, "Loop"],
                [102, 2, 0, 3, 0, "Loop"]
            ]
        }

        engine = GraphEngine(graph_data, 1280, 720, 41.708)
        dialogues = [{
            "raw": "Dialogue: 0,0:00:00.00,0:00:00.25,Default,,0,0,0,,{\\k25}Test FBF 2",
            "metrics": {
                "h": 35, "d": 0, "e": 0, "sel": True, "rw": 100, "l": 50, "c": 100, "r": 150, "t": 50, "m": 65, "b": 80,
                "syl_lefts": [50], "syl_centers": [100], "syl_rights": [150], "syl_widths": [100],
                "syl_starts": [0], "syl_ends": [250], "w": [100]
            }
        }]
        styles = {"Default": {}}

        lines = engine.process(dialogues, styles)
        # 250 ms / 83.4 ms = ceil(2.997) = 3 frames
        self.assertEqual(len(lines), 3)

    def test_maxloop_fbf_custom_start_end_properties(self):
        """Verifica que MaxLoop FBF acepte expresiones en start_time y end_time (ej. Lead In previo)."""
        graph_data = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"iterador": "line", "noblank": "No Blank"}, "outputs": [{"name": "Loop", "links": [101]}]},
                {
                    "id": 2,
                    "type": "Loops/MaxLoop",
                    "properties": {
                        "modo": "FBF",
                        "step_ms": "41.7",
                        "start_time": "line.start_time - 200",
                        "end_time": "line.start_time",
                        "var_name": "j"
                    },
                    "inputs": [{"name": "Loop In", "link": 101}],
                    "outputs": [{"name": "Loop Out", "links": [102]}]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 102},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": None}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 2, 0, "Loop"],
                [102, 2, 0, 3, 0, "Loop"]
            ]
        }

        engine = GraphEngine(graph_data, 1280, 720, 41.708)
        dialogues = [{
            "raw": "Dialogue: 0,0:00:10.00,0:00:15.00,Default,,0,0,0,,{\\k500}Test LeadIn",
            "metrics": {
                "h": 35, "d": 0, "e": 0, "sel": True, "rw": 100, "l": 50, "c": 100, "r": 150, "t": 50, "m": 65, "b": 80,
                "syl_lefts": [50], "syl_centers": [100], "syl_rights": [150], "syl_widths": [100],
                "syl_starts": [0], "syl_ends": [5000], "w": [100]
            }
        }]
        styles = {"Default": {}}

        lines = engine.process(dialogues, styles)
        # 200 ms lead-in (10000 - 200 = 9800 to 10000) / 41.7 = ceil(4.79) = 5 frames
        self.assertEqual(len(lines), 5)
        self.assertTrue("0:00:09.80" in lines[0] or ",9800," in lines[0])


if __name__ == "__main__":
    unittest.main()

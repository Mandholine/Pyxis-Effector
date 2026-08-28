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

# PyxisNodes/tests/test_time_sync_v099.py
"""Pruebas unitarias completas para el nodo Tiempo Sincronizado (Etapa 2 - v1.0.1)."""

import unittest
from models import PyxisLine, PyxisUnit
from nodes.time_nodes import time_synchronized_extra_node
from node_engine import GraphEngine


def _make_line(text="Hello", start=1000, end=2000, left=100, right=200, width=100):
    line = PyxisLine()
    line.text = text
    line.text_stripped = text
    line.start_time = start
    line.end_time = end
    line.duration = end - start
    line.left = left
    line.right = right
    line.width = width
    line.x = (left + right) / 2.0
    line.y = 700.0
    line.style_name = "Default"
    line.is_selected = True
    return line


class TestTimeSyncV099(unittest.TestCase):

    def test_single_line_isolated(self):
        """Línea aislada sin siguiente línea: tiempo extra = p_const * (char_count - 1) + delay."""
        line = _make_line(text="ABCDE", start=1000, end=2000)  # 5 chars
        ctx = {'line': line, 'active_line': line}
        # 5 chars -> (5 - 1) * 20 + 250 = 80 + 250 = 330.0
        res = time_synchronized_extra_node(ctx, progression_const=20, delay=250, max_added_time=2000)
        self.assertEqual(res, 330.0)

    def test_single_line_cap_max(self):
        """El tiempo extra no debe exceder max_added_time."""
        line = _make_line(text="A" * 100, start=1000, end=2000)
        ctx = {'line': line, 'active_line': line}
        res = time_synchronized_extra_node(ctx, progression_const=50, delay=250, max_added_time=500)
        self.assertEqual(res, 500.0)

    def test_two_lines_gap_too_small(self):
        """Si la brecha temporal entre líneas es menor que delay, devuelve 0 extra time."""
        line1 = _make_line(text="Línea 1", start=1000, end=2000)
        line2 = _make_line(text="Línea 2", start=2100, end=3000)  # gap = 100ms (< delay de 250ms)
        ctx = {'line': line1, 'active_line': line1, 'next_line': line2}
        res = time_synchronized_extra_node(ctx, progression_const=20, delay=250)
        self.assertEqual(res, 0.0)

    def test_two_lines_gap_exceeds_threshold(self):
        """Si la brecha temporal supera max_gap_threshold, devuelve el tiempo estándar."""
        line1 = _make_line(text="ABC", start=1000, end=2000)  # 3 chars
        line2 = _make_line(text="DEF", start=6000, end=7000)  # gap = 4000ms (> 3000ms threshold)
        ctx = {'line': line1, 'active_line': line1, 'next_line': line2}
        # (3 - 1) * 20 + 250 = 290.0
        res = time_synchronized_extra_node(ctx, progression_const=20, delay=250, max_gap_threshold=3000)
        self.assertEqual(res, 290.0)

    def test_two_lines_gap_within_threshold_compensation(self):
        """Dentro del umbral, calcula la compensación espacial y temporal inter-líneas."""
        line1 = _make_line(text="ABC", start=1000, end=2000, left=100, right=200, width=100)
        line2 = _make_line(text="DEF", start=2800, end=3800, left=250, right=350, width=100)  # gap = 800ms
        ctx = {'line': line1, 'active_line': line1, 'all_lines': [line1, line2]}
        res = time_synchronized_extra_node(ctx, progression_const=20, fade_dur=100, delay=250, max_gap_threshold=3000)
        self.assertGreater(res, 0.0)
        self.assertLessEqual(res, 2000.0)

    def test_graph_engine_evaluation_multi_slots(self):
        """Verifica la evaluación en grafo de Tiempo Sincronizado para slot 0 (Extra ms) y slot 1 (Sync End)."""
        line = _make_line(text="Pyxis", start=1000, end=2000)
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Time/Synced Time",
                    "properties": {
                        "progression_const": "20",
                        "fade_dur": "100",
                        "max_added_time": "1500",
                        "delay": "250",
                        "max_gap_threshold": "3000"
                    }
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        ctx = {'line': line, 'active_line': line}
        
        # 5 chars -> (5 - 1) * 20 + 250 = 80 + 250 = 330.0
        slot0_extra = engine.evaluate_data_node(1, ctx, output_slot_index=0)
        self.assertEqual(slot0_extra, "330.0")

        # Sync End = line.end_time (2000) + 330 = 2330.0
        slot1_sync_end = engine.evaluate_data_node(1, ctx, output_slot_index=1)
        self.assertEqual(slot1_sync_end, "2330.0")

    def test_syllable_nested_context_resolution(self):
        """Verifica la resolución de línea cuando el contexto activo es una sílaba (syl)."""
        line = _make_line(text="Mary", start=8320, end=13330)
        syl = PyxisUnit()
        syl.i = 1; syl.n = 2; syl.text = "Ma"; syl.line = line
        ctx = {'line': line, 'active_unit': syl, 'syl': syl}
        
        res = time_synchronized_extra_node(ctx, progression_const=30, delay=250)
        self.assertEqual(res, 340.0)  # (4 - 1) * 30 + 250 = 90 + 250 = 340.0


if __name__ == '__main__':
    unittest.main()

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

# PyxisNodes/tests/test_tag_oscillator_v101.py
"""Pruebas unitarias completas para el nodo Tag Oscilador unificado (v1.0.1)."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nodes.tag_nodes import tag_oscillator_node
from main import PYXIS_ENGINE_VERSION

class TestTagOscillatorNodeV101(unittest.TestCase):
    def test_version_bump_v101(self):
        self.assertEqual(PYXIS_ENGINE_VERSION, "1.0.5")

    def test_basic_oscillation_sequence(self):
        ctx = {"start_time": 0.0, "end_time": 1000.0}
        res = tag_oscillator_node(
            context=ctx,
            step_ms=200.0,
            trans_ms=50.0,
            tags=r"\fscx140\fscy140,\fscx100\fscy100",
            modo_oscilacion="Onda",
            modo_orden="Secuencial",
            output_slot_index=0
        )
        self.assertIn(r"\t(0,50,\fscx140\fscy140)", res)
        self.assertIn(r"\t(200,250,\fscx100\fscy100)", res)
        self.assertIn(r"\t(400,450,\fscx140\fscy140)", res)
        self.assertIn(r"\t(600,650,\fscx100\fscy100)", res)
        self.assertIn(r"\t(800,850,\fscx140\fscy140)", res)

    def test_strobe_rigid_mode(self):
        ctx = {"start_time": 0.0, "end_time": 500.0}
        res = tag_oscillator_node(
            context=ctx,
            step_ms=100.0,
            tags=r"\1c&HFF0000&,\1c&H00FF00&",
            modo_oscilacion="Destellos",
            output_slot_index=0
        )
        self.assertIn(r"\t(0,1,\1c&HFF0000&)", res)
        self.assertIn(r"\t(100,101,\1c&H00FF00&)", res)

    def test_duty_cycle(self):
        ctx = {"start_time": 0.0, "end_time": 400.0}
        res = tag_oscillator_node(
            context=ctx,
            step_ms=200.0,
            duty_cycle=0.25, # 25% of 200 = 50ms transition
            tags=r"\fscx120,\fscx100",
            output_slot_index=0
        )
        self.assertIn(r"\t(0,50,\fscx120)", res)
        self.assertIn(r"\t(200,250,\fscx100)", res)

    def test_ping_pong_order(self):
        ctx = {"start_time": 0.0, "end_time": 800.0}
        keyframes = tag_oscillator_node(
            context=ctx,
            step_ms=200.0,
            trans_ms=50.0,
            tags=r"\1c&H111111&,\1c&H222222&,\1c&H333333&",
            modo_orden="Ping-Pong",
            output_slot_index=2
        )
        # Expected index order: 0 (111111), 1 (222222), 2 (333333), 1 (222222)
        tag_sequence = [k[2] for k in keyframes]
        self.assertEqual(tag_sequence[0], r"\1c&H111111&")
        self.assertEqual(tag_sequence[1], r"\1c&H222222&")
        self.assertEqual(tag_sequence[2], r"\1c&H333333&")
        self.assertEqual(tag_sequence[3], r"\1c&H222222&")

    def test_rhythm_pattern(self):
        ctx = {"start_time": 0.0, "end_time": 600.0}
        keyframes = tag_oscillator_node(
            context=ctx,
            rhythm_pattern="100,50,200",
            trans_ms=30.0,
            tags=r"\alpha&H00&,\alpha&HFF&",
            output_slot_index=2
        )
        # Step 0: 0->30, Step 1: 100->130, Step 2: 150->180, Step 3: 350->380
        t_starts = [k[0] for k in keyframes]
        self.assertEqual(t_starts[0], 0)
        self.assertEqual(t_starts[1], 100)
        self.assertEqual(t_starts[2], 150)
        self.assertEqual(t_starts[3], 350)

if __name__ == "__main__":
    unittest.main()

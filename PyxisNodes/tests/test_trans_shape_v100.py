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

# tests/test_trans_shape_v100.py
"""Pruebas unitarias completas para el nodo Shape Manipulator (Offsetting real de contornos PyClipperOffset y modos de anclaje)."""

import unittest
from models import PyxisLine, PyxisUnit
from nodes.shape_nodes import shape_manipulator
from node_engine import GraphEngine


class TestTransShapeV100(unittest.TestCase):

    def setUp(self):
        self.sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        self.context = {
            'active_unit': PyxisUnit(),
            'active_line': PyxisLine(),
            'fx_pos_x': 200.0,
            'fx_pos_y': 300.0
        }

    def test_anchor_modes(self):
        """Verifica los modos de anclaje: center, topleft, absolute, original."""
        res_center = shape_manipulator(self.context, drawing=self.sq, scale_x=1.0, scale_y=1.0, mode="center")
        self.assertTrue(res_center.startswith("m -50 -50"))

        res_topleft = shape_manipulator(self.context, drawing=self.sq, scale_x=1.0, scale_y=1.0, mode="topleft")
        self.assertTrue(res_topleft.startswith("m 0 0"))

        res_abs = shape_manipulator(self.context, drawing=self.sq, scale_x=1.0, scale_y=1.0, mode="absolute")
        self.assertTrue(res_abs.startswith("m 150 250"))

        res_orig = shape_manipulator(self.context, drawing=self.sq, scale_x=1.0, scale_y=1.0, mode="original")
        self.assertTrue(res_orig.startswith("m 0 0"))

    def test_real_shape_offsetting(self):
        """Verifica la expansión (+10px) y contracción (-10px) de contornos usando PyClipperOffset."""
        res_plus = shape_manipulator(self.context, drawing=self.sq, offset_border=10.0, mode="topleft")
        self.assertIn("l", res_plus)
        self.assertNotIn("[Err", res_plus)

        res_minus = shape_manipulator(self.context, drawing=self.sq, offset_border=-10.0, mode="topleft")
        self.assertTrue(res_minus.startswith("m 80 80"))

    def test_full_node_execution(self):
        """Verifica la evaluación del nodo Shape Manipulator a través de GraphEngine."""
        graph = {
            'nodes': [
                {
                    'id': 1,
                    'type': 'Shape/Shape Manipulator',
                    'properties': {
                        'shape': self.sq,
                        'scale_x': '1.5',
                        'scale_y': '1.5',
                        'angle': '0',
                        'offset_x': '10',
                        'offset_y': '20',
                        'offset_border': '5.0',
                        'anchor': 'center'
                    },
                    'inputs': []
                }
            ],
            'links': []
        }

        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, self.context, output_slot_index=0)
        self.assertIsInstance(res, str)
        self.assertTrue(res.startswith("m "))


if __name__ == '__main__':
    unittest.main()

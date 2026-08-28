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

# tests/test_shape_slicer_pre_offset.py
"""Pruebas unitarias para pre_offset en el nodo Shape Slicer (ClipperEngine.slice_grid)."""

import unittest
from clipper_engine import ClipperEngine
from node_engine import GraphEngine


class TestShapeSlicerPreOffset(unittest.TestCase):

    def setUp(self):
        self.sq = "m 0 0 l 100 0 l 100 100 l 0 100"

    def test_pre_offset_expansion_in_slice_grid(self):
        """Verifica que pre_offset expanda la figura base antes del corte."""
        pieces_base = ClipperEngine.slice_grid(self.sq, cols=2, rows=2, pre_offset=0.0)
        pieces_exp = ClipperEngine.slice_grid(self.sq, cols=2, rows=2, pre_offset=10.0)

        bbox_base = ClipperEngine.get_bbox(ClipperEngine.parse_assdraw(pieces_base[0]['code']))
        bbox_exp = ClipperEngine.get_bbox(ClipperEngine.parse_assdraw(pieces_exp[0]['code']))

        # La pieza expandida debe tener mayor ancho/alto que la base
        self.assertGreater(bbox_exp[6], bbox_base[6])
        self.assertGreater(bbox_exp[7], bbox_base[7])

    def test_pre_offset_graph_evaluation(self):
        """Verifica la evaluación del nodo Shape Slicer con Pre-Offset en GraphEngine."""
        graph = {
            'nodes': [
                {
                    'id': 1,
                    'type': 'Shape/Shape Slicer',
                    'properties': {
                        'modo': 'Rejilla 1D/2D',
                        'cols': '2',
                        'rows': '2',
                        'pre_offset': '5.0',
                        'out_mode': 'Shape',
                        'anchor': 'piezas'
                    },
                    'inputs': []
                }
            ],
            'links': []
        }

        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {}, output_slot_index=0)
        self.assertIsInstance(res, str)
        self.assertTrue(res.startswith("m "))


if __name__ == '__main__':
    unittest.main()

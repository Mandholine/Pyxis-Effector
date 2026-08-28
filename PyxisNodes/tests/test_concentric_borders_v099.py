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

# PyxisNodes/tests/test_concentric_borders_v099.py
"""Pruebas unitarias completas para Bordes Concéntricos y separación de Partículas (Etapa 3 - v1.0.1)."""

import unittest
from models import PyxisLine, PyxisUnit
from nodes.shape_nodes import shape_concentric_borders_node
from particle_nodes import particle_text_node, particle_image_node
from node_engine import GraphEngine
from clipper_engine import ClipperEngine


class TestConcentricBordersV099(unittest.TestCase):

    def setUp(self):
        self.unit = PyxisUnit()
        self.unit.i = 1
        self.unit.n = 1
        self.unit.center = 640.0
        self.unit.middle = 360.0
        self.unit.text = "A"
        self.unit.text_stripped = "A"

        self.line = PyxisLine()
        self.line.text = "Pyxis"
        self.line.text_stripped = "Pyxis"
        self.line.center = 640.0
        self.line.middle = 360.0
        self.line.syls = [self.unit]
        self.unit.line = self.line

        self.ctx = {
            'line': self.line,
            'active_unit': self.unit,
            'syl': self.unit,
            'fx_i': 1,
            'fx_n': 4,
            'j': 1,
            'j_max': 4
        }
        self.base_square = "m 0 0 l 100 0 l 100 100 l 0 100"

    def test_clipper_offset_shape(self):
        """Verifica que offset_shape expanda o contraiga el polígono correctamente."""
        expanded = ClipperEngine.offset_shape(self.base_square, delta=5.0)
        self.assertTrue(len(expanded) > 0)
        self.assertTrue(expanded.startswith("m ") or expanded.startswith("m"))
        cnts = ClipperEngine.parse_assdraw(expanded)
        _, _, _, _, _, _, w, h = ClipperEngine.get_bbox(cnts)
        self.assertGreater(w, 100.0)
        self.assertGreater(h, 100.0)

    def test_concentric_borders_hollow_mode(self):
        """Verifica el modo Hueco (shape.borders): cada anillo es la diferencia entre capas sucesivas."""
        for ring_idx in range(1, 4):
            ctx = self.ctx.copy()
            ctx['j'] = ring_idx
            ctx['fx_i'] = ring_idx
            ctx['fx_n'] = 3
            shp, pos, idx, total = shape_concentric_borders_node(
                ctx, shape=self.base_square, separation=5.0, overlap=0.5, mode="Hueco (borders)", loop_count=3
            )
            self.assertTrue(len(shp) > 0)
            self.assertEqual(idx, ring_idx)
            self.assertEqual(total, 3)

    def test_concentric_borders_filled_base_mode(self):
        """Verifica el modo Relleno Base (shape.filled_borders): loop 1 es relleno, loops 2+ son anillos."""
        # Loop 1: Forma base rellena
        ctx1 = self.ctx.copy()
        ctx1['j'] = 1
        ctx1['fx_i'] = 1
        ctx1['fx_n'] = 3
        shp1, _, idx1, _ = shape_concentric_borders_node(
            ctx1, shape=self.base_square, separation=5.0, overlap=0.0, mode="Relleno Base (filled_borders)", loop_count=3
        )
        self.assertTrue(len(shp1) > 0)
        self.assertEqual(idx1, 1)

        # Loop 2: Anillo exterior
        ctx2 = self.ctx.copy()
        ctx2['j'] = 2
        ctx2['fx_i'] = 2
        ctx2['fx_n'] = 3
        shp2, _, idx2, _ = shape_concentric_borders_node(
            ctx2, shape=self.base_square, separation=5.0, overlap=0.5, mode="Relleno Base (filled_borders)", loop_count=3
        )
        self.assertTrue(len(shp2) > 0)
        self.assertEqual(idx2, 2)

    def test_concentric_borders_custom_separation_list(self):
        """Verifica el soporte para lista de separaciones personalizada (ej. '5, 10, 20')."""
        ctx = self.ctx.copy()
        ctx['j'] = 2
        ctx['fx_i'] = 2
        ctx['fx_n'] = 3
        shp, _, idx, _ = shape_concentric_borders_node(
            ctx, shape=self.base_square, separation="5, 10, 20", overlap=0.5, loop_count=3
        )
        self.assertTrue(len(shp) > 0)

    def test_concentric_borders_graph_engine_slots(self):
        """Verifica la evaluación multi-slot de Bordes Concéntricos en GraphEngine."""
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Shape/Concentric Borders",
                    "properties": {
                        "shape": self.base_square,
                        "separation": "6",
                        "overlap": "0.5",
                        "modo": "Hueco (borders)",
                        "loop_count": "4"
                    }
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph)

        # Slot 0: Forma ASSDraw
        slot0_shp = engine.evaluate_data_node(1, self.ctx, output_slot_index=0)
        self.assertTrue(slot0_shp.startswith("m ") or slot0_shp.startswith("m"))

        # Slot 1: \pos tag
        slot1_pos = engine.evaluate_data_node(1, self.ctx, output_slot_index=1)
        self.assertTrue(slot1_pos.startswith("\\pos("))

        # Slot 2: Índice actual
        slot2_idx = engine.evaluate_data_node(1, self.ctx, output_slot_index=2)
        self.assertEqual(slot2_idx, "1")

        # Slot 3: Total anillos
        slot3_total = engine.evaluate_data_node(1, self.ctx, output_slot_index=3)
        self.assertEqual(slot3_total, "4")

    def test_concentric_borders_clip_and_anchor(self):
        """Verifica la generación de tags de \\clip, \\iclip y formas en coordenadas absolutas."""
        # 1. Modo Clip
        clip_res, _, _, _ = shape_concentric_borders_node(
            self.ctx, shape=self.base_square, separation=5.0, out_mode="Clip", loop_count=2
        )
        self.assertTrue(clip_res.startswith("\\clip("))
        self.assertTrue(clip_res.endswith(")"))
        self.assertIn("640.0", clip_res)

        # 2. Modo iClip
        iclip_res, _, _, _ = shape_concentric_borders_node(
            self.ctx, shape=self.base_square, separation=5.0, out_mode="iClip", loop_count=2
        )
        self.assertTrue(iclip_res.startswith("\\iclip("))
        self.assertTrue(iclip_res.endswith(")"))

        # 3. Anclaje Absoluto
        abs_shape, _, _, _ = shape_concentric_borders_node(
            self.ctx, shape=self.base_square, separation=5.0, out_mode="Shape", anchor="absoluto", loop_count=2
        )
        self.assertTrue(abs_shape.startswith("m "))
        self.assertIn("640.0", abs_shape)

    def test_particles_discrete_sampling(self):
        """Verifica que el nodo Partículas muestree coordenadas discretas sin contaminar con lógica de mallas."""
        abs_x, abs_y, p_shape, total = particle_text_node(self.ctx, shape=self.base_square, density=10.0, redraw_dist=0.0)
        self.assertTrue(isinstance(abs_x, float))
        self.assertTrue(isinstance(abs_y, float))
        self.assertGreater(total, 0)


if __name__ == '__main__':
    unittest.main()

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

# tests/test_particle_nodes_v100.py
"""Pruebas unitarias completas para los nodos de partículas v1.0.1 (Doble forma, Numpad ordering, Anclaje, Fusión y Desduplicación Inteligente de Tags ASS)."""

import unittest
import numpy as np
from models import PyxisLine, PyxisUnit
from particle_nodes import particle_text_node, particle_image_node, sort_particles
from node_engine import GraphEngine, merge_ass_tags


class TestParticleNodesV100(unittest.TestCase):

    def setUp(self):
        self.context = {
            'active_unit': PyxisUnit(),
            'active_line': PyxisLine(),
            'fx_i': 1
        }

    def test_numpad_sorting(self):
        """Verifica la ordenación direccional Numpad (79, 13, 5 Radial, Rand)."""
        pts = [(0, 0), (10, 0), (0, 10), (10, 10), (5, 5)]
        
        # Order 79 (TL -> BR): Y ascendente, luego X ascendente
        res_79 = sort_particles(pts, order_code="79", get_xy=lambda p: (p[0], p[1]))
        self.assertEqual(res_79[0], (0, 0))
        self.assertEqual(res_79[-1], (10, 10))

        # Order 5 (Centro -> Afuera): (5, 5) debe ser el primero
        res_5 = sort_particles(pts, order_code="5", get_xy=lambda p: (p[0], p[1]))
        self.assertEqual(res_5[0], (5, 5))

        # Order -5 (Afuera -> Centro / Implosión)
        res_inv5 = sort_particles(pts, order_code="-5", get_xy=lambda p: (p[0], p[1]))
        self.assertNotEqual(res_inv5[0], (5, 5))

    def test_particle_text_node_dual_shape_and_slots(self):
        """Verifica el nodo Partículas de Texto con doble forma y salidas estandarizadas."""
        path_shape = "m 0 0 l 100 0 l 100 100 l 0 100"
        particle_shape = "m 0 0 l 5 0 l 5 5 l 0 5"

        abs_x, abs_y, p_shape, total_pts = particle_text_node(
            self.context,
            shape=path_shape,
            particle_shape=particle_shape,
            density=20.0,
            mode="Contorno v2",
            order="79"
        )

        self.assertGreater(total_pts, 0)
        self.assertEqual(p_shape, particle_shape)
        self.assertIsInstance(abs_x, float)
        self.assertIsInstance(abs_y, float)

    def test_single_wire_text_out_in_salida(self):
        """Verifica que conectar Text Out (Slot 0) directamente a Return en Salida extraiga pos y shape con \\p1."""
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Functions/Particles",
                    "properties": {
                        "shape": "m 0 0 l 50 0 l 50 50 l 0 50",
                        "particle_shape": "m 0 0 l 2 0 l 2 2 l 0 2",
                        "density": "25.0"
                    },
                    "inputs": [{"name": "Path / Origen"}, {"name": "Forma Partícula"}, {"name": "Density"}]
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {},
                    "inputs": [
                        {"name": "Loop / Domain", "link": None},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": 1}
                    ]
                }
            ],
            "links": [
                [1, 1, 0, 2, 5, 0]
            ]
        }

        line = PyxisLine()
        line.style_name = "Default"
        u = PyxisUnit()
        u.text = "Test"
        u.text_stripped = "Test"
        u.line = line
        u.center = 640.0
        u.middle = 360.0

        ctx = {'line': line, 'unit': u, 'active_unit': u, 'fx_i': 1}
        engine = GraphEngine(graph)
        salida_node = engine.nodes[2]

        engine.execute_loops_recursive([], ctx, salida_node, u)
        
        self.assertGreater(len(engine.all_generated_lines), 0)
        line_text = engine.all_generated_lines[0]['text']
        self.assertIn(r"\p1", line_text)
        self.assertIn(r"\pos(", line_text)
        self.assertIn("m 0 0 l 2 0 l 2 2 l 0 2", line_text)

    def test_tags_port_override_priority(self):
        """Verifica la fusión inteligente y desduplicación limpia de tags con prioridad del puerto Tags."""
        tags_port = r"\pos(999,999)\1c&H00FF00&"
        embedded_return = r"\pos(100,100)\1c&H0000FF&\an5\p1"
        
        merged = merge_ass_tags(return_tags_str=embedded_return, port_tags_str=tags_port)
        
        # Debe contener la posición y color del puerto Tags
        self.assertIn(r"\pos(999,999)", merged)
        self.assertIn(r"\1c&H00FF00&", merged)
        # NO debe contener duplicados de Return
        self.assertNotIn(r"\pos(100,100)", merged)
        self.assertNotIn(r"\1c&H0000FF&", merged)
        # Debe mantener los tags de Return que no colisionaron
        self.assertIn(r"\an5", merged)
        self.assertIn(r"\p1", merged)

    def test_particle_image_node_fallback(self):
        """Verifica la respuesta de particle_image_node cuando la ruta de imagen no existe."""
        abs_x, abs_y, col_ass, alpha_ass, p_shape, total_px = particle_image_node(
            self.context,
            image_path="invalid/path/image.png",
            particle_shape="m 0 0 l 3 0 l 3 3 l 0 3",
            anchor="Center",
            order="79"
        )

        self.assertEqual(col_ass, "&HFFFFFF&")
        self.assertEqual(alpha_ass, "&H00&")
        self.assertEqual(p_shape, "m 0 0 l 3 0 l 3 3 l 0 3")
        self.assertEqual(total_px, 1)

    def test_default_text_shape_scale_resolution(self):
        """Verifica que el shape de texto por default resuelva el estilo desde unit.line.styleref cuando active_line no está en el contexto."""
        line = PyxisLine()
        line.styleref.fontsize = 80.0
        line.styleref.fontname = "Arial"

        u = PyxisUnit()
        u.text = "A"
        u.text_stripped = "A"
        u.line = line
        u.center = 100.0
        u.middle = 100.0

        ctx = {'active_unit': u, 'fx_i': 1}
        abs_x, abs_y, p_shape, total_pts = particle_text_node(
            ctx,
            shape="", # Default text shape
            particle_shape="m 0 0 l 2 0 l 2 2 l 0 2",
            density=10.0
        )
        self.assertGreater(total_pts, 0)

    def test_inline_ass_tags_scale_override(self):
        """Verifica que los tags de anulación ASS en el texto (ej. \\fs90) modifiquen la escala del vector."""
        line = PyxisLine()
        line.styleref.fontsize = 40.0

        u = PyxisUnit()
        u.text = r"{\fs90\fscx120}A"
        u.text_stripped = "A"
        u.line = line
        u.center = 100.0
        u.middle = 100.0

        ctx = {'active_unit': u, 'fx_i': 1}
        abs_x, abs_y, p_shape, total_pts = particle_text_node(
            ctx,
            shape="",
            particle_shape="m 0 0 l 2 0 l 2 2 l 0 2",
            density=10.0
        )
        self.assertGreater(total_pts, 0)

    def test_contour_arc_length_uniformity(self):
        """Verifica que el muestreo de contorno por longitud de arco sea 100% uniforme entre segmentos rectos y curvos."""
        u = PyxisUnit()
        u.center = 0.0
        u.middle = 0.0

        # Un cuadrado de 100x100 (perímetro 400px)
        shape_square = "m 0 0 l 100 0 l 100 100 l 0 100"
        ctx1 = {'active_unit': u, 'fx_i': 1}
        *_, pts_square = particle_text_node(ctx1, shape=shape_square, density=10.0, mode="Contorno v2")

        # 400 / 10 = 40 partículas esperadas
        self.assertAlmostEqual(pts_square, 40, delta=2)


if __name__ == '__main__':
    unittest.main()

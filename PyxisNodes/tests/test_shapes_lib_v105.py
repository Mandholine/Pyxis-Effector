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

# PyxisNodes/tests/test_shapes_lib_v105.py
"""Pruebas unitarias completas para el Nodo Maestro Shapes Lib v1.0.5 con 80 formas."""

import unittest
from nodes.shape_nodes import eval_shapes_lib_node, RAW_PRESET_SHAPES, SHAPES_LIB_MAP
from node_engine import GraphEngine

class TestUnifiedShapesLibNode(unittest.TestCase):
    def setUp(self):
        self.context = {}

    def test_all_80_shapes_return_non_empty_ass_draw(self):
        """Verifica que cada una de las 80 formas retorne una cadena vectorial ASS válida."""
        self.assertGreaterEqual(len(RAW_PRESET_SHAPES), 80)
        for forma_key in RAW_PRESET_SHAPES.keys():
            with self.subTest(forma=forma_key):
                res = eval_shapes_lib_node(self.context, forma=forma_key)
                self.assertTrue(isinstance(res, str) and len(res) > 5, f"Falló forma '{forma_key}'")
                self.assertTrue(res.startswith("m "), f"Forma '{forma_key}' no inicia con comandos de trazado 'm '")

    def test_shortened_and_legacy_names(self):
        """Verifica que los nombres compactos y los alias tradicionales funcionen por igual."""
        pairs = [
            ("Esq. Curva", "Esquinas Redondeadas"),
            ("Corazon B", "Corazon Borde"),
            ("Geom. 10", "Geometrico 10"),
            ("Diag. 13R", "Diagonal 13R"),
            ("Diag. 13L", "Diagonal 13L"),
        ]
        for short_name, legacy_name in pairs:
            res1 = eval_shapes_lib_node(self.context, forma=short_name)
            res2 = eval_shapes_lib_node(self.context, forma=legacy_name)
            self.assertEqual(res1, res2, f"Discrepancia entre '{short_name}' y '{legacy_name}'")

    def test_shapes_by_category(self):
        """Verifica resolución de formas específicas de cada una de las 10 categorías."""
        samples = [
            ("Formas", "Esq. Curva"),
            ("Estrellas", "Estrella 5T"),
            ("Corazones", "Corazon B"),
            ("Brillos", "Brillo 3T"),
            ("Especiales", "Trebol"),
            ("Musica", "Nota 2T"),
            ("Sakura", "Sakura 4T"),
            ("Nieve", "Copo 1T"),
            ("Flores", "Flor 15T"),
            ("Geometria", "Geom. 10")
        ]
        for cat, shape_name in samples:
            with self.subTest(category=cat, shape=shape_name):
                res = eval_shapes_lib_node(self.context, categoria=cat, forma=shape_name)
                self.assertTrue(isinstance(res, str) and len(res) > 10)

    def test_graph_engine_shapes_lib_node_evaluation(self):
        shapes_node = {
            "id": 1,
            "type": "Shape/Shapes Library",
            "properties": {"categoria": "Formas", "forma": "Esq. Curva"},
            "inputs": []
        }
        graph_data = {"nodes": [shapes_node], "links": []}
        engine = GraphEngine(graph_data)
        res = engine.evaluate_data_node(1, {})
        self.assertTrue(isinstance(res, str) and res.startswith("m 20 0"))

    def test_shape_variable_invocations(self):
        """Verifica que se puedan invocar shapes vía sintaxis shape.nombre."""
        from node_engine import _eval_sys_var, FxContext
        from nodes.shape_nodes import shape_transform, shape_concentric_borders_node

        # 1. Direct variable sys var resolution
        res_corazon = _eval_sys_var("shape.corazon", self.context)
        self.assertTrue(isinstance(res_corazon, str) and res_corazon.startswith("m 50 25"))

        res_estrella = _eval_sys_var("shape.estrella_5t", self.context)
        self.assertTrue(isinstance(res_estrella, str) and res_estrella.startswith("m 33 29"))

        # 2. FxContext attribute access
        fx = FxContext(self.context)
        self.assertTrue(fx.shape.circulo.startswith("m 50 0"))
        self.assertTrue(fx.shape.corazon.startswith("m 50 25"))

        # 3. Direct use in shape_transform
        trans_res = shape_transform(self.context, drawing="shape.corazon", scale_x=2.0, scale_y=2.0)
        self.assertTrue(isinstance(trans_res, str) and len(trans_res) > 20 and trans_res.startswith("m "))

        # 4. Direct use in shape_concentric_borders_node
        borders_res = shape_concentric_borders_node(self.context, shape="shape.circulo", separation=5.0, loop_count=3)
        self.assertTrue(isinstance(borders_res[0], str) and len(borders_res[0]) > 20 and borders_res[0].startswith("m "))

        # 5. Graph evaluation in Shape Slicer
        slicer_graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Shape/Shape Slicer",
                    "properties": {
                        "shape": "shape.estrella_5t",
                        "modo": "Rejilla 1D/2D",
                        "cols": "2",
                        "rows": "2"
                    },
                    "inputs": []
                }
            ],
            "links": []
        }
        engine = GraphEngine(slicer_graph)
        slicer_res = engine.evaluate_data_node(1, self.context)
        self.assertTrue(isinstance(slicer_res, str) and slicer_res.startswith("m "))

        # 6. Clip / iClip in tag_master
        from nodes.tag_nodes import tag_master
        clip_res = tag_master(self.context, tag_type="clip", valor="shape.corazon")
        self.assertTrue(clip_res.startswith(r"\clip(m 50 25"))

        iclip_res = tag_master(self.context, tag_type="iclip", valor="shape.circulo")
        self.assertTrue(iclip_res.startswith(r"\iclip(m 50 0"))

        # 7. Text to Shape node
        from nodes.text_nodes import text_to_shape_node
        t2s_res = text_to_shape_node(self.context, text="shape.estrella_5t")
        self.assertTrue(t2s_res.startswith("m 33 29"))

if __name__ == "__main__":
    unittest.main()

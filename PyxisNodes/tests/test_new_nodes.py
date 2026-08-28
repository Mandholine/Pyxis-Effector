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

# test_new_nodes.py
"""Pruebas unitarias completas para los nuevos nodos dinámicos de Pyxis Node Engine v1.0.1."""

import unittest
import os
from node_engine import GraphEngine, _eval_num_expr
from font_vector_engine import FontVectorEngine
from clipper_engine import ClipperEngine

class TestNewNodes(unittest.TestCase):

    def setUp(self):
        from models import PyxisLine, PyxisUnit
        line = PyxisLine()
        line.text = "Pyxis"
        line.text_stripped = "Pyxis"
        unit = PyxisUnit()
        unit.i = 1
        unit.n = 4
        unit.text = "Pyxis"
        unit.text_stripped = "Pyxis"
        unit.line = line
        line.syls = [unit]

        self.context = {
            "fx_pos_x": 100,
            "fx_pos_y": 200,
            "line": line,
            "active_line": line,
            "active_unit": unit,
            "syl": unit
        }

    def test_font_vector_engine(self):
        shape = FontVectorEngine.text_to_shape("A", "Arial", 100)
        self.assertTrue(len(shape) > 0)
        self.assertTrue(shape.startswith("m ") or shape.startswith("m"))

    def test_clipper_engine_22_meshes(self):
        # Probar los 22 motores de malla en ClipperEngine
        for mesh in ClipperEngine.MESH_ENGINES:
            pieces = ClipperEngine.slice_grid("m 0 0 l 100 0 l 100 100 l 0 100", cols=2, rows=2, engine_mode=mesh)
            self.assertTrue(len(pieces) > 0, f"Engine {mesh} falló en cantidad de piezas")
            self.assertIn("code", pieces[0])
            self.assertIn("cx", pieces[0])

    def test_clipper_transform(self):
        res = ClipperEngine.transform_shape("m 0 0 l 100 0 l 100 100 l 0 100", mode="Escalar", factor=2.0)
        self.assertTrue("m " in res)

    def test_text_to_shape_node(self):
        from nodes.text_nodes import text_to_shape_node
        res = text_to_shape_node(self.context, text="Test", font_name="Arial")
        self.assertTrue(len(res) > 0)

    def test_text_transliterate_kana(self):
        from nodes.text_nodes import text_transliterate_kana
        res = text_transliterate_kana(self.context, text="sakura", mode="Romaji a Hiragana")
        self.assertEqual(res, "さくら")

    def test_bezier_node(self):
        from nodes.math_nodes import math_bezier_node
        res = math_bezier_node(self.context, p0="0,0", p1="50,100", p2="150,100", p3="200,0", t=0.5, mode="Cúbica 2D")
        self.assertTrue(res.startswith("\\pos("))

    def test_time_synchronized(self):
        from nodes.time_nodes import time_synchronized_extra_node
        res = time_synchronized_extra_node(self.context, progression_const=20, delay=250)
        self.assertTrue(isinstance(res, float))
        self.assertGreater(res, 0.0)

    def test_tag_oscillator(self):
        from nodes.tag_nodes import tag_oscillator_node
        res = tag_oscillator_node(self.context, step_ms=200, trans_ms=50, tags=r"\fscx140\fscy140,\fscx100\fscy100")
        self.assertTrue(res.startswith(r"\t("))

    def test_particles_node(self):
        from particle_nodes import particle_text_node
        res = particle_text_node(self.context, shape="m 0 0 l 100 0 l 100 100 l 0 100", density=10)
        self.assertIsNotNone(res)

        # Probar evaluación en GraphEngine multi-slot
        graph = {
            "nodes": [{"id": 1, "type": "Particles", "properties": {"shape": "m 0 0 l 100 0 l 100 100 l 0 100"}}],
            "links": []
        }
        engine = GraphEngine(graph)
        pos_tag = engine.evaluate_data_node(1, self.context, output_slot_index=0)
        self.assertIn(r"\pos(", pos_tag)

    def test_concentric_borders_node(self):
        from nodes.shape_nodes import shape_concentric_borders_node
        # Modo Hueco (borders)
        res = shape_concentric_borders_node(
            self.context, shape="m 0 0 l 100 0 l 100 100 l 0 100", separation=5, overlap=0.5, mode="Hueco (borders)", loop_count=3
        )
        self.assertIsNotNone(res)

    def test_img_to_shape_node(self):
        from PIL import Image, ImageDraw
        test_img_path = "test_node_img.png"
        img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 80, 80], fill=(255, 255, 255, 255))
        img.save(test_img_path)

        try:
            graph = {
                "nodes": [{
                    "id": 1,
                    "type": "IMG to Shape",
                    "properties": {
                        "image_path": test_img_path,
                        "modo": "Potrace",
                        "threshold": "128",
                        "tolerance": "1.0",
                        "out_scale": "1.0",
                        "anchor": "Center"
                    }
                }],
                "links": []
            }
            engine = GraphEngine(graph)
            shape_out = engine.evaluate_data_node(1, self.context, output_slot_index=0)
            width_out = engine.evaluate_data_node(1, self.context, output_slot_index=1)
            height_out = engine.evaluate_data_node(1, self.context, output_slot_index=2)

            self.assertTrue(len(shape_out) > 0)
            self.assertTrue(shape_out.startswith("m ") or shape_out.startswith("m"))
            self.assertGreater(float(width_out), 0.0)
            self.assertGreater(float(height_out), 0.0)
        finally:
            if os.path.exists(test_img_path):
                os.remove(test_img_path)

    def test_inverted_webp_generation(self):
        from PIL import Image, ImageDraw
        from img_tracer_engine import _get_or_create_inverted_webp
        test_img_path = "test_inv_source.png"
        img = Image.new("RGBA", (50, 50), (255, 0, 0, 255)) # Red image
        img.save(test_img_path)

        try:
            inv_webp = _get_or_create_inverted_webp(test_img_path)
            self.assertTrue(os.path.isfile(inv_webp))
            self.assertTrue(inv_webp.endswith(".webp"))
            self.assertGreater(os.path.getsize(inv_webp), 0)
        finally:
            if os.path.exists(test_img_path):
                os.remove(test_img_path)

    def test_img_to_shape_empty_inputs_and_size_matching(self):
        from PIL import Image, ImageDraw
        from img_tracer_engine import _get_or_create_inverted_webp
        test_img_path = "test_empty_props.png"
        img = Image.new("RGBA", (120, 80), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 100, 60], fill=(0, 0, 0, 255))
        img.save(test_img_path)

        try:
            # 1. Verify inverted webp dimension matching
            inv_webp = _get_or_create_inverted_webp(test_img_path)
            check_img = Image.open(inv_webp)
            self.assertEqual(check_img.size, (120, 80))
            check_img.close()

            # 2. Test graph evaluation with empty properties/inputs (testing default fallbacks)
            graph = {
                "nodes": [{
                    "id": 1,
                    "type": "IMG to Shape",
                    "properties": {
                        "image_path": test_img_path,
                        "threshold": "",
                        "tolerance": "   ",
                        "alphamax": "",
                        "opttoler": "",
                        "out_scale": "",
                        "out_w": "",
                        "out_h": "",
                        "offset_x": "",
                        "offset_y": "",
                        "img_scale": ""
                    }
                }],
                "links": []
            }
            engine = GraphEngine(graph)
            shape_out = engine.evaluate_data_node(1, self.context, output_slot_index=0)
            width_out = float(engine.evaluate_data_node(1, self.context, output_slot_index=1))
            height_out = float(engine.evaluate_data_node(1, self.context, output_slot_index=2))

            self.assertTrue(len(shape_out) > 0)
            self.assertEqual(width_out, 120.0)
            self.assertEqual(height_out, 80.0)
        finally:
            if os.path.exists(test_img_path):
                os.remove(test_img_path)

    def test_gif_to_shape_evaluation(self):
        from PIL import Image, ImageDraw
        test_gif_path = "test_animation.gif"
        frames = []
        for i in range(3):
            f = Image.new("RGBA", (100, 100), (255, 255, 255, 255))
            d = ImageDraw.Draw(f)
            d.rectangle([10 + i * 10, 10, 50 + i * 10, 50], fill=(0, 0, 0, 255))
            frames.append(f)
        frames[0].save(test_gif_path, save_all=True, append_images=frames[1:], duration=100, loop=0)

        try:
            # Test evaluating GIF for frame j = 2
            graph = {
                "nodes": [{
                    "id": 1,
                    "type": "IMG to Shape",
                    "properties": {
                        "image_path": test_gif_path,
                        "frame_idx": "2"
                    }
                }],
                "links": []
            }
            engine = GraphEngine(graph)

            # Evaluate with context containing j=2
            context_j2 = dict(self.context)
            context_j2["j"] = 2

            shape_out_j2 = engine.evaluate_data_node(1, context_j2, output_slot_index=0)
            shapes_array = engine.evaluate_data_node(1, context_j2, output_slot_index=4)
            total_frames = engine.evaluate_data_node(1, context_j2, output_slot_index=5)

            self.assertTrue(len(shape_out_j2) > 0)
            self.assertEqual(total_frames, "3")
            self.assertIn(",", shapes_array)
            shapes_split = shapes_array.split(",")
            self.assertEqual(len(shapes_split), 3)
        finally:
            if os.path.exists(test_gif_path):
                os.remove(test_gif_path)

    def test_sys_var_module_reading(self):
        # Graph testing Sys Var node reading 'module' directly from context
        test_ctx = self.context.copy()
        test_ctx["module"] = 0.75
        test_ctx["m"] = 0.75
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Sys Var",
                    "properties": { "var_name": "module" }
                },
                {
                    "id": 2,
                    "type": "Sys Var",
                    "properties": { "var_name": "fx.module" }
                }
            ]
        }
        engine = GraphEngine(graph)
        res1 = engine.evaluate_data_node(1, test_ctx, output_slot_index=0)
        res2 = engine.evaluate_data_node(2, test_ctx, output_slot_index=0)
        self.assertEqual(float(res1), 0.75)
        self.assertEqual(float(res2), 0.75)

    def test_bucles_module_master_node(self):
        # Test universal Module node in Bucles category with custom inputs (i=2, N=5, m=0.5)
        graph = {
            "nodes": [
                { "id": 1, "type": "String", "properties": { "valor": "2" } },
                { "id": 2, "type": "String", "properties": { "valor": "5" } },
                { "id": 3, "type": "String", "properties": { "valor": "0.5" } },
                {
                    "id": 4,
                    "type": "Loops/Module",
                    "properties": { "iter": "i", "total": "N", "sub_m": "0" },
                    "inputs": [
                        { "name": "Iterator (i)", "link": 10 },
                        { "name": "Total (N)", "link": 11 },
                        { "name": "Sub-step (m)", "link": 12 }
                    ]
                }
            ],
            "links": [
                [10, 1, 0, 4, 0, "string"],
                [11, 2, 0, 4, 1, "string"],
                [12, 3, 0, 4, 2, "string"]
            ]
        }
        engine = GraphEngine(graph)
        # (2 - 1 + 0.5) / (5 + 0.5 - 1) = 1.5 / 4.5 = 1/3 = 0.3333 (redondeado a 4 decimales limpios)
        res = engine.evaluate_data_node(4, self.context, output_slot_index=0)
        self.assertEqual(res, "0.3333")

    def test_bucles_module_simple_and_n1(self):
        # Test Module node as simple normalizer (i=3, N=5, m=0 => 0.5) and when N=1 => returns m
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Module",
                    "properties": { "iter": "3", "total": "5", "sub_m": "0" }
                },
                {
                    "id": 2,
                    "type": "Loops/Module",
                    "properties": { "iter": "1", "total": "1", "sub_m": "0.42" }
                }
            ]
        }
        engine = GraphEngine(graph)
        res1 = engine.evaluate_data_node(1, self.context, output_slot_index=0)
        res2 = engine.evaluate_data_node(2, self.context, output_slot_index=0)
        self.assertEqual(float(res1), 0.5)
        self.assertEqual(float(res2), 0.42)

    def test_img_to_shape_gif_support(self):
        from PIL import Image, ImageDraw
        test_gif_path = "test_anim.gif"
        frames = []
        for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
            f = Image.new("RGBA", (40, 40), (255, 255, 255, 255))
            d = ImageDraw.Draw(f)
            d.rectangle([10, 10, 30, 30], fill=color)
            frames.append(f)
        frames[0].save(test_gif_path, save_all=True, append_images=frames[1:], duration=100, loop=0)

        try:
            from main import PyxisAPI
            api = PyxisAPI("dummy.ass", "dummy.json", "dummy.json")
            res = api.trace_image_api({"image_path": test_gif_path, "frame_idx": "j", "preview_frame": 2})
            self.assertEqual(res.get("total_frames"), 3)
            self.assertEqual(res.get("frame_index"), 2)
            self.assertTrue("shapes_array" in res)
            self.assertIn(",", res["shapes_array"])

            graph = {
                "nodes": [{
                    "id": 1,
                    "type": "IMG to Shape",
                    "properties": { "image_path": test_gif_path, "frame_idx": "1" }
                }]
            }
            engine = GraphEngine(graph)
            res_shape = engine.evaluate_data_node(1, self.context, output_slot_index=0)
            self.assertTrue(len(res_shape) > 0)
        finally:
            if os.path.exists(test_gif_path):
                os.remove(test_gif_path)

    def test_img_to_pixels_preview_and_gif(self):
        from main import PyxisAPI
        from PIL import Image, ImageDraw
        test_gif_path = "test_pixels_anim.gif"
        frames = []
        for i in range(3):
            f = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
            d = ImageDraw.Draw(f)
            d.rectangle([5 + i * 2, 5 + i * 2, 20 + i * 2, 20 + i * 2], fill=(255, 0, 0, 255))
            frames.append(f)
        frames[0].save(test_gif_path, save_all=True, append_images=frames[1:], duration=100, loop=0)

        try:
            api = PyxisAPI("dummy.ass", "dummy_res.json", "dummy_session.json")
            res = api.sample_pixels_api({"image_path": test_gif_path, "frame": "j", "preview_frame": 2, "step": 2})
            self.assertEqual(res.get("total_frames"), 3)
            self.assertEqual(res.get("frame_index"), 2)
            self.assertTrue(len(res.get("pixels_points", [])) > 0)

            graph = {
                "nodes": [{
                    "id": 1,
                    "type": "Functions/IMG to Pixels",
                    "properties": { "image_path": test_gif_path, "frame": "1", "step": "2" }
                }]
            }
            engine = GraphEngine(graph)
            res_text = engine.evaluate_data_node(1, self.context, output_slot_index=0)
            res_pixels_arr = engine.evaluate_data_node(1, self.context, output_slot_index=6)
            self.assertTrue(len(res_text) > 0)
            self.assertTrue(len(res_pixels_arr) > 0)
        finally:
            if os.path.exists(test_gif_path):
                os.remove(test_gif_path)


if __name__ == "__main__":
    unittest.main()



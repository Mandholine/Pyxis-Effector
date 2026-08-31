# Pyxis Effector - Test Suite for Shape Walker (Recorredor) Node
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc

import pytest
import math
from nodes.shape_nodes import (
    parse_assdraw_segments,
    _eval_bezier_pt,
    _eval_bezier_tangent,
    de_casteljau_split,
    shape_walker_core,
    shape_walker_node
)
from node_engine import GraphEngine


class TestShapeWalkerCore:
    def test_parse_segments_line(self):
        shape = "m 0 0 l 100 0 l 100 50"
        contours = parse_assdraw_segments(shape)
        assert len(contours) == 1
        assert contours[0]['start'] == (0.0, 0.0)
        assert len(contours[0]['segments']) == 2
        assert contours[0]['segments'][0]['type'] == 'l'
        assert contours[0]['segments'][0]['p0'] == (0.0, 0.0)
        assert contours[0]['segments'][0]['p1'] == (100.0, 0.0)

    def test_parse_segments_bezier(self):
        shape = "m 0 0 b 25 50 75 50 100 0"
        contours = parse_assdraw_segments(shape)
        assert len(contours) == 1
        assert len(contours[0]['segments']) == 1
        b_seg = contours[0]['segments'][0]
        assert b_seg['type'] == 'b'
        assert b_seg['p0'] == (0.0, 0.0)
        assert b_seg['p1'] == (25.0, 50.0)
        assert b_seg['p2'] == (75.0, 50.0)
        assert b_seg['p3'] == (100.0, 0.0)

    def test_line_cut_half(self):
        shape = "m 0 0 l 100 0"
        cut_shp, tx, ty, angle, cut_len, total_len = shape_walker_core(shape, progress=0.5, start_t=0.0)
        assert "m 0 0" in cut_shp
        assert "l 50 0" in cut_shp
        assert pytest.approx(tx, 0.01) == 50.0
        assert pytest.approx(ty, 0.01) == 0.0
        assert pytest.approx(angle, 0.01) == 0.0
        assert pytest.approx(cut_len, 0.01) == 50.0
        assert pytest.approx(total_len, 0.01) == 100.0

    def test_line_cut_window_trim(self):
        shape = "m 0 0 l 100 0"
        cut_shp, tx, ty, angle, cut_len, total_len = shape_walker_core(shape, progress=0.7, start_t=0.2)
        assert "m 20 0" in cut_shp
        assert "l 70 0" in cut_shp
        assert pytest.approx(tx, 0.01) == 70.0
        assert pytest.approx(ty, 0.01) == 0.0
        assert pytest.approx(cut_len, 0.01) == 50.0

    def test_bezier_cut_symmetric(self):
        shape = "m 0 0 b 0 100 100 100 100 0"
        cut_shp, tx, ty, angle, cut_len, total_len = shape_walker_core(shape, progress=0.5, start_t=0.0)
        assert pytest.approx(tx, 0.5) == 50.0
        assert pytest.approx(ty, 0.5) == 75.0
        assert pytest.approx(angle, 1.0) == 0.0 or pytest.approx(angle, 1.0) == 360.0

    def test_multi_contour_global_mode(self):
        shape = "m 0 0 l 100 0 m 0 50 l 100 50"
        cut_shp, tx, ty, angle, cut_len, total_len = shape_walker_core(shape, progress=0.25, start_t=0.0, mode="Global")
        assert "m 0 0 l 50 0" in cut_shp
        assert "m 0 50" not in cut_shp
        assert pytest.approx(cut_len, 0.01) == 50.0
        assert pytest.approx(total_len, 0.01) == 200.0

        cut_shp2, tx2, ty2, angle2, cut_len2, _ = shape_walker_core(shape, progress=0.75, start_t=0.0, mode="Global")
        assert "m 0 0 l 100 0" in cut_shp2
        assert "m 0 50 l 50 50" in cut_shp2
        assert pytest.approx(cut_len2, 0.01) == 150.0
        assert pytest.approx(tx2, 0.01) == 50.0
        assert pytest.approx(ty2, 0.01) == 50.0

    def test_multi_contour_parallel_mode(self):
        shape = "m 0 0 l 100 0 m 0 50 l 100 50"
        cut_shp, tx, ty, angle, cut_len, total_len = shape_walker_core(shape, progress=0.5, start_t=0.0, mode="Por Contorno")
        assert "m 0 0 l 50 0" in cut_shp
        assert "m 0 50 l 50 50" in cut_shp
        assert pytest.approx(cut_len, 0.01) == 100.0

    def test_invert_cut(self):
        shape = "m 0 0 l 100 0"
        cut_shp, tx, ty, angle, cut_len, total_len = shape_walker_core(shape, progress=0.5, start_t=0.0, invert=True)
        assert "m 50 0" in cut_shp
        assert "l 100 0" in cut_shp
        assert pytest.approx(cut_len, 0.01) == 50.0

    def test_preset_shape_cut(self):
        # Preset circle cut
        res_shp, pos_str, angle, cut_len, tx, ty = shape_walker_node(
            context={},
            shape="shape.circulo",
            progress=0.5,
            start_t=0.0
        )
        assert res_shp.startswith("m ")
        assert "b " in res_shp
        assert cut_len > 0.0
        assert pos_str.startswith("\\pos(")

    def test_edge_cases(self):
        # Empty shape
        shp, pos, ang, clen, tx, ty = shape_walker_node(context={}, shape="", progress=0.5)
        assert shp == ""
        assert pos == ""

        # Zero or invalid progress
        shp2, _, _, _, _, _ = shape_walker_node(context={}, shape="m 0 0 l 100 0", progress=0.0, start_t=0.0)
        assert shp2 == ""


class TestShapeWalkerNodeEvaluation:
    def test_shape_walker_node_slots(self):
        node = {
            'id': 'walker_node_1',
            'type': 'Shape/Shape Walker',
            'properties': {
                'shape': 'm 0 0 l 200 0',
                'progress': '0.5',
                'start_t': '0.0',
                'modo': 'Global (Continuo)',
                'invert': '0'
            },
            'inputs': []
        }
        engine = GraphEngine({"nodes": [node]})
        context = {
            'active_unit': None,
            'line': None
        }

        shp_out = engine.evaluate_data_node('walker_node_1', context, output_slot_index=0)
        assert "m 0 0" in shp_out
        assert "l 100 0" in shp_out

        pos_tag = engine.evaluate_data_node('walker_node_1', context, output_slot_index=1)
        assert "\\pos(100" in pos_tag

        angle_tag = engine.evaluate_data_node('walker_node_1', context, output_slot_index=2)
        assert "\\frz(0" in angle_tag

        len_val = engine.evaluate_data_node('walker_node_1', context, output_slot_index=3)
        assert float(len_val) == pytest.approx(100.0, 0.01)

        tip_x = engine.evaluate_data_node('walker_node_1', context, output_slot_index=4)
        assert float(tip_x) == pytest.approx(100.0, 0.01)

        tip_y = engine.evaluate_data_node('walker_node_1', context, output_slot_index=5)
        assert float(tip_y) == pytest.approx(0.0, 0.01)

    def test_shape_walker_default_from_active_unit(self):
        class DummyUnit:
            def __init__(self, text="O"):
                self.text = text
                self.text_stripped = text
                self.height = 40

        unit = DummyUnit("O")
        node = {
            'id': 'walker_1',
            'type': 'Shape/Shape Walker',
            'properties': {
                'shape': '',
                'progress': '0.5',
                'start_t': '0.0',
                'modo': 'Global (Continuo)',
                'invert': '0'
            },
            'inputs': []
        }
        engine = GraphEngine({"nodes": [node]})
        context = {
            'active_unit': unit,
            'line': None
        }

        shp_out = engine.evaluate_data_node('walker_1', context, output_slot_index=0)
        assert shp_out.startswith("m ")
        assert len(shp_out) > 5

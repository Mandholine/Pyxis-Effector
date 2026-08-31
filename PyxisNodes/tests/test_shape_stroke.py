import unittest
from clipper_engine import ClipperEngine
from nodes.shape_nodes import shape_stroke_node, shape_walker_node
from node_engine import GraphEngine
from models import PyxisLine, PyxisUnit, StyleRef


class TestShapeStroke(unittest.TestCase):

    def test_clipper_stroke_straight_line_flat(self):
        line = "m 0 0 l 100 0"
        res = ClipperEngine.stroke_shape(line, width=10.0, cap_mode="Flat")
        self.true = self.assertTrue(res.startswith("m "))
        self.assertIn("5.0", res)
        self.assertIn("-5.0", res)
        self.assertIn("100.0", res)

    def test_clipper_stroke_straight_line_round(self):
        line = "m 0 0 l 100 0"
        res = ClipperEngine.stroke_shape(line, width=10.0, cap_mode="Round")
        self.assertTrue(res.startswith("m "))
        contours = ClipperEngine.parse_assdraw(res)
        self.assertEqual(len(contours), 1)
        min_x, min_y, max_x, max_y, cx, cy, w, h = ClipperEngine.get_bbox(contours)
        self.assertAlmostEqual(w, 110.0, delta=1.0)
        self.assertAlmostEqual(h, 10.0, delta=1.0)

    def test_clipper_stroke_bezier_curve(self):
        bezier = "m 0 0 b 0 100 100 100 100 0"
        res = ClipperEngine.stroke_shape(bezier, width=6.0, join_mode="Round", cap_mode="Round")
        self.assertTrue(res.startswith("m "))
        contours = ClipperEngine.parse_assdraw(res)
        self.assertEqual(len(contours), 1)
        min_x, min_y, max_x, max_y, cx, cy, w, h = ClipperEngine.get_bbox(contours)
        self.assertGreater(w, 90.0)
        self.assertGreater(h, 60.0)

    def test_clipper_stroke_join_modes(self):
        corner = "m 0 0 l 50 50 l 100 0"
        res_round = ClipperEngine.stroke_shape(corner, width=8.0, join_mode="Round")
        res_miter = ClipperEngine.stroke_shape(corner, width=8.0, join_mode="Miter", miter_limit=3.0)
        res_bevel = ClipperEngine.stroke_shape(corner, width=8.0, join_mode="Bevel")
        self.assertTrue(res_round.startswith("m "))
        self.assertTrue(res_miter.startswith("m "))
        self.assertTrue(res_bevel.startswith("m "))

    def test_shape_stroke_node_direct_call(self):
        context = {'j': 2, 'maxj': 4}
        res = shape_stroke_node(context, shape="m 0 0 l 100 0", width="2.0 * j", join_mode="Round", cap_mode="Flat")
        self.assertTrue(res.startswith("m "))
        self.assertIn("2.0", res)
        self.assertIn("-2.0", res)

    def test_shape_stroke_node_fallback_text(self):
        style = StyleRef()
        style.fontname = "Arial"
        style.fontsize = 40
        line = PyxisLine()
        line.styleref = style
        unit = PyxisUnit()
        unit.text = "L"
        unit.text_stripped = "L"
        unit.line = line
        unit.styleref = style

        context = {'active_unit': unit, 'line': line, 'syl': unit}
        res = shape_stroke_node(context, shape="", width=4.0)
        self.assertTrue(res.startswith("m "))
        self.assertGreater(len(res), 20)

    def test_graph_engine_shape_stroke_evaluation(self):
        graph = {
            'nodes': [
                {'id': 1, 'type': 'Shape/Shape Stroke', 'properties': {'shape': 'm 0 0 l 100 0', 'width': '8.0', 'join_mode': 'Round', 'cap_mode': 'Round'}, 'inputs': []}
            ],
            'links': []
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        shp_out = engine.evaluate_data_node(1, {}, output_slot_index=0)
        width_out = engine.evaluate_data_node(1, {}, output_slot_index=1)
        self.assertTrue(shp_out.startswith("m "))
        self.assertEqual(width_out, "8.0")

    def test_graph_engine_walker_into_stroke(self):
        graph = {
            'nodes': [
                {'id': 1, 'type': 'Loops/Main Loop', 'properties': {'iterador': 'syl'}, 'inputs': []},
                {'id': 2, 'type': 'Shape/Shape Walker', 'properties': {'shape': 'm 0 0 l 200 0', 'progress': '0.5', 'start_t': '0.0'}, 'inputs': [{'link': None}]},
                {'id': 3, 'type': 'Shape/Shape Stroke', 'properties': {'width': '6.0', 'join_mode': 'Round', 'cap_mode': 'Round'}, 'inputs': [{'link': 1}]},
                {'id': 4, 'type': 'System/Output', 'properties': {'apply_to': 'All Lines', 'origin_align': 5}, 'inputs': [{'link': 2}, None, None, None, None, {'link': 3}]}
            ],
            'links': [
                [1, 2, 0, 3, 0, 'data'],
                [2, 1, 0, 4, 0, 'bucle'],
                [3, 3, 0, 4, 5, 'data']
            ]
        }
        engine = GraphEngine(graph, 1280, 720, 41.7)
        raw_line = 'Dialogue: 0,0:00:00.00,0:00:00.20,Default,,0,0,0,,{\\k20}A'
        styles = {'Default': {'fontname': 'Arial', 'fontsize': 40}}
        engine.process_single([{'raw': raw_line}], styles)

        self.assertEqual(len(engine.all_generated_lines), 1)
        gen_line = engine.all_generated_lines[0]['text']
        self.assertIn("{\\an5\\p1", gen_line)
        self.assertIn("m ", gen_line)
        self.assertNotIn("[Err", gen_line)

    def test_clipper_stroke_closed_triangle_hollow(self):
        """Verifica que un triángulo 100% cerrado produzca un marco hueco con dos contornos (exterior e interior)."""
        tri = "m 50 0 l 0 86 l 100 86 l 50 0"
        res = ClipperEngine.stroke_shape(tri, width=4.0)
        contours = ClipperEngine.parse_assdraw(res)
        # Debe tener 2 contornos: el exterior y el recorte interior
        self.assertEqual(len(contours), 2)
        # Debe contener dos comandos 'm' en la cadena ASSDraw
        self.assertEqual(res.count("m "), 2)


if __name__ == '__main__':
    unittest.main()

# Pyxis Effector - Plugin for Aegisub
import unittest
from node_engine import GraphEngine


class TestBezierCurveNode(unittest.TestCase):
    def test_bezier_curve_cubic_2d(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Cubic 2D",
                "p0": "0,0",
                "p1": "0,100",
                "p2": "100,100",
                "p3": "100,0",
                "t": "0.5",
                "subdivs": "100"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        x = engine.evaluate_data_node(1, context={}, output_slot_index=1)
        y = engine.evaluate_data_node(1, context={}, output_slot_index=2)
        tan = engine.evaluate_data_node(1, context={}, output_slot_index=3)
        norm = engine.evaluate_data_node(1, context={}, output_slot_index=4)
        spline = engine.evaluate_data_node(1, context={}, output_slot_index=5)

        self.assertTrue(pos.startswith("\\pos("))
        self.assertEqual(x, "50")
        self.assertEqual(y, "75")
        self.assertTrue(spline.startswith("m 0.0 0.0 b 0.0 100.0 100.0 100.0 100.0 0.0"))
        self.assertAlmostEqual(float(tan) % 360.0, 0.0, delta=0.5)
        self.assertAlmostEqual(float(norm), 90.0, delta=0.5)

    def test_bezier_curve_canonical_lowercase_modes(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "cubic_2d",
                "p0": "0,0",
                "p1": "0,100",
                "p2": "100,100",
                "p3": "100,0",
                "t": "0.5",
                "subdivs": "100"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        self.assertTrue(pos.startswith("\\pos("))

        node_quad = {
            "id": 2,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "quadratic_2d",
                "p0": "0,0",
                "p1": "50,100",
                "p2": "100,0",
                "t": "0.5"
            }
        }
        engine2 = GraphEngine({"nodes": [node_quad], "links": []})
        pos_quad = engine2.evaluate_data_node(2, context={}, output_slot_index=0)
        self.assertEqual(pos_quad, "\\pos(50,50)")

        node_traj = {
            "id": 3,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "trajectory",
                "traj_mode": "free_wander",
                "dist_range": "50,120",
                "seed": "1",
                "loops": "4",
                "t": "0.5"
            }
        }
        engine3 = GraphEngine({"nodes": [node_traj], "links": []})
        pos_traj = engine3.evaluate_data_node(3, context={}, output_slot_index=0)
        self.assertTrue(pos_traj.startswith("\\pos("))

    def test_bezier_curve_quadratic_2d(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Quadratic 2D",
                "p0": "0,0",
                "p1": "50,100",
                "p2": "100,0",
                "t": "0.5",
                "subdivs": "100"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        x = engine.evaluate_data_node(1, context={}, output_slot_index=1)
        y = engine.evaluate_data_node(1, context={}, output_slot_index=2)
        spline = engine.evaluate_data_node(1, context={}, output_slot_index=5)

        self.assertEqual(pos, "\\pos(50,50)")
        self.assertEqual(x, "50")
        self.assertEqual(y, "50")
        self.assertTrue(spline.startswith("m 0.0 0.0 b 33.33 66.67 66.67 66.67 100.0 0.0"))

    def test_bezier_curve_n_degree(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "N-Degree",
                "points": "0 0, 0 100, 50 100, 100 100, 100 0",
                "t": "0.5",
                "subdivs": "100"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        x = engine.evaluate_data_node(1, context={}, output_slot_index=1)
        y = engine.evaluate_data_node(1, context={}, output_slot_index=2)
        spline = engine.evaluate_data_node(1, context={}, output_slot_index=5)

        self.assertTrue(pos.startswith("\\pos("))
        self.assertEqual(x, "50")
        self.assertTrue(spline.startswith("m 0.0 0.0"))

    def test_bezier_curve_subdivide(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Subdivide",
                "p0": "0,0",
                "p1": "0,100",
                "p2": "100,100",
                "p3": "100,0",
                "t": "0.5"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        x = engine.evaluate_data_node(1, context={}, output_slot_index=1)
        y = engine.evaluate_data_node(1, context={}, output_slot_index=2)
        spline_l = engine.evaluate_data_node(1, context={}, output_slot_index=6)
        spline_r = engine.evaluate_data_node(1, context={}, output_slot_index=7)

        self.assertEqual(pos, "\\pos(50,75)")
        self.assertEqual(x, "50")
        self.assertEqual(y, "75")
        self.assertTrue(spline_l.startswith("m 0.0 0.0 b"))
        self.assertTrue(spline_r.startswith("m 50.0 75.0 b"))

    def test_bezier_curve_trajectory_free_wander(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Trajectory",
                "traj_mode": "Free Wander",
                "origin": "100,200",
                "dist_range": "50,120",
                "seed": "1",
                "loops": "8",
                "t": "0.0"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        x_val = engine.evaluate_data_node(1, context={}, output_slot_index=1)
        y_val = engine.evaluate_data_node(1, context={}, output_slot_index=2)
        tan = engine.evaluate_data_node(1, context={}, output_slot_index=3)
        spline = engine.evaluate_data_node(1, context={}, output_slot_index=5)

        self.assertEqual(pos, r"\pos(100,200)")
        self.assertEqual(x_val, "100")
        self.assertEqual(y_val, "200")
        self.assertTrue(spline.startswith("m 100.0 200.0 b"))
        self.assertNotIn("[Err", tan)

    def test_bezier_curve_trajectory_bounded(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Trajectory",
                "traj_mode": "Bounded",
                "origin": "50,50",
                "dist_range": "20,40",
                "seed": "10",
                "loops": "4",
                "t": "0.0"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        spline = engine.evaluate_data_node(1, context={}, output_slot_index=5)

        self.assertEqual(pos, r"\pos(50,50)")
        self.assertTrue(spline.startswith("m 50.0 50.0 b"))

    def test_bezier_curve_trajectory_closed_loop(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Trajectory",
                "traj_mode": "Closed Loop",
                "origin": "300,400",
                "dist_range": "50,100",
                "seed": "5",
                "loops": "6",
                "t": "0.0"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos_start = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        node["properties"]["t"] = "1.0"
        pos_end = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        spline = engine.evaluate_data_node(1, context={}, output_slot_index=5)

        # In Closed Loop mode, t=0.0 and t=1.0 reach the exact same point
        self.assertEqual(pos_start, pos_end)
        self.assertTrue(spline.startswith("m "))

    def test_bezier_curve_trajectory(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Trajectory",
                "dist_range": "50,120",
                "seed": "1",
                "loops": "8",
                "t": "0.5"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        x_val = engine.evaluate_data_node(1, context={}, output_slot_index=1)
        y_val = engine.evaluate_data_node(1, context={}, output_slot_index=2)
        spline = engine.evaluate_data_node(1, context={}, output_slot_index=5)

        self.assertTrue(pos.startswith(r"\pos("))
        self.assertTrue(float(x_val) != 0.0 or float(y_val) != 0.0)
        self.assertTrue(spline.startswith("m 0.0 0.0 b") or spline.startswith("m 0 0 b"))

    def test_bezier_curve_assdraw_path(self):
        shp_node = {
            "id": 1,
            "type": "Library",
            "properties": {"forma": "Circulo"}
        }
        b_node = {
            "id": 2,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Shape Contour",
                "t": "0.25",
                "subdivs": "100"
            },
            "inputs": [{"name": "Shape", "link": 10}]
        }
        link = [10, 1, 0, 2, 0, "shape"]
        engine = GraphEngine({"nodes": [shp_node, b_node], "links": [link]})

        pos = engine.evaluate_data_node(2, context={}, output_slot_index=0)
        x = engine.evaluate_data_node(2, context={}, output_slot_index=1)
        y = engine.evaluate_data_node(2, context={}, output_slot_index=2)
        tan = engine.evaluate_data_node(2, context={}, output_slot_index=3)
        norm = engine.evaluate_data_node(2, context={}, output_slot_index=4)
        spline = engine.evaluate_data_node(2, context={}, output_slot_index=5)

        self.assertEqual(pos, "\\pos(0,50)")
        self.assertEqual(x, "0")
        self.assertEqual(y, "50")
        self.assertNotIn("[Err", pos)
        self.assertAlmostEqual(float(norm), (float(tan) + 90.0) % 360.0, delta=0.1)
        self.assertTrue(spline.startswith("m 50 0 b"))

    def test_bezier_curve_constant_speed(self):
        line_node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Constant Speed",
                "shape": "m 0 0 l 100 0 l 100 100",
                "t": "0.5",
                "subdivs": "100"
            }
        }
        engine = GraphEngine({"nodes": [line_node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        x = engine.evaluate_data_node(1, context={}, output_slot_index=1)
        y = engine.evaluate_data_node(1, context={}, output_slot_index=2)
        tan = engine.evaluate_data_node(1, context={}, output_slot_index=3)

        self.assertEqual(pos, "\\pos(100,0)")
        self.assertEqual(x, "100")
        self.assertEqual(y, "0")
        self.assertAlmostEqual(float(tan), 0.0, delta=0.1)

    def test_bezier_curve_tangent_and_normal(self):
        line_node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Shape Contour",
                "shape": "m 0 0 l 0 200",
                "t": "0.5",
                "subdivs": "100"
            }
        }
        engine = GraphEngine({"nodes": [line_node], "links": []})
        tan = engine.evaluate_data_node(1, context={}, output_slot_index=3)
        norm = engine.evaluate_data_node(1, context={}, output_slot_index=4)

    def test_bezier_curve_cubic_2d_with_origin(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Cubic 2D",
                "origin": "100,200",
                "p0": "0,0",
                "p1": "0,100",
                "p2": "100,100",
                "p3": "100,0",
                "t": "0.5",
                "subdivs": "100"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        x = engine.evaluate_data_node(1, context={}, output_slot_index=1)
        y = engine.evaluate_data_node(1, context={}, output_slot_index=2)
        tan = engine.evaluate_data_node(1, context={}, output_slot_index=3)
        spline = engine.evaluate_data_node(1, context={}, output_slot_index=5)

        # Without origin (50, 75). With origin (100, 200) -> (150, 275)
        self.assertEqual(pos, r"\pos(150,275)")
        self.assertEqual(x, "150")
        self.assertEqual(y, "275")
        self.assertTrue(spline.startswith("m 100.0 200.0 b"))
        self.assertAlmostEqual(float(tan) % 360.0, 0.0, delta=0.5)

    def test_bezier_curve_quadratic_2d_with_origin(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Quadratic 2D",
                "origin": "50,50",
                "p0": "0,0",
                "p1": "50,100",
                "p2": "100,0",
                "t": "0.5",
                "subdivs": "100"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        x = engine.evaluate_data_node(1, context={}, output_slot_index=1)
        y = engine.evaluate_data_node(1, context={}, output_slot_index=2)

        # Without origin (50, 50). With origin (50, 50) -> (100, 100)
        self.assertEqual(pos, r"\pos(100,100)")
        self.assertEqual(x, "100")
        self.assertEqual(y, "100")

    def test_bezier_curve_shape_contour_with_origin(self):
        node = {
            "id": 1,
            "type": "Functions/Bezier Curve",
            "properties": {
                "mode": "Shape Contour",
                "origin": "50,50",
                "shape": "m 0 0 l 100 0 l 100 100",
                "t": "0.5",
                "subdivs": "100"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        x = engine.evaluate_data_node(1, context={}, output_slot_index=1)
        y = engine.evaluate_data_node(1, context={}, output_slot_index=2)

        # Without origin (100, 0). With origin (50, 50) -> (150, 50)
        self.assertEqual(pos, r"\pos(150,50)")
        self.assertEqual(x, "150")
        self.assertEqual(y, "50")


if __name__ == "__main__":
    unittest.main()
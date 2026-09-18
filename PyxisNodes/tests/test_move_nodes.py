import unittest
from nodes.tag_nodes import move_tag_node
from nodes.text_nodes import move_text_node
from string_evaluator import eval_python_expr

class TestMoveNodes(unittest.TestCase):
    def test_move_tag_trajectory(self):
        res = move_tag_node(mode="Trajectory", shape="m 0 0 l 100 50", t1=0, t2=500, accel=1.0, step_px=100.0, anchor="origin")
        self.assertTrue(res.startswith(r"\an7\q2\pos(0.00,0.00)"))
        self.assertIn(r"\t(0,500,\fscx100.00\fscy50.00)", res)
        self.assertIn(r"\p1}m 0 0 m 100 100 {\p0\r", res)

    def test_move_tag_trajectory_bezier_resampling(self):
        res = move_tag_node(mode="Trajectory", shape="m 0 0 b 50 0 50 100 100 100", t1=0, t2=600, step_px=25.0, anchor="origin")
        self.assertTrue(res.startswith(r"\an7\q2\pos(0.00,0.00)"))
        self.assertIn(r"\t(", res)
        self.assertIn(r"\fscx100.00\fscy100.00", res)
        self.assertIn(r"\p1}m 0 0 m 100 100 {\p0\r", res)

    def test_move_tag_waypoints(self):
        res = move_tag_node(mode="Waypoints", points="0,0; 50,50; 100,0", t1=0, t2=600, accel=1.0, step_px=50.0, anchor="origin")
        self.assertTrue(res.startswith(r"\an7\q2\pos(0.00,0.00)"))
        self.assertIn(r"\t(0,300,\fscx50.00\fscy50.00)", res)
        self.assertIn(r"\t(300,600,\fscx100.00\fscy0.00)", res)

    def test_move_tag_waypoints_list_input(self):
        pts = [(0, 0), (50, 50), (100, 0)]
        res = move_tag_node(mode="Waypoints", points=pts, t1=0, t2=600, accel=1.0, step_px=50.0, anchor="origin")
        self.assertTrue(res.startswith(r"\an7\q2\pos(0.00,0.00)"))
        self.assertIn(r"\t(300,600,\fscx100.00\fscy0.00)", res)

    def test_move_tag_with_tags(self):
        res = move_tag_node(mode="Trajectory", shape="m 0 0 l 100 0", tags=r"\1c&H00FFFF&\bord3", t1=0, t2=100)
        self.assertIn(r"\p1}m 0 0 m 100 100 {\p0\r\1c&H00FFFF&\bord3", res)

    def test_move_text_bidirectional(self):
        res = move_text_node(text="Hola", dx=15, dy=0, ox=0, oy=0, t1=0, t2=400)
        self.assertIn(r"{\r\q2}Hola", res)
        self.assertIn(r"\fsp", res)
        self.assertIn(r"\fscy", res)

    def test_move_text_with_tags(self):
        res = move_text_node(text="ColorText", tags=r"\1c&H00FFFF&\blur2", dx=10, t1=0, t2=200)
        self.assertIn(r"{\r\1c&H00FFFF&\blur2\q2}ColorText", res)

    def test_move_text_trajectory_center_anchor(self):
        circle = "m 0 0 m 100 100 b 100 127 78 150 50 150 b 22 150 0 127 0 100 b 0 73 22 50 50 50 b 78 50 100 73 100 100"
        res = move_text_node(text="Kara", trajectory=circle, anchor="center", ox=0, oy=0, t1=0, t2=200, step_px=20.0)
        self.assertIn(r"Kara{\r\alpha&HFF&", res)
        self.assertIn(r"\t(", res)
        self.assertIn(r"\fscy", res)

    def test_move_text_trajectory_zero_anchor(self):
        circle = "m 0 0 m 100 100 b 100 127 78 150 50 150 b 22 150 0 127 0 100 b 0 73 22 50 50 50 b 78 50 100 73 100 100"
        res = move_text_node(text="Kara", trajectory=circle, anchor="zero", ox=0, oy=0, t1=0, t2=200, step_px=20.0)
        self.assertIn(r"\fsp0.00", res)
        self.assertIn(r"\fscy0.00", res)

    def test_move_text_trajectory_points_list(self):
        pts = "0,0; 50,100; 100,0"
        res = move_text_node(text="Kara", trajectory=pts, anchor="center", t1=0, t2=200, step_px=25.0)
        self.assertIn(r"Kara", res)
        self.assertIn(r"\t(", res)

    def test_move_text_zero_crossing(self):
        res = move_text_node(text="Test", ox=0, oy=10, dx=15, dy=-30, t1=0, t2=300)
        self.assertIn(r"{\r\fscy20.00", res)
        self.assertIn(r"\t(0.00,100.00,\fscy0.00)", res)
        self.assertIn(r"\t(100.00,300.00,\fscy40.00)", res)
        self.assertIn(r"Test{\r\alpha&HFF&", res)

    def test_move_tag_jitter_mode(self):
        res = move_tag_node(mode="Jitter", dx=10.0, dy=10.0, seed=12345, dur=50, t1=0, t2=200, anchor="origin")
        self.assertTrue(res.startswith(r"\an7\q2\pos("))
        self.assertIn(r"\t(", res)
        self.assertIn(r"\p1}m 0 0 m 100 100 {\p0\r", res)

    def test_string_evaluator_helpers(self):
        tag_res = eval_python_expr("move_tag(mode='Trajectory', shape='m 0 0 l 50 50', t1=0, t2=200, step_px=50, anchor='origin')")
        self.assertTrue(tag_res.startswith(r"\an7\q2\pos(0.00,0.00)"))
        
        text_res = eval_python_expr("move_text(text='Hello', dx=10, t1=0, t2=200)")
        self.assertIn("Hello", text_res)

    def test_move_tag_with_shape_and_active_unit(self):
        ctx = {
            "active_unit": type("Unit", (), {"center": 500.0, "middle": 112.5, "width": 80.0, "height": 40.0, "descent": 8.0})(),
            "_return_node_is_shape": True
        }
        res = move_tag_node(context=ctx, mode="Trajectory", shape="m 0 0 l 100 0", anchor="center", t1=0, t2=500, step_px=100.0)
        self.assertTrue(res.startswith(r"\an7\q2\pos(0.00,0.00)"))
        self.assertIn(r"\fscx450.00\fscy112.50", res)
        self.assertIn(r"\p1}m 0 0 m 100 100 {\p0\r", res)

    def test_move_tag_with_text_effector2_parity(self):
        ctx = {
            "active_unit": type("Unit", (), {"center": 500.0, "middle": 112.5, "width": 100.0, "height": 50.0, "descent": 10.0})(),
            "_return_node_is_shape": False
        }
        # Effector 2: add_x = -50, add_y = 75 - 10 = 65.
        # Trajectory centered: [450, 112.5] to [550, 112.5].
        # With add: [400, 177.5] to [500, 177.5].
        # min_x = 400 >= 0 -> x0 = 0.
        # min_y = 177.5 > fx_height (50) -> y0 = 0.
        # pos = \an7\q2\pos(0.00,-50.00).
        # fscx = 400 - 0 = 400.00, fscy = 177.5 - 0 = 177.50.
        res = move_tag_node(context=ctx, mode="Trajectory", shape="m 0 0 l 100 0", anchor="center", t1=0, t2=500, step_px=100.0)
        self.assertTrue(res.startswith(r"\an7\q2\pos(0.00,-50.00)"))
        self.assertIn(r"\fscx400.00\fscy177.50", res)
        self.assertIn(r"\p1}m 0 0 m 100 100 {\p0\r", res)

    def test_move_tag_canonical_lowercase_modes(self):
        res_traj = move_tag_node(mode="trajectory", shape="m 0 0 l 100 0", t1=0, t2=500, anchor="origin")
        self.assertTrue(res_traj.startswith(r"\an7\q2\pos(0.00,0.00)"))

        res_wp = move_tag_node(mode="waypoints", points="0,0; 50,50; 100,0", t1=0, t2=500, anchor="origin")
        self.assertTrue(res_wp.startswith(r"\an7\q2\pos(0.00,0.00)"))

        res_jit = move_tag_node(mode="jitter", dx=10.0, dy=10.0, seed=1, dur=50, t1=0, t2=200, anchor="origin")
        self.assertTrue(res_jit.startswith(r"\an7\q2\pos("))

    def test_polar_to_cartesian_canonical(self):
        from node_engine import GraphEngine
        node = {
            "id": 1,
            "type": "Functions/Polar to Cartesian",
            "properties": {
                "x": "100",
                "y": "200",
                "angle": "0",
                "radius": "50"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        pos = engine.evaluate_data_node(1, context={}, output_slot_index=0)
        x = engine.evaluate_data_node(1, context={}, output_slot_index=1)
        y = engine.evaluate_data_node(1, context={}, output_slot_index=2)
        dx = engine.evaluate_data_node(1, context={}, output_slot_index=3)
        dy = engine.evaluate_data_node(1, context={}, output_slot_index=4)

        self.assertEqual(pos, r"\pos(150,200)")
        self.assertEqual(x, "150")
        self.assertEqual(y, "200")
        self.assertEqual(dx, "50")
        self.assertEqual(dy, "0")

if __name__ == "__main__":
    unittest.main()


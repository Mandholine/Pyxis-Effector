# -*- coding: utf-8 -*-
"""Pruebas de ke_point / ke_segment / ke_shape (port de ke.shape de Effector)."""
import random
import unittest

from pyxis_core.domain.services import ke_point as kp
from pyxis_core.domain.services import ke_segment as ks
from pyxis_core.domain.services import ke_shape as ksh
from pyxis_core.domain.services import ke_shape_ops as ops
from pyxis_core.domain.services.ke_point import Point
from pyxis_core.domain.services.ke_segment import Segment
from pyxis_core.domain.services.ke_shape import Shape


class PointTests(unittest.TestCase):
    def test_basic(self):
        p = Point("m 12 -8.3")
        self.assertEqual((p.x, p.y, p.t), (12, -8.3, "m"))
        self.assertEqual(Point("12", "5").x, 12)
        self.assertEqual(Point(3, 4).len(), 5)
        self.assertEqual(Point(10, 0).middle(Point(0, 0)), Point(5, 0))
        self.assertEqual(Point(4, 3).perpendicular(Point(0, 0), 0.4, 5), Point(5.4, -2.2))
        self.assertEqual(Point(10, 0).rotate(90), Point(0, -10))
        self.assertEqual(Point(1, 2).reflect(Point(0, 0), Point(10, 0)), Point(1, -2))
        self.assertEqual(Point(0, 0).intersect(Point(10, 10), Point(0, 10), Point(10, 0)), Point(5, 5))
        self.assertEqual(Point(0, 0).ipol(0.5, Point(10, 10)), Point(5, 5))

    def test_groups(self):
        pts = [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10), Point(5, 5)]
        self.assertEqual(kp.to_convex(pts), [Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10)])
        self.assertEqual(kp.sort_points(pts, "maxy")[0], Point(10, 10))
        self.assertEqual(kp.group(pts, "bounding"), [0, 0, 10, 10])
        self.assertEqual(kp.to_shape(pts[:3]), "m 0 0 l 10 0 10 10 ")
        self.assertEqual(len(kp.triangulate(pts)), 4)
        found = Point(0, 0).rand({"dx": 60, "dy": 60, "n": 15, "distance": 12}, rng=random.Random(1))
        self.assertEqual(len(found), 15)
        for i, a in enumerate(found):
            for b in found[i + 1:]:
                self.assertGreaterEqual(a.distance(b), 12)


class SegmentTests(unittest.TestCase):
    ARCH = "0 20 b 20 0 40 0 60 20 "

    def test_bezier(self):
        b = Segment(self.ARCH)
        self.assertAlmostEqual(b.length(), 68.868, places=2)
        self.assertAlmostEqual(ks.length2t(b, 34.434), 0.5, places=3)  # ejemplo del autor
        self.assertEqual(b.bezier(0.25)[0], Point(15, 8.751))
        left, right, p = b.cut(0.5)
        self.assertEqual(p, Point(30, 5))
        self.assertEqual(Segment("m 0 20 b 20 0 40 0 60 20 ").inside(Point(30, 5)), 0.5)
        self.assertFalse(Segment("m 0 20 b 20 0 40 0 60 20 ").inside(Point(30, 50)))

    def test_lines(self):
        self.assertEqual(Segment("0 0 l 100 100 ").intersect(Segment("0 100 l 100 0 "))[0], Point(50, 50))
        self.assertFalse(Segment("0 0 l 10 0 ").intersect(Segment("0 5 l 10 5 ")))
        self.assertEqual(len(Segment("-5 25 l 57 3 ").intersect(Segment("15 2 b 12 47 32 -7 45 13 "))), 3)
        self.assertEqual(str(Segment("0 0 l 10 0 ").split([4])), "m 0 0 l 2.5 0 5 0 7.5 0 10 0 ")
        self.assertEqual(str(Segment("0 0 l 100 0 ").cut({"n": 4})), "m 0 0 l 25 0 50 0 75 0 100 0 ")
        self.assertEqual(Segment("0 0 l 10 10 ").angle(), 315)


class ShapeTests(unittest.TestCase):
    def test_parse_and_measure(self):
        r = Shape(ksh.RECTANGLE)
        self.assertEqual(Shape("m 0 0 l 0 20 20 20 20 0").code, "m 0 0 l 0 20 l 20 20 l 20 0 ")
        self.assertEqual(Shape("0,0,10,5").code, "m 0 0 l 0 5 l 10 5 l 10 0 ")
        self.assertEqual((r.n, r.width, r.height, r.center, r.length()), (5, 100, 100, 50, 400))
        self.assertEqual(r.area(), -10000)
        self.assertTrue(r.is_closed())
        self.assertAlmostEqual(Shape(ksh.CIRCLE).length(), 314.876, places=2)
        self.assertEqual(Shape(Shape(ksh.CIRCLE).segments()).code, ksh.CIRCLE)
        self.assertEqual(Shape(Shape(ksh.CIRCLE).points()).code, ksh.CIRCLE)

    def test_closed_inverse(self):
        s = Shape("m 0 0 l 0 20 l 20 20 l 20 0 m 30 20 l 30 0 l 50 0 l 50 20 ")
        self.assertEqual(s.closed().code, "m 0 0 l 0 20 l 20 20 l 20 0 l 0 0 m 30 20 l 30 0 l 50 0 l 50 20 l 30 20 ")
        self.assertEqual(Shape(ksh.RECTANGLE).unclosed().code, "m 0 0 l 0 100 l 100 100 l 100 0 ")
        self.assertEqual(Shape("m 0 0 l 0 20 l 20 20 l 20 0 ").inverse().code, "m 20 0 l 20 20 l 0 20 l 0 0 ")
        self.assertEqual(Shape(ksh.CIRCLE).inverse().inverse().code, ksh.CIRCLE)
        self.assertGreater(Shape("m 0 0 l 0 20 l 20 20 l 20 0 ").clockwise().area(), 0)

    def test_transforms(self):
        r = Shape(ksh.RECTANGLE)
        self.assertEqual((r + 7).code, "m 7 0 l 7 100 l 107 100 l 107 0 l 7 0 ")
        self.assertEqual((r * 0.25).bounding(), (0, 0, 25, 25))
        self.assertEqual(r.size(120, 45).bounding(), (0, 0, 120, 45))
        self.assertEqual(r.size(120, 0).bounding(), (0, 0, 120, 120))
        self.assertEqual(Shape("m 0 0 l 0 50 l 30 50 l 30 30 ").reflect("y").code, "m 0 0 l 0 50 l -30 50 l -30 30 ")
        self.assertEqual(r.gsub(lambda x, y, c: (x, y - c.Cx)).bounding(), (0, -50, 100, 50))
        self.assertEqual(Shape("m 0 0 l 10 0 l 20 0 l 20 10 ").reduce().code, "m 0 0 l 20 0 l 20 10 ")
        self.assertEqual(Shape("m 10 0 b 0 0 0 10 10 10 l 30 10 b 40 10 40 0 30 0 l 10 0 ").redraw(4, "line").round().code,
                         "m 10 0 b 0 0 0 10 10 10 l 14 10 l 18 10 l 22 10 l 26 10 l 30 10 "
                         "b 40 10 40 0 30 0 l 26 0 l 22 0 l 18 0 l 14 0 l 10 0 ")
        rounded = r.roundout(20)
        self.assertIn(" b 0 91.6 8.4 100 20 100 ", rounded.code)
        self.assertEqual(r.delete_points([4, 5]).code, "m 0 0 l 0 100 l 100 100 ")


if __name__ == "__main__":
    unittest.main()


class ShapeOpsTests(unittest.TestCase):
    def test_contours(self):
        sq = Shape("m 0 0 l 0 56 l 44 56 l 44 0 l 0 0 ")
        self.assertEqual(sq.line(4, "miter").code,
                         "m -2 -2 l -2 58 l 46 58 l 46 -2 l -2 -2 m 2 2 l 42 2 l 42 54 l 2 54 l 2 2 ")
        self.assertEqual(Shape(ksh.RECTANGLE).expand(6).bounding(), (-6, -6, 106, 106))

    def test_cut_and_parameter(self):
        r = Shape(ksh.RECTANGLE)
        cut, info = r.cut(0.625)
        self.assertEqual(cut.code, "m 0 0 l 0 100 l 100 100 l 100 50 ")
        self.assertEqual(info[0], Point(100, 50))
        pos, ang = Shape(ksh.CIRCLE).parameter(0.125)
        self.assertAlmostEqual(pos.x, 14.5, places=1)
        self.assertEqual(len(Shape(ksh.CIRCLE).parameter(None, 5)), 5)
        two = Shape("m 0 0 l 0 30 l 30 30 l 30 0 l 0 0 m 10 10 l 20 10 l 20 20 l 10 20 l 10 10 ")
        self.assertAlmostEqual(two.get_parameter(Point(10, 20)), 150 / 160)

    def test_pixels_and_clip(self):
        px = Shape("m 0 0 l 0 5 l 5 5 l 5 0 ").pixels()
        self.assertEqual(len(px), 25)
        self.assertEqual(px[0], {"a": "&H00&", "x": 1.0, "y": 1.0})
        self.assertEqual(Shape(ksh.RECTANGLE).to_clip(10, 20), "\\clip(m -40 -30 l -40 70 l 60 70 l 60 -30 l -40 -30 )")

    def test_insert_ipol_bezier(self):
        r, c = Shape(ksh.RECTANGLE), Shape(ksh.CIRCLE)
        a, b = r.insert(c)
        self.assertEqual(len(a.points()), len(b.points()))
        self.assertEqual(r.to_bezier().code, "m 0 0 b 0 33 0 67 0 100 b 33 100 67 100 100 100 b 100 67 100 33 100 0 b 67 0 33 0 0 0 ")
        mid = Shape(ops.ipol([ksh.RECTANGLE, ksh.CIRCLE], 0.5))
        self.assertAlmostEqual(mid.width, 100, places=0)

    def test_generators(self):
        self.assertEqual(Shape(ops.polygon(4, 50)).n, 5)
        self.assertEqual(len(Shape(ops.multi8(ksh.RECTANGLE, 100, 10, 10)).subshapes()), 10)
        self.assertEqual(len(Shape(ops.multi7(12, 100)).subshapes()), 12)
        self.assertGreater(Shape(ops.multi1(100, [8, [2], 4, [3]])).width, 80)
        arr = ops.array("m 0 0 l 0 12 12 12 12 0 ", dx=5, dy=5, loop={"x": 3, "y": 2})
        self.assertEqual((len(arr.subshapes()), arr.width, arr.height), (6, 46, 29))
        self.assertEqual(Shape(ops.banner(300, 40, "[]")).width, 300)
        rng = random.Random(3)
        for mode in ("bezier", "path", "line"):
            self.assertTrue(ops.trajectory(mode, rng=rng).code.startswith("m 0 0"))
        self.assertTrue(Shape(ops.gear(80, 8)).n > 20)
        bars = Shape("m 0 0 l 0 6 l 6 6 l 6 0 l 0 0 ").bars("\\1c&HFFFFFF&")
        self.assertTrue(bars.startswith("{\\1c&HFFFFFF&\\p1}bars m 0 0 l 0 0 0 1 6 1 6 0 6 0 0 0 {\\p0}\\N"))
        self.assertEqual(bars.count("bars m"), 6)


class ShapeBooleanTests(unittest.TestCase):
    def test_difference_from_original_example(self):
        from pyxis_core.infrastructure.adapters import ShapeBooleanAdapter
        from pyxis_core.domain.repositories import IShapeBooleanEngine
        eng = ShapeBooleanAdapter()
        self.assertIsInstance(eng, IShapeBooleanEngine)
        subject = "m 0 0 l 0 50 l 30 50 l 30 0 l 0 0 m 10 10 l 20 10 l 20 40 l 10 40 l 10 10 "
        clip = "m -5 20 l -5 30 l 40 30 l 40 20 l -5 20 "
        res = eng.boolean(subject, clip, "difference")
        self.assertIsInstance(res, Shape)
        self.assertEqual(res.bounding(), (0, 0, 30, 50))
        self.assertGreater(len(res.subshapes()), 1)
        union = eng.boolean("m 0 0 l 0 10 l 10 10 l 10 0 ", "m 5 0 l 5 10 l 15 10 l 15 0 ", "union")
        self.assertEqual(union.bounding(), (0, 0, 15, 10))
        inter = eng.boolean("m 0 0 l 0 10 l 10 10 l 10 0 ", "m 5 0 l 5 10 l 15 10 l 15 0 ", "intersection")
        self.assertEqual(inter.bounding(), (5, 0, 10, 10))


class ShapeDependentTests(unittest.TestCase):
    def test_normalize_with_shape_and_time_points(self):
        from pyxis_core.domain.services import ke_math, ke_time
        v = ke_math.normalize(0.25, None, ksh.CIRCLE)
        self.assertTrue(0 <= v <= 1)
        self.assertEqual(ke_math.normalize(0.5), 0.5)
        pts = [Point(0, 0), Point(10, 0), Point(10, 30)]
        res = ke_time.ipol([200, 500], points=pts)
        self.assertEqual(res, [[[200, 275.0], [275.0, 500.0]]])


class RendererCompatTests(unittest.TestCase):
    """Salidas que deben verse bien en libass (macOS), no solo en VSFilterMod."""

    def test_static_movevc_is_placed_clip_without_movevc(self):
        from pyxis_core.domain.services import ke_tag
        # rectangulo 100x100 centrado en (200, 150): esquina (150, 100), sin \movevc (libass lo ignora)
        tag = ke_tag.movevc(ksh.RECTANGLE, 200, 150)
        self.assertEqual(tag, "\\clip(m 150 100 l 150 200 l 250 200 l 250 100 l 150 100 )")
        self.assertNotIn("movevc", tag)
        self.assertTrue(ke_tag.movevci(ksh.RECTANGLE, 200, 150).startswith("\\iclip(m 150 100"))
        moving = ke_tag.movevc(ksh.RECTANGLE, 200, 150, 30, 0, 0, 500)      # con movimiento si usa \movevc
        self.assertIn("\\movevc(150,100,180,100,0,500)", moving)

    def test_bare_t_becomes_valid_transform(self):
        from pyxis_core.domain.services import ke_tag
        self.assertEqual(ke_tag.wrap_bare_t("\\fr-65\\t\\fr0\\fad(300,0)"), "\\fr-65\\t(\\fr0)\\fad(300,0)")
        self.assertEqual(ke_tag.wrap_bare_t("\\t\\fscx150\\blur2\\fad(0,300)"), "\\t(\\fscx150\\blur2)\\fad(0,300)")
        self.assertEqual(ke_tag.wrap_bare_t("\\t(0,100,\\fr0)\\bord2"), "\\t(0,100,\\fr0)\\bord2")   # ya valido
        self.assertEqual(ke_tag.wrap_bare_t("\\t\\pos(1,2)"), "\\t\\pos(1,2)")                       # nada animable
        from types import SimpleNamespace as NS
        line = NS(start_time=0, end_time=1000)
        unit = NS(line=line, word_start=0, word_end=100, syl_start=0, syl_end=100, char_start=None, char_end=None)
        self.assertEqual(ke_tag.times("\\fr-65\\t\\fr0\\fad(300,0)", unit, 0), "\\fr-65\\t(\\fr0)\\fad(300,0)")

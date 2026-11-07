import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from karaskel_engine import KaraskelEngine, KaraskelLine, KaraskelMeta
from ass_parser import KaraokeProcessor
from models import PyxisLine, PyxisUnit
from node_engine import GraphEngine


class TestLineTransformPositioning(unittest.TestCase):
    """
    Unit test suite verifying canonical non-destructive line positioning and relative synthesis
    for \\pos, \\move, and \\org tags across lines, syllables, and characters.
    """

    def setUp(self):
        self.meta = KaraskelMeta()
        self.meta.res_x = 1280
        self.meta.res_y = 720
        self.styles = {
            "Default": {
                "fontname": "Arial",
                "fontsize": 40.0,
                "bold": False,
                "italic": False,
                "underline": False,
                "strikeout": False,
                "scale_x": 100.0,
                "scale_y": 100.0,
                "spacing": 0.0,
                "angle": 0.0,
                "borderstyle": 1,
                "outline": 2.0,
                "shadow": 0.0,
                "align": 2,
                "margin_l": 30,
                "margin_r": 30,
                "margin_v": 30
            }
        }
        self.processor = KaraokeProcessor(res_x=1280, res_y=720)

    def test_pos_does_not_collapse_syllables(self):
        """Verifies that a line-level \\pos tag positions the line while syllables remain distributed."""
        k_line = KaraskelLine(
            raw_text=r"{\pos(640,680)\k30}Hel{\k40}lo {\k50}World",
            start_time=1000,
            end_time=2500,
            style="Default"
        )
        KaraskelEngine.preproc_line_text(self.meta, self.styles, k_line)
        KaraskelEngine.preproc_line_size(self.meta, self.styles, k_line)
        KaraskelEngine.preproc_line_pos(self.meta, self.styles, k_line)

        self.assertTrue(k_line.has_pos)
        self.assertAlmostEqual(k_line.x, 640.0, places=1)
        self.assertAlmostEqual(k_line.y, 680.0, places=1)

        content_syls = [s for s in k_line.kara if s.text_stripped]
        self.assertGreater(len(content_syls), 1)
        # Content syllables must NOT be collapsed onto the same X coordinate
        for idx in range(len(content_syls) - 1):
            s1 = content_syls[idx]
            s2 = content_syls[idx + 1]
            self.assertLess(s1.left, s2.left, f"Syllable {idx} left ({s1.left}) should be less than syllable {idx+1} left ({s2.left})")
            self.assertLess(s1.center, s2.center)

        # Ensure syllable style_override does not have has_pos set
        for syl in k_line.kara:
            if syl.style_override is not None:
                self.assertFalse(getattr(syl.style_override, 'has_pos', False))

    def test_move_positions_line_and_distributes_syllables(self):
        """Verifies that a line-level \\move tag anchors the initial line position and distributes syllables."""
        k_line = KaraskelLine(
            raw_text=r"{\move(200,500,800,500,0,1000)\k30}Move{\k40}ment",
            start_time=0,
            end_time=1000,
            style="Default"
        )
        KaraskelEngine.preproc_line_text(self.meta, self.styles, k_line)
        KaraskelEngine.preproc_line_size(self.meta, self.styles, k_line)
        KaraskelEngine.preproc_line_pos(self.meta, self.styles, k_line)

        self.assertTrue(k_line.has_move)
        self.assertAlmostEqual(k_line.move_x1, 200.0, places=1)
        self.assertAlmostEqual(k_line.move_y1, 500.0, places=1)
        self.assertAlmostEqual(k_line.move_x2, 800.0, places=1)
        self.assertAlmostEqual(k_line.move_y2, 500.0, places=1)

        # Line anchor should match move start position
        self.assertAlmostEqual(k_line.x, 200.0, places=1)
        self.assertAlmostEqual(k_line.y, 500.0, places=1)

        # Content syllables must be sequentially placed
        content_syls = [s for s in k_line.kara if s.text_stripped]
        self.assertEqual(len(content_syls), 2)
        self.assertLess(content_syls[0].left, content_syls[1].left)

    def test_node_engine_synthesizes_relative_move(self):
        """Verifies that node_engine generates relative \\move for child units when the original line has \\move."""
        engine = GraphEngine()

        line = PyxisLine()
        line.has_move = True
        line.move_x1 = 200.0
        line.move_y1 = 500.0
        line.move_x2 = 600.0
        line.move_y2 = 500.0
        line.move_t1 = 0
        line.move_t2 = 800
        line.x = 200.0
        line.y = 500.0
        line.center = 200.0
        line.middle = 500.0

        # Create active unit displaced by +50px X, +10px Y
        unit = PyxisUnit()
        unit.line = line
        unit.x = 250.0
        unit.y = 510.0
        unit.left = 230.0
        unit.center = 250.0
        unit.right = 270.0
        unit.top = 490.0
        unit.middle = 510.0
        unit.bottom = 530.0

        ctx = {'line': line, 'origin_align': 5}
        layer, st, et, tags, ret = engine._apply_defaults(
            active_unit=unit,
            layer_raw=0,
            st_raw=0,
            et_raw=1000,
            tags_raw="",
            return_raw="Test",
            context=ctx
        )

        # Should generate \move shifted by delta (+50, +10)
        # u_x1 = 200 + 50 = 250, u_y1 = 500 + 10 = 510
        # u_x2 = 600 + 50 = 650, u_y2 = 500 + 10 = 510
        self.assertIn(r"\move(250,510,650,510,0,800)", tags)
        self.assertNotIn(r"\pos", tags)

    def test_node_engine_precedence_over_original_move_and_pos(self):
        """Verifies that explicit \\pos or \\move from graph overrides original line pos/move."""
        engine = GraphEngine()

        line = PyxisLine()
        line.has_move = True
        line.move_x1 = 100.0
        line.move_y1 = 100.0
        line.move_x2 = 500.0
        line.move_y2 = 100.0
        line.x = 100.0
        line.y = 100.0

        unit = PyxisUnit()
        unit.line = line
        unit.center = 150.0
        unit.middle = 100.0

        ctx = {'line': line}
        # Explicit \pos from upstream node
        layer, st, et, tags, ret = engine._apply_defaults(
            active_unit=unit,
            layer_raw=0,
            st_raw=0,
            et_raw=1000,
            tags_raw=r"\pos(300,400)",
            return_raw="Test",
            context=ctx
        )

        self.assertIn(r"\pos(300,400)", tags)
        self.assertNotIn(r"\move", tags)

    def test_relative_org_calculation_option_a(self):
        """Verifies that Option A for \\org calculates the relative pivot for active units."""
        engine = GraphEngine()

        line = PyxisLine()
        line.has_org = True
        line.x = 200.0
        line.y = 300.0
        line.center = 200.0
        line.middle = 300.0
        line.org_x = 200.0
        line.org_y = 250.0  # 50px above line

        unit = PyxisUnit()
        unit.line = line
        unit.x = 350.0
        unit.y = 300.0
        unit.center = 350.0
        unit.middle = 300.0

        # Model property check
        # delta_x = 200 - 200 = 0 -> unit.org_x = 350
        # delta_y = 250 - 300 = -50 -> unit.org_y = 300 - 50 = 250
        self.assertAlmostEqual(unit.org_x, 350.0)
        self.assertAlmostEqual(unit.org_y, 250.0)

        # Output synthesis check
        ctx = {'line': line, 'origin_align': 5}
        layer, st, et, tags, ret = engine._apply_defaults(
            active_unit=unit,
            layer_raw=0,
            st_raw=0,
            et_raw=1000,
            tags_raw="",
            return_raw="Test",
            context=ctx
        )

        self.assertIn(r"\org(350,250)", tags)

    def test_explicit_org_from_node_overrides_line_org(self):
        """Verifies that an upstream \\org overrides the original line's \\org."""
        engine = GraphEngine()

        line = PyxisLine()
        line.has_org = True
        line.x = 100.0
        line.y = 100.0
        line.org_x = 100.0
        line.org_y = 50.0

        unit = PyxisUnit()
        unit.line = line
        unit.center = 120.0
        unit.middle = 100.0

        ctx = {'line': line}
        layer, st, et, tags, ret = engine._apply_defaults(
            active_unit=unit,
            layer_raw=0,
            st_raw=0,
            et_raw=1000,
            tags_raw=r"\org(0,0)",
            return_raw="Test",
            context=ctx
        )

        self.assertIn(r"\org(0,0)", tags)
        self.assertNotIn(r"\org(120,50)", tags)

    def test_ass_parser_chars_and_words_distribution_with_pos(self):
        """Verifies that ASSParser distributes chars and words properly across a line positioned with \\pos."""
        raw_dialogue = r"Dialogue: 0,0:00:01.00,0:00:05.00,Default,,0,0,0,,{\pos(640,680)\k30}Hel{\k40}lo {\k50}World"
        parsed = self.processor.process_line(raw_dialogue, self.styles["Default"])
        self.assertIsNotNone(parsed)
        self.assertTrue(parsed.has_pos)
        self.assertAlmostEqual(parsed.pos_x, 640.0, places=1)
        self.assertAlmostEqual(parsed.pos_y, 680.0, places=1)

        # Verify chars are sequentially advancing
        chars = parsed.chars
        self.assertGreater(len(chars), 5)
        for i in range(len(chars) - 1):
            c1 = chars[i]
            c2 = chars[i + 1]
            self.assertLessEqual(c1.left, c2.left)
            self.assertLessEqual(c1.center, c2.center)

        # Verify words are sequentially advancing
        words = parsed.words
        self.assertEqual(len(words), 2)  # "Hello" and "World"
        self.assertLess(words[0].left, words[1].left)
        self.assertLess(words[0].right, words[1].left)

    def test_ass_parser_chars_and_words_distribution_with_move(self):
        """Verifies that ASSParser distributes chars and words properly across a line positioned with \\move."""
        raw_dialogue = r"Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,{\move(200,500,800,500,0,1000)\k30}Move{\k40}ment"
        parsed = self.processor.process_line(raw_dialogue, self.styles["Default"])
        self.assertIsNotNone(parsed)
        self.assertTrue(parsed.has_move)
        self.assertAlmostEqual(parsed.move_x1, 200.0, places=1)
        self.assertAlmostEqual(parsed.move_y1, 500.0, places=1)

        chars = parsed.chars
        self.assertGreater(len(chars), 4)
        for i in range(len(chars) - 1):
            self.assertLessEqual(chars[i].left, chars[i + 1].left)


if __name__ == '__main__':
    unittest.main()

import unittest
from string_evaluator import (
    eval_string_template,
    expand_unit_shortcuts,
    substitute_dollar_vars,
    evaluate_inline_bang_expressions,
    expand_custom_dark_tags,
    evaluate_tag_parentheses
)
from models import PyxisLine, PyxisUnit, StyleRef
from node_engine import GraphEngine


class TestStringEvaluator(unittest.TestCase):

    def setUp(self):
        self.style = StyleRef({
            "Fontname": "Arial",
            "Fontsize": 25.0,
            "PrimaryColour": "&H00FFFFFF&",
            "SecondaryColour": "&H000000FF&",
            "OutlineColour": "&H00000000&",
            "BackColour": "&H00000000&",
            "ScaleX": 100.0,
            "ScaleY": 100.0,
            "Spacing": 0.0,
            "Outline": 2.0,
            "Shadow": 2.0,
            "angle": 0.0
        })
        self.line = PyxisLine()
        self.line.i = 1
        self.line.start_time = 1000
        self.line.end_time = 5000
        self.line.duration = 4000
        self.line.style = "Default"
        self.line.styleref = self.style
        self.line.text_stripped = "Test Karaoke"
        self.line.text = r"{\k40}Test {\k60}Karaoke"

        self.syl = PyxisUnit()
        self.syl.i = 1
        self.syl.n = 2
        self.syl.start_time = 1000
        self.syl.end_time = 2000
        self.syl.duration = 1000
        self.syl.text = "Test"
        self.syl.text_stripped = "Test"
        self.syl.left = 100.0
        self.syl.center = 150.0
        self.syl.right = 200.0
        self.syl.top = 50.0
        self.syl.middle = 70.0
        self.syl.bottom = 90.0
        self.syl.width = 100.0
        self.syl.height = 40.0
        self.syl.line = self.line

        self.context = {
            "active_unit": self.syl,
            "syl": self.syl,
            "line": self.line,
            "l": self.line,
            "j": 2,
            "maxj": 5,
            "frame_dur": 40.0,
            "ratio": 1.5,
            "res_x": 1920,
            "res_y": 1080
        }

    def test_static_string(self):
        text = "Hello World"
        res = eval_string_template(text, self.context)
        self.assertEqual(res, "Hello World")

    def test_unit_shortcuts(self):
        # 10f = 10 * 40.0 = 400
        # 2r = 2 * 1.5 = 3
        text = r"\fad(5f, 10f)\xbord(2r)"
        res = expand_unit_shortcuts(text, self.context)
        self.assertEqual(res, r"\fad(200, 400)\xbord(3)")

    def test_dollar_vars_simple(self):
        text = r"{\pos($center, $middle)\dur$dur}"
        res = substitute_dollar_vars(text, self.context)
        self.assertEqual(res, r"{\pos(150, 70)\dur1000}")

    def test_dollar_vars_dotted(self):
        text = r"{\an5\pos($syl.left, $syl.top)\1c$line.color1}"
        res = substitute_dollar_vars(text, self.context)
        self.assertEqual(res, r"{\an5\pos(100, 50)\1c&HFFFFFF&}")

    def test_dollar_vars_auto4_aliases(self):
        text = r"st=$start, et=$end, kdur=$kdur, mid=$mid, si=$si"
        res = substitute_dollar_vars(text, self.context)
        self.assertEqual(res, "st=1000, et=2000, kdur=100, mid=1500, si=1")

    def test_dollar_escape(self):
        text = r"Price: \$100 and $$50 but $center"
        res = substitute_dollar_vars(text, self.context)
        self.assertEqual(res, "Price: $100 and $50 but 150")

    def test_direct_parentheses_pos_move(self):
        text = r"{\pos(syl.center + 25, syl.middle - 10)}"
        res = evaluate_tag_parentheses(text, self.context)
        self.assertEqual(res, r"{\pos(175, 60)}")

    def test_direct_parentheses_math(self):
        text = r"{\frz(j * 360 / maxj)\fscx(100 + 50)}"
        res = evaluate_tag_parentheses(text, self.context)
        self.assertEqual(res, r"{\frz144\fscx150}")

    def test_direct_parentheses_t_tag(self):
        # \t(0, 10f, \fscxy(150))
        # 10f -> 400
        text = r"\t(0, 10f, \fscxy(150))"
        res = expand_unit_shortcuts(text, self.context)
        res = evaluate_tag_parentheses(res, self.context)
        self.assertEqual(res, r"\t(0, 400, \fscx150\fscy150)")

    def test_compound_dark_tags(self):
        text = r"\fscxy150\134c&H00FFFF&\bs0\xybord3\frxyz45"
        res = expand_custom_dark_tags(text, self.context)
        self.assertEqual(res, r"\fscx150\fscy150\1c&H00FFFF&\3c&H00FFFF&\4c&H00FFFF&\bord0\shad0\xbord3\ybord3\frx45\fry45\frz45")

    def test_style_restoration_tilde(self):
        # \fscxy~ -> \fscx100\fscy100, \1c~ -> \1c&HFFFFFF&, \bs~ -> \bord2\shad2
        text = r"\fscxy~\1c~\bs~"
        res = expand_custom_dark_tags(text, self.context)
        self.assertEqual(res, r"\fscx100\fscy100\1c&HFFFFFF&\bord2\shad2")

    def test_inline_bang_expressions(self):
        text = r"Text: !char.text.upper() if 'char' in context else syl.text.upper()!"
        res = evaluate_inline_bang_expressions(text, self.context)
        self.assertEqual(res, "Text: TEST")

    def test_full_pipeline_integrated(self):
        # Cadena compleja que combina todo
        raw = r"{\an5\pos(syl.center + 10, syl.middle)\fscxy(150)\134c$line.color1\t(0, 10f, \fscxy~)}"
        res = eval_string_template(raw, self.context)
        self.assertEqual(res, r"{\an5\pos(160, 70)\fscx150\fscy150\1c&HFFFFFF&\3c&HFFFFFF&\4c&HFFFFFF&\t(0, 400, \fscx100\fscy100)}")

    def test_stochastic_tags(self):
        raw = r"\frzR(-30, 30)\1cR()"
        res = eval_string_template(raw, self.context)
        # Debe contener \frz con un número y \1c con formato &H...&
        self.assertTrue(r"\frz" in res)
        self.assertTrue(r"\1c&H" in res)

    def test_graph_engine_string_node_execution(self):
        graph = {
            "nodes": [
                {
                    "id": "str1",
                    "type": "String",
                    "properties": {
                        "valor": r"{\pos(syl.center + 10, syl.middle)\fscxy150}"
                    }
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        str_out = engine._evaluate_data_node_body("str1", self.context, 0)
        self.assertEqual(str_out, r"{\pos(160, 70)\fscx150\fscy150}")


if __name__ == "__main__":
    unittest.main()

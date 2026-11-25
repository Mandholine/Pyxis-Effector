import os
import sys
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from models import PyxisLine, StyleRef
from string_evaluator import eval_string_template
from nodes.code_nodes import execute_lua_script
from node_validator import GraphValidator


def _make_line(raw_text: str, style_overrides: dict | None = None) -> PyxisLine:
    line = PyxisLine()
    style_data = {
        "Fontname": "Montserrat",
        "Fontsize": 52,
        "PrimaryColour": "&H00AABBCC&",
        "SecondaryColour": "&H00112233&",
        "OutlineColour": "&H00445566&",
        "BackColour": "&H00778899&",
        "Outline": 3.0,
        "Shadow": 1.5,
        "ScaleX": 110.0,
        "ScaleY": 95.0,
        "Spacing": 2.0,
        "Angle": 12.0,
        "Alignment": 5,
        "Bold": True,
        "Italic": False,
        "Underline": False,
        "StrikeOut": False,
    }
    if style_overrides:
        style_data.update(style_overrides)
    line.styleref = StyleRef(style_data)
    line.raw_text = raw_text
    return line


class TestLineOrgTags(unittest.TestCase):
    def test_styleref_fallback_when_no_inline_tags(self):
        line = _make_line("Plain subtitle text")
        self.assertEqual(line.color1_org, "&HAABBCC&")
        self.assertEqual(line.color2_org, "&H112233&")
        self.assertEqual(line.color3_org, "&H445566&")
        self.assertEqual(line.color4_org, "&H778899&")
        self.assertEqual(line.alpha_org, "&H00&")
        self.assertEqual(line.alpha1_org, "&H00&")
        self.assertEqual(line.fontname_org, "Montserrat")
        self.assertEqual(line.fontsize_org, 52.0)
        self.assertEqual(line.scale_x_org, 110.0)
        self.assertEqual(line.scale_y_org, 95.0)
        self.assertEqual(line.spacing_org, 2.0)
        self.assertEqual(line.bold_org, 1)
        self.assertEqual(line.italic_org, 0)
        self.assertEqual(line.align_org, 5)
        self.assertEqual(line.frz_org, 12.0)
        self.assertEqual(line.outline_org, 3.0)
        self.assertEqual(line.xbord_org, 3.0)
        self.assertEqual(line.ybord_org, 3.0)
        self.assertEqual(line.shadow_org, 1.5)
        self.assertEqual(line.xshad_org, 1.5)
        self.assertEqual(line.yshad_org, 1.5)
        self.assertEqual(line.blur_org, 0.0)
        self.assertEqual(line.be_org, 0.0)
        self.assertEqual(line.pos_org, "")
        self.assertEqual(line.clip_org, "")

    def test_inline_overrides_and_karaoke_transform_exclusion(self):
        line = _make_line(
            r"{\k45\kf20\1c&H123456&\bord4.5\ybord6\shad2\alpha&H80&\3a&H20&\pos(640,360)\clip(0,0,100,100)\blur1.5\t(0,500,\bord99\1c&HFFFFFF&)}Hello"
        )
        self.assertEqual(line.color1_org, "&H123456&")
        self.assertEqual(line.color3_org, "&H445566&")
        self.assertEqual(line.outline_org, 4.5)
        self.assertEqual(line.xbord_org, 4.5)
        self.assertEqual(line.ybord_org, 6.0)
        self.assertEqual(line.shadow_org, 2.0)
        self.assertEqual(line.xshad_org, 2.0)
        self.assertEqual(line.yshad_org, 2.0)
        self.assertEqual(line.alpha_org, "&H80&")
        self.assertEqual(line.alpha1_org, "&H80&")
        self.assertEqual(line.alpha3_org, "&H20&")
        self.assertEqual(line.pos_org, "640,360")
        self.assertEqual(line.clip_org, "0,0,100,100")
        self.assertEqual(line.blur_org, 1.5)

    def test_reset_tag_restores_styleref_in_leading_block(self):
        line = _make_line(r"{\bord10\1c&H000000&\r\fs70}Hello")
        self.assertEqual(line.outline_org, 3.0)
        self.assertEqual(line.color1_org, "&HAABBCC&")
        self.assertEqual(line.fontsize_org, 70.0)

    def test_dark_tag_line_prop_and_cross_tag_assignment(self):
        line = _make_line(
            r"{\1c&H010203&\4c&H040506&\bord5\shad2.5\fscx125\fscy80\pos(320,180)\fad(100,200)}Test"
        )
        ctx = {"line": line, "l": line, "styleref": line.styleref}
        out = eval_string_template(
            r"{\1c!line.color4!\bord!line.shadow!\13c!line.color1!\fscxy!line.scale_x!\pos!line.pos!\fad!line.fad!}",
            ctx,
        )
        self.assertIn(r"\1c&H040506&", out)
        self.assertIn(r"\bord2.5", out)
        self.assertIn(r"\1c&H010203&\3c&H010203&", out)
        self.assertIn(r"\fscx125\fscy125", out)
        self.assertIn(r"\pos(320,180)", out)
        self.assertIn(r"\fad(100,200)", out)

    def test_lua_script_exposes_line_org_props(self):
        line = _make_line(r"{\bord7\1c&HABCDEF&}Lua")
        ctx = {"line": line, "l": line, "styleref": line.styleref}
        res = execute_lua_script(
            ctx,
            "result = tostring(line.outline_org) .. '|' .. l.color1_org .. '|' .. tostring(line.fontsize_org)",
            {},
        )
        self.assertEqual(res, "7.0|&HABCDEF&|52.0")

    def test_validator_accepts_line_org_and_dark_tag_line_prop(self):
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"unit": "syl"},
                    "outputs": [{"name": "Loop", "links": [1]}],
                },
                {
                    "id": 2,
                    "type": "Variables/Define Vars",
                    "properties": {"vars": "b0 = line.outline_org\nc0 = l.color1_org"},
                },
                {
                    "id": 3,
                    "type": "Basics/Tags",
                    "properties": {"tags": r"\1c!line.color4!\bord!line.shadow!\13c!line.color1!"},
                    "outputs": [{"name": "Tags", "links": [2]}],
                },
                {
                    "id": 4,
                    "type": "System/Output",
                    "inputs": [
                        {"name": "Loop", "link": 1},
                        {"name": "Tags", "link": 2},
                    ],
                },
            ],
            "links": [
                [1, 1, 0, 4, 0, "loop"],
                [2, 3, 0, 4, 1, "string"],
            ],
        }
        issues = GraphValidator(graph_data).validate()
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()

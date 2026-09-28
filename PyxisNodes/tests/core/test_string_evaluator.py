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

"""Pruebas unitarias para evaluacion de plantillas de strings, interpolador de tags ASS y expresiones."""

import unittest 
from node_engine import GraphEngine ,_eval_num_expr 
from string_evaluator import eval_string_template 


class TestStringEvaluator (unittest .TestCase ):
    """Pruebas para el evaluador de expresiones de texto y tags ASS."""

    def setUp (self ):
        self .context ={
        "syl":type ("Syl",(),{
        "center":150.0 ,
        "middle":70.0 ,
        "dur":400.0 ,
        "i":1 ,
        "n":3 
        })(),
        "line":type ("Line",(),{
        "color1":"&HFFFFFF&",
        "dur":2000.0 
        })(),
        "fd":40.0 
        }

    def test_basic_arithmetic_expressions (self ):
        res =_eval_num_expr ("10 + 20 * 2",self .context )
        self .assertEqual (res ,50.0 )

    def test_context_variable_expressions (self ):
        res =_eval_num_expr ("syl.center + 10",self .context )
        self .assertEqual (res ,160.0 )

    def test_template_evaluation (self ):
        raw =r"{\an5\pos(syl.center + 10, syl.middle)\fscxy(150)}"
        res =eval_string_template (raw ,self .context )
        self .assertEqual (res ,r"{\an5\pos(160,70)\fscx150\fscy150}")

    def test_stochastic_tags (self ):
        raw =r"\frzR(-30, 30)\1cR()"
        res =eval_string_template (raw ,self .context )
        self .assertIn (r"\frz",res )
        self .assertIn (r"\1c&H",res )

    def test_alpha_tag_evaluation(self):
        self.assertEqual(eval_string_template(r"\alpha(255)", self.context), r"\alpha&HFF&")
        self.assertEqual(eval_string_template(r"\alpha(0)", self.context), r"\alpha&H00&")
        self.assertEqual(eval_string_template(r"\1a(128)", self.context), r"\1a&H80&")
        self.assertEqual(eval_string_template(r"\2a(255)", self.context), r"\2a&HFF&")
        self.assertEqual(eval_string_template(r"\3a(0)", self.context), r"\3a&H00&")
        self.assertEqual(eval_string_template(r"\4a(255)", self.context), r"\4a&HFF&")

    def test_composite_alpha_tags(self):
        self.assertEqual(eval_string_template(r"\134a(255)", self.context), r"\1a&HFF&\3a&HFF&\4a&HFF&")
        self.assertEqual(eval_string_template(r"\13a(128)", self.context), r"\1a&H80&\3a&H80&")
        self.assertEqual(eval_string_template(r"\14a(0)", self.context), r"\1a&H00&\4a&H00&")
        self.assertEqual(eval_string_template(r"\34a(255)", self.context), r"\3a&HFF&\4a&HFF&")
        self.assertEqual(eval_string_template(r"\134a255", self.context), r"\1a&HFF&\3a&HFF&\4a&HFF&")
        self.assertEqual(eval_string_template(r"\134a&H80&", self.context), r"\1a&H80&\3a&H80&\4a&H80&")

    def test_alpha_in_transform_tag(self):
        res = eval_string_template(r"\t(0, 200, \alpha(255))", self.context)
        self.assertEqual(res, r"\t(0,200,\alpha&HFF&)")
        res2 = eval_string_template(r"\t(0, 200, \134a(255))", self.context)
        self.assertEqual(res2, r"\t(0,200,\1a&HFF&\3a&HFF&\4a&HFF&)")

    def test_alpha_dollar_and_stochastic(self):
        ctx = dict(self.context)
        ctx["my_alpha"] = 255
        self.assertEqual(eval_string_template(r"\1a$my_alpha", ctx), r"\1a&HFF&")
        stoch_res = eval_string_template(r"\alphaR(0, 255)", self.context)
        self.assertRegex(stoch_res, r"\\alpha&H[0-9A-F]{2}&")

    def test_alpha_hex_letters_support(self):
        self.assertEqual(eval_string_template(r"\alpha(&H1A&)", self.context), r"\alpha&H1A&")
        self.assertEqual(eval_string_template(r"\1a(&hfa&)", self.context), r"\1a&HFA&")
        self.assertEqual(eval_string_template(r"\2a(&H3C&)", self.context), r"\2a&H3C&")
        self.assertEqual(eval_string_template(r"\3a(&h8c&)", self.context), r"\3a&H8C&")
        self.assertEqual(eval_string_template(r"\4a(&HB4&)", self.context), r"\4a&HB4&")
        self.assertEqual(eval_string_template(r"\134a(&H0E&)", self.context), r"\1a&H0E&\3a&H0E&\4a&H0E&")
        self.assertEqual(eval_string_template(r"\134aFA", self.context), r"\1a&HFA&\3a&HFA&\4a&HFA&")
        self.assertEqual(eval_string_template(r"\134a1a", self.context), r"\1a&H1A&\3a&H1A&\4a&H1A&")

    def test_raw_decimal_alpha_tags(self):
        self.assertEqual(eval_string_template(r"{\4a100}", self.context), r"{\4a&H64&}")
        self.assertEqual(eval_string_template(r"\4a100", self.context), r"\4a&H64&")
        self.assertEqual(eval_string_template(r"\alpha255", self.context), r"\alpha&HFF&")
        self.assertEqual(eval_string_template(r"\1a0", self.context), r"\1a&H00&")
        self.assertEqual(eval_string_template(r"\2a128", self.context), r"\2a&H80&")
        self.assertEqual(eval_string_template(r"\3a50", self.context), r"\3a&H32&")
        self.assertEqual(eval_string_template(r"{\an5\4a100\pos(150, 70)}", self.context), r"{\an5\4a&H64&\pos(150,70)}")

    def test_extended_dark_tags(self):
        # 2D & 3D rotation dark tags
        self.assertEqual(eval_string_template(r"\frxyz(45)", self.context), r"\frx45\fry45\frz45")
        self.assertEqual(eval_string_template(r"\frxy(30)", self.context), r"\frx30\fry30")
        self.assertEqual(eval_string_template(r"\frxz(20)", self.context), r"\frx20\frz20")
        self.assertEqual(eval_string_template(r"\fryz(15)", self.context), r"\fry15\frz15")
        self.assertEqual(eval_string_template(r"\frxyz45", self.context), r"\frx45\fry45\frz45")
        self.assertEqual(eval_string_template(r"\frxy30", self.context), r"\frx30\fry30")
        self.assertEqual(eval_string_template(r"\frxz20", self.context), r"\frx20\frz20")
        self.assertEqual(eval_string_template(r"\fryz15", self.context), r"\fry15\frz15")

        # Multi-channel color dark tags
        self.assertEqual(eval_string_template(r"\1234c(&H00FFFF&)", self.context), r"\1c&H00FFFF&\2c&H00FFFF&\3c&H00FFFF&\4c&H00FFFF&")
        self.assertEqual(eval_string_template(r"\134c(&H00FFFF&)", self.context), r"\1c&H00FFFF&\3c&H00FFFF&\4c&H00FFFF&")
        self.assertEqual(eval_string_template(r"\12c(&H00FFFF&)", self.context), r"\1c&H00FFFF&\2c&H00FFFF&")
        self.assertEqual(eval_string_template(r"\23c(&H00FFFF&)", self.context), r"\2c&H00FFFF&\3c&H00FFFF&")
        self.assertEqual(eval_string_template(r"\1234c&H00FFFF&", self.context), r"\1c&H00FFFF&\2c&H00FFFF&\3c&H00FFFF&\4c&H00FFFF&")

        # Multi-channel alpha dark tags
        self.assertEqual(eval_string_template(r"\1234a(255)", self.context), r"\1a&HFF&\2a&HFF&\3a&HFF&\4a&HFF&")
        self.assertEqual(eval_string_template(r"\12a(128)", self.context), r"\1a&H80&\2a&H80&")
        self.assertEqual(eval_string_template(r"\23a(0)", self.context), r"\2a&H00&\3a&H00&")
        self.assertEqual(eval_string_template(r"\1234a255", self.context), r"\1a&HFF&\2a&HFF&\3a&HFF&\4a&HFF&")

        # Scale, shear, border, shadow dark tags
        self.assertEqual(eval_string_template(r"\fscxy(120)", self.context), r"\fscx120\fscy120")
        self.assertEqual(eval_string_template(r"\faxy(0.5)", self.context), r"\fax0.5\fay0.5")
        self.assertEqual(eval_string_template(r"\xybord(3)", self.context), r"\xbord3\ybord3")
        self.assertEqual(eval_string_template(r"\xyshad(4)", self.context), r"\xshad4\yshad4")
        self.assertEqual(eval_string_template(r"\bs(2)", self.context), r"\bord2\shad2")

        # Dark tags restorations (~)
        ctx = {"line": type("Line", (), {"styleref": type("Style", (), {"color1": "&HFFFFFF&", "color2": "&H0000FF&", "color3": "&H000000&", "color4": "&H000000&", "alpha1": "&H00&", "alpha2": "&H00&", "alpha3": "&H00&", "alpha4": "&H00&", "scale_x": 100, "scale_y": 100, "fontsize": 25, "spacing": 0, "outline": 2, "shadow": 2, "angle": 0})()})()}
        self.assertEqual(eval_string_template(r"\134c~", ctx), r"\1c&HFFFFFF&\3c&H000000&\4c&H000000&")
        self.assertEqual(eval_string_template(r"\1234c~", ctx), r"\1c&HFFFFFF&\2c&H0000FF&\3c&H000000&\4c&H000000&")
        self.assertEqual(eval_string_template(r"\1234a~", ctx), r"\1a&H00&\2a&H00&\3a&H00&\4a&H00&")
        self.assertEqual(eval_string_template(r"\frxyz~", ctx), r"\frx0\fry0\frz0")
        self.assertEqual(eval_string_template(r"\bs~", ctx), r"\bord2\shad2")

    def test_explicit_hex_values_untouched(self):
        raw = r"{\an5\pos(150, 70)\alpha&H80&\1a&HFF&\2a&H00&\3a&H1A&\4a&H3C&\1c&H00FFFF&\3c&H000000&}Texto"
        res = eval_string_template(raw, self.context)
        self.assertEqual(res, r"{\an5\pos(150,70)\alpha&H80&\1a&HFF&\2a&H00&\3a&H1A&\4a&H3C&\1c&H00FFFF&\3c&H000000&}Texto")

        # Explicit hex inside \t transform
        raw_t = r"{\t(0, 300, \alpha&H00&\1a&HFA&)}"
        res_t = eval_string_template(raw_t, self.context)
        self.assertEqual(res_t, r"{\t(0,300,\alpha&H00&\1a&HFA&)}")

    def test_evaluate_ass_line_tag_blocks_with_assdraw(self):
        from string_evaluator import evaluate_ass_line_tag_blocks
        ctx = dict(self.context)
        ctx["center"] = 150.0
        ctx["middle"] = 70.0
        raw_line = r"{\an5\pos($center, $middle)\fscxy(150)}m 0 0 l 100 0 100 100 0 100"
        res_line = evaluate_ass_line_tag_blocks(raw_line, ctx)
        self.assertEqual(res_line, r"{\an5\pos(150,70)\fscx150\fscy150}m 0 0 l 100 0 100 100 0 100")

    def test_evaluate_ass_line_tag_blocks_multiple_blocks(self):
        from string_evaluator import evaluate_ass_line_tag_blocks
        ctx = dict(self.context)
        ctx["j"] = 2
        raw_line = r"{\an5\pos(syl.center + 10, syl.middle)}Hola{\r\frz(!j * 15!)\1c$line.color1}Mundo"
        res_line = evaluate_ass_line_tag_blocks(raw_line, ctx)
        self.assertEqual(res_line, r"{\an5\pos(160,70)}Hola{\r\frz30\1c&HFFFFFF&}Mundo")

    def test_basics_string_node_raw_value(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Basics/String", "properties": {"value": r"\pos($center, $middle)\frz(!j * 15!)"}}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, self.context)
        self.assertEqual(res, r"\pos($center, $middle)\frz(!j * 15!)")

    def test_basics_number_node_in_graph_engine(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Basics/Number", "properties": {"value": "syl.center + 10"}}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, self.context)
        self.assertEqual(res, "160")

    def test_full_pipeline_line_evaluation(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"base_unit": "syl"}},
                {"id": 2, "type": "Basics/String", "properties": {"value": r"\pos($center, $middle)\frz(!j * 15!)\fscxy(150)"}},
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {},
                    "inputs": [
                        {"name": "Flow", "link": 10},
                        {"name": "Layer"},
                        {"name": "Start Time"},
                        {"name": "End Time"},
                        {"name": "Tags", "link": 11},
                        {"name": "Return"}
                    ]
                }
            ],
            "links": [
                [10, 1, 0, 3, 0, "flow"],
                [11, 2, 0, 3, 4, "string"]
            ]
        }
        engine = GraphEngine(graph)
        styles = {'Default': {'Fontname': 'Arial', 'Fontsize': 40, 'PrimaryColour': '&H00FFFFFF&', 'SecondaryColour': '&H000000FF&', 'OutlineColour': '&H00000000&', 'BackColour': '&H00000000&', 'ScaleX': 100, 'ScaleY': 100, 'Spacing': 0, 'Outline': 2, 'Shadow': 0, 'Alignment': 5}}
        dialogues = [{'raw': 'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}Test', 'is_selected': True}]

        engine.process_single(dialogues, styles, allow_fallback_select_all=True)
        self.assertEqual(len(engine.all_generated_lines), 1)
        generated_text = engine.all_generated_lines[0]["text"]
        self.assertIn(r"\pos(", generated_text)
        self.assertIn(r"\fscx150\fscy150", generated_text)
        self.assertIn(r"\frz15", generated_text)

    def test_dark_tags_auto_origin(self):
        ctx = dict(self.context)
        ctx["x"] = 640.0
        ctx["y"] = 360.0
        raw = r"{\fro45\frxo30\fryo60\frxyo(15)\frxzo(20)\fryzo(25)\frxyzo(10)}"
        res = eval_string_template(raw, ctx)
        self.assertIn(r"\org(640,360)\frz45", res)
        self.assertIn(r"\org(640,360)\frx30", res)
        self.assertIn(r"\org(640,360)\fry60", res)
        self.assertIn(r"\org(640,360)\frx15\fry15", res)
        self.assertIn(r"\org(640,360)\frx20\frz20", res)
        self.assertIn(r"\org(640,360)\fry25\frz25", res)
        self.assertIn(r"\org(640,360)\frx10\fry10\frz10", res)

    def test_dark_tags_style_ratios(self):
        ctx = dict(self.context)
        # Standard scale is 100/100 and fontsize is 25 by default in context
        raw = r"{\fscxr1.5\fscyr0.8\fscxyr(2.0)\fsr(1.5)}"
        res = eval_string_template(raw, ctx)
        self.assertIn(r"\fscx150", res)
        self.assertIn(r"\fscy80", res)
        self.assertIn(r"\fscx200\fscy200", res)
        self.assertIn(r"\fs37.5", res)

    def test_dark_tags_contextual_time_transforms(self):
        mock_syl = type("Syl", (), {"start_time": 1000.0, "dur": 500.0, "center": 150.0, "middle": 70.0})()
        ctx = dict(self.context)
        ctx["dur"] = 500.0
        ctx["syl"] = mock_syl
        ctx["active_unit"] = mock_syl

        # \te inverted from end
        raw_te = r"{\te(0, 150, \alpha&HFF&)}"
        res_te = eval_string_template(raw_te, ctx)
        self.assertEqual(res_te, r"{\t(350,500,\alpha&HFF&)}")

        raw_te_single = r"{\te(200, \fscxy(0))}"
        res_te_single = eval_string_template(raw_te_single, ctx)
        self.assertEqual(res_te_single, r"{\t(300,500,\fscx0\fscy0)}")

        # \ts relative to syllable start
        raw_ts = r"{\ts(0, 100, \blur5)}"
        res_ts = eval_string_template(raw_ts, ctx)
        self.assertEqual(res_ts, r"{\t(1000,1100,\blur5)}")

    def test_whitespace_cleaning_in_tag_blocks(self):
        from string_evaluator import clean_tag_block_whitespace
        raw = r"{ \pos( 100 , 200 )   \blur2   \1c&HFFFFFF&   \t( 0 , 150 , \alpha&HFF&  \fscx120 ) }"
        cleaned = clean_tag_block_whitespace(raw)
        self.assertEqual(cleaned, r"{\pos(100,200)\blur2\1c&HFFFFFF&\t(0,150,\alpha&HFF&\fscx120)}")

        # Clip with assdraw preserves vector command spacing
        raw_clip = r"{\clip(  m  0  0  l  100  0  100  100  0  100  )   \blur3}"
        cleaned_clip = clean_tag_block_whitespace(raw_clip)
        self.assertEqual(cleaned_clip, r"{\clip(m 0 0 l 100 0 100 100 0 100)\blur3}")



class TestInterpolatorNode (unittest .TestCase ):
    """Pruebas de interpolacion lineal y acelerada de tags ASS numericos y alfa."""

    def test_interpolator_alpha_tags (self ):
        graph ={
        "nodes":[
        {
        "id":1 ,
        "type":"Functions/Interpolator",
        "properties":{
        "iterador":"5",
        "total":"9",
        "accel":"1.0",
        "v1":"&H00&",
        "v2":"&HFF&"
        },
        "inputs":[
        {"name":"Iterador"},
        {"name":"Total"},
        {"name":"Accel"},
        {"name":"v1","value":"&H00&"},
        {"name":"v2","value":"&HFF&"}
        ]
        }
        ],
        "links":[]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (1 ,{})
        self .assertEqual (res ,"&H80&")

    def test_interpolator_numeric_tags (self ):
        graph ={
        "nodes":[
        {
        "id":1 ,
        "type":"Functions/Interpolator",
        "properties":{
        "iterador":"5",
        "total":"9",
        "accel":"1.0",
        "v1":"100",
        "v2":"200"
        },
        "inputs":[
        {"name":"Iterador"},
        {"name":"Total"},
        {"name":"Accel"},
        {"name":"v1","value":"100"},
        {"name":"v2","value":"200"}
        ]
        }
        ],
        "links":[]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (1 ,{})
        self .assertEqual (res ,"150")


if __name__ =="__main__":
    unittest .main ()

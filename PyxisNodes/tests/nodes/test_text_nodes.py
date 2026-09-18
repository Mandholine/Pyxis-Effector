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

"""Pruebas unitarias para nodos de texto, trazado sobre rutas vectoriales y metricas tipograficas."""

import unittest 
from ass_parser import KaraokeProcessor 
from models import PyxisLine ,PyxisUnit 
from nodes .text_nodes import eval_text_node ,text_to_shape_node ,text_on_path_core ,text_on_path_node 
from nodes .shape_nodes import shape_circle 
from node_engine import GraphEngine 


class TestUnifiedTextNode (unittest .TestCase ):
    """Unit tests for the unified Text master node and string manipulation."""

    def setUp (self ):
        self .context ={
        'active_unit':type ('Unit',(),{'text':r'{\pos(100,200)}Hola Mundo','text_stripped':'Hola Mundo'})(),
        'active_line':type ('Line',(),{'text':r'{\pos(100,200)}Hola Mundo','text_stripped':'Hola Mundo'})()
        }

    def test_op_strip_tags (self ):
        res =eval_text_node (self .context ,operation ="Strip Tags",Text =r"{\b1\pos(10,20)}Prueba\NText")
        self .assertEqual (res ,"Prueba Text")

    def test_op_uppercase (self ):
        res =eval_text_node (self .context ,operation ="Uppercase",Text ="kara effector")
        self .assertEqual (res ,"KARA EFFECTOR")

    def test_op_lowercase (self ):
        res =eval_text_node (self .context ,operation ="Lowercase",Text ="PYXIS NODES")
        self .assertEqual (res ,"pyxis nodes")

    def test_op_replace (self ):
        res =eval_text_node (self .context ,operation ="Replace",Text ="Hola Mundo",Search ="Mundo",Replace ="Pyxis")
        self .assertEqual (res ,"Hola Pyxis")

    def test_op_substring (self ):
        res =eval_text_node (self .context ,operation ="Substring",Text ="Antigravity",Start =0 ,Length =4 )
        self .assertEqual (res ,"Anti")

    def test_op_length (self ):
        res =eval_text_node (self .context ,operation ="Length",Text ="PyxisNodes")
        self .assertEqual (res ,"10")

    def test_op_contains_true (self ):
        res =eval_text_node (self .context ,operation ="Contains",Text ="Efecto Visual",Search ="Efecto")
        self .assertEqual (res ,"1")

    def test_op_contains_false (self ):
        res =eval_text_node (self .context ,operation ="Contains",Text ="Efecto Visual",Search ="Audio")
        self .assertEqual (res ,"0")

    def test_op_kana_romaji_hiragana (self ):
        res =eval_text_node (self .context ,operation ="Kana",Text ="sakura",Mode ="Romaji to Hiragana")
        self .assertEqual (res ,"さくら")

    def test_op_kana_romaji_katakana (self ):
        res =eval_text_node (self .context ,operation ="Kana",Text ="sakura",Mode ="Romaji to Katakana")
        self .assertEqual (res ,"サクラ")

    def test_op_romaji_to_karaoke_basic (self ):
        res = eval_text_node(self.context, operation="Romaji to Karaoke", Text="sakura", Duration=30)
        self.assertEqual(res, r"{\k10}sa{\k10}ku{\k10}ra")

    def test_op_romaji_to_karaoke_phrase_and_spaces (self ):
        res = eval_text_node(self.context, operation="Romaji to Karaoke", Text="inochi aru subete no mono yo", Duration=240)
        self.assertEqual(res, r"{\k20}i{\k20}no{\k20}chi {\k20}a{\k20}ru {\k20}su{\k20}be{\k20}te {\k20}no {\k20}mo{\k20}no {\k20}yo")

    def test_op_romaji_to_karaoke_kmodes (self ):
        res_kf = eval_text_node(self.context, operation="Romaji to Karaoke", Text="sakura", kmode="kf", Duration=30)
        self.assertEqual(res_kf, r"{\kf10}sa{\kf10}ku{\kf10}ra")

        res_ko = eval_text_node(self.context, operation="Romaji to Karaoke", Text="kappatsu", kmode="ko", Duration=80)
        self.assertEqual(res_ko, r"{\ko20}ka{\ko20}p{\ko20}pa{\ko20}tsu")

    def test_op_romaji_to_karaoke_context_duration (self ):
        ctx = {
            'active_unit': type('Unit', (), {'text': 'tokyo', 'text_stripped': 'tokyo', 'duration': 400})(),
            'active_line': type('Line', (), {'text': 'tokyo', 'text_stripped': 'tokyo', 'duration': 400})()
        }
        res = eval_text_node(ctx, operation="Romaji to Karaoke")
        # 400ms = 40cs distributed between 2 syllables ('to', 'kyo') -> 20cs each
        self.assertEqual(res, r"{\k20}to{\k20}kyo")

    def test_graph_engine_text_node_evaluation (self ):
        text_node ={
        "id":1 ,
        "type":"Text",
        "properties":{"operation":"Replace"},
        "inputs":[
        {"name":"Text","value":"Pyxis V1"},
        {"name":"Search","value":"V1"},
        {"name":"Replace With","value":"V2"}
        ]
        }
        graph_data ={"nodes":[text_node ],"links":[]}
        engine =GraphEngine (graph_data )
        res =engine .evaluate_data_node (1 ,{})
        self .assertEqual (res ,"Pyxis V2")

    def test_graph_engine_romaji_to_karaoke_evaluation (self ):
        text_node = {
            "id": 1,
            "type": "Text",
            "properties": {"operation": "Romaji to Karaoke", "k_mode": "kf"},
            "inputs": [
                {"name": "Text", "value": "tsubasa"},
                {"name": "Duration (cs)", "value": "60"}
            ]
        }
        graph_data = {"nodes": [text_node], "links": []}
        engine = GraphEngine(graph_data)
        res = engine.evaluate_data_node(1, {})
        self.assertEqual(res, r"{\kf20}tsu{\kf20}ba{\kf20}sa")


class DummyUnit :
    def __init__ (self ,i =1 ,n =4 ,left =100.0 ,center =120.0 ,width =40.0 ,height =30.0 ,middle =50.0 ):
        self .i =i 
        self .n =n 
        self .left =left 
        self .center =center 
        self .width =width 
        self .height =height 
        self .middle =middle 


class DummyLine :
    def __init__ (self ,left =100.0 ,width =160.0 ,center =180.0 ,middle =50.0 ,text ="Test Line"):
        self .left =left 
        self .width =width 
        self .center =center 
        self .middle =middle 
        self .text =text 
        self .raw_text =text 


class TestTextOnPath (unittest .TestCase ):
    """Pruebas para el nodo Text on Path (trazado tipografico sobre curvas vectoriales)."""

    def setUp (self ):
        self .line =DummyLine ()
        self .u1 =DummyUnit (1 ,4 ,left =100.0 ,center =120.0 ,width =40.0 )
        self .u2 =DummyUnit (2 ,4 ,left =140.0 ,center =160.0 ,width =40.0 )

    def test_straight_line_center_mode (self ):
        line_shape ="m 0 0 l 400 0 "
        ctx ={'active_unit':self .u1 ,'active_line':self .line }

        tag_out ,pos_str ,frz_str ,x_val ,y_val ,total_len ,target_dist =text_on_path_core (
        line_shape ,
        context =ctx ,
        mode ="Center (Centrado)",
        offset =0.0 
        )

        self .assertEqual (total_len ,400.0 )
        self .assertEqual (target_dist ,140.0 )
        self .assertEqual (x_val ,140.0 )
        self .assertEqual (y_val ,0.0 )
        self .assertEqual (frz_str ,"\\frz0")
        self .assertTrue (pos_str .startswith ("\\pos(140"))

    def test_straight_line_left_and_right_modes (self ):
        line_shape ="m 0 0 l 400 0 "
        ctx ={'active_unit':self .u1 ,'active_line':self .line }


        tag_out ,pos_str ,frz_str ,x_val ,y_val ,total_len ,target_dist =text_on_path_core (
        line_shape ,context =ctx ,mode ="Left (Izquierda)",offset =0.0 
        )
        self .assertEqual (x_val ,20.0 )
        self .assertEqual (target_dist ,20.0 )


        tag_out ,pos_str ,frz_str ,x_val ,y_val ,total_len ,target_dist =text_on_path_core (
        line_shape ,context =ctx ,mode ="Right (Derecha)",offset =0.0 
        )
        self .assertEqual (x_val ,260.0 )
        self .assertEqual (target_dist ,260.0 )

    def test_vertical_line_tangent_angle (self ):
        vert_shape ="m 50 50 l 50 250 "
        ctx ={'active_unit':self .u1 ,'active_line':self .line }

        tag_out ,pos_str ,frz_str ,x_val ,y_val ,total_len ,target_dist =text_on_path_core (
        vert_shape ,context =ctx ,mode ="Left",offset =0.0 
        )
        self .assertEqual (total_len ,200.0 )
        self .assertEqual (x_val ,50.0 )
        self .assertEqual (y_val ,70.0 )
        self .assertEqual (frz_str ,"\\frz-90")
        self .assertIn ("\\frz-90",tag_out )


class TestRealWidthAndKerning (unittest .TestCase ):
    """Pruebas de precision metrica y calculo de dimensiones tipograficas."""

    def _process (self ,raw ,style =None ):
        proc =KaraokeProcessor (1280 ,720 ,41.708 )
        if style is None :
            style ={"Fontname":"Arial","Fontsize":"40","MarginL":"10","MarginR":"10","MarginV":"30","Alignment":"2"}
        return proc .process_line (raw ,style )

    def test_line_width_calculated (self ):
        raw ="Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola"
        line =self ._process (raw )
        self .assertIsNotNone (line )
        self .assertGreater (line .width ,0.0 )

    def test_alignment_bottom_center (self ):
        raw ="Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola"
        line =self ._process (raw )
        expected_center =1280.0 /2.0 
        self .assertAlmostEqual (line .center ,expected_center ,delta =1.0 )


class TestBasicsANodes(unittest.TestCase):
    """Pruebas unitarias para el micro-lote Basics-A: Number, String, Text, Color Picker."""

    def test_basics_number_node(self):
        node = {
            "id": 1,
            "type": "Basics/Number",
            "properties": {"value": "42.5"}
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        res = engine.evaluate_data_node(1, {})
        self.assertEqual(res, "42.5")

    def test_basics_string_node(self):
        node = {
            "id": 2,
            "type": "Basics/String",
            "properties": {"value": "Hello Pyxis"}
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        res = engine.evaluate_data_node(2, {})
        self.assertEqual(res, "Hello Pyxis")

    def test_basics_text_node_clean_spaces(self):
        node = {
            "id": 3,
            "type": "Basics/Text",
            "properties": {"operation": "clean_spaces"},
            "inputs": [{"name": "Text", "value": "  Pyxis   Effector   2026  "}]
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        res = engine.evaluate_data_node(3, {})
        self.assertEqual(res, "Pyxis Effector 2026")

    def test_basics_color_picker_node(self):
        node = {
            "id": 4,
            "type": "Basics/Color Picker",
            "properties": {
                "colors": ["#FF0000", "#00FF00"],
                "formats": ["ASS", "HEX"]
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        res_palette = engine.evaluate_data_node(4, {}, output_slot_index=0)
        self.assertIn("&H0000FF&", res_palette)
        self.assertIn("#00FF00", res_palette)

    def test_text_on_path_canonical_lowercase(self):
        node = {
            "id": 5,
            "type": "Functions/Text on Path",
            "properties": {
                "shape": "m 0 0 l 200 0",
                "mode": "center",
                "offset": "0",
                "extra_angle": "0",
                "subdivs": "30"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        tag_out = engine.evaluate_data_node(5, {}, output_slot_index=0)
        pos_tag = engine.evaluate_data_node(5, {}, output_slot_index=1)
        frz_tag = engine.evaluate_data_node(5, {}, output_slot_index=2)

        self.assertIn(r"\pos(", pos_tag)
        self.assertIn(r"\pos(", tag_out)

    def test_text_to_shape_canonical(self):
        node = {
            "id": 6,
            "type": "Functions/Text to Shape",
            "properties": {
                "text": "A",
                "font_name": "Arial",
                "font_size": "40",
                "scale": "1.0"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        shp_out = engine.evaluate_data_node(6, {}, output_slot_index=0)
        w_out = engine.evaluate_data_node(6, {}, output_slot_index=1)
        h_out = engine.evaluate_data_node(6, {}, output_slot_index=2)

        self.assertTrue(shp_out.startswith("m ") or shp_out.startswith("m-") or shp_out.startswith("m0"))
        self.assertTrue(float(w_out) > 0.0)
        self.assertTrue(float(h_out) > 0.0)


if __name__ == "__main__":
    unittest.main()


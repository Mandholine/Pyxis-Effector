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

r"""Pruebas unitarias completas y de paridad para los 4 nodos de la Etapa 3:
1. Text to Shape (Multi-ranura: Shape Out, Width, Height)
2. IMG to Shape (Multi-ranura: Shape Out, Width, Height, Puntos, Shapes Array, Total Frames)
3. IMG to Pixels / Imagen a Partículas (Multi-ranura: Shp Out, Color Arr, \pos Tag, X Arr, Y Arr, Total, Pixels Array)
4. Shapes Library / Shapes Lib (Catálogo de 80 formas vectoriales en 10 categorías)
"""

import unittest 
import numpy as np 
from node_engine import GraphEngine 
from models import PyxisLine ,PyxisUnit 
from nodes .shape_nodes import eval_shapes_lib_node ,RAW_PRESET_SHAPES ,SHAPES_LIB_MAP 
from nodes .text_nodes import text_to_shape_node 
from particle_nodes import particle_image_node ,sort_particles 


class TestEtapa3TextToShape (unittest .TestCase ):
    """Pruebas para el nodo Text to Shape."""

    def setUp (self ):
        self .context ={
        'active_unit':type ('Unit',(),{'text':'A','text_stripped':'A','height':50.0 })(),
        'active_line':type ('Line',(),{'text':'A','text_stripped':'A','styleref':type ('Style',(),{'fontname':'Arial','fontsize':40.0 ,'bold':False ,'italic':False })()})(),
        'i':1 
        }

    def test_text_to_shape_direct_call (self ):
        shape_str =text_to_shape_node (self .context ,text ="A",font_name ="Arial",font_size =50 ,scale =1.0 )
        self .assertIsInstance (shape_str ,str )
        self .assertTrue (shape_str .startswith ("m ")or "m "in shape_str )

    def test_text_to_shape_in_graphengine_multislot (self ):
        graph ={
        "nodes":[
        {
        "id":1 ,
        "type":"Functions/Text to Shape",
        "properties":{"text":"PYXIS","font_name":"Arial","font_size":"60","scale":"1.0"},
        "inputs":[],
        "outputs":[
        {"name":"Shape Out","type":"shape","slot_index":0 },
        {"name":"Width","type":"number","slot_index":1 },
        {"name":"Height","type":"number","slot_index":2 }
        ]
        }
        ],
        "links":[]
        }
        engine =GraphEngine (graph )
        shape_val =engine .evaluate_data_node (1 ,self .context ,output_slot_index =0 )
        width_val =engine .evaluate_data_node (1 ,self .context ,output_slot_index =1 )
        height_val =engine .evaluate_data_node (1 ,self .context ,output_slot_index =2 )

        self .assertTrue (shape_val .startswith ("m ")or "m "in shape_val )
        self .assertGreater (float (width_val ),0.0 )
        self .assertGreater (float (height_val ),0.0 )


class TestEtapa3ShapesLibrary (unittest .TestCase ):
    """Pruebas para el nodo maestro Shapes Library con 80 formas vectoriales."""

    def setUp (self ):
        self .context ={'i':1 }

    def test_all_categories_in_shapes_lib (self ):
        expected_categories =[
        "Formas","Corazones","Brillos","Especiales","Musica",
        "Estrellas","Sakura","Nieve","Flores","Geometria"
        ]
        for cat in expected_categories :
            res =eval_shapes_lib_node (self .context ,categoria =cat ,forma ="Circulo"if cat =="Formas"else None )
            self .assertTrue (isinstance (res ,str )and len (res )>5 )

    def test_shapes_library_graphengine (self ):
        graph ={
        "nodes":[
        {
        "id":1 ,
        "type":"Shape/Library",
        "properties":{"categoria":"Formas","forma":"Estrella"},
        "inputs":[],
        "outputs":[{"name":"Shape","type":"shape","slot_index":0 }]
        }
        ],
        "links":[]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (1 ,self .context ,output_slot_index =0 )
        self .assertTrue (isinstance (res ,str )and res .startswith ("m "))


class TestEtapa3ImgToPixels (unittest .TestCase ):
    """Pruebas para el nodo IMG to Pixels / Imagen a Partículas."""

    def setUp (self ):
        self .context ={
        'active_unit':type ('Unit',(),{'center':100.0 ,'middle':200.0 ,'i':1 ,'n':1 })(),
        'active_line':type ('Line',(),{'center':100.0 ,'middle':200.0 })(),
        'i':1 
        }

    def test_img_to_pixels_fallback_evaluation (self ):

        abs_x ,abs_y ,col_ass ,alpha_ass ,p_shape ,total_px =particle_image_node (
        self .context ,image_path ="",particle_shape ="",frame ="1",step =2 ,alpha_threshold =128 
        )
        self .assertEqual (abs_x ,100.0 )
        self .assertEqual (abs_y ,200.0 )
        self .assertEqual (col_ass ,"&HFFFFFF&")
        self .assertEqual (alpha_ass ,"&H00&")
        self .assertEqual (total_px ,1 )

    def test_img_to_pixels_graphengine_slots (self ):
        graph ={
        "nodes":[
        {
        "id":1 ,
        "type":"Functions/IMG to Pixels",
        "properties":{
        "image_path":"",
        "particle_shape":"m 0 0 l 2 0 l 2 2 l 0 2",
        "frame":"1",
        "step":"2",
        "alpha_threshold":"128",
        "scale":"1.0",
        "anchor":"Center",
        "order":"79"
        },
        "inputs":[],
        "outputs":[
        {"name":"Shp Out","type":"data","slot_index":0 },
        {"name":"Color Arr","type":"data","slot_index":1 },
        {"name":"\\pos Tag","type":"data","slot_index":2 },
        {"name":"X Arr","type":"data","slot_index":3 },
        {"name":"Y Arr","type":"data","slot_index":4 },
        {"name":"Total","type":"data","slot_index":5 },
        {"name":"Pixels Array","type":"data","slot_index":6 }
        ]
        }
        ],
        "links":[]
        }
        engine =GraphEngine (graph )
        slot0 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =0 )
        slot1 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =1 )
        slot2 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =2 )
        slot3 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =3 )
        slot4 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =4 )
        slot5 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =5 )
        slot6 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =6 )

        self .assertIn (r"\pos(100.0,200.0)",slot0 )
        self .assertEqual (slot1 ,"&HFFFFFF&")
        self .assertEqual (slot2 ,r"\pos(100.0,200.0)")
        self .assertEqual (slot3 ,"100.0")
        self .assertEqual (slot4 ,"200.0")
        self .assertEqual (slot5 ,"1")
        self .assertIn (r"\pos(100.0,200.0)",slot6 )


class TestEtapa3ImgToShape (unittest .TestCase ):
    """Pruebas para el nodo IMG to Shape."""

    def setUp (self ):
        self .context ={'i':1 }

    def test_img_to_shape_graphengine_slots (self ):
        graph ={
        "nodes":[
        {
        "id":1 ,
        "type":"Shape/IMG to Shape",
        "properties":{
        "image_path":"",
        "frame_idx":"1",
        "threshold":"128",
        "tolerance":"1.0",
        "alphamax":"1.0",
        "opttoler":"0.2",
        "out_scale":"1.0",
        "out_w":"0.0",
        "out_h":"0.0",
        "offset_x":"0.0",
        "offset_y":"0.0",
        "img_scale":"1.0",
        "bin_mode":"Luminance",
        "mode":"Potrace",
        "anchor":"Center",
        "invert":"Normal",
        "invert_img":"Normal"
        },
        "inputs":[],
        "outputs":[
        {"name":"Shape Out","type":"shape","slot_index":0 },
        {"name":"Width","type":"number","slot_index":1 },
        {"name":"Height","type":"number","slot_index":2 },
        {"name":"Puntos","type":"number","slot_index":3 },
        {"name":"Shapes Array","type":"data","slot_index":4 },
        {"name":"Total Frames","type":"number","slot_index":5 }
        ]
        }
        ],
        "links":[]
        }
        engine =GraphEngine (graph )
        slot0 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =0 )
        slot1 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =1 )
        slot2 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =2 )
        slot3 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =3 )
        slot4 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =4 )
        slot5 =engine .evaluate_data_node (1 ,self .context ,output_slot_index =5 )

        self .assertEqual (slot0 ,"")
        self .assertEqual (float (slot1 ),0.0 )
        self .assertEqual (float (slot2 ),0.0 )
        self .assertEqual (int (slot3 ),0 )
        self .assertEqual (slot4 ,"")
        self .assertEqual (int (slot5 ),1 )

    def test_img_to_shape_english_parameters(self):
        from img_tracer_engine import _trace_python_native
        from PIL import Image
        img = Image.new('RGBA', (20, 20), (255, 255, 255, 255))
        # Test Silhouette binarize mode in English
        res_sil = _trace_python_native(img, mode="Polygon", threshold=128, invert=False, tolerance=1.0, bin_mode="Silhouette")
        self.assertTrue(isinstance(res_sil, str))
        # Test Inverted in English
        res_inv = _trace_python_native(img, mode="Polygon", threshold=128, invert=True, tolerance=1.0, bin_mode="Luminance")
        self.assertTrue(isinstance(res_inv, str))


if __name__ =="__main__":
    unittest .main ()

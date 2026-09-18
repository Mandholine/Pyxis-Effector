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

"""Pruebas unitarias completas para nodos de formas vectoriales (Shape Nodes).

Incluye:
- Shapes Library (80 formas maestras y alias)
- Shape Slicer (los 22 motores de corte poligonal)
- Shape Walker (recorredor y segmentacion de curvas de Bezier y lineas)
- Transformaciones avanzadas (escalado, rotacion, pivote, deformaciones)
- Bordes concentricos y Clip Gradient
"""

import math 
import unittest 

from clipper_engine import ClipperEngine 
from node_engine import GraphEngine 
from nodes .shape_nodes import (
eval_shapes_lib_node ,
RAW_PRESET_SHAPES ,
SHAPES_LIB_MAP ,
parse_assdraw_segments ,
shape_walker_core ,
shape_walker_node ,
shape_manipulator ,
shape_filter ,
shape_transform ,
shape_concentric_borders_node ,
clip_gradient_node ,
sort_1d_indices ,
shape_union_divide_node 
)

ALL_22_ENGINES =[
"Rejilla 1D/2D",
"hex",
"tri",
"dia",
"ring",
"ray",
"quad",
"bez",
"jigsaw",
"voronoi",
"delaunay",
"ashlar",
"brick",
"mondrian",
"herringbone",
"scallop",
"web",
"rhombille",
"octagon",
"kagome",
"truchet",
"circuit",
"pattern"
]

TEST_SHAPE_SQUARE ="m 0 0 l 100 0 l 100 100 l 0 100"
TEST_SHAPE_COMPLEX ="m 0 0 l 200 0 l 200 50 l 50 50 l 50 150 l 200 150 l 200 200 l 0 200"


class TestShapesLibrary (unittest .TestCase ):
    """Pruebas para la biblioteca de 80 formas vectoriales de Pyxis."""

    def setUp (self ):
        self .context ={}

    def test_all_80_shapes_return_non_empty_ass_draw (self ):
        self .assertGreaterEqual (len (RAW_PRESET_SHAPES ),80 )
        for forma_key in RAW_PRESET_SHAPES .keys ():
            with self .subTest (forma =forma_key ):
                res =eval_shapes_lib_node (self .context ,forma =forma_key )
                self .assertTrue (isinstance (res ,str )and len (res )>5 ,f"Fallo forma '{forma_key }'")
                self .assertTrue (res .startswith ("m "),f"Forma '{forma_key }' no inicia con 'm '")

    def test_shortened_and_legacy_names (self ):
        pairs =[
        ("Esq. Curva","Esquinas Redondeadas"),
        ("Estrella 4","Estrella de 4 Puntas"),
        ("Flecha Der.","Flecha Derecha"),
        ("Globo Texto","Burbuja de Dialogo"),
        ]
        for short_name ,long_name in pairs :
            if short_name in SHAPES_LIB_MAP and long_name in SHAPES_LIB_MAP :
                res1 =eval_shapes_lib_node (self .context ,forma =short_name )
                res2 =eval_shapes_lib_node (self .context ,forma =long_name )
                self .assertEqual (res1 ,res2 ,f"Discrepancia entre alias '{short_name }' y '{long_name }'")


class TestShapeSlicer (unittest .TestCase ):
    """Pruebas para el motor de segmentacion poligonal y los 22 algoritmos de corte."""

    def test_all_22_engines_direct_slicing (self ):
        for engine in ALL_22_ENGINES :
            with self .subTest (engine =engine ):
                pieces =ClipperEngine .slice_grid (
                TEST_SHAPE_SQUARE ,
                engine_mode =engine ,
                cols =3 ,
                rows =3 ,
                size_x =20 ,
                size_y =20 ,
                accel_x =1.0 ,
                accel_y =1.0 ,
                order =79 
                )
                self .assertGreater (len (pieces ),0 ,f"Motor '{engine }' no genero piezas.")
                for idx ,p in enumerate (pieces ):
                    code =p .get ("code","")
                    cx =p .get ("cx")
                    cy =p .get ("cy")
                    self .assertTrue (code and str (code ).strip ().startswith ("m "),f"Pieza {idx } de {engine } invalida")
                    self .assertIsNotNone (cx )
                    self .assertIsNotNone (cy )
                    self .assertFalse (math .isnan (cx ))
                    self .assertFalse (math .isnan (cy ))

    def test_complex_non_convex_shape (self ):
        for engine in ALL_22_ENGINES :
            with self .subTest (engine =engine ):
                pieces =ClipperEngine .slice_grid (
                TEST_SHAPE_COMPLEX ,
                engine_mode =engine ,
                cols =4 ,
                rows =4 ,
                size_x =25 ,
                size_y =25 ,
                overlap =1.0 
                )
                self .assertGreater (len (pieces ),0 ,f"Fallo motor '{engine }' en silueta compleja")
                for p in pieces :
                    self .assertTrue (p .get ("code","").startswith ("m "))

    def test_shape_slicer_graph_engine_evaluation (self ):
        for engine in ALL_22_ENGINES :
            with self .subTest (engine =engine ):
                node ={
                "id":101 ,
                "type":"Shape/Slicer",
                "properties":{
                "modo":engine ,
                "shape":TEST_SHAPE_SQUARE ,
                "Cols":2 ,
                "Rows":2 ,
                "Size X":20 ,
                "Size Y":20 ,
                "out_mode":"shape"
                },
                "inputs":[]
                }
                engine_inst =GraphEngine ({"nodes":[node ],"links":[]})
                ctx ={"j":1 }
                out_shape =engine_inst .evaluate_data_node (101 ,ctx )
                self .assertTrue (isinstance (out_shape ,str )and out_shape .startswith ("m "),f"Fallo evaluacion de {engine }")

    def test_spatial_sorting_radial (self ):
        pieces =ClipperEngine .slice_grid (
        TEST_SHAPE_SQUARE ,
        engine_mode ="hex",
        size_x =15 ,
        order =5 
        )
        self .assertGreaterEqual (len (pieces ),2 )
        d_first =math .sqrt ((pieces [0 ]["cx"]-50 )**2 +(pieces [0 ]["cy"]-50 )**2 )
        d_last =math .sqrt ((pieces [-1 ]["cx"]-50 )**2 +(pieces [-1 ]["cy"]-50 )**2 )
        self .assertLessEqual (d_first ,d_last +1.0 )


class TestShapeWalker (unittest .TestCase ):
    """Pruebas del algoritmo de recorrido de trazados y recorte parametrico."""

    def test_parse_segments_line (self ):
        shape ="m 0 0 l 100 0 l 100 50"
        contours =parse_assdraw_segments (shape )
        self .assertEqual (len (contours ),1 )
        self .assertEqual (contours [0 ]['start'],(0.0 ,0.0 ))
        self .assertEqual (len (contours [0 ]['segments']),2 )
        self .assertEqual (contours [0 ]['segments'][0 ]['type'],'l')
        self .assertEqual (contours [0 ]['segments'][0 ]['p0'],(0.0 ,0.0 ))
        self .assertEqual (contours [0 ]['segments'][0 ]['p1'],(100.0 ,0.0 ))

    def test_parse_segments_bezier (self ):
        shape ="m 0 0 b 25 50 75 50 100 0"
        contours =parse_assdraw_segments (shape )
        self .assertEqual (len (contours ),1 )
        self .assertEqual (len (contours [0 ]['segments']),1 )
        b_seg =contours [0 ]['segments'][0 ]
        self .assertEqual (b_seg ['type'],'b')
        self .assertEqual (b_seg ['p0'],(0.0 ,0.0 ))
        self .assertEqual (b_seg ['p1'],(25.0 ,50.0 ))
        self .assertEqual (b_seg ['p2'],(75.0 ,50.0 ))
        self .assertEqual (b_seg ['p3'],(100.0 ,0.0 ))

    def test_line_cut_half (self ):
        shape ="m 0 0 l 100 0"
        cut_shp ,tx ,ty ,angle ,cut_len ,total_len =shape_walker_core (shape ,progress =0.5 ,start_t =0.0 )
        self .assertIn ("m 0 0",cut_shp )
        self .assertIn ("l 50",cut_shp )
        self .assertAlmostEqual (tx ,50.0 ,delta =0.1 )
        self .assertAlmostEqual (ty ,0.0 ,delta =0.1 )
        self .assertAlmostEqual (cut_len ,50.0 ,delta =0.1 )
        self .assertAlmostEqual (total_len ,100.0 ,delta =0.1 )

    def test_line_cut_window_trim (self ):
        shape ="m 0 0 l 100 0"
        cut_shp ,tx ,ty ,angle ,cut_len ,total_len =shape_walker_core (shape ,progress =0.7 ,start_t =0.2 )
        self .assertIn ("m 20",cut_shp )
        self .assertIn ("l 70",cut_shp )
        self .assertAlmostEqual (tx ,70.0 ,delta =0.1 )
        self .assertAlmostEqual (ty ,0.0 ,delta =0.1 )
        self .assertAlmostEqual (cut_len ,50.0 ,delta =0.1 )

    def test_shape_walker_node_pure_shape_out (self ):
        shape ="m 0 0 l 100 0"
        final_shp ,pos_str ,angle ,cut_len ,tip_x ,tip_y =shape_walker_node (None ,shape =shape ,progress =0.5 )
        self .assertTrue (final_shp .startswith ("m "))
        self .assertNotIn ("\\pos",final_shp )
        self .assertNotIn ("{\\",final_shp )

    def test_shape_walker_node_unit_position_inheritance (self ):
        class DummyUnit :
            center =640.0 
            middle =360.0 
        ctx ={"active_unit":DummyUnit ()}
        shape ="m 0 0 l 100 0"
        final_shp ,pos_str ,angle ,cut_len ,tip_x ,tip_y =shape_walker_node (ctx ,shape =shape ,progress =0.5 )
        self .assertEqual (tip_x ,690.0 )
        self .assertEqual (tip_y ,360.0 )
        self .assertEqual (pos_str ,"\\pos(690,360)")
        self .assertTrue (final_shp .startswith ("m "))
        self .assertNotIn ("\\pos",final_shp )

    def test_shape_walker_node_line_position_inheritance (self ):
        class DummyLine :
            center =500.0 
            middle =200.0 
        ctx ={"active_line":DummyLine ()}
        shape ="m 0 0 l 100 0"
        final_shp ,pos_str ,angle ,cut_len ,tip_x ,tip_y =shape_walker_node (ctx ,shape =shape ,progress =0.5 )
        self .assertEqual (tip_x ,550.0 )
        self .assertEqual (tip_y ,200.0 )
        self .assertEqual (pos_str ,"\\pos(550,200)")

    def test_shape_walker_node_fx_override (self ):
        class DummyUnit :
            center =640.0 
            middle =360.0 
        ctx ={"active_unit":DummyUnit (),"fx_pos_x":100.0 ,"fx_pos_y":50.0 }
        shape ="m 0 0 l 100 0"
        final_shp ,pos_str ,angle ,cut_len ,tip_x ,tip_y =shape_walker_node (ctx ,shape =shape ,progress =0.5 )
        self .assertEqual (tip_x ,150.0 )
        self .assertEqual (tip_y ,50.0 )
        self .assertEqual (pos_str ,"\\pos(150,50)")

    def test_shape_walker_node_no_context_fallback (self ):
        shape ="m 0 0 l 100 0"
        final_shp ,pos_str ,angle ,cut_len ,tip_x ,tip_y =shape_walker_node (None ,shape =shape ,progress =0.5 )
        self .assertEqual (tip_x ,50.0 )
        self .assertEqual (tip_y ,0.0 )
        self .assertEqual (pos_str ,"\\pos(50,0)")


class TestShapeTransformAdvanced (unittest .TestCase ):
    """Pruebas de transformacion, rotacion, pivote y deformaciones."""

    def test_shape_manipulator_scale (self ):
        shape ="m 0 0 l 100 0 l 100 100 l 0 100"
        transformed =shape_manipulator (None ,drawing =shape ,scale_x =2.0 ,scale_y =2.0 ,mode ="origin")
        self .assertTrue (transformed .startswith ("m 0 0"))
        self .assertIn ("l 200 0",transformed )
        self .assertIn ("l 200 200",transformed )

    def test_shape_manipulator_translation (self ):
        shape ="m 0 0 l 10 0"
        transformed =shape_manipulator (None ,drawing =shape ,offset_x =50.0 ,offset_y =30.0 ,mode ="origin")
        self .assertTrue (transformed .startswith ("m 50 30"))
        self .assertIn ("l 60 30",transformed )

    def test_shape_manipulator_redraw_densify (self ):

        shape ="m 0 0 b 0 50 50 100 100 100"

        redrawn =shape_manipulator (None ,drawing =shape ,op_mode ="Redibujar",density =10.0 )
        self .assertTrue (redrawn .startswith ("m 0 0"))
        self .assertIn ("b ",redrawn )

        b_count =redrawn .count ("b ")
        self .assertGreater (b_count ,1 )

    def test_shape_manipulator_redraw_simplify (self ):

        shape ="m 0 0 b 0 50 50 100 100 100"

        simplified =shape_manipulator (None ,drawing =shape ,op_mode ="Redibujar",density =-25.0 )
        self .assertTrue (simplified .startswith ("m 0 0"))
        self .assertNotIn ("b ",simplified )
        self .assertIn ("l ",simplified )

    def test_shape_manipulator_rotate_3d (self ):
        shape ="m -50 -50 l 50 -50 l 50 50 l -50 50"
        rotated =shape_manipulator (None ,drawing =shape ,op_mode ="Giro 3D",angle_x =45.0 ,angle_y =30.0 ,angle_z =60.0 )
        self .assertTrue (rotated .startswith ("m "))
        self .assertIn ("l ",rotated )
        tokens =rotated .split ()
        self .assertEqual (len (tokens ),12 )

    def test_shape_manipulator_rotate_3d_z_pure (self ):
        shape ="m -50 -50 l 50 -50 l 50 50 l -50 50"

        rotated =shape_manipulator (None ,drawing =shape ,op_mode ="Giro 3D",angle_x =0.0 ,angle_y =0.0 ,angle_z =90.0 )
        self .assertTrue (rotated .startswith ("m 50 -50"))
        self .assertIn ("l 50 50",rotated )
        self .assertIn ("l -50 50",rotated )
        self .assertIn ("l -50 -50",rotated )

    def test_shape_manipulator_reflect_y (self ):
        shape ="m 10 10 l 20 10 l 20 30 l 10 30"

        reflected =shape_manipulator (None ,drawing =shape ,op_mode ="Reflejar",axis ="y")
        self .assertTrue (reflected .startswith ("m 20 10"))
        self .assertIn ("l 10 10",reflected )
        self .assertIn ("l 10 30",reflected )
        self .assertIn ("l 20 30",reflected )

    def test_shape_manipulator_reflect_x (self ):
        shape ="m 10 10 l 20 10 l 20 30 l 10 30"

        reflected =shape_manipulator (None ,drawing =shape ,op_mode ="Reflejar",axis ="x")
        self .assertTrue (reflected .startswith ("m 10 30"))
        self .assertIn ("l 20 30",reflected )
        self .assertIn ("l 20 10",reflected )
        self .assertIn ("l 10 10",reflected )

    def test_shape_manipulator_reflect_offset (self ):
        shape ="m 0 0 l 10 0"

        reflected =shape_manipulator (None ,drawing =shape ,op_mode ="Reflejar",axis ="y",offset_x =10.0 )
        self .assertTrue (reflected .startswith ("m 30 0"))
        self .assertIn ("l 20 0",reflected )

    def test_shape_manipulator_scale_t (self ):
        shape ="m 0 0 l 100 0 l 100 100 l 0 100"

        res_t0 =shape_manipulator (None ,drawing =shape ,scale_x =2.0 ,scale_y =2.0 ,mode ="origin",t =0.0 )
        self .assertTrue (res_t0 .startswith ("m 0 0"))
        self .assertIn ("l 100 0",res_t0 )
        self .assertIn ("l 100 100",res_t0 )


        res_t05 =shape_manipulator (None ,drawing =shape ,scale_x =2.0 ,scale_y =2.0 ,mode ="origin",t =0.5 )
        self .assertIn ("l 150 0",res_t05 )
        self .assertIn ("l 150 150",res_t05 )


        res_t1 =shape_manipulator (None ,drawing =shape ,scale_x =2.0 ,scale_y =2.0 ,mode ="origin",t =1.0 )
        self .assertIn ("l 200 0",res_t1 )
        self .assertIn ("l 200 200",res_t1 )

    def test_shape_manipulator_position_t (self ):
        shape ="m 0 0 l 10 0"
        res_t0 =shape_manipulator (None ,drawing =shape ,offset_x =100.0 ,offset_y =50.0 ,mode ="origin",t =0.0 )
        self .assertTrue (res_t0 .startswith ("m 0 0"))
        self .assertIn ("l 10 0",res_t0 )

        res_t05 =shape_manipulator (None ,drawing =shape ,offset_x =100.0 ,offset_y =50.0 ,mode ="origin",t =0.5 )
        self .assertTrue (res_t05 .startswith ("m 50 25"))
        self .assertIn ("l 60 25",res_t05 )

        res_t1 =shape_manipulator (None ,drawing =shape ,offset_x =100.0 ,offset_y =50.0 ,mode ="origin",t =1.0 )
        self .assertTrue (res_t1 .startswith ("m 100 50"))
        self .assertIn ("l 110 50",res_t1 )

    def test_shape_manipulator_border_t (self ):
        shape ="m 0 0 l 100 0 l 100 100 l 0 100"

        res_t0 =shape_manipulator (None ,drawing =shape ,op_mode ="Bordes",offset_border =10.0 ,mode ="origin",t =0.0 )
        self .assertIn ("m 0 0",res_t0 )


        res_t1 =shape_manipulator (None ,drawing =shape ,op_mode ="Bordes",offset_border =10.0 ,mode ="origin",t =1.0 )
        self .assertTrue (res_t1 .startswith ("m "))
        self .assertNotEqual (res_t0 ,res_t1 )

    def test_shape_manipulator_rotate_3d_t (self ):
        shape ="m -50 -50 l 50 -50 l 50 50 l -50 50"

        res_t0 =shape_manipulator (None ,drawing =shape ,op_mode ="Giro 3D",angle_z =90.0 ,t =0.0 )
        self .assertTrue (res_t0 .startswith ("m -50 -50"))


        res_t1 =shape_manipulator (None ,drawing =shape ,op_mode ="Giro 3D",angle_z =90.0 ,t =1.0 )
        self .assertTrue (res_t1 .startswith ("m 50 -50"))

    def test_shape_manipulator_reflect_t (self ):
        shape ="m 10 10 l 20 10 l 20 30 l 10 30"

        res_t0 =shape_manipulator (None ,drawing =shape ,op_mode ="Reflejar",axis ="y",t =0.0 )
        self .assertTrue (res_t0 .startswith ("m 10 10"))


        res_t05 =shape_manipulator (None ,drawing =shape ,op_mode ="Reflejar",axis ="y",t =0.5 )
        self .assertTrue (res_t05 .startswith ("m 15 10"))


        res_t1 =shape_manipulator (None ,drawing =shape ,op_mode ="Reflejar",axis ="y",t =1.0 )
        self .assertTrue (res_t1 .startswith ("m 20 10"))

    def test_shape_manipulator_redraw_t (self ):
        shape ="m 0 0 b 0 50 50 100 100 100"

        res_t0 =shape_manipulator (None ,drawing =shape ,op_mode ="Redibujar",density =10.0 ,t =0.0 )
        self .assertEqual (res_t0 .count ("b "),1 )


        res_t1 =shape_manipulator (None ,drawing =shape ,op_mode ="Redibujar",density =10.0 ,t =1.0 )
        self .assertGreater (res_t1 .count ("b "),1 )

    def test_shape_manipulator_node_engine_dispatch (self ):

        node_def ={
        "id":1 ,
        "type":"Shape/Manipulator",
        "properties":{
        "shape":"m 0 0 l 100 0 l 100 100 l 0 100",
        "mode":"Escalar",
        "t":"0.5",
        "scale_x":"200",
        "scale_y":"200",
        "anchor":"origin"
        }
        }
        engine =GraphEngine ({"nodes":[node_def ],"links":[]})
        res =engine .evaluate_data_node (1 ,context ={})
        self .assertTrue (isinstance (res ,str ))
        self .assertIn ("l 150 0",res )
        self .assertIn ("l 150 150",res )

    def test_shape_transform_inflate (self ):
        sq ="m 0 0 l 100 0 l 100 100 l 0 100"
        res_t0 =shape_transform (None ,drawing =sq ,mode ="Inflate",t =0.0 ,ratio =1.0 ,anchor ="origin")
        self .assertIn ("m 0 0",res_t0 )
        res_t05 =shape_transform (None ,drawing =sq ,mode ="Inflate",t =0.5 ,ratio =1.0 ,anchor ="center")
        self .assertTrue (res_t05 .startswith ("m "))


        res_t1_r05 =shape_transform (None ,drawing =sq ,mode ="Inflate",t =1.0 ,ratio =0.5 ,anchor ="center")
        self .assertEqual (res_t05 ,res_t1_r05 )


        res_t1_r0 =shape_transform (None ,drawing =sq ,mode ="Inflate",t =1.0 ,ratio =0.0 ,anchor ="origin")
        self .assertEqual (res_t0 ,res_t1_r0 )

    def test_shape_transform_skew_t (self ):
        sq ="m 0 0 l 100 0 l 100 100 l 0 100"

        res_t0 =shape_transform (None ,drawing =sq ,mode ="Skew",angle_x =45.0 ,angle_y =0.0 ,anchor ="origin",t =0.0 )
        self .assertTrue (res_t0 .startswith ("m 0 0"))
        self .assertIn ("l 100 0",res_t0 )
        self .assertIn ("l 100 100",res_t0 )


        res_t1 =shape_transform (None ,drawing =sq ,mode ="Skew",angle_x =45.0 ,angle_y =0.0 ,anchor ="origin",t =1.0 )
        self .assertIn ("l 200 100",res_t1 )
        self .assertIn ("l 100 100",res_t1 )

    def test_shape_transform_round_corners_t (self ):
        sq ="m 0 0 l 100 0 l 100 100 l 0 100"

        res_t0 =shape_transform (None ,drawing =sq ,mode ="Round Corners",radius =20.0 ,anchor ="origin",t =0.0 )
        self .assertNotIn ("b ",res_t0 )
        self .assertIn ("l 100 0",res_t0 )


        res_t1 =shape_transform (None ,drawing =sq ,mode ="Round Corners",radius =20.0 ,anchor ="origin",t =1.0 )
        self .assertIn ("b ",res_t1 )

    def test_shape_transform_corner_modes (self ):
        sq ="m 0 0 l 100 0 l 100 100 l 0 100"

        res_round =shape_transform (None ,drawing =sq ,mode ="Round Corners",radius =20.0 ,corner_mode ="Round",anchor ="origin",t =1.0 )
        self .assertIn ("b ",res_round )


        res_bevel =shape_transform (None ,drawing =sq ,mode ="Round Corners",radius =20.0 ,corner_mode ="Bevel",anchor ="origin",t =1.0 )
        self .assertNotIn ("b ",res_bevel )
        self .assertIn ("l ",res_bevel )


        res_miter =shape_transform (None ,drawing =sq ,mode ="Round Corners",radius =20.0 ,corner_mode ="Miter",anchor ="origin",t =1.0 )
        self .assertNotIn ("b ",res_miter )
        self .assertIn ("l ",res_miter )
        self .assertGreater (len (res_miter .split ("l ")),len (res_bevel .split ("l ")))

    def test_shape_transform_flexor_t (self ):
        line_shp ="m 0 0 l 100 0"

        res_t0 =shape_transform (None ,drawing =line_shp ,mode ="Flexor",curve ="45",anchor ="origin",t =0.0 )
        self .assertTrue (res_t0 .startswith ("m 0 0"))


        res_t1 =shape_transform (None ,drawing =line_shp ,mode ="Flexor",curve ="45",anchor ="origin",t =1.0 )
        self .assertTrue (res_t1 .startswith ("m "))
        self .assertNotEqual (res_t0 ,res_t1 )

    def test_shape_transform_graph_engine_skew_and_corners (self ):
        node_skew ={
        "id":301 ,
        "type":"Shape/Transform",
        "properties":{
        "shape":"m 0 0 l 100 0 l 100 100 l 0 100",
        "mode":"Skew",
        "t":"1.0",
        "angle_x":"45",
        "angle_y":"0",
        "anchor":"origin"
        }
        }
        engine =GraphEngine ({"nodes":[node_skew ],"links":[]})
        out_skew =engine .evaluate_data_node (301 ,context ={})
        self .assertTrue (isinstance (out_skew ,str ))
        self .assertIn ("l 200 100",out_skew )

        node_round ={
        "id":302 ,
        "type":"Shape/Transform",
        "properties":{
        "shape":"m 0 0 l 100 0 l 100 100 l 0 100",
        "mode":"Round Corners",
        "t":"1.0",
        "radius":"20.0",
        "anchor":"origin"
        }
        }
        engine_round =GraphEngine ({"nodes":[node_round ],"links":[]})
        out_round =engine_round .evaluate_data_node (302 ,context ={})
        self .assertTrue (isinstance (out_round ,str ))
        self .assertIn ("b ",out_round )

    def test_shape_transform_distort_basic (self ):
        sq ="m 0 0 l 100 0 l 100 100 l 0 100"
        tri ="m 0 0 l 100 0 l 50 100"
        res_t0 =shape_transform (None ,drawing =sq ,target_shape =tri ,mode ="Distort",t =0.0 ,anchor ="origin")
        self .assertTrue (isinstance (res_t0 ,str )and res_t0 .startswith ("m "))
        res_t1 =shape_transform (None ,drawing =sq ,target_shape =tri ,mode ="Distort",t =1.0 ,anchor ="origin")
        self .assertTrue (isinstance (res_t1 ,str )and res_t1 .startswith ("m "))

    def test_shape_transform_distort2_progression (self ):
        shape_a ="m 0 0 l 100 0 l 100 100 l 0 100"
        shape_b ="m 0 0 l 100 0 l 50 100"
        shape_c ="m 0 0 l 100 50 l 0 100"


        res_t0 =shape_transform (None ,drawing =shape_a ,mid_shape =shape_b ,target_shape =shape_c ,mode ="Distort2",t =0.0 ,anchor ="origin")
        expected_t0 =shape_transform (None ,drawing =shape_a ,target_shape =shape_b ,mode ="Distort",t =0.0 ,anchor ="origin")
        self .assertEqual (res_t0 ,expected_t0 )


        res_t05 =shape_transform (None ,drawing =shape_a ,mid_shape =shape_b ,target_shape =shape_c ,mode ="Distort2",t =0.5 ,anchor ="origin")
        expected_t05 =shape_transform (None ,drawing =shape_a ,target_shape =shape_b ,mode ="Distort",t =1.0 ,anchor ="origin")
        self .assertEqual (res_t05 ,expected_t05 )


        res_t1 =shape_transform (None ,drawing =shape_a ,mid_shape =shape_b ,target_shape =shape_c ,mode ="Distort2",t =1.0 ,anchor ="origin")
        expected_t1 =shape_transform (None ,drawing =shape_b ,target_shape =shape_c ,mode ="Distort",t =1.0 ,anchor ="origin")
        self .assertEqual (res_t1 ,expected_t1 )


        res_t025 =shape_transform (None ,drawing =shape_a ,mid_shape =shape_b ,target_shape =shape_c ,mode ="Distort2",t =0.25 ,anchor ="origin")
        expected_t025 =shape_transform (None ,drawing =shape_a ,target_shape =shape_b ,mode ="Distort",t =0.5 ,anchor ="origin")
        self .assertEqual (res_t025 ,expected_t025 )

        res_t075 =shape_transform (None ,drawing =shape_a ,mid_shape =shape_b ,target_shape =shape_c ,mode ="Distort2",t =0.75 ,anchor ="origin")
        expected_t075 =shape_transform (None ,drawing =shape_b ,target_shape =shape_c ,mode ="Distort",t =0.5 ,anchor ="origin")
        self .assertEqual (res_t075 ,expected_t075 )

    def test_shape_transform_distort2_graph_engine_evaluation (self ):
        shape_a ="m 0 0 l 100 0 l 100 100 l 0 100"
        shape_b ="m 0 0 l 100 0 l 50 100"
        shape_c ="m 0 0 l 100 50 l 0 100"

        node ={
        "id":201 ,
        "type":"Shape/Transform",
        "properties":{
        "mode":"Distort2",
        "shape":shape_a ,
        "mid_shape":shape_b ,
        "target_shape":shape_c ,
        "t":"0.5",
        "energy":"0.35",
        "step_px":"0",
        "anchor":"origin"
        },
        "inputs":[]
        }
        engine_inst =GraphEngine ({"nodes":[node ],"links":[]})
        ctx ={"j":1 }
        out_shape =engine_inst .evaluate_data_node (201 ,ctx )
        self .assertTrue (isinstance (out_shape ,str )and out_shape .startswith ("m "))
        expected =shape_transform (None ,drawing =shape_a ,target_shape =shape_b ,mode ="Distort",t =1.0 ,anchor ="origin")
        self .assertEqual (out_shape ,expected )

    def test_shape_transform_distort2_fallbacks (self ):
        shape_a ="m 0 0 l 100 0 l 100 100 l 0 100"
        shape_c ="m 0 0 l 100 50 l 0 100"


        res =shape_transform (None ,drawing =shape_a ,mid_shape ="",target_shape =shape_c ,mode ="Distort2",t =0.5 ,anchor ="origin")
        expected =shape_transform (None ,drawing =shape_a ,target_shape =shape_c ,mode ="Distort",t =0.5 ,anchor ="origin")
        self .assertEqual (res ,expected )

    def test_shape_transform_distort2_polyline_step (self ):
        shape_a ="m 0 0 l 100 0 l 100 100 l 0 100"
        shape_b ="m 0 0 l 100 0 l 50 100"
        shape_c ="m 0 0 l 100 50 l 0 100"

        res_poly =shape_transform (None ,drawing =shape_a ,mid_shape =shape_b ,target_shape =shape_c ,mode ="Distort2",t =0.3 ,step_px =5.0 ,anchor ="origin")
        self .assertTrue (isinstance (res_poly ,str )and res_poly .startswith ("m "))
        self .assertIn ("l ",res_poly )


class TestConcentricBordersAndClip (unittest .TestCase ):
    """Pruebas de generacion de bordes concentricos y gradientes de corte."""

    def test_concentric_borders_generation (self ):
        shape ="m 0 0 l 100 0 l 100 100 l 0 100"
        ctx ={"start_time":0 ,"end_time":1000 ,"b_i":2 }
        res =shape_concentric_borders_node (ctx ,shape =shape ,loop_count =3 ,separation =4.0 )
        self .assertIsNotNone (res )
        self .assertEqual (ctx .get ("b_i"),2 )
        self .assertEqual (ctx .get ("b_n"),3 )
        self .assertEqual (ctx .get ("ring_i"),2 )
        self .assertEqual (ctx .get ("ring_n"),3 )
        self .assertNotIn ("j_max",ctx )

    def test_sort_1d_indices_canonical_modes (self ):
        """Verifica permutaciones de los 5 órdenes 1D canónicos."""
        self .assertEqual (sort_1d_indices (5 ,order ="normal"),[0 ,1 ,2 ,3 ,4 ])
        self .assertEqual (sort_1d_indices (5 ,order ="reverse"),[4 ,3 ,2 ,1 ,0 ])
        self .assertEqual (sort_1d_indices (5 ,order ="center_to_edges"),[2 ,1 ,3 ,0 ,4 ])
        self .assertEqual (sort_1d_indices (5 ,order ="edges_to_center"),[0 ,4 ,1 ,3 ,2 ])

        rnd_idx =sort_1d_indices (5 ,order ="random")
        self .assertEqual (sorted (rnd_idx ),[0 ,1 ,2 ,3 ,4 ])
        self .assertEqual (rnd_idx ,sort_1d_indices (5 ,order ="random"))

    def test_sort_1d_indices_spanish_aliases (self ):
        """Verifica compatibilidad con alias en español antiguos."""
        self .assertEqual (sort_1d_indices (5 ,order ="Normal"),[0 ,1 ,2 ,3 ,4 ])
        self .assertEqual (sort_1d_indices (5 ,order ="Invertido"),[4 ,3 ,2 ,1 ,0 ])
        self .assertEqual (sort_1d_indices (5 ,order ="Centro a Extremos"),[2 ,1 ,3 ,0 ,4 ])
        self .assertEqual (sort_1d_indices (5 ,order ="Extremos al Centro"),[0 ,4 ,1 ,3 ,2 ])
        self .assertEqual (sorted (sort_1d_indices (5 ,order ="Aleatorio")),[0 ,1 ,2 ,3 ,4 ])

    def test_clip_gradient_node_1d_orders_and_modes (self ):
        """Verifica generación de tags de clipping con los 5 órdenes 1D y modos out_mode."""
        ctx ={"active_unit":None ,"active_line":None ,"c_i":1 }
        tag ,prog ,idx ,tot =clip_gradient_node (ctx ,num_clips ="5",angle ="0",padding ="4",overlap ="0.5",order ="normal",out_mode ="clip")
        self .assertTrue (tag .startswith ("\\clip("))
        self .assertEqual (prog ,0.0 )
        self .assertEqual (idx ,1 )
        self .assertEqual (tot ,5 )

        ctx_rev ={"active_unit":None ,"active_line":None ,"c_i":1 }
        _ ,prog_rev ,_ ,_ =clip_gradient_node (ctx_rev ,num_clips ="5",angle ="0",padding ="4",overlap ="0.5",order ="reverse",out_mode ="clip")
        self .assertEqual (prog_rev ,1.0 )

        tag_iclip ,_ ,_ ,_ =clip_gradient_node ({"c_i":1 },num_clips ="3",angle ="0",out_mode ="iclip")
        self .assertTrue (tag_iclip .startswith ("\\iclip("))

        tag_shp ,_ ,_ ,_ =clip_gradient_node ({"c_i":1 },num_clips ="3",angle ="0",out_mode ="shape")
        self .assertTrue (tag_shp .startswith ("m "))


class TestShapeFilter (unittest .TestCase ):
    """Pruebas unitarias completas para el nodo Shape Filter en sus 3 modos (Vértices, Grupo, Ruido)."""

    def test_shape_filter_vertices_math_and_t (self ):
        sq ="m 0 0 l 100 0 l 100 100 l 0 100"

        res_t1 =shape_filter (None ,drawing =sq ,mode ="Vértices",expr_x ="x + 10",expr_y ="y + 20",t =1.0 )
        self .assertTrue (res_t1 .startswith ("m 10 20"))
        self .assertIn ("l 110 20",res_t1 )
        self .assertIn ("l 110 120",res_t1 )
        self .assertIn ("l 10 120",res_t1 )


        res_t0 =shape_filter (None ,drawing =sq ,mode ="Vértices",expr_x ="x + 50",expr_y ="y + 50",t =0.0 )
        self .assertTrue (res_t0 .startswith ("m 0 0"))
        self .assertIn ("l 100 0",res_t0 )
        self .assertIn ("l 100 100",res_t0 )
        self .assertIn ("l 0 100",res_t0 )


        res_t05 =shape_filter (None ,drawing =sq ,mode ="Vértices",expr_x ="x + 20",expr_y ="y + 40",t =0.5 )
        self .assertTrue (res_t05 .startswith ("m 10 20"))
        self .assertIn ("l 110 20",res_t05 )

    def test_shape_filter_vertices_env_vars (self ):
        sq ="m 0 0 l 100 0 l 100 100 l 0 100"

        res =shape_filter (None ,drawing =sq ,mode ="Vértices",expr_x ="x + 10 * sin(mx * pi)",expr_y ="y + cy",t =1.0 )
        self .assertTrue (res .startswith ("m "))
        tokens =res .split ()
        self .assertEqual (len (tokens ),12 )

    def test_shape_filter_vertices_subdivs (self ):
        sq ="m 0 0 l 100 0 l 100 100 l 0 100"

        res =shape_filter (None ,drawing =sq ,mode ="Vértices",expr_x ="x + 5 * sin(mx * 2 * pi)",subdivs =20.0 )
        tokens =res .split ()
        self .assertGreater (len (tokens ),12 )

    def test_shape_filter_group_rotation_and_offset (self ):

        multi ="m 0 0 l 10 0 l 10 10 l 0 10 m 20 0 l 30 0 l 30 10 l 20 10 m 40 0 l 50 0 l 50 10 l 40 10"
        res =shape_filter (None ,drawing =multi ,mode ="Grupo",rot_step =45.0 ,offset_x =15.0 ,t =1.0 ,anchor ="center")
        self .assertEqual (res .count ("m "),3 )
        self .assertTrue (res .startswith ("m "))


        res_t0 =shape_filter (None ,drawing =multi ,mode ="Grupo",rot_step =90.0 ,offset_x =50.0 ,t =0.0 ,anchor ="center")
        self .assertEqual (res_t0 .count ("m "),3 )

    def test_shape_filter_noise_deterministic (self ):
        sq ="m 0 0 l 100 0 l 100 100 l 0 100"

        res1 =shape_filter (None ,drawing =sq ,mode ="Ruido",radius_x =10.0 ,radius_y =10.0 ,subdivs =0 ,seed =1234 )
        res2 =shape_filter (None ,drawing =sq ,mode ="Ruido",radius_x =10.0 ,radius_y =10.0 ,subdivs =0 ,seed =1234 )
        self .assertEqual (res1 ,res2 )


        res3 =shape_filter (None ,drawing =sq ,mode ="Ruido",radius_x =10.0 ,radius_y =10.0 ,subdivs =0 ,seed =9999 )
        self .assertNotEqual (res1 ,res3 )

    def test_shape_filter_node_engine_dispatch (self ):
        node_def ={
        "id":1 ,
        "type":"Shape/Filter",
        "properties":{
        "shape":"m 0 0 l 50 0 l 50 50 l 0 50",
        "mode":"Vértices",
        "expr_x":"x + 5",
        "expr_y":"y + 10",
        "t":"1.0",
        "subdivs":"0"
        }
        }
        engine =GraphEngine ({"nodes":[node_def ],"links":[]})
        res =engine .evaluate_data_node (1 ,context ={})
        self .assertTrue (isinstance (res ,str ))
        self .assertTrue (res .startswith ("m 5 10"))

    def test_shape_multi_all_modes_direct (self ):
        from nodes .shape_nodes import shape_multi 


        res1 =shape_multi (None ,mode ="Cuadros Concéntricos",size =100.0 ,px ="4",t =1.0 )
        self .assertTrue (isinstance (res1 ,str ))
        self .assertTrue (res1 .startswith ("m "))

        res1_pat =shape_multi (None ,mode ="Cuadros Concéntricos",size =100.0 ,px ="8, {2}, 4, {3}",t =1.0 )
        self .assertTrue (res1_pat .startswith ("m "))


        res2 =shape_multi (None ,mode ="Franjas Diagonales",width =70.0 ,height =50.0 ,px ="6",t =1.0 )
        self .assertTrue (isinstance (res2 ,str ))
        self .assertTrue (res2 .startswith ("m "))


        res3 =shape_multi (None ,drawing ="m 0 0 l 100 0 l 100 100 l 0 100",mode ="Anillos Concéntricos",size =100.0 ,bord ="4",t =1.0 )
        self .assertTrue (isinstance (res3 ,str ))
        self .assertTrue (res3 .startswith ("m "))


        res4 =shape_multi (None ,mode ="Mosaico Poligonal",size =64.0 ,sides =6 ,rings =1 ,n_layers =5 ,t =1.0 )
        self .assertTrue (isinstance (res4 ,str ))
        self .assertTrue (res4 .startswith ("m "))

        res4_rings =shape_multi (None ,mode ="Mosaico Poligonal",size =64.0 ,sides =6 ,rings =3 ,n_layers =3 ,separation =4.0 ,t =1.0 )
        self .assertTrue (isinstance (res4_rings ,str ))
        self .assertTrue (res4_rings .startswith ("m "))


        res5 =shape_multi (None ,drawing ="m 0 0 l 10 0 l 10 10 l 0 10",mode ="Mosaico Multi-Forma",width =60.0 ,height =50.0 ,dx =2.0 ,dy =2.0 )
        self .assertTrue (isinstance (res5 ,str ))
        self .assertTrue (res5 .startswith ("m "))


        res6 =shape_multi (None ,mode ="Borde Segmentado",width =104.0 ,height =104.0 ,bord =4.0 ,space =2.0 ,length =20.0 ,t =1.0 )
        self .assertTrue (isinstance (res6 ,str ))
        self .assertTrue (res6 .startswith ("m "))

        res6_custom =shape_multi (None ,drawing ="Estrella",mode ="Borde Segmentado",width =120.0 ,height =100.0 ,bord =10.0 ,space =4.0 ,length =15.0 ,t =1.0 )
        self .assertTrue (isinstance (res6_custom ,str ))
        self .assertTrue (res6_custom .startswith ("m "))


        res7_pie =shape_multi (None ,mode ="Roseta Radial",parts =12 ,r_out =50.0 ,r_in =0.0 ,t =1.0 )
        self .assertTrue (isinstance (res7_pie ,str ))
        self .assertTrue (res7_pie .startswith ("m "))
        self .assertIn ("b ",res7_pie )

        res7_ring =shape_multi (None ,mode ="Roseta Radial",parts =12 ,r_out =50.0 ,r_in =20.0 ,t =1.0 )
        self .assertTrue (isinstance (res7_ring ,str ))
        self .assertTrue (res7_ring .startswith ("m "))


        res8 =shape_multi (None ,drawing ="m 0 0 l 100 0 l 100 100 l 0 100",mode ="Túnel / Cascada",size1 =100.0 ,size2 =10.0 ,loop =5 ,t =1.0 )
        self .assertTrue (isinstance (res8 ,str ))
        self .assertTrue (res8 .startswith ("m "))

    def test_shape_multi_factor_t_progress (self ):
        from nodes .shape_nodes import shape_multi 


        r_half =shape_multi (None ,mode ="Roseta Radial",parts =12 ,r_out =50.0 ,r_in =0.0 ,t =0.5 )
        r_full =shape_multi (None ,mode ="Roseta Radial",parts =12 ,r_out =50.0 ,r_in =0.0 ,t =1.0 )
        self .assertLess (len (r_half ),len (r_full ))


        b_quarter =shape_multi (None ,mode ="Borde Segmentado",width =104.0 ,height =104.0 ,bord =4.0 ,length =20.0 ,t =0.25 )
        b_full =shape_multi (None ,mode ="Borde Segmentado",width =104.0 ,height =104.0 ,bord =4.0 ,length =20.0 ,t =1.0 )
        self .assertLess (len (b_quarter ),len (b_full ))


        t_half =shape_multi (None ,mode ="Túnel / Cascada",size1 =100.0 ,size2 =10.0 ,loop =8 ,t =0.5 )
        t_full =shape_multi (None ,mode ="Túnel / Cascada",size1 =100.0 ,size2 =10.0 ,loop =8 ,t =1.0 )
        self .assertLess (len (t_half ),len (t_full ))

    def test_shape_multi_separation_and_overlap (self ):
        from nodes .shape_nodes import shape_multi 


        res_sep0 =shape_multi (None ,mode ="Roseta Radial",parts =4 ,r_out =50.0 ,r_in =0.0 ,separation =0.0 ,t =1.0 )
        res_sep10 =shape_multi (None ,mode ="Roseta Radial",parts =4 ,r_out =50.0 ,r_in =0.0 ,separation =10.0 ,t =1.0 )
        res_sep_neg =shape_multi (None ,mode ="Roseta Radial",parts =4 ,r_out =50.0 ,r_in =0.0 ,separation =-5.0 ,t =1.0 )

        self .assertNotEqual (res_sep0 ,res_sep10 )
        self .assertNotEqual (res_sep0 ,res_sep_neg )
        self .assertTrue (res_sep10 .startswith ("m "))
        self .assertTrue (res_sep_neg .startswith ("m "))


        res_poly0 =shape_multi (None ,mode ="Mosaico Poligonal",size =64.0 ,sides =6 ,rings =1 ,n_layers =5 ,separation =0.0 ,t =1.0 )
        res_poly5 =shape_multi (None ,mode ="Mosaico Poligonal",size =64.0 ,sides =6 ,rings =1 ,n_layers =5 ,separation =5.0 ,t =1.0 )
        self .assertNotEqual (res_poly0 ,res_poly5 )


        res_sq0 =shape_multi (None ,mode ="Cuadros Concéntricos",size =100.0 ,px ="4",separation =0.0 ,t =1.0 )
        res_sq5 =shape_multi (None ,mode ="Cuadros Concéntricos",size =100.0 ,px ="4",separation =5.0 ,t =1.0 )
        self .assertNotEqual (res_sq0 ,res_sq5 )


        res_tun0 =shape_multi (None ,drawing ="m 0 0 l 100 0 l 100 100 l 0 100",mode ="Túnel / Cascada",size1 =100.0 ,size2 =10.0 ,loop =5 ,separation =0.0 ,t =1.0 )
        res_tun10 =shape_multi (None ,drawing ="m 0 0 l 100 0 l 100 100 l 0 100",mode ="Túnel / Cascada",size1 =100.0 ,size2 =10.0 ,loop =5 ,separation =10.0 ,t =1.0 )
        self .assertNotEqual (res_tun0 ,res_tun10 )

    def test_shape_multi_diagonal_stripes_corner_coverage (self ):
        from nodes .shape_nodes import shape_multi ,_get_drawing_bbox 


        res_diag0 =shape_multi (None ,mode ="Franjas Diagonales",width =100.0 ,height =200.0 ,px ="10",separation =0.0 ,t =1.0 ,anchor ="origin")
        bbox0 =_get_drawing_bbox (res_diag0 )
        self .assertEqual (bbox0 ,(0.0 ,100.0 ,0.0 ,200.0 ))


        res_diag2 =shape_multi (None ,mode ="Franjas Diagonales",width =100.0 ,height =200.0 ,px ="10",separation =2.0 ,t =1.0 ,anchor ="origin")
        bbox2 =_get_drawing_bbox (res_diag2 )
        self .assertEqual (bbox2 ,(0.0 ,100.0 ,0.0 ,200.0 ))


        res_diag_h =shape_multi (None ,mode ="Franjas Diagonales",width =200.0 ,height =100.0 ,px ="10",separation =2.0 ,t =1.0 ,anchor ="origin")
        bbox_h =_get_drawing_bbox (res_diag_h )
        self .assertEqual (bbox_h ,(0.0 ,200.0 ,0.0 ,100.0 ))


        res_diag_sq =shape_multi (None ,mode ="Franjas Diagonales",width =100.0 ,height =100.0 ,px ="10",separation =0.0 ,t =1.0 ,anchor ="origin")
        bbox_sq =_get_drawing_bbox (res_diag_sq )
        self .assertEqual (bbox_sq ,(0.0 ,100.0 ,0.0 ,100.0 ))

    def test_shape_multi_node_engine_separation_inputs (self ):

        node_def ={
        "id":1 ,
        "type":"Shape/Multi",
        "properties":{
        "mode":"Roseta Radial",
        "parts":"8",
        "r_out":"60.0",
        "r_in":"10.0",
        "separation":"15.0",
        "t":"1.0"
        }
        }
        engine =GraphEngine ({"nodes":[node_def ],"links":[]})
        res =engine .evaluate_data_node (1 ,context ={})
        self .assertTrue (isinstance (res ,str )and res .startswith ("m "))


        sep_node ={
        "id":2 ,
        "type":"Functions/Number",
        "properties":{"value":"20.0"}
        }
        node_def_linked ={
        "id":3 ,
        "type":"Shape/Multi",
        "properties":{
        "mode":"Roseta Radial",
        "parts":"8",
        "r_out":"60.0",
        "r_in":"10.0",
        "t":"1.0"
        },
        "inputs":[{"name":"Separación","link":10 }]
        }
        link =[10 ,2 ,0 ,3 ,3 ,"number"]
        engine2 =GraphEngine ({"nodes":[sep_node ,node_def_linked ],"links":[link ]})
        res2 =engine2 .evaluate_data_node (3 ,context ={})
        self .assertTrue (isinstance (res2 ,str )and res2 .startswith ("m "))

    def test_shape_multi_anchor_modes (self ):
        from nodes .shape_nodes import shape_multi 


        res_center =shape_multi (None ,mode ="Cuadros Concéntricos",size =100.0 ,px ="4",separation =0.0 ,t =1.0 ,anchor ="center")
        res_origin =shape_multi (None ,mode ="Cuadros Concéntricos",size =100.0 ,px ="4",separation =0.0 ,t =1.0 ,anchor ="origin")
        ctx ={"fx_pos_x":200.0 ,"fx_pos_y":150.0 }
        res_zero =shape_multi (ctx ,mode ="Cuadros Concéntricos",size =100.0 ,px ="4",separation =0.0 ,t =1.0 ,anchor ="zero")

        self .assertTrue (res_center .startswith ("m "))
        self .assertTrue (res_origin .startswith ("m "))
        self .assertTrue (res_zero .startswith ("m "))
        self .assertNotEqual (res_center ,res_origin )
        self .assertNotEqual (res_center ,res_zero )


        res_tun_center =shape_multi (None ,drawing ="m 0 0 l 100 0 l 100 100 l 0 100",mode ="Túnel / Cascada",size1 =100.0 ,size2 =10.0 ,loop =5 ,anchor ="center")
        res_tun_origin =shape_multi (None ,drawing ="m 0 0 l 100 0 l 100 100 l 0 100",mode ="Túnel / Cascada",size1 =100.0 ,size2 =10.0 ,loop =5 ,anchor ="origin")
        self .assertTrue (res_tun_center .startswith ("m "))
        self .assertTrue (res_tun_origin .startswith ("m "))
        self .assertNotEqual (res_tun_center ,res_tun_origin )


        res_multi_center =shape_multi (None ,drawing ="m 0 0 l 20 0 l 20 20 l 0 20",mode ="Mosaico Multi-Forma",width =60.0 ,height =60.0 ,anchor ="center")
        res_multi_origin =shape_multi (None ,drawing ="m 0 0 l 20 0 l 20 20 l 0 20",mode ="Mosaico Multi-Forma",width =60.0 ,height =60.0 ,anchor ="origin")
        self .assertTrue (res_multi_center .startswith ("m "))
        self .assertTrue (res_multi_origin .startswith ("m "))
        self .assertNotEqual (res_multi_center ,res_multi_origin )

    def test_shape_multi_node_engine_anchor (self ):

        node_def_origin ={
        "id":1 ,
        "type":"Shape/Multi",
        "properties":{
        "mode":"Cuadros Concéntricos",
        "size":"100.0",
        "px":"4",
        "separation":"0.0",
        "t":"1.0",
        "anchor":"origin"
        }
        }
        engine_origin =GraphEngine ({"nodes":[node_def_origin ],"links":[]})
        res_origin =engine_origin .evaluate_data_node (1 ,context ={})

        node_def_center ={
        "id":2 ,
        "type":"Shape/Multi",
        "properties":{
        "mode":"Cuadros Concéntricos",
        "size":"100.0",
        "px":"4",
        "separation":"0.0",
        "t":"1.0",
        "anchor":"center"
        }
        }
        engine_center =GraphEngine ({"nodes":[node_def_center ],"links":[]})
        res_center =engine_center .evaluate_data_node (2 ,context ={})

        self .assertTrue (res_origin .startswith ("m "))
        self .assertTrue (res_center .startswith ("m "))
        self .assertNotEqual (res_origin ,res_center )

    def test_shape_multi_node_engine_dispatch (self ):

        modes =[
        ("Cuadros Concéntricos",{"size":"100.0","px":"4","separation":"2.0","t":"1.0","anchor":"center"}),
        ("Franjas Diagonales",{"width":"70.0","height":"50.0","px":"6","separation":"1.0","t":"1.0","anchor":"center"}),
        ("Anillos Concéntricos",{"shape":"circle","size":"100.0","bord":"4","separation":"2.0","t":"1.0","anchor":"center"}),
        ("Mosaico Poligonal",{"size":"64.0","sides":"6","rings":"1","n_layers":"5","separation":"3.0","t":"1.0","anchor":"center"}),
        ("Mosaico Multi-Forma",{"shape":"rectangle","width":"60.0","height":"50.0","dx":"0","dy":"0","anchor":"center"}),
        ("Borde Segmentado",{"width":"104.0","height":"104.0","bord":"4.0","space":"0","separation":"2.0","length":"20.0","t":"1.0","anchor":"center"}),
        ("Roseta Radial",{"parts":"12","r_out":"50.0","r_in":"0.0","separation":"4.0","t":"1.0","anchor":"center"}),
        ("Túnel / Cascada",{"shape":"rectangle","size1":"100.0","size2":"10.0","loop":"6","separation":"2.0","t":"1.0","anchor":"center"}),
        ]

        for idx ,(m_name ,props_dict )in enumerate (modes ,start =1 ):
            props_all ={"mode":m_name }
            props_all .update (props_dict )
            node_def ={
            "id":idx ,
            "type":"Shape/Multi",
            "properties":props_all 
            }
            engine =GraphEngine ({"nodes":[node_def ],"links":[]})
            res =engine .evaluate_data_node (idx ,context ={})
            self .assertTrue (isinstance (res ,str ),f"Fallo en modo {m_name }")
    def test_shape_multi_concentric_rings_hollow (self ):
        from nodes .shape_nodes import shape_multi ,parse_assdraw_segments 


        res =shape_multi (None ,mode ="Anillos Concéntricos",size =60.0 ,bord ="3, 7",separation =0.0 ,t =1.0 )
        self .assertTrue (isinstance (res ,str ))
        self .assertTrue (res .startswith ("m "))


        contours =parse_assdraw_segments (res )
        self .assertGreater (len (contours ),1 )
        for c in contours :

            for s in c ["segments"]:
                self .assertEqual (s ["type"],"b")

    def test_shape_multi_concentric_rings_gap (self ):
        from nodes .shape_nodes import shape_multi ,parse_assdraw_segments 


        res_gap =shape_multi (None ,mode ="Anillos Concéntricos",size =60.0 ,bord ="{-4}, 4",separation =0.0 ,t =1.0 )
        self .assertTrue (isinstance (res_gap ,str ))
        self .assertTrue (res_gap .startswith ("m "))
    def test_shape_multi_segmented_border_custom_shape (self ):
        from nodes .shape_nodes import shape_multi ,parse_assdraw_segments 


        res_rect =shape_multi (None ,mode ="Borde Segmentado",width =100.0 ,height =100.0 ,bord =4.0 ,space =5.0 ,length =20.0 ,t =1.0 )
        self .assertTrue (isinstance (res_rect ,str ))
        self .assertTrue (res_rect .startswith ("m "))


        heart_shape ="m 50 20 b 50 10 35 0 20 0 b 0 0 0 30 0 30 b 0 60 50 90 50 90 b 50 90 100 60 100 30 b 100 30 100 0 80 0 b 65 0 50 10 50 20"
        res_heart =shape_multi (None ,drawing =heart_shape ,mode ="Borde Segmentado",bord =4.0 ,space =5.0 ,length =15.0 ,t =1.0 )
        self .assertTrue (isinstance (res_heart ,str ))
        self .assertTrue (res_heart .startswith ("m "))
        contours =parse_assdraw_segments (res_heart )
        self .assertGreater (len (contours ),1 ,"Debe generar múltiples trazos/segmentos a lo largo del contorno")


        res_heart_half =shape_multi (None ,drawing =heart_shape ,mode ="Borde Segmentado",bord =4.0 ,space =5.0 ,length =15.0 ,t =0.5 )
        contours_half =parse_assdraw_segments (res_heart_half )
        self .assertLess (len (contours_half ),len (contours ),"t=0.5 debe generar menos segmentos que t=1.0")

    def test_shape_multi_tunnel_cascade_directions (self ):
        from nodes .shape_nodes import shape_multi 


        res_up =shape_multi (None ,drawing ="m 0 0 l 20 0 l 20 20 l 0 20",mode ="Túnel / Cascada",size1 =50.0 ,size2 =10.0 ,loop =4 ,separation =10.0 ,angle =0.0 )
        res_right =shape_multi (None ,drawing ="m 0 0 l 20 0 l 20 20 l 0 20",mode ="Túnel / Cascada",size1 =50.0 ,size2 =10.0 ,loop =4 ,separation =10.0 ,angle =90.0 )
        res_down =shape_multi (None ,drawing ="m 0 0 l 20 0 l 20 20 l 0 20",mode ="Túnel / Cascada",size1 =50.0 ,size2 =10.0 ,loop =4 ,separation =10.0 ,angle =180.0 )
        res_left =shape_multi (None ,drawing ="m 0 0 l 20 0 l 20 20 l 0 20",mode ="Túnel / Cascada",size1 =50.0 ,size2 =10.0 ,loop =4 ,separation =10.0 ,angle =270.0 )

        self .assertTrue (res_up .startswith ("m "))
        self .assertTrue (res_right .startswith ("m "))
        self .assertTrue (res_down .startswith ("m "))
        self .assertTrue (res_left .startswith ("m "))
        self .assertNotEqual (res_up ,res_right )
        self .assertNotEqual (res_up ,res_down )
        self .assertNotEqual (res_right ,res_left )


        res_up_name =shape_multi (None ,drawing ="m 0 0 l 20 0 l 20 20 l 0 20",mode ="Túnel / Cascada",size1 =50.0 ,size2 =10.0 ,loop =4 ,separation =10.0 ,angle ="arriba")
        res_up_num =shape_multi (None ,drawing ="m 0 0 l 20 0 l 20 20 l 0 20",mode ="Túnel / Cascada",size1 =50.0 ,size2 =10.0 ,loop =4 ,separation =10.0 ,angle =0.0 )
        self .assertEqual (res_up_name ,res_up_num )

        res_right_name =shape_multi (None ,drawing ="m 0 0 l 20 0 l 20 20 l 0 20",mode ="Túnel / Cascada",size1 =50.0 ,size2 =10.0 ,loop =4 ,separation =10.0 ,angle ="derecha")
        res_right_num =shape_multi (None ,drawing ="m 0 0 l 20 0 l 20 20 l 0 20",mode ="Túnel / Cascada",size1 =50.0 ,size2 =10.0 ,loop =4 ,separation =10.0 ,angle =90.0 )
        self .assertEqual (res_right_name ,res_right_num )

    def test_shape_array_node_progress_t (self ):
        from nodes .shape_nodes import shape_array_node ,parse_assdraw_segments 


        res_full ,pos ,px ,py ,ang ,ai ,total ,col ,row =shape_array_node (
        context ={},
        mode ="Grid",
        out_mode ="Shape",
        cols =5 ,
        rows =3 ,
        t =1.0 ,
        order ="79"
        )
        self .assertEqual (total ,15 )
        segments_full =parse_assdraw_segments (res_full )
        self .assertEqual (len (segments_full ),15 )


        res_half ,_ ,_ ,_ ,_ ,_ ,_ ,_ ,_ =shape_array_node (
        context ={},
        mode ="Grid",
        out_mode ="Shape",
        cols =5 ,
        rows =3 ,
        t =0.5 ,
        order ="79"
        )
        segments_half =parse_assdraw_segments (res_half )
        self .assertEqual (len (segments_half ),8 )


        res_zero ,_ ,_ ,_ ,_ ,_ ,_ ,_ ,_ =shape_array_node (
        context ={},
        mode ="Grid",
        out_mode ="Shape",
        cols =5 ,
        rows =3 ,
        t =0.0 ,
        order ="79"
        )
        self .assertEqual (res_zero ,"")



        res_loop_5 ,_ ,_ ,_ ,_ ,ai5 ,tot5 ,_ ,_ =shape_array_node (
        context ={"a_i":5 },
        mode ="Grid",
        out_mode ="Loops",
        cols =5 ,
        rows =3 ,
        t =0.5 
        )
        self .assertTrue (res_loop_5 .startswith ("m "))

        res_loop_12 ,_ ,_ ,_ ,_ ,ai12 ,tot12 ,_ ,_ =shape_array_node (
        context ={"a_i":12 },
        mode ="Grid",
        out_mode ="Loops",
        cols =5 ,
        rows =3 ,
        t =0.5 
        )
        self .assertEqual (res_loop_12 ,"","Partículas más allá del umbral t deben retornar dibujo vacío")


        res_spiral_t ,_ ,_ ,_ ,_ ,_ ,tot_sp ,_ ,_ =shape_array_node (
        context ={},
        mode ="Spiral",
        out_mode ="Shape",
        count =20 ,
        t =0.4 
        )
        segments_spiral =parse_assdraw_segments (res_spiral_t )
        self .assertEqual (len (segments_spiral ),8 )


class TestShapeUnionAndDivide (unittest .TestCase ):
    """Pruebas unitarias completas para el nodo Shape Union & Divide (v1.0.8).
    
    Cubre:
    - Descomposición topológica real PolyTree (preservando agujeros en glifos compuestos como B, O, 8)
    - Descomposición de figuras disjuntas (como puntos de la i, signos de admiración)
    - Preservación del marco delimitador Effector 2 (m x1 y1 l x2 y1 m x1 y2 l x2 y2)
    - Modo Aislado (Limpio)
    - Unión Booleana (Merge) con Clipper
    - División Naive por sub-rutas
    - Fusión con etiquetas ASS
    - Evaluación multi-slot en GraphEngine
    """

    def setUp (self ):
        self .context ={}

        self .shape_B ="m 0 0 l 100 0 l 100 100 l 0 100 m 20 20 l 40 20 l 40 40 l 20 40 m 20 60 l 40 60 l 40 80 l 20 80"

        self .shape_i ="m 40 0 l 60 0 l 60 20 l 40 20 m 40 40 l 60 40 l 60 100 l 40 100"

        self .rect_a ="m 0 0 l 60 0 l 60 60 l 0 60"
        self .rect_b ="m 40 40 l 100 40 l 100 100 l 40 100"

    def test_polytree_decomposition_compound_letter_b (self ):
        """Un glifo con agujeros (B, O, 8) debe generar 1 sola figura real que contiene sus agujeros."""
        pieces =shape_union_divide_node (
        self .context ,
        drawing =self .shape_B ,
        modo ="Dividir (PolyTree)",
        bbox_mode ="Aislado (Limpio)",
        return_all_pieces =True 
        )
        self .assertEqual (len (pieces ),1 ,"La letra B debe descomponerse en exactamente 1 isla")

        self .assertEqual (pieces [0 ].count ("m "),3 )

    def test_polytree_decomposition_disjoint_letter_i (self ):
        """Un glifo con partes separadas (i, j, !) debe descomponerse en tantas figuras como islas existan."""
        pieces =shape_union_divide_node (
        self .context ,
        drawing =self .shape_i ,
        modo ="Dividir (PolyTree)",
        bbox_mode ="Aislado (Limpio)",
        return_all_pieces =True 
        )
        self .assertEqual (len (pieces ),2 ,"La letra i debe descomponerse en exactamente 2 islas independientes")

    def test_polytree_index_selection (self ):
        """La selección por índice j (1-based) debe retornar la figura correspondiente."""
        piece_1 =shape_union_divide_node (
        self .context ,
        drawing =self .shape_i ,
        modo ="Dividir (PolyTree)",
        bbox_mode ="Aislado (Limpio)",
        index_j =1 
        )
        piece_2 =shape_union_divide_node (
        self .context ,
        drawing =self .shape_i ,
        modo ="Dividir (PolyTree)",
        bbox_mode ="Aislado (Limpio)",
        index_j =2 
        )
        self .assertTrue (piece_1 .startswith ("m "))
        self .assertTrue (piece_2 .startswith ("m "))
        self .assertNotEqual (piece_1 ,piece_2 )

    def test_effector2_bbox_frame_preservation (self ):
        """El modo Marco no debe inyectar trazos fantasma de mark_str para evitar artefactos con bord > 0."""
        piece_eff2 =shape_union_divide_node (
        self .context ,
        drawing =self .shape_i ,
        modo ="Dividir (PolyTree)",
        bbox_mode ="Marco (Effector 2)",
        index_j =1 
        )

        self .assertTrue (piece_eff2 .startswith ("m "))
        self .assertNotIn ("l 60.0 0.0 m",piece_eff2 )

    def test_resolve_shape_value_text_to_shape (self ):
        """resolve_shape_value debe convertir automáticamente texto plano a dibujo ASS vectorial."""
        from nodes .shape_nodes import resolve_shape_value 
        res =resolve_shape_value ("A",self .context )
        self .assertTrue (res .startswith ("m "))

    def test_output_alignment_matrix_coordinates (self ):
        """bind_active_unit debe calcular fx_pos_x y fx_pos_y correctamente según origin_align (1-9)."""
        class DummyUnit :
            def __init__ (self ):
                self .left =10.0 
                self .center =50.0 
                self .right =90.0 
                self .top =20.0 
                self .middle =60.0 
                self .bottom =100.0 
                self .width =80.0 
                self .height =80.0 

        engine =GraphEngine ()
        unit =DummyUnit ()


        ctx7 ={}
        out_node_7 ={"properties":{"origin_align":7 }}
        engine .bind_active_unit (ctx7 ,unit ,output_node =out_node_7 )
        self .assertEqual (ctx7 ["fx_pos_x"],10.0 )
        self .assertEqual (ctx7 ["fx_pos_y"],20.0 )


        ctx5 ={}
        out_node_5 ={"properties":{"origin_align":5 }}
        engine .bind_active_unit (ctx5 ,unit ,output_node =out_node_5 )
        self .assertEqual (ctx5 ["fx_pos_x"],50.0 )
        self .assertEqual (ctx5 ["fx_pos_y"],60.0 )


        ctx3 ={}
        out_node_3 ={"properties":{"origin_align":3 }}
        engine .bind_active_unit (ctx3 ,unit ,output_node =out_node_3 )
        self .assertEqual (ctx3 ["fx_pos_x"],90.0 )
        self .assertEqual (ctx3 ["fx_pos_y"],100.0 )

    def test_isolated_clean_mode (self ):
        """El modo Aislado (Limpio) no debe contener líneas de marco delimitador."""
        piece_clean =shape_union_divide_node (
        self .context ,
        drawing =self .shape_i ,
        modo ="Dividir (PolyTree)",
        bbox_mode ="Aislado (Limpio)",
        index_j =1 
        )

        self .assertEqual (piece_clean .count ("m "),1 )

    def test_boolean_union_merge (self ):
        """La unión booleana debe fusionar figuras solapadas en un solo contorno unificado."""
        res_union =shape_union_divide_node (
        self .context ,
        drawing =self .rect_a ,
        shape_b =self .rect_b ,
        modo ="Unir (Merge/Union)",
        anchor ="origin"
        )
        self .assertTrue (res_union .startswith ("m "))

        bbox =ClipperEngine .calc_bbox_raw (res_union )
        self .assertEqual (bbox ["x1"],0.0 )
        self .assertEqual (bbox ["y1"],0.0 )
        self .assertEqual (bbox ["x2"],100.0 )
        self .assertEqual (bbox ["y2"],100.0 )

    def test_subpaths_naive_division (self ):
        """El modo de sub-rutas naive debe separar cada comando 'm' sin jerarquía."""
        pieces_naive =shape_union_divide_node (
        self .context ,
        drawing =self .shape_B ,
        modo ="Dividir (Sub-rutas)",
        bbox_mode ="Aislado (Limpio)",
        return_all_pieces =True 
        )

        self .assertEqual (len (pieces_naive ),3 )

    def test_fusion_shapes_tags (self ):
        """El modo fusión debe unir las piezas con las etiquetas indicadas."""
        fused =shape_union_divide_node (
        self .context ,
        drawing =self .shape_i ,
        modo ="Fusión (Tags)",
        tags ="\\1c&HFF0000&",
        bbox_mode ="Aislado (Limpio)"
        )
        self .assertIn ("{\\1c&HFF0000&}",fused )

    def test_fusion_shapes_list_preserves_internal_subpaths (self ):
        """Fusión con una lista de figuras debe aplicar tags entre los elementos de la lista sin romper las 'm' internas."""
        shape1 ="m 0 0 l 10 0 l 10 10 l 0 10 m 2 2 l 8 2 l 8 8 l 2 8"
        shape2 ="m 50 50 l 60 50 l 60 60 l 50 60"
        fused =shape_union_divide_node (
        self .context ,
        drawing =[shape1 ,shape2 ],
        modo ="Fusión (Tags)",
        tags ="\\1c&HFF0000&, \\1c&H00FF00&",
        anchor ="relativo"
        )

        self .assertTrue (fused .startswith ("{\\1c&HFF0000&}"))
        self .assertIn ("{\\1c&H00FF00&}",fused )

        part1 =fused .split ("{\\1c&H00FF00&}")[0 ]
        self .assertEqual (part1 .count ("m "),2 )

    def test_fusion_shapes_tags_backslash_normalization (self ):
        """Fusión debe normalizar tags accidentales con doble barra (\\\\1c -> \\1c)."""
        fused =shape_union_divide_node (
        self .context ,
        drawing =["m 0 0 l 10 10","m 20 20 l 30 30"],
        modo ="Fusión (Tags)",
        tags ="\\\\1c&HFF0000&, \\\\1c&H00FF00&",
        anchor ="relativo"
        )
        self .assertIn ("{\\1c&HFF0000&}",fused )
        self .assertIn ("{\\1c&H00FF00&}",fused )
        self .assertNotIn ("{\\\\1c",fused )

    def test_graph_engine_evaluation_multi_slots (self ):
        """GraphEngine debe evaluar correctamente todos los slots de Shape Union & Divide y sus variables d_i/d_n."""
        ctx ={"d_i":2 ,"j":99 ,"maxj":99 }
        node_def ={
        "id":42 ,
        "type":"Shape/Union & Divide",
        "properties":{
        "shape":self .shape_i ,
        "modo":"Dividir (PolyTree)",
        "bbox_mode":"Marco (Effector 2)"
        }
        }
        engine =GraphEngine ({"nodes":[node_def ],"links":[]})


        out_shp =engine .evaluate_data_node (42 ,ctx ,output_slot_index =0 )
        self .assertTrue (out_shp .startswith ("m "))
        self .assertEqual (ctx .get ("d_i"),2 )
        self .assertEqual (ctx .get ("d_n"),2 )
        self .assertEqual (ctx .get ("d_max"),2 )
        self .assertEqual (ctx .get ("maxloop"),2 )

        self .assertEqual (ctx .get ("j"),99 )
        self .assertEqual (ctx .get ("maxj"),99 )


        out_list =engine .evaluate_data_node (42 ,ctx ,output_slot_index =1 )
        import json 
        parsed =json .loads (out_list )
        self .assertEqual (len (parsed ),2 )


        out_bbox =engine .evaluate_data_node (42 ,ctx ,output_slot_index =2 )

        self .assertTrue ("40"in out_bbox and "100"in out_bbox )

    def test_divide_anchor_relative_preserves_layout (self ):
        """El anclaje 'relativo' debe preservar las posiciones relativas originales de las piezas."""
        pieces =shape_union_divide_node (
        self .context ,
        drawing =self .shape_i ,
        modo ="Dividir (PolyTree)",
        anchor ="relativo",
        return_all_pieces =True 
        )
        self .assertEqual (len (pieces ),2 )


        bboxes =[ClipperEngine .calc_bbox_raw (p )for p in pieces ]
        cys =sorted ([b ["cy"]for b in bboxes ])
        self .assertEqual (cys ,[-40.0 ,20.0 ])

    def test_divide_anchor_piezas_centers_each_piece_individually (self ):
        """El anclaje 'piezas' debe centrar cada pieza independientemente en (0,0)."""
        pieces =shape_union_divide_node (
        self .context ,
        drawing =self .shape_i ,
        modo ="Dividir (PolyTree)",
        anchor ="piezas",
        return_all_pieces =True 
        )
        self .assertEqual (len (pieces ),2 )

        bbox_dot =ClipperEngine .calc_bbox_raw (pieces [0 ])
        bbox_body =ClipperEngine .calc_bbox_raw (pieces [1 ])
        self .assertEqual (bbox_dot ["cx"],0.0 )
        self .assertEqual (bbox_dot ["cy"],0.0 )
        self .assertEqual (bbox_body ["cx"],0.0 )
        self .assertEqual (bbox_body ["cy"],0.0 )

    def test_shape_union_divide_expression_evaluation (self ):
        """d_i y d_n deben evaluarse correctamente en expresiones matemáticas y de formato."""
        from node_engine import _eval_num_expr 
        ctx ={"d_i":2 ,"d_n":5 ,"d_max":5 }
        val_ratio =_eval_num_expr ("d_i / d_n",ctx ,default =0.0 )
        self .assertEqual (val_ratio ,0.4 )
        val_cond =_eval_num_expr ("1 if d_i == 2 else 0",ctx ,default =0 )
        self .assertEqual (val_cond ,1 )

    def test_shape_multi_tag_fusion_and_gradient (self ):
        """Shape Multi debe fusionar tags o interpolar gradientes de color entre sus piezas."""
        from nodes .shape_nodes import shape_multi 


        res1 =shape_multi (self .context ,mode ="Cuadros Concéntricos",size =100.0 ,px ="4",tags ="#FF0000, #0000FF")
        self .assertIn ("{\\1c&H",res1 )
        self .assertTrue (res1 .count ("{\\1c&H")>=2 )


        res7 =shape_multi (self .context ,mode ="Roseta Radial",parts =4 ,r_out =50.0 ,r_in =0.0 ,tags ="\\1c&H0000FF&, \\1c&H00FF00&")
        self .assertIn ("{\\1c&H0000FF&}",res7 )
        self .assertIn ("{\\1c&H00FF00&}",res7 )
        self .assertEqual (res7 .count ("{\\1c&H"),4 )


        res4 =shape_multi (self .context ,mode ="Mosaico Poligonal",size =64.0 ,sides =6 ,rings =5 ,n_layers =5 ,tags ="\\1c&HFFFFFF&")
        self .assertIn ("{\\1c&HFFFFFF&}",res4 )
        self .assertEqual (res4 .count ("{\\1c&HFFFFFF&}"),5 )


        res8 =shape_multi (self .context ,drawing ="m 0 0 l 100 0 l 100 100 l 0 100",mode ="Túnel / Cascada",size1 =100.0 ,size2 =10.0 ,loop =5 ,tags ="\\1c&H000000&, \\1c&HFFFFFF&")
        self .assertEqual (res8 .count ("{\\1c&H"),5 )

    def test_fusion_tags_composition (self ):
        """El modo Fusión con Tags debe encapsular cada figura con su tag correspondiente."""
        res_fused =shape_union_divide_node (
        self .context ,
        drawing =[self .rect_a ,self .rect_b ],
        modo ="Fusión (Tags)",
        tags ="\\1c&HFF0000&, \\1c&H00FF00&"
        )
        self .assertIn ("{\\1c&HFF0000&}",res_fused )
        self .assertIn ("{\\1c&H00FF00&}",res_fused )
    def test_fusion_full_graph_preserves_inline_tags (self ):
        """GraphEngine debe preservar los tags intercalados de Fusión en el cuerpo del dibujo y no moverlos a la cabecera."""
        graph_data ={
        "nodes":[
        {"id":1 ,"type":"Loops/Main Loop","properties":{"iterador":"line"},"inputs":[]},
        {"id":2 ,"type":"MultiTag","properties":{"tag_type":"pos","X":"640","Y":"360"},"inputs":[{"link":None },{"link":None }]},
        {"id":3 ,"type":"Shape/Library","properties":{"forma":"Sakura 6T"},"inputs":[]},
        {"id":4 ,"type":"Shape/Union & Divide","properties":{"modo":"Fusión (Tags)","tagmode":"ipol","anchor":"relativo","tags":"#87F337, #61FBC7, #AF6DF6"},"inputs":[{"link":2 },{"link":None },{"link":None },{"link":None }]},
        {"id":5 ,"type":"Concatenate","properties":{"separator":"nil"},"inputs":[{"link":4 },{"link":None },{"link":5 }]},
        {"id":6 ,"type":"String","properties":{"valor":"\\an7"},"inputs":[]},
        {"id":8 ,"type":"System/Output","properties":{},"inputs":[{"link":1 },{"link":None },{"link":None },{"link":None },{"link":6 },{"link":3 }]}
        ],
        "links":[
        [1 ,1 ,0 ,8 ,0 ,"bucle"],
        [2 ,3 ,0 ,4 ,0 ,"data"],
        [3 ,4 ,0 ,8 ,5 ,"data"],
        [4 ,2 ,0 ,5 ,0 ,"data"],
        [5 ,6 ,0 ,5 ,2 ,"data"],
        [6 ,5 ,0 ,8 ,4 ,"data"]
        ]
        }
        engine =GraphEngine (graph_data )
        styles ={'Default':{'Fontname':'Arial','Fontsize':40 ,'PrimaryColour':'&H00FFFFFF&','SecondaryColour':'&H000000FF&','OutlineColour':'&H00000000&','BackColour':'&H00000000&','ScaleX':100 ,'ScaleY':100 ,'Spacing':0 ,'Outline':2 ,'Shadow':0 ,'Alignment':5 }}
        dialogues =[{'raw':'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k10}Test','is_selected':True }]
        engine .process_single (dialogues ,styles ,allow_fallback_select_all =True )

        self .assertEqual (len (engine .all_generated_lines ),1 )
        gen_text =engine .all_generated_lines [0 ]['text']

        header_block =gen_text .split ("}")[0 ]+"}"
        self .assertIn (r"\an7",header_block )
        self .assertIn (r"\pos(640,360)",header_block )
        self .assertIn (r"\1c&H37F387&",header_block )
        self .assertIn (r"\p1",header_block )

        self .assertTrue (gen_text .count (r"{\1c&H")>=5 )

    def test_fusion_shapes_tags_multi_tag_interpolation (self ):
        """fusion_shapes_tags debe interpolar múltiples tags numéricos y colores simultáneamente."""
        from clipper_engine import ClipperEngine 
        shapes =[
        "m 0 0 l 10 0 10 10 0 10",
        "m 20 0 l 30 0 30 10 20 10",
        "m 40 0 l 50 0 50 10 40 10",
        "m 60 0 l 70 0 70 10 60 10",
        "m 80 0 l 90 0 90 10 80 10"
        ]

        tag_keyframes =r"\1c&H51F6ED&\frz0\fry0\blur1, \1c&HFE88E5&\frz40\fry80\blur5"
        fused =ClipperEngine .fusion_shapes_tags (shapes ,tags =tag_keyframes )


        self .assertIn (r"{\1c&H51F6ED&\frz0\fry0\blur1}",fused )
        self .assertIn (r"\frz10\fry20\blur2",fused )
        self .assertIn (r"\frz20\fry40\blur3",fused )
        self .assertIn (r"\frz30\fry60\blur4",fused )
        self .assertIn (r"{\1c&HFE88E5&\frz40\fry80\blur5}",fused )

    def test_fusion_shapes_tags_global_tags_handling (self ):
        """Los tags únicos por línea (pos, org, an) no deben ser interpolados en piezas interiores."""
        from clipper_engine import ClipperEngine 
        shapes =[
        "m 0 0 l 10 0 10 10 0 10",
        "m 20 0 l 30 0 30 10 20 10",
        "m 40 0 l 50 0 50 10 40 10"
        ]
        tag_keyframes =r"\pos(100,200)\an7\1c#FF0000\fscx100, \pos(500,600)\an5\1c#0000FF\fscx200"
        fused =ClipperEngine .fusion_shapes_tags (shapes ,tags =tag_keyframes )


        first_block =fused .split ("}")[0 ]+"}"
        self .assertIn (r"\an7",first_block )
        self .assertIn (r"\pos(100,200)",first_block )
        self .assertIn (r"\fscx100",first_block )


        rest =fused [len (first_block ):]
        self .assertNotIn (r"\pos",rest )
        self .assertNotIn (r"\an",rest )

        self .assertIn (r"\fscx150",rest )
        self .assertIn (r"\fscx200",rest )


    def test_shape_array_grid_mode_generation (self ):
        """Shape Array en modo Grid debe generar la grilla completa con posiciones y tags."""
        from nodes .shape_nodes import shape_array_node 

        ctx =dict (self .context ,a_i =5 )
        res_shp ,pos_tag ,px ,py ,ang ,out_idx ,total_count ,cur_col ,cur_row =shape_array_node (
        context =ctx ,
        particle ="m 0 0 l 10 0 l 10 10 l 0 10",
        mode ="Grid",
        out_mode ="Loops",
        cols =3 ,
        rows =3 ,
        sep_x =5.0 ,
        sep_y =5.0 ,
        tags ="\\1c&HFF0000&, \\1c&H00FF00&, \\1c&H0000FF&",
        index_j =5 
        )
        self .assertEqual (total_count ,9 )
        self .assertEqual (out_idx ,5 )
        self .assertEqual (cur_col ,2 )
        self .assertEqual (cur_row ,2 )
        self .assertIn ("\\pos(",pos_tag )
        self .assertTrue (res_shp .startswith ("m "))


        shape_out ,_ ,_ ,_ ,_ ,_ ,_ ,_ ,_ =shape_array_node (
        context =self .context ,
        particle ="m 0 0 l 10 0 l 10 10 l 0 10",
        mode ="Grid",
        out_mode ="Shape",
        cols =3 ,
        rows =3 ,
        sep_x =5.0 ,
        sep_y =5.0 ,
        tags ="\\1c&HFF0000&"
        )
        self .assertEqual (shape_out .count ("{\\1c&H"),9 )


        shp_rings ,_ ,_ ,_ ,_ ,_ ,total_rings ,_ ,_ =shape_array_node (
        context =self .context ,
        particle ="m 0 0 l 5 0 l 5 5 l 0 5",
        mode ="Rings",
        out_mode ="Shape",
        rings =2 ,
        count_per_ring ="4, 8",
        tags ="\\1c&HFFFF00&"
        )
        self .assertEqual (total_rings ,12 )
        self .assertEqual (shp_rings .count ("{\\1c&HFFFF00&}"),12 )

    def test_shape_array_graph_engine_evaluation (self ):
        """GraphEngine debe evaluar Shape Array con tags y despachar slots correctamente."""
        node_def ={
        "id":99 ,
        "type":"Shape/Array",
        "properties":{
        "particle":"m 0 0 l 10 0 l 10 10 l 0 10",
        "modo":"Grid",
        "out_mode":"Shape",
        "cols":"2",
        "rows":"2",
        "tags":"\\1c&H111111&, \\1c&H222222&"
        }
        }
        engine =GraphEngine ({"nodes":[node_def ],"links":[]})
        out_shp =engine .evaluate_data_node (99 ,self .context ,output_slot_index =0 )
        self .assertIn ("{\\1c&H111111&}",out_shp )
        self .assertIn ("{\\1c&H222222&}",out_shp )
        self.assertEqual(out_shp.count("{\\1c&H"), 4)

    def test_shape_array_canonical_multislot_evaluation(self):
        """Shape Array canonical inputs and multi-slot outputs in GraphEngine."""
        node_def = {
            "id": 101,
            "type": "Shape/Array",
            "properties": {
                "particle": "m 0 0 l 10 0 l 10 10 l 0 10",
                "mode": "grid",
                "out_mode": "loops",
                "cols": "3",
                "rows": "2",
                "scale": "1.0",
                "anchor": "pieces",
                "order": "79"
            },
            "inputs": [],
            "outputs": [
                {"name": "Shape", "slot_index": 0},
                {"name": "\\pos Tag", "slot_index": 1},
                {"name": "X", "slot_index": 2},
                {"name": "Y", "slot_index": 3},
                {"name": "Angle (\\frz)", "slot_index": 4},
                {"name": "Index (a_i)", "slot_index": 5},
                {"name": "Total (a_n)", "slot_index": 6},
                {"name": "Col / Ring", "slot_index": 7},
                {"name": "Row / IdxRing", "slot_index": 8}
            ]
        }
        ctx = dict(self.context)
        ctx['a_i'] = 1
        engine = GraphEngine({"nodes": [node_def], "links": []})
        shp = engine.evaluate_data_node(101, ctx, output_slot_index=0)
        pos = engine.evaluate_data_node(101, ctx, output_slot_index=1)
        x_val = engine.evaluate_data_node(101, ctx, output_slot_index=2)
        y_val = engine.evaluate_data_node(101, ctx, output_slot_index=3)
        frz = engine.evaluate_data_node(101, ctx, output_slot_index=4)
        ai = engine.evaluate_data_node(101, ctx, output_slot_index=5)
        an = engine.evaluate_data_node(101, ctx, output_slot_index=6)
        col = engine.evaluate_data_node(101, ctx, output_slot_index=7)
        row = engine.evaluate_data_node(101, ctx, output_slot_index=8)

        self.assertTrue(shp.startswith("m "))
        self.assertTrue(pos.startswith("\\pos("))
        self.assertEqual(ai, "1")
        self.assertEqual(an, "6")
        self.assertEqual(col, "1")
        self.assertEqual(row, "1")

    def test_shape_library_canonical_evaluation(self):
        """Shape Library canonical evaluation in GraphEngine."""
        node_def = {
            "id": 102,
            "type": "Shape/Library",
            "properties": {
                "category": "shapes",
                "shape": "circle"
            },
            "inputs": [],
            "outputs": [
                {"name": "Shape", "slot_index": 0}
            ]
        }
        engine = GraphEngine({"nodes": [node_def], "links": []})
        shp = engine.evaluate_data_node(102, self.context, output_slot_index=0)
        self.assertTrue(isinstance(shp, str) and shp.startswith("m "))

    def test_shape_union_divide_auto_convert_text_input (self ):
        """Shape Union & Divide debe auto-convertir cadenas de texto provistas como entrada a figuras vectoriales."""
        pieces =shape_union_divide_node (
        self .context ,
        drawing ="i",
        modo ="Dividir (PolyTree)",
        return_all_pieces =True 
        )
        self .assertEqual (len (pieces ),2 )
        self .assertTrue (pieces [0 ].startswith ("m "))
        self .assertTrue (pieces [1 ].startswith ("m "))

    def test_shape_union_divide_auto_active_unit_fallback (self ):
        """Shape Union & Divide debe usar el texto de la unidad activa del Main Loop cuando no se provee entrada."""
        class DummySyl :
            def __init__ (self ,text ):
                self .text =text 
                self .text_stripped =text 

        ctx =dict (self .context )
        ctx ["active_unit"]=DummySyl ("i")
        ctx ["syl"]=ctx ["active_unit"]

        pieces =shape_union_divide_node (
        ctx ,
        drawing ="",
        modo ="Dividir (PolyTree)",
        return_all_pieces =True 
        )
        self .assertEqual (len (pieces ),2 )
    def test_shape_union_divide_auto_loop_distinct_pieces_execution (self ):
        """GraphEngine en auto-loop debe iterar d_i y despachar cada pieza independiente de la división."""
        graph_data ={
        "nodes":[
        {
        "id":1 ,
        "type":"Loops/Main Loop",
        "properties":{"iterador":"line","noblank":"No Blank"},
        "outputs":[{"name":"Loop","type":"bucle","links":[1 ]}]
        },
        {
        "id":5 ,
        "type":"Shape/Union & Divide",
        "properties":{"shape":"m 0 0 l 10 0 10 10 0 10 m 20 0 l 40 0 40 20 20 20 m 50 0 l 80 0 80 30 50 30","modo":"Dividir (PolyTree)","anchor":"center"},
        "outputs":[{"name":"Shape","type":"string","links":[2 ]}]
        },
        {
        "id":3 ,
        "type":"System/Output",
        "properties":{"origin_align":5 },
        "inputs":[
        {"name":"Loop","type":"data","link":1 },
        {"name":"Capa","type":0 ,"link":None },
        {"name":"Start","type":0 ,"link":None },
        {"name":"End","type":0 ,"link":None },
        {"name":"Tags","type":0 ,"link":None },
        {"name":"Retorno","type":"string","link":2 }
        ]
        }
        ],
        "links":[
        [1 ,1 ,0 ,3 ,0 ,"bucle"],
        [2 ,5 ,0 ,3 ,5 ,"data"]
        ]
        }
        engine =GraphEngine (graph_data )
        styles ={
        'Default':{
        'Fontname':'Arial','Fontsize':40.0 ,
        'PrimaryColour':'&H00FFFFFF&','SecondaryColour':'&H000000FF&',
        'OutlineColour':'&H00000000&','BackColour':'&H00000000&',
        'ScaleX':100.0 ,'ScaleY':100.0 ,'Spacing':0.0 ,'Outline':2.0 ,
        'Shadow':0.0 ,'Alignment':5 
        }
        }
        dialogues =[{'raw':'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Hello','is_selected':True }]
        engine .process_single (dialogues ,styles ,allow_fallback_select_all =True )
        self .assertEqual (len (engine .all_generated_lines ),3 )
        shapes_generated =[l ['text']for l in engine .all_generated_lines ]
        self .assertNotEqual (shapes_generated [0 ],shapes_generated [1 ])
        self .assertNotEqual (shapes_generated [1 ],shapes_generated [2 ])

    def test_shape_union_divide_geometric_anchors (self ):
        """Verificar los 4 modos de anclaje geométrico ('center', 'origin', 'zero', 'pos')."""
        test_shp ="m 100 100 l 120 100 120 120 100 120"
        ctx ={"fx_pos_x":300.0 ,"fx_pos_y":200.0 }


        p_center =shape_union_divide_node (ctx ,drawing =test_shp ,modo ="Dividir (PolyTree)",anchor ="center")
        bbox_c =ClipperEngine .calc_bbox_raw (p_center )
        self .assertEqual (round (bbox_c ["cx"]),0 )
        self .assertEqual (round (bbox_c ["cy"]),0 )


        p_origin =shape_union_divide_node (ctx ,drawing =test_shp ,modo ="Dividir (PolyTree)",anchor ="origin")
        bbox_o =ClipperEngine .calc_bbox_raw (p_origin )
        self .assertEqual (round (bbox_o ["x1"]),0 )
        self .assertEqual (round (bbox_o ["y1"]),0 )


        p_zero =shape_union_divide_node (ctx ,drawing =test_shp ,modo ="Dividir (PolyTree)",anchor ="zero")
        bbox_z =ClipperEngine .calc_bbox_raw (p_zero )
        self .assertEqual (round (bbox_z ["cx"]),300 )
        self .assertEqual (round (bbox_z ["cy"]),200 )


        p_pos =shape_union_divide_node (ctx ,drawing =test_shp ,modo ="Dividir (PolyTree)",anchor ="pos")
        bbox_p =ClipperEngine .calc_bbox_raw (p_pos )
        self .assertEqual (round (bbox_p ["x1"]),-200 )
        self .assertEqual (round (bbox_p ["y1"]),-100 )

    def test_resolve_shape_value_with_context_fontsize (self ):
        """Verificar que resolve_shape_value escala el shape vectorial usando el fontsize de styleref."""
        from nodes .shape_nodes import resolve_shape_value 
        from models import StyleRef ,PyxisLine ,PyxisUnit 


        style_100 =StyleRef ({"Fontname":"Arial","Fontsize":100 })
        style_20 =StyleRef ({"Fontname":"Arial","Fontsize":20 })

        line_100 =PyxisLine ()
        line_100 .styleref =style_100 
        line_100 .text_stripped ="A"

        line_20 =PyxisLine ()
        line_20 .styleref =style_20 
        line_20 .text_stripped ="A"

        shp_100 =resolve_shape_value ("A",{"active_line":line_100 })
        shp_20 =resolve_shape_value ("A",{"active_line":line_20 })

        self .assertTrue (shp_100 .startswith ("m ")or shp_100 .startswith ("m-")or shp_100 .startswith ("m0"))
        self .assertTrue (shp_20 .startswith ("m ")or shp_20 .startswith ("m-")or shp_20 .startswith ("m0"))

        bbox_100 =ClipperEngine .calc_bbox_raw (shp_100 )
        bbox_20 =ClipperEngine .calc_bbox_raw (shp_20 )


        self .assertGreater (bbox_100 ["h"],bbox_20 ["h"]*3.5 )


    def test_clean_self_intersections_with_string_fill_rule (self ):
        """clean_self_intersections y merge_multiple_shapes deben aceptar cadenas como fill_rule sin error de tipo."""
        shp ="m 0 0 l 100 0 l 100 100 l 0 100"
        res_evenodd =ClipperEngine .clean_self_intersections (shp ,fill_rule ="EvenOdd")
        res_nonzero =ClipperEngine .clean_self_intersections (shp ,fill_rule ="NonZero")
        self .assertTrue (res_evenodd .startswith ("m "))
        self .assertTrue (res_nonzero .startswith ("m "))


        res_single_merge =ClipperEngine .merge_multiple_shapes ([shp ],fill_rule ="EvenOdd")
        self .assertTrue (res_single_merge .startswith ("m "))

    def test_resolve_shape_value_json_list (self ):
        """resolve_shape_value debe deserializar listas en formato JSON string."""
        from nodes .shape_nodes import resolve_shape_value 
        import json 
        raw_list =["m 0 0 l 10 0 l 10 10 l 0 10","m 50 50 l 60 50 l 60 60 l 50 60"]
        json_str =json .dumps (raw_list )
        resolved =resolve_shape_value (json_str ,self .context )
        self .assertIsInstance (resolved ,list )
        self .assertEqual (len (resolved ),2 )
        self .assertEqual (resolved [0 ],raw_list [0 ])
        self .assertEqual (resolved [1 ],raw_list [1 ])

    def test_shape_union_divide_with_list_input_in_divide_mode (self ):
        """Dividir (PolyTree y Sub-rutas) debe descomponer correctamente entradas pasadas como lista de figuras."""
        raw_list =["m 0 0 l 10 0 l 10 10 l 0 10","m 50 50 l 60 50 l 60 60 l 50 60"]
        pieces_polytree =shape_union_divide_node (
        self .context ,
        drawing =raw_list ,
        modo ="Dividir (PolyTree)",
        return_all_pieces =True 
        )
        self .assertEqual (len (pieces_polytree ),2 )

        pieces_subpaths =shape_union_divide_node (
        self .context ,
        drawing =raw_list ,
        modo ="Dividir (Sub-rutas)",
        return_all_pieces =True 
        )
        self .assertEqual (len (pieces_subpaths ),2 )

    def test_apply_geometric_anchor_with_dict_ref_bbox (self ):
        """apply_geometric_anchor debe aceptar ref_bbox suministrado como diccionario."""
        from nodes .shape_nodes import apply_geometric_anchor 
        shp ="m 0 0 l 10 0 l 10 10 l 0 10"
        ref_dict ={"x1":0.0 ,"y1":0.0 ,"x2":100.0 ,"y2":100.0 }
        anchored =apply_geometric_anchor (shp ,anchor ="relativo",ref_bbox =ref_dict )
        self .assertTrue (anchored .startswith ("m "))
        bbox =ClipperEngine .calc_bbox_raw (anchored )

        self .assertEqual (bbox ["x1"],-50.0 )
        self .assertEqual (bbox ["y1"],-50.0 )

    def test_shape_union_divide_bbox_data_in_union_mode (self ):
        """Slot 2 (BBox Data) en modo Unir debe abarcar tanto Shape A como Shape B."""
        node_def ={
        "id":42 ,
        "type":"Shape/Union & Divide",
        "properties":{
        "shape":"m 0 0 l 50 0 l 50 50 l 0 50",
        "shape_b":"m 50 50 l 100 50 l 100 100 l 50 100",
        "modo":"Unir (Merge/Union)"
        }
        }
        engine =GraphEngine ({"nodes":[node_def ],"links":[]})
        out_bbox =engine .evaluate_data_node (42 ,self .context ,output_slot_index =2 )

        parts =[float (x )for x in out_bbox .split (",")]
        self .assertEqual (parts [0 ],0.0 )
        self .assertEqual (parts [1 ],0.0 )
        self .assertEqual (parts [2 ],100.0 )
        self .assertEqual (parts [3 ],100.0 )
        self .assertEqual (parts [6 ],100.0 )
        self .assertEqual (parts [7 ],100.0 )

    def test_shape_union_divide_dynamic_tags_memoization (self ):
        """En Fusión con Tags, si los tags cambian dinámicamente, la evaluación en GraphEngine no debe devolver caché obsoleto."""
        node_def ={
        "id":42 ,
        "type":"Shape/Union & Divide",
        "properties":{
        "shape":self .shape_i ,
        "modo":"Fusión (Tags)",
        "tags":"\\1c&HFF0000&"
        }
        }
        engine =GraphEngine ({"nodes":[node_def ],"links":[]})
        ctx1 ={"d_i":1 }
        res1 =engine .evaluate_data_node (42 ,ctx1 ,output_slot_index =0 )
        self .assertIn ("{\\1c&HFF0000&}",res1 )


        node_def ["properties"]["tags"]="\\1c&H00FF00&"
        res2 =engine .evaluate_data_node (42 ,ctx1 ,output_slot_index =0 )
        self .assertIn ("{\\1c&H00FF00&}",res2 )

    def test_shape_union_divide_fusion_single_shape_input (self ):
        """Fusión con un único shape compuesto (string) debe descomponerlo en islas y aplicar tags."""
        fused =shape_union_divide_node (
        self .context ,
        drawing =self .shape_i ,
        modo ="Fusión (Tags)",
        tags ="\\1c&H111111&, \\1c&H222222&",
        anchor ="relativo"
        )
        self .assertIn ("{\\1c&H111111&}",fused )
        self .assertIn ("{\\1c&H222222&}",fused )
        self .assertTrue (fused .startswith ("{\\1c&H111111&}"))

    def test_shape_union_divide_fusion_list_input (self ):
        """Fusión con una lista de shapes en una sola entrada debe fusionar los elementos con tags."""
        shapes_in =[self .rect_a ,self .rect_b ]
        fused =shape_union_divide_node (
        self .context ,
        drawing =shapes_in ,
        modo ="Fusión (Tags)",
        tags ="\\1c&HAAAAAA&, \\1c&HBBBBBB&",
        anchor ="relativo"
        )
        self .assertIn ("{\\1c&HAAAAAA&}",fused )
        self .assertIn ("{\\1c&HBBBBBB&}",fused )
        self .assertEqual (fused .count ("{\\1c&H"),2 )

    def test_shape_union_divide_fusion_4_port_graphengine (self ):
        """GraphEngine con layout de 4 puertos (Shape In, Tag Mode, Tags, Anchor) debe evaluar correctamente Fusión."""
        graph_data ={
        "nodes":[
        {
        "id":1 ,
        "type":"Shape/Union & Divide",
        "properties":{
        "shape":self .shape_i ,
        "modo":"Fusión (Tags)",
        "tagmode":"ipol",
        "tags":"\\1c&H123456&",
        "anchor":"relativo"
        },
        "inputs":[
        {"name":"Shape In","property":"shape"},
        {"name":"Tag Mode","property":"tagmode"},
        {"name":"Tags","property":"tags"},
        {"name":"Anchor","property":"anchor"}
        ]
        }
        ],
        "links":[]
        }
        engine =GraphEngine (graph_data )
        res =engine .evaluate_data_node (1 ,self .context ,output_slot_index =0 )
        self .assertIn ("{\\1c&H123456&}",res )

    def test_system_output_unpacks_out_list_json (self ):
        """System/Output debe desempaquetar limpiamente strings JSON cuando Out List se conecta a Return."""
        graph_data ={
        "nodes":[
        {"id":1 ,"type":"Loops/Main Loop","properties":{"iterador":"line"},"inputs":[]},
        {
        "id":2 ,
        "type":"Shape/Union & Divide",
        "properties":{
        "shape":self .shape_i ,
        "modo":"Fusión (Tags)",
        "tagmode":"ipol",
        "tags":"\\1c&HFFFFFF&",
        "anchor":"relativo"
        },
        "inputs":[
        {"name":"Shape In","property":"shape"},
        {"name":"Tag Mode","property":"tagmode"},
        {"name":"Tags","property":"tags"},
        {"name":"Anchor","property":"anchor"}
        ]
        },
        {
        "id":3 ,
        "type":"System/Output",
        "properties":{},
        "inputs":[
        {"link":1 },
        {"link":None },
        {"link":None },
        {"link":None },
        {"link":None },
        {"link":2 }
        ]
        }
        ],
        "links":[
        [1 ,1 ,0 ,3 ,0 ,"bucle"],
        [2 ,2 ,1 ,3 ,5 ,"data"]
        ]
        }
        engine =GraphEngine (graph_data )
        styles ={'Default':{'Fontname':'Arial','Fontsize':40 }}
        dialogues =[{'raw':'Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{\\k50}Test','is_selected':True }]
        engine .process_single (dialogues ,styles )
        self .assertEqual (len (engine .all_generated_lines ),1 )
        gen_text =engine .all_generated_lines [0 ]['text']
        self .assertNotIn ('["',gen_text )
        self .assertNotIn ('"]',gen_text )
        self .assertIn ('m ',gen_text )

    def test_shape_union_divide_dividir_anchors_assemble_shape (self ):
        """Dividir (PolyTree) con anchor 'piezas' debe emitir \\pos individuales en las posiciones reales de cada pieza."""
        graph_piezas ={
        'nodes':[
        {'id':1 ,'type':'Loops/Main Loop','properties':{'iterador':'line'},'inputs':[]},
        {'id':2 ,'type':'Shape/Library','properties':{'forma':'Sakura 1T'},'inputs':[]},
        {'id':3 ,'type':'Shape/Union & Divide','properties':{'modo':'Dividir (PolyTree)','anchor':'piezas'},'inputs':[{'link':2 }]},
        {'id':4 ,'type':'System/Output','properties':{'origin_align':5 },'inputs':[{'link':1 },None ,None ,None ,None ,{'link':3 }]}
        ],
        'links':[
        [1 ,1 ,0 ,4 ,0 ,'bucle'],
        [2 ,2 ,0 ,3 ,0 ,'data'],
        [3 ,3 ,0 ,4 ,5 ,'data']
        ]
        }
        engine =GraphEngine (graph_piezas ,1280 ,720 ,41.7 )
        styles ={'Default':{'Fontname':'Arial','Fontsize':40 }}
        dialogues =[{'raw':'Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{\\k50}Test','is_selected':True }]
        engine .process_single (dialogues ,styles )
        self .assertEqual (len (engine .all_generated_lines ),6 )

        positions =set ()
        for line in engine .all_generated_lines :
            import re 
            m =re .search (r'\\pos\(([^)]+)\)',line ['text'])
            self .assertIsNotNone (m )
            positions .add (m .group (1 ))

        self .assertGreaterEqual (len (positions ),4 )


    def test_shape_fusion_tags_default_empty (self ):
        """Shape Union & Divide en modo Fusión con tags='' debe generar figura unida sin bloques {...}."""
        graph ={
        'nodes':[
        {'id':1 ,'type':'Shape/Library','properties':{'forma':'Sakura 1T'},'inputs':[]},
        {'id':2 ,'type':'Shape/Union & Divide','properties':{'modo':'Fusión (Tags)','tags':'','tagmode':'ipol'},'inputs':[{'link':101 }]},
        ],
        'links':[[101 ,1 ,0 ,2 ,0 ,'data']]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (2 ,{})
        self .assertNotIn ('{',res )
        self .assertNotIn ('}',res )
        self .assertTrue (res .startswith ('m ')or 'm 'in res )

    def test_shape_fusion_tags_line_mode_exact (self ):
        """Shape Union & Divide en modo Fusión con tagmode='line' asigna tags 1:1 exactamente."""
        shapes =["m 0 0 l 10 0 l 10 10 l 0 10","m 20 0 l 30 0 l 30 10 l 20 10"]
        from clipper_engine import ClipperEngine 
        res =ClipperEngine .fusion_shapes_tags (shapes ,tags ="\\1c&H0000FF&, \\1c&H00FF00&",tag_mode ="line")
        self .assertIn ("{\\1c&H0000FF&}",res )
        self .assertIn ("{\\1c&H00FF00&}",res )

    def test_shape_fusion_tags_line_mode_fewer_tags (self ):
        """Shape Union & Divide en modo Fusión con tagmode='line' y menos tags que piezas preserva formación usando {\\p1}."""
        shapes =[
        "m 0 0 l 10 0 l 10 10 l 0 10",
        "m 20 0 l 30 0 l 30 10 l 20 10",
        "m 40 0 l 50 0 l 50 10 l 40 10"
        ]
        from clipper_engine import ClipperEngine 
        res =ClipperEngine .fusion_shapes_tags (shapes ,tags ="\\1c&H0000FF&",tag_mode ="line")

        self .assertTrue (res .startswith ("{\\1c&H0000FF&}"))
        self .assertIn ("{\\p1}",res )
        self .assertEqual (res .count ("{\\p1}"),2 )

    def test_shape_fusion_tags_grid_formation_preserved_in_line_mode (self ):
        """Verifica que en modo line con 2 tags y múltiples piezas la formación geométrica y delimitación se mantengan exactas."""
        from clipper_engine import ClipperEngine 
        shapes =[f"m {x } {y } l {x +10 } {y } l {x +10 } {y +10 } l {x } {y +10 } l {x } {y }"for x in range (0 ,50 ,10 )for y in range (0 ,50 ,10 )]
        self .assertEqual (len (shapes ),25 )
        res =ClipperEngine .fusion_shapes_tags (shapes ,tags ="\\1c&H0000FF&, \\1c&H00FF00&",tag_mode ="line")
        self .assertEqual (res .count ("{"),25 )
        self .assertIn ("{\\1c&H0000FF&}",res )
        self .assertIn ("{\\1c&H00FF00&}",res )
        self .assertEqual (res .count ("{\\p1}"),23 )

    def test_shape_fusion_tags_line_mode_excess_tags (self ):
        """Shape Union & Divide en modo Fusión con tagmode='line' y más tags que piezas descarta los tags sobrantes."""
        shapes =[
        "m 0 0 l 10 0 l 10 10 l 0 10",
        "m 20 0 l 30 0 l 30 10 l 20 10"
        ]
        from clipper_engine import ClipperEngine 
        res =ClipperEngine .fusion_shapes_tags (shapes ,tags ="\\1c&H0000FF&, \\1c&H00FF00&, \\1c&HFF0000&, \\1c&HFFFFFF&",tag_mode ="line")
        self .assertEqual (res .count ("{"),2 )
        self .assertIn ("{\\1c&H0000FF&}",res )
        self .assertIn ("{\\1c&H00FF00&}",res )
        self .assertNotIn ("{\\1c&HFF0000&}",res )
        self .assertNotIn ("{\\1c&HFFFFFF&}",res )

    def test_shape_fusion_tags_with_concatenate_zip_pipeline (self ):
        """Integración de Concatenate (Zip) alimentando Shape Union & Divide (Fusión Tags, line)."""
        graph ={
        'nodes':[
        {'id':1 ,'type':'Text','properties':{'value':'#FF0000, #00FF00'},'inputs':[],'outputs':[{'name':'String'}]},
        {'id':2 ,'type':'Text','properties':{'value':'10, 20'},'inputs':[],'outputs':[{'name':'String'}]},
        {'id':3 ,'type':'Concatenate','properties':{'separator':'zip','In1':'\\1c','In2':'\\frz'},'inputs':[{'link':101 },{'link':102 }],'outputs':[{'name':'String'}]},
        {'id':4 ,'type':'Text','properties':{'value':'m 0 0 l 10 0 l 10 10 l 0 10, m 20 0 l 30 0 l 30 10 l 20 10'},'inputs':[],'outputs':[{'name':'Shape'}]},
        {'id':5 ,'type':'Shape/Union & Divide','properties':{'mode':'fusion_tags','tagmode':'line'},'inputs':[{'link':104 },{'link':None },{'link':103 }],'outputs':[{'name':'Shape Out'}]}
        ],
        'links':[
        [101 ,1 ,0 ,3 ,0 ,'data'],
        [102 ,2 ,0 ,3 ,1 ,'data'],
        [103 ,3 ,0 ,5 ,2 ,'data'],
        [104 ,4 ,0 ,5 ,0 ,'data']
        ]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (5 ,{})
        self .assertIn ("{\\1c&H0000FF&\\frz10}",res )
        self .assertIn ("{\\1c&H00FF00&\\frz20}",res )

    def test_shape_fusion_tags_with_concatenate_zip_pipeline_ipol (self ):
        """Integración de Concatenate (Zip) alimentando Shape Union & Divide (Fusión Tags, ipol) con interpolación de tags."""
        three_squares ="m 0 0 l 10 0 10 10 0 10 m 20 0 l 30 0 30 10 20 10 m 40 0 l 50 0 50 10 40 10"
        graph ={
        'nodes':[
        {'id':1 ,'type':'Text','properties':{'value':'#0000FF, #FF0000'},'inputs':[],'outputs':[{'name':'String'}]},
        {'id':2 ,'type':'Text','properties':{'value':'0, 90'},'inputs':[],'outputs':[{'name':'String'}]},
        {'id':3 ,'type':'Concatenate','properties':{'separator':'zip','In1':'\\1c','In2':'\\frz'},'inputs':[{'link':101 },{'link':102 }],'outputs':[{'name':'String'}]},
        {'id':4 ,'type':'Text','properties':{'value':three_squares },'inputs':[],'outputs':[{'name':'Shape'}]},
        {'id':5 ,'type':'Shape/Union & Divide','properties':{'mode':'fusion_tags','tagmode':'ipol'},'inputs':[{'link':104 },{'link':None },{'link':103 }],'outputs':[{'name':'Shape Out'}]}
        ],
        'links':[
        [101 ,1 ,0 ,3 ,0 ,'data'],
        [102 ,2 ,0 ,3 ,1 ,'data'],
        [103 ,3 ,0 ,5 ,2 ,'data'],
        [104 ,4 ,0 ,5 ,0 ,'data']
        ]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (5 ,{})



        self .assertIn ("{\\1c&HFF0000&\\frz0}",res )
        self .assertIn ("{\\1c&H800080&\\frz45}",res )
        self .assertIn ("{\\1c&H0000FF&\\frz90}",res )

    def test_decompose_shape_islands_spatial_reading_order (self ):
        """decompose_shape_islands debe retornar las figuras ordenadas espacialmente de izquierda a derecha y arriba hacia abajo."""


        shape_jumbled ="m 100 0 l 110 0 110 10 100 10 m 0 0 l 10 0 10 10 0 10 m 50 0 l 60 0 60 10 50 10"
        islands =ClipperEngine .decompose_shape_islands (shape_jumbled ,bbox_mode ="marco")
        self .assertEqual (len (islands ),3 )

        bboxes =[ClipperEngine .get_bbox (ClipperEngine .parse_assdraw (isl ))for isl in islands ]
        min_xs =[b [0 ]for b in bboxes ]
        self .assertEqual (min_xs ,[0.0 ,50.0 ,100.0 ],f"Las islas deben estar ordenadas de izquierda a derecha: {min_xs }")

    def test_shape_union_divide_order_circular_cw (self ):
        """Shape Union & Divide con order='cw' debe ordenar las figuras en sentido horario desde las 12:00."""

        top ="m -5 -50 l 5 -50 5 -40 -5 -40"
        right ="m 40 -5 l 50 -5 50 5 40 5"
        bottom ="m -5 40 l 5 40 5 50 -5 50"
        left ="m -50 -5 l -40 -5 -40 5 -50 5"


        jumbled_cross =f"{bottom } {left } {top } {right }"
        islands_cw =ClipperEngine .decompose_shape_islands (jumbled_cross ,order ="cw")
        self .assertEqual (len (islands_cw ),4 )

        bboxes =[ClipperEngine .get_bbox (ClipperEngine .parse_assdraw (isl ))for isl in islands_cw ]
        centers =[(b [4 ],b [5 ])for b in bboxes ]

        self .assertAlmostEqual (centers [0 ][0 ],0.0 ,delta =1.0 )
        self .assertAlmostEqual (centers [0 ][1 ],-45.0 ,delta =1.0 )
        self .assertAlmostEqual (centers [1 ][0 ],45.0 ,delta =1.0 )
        self .assertAlmostEqual (centers [1 ][1 ],0.0 ,delta =1.0 )
        self .assertAlmostEqual (centers [2 ][0 ],0.0 ,delta =1.0 )
        self .assertAlmostEqual (centers [2 ][1 ],45.0 ,delta =1.0 )
        self .assertAlmostEqual (centers [3 ][0 ],-45.0 ,delta =1.0 )
        self .assertAlmostEqual (centers [3 ][1 ],0.0 ,delta =1.0 )

    def test_shape_fusion_tags_with_order_cw (self ):
        """Shape Union & Divide en modo Fusión (Tags) con order='cw' debe interpolar tags en secuencia horaria perfecta."""
        top ="m -5 -50 l 5 -50 5 -40 -5 -40"
        right ="m 40 -5 l 50 -5 50 5 40 5"
        bottom ="m -5 40 l 5 40 5 50 -5 50"
        left ="m -50 -5 l -40 -5 -40 5 -50 5"

        jumbled_cross =f"{bottom } {left } {top } {right }"
        graph ={
        'nodes':[
        {'id':1 ,'type':'Text','properties':{'value':jumbled_cross },'inputs':[],'outputs':[{'name':'Shape'}]},
        {'id':2 ,'type':'Shape/Union & Divide','properties':{'mode':'fusion_tags','tags':'\\1c&H0000FF&, \\1c&HFF0000&','tagmode':'ipol','order':'cw'},'inputs':[{'link':101 }],'outputs':[{'name':'Shape Out'}]}
        ],
        'links':[
        [101 ,1 ,0 ,2 ,0 ,'data']
        ]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (2 ,{})




        self .assertIn ("{\\1c&H0000FF&}",res )
        self .assertIn ("{\\1c&H5500AA&}",res )
        self .assertIn ("{\\1c&HAA0055&}",res )
        self .assertIn ("{\\1c&HFF0000&}",res )

    def test_shape_union_divide_order_modes (self ):
        """Shape Union & Divide debe responder adecuadamente a órdenes numéricos Numpad, radiales y circulares."""

        top ="m -5 -50 l 5 -50 5 -40 -5 -40"
        right ="m 40 -5 l 50 -5 50 5 40 5"
        bottom ="m -5 40 l 5 40 5 50 -5 50"
        left ="m -50 -5 l -40 -5 -40 5 -50 5"
        center ="m -5 -5 l 5 -5 5 5 -5 5"

        shapes_5 =f"{top } {right } {bottom } {left } {center }"


        islands_5 =ClipperEngine .decompose_shape_islands (shapes_5 ,order ="5")
        b0 =ClipperEngine .get_bbox (ClipperEngine .parse_assdraw (islands_5 [0 ]))
        self .assertAlmostEqual (b0 [4 ],0.0 ,delta =1.0 )
        self .assertAlmostEqual (b0 [5 ],0.0 ,delta =1.0 )


        islands_ccw =ClipperEngine .decompose_shape_islands (f"{bottom } {left } {top } {right }",order ="ccw")
        b_ccw =[ClipperEngine .get_bbox (ClipperEngine .parse_assdraw (isl ))for isl in islands_ccw ]
        c_ccw =[(b [4 ],b [5 ])for b in b_ccw ]

        self .assertAlmostEqual (c_ccw [0 ][1 ],-45.0 ,delta =1.0 )
        self .assertAlmostEqual (c_ccw [1 ][0 ],-45.0 ,delta =1.0 )
        self .assertAlmostEqual (c_ccw [2 ][1 ],45.0 ,delta =1.0 )
        self .assertAlmostEqual (c_ccw [3 ][0 ],45.0 ,delta =1.0 )


    def test_shape_multi_loop_mode_and_clip_out_mode (self ):
        """Shape Multi en loop_mode='Loops'/'Shape' y out_mode='\\clip'/'\\iclip'."""
        from nodes .shape_nodes import shape_multi 


        ctx_shape ={}
        res_shape =shape_multi (ctx_shape ,mode ="Cuadros Concéntricos",size =100.0 ,px ="4, 4",loop_mode ="Shape",out_mode =r"\iclip")
        self .assertTrue (isinstance (res_shape ,str ))
        self .assertTrue (res_shape .startswith (r"{\iclip(m "))
        self .assertTrue (res_shape .endswith (")}"))
        self .assertEqual (ctx_shape .get ("maxloop"),1 )


        ctx_loops ={"m_i":1 }
        piece1 =shape_multi (ctx_loops ,mode ="Cuadros Concéntricos",size =100.0 ,px ="4, 4",loop_mode ="Loops",out_mode =r"\clip")
        self .assertEqual (ctx_loops .get ("m_n"),13 )
        self .assertEqual (ctx_loops .get ("maxloop"),13 )
        self .assertTrue (isinstance (piece1 ,tuple ))
        self .assertTrue (piece1 [0 ].startswith (r"{\clip(m "))
        self .assertTrue (piece1 [0 ].endswith (")}"))

    def test_shape_slicer_loop_mode_and_clip_out_mode (self ):
        """Shape Slicer con loop_mode='Loops'/'Shape' y out_mode='\\clip'/'\\iclip'."""

        node_shape ={
        "id":101 ,
        "type":"Shape/Slicer",
        "properties":{
        "modo":"Rejilla 1D/2D",
        "shape":TEST_SHAPE_SQUARE ,
        "Cols":2 ,
        "Rows":2 ,
        "loop_mode":"Shape",
        "out_mode":r"\clip"
        },
        "inputs":[]
        }
        engine_inst =GraphEngine ({"nodes":[node_shape ],"links":[]})
        ctx_shape ={}
        out_shape =engine_inst .evaluate_data_node (101 ,ctx_shape )
        self .assertTrue (isinstance (out_shape ,str ))
        self .assertTrue (out_shape .startswith (r"{\clip(m "))
        self .assertTrue (out_shape .endswith (")}"))
        self .assertEqual (ctx_shape .get ("maxloop"),1 )


        node_loops ={
        "id":102 ,
        "type":"Shape/Slicer",
        "properties":{
        "modo":"Rejilla 1D/2D",
        "shape":TEST_SHAPE_SQUARE ,
        "Cols":2 ,
        "Rows":2 ,
        "loop_mode":"Loops",
        "out_mode":r"\iclip"
        },
        "inputs":[]
        }
        engine_inst_loops =GraphEngine ({"nodes":[node_loops ],"links":[]})
        ctx_loops ={"s_i":1 }
        out_piece =engine_inst_loops .evaluate_data_node (102 ,ctx_loops )
        self .assertTrue (isinstance (out_piece ,str ))
        self .assertTrue (out_piece .startswith (r"{\iclip(m "))
        self .assertTrue (out_piece .endswith (")}"))
        self .assertEqual (ctx_loops .get ("maxloop"),4 )

    def test_shape_array_maxloop_shape_vs_loops (self ):
        """Shape Array en modo Shape debe establecer maxloop=1; en modo Loops maxloop=N."""
        from nodes .shape_nodes import shape_array_node 

        ctx_shape ={}
        shape_array_node (ctx_shape ,out_mode ="Shape",cols =3 ,rows =3 )
        self .assertEqual (ctx_shape .get ("maxloop"),1 )
        self .assertEqual (ctx_shape .get ("a_n"),1 )

    def test_fusion_coordinates_preservation_no_vertical_offset (self ):
        """fusion_shapes_tags aplica compensación exacta de glifo para VSFilter cuando hay tags, y preserva coordenadas cuando no hay tags."""
        from clipper_engine import ClipperEngine 
        import re 
        shapes =[
        "m 0 100 l 50 100 l 50 150 l 0 150",
        "m 100 200 l 120 200 l 120 220 l 100 220"
        ]

        fused_notags =ClipperEngine .fusion_shapes_tags (shapes ,tags ="")
        cnt_notags =ClipperEngine .parse_assdraw (fused_notags )
        bbox_notags =ClipperEngine .get_bbox (cnt_notags )
        self .assertAlmostEqual (bbox_notags [0 ],0.0 ,places =2 )
        self .assertAlmostEqual (bbox_notags [1 ],100.0 ,places =2 )
        self .assertAlmostEqual (bbox_notags [2 ],120.0 ,places =2 )
        self .assertAlmostEqual (bbox_notags [3 ],220.0 ,places =2 )


        tags =r"\1c&HFF0000&, \1c&H00FF00&"
        fused =ClipperEngine .fusion_shapes_tags (shapes ,tags =tags )
        self .assertIn (r"{\1c&HFF0000&}",fused )
        self .assertIn (r"{\1c&H00FF00&}",fused )

        self .assertTrue ("m 0 100"in fused or "m 0.0 100.0"in fused )

        self .assertTrue ("m 50 170"in fused or "m 50.0 170.0"in fused )


    def test_shape_multi_banner_geometry(self):
        """Verifica la generación geométrica de Banner en Shape Multi, anclaje y factor t con nombres canónicos."""
        from nodes.shape_nodes import shape_multi

        # Banner con puntas flecha Arrow
        res_arrow = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Arrow", t=1.0, anchor="center")
        self.assertTrue(res_arrow.startswith("m "))
        self.assertIn("l ", res_arrow)

        # Banner plano Flat
        res_flat = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Flat", t=1.0, anchor="center")
        self.assertTrue(res_flat.startswith("m "))

        # Banner redondeado Round con curvas de Bézier
        res_round = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Round", t=1.0, anchor="center")
        self.assertTrue(res_round.startswith("m "))
        self.assertIn("b ", res_round)

        # Banner decorativo Brace
        res_brace = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Brace", t=1.0, anchor="center")
        self.assertTrue(res_brace.startswith("m "))

        # Banner Chamfer (chaflán)
        res_chamfer = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Chamfer", t=1.0, anchor="center")
        self.assertTrue(res_chamfer.startswith("m "))

        # Banner Notch (cola milano)
        res_notch = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Notch", t=1.0, anchor="center")
        self.assertTrue(res_notch.startswith("m "))

        # Banner Fishtail (doble muesca)
        res_fishtail = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Fishtail", t=1.0, anchor="center")
        self.assertTrue(res_fishtail.startswith("m "))

        # Banner Crown (tridente / corona)
        res_crown = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Crown", t=1.0, anchor="center")
        self.assertTrue(res_crown.startswith("m "))

        # Banner Ticket (perforación semicircular)
        res_ticket = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Ticket", t=1.0, anchor="center")
        self.assertTrue(res_ticket.startswith("m "))
        self.assertIn("b ", res_ticket)

        # Banner Wave (curva senoidal)
        res_wave = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Wave", t=1.0, anchor="center")
        self.assertTrue(res_wave.startswith("m "))
        self.assertIn("b ", res_wave)

        # Anclaje origin vs center deben diferir
        res_origin = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Arrow", t=1.0, anchor="origin")
        self.assertNotEqual(res_arrow, res_origin)

        # Factor t=0.5 vs t=1.0
        res_half = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Arrow", t=0.5, anchor="center")
        self.assertNotEqual(res_arrow, res_half)

        # out_mode = '\clip'
        res_clip = shape_multi(None, mode="Banner", width=200.0, height=50.0, tip_style="Arrow", t=1.0, out_mode=r"\clip")
        self.assertTrue(res_clip.startswith(r"{\clip(m "))

        # loop_mode = 'Loops'
        ctx_loop = {"m_i": 1}
        piece, pos, x, y, ang, mi, mn, _, _ = shape_multi(ctx_loop, mode="Banner", width=200.0, height=50.0, tip_style="Arrow", loop_mode="Loops")
        self.assertTrue(piece.startswith("m "))
        self.assertEqual(mn, 3)

    def test_shape_multi_gear_geometry(self):
        """Verifica la generación geométrica de Gear en Shape Multi, orificio y factor t."""
        from nodes.shape_nodes import shape_multi

        # Gear con 8 dientes y orificio central
        res_gear = shape_multi(None, mode="Gear", parts=8, r_out=60.0, r_in=45.0, r_hole=15.0, slant=0.35, t=1.0, anchor="center")
        self.assertTrue(res_gear.startswith("m "))
        self.assertIn("b ", res_gear)  # El orificio central usa b (arcos Bézier)

        # Gear macizo sin orificio
        res_solid = shape_multi(None, mode="Gear", parts=8, r_out=60.0, r_in=45.0, r_hole=0.0, slant=0.35, t=1.0, anchor="center")
        self.assertTrue(res_solid.startswith("m "))
        self.assertNotIn("b ", res_solid)

        # Anclaje origin vs center
        res_origin = shape_multi(None, mode="Gear", parts=8, r_out=60.0, r_in=45.0, r_hole=15.0, anchor="origin")
        self.assertNotEqual(res_gear, res_origin)

        # Factor t=0.5 (construcción progresiva del orificio interno con los dientes)
        res_half = shape_multi(None, mode="Gear", parts=8, r_out=60.0, r_in=45.0, r_hole=15.0, t=0.5)
        self.assertNotEqual(res_gear, res_half)
        self.assertEqual(res_gear.strip().count("m "), 2)  # t=1.0 tiene contorno exterior y orificio circular separado
        self.assertEqual(res_half.strip().count("m "), 1)  # t=0.5 es un único contorno con el orificio integrado progresivamente
        self.assertIn("b ", res_half)  # El arco interno usa curvas Bézier

        # Factor t=0.5 sin orificio
        res_solid_half = shape_multi(None, mode="Gear", parts=8, r_out=60.0, r_in=45.0, r_hole=0.0, t=0.5)
        self.assertEqual(res_solid_half.strip().count("m "), 1)
        self.assertNotIn("b ", res_solid_half)

        # out_mode = '\iclip'
        res_iclip = shape_multi(None, mode="Gear", parts=8, r_out=60.0, r_in=45.0, r_hole=15.0, out_mode=r"\iclip")
        self.assertTrue(res_iclip.startswith(r"{\iclip(m "))

        # loop_mode = 'Loops' (cada diente es una pieza)
        ctx_loop = {"m_i": 1}
        piece, pos, x, y, ang, mi, mn, _, _ = shape_multi(ctx_loop, mode="Gear", parts=8, r_out=60.0, r_in=45.0, r_hole=15.0, loop_mode="Loops")
        self.assertTrue(piece.startswith("m "))
        self.assertEqual(mn, 8)

    def test_shape_multi_piece_positioning_and_coordinate_stability(self):
        """Verifica que las formas parciales (t < 1) permanezcan estables en pantalla
        sin desplazarse a medida que se dibujan, y que en modo Loops con anchor='piezas'
        se posicione cada pieza como en Slicer (pos_x, pos_y, pos_overridden, has_org, org_x, org_y)."""
        from nodes.shape_nodes import shape_multi

        # 1. Estabilidad geométrica de formas parciales (Gear con t=0.25 vs t=1.0)
        res_mono_p = shape_multi(None, mode="Gear", parts=8, t=0.25, anchor="center")
        res_mono_f = shape_multi(None, mode="Gear", parts=8, t=1.0, anchor="center")
        self.assertEqual(res_mono_p[:50], res_mono_f[:50])

        # 2. En modo anchor='center', el contexto original de pos_x/pos_y NO debe ser alterado
        ctx_gear = {"pos_x": 500.0, "pos_y": 300.0, "fx_pos_x": 500.0, "fx_pos_y": 300.0}
        shape_multi(ctx_gear, mode="Gear", parts=8, r_out=60.0, r_in=45.0, r_hole=15.0, t=0.5, anchor="center")
        self.assertEqual(ctx_gear["pos_x"], 500.0)
        self.assertEqual(ctx_gear["pos_y"], 300.0)
        self.assertEqual(ctx_gear["fx_pos_x"], 500.0)
        self.assertEqual(ctx_gear["fx_pos_y"], 300.0)

        # 3. En modo Loops con anchor='piezas', posicionamiento idéntico a Slicer
        ctx_loop = {"pos_x": 500.0, "pos_y": 300.0, "m_i": 1}
        res_tuple = shape_multi(ctx_loop, mode="Gear", parts=8, loop_mode="Loops", anchor="piezas")
        self.assertIsInstance(res_tuple, tuple)
        self.assertEqual(len(res_tuple), 9)
        self.assertTrue(ctx_loop.get("pos_overridden"))
        self.assertTrue(ctx_loop.get("has_org"))
        self.assertEqual(ctx_loop.get("m_n"), 8)
        self.assertEqual(ctx_loop.get("multi_n"), 8)
        self.assertAlmostEqual(ctx_loop["pos_x"], 525.03, places=1)
        self.assertAlmostEqual(ctx_loop["org_x"], 525.03, places=1)

    def test_node_engine_banner_and_gear(self):
        """Evalúa nodos Shape/Multi en modos Banner y Gear a través de GraphEngine."""
        from node_engine import GraphEngine

        node_banner = {
            "id": 1,
            "type": "Shape/Multi",
            "properties": {
                "mode": "Banner",
                "width": "250.0",
                "height": "60.0",
                "tip_style": "Arrow",
                "t": "1.0",
                "anchor": "center"
            }
        }
        engine = GraphEngine({"nodes": [node_banner], "links": []})
        res_b = engine.evaluate_data_node(1, context={})
        self.assertTrue(isinstance(res_b, str) and res_b.startswith("m "))

        node_gear = {
            "id": 2,
            "type": "Shape/Multi",
            "properties": {
                "mode": "Gear",
                "parts": "12",
                "r_out": "80.0",
                "r_in": "60.0",
                "r_hole": "20.0",
                "t": "1.0",
                "anchor": "center"
            }
        }
        engine_g = GraphEngine({"nodes": [node_gear], "links": []})
        res_g = engine_g.evaluate_data_node(2, context={})
        self.assertTrue(isinstance(res_g, str) and res_g.startswith("m "))

    def test_shape_multi_mosaic_t_factor(self):
        """Verifica que el factor t controle progresivamente las piezas en Mosaico Poligonal y Multi-Shape Mosaic."""
        from nodes.shape_nodes import _gen_multi4_polygonal_mosaic, _gen_multi5_multi_shape_mosaic, shape_multi

        # 1. Polygonal Mosaic generator directly
        pieces_t0 = _gen_multi4_polygonal_mosaic(size=64.0, sides=6, rings=1, t=0.0, return_list=True)
        self.assertEqual(len(pieces_t0), 0)

        pieces_t05 = _gen_multi4_polygonal_mosaic(size=64.0, sides=6, rings=1, t=0.5, return_list=True)
        self.assertEqual(len(pieces_t05), 3)

        pieces_t1 = _gen_multi4_polygonal_mosaic(size=64.0, sides=6, rings=1, t=1.0, return_list=True)
        self.assertEqual(len(pieces_t1), 6)

        # In string mode via shape_multi
        res_str_t0 = shape_multi(self.context, mode="Mosaico Poligonal", size=64.0, sides=6, rings=1, t=0.0)
        self.assertEqual(res_str_t0, "")

        res_str_t05 = shape_multi(self.context, mode="Mosaico Poligonal", size=64.0, sides=6, rings=1, t=0.5)
        self.assertTrue(res_str_t05.startswith("m ") and res_str_t05.count("m ") == 3)

        res_str_t1 = shape_multi(self.context, mode="Mosaico Poligonal", size=64.0, sides=6, rings=1, t=1.0)
        self.assertTrue(res_str_t1.startswith("m ") and res_str_t1.count("m ") == 6)

        # In loops mode via shape_multi
        ctx0 = {}
        res_loop_t0 = shape_multi(ctx0, mode="Mosaico Poligonal", size=64.0, sides=6, rings=1, t=0.0, loop_mode="Loops")
        self.assertEqual(res_loop_t0[6], 0)

        ctx05 = {}
        res_loop_t05 = shape_multi(ctx05, mode="Mosaico Poligonal", size=64.0, sides=6, rings=1, t=0.5, loop_mode="Loops")
        self.assertEqual(res_loop_t05[6], 3)
        self.assertEqual(ctx05.get("m_n"), 3)

        ctx1 = {}
        res_loop_t1 = shape_multi(ctx1, mode="Mosaico Poligonal", size=64.0, sides=6, rings=1, t=1.0, loop_mode="Loops")
        self.assertEqual(res_loop_t1[6], 6)
        self.assertEqual(ctx1.get("m_n"), 6)

        # 2. Multi-Shape Mosaic
        tri = "m 0 0 l 20 0 l 10 20"
        sq = "m 0 0 l 20 0 l 20 20 l 0 20"
        ms_t0 = _gen_multi5_multi_shape_mosaic(shapes=[tri, sq], width=60.0, height=50.0, t=0.0, return_list=True)
        self.assertEqual(len(ms_t0), 0)

        ms_t05 = _gen_multi5_multi_shape_mosaic(shapes=[tri, sq], width=60.0, height=50.0, t=0.5, return_list=True)
        ms_t1 = _gen_multi5_multi_shape_mosaic(shapes=[tri, sq], width=60.0, height=50.0, t=1.0, return_list=True)
        self.assertGreater(len(ms_t1), len(ms_t05))
        self.assertGreater(len(ms_t05), 0)

        # 3. Via GraphEngine node evaluation
        from node_engine import GraphEngine
        node_poly = {
            "id": 10,
            "type": "Shape/Multi",
            "properties": {
                "mode": "Polygonal Mosaic",
                "size": "64.0",
                "sides": "6",
                "rings": "1",
                "t": "0.5"
            }
        }
        engine_poly = GraphEngine({"nodes": [node_poly], "links": []})
        res_poly = engine_poly.evaluate_data_node(10, context={})
        self.assertEqual(res_poly.count("m "), 3)

    def test_shape_multi_multishape_order(self):
        """Verifica que el modo Multi-Shape Mosaic respete el ordenamiento de Slicer (Normal, Invertido, 13, 79, Centro a Extremos, etc.)."""
        from nodes.shape_nodes import _gen_multi5_multi_shape_mosaic, shape_multi
        from node_engine import GraphEngine

        tri = "m 0 0 l 20 0 l 10 20"
        sq = "m 0 0 l 20 0 l 20 20 l 0 20"

        # 1. Normal vs Invertido
        pieces_normal = _gen_multi5_multi_shape_mosaic(shapes=[tri, sq], width=60.0, height=50.0, t=1.0, return_list=True, order="Normal")
        pieces_inv = _gen_multi5_multi_shape_mosaic(shapes=[tri, sq], width=60.0, height=50.0, t=1.0, return_list=True, order="Invertido")

        self.assertEqual(len(pieces_normal), len(pieces_inv))
        self.assertGreater(len(pieces_normal), 1)
        self.assertEqual(pieces_normal, list(reversed(pieces_inv)))

        # 2. t=0.5 with Normal vs Invertido gives different pieces
        half_normal = _gen_multi5_multi_shape_mosaic(shapes=[tri, sq], width=60.0, height=50.0, t=0.5, return_list=True, order="Normal")
        half_inv = _gen_multi5_multi_shape_mosaic(shapes=[tri, sq], width=60.0, height=50.0, t=0.5, return_list=True, order="Invertido")
        self.assertNotEqual(half_normal, half_inv)
        self.assertEqual(half_normal[0], pieces_normal[0])
        self.assertEqual(half_inv[0], pieces_inv[0])

        # 3. Order 13 (Bottom-Left to Top-Right)
        pieces_13 = _gen_multi5_multi_shape_mosaic(shapes=[tri, sq], width=60.0, height=50.0, t=1.0, return_list=True, order="13")
        self.assertEqual(len(pieces_13), len(pieces_normal))
        self.assertNotEqual(pieces_13, pieces_normal)

        # 4. Order Centro a Extremos / 5
        pieces_center = _gen_multi5_multi_shape_mosaic(shapes=[tri, sq], width=60.0, height=50.0, t=1.0, return_list=True, order="Centro a Extremos")
        self.assertEqual(len(pieces_center), len(pieces_normal))

        # 5. Via GraphEngine node evaluation with order property
        node_ms_norm = {
            "id": 20,
            "type": "Shape/Multi",
            "properties": {
                "mode": "Multi-Shape Mosaic",
                "shape": f"{tri}, {sq}",
                "width": "60.0",
                "height": "50.0",
                "t": "0.5",
                "order": "Normal"
            }
        }
        node_ms_inv = {
            "id": 21,
            "type": "Shape/Multi",
            "properties": {
                "mode": "Multi-Shape Mosaic",
                "shape": f"{tri}, {sq}",
                "width": "60.0",
                "height": "50.0",
                "t": "0.5",
                "order": "Invertido"
            }
        }
        engine = GraphEngine({"nodes": [node_ms_norm, node_ms_inv], "links": []})
        res_norm = engine.evaluate_data_node(20, context={})
        res_inv = engine.evaluate_data_node(21, context={})
        self.assertNotEqual(res_norm, res_inv)
        self.assertTrue(res_norm.startswith("m "))
        self.assertTrue(res_inv.startswith("m "))

    def test_shape_multi_polygonal_mosaic_order(self):
        """Verifica que el modo Polygonal Mosaic respete el ordenamiento y factor t."""
        from nodes.shape_nodes import _gen_multi4_polygonal_mosaic, shape_multi
        from node_engine import GraphEngine

        pieces_norm = _gen_multi4_polygonal_mosaic(size=64.0, sides=6, rings=2, t=1.0, return_list=True, order="Normal")
        pieces_inv = _gen_multi4_polygonal_mosaic(size=64.0, sides=6, rings=2, t=1.0, return_list=True, order="Invertido")
        self.assertEqual(len(pieces_norm), len(pieces_inv))
        self.assertGreater(len(pieces_norm), 1)
        self.assertEqual(pieces_norm, list(reversed(pieces_inv)))

        half_norm = _gen_multi4_polygonal_mosaic(size=64.0, sides=6, rings=2, t=0.5, return_list=True, order="Normal")
        half_inv = _gen_multi4_polygonal_mosaic(size=64.0, sides=6, rings=2, t=0.5, return_list=True, order="Invertido")
        self.assertNotEqual(half_norm, half_inv)
        self.assertEqual(half_norm[0], pieces_norm[0])
        self.assertEqual(half_inv[0], pieces_inv[0])

        node_poly_norm = {
            "id": 30,
            "type": "Shape/Multi",
            "properties": {
                "mode": "Polygonal Mosaic",
                "size": "64.0",
                "sides": "6",
                "rings": "2",
                "t": "0.5",
                "order": "Normal"
            }
        }
        node_poly_inv = {
            "id": 31,
            "type": "Shape/Multi",
            "properties": {
                "mode": "Polygonal Mosaic",
                "size": "64.0",
                "sides": "6",
                "rings": "2",
                "t": "0.5",
                "order": "Invertido"
            }
        }
        engine = GraphEngine({"nodes": [node_poly_norm, node_poly_inv], "links": []})
        res_norm = engine.evaluate_data_node(30, context={})
        res_inv = engine.evaluate_data_node(31, context={})
        self.assertNotEqual(res_norm, res_inv)
        self.assertTrue(res_norm.startswith("m "))
        self.assertTrue(res_inv.startswith("m "))

    def test_shape_multi_cache_equivalence(self):
        """Verifica que el resultado con caché sea idéntico bit a bit al resultado sin caché."""
        from nodes.shape_nodes import shape_multi, clear_multi_caches, _GLOBAL_MULTI_GRID_CACHE

        clear_multi_caches()
        self.assertEqual(len(_GLOBAL_MULTI_GRID_CACHE), 0)

        tri = "m 0 0 l 20 0 l 10 20"
        sq = "m 0 0 l 20 0 l 20 20 l 0 20"

        # 1st call: populates cache
        res1 = shape_multi({}, drawing=f"{tri}, {sq}", mode="Multi-Shape Mosaic", width=120.0, height=100.0, t=0.7, order="79")
        self.assertGreater(len(_GLOBAL_MULTI_GRID_CACHE), 0)

        # 2nd call: hits cache
        res2 = shape_multi({}, drawing=f"{tri}, {sq}", mode="Multi-Shape Mosaic", width=120.0, height=100.0, t=0.7, order="79")
        self.assertEqual(res1, res2)

    def test_shape_multi_cache_loop_mode(self):
        """Verifica que el modo Loops utilice la memorización de piezas y extraiga cada m_i correctamente."""
        from nodes.shape_nodes import shape_multi, clear_multi_caches

        clear_multi_caches()
        tri = "m 0 0 l 20 0 l 10 20"

        ctx = {'m_i': 1}
        piece1, pos1, x1, y1, ang1, mi1, mn1, col1, row1 = shape_multi(ctx, drawing=tri, mode="Multi-Shape Mosaic", width=80.0, height=80.0, loop_mode="Loops", order="Normal")

        self.assertEqual(mi1, 1)
        self.assertGreater(mn1, 1)
        self.assertTrue(piece1.startswith("m "))

        # Second iteration: m_i = 2
        ctx['m_i'] = 2
        piece2, pos2, x2, y2, ang2, mi2, mn2, col2, row2 = shape_multi(ctx, drawing=tri, mode="Multi-Shape Mosaic", width=80.0, height=80.0, loop_mode="Loops", order="Normal")

        self.assertEqual(mi2, 2)
        self.assertEqual(mn2, mn1)
        self.assertNotEqual(piece1, piece2)
        self.assertTrue(piece2.startswith("m "))

    def test_shape_multi_cache_invalidation(self):
        """Verifica que clear_multi_caches vacíe completamente la caché global."""
        from nodes.shape_nodes import shape_multi, clear_multi_caches, _GLOBAL_MULTI_GRID_CACHE

        shape_multi({}, drawing="m 0 0 l 10 0 l 10 10 l 0 10", mode="Multi-Shape Mosaic", width=50.0, height=50.0)
        self.assertGreater(len(_GLOBAL_MULTI_GRID_CACHE), 0)

        clear_multi_caches()
        self.assertEqual(len(_GLOBAL_MULTI_GRID_CACHE), 0)

    def test_shape_slicer_canonical_modes_graphengine(self):
        """Shape/Slicer evaluado a través de GraphEngine con modos canónicos en minúsculas."""
        for mode_name in ["grid", "hex", "tri", "diamond", "rings", "cubes"]:
            node = {
                "id": 201,
                "type": "Shape/Slicer",
                "properties": {
                    "mode": mode_name,
                    "shape": TEST_SHAPE_SQUARE,
                    "cols": "2",
                    "rows": "2",
                    "size_x": "20",
                    "size_y": "20"
                },
                "inputs": []
            }
            engine = GraphEngine({"nodes": [node], "links": []})
            ctx = {"s_i": 1}
            res = engine.evaluate_data_node(201, ctx, output_slot_index=0)
            self.assertTrue(isinstance(res, str), f"Modo {mode_name} debe retornar string")
            self.assertTrue(res.startswith("m "), f"Modo {mode_name} debe retornar ASSdraw válido")

    def test_shape_stroke_canonical_graphengine(self):
        """Shape/Stroke evaluado a través de GraphEngine con props canónicas en minúsculas."""
        node = {
            "id": 202,
            "type": "Shape/Stroke",
            "properties": {
                "shape": "m 0 0 l 100 0",
                "width": "6.0",
                "join_mode": "round",
                "cap_mode": "bezier",
                "miter_limit": "2.0"
            },
            "inputs": []
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        ctx = {}
        res_shape = engine.evaluate_data_node(202, ctx, output_slot_index=0)
        res_width = engine.evaluate_data_node(202, ctx, output_slot_index=1)
        self.assertTrue(isinstance(res_shape, str))
        self.assertTrue(res_shape.startswith("m "))
        self.assertEqual(res_width, "6.0")

    def test_shape_walker_canonical_graphengine(self):
        """Shape/Walker evaluado a través de GraphEngine con modos canónicos global y piece."""
        node = {
            "id": 203,
            "type": "Shape/Walker",
            "properties": {
                "shape": "m 0 0 l 100 0 l 100 100",
                "progress": "0.5",
                "start_t": "0.0",
                "mode": "global",
                "invert": "normal",
                "subdivs": "30"
            },
            "inputs": []
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        ctx = {"pos_x": 10.0, "pos_y": 20.0}
        shape_out = engine.evaluate_data_node(203, ctx, output_slot_index=0)
        pos_out = engine.evaluate_data_node(203, ctx, output_slot_index=1)
        frz_out = engine.evaluate_data_node(203, ctx, output_slot_index=2)
        len_out = engine.evaluate_data_node(203, ctx, output_slot_index=3)
        tip_x_out = engine.evaluate_data_node(203, ctx, output_slot_index=4)
        tip_y_out = engine.evaluate_data_node(203, ctx, output_slot_index=5)

        self.assertTrue(shape_out.startswith("m "))
        self.assertTrue(pos_out.startswith(r"\pos("))
        self.assertTrue(frz_out.startswith(r"\frz"))
        self.assertAlmostEqual(float(len_out), 100.0, places=1)
        self.assertAlmostEqual(float(tip_x_out), 110.0, places=1)
        self.assertAlmostEqual(float(tip_y_out), 20.0, places=1)

    def test_shape_manipulator_canonical_graphengine(self):
        """Shape/Manipulator evaluado a través de GraphEngine con props canónicas."""
        node = {
            "id": 204,
            "type": "Shape/Manipulator",
            "properties": {
                "shape": "m 0 0 l 100 0 l 100 100 l 0 100",
                "mode": "scale",
                "scale_x": "200",
                "scale_y": "200",
                "anchor": "center",
                "t": "1.0"
            },
            "inputs": []
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        res = engine.evaluate_data_node(204, {})
        self.assertTrue(isinstance(res, str))
        self.assertTrue(res.startswith("m "))

    def test_shape_transform_canonical_graphengine(self):
        """Shape/Transform evaluado a través de GraphEngine con props canónicas."""
        node = {
            "id": 205,
            "type": "Shape/Transform",
            "properties": {
                "shape": "m 0 0 l 100 0 l 100 100 l 0 100",
                "mode": "inflate",
                "ratio": "1.0",
                "inflate_mode": "circle",
                "anchor": "center",
                "t": "0.5"
            },
            "inputs": []
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        res = engine.evaluate_data_node(205, {})
        self.assertTrue(isinstance(res, str))
        self.assertTrue(res.startswith("m "))

    def test_shape_filter_canonical_graphengine(self):
        """Shape/Filter evaluado a través de GraphEngine con props canónicas."""
        node = {
            "id": 206,
            "type": "Shape/Filter",
            "properties": {
                "shape": "m 0 0 l 100 0 l 100 100 l 0 100",
                "mode": "vertices",
                "expr_x": "x + 10",
                "expr_y": "y + 5",
                "t": "1.0",
                "subdivs": "0"
            },
            "inputs": []
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        res = engine.evaluate_data_node(206, {})
        self.assertTrue(isinstance(res, str))
        self.assertTrue(res.startswith("m "))

    def test_shape_union_divide_canonical_graphengine(self):
        """Shape/Union & Divide evaluado a través de GraphEngine con props canónicas en minúsculas."""
        # Divide mode
        node_div = {
            "id": 301,
            "type": "Shape/Union & Divide",
            "properties": {
                "shape": "m 0 0 l 20 0 l 20 20 l 0 20 m 50 50 l 70 50 l 70 70 l 50 70",
                "mode": "divide",
                "fill_type": "evenodd",
                "anchor": "pieces",
                "order": "79"
            },
            "inputs": []
        }
        engine_div = GraphEngine({"nodes": [node_div], "links": []})
        res_div = engine_div.evaluate_data_node(301, {"d_i": 1})
        self.assertTrue(isinstance(res_div, str))
        self.assertTrue(res_div.startswith("m "))

        # Union mode
        node_union = {
            "id": 302,
            "type": "Shape/Union & Divide",
            "properties": {
                "shape": "m 0 0 l 20 0 l 20 20 l 0 20",
                "shape_b": "m 10 0 l 30 0 l 30 20 l 10 20",
                "mode": "union",
                "fill_type": "evenodd",
                "anchor": "center"
            },
            "inputs": []
        }
        engine_union = GraphEngine({"nodes": [node_union], "links": []})
        res_union = engine_union.evaluate_data_node(302, {})
        self.assertTrue(isinstance(res_union, str))
        self.assertTrue(res_union.startswith("m "))

        # Difference mode
        node_diff = {
            "id": 303,
            "type": "Shape/Union & Divide",
            "properties": {
                "shape": "m 0 0 l 30 0 l 30 30 l 0 30",
                "shape_b": "m 10 10 l 20 10 l 20 20 l 10 20",
                "mode": "difference",
                "fill_type": "evenodd",
                "anchor": "pieces"
            },
            "inputs": []
        }
        engine_diff = GraphEngine({"nodes": [node_diff], "links": []})
        res_diff = engine_diff.evaluate_data_node(303, {})
        self.assertTrue(isinstance(res_diff, str))
        self.assertTrue(res_diff.startswith("m "))

    def test_shape_multi_canonical_graphengine(self):
        """Shape/Multi evaluado a través de GraphEngine con props canónicas en minúsculas."""
        node_multi = {
            "id": 304,
            "type": "Shape/Multi",
            "properties": {
                "mode": "concentric_squares",
                "size": "80.0",
                "px": "4",
                "separation": "2.0",
                "t": "1.0",
                "anchor": "center",
                "out_mode": "shape",
                "loop_mode": "shape"
            },
            "inputs": []
        }
        engine_multi = GraphEngine({"nodes": [node_multi], "links": []})
        res_multi = engine_multi.evaluate_data_node(304, {})
        self.assertTrue(isinstance(res_multi, str))
        self.assertTrue(res_multi.startswith("m "))

    def test_shape_concentric_borders_canonical_graphengine(self):
        """Shape/Concentric Borders evaluado a través de GraphEngine con props canónicas en minúsculas."""
        # Hollow shape mode
        node_borders = {
            "id": 305,
            "type": "Shape/Concentric Borders",
            "properties": {
                "shape": "m 0 0 l 50 0 l 50 50 l 0 50",
                "mode": "hollow",
                "loop_count": "3",
                "separation": "5",
                "overlap": "0.5",
                "out_mode": "shape",
                "anchor": "relative"
            },
            "inputs": []
        }
        engine_borders = GraphEngine({"nodes": [node_borders], "links": []})
        res_borders = engine_borders.evaluate_data_node(305, {"b_i": 1})
        self.assertTrue(isinstance(res_borders, str))
        self.assertTrue(res_borders.startswith("m "))

        # Clip output mode
        node_clip = {
            "id": 306,
            "type": "Shape/Concentric Borders",
            "properties": {
                "shape": "m 0 0 l 50 0 l 50 50 l 0 50",
                "mode": "solid",
                "loop_count": "2",
                "separation": "4",
                "overlap": "0.5",
                "out_mode": "clip",
                "anchor": "relative"
            },
            "inputs": []
        }
        engine_clip = GraphEngine({"nodes": [node_clip], "links": []})
        res_clip = engine_clip.evaluate_data_node(306, {"b_i": 1})
        self.assertTrue(isinstance(res_clip, str))
        self.assertTrue(res_clip.startswith("\\clip("))


if __name__ =="__main__":
    unittest .main ()





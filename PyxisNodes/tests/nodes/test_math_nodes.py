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

"""Pruebas unitarias para nodos matematicos, vectorizados y osciladores de tags."""

import math 
import time 
import unittest 

from nodes .math_nodes import eval_math_node ,_eval_num 
from nodes .tag_nodes import tag_oscillator_node 
from particle_nodes import sort_particles ,_point_in_contour 


class TestUnifiedMathNode (unittest .TestCase ):
    """Pruebas completas de todas las categorias y operaciones del nodo Math."""

    def test_eval_num_helper (self ):
        ctx ={"x":10 ,"syl":{"duration":500 }}
        self .assertEqual (_eval_num ("15.5",ctx ),15.5 )
        self .assertEqual (_eval_num ("x",ctx ),10.0 )
        self .assertEqual (_eval_num ("syl.duration",ctx ),500.0 )
        self .assertEqual (_eval_num ("x * 2 + 5",ctx ),25.0 )




    def test_basico_suma (self ):
        res =eval_math_node (None ,categoria ="Basico",operacion ="Suma",A =10 ,B =25 )
        self .assertEqual (res ,35.0 )

    def test_basico_resta (self ):
        res =eval_math_node (None ,categoria ="Basico",operacion ="Resta",A =50 ,B =15 )
        self .assertEqual (res ,35.0 )

    def test_basico_multiplicacion (self ):
        res =eval_math_node (None ,categoria ="Basico",operacion ="Multiplicacion",A =6 ,B =7 )
        self .assertEqual (res ,42.0 )

    def test_basico_division (self ):
        res =eval_math_node (None ,categoria ="Basico",operacion ="Division",A =100 ,B =4 )
        self .assertEqual (res ,25.0 )

        res_zero =eval_math_node (None ,categoria ="Basico",operacion ="Division",A =100 ,B =0 )
        self .assertEqual (res_zero ,0.0 )

    def test_basico_modulo (self ):
        res =eval_math_node (None ,categoria ="Basico",operacion ="Modulo",A =10 ,B =3 )
        self .assertEqual (res ,1.0 )

        res_zero =eval_math_node (None ,categoria ="Basico",operacion ="Modulo",A =10 ,B =0 )
        self .assertEqual (res_zero ,0.0 )

    def test_basico_potencia (self ):
        res =eval_math_node (None ,categoria ="Basico",operacion ="Potencia",A =2 ,B =8 )
        self .assertEqual (res ,256.0 )

    def test_basico_absoluto (self ):
        res =eval_math_node (None ,categoria ="Basico",operacion ="Absoluto",A =-42 )
        self .assertEqual (res ,42.0 )

    def test_basico_negativo (self ):
        res =eval_math_node (None ,categoria ="Basico",operacion ="Negativo",A =15 )
        self .assertEqual (res ,-15.0 )

    def test_basico_redondear (self ):
        res =eval_math_node (None ,categoria ="Basico",operacion ="Redondear",A =3.7 )
        self .assertEqual (res ,4.0 )

    def test_basico_piso (self ):
        res =eval_math_node (None ,categoria ="Basico",operacion ="Piso",A =3.9 )
        self .assertEqual (res ,3.0 )

    def test_basico_techo (self ):
        res =eval_math_node (None ,categoria ="Basico",operacion ="Techo",A =3.1 )
        self .assertEqual (res ,4.0 )




    def test_trigono_seno (self ):
        res =eval_math_node (None ,categoria ="Trigono",operacion ="Seno",A =90 )
        self .assertAlmostEqual (res ,1.0 ,places =5 )

    def test_trigono_coseno (self ):
        res =eval_math_node (None ,categoria ="Trigono",operacion ="Coseno",A =0 )
        self .assertAlmostEqual (res ,1.0 ,places =5 )

    def test_trigono_tangente (self ):
        res =eval_math_node (None ,categoria ="Trigono",operacion ="Tangente",A =45 )
        self .assertAlmostEqual (res ,1.0 ,places =5 )

    def test_trigono_arcseno (self ):
        res =eval_math_node (None ,categoria ="Trigono",operacion ="ArcSeno",A =1.0 )
        self .assertAlmostEqual (res ,90.0 ,places =5 )

    def test_trigono_arccoseno (self ):
        res =eval_math_node (None ,categoria ="Trigono",operacion ="ArcCoseno",A =1.0 )
        self .assertAlmostEqual (res ,0.0 ,places =5 )

    def test_trigono_arctangente (self ):
        res =eval_math_node (None ,categoria ="Trigono",operacion ="ArcTangente",A =1.0 )
        self .assertAlmostEqual (res ,45.0 ,places =5 )

    def test_trigono_atan2 (self ):
        res =eval_math_node (None ,categoria ="Trigono",operacion ="ArcTangente2",Y =10.0 ,X =10.0 )
        self .assertAlmostEqual (res ,45.0 ,places =5 )




    def test_easing_ease_in (self ):
        res =eval_math_node (None ,categoria ="Easing",operacion ="EaseIn",t =0.5 )
        self .assertEqual (res ,0.25 )

    def test_easing_ease_out (self ):
        res =eval_math_node (None ,categoria ="Easing",operacion ="EaseOut",t =0.5 )
        self .assertEqual (res ,0.75 )

    def test_easing_ease_in_out (self ):
        res1 =eval_math_node (None ,categoria ="Easing",operacion ="EaseInOut",t =0.25 )
        res2 =eval_math_node (None ,categoria ="Easing",operacion ="EaseInOut",t =0.75 )
        self .assertEqual (res1 ,0.125 )
        self .assertEqual (res2 ,0.875 )




    def test_ondas_seno (self ):
        res =eval_math_node (None ,categoria ="Ondas",operacion ="Seno",t =0.25 ,Frecuencia =1.0 ,Amplitud =10.0 )
        self .assertAlmostEqual (res ,10.0 ,places =4 )

    def test_ondas_cuadrada (self ):
        res_pos =eval_math_node (None ,categoria ="Ondas",operacion ="Cuadrada",t =0.25 ,Frecuencia =1.0 ,Amplitud =5.0 )
        res_neg =eval_math_node (None ,categoria ="Ondas",operacion ="Cuadrada",t =0.75 ,Frecuencia =1.0 ,Amplitud =5.0 )
        self .assertEqual (res_pos ,5.0 )
        self .assertEqual (res_neg ,-5.0 )




    def test_utilidades_clamp (self ):
        res_high =eval_math_node (None ,categoria ="Utilidades",operacion ="Clamp",Value =150 ,Min =0 ,Max =100 )
        res_low =eval_math_node (None ,categoria ="Utilidades",operacion ="Clamp",Value =-20 ,Min =0 ,Max =100 )
        res_mid =eval_math_node (None ,categoria ="Utilidades",operacion ="Clamp",Value =50 ,Min =0 ,Max =100 )
        self .assertEqual (res_high ,100.0 )
        self .assertEqual (res_low ,0.0 )
        self .assertEqual (res_mid ,50.0 )

    def test_utilidades_lerp (self ):
        res =eval_math_node (None ,categoria ="Utilidades",operacion ="Lerp",A =100 ,B =200 ,t =0.5 )
        self .assertEqual (res ,150.0 )

    def test_utilidades_min_max (self ):
        self .assertEqual (eval_math_node (None ,categoria ="Utilidades",operacion ="Minimo",A =10 ,B =20 ),10.0 )
        self .assertEqual (eval_math_node (None ,categoria ="Utilidades",operacion ="Maximo",A =10 ,B =20 ),20.0 )

    def test_utilidades_aleatorio_con_semilla (self ):
        ctx ={"syl":{"i":3 }}
        res1 =eval_math_node (ctx ,categoria ="Utilidades",operacion ="Aleatorio",Min =0 ,Max =1000 ,Seed ="syl.i")
        res2 =eval_math_node (ctx ,categoria ="Utilidades",operacion ="Aleatorio",Min =0 ,Max =1000 ,Seed ="syl.i")
        self .assertEqual (res1 ,res2 )

    def test_utilidades_mapear_rango (self ):
        res =eval_math_node (None ,categoria ="Utilidades",operacion ="MapearRango",Value =5 ,MinIn =0 ,MaxIn =10 ,MinOut =0 ,MaxOut =100 )
        self .assertEqual (res ,50.0 )


class TestVectorizedMath (unittest .TestCase ):
    """Pruebas de optimizaciones vectorizadas y ordenamiento de particulas."""

    def setUp (self ):
        self .items =[(float (x ),float (y ),255 ,255 ,255 ,255 )for x in range (50 )for y in range (100 )]

    def test_numpad_sorting_accuracy (self ):
        orders =["79","13","97","31","5","-5","71","17","rand"]
        for order in orders :
            sorted_items =sort_particles (self .items ,order_code =order )
            self .assertEqual (len (sorted_items ),len (self .items ),f"Fallo conteo para orden {order }")
            self .assertTrue (isinstance (sorted_items ,list ),f"Se esperaba lista para orden {order }")

    def test_vectorized_sorting_speed (self ):
        large_items =[(float (x ),float (y ))for x in range (100 )for y in range (100 )]
        start =time .time ()
        res =sort_particles (large_items ,order_code ="79")
        elapsed =time .time ()-start 
        self .assertEqual (len (res ),10000 )
        self .assertLess (elapsed ,0.5 ,f"Ordenamiento vectorizado tomo demasiado tiempo ({elapsed :.4f}s)")

    def test_point_in_contour (self ):
        poly =[(0 ,0 ),(100 ,0 ),(100 ,100 ),(0 ,100 )]
        self .assertTrue (_point_in_contour (50 ,50 ,poly ))
        self .assertFalse (_point_in_contour (150 ,50 ,poly ))


class TestTagOscillatorNode (unittest .TestCase ):
    """Pruebas completas para el nodo Tag Oscilador."""

    def test_basic_oscillation_sequence (self ):
        ctx ={"start_time":0.0 ,"end_time":1000.0 }
        res =tag_oscillator_node (
        context =ctx ,
        step_ms =200.0 ,
        trans_ms =50.0 ,
        tags =r"\fscx140\fscy140,\fscx100\fscy100",
        modo_oscilacion ="Onda",
        modo_orden ="Secuencial",
        output_slot_index =0 
        )
        self .assertIn (r"\t(0,50,\fscx140\fscy140)",res )
        self .assertIn (r"\t(200,250,\fscx100\fscy100)",res )
        self .assertIn (r"\t(400,450,\fscx140\fscy140)",res )
        self .assertIn (r"\t(600,650,\fscx100\fscy100)",res )
        self .assertIn (r"\t(800,850,\fscx140\fscy140)",res )

    def test_strobe_rigid_mode (self ):
        ctx ={"start_time":0.0 ,"end_time":500.0 }
        res =tag_oscillator_node (
        context =ctx ,
        step_ms =100.0 ,
        tags =r"\1c&HFF0000&,\1c&H00FF00&",
        modo_oscilacion ="Destellos",
        output_slot_index =0 
        )
        self .assertIn (r"\t(0,1,\1c&HFF0000&)",res )
        self .assertIn (r"\t(100,101,\1c&H00FF00&)",res )

    def test_duty_cycle (self ):
        ctx ={"start_time":0.0 ,"end_time":400.0 }
        res =tag_oscillator_node (
        context =ctx ,
        step_ms =200.0 ,
        duty_cycle =0.25 ,
        tags =r"\fscx120,\fscx100",
        output_slot_index =0 
        )
        self .assertIn (r"\t(0,50,\fscx120)",res )
        self .assertIn (r"\t(200,250,\fscx100)",res )

    def test_ping_pong_order (self ):
        ctx ={"start_time":0.0 ,"end_time":800.0 }
        keyframes =tag_oscillator_node (
        context =ctx ,
        step_ms =200.0 ,
        trans_ms =50.0 ,
        tags =r"\1c&H111111&,\1c&H222222&,\1c&H333333&",
        modo_orden ="Ping-Pong",
        output_slot_index =2 
        )
        tag_sequence =[k [2 ]for k in keyframes ]
        self .assertEqual (tag_sequence [0 ],r"\1c&H111111&")
        self .assertEqual (tag_sequence [1 ],r"\1c&H222222&")
        self .assertEqual (tag_sequence [2 ],r"\1c&H333333&")
        self .assertEqual (tag_sequence [3 ],r"\1c&H222222&")

    def test_rhythm_pattern (self ):
        ctx ={"start_time":0.0 ,"end_time":600.0 }
        keyframes =tag_oscillator_node (
        context =ctx ,
        rhythm_pattern ="100,50,200",
        trans_ms =30.0 ,
        tags =r"\alpha&H00&,\alpha&HFF&",
        output_slot_index =2 
        )
        t_starts =[k [0 ]for k in keyframes ]
        self .assertEqual (t_starts [0 ],0 )
        self .assertEqual (t_starts [1 ],100 )
        self .assertEqual (t_starts [2 ],150 )
        self .assertEqual (t_starts [3 ],350 )



class TestBasicsBNodes(unittest.TestCase):
    """Pruebas unitarias para micro-lote canónico Basics-B."""

    def test_canonical_math_basic_operations(self):
        self.assertEqual(eval_math_node(None, category="basic", operation="add", A=15, B=25), 40.0)
        self.assertEqual(eval_math_node(None, category="basic", operation="sub", A=50, B=20), 30.0)
        self.assertEqual(eval_math_node(None, category="basic", operation="mul", A=6, B=7), 42.0)
        self.assertEqual(eval_math_node(None, category="basic", operation="div", A=100, B=4), 25.0)
        self.assertEqual(eval_math_node(None, category="basic", operation="mod", A=10, B=3), 1.0)
        self.assertEqual(eval_math_node(None, category="basic", operation="pow", A=2, B=4), 16.0)

    def test_canonical_math_rounding_and_clamping(self):
        self.assertEqual(eval_math_node(None, category="rounding", operation="round", A=3.7), 4.0)
        self.assertEqual(eval_math_node(None, category="rounding", operation="floor", A=3.9), 3.0)
        self.assertEqual(eval_math_node(None, category="rounding", operation="ceil", A=3.1), 4.0)
        self.assertEqual(eval_math_node(None, category="clamping", operation="clamp", Value=150, Min=0, Max=100), 100.0)
        self.assertEqual(eval_math_node(None, category="clamping", operation="min", A=10, B=20), 10.0)
        self.assertEqual(eval_math_node(None, category="clamping", operation="max", A=10, B=20), 20.0)

    def test_canonical_math_easing_and_waves(self):
        self.assertEqual(eval_math_node(None, category="easing", operation="ease_in", t=0.5), 0.25)
        self.assertEqual(eval_math_node(None, category="easing", operation="ease_out", t=0.5), 0.75)
        res_wave = eval_math_node(None, category="waves", operation="sine", t=0.25, freq=1.0, amp=10.0)
        self.assertAlmostEqual(res_wave, 10.0, places=4)

    def test_graphengine_basics_math(self):
        from node_engine import GraphEngine
        graph = {
            'nodes': [
                {'id': 1, 'type': 'Basics/Math', 'properties': {'category': 'basic', 'operation': 'add', 'A': '12', 'B': '8'}, 'inputs': [], 'outputs': [{'name': 'Out'}]}
            ],
            'links': []
        }
        engine = GraphEngine(graph)
        self.assertEqual(engine.evaluate_data_node(1, {}), "20")

    def test_graphengine_basics_multirandom(self):
        from node_engine import GraphEngine
        graph = {
            'nodes': [
                {'id': 1, 'type': 'Basics/MultiRandom', 'properties': {'mode': 'Rfake', 'min': '10', 'max': '50', 'counter': '5'}, 'inputs': [], 'outputs': [{'name': 'Data'}]}
            ],
            'links': []
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {})
        self.assertTrue(res.isdigit())
        self.assertGreaterEqual(int(res), 10)
        self.assertLessEqual(int(res), 50)

    def test_graphengine_basics_concatenate(self):
        from node_engine import GraphEngine
        graph = {
            'nodes': [
                {'id': 1, 'type': 'Basics/String', 'properties': {'value': 'Hello'}, 'inputs': [], 'outputs': [{'name': 'String'}]},
                {'id': 2, 'type': 'Basics/String', 'properties': {'value': 'World'}, 'inputs': [], 'outputs': [{'name': 'String'}]},
                {'id': 3, 'type': 'Basics/Concatenate', 'properties': {'separator': 'space'}, 'inputs': [{'link': 101}, {'link': 102}], 'outputs': [{'name': 'String'}]}
            ],
            'links': [
                [101, 1, 0, 3, 0, 'data'],
                [102, 2, 0, 3, 1, 'data']
            ]
        }
        engine = GraphEngine(graph)
        self.assertEqual(engine.evaluate_data_node(3, {}), "Hello World")

    def test_graphengine_basics_dynamic_format(self):
        from node_engine import GraphEngine
        graph = {
            'nodes': [
                {'id': 1, 'type': 'Basics/Number', 'properties': {'value': '42'}, 'inputs': [], 'outputs': [{'name': 'Number'}]},
                {'id': 2, 'type': 'Basics/Dynamic Format', 'properties': {'format': 'Value is %04d'}, 'inputs': [{'link': 101}], 'outputs': [{'name': 'String'}]}
            ],
            'links': [
                [101, 1, 0, 2, 0, 'data']
            ]
        }
        engine = GraphEngine(graph)
        self.assertEqual(engine.evaluate_data_node(2, {}), "Value is 0042")


if __name__ == "__main__":
    unittest.main()

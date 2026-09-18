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

"""Pruebas unitarias completas para nodos de particulas y emisores morfologicos."""

import unittest 
from models import PyxisLine ,PyxisUnit 
from particle_nodes import particle_text_node ,particle_image_node ,sort_particles 
from node_engine import GraphEngine ,merge_ass_tags 


class TestParticleNodesCore (unittest .TestCase ):
    """Pruebas para nodos de particulas de texto e imagen con ordenamiento Numpad."""

    def setUp (self ):
        self .context ={
        'active_unit':PyxisUnit (),
        'active_line':PyxisLine (),
        'fx_i':1 
        }

    def test_numpad_sorting (self ):
        pts =[(0 ,0 ),(10 ,0 ),(0 ,10 ),(10 ,10 ),(5 ,5 )]
        res_79 =sort_particles (pts ,order_code ="79",get_xy =lambda p :(p [0 ],p [1 ]))
        self .assertEqual (res_79 [0 ],(0 ,0 ))
        self .assertEqual (res_79 [-1 ],(10 ,10 ))

        res_5 =sort_particles (pts ,order_code ="5",get_xy =lambda p :(p [0 ],p [1 ]))
        self .assertEqual (res_5 [0 ],(5 ,5 ))

        res_inv5 =sort_particles (pts ,order_code ="-5",get_xy =lambda p :(p [0 ],p [1 ]))
        self .assertNotEqual (res_inv5 [0 ],(5 ,5 ))

    def test_particle_text_node_dual_shape_and_slots (self ):
        path_shape ="m 0 0 l 100 0 l 100 100 l 0 100"
        particle_shape ="m 0 0 l 5 0 l 5 5 l 0 5"

        abs_x ,abs_y ,p_shape ,total_pts =particle_text_node (
        self .context ,
        shape =path_shape ,
        particle_shape =particle_shape ,
        density =20.0 ,
        mode ="Contorno v2",
        order ="79"
        )

        self .assertGreater (total_pts ,0 )
        self .assertEqual (p_shape ,particle_shape )
        self .assertIsInstance (abs_x ,float )
        self .assertIsInstance (abs_y ,float )

    def test_merge_ass_tags_deduplication (self ):
        base_tags =r"\pos(100,200)\fscx100\fscy100"
        new_tags =r"\fscx150\1c&H00FFFF&"
        merged =merge_ass_tags (base_tags ,new_tags )
        self .assertIn (r"\fscx150",merged )
        self .assertIn (r"\fscy100",merged )
        self .assertIn (r"\1c&H00FFFF&",merged )

    def test_particle_variables_isolation (self ):
        ctx ={'active_unit':PyxisUnit (),'active_line':PyxisLine (),'tp_i':2 ,'p_i':5 }
        path_shape ="m 0 0 l 100 0 l 100 100 l 0 100"
        particle_text_node (ctx ,shape =path_shape ,density =20.0 ,mode ="Contorno v2")
        self .assertEqual (ctx .get ('tp_i'),2 )
        self .assertGreater (ctx .get ('tp_n',0 ),0 )
        self .assertEqual (ctx .get ('text_p_i'),2 )

    def test_particle_image_isolation (self ):
        ctx ={'active_unit':PyxisUnit (),'active_line':PyxisLine (),'ip_i':1 }
        abs_x ,abs_y ,col_ass ,alpha_ass ,p_shape ,total_px =particle_image_node (ctx ,image_path ="",particle_shape ="")
        self .assertEqual (ctx .get ('ip_i'),1 )
        self .assertEqual (ctx .get ('ip_n'),1 )

    def test_particle_text_to_shape_generation (self ):
        """Verifica que el nodo de partículas invoque a FontVectorEngine para convertir texto a shape."""
        from models import StyleRef 
        line =PyxisLine ()
        line .text ="TEST"
        line .text_stripped ="TEST"
        line .styleref =StyleRef ({"Fontname":"Arial","Fontsize":40 })
        unit =PyxisUnit ()
        unit .text ="TEST"
        unit .text_stripped ="TEST"
        unit .line =line 
        ctx ={'active_unit':unit ,'active_line':line }


        abs_x ,abs_y ,p_shp ,total_pts =particle_text_node (ctx ,shape ="",particle_shape ="")
        self .assertGreater (total_pts ,0 )
        self .assertEqual (p_shp ,"m 0 0 l 2 0 l 2 2 l 0 2")


        abs_x2 ,abs_y2 ,p_shp2 ,total_pts2 =particle_text_node (ctx ,shape ="H",particle_shape ="")
        self .assertGreater (total_pts2 ,0 )
        self .assertEqual (p_shp2 ,"m 0 0 l 2 0 l 2 2 l 0 2")


        abs_x3 ,abs_y3 ,p_shp3 ,total_pts3 =particle_text_node (ctx ,shape ="",particle_shape ="circle")
        self .assertGreater (total_pts3 ,0 )
        self .assertTrue (p_shp3 .startswith ("m "))
        self .assertNotEqual (p_shp3 ,"m 0 0 l 2 0 l 2 2 l 0 2")


class TestMaxLoopModuleMorph (unittest .TestCase ):
    """Pruebas de morph y deformaciones morfologicas en bucles MaxLoop."""

    def test_maxloop_module_distortion (self ):
        graph ={
        "last_node_id":9 ,
        "last_link_id":10 ,
        "nodes":[
        {
        "id":1 ,
        "type":"Loops/Main Loop",
        "properties":{"iterador":"line","noblank":"No Blank (Ignorar Espacios)"},
        "outputs":[{"name":"Loop","type":"bucle","links":[1 ],"slot_index":0 }]
        },
        {
        "id":2 ,
        "type":"Loops/MaxLoop",
        "properties":{"modo":"FBF","start_time":"1000","end_time":"1200","step_ms":"50","var_name":"j"},
        "inputs":[{"name":"Loop In","type":"bucle","link":1 }],
        "outputs":[
        {"name":"Loop Out","type":"bucle","links":[2 ],"slot_index":0 },
        {"name":"Iterator (j)","type":"data","links":[3 ],"slot_index":1 },
        {"name":"Total (N)","type":"data","links":[4 ],"slot_index":2 }
        ]
        },
        {
        "id":3 ,
        "type":"Loops/Module",
        "properties":{"iter":"i","total":"N","sub_m":"0"},
        "inputs":[
        {"name":"Iterator (i)","type":"data","link":3 },
        {"name":"Total (N)","type":"data","link":4 },
        {"name":"Sub-step (m)","type":"data","link":None }
        ],
        "outputs":[{"name":"Data","type":"data","links":[5 ],"slot_index":0 }]
        },
        {
        "id":4 ,
        "type":"Functions/Text to Shape",
        "properties":{"text":"A","font_name":"Arial","font_size":"40"},
        "outputs":[{"name":"Shape Out","type":"shape","links":[6 ],"slot_index":0 }]
        },
        {
        "id":5 ,
        "type":"Functions/Text to Shape",
        "properties":{"text":"B","font_name":"Arial","font_size":"40"},
        "outputs":[{"name":"Shape Out","type":"shape","links":[7 ],"slot_index":0 }]
        },
        {
        "id":6 ,
        "type":"Shape/Transform",
        "properties":{"mode":"Distort","t":"0.5"},
        "inputs":[
        {"name":"Shape / Texto","type":"data","link":6 },
        {"name":"Target Shape","type":"data","link":7 },
        {"name":"Factor (t)","type":"data","link":5 },
        {"name":"Anchor","type":"data","link":None }
        ],
        "outputs":[{"name":"Shape","type":"data","links":[8 ],"slot_index":0 }]
        },
        {
        "id":7 ,
        "type":"System/Output",
        "properties":{"apply_to":"Sel. Lines"},
        "inputs":[
        {"name":"Loop / Domain","type":"bucle","link":2 },
        {"name":"Layer","type":"data","link":None },
        {"name":"Start Time","type":"data","link":None },
        {"name":"End Time","type":"data","link":None },
        {"name":"Tags","type":"data","link":None },
        {"name":"Return","type":"data","link":8 }
        ],
        "outputs":[{"name":"Preview","type":"data","links":[]}]
        }
        ],
        "links":[
        [1 ,1 ,0 ,2 ,0 ,"bucle"],
        [2 ,2 ,0 ,7 ,0 ,"bucle"],
        [3 ,2 ,1 ,3 ,0 ,"data"],
        [4 ,2 ,2 ,3 ,1 ,"data"],
        [5 ,3 ,0 ,6 ,2 ,"data"],
        [6 ,4 ,0 ,6 ,0 ,"shape"],
        [7 ,5 ,0 ,6 ,1 ,"shape"],
        [8 ,6 ,0 ,7 ,5 ,"data"]
        ]
        }
        styles ={
        'Default':{
        'Fontname':'Arial',
        'Fontsize':40.0 ,
        'PrimaryColour':'&H00FFFFFF&',
        'SecondaryColour':'&H000000FF&',
        'OutlineColour':'&H00000000&',
        'BackColour':'&H00000000&',
        'ScaleX':100.0 ,
        'ScaleY':100.0 ,
        'Spacing':0.0 ,
        'Outline':2.0 ,
        'Shadow':0.0 ,
        'Alignment':5 
        }
        }
        dialogue_items =[
        {
        'raw':'Dialogue: 0,0:00:01.00,0:00:01.20,Default,,0,0,0,,{\\k20}A',
        'is_selected':True 
        }
        ]
        ge =GraphEngine (graph )
        ge .process_single (dialogue_items ,styles ,allow_fallback_select_all =True )
        self.assertGreater (len (ge .all_generated_lines ),1 )
        first_line =ge .all_generated_lines [0 ]['text']
        last_line =ge .all_generated_lines [-1 ]['text']
        self .assertNotEqual (first_line ,last_line )

    def test_particles_canonical_lowercase(self):
        node = {
            "id": 1,
            "type": "Functions/Particles",
            "properties": {
                "shape": "m 0 0 l 100 0 l 100 50 l 0 50",
                "particle_shape": "m 0 0 l 5 0 l 5 5 l 0 5",
                "density": "20.0",
                "redraw_dist": "0",
                "seed": "1",
                "scale": "1.0",
                "mode": "outline_v2",
                "order": "79"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        shp_out = engine.evaluate_data_node(1, context={"fx_i": 1}, output_slot_index=0)
        pos_tag = engine.evaluate_data_node(1, context={"fx_i": 1}, output_slot_index=1)
        total_pts = engine.evaluate_data_node(1, context={"fx_i": 1}, output_slot_index=4)

        self.assertIn(r"\pos(", pos_tag)
        self.assertTrue(int(total_pts) > 0)
        self.assertIn("m 0 0 l 5 0", shp_out)

    def test_interpolator_canonical(self):
        node = {
            "id": 1,
            "type": "Functions/Interpolator",
            "properties": {
                "iterator": "1",
                "total": "5",
                "accel": "1.0",
                "v1": "10",
                "v2": "50"
            }
        }
        engine = GraphEngine({"nodes": [node], "links": []})
        res_single = engine.evaluate_data_node(1, context={"i": 1, "N": 5}, output_slot_index=0)
        self.assertEqual(res_single, "10")

        res_batch = engine.evaluate_data_node(1, context={"i": 1, "N": 5}, output_slot_index=1)
        self.assertIn("10", res_batch)
        self.assertIn("50", res_batch)


if __name__ =="__main__":
    unittest .main ()

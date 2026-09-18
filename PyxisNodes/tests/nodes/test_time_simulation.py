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

"""Simulaciones avanzadas y certificacion de funcionamiento para Time to Frame y Frame to Time."""

import math 
import unittest 
from models import PyxisLine ,PyxisUnit 
from node_engine import GraphEngine 
from nodes .time_nodes import (
time_to_frame_node ,
frame_to_time_node ,
time_offset ,
time_parse_ass ,
time_format_ass ,
)
from utils import format_time ,parse_time 



def _create_test_line (start =1000 ,end =3000 ,text =r"{\k50}A{\k50}B"):
    line =PyxisLine ()
    line .layer =0 
    line .start_time =start 
    line .end_time =end 
    line .duration =end -start 
    line .style_name ="Default"
    line .text =text 
    line .text_stripped ="AB"
    line .is_selected =True 

    u1 =PyxisUnit ()
    u1 .i ,u1 .n =1 ,2 
    u1 .start_time ,u1 .end_time ,u1 .dur =start ,start +500 ,500 
    u1 .text ,u1 .text_stripped ="A","A"

    u2 =PyxisUnit ()
    u2 .i ,u2 .n =2 ,2 
    u2 .start_time ,u2 .end_time ,u2 .dur =start +500 ,end ,1500 
    u2 .text ,u2 .text_stripped ="B","B"

    line .syls =[u1 ,u2 ]
    return line 


class TestTimeSimulationScenarios (unittest .TestCase ):
    """Bateria de simulaciones exhaustivas para certificar ambos nodos."""

    def setUp (self ):
        self .line =_create_test_line ()
        self .unit =self .line .syls [0 ]




    def test_simulation_fps_rates_and_roundtrip (self ):
        """Simula video con cadencias cinematograficas, broadcast y gaming."""
        test_rates ={
        "23.976_fps":1000.0 /23.976 ,
        "24.0_fps":1000.0 /24.0 ,
        "25.0_fps":40.0 ,
        "29.97_fps":1000.0 /29.97 ,
        "50.0_fps":20.0 ,
        "60.0_fps":1000.0 /60.0 ,
        "120.0_fps":1000.0 /120.0 ,
        }

        test_times =[0 ,42 ,100 ,250 ,1000 ,3500 ,60000 ]

        for rate_name ,fd in test_rates .items ():
            ctx ={'frame_dur':fd ,'active_unit':self .unit }
            for t in test_times :

                frames_ceil =time_to_frame_node (ctx ,time_val =t ,mode ="Ceil")
                expected_ceil =int (math .ceil (t /fd ))
                self .assertEqual (frames_ceil ,expected_ceil ,f"Fallo Ceil en {rate_name } para {t }ms")


                frames_floor =time_to_frame_node (ctx ,time_val =t ,mode ="Floor")
                expected_floor =int (math .floor (t /fd ))
                self .assertEqual (frames_floor ,expected_floor ,f"Fallo Floor en {rate_name } para {t }ms")


                ms3_back =frame_to_time_node (ctx ,frames =frames_floor ,format ="MS")
                expected_ms =round (frames_floor *fd ,2 )
                self .assertAlmostEqual (ms3_back ,expected_ms ,places =2 )


                sec_back =frame_to_time_node (ctx ,frames =frames_floor ,format ="SEC")
                expected_sec =round ((frames_floor *fd )/1000.0 ,3 )
                self .assertAlmostEqual (sec_back ,expected_sec ,places =3 )




    def test_simulation_nested_loops_and_iterators (self ):
        """Simula bucles anidados i (silaba), j (maxloop exterior) y k (maxloop interior)."""
        fd =40.0 
        for s_idx ,syl in enumerate (self .line .syls ,start =1 ):
            for j_val in range (1 ,4 ):
                for k_val in range (1 ,5 ):
                    ctx ={
                    'active_unit':syl ,
                    'i':s_idx ,
                    'j':j_val ,
                    'k':k_val ,
                    'step_i':k_val *10 ,
                    'piece_idx':j_val *100 +k_val ,
                    'frame_dur':fd 
                    }


                    time_k =frame_to_time_node (ctx ,source ="Iterador",iter_name ="k",format ="MS")
                    self .assertEqual (time_k ,k_val *fd )


                    time_j =frame_to_time_node (ctx ,source ="Iterador",iter_name ="j",format ="MS")
                    self .assertEqual (time_j ,j_val *fd )


                    time_step =frame_to_time_node (ctx ,source ="Iterador",iter_name ="step_i",format ="MS")
                    self .assertEqual (time_step ,(k_val *10 )*fd )


                    time_expr =frame_to_time_node (ctx ,source ="Iterador",iter_name ="k * 2 + j",format ="MS")
                    expected_expr =((k_val *2 )+j_val )*fd 
                    self .assertEqual (time_expr ,expected_expr )


                    time_fallback =frame_to_time_node (ctx ,source ="Iterador",iter_name ="",format ="MS")
                    self .assertEqual (time_fallback ,j_val *fd )




    def test_simulation_graph_engine_pipeline (self ):
        """Ejecuta un grafo completo procesando líneas de subtítulos reales."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Loops/Main Loop',
        'properties':{'iterador':'syl'},
        'inputs':[]
        },
        {
        'id':2 ,
        'type':'Time/Time to Frame',
        'properties':{'mode':'Posición (Floor)','source':'Start Time','time':'0','frame_dur':'40.0'},
        'inputs':[]
        },
        {
        'id':3 ,
        'type':'Time/Frame to Time',
        'properties':{'format':'Milisegundos (ms)','source':'Iterador','iter_name':'k','frame_dur':'40.0'},
        'inputs':[]
        },
        {
        'id':4 ,
        'type':'Loops/MaxLoop',
        'properties':{'veces':'3','var_name':'k'},
        'inputs':[{'link':1 }]
        },
        {
        'id':5 ,
        'type':'System/Output',
        'properties':{'apply_to':'All Lines','origin_align':5 },
        'inputs':[{'link':2 },None ,None ,None ,None ,None ]
        }
        ],
        'links':[
        [1 ,1 ,0 ,4 ,0 ,'bucle'],
        [2 ,4 ,0 ,5 ,0 ,'bucle'],
        ]
        }

        engine =GraphEngine (graph ,1280 ,720 ,40.0 )


        ctx_syl1 ={'active_unit':self .line .syls [0 ],'active_line':self .line ,'frame_dur':40.0 }
        start_frame =engine .evaluate_data_node (2 ,ctx_syl1 ,output_slot_index =0 )
        self .assertEqual (int (start_frame ),25 )


        ctx_k2 =dict (ctx_syl1 ,k =2 )
        ms_out =engine .evaluate_data_node (3 ,ctx_k2 ,output_slot_index =0 )
        self .assertEqual (float (ms_out ),80.0 )


        ass_time_out =engine .evaluate_data_node (3 ,ctx_k2 ,output_slot_index =1 )
        self .assertEqual (ass_time_out ,"0:00:00.08")


        raw_dialogue =r"Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\k50}Ma{\k50}ry"
        styles ={'Default':{'fontname':'Arial','fontsize':40 }}
        engine .process_single ([{'raw':raw_dialogue }],styles )

        self .assertEqual (len (engine .all_generated_lines ),6 )
        for gen in engine .all_generated_lines :
            self .assertNotIn ("[Err",gen ['text'])




    def test_simulation_data_flow_link_between_time_nodes (self ):
        """Conecta la salida de Time to Frame a la entrada Frames de Frame to Time."""
        graph ={
        'nodes':[
        {
        'id':10 ,
        'type':'Time/Time to Frame',
        'properties':{'mode':'Duración (Ceil)','source':'Custom','time':'250','frame_dur':'40.0'},
        'inputs':[]
        },
        {
        'id':20 ,
        'type':'Time/Frame to Time',
        'properties':{'format':'ASS Timestamp (HMS)','source':'Custom','frames':'1','frame_dur':'40.0'},
        'inputs':[{'link':1 }]
        }
        ],
        'links':[
        [1 ,10 ,0 ,20 ,0 ,'data']
        ]
        }

        engine =GraphEngine (graph ,1280 ,720 ,40.0 )
        ctx ={'frame_dur':40.0 }


        f_out =engine .evaluate_data_node (10 ,ctx ,output_slot_index =0 )
        self .assertEqual (int (f_out ),7 )


        hms_out =engine .evaluate_data_node (20 ,ctx ,output_slot_index =0 )
        self .assertEqual (hms_out ,"0:00:00.28")




    def test_simulation_edge_cases_and_error_handling (self ):
        """Prueba tiempos negativos, frames nulos, entradas corruptas y tipos de datos anómalos."""
        ctx ={'frame_dur':40.0 }


        self .assertEqual (time_to_frame_node (ctx ,time_val =0 ,mode ="Ceil"),0 )
        self .assertEqual (time_to_frame_node (ctx ,time_val =-120 ,mode ="Floor"),-3 )
        self .assertEqual (frame_to_time_node (ctx ,frames =0 ,format ="MS"),0.0 )
        self .assertEqual (frame_to_time_node (ctx ,frames =-5 ,format ="MS"),-200.0 )


        ctx_bad_fd ={'frame_dur':0 }
        res_safe =time_to_frame_node (ctx_bad_fd ,time_val =100 )
        self .assertIsInstance (res_safe ,int )

        ctx_neg_fd ={'frame_dur':-10 }
        res_safe_neg =frame_to_time_node (ctx_neg_fd ,frames =10 ,format ="MS")
        self .assertIsInstance (res_safe_neg ,float )


        res_invalid_expr =frame_to_time_node (ctx ,source ="Iterador",iter_name ="variable_inexistente_xyz",format ="MS")
        self .assertEqual (res_invalid_expr ,40.0 )


        self .assertEqual (time_to_frame_node (ctx ,time_val ="0:00:01.00",mode ="Floor"),25 )
        self .assertEqual (time_to_frame_node (ctx ,time_val ="1:00:00.00",mode ="Floor"),90000 )


        ass_str =frame_to_time_node (ctx ,frames =90000 ,format ="HMS")
        self .assertEqual (ass_str ,"1:00:00.00")




    def test_simulation_context_sources (self ):
        """Verifica que 'Start Time', 'End Time' y 'Duration' lean correctamente unit y line."""
        ctx_unit ={
        'active_unit':self .unit ,
        'active_line':self .line ,
        'frame_dur':40.0 
        }


        self .assertEqual (time_to_frame_node (ctx_unit ,source ="Start Time",mode ="Floor"),25 )
        self .assertEqual (time_to_frame_node (ctx_unit ,source ="End Time",mode ="Floor"),37 )
        self .assertEqual (time_to_frame_node (ctx_unit ,source ="Duration",mode ="Ceil"),13 )


        ctx_line_only ={
        'active_unit':None ,
        'line':self .line ,
        'frame_dur':40.0 
        }
        self .assertEqual (time_to_frame_node (ctx_line_only ,source ="Start Time",mode ="Floor"),25 )
        self .assertEqual (time_to_frame_node (ctx_line_only ,source ="End Time",mode ="Floor"),75 )
        self .assertEqual (time_to_frame_node (ctx_line_only ,source ="Duration",mode ="Ceil"),50 )




    def test_simulation_offset_node_scenarios (self ):
        """Certifica el comportamiento del nodo Offset con desplazamientos positivos, negativos y expresiones."""
        ctx ={
        'active_unit':self .unit ,
        'active_line':self .line ,
        'frame_dur':40.0 
        }


        self .assertEqual (time_offset (ctx ,base =1000 ,offset =250 ),1250 )
        self .assertEqual (time_offset (ctx ,base =0 ,offset =100 ),100 )


        self .assertEqual (time_offset (ctx ,base =1000 ,offset =-350 ),650 )
        self .assertEqual (time_offset (ctx ,base =200 ,offset =-500 ),-300 )


        self .assertEqual (time_offset (ctx ,base ="active_unit.start_time",offset =150 ),1150 )
        self .assertEqual (time_offset (ctx ,base =1000 ,offset ="50 * 3"),1150 )
        self .assertEqual (time_offset (ctx ,base ="active_line.end_time",offset ="-200"),2800 )


        self .assertEqual (time_offset (ctx ,offset ="200"),200 )
        self .assertEqual (time_offset (None ,base =500 ,offset =100 ),600 )




    def test_simulation_parse_ass_time_scenarios (self ):
        """Certifica la conversion de timestamps ASS a ms y roundtrip con Format ASS Time."""
        ctx ={
        'active_unit':self .unit ,
        'active_line':self .line ,
        'frame_dur':40.0 
        }


        self .assertEqual (time_parse_ass (ctx ,ass_time ="0:00:00.00"),0 )
        self .assertEqual (time_parse_ass (ctx ,ass_time ="0:00:01.50"),1500 )
        self .assertEqual (time_parse_ass (ctx ,ass_time ="0:01:23.45"),83450 )
        self .assertEqual (time_parse_ass (ctx ,ass_time ="1:23:45.67"),5025670 )


        self .line .start_str ="0:00:01.00"
        self .assertEqual (time_parse_ass (ctx ,ass_time =""),1000 )


        orig_timestamp ="0:02:15.80"
        ms_parsed =time_parse_ass (ctx ,ass_time =orig_timestamp )
        self .assertEqual (ms_parsed ,135800 )

        ms_offsetted =time_offset (ctx ,base =ms_parsed ,offset =250 )
        self .assertEqual (ms_offsetted ,136050 )

        formatted_back =time_format_ass (ctx ,ms =ms_offsetted )
        self .assertEqual (formatted_back ,"0:02:16.05")




    def test_simulation_graph_engine_offset_and_parse_ass_pipeline (self ):
        """Ejecuta un grafo enlazado donde Parse ASS Time alimenta a Offset y este a Time to Frame y Format ASS Time."""
        graph ={
        'nodes':[
        {
        'id':100 ,
        'type':'Time/Parse ASS Time',
        'properties':{'ass_time':'0:00:05.00'},
        'outputs':[{'name':'Time (ms)','type':'data','links':[101 ]}]
        },
        {
        'id':101 ,
        'type':'Time/Offset',
        'properties':{'offset':'250'},
        'inputs':[{'name':'Base (ms)','type':'data','link':101 }],
        'outputs':[{'name':'Time (ms)','type':'data','links':[102 ,103 ]}]
        },
        {
        'id':102 ,
        'type':'Time/Time to Frame',
        'properties':{'mode':'Ceil','source':'Entrada (ms)'},
        'inputs':[{'name':'Time (ms)','type':'data','link':102 }],
        'outputs':[{'name':'Frames (f)','type':'data','links':[]}]
        },
        {
        'id':103 ,
        'type':'Time/Format ASS Time',
        'properties':{},
        'inputs':[{'name':'Time (ms)','type':'data','link':103 }],
        'outputs':[{'name':'ASS Time','type':'data','links':[]}]
        }
        ],
        'links':[
        [101 ,100 ,0 ,101 ,0 ,'data'],
        [102 ,101 ,0 ,102 ,0 ,'data'],
        [103 ,101 ,0 ,103 ,0 ,'data']
        ]
        }

        engine =GraphEngine (graph )
        ctx ={
        'active_unit':self .unit ,
        'active_line':self .line ,
        'frame_dur':40.0 
        }


        val_parse =engine .evaluate_data_node (100 ,ctx ,output_slot_index =0 )
        self .assertEqual (val_parse ,"5000")


        val_offset =engine .evaluate_data_node (101 ,ctx ,output_slot_index =0 )
        self .assertEqual (val_offset ,"5250")


        val_frames =engine .evaluate_data_node (102 ,ctx ,output_slot_index =0 )
        self .assertEqual (val_frames ,"132")


        val_formatted =engine .evaluate_data_node (103 ,ctx ,output_slot_index =0 )
        self .assertEqual (val_formatted ,"0:00:05.25")


if __name__ =='__main__':
    unittest .main ()

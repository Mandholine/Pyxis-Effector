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

"""Pruebas unitarias para el motor central de grafos (GraphEngine) y procesamiento de lineas."""

import unittest 
from ass_parser import KaraokeProcessor 
from models import PyxisLine ,PyxisUnit 
from node_engine import GraphEngine 
from template_store import PYXIS_ENGINE_VERSION 


class TestGraphEngineCore (unittest .TestCase ):
    """Pruebas de inicializacion, memoria y evaluacion en GraphEngine."""

    def setUp (self ):
        self .sample_line =PyxisLine ()
        self .sample_line .layer =0 
        self .sample_line .start_time =0 
        self .sample_line .end_time =2000 
        self .sample_line .style_name ="Default"
        self .sample_line .text ="Hello Pyxis"
        self .sample_line .is_selected =True 

        self .sample_syl =PyxisUnit ()
        self .sample_syl .text ="Hello"
        self .sample_syl .text_stripped ="Hello"
        self .sample_syl .duration =1000 
        self .sample_syl .dur =1000 
        self .sample_syl .start_time =0 
        self .sample_syl .end_time =1000 
        self .sample_syl .i =1 
        self .sample_syl .n =2 
        self .sample_syl .center =640.0 
        self .sample_syl .middle =360.0 
        self .sample_line .syls =[self .sample_syl ]

    def test_version_current (self ):
        self .assertEqual (PYXIS_ENGINE_VERSION ,"1.1.0")

    def test_remember_and_recall_memory (self ):
        engine =GraphEngine ({"nodes":[],"links":[]})
        val =engine .remember ("mi_pos_x",450.5 )
        self .assertEqual (val ,450.5 )
        recalled =engine .recall ("mi_pos_x",default =0.0 )
        self .assertEqual (recalled ,450.5 )
        default_val =engine .recall ("clave_inexistente",default =123 )
        self .assertEqual (default_val ,123 )

    def test_simple_graph_pipeline (self ):
        graph ={
        "nodes":[
        {
        "id":1 ,
        "type":"Loops/Main Loop",
        "properties":{"base_unit":"line","noblank":"No Blank"}
        },
        {
        "id":2 ,
        "type":"String",
        "properties":{"valor":"Processed Text"}
        },
        {
        "id":3 ,
        "type":"System/Output",
        "properties":{"apply_to":"Selected Lines"},
        "inputs":[
        {"name":"Loop","type":"data","link":101 },
        {"name":"Capa","type":0 ,"link":None },
        {"name":"Start","type":0 ,"link":None },
        {"name":"End","type":0 ,"link":None },
        {"name":"Tags","type":0 ,"link":None },
        {"name":"Retorno","type":"string","link":102 }
        ]
        }
        ],
        "links":[
        [101 ,1 ,0 ,3 ,0 ,"data"],
        [102 ,2 ,0 ,3 ,5 ,"string"]
        ]
        }
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
        engine =GraphEngine (graph )
        engine .process_single (dialogues ,styles ,allow_fallback_select_all =True )
        self .assertGreater (len (engine .all_generated_lines ),0 )


class TestPyxisAutonomousProcessing (unittest .TestCase ):
    """Pruebas de procesamiento de lineas ASS mediante KaraokeProcessor y Karaskel."""

    def test_line_karaoke_syllables_extraction (self ):
        kp =KaraokeProcessor (1280 ,720 ,41.708 )
        raw =r"Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,{\k50}Hel{\k50}lo {\k100}World"
        style ={"Fontname":"Arial","Fontsize":"40","MarginL":"10","MarginR":"10","MarginV":"30","Alignment":"2"}
        line =kp .process_line (raw ,style )
        self .assertIsNotNone (line )
        self .assertEqual (line .start_time ,1000 )
        self .assertEqual (line .end_time ,4000 )
        self .assertGreater (len (line .syls ),0 )


    def test_output_merges_only_first_comment_block_and_preserves_subsequent (self ):
        """Salida debe fusionar solo el primer bloque {...} de Return con los tags y preservar los posteriores."""
        graph ={
        "nodes":[
        {"id":1 ,"type":"Loops/Main Loop","properties":{"base_unit":"line","noblank":"No Blank"},"inputs":[]},
        {"id":2 ,"type":"String","properties":{"valor":"{\\1c&H51F6ED&}m 0 0 l 10 10{\\1c&H8FF5B5&}m 20 20 l 30 30"},"inputs":[]},
        {"id":3 ,"type":"String","properties":{"valor":"\\blur2"},"inputs":[]},
        {
        "id":4 ,
        "type":"System/Output",
        "properties":{"apply_to":"Selected Lines","origin_align":7 },
        "inputs":[
        {"name":"Loop","type":"data","link":101 },
        {"name":"Capa","type":0 ,"link":None },
        {"name":"Start","type":0 ,"link":None },
        {"name":"End","type":0 ,"link":None },
        {"name":"Tags","type":0 ,"link":103 },
        {"name":"Retorno","type":"string","link":102 }
        ]
        }
        ],
        "links":[
        [101 ,1 ,0 ,4 ,0 ,"data"],
        [102 ,2 ,0 ,4 ,5 ,"string"],
        [103 ,3 ,0 ,4 ,4 ,"string"]
        ]
        }
        styles ={'Default':{'Fontname':'Arial','Fontsize':40.0 ,'Alignment':5 }}
        dialogues =[{'raw':'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Hello','is_selected':True }]
        engine =GraphEngine (graph )
        engine .process_single (dialogues ,styles ,allow_fallback_select_all =True )
        self .assertEqual (len (engine .all_generated_lines ),1 )
        line_text =engine .all_generated_lines [0 ]['text']


        self .assertFalse (line_text .startswith ("}{")or "}{"in line_text [:50 ])

        header =line_text .split ("}")[0 ]+"}"
        self .assertIn (r"\an5",header )
        self .assertIn (r"\1c&H51F6ED&",header )
        self .assertIn (r"\blur2",header )
        self .assertIn (r"\p1",header )

        self .assertIn (r"{\1c&H8FF5B5&}",line_text )
        self .assertTrue (line_text .endswith ("m 20 20 l 30 30"))

    def test_output_tags_port_overrides_first_comment_block_on_collision (self ):
        """Las etiquetas del puerto Tags tienen prioridad absoluta y reemplazan a las de Return en caso de colisión."""
        graph ={
        "nodes":[
        {"id":1 ,"type":"Loops/Main Loop","properties":{"base_unit":"line","noblank":"No Blank"},"inputs":[]},
        {"id":2 ,"type":"String","properties":{"valor":"{\\1c&H0000FF&\\fscx100}m 0 0 l 10 10"},"inputs":[]},
        {"id":3 ,"type":"String","properties":{"valor":"\\1c&HFFFFFF&"},"inputs":[]},
        {
        "id":4 ,
        "type":"System/Output",
        "properties":{"apply_to":"Selected Lines","origin_align":5 },
        "inputs":[
        {"name":"Loop","type":"data","link":101 },
        {"name":"Capa","type":0 ,"link":None },
        {"name":"Start","type":0 ,"link":None },
        {"name":"End","type":0 ,"link":None },
        {"name":"Tags","type":0 ,"link":103 },
        {"name":"Retorno","type":"string","link":102 }
        ]
        }
        ],
        "links":[
        [101 ,1 ,0 ,4 ,0 ,"data"],
        [102 ,2 ,0 ,4 ,5 ,"string"],
        [103 ,3 ,0 ,4 ,4 ,"string"]
        ]
        }
        styles ={'Default':{'Fontname':'Arial','Fontsize':40.0 ,'Alignment':5 }}
        dialogues =[{'raw':'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Hello','is_selected':True }]
        engine =GraphEngine (graph )
        engine .process_single (dialogues ,styles ,allow_fallback_select_all =True )
        self .assertEqual (len (engine .all_generated_lines ),1 )
        line_text =engine .all_generated_lines [0 ]['text']

        header =line_text .split ("}")[0 ]+"}"
        self .assertIn (r"\1c&HFFFFFF&",header )
        self .assertNotIn (r"\1c&H0000FF&",header )
        self .assertIn (r"\fscx100",header )
        self .assertIn (r"\p1",header )

    def test_fx_context_output_times (self ):
        """Verifica que fx.dur, fx.start_time y fx.end_time provengan estrictamente de Salida."""
        from node_engine import FxContext 
        ctx ={
        'dur':64.0 ,'start_time':6820.0 ,'end_time':6884.0 ,
        'fx_dur':2090.0 ,'fx_start_time':6820.0 ,'fx_end_time':8910.0 
        }
        fx =FxContext (ctx )
        self .assertEqual (fx .dur ,2090.0 )
        self .assertEqual (fx .duration ,2090.0 )
        self .assertEqual (fx .start_time ,6820.0 )
        self .assertEqual (fx .end_time ,8910.0 )
        self .assertEqual (fx .st ,6820.0 )
        self .assertEqual (fx .et ,8910.0 )

    def test_output_origin_align_defaults_to_an5_and_respects_explicit_an (self ):
        """Verifica que cambiar origin_align no altere el \\an5 por defecto, pero respete \\an explícito."""
        engine = GraphEngine()
        class DummyUnit:
            left = 100.0
            center = 200.0
            right = 300.0
            top = 50.0
            middle = 75.0
            bottom = 100.0
            start_time = 0
            end_time = 1000
            text_stripped = "test"

        unit = DummyUnit()
        ctx = {"val_left": 100.0, "val_center": 200.0, "val_right": 300.0,
               "val_top": 50.0, "val_middle": 75.0, "val_bottom": 100.0,
               "origin_align": 7}

        # 1. Sin \an explícito -> debe generar \an5 con pos calculado según origin_align=7 (left=100, top=50)
        _, _, _, tags_out_default, _ = engine._apply_defaults(unit, 0, 0, 1000, r"\blur1", "test", context=ctx)
        self.assertTrue(tags_out_default.startswith(r"\an5"))
        self.assertIn(r"\pos(100,50)", tags_out_default)

        # 2. Con \an explícito (ej. \an1) -> debe respetar \an1
        _, _, _, tags_out_explicit, _ = engine._apply_defaults(unit, 0, 0, 1000, r"\an1\blur1", "test", context=ctx)
        self.assertTrue(tags_out_explicit.startswith(r"\an1"))
        self.assertNotIn(r"\an5", tags_out_explicit)
        self.assertIn(r"\pos(100,50)", tags_out_explicit)


if __name__ =="__main__":
    unittest .main ()



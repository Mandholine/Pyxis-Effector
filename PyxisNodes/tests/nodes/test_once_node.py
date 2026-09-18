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

"""Pruebas unitarias para el nodo adaptador Once (Sample & Hold / Freeze Scope)."""

import unittest 
import sys 
import os 

sys .path .insert (0 ,os .path .abspath (os .path .join (os .path .dirname (__file__ ),'..','..')))

from node_engine import GraphEngine 


class TestOnceNode (unittest .TestCase ):
    """Pruebas unitarias para verificar los modos de alcance del nodo Once."""

    def setUp (self ):
        self .styles ={
        'Default':{
        'Fontname':'Arial','Fontsize':40.0 ,
        'PrimaryColour':'&H00FFFFFF&','SecondaryColour':'&H000000FF&',
        'OutlineColour':'&H00000000&','BackColour':'&H00000000&',
        'ScaleX':100.0 ,'ScaleY':100.0 ,'Spacing':0.0 ,'Outline':2.0 ,
        'Shadow':0.0 ,'Alignment':5 
        }
        }

    @staticmethod 
    def _extract_tag_payload (text ):
        import re 
        tag_block =text .split ('}')[0 ].lstrip ('{')
        cleaned =re .sub (r'\\pos\([^)]+\)','',tag_block )
        cleaned =re .sub (r'^\\an\d','',cleaned )
        return cleaned .strip ()

    def test_once_line_mode_synchronization (self ):
        """Verifica que con Once en modo line, todas las chars de una linea compartan el mismo valor estocastico."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Loops/Main Loop',
        'properties':{'iterator':'char','blank_mode':'no_blank'},
        'outputs':[{'name':'Loop','type':'bucle','links':[101 ]}]
        },
        {
        'id':2 ,
        'type':'Basics/MultiRandom',
        'properties':{'min':'100','max':'999','seed':'0'},
        'outputs':[{'name':'Out','type':'data','links':[102 ]}]
        },
        {
        'id':3 ,
        'type':'Basics/Once',
        'properties':{'mode':'line','iterator':'j'},
        'inputs':[{'name':'','type':0 ,'link':102 }],
        'outputs':[{'name':'','type':0 ,'links':[103 ]}]
        },
        {
        'id':4 ,
        'type':'System/Output',
        'properties':{'apply_to':'All Lines'},
        'inputs':[
        {'name':'Loop','type':'bucle','link':101 },
        {'name':'Layer','type':0 ,'link':None },
        {'name':'Start Time','type':0 ,'link':None },
        {'name':'End Time','type':0 ,'link':None },
        {'name':'Tags','type':0 ,'link':103 },
        {'name':'Return','type':'string','link':None }
        ]
        }
        ],
        'links':[
        [101 ,1 ,0 ,4 ,0 ,'bucle'],
        [102 ,2 ,0 ,3 ,0 ,'data'],
        [103 ,3 ,0 ,4 ,4 ,'data']
        ]
        }

        dialogues =[{'raw':r'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\k50}Hel{\k50}lo','is_selected':True }]
        engine =GraphEngine (graph )
        engine .process_single (dialogues ,self .styles ,allow_fallback_select_all =True )

        self .assertGreaterEqual (len (engine .all_generated_lines ),5 )
        tag_val =self ._extract_tag_payload (engine .all_generated_lines [0 ]['text'])
        self .assertTrue (bool (tag_val ),"El payload de tag generado por MultiRandom no debe estar vacio")
        for line_obj in engine .all_generated_lines :
            cur_tag =self ._extract_tag_payload (line_obj ['text'])
            self .assertEqual (cur_tag ,tag_val ,'Todos los caracteres deben compartir exactamente el mismo tag en modo line')

    def test_once_syl_mode_differentiation (self ):
        """Verifica que en modo syl, los caracteres de la misma silaba compartan valor pero difieran entre silabas."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Loops/Main Loop',
        'properties':{'iterator':'char','blank_mode':'no_blank'},
        'outputs':[{'name':'Loop','type':'bucle','links':[101 ]}]
        },
        {
        'id':2 ,
        'type':'Basics/MultiRandom',
        'properties':{'min':'1000','max':'9999','seed':'0'},
        'outputs':[{'name':'Out','type':'data','links':[102 ]}]
        },
        {
        'id':3 ,
        'type':'Basics/Once',
        'properties':{'mode':'syl','iterator':'j'},
        'inputs':[{'name':'','type':0 ,'link':102 }],
        'outputs':[{'name':'','type':0 ,'links':[103 ]}]
        },
        {
        'id':4 ,
        'type':'System/Output',
        'properties':{'apply_to':'All Lines'},
        'inputs':[
        {'name':'Loop','type':'bucle','link':101 },
        {'name':'Layer','type':0 ,'link':None },
        {'name':'Start Time','type':0 ,'link':None },
        {'name':'End Time','type':0 ,'link':None },
        {'name':'Tags','type':0 ,'link':103 },
        {'name':'Return','type':'string','link':None }
        ]
        }
        ],
        'links':[
        [101 ,1 ,0 ,4 ,0 ,'bucle'],
        [102 ,2 ,0 ,3 ,0 ,'data'],
        [103 ,3 ,0 ,4 ,4 ,'data']
        ]
        }

        dialogues =[{'raw':r'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\k50}Ma{\k50}ry','is_selected':True }]
        engine =GraphEngine (graph )
        engine .process_single (dialogues ,self .styles ,allow_fallback_select_all =True )

        self .assertEqual (len (engine .all_generated_lines ),4 )
        m_tag =self ._extract_tag_payload (engine .all_generated_lines [0 ]['text'])
        a_tag =self ._extract_tag_payload (engine .all_generated_lines [1 ]['text'])
        r_tag =self ._extract_tag_payload (engine .all_generated_lines [2 ]['text'])
        y_tag =self ._extract_tag_payload (engine .all_generated_lines [3 ]['text'])

        self .assertTrue (bool (m_tag ),"m_tag no debe estar vacio")
        self .assertEqual (m_tag ,a_tag ,'M y a pertenecen a la silaba 1 y deben tener el mismo valor')
        self .assertEqual (r_tag ,y_tag ,'r e y pertenecen a la silaba 2 y deben tener el mismo valor')
        self .assertNotEqual (m_tag ,r_tag ,'Las silabas 1 y 2 deben tener valores distintos de random')

    def test_once_global_mode_persistence (self ):
        """Verifica que en modo global, multiples lineas distintas compartan el mismo valor."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Loops/Main Loop',
        'properties':{'iterator':'line'},
        'outputs':[{'name':'Loop','type':'bucle','links':[101 ]}]
        },
        {
        'id':2 ,
        'type':'Basics/MultiRandom',
        'properties':{'min':'1000','max':'9999','seed':'0'},
        'outputs':[{'name':'Out','type':'data','links':[102 ]}]
        },
        {
        'id':3 ,
        'type':'Basics/Once',
        'properties':{'mode':'global','iterator':'j'},
        'inputs':[{'name':'','type':0 ,'link':102 }],
        'outputs':[{'name':'','type':0 ,'links':[103 ]}]
        },
        {
        'id':4 ,
        'type':'System/Output',
        'properties':{'apply_to':'All Lines'},
        'inputs':[
        {'name':'Loop','type':'bucle','link':101 },
        {'name':'Layer','type':0 ,'link':None },
        {'name':'Start Time','type':0 ,'link':None },
        {'name':'End Time','type':0 ,'link':None },
        {'name':'Tags','type':0 ,'link':103 },
        {'name':'Return','type':'string','link':None }
        ]
        }
        ],
        'links':[
        [101 ,1 ,0 ,4 ,0 ,'bucle'],
        [102 ,2 ,0 ,3 ,0 ,'data'],
        [103 ,3 ,0 ,4 ,4 ,'data']
        ]
        }

        dialogues =[
        {'raw':r'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Line One','is_selected':True },
        {'raw':r'Dialogue: 0,0:00:04.00,0:00:06.00,Default,,0,0,0,,Line Two','is_selected':True }
        ]
        engine =GraphEngine (graph )
        engine .process_single (dialogues ,self .styles ,allow_fallback_select_all =True )

        self .assertEqual (len (engine .all_generated_lines ),2 )
        l1_tag =self ._extract_tag_payload (engine .all_generated_lines [0 ]['text'])
        l2_tag =self ._extract_tag_payload (engine .all_generated_lines [1 ]['text'])
        self .assertTrue (bool (l1_tag ),"l1_tag no debe estar vacio")
        self .assertEqual (l1_tag ,l2_tag ,'En modo global, lineas distintas deben compartir el mismo valor')

    def test_once_bucle_mode_iterator_scope (self ):
        """Verifica que en modo bucle, el valor cambie unicamente cuando la variable del iterador indicada cambia."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Loops/Main Loop',
        'properties':{'iterator':'line'},
        'outputs':[{'name':'Loop','type':'bucle','links':[101 ]}]
        },
        {
        'id':2 ,
        'type':'Loops/MaxLoop',
        'properties':{'mode':'normal','iterations':'2','var_name':'j'},
        'inputs':[{'name':'Loop In','type':'bucle','link':101 }],
        'outputs':[{'name':'Loop Out','type':'bucle','links':[102 ]}]
        },
        {
        'id':3 ,
        'type':'Loops/MaxLoop',
        'properties':{'mode':'normal','iterations':'2','var_name':'k'},
        'inputs':[{'name':'Loop In','type':'bucle','link':102 }],
        'outputs':[{'name':'Loop Out','type':'bucle','links':[103 ]}]
        },
        {
        'id':4 ,
        'type':'Basics/MultiRandom',
        'properties':{'min':'1000','max':'9999','seed':'0'},
        'outputs':[{'name':'Out','type':'data','links':[104 ]}]
        },
        {
        'id':5 ,
        'type':'Basics/Once',
        'properties':{'mode':'loop','iterator':'j'},
        'inputs':[{'name':'','type':0 ,'link':104 }],
        'outputs':[{'name':'','type':0 ,'links':[105 ]}]
        },
        {
        'id':6 ,
        'type':'System/Output',
        'properties':{'apply_to':'All Lines'},
        'inputs':[
        {'name':'Loop','type':'bucle','link':103 },
        {'name':'Layer','type':0 ,'link':None },
        {'name':'Start Time','type':0 ,'link':None },
        {'name':'End Time','type':0 ,'link':None },
        {'name':'Tags','type':0 ,'link':105 },
        {'name':'Return','type':'string','link':None }
        ]
        }
        ],
        'links':[
        [101 ,1 ,0 ,2 ,0 ,'bucle'],
        [102 ,2 ,0 ,3 ,0 ,'bucle'],
        [103 ,3 ,0 ,6 ,0 ,'bucle'],
        [104 ,4 ,0 ,5 ,0 ,'data'],
        [105 ,5 ,0 ,6 ,4 ,'data']
        ]
        }

        dialogues =[{'raw':r'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Hello','is_selected':True }]
        engine =GraphEngine (graph )
        engine .process_single (dialogues ,self .styles ,allow_fallback_select_all =True )

        self .assertEqual (len (engine .all_generated_lines ),4 )
        j1_k1 =self ._extract_tag_payload (engine .all_generated_lines [0 ]['text'])
        j1_k2 =self ._extract_tag_payload (engine .all_generated_lines [1 ]['text'])
        j2_k1 =self ._extract_tag_payload (engine .all_generated_lines [2 ]['text'])
        j2_k2 =self ._extract_tag_payload (engine .all_generated_lines [3 ]['text'])

        self .assertTrue (bool (j1_k1 ),"j1_k1 no debe estar vacio")
        self .assertEqual (j1_k1 ,j1_k2 ,'Para j=1, las iteraciones de k deben compartir el mismo valor')
        self .assertEqual (j2_k1 ,j2_k2 ,'Para j=2, las iteraciones de k deben compartir el mismo valor')
        self .assertNotEqual (j1_k1 ,j2_k1 ,'j=1 y j=2 deben tener valores distintos en Once(bucle=j)')

    def test_once_glitter_animation_unison (self ):
        """Verifica que conectar Glitter a traves de Once(line) haga que todas las chars tengan animaciones identicas."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Loops/Main Loop',
        'properties':{'iterator':'char','blank_mode':'no_blank'},
        'outputs':[{'name':'Loop','type':'bucle','links':[101 ]}]
        },
        {
        'id':2 ,
        'type':'Functions/Glitter',
        'properties':{
        'expandable':True ,
        'start_time':'0',
        'end_time':'fx.dur',
        'mode':'pulses',
        'density':'1.0',
        'seed':'0',
        'tags':[r'\fscxy',r'\blur'],
        'mins':['100','1'],
        'maxs':['150','5'],
        'tag_0':r'\fscxy','min_0':'100','max_0':'150',
        'tag_1':r'\blur','min_1':'1','max_1':'5'
        },
        'outputs':[{'name':'List','type':'data','links':[102 ]}]
        },
        {
        'id':3 ,
        'type':'Basics/Once',
        'properties':{'mode':'line'},
        'inputs':[{'name':'','type':0 ,'link':102 }],
        'outputs':[{'name':'','type':0 ,'links':[103 ]}]
        },
        {
        'id':4 ,
        'type':'System/Output',
        'properties':{'apply_to':'All Lines'},
        'inputs':[
        {'name':'Loop','type':'bucle','link':101 },
        {'name':'Layer','type':0 ,'link':None },
        {'name':'Start Time','type':0 ,'link':None },
        {'name':'End Time','type':0 ,'link':None },
        {'name':'Tags','type':0 ,'link':103 },
        {'name':'Return','type':'string','link':None }
        ]
        }
        ],
        'links':[
        [101 ,1 ,0 ,4 ,0 ,'bucle'],
        [102 ,2 ,0 ,3 ,0 ,'data'],
        [103 ,3 ,0 ,4 ,4 ,'data']
        ]
        }

        dialogues =[{'raw':r'Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,{\k50}A{\k50}B{\k50}C','is_selected':True }]
        engine =GraphEngine (graph )
        engine .process_single (dialogues ,self .styles ,allow_fallback_select_all =True )

        self .assertEqual (len (engine .all_generated_lines ),3 )
        import re 
        def extract_t_transforms (text ):
            return re .findall (r'\\t\([^)]+\)',text )

        t_0 =extract_t_transforms (engine .all_generated_lines [0 ]['text'])
        t_1 =extract_t_transforms (engine .all_generated_lines [1 ]['text'])
        t_2 =extract_t_transforms (engine .all_generated_lines [2 ]['text'])

        self .assertGreater (len (t_0 ),0 ,'Glitter debe generar transformaciones')
        self .assertEqual (t_0 ,t_1 ,'A y B deben tener exactamente las mismas transformaciones al pasar por Once(line)')
        self .assertEqual (t_1 ,t_2 ,'B y C deben tener exactamente las mismas transformaciones al pasar por Once(line)')

    def test_basics_once_canonical (self ):
        """Verifica la compatibilidad canónica de Basics/Once con propiedades en inglés."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Basics/Once',
        'properties':{'mode':'line','iterator':'j'},
        'inputs':[{'name':'In','type':0 ,'link':10 }],
        'outputs':[{'name':'Out','type':0 ,'links':[]}]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        call_count =0 
        def _mock_input (node ,slot ,context =None ):
            nonlocal call_count 
            call_count +=1 
            return f"VAL_{call_count }"
        engine .get_input_value =_mock_input 

        line_ctx ={'line':type ('L',(),{'i':1 })()}
        v1 =engine .evaluate_data_node (1 ,line_ctx ,output_slot_index =0 )
        v2 =engine .evaluate_data_node (1 ,line_ctx ,output_slot_index =0 )
        self .assertEqual (v1 ,"VAL_1")
        self .assertEqual (v2 ,"VAL_1")
        self .assertEqual (call_count ,1 )


if __name__ =='__main__':
    unittest .main ()


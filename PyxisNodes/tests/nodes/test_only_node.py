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

"""Pruebas unitarias para el nodo comodín Only (Compuerta Condicional de Datos)."""

import unittest 
import sys 
import os 
import re 

sys .path .insert (0 ,os .path .abspath (os .path .join (os .path .dirname (__file__ ),'..','..')))

from node_engine import GraphEngine 


class TestOnlyNode (unittest .TestCase ):
    """Pruebas unitarias para verificar la compuerta condicional del nodo Only."""

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
        tag_block =text .split ('}')[0 ].lstrip ('{')
        cleaned =re .sub (r'\\pos\([^)]+\)','',tag_block )
        cleaned =re .sub (r'^\\an\d','',cleaned )
        return cleaned .strip ()

    def test_only_true_passes_data (self ):
        """Verifica que con condicion=True o '1', los datos de entrada pasan intactos hacia la salida."""
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
        'properties':{'min':'100','max':'999','seed':'0'},
        'outputs':[{'name':'Out','type':'data','links':[102 ]}]
        },
        {
        'id':3 ,
        'type':'Basics/Only',
        'properties':{'condition':'True'},
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

        dialogues =[{'raw':r'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Hello','is_selected':True }]
        engine =GraphEngine (graph )
        engine .process_single (dialogues ,self .styles ,allow_fallback_select_all =True )

        self .assertEqual (len (engine .all_generated_lines ),1 )
        tag_val =self ._extract_tag_payload (engine .all_generated_lines [0 ]['text'])
        self .assertTrue (bool (tag_val ),"El dato debió pasar a través de Only cuando la condición es True")
        self .assertTrue (tag_val .isdigit ())

    def test_only_false_blocks_data (self ):
        """Verifica que con condicion=False o '0', los datos son bloqueados (retorna vacío)."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Loops/Main Loop',
        'properties':{'iterator':'line'},
        'outputs':[{'name':'Loop','type':'bucle','links':[201 ]}]
        },
        {
        'id':2 ,
        'type':'Basics/MultiRandom',
        'properties':{'min':'100','max':'999','seed':'0'},
        'outputs':[{'name':'Out','type':'data','links':[202 ]}]
        },
        {
        'id':3 ,
        'type':'Only',
        'properties':{'condition':'False'},
        'inputs':[{'name':'','type':0 ,'link':202 }],
        'outputs':[{'name':'','type':0 ,'links':[203 ]}]
        },
        {
        'id':4 ,
        'type':'System/Output',
        'properties':{'apply_to':'All Lines'},
        'inputs':[
        {'name':'Loop','type':'bucle','link':201 },
        {'name':'Layer','type':0 ,'link':None },
        {'name':'Start Time','type':0 ,'link':None },
        {'name':'End Time','type':0 ,'link':None },
        {'name':'Tags','type':0 ,'link':203 },
        {'name':'Return','type':'string','link':None }
        ]
        }
        ],
        'links':[
        [201 ,1 ,0 ,4 ,0 ,'bucle'],
        [202 ,2 ,0 ,3 ,0 ,'data'],
        [203 ,3 ,0 ,4 ,4 ,'data']
        ]
        }

        dialogues =[{'raw':r'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Hello','is_selected':True }]
        engine =GraphEngine (graph )
        engine .process_single (dialogues ,self .styles ,allow_fallback_select_all =True )

        self .assertEqual (len (engine .all_generated_lines ),1 )
        tag_val =self ._extract_tag_payload (engine .all_generated_lines [0 ]['text'])
        self .assertEqual (tag_val ,"","No debe haber ningún tag cuando la condición es False")

    def test_only_variable_condition_alternation (self ):
        """Verifica que con condición '$j % 2 == 1', Only deje pasar datos en impares y bloquee en pares."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Loops/Main Loop',
        'properties':{'iterator':'line'},
        'outputs':[{'name':'Loop','type':'bucle','links':[301 ]}]
        },
        {
        'id':2 ,
        'type':'Loops/MaxLoop',
        'properties':{'mode':'normal','iterations':'4','var_name':'j'},
        'inputs':[{'name':'Loop In','type':'bucle','link':301 }],
        'outputs':[{'name':'Loop Out','type':'bucle','links':[302 ]}]
        },
        {
        'id':3 ,
        'type':'Basics/MultiRandom',
        'properties':{'min':'1000','max':'9999','seed':'0'},
        'outputs':[{'name':'Out','type':'data','links':[303 ]}]
        },
        {
        'id':4 ,
        'type':'Basics/Only',
        'properties':{'condition':'$j % 2 == 1'},
        'inputs':[{'name':'','type':0 ,'link':303 }],
        'outputs':[{'name':'','type':0 ,'links':[304 ]}]
        },
        {
        'id':5 ,
        'type':'System/Output',
        'properties':{'apply_to':'All Lines'},
        'inputs':[
        {'name':'Loop','type':'bucle','link':302 },
        {'name':'Layer','type':0 ,'link':None },
        {'name':'Start Time','type':0 ,'link':None },
        {'name':'End Time','type':0 ,'link':None },
        {'name':'Tags','type':0 ,'link':304 },
        {'name':'Return','type':'string','link':None }
        ]
        }
        ],
        'links':[
        [301 ,1 ,0 ,2 ,0 ,'bucle'],
        [302 ,2 ,0 ,5 ,0 ,'bucle'],
        [303 ,3 ,0 ,4 ,0 ,'data'],
        [304 ,4 ,0 ,5 ,4 ,'data']
        ]
        }

        dialogues =[{'raw':r'Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Hello','is_selected':True }]
        engine =GraphEngine (graph )
        engine .process_single (dialogues ,self .styles ,allow_fallback_select_all =True )

        self .assertEqual (len (engine .all_generated_lines ),4 )
        vals =[self ._extract_tag_payload (l ['text'])for l in engine .all_generated_lines ]


        self .assertTrue (vals [0 ].isdigit ()and len (vals [0 ])==4 )

        self .assertEqual (vals [1 ],"")

        self .assertTrue (vals [2 ].isdigit ()and len (vals [2 ])==4 )

        self .assertEqual (vals [3 ],"")

    def test_only_prevents_upstream_execution (self ):
        """Verifica que cuando Only evalúa False, la cadena upstream no se ejecuta."""
        execution_tracker ={'count':0 }

        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Only',
        'properties':{'condition':'False'},
        'inputs':[{'name':'','type':0 ,'link':401 }],
        'outputs':[{'name':'','type':0 ,'links':[402 ]}]
        },
        {
        'id':2 ,
        'type':'Basics/MultiRandom',
        'properties':{'min':'10','max':'20','seed':'0'},
        'outputs':[{'name':'Out','type':'data','links':[401 ]}]
        }
        ],
        'links':[
        [401 ,2 ,0 ,1 ,0 ,'data']
        ]
        }

        engine =GraphEngine (graph )
        orig_get_input =engine .get_input_value 
        def tracked_get_input (node ,slot ,context =None ):
            if node .get ('id')==1 and slot ==0 :
                execution_tracker ['count']+=1 
            return orig_get_input (node ,slot ,context )
        engine .get_input_value =tracked_get_input 

        res =engine .evaluate_data_node (1 ,{})
        self .assertEqual (res ,"")
        self .assertEqual (execution_tracker ['count'],0 ,"No debe llamarse get_input_value cuando la condición es False")

    def test_only_select_ternary_both_inputs (self ):
        """Verifica que el modo Ternario (select) retorne Entrada 0 si True y Entrada 1 si False."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Only',
        'properties':{'condition':'$val > 10','mode':'select'},
        'inputs':[
        {'name':'True','type':0 ,'link':11 },
        {'name':'False','type':0 ,'link':12 }
        ],
        'outputs':[{'name':'Out','type':0 ,'links':[13 ]}]
        },
        {
        'id':2 ,
        'type':'Basics/MultiRandom',
        'properties':{'min':'100','max':'100','seed':'0'},
        'outputs':[{'name':'Out','type':'data','links':[11 ]}]
        },
        {
        'id':3 ,
        'type':'Basics/MultiRandom',
        'properties':{'min':'200','max':'200','seed':'0'},
        'outputs':[{'name':'Out','type':'data','links':[12 ]}]
        }
        ],
        'links':[
        [11 ,2 ,0 ,1 ,0 ,'data'],
        [12 ,3 ,0 ,1 ,1 ,'data']
        ]
        }

        engine =GraphEngine (graph )
        res_true =engine .evaluate_data_node (1 ,{'val':25 })
        self .assertEqual (res_true ,"100")

        res_false =engine .evaluate_data_node (1 ,{'val':5 })
        self .assertEqual (res_false ,"200")

    def test_only_select_short_circuit (self ):
        """Verifica que el modo Ternario no evalúe la rama inactiva."""
        tracker ={'in0':0 ,'in1':0 }

        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Only',
        'properties':{'condition':'True','mode':'select'},
        'inputs':[
        {'name':'True','type':0 ,'link':21 },
        {'name':'False','type':0 ,'link':22 }
        ],
        'outputs':[{'name':'Out','type':0 ,'links':[]}]
        }
        ],
        'links':[]
        }

        engine =GraphEngine (graph )
        orig_get_input =engine .get_input_value 
        def mock_get_input (node ,slot ,context =None ):
            if slot ==0 :
                tracker ['in0']+=1 
                return "A"
            elif slot ==1 :
                tracker ['in1']+=1 
                return "B"
            return ""
        engine .get_input_value =mock_get_input 


        res =engine .evaluate_data_node (1 ,{})
        self .assertEqual (res ,"A")
        self .assertEqual (tracker ['in0'],1 )
        self .assertEqual (tracker ['in1'],0 )


        engine .nodes [1 ]['properties']['condition']='False'
        res =engine .evaluate_data_node (1 ,{})
        self .assertEqual (res ,"B")
        self .assertEqual (tracker ['in0'],1 )
        self .assertEqual (tracker ['in1'],1 )

    def test_only_split_mode_routing (self ):
        """Verifica que el modo Desviador (split) enrute a la salida True (slot 0) o False (slot 1)."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Only',
        'properties':{'condition':'$flag == 1','mode':'split'},
        'inputs':[{'name':'In','type':0 ,'link':31 }],
        'outputs':[
        {'name':'True','type':0 ,'links':[]},
        {'name':'False','type':0 ,'links':[]}
        ]
        }
        ],
        'links':[]
        }

        engine =GraphEngine (graph )
        engine .get_input_value =lambda node ,slot ,context =None :"DATA_IN"



        out0_true =engine .evaluate_data_node (1 ,{'flag':1 },output_slot_index =0 )
        self .assertEqual (out0_true ,"DATA_IN")

        out1_true =engine .evaluate_data_node (1 ,{'flag':1 },output_slot_index =1 )
        self .assertEqual (out1_true ,"")



        out0_false =engine .evaluate_data_node (1 ,{'flag':0 },output_slot_index =0 )
        self .assertEqual (out0_false ,"")

        out1_false =engine .evaluate_data_node (1 ,{'flag':0 },output_slot_index =1 )
        self .assertEqual (out1_false ,"DATA_IN")

    def test_basics_only_canonical (self ):
        """Verifica la compatibilidad canónica de Basics/Only con propiedades en inglés."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Basics/Only',
        'properties':{'condition':'$flag == 1','mode':'select'},
        'inputs':[{'name':'True','type':0 ,'link':10 },{'name':'False','type':0 ,'link':20 }],
        'outputs':[{'name':'Out','type':0 ,'links':[]}]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        engine .get_input_value =lambda node ,slot ,context =None :("TRUE_VAL"if slot ==0 else "FALSE_VAL")
        self .assertEqual (engine .evaluate_data_node (1 ,{'flag':1 },output_slot_index =0 ),"TRUE_VAL")
        self .assertEqual (engine .evaluate_data_node (1 ,{'flag':0 },output_slot_index =0 ),"FALSE_VAL")


if __name__ =='__main__':
    unittest .main ()


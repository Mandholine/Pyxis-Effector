import unittest 
import sys 
import os 
import re 

sys .path .insert (0 ,os .path .abspath (os .path .join (os .path .dirname (__file__ ),'..','..')))

from node_engine import GraphEngine 
from nodes .tag_nodes import node_color_gradient 


class TestTagAndColorNodes (unittest .TestCase ):

    def test_color_gradient_slot0_single (self ):
        ctx ={'char':type ('Char',(),{'i':1 ,'n':3 })()}
        res0 =node_color_gradient (ctx ,prog ='0.0',colors_str ='#FF0000,#0000FF',total =3 ,accel =1.0 ,output_slot_index =0 )
        self .assertEqual (res0 ,'&H0000FF&')
        res1 =node_color_gradient (ctx ,prog ='1.0',colors_str ='#FF0000,#0000FF',total =3 ,accel =1.0 ,output_slot_index =0 )
        self .assertEqual (res1 ,'&HFF0000&')

    def test_color_gradient_slot1_batch_list (self ):
        ctx ={}
        batch =node_color_gradient (ctx ,prog ='0.5',colors_str ='#FF0000,#0000FF',total =3 ,accel =1.0 ,output_slot_index =1 )
        colors =[c .strip ()for c in batch .split (',')]
        self .assertEqual (len (colors ),3 )
        self .assertEqual (colors [0 ],'&H0000FF&')
        self .assertEqual (colors [2 ],'&HFF0000&')

    def test_color_gradient_default_total_1 (self ):
        ctx ={}
        batch =node_color_gradient (ctx ,output_slot_index =1 )
        colors =[c .strip ()for c in batch .split (',')]
        self .assertEqual (len (colors ),1 )

    def test_color_gradient_slot2_tags_batch (self ):
        ctx ={}
        batch_tags =node_color_gradient (ctx ,prog ='0.5',colors_str ='#FFFFFF,#000000',total =3 ,accel =1.0 ,tag_type ='\\1c',output_slot_index =2 )
        tags =[t .strip ()for t in batch_tags .split (',')]
        self .assertEqual (len (tags ),3 )
        self .assertTrue (tags [0 ].startswith ('\\1c&H'))
        self .assertTrue (tags [2 ].startswith ('\\1c&H'))


        batch_tags_3c =node_color_gradient (ctx ,prog ='0.5',colors_str ='#FFFFFF,#000000',total =3 ,accel =1.0 ,tag_type ='\\3c',output_slot_index =2 )
        tags_3c =[t .strip ()for t in batch_tags_3c .split (',')]
        self .assertEqual (len (tags_3c ),3 )
        self .assertTrue (tags_3c [0 ].startswith ('\\3c&H'))
        self .assertTrue (tags_3c [2 ].startswith ('\\3c&H'))

    def test_color_gradient_with_dynamic_dn_and_di (self ):

        ctx ={'d_i':3 ,'d_n':5 ,'a_n':8 }


        col_single =node_color_gradient (ctx ,prog ='d_i / d_n',colors_str ='#000000,#FFFFFF',output_slot_index =0 )
        self .assertTrue (col_single .startswith ('&H'))


        col_batch_dn =node_color_gradient (ctx ,total ='d_n',colors_str ='#FF0000,#00FF00,#0000FF',output_slot_index =1 )
        colors_dn =[c .strip ()for c in col_batch_dn .split (',')]
        self .assertEqual (len (colors_dn ),5 )


        col_batch_an =node_color_gradient (ctx ,total ='a_n',colors_str ='#FF0000,#0000FF',output_slot_index =1 )
        colors_an =[c .strip ()for c in col_batch_an .split (',')]
        self .assertEqual (len (colors_an ),8 )

    def test_color_picker_multi_swatch_and_palette (self ):
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Color Picker',
        'properties':{
        'colors':['#FF0000','#00FF00','#0000FF'],
        'formats':['ASS','ASS','ASS']
        },
        'inputs':[],
        'outputs':[
        {'name':'Color List'},
        {'name':'Color 1'},
        {'name':'Color 2'},
        {'name':'Color 3'}
        ]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )

        res_slot0 =engine .evaluate_data_node (1 ,{},output_slot_index =0 )
        self .assertEqual (res_slot0 ,'&H0000FF&, &H00FF00&, &HFF0000&')


        res_slot1 =engine .evaluate_data_node (1 ,{},output_slot_index =1 )
        self .assertEqual (res_slot1 ,'&H0000FF&')


        res_slot2 =engine .evaluate_data_node (1 ,{},output_slot_index =2 )
        self .assertEqual (res_slot2 ,'&H00FF00&')


        res_slot3 =engine .evaluate_data_node (1 ,{},output_slot_index =3 )
        self .assertEqual (res_slot3 ,'&HFF0000&')

    def test_interpolator_slot1_batch_numeric (self ):
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Functions/Interpolator',
        'properties':{
        'iterator':'1',
        'total':'5',
        'accel':'1.0',
        'v1':'10',
        'v2':'50'
        },
        'inputs':[
        {'name':'Iterator'},
        {'name':'Total'},
        {'name':'Accel'},
        {'name':'v1','value':'10'},
        {'name':'v2','value':'50'}
        ]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        res_batch =engine .evaluate_data_node (1 ,{},output_slot_index =1 )
        nums =[n .strip ()for n in res_batch .split (',')]
        self .assertEqual (len (nums ),5 )
        self .assertEqual (nums [0 ],'10')
        self .assertEqual (nums [1 ],'20')
        self .assertEqual (nums [2 ],'30')
        self .assertEqual (nums [3 ],'40')
        self .assertEqual (nums [4 ],'50')

    def test_interpolator_slot1_batch_alpha (self ):
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Functions/Interpolator',
        'properties':{
        'iterator':'1',
        'total':'3',
        'accel':'1.0',
        'v1':'&H00&',
        'v2':'&HFF&'
        },
        'inputs':[
        {'name':'Iterator'},
        {'name':'Total'},
        {'name':'Accel'},
        {'name':'v1','value':'&H00&'},
        {'name':'v2','value':'&HFF&'}
        ]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        res_batch =engine .evaluate_data_node (1 ,{},output_slot_index =1 )
        alphas =[a .strip ()for a in res_batch .split (',')]
        self .assertEqual (len (alphas ),3 )
        self .assertEqual (alphas [0 ],'&H00&')
        self .assertEqual (alphas [1 ],'&H80&')
        self .assertEqual (alphas [2 ],'&HFF&')

    def test_interpolator_ass_tags_and_multitags (self ):
        """Verifica que Interpolator interpole etiquetas ASS directas, colores y multi-tags compuestos."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Functions/Interpolator',
        'properties':{
        'iterator':'1',
        'total':'5',
        'accel':'1.0',
        'v1':r'\1c&H0000FF&\frz0',
        'v2':r'\1c&HFF0000&\frz90'
        },
        'inputs':[
        {'name':'Iterator'},
        {'name':'Total'},
        {'name':'Accel'},
        {'name':'v1','value':r'\1c&H0000FF&\frz0'},
        {'name':'v2','value':r'\1c&HFF0000&\frz90'}
        ]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        res_batch =engine .evaluate_data_node (1 ,{},output_slot_index =1 )
        tags =[t .strip ()for t in res_batch .split (',')]
        self .assertEqual (len (tags ),5 )
        self .assertEqual (tags [0 ],r'\1c&H0000FF&\frz0')
        self .assertEqual (tags [1 ],r'\1c&H4000BF&\frz22.5')
        self .assertEqual (tags [2 ],r'\1c&H800080&\frz45')
        self .assertEqual (tags [3 ],r'\1c&HBF0040&\frz67.5')
        self .assertEqual (tags [4 ],r'\1c&HFF0000&\frz90')

    def test_interpolator_multi_keyframes_and_list_input (self ):
        """Verifica que Interpolator procese 3 o más keyframes y soporte entradas de listas conectadas o por propiedad."""
        graph ={
        'nodes':[
        {
        'id':10 ,
        'type':'Text',
        'properties':{'text':'#FF0000, #00FF00, #0000FF'},
        'inputs':[],
        'outputs':[{'name':'Text'}]
        },
        {
        'id':1 ,
        'type':'Functions/Interpolator',
        'properties':{
        'iterator':'1',
        'total':'5',
        'accel':'1.0',
        'v1':'',
        'v2':''
        },
        'inputs':[
        {'name':'Iterator'},
        {'name':'Total'},
        {'name':'Accel'},
        {'name':'v1','link':100 },
        {'name':'v2'}
        ]
        }
        ],
        'links':[[100 ,10 ,0 ,1 ,3 ,'text']]
        }
        engine =GraphEngine (graph )
        res_batch =engine .evaluate_data_node (1 ,{},output_slot_index =1 )
        colors =[c .strip ()for c in res_batch .split (',')]
        self .assertEqual (len (colors ),5 )
        self .assertEqual (colors [0 ],'#FF0000')
        self .assertEqual (colors [1 ],'#808000')
        self .assertEqual (colors [2 ],'#00FF00')
        self .assertEqual (colors [3 ],'#008080')
        self .assertEqual (colors [4 ],'#0000FF')
    def test_multirandom_slot1_batch (self ):
        """Verifica que MultiRandom slot 1 genere un batch de N números aleatorios."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'MultiRandom',
        'properties':{
        'mode':'R',
        'min':'10',
        'max':'20',
        'step':'1',
        'total':'5'
        },
        'inputs':[
        {'name':'Min','value':'10'},
        {'name':'Max','value':'20'},
        {'name':'Total (N)','value':'5'}
        ]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        res_batch =engine .evaluate_data_node (1 ,{},output_slot_index =1 )
        r_vals =[int (v .strip ())for v in res_batch .split (',')]
        self .assertEqual (len (r_vals ),5 )
        for val in r_vals :
            self .assertTrue (10 <=val <=20 )

    def test_conditioner_scalar (self ):
        """Verifica que Conditioner evalúe la condición y devuelva el elemento correspondiente."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Functions/Conditioner',
        'properties':{
        'condition':'True',
        'if_true':'\\blur2',
        'if_false':'\\blur0'
        },
        'inputs':[
        {'name':'Condition'},
        {'name':'If True'},
        {'name':'If False'}
        ]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        res_true =engine .evaluate_data_node (1 ,{})
        self .assertEqual (res_true ,'\\blur2')

        graph ['nodes'][0 ]['properties']['condition']='False'
        res_false =engine .evaluate_data_node (1 ,{})
        self .assertEqual (res_false ,'\\blur0')

    def test_conditioner_complete_lists_and_objects (self ):
        """Verifica que Conditioner entregue el elemento o lista completa de If True o If False según la condición."""
        from nodes .tag_nodes import node_condicionador 


        res_list_true =node_condicionador (
        {},
        condition ='True',
        if_true =r'\1c#FF0000\frz0, \1c#0000FF\frz40',
        if_false =r'\1c#FFFFFF\frz0'
        )
        self .assertEqual (res_list_true ,r'\1c#FF0000\frz0, \1c#0000FF\frz40')


        res_list_false =node_condicionador (
        {},
        condition ='False',
        if_true =r'\1c#FF0000\frz0',
        if_false =r'\pos(100,200), \pos(300,400)'
        )
        self .assertEqual (res_list_false ,r'\pos(100,200), \pos(300,400)')


        res_py_list =node_condicionador (
        {},
        condition ='True',
        if_true =['#FF0000','#00FF00','#0000FF'],
        if_false =['#AAAAAA']
        )
        self .assertEqual (res_py_list ,'#FF0000, #00FF00, #0000FF')

    def test_conditioner_with_context_expressions (self ):
        """Verifica que Conditioner evalúe expresiones de contexto correctamente."""
        from nodes .tag_nodes import node_condicionador 
        ctx ={'i':3 }
        res_odd =node_condicionador (ctx ,condition ='$i % 2 == 1',if_true ='impar',if_false ='par')
        self .assertEqual (res_odd ,'impar')

        ctx_even ={'i':4 }
        res_even =node_condicionador (ctx_even ,condition ='$i % 2 == 1',if_true ='impar',if_false ='par')
        self .assertEqual (res_even ,'par')

    def test_multitag_scalar_generation (self ):
        """Verifica que MultiTag genere tags ASS escalares individuales correctamente según el modo."""
        from nodes .tag_nodes import tag_master 

        res_blur =tag_master ({},tag_type ='blur',value ='2.5')
        self .assertEqual (res_blur ,'\\blur2.5')


        res_1a =tag_master ({},tag_type ='1a',value ='&H80&')
        self .assertEqual (res_1a ,'\\1a&H80&')


        res_1c =tag_master ({},tag_type ='1c',value ='#FF0000')
        self .assertEqual (res_1c ,'\\1c&H0000FF&')


        res_pos =tag_master ({},tag_type ='pos',x ='100',y ='200')
        self .assertEqual (res_pos ,'\\pos(100,200)')


        res_frz =tag_master ({},tag_type ='frz',value ='45')
        self .assertEqual (res_frz ,'\\frz45')

    def test_basics_multitag_canonical_graph (self ):
        """Verifica la ejecución de Basics/MultiTag en GraphEngine con propiedades en inglés."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Basics/MultiTag',
        'properties':{'tag_type':'pos','x':'320','y':'240'},
        'inputs':[{'name':'X','type':0 ,'link':None },{'name':'Y','type':0 ,'link':None }],
        'outputs':[{'name':'String','type':'string','links':[]}]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (1 ,{},output_slot_index =0 )
        self .assertEqual (res ,'\\pos(320,240)')

    def test_dynamic_format_vector_zip (self ):
        """Verifica que Dynamic Format ejecute vector zip cuando las entradas son listas."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Dynamic Format',
        'properties':{
        'Formato':'\\blur%s\\bord%s',
        'In1':'1, 2, 3',
        'In2':'0.5, 1.0, 1.5'
        },
        'inputs':[
        {'name':'In1','value':'1, 2, 3'},
        {'name':'In2','value':'0.5, 1.0, 1.5'}
        ]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (1 ,{})
        items =[x .strip ()for x in res .split (',')]
        self .assertEqual (len (items ),3 )
        self .assertEqual (items [0 ],'\\blur1\\bord0.5')
        self .assertEqual (items [1 ],'\\blur2\\bord1.0')
        self .assertEqual (items [2 ],'\\blur3\\bord1.5')

    def test_multirandom_scalar (self ):
        """Verifica que MultiRandom genere valores aleatorios escalares para 1 valor por loop."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'MultiRandom',
        'properties':{
        'mode':'R',
        'min':'10',
        'max':'20',
        'step':'1'
        },
        'inputs':[
        {'name':'Min','value':'10'},
        {'name':'Max','value':'20'},
        {'name':'Step','value':'1'}
        ]
        },
        {
        'id':2 ,
        'type':'MultiRandom',
        'properties':{
        'mode':'Rcolor',
        'min':'#FFFFFF',
        'max':'#000000'
        },
        'inputs':[
        {'name':'Color Min','value':'#FFFFFF'},
        {'name':'Color Max','value':'#000000'}
        ]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )

        res_scalar =engine .evaluate_data_node (1 ,{})
        val =int (res_scalar )
        self .assertTrue (10 <=val <=20 )


        res_col_scalar =engine .evaluate_data_node (2 ,{})
        self .assertTrue (res_col_scalar .startswith ('#')or res_col_scalar .startswith ('&H'))

    def test_multirandom_batch_slot1 (self ):
        """Verifica que MultiRandom genere un lote separado por comas en slot 1 con Total (N)."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'MultiRandom',
        'properties':{
        'mode':'R',
        'min':'10',
        'max':'20',
        'step':'1',
        'total':'5'
        },
        'inputs':[
        {'name':'Min','value':'10'},
        {'name':'Max','value':'20'},
        {'name':'Step','value':'1'},
        {'name':'Total (N)','value':'5'}
        ]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        res_batch =engine .evaluate_data_node (1 ,{},output_slot_index =1 )
        items =[int (x .strip ())for x in res_batch .split (',')]
        self .assertEqual (len (items ),5 )
        for val in items :
            self .assertTrue (10 <=val <=20 )

    def test_conditioner_single_default_total (self ):
        """Verifica que Conditioner en slot 0 por defecto evalúe 1 solo valor."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Functions/Conditioner',
        'properties':{
        'condicion':'True',
        'si_verdadero':'\\1c&H0000FF&',
        'si_falso':'\\1c&HFF0000&',
        'total':'1'
        },
        'inputs':[
        {'name':'Condition'},
        {'name':'If True'},
        {'name':'If False'},
        {'name':'Total (N)','value':'1'}
        ]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        res_single =engine .evaluate_data_node (1 ,{},output_slot_index =0 )
        self .assertEqual (res_single ,'\\1c&H0000FF&')

    def test_color_gradient_slot2_tags_single_progression (self ):
        """Verifica que Color Gradient en slot 2 (Tags) retorne el tag con \\1c y el color interpolado."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Functions/Color Gradient',
        'properties':{
        'prog':'d_i / d_n',
        'colors_str':'#FF0000, #00FF00',
        'total':'1',
        'accel':'1.0',
        'tag_type':'\\1c'
        }
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        ctx1 ={'d_i':1 ,'d_n':2 }
        res1 =engine .evaluate_data_node (1 ,ctx1 ,output_slot_index =2 )

        self .assertTrue (res1 .startswith ('\\1c&H'))


        res_col =engine .evaluate_data_node (1 ,ctx1 ,output_slot_index =0 )
        self .assertTrue (res_col .startswith ('&H')and res_col .endswith ('&'))

    def test_color_gradient_batch (self ):
        """Verifica que Color Gradient en modo batch genere lista separada por comas."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Functions/Color Gradient',
        'properties':{
        'colors_str':'#FF0000, #0000FF',
        'total':'3',
        'accel':'1.0',
        'tag_type':'\\1c'
        }
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )

        res_batch_cols =engine .evaluate_data_node (1 ,{},output_slot_index =1 )
        self .assertEqual (len (res_batch_cols .split (', ')),3 )


        res_batch_tags =engine .evaluate_data_node (1 ,{},output_slot_index =2 )
        tags =res_batch_tags .split (', ')
        self .assertEqual (len (tags ),3 )
        for t in tags :
            self .assertTrue (t .startswith ('\\1c&H'))

    def test_concatenate_standard_modes (self ):
        """Verifica modos tradicionales de Concatenate (nil, espacio, coma, punto_coma, salto)."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Concatenate',
        'properties':{'separator':'nil','In1':'A','In2':'B','In3':'C'},
        'inputs':[{'link':None },{'link':None },{'link':None }]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        self .assertEqual (engine .evaluate_data_node (1 ,{}),"ABC")


        graph ['nodes'][0 ]['properties']['separator']='space'
        self .assertEqual (engine .evaluate_data_node (1 ,{}),"A B C")


        graph ['nodes'][0 ]['properties']['separator']='comma'
        self .assertEqual (engine .evaluate_data_node (1 ,{}),"A,B,C")


        graph ['nodes'][0 ]['properties']['separator']='semicolon'
        self .assertEqual (engine .evaluate_data_node (1 ,{}),"A;B;C")


        graph ['nodes'][0 ]['properties']['separator']='newline'
        self .assertEqual (engine .evaluate_data_node (1 ,{}),"A\nB\nC")

    def test_concatenate_zip_mode_wire_numbers_with_prefix (self ):
        """Verifica que Concatenate en modo Zip tome números por cable e inyecte el tag de la caja."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Text',
        'properties':{'value':'10, 20, 30'},
        'inputs':[],
        'outputs':[{'name':'String'}]
        },
        {
        'id':2 ,
        'type':'Concatenate',
        'properties':{'separator':'zip','In1':'\\frz'},
        'inputs':[{'link':101 }],
        'outputs':[{'name':'String'}]
        }
        ],
        'links':[[101 ,1 ,0 ,2 ,0 ,'data']]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (2 ,{})
        self .assertEqual (res ,"\\frz10, \\frz20, \\frz30")

    def test_concatenate_zip_mode_wire_hex_colors_with_prefix (self ):
        """Verifica que Concatenate en modo Zip formatee colores hex web a formato de color ASS &HBBGGRR&."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Text',
        'properties':{'value':'#FF0000, #00FF00, #0000FF'},
        'inputs':[],
        'outputs':[{'name':'String'}]
        },
        {
        'id':2 ,
        'type':'Concatenate',
        'properties':{'separator':'zip','In1':'\\1c'},
        'inputs':[{'link':101 }],
        'outputs':[{'name':'String'}]
        }
        ],
        'links':[[101 ,1 ,0 ,2 ,0 ,'data']]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (2 ,{})
        self .assertEqual (res ,"\\1c&H0000FF&, \\1c&H00FF00&, \\1c&HFF0000&")

    def test_concatenate_zip_mode_broadcast_scalar (self ):
        """Verifica que Concatenate en modo Zip difunda (broadcast) un tag escalar a todos los keyframes."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Text',
        'properties':{'value':'10, 20, 30'},
        'inputs':[],
        'outputs':[{'name':'String'}]
        },
        {
        'id':2 ,
        'type':'Concatenate',
        'properties':{'separator':'zip','In1':'\\frz','In2':'\\blur2'},
        'inputs':[{'link':101 },{'link':None }],
        'outputs':[{'name':'String'}]
        }
        ],
        'links':[[101 ,1 ,0 ,2 ,0 ,'data']]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (2 ,{})
        self .assertEqual (res ,"\\frz10\\blur2, \\frz20\\blur2, \\frz30\\blur2")

    def test_concatenate_zip_mode_multiple_lists_and_scalars (self ):
        """Verifica la combinación multi-entrada de colores, rotaciones y alphas escalares."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Text',
        'properties':{'value':'#FF0000, #0000FF'},
        'inputs':[],
        'outputs':[{'name':'String'}]
        },
        {
        'id':2 ,
        'type':'Text',
        'properties':{'value':'10, 20'},
        'inputs':[],
        'outputs':[{'name':'String'}]
        },
        {
        'id':3 ,
        'type':'Concatenate',
        'properties':{'separator':'zip','In1':'\\1c','In2':'\\frz','In3':'\\alpha&H80&'},
        'inputs':[{'link':101 },{'link':102 },{'link':None }],
        'outputs':[{'name':'String'}]
        }
        ],
        'links':[
        [101 ,1 ,0 ,3 ,0 ,'data'],
        [102 ,2 ,0 ,3 ,1 ,'data']
        ]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (3 ,{})
        self .assertEqual (res ,"\\1c&H0000FF&\\frz10\\alpha&H80&, \\1c&HFF0000&\\frz20\\alpha&H80&")

    def test_concatenate_zip_mode_uneven_lengths_truncation (self ):
        """Verifica que si dos listas tienen longitudes desiguales se trunque a la longitud mínima."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Text',
        'properties':{'value':'10, 20, 30, 40'},
        'inputs':[],
        'outputs':[{'name':'String'}]
        },
        {
        'id':2 ,
        'type':'Text',
        'properties':{'value':'100, 200'},
        'inputs':[],
        'outputs':[{'name':'String'}]
        },
        {
        'id':3 ,
        'type':'Concatenate',
        'properties':{'separator':'zip','In1':'\\frz','In2':'\\fscx'},
        'inputs':[{'link':101 },{'link':102 }],
        'outputs':[{'name':'String'}]
        }
        ],
        'links':[
        [101 ,1 ,0 ,3 ,0 ,'data'],
        [102 ,2 ,0 ,3 ,1 ,'data']
        ]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (3 ,{})
        self .assertEqual (res ,"\\frz10\\fscx100, \\frz20\\fscx200")

    def test_concatenate_zip_mode_no_duplicate_prefix (self ):
        """Verifica que si el valor entrante ya contiene el tag, no lo duplique."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Text',
        'properties':{'value':'\\frz10, \\frz20'},
        'inputs':[],
        'outputs':[{'name':'String'}]
        },
        {
        'id':2 ,
        'type':'Concatenate',
        'properties':{'separator':'zip','In1':'\\frz'},
        'inputs':[{'link':101 }],
        'outputs':[{'name':'String'}]
        }
        ],
        'links':[[101 ,1 ,0 ,2 ,0 ,'data']]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (2 ,{})
        self .assertEqual (res ,"\\frz10, \\frz20")

    def test_concatenate_zip_mode_direct_boxes_no_wires (self ):
        """Verifica que Concatenate en modo Zip funcione con listas escritas directamente en las cajas."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Concatenate',
        'properties':{
        'separator':'zip',
        'In1':'\\1c&H0000FF&, \\1c&H00FF00&',
        'In2':'\\frz0, \\frz45'
        },
        'inputs':[{'link':None },{'link':None }],
        'outputs':[{'name':'String'}]
        }
        ],
        'links':[]
        }
    def test_concatenate_zip_mode_color_gradient_connection (self ):
        """Verifica que Concatenate en modo Zip conectado a Color Gradient arme keyframes correctamente."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Functions/Color Gradient',
        'properties':{
        'colors_str':'#FF0000, #00FF00, #0000FF',
        'total':'3',
        'accel':'1.0'
        },
        'inputs':[],
        'outputs':[{'name':'Color (ASS)'},{'name':'Color List (Batch)'}]
        },
        {
        'id':2 ,
        'type':'Text',
        'properties':{'value':'0, 45, 90'},
        'inputs':[],
        'outputs':[{'name':'String'}]
        },
        {
        'id':3 ,
        'type':'Concatenate',
        'properties':{
        'separator':'zip',
        'In1':'\\1c',
        'In2':'\\frz',
        'In3':'\\blur1'
        },
        'inputs':[{'link':101 },{'link':102 },{'link':None }],
        'outputs':[{'name':'String'}]
        }
        ],
        'links':[
        [101 ,1 ,1 ,3 ,0 ,'data'],
        [102 ,2 ,0 ,3 ,1 ,'data']
        ]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (3 ,{})
        self .assertEqual (res ,"\\1c&H0000FF&\\frz0\\blur1, \\1c&H00FF00&\\frz45\\blur1, \\1c&HFF0000&\\frz90\\blur1")

    def test_glitter_destellos_profile (self ):
        from nodes .tag_nodes import glitter_node 
        res =glitter_node (None ,start_time ="0",end_time ="500",modo_oscilacion ="Destellos",tag_0 =r"\fscx",min_0 ="150",max_0 ="250",output_slot_index =0 )
        self .assertIn (r"\t(",res )
        self .assertIn (r"\fscx",res )

    def test_glitter_color_interpolation (self ):
        from nodes .tag_nodes import glitter_node 
        res =glitter_node (None ,start_time ="0",end_time ="300",modo_oscilacion ="Oleaje",tag_0 =r"\1c",min_0 ="&HFFFFFF&",max_0 ="&H0000FF&",output_slot_index =0 )
        self .assertIn (r"\t(",res )
        self .assertIn (r"\1c&H",res )

    def test_glitter_graph_engine_multi_slot (self ):
        graph ={
        'nodes':[
        {
        'id':100 ,
        'type':'Functions/Glitter',
        'properties':{
        'start_time':'0',
        'end_time':'400',
        'modo_oscilacion':'Pulsos',
        'tag_0':r'\fscx',
        'min_0':'120',
        'max_0':'200',
        'tag_1':r'\blur',
        'min_1':'1.0',
        'max_1':'4.0'
        },
        'inputs':[],
        'outputs':[{'name':'List'},{'name':'TAG 1'},{'name':'TAG 2'}]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        res_list =engine .evaluate_data_node (100 ,{},output_slot_index =0 )
        self .assertIn (r"\fscx",res_list )
        self .assertIn (r"\blur",res_list )

        res_tag1 =engine .evaluate_data_node (100 ,{},output_slot_index =1 )
        self .assertIn (r"\fscx",res_tag1 )
        self .assertNotIn (r"\blur",res_tag1 )

        res_tag2 =engine .evaluate_data_node (100 ,{},output_slot_index =2 )
        self .assertIn (r"\blur",res_tag2 )
        self .assertNotIn (r"\fscx",res_tag2 )

    def test_glitter_pairs_effector2_structure (self ):
        """Verifica que destellos genere pares (subida a pico y decaimiento a base) según ke.tag.glitter de Effector 2."""
        from nodes .tag_nodes import glitter_node 
        import re 
        res =glitter_node (None ,start_time ="0",end_time ="600",modo_oscilacion ="Destellos",tag_0 =r"\fscx",min_0 ="150",max_0 ="250",output_slot_index =0 )

        matches =re .findall (r"\\t\((\d+),(\d+),\\fscx(\d+)\)",res )
        self .assertGreaterEqual (len (matches ),2 ,"Debe haber al menos un par (subida y bajada) en 600ms")

        first_peak =int (matches [0 ][2 ])
        first_base =int (matches [1 ][2 ])
        self .assertGreaterEqual (first_peak ,200 ,f"El pico ({first_peak }) debe alcanzar valores altos")
        self .assertLessEqual (first_base ,185 ,f"La base de decaimiento ({first_base }) debe regresar al valor base/mínimo")

    def test_glitter_textbox_custom_values (self ):
        """Verifica que valores arbitrarios en las cajas de texto (p.ej. \blur, min 1, max 8) sean tomados directamente."""
        from nodes .tag_nodes import glitter_node 
        import re 
        res =glitter_node (None ,start_time ="0",end_time ="600",modo_oscilacion ="Destellos",tag_0 =r"\blur",min_0 ="1",max_0 ="8",output_slot_index =0 )
        matches =re .findall (r"\\t\((\d+),(\d+),\\blur(\d+)\)",res )
        self .assertTrue (len (matches )>=2 )
        vals =[int (m [2 ])for m in matches ]

        for v in vals :
            self .assertTrue (1 <=v <=8 ,f"El valor {v } debe estar dentro de [1, 8]")

    def test_glitter_random_duration_ranges (self ):
        """Verifica que Oleaje (250-400ms), Pulsos (150-250ms) y Flashes (40-100ms) respeten sus rangos temporales."""
        from nodes .tag_nodes import glitter_node 
        import re 


        res_flash =glitter_node (None ,start_time ="0",end_time ="3000",modo_oscilacion ="Destellos",tag_0 =r"\fscx",min_0 ="100",max_0 ="200",output_slot_index =0 )

        pairs_flash =re .findall (r"\\t\((\d+),(\d+),[^\)]+\)\\t\((\d+),(\d+),[^\)]+\)",res_flash )
        self .assertTrue (len (pairs_flash )>0 )
        for t1 ,t2 ,t3 ,t4 in pairs_flash :
            decay =int (t4 )-int (t3 )

            if int (t4 )<3000 :
                self .assertTrue (40 <=decay <=100 ,f"Decaimiento de flash ({decay }ms) debe estar entre 40 y 100ms")


        res_pulso =glitter_node (None ,start_time ="0",end_time ="3000",modo_oscilacion ="Pulsos",tag_0 =r"\fscx",min_0 ="100",max_0 ="200",output_slot_index =0 )
        pairs_pulso =re .findall (r"\\t\((\d+),(\d+),[^\)]+\)\\t\((\d+),(\d+),[^\)]+\)",res_pulso )
        self .assertTrue (len (pairs_pulso )>0 )
        for t1 ,t2 ,t3 ,t4 in pairs_pulso :
            rise =int (t2 )-int (t1 )
            decay =int (t4 )-int (t3 )
            if int (t2 )<3000 :
                self .assertTrue (150 <=rise <=250 ,f"Subida de pulso ({rise }ms) debe estar entre 150 y 250ms")
            if int (t4 )<3000 :
                self .assertTrue (150 <=decay <=250 ,f"Decaimiento de pulso ({decay }ms) debe estar entre 150 y 250ms")


        res_oleaje =glitter_node (None ,start_time ="0",end_time ="3000",modo_oscilacion ="Oleaje",tag_0 =r"\fscx",min_0 ="100",max_0 ="200",output_slot_index =0 )
        pairs_oleaje =re .findall (r"\\t\((\d+),(\d+),[^\)]+\)\\t\((\d+),(\d+),[^\)]+\)",res_oleaje )
        self .assertTrue (len (pairs_oleaje )>0 )
        for t1 ,t2 ,t2_bis ,t3 in pairs_oleaje :
            rise =int (t2 )-int (t1 )
            decay =int (t3 )-int (t2_bis )
            if int (t2 )<3000 :
                self .assertTrue (250 <=rise <=400 ,f"Subida de oleaje ({rise }ms) debe estar entre 250 y 400ms")
            if int (t3 )<3000 :
                self .assertTrue (250 <=decay <=400 ,f"Bajada de oleaje ({decay }ms) debe estar entre 250 y 400ms")

    def test_glitter_time_window_control (self ):
        """Verifica que las transformaciones se mantengan estrictamente dentro de la ventana [start_time, end_time]."""
        from nodes .tag_nodes import glitter_node 
        import re 


        ctx ={"fx_dur":600 }
        res =glitter_node (ctx ,start_time ="150",end_time ="450",modo_oscilacion ="Destellos",tag_0 =r"\fscx",min_0 ="100",max_0 ="200",output_slot_index =0 )
        times =re .findall (r"\\t\((\d+),(\d+),",res )
        self .assertTrue (len (times )>0 )
        for t1_s ,t2_s in times :
            t1 =int (t1_s )
            t2 =int (t2_s )
            self .assertGreaterEqual (t1 ,150 ,f"t1 ({t1 }) debe ser >= start_time (150)")
            self .assertLessEqual (t2 ,450 ,f"t2 ({t2 }) debe ser <= end_time (450)")


        res_expr =glitter_node (ctx ,start_time ="50",end_time ="fx.dur / 2",modo_oscilacion ="Pulsos",tag_0 =r"\fscx",min_0 ="100",max_0 ="200",output_slot_index =0 )
        times_expr =re .findall (r"\\t\((\d+),(\d+),",res_expr )
        self .assertTrue (len (times_expr )>0 )
        for t1_s ,t2_s in times_expr :
            t1 =int (t1_s )
            t2 =int (t2_s )
            self .assertGreaterEqual (t1 ,50 ,f"t1 ({t1 }) debe ser >= 50")
            self .assertLessEqual (t2 ,300 ,f"t2 ({t2 }) debe ser <= fx.dur / 2 (300)")

    def test_glitter_time_window_inputs_cables (self ):
        """Verifica que los cables conectados a Start (slot 0) y End (slot 1) sobrescriban la ventana temporal en GraphEngine."""
        from node_engine import GraphEngine 
        import re 

        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Text',
        'properties':{'text':'200'},
        'inputs':[],
        'outputs':[{'name':'Text','links':[1 ]}]
        },
        {
        'id':2 ,
        'type':'Text',
        'properties':{'text':'500'},
        'inputs':[],
        'outputs':[{'name':'Text','links':[2 ]}]
        },
        {
        'id':100 ,
        'type':'Functions/Glitter',
        'properties':{
        'start_time':'0',
        'end_time':'fx.dur',
        'modo_oscilacion':'Destellos',
        'tag_0':r'\fscx',
        'min_0':'150',
        'max_0':'250'
        },
        'inputs':[{'name':'Start','link':1 },{'name':'End','link':2 },{'name':'In 1'}],
        'outputs':[{'name':'List'},{'name':'TAG 1'}]
        }
        ],
        'links':[
        [1 ,1 ,0 ,100 ,0 ,'data'],
        [2 ,2 ,0 ,100 ,1 ,'data']
        ]
        }
        engine =GraphEngine (graph )
        res =engine .evaluate_data_node (100 ,{'fx_dur':1000 },output_slot_index =0 )
        times =re .findall (r"\\t\((\d+),(\d+),",res )
        self .assertTrue (len (times )>0 )
        for t1_s ,t2_s in times :
            t1 =int (t1_s )
            t2 =int (t2_s )
            self .assertGreaterEqual (t1 ,200 ,f"t1 ({t1 }) debe ser >= cable Start (200)")
            self .assertLessEqual (t2 ,500 ,f"t2 ({t2 }) debe ser <= cable End (500)")

    def test_glitter_density_scaling (self ):
        """Verifica que la densidad escale inversamente las pausas (mayor densidad = mayor cantidad de destellos)."""
        from nodes .tag_nodes import glitter_node 

        ctx_low ={'unit_i':10 }
        ctx_med ={'unit_i':10 }
        ctx_high ={'unit_i':10 }

        res_low =glitter_node (ctx_low ,start_time ="0",end_time ="4000",density ="0.2",modo_oscilacion ="Destellos",tag_0 =r"\fscx",min_0 ="100",max_0 ="200",output_slot_index =0 )
        res_med =glitter_node (ctx_med ,start_time ="0",end_time ="4000",density ="1.0",modo_oscilacion ="Destellos",tag_0 =r"\fscx",min_0 ="100",max_0 ="200",output_slot_index =0 )
        res_high =glitter_node (ctx_high ,start_time ="0",end_time ="4000",density ="5.0",modo_oscilacion ="Destellos",tag_0 =r"\fscx",min_0 ="100",max_0 ="200",output_slot_index =0 )

        count_low =len (re .findall (r"\\t\(",res_low ))
        count_med =len (re .findall (r"\\t\(",res_med ))
        count_high =len (re .findall (r"\\t\(",res_high ))

        self .assertGreater (count_high ,count_med ,f"Alta densidad ({count_high }) debe producir más transformaciones que media ({count_med })")
        self .assertGreater (count_med ,count_low ,f"Media densidad ({count_med }) debe producir más transformaciones que baja ({count_low })")

    def test_glitter_memoization_cache (self ):
        """Verifica que GraphEngine use la caché intra-contexto para no recalcular la simulación estocástica en puertos múltiples."""
        graph ={
        'nodes':[
        {
        'id':100 ,
        'type':'Functions/Glitter',
        'properties':{
        'start_time':'0',
        'end_time':'1000',
        'density':'1.5',
        'modo_oscilacion':'Destellos',
        'tag_0':r'\fscx',
        'min_0':'100',
        'max_0':'200',
        'tag_1':r'\fscy',
        'min_1':'80',
        'max_1':'180'
        },
        'inputs':[{'name':'Start'},{'name':'End'},{'name':'Density'},{'name':'In 1'},{'name':'In 2'}],
        'outputs':[{'name':'List'},{'name':'TAG 1'},{'name':'TAG 2'}]
        }
        ],
        'links':[]
        }
        engine =GraphEngine (graph )
        ctx ={'fx_dur':1000 ,'unit_i':7 }


        res_list =engine .evaluate_data_node (100 ,ctx ,output_slot_index =0 )


        memo_keys =[k for k in ctx .keys ()if k .startswith ('_glitter_100_')]
        self .assertEqual (len (memo_keys ),1 ,"Debe existir una clave de caché intra-contexto para el nodo Glitter")


        res_tag1 =engine .evaluate_data_node (100 ,ctx ,output_slot_index =1 )

        res_tag2 =engine .evaluate_data_node (100 ,ctx ,output_slot_index =2 )


        times_tag1 =re .findall (r"\\t\((\d+,\d+),",res_tag1 )
        times_tag2 =re .findall (r"\\t\((\d+,\d+),",res_tag2 )

        self .assertTrue (len (times_tag1 )>0 )
        self .assertEqual (times_tag1 ,times_tag2 ,"Ambas salidas TAG deben compartir exactamente los mismos intervalos de tiempo por caché")
        for t_pair in times_tag1 :
            self .assertIn (f"\\t({t_pair },",res_list )
            self .assertIn (r"\fscx",res_list )
            self .assertIn (r"\fscy",res_list )

    def test_glitter_density_input_cable (self ):
        """Verifica que el puerto de entrada 'Density' (input 2) acepte cables y sobrescriba la propiedad local."""
        graph ={
        'nodes':[
        {
        'id':1 ,
        'type':'Text',
        'properties':{'text':'4.0'},
        'inputs':[],
        'outputs':[{'name':'Text','links':[1 ]}]
        },
        {
        'id':100 ,
        'type':'Functions/Glitter',
        'properties':{
        'start_time':'0',
        'end_time':'2000',
        'density':'0.1',
        'modo_oscilacion':'Destellos',
        'tag_0':r'\fscx',
        'min_0':'100',
        'max_0':'200'
        },
        'inputs':[{'name':'Start'},{'name':'End'},{'name':'Density','link':1 },{'name':'In 1'}],
        'outputs':[{'name':'List'},{'name':'TAG 1'}]
        }
        ],
        'links':[
        [1 ,1 ,0 ,100 ,2 ,'data']
        ]
        }
        engine =GraphEngine (graph )
        res_cabled =engine .evaluate_data_node (100 ,{'fx_dur':2000 ,'unit_i':1 },output_slot_index =0 )
        count_cabled =len (re .findall (r"\\t\(",res_cabled ))


        graph ['links']=[]
        graph ['nodes'][1 ]['inputs'][2 ]['link']=None 
        res_uncabled =engine .evaluate_data_node (100 ,{'fx_dur':2000 ,'unit_i':1 },output_slot_index =0 )
        count_uncabled =len (re .findall (r"\\t\(",res_uncabled ))

        self .assertGreater (count_cabled ,count_uncabled *2 ,f"Con cable Density 4.0 ({count_cabled }) debe generar significativamente más que con 0.1 ({count_uncabled })")

    def test_glitter_list_zip_mode_pairing (self ):
        """Verifica que la salida 'List' empareje todos los tags bajo un único \\t con valores aleatorios independientes respetando sus rangos."""
        from nodes .tag_nodes import glitter_node 
        res =glitter_node (
        None ,
        start_time ="100",
        end_time ="800",
        modo_oscilacion ="Destellos",
        tags =[r"\fscx",r"\fscy",r"\blur"],
        mins =["100","80","1"],
        maxs =["200","180","5"],
        output_slot_index =0 
        )

        t_blocks =re .findall (r"\\t\(([^)]+)\)",res )
        self .assertTrue (len (t_blocks )>0 ,"Debe generar bloques de transformación")

        for block in t_blocks :
            parts =block .split (",")
            t1 =int (parts [0 ])
            t2 =int (parts [1 ])
            body =parts [2 ]if len (parts )==3 else parts [3 ]


            self .assertGreaterEqual (t1 ,100 )
            self .assertLessEqual (t2 ,800 )


            self .assertIn (r"\fscx",body )
            self .assertIn (r"\fscy",body )
            self .assertIn (r"\blur",body )


            m_x =re .search (r"\\fscx(\d+)",body )
            m_y =re .search (r"\\fscy(\d+)",body )
            m_b =re .search (r"\\blur(\d+)",body )

            self .assertIsNotNone (m_x )
            self .assertIsNotNone (m_y )
            self .assertIsNotNone (m_b )

            val_x =int (m_x .group (1 ))
            val_y =int (m_y .group (1 ))
            val_b =int (m_b .group (1 ))


            self .assertTrue (100 <=val_x <=200 )
            self .assertTrue (80 <=val_y <=180 )
            self .assertTrue (1 <=val_b <=5 )

    def test_glitter_row_multi_tag_expansion (self ):
        """Verifica que si una fila contiene múltiples tags concatenados (p.ej. \\fscx\\fscy), se expandan y emparejen correctamente."""
        from nodes .tag_nodes import glitter_node 
        res =glitter_node (
        None ,
        start_time ="0",
        end_time ="500",
        modo_oscilacion ="Oleaje",
        tags =[r"\fscx\fscy"],
        mins =["100, 80"],
        maxs =["200, 180"],
        output_slot_index =0 
        )
        t_blocks =re .findall (r"\\t\(([^)]+)\)",res )
        self .assertTrue (len (t_blocks )>0 )
        for block in t_blocks :
            parts =block .split (",")
            body =parts [-1 ]
            self .assertIn (r"\fscx",body )
            self .assertIn (r"\fscy",body )

            self .assertIsNotNone (re .search (r"\\fscx\d+",body ))
            self .assertIsNotNone (re .search (r"\\fscy\d+",body ))

    def test_glitter_dark_tags_comodines (self ):
        """Verifica que Glitter acepte y expanda tags comodines (Dark Tags) como \\fscxy, \\13c y \\bs."""
        from nodes .tag_nodes import glitter_node 


        res_xy =glitter_node (None ,tag_0 =r"\fscxy",min_0 ="150",max_0 ="250",output_slot_index =0 )
        self .assertNotIn (r"\fscxy",res_xy ,"\\fscxy debe expandirse a tags ASS estándar")
        self .assertIn (r"\fscx",res_xy )
        self .assertIn (r"\fscy",res_xy )

        for m in re .finditer (r"\\fscx(\d+)\\fscy(\d+)",res_xy ):
            self .assertEqual (m .group (1 ),m .group (2 ),"Ambos ejes deben compartir exactamente el mismo valor de escala con \\fscxy")


        res_13c =glitter_node (None ,tag_0 =r"\13c",min_0 ="&HFFFFFF&",max_0 ="&H0000FF&",output_slot_index =0 )
        self .assertNotIn (r"\13c",res_13c )
        self .assertIn (r"\1c",res_13c )
        self .assertIn (r"\3c",res_13c )
        for m in re .finditer (r"\\1c(&H[0-9a-fA-F]+&)\\3c(&H[0-9a-fA-F]+&)",res_13c ):
            self .assertEqual (m .group (1 ),m .group (2 ),"Ambos colores deben compartir el mismo valor con \\13c")


        res_bs =glitter_node (None ,tag_0 =r"\bs",min_0 ="1",max_0 ="5",output_slot_index =0 )
        self .assertNotIn (r"\bs",res_bs )
        self .assertIn (r"\bord",res_bs )
        self .assertIn (r"\shad",res_bs )
        for m in re .finditer (r"\\bord(\d+)\\shad(\d+)",res_bs ):
            self .assertEqual (m .group (1 ),m .group (2 ),"Borde y sombra deben compartir el mismo valor con \\bs")


if __name__ =='__main__':
    unittest .main ()






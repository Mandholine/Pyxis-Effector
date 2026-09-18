import unittest 
from font_vector_engine import FontVectorEngine 
from models import StyleRef ,PyxisLine ,PyxisUnit 

class TestFontVectorEngineCanonical (unittest .TestCase ):
    def setUp (self ):
        FontVectorEngine .clear_cache ()

    def test_extract_font_params_from_styleref_object (self ):
        style =StyleRef ({
        "Fontname":"Trebuchet MS",
        "Fontsize":75 ,
        "Bold":True ,
        "Italic":False ,
        "ScaleX":110.0 ,
        "ScaleY":90.0 
        })
        line =PyxisLine ()
        line .styleref =style 
        line .text_stripped ="Hola"

        params =FontVectorEngine .extract_font_params (context ={"active_line":line })
        self .assertEqual (params ["text"],"Hola")
        self .assertEqual (params ["font_name"],"Trebuchet MS")
        self .assertEqual (params ["font_size"],75.0 )
        self .assertTrue (params ["bold"])
        self .assertFalse (params ["italic"])
        self .assertEqual (params ["scale_x"],110.0 )
        self .assertEqual (params ["scale_y"],90.0 )

    def test_extract_font_params_from_styleref_dict (self ):
        style_dict ={
        "Fontname":"Impact",
        "Fontsize":55 ,
        "Bold":False ,
        "Italic":True ,
        "ScaleX":120.0 ,
        "ScaleY":80.0 
        }
        ctx ={"styleref":style_dict }
        params =FontVectorEngine .extract_font_params (text ="Test",context =ctx )
        self .assertEqual (params ["text"],"Test")
        self .assertEqual (params ["font_name"],"Impact")
        self .assertEqual (params ["font_size"],55.0 )
        self .assertFalse (params ["bold"])
        self .assertTrue (params ["italic"])
        self .assertEqual (params ["scale_x"],120.0 )
        self .assertEqual (params ["scale_y"],80.0 )

    def test_extract_font_params_ass_inline_tags_override (self ):
        style =StyleRef ({"Fontname":"Arial","Fontsize":40 })
        line =PyxisLine ()
        line .styleref =style 
        line .text =r"{\fnGeorgia\fs60\fscx150\fscy75\b1\i1}Especial"
        line .text_stripped ="Especial"

        params =FontVectorEngine .extract_font_params (context ={"active_line":line })
        self .assertEqual (params ["text"],"Especial")
        self .assertEqual (params ["font_name"],"Georgia")
        self .assertEqual (params ["font_size"],60.0 )
        self .assertTrue (params ["bold"])
        self .assertTrue (params ["italic"])
        self .assertEqual (params ["scale_x"],150.0 )
        self .assertEqual (params ["scale_y"],75.0 )

    def test_extract_font_params_explicit_arguments_priority (self ):
        style =StyleRef ({"Fontname":"Arial","Fontsize":40 })
        line =PyxisLine ()
        line .styleref =style 
        line .text_stripped ="Base"

        params =FontVectorEngine .extract_font_params (
        text ="Explicit",
        context ={"active_line":line },
        font_name ="Verdana",
        font_size =90 ,
        bold =True ,
        scale_x =130.0 
        )
        self .assertEqual (params ["text"],"Explicit")
        self .assertEqual (params ["font_name"],"Verdana")
        self .assertEqual (params ["font_size"],90.0 )
        self .assertTrue (params ["bold"])
        self .assertEqual (params ["scale_x"],130.0 )

    def test_from_context_generation_and_caching (self ):
        style =StyleRef ({"Fontname":"Arial","Fontsize":50 })
        line =PyxisLine ()
        line .styleref =style 
        line .text_stripped ="M"


        shp1 =FontVectorEngine .from_context (context ={"active_line":line })
        self .assertTrue (shp1 .startswith ("m ")or shp1 .startswith ("m-")or shp1 .startswith ("m0"))
        self .assertGreater (FontVectorEngine .get_cache_size (),0 )


        cached_count =FontVectorEngine .get_cache_size ()
        shp2 =FontVectorEngine .from_context (context ={"active_line":line })
        self .assertEqual (shp1 ,shp2 )
        self .assertEqual (FontVectorEngine .get_cache_size (),cached_count )


        FontVectorEngine .clear_cache ()
        self .assertEqual (FontVectorEngine .get_cache_size (),0 )

    def test_lru_cache_eviction (self ):

        orig_limit =FontVectorEngine .MAX_CACHE_SIZE 
        try :
            FontVectorEngine .MAX_CACHE_SIZE =5 
            for i in range (10 ):
                FontVectorEngine .text_to_shape (f"Char_{i }",font_name ="Arial",font_size =20 )
            self .assertEqual (FontVectorEngine .get_cache_size (),5 )
        finally :
            FontVectorEngine .MAX_CACHE_SIZE =orig_limit 
            FontVectorEngine .clear_cache ()

    def test_resolve_shape_value_integration_with_text (self ):
        from nodes .shape_nodes import resolve_shape_value 
        style =StyleRef ({"Fontname":"Arial","Fontsize":40 })
        line =PyxisLine ()
        line .styleref =style 
        line .text_stripped ="Hello"
        ctx ={"active_line":line }


        shape =resolve_shape_value ("Hello",ctx )
        self .assertTrue (shape .startswith ("m ")or shape .startswith ("m-")or shape .startswith ("m0"))


        circle_shape =resolve_shape_value ("circle",ctx )
        self .assertTrue (circle_shape .startswith ("m "))

    def test_font_vector_engine_grid_advance_fidelity(self):
        shape = FontVectorEngine.text_to_shape("Mary tenia un corderito", font_name="Arial", font_size=65.0)
        self.assertTrue(shape.startswith("m ") or shape.startswith("m-"))
        tokens = shape.split()
        xs = [float(tokens[i]) for i in range(1, len(tokens)) if tokens[i-1] in ("m", "l")]
        self.assertLess(max(xs), 273.0)

    def test_font_vector_engine_glyph_symmetry(self):
        shape = FontVectorEngine.text_to_shape("asa", font_name="Arial", font_size=50.0)
        self.assertTrue(shape.startswith("m ") or shape.startswith("m-"))
        tokens = shape.split()
        xs = [float(tokens[i]) for i in range(1, len(tokens)) if tokens[i-1] in ("m", "l")]
        # Shape should be centered symmetrically around 0.0
        self.assertAlmostEqual(min(xs) + max(xs), 0.0, delta=2.0)

if __name__ =="__main__":
    unittest .main ()



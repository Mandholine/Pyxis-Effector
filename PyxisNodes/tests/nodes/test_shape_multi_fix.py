# Pyxis Effector - Plugin for Aegisub
import unittest 
from node_engine import GraphEngine 

class TestShapeMultiFix (unittest .TestCase ):
    def test_shape_multi_wire_input_tunnel_mode (self ):
        star_node ={
        "id":1 ,
        "type":"Library",
        "properties":{"forma":"Estrella"}
        }
        multi_node ={
        "id":2 ,
        "type":"Shape/Multi",
        "properties":{
        "mode":"Túnel / Cascada",
        "size1":"100.0",
        "size2":"10.0",
        "loop":"4"
        },
        "inputs":[{"name":"Forma Base","link":100 }]
        }
        link =[100 ,1 ,0 ,2 ,0 ,"shape"]

        engine =GraphEngine ({"nodes":[star_node ,multi_node ],"links":[link ]})
        res =engine .evaluate_data_node (2 ,context ={})
        self .assertTrue (isinstance (res ,str ))
        self .assertTrue (res .startswith ("m"))

        self .assertIn ("47.5",res )

    def test_shape_multi_wire_input_concentric_rings_mode (self ):
        star_node ={
        "id":1 ,
        "type":"Library",
        "properties":{"forma":"Estrella"}
        }
        multi_node ={
        "id":2 ,
        "type":"Shape/Multi",
        "properties":{
        "mode":"Anillos Concéntricos",
        "size":"100.0",
        "bord":"4"
        },
        "inputs":[{"name":"Forma Base","link":101 }]
        }
        link =[101 ,1 ,0 ,2 ,0 ,"shape"]

        engine = GraphEngine({"nodes": [star_node, multi_node], "links": [link]})
        res = engine.evaluate_data_node(2, context={})
        self.assertTrue(isinstance(res, str))
        self.assertTrue(res.startswith("m"))
        self.assertIn("47.5", res)

    def test_shape_multi_text_concentric_rings(self):
        from font_vector_engine import FontVectorEngine
        txt_shape = FontVectorEngine.text_to_shape("Test", "Arial", 40.0)
        from nodes.shape_nodes import shape_multi
        res = shape_multi(None, drawing=txt_shape, mode="Anillos Concéntricos", size=100.0, bord=4.0, separation=1.0)
        self.assertTrue(isinstance(res, str))
        self.assertTrue(res.startswith("m "))
        self.assertGreater(len(res), 500)


if __name__ == "__main__":
    unittest.main()

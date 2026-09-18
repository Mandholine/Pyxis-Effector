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

"""Pruebas unitarias para nodos del sistema (Sys Var, Code Node, Dynamic Nodes y Registro)."""

import unittest 
from decorators import NODE_REGISTRY 
from models import PyxisLine ,PyxisUnit ,StyleRef 
from node_engine import GraphEngine ,_eval_sys_var 
from nodes .code_nodes import execute_python_script ,execute_lua_script ,code_script_master 


class TestSysVarEval (unittest .TestCase ):
    """Pruebas del evaluador de variables de sistema (Sys Var)."""

    def setUp (self ):
        self .engine =GraphEngine ({"nodes":[],"links":[]})
        self .line =PyxisLine ()
        self .line .text_stripped ="Karaoke Test Line"
        self .line .raw_text =r"{\k50}Karaoke Test Line"
        self .line .start_time =1000 
        self .line .end_time =5000 
        self .line .duration =4000 
        self .line .style_name ="TitleStyle"

        style_dict ={
        "Fontname":"Trebuchet MS",
        "Fontsize":"48",
        "PrimaryColour":"&H0000FFFF&",
        "SecondaryColour":"&H000000FF&",
        "OutlineColour":"&H00000000&",
        "BackColour":"&H00000000&",
        "Outline":"3.5",
        "Shadow":"1.5"
        }
        self .line .styleref =StyleRef (style_dict )

        self .syl =PyxisUnit ()
        self .syl .text_stripped ="Ka"
        self .syl .start_time =1000 
        self .syl .end_time =1500 
        self .syl .duration =500 
        self .syl .i =1 
        self .syl .n =5 
        self .syl .x =240.0 
        self .syl .y =360.0 
        self .syl .line =self .line 

        self .context ={
        "active_unit":self .syl ,
        "syl":self .syl ,
        "active_line":self .line ,
        "line":self .line ,
        "start_time":1000 ,
        "end_time":1500 ,
        "duration":500 ,
        "fx_start_time":1050 ,
        "fx_end_time":1450 ,
        "fx_dur":400 ,
        "fx_pos_x":245.5 ,
        "fx_pos_y":365.2 ,
        "i":1 ,
        "n":5 
        }

    def test_syl_variables (self ):
        self .assertEqual (_eval_sys_var ("syl.i",self .context ),1 )
        self .assertEqual (_eval_sys_var ("syl.n",self .context ),5 )
        self .assertEqual (_eval_sys_var ("syl.dur",self .context ),500 )
        self .assertEqual (_eval_sys_var ("syl.text",self .context ),"Ka")

    def test_line_variables (self ):
        self .assertEqual (_eval_sys_var ("line.duration",self .context ),4000 )
        self .assertEqual (_eval_sys_var ("line.style",self .context ),"TitleStyle")

    def test_fx_variables (self ):
        self .assertEqual (_eval_sys_var ("fx.dur",self .context ),400 )
        self .assertEqual (_eval_sys_var ("fx.pos_x",self .context ),245.5 )


class TestCodeNodes (unittest .TestCase ):
    """Pruebas de ejecucion de scripts Python embebidos en el nodo Code."""

    def setUp (self ):
        self .context ={
        "syl":type ("Syl",(),{
        "i":1 ,
        "n":2 ,
        "text":"World",
        "text_stripped":"World",
        "duration":500 ,
        "dur":500 ,
        "start_time":0 ,
        "end_time":500 ,
        "x":100.0 ,
        "y":200.0 ,
        "center":100.0 ,
        "middle":200.0 
        })(),
        "line":type ("Line",(),{
        "layer":0 ,
        "style_name":"Default",
        "text":"Hello World"
        })(),
        "rx":1280 ,
        "ry":720 ,
        "fd":41.708 
        }

    def test_python_script_execution_basic (self ):
        script ="result = 'Hello ' + syl.text"
        res =execute_python_script (self .context ,script ,{})
        self .assertEqual (res ,"Hello World")

    def test_python_print_and_single_expressions (self ):
        res_print =execute_python_script (self .context ,"print(syl.i)",{})
        self .assertEqual (res_print ,"")

        res_expr =execute_python_script (self .context ,"syl.x * 2",{})
        self .assertEqual (float (res_expr ),200.0 )


class TestGhostNodeRegistry (unittest .TestCase ):
    """Pruebas de integridad del registro global de nodos."""

    def test_registry_populated (self ):
        self .assertGreater (len (NODE_REGISTRY ),20 )

    def test_essential_categories_present (self ):
        categories ={k .split ("/")[0 ]for k in NODE_REGISTRY .keys ()if "/"in k }
        for cat in ["Shape","Text","Time","Functions","Variables"]:
            self .assertIn (cat ,categories ,f"Categoria '{cat }' no encontrada en el registro")


class TestOutputNodeLayer(unittest.TestCase):
    """Pruebas para el manejo de capa (layer) en el nodo Output (Salida)."""

    def test_output_layer_unspecified_defaults_to_zero(self):
        """Cuando no se conecta o especifica un número de capa, Output siempre debe generar layer 0."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"base_unit": "line"}},
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 101},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": 102}
                    ]
                },
                {"id": 3, "type": "Text", "properties": {"text": "Output text"}}
            ],
            "links": [
                [101, 1, 0, 2, 0, "loop"],
                [102, 3, 0, 2, 5, "data"]
            ]
        }
        dialogues = [
            {"raw": "Dialogue: 5,0:00:01.00,0:00:03.00,Default,,0,0,0,,Line on layer 5", "is_selected": True},
            {"raw": "Dialogue: 12,0:00:04.00,0:00:06.00,Default,,0,0,0,,Line on layer 12", "is_selected": True}
        ]
        styles = {"Default": {}}
        engine = GraphEngine(graph)
        res = engine.process_single(dialogues, styles)
        self.assertEqual(len(res), 2)
        for line in res:
            self.assertEqual(line["layer"], 0, f"Expected layer 0 when unspecified, got {line['layer']}")

    def test_output_layer_specified_numeric(self):
        """Cuando se especifica un número de capa mediante un nodo, Output debe respetar dicho valor."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"base_unit": "line"}},
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 101},
                        {"name": "Layer", "link": 103},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": 102}
                    ]
                },
                {"id": 3, "type": "Text", "properties": {"text": "Output text"}},
                {"id": 4, "type": "Math", "properties": {"A": 7, "B": 0, "category": "Basic", "operation": "Add"}, "outputs": [{"name": "Out", "type": "data"}]}
            ],
            "links": [
                [101, 1, 0, 2, 0, "loop"],
                [102, 3, 0, 2, 5, "data"],
                [103, 4, 0, 2, 1, "data"]
            ]
        }
        dialogues = [{"raw": "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Line", "is_selected": True}]
        styles = {"Default": {}}
        engine = GraphEngine(graph)
        res = engine.process_single(dialogues, styles)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["layer"], 7)


class TestSystemNodesSuite(unittest.TestCase):
    """Pruebas unitarias completas para los 4 nodos canónicos de System."""

    def test_system_nodes_registered(self):
        """Verificar que los 4 nodos de System estén presentes en SYSTEM_NODE_DB con firma canónica."""
        from decorators import SYSTEM_NODE_DB
        self.assertIn("System", SYSTEM_NODE_DB, "Categoría 'System' no encontrada en SYSTEM_NODE_DB")
        expected_nodes = [
            "Output",
            "Previewer",
            "Script Code",
            "Benchmark Math"
        ]
        for node_name in expected_nodes:
            self.assertIn(node_name, SYSTEM_NODE_DB["System"], f"Nodo {node_name} no registrado en SYSTEM_NODE_DB['System']")

    def test_script_code_master_dispatch(self):
        """Probar el despacho de script_code_master con lenguaje Python."""
        ctx = {"syl": type("Syl", (), {"text": "Alpha"})()}
        res = code_script_master(ctx, script="result = 'Test ' + syl.text", language="Python")
        self.assertEqual(res, "Test Alpha")

        res_in = code_script_master(ctx, script="result = 'In: ' + str(in1)", language="Python", in1="Beta")
        self.assertEqual(res_in, "In: Beta")

    def test_benchmark_math_node_execution(self):
        """Probar la ejecución de Benchmark Math en GraphEngine."""
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "System/Benchmark Math",
                    "properties": {"iterations": "100", "complexity": "Heavy Math (Trig + Sqrt)"},
                    "inputs": [{"name": "Iterations", "link": None}]
                }
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        ctx = {}
        out_val = engine.evaluate_data_node(1, ctx, output_slot_index=0)
        time_ms = engine.evaluate_data_node(1, ctx, output_slot_index=1)
        self.assertTrue(str(out_val).startswith("[Bench:") or float(time_ms) >= 0.0)
        self.assertGreaterEqual(float(time_ms), 0.0)

    def test_script_code_in_graph_loop(self):
        """Probar nodo Script Code insertado en la cadena de bucle de Output."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"base_unit": "line"}},
                {
                    "id": 2,
                    "type": "System/Script Code",
                    "properties": {
                        "language": "Python",
                        "script": "result = '\\\\an7'"
                    },
                    "inputs": [
                        {"name": "Loop In", "link": 101},
                        {"name": "In1", "link": None},
                        {"name": "In2", "link": None}
                    ]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 102},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Return", "link": 103}
                    ]
                },
                {"id": 4, "type": "Text", "properties": {"text": "Scripted Line"}}
            ],
            "links": [
                [101, 1, 0, 2, 0, "loop"],
                [102, 2, 0, 3, 0, "loop"],
                [103, 4, 0, 3, 5, "data"]
            ]
        }
        dialogues = [{"raw": "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Line", "is_selected": True}]
        styles = {"Default": {}}
        engine = GraphEngine(graph)
        res = engine.process_single(dialogues, styles)
        self.assertEqual(len(res), 1)
        self.assertIn(r"\an7", res[0]["text"])


if __name__ == "__main__":
    unittest.main()


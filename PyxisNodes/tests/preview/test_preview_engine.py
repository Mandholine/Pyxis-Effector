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

"""Pruebas unitarias para el motor de previsualizacion en tiempo real y conexion con nodos Salida."""

import os
import sys
import unittest

if not sys.argv or not os.path.exists(sys.argv[0]):
    sys.argv = [os.path.abspath(__file__)]

from node_engine import GraphEngine 


class TestPreviewSinglePort (unittest .TestCase ):
    """Pruebas de generacion de preview y resolucion de puertos de salida."""

    def setUp (self ):
        self .dialogues =[{
        'raw':r"Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\k50}Test{\k50}Line",
        'metrics':{'h':20.0 ,'d':5.0 ,'e':0.0 ,'sel':True ,'w':[40.0 ,40.0 ]}
        }]
        self .styles ={
        "Default":{
        "Fontname":"Arial","Fontsize":40.0 ,
        "PrimaryColour":"&H00FFFFFF&","SecondaryColour":"&H000000FF&",
        "OutlineColour":"&H00000000&","BackColour":"&H00000000&",
        "ScaleX":100.0 ,"ScaleY":100.0 ,"Spacing":0.0 ,"Outline":2.0 ,
        "Shadow":0.0 ,"Alignment":5 
        }
        }

    def test_default_output_id_matching (self ):
        graph_data ={
        "nodes":[
        {
        "id":1 ,
        "type":"Loops/Main Loop",
        "properties":{"iterador":"syl"},
        "outputs":[{"name":"Loop","type":"bucle","links":[101 ]}]
        },
        {
        "id":2 ,
        "type":"System/Output",
        "properties":{"apply_to":"All Lines"},
        "inputs":[
        {"name":"Loop / Domain","type":"bucle","link":101 },
        {"name":"Layer","type":"data","link":None },
        {"name":"Start Time","type":"data","link":None },
        {"name":"End Time","type":"data","link":None },
        {"name":"Tags","type":"data","link":None },
        {"name":"Return","type":"data","link":None },
        {"name":"Queue ID","type":"data","link":None },
        {"name":"Queue Order","type":"data","link":None }
        ],
        "outputs":[]
        }
        ],
        "links":[
        [101 ,1 ,0 ,2 ,0 ,"bucle"]
        ]
        }
        engine =GraphEngine (graph_data )
        engine .process_single (self .dialogues ,self .styles ,allow_fallback_select_all =True )
        self .assertGreaterEqual (len (engine .all_generated_lines ),1 )

    def test_cleanup_sliding_window (self ):
        """Verifica que cleanup_temp_files no elimine archivos accedidos recientemente."""
        import os, tempfile, time
        from main import PyxisAPI
        
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        bg_media_dir = os.path.join(appdata_dir, "PyxisNodes", "bg_media")
        os.makedirs(bg_media_dir, exist_ok=True)
        
        test_file = os.path.join(bg_media_dir, "preview_bg_dummy_test_sliding_window.mp4")
        with open(test_file, "wb") as f:
            f.write(b"dummy mp4 data header ftyp moov testing")
        
        try:
            # Simular que el archivo tiene mtime de hace 100 horas pero atime de ahora
            old_time = time.time() - (100 * 3600)
            now_time = time.time()
            os.utime(test_file, (now_time, old_time))
            
            # Correr limpieza con max_age_hours=72
            res = PyxisAPI.cleanup_temp_files(max_age_hours=72, force_all=False)
            
            # El archivo NO debe haber sido eliminado porque atime es reciente
            self.assertTrue(os.path.exists(test_file))
        finally:
            if os.path.exists(test_file):
                try: os.remove(test_file)
                except Exception: pass

    def test_detect_best_h264_encoder(self):
        """Verifica que la detección dinámica de encoder H264 retorne un codec y flags válidos."""
        from main import PyxisAPI
        enc_name, enc_args = PyxisAPI._detect_best_h264_encoder()
        self.assertIn(enc_name, ("h264_nvenc", "h264_amf", "h264_qsv", "libx264"))
        self.assertIsInstance(enc_args, list)
        self.assertIn("-c:v", enc_args)
        self.assertIn(enc_name, enc_args)

    def test_preview_empty_target_outputs_reverts_to_base(self):
        """Verifica que si target_output_id es una lista vacia, no se generen efectos y se preserve el subtitulo base."""
        from main import PyxisAPI
        api = PyxisAPI("dummy_temp.ass", "dummy_res.txt", "dummy_session.json")
        
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterator": "syl"},
                    "outputs": [{"name": "Loop", "type": "bucle", "links": [101]}]
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 101},
                        {"name": "Layer", "type": "data", "link": None},
                        {"name": "Start Time", "type": "data", "link": None},
                        {"name": "End Time", "type": "data", "link": None},
                        {"name": "Tags", "type": "data", "link": None},
                        {"name": "Return", "type": "data", "link": None},
                        {"name": "Queue ID", "type": "data", "link": None},
                        {"name": "Queue Order", "type": "data", "link": None}
                    ],
                    "outputs": []
                }
            ],
            "links": [
                [101, 1, 0, 2, 0, "bucle"]
            ]
        }
        
        # Con target_output_id = [] (sin salidas conectadas ni nombradas)
        res = api.generate_preview_ass(graph_data, target_output_id=[])
        self.assertTrue(res.get("success"))
        content = res.get("content", "")
        # Debe contener Dialogue: (el subtítulo base no comentado)
        self.assertIn("Dialogue:", content)
        # No debe haber comentarios de reemplazo ni efectos de nodos
        comment_count = sum(1 for line in content.splitlines() if line.startswith("Comment:") and "PyxisMetrics" not in line)
        self.assertEqual(comment_count, 0)

    def test_preview_target_output_isolation(self):
        """Verifica que preview no aplique más salidas que las explícitamente conectadas/nombradas."""
        from main import PyxisAPI
        api = PyxisAPI("dummy_temp.ass", "dummy_res.txt", "dummy_session.json")
        
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterator": "syl"},
                    "outputs": [{"name": "Loop", "type": "bucle", "links": [101, 102]}]
                },
                {
                    "id": 10,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines", "output_id": "out_active"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 101},
                        {"name": "Layer", "type": "data", "link": None},
                        {"name": "Start Time", "type": "data", "link": None},
                        {"name": "End Time", "type": "data", "link": None},
                        {"name": "Tags", "type": "data", "link": None},
                        {"name": "Return", "type": "data", "link": None},
                        {"name": "Queue ID", "type": "data", "link": None},
                        {"name": "Queue Order", "type": "data", "link": None}
                    ],
                    "outputs": []
                },
                {
                    "id": 20,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines", "output_id": "out_unconnected"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 102},
                        {"name": "Layer", "type": "data", "link": None},
                        {"name": "Start Time", "type": "data", "link": None},
                        {"name": "End Time", "type": "data", "link": None},
                        {"name": "Tags", "type": "data", "link": None},
                        {"name": "Return", "type": "data", "link": None},
                        {"name": "Queue ID", "type": "data", "link": None},
                        {"name": "Queue Order", "type": "data", "link": None}
                    ],
                    "outputs": []
                }
            ],
            "links": [
                [101, 1, 0, 10, 0, "bucle"],
                [102, 1, 0, 20, 0, "bucle"]
            ]
        }
        
        all_output_nodes = [n for n in graph_data["nodes"] if n["id"] in (10, 20)]
        
        # Test unitario directo de _matches_output_node
        self.assertFalse(api._matches_output_node(all_output_nodes[0], []))
        self.assertTrue(api._matches_output_node(all_output_nodes[0], ["10"]))
        self.assertFalse(api._matches_output_node(all_output_nodes[1], ["10"]))
        self.assertTrue(api._matches_output_node(all_output_nodes[1], ["out_unconnected"]))
        self.assertFalse(api._matches_output_node(all_output_nodes[0], ["out_unconnected"]))


if __name__ =="__main__":
    unittest.main()


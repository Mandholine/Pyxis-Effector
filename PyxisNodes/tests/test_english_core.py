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

# -*- coding: utf-8 -*-
"""
Prueba unitaria para certificar la integridad del núcleo 100% en inglés en Pyxis Effector.
Verifica que las categorías, nombres de nodos, slots y pipelines operen limpiamente en inglés.
"""

import unittest
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

import nodes_library
from decorators import SYSTEM_NODE_DB, PYXIS_DB
from node_engine import GraphEngine
from models import PyxisLine, PyxisUnit


class TestEnglishCore(unittest.TestCase):
    def setUp(self):
        self.sample_line = PyxisLine()
        self.sample_line.layer = 0
        self.sample_line.start_time = 0
        self.sample_line.end_time = 2000
        self.sample_line.style_name = "Default"
        self.sample_line.text = "Pyxis English Core"
        self.sample_line.is_selected = True

        self.sample_syl = PyxisUnit()
        self.sample_syl.text = "English"
        self.sample_syl.text_stripped = "English"
        self.sample_syl.duration = 1000
        self.sample_syl.dur = 1000
        self.sample_syl.start_time = 0
        self.sample_syl.end_time = 1000
        self.sample_syl.i = 1
        self.sample_syl.n = 1
        self.sample_syl.center = 640.0
        self.sample_syl.middle = 360.0
        self.sample_line.syls = [self.sample_syl]

    def test_categories_are_in_english(self):
        """Verifica que las categorías registradas sean 100% en inglés."""
        valid_categories = {"Loops", "Variables", "System", "Functions", "Shape", "Time", "Audio", ""}
        # Categorías en español que no deben existir
        spanish_categories = ["Bucles", "Sistema", "Func"]

        for category, node_dict in SYSTEM_NODE_DB.items():
            self.assertNotIn(
                category,
                spanish_categories,
                f"Categoría '{category}' sigue en español en SYSTEM_NODE_DB"
            )
            self.assertIn(
                category,
                valid_categories,
                f"Categoría desconocida '{category}' en SYSTEM_NODE_DB"
            )

    def test_essential_nodes_registered_in_english(self):
        """Verifica que los nodos esenciales existan con sus identificadores en inglés."""
        essential_nodes = [
            ("Loops", "Main Loop"),
            ("Loops", "MaxLoop"),
            ("Loops", "Module"),
            ("Variables", "Define Vars"),
            ("Variables", "Get Var"),
            ("Variables", "Memory"),
            ("System", "Output"),
            ("System", "Previewer"),
            ("System", "Benchmark Math"),
            ("Functions", "Interpolator"),
            ("Functions", "Conditioner"),
            ("Functions", "Bezier Curve"),
            ("Functions", "Color Gradient"),
            ("Functions", "Particles"),
            ("Functions", "Polar to Cartesian"),
            ("Functions", "Tag Oscillator"),
            ("Shape", "Shapes Library"),
            ("Shape", "Shape Slicer"),
            ("Shape", "Shape Transform"),
            ("Shape", "Concentric Borders"),
            ("Time", "Time Ipol"),
            ("Time", "Synced Time"),
            ("Audio", "Audio Modulator"),
            ("Audio", "Audio Waveform"),
            ("", "Number"),
            ("", "Concatenate"),
            ("", "Dynamic Format")
        ]
        for cat, name in essential_nodes:
            self.assertIn(cat, SYSTEM_NODE_DB, f"Categoría '{cat}' no encontrada en SYSTEM_NODE_DB")
            self.assertIn(name, SYSTEM_NODE_DB[cat], f"Nodo '{name}' no encontrado en categoría '{cat}'")

    def test_slots_are_in_english(self):
        """Verifica que los slots de los nodos principales no conserven nombres en español."""
        # Slots en español que no deben aparecer
        spanish_slots = [
            "Bucle", "Bucle In", "Bucle Out", "Bucle / Dominio",
            "Iterador (i)", "Iterador (j)", "Vueltas (N)",
            "Flujo In", "Flujo Out", "Resultado", "Salida", "Dato", "Valor",
            "Duración (ms)", "Puntos / Valores", "Aceleración", "Inicio", "Fin"
        ]
        for cat, node_dict in SYSTEM_NODE_DB.items():
            for node_name, defn in node_dict.items():
                inputs = defn.get("inputs", [])
                outputs = defn.get("outputs", [])
                for inp in inputs:
                    self.assertNotIn(
                        inp,
                        spanish_slots,
                        f"En nodo '{cat}/{node_name}', input slot '{inp}' sigue en español"
                    )
                for out in outputs:
                    self.assertNotIn(
                        out,
                        spanish_slots,
                        f"En nodo '{cat}/{node_name}', output slot '{out}' sigue en español"
                    )

    def test_english_pipeline_execution(self):
        """Ejecuta un grafo puro en inglés: Loops/Main Loop -> Variables/Define Vars -> System/Output."""
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl", "noblank": "No Blank"},
                    "outputs": [{"name": "Loop", "type": "bucle", "links": [101]}]
                },
                {
                    "id": 2,
                    "type": "Variables/Define Vars",
                    "properties": {"variables": "pos_x = 640\npos_y = 360"},
                    "inputs": [{"name": "In", "type": "data", "link": 101}],
                    "outputs": [{"name": "Out", "type": "data", "links": [103]}]
                },
                {
                    "id": 3,
                    "type": "MultiTag",
                    "properties": {"tag_type": "pos", "x": "pos_x", "y": "pos_y"},
                    "outputs": [{"name": "String", "type": "data", "links": [102]}]
                },
                {
                    "id": 4,
                    "type": "System/Output",
                    "properties": {"apply_to": "Sel. Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "type": "bucle", "link": 103},
                        {"name": "Layer", "type": "data", "link": None},
                        {"name": "Start Time", "type": "data", "link": None},
                        {"name": "End Time", "type": "data", "link": None},
                        {"name": "Tags", "type": "data", "link": 102},
                        {"name": "Return", "type": "data", "link": None}
                    ],
                    "outputs": []
                }
            ],
            "links": [
                [101, 1, 0, 2, 0, "bucle"],
                [102, 3, 0, 4, 4, "data"],
                [103, 2, 0, 4, 0, "bucle"]
            ]
        }

        engine = GraphEngine(graph_data)
        dialogues = [{"raw": "Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,{\\k100}English", "metrics": {"sel": True}}]
        styles = {"Default": {"Fontname": "Arial", "Fontsize": "20"}}

        lines = engine.process(dialogues, styles)
        self.assertEqual(len(lines), 1)
        self.assertIn(r"\pos(640,360)", lines[0])
        self.assertIn("English", lines[0])


if __name__ == "__main__":
    unittest.main()

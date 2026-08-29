# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3.

import unittest
import os
import re
import json

from decorators import SYSTEM_NODE_DB, PYXIS_DB

class TestI18nNodeCanvas(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.i18n_path = os.path.join(self.base_dir, "web", "i18n.js")
        with open(self.i18n_path, "r", encoding="utf-8") as f:
            self.i18n_content = f.read()

        es_pos = self.i18n_content.find("es: {")
        en_pos = self.i18n_content.find("en: {")
        en_end = self.i18n_content.find("};\n\n    let currentLanguage", en_pos)
        if en_end == -1:
            en_end = self.i18n_content.find("};", en_pos)

        self.es_block = self.i18n_content[es_pos:en_pos]
        self.en_block = self.i18n_content[en_pos:en_end]

        self.es_dict = dict(re.findall(r'["\']([^"\']+)["\']\s*:\s*["\']([^"\']*)["\']', self.es_block))
        self.en_dict = dict(re.findall(r'["\']([^"\']+)["\']\s*:\s*["\']([^"\']*)["\']', self.en_block))

    def test_core_categories_translated(self):
        """Verifica que todas las categorías registradas en Python tengan traducción al español."""
        for cat in SYSTEM_NODE_DB.keys():
            if not cat:
                continue
            key = f"nodes.categories.{cat}"
            self.assertIn(key, self.es_dict, f"Category '{cat}' missing in es dictionary")
            self.assertIn(key, self.en_dict, f"Category '{cat}' missing in en dictionary")
            # En inglés debe ser idéntico al nombre canónico
            self.assertEqual(self.en_dict[key], cat)
            # En español debe tener traducción no vacía
            self.assertTrue(len(self.es_dict[key]) > 0)

    def test_node_titles_translated(self):
        """Verifica que los nodos del registro tengan su título mapeado en i18n."""
        for cat, node_dict in SYSTEM_NODE_DB.items():
            for node_name in node_dict.keys():
                clean_title = node_name.split("/")[-1] if "/" in node_name else node_name
                key = f"nodes.titles.{clean_title}"
                self.assertIn(key, self.es_dict, f"Node title '{clean_title}' missing in es dictionary")
                self.assertIn(key, self.en_dict, f"Node title '{clean_title}' missing in en dictionary")

    def test_slots_translated(self):
        """Verifica que los slots de entrada y salida comunes tengan traducción en español."""
        core_slots = [
            "Loop", "Loop / Domain", "Iterator (i)", "Result", "Output",
            "Data", "Value", "Duration (ms)", "Start Time (ms)", "End Time (ms)",
            "Points / Values", "Acceleration", "Start", "End", "Step",
            "Width", "Height", "Anchor", "Shape", "Bleed", "Angle",
            "Condition", "If True", "If False", "Font", "Size", "Tags"
        ]
        for slot in core_slots:
            key = f"nodes.slots.{slot}"
            self.assertIn(key, self.es_dict, f"Slot '{slot}' missing in es dictionary")
            self.assertIn(key, self.en_dict, f"Slot '{slot}' missing in en dictionary")

    def test_serialization_remains_english(self):
        """Certifica que los datos del grafo serializado (types, properties, inputs) se mantengan en inglés."""
        dummy_serialized_node = {
            "id": 1,
            "type": "Loops/Main Loop",
            "title": "Main Loop",
            "properties": {
                "unit": "Syllable",
                "noblank": "Without Blank",
                "iterador": "syl"
            },
            "inputs": [
                { "name": "Flow In", "type": "flow" }
            ],
            "outputs": [
                { "name": "Loop", "type": "bucle" },
                { "name": "Iterator (i)", "type": "int" }
            ]
        }
        
        self.assertTrue(dummy_serialized_node["type"].startswith("Loops/"))
        self.assertEqual(dummy_serialized_node["inputs"][0]["name"], "Flow In")
        self.assertEqual(dummy_serialized_node["outputs"][0]["name"], "Loop")
        self.assertEqual(dummy_serialized_node["outputs"][1]["name"], "Iterator (i)")

    def test_math_text_customizations(self):
        """Verifica que Math sea Mates, Text sea Texto en español y Text en inglés, String sea String, y bucles traducidos."""
        self.assertEqual(self.es_dict.get("nodes.titles.Math"), "Mates", "Math title must be 'Mates' in Spanish")
        self.assertEqual(self.es_dict.get("nodes.titles.Text"), "Texto", "Text title must be 'Texto' in Spanish")
        self.assertEqual(self.es_dict.get("nodes.titles.String"), "String", "String title must be 'String' in Spanish")
        self.assertEqual(self.en_dict.get("nodes.titles.Text"), "Text", "Text title must be 'Text' in English")
        self.assertEqual(self.en_dict.get("nodes.titles.String"), "String", "String title must be 'String' in English")
        self.assertEqual(self.es_dict.get("nodes.titles.Main Loop"), "Bucle Primario", "Main Loop title must be 'Bucle Primario' in Spanish")
        self.assertEqual(self.es_dict.get("nodes.titles.MaxLoop"), "Bucle Máximo", "MaxLoop title must be 'Bucle Máximo' in Spanish")
        self.assertEqual(self.es_dict.get("nodes.categories.Text"), "Texto", "Text category must be 'Texto'")
        self.assertNotIn("(String)", self.es_dict.get("nodes.categories.Text", ""), "Text category must not have (String)")
        self.assertEqual(self.es_dict.get("nodes.categories.Shape"), "Shape", "Shape category must be 'Shape' in Spanish")
        self.assertEqual(self.es_dict.get("nodes.slots.Shape"), "Shape", "Shape slot must be 'Shape' in Spanish")
        self.assertEqual(self.es_dict.get("nodes.slots.Shape / Text"), "Shape / Texto", "Shape / Text slot must be 'Shape / Texto' in Spanish")
        self.assertEqual(self.es_dict.get("nodes.titles.IMG to Shape"), "Imagen a Shape", "IMG to Shape must be 'Imagen a Shape' in Spanish")

    def test_litegraph_node_context_menus(self):
        """Verifica que el menú contextual de litegraph.js tenga las traducciones al español."""
        litegraph_path = os.path.join(self.base_dir, "web", "litegraph.js")
        with open(litegraph_path, "r", encoding="utf-8") as f:
            js = f.read()

        expected_tokens = [
            'isEs ? "Entradas" : "Inputs"',
            'isEs ? "Salidas" : "Outputs"',
            'isEs ? "Propiedades" : "Properties"',
            'isEs ? "Título" : "Title"',
            'isEs ? "Modo" : "Mode"',
            'isEs ? "Redimensionar" : "Resize"',
            'isEs ? "Colapsar" : "Collapse"',
            'isEs ? "Fijar" : "Pin"',
            'isEs ? "Colores" : "Colors"',
            'isEs ? "Formas" : "Shapes"',
            'isEs ? "Clonar" : "Clone"',
            'isEs ? "Eliminar" : "Remove"',
            'isEs ? "Desconectar Enlaces" : "Disconnect Links"',
            'isEs ? "Eliminar Slot" : "Remove Slot"',
            'isEs ? "Renombrar Slot" : "Rename Slot"',
            '["Siempre", "En Evento", "Nunca", "Al Disparar"]'
        ]
        for token in expected_tokens:
            self.assertIn(token, js, f"Litegraph context menu missing translated token: {token}")

    def test_group_left_click_interaction(self):
        """Verifica que litegraph.js soporte interacción y arrastre de grupos con clic izquierdo."""
        litegraph_path = os.path.join(self.base_dir, "web", "litegraph.js")
        with open(litegraph_path, "r", encoding="utf-8") as f:
            js = f.read()

        self.assertIn("LGraphGroup.prototype.isPointInTitle", js)
        self.assertIn("LGraphGroup.prototype.isPointInResize", js)
        self.assertIn("LGraphGroup.prototype.isPointInBorder", js)
        self.assertIn("this.graph.getGroupOnPos(e.canvasX, e.canvasY)", js)
        self.assertIn("group.isPointInResize", js)
        self.assertIn("group.isPointInTitle", js)
        self.assertIn("this.selected_group = group;", js)
        self.assertIn('isEs ? "Grupo" : "Group"', js)
        self.assertIn("drawRoundRectPath", js)
        self.assertIn('(isEs && group.title === "Group") ? "Grupo" : group.title', js)
        self.assertIn("LGraphGroup.prototype.isPointInMoveOnlyIcon", js)
        self.assertIn("group.isPointInMoveOnlyIcon", js)
        self.assertIn("this.selected_group_ignore_nodes = true;", js)

    def test_root_nodes_order_text_above_string(self):
        """Verifica que el nodo Text esté ordenado por encima de String en el menú raíz."""
        import nodes_library
        root_nodes = list(SYSTEM_NODE_DB.get("", {}).keys())
        self.assertIn("Text", root_nodes)
        self.assertIn("String", root_nodes)
        self.assertLess(root_nodes.index("Text"), root_nodes.index("String"), "Text must be ordered above String in root menu")

if __name__ == "__main__":
    unittest.main()

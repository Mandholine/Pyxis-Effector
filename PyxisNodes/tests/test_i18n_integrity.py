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

import unittest
import os
import re
import json

class TestI18nIntegrity(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.i18n_path = os.path.join(self.base_dir, "web", "i18n.js")
        self.index_path = os.path.join(self.base_dir, "web", "index.html")
        self.theme_manager_path = os.path.join(self.base_dir, "web", "theme_manager.js")
        self.litegraph_path = os.path.join(self.base_dir, "web", "litegraph.js")
        self.main_path = os.path.join(self.base_dir, "main.py")

    def test_i18n_file_exists(self):
        self.assertTrue(os.path.exists(self.i18n_path), "web/i18n.js must exist")

    def test_i18n_key_parity(self):
        with open(self.i18n_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extraer bloques es: { ... } y en: { ... }
        es_pos = content.find("es: {")
        en_pos = content.find("en: {")
        en_end = content.find("};\n\n    let currentLanguage", en_pos)
        if en_end == -1:
            en_end = content.find("};", en_pos)

        self.assertNotEqual(es_pos, -1, "es block not found in i18n.js")
        self.assertNotEqual(en_pos, -1, "en block not found in i18n.js")

        es_block = content[es_pos:en_pos]
        en_block = content[en_pos:en_end]

        es_keys = set(re.findall(r'["\']([^"\']+)["\']\s*:', es_block))
        en_keys = set(re.findall(r'["\']([^"\']+)["\']\s*:', en_block))

        self.assertGreater(len(es_keys), 200, "Should have 200+ defined translation keys")
        missing_in_en = es_keys - en_keys
        missing_in_es = en_keys - es_keys

        self.assertEqual(missing_in_en, set(), f"Keys missing in EN: {missing_in_en}")
        self.assertEqual(missing_in_es, set(), f"Keys missing in ES: {missing_in_es}")

        # Certificar presencia de categorías, slots y títulos de nodos
        node_categories = [k for k in es_keys if k.startswith("nodes.categories.")]
        node_titles = [k for k in es_keys if k.startswith("nodes.titles.")]
        node_slots = [k for k in es_keys if k.startswith("nodes.slots.")]
        self.assertGreater(len(node_categories), 5, "Must have node categories translated")
        self.assertGreater(len(node_titles), 40, "Must have 40+ node titles translated")
        self.assertGreater(len(node_slots), 60, "Must have 60+ node slots translated")

    def test_i18n_helper_methods(self):
        with open(self.i18n_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("getNodeTitle", content)
        self.assertIn("translateSlot", content)
        self.assertIn("getCategoryTitle", content)
        self.assertIn("getTagDesc", content)
        self.assertIn("getRandomDesc", content)
        self.assertIn("getSalidaBadgeText", content)
        self.assertIn("getBlankBadgeText", content)
        self.assertIn("getAlignTitle", content)

    def test_settings_modal_header_button_and_no_redundant_select(self):
        with open(self.theme_manager_path, "r", encoding="utf-8") as f:
            content = f.read()

        # El botón de toggle de idioma debe estar en la cabecera de ajustes
        self.assertIn('id="btn-settings-lang-toggle"', content, "Settings modal header must contain btn-settings-lang-toggle")
        self.assertIn('class="pyxis-lang-pill', content, "Settings modal button must have ES | EN pills")
        
        # El select redundante no debe existir en la ventana de ajustes
        self.assertNotIn('id="setting-language"', content, "Redundant select #setting-language must be removed")

    def test_index_html_clean_topbar(self):
        with open(self.index_path, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn('src="i18n.js"', html, "index.html must include i18n.js script tag")
        self.assertIn('data-i18n', html, "index.html must use data-i18n attributes")
        self.assertNotIn('id="btn-lang-toggle"', html, "index.html topbar must NOT have redundant #btn-lang-toggle")
        self.assertIn('pyxis:languageChanged', html, "index.html must handle pyxis:languageChanged event")

    def test_litegraph_canvas_hooks(self):
        with open(self.litegraph_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Hook en getTitle
        self.assertIn("window.PyxisI18n.getNodeTitle", content, "LGraphNode.prototype.getTitle must call PyxisI18n.getNodeTitle")
        # Hook en slots
        self.assertIn("window.PyxisI18n.translateSlot", content, "Slot rendering must call PyxisI18n.translateSlot")
        # Hook en menú contextual
        self.assertIn("window.PyxisI18n.getCategoryTitle", content, "Context menu must call PyxisI18n.getCategoryTitle")

    def test_main_config_language_support(self):
        with open(self.main_path, "r", encoding="utf-8") as f:
            py_code = f.read()
        self.assertIn('"language": "es"', py_code, "main.py must include default language in get_user_config")
        self.assertIn('"language": config_data.get("language", "es")', py_code, "main.py must persist language in save_user_config")

if __name__ == "__main__":
    unittest.main()

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

"""Pruebas unitarias para paridad de traduccion e internacionalizacion (ES / EN) en la UI."""

import json
import os
import re
import unittest


class TestI18nIntegrity(unittest.TestCase):
    """Pruebas de paridad entre diccionarios de traduccion espanol e ingles."""

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.i18n_path = os.path.join(self.base_dir, "web", "i18n.js")

    def test_i18n_file_exists(self):
        self.assertTrue(os.path.exists(self.i18n_path), "web/i18n.js debe existir")

    def test_i18n_key_parity(self):
        with open(self.i18n_path, "r", encoding="utf-8") as f:
            content = f.read()

        es_pos = content.find("es: {")
        en_pos = content.find("en: {")
        en_end = content.find("};\n\n    let currentLanguage", en_pos)
        if en_end == -1:
            en_end = content.find("};", en_pos)

        self.assertNotEqual(es_pos, -1, "Bloque 'es' no encontrado en i18n.js")
        self.assertNotEqual(en_pos, -1, "Bloque 'en' no encontrado en i18n.js")

        es_block = content[es_pos:en_pos]
        en_block = content[en_pos:en_end]

        es_keys = set(re.findall(r'["\']([^"\']+)["\']\s*:', es_block))
        en_keys = set(re.findall(r'["\']([^"\']+)["\']\s*:', en_block))

        self.assertGreater(len(es_keys), 200, "Deben existir mas de 200 claves de traduccion")
        missing_in_en = es_keys - en_keys
        missing_in_es = en_keys - es_keys

        self.assertEqual(missing_in_en, set(), f"Claves faltantes en EN: {missing_in_en}")
        self.assertEqual(missing_in_es, set(), f"Claves faltantes en ES: {missing_in_es}")


if __name__ == "__main__":
    unittest.main()

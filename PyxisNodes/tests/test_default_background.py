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

# tests/test_default_background.py
"""Pruebas unitarias para el fondo por defecto (default_back.webp), opacidad 85% y modo puntos."""

import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import PyxisAPI


class TestDefaultBackground(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fake_appdata = self.temp_dir.name
        self.orig_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = self.fake_appdata

        self.api = PyxisAPI("dummy.ass", "dummy.ass", "dummy.json")

    def tearDown(self):
        if self.orig_appdata:
            os.environ["APPDATA"] = self.orig_appdata
        else:
            os.environ.pop("APPDATA", None)
        self.temp_dir.cleanup()

    def test_default_back_file_found(self):
        """Verifica que el archivo default_back.webp se localice en la estructura de PyxisNodes."""
        default_path = self.api._get_default_back_path()
        self.assertIsNotNone(default_path, "No se encontró default_back.webp")
        self.assertTrue(os.path.isfile(default_path), f"La ruta {default_path} no es un archivo válido")
        self.assertTrue(default_path.endswith("default_back.webp"))

    def test_default_back_used_when_no_user_files(self):
        """Verifica que si no hay fondos propios del usuario, se tome default_back.webp como fondo."""
        info = self.api._get_bg_media_info()
        self.assertTrue(info["has_bg"], "has_bg debe ser True")
        self.assertEqual(info["media_type"], "image")
        self.assertTrue(info["is_default"], "is_default debe ser True")
        self.assertTrue(info["data_url"].startswith("data:image/webp;base64,"))
        self.assertGreater(len(info["data_url"]), 1000)

    def test_user_config_defaults_opacity_and_dots_grid(self):
        """Verifica que la configuración por defecto establezca opacidad en 0.85 y rejilla en modo puntos (1)."""
        config = self.api.get_user_config()
        self.assertEqual(config["grid_mode"], 1, "La rejilla por defecto debe ser modo puntos (1)")
        self.assertEqual(config["bg_image_opacity"], 0.85, "La opacidad por defecto debe ser 0.85 (85%)")
        self.assertTrue(config["has_bg_image"])
        self.assertTrue(config["is_default_bg"])

    def test_user_custom_image_takes_precedence(self):
        """Verifica que si el usuario sube su propia imagen, esta tenga prioridad sobre el fondo por defecto."""
        pyxis_config_dir = os.path.join(self.fake_appdata, "PyxisNodes")
        os.makedirs(pyxis_config_dir, exist_ok=True)
        custom_img = os.path.join(pyxis_config_dir, "bg_image.png")
        with open(custom_img, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRdummycustomimage")

        info = self.api._get_bg_media_info()
        self.assertTrue(info["has_bg"])
        self.assertFalse(info["is_default"], "is_default debe ser False cuando el usuario tiene su propio archivo")

    def test_user_clear_background_disables_default(self):
        """Verifica que si el usuario presiona 'Quitar fondo', se guarde no_bg y no se fuerce el fondo por defecto."""
        self.api.save_user_config({"remove_bg_image": True})
        info = self.api._get_bg_media_info()
        self.assertFalse(info["has_bg"], "has_bg debe ser False tras quitar el fondo")


if __name__ == "__main__":
    unittest.main()
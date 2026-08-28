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

# tests/test_temp_cleanup.py
"""Pruebas unitarias para la purga de temporales (> 72h) y proteccion estricta de archivos de usuario."""

import os
import sys
import time
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import PyxisAPI


class TestTempCleanup(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.fake_appdata = self.temp_dir.name
        self.orig_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = self.fake_appdata

        self.pyxis_dir = os.path.join(self.fake_appdata, "PyxisNodes")
        os.makedirs(self.pyxis_dir, exist_ok=True)

        self.temp_cache = os.path.join(self.pyxis_dir, "temp_cache")
        self.temp_folder = os.path.join(self.pyxis_dir, "temp")
        self.bg_media = os.path.join(self.pyxis_dir, "bg_media")
        self.fonts = os.path.join(self.pyxis_dir, "fonts")
        self.themes = os.path.join(self.pyxis_dir, "themes")
        self.templates = os.path.join(self.pyxis_dir, "templates")

        for d in (self.temp_cache, self.temp_folder, self.bg_media, self.fonts, self.themes, self.templates):
            os.makedirs(d, exist_ok=True)

    def tearDown(self):
        if self.orig_appdata:
            os.environ["APPDATA"] = self.orig_appdata
        else:
            os.environ.pop("APPDATA", None)
        self.temp_dir.cleanup()

    def _create_file_with_age(self, path, age_hours):
        with open(path, "w", encoding="utf-8") as f:
            f.write("dummy test data")
        past_time = time.time() - (age_hours * 3600)
        os.utime(path, (past_time, past_time))

    def test_cleanup_deletes_files_older_than_72h(self):
        old_ass = os.path.join(self.temp_cache, "Pyxis_temp_old.ass")
        self._create_file_with_age(old_ass, 75)

        old_log = os.path.join(self.temp_folder, "player_debug.log")
        self._create_file_with_age(old_log, 80)

        old_font = os.path.join(self.fonts, "Arial.ttf")
        self._create_file_with_age(old_font, 100)

        old_preview = os.path.join(self.bg_media, "preview_bg_dummy_123.mp4")
        self._create_file_with_age(old_preview, 90)

        old_export = os.path.join(self.bg_media, "export_bg_dummy_456.mp4")
        self._create_file_with_age(old_export, 80)

        res = PyxisAPI.cleanup_temp_files(max_age_hours=72)
        self.assertEqual(res["cleaned_files"], 5)

        self.assertFalse(os.path.exists(old_ass))
        self.assertFalse(os.path.exists(old_log))
        self.assertFalse(os.path.exists(old_font))
        self.assertFalse(os.path.exists(old_preview))
        self.assertFalse(os.path.exists(old_export))

    def test_cleanup_preserves_recent_temp_files(self):
        recent_ass = os.path.join(self.temp_cache, "Pyxis_temp_recent.ass")
        self._create_file_with_age(recent_ass, 24)

        recent_preview = os.path.join(self.bg_media, "preview_bg_recent.mp4")
        self._create_file_with_age(recent_preview, 10)

        res = PyxisAPI.cleanup_temp_files(max_age_hours=72)
        self.assertEqual(res["cleaned_files"], 0)

        self.assertTrue(os.path.exists(recent_ass))
        self.assertTrue(os.path.exists(recent_preview))

    def test_cleanup_strictly_protects_user_config_and_backgrounds(self):
        user_cfg = os.path.join(self.pyxis_dir, "user_config.json")
        self._create_file_with_age(user_cfg, 500)

        prev_base = os.path.join(self.pyxis_dir, "preview_base.ass")
        self._create_file_with_age(prev_base, 500)

        bg_img = os.path.join(self.pyxis_dir, "bg_image.webp")
        self._create_file_with_age(bg_img, 500)

        def_back = os.path.join(self.pyxis_dir, "default_back.webp")
        self._create_file_with_age(def_back, 500)

        user_video = os.path.join(self.bg_media, "bg_video.mp4")
        self._create_file_with_age(user_video, 500)

        user_poster = os.path.join(self.bg_media, "bg_poster.webp")
        self._create_file_with_age(user_poster, 500)

        custom_theme = os.path.join(self.themes, "my_theme.json")
        self._create_file_with_age(custom_theme, 500)

        custom_tpl = os.path.join(self.templates, "my_tpl.json")
        self._create_file_with_age(custom_tpl, 500)

        res = PyxisAPI.cleanup_temp_files(max_age_hours=72, force_all=True)

        self.assertTrue(os.path.exists(user_cfg), "user_config.json NUNCA debe ser eliminado")
        self.assertTrue(os.path.exists(prev_base), "preview_base.ass NUNCA debe ser eliminado")
        self.assertTrue(os.path.exists(bg_img), "bg_image.webp NUNCA debe ser eliminado")
        self.assertTrue(os.path.exists(def_back), "default_back.webp NUNCA debe ser eliminado")
        self.assertTrue(os.path.exists(user_video), "bg_video.mp4 NUNCA debe ser eliminado")
        self.assertTrue(os.path.exists(user_poster), "bg_poster.webp NUNCA debe ser eliminado")
        self.assertTrue(os.path.exists(custom_theme), "Los temas personalizados NUNCA deben ser eliminados")
        self.assertTrue(os.path.exists(custom_tpl), "Las plantillas personalizadas NUNCA deben ser eliminadas")


if __name__ == "__main__":
    unittest.main()

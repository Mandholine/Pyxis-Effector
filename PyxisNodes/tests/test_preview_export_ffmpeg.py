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

# tests/test_preview_export_ffmpeg.py
"""Pruebas unitarias para validar la diferenciacion de parametros FFmpeg entre Preview y Export."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import PyxisAPI


class TestPreviewExportFFmpeg(unittest.TestCase):

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

    @patch("subprocess.run")
    def test_preview_uses_preset_fast_crf_21_and_deblock(self, mock_run):
        def fake_run(cmd, *args, **kwargs):
            out_clip = cmd[-1]
            with open(out_clip, "wb") as f:
                f.write(b"....ftyp....moov...." + b"dummy mp4 data" * 100)
            proc = MagicMock()
            proc.returncode = 0
            return proc

        mock_run.side_effect = fake_run

        info = {
            "res_x": 1280,
            "res_y": 720,
            "fps": 24.0,
            "clip_start_sec": 0.0,
            "clip_duration_sec": 5.0,
            "dummy_info": {"color_hex": "000000"}
        }

        # Vista desde el nodo (is_export=False)
        clip_path = self.api._ensure_preview_media_clip(info, is_export=False)
        self.assertIsNotNone(clip_path)
        self.assertIn("preview_bg_", os.path.basename(clip_path))

        # Verificar argumentos enviados a subprocess.run
        self.assertTrue(mock_run.called)
        cmd = mock_run.call_args[0][0]

        # Verificar preset fast
        self.assertIn("-preset", cmd)
        self.assertEqual(cmd[cmd.index("-preset") + 1], "fast")

        # Verificar crf 21
        self.assertIn("-crf", cmd)
        self.assertEqual(cmd[cmd.index("-crf") + 1], "21")

        # Verificar reduccion de deblocking
        self.assertIn("-deblock", cmd)
        self.assertEqual(cmd[cmd.index("-deblock") + 1], "-1:-1")

    @patch("subprocess.run")
    def test_export_uses_preset_ultrafast_and_crf_18(self, mock_run):
        def fake_run(cmd, *args, **kwargs):
            out_clip = cmd[-1]
            with open(out_clip, "wb") as f:
                f.write(b"....ftyp....moov...." + b"dummy mp4 data" * 100)
            proc = MagicMock()
            proc.returncode = 0
            return proc

        mock_run.side_effect = fake_run

        info = {
            "res_x": 1280,
            "res_y": 720,
            "fps": 24.0,
            "clip_start_sec": 0.0,
            "clip_duration_sec": 5.0,
            "dummy_info": {"color_hex": "000000"}
        }

        # Exportacion del clip (is_export=True)
        clip_path = self.api._ensure_preview_media_clip(info, is_export=True)
        self.assertIsNotNone(clip_path)
        self.assertIn("export_bg_", os.path.basename(clip_path))

        # Verificar argumentos enviados a subprocess.run
        self.assertTrue(mock_run.called)
        cmd = mock_run.call_args[0][0]

        # Verificar preset ultrafast
        self.assertIn("-preset", cmd)
        self.assertEqual(cmd[cmd.index("-preset") + 1], "ultrafast")

        # Verificar crf 18
        self.assertIn("-crf", cmd)
        self.assertEqual(cmd[cmd.index("-crf") + 1], "18")

        # Verificar que NO se altere el deblocking en export
        self.assertNotIn("-deblock", cmd)


if __name__ == "__main__":
    unittest.main()

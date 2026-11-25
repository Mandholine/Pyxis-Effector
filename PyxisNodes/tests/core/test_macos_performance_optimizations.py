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

"""Regression tests for macOS ARM performance optimisations."""

import http.client
import os
import sys
import tempfile
import types
import unittest
from unittest import mock

import numpy as np

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import font_resolver
import gpu_engine
import node_engine
from font_engine import FontEngine
from font_vector_engine import FontVectorEngine
from karaskel_engine import KaraskelEngine, KaraskelLine, KaraskelMeta


class TestMacosPerformanceOptimisations(unittest.TestCase):
    """Validates cross-platform spawn guards, font caching, linear layout, VideoToolbox, and HTTP streaming."""

    def tearDown(self):
        node_engine.abort_global_multiprocessing()
        font_resolver.clear_cache()
        FontEngine.clear_cache()
        FontVectorEngine.clear_cache()

    def test_spawn_guards_skip_pool_for_lightweight_darwin_workload(self):
        """Lightweight scripts on macOS spawn must run sequentially without launching worker pools."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Syllables", "properties": {}},
                {"id": 2, "type": "System/Output", "properties": {"apply_to": "All Lines"}},
            ],
            "links": [[1, 1, 0, 2, 0, "LOOP"]],
        }
        styles = {
            "Default": {
                "Name": "Default",
                "Fontname": "Arial",
                "Fontsize": 40,
                "ScaleX": 100,
                "ScaleY": 100,
                "Spacing": 0,
            }
        }
        dialogues = [
            {"raw": r"Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\k50}Hel{\k50}lo", "i": 1, "selected": True},
            {"raw": r"Dialogue: 0,0:00:04.00,0:00:06.00,Default,,0,0,0,,{\k50}Wor{\k50}ld", "i": 2, "selected": True},
            {"raw": r"Dialogue: 0,0:00:07.00,0:00:09.00,Default,,0,0,0,,{\k50}Py{\k50}xis", "i": 3, "selected": True},
        ]

        eng_seq = node_engine.GraphEngine(graph, 1280, 720, 41.708)
        expected = eng_seq.process(dialogues, styles, use_multiprocessing=False)

        with mock.patch.object(sys, "platform", "darwin"), \
             mock.patch("node_engine._is_spawn_platform", return_value=True), \
             mock.patch("node_engine._get_or_create_persistent_pool") as mock_pool:
            eng_mp = node_engine.GraphEngine(graph, 1280, 720, 41.708)
            actual = eng_mp.process(dialogues, styles, use_multiprocessing=True)
            mock_pool.assert_not_called()

        self.assertEqual(actual, expected)

    def test_persistent_pool_abort_resets_state(self):
        """abort_global_multiprocessing must terminate and clear persistent pool references."""
        fake_pool = mock.MagicMock()
        fake_pool._broken = False
        fake_pool._processes = {}

        with mock.patch("concurrent.futures.ProcessPoolExecutor", return_value=fake_pool):
            pool, counter, cancel = node_engine._get_or_create_persistent_pool(2)
            self.assertIs(pool, fake_pool)
            counter.value = 12
            cancel.value = True

            pool2, counter2, cancel2 = node_engine._get_or_create_persistent_pool(2)
            self.assertIs(pool2, fake_pool)
            self.assertEqual(counter2.value, 0)
            self.assertFalse(cancel2.value)

            node_engine.abort_global_multiprocessing()
            fake_pool.shutdown.assert_called_once_with(wait=False, cancel_futures=True)
            self.assertIsNone(node_engine._PERSISTENT_POOL)

    def test_font_resolver_seed_and_disk_cache_roundtrip(self):
        """seed_resolve_cache and disk index cache must bypass FreeType scanning across runs."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            dummy_font = os.path.join(tmp_dir, "TestFont.ttf")
            with open(dummy_font, "wb") as fh:
                fh.write(b"\x00\x01\x00\x00")

            font_resolver.seed_resolve_cache({("testfont", False, False): dummy_font})
            with mock.patch("font_resolver._fc_match") as mock_fc, \
                 mock.patch("font_resolver._build_family_index") as mock_idx:
                resolved = font_resolver.resolve_font_file("TestFont")
                self.assertEqual(resolved, dummy_font)
                mock_fc.assert_not_called()
                mock_idx.assert_not_called()

            font_resolver.clear_cache()
            user_dir = os.path.join(tmp_dir, "user_data")
            fonts_dir = os.path.join(tmp_dir, "fonts")
            os.makedirs(user_dir, exist_ok=True)
            os.makedirs(fonts_dir, exist_ok=True)
            dummy_font2 = os.path.join(fonts_dir, "CustomFont.ttf")
            with open(dummy_font2, "wb") as fh:
                fh.write(b"\x00\x01\x00\x00")

            with mock.patch("font_resolver.get_user_data_dir", return_value=user_dir):
                font_resolver._FAMILY_INDEX["mycustomfont"] = {(False, False): dummy_font2}
                font_resolver._save_disk_index_cache([fonts_dir])
                font_resolver._FAMILY_INDEX.clear()

                loaded = font_resolver._load_disk_index_cache([fonts_dir])
                self.assertTrue(loaded)
                self.assertEqual(font_resolver._FAMILY_INDEX["mycustomfont"][(False, False)], dummy_font2)

                # Invalidate when directory timestamp changes
                os.utime(fonts_dir, (1, 1))
                self.assertFalse(font_resolver._load_disk_index_cache([fonts_dir]))

    def test_font_vector_engine_lru_face_cache(self):
        """FontVectorEngine._get_freetype_face must cache Faces and update char_size only on change."""
        created_faces = []

        class _FakeFace:
            def __init__(self, path):
                self.path = path
                self.sizes = []
                created_faces.append(self)

            def set_char_size(self, sz):
                self.sizes.append(sz)

        fake_ft = types.SimpleNamespace(Face=_FakeFace)
        FontVectorEngine.clear_cache()
        with mock.patch.dict(sys.modules, {"freetype": fake_ft}):
            f1 = FontVectorEngine._get_freetype_face("/fonts/A.ttf", 40.0)
            f2 = FontVectorEngine._get_freetype_face("/fonts/A.ttf", 40.0)
            f3 = FontVectorEngine._get_freetype_face("/fonts/A.ttf", 48.0)

            self.assertIs(f1, f2)
            self.assertIs(f1, f3)
            self.assertEqual(len(created_faces), 1)
            self.assertEqual(f1.sizes, [40 * 64, 48 * 64])

            # Check LRU eviction beyond MAX_FT_FACE_CACHE
            for idx in range(FontVectorEngine.MAX_FT_FACE_CACHE + 5):
                FontVectorEngine._get_freetype_face(f"/fonts/F_{idx}.ttf", 32.0)
            self.assertEqual(len(FontVectorEngine._ft_face_cache), FontVectorEngine.MAX_FT_FACE_CACHE)

    def test_karaskel_linear_layout_parity_on_darwin(self):
        """Linear O(N) FreeType layout in do_basic_layout must match growing-prefix measurement."""
        widths_map = {"H": 14.0, "e": 10.5, "l": 5.0, "o": 11.25, " ": 6.0, "W": 18.0, "r": 7.5, "d": 11.5}

        def _fake_char_widths(style, text):
            sc = float(style.get("ScaleX", 100.0)) / 100.0
            return [FontEngine.snap_26_6(widths_map.get(c, 10.0) * sc) for c in text]

        def _fake_extents(style, text):
            sc = float(style.get("ScaleX", 100.0)) / 100.0
            sp = float(style.get("Spacing", 0.0))
            w_sum = sum(widths_map.get(c, 10.0) * sc for c in text)
            w_tot = w_sum + sp * max(0, len(text) - 1) * sc
            return FontEngine.snap_26_6(w_tot), 40.0, 8.0, 0.0

        meta = KaraskelMeta(res_x=1280, res_y=720, video_x_correct_factor=1.15)
        for spacing_val in (0.0, 2.5):
            styles = {
                "Default": {
                    "Name": "Default",
                    "Fontname": "Arial",
                    "Fontsize": 40.0,
                    "ScaleX": 100.0,
                    "Spacing": spacing_val,
                }
            }
            raw_text = r"{\k40}Hel{\k30}lo {\k50}Wor{\k40}ld"
            k_linear = KaraskelLine(raw_text=raw_text, start_time=0, end_time=1600, style="Default")
            with mock.patch("karaskel_engine.platform.system", return_value="Darwin"), \
                 mock.patch.object(FontEngine, "get_char_widths", side_effect=_fake_char_widths), \
                 mock.patch.object(FontEngine, "get_text_extents", side_effect=_fake_extents):
                KaraskelEngine.preproc_line(meta, styles, k_linear)

            k_prefix = KaraskelLine(raw_text=raw_text, start_time=0, end_time=1600, style="Default")
            with mock.patch("karaskel_engine.platform.system", return_value="Windows"), \
                 mock.patch.object(FontEngine, "get_shaped_char_advances", return_value=([], False)), \
                 mock.patch.object(FontEngine, "get_text_extents", side_effect=_fake_extents):
                KaraskelEngine.preproc_line(meta, styles, k_prefix)

            self.assertEqual(len(k_linear.kara), len(k_prefix.kara))
            for s_lin, s_pfx in zip(k_linear.kara, k_prefix.kara):
                self.assertAlmostEqual(s_lin.prespace_left, s_pfx.prespace_left, places=6)
                self.assertAlmostEqual(s_lin.left, s_pfx.left, places=6)
                self.assertAlmostEqual(s_lin.width, s_pfx.width, places=6)
                self.assertAlmostEqual(s_lin.right, s_pfx.right, places=6)
                self.assertAlmostEqual(s_lin.postspace_left, s_pfx.postspace_left, places=6)

    @staticmethod
    def _import_main_safe():
        """Imports src/main.py with a stubbed pywebview module safe under python311.zip unittest."""
        if "main" in sys.modules:
            return sys.modules["main"]
        fake_webview = types.ModuleType("webview")
        fake_webview.windows = []
        fake_webview.settings = {}
        fake_webview.http = types.SimpleNamespace()
        with mock.patch.dict(sys.modules, {"webview": fake_webview}):
            import main as pyxis_main
            return pyxis_main

    def test_videotoolbox_encoder_selection_on_darwin(self):
        """macOS must select h264_videotoolbox without unsupported x264 flags and fall back cleanly."""
        pyxis_main = self._import_main_safe()

        pyxis_main.PyxisAPI._CACHED_H264_ENCODER = None
        ok_proc = types.SimpleNamespace(returncode=0)
        with mock.patch.object(sys, "platform", "darwin"), \
             mock.patch("subprocess.run", return_value=ok_proc) as mock_run:
            enc_name, _ = pyxis_main.PyxisAPI._detect_best_h264_encoder("ffmpeg")
            self.assertEqual(enc_name, "h264_videotoolbox")
            self.assertEqual(mock_run.call_count, 1)

            _, preview_args = pyxis_main.PyxisAPI._get_h264_encode_args("ffmpeg", profile="preview")
            self.assertIn("h264_videotoolbox", preview_args)
            for forbidden in ("-crf", "-preset", "-tune", "-deblock"):
                self.assertNotIn(forbidden, preview_args)

        pyxis_main.PyxisAPI._CACHED_H264_ENCODER = None
        fail_proc = types.SimpleNamespace(returncode=1)
        with mock.patch.object(sys, "platform", "darwin"), \
             mock.patch("subprocess.run", return_value=fail_proc):
            enc_name, _ = pyxis_main.PyxisAPI._detect_best_h264_encoder("ffmpeg")
            self.assertEqual(enc_name, "libx264")
        pyxis_main.PyxisAPI._CACHED_H264_ENCODER = None

    def test_gpu_engine_identity_and_no_fake_ctypes_backend(self):
        """Identity particle transforms must short-circuit and ctypes OpenCL probe must not masquerade as GPU."""
        mgr = gpu_engine.GpuEngineManager.__new__(gpu_engine.GpuEngineManager)
        mgr.backend = "OpenCL (PyOpenCL)"
        mgr.cl_context = object()
        mgr.cl_queue = object()

        pts = np.array([[10.0, 20.0, 255.0, 255.0, 255.0, 255.0]], dtype=np.float64)
        out = mgr.transform_particles_gpu(pts, scale_x=1.0, scale_y=1.0, angle_deg=0.0)
        self.assertIs(out, pts)

        mgr2 = gpu_engine.GpuEngineManager.__new__(gpu_engine.GpuEngineManager)
        mgr2.backend = "CPU"
        mgr2.device_name = "CPU"
        mgr2.is_healthy = False
        mgr2.cl_context = None
        mgr2.cl_queue = None
        mgr2.cl_program = None
        mgr2.cuda_module = None
        with mock.patch("importlib.import_module", side_effect=ImportError("no pyopencl")):
            self.assertFalse(mgr2._probe_opencl_health())
            self.assertEqual(mgr2.backend, "CPU")

    def test_preview_fonts_map_no_base64_and_daemon_mime_headers(self):
        """get_preview_fonts_map must emit HTTP URLs without Base64 data, and daemon must set font MIME & Cache-Control."""
        pyxis_main = self._import_main_safe()
        from pyxis_daemon import PyxisDaemonServer

        self.assertFalse(hasattr(pyxis_main.PyxisAPI, "get_preview_font_data_url"))

        with tempfile.TemporaryDirectory() as tmp_dir:
            font_file = os.path.join(tmp_dir, "TestPreview.ttc")
            with open(font_file, "wb") as fh:
                fh.write(b"ttcf\x00\x01\x00\x00")

            daemon = PyxisDaemonServer()
            with mock.patch("pyxis_daemon.PyxisDaemonServer._monitor_aegisub_pid"):
                daemon.start(port=0)
            try:
                api = pyxis_main.PyxisAPI.__new__(pyxis_main.PyxisAPI)
                api._daemon_server = daemon
                api._preview_base_hash = "h1"
                api._cached_fonts_map = {}

                fake_info = {
                    "styles": {"Default": {"Fontname": "TestPreview"}},
                    "font_name": "TestPreview",
                }
                with mock.patch.object(api, "get_preview_info", return_value=fake_info), \
                     mock.patch.object(api, "_find_font_file", return_value=font_file):
                    fmap = api.get_preview_fonts_map(source="base")

                self.assertIn("testpreview", fmap)
                entry = fmap["testpreview"]
                self.assertNotIn("data", entry)
                self.assertEqual(entry["mime"], "font/collection")
                self.assertIn(f"127.0.0.1:{daemon.actual_port}/media_file", entry["http_url"])

                # Request font over local HTTP daemon
                conn = http.client.HTTPConnection("127.0.0.1", daemon.actual_port, timeout=2.0)
                req_path = entry["http_url"].split(f":{daemon.actual_port}", 1)[1]
                conn.request("GET", req_path)
                resp = conn.getresponse()
                body = resp.read()
                conn.close()

                self.assertEqual(resp.status, 200)
                self.assertEqual(resp.getheader("Content-Type"), "font/collection")
                self.assertEqual(resp.getheader("Cache-Control"), "public, max-age=3600")
                self.assertEqual(body, b"ttcf\x00\x01\x00\x00")
            finally:
                daemon.running = False
                if daemon.server:
                    daemon.server.shutdown()
                    daemon.server.server_close()


if __name__ == "__main__":
    unittest.main()

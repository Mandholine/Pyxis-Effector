"""
Unit tests for Previewer source-switching optimisations in `main.py`:
- Atomic `get_preview_source_bundle` IPC method (single `get_preview_info` evaluation,
  font-hash deduplication, unified audio bypass).
- `(abspath, mtime_ns, size)` stat fast-path in `_load_and_cache_aegisub_source` and
  `_load_and_cache_preview_base`.
- Idempotent, lock-safe `prewarm_aegisub_preview` and cache invalidation reset.
"""

import os
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

if "webview" not in sys.modules:
    try:
        import webview  # noqa: F401
    except ValueError:
        # pywebview.util.base_uri() fails when invoked via `python -m unittest` from python311.zip
        sys.modules["webview"] = types.ModuleType("webview")

from main import PyxisAPI


SAMPLE_ASS = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Hello Pyxis
"""


class TestPreviewSourceSwitchingOptimisations(unittest.TestCase):
    """Verify atomic bundle, stat fast-path, and prewarm guarantees."""

    def _make_bare_api(self, temp_ass_path=None):
        api = PyxisAPI.__new__(PyxisAPI)
        api.temp_ass = temp_ass_path
        api.result_file = None
        api.session_file = None
        api.aegisub_version = "test"
        api.lock_file = None
        api._initial_lock_file = None
        api._daemon_server = None
        api._store = None
        api._active_engine = None
        api._cached_preview_base_info = None
        api._cached_aegisub_info = None
        api._cached_aegisub_parsed = None
        api._cached_fonts_map = {}
        api._clip_lock = threading.RLock()
        api._aegisub_source_lock = threading.RLock()
        api._preview_base_lock = threading.RLock()
        api._aegisub_prewarm_lock = threading.Lock()
        api._aegisub_prewarm_key = None
        api._preview_cancelled = False
        return api

    def test_get_preview_source_bundle_single_info_and_font_dedup(self):
        """Bundle resolves get_preview_info once, skips unified audio, and omits unchanged fonts_map."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_file = os.path.join(tmp_dir, "clip.mp4")
            ass_file = os.path.join(tmp_dir, "sub.ass")
            with open(video_file, "wb") as fp:
                fp.write(b"fake-mp4-header")
            with open(ass_file, "w", encoding="utf-8") as fp:
                fp.write(SAMPLE_ASS)

            api = self._make_bare_api(temp_ass_path=ass_file)
            api._aegisub_temp_hash = "abc123hash"
            api._cached_fonts_map = {
                "aegisub:abc123hash": {"arial": {"http_url": "http://127.0.0.1/f/arial.ttf", "path": "arial.ttf", "mime": "font/ttf"}}
            }

            fake_info = {
                "source": "aegisub",
                "has_aegisub": True,
                "path": ass_file,
                "res_x": 1280,
                "res_y": 720,
                "real_video_file": video_file,
                "real_audio_file": video_file,
                "media_meta": {"video_codec": "h264", "audio_codec": "aac"},
            }

            info_calls = []

            def fake_get_preview_info(source="base", target_output_id=None, payload=None):
                info_calls.append((source, target_output_id))
                return fake_info

            with patch.object(api, "get_preview_info", side_effect=fake_get_preview_info), \
                 patch.object(api, "_ensure_browser_compatible_media", return_value=video_file), \
                 patch.object(api, "_build_media_file_url", return_value="http://127.0.0.1/media/clip.mp4"):
                bundle1 = api.get_preview_source_bundle(source="aegisub", last_fonts_hash=None)
                self.assertEqual(len(info_calls), 1)
                self.assertEqual(bundle1["video_url"], "http://127.0.0.1/media/clip.mp4")
                self.assertEqual(bundle1["audio_url"], "")
                self.assertEqual(bundle1["fonts_hash"], "aegisub:abc123hash")
                self.assertIsNotNone(bundle1["fonts_map"])
                self.assertIn("PlayResX: 1280", bundle1["base_ass"])

                bundle2 = api.get_preview_source_bundle(source="aegisub", last_fonts_hash="aegisub:abc123hash")
                self.assertEqual(len(info_calls), 2)
                self.assertIsNone(bundle2["fonts_map"])
                self.assertEqual(bundle2["fonts_hash"], "aegisub:abc123hash")

    def test_aegisub_stat_fast_path_and_invalidation(self):
        """Unchanged stat returns cached info without re-parsing; content change invalidates cleanly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ass_file = os.path.join(tmp_dir, "active.ass")
            with open(ass_file, "w", encoding="utf-8") as fp:
                fp.write(SAMPLE_ASS)

            api = self._make_bare_api(temp_ass_path=ass_file)
            with patch.object(api, "_probe_media_metadata", return_value={"video_codec": "DUMMY", "audio_codec": ""}) as probe_mock:
                info1 = api._load_and_cache_aegisub_source()
                self.assertTrue(info1["has_aegisub"])
                self.assertEqual(probe_mock.call_count, 1)

                with patch("hashlib.sha256", side_effect=AssertionError("sha256 must not run when stat matches")):
                    info2 = api._load_and_cache_aegisub_source()
                self.assertIs(info2, info1)
                self.assertEqual(probe_mock.call_count, 1)

                # Modify file size and mtime
                with open(ass_file, "w", encoding="utf-8") as fp:
                    fp.write(SAMPLE_ASS + "Dialogue: 0,0:00:04.00,0:00:05.00,Default,,0,0,0,,Second\n")
                info3 = api._load_and_cache_aegisub_source()
                self.assertEqual(len(info3["dialogues"]), 2)

    def test_prewarm_idempotent_and_reset_on_invalidate(self):
        """prewarm_aegisub_preview runs once per stat key and re-arms on invalidate_aegisub_cache."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ass_file = os.path.join(tmp_dir, "active.ass")
            with open(ass_file, "w", encoding="utf-8") as fp:
                fp.write(SAMPLE_ASS)

            api = self._make_bare_api(temp_ass_path=ass_file)
            done_event = threading.Event()
            calls = []

            def fake_load(*args, **kwargs):
                calls.append(1)
                done_event.set()
                return {"has_aegisub": True}

            with patch.object(api, "_load_and_cache_aegisub_source", side_effect=fake_load):
                self.assertTrue(api.prewarm_aegisub_preview())
                self.assertTrue(done_event.wait(timeout=2.0))
                self.assertFalse(api.prewarm_aegisub_preview())
                self.assertEqual(len(calls), 1)

                api.invalidate_aegisub_cache()
                done_event.clear()
                self.assertTrue(api.prewarm_aegisub_preview())
                self.assertTrue(done_event.wait(timeout=2.0))
                self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()

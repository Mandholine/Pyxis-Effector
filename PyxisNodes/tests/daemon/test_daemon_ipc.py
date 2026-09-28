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

"""Pruebas unitarias para el servidor daemon IPC y gestion del ciclo de vida de bloqueos."""

import os
import tempfile
import unittest
from pyxis_daemon import PyxisDaemonServer


class DummyWindow:
    def __init__(self):
        self.shown = False
        self.restored = False
        self.focus = True
        self.js_evaluated = []
        self.title = "Pyxis Node Engine 1.1.1"

    def show(self):
        self.shown = True

    def restore(self):
        self.restored = True

    def evaluate_js(self, code):
        self.js_evaluated.append(code)


class DummyAPI:
    def __init__(self):
        self.temp_ass = "old.ass"
        self.result_file = "old_res.txt"
        self.lock_file = "old_lock.txt"
        self.session_file = "old_session.json"
        self.aegisub_version = "3.4.0"

    def release_lock(self):
        if self.lock_file and os.path.exists(self.lock_file):
            try:
                os.remove(self.lock_file)
            except Exception:
                pass
        self.lock_file = None

    def invalidate_aegisub_cache(self):
        pass

    def invalidate_preview_base_cache(self):
        pass


class TestDaemonIPC(unittest.TestCase):
    """Pruebas de inicializacion del servidor daemon y endpoints IPC."""

    def test_daemon_server_initialization(self):
        api = DummyAPI()
        window = DummyWindow()
        server = PyxisDaemonServer(main_api=api, window=window)
        self.assertIsNotNone(server)
        self.assertEqual(server.main_api.aegisub_version, "3.4.0")

    def test_lock_file_lifecycle(self):
        temp_dir = tempfile.mkdtemp()
        lock_path = os.path.join(temp_dir, "test.lock")
        with open(lock_path, "w", encoding="utf-8") as f:
            f.write("1")

        api = DummyAPI()
        api.lock_file = lock_path
        self.assertTrue(os.path.exists(lock_path))

        api.release_lock()
        self.assertFalse(os.path.exists(lock_path))
        self.assertIsNone(api.lock_file)

    def test_daemon_reopen_window_no_bool_callable_error(self):
        api = DummyAPI()
        window = DummyWindow()
        server = PyxisDaemonServer(main_api=api, window=window)
        res = server.reopen_session({
            "temp_ass": "new.ass",
            "result_file": "new_res.txt",
            "lock_file": "new_lock.txt",
            "session_file": "new_session.json",
            "aegisub_version": "3.4.2"
        })
        self.assertTrue(res)
        self.assertTrue(window.shown)
        self.assertTrue(window.restored)
        self.assertEqual(api.temp_ass, "new.ass")

    def test_console_logs_buffer_and_api(self):
        from main import _LogBufferStream, PyxisAPI
        _LogBufferStream.clear()
        self.assertEqual(len(_LogBufferStream.get_logs()), 0)
        
        print("[Pyxis Test] Hello debug console log line 1")
        print("[Pyxis Test] Hello debug console log line 2")
        
        logs = _LogBufferStream.get_logs()
        self.assertTrue(any("Hello debug console log line 1" in str(line) for line in logs))
        
        api = PyxisAPI("dummy_temp.ass", "dummy_res.txt", "dummy_session.json")
        api_res = api.get_console_logs()
        self.assertTrue(api_res.get("success"))
        self.assertTrue(len(api_res.get("logs", [])) > 0)
        
        clear_res = api.clear_console_logs()
        self.assertTrue(clear_res.get("success"))
        self.assertEqual(len(_LogBufferStream.get_logs()), 0)


if __name__ == "__main__":
    unittest.main()

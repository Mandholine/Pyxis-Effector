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

import json
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyxis_daemon import check_daemon_running, notify_daemon_reopen, PyxisDaemonServer

class DummyWindow:
    def __init__(self):
        self.shown = False
        self.restored = False
        self.focused = False
        self.js_evaluated = []

    def show(self):
        self.shown = True

    def restore(self):
        self.restored = True

    def focus(self):
        self.focused = True

    def evaluate_js(self, code):
        self.js_evaluated.append(code)


class DummyAPI:
    def __init__(self):
        self.temp_ass = "old.ass"
        self.result_file = "old_res.txt"
        self.lock_file = "old_lock.txt"
        self.session_file = "old_session.json"
        self.aegisub_version = "3.4.0"


class TestPyxisDaemon(unittest.TestCase):
    def test_daemon_lifecycle_and_reopen(self):
        api = DummyAPI()
        window = DummyWindow()
        server = PyxisDaemonServer(main_api=api, window=window)
        test_port = 28799
        server.start(port=test_port)

        # Dar 300ms al servidor HTTP para escuchar
        time.sleep(0.3)

        status_res = check_daemon_running(port=test_port)
        self.assertIsNotNone(status_res)
        self.assertEqual(status_res.get("status"), "ok")

        # Notificar reopen
        payload = {
            "temp_ass": "new.ass",
            "result_file": "new_res.txt",
            "lock_file": "new_lock.txt",
            "session_file": "new_session.json",
            "aegisub_version": "3.4.2"
        }
        reopened = notify_daemon_reopen(payload, port=test_port)
        self.assertTrue(reopened)

        self.assertEqual(api.temp_ass, "new.ass")
        self.assertEqual(api.result_file, "new_res.txt")
        self.assertTrue(window.shown)
        self.assertTrue(window.restored)

        # Apagar daemon limpiamente
        server.running = False
        if server.server:
            try:
                server.server.shutdown()
                server.server.server_close()
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()

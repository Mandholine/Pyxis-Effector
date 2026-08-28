# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3.

import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock

# Ajustar sys.path para importar desde el directorio de PyxisNodes
current_dir = os.path.dirname(os.path.abspath(__file__))
pyxis_dir = os.path.dirname(current_dir)
if pyxis_dir not in sys.path:
    sys.path.insert(0, pyxis_dir)

from main import PyxisAPI
from pyxis_daemon import PyxisDaemonServer


class TestDaemonLockLifecycle(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.appdata_dir = os.path.join(self.temp_dir.name, "AppData", "Roaming")
        os.makedirs(os.path.join(self.appdata_dir, "PyxisNodes", "temp"), exist_ok=True)
        self.orig_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = self.appdata_dir

        self.initial_lock = os.path.join(self.appdata_dir, "PyxisNodes", "temp", "pyxis_lock_initial.txt")
        with open(self.initial_lock, "w", encoding="utf-8") as f:
            f.write("1")

        self.api = PyxisAPI("dummy.ass", "dummy_result.txt", "dummy_session.json", lock_file=self.initial_lock)

    def tearDown(self):
        if self.orig_appdata:
            os.environ["APPDATA"] = self.orig_appdata
        else:
            os.environ.pop("APPDATA", None)
        self.temp_dir.cleanup()

    def test_release_lock_basic(self):
        self.assertTrue(os.path.exists(self.initial_lock))
        self.assertEqual(self.api.lock_file, self.initial_lock)

        self.api.release_lock()

        self.assertFalse(os.path.exists(self.initial_lock))
        self.assertIsNone(self.api.lock_file)

    def test_release_lock_reopened_session(self):
        # Simular que el daemon recibe una nueva sesión (/reopen) con un nuevo lock file
        new_lock = os.path.join(self.appdata_dir, "PyxisNodes", "temp", "pyxis_lock_reopened.txt")
        with open(new_lock, "w", encoding="utf-8") as f:
            f.write("1")

        self.api.lock_file = new_lock

        self.assertTrue(os.path.exists(self.initial_lock))
        self.assertTrue(os.path.exists(new_lock))

        # Al llamar a release_lock(), DEBE borrar tanto el lock dinámico como el inicial
        self.api.release_lock()

        self.assertFalse(os.path.exists(new_lock), "El lock de la sesión reabierta debió ser eliminado")
        self.assertFalse(os.path.exists(self.initial_lock), "El lock inicial debió ser eliminado")
        self.assertIsNone(self.api.lock_file)

    def test_release_lock_retry_on_windows_collision(self):
        # Simular error transitorio [WinError 32] (archivo en uso por Lua) y verificar que reintenta y logra borrarlo
        call_count = 0
        real_remove = os.remove

        def mock_remove(path):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise PermissionError(32, "El proceso no puede acceder al archivo porque está siendo utilizado por otro proceso")
            return real_remove(path)

        with patch("os.remove", side_effect=mock_remove):
            self.api.release_lock()

        self.assertGreaterEqual(call_count, 3, "Debió reintentar al encontrar colisión de archivo en uso")
        self.assertFalse(os.path.exists(self.initial_lock))
        self.assertIsNone(self.api.lock_file)

    def test_daemon_server_shutdown_releases_lock(self):
        # Verificar que el método shutdown() de PyxisDaemonServer invoca release_lock en main_api
        daemon_server = PyxisDaemonServer(main_api=self.api)
        self.assertTrue(os.path.exists(self.initial_lock))

        with patch("threading.Thread"):  # Prevenir que _deferred_exit lance un hilo con os._exit
            daemon_server.shutdown()

        self.assertFalse(os.path.exists(self.initial_lock))
        self.assertIsNone(self.api.lock_file)

    def test_reopen_session_cleans_dangling_previous_lock(self):
        # Si había un lock previo colgado y llega una nueva sesión, se debe limpiar el previo
        old_lock = self.initial_lock
        new_lock = os.path.join(self.appdata_dir, "PyxisNodes", "temp", "pyxis_lock_second.txt")
        with open(new_lock, "w", encoding="utf-8") as f:
            f.write("1")

        daemon_server = PyxisDaemonServer(main_api=self.api, window=MagicMock())
        daemon_server.reopen_session({"lock_file": new_lock})

        self.assertFalse(os.path.exists(old_lock), "El lock viejo debió ser purgado al recibir la nueva sesión")
        self.assertEqual(self.api.lock_file, new_lock)

        # Y al liberar, se borra el nuevo
        self.api.release_lock()
        self.assertFalse(os.path.exists(new_lock))

    def test_on_closing_with_daemon_disabled(self):
        # Cuando daemon_mode es False, on_closing debe liberar el lock y llamar a shutdown_daemon
        self.api.get_user_config = MagicMock(return_value={"daemon_mode": False})
        with patch.object(self.api, "release_lock") as mock_release,              patch.object(self.api, "shutdown_daemon") as mock_shutdown:
            
            # Ejecutar secuencia idéntica a on_closing()
            self.api.release_lock()
            config = self.api.get_user_config()
            if not config.get("daemon_mode", True):
                self.api.shutdown_daemon()

            self.assertTrue(mock_release.called)
            self.assertTrue(mock_shutdown.called)

    def test_complete_and_hide_releases_lock(self):
        self.assertTrue(os.path.exists(self.initial_lock))
        with patch.object(self.api, "shutdown_daemon"):
            self.api.complete_and_hide()
        self.assertFalse(os.path.exists(self.initial_lock))
        self.assertIsNone(self.api.lock_file)

    def test_default_bg_mode_is_cover(self):
        cfg = self.api.get_user_config()
        self.assertEqual(cfg.get("bg_image_mode"), "cover")

    def test_reopen_session_restores_maximized_window(self):
        mock_window = MagicMock()
        daemon_server = PyxisDaemonServer(main_api=self.api, window=mock_window)
        self.api._saved_window_state = {"maximized": True, "width": 1920, "height": 1080}

        daemon_server.reopen_session({})

        mock_window.show.assert_called_once()
        mock_window.maximize.assert_called_once()
        mock_window.restore.assert_not_called()

    def test_reopen_session_restores_window_dimensions_when_not_maximized(self):
        mock_window = MagicMock()
        daemon_server = PyxisDaemonServer(main_api=self.api, window=mock_window)
        self.api._saved_window_state = {"maximized": False, "width": 1600, "height": 900}

        daemon_server.reopen_session({})

        mock_window.show.assert_called_once()
        mock_window.restore.assert_called_once()
    def test_bring_to_foreground_does_not_unmaximize_when_maximized(self):
        with patch("ctypes.windll.user32") as mock_user32, \
             patch("ctypes.windll.kernel32") as mock_kernel32, \
             patch("os.getpid", return_value=1234):
            mock_user32.FindWindowW.return_value = 5678
            mock_user32.IsZoomed.return_value = 1
            mock_user32.IsIconic.return_value = 0

            PyxisDaemonServer.bring_to_foreground("Test Window", is_maximized=True)

            # SW_MAXIMIZE es 3, SW_RESTORE es 9
            # Verificar que ShowWindow fue llamado con SW_MAXIMIZE (3) y NUNCA con SW_RESTORE (9)
            called_show_cmds = [call_args[0][1] for call_args in mock_user32.ShowWindow.call_args_list]
            self.assertIn(3, called_show_cmds)
            self.assertNotIn(9, called_show_cmds)


if __name__ == "__main__":
    unittest.main()

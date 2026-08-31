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
import time
import threading
import urllib.request
try:
    from http.server import ThreadingHTTPServer as HTTPServer, BaseHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler

PYXIS_DAEMON_PORT = 28723


class PyxisDaemonHandler(BaseHTTPRequestHandler):
    daemon_context = None

    def log_message(self, format, *args):
        # Silenciar logs HTTP de la consola
        pass

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        if self.path == "/status":
            self._send_json({
                "status": "ok",
                "version": "1.0.5",
                "pid": os.getpid(),
                "daemon_mode": getattr(self.daemon_context, "daemon_mode", True)
            })
        elif self.path.startswith("/media_file") or self.path.startswith("/bg_media/"):
            try:
                from urllib.parse import parse_qs, urlparse
                parsed = urlparse(self.path)
                file_path = None
                if self.path.startswith("/bg_media/"):
                    f_name = parsed.path.replace("/bg_media/", "").strip()
                    appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
                    file_path = os.path.join(appdata_dir, "PyxisNodes", "bg_media", f_name)
                else:
                    params = parse_qs(parsed.query)
                    file_path = params.get("path", [None])[0]

                if file_path and os.path.isfile(file_path):
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(file_path)
                    mime_type = mime_type or "video/mp4"
                    file_size = os.path.getsize(file_path)

                    range_header = self.headers.get("Range")
                    if range_header:
                        bytes_range = range_header.replace("bytes=", "").split("-")
                        start = int(bytes_range[0]) if bytes_range[0] else 0
                        end = int(bytes_range[1]) if len(bytes_range) > 1 and bytes_range[1] else file_size - 1

                        if start >= file_size or start < 0 or (end is not None and end < start):
                            self.send_response(416)
                            self.send_header("Content-Range", f"bytes */{file_size}")
                            self.send_header("Accept-Ranges", "bytes")
                            self.end_headers()
                            return

                        end = min(end, file_size - 1)
                        chunk_size = end - start + 1

                        self.send_response(206)
                        self.send_header("Content-Type", mime_type)
                        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                        self.send_header("Content-Length", str(chunk_size))
                        self.send_header("Accept-Ranges", "bytes")
                        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                        self.send_header("Access-Control-Allow-Headers", "*")
                        self.end_headers()

                        with open(file_path, "rb") as f:
                            f.seek(start)
                            remaining = chunk_size
                            buffer_size = 65536
                            while remaining > 0:
                                to_read = min(buffer_size, remaining)
                                chunk_data = f.read(to_read)
                                if not chunk_data:
                                    break
                                self.wfile.write(chunk_data)
                                remaining -= len(chunk_data)
                    else:
                        self.send_response(200)
                        self.send_header("Content-Type", mime_type)
                        self.send_header("Content-Length", str(file_size))
                        self.send_header("Accept-Ranges", "bytes")
                        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                        self.send_header("Access-Control-Allow-Headers", "*")
                        self.end_headers()

                        with open(file_path, "rb") as f:
                            buffer_size = 65536
                            while True:
                                chunk_data = f.read(buffer_size)
                                if not chunk_data:
                                    break
                                self.wfile.write(chunk_data)
                    return
            except (BrokenPipeError, ConnectionResetError):
                # Desconexión normal del reproductor durante seek o carga inicial
                return
            except Exception as e:
                print(f"[Pyxis Daemon Media Stream Error] {e}", flush=True)
            try:
                self.send_error(404, "File Not Found")
            except Exception:
                pass
        elif ".well-known" in self.path or "devtools" in self.path:
            self._send_json({}, 200)
        else:
            self._send_json({"error": "not_found"}, 404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            payload = {}

        if self.path == "/reopen":
            if self.daemon_context and hasattr(self.daemon_context, "reopen_session"):
                success = self.daemon_context.reopen_session(payload)
                self._send_json({"status": "reopened" if success else "error"})
            else:
                self._send_json({"status": "error", "message": "no context"}, 500)

        elif self.path == "/shutdown":
            self._send_json({"status": "shutting_down"})
            threading.Thread(target=self.daemon_context.shutdown, daemon=True).start()
        else:
            self._send_json({"error": "not_found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


class PyxisDaemonServer:
    def __init__(self, main_api=None, window=None):
        self.main_api = main_api
        self.window = window
        self.server = None
        self.server_thread = None
        self.aegisub_pid = None
        self.daemon_mode = True
        self.running = False
        self._is_shutting_down = False

    def start(self, port=PYXIS_DAEMON_PORT):
        if self.running:
            return
        PyxisDaemonHandler.daemon_context = self
        try:
            self.server = HTTPServer(("127.0.0.1", port), PyxisDaemonHandler)
            self.running = True
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            print(f"[Pyxis Daemon] Servidor escuchando en http://127.0.0.1:{port} (PID: {os.getpid()})", flush=True)

            # Iniciar hilo de monitoreo de proceso padre Aegisub
            threading.Thread(target=self._monitor_aegisub_pid, daemon=True).start()
        except Exception as e:
            print(f"[Pyxis Daemon Warning] No se pudo iniciar el puerto {port}: {e}", flush=True)

    def _monitor_aegisub_pid(self):
        """Si Aegisub se cierra, el daemon finaliza automáticamente para no dejar procesos colgados."""
        while self.running:
            time.sleep(1.0)
            if self.aegisub_pid:
                if not self.is_pid_alive(self.aegisub_pid):
                    print(f"[Pyxis Daemon] Aegisub (PID {self.aegisub_pid}) se ha cerrado. Apagando servidor daemon.", flush=True)
                    self.shutdown()
                    break

    @staticmethod
    def is_pid_alive(pid):
        if not pid:
            return True
        try:
            import psutil
            if psutil.pid_exists(int(pid)):
                proc = psutil.Process(int(pid))
                return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            return False
        except Exception:
            pass

        try:
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259

            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
            if not handle:
                return False
            exit_code = wintypes.DWORD()
            success = kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            kernel32.CloseHandle(handle)
            if success:
                return exit_code.value == STILL_ACTIVE
            return False
        except Exception:
            return False

    def reopen_session(self, payload):
        if not self.window:
            return False

        try:
            temp_ass = payload.get("temp_ass")
            result_file = payload.get("result_file")
            lock_file = payload.get("lock_file")
            session_file = payload.get("session_file")
            aegisub_version = payload.get("aegisub_version", "unknown")
            aegisub_pid = payload.get("aegisub_pid")

            if aegisub_pid:
                self.aegisub_pid = aegisub_pid

            if self.main_api:
                # Si existía un lock previo no liberado, liberarlo antes de adoptar el nuevo
                if getattr(self.main_api, "lock_file", None) and self.main_api.lock_file != lock_file:
                    if hasattr(self.main_api, "release_lock"):
                        try:
                            self.main_api.release_lock()
                        except Exception:
                            pass

                self.main_api.temp_ass = temp_ass or self.main_api.temp_ass
                self.main_api.result_file = result_file or self.main_api.result_file
                self.main_api.lock_file = lock_file or getattr(self.main_api, "lock_file", None)
                self.main_api.session_file = session_file or self.main_api.session_file
                self.main_api.aegisub_version = aegisub_version or self.main_api.aegisub_version
                if hasattr(self.main_api, "invalidate_aegisub_cache"):
                    self.main_api.invalidate_aegisub_cache()
                else:
                    self.main_api._cached_aegisub_info = None
                if hasattr(self.main_api, "invalidate_preview_base_cache"):
                    self.main_api.invalidate_preview_base_cache()
                else:
                    self.main_api._cached_preview_base_info = None

            # Mostrar y traer al frente la ventana restaurando el formato previo
            try:
                saved_state = getattr(self.main_api, "_saved_window_state", None)
                if not saved_state and hasattr(self.main_api, "get_user_config"):
                    try:
                        cfg = self.main_api.get_user_config()
                        saved_state = cfg.get("window_state")
                    except Exception:
                        pass

                is_max = bool(saved_state and saved_state.get("maximized"))

                self.window.show()
                if is_max:
                    self.window.maximize()
                else:
                    self.window.restore()
                    if saved_state and saved_state.get("width") and saved_state.get("height"):
                        try:
                            self.window.resize(saved_state["width"], saved_state["height"])
                        except Exception:
                            pass
                self.window.focus()
            except Exception as e:
                print(f"[Pyxis Daemon Warning Window Reopen] {e}", flush=True)

            if self.window and getattr(self.window, "title", None):
                self.bring_to_foreground(self.window.title, is_maximized=is_max)

            # Notificar al frontend en JS para reanudar reproductores y recargar el subtítulo (con la ventana ya visible)
            try:
                js_code = "if (window.PyxisNodePlayerManager && typeof window.PyxisNodePlayerManager.resumeFromDaemon === 'function') window.PyxisNodePlayerManager.resumeFromDaemon(); if (window.__pyxis_reload_subtitles) window.__pyxis_reload_subtitles();"
                self.window.evaluate_js(js_code)
            except Exception as e:
                print(f"[Pyxis Daemon Warning JS Reload] {e}", flush=True)

            return True
        except Exception as e:
            print(f"[Pyxis Daemon Error Reopen] {e}", flush=True)
            return False

    @classmethod
    def bring_to_foreground(cls, title=None, is_maximized=False):
        try:
            import ctypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            my_pid = os.getpid()
            found_hwnd = None

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            def enum_windows_callback(hwnd, lParam):
                nonlocal found_hwnd
                lpdwProcessId = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lpdwProcessId))
                if lpdwProcessId.value == my_pid:
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        if "Pyxis" in buff.value or "Engine" in buff.value or not title or str(title) in buff.value:
                            found_hwnd = hwnd
                            return False
                return True

            cb = WNDENUMPROC(enum_windows_callback)
            user32.EnumWindows(cb, 0)

            if not found_hwnd and title:
                found_hwnd = user32.FindWindowW(None, str(title))

            if not found_hwnd:
                return False

            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                ico_path = os.path.join(script_dir, "web", "icon.ico")
                if os.path.exists(ico_path):
                    from ctypes import wintypes
                    WM_SETICON = 0x0080
                    ICON_SMALL = 0
                    ICON_BIG = 1
                    LR_LOADFROMFILE = 0x0010
                    IMAGE_ICON = 1

                    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
                    user32.LoadImageW.restype = wintypes.HANDLE

                    sm_cx = user32.GetSystemMetrics(49) or 16
                    sm_cy = user32.GetSystemMetrics(50) or 16
                    big_cx = user32.GetSystemMetrics(11) or 32
                    big_cy = user32.GetSystemMetrics(12) or 32

                    h_icon_big = user32.LoadImageW(None, ico_path, IMAGE_ICON, big_cx, big_cy, LR_LOADFROMFILE)
                    h_icon_small = user32.LoadImageW(None, ico_path, IMAGE_ICON, sm_cx, sm_cy, LR_LOADFROMFILE)

                    if h_icon_big:
                        user32.SendMessageW(found_hwnd, WM_SETICON, ICON_BIG, h_icon_big)
                    if h_icon_small:
                        user32.SendMessageW(found_hwnd, WM_SETICON, ICON_SMALL, h_icon_small)
            except Exception:
                pass

            SW_MAXIMIZE = 3
            SW_SHOW = 5
            SW_RESTORE = 9
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_SHOWWINDOW = 0x0040

            fore_thread = user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), None)
            app_thread = kernel32.GetCurrentThreadId()

            attached = False
            if fore_thread != app_thread and fore_thread != 0:
                attached = user32.AttachThreadInput(fore_thread, app_thread, True)

            try:
                # Si la ventana debe estar maximizada o ya está maximizada,
                # nunca invocar SW_RESTORE (9) porque Windows la des-maximiza y la devuelve a 720p.
                if is_maximized or user32.IsZoomed(found_hwnd):
                    user32.ShowWindow(found_hwnd, SW_MAXIMIZE)
                elif user32.IsIconic(found_hwnd):
                    user32.ShowWindow(found_hwnd, SW_RESTORE)
                else:
                    user32.ShowWindow(found_hwnd, SW_SHOW)

                user32.SetForegroundWindow(found_hwnd)
                user32.BringWindowToTop(found_hwnd)
            finally:
                if attached:
                    user32.AttachThreadInput(fore_thread, app_thread, False)

            user32.SetWindowPos(found_hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
            user32.SetWindowPos(found_hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
            return True
        except Exception as e:
            print(f"[Pyxis Daemon Warning Focus] {e}", flush=True)
            return False

    def shutdown(self):
        if self._is_shutting_down:
            return
        self._is_shutting_down = True
        self.running = False

        if self.main_api and hasattr(self.main_api, "release_lock"):
            try:
                self.main_api.release_lock()
            except Exception:
                pass

        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass

        def _deferred_exit():
            time.sleep(0.1)
            if self.window:
                try:
                    self.window.destroy()
                except Exception:
                    pass
            os._exit(0)

        threading.Thread(target=_deferred_exit, daemon=True).start()


def check_daemon_running(port=PYXIS_DAEMON_PORT):
    try:
        url = f"http://127.0.0.1:{port}/status"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data
    except Exception:
        pass
    return None


def notify_daemon_reopen(payload, port=PYXIS_DAEMON_PORT):
    try:
        url = f"http://127.0.0.1:{port}/reopen"
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("status") == "reopened"
    except Exception as e:
        print(f"[Pyxis Notify Daemon Error] {e}", flush=True)
    return False



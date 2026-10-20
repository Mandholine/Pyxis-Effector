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
# For any question you can visit: https://discord.gg/fsxRESeQZN

"""Pyxis Effector — Main PyWebView application bootstrap and JS-Python API bridge.

Provides the primary graphical runtime for Pyxis Node Engine 1.1.4, managing
PyWebView window initialisation, thread pooling, log buffering, OS job objects,
configuration persistence, template storage, dialogue windows, script syntax
validation, and communication bridges between client-side JavaScript and backend
Python routines.
"""

import json
import os
import re
import socketserver
import subprocess
import sys
import traceback
import uuid
import wsgiref.simple_server
from datetime import datetime, timezone

socketserver.TCPServer.request_queue_size = 256
wsgiref.simple_server.WSGIServer.request_queue_size = 256

class _LogBufferStream:
    """Tee stream capturing standard output and error into an in-memory buffer.

    Maintains a rolling ring buffer of console output (up to 3,000 entries)
    to facilitate runtime diagnostics and integrated debug console inspection
    without blocking standard stdout and stderr forwarding.
    """
    _buffer = []
    _max_buffer = 3000

    def __init__(self, original_stream=None):
        """Initialises the logging stream wrapper.

        Args:
            original_stream (io.TextIOBase, optional): Underlying stream to receive
                mirrored writes. Defaults to None.
        """
        self.original_stream = original_stream

    @classmethod
    def clear(cls):
        """Empties the accumulated in-memory log buffer."""
        cls._buffer.clear()

    @classmethod
    def get_logs(cls):
        """Retrieves a shallow copy of all log lines currently held in the ring buffer.

        Returns:
            list[str]: Copy of collected log strings.
        """
        return list(cls._buffer)

    def write(self, s):
        """Appends output to the internal ring buffer and forwards to original_stream.

        Args:
            s (str): String snippet to record.
        """
        if s:
            _LogBufferStream._buffer.append(s)
            if len(_LogBufferStream._buffer) > _LogBufferStream._max_buffer:
                _LogBufferStream._buffer.pop(0)
            if self.original_stream:
                try:
                    self.original_stream.write(s)
                    self.original_stream.flush()
                except Exception:
                    pass

    def flush(self):
        """Flushes the underlying stream if present."""
        if self.original_stream:
            try:
                self.original_stream.flush()
            except Exception:
                pass

ORIGINAL_STDOUT = sys.stdout
ORIGINAL_STDERR = sys.stderr
GLOBAL_STDOUT_STREAM = _LogBufferStream(ORIGINAL_STDOUT)
GLOBAL_STDERR_STREAM = _LogBufferStream(ORIGINAL_STDERR)

sys.stdout = GLOBAL_STDOUT_STREAM
sys.stderr = GLOBAL_STDERR_STREAM
import atexit
import webview
try:
    import webview.http
    if hasattr(webview.http, 'WSGIServer'):
        webview.http.WSGIServer.request_queue_size = 256
except Exception:
    pass

try:
    from version import (
        PYXIS_VERSION as PYXIS_ENGINE_VERSION,
        PYXIS_APP_ID,
        PYXIS_CLIENT_AUTH,
        PYXIS_STAGE,
        PYXIS_FULL_VERSION,
        PYXIS_VERSION_STRING
    )
except ImportError:
    PYXIS_ENGINE_VERSION = "1.1.4"
    PYXIS_APP_ID = "Mandholine.Pyxis.NodeEngine.1.1.4"
    PYXIS_CLIENT_AUTH = "pyxis-beta-1.1.4-client"
    PYXIS_STAGE = "Beta"
    PYXIS_FULL_VERSION = "Beta v1.1.4"
    PYXIS_VERSION_STRING = "v1.1.4"

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(PYXIS_APP_ID)
    except Exception:
        pass


def _apply_pyxis_window_icon(hwnd=None):
    """Sets the high-resolution and low-resolution window icons on Windows.

    Resolves the application icon (`icon.ico` or converts from `icon.png`),
    locates the Pyxis engine window handle via Win32 `EnumWindows` if not
    explicitly provided, and dispatches `WM_SETICON` messages for both
    `ICON_BIG` (32x32) and `ICON_SMALL` (16x16).

    Args:
        hwnd (int, optional): Explicit Win32 window handle. If None, the window
            is located dynamically by process ID and title match.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32

        try:
            from paths import get_web_path
            ico_path = get_web_path("icon.ico")
            png_path = get_web_path("icon.png")
        except Exception:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            ico_path = os.path.join(script_dir, "..", "web", "icon.ico")
            png_path = os.path.join(script_dir, "..", "web", "icon.png")
            if not os.path.exists(ico_path):
                ico_path = os.path.join(script_dir, "web", "icon.ico")
                png_path = os.path.join(script_dir, "web", "icon.png")
            if os.path.exists(png_path):
                try:
                    from PIL import Image
                    im = Image.open(png_path).convert("RGBA")
                    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
                    resized_list = [im.resize(s, Image.Resampling.LANCZOS) for s in sizes]
                    resized_list[0].save(ico_path, format="ICO", sizes=sizes, append_images=resized_list[1:])
                except Exception:
                    pass

        if not os.path.exists(ico_path):
            return

        if not hwnd:
            kernel32 = ctypes.windll.kernel32
            con_hwnd = kernel32.GetConsoleWindow() if hasattr(kernel32, "GetConsoleWindow") else None
            my_pid = os.getpid()
            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            def enum_cb(h, l):
                nonlocal hwnd
                if con_hwnd and h == con_hwnd:
                    return True
                cls_buff = ctypes.create_unicode_buffer(64)
                user32.GetClassNameW(h, cls_buff, 64)
                if cls_buff.value == "ConsoleWindowClass":
                    return True
                lp = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(h, ctypes.byref(lp))
                if lp.value == my_pid:
                    length = user32.GetWindowTextLengthW(h)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(h, buff, length + 1)
                        if "Pyxis Node Engine" in buff.value:
                            hwnd = h
                            return False
                return True
            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

        if hwnd:
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
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon_big)
            if h_icon_small:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon_small)
    except Exception as e:
        print(f"[Pyxis Apply Icon Error] {e}", flush=True)


def _setup_windows_job_object():
    """Binds the Python process to a Windows Job Object with kill-on-close policy.

    Ensures that whenever the host process terminates, crashes, or is cancelled,
    the Windows kernel immediately terminates all child processes (such as
    multiprocessing worker pools, FFmpeg, or Potrace) to eliminate zombie tasks.

    Returns:
        int | None: Win32 handle to the created job object, or None if setup failed.
    """
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ('ReadOperationCount', ctypes.c_uint64),
                ('WriteOperationCount', ctypes.c_uint64),
                ('OtherOperationCount', ctypes.c_uint64),
                ('ReadTransferCount', ctypes.c_uint64),
                ('WriteTransferCount', ctypes.c_uint64),
                ('OtherTransferCount', ctypes.c_uint64),
            ]

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('PerProcessUserTimeLimit', ctypes.c_int64),
                ('PerJobUserTimeLimit', ctypes.c_int64),
                ('LimitFlags', wintypes.DWORD),
                ('MinimumWorkingSetSize', ctypes.c_size_t),
                ('MaximumWorkingSetSize', ctypes.c_size_t),
                ('ActiveProcessLimit', wintypes.DWORD),
                ('Affinity', ctypes.c_size_t),
                ('PriorityClass', wintypes.DWORD),
                ('SchedulingClass', wintypes.DWORD),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ('IoInfo', IO_COUNTERS),
                ('ProcessMemoryLimit', ctypes.c_size_t),
                ('JobMemoryLimit', ctypes.c_size_t),
                ('PeakProcessMemoryUsed', ctypes.c_size_t),
                ('PeakJobMemoryUsed', ctypes.c_size_t),
            ]

        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
        JobObjectExtendedLimitInformation = 9

        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return None

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

        ok = kernel32.SetInformationJobObject(
            job,
            JobObjectExtendedLimitInformation,
            ctypes.byref(info),
            ctypes.sizeof(info)
        )
        if ok:
            h_proc = kernel32.OpenProcess(0x1F0FFF, False, os.getpid())
            if h_proc:
                kernel32.AssignProcessToJobObject(job, h_proc)
                kernel32.CloseHandle(h_proc)
                return job
    except Exception as e:
        print(f"[Pyxis Warning JobObject Setup] {e}", flush=True)
    return None

_GLOBAL_JOB_OBJECT = _setup_windows_job_object()

def _cleanup_at_exit():
    """At-exit handler ensuring all global multiprocessing worker pools are aborted."""
    try:
        from node_engine import abort_global_multiprocessing
        abort_global_multiprocessing()
    except Exception:
        pass
atexit.register(_cleanup_at_exit)


def _atomic_write(path, data):
    """Writes text data atomically to disk with explicit directory creation and sync.

    Writes initially to a hidden sibling file (`<path>.tmp`), flushes buffers,
    issues `os.fsync`, and atomically replaces the target using `os.replace`.

    Args:
        path (str): Target filesystem path.
        data (str): Text content to write.
    """
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(data)
            file_handle.flush()
            os.fsync(file_handle.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            with open(path, "w", encoding="utf-8") as file_handle:
                file_handle.write(data)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass


def _to_int_or_default(value, default=None):
    """Safely converts an arbitrary scalar value to an integer with a fallback.

    Args:
        value (Any): Input value to parse.
        default (int | None, optional): Fallback value if conversion fails or
            input is empty. Defaults to None.

    Returns:
        int | None: Parsed integer or default value.
    """
    if value is None:
        return default
    if isinstance(value, int):
        return value
    try:
        s = str(value).strip()
        if not s:
            return default
        return int(float(s))
    except Exception:
        return default



class PyxisAPI:
    """Primary JavaScript-Python bridge exposed to the PyWebView graphical interface.

    Coordinates session parameters, configuration storage, theme management,
    integrated console logs, bug reporting, background media, file diálogos,
    template persistence, and execution pipelines between the frontend web canvas
    and backend rendering routines.
    """

    def __init__(self, temp_ass, result_file, session_file, aegisub_version="unknown", lock_file=None):
        """Initialises the Pyxis API bridge instance with session parameters.

        Args:
            temp_ass (str): Path to the temporary ASS subtitle file exported by Aegisub.
            result_file (str): Destination path for generated ASS dialogue lines.
            session_file (str): Path to the session state file.
            aegisub_version (str, optional): Version string of the calling Aegisub instance.
            lock_file (str | None, optional): Path to the Aegisub lockfile indicating active edit.
        """
        self.temp_ass = temp_ass
        self.result_file = result_file
        self.session_file = session_file
        self.aegisub_version = aegisub_version
        self.lock_file = lock_file
        self._initial_lock_file = lock_file
        self._daemon_server = None
        self.system_templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        self.user_templates_dir = os.path.join(appdata_dir, "PyxisNodes", "templates")
        os.makedirs(self.user_templates_dir, exist_ok=True)
        self.templates_dir = self.user_templates_dir
        self._store = None
        self._active_engine = None
        self._cached_preview_base_info = None
        self._load_and_cache_preview_base()
        self._cached_docs_toc = None
        self._cached_node_map = None

        import threading
        self._clip_lock = threading.RLock()

        try:
            threading.Thread(target=self.cleanup_temp_files, kwargs={"max_age_hours": 72}, daemon=True).start()
            threading.Thread(target=self._purge_corrupted_bg_media, daemon=True).start()
        except Exception as e:
            print(f"[Pyxis] Error starting background maintenance threads: {e}", flush=True)

    def release_lock(self):
        """Atomically and reliably releases the lock file for Aegisub on Windows.

        Includes retries with micro-pauses (up to 6 attempts) to prevent
        WinError 32 sharing collisions when the calling Lua macro in Aegisub
        is concurrently polling the file.
        """
        targets = []
        if hasattr(self, "lock_file") and self.lock_file:
            targets.append(self.lock_file)
        if hasattr(self, "_initial_lock_file") and self._initial_lock_file:
            targets.append(self._initial_lock_file)

        for path in set(targets):
            if not path or not os.path.exists(path):
                continue
            for attempt in range(6):
                try:
                    os.remove(path)
                    break
                except OSError:
                    import time
                    time.sleep(0.02)
        self.lock_file = None

    def get_version_info(self):
        """Returns the canonical Pyxis engine version information dictionary.

        Returns:
            dict: Structured dictionary with version, stage, full_version, and app_id.
        """
        return {
            "version": PYXIS_ENGINE_VERSION,
            "stage": PYXIS_STAGE,
            "version_string": PYXIS_VERSION_STRING,
            "full_version": PYXIS_FULL_VERSION,
            "app_id": PYXIS_APP_ID,
        }

    def get_console_logs(self):
        """Returns the accumulated in-memory log buffer for the integrated debug console.

        Returns:
            dict[str, Any]: Dictionary containing status flag and list of log strings.
        """
        try:
            return {
                "success": True,
                "logs": _LogBufferStream.get_logs()
            }
        except Exception as e:
            return {"success": False, "error": str(e), "logs": []}

    def clear_console_logs(self):
        """Clears the accumulated in-memory log buffer.

        Returns:
            dict[str, Any]: Status dictionary indicating operation success or error.
        """
        try:
            _LogBufferStream.clear()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_bug_report(self, payload):
        """Transmits a structured bug report payload to the Cloudflare Worker proxy.

        Enforces a 15-second client-side cooldown to prevent duplicate submissions,
        assembles diagnostic telemetry (engine version, OS, Python runtime, Aegisub
        version, GPU backend, screen resolution, backend logs), and dispatches an
        HTTP POST request.

        Args:
            payload (dict): Submission data containing user intent, failure
                description, optional base64 canvas screenshot, and diagnostic options.

        Returns:
            dict[str, Any]: Result dictionary with `success`, optional `cooldown`,
                or error details.
        """
        import json
        import time
        import urllib.request
        import urllib.error
        import platform

        if not hasattr(self, "_last_bug_report_time"):
            self._last_bug_report_time = 0.0

        now = time.time()
        # Cooldown de 15 segundos para evitar envíos dobles o accidentales
        if now - self._last_bug_report_time < 15.0:
            remaining = int(15.0 - (now - self._last_bug_report_time))
            return {
                "success": False,
                "error": f"Cooldown active. Please wait {remaining} seconds.",
                "cooldown": True
            }

        if not isinstance(payload, dict):
            return {"success": False, "error": "Invalid payload format"}

        intent = str(payload.get("intent") or "").strip()
        failure = str(payload.get("failure") or "").strip()
        if not intent or not failure:
            return {"success": False, "error": "Intent and failure descriptions are required"}

        worker_url = payload.get("worker_url") or getattr(self, "_bug_report_worker_url", None)
        if not worker_url:
            worker_url = os.environ.get("PYXIS_BUG_REPORT_WORKER_URL") or "https://pyxis-bugs-reports.mandholine.workers.dev"

        gpu_info = "Unknown"
        try:
            import gpu_engine
            gpu_info = getattr(gpu_engine, "ACTIVE_BACKEND", None) or "OpenCL / CPU"
        except Exception:
            pass

        diagnostics = {
            "engine_version": PYXIS_ENGINE_VERSION,
            "os": f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
            "python": platform.python_version(),
            "aegisub": getattr(self, "aegisub_version", "unknown"),
            "gpu_backend": gpu_info,
            "resolution": payload.get("resolution", "unknown"),
            "devtools_logs": payload.get("devtools_logs") if payload.get("include_diagnostics", True) else [],
            "backend_logs": _LogBufferStream.get_logs()[-100:] if payload.get("include_diagnostics", True) else [],
        }

        full_payload = {
            "intent": intent,
            "failure": failure,
            "image_base64": payload.get("image_base64"),
            "diagnostics": diagnostics,
        }

        try:
            req_data = json.dumps(full_payload).encode("utf-8")
            req = urllib.request.Request(
                worker_url,
                data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"Pyxis-Effector/{PYXIS_ENGINE_VERSION}",
                    "X-Pyxis-Client-Auth": PYXIS_CLIENT_AUTH,
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                status_code = response.getcode()
                resp_text = response.read().decode("utf-8")
                try:
                    resp_json = json.loads(resp_text)
                except Exception:
                    resp_json = {"success": status_code == 200}

                if resp_json.get("success"):
                    self._last_bug_report_time = now
                    return {"success": True}
                else:
                    return {
                        "success": False,
                        "error": resp_json.get("error", f"Worker returned status {status_code}")
                    }
        except urllib.error.HTTPError as he:
            err_body = ""
            try:
                err_body = he.read().decode("utf-8")
                err_json = json.loads(err_body)
                if "error" in err_json:
                    err_body = err_json["error"]
            except Exception:
                pass
            return {"success": False, "error": f"HTTP {he.code}: {err_body or he.reason}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_external_url(self, url):
        """Safely opens a web URL or mailto link in the OS default browser or mail client.

        Args:
            url (str): Target URL starting with http://, https://, or mailto:.

        Returns:
            bool: True if launched successfully, False if blocked or invalid.
        """
        import webbrowser
        try:
            url_str = str(url or "").strip()
            if url_str.startswith("https://") or url_str.startswith("http://") or url_str.startswith("mailto:"):
                webbrowser.open(url_str)
                return True
        except Exception:
            pass
        return False

    @property
    def template_store(self):
        """Provides a lazily-instantiated TemplateStore singleton instance."""
        if self._store is None:
            from template_store import TemplateStore
            self._store = TemplateStore(
                templates_dir=self.system_templates_dir,
                aegisub_version=self.aegisub_version,
                user_templates_dir=self.user_templates_dir,
            )
        return self._store

    def _get_config_path(self):
        """Resolves the absolute path to user_config.json under the user's APPDATA directory."""
        appdata_dir = os.environ.get("APPDATA")
        if not appdata_dir:
            appdata_dir = os.path.expanduser("~")
        pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
        os.makedirs(pyxis_config_dir, exist_ok=True)
        return os.path.join(pyxis_config_dir, "user_config.json")

    def _get_bg_media_dir(self):
        """Resolves the directory storing background video and poster assets."""
        appdata_dir = os.environ.get("APPDATA")
        if not appdata_dir:
            appdata_dir = os.path.expanduser("~")
        bg_media_dir = os.path.join(appdata_dir, "PyxisNodes", "bg_media")
        os.makedirs(bg_media_dir, exist_ok=True)
        return bg_media_dir

    def _get_bg_image_path(self):
        """Resolves the active background image path (preferring WebP over PNG)."""
        appdata_dir = os.environ.get("APPDATA")
        if not appdata_dir:
            appdata_dir = os.path.expanduser("~")
        pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
        os.makedirs(pyxis_config_dir, exist_ok=True)
        webp_path = os.path.join(pyxis_config_dir, "bg_image.webp")
        png_path = os.path.join(pyxis_config_dir, "bg_image.png")
        if not os.path.exists(webp_path) and os.path.exists(png_path):
            return png_path
        return webp_path

    def _get_default_back_path(self):
        """Locates the default bundled background image across multiple candidate paths."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
        candidates = [
            os.path.join(script_dir, "..", "web", "default_back.webp"),
            os.path.join(script_dir, "web", "default_back.webp"),
            os.path.join(script_dir, "..", "default_back.webp"),
            os.path.join(script_dir, "default_back.webp"),
            os.path.join(pyxis_config_dir, "default_back.webp")
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

    def _get_bg_media_info(self):
        """Inspects and returns metadata regarding active background video or image.

        Returns:
            dict[str, Any]: Dictionary detailing `has_bg`, `media_type` ('video',
                'image', or 'none'), loopback media streaming URLs, poster URLs,
                or base64 data URLs.
        """
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
        bg_media_dir = os.path.join(pyxis_config_dir, "bg_media")

        poster_path = os.path.join(bg_media_dir, "bg_poster.webp")
        active_video = None
        for ext in [".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"]:
            v_check = os.path.join(bg_media_dir, f"bg_video{ext}")
            if os.path.exists(v_check):
                active_video = v_check
                break

        webp_path = os.path.join(pyxis_config_dir, "bg_image.webp")
        png_path = os.path.join(pyxis_config_dir, "bg_image.png")
        active_image = webp_path if os.path.exists(webp_path) else (png_path if os.path.exists(png_path) else None)

        import urllib.parse
        if active_video:
            mtime = int(os.path.getmtime(active_video) * 1000) if os.path.exists(active_video) else 0
            v_url = f"http://127.0.0.1:28723/media_file?path={urllib.parse.quote(active_video)}&t={mtime}"
            p_mtime = int(os.path.getmtime(poster_path) * 1000) if os.path.exists(poster_path) else 0
            p_url = f"http://127.0.0.1:28723/media_file?path={urllib.parse.quote(poster_path)}&t={p_mtime}" if os.path.exists(poster_path) else ""
            return {
                "has_bg": True,
                "media_type": "video",
                "video_url": v_url,
                "poster_url": p_url,
                "data_url": "",
                "is_default": False
            }
        elif active_image:
            try:
                import base64
                import mimetypes
                mime_type, _ = mimetypes.guess_type(active_image)
                mime_type = mime_type or ("image/webp" if active_image.endswith(".webp") else "image/png")
                with open(active_image, "rb") as img_file:
                    encoded = base64.b64encode(img_file.read()).decode("utf-8")
                data_url = f"data:{mime_type};base64,{encoded}"
                return {
                    "has_bg": True,
                    "media_type": "image",
                    "video_url": "",
                    "poster_url": "",
                    "data_url": data_url,
                    "is_default": False
                }
            except Exception as e:
                print("Pyxis: error encoding background image", e)

        no_bg = False
        try:
            config_path = self._get_config_path()
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    no_bg = bool(cfg.get("no_bg", False))
        except Exception:
            pass

        if not no_bg:
            default_back = self._get_default_back_path()
            if default_back:
                try:
                    import base64
                    with open(default_back, "rb") as img_file:
                        encoded = base64.b64encode(img_file.read()).decode("utf-8")
                    data_url = f"data:image/webp;base64,{encoded}"
                    return {
                        "has_bg": True,
                        "media_type": "image",
                        "video_url": "",
                        "poster_url": "",
                        "data_url": data_url,
                        "is_default": True
                    }
                except Exception as e:
                    print("Pyxis: error encoding default background", e)

        return {
            "has_bg": False,
            "media_type": "none",
            "video_url": "",
            "poster_url": "",
            "data_url": "",
            "is_default": False
        }

    def get_user_config(self):
        """Loads and returns user configuration settings merged with default values.

        Reads from `%APPDATA%/PyxisNodes/user_config.json`, backfilling missing
        attributes with defaults (theme, grid snapping, undo steps, background
        media opacity and mode, language, telemetry scales).

        Returns:
            dict[str, Any]: Merged configuration dictionary.
        """
        config = {
            "theme": "teal",
            "grid_mode": 1,
            "undo_steps": 30,
            "bg_image_mode": "cover",
            "bg_image_opacity": 0.85,
            "has_bg_image": False,
            "bg_media_type": "none",
            "convert_video": True,
            "daemon_mode": True,
            "language": "es",
            "active_template_id": None,
            "active_template_name": None,
            "telemetry_scales": {
                "render_ms": "auto",
                "total_kb": "auto",
                "largest_kb": "auto",
                "objects": "auto"
            },
            "telemetry_active_metrics": {
                "render_ms": True,
                "total_kb": True,
                "largest_kb": False,
                "objects": False
            }
        }
        try:
            config_path = self._get_config_path()
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        config.update(loaded)

            bg_info = self._get_bg_media_info()
            config["has_bg_image"] = bg_info["has_bg"]
            config["bg_media_type"] = bg_info["media_type"]
            config["is_default_bg"] = bg_info.get("is_default", False)
        except Exception as e:
            print("Pyxis: error reading user_config", e)
        return config

    def get_bg_image_data(self):
        """Retrieves base64 data URL for the configured background image.

        Returns:
            str: Base64 data URL or empty string if no image background is configured.
        """
        try:
            info = self._get_bg_media_info()
            return info.get("data_url", "")
        except Exception as e:
            print("Pyxis: error getting background image data", e)
        return ""

    def get_bg_media_data(self):
        """Retrieves the complete background media information dictionary.

        Returns:
            dict[str, Any]: Media metadata dictionary.
        """
        try:
            return self._get_bg_media_info()
        except Exception as e:
            print("Pyxis: error getting background media data", e)
            return {"has_bg": False, "media_type": "none", "video_url": "", "poster_url": "", "data_url": "", "is_default": False}

    def save_user_config(self, payload):
        """Persists updated user settings atomically to user_config.json.

        Supports removal of existing background assets when requested, validates
        theme identifiers and telemetry scales, persists configuration atomically,
        and dynamically updates daemon mode on the active daemon server.

        Args:
            payload (dict | str): Updated configuration dictionary or JSON string.

        Returns:
            bool: True if configuration was successfully persisted, False otherwise.
        """
        try:
            config_data = payload if isinstance(payload, dict) else json.loads(payload)
            is_removing_bg = bool(config_data.get("remove_bg_image", False) or config_data.get("remove_bg_media", False))
            
            if is_removing_bg:
                appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
                pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
                bg_media_dir = os.path.join(pyxis_config_dir, "bg_media")

                for f in ["bg_image.webp", "bg_image.png"]:
                    p = os.path.join(pyxis_config_dir, f)
                    if os.path.exists(p):
                        try: os.remove(p)
                        except OSError: pass
                for ext in [".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"]:
                    p = os.path.join(bg_media_dir, f"bg_video{ext}")
                    if os.path.exists(p):
                        try: os.remove(p)
                        except OSError: pass
                poster_p = os.path.join(bg_media_dir, "bg_poster.webp")
                if os.path.exists(poster_p):
                    try: os.remove(poster_p)
                    except OSError: pass

            config_path = self._get_config_path()
            existing_config = {}
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        loaded_existing = json.load(f)
                        if isinstance(loaded_existing, dict):
                            existing_config = loaded_existing
                except Exception:
                    pass

            is_daemon = bool(config_data["daemon_mode"]) if "daemon_mode" in config_data else bool(existing_config.get("daemon_mode", True))
            saved_theme = config_data.get("theme", existing_config.get("theme", "teal"))
            if saved_theme in ["obsidian", "cyber", "slate", "nordic"]:
                saved_theme = "teal"

            if is_removing_bg:
                no_bg = True
            elif "no_bg" in config_data:
                no_bg = bool(config_data["no_bg"])
            elif "has_bg_image" in config_data:
                if config_data["has_bg_image"] is True:
                    no_bg = False
                elif config_data["has_bg_image"] is False:
                    no_bg = True
                else:
                    no_bg = bool(existing_config.get("no_bg", False))
            else:
                no_bg = bool(existing_config.get("no_bg", False))

            if no_bg:
                bg_info = {"has_bg": False, "media_type": "none", "is_default": False}
            else:
                bg_info = self._get_bg_media_info()

            active_tpl_id = config_data.get("active_template_id", existing_config.get("active_template_id", None))
            active_tpl_name = config_data.get("active_template_name", existing_config.get("active_template_name", None))
            if "active_template_id" in config_data and config_data["active_template_id"] is None:
                active_tpl_id = None
                active_tpl_name = None

            grid_mode = config_data["grid_mode"] if "grid_mode" in config_data else existing_config.get("grid_mode", 1)
            try:
                grid_mode = int(grid_mode)
            except (ValueError, TypeError):
                grid_mode = 1

            undo_steps = config_data["undo_steps"] if "undo_steps" in config_data else existing_config.get("undo_steps", 30)
            try:
                undo_steps = int(undo_steps)
            except (ValueError, TypeError):
                undo_steps = 30

            bg_image_mode = config_data["bg_image_mode"] if "bg_image_mode" in config_data else existing_config.get("bg_image_mode", "cover")
            
            bg_image_opacity = config_data["bg_image_opacity"] if "bg_image_opacity" in config_data else existing_config.get("bg_image_opacity", 0.85)
            try:
                bg_image_opacity = float(bg_image_opacity)
            except (ValueError, TypeError):
                bg_image_opacity = 0.85

            convert_video = bool(config_data["convert_video"]) if "convert_video" in config_data else bool(existing_config.get("convert_video", True))
            language = config_data.get("language", existing_config.get("language", "es"))
            window_state = config_data.get("window_state", existing_config.get("window_state", getattr(self, "_saved_window_state", {})))

            default_tel_scales = {
                "render_ms": "auto",
                "total_kb": "auto",
                "largest_kb": "auto",
                "objects": "auto"
            }
            raw_tel_scales = config_data.get("telemetry_scales", existing_config.get("telemetry_scales", default_tel_scales))
            telemetry_scales = dict(default_tel_scales)
            if isinstance(raw_tel_scales, dict):
                for k in default_tel_scales:
                    if k in raw_tel_scales and raw_tel_scales[k] is not None:
                        telemetry_scales[k] = str(raw_tel_scales[k])

            default_tel_metrics = {
                "render_ms": True,
                "total_kb": True,
                "largest_kb": False,
                "objects": False
            }
            raw_tel_metrics = config_data.get("telemetry_active_metrics", existing_config.get("telemetry_active_metrics", default_tel_metrics))
            telemetry_active_metrics = dict(default_tel_metrics)
            if isinstance(raw_tel_metrics, dict):
                for k in default_tel_metrics:
                    if k in raw_tel_metrics:
                        telemetry_active_metrics[k] = bool(raw_tel_metrics[k])

            clean_config = {
                "theme": saved_theme,
                "grid_mode": grid_mode,
                "undo_steps": undo_steps,
                "bg_image_mode": bg_image_mode,
                "bg_image_opacity": bg_image_opacity,
                "has_bg_image": bg_info["has_bg"],
                "bg_media_type": bg_info["media_type"],
                "is_default_bg": bg_info.get("is_default", False),
                "no_bg": no_bg,
                "convert_video": convert_video,
                "daemon_mode": is_daemon,
                "language": language,
                "window_state": window_state,
                "active_template_id": active_tpl_id,
                "active_template_name": active_tpl_name,
                "telemetry_scales": telemetry_scales,
                "telemetry_active_metrics": telemetry_active_metrics
            }
            if "dependency_check" in existing_config:
                clean_config["dependency_check"] = existing_config["dependency_check"]

            _atomic_write(config_path, json.dumps(clean_config, ensure_ascii=False, indent=2))

            if hasattr(self, "_daemon_server") and self._daemon_server:
                self._daemon_server.daemon_mode = is_daemon

            return True
        except Exception as e:
            print("Pyxis: error saving user_config", e)
            return False

    def _get_themes_dir(self):
        """Resolves the directory storing individual user theme JSON files."""
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        pyxis_themes_dir = os.path.join(appdata_dir, "PyxisNodes", "themes")
        os.makedirs(pyxis_themes_dir, exist_ok=True)
        return pyxis_themes_dir

    def _get_custom_themes_path(self):
        """Resolves the path to the consolidated custom_themes.json file."""
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
        os.makedirs(pyxis_config_dir, exist_ok=True)
        return os.path.join(pyxis_config_dir, "custom_themes.json")

    def get_custom_themes(self):
        """Loads and aggregates all custom UI themes from disk.

        Scans both the legacy consolidated `custom_themes.json` and the dedicated
        `themes/` folder, tagging each theme with `isCustom: True`.

        Returns:
            dict[str, dict[str, Any]]: Mapping of theme IDs to theme definitions.
        """
        themes = {}
        try:
            path = self._get_custom_themes_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                    if isinstance(c_data, dict):
                        for k, v in c_data.items():
                            if isinstance(v, dict) and v.get("id"):
                                v["isCustom"] = True
                                themes[v["id"]] = v

            themes_dir = self._get_themes_dir()
            if os.path.exists(themes_dir):
                for fname in os.listdir(themes_dir):
                    if fname.lower().endswith(".json"):
                        fpath = os.path.join(themes_dir, fname)
                        try:
                            with open(fpath, "r", encoding="utf-8") as f:
                                t_data = json.load(f)
                                if isinstance(t_data, dict) and t_data.get("id"):
                                    t_data["isCustom"] = True
                                    themes[t_data["id"]] = t_data
                        except Exception as fe:
                            print(f"Pyxis: error loading individual theme {fname}: {fe}")
        except Exception as e:
            print("Pyxis: error reading custom_themes", e)
        return themes

    def save_custom_themes(self, payload):
        """Persists multiple custom themes to disk atomically.

        Args:
            payload (dict | str): Theme mapping or JSON string.

        Returns:
            bool: True if themes were saved successfully, False on error.
        """
        try:
            themes = payload if isinstance(payload, dict) else json.loads(payload)
            themes_dir = self._get_themes_dir()
            for t_id, t_data in themes.items():
                if isinstance(t_data, dict) and t_data.get("id"):
                    t_data["isCustom"] = True
                    safe_fn = "".join(c for c in t_id if c.isalnum() or c in ("-", "_")) + ".json"
                    _atomic_write(os.path.join(themes_dir, safe_fn), json.dumps(t_data, ensure_ascii=False, indent=2))

            path = self._get_custom_themes_path()
            _atomic_write(path, json.dumps(themes, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print("Pyxis: error saving custom_themes", e)
            return False

    def save_custom_theme(self, payload):
        """Saves or updates a single custom UI theme atomically.

        Writes both an individual file in `%APPDATA%/PyxisNodes/themes/` and
        synchronises the entry in `custom_themes.json`.

        Args:
            payload (dict | str): Theme dictionary or JSON string containing 'id'.

        Returns:
            bool: True if the theme was saved, False otherwise.
        """
        try:
            theme_data = payload if isinstance(payload, dict) else json.loads(payload)
            theme_id = theme_data.get("id")
            if not theme_id:
                return False
            theme_data["isCustom"] = True
            
            themes_dir = self._get_themes_dir()
            safe_fn = "".join(c for c in theme_id if c.isalnum() or c in ("-", "_")) + ".json"
            ind_path = os.path.join(themes_dir, safe_fn)
            _atomic_write(ind_path, json.dumps(theme_data, ensure_ascii=False, indent=2))

            path = self._get_custom_themes_path()
            themes = {}
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        themes = json.load(f)
                except Exception:
                    themes = {}
            themes[theme_id] = theme_data
            _atomic_write(path, json.dumps(themes, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print("Pyxis: error saving custom_theme", e)
            return False

    def delete_custom_theme(self, theme_id):
        """Deletes a custom theme from both the consolidated file and individual storage.

        Args:
            theme_id (str): Unique theme identifier to delete.

        Returns:
            bool: True if deletion succeeded, False otherwise.
        """
        try:
            path = self._get_custom_themes_path()
            themes = {}
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        themes = json.load(f)
                except Exception:
                    themes = {}
            if theme_id in themes:
                del themes[theme_id]
                _atomic_write(path, json.dumps(themes, ensure_ascii=False, indent=2))

            themes_dir = self._get_themes_dir()
            if os.path.exists(themes_dir):
                safe_fn = "".join(c for c in theme_id if c.isalnum() or c in ("-", "_")) + ".json"
                ind_path = os.path.join(themes_dir, safe_fn)
                if os.path.exists(ind_path):
                    try:
                        os.remove(ind_path)
                    except Exception:
                        pass

                for fname in list(os.listdir(themes_dir)):
                    if fname.lower().endswith(".json"):
                        fpath = os.path.join(themes_dir, fname)
                        try:
                            with open(fpath, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            if isinstance(data, dict) and data.get("id") == theme_id:
                                os.remove(fpath)
                        except Exception:
                            pass

            return True
        except Exception as e:
            print("Pyxis: error deleting custom_theme", e)
            return False

    @staticmethod
    def cleanup_temp_files(max_age_hours=72, force_all=False):
        """Deletes temporary files and cache fragments older than max_age_hours (default 72h).

        Purges expired files from `temp_cache`, `temp`, `fonts`, and preview
        media files in `bg_media` (`preview_bg_*`, `export_bg_*`).

        Args:
            max_age_hours (int, optional): Cut-off threshold in hours. Defaults to 72.
            force_all (bool, optional): If True, unlinks all files regardless of age.

        Returns:
            dict[str, Any]: Summary containing `cleaned_files` count and `freed_bytes`.
        """
        import time
        try:
            appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            pyxis_dir = os.path.join(appdata_dir, "PyxisNodes")
            if not os.path.exists(pyxis_dir):
                return {"cleaned_files": 0, "freed_bytes": 0}

            now = time.time()
            cutoff_sec = max_age_hours * 3600
            cleaned_files = 0
            freed_bytes = 0

            def _is_expired(fp):
                if force_all:
                    return True
                try:
                    mt = os.path.getmtime(fp)
                    try:
                        at = os.path.getatime(fp)
                    except Exception:
                        at = mt
                    last_used = max(mt, at)
                    return (now - last_used > cutoff_sec)
                except Exception:
                    return False

            temp_cache_dir = os.path.join(pyxis_dir, "temp_cache")
            if os.path.isdir(temp_cache_dir):
                for fname in os.listdir(temp_cache_dir):
                    fpath = os.path.join(temp_cache_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            if _is_expired(fpath):
                                size = os.path.getsize(fpath)
                                os.remove(fpath)
                                cleaned_files += 1
                                freed_bytes += size
                        except Exception:
                            pass

            temp_dir = os.path.join(pyxis_dir, "temp")
            if os.path.isdir(temp_dir):
                for fname in os.listdir(temp_dir):
                    fpath = os.path.join(temp_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            if _is_expired(fpath):
                                size = os.path.getsize(fpath)
                                os.remove(fpath)
                                cleaned_files += 1
                                freed_bytes += size
                        except Exception:
                            pass

            fonts_dir = os.path.join(pyxis_dir, "fonts")
            if os.path.isdir(fonts_dir):
                for fname in os.listdir(fonts_dir):
                    fpath = os.path.join(fonts_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            if _is_expired(fpath):
                                size = os.path.getsize(fpath)
                                os.remove(fpath)
                                cleaned_files += 1
                                freed_bytes += size
                        except Exception:
                            pass

            bg_media_dir = os.path.join(pyxis_dir, "bg_media")
            if os.path.isdir(bg_media_dir):
                for fname in os.listdir(bg_media_dir):
                    if not (fname.startswith("preview_bg_") or fname.startswith("export_bg_")):
                        continue
                    fpath = os.path.join(bg_media_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            if _is_expired(fpath):
                                size = os.path.getsize(fpath)
                                os.remove(fpath)
                                cleaned_files += 1
                                freed_bytes += size
                        except Exception:
                            pass

            if cleaned_files > 0:
                print(f"[Pyxis Auto-Cleanup] Purga completada (> {max_age_hours}h): {cleaned_files} archivos eliminados, {freed_bytes / (1024*1024):.2f} MB liberados.", flush=True)

            return {"cleaned_files": cleaned_files, "freed_bytes": freed_bytes}
        except Exception as e:
            print(f"[Pyxis Auto-Cleanup Error] {e}", flush=True)
            return {"cleaned_files": 0, "freed_bytes": 0, "error": str(e)}

    def clean_temp_cache(self, max_age_hours=72, force_all=False):
        """Convenience alias for cleanup_temp_files."""
        return self.cleanup_temp_files(max_age_hours=max_age_hours, force_all=force_all)

    def export_theme_dialog(self, payload):
        """Displays a native file save dialogue to export a theme JSON document.

        Uses PyWebView's `create_file_dialog` with Tkinter fallback if webview
        dialogues are unavailable.

        Args:
            payload (dict | str): Theme data to export.

        Returns:
            dict[str, Any]: Status dictionary containing `success`, exported `path`,
                or `cancelled` flag.
        """
        try:
            theme = payload if isinstance(payload, dict) else json.loads(payload)
            theme_name = theme.get("name", "Tema_Pyxis").replace(" ", "_")
            default_fn = f"{theme_name}.json"

            save_path = None
            if hasattr(webview, "windows") and webview.windows:
                window = webview.windows[0]
                save_flag = getattr(webview, 'FileDialog', None).SAVE if hasattr(webview, 'FileDialog') else webview.SAVE_DIALOG
                result = window.create_file_dialog(
                    save_flag,
                    save_filename=default_fn,
                    file_types=("Pyxis Theme File (*.json)", "All Files (*.*)"),
                )
                if result:
                    save_path = result if isinstance(result, str) else result[0]

            if not save_path:
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes("-topmost", True)
                    save_path = filedialog.asksaveasfilename(
                        title="Export Pyxis Theme",
                        defaultextension=".json",
                        initialfile=default_fn,
                        filetypes=[("Pyxis Theme File", "*.json"), ("All Files", "*.*")]
                    )
                    root.destroy()
                except Exception as e:
                    print("[Pyxis export theme tkinter warning]", e, flush=True)

            if not save_path:
                return {"success": False, "cancelled": True}

            _atomic_write(save_path, json.dumps(theme, ensure_ascii=False, indent=2))
            return {"success": True, "path": save_path, "theme_name": theme.get("name")}
        except Exception as e:
            print("[Pyxis export_theme_dialog error]", e, flush=True)
            return {"success": False, "error": str(e)}

    def import_theme_dialog(self):
        """Displays a native file open dialogue to import a theme JSON document.

        Validates the structure of the loaded theme, assigns a fallback ID if missing,
        marks `isCustom: True`, and persists to custom themes storage.

        Returns:
            dict[str, Any]: Status dictionary containing imported `theme` or `cancelled` flag.
        """
        try:
            import time
            open_path = None
            if hasattr(webview, "windows") and webview.windows:
                window = webview.windows[0]
                open_flag = getattr(webview, 'FileDialog', None).OPEN if hasattr(webview, 'FileDialog') else webview.OPEN_DIALOG
                result = window.create_file_dialog(
                    open_flag,
                    file_types=("Pyxis Theme File (*.json)", "All Files (*.*)"),
                    allow_multiple=False
                )
                if result:
                    open_path = result if isinstance(result, str) else result[0]

            if not open_path:
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes("-topmost", True)
                    open_path = filedialog.askopenfilename(
                        title="Import Pyxis Theme",
                        filetypes=[("Pyxis Theme File", "*.json"), ("All Files", "*.*")]
                    )
                    root.destroy()
                except Exception as e:
                    print("[Pyxis import theme tkinter warning]", e, flush=True)

            if not open_path or not os.path.exists(open_path):
                return {"success": False, "cancelled": True}

            with open(open_path, "r", encoding="utf-8") as f:
                theme_data = json.load(f)

            if not isinstance(theme_data, dict) or ("canvasBg" not in theme_data and "categories" not in theme_data and "name" not in theme_data):
                return {"success": False, "error": "File does not contain a valid Pyxis theme structure"}

            if "id" not in theme_data or not theme_data["id"]:
                theme_data["id"] = f"imported_{int(time.time() * 1000)}"
            theme_data["isCustom"] = True

            self.save_custom_theme(theme_data)
            return {"success": True, "theme": theme_data}
        except Exception as e:
            print("[Pyxis import_theme_dialog error]", e, flush=True)
            return {"success": False, "error": str(e)}

    def _get_code_templates_path(self):
        """Resolves the path to the user code snippet templates configuration file."""
        appdata_dir = os.environ.get("APPDATA")
        if not appdata_dir:
            appdata_dir = os.path.expanduser("~")
        pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
        os.makedirs(pyxis_config_dir, exist_ok=True)
        return os.path.join(pyxis_config_dir, "user_code_templates.json")

    def get_code_templates(self):
        """Loads and returns user code snippet presets from user_code_templates.json.

        Returns:
            dict[str, Any]: Dictionary of code templates.
        """
        try:
            path = self._get_code_templates_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print("Pyxis: error reading user_code_templates", e)
        return {}

    def save_code_templates(self, payload):
        """Persists user code snippet presets atomically to user_code_templates.json.

        Args:
            payload (dict | str): Presets dictionary or JSON string.

        Returns:
            bool: True if saved successfully, False on error.
        """
        try:
            templates = payload if isinstance(payload, dict) else json.loads(payload)
            path = self._get_code_templates_path()
            _atomic_write(path, json.dumps(templates, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print("Pyxis: error saving user_code_templates", e)
            return False

    def validate_script_syntax(self, script, language="Python"):
        """Validates the syntax of Python or Lua user script snippets.

        Applies regex pre-processing to handle Pyxis-specific shorthand unit
        suffixes (such as `40Line`, `40ms`, `10f`, `5r`, `40li`) preventing
        false-positive parse failures. Uses Python's `ast.parse` for Python
        code and `lupa.LuaRuntime` for Lua scripts (with fallback to client-side
        JS verification if `lupa` is not installed).

        Args:
            script (str): Script text to validate.
            language (str, optional): Target language ("Python" or "Lua"). Defaults to "Python".

        Returns:
            dict[str, Any]: Validation result containing `valid: bool`, optional
                `line: int`, and `error: str | None`.
        """
        script_str = str(script or "").strip()
        if not script_str:
            return {"valid": True, "error": None}

        lang = str(language or "Python").strip().lower()
        if lang == "python":
            import ast
            # Preprocess code to handle implicit multiplication and unit suffixes (e.g., 40Line -> 40 * Line, 40ms -> 40 * ms)
            # so ast.parse does not raise false positive 'invalid decimal literal' for Pyxis shorthand expressions.
            sanitized_str = re.sub(r'(?<!0[xXbBoO])(\b\d+(?:\.\d+)?)(?![eE][+-]?\d+)([a-zA-Z_]\w*)', r'\1 * \2', script_str)
            try:
                ast.parse(sanitized_str, "<pyxis_script>", "exec")
                return {"valid": True, "error": None}
            except SyntaxError as se:
                msg = f"SyntaxError line {se.lineno}: {se.msg}"
                return {"valid": False, "line": se.lineno, "error": msg}
            except Exception as e:
                return {"valid": False, "line": 1, "error": str(e)}
        elif lang == "lua":
            try:
                import lupa
                # Preprocess Pyxis shorthand unit suffixes (e.g., 10f -> (10 * 40.0), 5r -> (5 * 1.0), 40li -> 40 * li)
                # so lupa compiler does not flag Pyxis shorthand units as syntax errors.
                sanitized_str = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*(li|lo|m1|m2|l1|l2)\b', r'\1 * \2', script_str)
                sanitized_str = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*f\b', r'(\1 * 40.0)', sanitized_str)
                sanitized_str = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*r\b', r'(\1 * 1.0)', sanitized_str)

                lua = lupa.LuaRuntime()
                lua.execute(f"function _pyxis_syntax_chk()\n{sanitized_str}\nend")
                return {"valid": True, "error": None}
            except (ImportError, ModuleNotFoundError):
                # Defer Lua syntax checking to frontend JS validator if lupa is missing
                return {"valid": True, "error": None}
            except Exception as le:
                err_str = str(le)
                m_line = re.search(r':(\d+):', err_str)
                raw_line = int(m_line.group(1)) if m_line else 1
                line_num = max(1, raw_line - 1)
                clean_err = re.sub(r'^.*?:\d+:\s*', '', err_str)
                clean_err = clean_err.replace("_pyxis_syntax_chk", "script")
                return {"valid": False, "line": line_num, "error": f"Lua Error line {line_num}: {clean_err}"}
        return {"valid": True, "error": None}

    def _optimize_bg_image(self, input_path, output_path):
        """Optimises and compresses a background image into WebP format.

        Transposes EXIF orientation tags, downsamples resolutions exceeding
        2560x1440 using Lanczos filtering, and iteratively adjusts compression
        quality to respect a strict 250 KB budget.

        Args:
            input_path (str): Source image filesystem path.
            output_path (str): Destination WebP filesystem path.
        """
        from PIL import Image, ImageOps
        import io

        with Image.open(input_path) as img:
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            max_w, max_h = 2560, 1440
            if img.width > max_w or img.height > max_h:
                try:
                    resampling = Image.Resampling.LANCZOS
                except AttributeError:
                    resampling = Image.LANCZOS
                img.thumbnail((max_w, max_h), resampling)

            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA" if "transparency" in img.info else "RGB")

            max_bytes = 250 * 1024
            quality = 80
            best_bytes = None

            while quality >= 30:
                buf = io.BytesIO()
                img.save(buf, "WEBP", quality=quality, method=4)
                data = buf.getvalue()
                if len(data) <= max_bytes:
                    best_bytes = data
                    break
                best_bytes = data
                quality -= 10

            if best_bytes:
                with open(output_path, "wb") as f:
                    f.write(best_bytes)
            else:
                img.save(output_path, "WEBP", quality=50)

    def _generate_video_poster(self, video_path, poster_path):
        """Extracts the first frame of a background video as a WebP poster image.

        Args:
            video_path (str): Source video file path.
            poster_path (str): Target WebP image file path.
        """
        ffmpeg_exe = self._find_ffmpeg()
        import subprocess
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
        poster_cmd = [
            ffmpeg_exe, "-y",
            "-i", video_path,
            "-vframes", "1",
            "-c:v", "libwebp",
            "-quality", "75",
            poster_path
        ]
        try:
            subprocess.run(poster_cmd, startupinfo=startupinfo, capture_output=True)
        except Exception:
            pass

    def _optimize_bg_video(self, input_path, output_path, poster_path=None):
        """Transcodes background video to optimised H.264 MP4 with faststart flags.

        Strips audio tracks, downscales to a maximum of 1920x1080 (ensuring even
        dimensions), and generates an accompanying WebP poster thumbnail.

        Args:
            input_path (str): Source video file path.
            output_path (str): Target MP4 file path.
            poster_path (str, optional): Target WebP poster thumbnail path.
        """
        ffmpeg_exe = self._find_ffmpeg()
        
        if poster_path is None:
            poster_path = os.path.join(os.path.dirname(output_path), "bg_poster.webp")
        
        import subprocess
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

        cmd = [
            ffmpeg_exe, "-y",
            "-i", input_path,
            "-an",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "24",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-vf", "scale=w='min(1920,trunc(iw/2)*2)':h='min(1080,trunc(ih/2)*2)':force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2",
            output_path
        ]
        try:
            subprocess.run(cmd, check=True, startupinfo=startupinfo, capture_output=True)
            self._generate_video_poster(output_path, poster_path)
        except Exception as e:
            print("Pyxis: error optimizing video with ffmpeg, trying simple transcode", e)
            try:
                cmd_simple = [
                    ffmpeg_exe, "-y",
                    "-i", input_path,
                    "-an",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    output_path
                ]
                subprocess.run(cmd_simple, check=True, startupinfo=startupinfo, capture_output=True)
                self._generate_video_poster(output_path, poster_path)
            except Exception as e2:
                print("Pyxis: simple transcoding failed, using direct copy", e2)
                import shutil
                shutil.copyfile(input_path, output_path)
                self._generate_video_poster(output_path, poster_path)

    def select_bg_media(self, convert_video=True):
        """Displays a native file selection dialogue for background image or video assets.

        Processes chosen media, transcode-optimising video to MP4/WebP poster
        or compressing image to WebP under strict byte budgets, and updates
        persisted background media assets.

        Args:
            convert_video (bool, optional): Whether to transcode imported video
                via FFmpeg. Defaults to True.

        Returns:
            dict[str, Any]: Media description dictionary containing status, URLs,
                and format details.
        """
        try:
            file_path = None
            if hasattr(webview, "windows") and webview.windows:
                window = webview.windows[0]
                open_flag = getattr(webview, 'FileDialog', None).OPEN if hasattr(webview, 'FileDialog') else webview.OPEN_DIALOG
                result = window.create_file_dialog(
                    open_flag,
                    file_types=(
                        "Fondos Multimedia (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp;*.mp4;*.webm;*.mov;*.mkv;*.avi;*.m4v)",
                        "Videos (*.mp4;*.webm;*.mov;*.mkv;*.avi;*.m4v)",
                        "Images (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp)",
                        "All Files (*.*)"
                    ),
                    allow_multiple=False,
                )
                if result:
                    file_path = result if isinstance(result, str) else result[0]

            if not file_path:
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes("-topmost", True)
                    file_path = filedialog.askopenfilename(
                        title="Seleccionar Fondo Multimedia (Imagen o Video)",
                        filetypes=[
                            ("Fondos Multimedia", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp;*.mp4;*.webm;*.mov;*.mkv;*.avi;*.m4v"),
                            ("Videos", "*.mp4;*.webm;*.mov;*.mkv;*.avi;*.m4v"),
                            ("Imágenes", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp"),
                            ("All Files", "*.*")
                        ]
                    )
                    root.destroy()
                except Exception as e:
                    print("[Pyxis select_bg_media tkinter warning]", e, flush=True)

            if not file_path or not os.path.exists(file_path):
                return {"success": False, "cancelled": True}
            
            appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
            bg_media_dir = os.path.join(pyxis_config_dir, "bg_media")
            os.makedirs(bg_media_dir, exist_ok=True)
            
            ext = os.path.splitext(file_path)[1].lower()
            is_video = ext in (".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v")
            
            if is_video:
                should_convert = bool(convert_video) or ext not in (".mp4", ".webm")
                target_ext = '.mp4' if should_convert else ext
                temp_video = os.path.join(bg_media_dir, f"bg_video_temp{target_ext}")
                temp_poster = os.path.join(bg_media_dir, "bg_poster_temp.webp")

                for p in [temp_video, temp_poster]:
                    if os.path.exists(p):
                        try: os.remove(p)
                        except OSError: pass

                if should_convert:
                    self._optimize_bg_video(file_path, temp_video, temp_poster)
                else:
                    import shutil
                    shutil.copyfile(file_path, temp_video)
                    self._generate_video_poster(temp_video, temp_poster)
                
                if not os.path.exists(temp_video) or os.path.getsize(temp_video) == 0:
                    raise RuntimeError("Failed to process background video.")

                # Conversion succeeded: safely remove previous background files
                for f in ["bg_image.webp", "bg_image.png"]:
                    p = os.path.join(pyxis_config_dir, f)
                    if os.path.exists(p):
                        try: os.remove(p)
                        except OSError: pass
                for vext in [".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"]:
                    p = os.path.join(bg_media_dir, f"bg_video{vext}")
                    if os.path.exists(p):
                        try: os.remove(p)
                        except OSError: pass
                poster_p = os.path.join(bg_media_dir, "bg_poster.webp")
                if os.path.exists(poster_p):
                    try: os.remove(poster_p)
                    except OSError: pass

                dest_video = os.path.join(bg_media_dir, f"bg_video{target_ext}")
                os.replace(temp_video, dest_video)
                if os.path.exists(temp_poster) and os.path.getsize(temp_poster) > 0:
                    os.replace(temp_poster, poster_p)
                elif os.path.exists(temp_poster):
                    try: os.remove(temp_poster)
                    except OSError: pass

                import urllib.parse
                import time
                ts = int(time.time() * 1000)
                v_url = f"http://127.0.0.1:28723/media_file?path={urllib.parse.quote(dest_video)}&t={ts}"
                p_url = f"http://127.0.0.1:28723/media_file?path={urllib.parse.quote(poster_p)}&t={ts}" if os.path.exists(poster_p) else ""
                return {
                    "success": True,
                    "media_type": "video",
                    "video_url": v_url,
                    "poster_url": p_url,
                    "has_bg": True,
                    "converted": should_convert,
                    "filename": os.path.basename(file_path)
                }
            else:
                temp_image = os.path.join(pyxis_config_dir, "bg_image_temp.webp")
                if os.path.exists(temp_image):
                    try: os.remove(temp_image)
                    except OSError: pass

                try:
                    self._optimize_bg_image(file_path, temp_image)
                except Exception as e:
                    print("Pyxis: WEBP compression not available, using direct copy", e)
                    import shutil
                    shutil.copyfile(file_path, temp_image)

                if not os.path.exists(temp_image) or os.path.getsize(temp_image) == 0:
                    raise RuntimeError("Failed to process background image.")

                # Optimization succeeded: safely remove previous background files
                for f in ["bg_image.webp", "bg_image.png"]:
                    p = os.path.join(pyxis_config_dir, f)
                    if os.path.exists(p):
                        try: os.remove(p)
                        except OSError: pass
                for vext in [".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"]:
                    p = os.path.join(bg_media_dir, f"bg_video{vext}")
                    if os.path.exists(p):
                        try: os.remove(p)
                        except OSError: pass
                poster_p = os.path.join(bg_media_dir, "bg_poster.webp")
                if os.path.exists(poster_p):
                    try: os.remove(poster_p)
                    except OSError: pass

                dest_image = os.path.join(pyxis_config_dir, "bg_image.webp")
                os.replace(temp_image, dest_image)

                import base64
                import mimetypes
                mime_type, _ = mimetypes.guess_type(dest_image)
                mime_type = mime_type or "image/webp"
                with open(dest_image, "rb") as img_file:
                    encoded = base64.b64encode(img_file.read()).decode("utf-8")
                data_url = f"data:{mime_type};base64,{encoded}"
                return {
                    "success": True,
                    "media_type": "image",
                    "video_url": "",
                    "poster_url": "",
                    "data_url": data_url,
                    "has_bg": True,
                    "converted": False,
                    "filename": os.path.basename(file_path)
                }
        except Exception as e:
            print("Pyxis: error selecting background", e)
            try:
                appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
                pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
                bg_media_dir = os.path.join(pyxis_config_dir, "bg_media")
                temp_image = os.path.join(pyxis_config_dir, "bg_image_temp.webp")
                if os.path.exists(temp_image):
                    try: os.remove(temp_image)
                    except OSError: pass
                for vext in [".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"]:
                    tp = os.path.join(bg_media_dir, f"bg_video_temp{vext}")
                    if os.path.exists(tp):
                        try: os.remove(tp)
                        except OSError: pass
                tp_poster = os.path.join(bg_media_dir, "bg_poster_temp.webp")
                if os.path.exists(tp_poster):
                    try: os.remove(tp_poster)
                    except OSError: pass
            except Exception:
                pass
            return {"success": False, "error": str(e)}

    def select_bg_image(self):
        """Opens media selection dialogue and returns the resolved media URL."""
        res = self.select_bg_media()
        if isinstance(res, dict):
            if res.get("media_type") == "image":
                return res.get("data_url", "")
            elif res.get("media_type") == "video":
                return res.get("video_url", "")
        return ""

    def select_image_dialog(self):
        """Displays a native file dialogue to pick a raster image file for nodes.

        Returns:
            str: Absolute path to the selected image file, or empty string if cancelled.
        """
        try:
            if not webview.windows:
                return ""
            window = webview.windows[0]
            open_flag = getattr(webview, 'FileDialog', None).OPEN if hasattr(webview, 'FileDialog') else webview.OPEN_DIALOG
            result = window.create_file_dialog(
                open_flag,
                file_types=("Images (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp)", "All Files (*.*)"),
                allow_multiple=False,
            )
            if not result:
                return ""
            file_path = result if isinstance(result, str) else result[0]
            if not file_path or not os.path.exists(file_path):
                return ""
            return os.path.abspath(file_path)
        except Exception as e:
            print("Pyxis: error opening image selection dialog", e)
            return ""

    def log_js_error(self, msg):
        """Logs an error message originating from the frontend JavaScript context."""
        print(f"[Pyxis JS ERROR] {msg}", flush=True)
        return True

    def log_js_info(self, msg):
        """Logs an informational message originating from frontend JavaScript."""
        print(f"[Pyxis JS INFO] {msg}", flush=True)
        return True

    def get_manifest(self):
        """Returns the registered node manifest dictionary for the frontend node palette."""
        from decorators import get_manifest
        import nodes_library
        return get_manifest()

    def get_session_graph(self):
        """Loads and returns the active graph session JSON string from session_file."""
        try:
            with open(self.session_file, "r", encoding="utf-8") as file_handle:
                return file_handle.read()
        except (FileNotFoundError, OSError):
            return ""

    def save_session(self, payload):
        """Persists the current canvas graph state atomically into session_file.

        Args:
            payload (dict | str): Graph data structure or JSON string.

        Returns:
            bool: True if session state was persisted, False on error.
        """
        try:
            graph_data = self._normalize_graph(payload)
            _atomic_write(
                self.session_file,
                json.dumps(graph_data, ensure_ascii=False, separators=(",", ":"), default=str),
            )
            return True
        except Exception as e:
            print(f"[Pyxis Warning] Could not save temporary session file ({e})", flush=True)
            try:
                dir_name = os.path.dirname(self.session_file)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                with open(self.session_file, "w", encoding="utf-8") as f:
                    json.dump(graph_data, f, ensure_ascii=False, default=str)
                return True
            except Exception:
                return False

    def save_template(self, name, comment, payload, template_id=None):
        """Saves or updates a template in user templates storage.

        Args:
            name (str): Template display name.
            comment (str): Template description or instructions.
            payload (dict | str): Graph structure.
            template_id (str, optional): Target template identifier.

        Returns:
            dict[str, Any]: Saved template metadata dictionary.
        """
        graph_data = self._normalize_graph(payload)
        metadata = self.template_store.save_template(
            name, comment, graph_data, template_id=str(template_id) if template_id else None
        )
        return metadata

    def save_template_as(self, payload, default_name=None):
        """Displays a native save file dialogue to export the graph to a custom location.

        Args:
            payload (dict | str): Graph data structure.
            default_name (str, optional): Suggested file name. Defaults to "template".

        Returns:
            dict[str, Any] | None: Metadata of exported template, or None if cancelled.
        """
        try:
            graph_data = self._normalize_graph(payload)
            window = webview.windows[0]
            suggested_name = str(default_name or "template").strip()
            if not suggested_name.lower().endswith(".json"):
                suggested_name += ".json"
            save_flag = getattr(webview, 'FileDialog', None).SAVE if hasattr(webview, 'FileDialog') else webview.SAVE_DIALOG
            result = window.create_file_dialog(
                save_flag,
                file_types=("Pyxis Template (*.json)", "All Files (*.*)"),
                save_filename=suggested_name,
            )
            if not result:
                return None
            save_path = result if isinstance(result, str) else result[0]
            if not save_path:
                return None

            clean_name = os.path.splitext(os.path.basename(save_path))[0]
            now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
            metadata = {
                "template_id": f"external_{uuid.uuid4().hex[:8]}",
                "name": clean_name,
                "comment": "Saved to external file",
                "created_at": now,
                "updated_at": now,
                "aegisub_version": self.template_store.aegisub_version,
                "os": self.template_store._os_description(),
                "pyxis_engine_version": PYXIS_ENGINE_VERSION,
                "node_count": len(graph_data.get("nodes", [])),
                "node_types": self.template_store._node_types(graph_data),
                "is_favorite": False,
            }
            document = {
                "schema_version": 1,
                "metadata": metadata,
                "graph": graph_data,
            }
            _atomic_write(save_path, json.dumps(document, ensure_ascii=False, indent=2))
            return metadata
        except Exception as error:
            print("Pyxis: error saving to file", error)
            raise ValueError(f"Could not save file: {error}")

    def list_templates(self):
        """Returns the sorted list of all available system and user templates."""
        return self.template_store.list_templates()

    def load_template(self, template_id):
        """Loads and parses a template document by identifier.

        Args:
            template_id (str): Unique template identifier.

        Returns:
            dict[str, Any]: Dictionary containing `metadata` and `graph`.
        """
        document = self.template_store.load_template(str(template_id))
        return {
            "metadata": document.get("metadata", {}),
            "graph": document["graph"],
        }

    def delete_template(self, template_id):
        """Deletes a user-created template file from disk.

        Args:
            template_id (str): Unique identifier of template to delete.

        Returns:
            bool: True upon successful deletion.
        """
        self.template_store.delete_template(str(template_id))
        return True

    def toggle_favorite(self, template_id):
        """Toggles the favourite bookmark flag of the target template.

        Args:
            template_id (str): Unique template identifier.

        Returns:
            bool: Updated favourite status.
        """
        return self.template_store.toggle_favorite(str(template_id))

    def export_template(self, template_id):
        """Exports an existing template to an external JSON file via save file dialogue.

        Args:
            template_id (str): Unique template identifier.

        Returns:
            bool: True if exported, False if cancelled or on error.
        """
        try:
            document = self.template_store.load_template(str(template_id))
            meta = document.get("metadata", {})
            tpl_name = meta.get("name", "template")
            clean_name = self.template_store._clean_name(tpl_name) or "template"
            suggested_name = f"{clean_name}.json"
            window = webview.windows[0]
            save_flag = getattr(webview, 'FileDialog', None).SAVE if hasattr(webview, 'FileDialog') else webview.SAVE_DIALOG
            result = window.create_file_dialog(
                save_flag,
                file_types=("Pyxis Template (*.json)", "All Files (*.*)"),
                save_filename=suggested_name,
            )
            if not result:
                return False
            save_path = result if isinstance(result, str) else result[0]
            if not save_path:
                return False
            _atomic_write(save_path, json.dumps(document, ensure_ascii=False, indent=2))
            return True
        except Exception as error:
            print("Pyxis: error exporting template", error)
            return False

    def import_template(self):
        """Imports an external template JSON file into the user's template library.

        Returns:
            dict[str, Any] | None: Metadata of imported template, or None if cancelled.
        """
        try:
            window = webview.windows[0]
            save_flag = getattr(webview, 'FileDialog', None).OPEN if hasattr(webview, 'FileDialog') else webview.OPEN_DIALOG
            result = window.create_file_dialog(
                save_flag,
                file_types=("Pyxis Template (*.json)", "All Files (*.*)"),
                allow_multiple=False,
            )
            if not result:
                return None
            load_path = result if isinstance(result, str) else result[0]
            if not load_path or not os.path.exists(load_path):
                return None
            with open(load_path, "r", encoding="utf-8") as f:
                document = json.load(f)
            if not isinstance(document, dict):
                raise ValueError("Invalid file format (must be a JSON object)")
            if "graph" in document and isinstance(document["graph"], dict):
                graph = document["graph"]
                metadata = document.get("metadata", {})
            elif "nodes" in document and isinstance(document["nodes"], list):
                graph = document
                metadata = {}
            else:
                raise ValueError("Invalid file format (does not contain graph nodes)")

            name = metadata.get("name") or os.path.splitext(os.path.basename(load_path))[0] or "Template Importado"
            comment = metadata.get("comment", "Imported from file")
            new_metadata = self.template_store.save_template(name, comment, graph)
            return new_metadata
        except Exception as error:
            print("Pyxis: error importing template", error)
            raise ValueError(f"Could not import template: {error}")

    def estimate_workload_api(self, graph_payload):
        """Calculates instantaneous workload metrics and complexity estimation (< 1ms).

        Estimates total output line counts, base units, and rendering complexity
        indicators for the given graph before initiating full generation.

        Args:
            graph_payload (dict | str): Graph data structure.

        Returns:
            dict[str, Any]: Workload metrics including `estimated_lines`, `input_lines`,
                `base_units`, and complexity classifications.
        """
        try:
            from ass_parser import ASSParser
            from node_engine import GraphEngine
            graph_data = self._normalize_graph(graph_payload)
            parsed_ass = None
            if self.temp_ass and os.path.isfile(self.temp_ass):
                try:
                    parsed_ass = ASSParser.read_file(self.temp_ass)
                except Exception:
                    parsed_ass = None
            if not parsed_ass or not parsed_ass.dialogues:
                parsed_ass = getattr(self, '_cached_aegisub_parsed', None)
            if not parsed_ass or not parsed_ass.dialogues:
                appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
                preview_ass = os.path.join(appdata_dir, "PyxisNodes", "preview_base.ass")
                if not os.path.isfile(preview_ass):
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    preview_ass = os.path.join(script_dir, "..", "preview_base.ass")
                if os.path.isfile(preview_ass):
                    try:
                        parsed_ass = ASSParser.read_file(preview_ass)
                    except Exception:
                        pass

            if parsed_ass and parsed_ass.dialogues:
                styles, dialogues, res_x, res_y, frame_duration = parsed_ass
                engine = GraphEngine(graph_data, res_x, res_y, frame_duration)
                est = engine.estimate_workload(dialogues, styles, allow_fallback_select_all=True)
                try:
                    from ass_telemetry_engine import GLOBAL_TELEMETRY_MANAGER
                    last_tel = GLOBAL_TELEMETRY_MANAGER.get_last_result()
                    if isinstance(last_tel, dict) and last_tel.get("success") and isinstance(last_tel.get("summary"), dict):
                        summary = last_tel["summary"]
                        est["last_telemetry_peak_ms"] = summary.get("peak_ms", 0.0)
                        est["last_telemetry_budget_pct"] = summary.get("budget_usage_pct", 0.0)
                except Exception:
                    pass
                return est
            else:
                return {
                    "estimated_lines": 0,
                    "input_lines": 0,
                    "base_units": 0,
                    "output_nodes_count": 0,
                    "complexity": "Baja",
                    "complexity_color": "#34d399",
                    "is_heavy": False
                }
        except Exception as e:
            print(f"[Pyxis Error in estimate_workload_api] {e}", flush=True)
            return {
                "estimated_lines": 0,
                "input_lines": 0,
                "base_units": 0,
                "output_nodes_count": 0,
                "complexity": "Desconocida",
                "complexity_color": "#94a3b8",
                "error": str(e)
            }

    def cancel_generation(self):
        """Cancels active generation immediately across any thread or subprocess.

        Signals the active `GraphEngine` instance, updates the shared multiprocessing
        cancellation flag, and invokes `abort_global_multiprocessing()` to terminate
        worker pools.

        Returns:
            dict[str, bool]: Execution status mapping with `success` and `cancelled`.
        """
        print("[Pyxis] Cancellation requested by user from UI.", flush=True)
        self._preview_cancelled = True
        if getattr(self, '_active_engine', None) is not None:
            self._active_engine.is_cancelled = True
            if getattr(self._active_engine, 'shared_cancel_flag', None) is not None:
                try:
                    self._active_engine.shared_cancel_flag.value = True
                except Exception:
                    pass
        if getattr(self, '_active_preview_engine', None) is not None:
            self._active_preview_engine.is_cancelled = True
            if getattr(self._active_preview_engine, 'shared_cancel_flag', None) is not None:
                try:
                    self._active_preview_engine.shared_cancel_flag.value = True
                except Exception:
                    pass
        from node_engine import abort_global_multiprocessing
        abort_global_multiprocessing()
        return {"success": True, "cancelled": True}

    def cancel_preview_ass(self):
        """Cancels active preview ASS generation immediately.

        Signals the active preview `GraphEngine` instance, updates its shared cancel
        flag, and invokes `abort_global_multiprocessing()` to ensure preview rendering
        halts promptly.

        Returns:
            dict[str, bool]: Execution status mapping with `success` and `cancelled`.
        """
        print("[Pyxis] Preview cancellation requested by user from UI.", flush=True)
        self.log_player_event("cancel_preview_ass called by user.")
        self._preview_cancelled = True
        if getattr(self, '_active_preview_engine', None) is not None:
            self._active_preview_engine.is_cancelled = True
            if getattr(self._active_preview_engine, 'shared_cancel_flag', None) is not None:
                try:
                    self._active_preview_engine.shared_cancel_flag.value = True
                except Exception:
                    pass
        from node_engine import abort_global_multiprocessing
        abort_global_multiprocessing()
        return {"success": True, "cancelled": True}

    def complete_and_hide(self):
        """Hides the PyWebView window or shuts down the daemon upon completion.

        Releases the IPC lock file and either hides the primary webview window (if running
        in daemon mode) or triggers complete daemon shutdown.

        Returns:
            dict[str, bool]: Execution status with `success=True`.
        """
        self.release_lock()

        config = self.get_user_config()
        is_daemon = config.get("daemon_mode", True)
        if is_daemon and webview.windows:
            try:
                webview.windows[0].hide()
            except Exception:
                pass
        else:
            self.shutdown_daemon()
        return {"success": True}

    def validate_graph(self, payload):
        """Validates graph structure, node connections, and properties via GraphValidator.

        Inspects the deserialised graph for unconnected required inputs, type mismatches,
        cyclic dependencies, and variable syntax errors.

        Args:
            payload (dict | str): Graph data structure or JSON string.

        Returns:
            dict[str, Any]: Validation summary containing `success`, list of `issues`,
                `has_critical`, `has_warning`, and `total_issues`.
        """
        try:
            graph_data = self._normalize_graph(payload)
            from node_validator import GraphValidator
            validator = GraphValidator(graph_data)
            issues = validator.validate()
            return {
                "success": True,
                "issues": issues,
                "has_critical": any(i.get("severity") == "critical" for i in issues),
                "has_warning": any(i.get("severity") == "warning" for i in issues),
                "total_issues": len(issues)
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "issues": [],
                "has_critical": False,
                "has_warning": False,
                "total_issues": 0
            }

    def process_graph(self, payload):
        """Executes full node graph processing to generate ASS subtitle dialogue lines.

        Normalises the graph payload, creates an auto-save session checkpoint, scans
        for audio-dependent nodes to pre-convert and load PCM audio into `AudioEngine`,
        instantiates `GraphEngine`, and evaluates the pipeline over input subtitle
        dialogues and styles with real-time UI progress streaming.

        On successful completion, writes generated dialogue lines along with the
        `#PYXIS_USED_IDX` provenance header to `self.result_file`, flushes to disk via
        `os.fsync`, and releases the lock file. On failure, captures the traceback to
        a companion `_debug.log` file.

        Args:
            payload (dict | str): Graph structure and execution parameters.

        Returns:
            dict[str, Any]: Processing result containing `success`, `cancelled`,
                `lines_generated`, and optional `error` traceback.
        """
        try:
            graph_data = self._normalize_graph(payload)
            try:
                self.save_session(graph_data)
            except Exception as se:
                print(f"[Pyxis Warning] save_session non-critical: {se}", flush=True)

            def report_progress(data):
                try:
                    if webview.windows:
                        if isinstance(data, dict):
                            import json
                            js_str = json.dumps(data)
                            webview.windows[0].evaluate_js(
                                f"if (typeof window.__pyxis_on_progress === 'function') window.__pyxis_on_progress({js_str});"
                            )
                        else:
                            pct_val = int(float(data))
                            webview.windows[0].evaluate_js(
                                f"if (typeof window.__pyxis_on_progress === 'function') window.__pyxis_on_progress({pct_val});"
                            )
                except Exception:
                    pass

            from ass_parser import ASSParser
            from node_engine import GraphEngine
            from audio_preprocessor import AudioPreprocessor
            from audio_engine import AudioEngine

            parsed_ass = ASSParser.read_file(self.temp_ass)
            styles, dialogues, res_x, res_y, frame_duration = parsed_ass
            default_audio_source = getattr(parsed_ass, "audio_file", "") or getattr(parsed_ass, "video_file", "")

            for n in graph_data.get("nodes", []):
                n_type = str(n.get("type", ""))
                if "Audio" in n_type or "audio" in n_type.lower() or "Waveform" in n_type or "Modulador" in n_type:
                    node_audio = str(n.get("properties", {}).get("audio_path", "")).strip()
                    src_to_check = node_audio if node_audio else default_audio_source
                    if src_to_check:
                        try:
                            report_progress({"percent": 5, "phase": "Processing..."})
                            wav_path = AudioPreprocessor.ensure_audio_wav(
                                src_to_check,
                                progress_callback=lambda msg: report_progress({"percent": 12, "phase": "Processing..."})
                            )
                            report_progress({"percent": 18, "phase": "Processing..."})
                            AudioEngine.load_wav(wav_path)
                            report_progress({"percent": 24, "phase": "Processing..."})
                        except Exception as ae:
                            print(f"[Pyxis Warning Audio Preprocessor] {ae}", flush=True)

            engine = GraphEngine(graph_data, res_x, res_y, frame_duration, default_audio_source=default_audio_source)
            self._active_engine = engine
            generated_lines = engine.process(
                dialogues,
                styles,
                progress_callback=report_progress,
                check_cancel_callback=lambda: getattr(engine, 'is_cancelled', False)
            )

            if getattr(engine, 'is_cancelled', False):
                print("[Pyxis] Generation aborted by cancellation.", flush=True)
                return {"success": False, "cancelled": True, "lines_generated": 0}

            generated_count = len(generated_lines)
            with open(self.result_file, "w", encoding="utf-8") as result_file:
                if hasattr(engine, 'used_line_indices') and engine.used_line_indices:
                    idx_str = ",".join(str(x) for x in sorted(engine.used_line_indices))
                    result_file.write(f"#PYXIS_USED_IDX: {idx_str}\n")
                result_file.writelines(generated_lines)
                result_file.flush()
                os.fsync(result_file.fileno())

            self.release_lock()

            return {"success": True, "cancelled": False, "lines_generated": generated_count}
        except Exception:
            debug_file = self.result_file + "_debug.log"
            with open(debug_file, "w", encoding="utf-8") as error_file:
                error_file.write(traceback.format_exc())
                error_file.flush()
                os.fsync(error_file.fileno())
            print(f"[Pyxis Error in process_graph] {traceback.format_exc()}", flush=True)
            return {"success": False, "error": traceback.format_exc(), "lines_generated": 0}
        finally:
            self._active_engine = None

    def get_image_file_data_url(self, file_path):
        """Reads an image file from disk and encodes it into a base64 Data URL.

        Determines the MIME type using `mimetypes` (with fallback to PNG/JPEG/WebP)
        and constructs an inline `data:<mime>;base64,...` URI suitable for webview
        display.

        Args:
            file_path (str): Absolute or relative filesystem path to the image.

        Returns:
            str: Base64 data URL string, or empty string on missing file or error.
        """
        try:
            if not file_path or not os.path.exists(file_path):
                return ""
            import base64, mimetypes
            mime, _ = mimetypes.guess_type(file_path)
            if not mime:
                ext = os.path.splitext(file_path)[1].lower()
                mime = 'image/png' if ext == '.png' else ('image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/webp')
            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{mime};base64,{encoded}"
        except Exception as e:
            print(f"[Pyxis Error getting image data URL] {e}", flush=True)
            return ""

    def trace_image_api(self, node_props):
        """Executes Potrace vectorisation on a raster image via `img_tracer_engine`.

        Extracts tracing parameters (threshold, tolerance, bin_mode, alphamax, turnpolicy,
        and frame index for animated formats) from `node_props` and delegates to
        `img_tracer_engine.trace_image`.

        Args:
            node_props (dict): Property dictionary configured on the `Image/Trace` node.

        Returns:
            dict[str, Any]: Tracing result containing ASS drawing shape command `shape`,
                `width`, `height`, `points`, or error details.
        """
        try:
            from img_tracer_engine import trace_image
            if not isinstance(node_props, dict):
                node_props = {}
            image_path = str(node_props.get("image_path", "")).strip()
            if not image_path or not os.path.exists(image_path):
                return {"shape": "", "width": 0, "height": 0, "points": 0}

            mode = str(node_props.get("mode", "Potrace")).strip()
            threshold_raw = node_props.get("threshold", "128")
            threshold = int(float(threshold_raw) if str(threshold_raw).replace('.','',1).isdigit() else 128)
            tolerance_raw = node_props.get("tolerance", "1.0")
            tolerance = float(tolerance_raw if str(tolerance_raw).replace('.','',1).isdigit() else 1.0)
            out_scale_raw = node_props.get("out_scale", "1.0")
            out_scale = float(out_scale_raw if str(out_scale_raw).replace('.','',1).isdigit() else 1.0)
            out_w_raw = node_props.get("out_w", "0.0")
            out_w = float(out_w_raw if str(out_w_raw).replace('.','',1).isdigit() else 0.0)
            out_h_raw = node_props.get("out_h", "0.0")
            out_h = float(out_h_raw if str(out_h_raw).replace('.','',1).isdigit() else 0.0)
            anchor = str(node_props.get("anchor", "Center")).strip()
            offset_x_raw = node_props.get("offset_x", "0.0")
            offset_x = float(offset_x_raw if str(offset_x_raw).replace('.','',1).isdigit() else 0.0)
            offset_y_raw = node_props.get("offset_y", "0.0")
            offset_y = float(offset_y_raw if str(offset_y_raw).replace('.','',1).isdigit() else 0.0)
            img_scale_raw = node_props.get("img_scale", "1.0")
            img_scale = float(img_scale_raw if str(img_scale_raw).replace('.','',1).isdigit() else 1.0)
            invert_str = str(node_props.get("invert", "Normal")).strip()
            invert = invert_str.lower() == "inverted"
            bin_mode = str(node_props.get("bin_mode", "Luminance")).strip()
            alphamax_raw = node_props.get("alphamax", "1.0")
            alphamax = float(alphamax_raw if str(alphamax_raw).replace('.','',1).isdigit() else 1.0)
            opttoler_raw = node_props.get("opttoler", "0.2")
            opttoler = float(opttoler_raw if str(opttoler_raw).replace('.','',1).isdigit() else 0.2)
            turnpolicy = str(node_props.get("turnpolicy", "minority")).strip()

            frame_idx_raw = node_props.get("preview_frame", node_props.get("frame_idx", "1"))
            if str(frame_idx_raw).strip() == "j":
                preview_f = node_props.get("preview_frame", 1)
                try: frame_index = int(preview_f)
                except Exception: frame_index = 1
            else:
                try: frame_index = int(float(frame_idx_raw))
                except Exception: frame_index = 1

            invert_img_str = str(node_props.get("invert_img", "Normal")).strip()
            use_inverted_img = invert_img_str.lower() == "inverted"

            traced = trace_image(
                image_path=image_path,
                mode=mode,
                threshold=threshold,
                invert=invert,
                tolerance=tolerance,
                out_scale=1.0,
                out_w=0.0,
                out_h=0.0,
                anchor="Center",
                offset_x=0.0,
                offset_y=0.0,
                img_scale=1.0,
                bin_mode=bin_mode,
                alphamax=alphamax,
                opttoler=opttoler,
                turnpolicy=turnpolicy,
                frame_index=frame_index,
                invert_img=use_inverted_img
            )
            return traced
        except Exception as e:
            print(f"[Pyxis Error trace_image_api] {e}", flush=True)
            return {"shape": "", "error": str(e)}

    _SAMPLE_PIXELS_CACHE = {}

    def sample_pixels_api(self, node_props):
        """Samples pixel coordinates and RGBA colour data from a raster image or GIF.

        Performs alpha-threshold filtering, adaptive grid subsampling (capping maximum
        points to 8,000 to maintain smooth webview performance), and caches sampled
        results in `PyxisAPI._SAMPLE_PIXELS_CACHE` (up to 500 entries).

        Args:
            node_props (dict): Property dictionary configured on the `Image/SamplePixels` node.

        Returns:
            dict[str, Any]: Sampled pixel points list `[x, y, r, g, b, a]`, total pixel
                count, dimensions, frame indices, and sampling step sizes.
        """
        try:
            if not isinstance(node_props, dict):
                node_props = {}
            image_path = str(node_props.get("image_path", "")).strip()
            if not image_path or not os.path.exists(image_path):
                return {"pixels_points": [], "total_pixels": 0, "total_frames": 1, "frame_index": 1}

            frame_raw = node_props.get("preview_frame", node_props.get("frame", node_props.get("frame_idx", "1")))
            if str(frame_raw).strip() == "j":
                preview_f = node_props.get("preview_frame", 1)
                try: frame_index = int(preview_f)
                except Exception: frame_index = 1
            else:
                try: frame_index = int(float(frame_raw))
                except Exception: frame_index = 1
            if frame_index < 1: frame_index = 1

            step_raw = node_props.get("step", "2")
            try: step = max(1, int(float(step_raw)))
            except Exception: step = 2

            alpha_th_raw = node_props.get("alpha_threshold", "128")
            try: alpha_th = int(float(alpha_th_raw))
            except Exception: alpha_th = 128

            scale_raw = node_props.get("scale", "1.0")
            try: scale = float(scale_raw)
            except Exception: scale = 1.0

            anchor = str(node_props.get("anchor", "Center")).strip()

            from img_tracer_engine import _is_animated_gif, _get_or_extract_gif_frames
            total_frames = 1
            target_frame_idx = 1
            target_image_path = image_path

            if _is_animated_gif(image_path):
                all_frames, total_frames = _get_or_extract_gif_frames(image_path)
                if total_frames > 0:
                    target_frame_idx = (frame_index - 1) % total_frames + 1
                    target_image_path = all_frames[target_frame_idx - 1]

            cache_key = (target_image_path, step, alpha_th, total_frames, target_frame_idx)
            if cache_key in PyxisAPI._SAMPLE_PIXELS_CACHE:
                return PyxisAPI._SAMPLE_PIXELS_CACHE[cache_key]

            from PIL import Image
            import numpy as np
            import math
            img = Image.open(target_image_path).convert("RGBA")
            arr = np.array(img)
            h, w, c = arr.shape

            y_indices, x_indices = np.where(arr[:, :, 3] >= alpha_th)
            total_matching_px = len(x_indices)

            preview_step = max(1, step)
            grid_h = h // preview_step
            grid_w = w // preview_step
            if grid_h * grid_w > 8000:
                sub_factor = int(math.ceil(math.sqrt((grid_h * grid_w) / 8000.0)))
                preview_step = preview_step * sub_factor

            pixels_points = []
            for gy in range(0, h, preview_step):
                for gx in range(0, w, preview_step):
                    a_val = int(arr[gy, gx, 3])
                    if a_val >= alpha_th:
                        r_val = int(arr[gy, gx, 0])
                        g_val = int(arr[gy, gx, 1])
                        b_val = int(arr[gy, gx, 2])
                        pixels_points.append([float(gx), float(gy), r_val, g_val, b_val, a_val])

            res = {
                "pixels_points": pixels_points,
                "total_pixels": total_matching_px,
                "total_frames": total_frames,
                "frame_index": target_frame_idx,
                "preview_image_path": target_image_path,
                "img_width": w,
                "img_height": h,
                "step": step,
                "preview_step": preview_step
            }
            if len(PyxisAPI._SAMPLE_PIXELS_CACHE) > 500:
                PyxisAPI._SAMPLE_PIXELS_CACHE.clear()
            PyxisAPI._SAMPLE_PIXELS_CACHE[cache_key] = res
            return res
        except Exception as e:
            print(f"[sample_pixels_api Error] {e}", flush=True)
            return {"pixels_points": [], "total_pixels": 0, "total_frames": 1, "frame_index": 1, "error": str(e)}

    @staticmethod
    def _find_ffmpeg():
        """Resolves the executable path to the FFmpeg binary.

        Checks the bundled binary directory via `paths.get_bin_path("ffmpeg.exe")`,
        local relative candidate directories, and the operating system PATH via `shutil.which`.

        Returns:
            str: Resolved path to the FFmpeg executable or fallback command name.
        """
        try:
            from paths import get_bin_path
            target = get_bin_path("ffmpeg.exe")
            if os.path.isfile(target):
                return target
        except Exception:
            pass
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(base_dir, "bin", "ffmpeg.exe"),
            os.path.join(base_dir, "..", "bin", "ffmpeg.exe"),
            os.path.join(base_dir, "ffmpeg.exe"),
            os.path.join(base_dir, "..", "ffmpeg.exe"),
        ]
        for cand in candidates:
            if os.path.isfile(cand):
                return cand
        from shutil import which
        sys_ffmpeg = which("ffmpeg")
        if sys_ffmpeg:
            return sys_ffmpeg
        return "ffmpeg"

    _CACHED_H264_ENCODER = None

    @classmethod
    def _detect_best_h264_encoder(cls, ffmpeg_exe: str = None) -> tuple[str, list[str]]:
        """Probes and selects the optimal H.264 video encoder available on the system.

        Tests hardware-accelerated encoders in order of priority (`h264_nvenc`,
        `h264_amf`, `h264_qsv`) using a null-device command probe. Caches the
        first functioning hardware encoder, or falls back to software `libx264`
        with multi-threaded presets.

        Args:
            ffmpeg_exe (str, optional): Custom path to the FFmpeg binary. Defaults to None.

        Returns:
            tuple[str, list[str]]: A 2-tuple of `(encoder_name, ffmpeg_argument_list)`.
        """
        if cls._CACHED_H264_ENCODER is not None:
            return cls._CACHED_H264_ENCODER

        exe = ffmpeg_exe or cls._find_ffmpeg()
        candidates = [
            ("h264_nvenc", ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "16", "-tune", "hq", "-pix_fmt", "yuv420p"]),
            ("h264_amf", ["-c:v", "h264_amf", "-quality", "quality", "-rc", "cqp", "-qp_i", "16", "-qp_p", "16", "-pix_fmt", "yuv420p"]),
            ("h264_qsv", ["-c:v", "h264_qsv", "-preset", "medium", "-global_quality", "16", "-pix_fmt", "nv12"]),
        ]
        import subprocess
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if os.name == 'nt' else 0

        for enc_name, enc_args in candidates:
            try:
                probe_cmd = [
                    exe, "-y",
                    "-f", "lavfi", "-i", "color=s=1280x720:d=0.04",
                    *enc_args,
                    "-f", "null", "-"
                ]
                res = subprocess.run(probe_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags, timeout=2.0)
                if res.returncode == 0:
                    print(f"[Pyxis FFmpeg] Hardware encoder GPU detectado y activo: {enc_name}", flush=True)
                    cls._CACHED_H264_ENCODER = (enc_name, enc_args)
                    return cls._CACHED_H264_ENCODER
            except Exception:
                pass

        print("[Pyxis FFmpeg] Utilizando codificador x264 por software (multi-hilo optimizado)", flush=True)
        cls._CACHED_H264_ENCODER = ("libx264", ["-c:v", "libx264", "-preset", "medium", "-crf", "15", "-tune", "animation", "-pix_fmt", "yuv420p", "-threads", "0"])
        return cls._CACHED_H264_ENCODER

    @staticmethod
    def _shift_ass_timestamp(time_str: str, shift_ms: int) -> str:
        """Subtracts a millisecond offset from an ASS timestamp string (`H:MM:SS.cs`).

        Args:
            time_str (str): Formatted ASS timestamp.
            shift_ms (int): Milliseconds to subtract (clamped to zero).

        Returns:
            str: Shifted ASS timestamp string in `H:MM:SS.cs` format.
        """
        if not time_str:
            return "0:00:00.00"
        orig_ms = PyxisAPI._parse_ass_time(time_str)
        shifted_ms = max(0, orig_ms - shift_ms)
        cs = (shifted_ms % 1000) // 10
        total_s = shifted_ms // 1000
        s = total_s % 60
        total_m = total_s // 60
        m = total_m % 60
        h = total_m // 60
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    @classmethod
    def _shift_ass_line(cls, line_str: str, shift_ms: int) -> str:
        """Adjusts Start and End timestamps of a Dialogue or Comment ASS line.

        Parses the comma-delimited fields of the line and shifts indices 1 (Start)
        and 2 (End) backwards by `shift_ms` milliseconds for sub-clip audio/video sync.

        Args:
            line_str (str): Raw ASS Dialogue or Comment line.
            shift_ms (int): Millisecond offset to shift.

        Returns:
            str: Line string with shifted Start and End timestamps.
        """
        if not shift_ms or shift_ms <= 0:
            return line_str
        line_clean = line_str.lstrip('\ufeff')
        has_newline = line_str.endswith('\n')
        line_stripped = line_clean.rstrip('\r\n')

        is_dialogue = line_stripped.startswith("Dialogue:") or line_stripped.startswith("Dialogue :")
        is_comment = line_stripped.startswith("Comment:") or line_stripped.startswith("Comment :")
        if not (is_dialogue or is_comment):
            return line_str

        prefix = "Dialogue: " if is_dialogue else "Comment: "
        colon_pos = line_stripped.find(":")
        if colon_pos == -1:
            return line_str

        content = line_stripped[colon_pos + 1:].strip()
        fields = content.split(",", 9)
        if len(fields) >= 10:
            fields[1] = cls._shift_ass_timestamp(fields[1].strip(), shift_ms)
            fields[2] = cls._shift_ass_timestamp(fields[2].strip(), shift_ms)
            res = prefix + ",".join(fields)
            return (res + "\n") if has_newline else res
        return line_str

    @staticmethod
    def _is_valid_mp4(filepath):
        """Validates that an MP4 container file is non-empty and structurally intact.

        Checks file existence, minimum size (128 bytes), and inspects the initial
        and terminal byte chunks for valid ISO Base Media File Format atoms (`ftyp`
        and `moov`).

        Args:
            filepath (str): Filesystem path to the candidate MP4 video.

        Returns:
            bool: True if the file contains valid MP4 container headers and moov atom.
        """
        if not filepath or not os.path.isfile(filepath):
            return False
        try:
            size = os.path.getsize(filepath)
            if size < 128:
                return False
            with open(filepath, 'rb') as f:
                header = f.read(64)
                if b'ftyp' not in header and b'moov' not in header:
                    return False
                f.seek(0)
                chunk_start = f.read(min(size, 2 * 1024 * 1024))
                if b'moov' in chunk_start:
                    return True
                if size > 2 * 1024 * 1024:
                    f.seek(max(0, size - 2 * 1024 * 1024))
                    chunk_end = f.read(2 * 1024 * 1024)
                    if b'moov' in chunk_end:
                        return True
            return False
        except Exception:
            return False

    def _purge_corrupted_bg_media(self):
        """Scans and purges corrupted or temporary video cache files in background storage.

        Inspects `%APPDATA%/PyxisNodes/bg_media/` for partial `.tmp.mp4` files or
        containers that fail `_is_valid_mp4` validation, deleting invalid files to
        prevent playback hangs.
        """
        try:
            appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            bg_media_dir = os.path.join(appdata_dir, "PyxisNodes", "bg_media")
            if os.path.isdir(bg_media_dir):
                for fname in os.listdir(bg_media_dir):
                    if fname.endswith(".mp4"):
                        fpath = os.path.join(bg_media_dir, fname)
                        if fname.endswith(".tmp.mp4") or ".tmp_" in fname:
                            try: os.remove(fpath)
                            except Exception: pass
                        elif not self._is_valid_mp4(fpath):
                            print(f"[Pyxis Smart Cache] Purgando archivo corrupto detectado en bg_media: {fname}", flush=True)
                            try: os.remove(fpath)
                            except Exception: pass
        except Exception:
            pass

    @staticmethod
    def _clean_and_resolve_media_path(raw_path, base_ass_path=None, script_file=None):
        """Cleans Aegisub project URI prefixes and resolves media files against candidate paths.

        Strips enclosing quotes, normalises Aegisub macro prefixes (`?video:`, `?audio:`),
        filters out dummy media placeholders, and attempts resolution in order:
        direct filesystem path, directory of the active ASS script file, and directory
        of the base ASS file.

        Args:
            raw_path (str | None): Raw video/audio path string from the ASS header.
            base_ass_path (str | None, optional): Fallback base ASS script path. Defaults to None.
            script_file (str | None, optional): Explicit Aegisub script path. Defaults to None.

        Returns:
            str | None: Absolute resolved filesystem path to the valid media file, or None.
        """
        if not raw_path:
            return None
        p = str(raw_path).strip()
        if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
            p = p[1:-1].strip()
        lower_p = p.lower()
        if lower_p.startswith("?video:"):
            p = p[7:].strip()
        elif lower_p.startswith("?video"):
            p = p[6:].strip()
        elif lower_p.startswith("?audio:"):
            p = p[7:].strip()
        elif lower_p.startswith("?audio"):
            p = p[6:].strip()
        elif lower_p.startswith("dummy") or "dummy-audio" in lower_p or "silence?" in lower_p or lower_p.startswith("?dummy"):
            return None

        if not p:
            return None

        if os.path.isfile(p):
            return os.path.abspath(p)

        if script_file and os.path.exists(script_file):
            script_dir = os.path.dirname(os.path.abspath(script_file))
            rel = os.path.join(script_dir, p)
            if os.path.isfile(rel):
                return os.path.abspath(rel)

        if base_ass_path and os.path.exists(base_ass_path):
            ass_dir = os.path.dirname(os.path.abspath(base_ass_path))
            rel = os.path.join(ass_dir, p)
            if os.path.isfile(rel):
                return os.path.abspath(rel)

        return None

    @staticmethod
    def _get_aegisub_mru_media():
        """Reads the most recent valid video path from Aegisub's mru.json configuration.

        Acts as a defensive fallback when the active ASS header omits video path entries
        or uses relative paths detached from the disk structure. Inspects the `Video`
        MRU array in `%APPDATA%/Aegisub/mru.json`, filtering out dummy media.

        Returns:
            str | None: Absolute path to the most recent valid video, or None.
        """
        try:
            appdata = os.environ.get("APPDATA")
            if not appdata:
                return None
            mru_path = os.path.join(appdata, "Aegisub", "mru.json")
            if not os.path.isfile(mru_path):
                return None
            import json
            with open(mru_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            video_list = data.get("Video") or []
            for v in video_list:
                if not v or not isinstance(v, str):
                    continue
                v_clean = v.strip()
                if (v_clean.startswith('"') and v_clean.endswith('"')) or (v_clean.startswith("'") and v_clean.endswith("'")):
                    v_clean = v_clean[1:-1].strip()
                lower_v = v_clean.lower()
                if lower_v.startswith("dummy") or lower_v.startswith("?dummy") or "dummy-audio" in lower_v:
                    continue
                if os.path.isfile(v_clean):
                    return os.path.abspath(v_clean)
        except Exception:
            pass
        return None

    def _ensure_preview_media_clip(self, info, is_export=False):
        """Ensures the presence of an optimised MP4 preview clip in background cache storage.

        Generates or reuses a clipped MP4 sub-segment in `%APPDATA%/PyxisNodes/bg_media/`
        spanning the effective dialogue timeline window. Handles real video/audio multiplexing,
        audio-only background with solid colour canvas, or synthetic dummy video/audio generation
        using FFmpeg lavfi filters. Employs SHA-256 fingerprint caching and atomic file replacement.

        Args:
            info (dict[str, Any]): Media metadata dictionary containing resolution, frame rate,
                time intervals (`clip_start_sec`, `clip_dur_sec`), and resolved file paths.
            is_export (bool, optional): Whether rendering for hardsub export (higher quality)
                or live player preview. Defaults to False.

        Returns:
            str | None: Filesystem path to the validated MP4 clip file, or None on error.
        """
        if not hasattr(self, "_clip_lock"):
            import threading
            self._clip_lock = threading.RLock()

        with self._clip_lock:
            try:
                appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
                bg_media_dir = os.path.join(appdata_dir, "PyxisNodes", "bg_media")
                os.makedirs(bg_media_dir, exist_ok=True)

                res_x = int(info.get("res_x", 1280))
                res_y = int(info.get("res_y", 720))
                res_x = max(2, res_x - (res_x % 2))
                res_y = max(2, res_y - (res_y % 2))
                fps = float(info.get("fps") or 23.976)
                clip_start_sec = float(info.get("clip_start_sec", 0.0))
                clip_dur_sec = float(info.get("clip_duration_sec", 15.0))
                clip_end_sec = float(info.get("clip_end_sec", clip_start_sec + clip_dur_sec))
                real_video = info.get("real_video_file")
                real_audio = info.get("real_audio_file")
                dummy_info = info.get("dummy_info") or {}
                color_hex = str(dummy_info.get("color_hex") or "969696").lower()

                ffmpeg_exe = self._find_ffmpeg()
                import subprocess
                creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if os.name == 'nt' else 0

                if is_export:
                    clip_prefix = "export_bg"
                    v_preset = "ultrafast"
                    v_crf = "18"
                    deblock_args = []
                else:
                    clip_prefix = "preview_bg"
                    v_preset = "fast"
                    v_crf = "21"
                    deblock_args = ["-deblock", "-1:-1"]

                import hashlib
                v_mtime = os.path.getmtime(real_video) if (real_video and os.path.isfile(real_video)) else 0
                v_size = os.path.getsize(real_video) if (real_video and os.path.isfile(real_video)) else 0
                a_mtime = os.path.getmtime(real_audio) if (real_audio and os.path.isfile(real_audio)) else 0
                a_size = os.path.getsize(real_audio) if (real_audio and os.path.isfile(real_audio)) else 0

                if not real_video and not real_audio:
                    d_meta_dur = (info.get("media_meta") or {}).get("duration_sec")
                    if d_meta_dur and float(d_meta_dur) > 0:
                        raw_dur = float(d_meta_dur)
                    elif dummy_info.get("frames") and dummy_info.get("fps") and float(dummy_info["fps"]) > 0:
                        raw_dur = float(dummy_info["frames"]) / float(dummy_info["fps"])
                    else:
                        raw_dur = float(info.get("total_duration_sec") or max(clip_end_sec, 15.0))

                    if raw_dur <= 180.0:
                        dummy_target_dur = max(raw_dur, clip_end_sec)
                    else:
                        dummy_target_dur = max(clip_end_sec + 10.0, 60.0)

                    key_src = (
                        f"dummy:{res_x}x{res_y}:{fps:.3f}:{color_hex}:{dummy_target_dur:.3f}|"
                        f"mode:{clip_prefix}:{v_preset}:{v_crf}"
                    )
                    hash_16 = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:16]
                    clip_type = "dummy"
                    clip_filename = f"{clip_prefix}_dummy_{hash_16}_{res_x}x{res_y}_{dummy_target_dur:.2f}s.mp4"
                else:
                    key_src = (
                        f"v:{real_video}:{v_mtime}:{v_size}|"
                        f"a:{real_audio}:{a_mtime}:{a_size}|"
                        f"{clip_start_sec:.3f}:{clip_dur_sec:.3f}:{res_x}x{res_y}:{fps:.2f}:{color_hex}|"
                        f"mode:{clip_prefix}:{v_preset}:{v_crf}"
                    )
                    hash_16 = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:16]
                    clip_type = "real" if real_video else "audio"
                    clip_filename = f"{clip_prefix}_{clip_type}_{hash_16}_{res_x}x{res_y}_{clip_start_sec:.2f}s_{clip_dur_sec:.2f}s.mp4"
                clip_path = os.path.join(bg_media_dir, clip_filename)

                if os.path.exists(clip_path):
                    if self._is_valid_mp4(clip_path):
                        try:
                            os.utime(clip_path, None)
                        except Exception:
                            pass
                        return clip_path
                    else:
                        print(f"[Pyxis Smart Cache Purge] Archivo MP4 corrupto o incompleto detectado: {clip_path}. Eliminando...", flush=True)
                        try:
                            os.remove(clip_path)
                        except Exception:
                            pass

                import threading
                import time
                temp_clip = f"{clip_path}.tmp_{os.getpid()}_{threading.get_ident()}_{int(time.time()*1000)}.mp4"

                v_codec = ["-c:v", "libx264", "-preset", v_preset, "-crf", v_crf]
                if deblock_args:
                    v_codec.extend(deblock_args)

                if real_video and os.path.isfile(real_video) and (not real_audio or real_audio == real_video):
                    cmd = [
                        ffmpeg_exe, "-y",
                        "-ss", f"{clip_start_sec:.3f}",
                        "-t", f"{clip_dur_sec:.3f}",
                        "-i", real_video,
                        "-avoid_negative_ts", "make_zero",
                        *v_codec,
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-movflags", "+faststart",
                        temp_clip
                    ]
                elif real_video and os.path.isfile(real_video) and real_audio and os.path.isfile(real_audio):
                    cmd = [
                        ffmpeg_exe, "-y",
                        "-ss", f"{clip_start_sec:.3f}",
                        "-t", f"{clip_dur_sec:.3f}",
                        "-i", real_video,
                        "-ss", f"{clip_start_sec:.3f}",
                        "-t", f"{clip_dur_sec:.3f}",
                        "-i", real_audio,
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-avoid_negative_ts", "make_zero",
                        *v_codec,
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-shortest",
                        "-movflags", "+faststart",
                        temp_clip
                    ]
                elif real_audio and os.path.isfile(real_audio):
                    cmd = [
                        ffmpeg_exe, "-y",
                        "-f", "lavfi", "-i", f"color=c=0x{color_hex}:s={res_x}x{res_y}:r={fps:.3f}:d={clip_dur_sec:.3f}",
                        "-ss", f"{clip_start_sec:.3f}",
                        "-t", f"{clip_dur_sec:.3f}",
                        "-i", real_audio,
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-avoid_negative_ts", "make_zero",
                        *v_codec,
                        "-tune", "stillimage",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-shortest",
                        "-movflags", "+faststart",
                        temp_clip
                    ]
                else:
                    cmd = [
                        ffmpeg_exe, "-y",
                        "-f", "lavfi", "-i", f"color=c=0x{color_hex}:s={res_x}x{res_y}:r={fps:.3f}:d={dummy_target_dur:.3f}",
                        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        *v_codec,
                        "-tune", "stillimage",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "aac",
                        "-b:a", "64k",
                        "-shortest",
                        "-movflags", "+faststart",
                        temp_clip
                    ]

                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creationflags)
                if proc.returncode == 0 and os.path.exists(temp_clip) and self._is_valid_mp4(temp_clip):
                    try:
                        os.replace(temp_clip, clip_path)
                        actual_dur = dummy_target_dur if (not real_video and not real_audio) else clip_dur_sec
                        print(f"[Pyxis Smart Cache] Clip {clip_prefix} generado ({clip_type}): {clip_filename} ({actual_dur:.2f}s)", flush=True)
                        return clip_path
                    except Exception as e_mv:
                        print(f"[Pyxis Smart Cache Error moving clip] {e_mv}", flush=True)
                        if os.path.exists(clip_path) and self._is_valid_mp4(clip_path):
                            return clip_path
                else:
                    print(f"[Pyxis FFmpeg Clip Error] {proc.stderr}", flush=True)
                    if os.path.exists(temp_clip):
                        try:
                            os.remove(temp_clip)
                        except Exception:
                            pass

            except Exception as e:
                print(f"[Pyxis Error in _ensure_preview_media_clip] {e}", flush=True)

            return None

    def _matches_output_node(self, node, target_ids, all_output_nodes=None):
        """Evaluates whether an Output node matches the targeted output filter list.

        Checks node identifiers across multiple representations: literal node ID,
        integer ID, node title, property `output_id`, widget `queue_id`, or 1-based
        index within the ordered list of all Output nodes.

        Args:
            node (dict[str, Any]): Node data dictionary from the graph.
            target_ids (list | tuple | set | str | int | None): Target output criteria.
                If None or containing wildcard ('all', '*'), matches any output node.
            all_output_nodes (list[dict[str, Any]] | None, optional): Full list of
                Output nodes in the graph for index-based matching. Defaults to None.

        Returns:
            bool: True if the node satisfies the target criteria, False otherwise.
        """
        if not node:
            return False
        n_type = str(node.get('type', '')).lower()
        if 'output' not in n_type:
            return False

        if target_ids is None:
            return True

        if isinstance(target_ids, (list, tuple, set)):
            target_strs = set()
            for x in target_ids:
                if x is not None:
                    for s in str(x).split(','):
                        s_c = s.strip()
                        if s_c:
                            target_strs.add(s_c)
        else:
            target_strs = set(s.strip() for s in str(target_ids).split(',') if s.strip())

        if not target_strs:
            return False

        if any(x.lower() in ('all', '*', 'all_outputs') for x in target_strs):
            return True

        nid_str = str(node.get('id', ''))
        nid_int = node.get('id')
        node_title = str(node.get('title') or '').strip()
        props = node.get('properties', {}) or {}
        out_id = str(props.get('output_id') or '').strip()
        queue_id = str(props.get('queue_id') or props.get('Queue ID') or props.get('Queue_ID') or '').strip()
        if not queue_id and isinstance(node.get('widgets'), list):
            for w in node.get('widgets'):
                if isinstance(w, dict) and str(w.get('property') or w.get('name') or '').lower() in ('queue_id', 'queue id', 'output_id'):
                    w_val = str(w.get('value') or '').strip()
                    if w_val:
                        queue_id = w_val
                        break

        numeric_targets = set()
        for t in target_strs:
            try:
                numeric_targets.add(int(t))
            except (ValueError, TypeError):
                pass

        if nid_str in target_strs:
            return True
        if nid_int is not None and nid_int in numeric_targets:
            return True
        if node_title and node_title in target_strs:
            return True
        if out_id and (out_id in target_strs or (_to_int_or_default(out_id, None) in numeric_targets)):
            return True
        if queue_id and (queue_id in target_strs or (_to_int_or_default(queue_id, None) in numeric_targets)):
            return True
        if 'default' in (x.lower() for x in target_strs) and (not out_id or out_id.lower() == 'default'):
            return True

        if all_output_nodes and node in all_output_nodes:
            idx_1based = all_output_nodes.index(node) + 1
            if (str(idx_1based) in target_strs or 
                idx_1based in numeric_targets or 
                f"Output {idx_1based}" in target_strs or 
                f"Output_{idx_1based}" in target_strs or
                f"Output {idx_1based}".lower() in (x.lower() for x in target_strs) or 
                f"Output_{idx_1based}".lower() in (x.lower() for x in target_strs)):
                return True

        return False

    def _calculate_effective_dialogue_range(self, dialogues, payload=None, target_output_id=None):
        """Computes the effective millisecond start/end window for subtitle preview and rendering.

        Inspects dialogue lines against targeted Output nodes, respecting selection scopes
        (`All Lines`, `Style Lines`, or `Selected Lines`), and adds a 2.0-second safety margin
        around the boundaries to accommodate kinematic and particle lead-in / lead-out effects.

        Args:
            dialogues (list): List of parsed ASS dialogue objects or dictionaries.
            payload (dict | None, optional): Graph topology payload. Defaults to None.
            target_output_id (list | str | int | None, optional): Filter criteria for Output nodes.

        Returns:
            tuple[int, int, float, float, float, int]: A 6-tuple containing:
                `(min_start_ms, max_end_ms, clip_start_sec, clip_end_sec, clip_duration_sec, clip_start_ms)`.
        """
        if not dialogues:
            return 0, 15000, 0.0, 15.0, 15.0, 0

        target_ids = []
        if isinstance(target_output_id, list):
            for x in target_output_id:
                if x is not None:
                    s_clean = str(x).strip()
                    if s_clean: target_ids.append(s_clean)
        elif target_output_id is not None:
            s_clean = str(target_output_id).strip()
            if s_clean: target_ids.append(s_clean)

        if not payload:
            try:
                s_json = self.get_session_graph()
                if s_json:
                    import json
                    payload = json.loads(s_json)
            except Exception:
                payload = None

        min_d_start = None
        max_d_end = None

        graph_data = self._normalize_graph(payload) if payload else {}
        nodes_dict = graph_data.get("nodes", {}) if isinstance(graph_data, dict) else {}
        if isinstance(nodes_dict, list):
            nodes_dict = {n.get("id"): n for n in nodes_dict if isinstance(n, dict)}

        all_output_nodes = [n for n in nodes_dict.values() if 'output' in str(n.get('type', '')).lower()]
        matching_outputs = [n for n in all_output_nodes if self._matches_output_node(n, target_ids, all_output_nodes)]

        use_all_lines = False
        use_style_lines = False
        target_styles = set()

        if matching_outputs:
            for s_node in matching_outputs:
                props = s_node.get('properties', {}) or {}
                apply_to = str(props.get('apply_to', 'Selected Lines')).strip().lower()
                if apply_to in ['all lines', 'all']:
                    use_all_lines = True
                    break
                elif apply_to in ['style lines', 'style']:
                    use_style_lines = True
                    st_name = str(props.get('style', '')).strip()
                    if st_name:
                        target_styles.add(st_name)

        if use_style_lines:
            for d in dialogues:
                is_sel = False
                st_name = ""
                if isinstance(d, dict):
                    is_sel = bool(d.get('is_selected', False) or (d.get('metrics') and d['metrics'].get('sel')))
                    st_name = str(d.get('style_name', ''))
                    if not st_name and 'raw' in d:
                        raw = str(d.get('raw', ''))
                        fields = raw.split(',', 9)
                        if len(fields) >= 4:
                            st_name = fields[3].strip()
                elif hasattr(d, 'is_selected') and hasattr(d, 'style_name'):
                    is_sel = getattr(d, 'is_selected', False)
                    st_name = getattr(d, 'style_name', '')
                if is_sel and st_name:
                    target_styles.add(st_name)

            if not target_styles:
                for d in dialogues:
                    st_name = ""
                    if isinstance(d, dict):
                        st_name = str(d.get('style_name', ''))
                        if not st_name and 'raw' in d:
                            raw = str(d.get('raw', ''))
                            fields = raw.split(',', 9)
                            if len(fields) >= 4:
                                st_name = fields[3].strip()
                    elif hasattr(d, 'style_name'):
                        st_name = getattr(d, 'style_name', '')
                    if st_name:
                        target_styles.add(st_name)

        starts = []
        ends = []
        for d in dialogues:
            st = None
            et = None
            is_sel = False
            style_name = ""
            if isinstance(d, dict):
                raw_str = str(d.get('raw', '')).strip()
                if raw_str.startswith('Comment:') or raw_str.startswith('Comment :') or d.get('is_comment'):
                    continue
                st = d.get('start_time')
                et = d.get('end_time')
                is_sel = bool(d.get('is_selected', False) or (d.get('metrics') and d['metrics'].get('sel')))
                style_name = str(d.get('style_name', ''))
                if (st is None or et is None or not style_name) and raw_str:
                    if raw_str.startswith('Dialogue:') or raw_str.startswith('Dialogue :'):
                        fields = raw_str.split(',', 9)
                        if len(fields) >= 4:
                            if st is None:
                                st = self._parse_ass_time(fields[1])
                            if et is None:
                                et = self._parse_ass_time(fields[2])
                            if not style_name:
                                style_name = fields[3].strip()
            elif hasattr(d, 'start_time') and hasattr(d, 'end_time'):
                if getattr(d, 'is_comment', False):
                    continue
                st = d.start_time
                et = d.end_time
                is_sel = getattr(d, 'is_selected', False)
                style_name = getattr(d, 'style_name', '')

            if st is None or et is None:
                continue

            if use_all_lines:
                starts.append(st)
                ends.append(et)
            elif use_style_lines and target_styles and style_name in target_styles:
                starts.append(st)
                ends.append(et)
            elif is_sel:
                starts.append(st)
                ends.append(et)

        if not starts or not ends:
            for d in dialogues:
                st = None
                et = None
                if isinstance(d, dict):
                    st = d.get('start_time')
                    et = d.get('end_time')
                    if (st is None or et is None) and 'raw' in d:
                        raw = str(d.get('raw', ''))
                        if raw.startswith('Dialogue:') or raw.startswith('Dialogue :') or raw.startswith('Comment:') or raw.startswith('Comment :'):
                            fields = raw.split(',', 9)
                            if len(fields) >= 3:
                                st = self._parse_ass_time(fields[1])
                                et = self._parse_ass_time(fields[2])
                elif hasattr(d, 'start_time') and hasattr(d, 'end_time'):
                    st = d.start_time
                    et = d.end_time
                if st is not None and et is not None:
                    starts.append(st)
                    ends.append(et)

        min_start_ms = min(starts) if starts else 0
        max_end_ms = max(ends) if ends else 15000

        clip_start_sec = max(0.0, (min_start_ms - 2000) / 1000.0)
        clip_end_sec = (max_end_ms + 2000) / 1000.0
        clip_duration_sec = max(2.0, clip_end_sec - clip_start_sec)
        clip_start_ms = int(clip_start_sec * 1000)

        return min_start_ms, max_end_ms, clip_start_sec, clip_end_sec, clip_duration_sec, clip_start_ms

    def invalidate_aegisub_cache(self):
        """Invalidates all cached Aegisub project state, parsed dialogues, and telemetry results.

        Clears file hashes, cached parsed models, temporary file paths, last generated preview
        ASS content, and resets the in-memory `GLOBAL_TELEMETRY_MANAGER` state.
        """
        self._cached_aegisub_info = None
        self._cached_aegisub_parsed = None
        self._aegisub_temp_hash = None
        self._aegisub_temp_mtime = None
        self._aegisub_temp_path = None
        self._last_preview_ass_content = None
        self._last_preview_ass_info = None
        try:
            from ass_telemetry_engine import GLOBAL_TELEMETRY_MANAGER
            GLOBAL_TELEMETRY_MANAGER.clear_last_result()
        except Exception:
            pass

    def _load_and_cache_aegisub_source(self, payload=None, target_output_id=None, force_reload=False):
        """Parses and caches the active Aegisub ASS subtitle project with SHA-256 fingerprinting.

        Reads `self.temp_ass` via `ASSParser`, resolving script video/audio files, effective
        dialogue ranges, primary font family and sizes, and probes detailed media metadata
        via FFmpeg. Caches the result dictionary in `_cached_aegisub_info`.

        Args:
            payload (dict | None, optional): Graph topology for Output node resolution. Defaults to None.
            target_output_id (list | str | int | None, optional): Targeted Output node IDs. Defaults to None.
            force_reload (bool, optional): Force re-parsing even if SHA-256 hash matches. Defaults to False.

        Returns:
            dict[str, Any]: Project information dictionary containing styles, dialogues, resolution,
                frame rates, media paths, and clip time windows.
        """
        if not self.temp_ass or not os.path.isfile(self.temp_ass):
            return {"has_aegisub": False, "source": "aegisub"}

        try:
            current_mtime = os.path.getmtime(self.temp_ass)
            current_path = os.path.abspath(self.temp_ass)
            import hashlib
            with open(self.temp_ass, "rb") as fp:
                current_hash = hashlib.sha256(fp.read()).hexdigest()

            parsed_cached = getattr(self, '_cached_aegisub_parsed', None)
            cached_hash = getattr(self, '_aegisub_temp_hash', None)
            cached_path = getattr(self, '_aegisub_temp_path', None)

            if force_reload or not parsed_cached or cached_hash != current_hash or cached_path != current_path:
                from ass_parser import ASSParser
                parsed = ASSParser.read_file(self.temp_ass)
                if not parsed or not parsed.dialogues:
                    return {"has_aegisub": False, "source": "aegisub"}
                self._cached_aegisub_parsed = parsed
                self._aegisub_temp_hash = current_hash
                self._aegisub_temp_mtime = current_mtime
                self._aegisub_temp_path = current_path
            else:
                parsed = self._cached_aegisub_parsed

            styles, dialogues, res_x, res_y, frame_dur = parsed.styles, parsed.dialogues, parsed.res_x, parsed.res_y, parsed.frame_dur

            video_file = getattr(parsed, 'video_file', '')
            audio_file = getattr(parsed, 'audio_file', '')
            is_dummy_video = getattr(parsed, 'is_dummy_video', False)
            is_dummy_audio = getattr(parsed, 'is_dummy_audio', False)
            dummy_info = getattr(parsed, 'dummy_info', {}) or {}
            fps = dummy_info.get("fps") or (1000.0 / frame_dur if frame_dur > 0 else 23.976)

            script_file = getattr(parsed, 'script_file', None)
            real_video = None
            if not is_dummy_video:
                real_video = self._clean_and_resolve_media_path(video_file, self.temp_ass, script_file=script_file)
                if not real_video:
                    real_video = self._get_aegisub_mru_media()

            real_audio = None
            if not is_dummy_audio:
                real_audio = self._clean_and_resolve_media_path(audio_file, self.temp_ass, script_file=script_file)
                if not real_audio and real_video:
                    real_audio = real_video

            if not real_audio and real_video:
                real_audio = real_video

            min_start_ms, max_end_ms, clip_start_sec, clip_end_sec, clip_duration_sec, clip_start_ms = self._calculate_effective_dialogue_range(
                dialogues, payload=payload, target_output_id=target_output_id
            )

            primary_font_name = "Arial"
            primary_font_size = 65
            target_style_name = None
            if dialogues:
                for d in dialogues:
                    is_sel = False
                    st_name = ""
                    if isinstance(d, dict):
                        is_sel = bool(d.get('is_selected', False) or (d.get('metrics') and d['metrics'].get('sel')))
                        st_name = str(d.get('style_name', ''))
                        if not st_name and 'raw' in d:
                            fields = str(d['raw']).split(',', 9)
                            if len(fields) >= 4:
                                st_name = fields[3].strip()
                    elif hasattr(d, 'is_selected') and hasattr(d, 'style_name'):
                        is_sel = getattr(d, 'is_selected', False)
                        st_name = getattr(d, 'style_name', '')
                    if is_sel and st_name:
                        target_style_name = st_name
                        break
                if not target_style_name and dialogues:
                    first_d = dialogues[0]
                    if isinstance(first_d, dict):
                        target_style_name = str(first_d.get('style_name', ''))
                        if not target_style_name and 'raw' in first_d:
                            fields = str(first_d['raw']).split(',', 9)
                            if len(fields) >= 4:
                                target_style_name = fields[3].strip()
                    elif hasattr(first_d, 'style_name'):
                        target_style_name = getattr(first_d, 'style_name', '')

            if styles:
                matched_style = styles.get(target_style_name) if target_style_name else None
                if not matched_style and target_style_name:
                    for s_k, s_v in styles.items():
                        if str(s_k).strip().lower() == target_style_name.strip().lower():
                            matched_style = s_v
                            break
                if not matched_style:
                    matched_style = next(iter(styles.values()))

                if isinstance(matched_style, dict):
                    primary_font_name = matched_style.get("Fontname") or matched_style.get("fontname") or "Arial"
                    try:
                        primary_font_size = int(matched_style.get("Fontsize", 65))
                    except Exception:
                        pass

            info_dict = {
                "source": "aegisub",
                "has_aegisub": True,
                "path": self.temp_ass,
                "res_x": res_x,
                "res_y": res_y,
                "aspect_ratio": (res_x / res_y) if res_y > 0 else (16 / 9),
                "fps": fps,
                "frame_dur": frame_dur,
                "styles": styles,
                "dialogues": dialogues,
                "min_start_ms": min_start_ms,
                "max_end_ms": max_end_ms,
                "clip_start_sec": clip_start_sec,
                "clip_end_sec": clip_end_sec,
                "clip_duration_sec": clip_duration_sec,
                "clip_start_ms": clip_start_ms,
                "render_start_sec": clip_start_sec,
                "render_duration_sec": clip_duration_sec,
                "audio_file": real_audio,
                "video_file": real_video,
                "real_video_file": real_video,
                "real_audio_file": real_audio,
                "has_real_video": bool(real_video and os.path.isfile(real_video)),
                "has_real_audio": bool(real_audio and os.path.isfile(real_audio)),
                "dummy_info": dummy_info,
                "font_name": primary_font_name,
                "font_size": primary_font_size,
            }

            info_dict["clip_path"] = real_video or real_audio or None

            info_dict["media_meta"] = self._probe_media_metadata(
                video_file=real_video,
                audio_file=real_audio,
                dummy_info=dummy_info if is_dummy_video else None,
                default_fps=fps,
                res_x=res_x,
                res_y=res_y
            )
            dur_sec = (info_dict.get("media_meta") or {}).get("duration_sec")
            if dur_sec and float(dur_sec) > info_dict["clip_start_sec"]:
                info_dict["clip_end_sec"] = min(info_dict["clip_end_sec"], float(dur_sec))
                info_dict["clip_duration_sec"] = max(0.5, info_dict["clip_end_sec"] - info_dict["clip_start_sec"])
                info_dict["render_duration_sec"] = info_dict["clip_duration_sec"]

            self._cached_aegisub_info = info_dict
            return info_dict
        except Exception as e:
            print(f"[Pyxis Error in _load_and_cache_aegisub_source] {e}", flush=True)
            return {"has_aegisub": False, "source": "aegisub"}

    def _ensure_fallback_dummy_url(self):
        """Generates a default dark grey dummy video URL as fallback when no media is available.

        Returns:
            str: HTTP endpoint URL on local daemon streaming the fallback video.
        """
        try:
            fallback_info = {
                "res_x": 1280,
                "res_y": 720,
                "fps": 23.976,
                "clip_start_sec": 0.0,
                "clip_duration_sec": 15.0,
                "real_video_file": None,
                "real_audio_file": None,
                "dummy_info": {"color_hex": "2a2a2a"}
            }
            clip_path = self._ensure_preview_media_clip(fallback_info)
            if clip_path and os.path.exists(clip_path) and self._is_valid_mp4(clip_path):
                import urllib.parse
                quoted_path = urllib.parse.quote(clip_path)
                return f"http://127.0.0.1:28723/media_file?path={quoted_path}"
        except Exception as e:
            print(f"[Pyxis Fallback Dummy Error] {e}", flush=True)
        return ""

    def get_preview_video_data_url(self, source="base", target_output_id=None, payload=None):
        """Resolves the streaming HTTP URL for the preview video.

        Attempts direct byte streaming via HTTP 206 Partial Content for local video files.
        If only audio is present, streams original audio. If media is missing or dummy,
        generates or serves the cached synthetic MP4 preview clip.

        Args:
            source (str, optional): Media source ("aegisub" or "base"). Defaults to "base".
            target_output_id (list | str | int | None, optional): Filter criteria for Output nodes.
            payload (dict | None, optional): Graph topology for timeline evaluation.

        Returns:
            str: Daemon HTTP streaming URL for the video resource.
        """
        try:
            info = self.get_preview_info(source=source, target_output_id=target_output_id, payload=payload)
            # 1. Direct stream of original video via HTTP 206 Partial Content (no FFmpeg transcode)
            user_video = info.get("real_video_file")
            if user_video and os.path.exists(user_video):
                import urllib.parse
                quoted_path = urllib.parse.quote(user_video)
                return f"http://127.0.0.1:28723/media_file?path={quoted_path}"

            # 2. If no video but user audio exists, direct stream original audio
            user_audio = info.get("real_audio_file")
            if user_audio and os.path.exists(user_audio):
                import urllib.parse
                quoted_path = urllib.parse.quote(user_audio)
                return f"http://127.0.0.1:28723/media_file?path={quoted_path}"

            # 3. Fallback: Dummy video clip (e.g. preview_base template with ?dummy Aegisub media)
            clip_path = info.get("clip_path") or self._ensure_preview_media_clip(info)
            if clip_path and os.path.exists(clip_path) and self._is_valid_mp4(clip_path):
                import urllib.parse
                quoted_path = urllib.parse.quote(clip_path)
                return f"http://127.0.0.1:28723/media_file?path={quoted_path}"
        except Exception as e:
            print(f"[Pyxis Error getting preview video URL] {e}", flush=True)
        return self._ensure_fallback_dummy_url()

    def get_preview_audio_data_url(self, source="base", target_output_id=None, payload=None):
        """Resolves the streaming HTTP URL for the preview audio track.

        Args:
            source (str, optional): Media source ("aegisub" or "base"). Defaults to "base".
            target_output_id (list | str | int | None, optional): Filter criteria for Output nodes.
            payload (dict | None, optional): Graph topology for timeline evaluation.

        Returns:
            str: Daemon HTTP streaming URL for the audio resource, or empty string.
        """
        try:
            info = self.get_preview_info(source=source, target_output_id=target_output_id, payload=payload)
            user_audio = info.get("real_audio_file")
            if user_audio and os.path.exists(user_audio):
                import urllib.parse
                quoted_path = urllib.parse.quote(user_audio)
                return f"http://127.0.0.1:28723/media_file?path={quoted_path}"
        except Exception as e:
            print(f"[Pyxis Error getting preview audio URL] {e}", flush=True)
        return ""

    def _probe_media_metadata(self, video_file=None, audio_file=None, dummy_info=None, default_fps=23.976, res_x=1280, res_y=720):
        """Extracts technical stream metadata from video and audio containers using FFmpeg.

        Invokes FFmpeg probe via subprocess with in-memory 7-tuple hash caching. Parses
        stream descriptors using regular expressions for video codec (H.264, H.265, VP9, AV1),
        resolution, exact frame rate, audio codec, sampling rate (kHz), audio channels
        (Stereo/Mono), overall bitrate, and duration in seconds.

        Args:
            video_file (str | None, optional): Path to the video container. Defaults to None.
            audio_file (str | None, optional): Path to the audio file. Defaults to None.
            dummy_info (dict | None, optional): Fallback parameters for synthetic media. Defaults to None.
            default_fps (float, optional): Fallback frame rate. Defaults to 23.976.
            res_x (int, optional): Fallback width in pixels. Defaults to 1280.
            res_y (int, optional): Fallback height in pixels. Defaults to 720.

        Returns:
            dict[str, Any]: Dictionary containing codecs, resolution, frame rate, bitrate,
                duration, and channel specifications.
        """
        if not hasattr(self, "_media_metadata_cache"):
            self._media_metadata_cache = {}

        v_mtime = 0
        if video_file and os.path.isfile(video_file):
            try:
                v_mtime = os.path.getmtime(video_file)
            except Exception:
                pass

        a_mtime = 0
        if audio_file and os.path.isfile(audio_file):
            try:
                a_mtime = os.path.getmtime(audio_file)
            except Exception:
                pass

        cache_key = f"{video_file}_{v_mtime}_{audio_file}_{a_mtime}_{bool(dummy_info)}_{res_x}x{res_y}_{default_fps}"
        if cache_key in self._media_metadata_cache:
            return self._media_metadata_cache[cache_key]

        meta = {
            "video_codec": "NO VIDEO",
            "resolution": f"{res_x}x{res_y}",
            "res_x": res_x,
            "res_y": res_y,
            "fps": default_fps,
            "fps_str": f"{default_fps:.2f} fps",
            "audio_codec": "NO AUDIO",
            "audio_hz": None,
            "audio_hz_str": "N/A",
            "bitrate_kbps": None,
            "bitrate_str": "N/A",
            "audio_channels": "N/A",
            "duration": "00:00",
            "duration_sec": None
        }

        if dummy_info and isinstance(dummy_info, dict):
            meta["video_codec"] = "DUMMY"
            meta["audio_codec"] = "DUMMY"
            d_fps = dummy_info.get("fps") or default_fps
            meta["fps"] = d_fps
            meta["fps_str"] = f"{d_fps:.2f} fps" if d_fps else f"{default_fps:.2f} fps"
            d_w = dummy_info.get("width", res_x)
            d_h = dummy_info.get("height", res_y)
            meta["resolution"] = f"{d_w}x{d_h}"
            meta["res_x"] = d_w
            meta["res_y"] = d_h
            if dummy_info.get("frames") and d_fps and float(d_fps) > 0:
                d_sec = float(dummy_info["frames"]) / float(d_fps)
                meta["duration_sec"] = round(d_sec, 3)
                m = int(d_sec // 60)
                s = int(d_sec % 60)
                meta["duration"] = f"{m:02d}:{s:02d}"

        ffmpeg_bin = self._find_ffmpeg()
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if os.name == 'nt' else 0

        if video_file and os.path.isfile(video_file) and ffmpeg_bin:
            try:
                cmd = [ffmpeg_bin, "-hide_banner", "-i", video_file]
                res = subprocess.run(
                    cmd,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    creationflags=creationflags,
                    timeout=5
                )
                out = res.stderr or ""

                m_dur = re.search(r'Duration:\s*(\d+:\d+:\d+(?:\.\d+)?)', out)
                if m_dur:
                    dur_str = m_dur.group(1)
                    parts = dur_str.split(':')
                    if len(parts) >= 3:
                        meta["duration"] = f"{int(parts[0])*60 + int(parts[1]):02d}:{int(float(parts[2])):02d}"
                        meta["duration_sec"] = round(int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2]), 3)
                    else:
                        meta["duration"] = dur_str

                m_br = re.search(r'bitrate:\s*(\d+)\s*kb/s', out)
                if m_br:
                    kbps = int(m_br.group(1))
                    meta["bitrate_kbps"] = kbps
                    if kbps >= 1000:
                        meta["bitrate_str"] = f"{kbps/1000.0:.1f} Mb/s"
                    else:
                        meta["bitrate_str"] = f"{kbps} kb/s"

                m_vid = re.search(r'Stream\s+#\d+:\d+.*?Video:\s*([a-zA-Z0-9_-]+).*?,\s*(\d{2,5}x\d{2,5})', out)
                if m_vid:
                    v_raw = m_vid.group(1).lower()
                    if "h264" in v_raw or "avc" in v_raw:
                        meta["video_codec"] = "H.264"
                    elif "hevc" in v_raw or "h265" in v_raw:
                        meta["video_codec"] = "H.265"
                    elif "vp9" in v_raw:
                        meta["video_codec"] = "VP9"
                    elif "av01" in v_raw or "av1" in v_raw:
                        meta["video_codec"] = "AV1"
                    else:
                        meta["video_codec"] = m_vid.group(1).upper()
                    meta["resolution"] = m_vid.group(2)
                    try:
                        rw, rh = [int(x) for x in m_vid.group(2).split('x')]
                        meta["res_x"] = rw
                        meta["res_y"] = rh
                    except Exception:
                        pass

                m_fps = re.search(r'(\d+(?:\.\d+)?)\s*fps', out)
                if m_fps:
                    parsed_fps = float(m_fps.group(1))
                    meta["fps"] = parsed_fps
                    meta["fps_str"] = f"{parsed_fps:.2f} fps" if (parsed_fps % 1 != 0) else f"{int(parsed_fps)} fps"

                m_aud = re.search(r'Stream\s+#\d+:\d+.*?Audio:\s*([a-zA-Z0-9_-]+).*?,\s*(\d+)\s*Hz', out)
                if m_aud:
                    meta["audio_codec"] = m_aud.group(1).upper()
                    hz = int(m_aud.group(2))
                    meta["audio_hz"] = hz
                    meta["audio_hz_str"] = f"{hz/1000.0:.1f} kHz"

                m_ch = re.search(r'Audio:.*?(mono|stereo|[0-9\.]+\s*channels?)', out, re.IGNORECASE)
                if m_ch:
                    ch_raw = m_ch.group(1).lower()
                    if "stereo" in ch_raw:
                        meta["audio_channels"] = "Stereo"
                    elif "mono" in ch_raw:
                        meta["audio_channels"] = "Mono"
                    else:
                        meta["audio_channels"] = ch_raw.title()
            except Exception as e:
                print(f"[Pyxis Meta Probe Video Error] {e}", flush=True)

        target_audio = audio_file if (audio_file and audio_file != video_file) else None
        if target_audio and os.path.isfile(target_audio) and ffmpeg_bin:
            try:
                cmd = [ffmpeg_bin, "-hide_banner", "-i", target_audio]
                res = subprocess.run(
                    cmd,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    creationflags=creationflags,
                    timeout=5
                )
                out_a = res.stderr or ""
                if not meta.get("duration_sec"):
                    m_dur_a = re.search(r'Duration:\s*(\d+:\d+:\d+(?:\.\d+)?)', out_a)
                    if m_dur_a:
                        dur_str_a = m_dur_a.group(1)
                        parts_a = dur_str_a.split(':')
                        if len(parts_a) >= 3:
                            meta["duration"] = f"{int(parts_a[0])*60 + int(parts_a[1]):02d}:{int(float(parts_a[2])):02d}"
                            meta["duration_sec"] = round(int(parts_a[0]) * 3600 + int(parts_a[1]) * 60 + float(parts_a[2]), 3)
                m_aud = re.search(r'Stream\s+#\d+:\d+.*?Audio:\s*([a-zA-Z0-9_-]+).*?,\s*(\d+)\s*Hz', out_a)
                if m_aud:
                    meta["audio_codec"] = m_aud.group(1).upper()
                    hz = int(m_aud.group(2))
                    meta["audio_hz"] = hz
                    meta["audio_hz_str"] = f"{hz/1000.0:.1f} kHz"

                m_ch = re.search(r'Audio:.*?(mono|stereo|[0-9\.]+\s*channels?)', out_a, re.IGNORECASE)
                if m_ch:
                    ch_raw = m_ch.group(1).lower()
                    if "stereo" in ch_raw:
                        meta["audio_channels"] = "Stereo"
                    elif "mono" in ch_raw:
                        meta["audio_channels"] = "Mono"
                    else:
                        meta["audio_channels"] = ch_raw.title()

                if meta["bitrate_str"] == "N/A":
                    m_br_a = re.search(r'bitrate:\s*(\d+)\s*kb/s', out_a)
                    if m_br_a:
                        kbps = int(m_br_a.group(1))
                        meta["bitrate_kbps"] = kbps
                        if kbps >= 1000:
                            meta["bitrate_str"] = f"{kbps/1000.0:.1f} Mb/s"
                        else:
                            meta["bitrate_str"] = f"{kbps} kb/s"
            except Exception as e:
                print(f"[Pyxis Meta Probe Audio Error] {e}", flush=True)

        self._media_metadata_cache[cache_key] = meta
        return meta

    def get_preview_info(self, source="base", target_output_id=None, payload=None):
        """Compiles complete runtime preview parameters, styles, dialogues, and media paths.

        Dispatches between Aegisub live project data (`source="aegisub"`) and standalone
        offline template data (`source="base"`). Injects resolution, aspect ratio, styles,
        dialogues, effective timing bounds, resolved media paths, and probed stream metadata.

        Args:
            source (str, optional): Target source mode ("aegisub" or "base"). Defaults to "base".
            target_output_id (list | str | int | None, optional): Filter criteria for Output nodes.
            payload (dict | None, optional): Graph topology for timeline evaluation.

        Returns:
            dict[str, Any]: Comprehensive preview configuration dictionary consumed by
                ArtPlayer / JASSUB WebAssembly player and backend rendering pipelines.
        """
        has_aegisub = bool(self.temp_ass and os.path.isfile(self.temp_ass))
        if str(source).lower() == "aegisub" and has_aegisub:
            info = self._load_and_cache_aegisub_source(payload=payload, target_output_id=target_output_id)
            if info.get("has_aegisub"):
                info["has_aegisub"] = True
                if "media_meta" not in info:
                    info["media_meta"] = self._probe_media_metadata(
                        video_file=info.get("real_video_file"),
                        audio_file=info.get("real_audio_file"),
                        dummy_info=info.get("dummy_info"),
                        default_fps=info.get("fps", 23.976),
                        res_x=info.get("res_x", 1280),
                        res_y=info.get("res_y", 720)
                    )
                return info

        info = self._load_and_cache_preview_base()
        info["has_aegisub"] = has_aegisub
        info["source"] = "base"
        res_x = info.get("res_x", 1280)
        res_y = info.get("res_y", 720)
        aspect = info.get("aspect_ratio") or ((res_x / res_y) if res_y > 0 else (16 / 9))
        meta = info.get("media_meta") or self._probe_media_metadata(
            video_file=info.get("real_video_file"),
            audio_file=info.get("real_audio_file"),
            dummy_info=info.get("dummy_info"),
            default_fps=info.get("fps", 23.976),
            res_x=res_x,
            res_y=res_y
        )
        dialogues = info.get("dialogues", [])
        min_start_ms = info.get("min_start_ms", 0)
        max_end_ms = info.get("max_end_ms", 15000)
        clip_start_sec = info.get("clip_start_sec", 0.0)
        clip_end_sec = info.get("clip_end_sec", 15.0)
        clip_duration_sec = info.get("clip_duration_sec", 15.0)
        clip_start_ms = info.get("clip_start_ms", 0)

        dur_sec = (meta or {}).get("duration_sec")
        if dur_sec and float(dur_sec) > clip_start_sec:
            clip_end_sec = min(clip_end_sec, float(dur_sec))
            clip_duration_sec = max(0.5, clip_end_sec - clip_start_sec)

        return {
            "source": info.get("source", "base"),
            "has_aegisub": has_aegisub,
            "res_x": res_x,
            "res_y": res_y,
            "aspect_ratio": aspect,
            "fps": info.get("fps", 23.976),
            "frame_dur": info.get("frame_dur", 41.708),
            "min_start_ms": min_start_ms,
            "max_end_ms": max_end_ms,
            "clip_start_sec": clip_start_sec,
            "clip_end_sec": clip_end_sec,
            "clip_duration_sec": clip_duration_sec,
            "clip_start_ms": clip_start_ms,
            "render_start_sec": clip_start_sec,
            "has_custom_video": bool(info.get("real_video_file")),
            "has_custom_audio": bool(info.get("real_audio_file")),
            "has_real_video": bool(info.get("real_video_file")),
            "has_real_audio": bool(info.get("real_audio_file")),
            "audio_file": info.get("real_audio_file"),
            "video_file": info.get("real_video_file"),
            "real_video_file": info.get("real_video_file"),
            "real_audio_file": info.get("real_audio_file"),
            "dummy_info": info.get("dummy_info", {}),
            "font_name": info.get("font_name", "Arial"),
            "font_size": info.get("font_size", 65),
            "clip_path": info.get("clip_path"),
            "path": info.get("path"),
            "styles": info.get("styles", {}),
            "dialogues": dialogues,
            "media_meta": meta
        }

    def _get_temp_dir(self):
        """Resolves and creates the user-level temporary directory for PyxisNodes."""
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        temp_dir = os.path.join(appdata_dir, "PyxisNodes", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def log_player_event(self, msg):
        """Appends a diagnostic player event entry with timestamp to player_debug.log.

        Args:
            msg (str): Informational or diagnostic message from the media player subsystem.

        Returns:
            bool: True if logged successfully, False on I/O error.
        """

    def _extract_font_data_from_gdi(self, font_name: str):
        """Extracts raw binary font data directly from Windows GDI device context memory.

        Invokes native Win32 GDI calls (CreateFontW, SelectObject, GetTextFaceW, and GetFontData)
        to extract the uncompressed font table stream (.ttf, .otf, or .ttc container) without
        requiring file system access or administrative privileges. Discards system fallback fonts
        (such as System or Arial) if they do not match the requested typeface name.

        Args:
            font_name (str): Family or typeface name requested in the ASS style definition.

        Returns:
            tuple[bytes, str] | None: A tuple comprising (font_bytes, selected_face) upon
            successful extraction, or None if extraction fails or resolves to an unwanted fallback.
        """
        if not font_name:
            return None
        try:
            import ctypes
            gdi32 = ctypes.WinDLL("gdi32")
            user32 = ctypes.WinDLL("user32")
            hdc = user32.GetDC(None)
            if not hdc:
                return None
            try:
                hfont = gdi32.CreateFontW(50, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 4, 0, str(font_name))
                if not hfont:
                    return None
                old = gdi32.SelectObject(hdc, hfont)

                face_buf = (ctypes.c_wchar * 256)()
                gdi32.GetTextFaceW(hdc, 256, face_buf)
                selected_face = face_buf.value

                clean_req = str(font_name).lower().replace(" ", "").replace("-", "").replace("_", "")
                clean_sel = str(selected_face).lower().replace(" ", "").replace("-", "").replace("_", "")
                if clean_req not in clean_sel and clean_sel not in clean_req:
                    if clean_sel in ["mssansserif", "system", "arial"] and clean_req != "arial":
                        gdi32.SelectObject(hdc, old)
                        gdi32.DeleteObject(hfont)
                        print(f"[Pyxis Font GDI] GDI selected fallback '{selected_face}' for '{font_name}' (discarded)", flush=True)
                        return None

                size = gdi32.GetFontData(hdc, 0, 0, None, 0)
                if size == 0xFFFFFFFF or size <= 0:
                    gdi32.SelectObject(hdc, old)
                    gdi32.DeleteObject(hfont)
                    return None

                buf = (ctypes.c_char * size)()
                read_b = gdi32.GetFontData(hdc, 0, 0, buf, size)
                gdi32.SelectObject(hdc, old)
                gdi32.DeleteObject(hfont)

                if read_b > 0:
                    font_bytes = bytes(buf[:read_b])
                    print(f"[Pyxis Font GDI] SUCCESS! Extracted {read_b} bytes directly from Windows GDI for '{font_name}' (Face: '{selected_face}')", flush=True)
                    return font_bytes, selected_face
            finally:
                user32.ReleaseDC(None, hdc)
        except Exception as e:
            print(f"[Pyxis Font GDI Error] {e}", flush=True)
        return None

    def _find_font_file(self, font_name: str):
        """Locates the physical font file path on the host system or extracts it into cache.

        Executes a multi-tier resolution strategy:
        1. Direct Windows GDI binary extraction cached into `%APPDATA%/PyxisNodes/fonts/`.
        2. Windows Registry scan across HKCU and HKLM font registries.
        3. Directory scanning across system Fonts, LocalAppData, FontBase, and application dirs.
        4. Direct filename matching and fuzzy case-insensitive directory listing.
        5. Ultimate fallback to standard Arial font if resolution fails.

        Args:
            font_name (str): The font family name to discover on the host machine.

        Returns:
            str | None: Absolute path to the resolved .ttf/.otf/.ttc file, or None if unavailable.
        """
        if not font_name:
            print("[Pyxis Font] _find_font_file called with empty name", flush=True)
            return None
        
        font_name_clean = str(font_name).strip().lower()
        print(f"[Pyxis Font] Searching system for font file: '{font_name}' (limpio: '{font_name_clean}')", flush=True)

        gdi_res = self._extract_font_data_from_gdi(font_name)
        if gdi_res:
            raw_bytes, actual_face = gdi_res
            ext = ".otf" if raw_bytes[:4] == b"OTTO" else ".ttf"
            appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            cache_dir = os.path.join(appdata_dir, "PyxisNodes", "fonts")
            os.makedirs(cache_dir, exist_ok=True)
            cached_file = os.path.join(cache_dir, f"{font_name}{ext}")
            try:
                with open(cached_file, "wb") as f:
                    f.write(raw_bytes)
                print(f"[Pyxis Font] GDI font cached: '{cached_file}'", flush=True)
                return cached_file
            except Exception as e:
                print(f"[Pyxis Font Cache Error] {e}", flush=True)

        candidates_from_reg = []
        
        try:
            import winreg
            for root_name, root in [("HKCU", winreg.HKEY_CURRENT_USER), ("HKLM", winreg.HKEY_LOCAL_MACHINE)]:
                try:
                    key = winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
                    for i in range(winreg.QueryInfoKey(key)[1]):
                        reg_name, reg_val, _ = winreg.EnumValue(key, i)
                        clean_reg = reg_name.split('(')[0].strip().lower()
                        if clean_reg == font_name_clean:
                            candidates_from_reg.insert(0, reg_val)
                            print(f"[Pyxis Font] EXACT match in {root_name} Fonts: '{reg_name}' -> '{reg_val}'", flush=True)
                        elif font_name_clean in clean_reg:
                            candidates_from_reg.append(reg_val)
                            print(f"[Pyxis Font] Partial match in {root_name} Fonts: '{reg_name}' -> '{reg_val}'", flush=True)
                    winreg.CloseKey(key)
                except Exception as e:
                    print(f"[Pyxis Font] Error reading registry {root_name}: {e}", flush=True)
        except Exception as e:
            print(f"[Pyxis Font] General exception scanning registry: {e}", flush=True)

        search_dirs = [
            os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Windows\Fonts"),
            os.path.join(os.environ.get("APPDATA", ""), r"PyxisNodes\fonts"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"),
            r"E:\Fuentes\FontBase",
            r"E:\Fuentes",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "FontBase"),
            os.path.join(os.environ.get("APPDATA", ""), "FontBase"),
        ]
        print(f"[Pyxis Font] Font search directories: {search_dirs}", flush=True)

        for val in candidates_from_reg:
            if os.path.isabs(val) and os.path.exists(val):
                print(f"[Pyxis Font] FOUND via registry (absolute path)! '{font_name}' -> '{val}'", flush=True)
                return val
            for s_dir in search_dirs:
                if s_dir and os.path.isdir(s_dir):
                    p = os.path.join(s_dir, val)
                    if os.path.exists(p):
                        print(f"[Pyxis Font] FOUND via registry in folder! '{font_name}' -> '{p}'", flush=True)
                        return p

        clean_nosp = font_name_clean.replace(" ", "")
        direct_names = [
            f"{font_name}.ttf", f"{font_name}.otf", f"{font_name}.ttc",
            f"{font_name_clean}.ttf", f"{font_name_clean}.otf", f"{font_name_clean}.ttc",
            f"{clean_nosp}.ttf", f"{clean_nosp}.otf"
        ]
        for s_dir in search_dirs:
            if s_dir and os.path.isdir(s_dir):
                for dn in direct_names:
                    p = os.path.join(s_dir, dn)
                    if os.path.exists(p):
                        print(f"[Pyxis Font] ¡FOUND by direct name! '{font_name}' -> '{p}'", flush=True)
                        return p
                try:
                    for fn in os.listdir(s_dir):
                        fn_lower = fn.lower()
                        if clean_nosp in fn_lower and any(fn_lower.endswith(ext) for ext in ['.ttf', '.otf', '.ttc']):
                            p = os.path.join(s_dir, fn)
                            print(f"[Pyxis Font] ¡FOUND by fuzzy file search! '{font_name}' -> '{p}'", flush=True)
                            return p
                except Exception as e:
                    print(f"[Pyxis Font] Error listing directory {s_dir}: {e}", flush=True)

        print(f"[Pyxis Font] WARNING: No specific file found for '{font_name}'. Falling back to Arial...", flush=True)
        for s_dir in search_dirs:
            if s_dir and os.path.isdir(s_dir):
                for af in ["arial.ttf", "Arial.ttf", "ARIAL.TTF"]:
                    p = os.path.join(s_dir, af)
                    if os.path.exists(p):
                        print(f"[Pyxis Font] Fallback a Arial resuelto en: '{p}'", flush=True)
                        return p
        print(f"[Pyxis Font] ERROR: Arial not found in {search_dirs}", flush=True)
        return None

    def get_preview_fonts_map(self, source="base"):
        """Compiles a comprehensive dictionary of all font assets required by preview subtitles.

        Inspects the ASS style definitions and active lines for the chosen source, locates the
        corresponding binary font files, and packages them with base64 Data URLs, local HTTP URLs,
        and absolute file paths for consumption by the WebAssembly (JASSUB/ArtPlayer) canvas.

        Args:
            source (str): Source context identifier ('base' for preview_base.ass or 'aegisub').

        Returns:
            dict[str, dict[str, str]]: Dictionary mapping font family names (including lowercase
            and whitespace-stripped keys) to metadata dictionaries containing 'data' (Data URL),
            'http_url', 'path', and 'mime'.
        """
        font_map = {}
        try:
            info = self.get_preview_info(source=source)
            styles = info.get("styles", {}) or {}
            print(f"[Pyxis Font] get_preview_fonts_map invoked for source '{source}'. Available ASS styles: {list(styles.keys())}", flush=True)
            requested_fonts = set()
            for s_name, s in styles.items():
                if isinstance(s, dict):
                    fn = s.get("Fontname") or s.get("fontname")
                    print(f"[Pyxis Font] Style '{s_name}' uses font: '{fn}'", flush=True)
                    if fn:
                        requested_fonts.add(str(fn).strip())
            
            primary_fn = str(info.get("font_name") or "Arial").strip()
            print(f"[Pyxis Font] Primary font detected from active line: '{primary_fn}'", flush=True)
            if primary_fn:
                requested_fonts.add(primary_fn)
            if not requested_fonts:
                requested_fonts.add("Arial")

            print(f"[Pyxis Font] Total requested fonts to resolve: {requested_fonts}", flush=True)
            import base64
            from urllib.parse import quote
            for fn in requested_fonts:
                f_path = self._find_font_file(fn)
                if f_path and os.path.exists(f_path):
                    mime = "font/otf" if f_path.lower().endswith(".otf") else "font/ttf"
                    try:
                        file_size = os.path.getsize(f_path)
                        with open(f_path, "rb") as f:
                            encoded = base64.b64encode(f.read()).decode("utf-8")
                        d_url = f"data:{mime};base64,{encoded}"
                        quoted_path = quote(os.path.abspath(f_path))
                        http_url = f"http://127.0.0.1:28723/media_file?path={quoted_path}"
                        entry = {
                            "data": d_url,
                            "http_url": http_url,
                            "path": f_path,
                            "mime": mime
                        }
                        font_map[fn.lower()] = entry
                        font_map[fn] = entry
                        font_map[fn.lower().replace(" ", "")] = entry
                        print(f"[Pyxis Font] Fuente '{fn}' empaquetada exitosamente: {file_size} bytes, ruta='{f_path}'", flush=True)
                    except Exception as e:
                        print(f"[Pyxis Error reading font file {f_path}] {e}", flush=True)
                else:
                    print(f"[Pyxis Font] ERROR: Could not resolve physical file for '{fn}'", flush=True)
        except Exception as e:
            print(f"[Pyxis Error getting preview fonts map] {e}", flush=True)
        print(f"[Pyxis Font] Final font map generated with {len(font_map)} keys.", flush=True)
        return font_map

    def get_preview_font_data_url(self, source="base"):
        """Generates a base64 Data URL for the primary font family of the current preview session.

        Resolves the physical font file for the active dialogue style and encodes its binary
        payload into a data URI scheme suitable for inline CSS `@font-face` injection.

        Args:
            source (str): Media source mode ('base' or 'aegisub').

        Returns:
            str: Base64-encoded Data URL ('data:font/ttf;base64,...'), or an empty string on error.
        """
        try:
            info = self.get_preview_info(source=source)
            requested_font = str(info.get("font_name") or "Arial").strip()
            target_font_path = self._find_font_file(requested_font)
            if target_font_path and os.path.exists(target_font_path):
                import base64
                mime = "font/otf" if target_font_path.lower().endswith(".otf") else "font/ttf"
                with open(target_font_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                return f"data:{mime};base64,{encoded}"
        except Exception as e:
            print(f"[Pyxis Error getting font data URL] {e}", flush=True)
        return ""

    def invalidate_preview_base_cache(self):
        """Invalidates in-memory caches and telemetry buffers for the base preview subtitle file.

        Clears cached parsed structures, SHA-256 content hashes, previous ASS payloads, and resets
        the global libass telemetry manager cache to force a re-evaluation on next access.
        """
        self._cached_preview_base_info = None
        self._preview_base_hash = None
        self._last_preview_ass_content = None
        self._last_preview_ass_info = None
        try:
            from ass_telemetry_engine import GLOBAL_TELEMETRY_MANAGER
            GLOBAL_TELEMETRY_MANAGER.clear_last_result()
        except Exception:
            pass

    def ensure_preview_base_ass(self):
        """Ensures the existence of preview_base.ass in the user application data directory.

        Verifies `%APPDATA%/PyxisNodes/preview_base.ass`. If absent, copies the distribution master
        template from the application repository while preserving existing user customisations.

        Returns:
            str | None: Absolute path to the user preview_base.ass file, or None on failure.
        """
        try:
            appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            pyxis_user_dir = os.path.join(appdata_dir, "PyxisNodes")
            os.makedirs(pyxis_user_dir, exist_ok=True)
            user_base_path = os.path.join(pyxis_user_dir, "preview_base.ass")
            try:
                from paths import PREVIEW_BASE_ASS
                master_path = PREVIEW_BASE_ASS
            except Exception:
                master_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "preview_base.ass")
                if not os.path.exists(master_path):
                    master_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview_base.ass")

            if os.path.exists(user_base_path):
                return user_base_path
            elif os.path.exists(master_path):
                import shutil
                shutil.copyfile(master_path, user_base_path)
                print(f"[Pyxis] Initial copy created for preview_base.ass master -> {user_base_path}", flush=True)
                return user_base_path
        except Exception as e:
            print(f"[Pyxis Error in ensure_preview_base_ass] {e}", flush=True)
        return None

    @staticmethod
    def _parse_ass_time(t_str: str) -> int:
        """Parses an Advanced SubStation Alpha timestamp into total elapsed milliseconds.

        Converts the standard ASS time format (H:MM:SS.CS or H:MM:SS.MS) into an absolute
        integer millisecond offset.

        Args:
            t_str (str): ASS timestamp string representation (e.g. '0:01:23.45').

        Returns:
            int: Total time in milliseconds, or 0 if malformed or empty.
        """
        if not t_str:
            return 0
        try:
            parts = str(t_str).strip().split(":")
            if len(parts) == 3:
                h = int(parts[0])
                m = int(parts[1])
                sec_parts = parts[2].split(".")
                s = int(sec_parts[0])
                cs = int(sec_parts[1]) if len(sec_parts) > 1 else 0
                ms = cs * 10 if len(sec_parts[1]) == 2 else int(sec_parts[1])
                return (h * 3600 + m * 60 + s) * 1000 + ms
        except Exception:
            pass
        return 0

    def _load_and_cache_preview_base(self, force_reload=False):
        """Parses preview_base.ass and caches structural metadata with SHA-256 validation.

        Computes a SHA-256 digest of the physical file to avoid redundant parsing. Extracts ASS
        header resolutions (PlayResX, PlayResY), styles, dialogues, timing spans, referenced
        media paths, dummy clip specifications, and media stream metadata via FFprobe.

        Args:
            force_reload (bool): If True, bypasses cache comparisons and forces full re-parsing.

        Returns:
            dict[str, Any]: Comprehensive metadata dictionary describing preview base parameters,
            effective clip intervals, dummy video parameters, and media stream properties.
        """
        try:
            user_base_path = self.ensure_preview_base_ass()
            if not user_base_path or not os.path.exists(user_base_path):
                return {"source": "base", "path": None, "res_x": 1280, "res_y": 720, "has_aegisub": False}

            import hashlib
            with open(user_base_path, "rb") as fp:
                current_hash = hashlib.sha256(fp.read()).hexdigest()

            cached = getattr(self, '_cached_preview_base_info', None)
            cached_hash = getattr(self, '_preview_base_hash', None)

            if (not force_reload) and cached and cached_hash == current_hash:
                return cached

            self._preview_base_hash = current_hash
            from ass_parser import ASSParser
            parsed = ASSParser.read_file(user_base_path)
            if not parsed:
                return {"source": "base", "path": user_base_path, "res_x": 1280, "res_y": 720, "has_aegisub": False}

            styles, dialogues, res_x, res_y, frame_dur = parsed.styles, parsed.dialogues, parsed.res_x, parsed.res_y, parsed.frame_dur

            video_file = getattr(parsed, 'video_file', '')
            audio_file = getattr(parsed, 'audio_file', '')
            is_dummy_video = getattr(parsed, 'is_dummy_video', False)
            is_dummy_audio = getattr(parsed, 'is_dummy_audio', False)
            dummy_info = getattr(parsed, 'dummy_info', {}) or {}
            fps = dummy_info.get("fps") or (1000.0 / frame_dur if frame_dur > 0 else 23.976)

            real_video = None
            if not is_dummy_video:
                real_video = self._clean_and_resolve_media_path(video_file, user_base_path)

            real_audio = None
            if not is_dummy_audio:
                real_audio = self._clean_and_resolve_media_path(audio_file, user_base_path)

            if not real_audio and real_video:
                real_audio = real_video

            min_start_ms = 0
            max_end_ms = 15000
            if dialogues:
                starts = []
                ends = []
                for d in dialogues:
                    if isinstance(d, dict):
                        if 'start_time' in d and 'end_time' in d:
                            starts.append(d['start_time'])
                            ends.append(d['end_time'])
                        elif 'raw' in d:
                            raw = str(d['raw'])
                            if raw.startswith('Dialogue:') or raw.startswith('Dialogue :'):
                                fields = raw.split(',', 9)
                                if len(fields) >= 3:
                                    starts.append(self._parse_ass_time(fields[1]))
                                    ends.append(self._parse_ass_time(fields[2]))
                    elif hasattr(d, 'start_time') and hasattr(d, 'end_time'):
                        starts.append(d.start_time)
                        ends.append(d.end_time)
                if starts and ends:
                    min_start_ms = min(starts)
                    max_end_ms = max(ends)

            clip_start_sec = max(0.0, (min_start_ms - 2000) / 1000.0)
            clip_end_sec = (max_end_ms + 2000) / 1000.0
            clip_duration_sec = max(2.0, clip_end_sec - clip_start_sec)
            clip_start_ms = int(clip_start_sec * 1000)

            primary_font_name = "Arial"
            primary_font_size = 65
            if styles:
                first_style = next(iter(styles.values()))
                if isinstance(first_style, dict):
                    primary_font_name = first_style.get("Fontname", "Arial")
                    try:
                        primary_font_size = int(first_style.get("Fontsize", 65))
                    except Exception:
                        pass

            info_dict = {
                "source": "base",
                "path": user_base_path,
                "res_x": res_x,
                "res_y": res_y,
                "aspect_ratio": (res_x / res_y) if res_y > 0 else (16 / 9),
                "fps": fps,
                "frame_dur": frame_dur,
                "styles": styles,
                "dialogues": dialogues,
                "min_start_ms": min_start_ms,
                "max_end_ms": max_end_ms,
                "clip_start_sec": clip_start_sec,
                "clip_end_sec": clip_end_sec,
                "clip_duration_sec": clip_duration_sec,
                "clip_start_ms": clip_start_ms,
                "render_start_sec": clip_start_sec,
                "render_duration_sec": clip_duration_sec,
                "audio_file": real_audio,
                "video_file": real_video,
                "real_video_file": real_video,
                "real_audio_file": real_audio,
                "has_real_video": bool(real_video and os.path.isfile(real_video)),
                "has_real_audio": bool(real_audio and os.path.isfile(real_audio)),
                "dummy_info": dummy_info,
                "font_name": primary_font_name,
                "font_size": primary_font_size,
            }

            info_dict["clip_path"] = real_video or real_audio or None

            info_dict["media_meta"] = self._probe_media_metadata(
                video_file=real_video,
                audio_file=real_audio,
                dummy_info=dummy_info if is_dummy_video else None,
                default_fps=fps,
                res_x=res_x,
                res_y=res_y
            )
            dur_sec = (info_dict.get("media_meta") or {}).get("duration_sec")
            if dur_sec and float(dur_sec) > info_dict["clip_start_sec"]:
                info_dict["clip_end_sec"] = min(info_dict["clip_end_sec"], float(dur_sec))
                info_dict["clip_duration_sec"] = max(0.5, info_dict["clip_end_sec"] - info_dict["clip_start_sec"])
                info_dict["render_duration_sec"] = info_dict["clip_duration_sec"]

            self._cached_preview_base_info = info_dict
            print(f"[Pyxis Scan] preview_base.ass loaded: Res={res_x}x{res_y} ({res_x/res_y:.3f}), Dialogues={len(dialogues)}, Clip={info_dict['clip_start_sec']:.2f}s to {info_dict['clip_end_sec']:.2f}s ({info_dict['clip_duration_sec']:.2f}s)", flush=True)
            return self._cached_preview_base_info
        except Exception as e:
            print(f"[Pyxis Error in _load_and_cache_preview_base] {e}", flush=True)

        self._cached_preview_base_info = {
            "path": None,
            "res_x": 1280,
            "res_y": 720,
            "aspect_ratio": 1280 / 720,
            "fps": 23.976,
            "frame_dur": 41.708,
            "styles": {},
            "dialogues": [],
            "min_start_ms": 0,
            "max_end_ms": 15000,
            "clip_start_sec": 0.0,
            "clip_end_sec": 15.0,
            "clip_duration_sec": 15.0,
            "clip_start_ms": 0,
            "render_start_sec": 0.0,
            "render_duration_sec": 15.0,
            "audio_file": None,
            "video_file": None,
            "real_video_file": None,
            "real_audio_file": None,
            "dummy_info": {},
            "font_name": "Arial",
            "font_size": 65,
            "clip_path": None
        }
        return self._cached_preview_base_info

    def get_initial_base_ass(self, source="base", target_output_id=None, payload=None):
        """Retrieves and prepares the raw initial ASS script text for player initialisation.

        Reads the active subtitle source file, synchronises PlayResX and PlayResY declarations with
        effective canvas dimensions, filters out extraneous sections, and returns the normalised
        ASS script content.

        Args:
            source (str): Source subtitle selector ('base' or 'aegisub').
            target_output_id (str | None): Specific Output node identifier in the active graph.
            payload (dict | None): Graph serialisation payload for dialogue node resolution.

        Returns:
            str: Normalised ASS script content as a plain text string.
        """
        try:
            info = self.get_preview_info(source=source, target_output_id=target_output_id, payload=payload)
            ass_path = info.get("path") or (self.ensure_preview_base_ass() if source == "base" else None)
            clip_start_ms = info.get("clip_start_ms", 0)
            if ass_path and os.path.exists(ass_path):
                rx, ry = info.get("res_x", 1280), info.get("res_y", 720)
                with open(ass_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                    lines = f.readlines()
                output = []
                in_events = False
                for line in lines:
                    line_clean = line.lstrip('\ufeff')
                    if line_clean.startswith("PlayResX:"):
                        output.append(f"PlayResX: {rx}\n")
                    elif line_clean.startswith("PlayResY:"):
                        output.append(f"PlayResY: {ry}\n")
                    elif line_clean.strip().startswith("[Events]"):
                        in_events = True
                        output.append(line)
                    elif in_events and (line_clean.startswith("Dialogue:") or line_clean.startswith("Comment:")):
                        output.append(line)
                    else:
                        output.append(line)
                return "".join(output)
        except Exception as e:
            print(f"[Pyxis Error reading initial ASS source={source}] {e}", flush=True)
        return ""

    def generate_preview_ass(self, payload, target_output_id=None, out_filename="preview_dummy.ass", preview_res_x=None, preview_res_y=None, source="base", for_hardsub=False):
        """Generates an Advanced SubStation Alpha preview script from the current node graph.

        Executes the graph pipeline targeting specified Output nodes, synchronises subtitle
        events with the video clip time span, comments out replaced dialogue lines based on style
        or selection criteria, and shifts timestamps if exporting for hardsub rendering.

        Args:
            payload (dict | str): Serialised graph topology payload from LiteGraph.
            target_output_id (str | list[str] | None): Specific Output node ID(s) to render.
            out_filename (str): Base file name for telemetry and diagnostic logging.
            preview_res_x (int | None): Custom horizontal canvas resolution override.
            preview_res_y (int | None): Custom vertical canvas resolution override.
            source (str): Subtitle source identifier ('base' or 'aegisub').
            for_hardsub (bool): If True, shifts timestamps to align with clipped media origin.

        Returns:
            dict[str, Any]: Execution result payload containing 'success', 'content' (ASS script),
            and time boundaries ('clip_start_sec', 'clip_end_sec', 'clip_duration_sec', etc.).
        """
        try:
            info = self.get_preview_info(source=source, target_output_id=target_output_id, payload=payload)
            res_x = preview_res_x if preview_res_x is not None else info.get("res_x", 1280)
            res_y = preview_res_y if preview_res_y is not None else info.get("res_y", 720)
            styles = info.get("styles", {})
            dialogues = info.get("dialogues", [])
            frame_dur = info.get("frame_dur", 41.708)
            clip_start_sec = info.get("clip_start_sec", 0.0)
            clip_end_sec = info.get("clip_end_sec", 15.0)
            clip_duration_sec = info.get("clip_duration_sec", 15.0)
            clip_start_ms = info.get("clip_start_ms", 0)
            shift_amount = clip_start_ms if for_hardsub else 0
            ass_path = info.get("path") or (self.ensure_preview_base_ass() if source == "base" else None)

            self.log_player_event(f"generate_preview_ass source={source} called with target_output_id: {target_output_id}, res: {res_x}x{res_y}, shift_ms: {shift_amount}")
            graph_data = self._normalize_graph(payload)
            from node_engine import GraphEngine

            output_id_list = []
            if isinstance(target_output_id, list):
                for x in target_output_id:
                    if x is not None:
                        s_val = str(x).strip()
                        if s_val and s_val not in output_id_list:
                            output_id_list.append(s_val)
            elif target_output_id is not None:
                s_val = str(target_output_id).strip()
                if s_val:
                    output_id_list.append(s_val)

            self.log_player_event(f"output_id_list targets: {output_id_list}")

            default_audio = info.get("real_audio_file") or info.get("real_video_file") or info.get("audio_file") or ""
            
            base_lines = []
            if ass_path and os.path.exists(ass_path):
                with open(ass_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                    base_lines = f.readlines()
            elif dialogues or styles:
                base_lines.append("[Script Info]\n")
                base_lines.append(f"PlayResX: {res_x}\n")
                base_lines.append(f"PlayResY: {res_y}\n")
                base_lines.append("ScriptType: v4.00+\n\n")
                base_lines.append("[V4+ Styles]\n")
                base_lines.append("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                if styles:
                    for s_name, s_data in styles.items():
                        if isinstance(s_data, dict):
                            fn = s_data.get("Fontname", "Arial")
                            fs = s_data.get("Fontsize", 40)
                            c1 = s_data.get("PrimaryColour", "&H00FFFFFF&")
                            c2 = s_data.get("SecondaryColour", "&H000000FF&")
                            c3 = s_data.get("OutlineColour", "&H00000000&")
                            c4 = s_data.get("BackColour", "&H00000000&")
                            b = -1 if s_data.get("Bold") else 0
                            it = -1 if s_data.get("Italic") else 0
                            u = -1 if s_data.get("Underline") else 0
                            so = -1 if s_data.get("StrikeOut") else 0
                            sx = s_data.get("ScaleX", 100)
                            sy = s_data.get("ScaleY", 100)
                            sp = s_data.get("Spacing", 0)
                            ang = s_data.get("Angle", 0)
                            bs = s_data.get("BorderStyle", 1)
                            out = s_data.get("Outline", 2)
                            sh = s_data.get("Shadow", 0)
                            al = s_data.get("Alignment", 2)
                            ml = s_data.get("MarginL", 10)
                            mr = s_data.get("MarginR", 10)
                            mv = s_data.get("MarginV", 10)
                            enc = s_data.get("Encoding", 1)
                            base_lines.append(f"Style: {s_name},{fn},{fs},{c1},{c2},{c3},{c4},{b},{it},{u},{so},{sx},{sy},{sp},{ang},{bs},{out},{sh},{al},{ml},{mr},{mv},{enc}\n")
                        elif isinstance(s_data, str):
                            base_lines.append(s_data.strip() + "\n")
                else:
                    base_lines.append("Style: Default,Arial,40,&H00FFFFFF&,&H000000FF&,&H00000000&,&H00000000&,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n")
                base_lines.append("\n[Events]\n")
                base_lines.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                for d in dialogues:
                    if isinstance(d, dict) and 'raw' in d:
                        base_lines.append(str(d['raw']).strip() + "\n")
                    elif isinstance(d, str):
                        base_lines.append(d.strip() + "\n")

            self._preview_cancelled = False
            if len(base_lines) > 0:
                generated_lines = []
                if len(output_id_list) > 0:
                    engine = GraphEngine(graph_data, res_x, res_y, frame_dur, default_audio_source=default_audio)
                    engine.target_output_id = output_id_list
                    self._active_preview_engine = engine

                    def report_preview_progress(data):
                        try:
                            if webview.windows:
                                if isinstance(data, dict):
                                    import json
                                    js_str = json.dumps(data)
                                    webview.windows[0].evaluate_js(
                                        f"if (typeof window.__pyxis_on_preview_progress === 'function') window.__pyxis_on_preview_progress({js_str});"
                                    )
                                else:
                                    pct_val = int(float(data))
                                    webview.windows[0].evaluate_js(
                                        f"if (typeof window.__pyxis_on_preview_progress === 'function') window.__pyxis_on_preview_progress({pct_val});"
                                    )
                        except Exception:
                            pass

                    generated_lines = engine.process(
                        dialogues,
                        styles,
                        progress_callback=report_preview_progress,
                        check_cancel_callback=lambda: getattr(self, '_preview_cancelled', False) or getattr(engine, 'is_cancelled', False)
                    )
                    self.log_player_event(f"GraphEngine targets={output_id_list} (Res {res_x}x{res_y}) produced {len(generated_lines)} lines")

                    if getattr(self, '_preview_cancelled', False) or getattr(engine, 'is_cancelled', False):
                        self.log_player_event("generate_preview_ass aborted due to user cancellation.")
                        self._active_preview_engine = None
                        return {"success": False, "cancelled": True}

                output_ass_lines = []
                in_events = False
                last_was_selected_metric = False
                has_any_selection = any(
                    bool((isinstance(d, dict) and (d.get('is_selected') or (isinstance(d.get('metrics'), dict) and d['metrics'].get('sel')))))
                    for d in dialogues
                )
                nodes_dict = graph_data.get("nodes", {}) or {}
                if isinstance(nodes_dict, list):
                    nodes_dict = {n.get("id"): n for n in nodes_dict if isinstance(n, dict)}
                
                all_output_nodes = [n for n in nodes_dict.values() if 'output' in str(n.get('type', '')).lower()]
                matching_outputs = [n for n in all_output_nodes if self._matches_output_node(n, output_id_list, all_output_nodes)]
                
                use_all_lines = False
                use_style_lines = False
                target_styles = set()
                for s_node in matching_outputs:
                    props = s_node.get('properties', {}) or {}
                    app = str(props.get('apply_to', 'Selected Lines')).strip().lower()
                    if app in ['all lines', 'all']:
                        use_all_lines = True
                        break
                    elif app in ['style lines', 'style']:
                        use_style_lines = True
                        st_name = str(props.get('style', '')).strip()
                        if st_name:
                            target_styles.add(st_name)

                if use_style_lines:
                    for d in dialogues:
                        is_sel = False
                        st_name = ""
                        if isinstance(d, dict):
                            raw = str(d.get('raw', ''))
                            if raw.strip().startswith('Comment:') or raw.strip().startswith('Comment :'):
                                continue
                            is_sel = bool(d.get('is_selected', False) or (d.get('metrics') and d['metrics'].get('sel')))
                            st_name = str(d.get('style_name', ''))
                            if not st_name and raw:
                                fields = raw.split(',', 9)
                                if len(fields) >= 4:
                                    st_name = fields[3].strip()
                        elif hasattr(d, 'is_selected') and hasattr(d, 'style_name'):
                            if getattr(d, 'is_comment', False):
                                continue
                            is_sel = getattr(d, 'is_selected', False)
                            st_name = getattr(d, 'style_name', '')
                        if is_sel and st_name:
                            target_styles.add(st_name)

                    if not target_styles:
                        for d in dialogues:
                            st_name = ""
                            if isinstance(d, dict):
                                raw = str(d.get('raw', ''))
                                if raw.strip().startswith('Comment:') or raw.strip().startswith('Comment :'):
                                    continue
                                st_name = str(d.get('style_name', ''))
                                if not st_name and raw:
                                    fields = raw.split(',', 9)
                                    if len(fields) >= 4:
                                        st_name = fields[3].strip()
                            elif hasattr(d, 'style_name'):
                                if getattr(d, 'is_comment', False):
                                    continue
                                st_name = getattr(d, 'style_name', '')
                            if st_name:
                                target_styles.add(st_name)

                for line in base_lines:
                    line_clean = line.lstrip('\ufeff')
                    if line_clean.startswith("PlayResX:"):
                        output_ass_lines.append(f"PlayResX: {res_x}\n")
                        continue
                    elif line_clean.startswith("PlayResY:"):
                        output_ass_lines.append(f"PlayResY: {res_y}\n")
                        continue
                    if line_clean.strip().startswith("[Events]"):
                        in_events = True
                        output_ass_lines.append(line)
                        continue
                    if not in_events:
                        output_ass_lines.append(line)
                    else:
                        is_comm = line_clean.strip().startswith("Comment:")
                        is_diag = line_clean.strip().startswith("Dialogue:")
                        if is_comm and "PyxisMetrics" in line_clean:
                            last_was_selected_metric = ("sel=1" in line_clean)
                            output_ass_lines.append(self._shift_ass_line(line, shift_amount))
                        elif is_diag:
                            fields = line_clean.split(',', 9)
                            style_name = fields[3].strip() if len(fields) >= 4 else ""
                            should_comment = (
                                (source == "base") or 
                                use_all_lines or 
                                (use_style_lines and style_name in target_styles) or
                                (last_was_selected_metric and not use_style_lines) or 
                                (not has_any_selection)
                            )
                            if should_comment and len(output_id_list) > 0 and len(generated_lines) > 0:
                                comment_line = "Comment: " + line_clean[9:]
                                output_ass_lines.append(self._shift_ass_line(comment_line, shift_amount))
                            else:
                                output_ass_lines.append(self._shift_ass_line(line, shift_amount))
                            last_was_selected_metric = False
                        elif is_comm:
                            output_ass_lines.append(self._shift_ass_line(line, shift_amount))
                        else:
                            output_ass_lines.append(line)

                if len(generated_lines) > 0:
                    for g_line in generated_lines:
                        output_ass_lines.append(self._shift_ass_line(g_line, shift_amount))

                full_ass_content = "".join(output_ass_lines)
            else:
                self.log_player_event("ass_path missing and no in-memory dialogues/styles!")
                full_ass_content = ""

            clip_end_ms = int(round(clip_end_sec * 1000)) if clip_end_sec > 0 else (clip_start_ms + int(round(clip_duration_sec * 1000)))
            if not for_hardsub and full_ass_content:
                self._last_preview_ass_content = full_ass_content
                self._last_preview_ass_info = {
                    "res_x": res_x,
                    "res_y": res_y,
                    "fps": info.get("fps", 23.976),
                    "frame_dur": frame_dur,
                    "clip_start_ms": clip_start_ms,
                    "clip_end_ms": clip_end_ms,
                    "clip_start_sec": clip_start_sec,
                    "clip_end_sec": clip_end_sec,
                    "clip_duration_sec": clip_duration_sec,
                    "source": source,
                    "target_output_id": output_id_list,
                }

            self.log_player_event(f"generate_preview_ass finished, total ASS length: {len(full_ass_content)}, window: {clip_start_sec:.2f}s..{clip_end_sec:.2f}s")
            return {
                "success": True,
                "content": full_ass_content,
                "clip_start_sec": clip_start_sec,
                "clip_end_sec": clip_end_sec,
                "clip_duration_sec": clip_duration_sec,
                "clip_start_ms": clip_start_ms,
                "clip_end_ms": clip_end_ms,
            }
        except Exception as err:
            self.log_player_event(f"[Pyxis Error in generate_preview_ass] {err}")
            return {"success": False, "error": str(err)}
        finally:
            self._active_preview_engine = None

    def run_ass_telemetry(self, payload=None, target_output_id=None, source="base", force_regenerate=False, clip_start_ms=None, clip_end_ms=None):
        """Executes multi-worker libass profiler telemetry on the active preview subtitle script.

        Analyses rasterisation cost, glyph rendering complexity, line budget consumption, and
        frame-by-frame execution spikes using the native libass_profiler background engine.

        Args:
            payload (dict | None): Graph payload for on-demand regeneration if ASS is uncached.
            target_output_id (str | list[str] | None): Target Output node identifiers.
            source (str): Source context identifier ('base' or 'aegisub').
            force_regenerate (bool): If True, forces fresh generation of the preview ASS script.
            clip_start_ms (int | None): Optional start boundary in milliseconds.
            clip_end_ms (int | None): Optional end boundary in milliseconds.

        Returns:
            dict[str, Any]: Telemetry metrics payload detailing execution duration, frame spikes,
            peak lines, memory usage, and budget thresholds.
        """
        try:
            from ass_telemetry_engine import GLOBAL_TELEMETRY_MANAGER

            ass_content = getattr(self, "_last_preview_ass_content", None)
            cached_info = getattr(self, "_last_preview_ass_info", None) or {}
            if cached_info.get("source") and str(cached_info.get("source")).lower() != str(source).lower():
                ass_content = None

            if force_regenerate or not ass_content:
                effective_outputs = target_output_id
                if effective_outputs is None and payload is not None:
                    graph_data = self._normalize_graph(payload)
                    nodes_dict = graph_data.get("nodes", {}) if isinstance(graph_data, dict) else {}
                    if isinstance(nodes_dict, list):
                        nodes_dict = {n.get("id"): n for n in nodes_dict if isinstance(n, dict)}
                    all_output_nodes = [
                        n for n in nodes_dict.values()
                        if "output" in str(n.get("type", "")).lower()
                    ]
                    effective_outputs = [str(n.get("id")) for n in all_output_nodes if n.get("id") is not None]

                gen_res = self.generate_preview_ass(
                    payload=payload or {},
                    target_output_id=effective_outputs,
                    out_filename="telemetry_preview.ass",
                    source=source,
                    for_hardsub=False,
                )
                if isinstance(gen_res, dict) and gen_res.get("success") and gen_res.get("content"):
                    ass_content = gen_res["content"]
                    cached_info = getattr(self, "_last_preview_ass_info", None) or {}

            if not ass_content:
                ass_content = self.get_initial_base_ass(source=source, target_output_id=target_output_id, payload=payload)
                info = self.get_preview_info(source=source, target_output_id=target_output_id, payload=payload)
                c_start_ms = info.get("clip_start_ms", 0)
                clip_end_sec = info.get("clip_end_sec", 0.0)
                clip_dur_sec = info.get("clip_duration_sec", 0.0)
                c_end_ms = int(round(clip_end_sec * 1000)) if clip_end_sec > 0 else (c_start_ms + int(round(clip_dur_sec * 1000)))
                cached_info = {
                    "res_x": info.get("res_x", 1280),
                    "res_y": info.get("res_y", 720),
                    "fps": info.get("fps", 23.976),
                    "frame_dur": info.get("frame_dur", 41.708),
                    "clip_start_ms": c_start_ms,
                    "clip_end_ms": c_end_ms,
                }

            if not ass_content:
                return {"success": False, "error": "No ASS subtitle content available for telemetry."}

            res_x = cached_info.get("res_x", 1280)
            res_y = cached_info.get("res_y", 720)
            fps = cached_info.get("fps", 23.976)
            eff_start_ms = int(clip_start_ms) if clip_start_ms is not None else cached_info.get("clip_start_ms", 0)
            eff_end_ms = int(clip_end_ms) if clip_end_ms is not None else cached_info.get("clip_end_ms", 0)

            return GLOBAL_TELEMETRY_MANAGER.run_telemetry(
                ass_content=ass_content,
                res_x=res_x,
                res_y=res_y,
                fps=fps,
                clip_start_ms=eff_start_ms,
                clip_end_ms=eff_end_ms,
                source=source,
            )
        except Exception as err:
            self.log_player_event(f"[Pyxis Error in run_ass_telemetry] {err}")
            return {"success": False, "error": str(err)}


    def get_last_telemetry(self):
        """Retrieves the most recent completed libass telemetry payload from in-memory cache.

        Returns:
            dict[str, Any]: The cached telemetry dictionary if available, or a fallback payload
            indicating an empty state or query failure.
        """
        try:
            from ass_telemetry_engine import GLOBAL_TELEMETRY_MANAGER
            last_res = GLOBAL_TELEMETRY_MANAGER.get_last_result()
            if last_res:
                return last_res
            return {"success": False, "empty": True}
        except Exception as err:
            return {"success": False, "error": str(err)}

    def cancel_ass_telemetry(self):
        """Terminates any active libass profiler worker background processes immediately.

        Returns:
            dict[str, Any]: Confirmation dictionary with 'success': True or an error description.
        """
        try:
            from ass_telemetry_engine import GLOBAL_TELEMETRY_MANAGER
            GLOBAL_TELEMETRY_MANAGER.cancel_active()
            return {"success": True}
        except Exception as err:
            return {"success": False, "error": str(err)}

    def clear_ass_telemetry(self):
        """Purges cached preview ASS script buffers and resets in-memory telemetry results.

        Returns:
            dict[str, Any]: Confirmation dictionary with 'success': True or an error description.
        """
        try:
            self._last_preview_ass_content = None
            self._last_preview_ass_info = None
            from ass_telemetry_engine import GLOBAL_TELEMETRY_MANAGER
            GLOBAL_TELEMETRY_MANAGER.clear_last_result()
            return {"success": True}
        except Exception as err:
            return {"success": False, "error": str(err)}

    def _select_save_video_path(self, default_filename="hardsub_clip.mp4"):
        """Displays an interactive native save file dialog to select the destination MP4 path.

        Attempts invocation via PyWebView file dialog first, falling back to Tkinter if unavailable.

        Args:
            default_filename (str): Suggested default output filename.

        Returns:
            str | None: Absolute destination path selected by the user, or None if cancelled.
        """
        try:
            if hasattr(webview, "windows") and webview.windows:
                window = webview.windows[0]
                save_flag = getattr(webview, 'FileDialog', None).SAVE if hasattr(webview, 'FileDialog') else webview.SAVE_DIALOG
                result = window.create_file_dialog(
                    save_flag,
                    save_filename=default_filename,
                    file_types=("MP4 Video (*.mp4)", "All files (*.*)"),
                )
                if not result:
                    return None
                if isinstance(result, (list, tuple)):
                    return result[0] if result else None
                return str(result)
        except Exception as e:
            print("[Pyxis pywebview save dialog warning]", e, flush=True)

        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            file_path = filedialog.asksaveasfilename(
                title="Save Hardsub Video Clip",
                defaultextension=".mp4",
                initialfile=default_filename,
                filetypes=[("MP4 Video", "*.mp4"), ("All files", "*.*")]
            )
            root.destroy()
            return file_path if file_path else None
        except Exception as e:
            print("[Pyxis tkinter save dialog warning]", e, flush=True)
            return None

    def render_preview_hardsub(self, payload, target_output_id=None, out_filename=None, source="base"):
        """Renders an exported MP4 video clip with burned-in hardsub subtitles using FFmpeg.

        Generates the target preview ASS script, probes available hardware encoders (NVENC, AMF,
        QSV, or libx264 CPU fallback), binds the ASS subtitles filter with custom fonts directory,
        and encodes an MP4 video clip into the chosen destination path.

        Args:
            payload (dict | str): Graph topology serialisation payload.
            target_output_id (str | list[str] | None): Target Output node identifier(s).
            out_filename (str | None): Optional predefined output filename.
            source (str): Subtitle source mode ('base' or 'aegisub').

        Returns:
            dict[str, Any]: Result dictionary containing 'success', 'saved_path', and 'data_url'
            with base64-encoded video content for immediate frontend playback.
        """
        try:
            import time
            info = self.get_preview_info(source=source, target_output_id=target_output_id, payload=payload)
            clock_num = int(time.time() * 1000) % 1000000
            output_tag = f"multi_{len(target_output_id)}" if isinstance(target_output_id, list) else (target_output_id or "dummy")
            default_fn = out_filename or f"Effect_{clock_num:06d}.mp4"

            save_path = self._select_save_video_path(default_filename=default_fn)
            if not save_path:
                return {"success": False, "cancelled": True, "message": "Rendering cancelled by user"}

            ass_filename = f"preview_dummy_{output_tag}.ass"
            gen_res = self.generate_preview_ass(payload, target_output_id=target_output_id, out_filename=ass_filename, source=source, for_hardsub=True)
            appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            pyxis_dir = os.path.join(appdata_dir, "PyxisNodes")
            temp_dir = os.path.join(pyxis_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            preview_ass_path = os.path.join(temp_dir, ass_filename)

            if isinstance(gen_res, dict) and gen_res.get("content"):
                with open(preview_ass_path, "w", encoding="utf-8") as f:
                    f.write(gen_res["content"])

            ffmpeg_exe = self._find_ffmpeg()

            res_x = int(info.get("res_x", 1280))
            res_y = int(info.get("res_y", 720))
            res_x = max(2, res_x - (res_x % 2))
            res_y = max(2, res_y - (res_y % 2))
            fps = float(info.get("fps") or 23.976)
            clip_start_sec = float(info.get("clip_start_sec", 0.0))
            clip_dur_sec = float(info.get("clip_duration_sec", 15.0))
            real_video = info.get("real_video_file")
            real_audio = info.get("real_audio_file")
            dummy_info = info.get("dummy_info") or {}
            color_hex = str(dummy_info.get("color_hex") or "969696").lower()

            # Fonts directory detection for libass filter
            fonts_dir_param = ""
            ass_base = getattr(self, "base_ass_path", None) or info.get("base_ass_path")
            if ass_base and os.path.exists(ass_base):
                script_dir = os.path.dirname(os.path.abspath(ass_base))
                candidate_fonts = os.path.join(script_dir, "fonts")
                if os.path.isdir(candidate_fonts):
                    f_clean = candidate_fonts.replace("\\", "/")
                    fonts_dir_param = f":fontsdir='{f_clean}'"
                elif os.path.isdir(script_dir):
                    f_clean = script_dir.replace("\\", "/")
                    fonts_dir_param = f":fontsdir='{f_clean}'"

            sub_filter = f"subtitles='{ass_filename}'{fonts_dir_param}"

            enc_name, enc_args = self._detect_best_h264_encoder(ffmpeg_exe)

            def _build_cmd(v_encoder_args):
                if real_video and os.path.isfile(real_video) and (not real_audio or real_audio == real_video):
                    return [
                        ffmpeg_exe, "-y",
                        "-ss", f"{clip_start_sec:.3f}",
                        "-t", f"{clip_dur_sec:.3f}",
                        "-i", real_video,
                        "-avoid_negative_ts", "make_zero",
                        "-vf", sub_filter,
                        *v_encoder_args,
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-movflags", "+faststart",
                        save_path
                    ]
                elif real_video and os.path.isfile(real_video) and real_audio and os.path.isfile(real_audio):
                    return [
                        ffmpeg_exe, "-y",
                        "-ss", f"{clip_start_sec:.3f}",
                        "-t", f"{clip_dur_sec:.3f}",
                        "-i", real_video,
                        "-ss", f"{clip_start_sec:.3f}",
                        "-t", f"{clip_dur_sec:.3f}",
                        "-i", real_audio,
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-avoid_negative_ts", "make_zero",
                        "-vf", sub_filter,
                        *v_encoder_args,
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-shortest",
                        "-movflags", "+faststart",
                        save_path
                    ]
                elif real_audio and os.path.isfile(real_audio):
                    return [
                        ffmpeg_exe, "-y",
                        "-f", "lavfi", "-i", f"color=c=0x{color_hex}:s={res_x}x{res_y}:r={fps:.3f}:d={clip_dur_sec:.3f}",
                        "-ss", f"{clip_start_sec:.3f}",
                        "-t", f"{clip_dur_sec:.3f}",
                        "-i", real_audio,
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-avoid_negative_ts", "make_zero",
                        "-vf", sub_filter,
                        *v_encoder_args,
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-shortest",
                        "-movflags", "+faststart",
                        save_path
                    ]
                else:
                    return [
                        ffmpeg_exe, "-y",
                        "-f", "lavfi", "-i", f"color=c=0x{color_hex}:s={res_x}x{res_y}:r={fps:.3f}:d={clip_dur_sec:.3f}",
                        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                        "-vf", sub_filter,
                        *v_encoder_args,
                        "-c:a", "aac",
                        "-b:a", "64k",
                        "-shortest",
                        "-movflags", "+faststart",
                        save_path
                    ]

            cmd = _build_cmd(enc_args)

            import subprocess
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if os.name == 'nt' else 0
            proc = subprocess.run(
                cmd,
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags
            )

            if proc.returncode != 0 and enc_name != "libx264":
                print(f"[Pyxis FFmpeg] Hardware encoder '{enc_name}' falló durante la exportación de Hardsub ({proc.stderr[-180:] if proc.stderr else ''}). Reintentando con libx264 CPU...", flush=True)
                cpu_enc_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "15", "-tune", "animation", "-pix_fmt", "yuv420p", "-threads", "0"]
                fallback_cmd = _build_cmd(cpu_enc_args)
                proc = subprocess.run(
                    fallback_cmd,
                    cwd=temp_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=creationflags
                )

            if proc.returncode != 0:
                err_msg = proc.stderr[-400:] if proc.stderr else f"Exit code {proc.returncode}"
                print(f"[Pyxis FFmpeg Hardsub Error] code {proc.returncode}:\n{proc.stderr}", flush=True)
                return {"success": False, "error": f"FFmpeg error: {err_msg}"}

            import base64
            with open(save_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")

            return {
                "success": True,
                "saved_path": save_path,
                "data_url": f"data:video/mp4;base64,{encoded}"
            }
        except Exception as err:
            print(f"[Pyxis Error in render_preview_hardsub] {err}", flush=True)
            return {"success": False, "error": str(err)}

    def _get_docs_dir(self, lang=None):
        """Resolves the physical directory containing technical manual documentation chapters.

        Inspects the requested language code ('es' or 'en') and validates folder existence
        within the PyxisNodes distribution package.

        Args:
            lang (str | None): Target ISO language code ('es' for Spanish, 'en' for British English).

        Returns:
            str: Absolute path to the resolved documentation directory.
        """
        try:
            from paths import DOCS_DIR
            root_docs = DOCS_DIR
        except Exception:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            root_docs = os.path.join(base_dir, "..", "docs")
            if not os.path.isdir(root_docs):
                root_docs = os.path.join(base_dir, "docs")
        
        target_lang = str(lang or "es").lower().strip()
        lang_sub = "en" if target_lang.startswith("en") else "es"
        candidate_dir = os.path.join(root_docs, lang_sub)

        if os.path.isdir(candidate_dir):
            return candidate_dir
        if os.path.isdir(root_docs):
            return root_docs
        return base_dir

    def _build_docs_index(self, lang=None, force=False):
        """Scans and indexes technical documentation markdown files into memory.

        Extracts chapter titles, node headers (## X. Node Type), anchors, and cross-references,
        maintaining an ordered table of contents (TOC) and a lookup map keyed by node type.

        Args:
            lang (str | None): Language identifier ('es' or 'en').
            force (bool): If True, bypasses in-memory caching and rebuilds index from disk.

        Returns:
            tuple[list[dict], dict[str, dict]]: A tuple comprising (toc_list, node_lookup_map).
        """
        target_lang = str(lang or "es").lower().strip()
        lang_key = "en" if target_lang.startswith("en") else "es"

        if not hasattr(self, "_cached_docs_tocs") or self._cached_docs_tocs is None:
            self._cached_docs_tocs = {}
            self._cached_node_maps = {}

        if not force and lang_key in self._cached_docs_tocs and lang_key in self._cached_node_maps:
            return self._cached_docs_tocs[lang_key], self._cached_node_maps[lang_key]

        docs_dir = self._get_docs_dir(lang_key)
        toc = []
        node_map = {}

        if not os.path.isdir(docs_dir):
            self._cached_docs_tocs[lang_key] = []
            self._cached_node_maps[lang_key] = {}
            return [], {}

        files = sorted(os.listdir(docs_dir))
        node_pattern = re.compile(r"^##\s+(\d+)\.\s+(?:Nodo|Node)\s+[`\"']?([^`\"'\(\)\n]+)[`\"']?\s*(?:\((.*?)\))?", re.MULTILINE)
        title_pattern = re.compile(r"^#\s+(.+)$", re.MULTILINE)

        for fname in files:
            if not fname.lower().endswith(".md"):
                continue
            fpath = os.path.join(docs_dir, fname)
            if not os.path.isfile(fpath):
                continue

            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            m_title = title_pattern.search(content)
            chapter_title = m_title.group(1).strip() if m_title else os.path.splitext(fname)[0]

            chapter_nodes = []
            for match in node_pattern.finditer(content):
                num_idx = int(match.group(1))
                canonical_type = match.group(2).strip()
                label = match.group(3).strip() if match.group(3) else ""
                anchor = f"node-{canonical_type.lower().replace('/', '-').replace(' ', '-')}"

                node_entry = {
                    "type": canonical_type,
                    "name": canonical_type.split("/")[-1].strip() if "/" in canonical_type else canonical_type,
                    "index": num_idx,
                    "label": label,
                    "anchor": anchor,
                    "title": f"{num_idx}. {canonical_type}" + (f" ({label})" if label else ""),
                    "file": fname
                }
                chapter_nodes.append(node_entry)
                node_map[canonical_type.lower()] = {
                    **node_entry,
                    "chapter_file": fname,
                    "chapter_title": chapter_title
                }

            # Extracción del número o prefijo de capítulo para ordenación
            m_num = re.match(r"^(\d+)", fname)
            chapter_num = int(m_num.group(1)) if m_num else 999

            toc.append({
                "file": fname,
                "chapter_num": chapter_num,
                "title": chapter_title,
                "node_count": len(chapter_nodes),
                "nodes": chapter_nodes
            })

        toc.sort(key=lambda x: (x["chapter_num"], x["file"]))
        self._cached_docs_tocs[lang_key] = toc
        self._cached_node_maps[lang_key] = node_map
        return toc, node_map

    def get_docs_toc(self, lang=None):
        """Retrieves the complete Table of Contents of the Pyxis technical manual for the GUI.

        Args:
            lang (str | None): Requested language ('es' or 'en').

        Returns:
            dict[str, Any]: Result dictionary containing 'success' and 'toc' chapter list.
        """
        try:
            toc, _ = self._build_docs_index(lang)
            return {"success": True, "toc": toc}
        except Exception as e:
            return {"success": False, "error": str(e), "toc": []}

    def get_doc_chapter(self, filename, lang=None):
        """Reads and returns the complete markdown content of a specific manual chapter.

        Resolves filename variants and provides graceful fallback to Spanish documentation
        if an English chapter translation is not yet available.

        Args:
            filename (str): Name or prefix of the chapter markdown file (e.g. '03 Basics.md').
            lang (str | None): Language identifier ('es' or 'en').

        Returns:
            dict[str, Any]: Result dictionary containing 'success', 'filename', and 'content'.
        """
        try:
            safe_name = os.path.basename(str(filename).strip())
            docs_dir = self._get_docs_dir(lang)
            target_path = os.path.join(docs_dir, safe_name)

            if not os.path.isfile(target_path) and os.path.isdir(docs_dir):
                m_num = re.match(r"^(\d+)", safe_name)
                if m_num:
                    ch_prefix = int(m_num.group(1))
                    for candidate in os.listdir(docs_dir):
                        if candidate.lower().endswith(".md") and re.match(r"^0*" + str(ch_prefix) + r"\b", candidate):
                            target_path = os.path.join(docs_dir, candidate)
                            safe_name = candidate
                            break

            if not os.path.isfile(target_path):
                # Fallback to Spanish directory if not found in requested language
                es_dir = self._get_docs_dir("es")
                target_path = os.path.join(es_dir, safe_name)
                if not os.path.isfile(target_path) and os.path.isdir(es_dir):
                    m_num = re.match(r"^(\d+)", safe_name)
                    if m_num:
                        ch_prefix = int(m_num.group(1))
                        for candidate in os.listdir(es_dir):
                            if candidate.lower().endswith(".md") and re.match(r"^0*" + str(ch_prefix) + r"\b", candidate):
                                target_path = os.path.join(es_dir, candidate)
                                safe_name = candidate
                                break

            if not os.path.isfile(target_path):
                return {"success": False, "error": f"Chapter file '{safe_name}' not found"}

            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {
                "success": True,
                "filename": safe_name,
                "content": content
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_node_doc(self, node_type, lang=None):
        """Extracts the contextual documentation section for a single canonical node type.

        Locates the chapter containing the node definition and slices the markdown content
        between the node's `##` header and the subsequent section delimiter.

        Args:
            node_type (str): Canonical node type identifier (e.g. 'Basic/Coordinate System').
            lang (str | None): Target language identifier ('es' or 'en').

        Returns:
            dict[str, Any]: Result payload with 'success', 'found', 'node_type', 'chapter_file',
            'chapter_title', 'section_title', 'anchor', and 'content'.
        """
        try:
            if not node_type or not isinstance(node_type, str):
                return {"success": False, "found": False, "error": "Invalid node_type"}

            canonical_key = node_type.strip().lower()
            _, node_map = self._build_docs_index(lang)

            info = node_map.get(canonical_key)
            if not info:
                # Fallback to Spanish index if not found in requested language
                _, node_map_es = self._build_docs_index("es")
                info = node_map_es.get(canonical_key)

            if not info:
                # Intentar buscar por coincidencia parcial si tiene prefijo
                for k, v in node_map.items():
                    if k.endswith("/" + canonical_key) or canonical_key.endswith("/" + k):
                        info = v
                        break

            if not info:
                return {
                    "success": True,
                    "found": False,
                    "node_type": node_type,
                    "message": f"Documentation for node '{node_type}' not found."
                }

            chapter_file = info["chapter_file"]
            docs_dir = self._get_docs_dir(lang)
            target_path = os.path.join(docs_dir, chapter_file)
            if not os.path.isfile(target_path):
                target_path = os.path.join(self._get_docs_dir("es"), chapter_file)

            with open(target_path, "r", encoding="utf-8") as f:
                full_content = f.read()

            # Extraer la sección del nodo desde su encabezado ## hasta el siguiente ## o fin de archivo
            pattern = re.compile(
                r"(^##\s+\d+\.\s+(?:Nodo|Node)\s+[`\"']?" + re.escape(info["type"]) + r"[`\"']?.*?)(?=\n---\s*\n##\s+|\n##\s+|\Z)",
                re.MULTILINE | re.DOTALL
            )
            match = pattern.search(full_content)
            section_content = match.group(1).strip() if match else ""

            return {
                "success": True,
                "found": True,
                "node_type": info["type"],
                "chapter_file": chapter_file,
                "chapter_title": info.get("chapter_title", ""),
                "section_title": info.get("title", ""),
                "anchor": info.get("anchor", ""),
                "content": section_content
            }
        except Exception as e:
            return {"success": False, "found": False, "error": str(e)}

    def get_doc_image(self, name):
        """Locates and encodes a documentation asset image into a base64 Data URL.

        Searches within language-specific and root documentation `img/` directories.

        Args:
            name (str): Image filename (e.g. 'diagram_nodes.png').

        Returns:
            dict[str, Any]: Result dictionary with 'success' and base64 'data_url'.
        """
        try:
            try:
                from paths import DOCS_DIR
                root_docs = DOCS_DIR
            except Exception:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                root_docs = os.path.join(base_dir, "..", "docs")
                if not os.path.isdir(root_docs):
                    root_docs = os.path.join(base_dir, "docs")

            safe_name = os.path.basename(str(name).strip())
            
            candidates = [
                os.path.join(root_docs, "img", safe_name),
                os.path.join(root_docs, "es", "img", safe_name),
                os.path.join(root_docs, "en", "img", safe_name),
                os.path.join(root_docs, safe_name)
            ]
            img_path = None
            for c in candidates:
                if os.path.isfile(c):
                    img_path = c
                    break

            if img_path and os.path.isfile(img_path):
                import base64
                with open(img_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                ext = os.path.splitext(img_path)[1].lower().replace(".", "")
                mime = "image/png" if ext == "png" else f"image/{ext}"
                return {"success": True, "data_url": f"data:{mime};base64,{b64}"}
            return {"success": False, "error": f"Image '{safe_name}' not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def shutdown_daemon(self):
        """Gracefully shuts down the background daemon server and closes GUI windows.

        Releases the Aegisub lock file, terminates the HTTP/WebSocket daemon listener, and
        destroys the native PyWebView window.
        """
        try:
            self.release_lock()
            if hasattr(self, "_daemon_server") and self._daemon_server:
                self._daemon_server.shutdown()
            elif webview.windows:
                webview.windows[0].destroy()
        except Exception:
            sys.exit(0)

    @staticmethod
    def _normalize_graph(payload):
        """Validates and extracts the canonical graph structure from a serialised payload.

        Ensures the payload contains valid 'nodes' and 'links' collections, unwrapping
        nested graph containers if necessary.

        Args:
            payload (dict | str): Graph dictionary or JSON string.

        Returns:
            dict: Normalised graph dictionary containing 'nodes' and optional 'links'.

        Raises:
            ValueError: If the payload structure violates essential LiteGraph schema rules.
        """
        graph_data = payload if isinstance(payload, dict) else json.loads(payload)
        if "nodes" not in graph_data and "graph" in graph_data:
            graph_data = graph_data["graph"]
        if not isinstance(graph_data, dict):
            raise ValueError("Graph must be a JSON object")
        if not isinstance(graph_data.get("nodes"), list):
            raise ValueError("Graph must contain a list of nodes")
        if "links" in graph_data and not isinstance(graph_data["links"], list):
            raise ValueError("Links must be a list")
        return graph_data


def main():
    """Main application bootstrap entry point for Pyxis Effector.

    Parses command-line arguments passed from Aegisub Automation or standalone launcher,
    checks for an existing daemon instance to facilitate instant hot-reloading, enforces
    Microsoft Edge WebView2 runtime dependencies, initialises the native window, binds
    PyxisAPI, starts the PyxisDaemonServer listener, and handles the application lifecycle.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
    user_temp_dir = os.path.join(appdata_dir, "PyxisNodes", "temp")
    os.makedirs(user_temp_dir, exist_ok=True)

    temp_ass = sys.argv[1] if len(sys.argv) > 1 else os.path.join(user_temp_dir, "pyxis_temp.ass")
    result_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(user_temp_dir, "pyxis_result.txt")
    lock_file = sys.argv[3] if len(sys.argv) > 3 else os.path.join(user_temp_dir, "pyxis_lock.txt")
    session_file = sys.argv[4] if len(sys.argv) > 4 else os.path.join(user_temp_dir, "pyxis_session.json")
    aegisub_version = sys.argv[5] if len(sys.argv) > 5 else "unknown"
    aegisub_pid = int(sys.argv[6]) if (len(sys.argv) > 6 and sys.argv[6].isdigit()) else None

    from pyxis_daemon import check_daemon_running, notify_daemon_reopen, PyxisDaemonServer

    daemon_info = check_daemon_running()
    if daemon_info:
        reopen_payload = {
            "temp_ass": temp_ass,
            "result_file": result_file,
            "lock_file": lock_file,
            "session_file": session_file,
            "aegisub_version": aegisub_version,
            "aegisub_pid": aegisub_pid
        }
        if notify_daemon_reopen(reopen_payload):
            sys.exit(0)

    try:
        api = PyxisAPI(temp_ass, result_file, session_file, aegisub_version, lock_file=lock_file)

        # Enforce EdgeChromium (WebView2) and strictly block deprecated MSHTML / Internet Explorer
        os.environ["PYWEBVIEW_GUI"] = "edgechromium"
        from dependency_checker import ensure_dependencies
        if not ensure_dependencies(api._get_config_path()):
            if hasattr(api, "release_lock"):
                api.release_lock()
            sys.exit(1)

        try:
            from paths import get_web_path
            html_path = get_web_path("index.html")
        except Exception:
            html_path = os.path.join(script_dir, "..", "web", "index.html")
            if not os.path.exists(html_path):
                html_path = os.path.join(script_dir, "web", "index.html")
        html_url = html_path + f"?v={int(os.path.getmtime(html_path))}" if os.path.exists(html_path) else html_path
        initial_config = api.get_user_config()
        saved_win_state = initial_config.get("window_state", {})
        init_width = 1280
        init_height = 720
        if isinstance(saved_win_state, dict):
            w_val = saved_win_state.get("width")
            h_val = saved_win_state.get("height")
            if isinstance(w_val, int) and isinstance(h_val, int) and w_val >= 800 and h_val >= 600:
                init_width = w_val
                init_height = h_val

        os.environ["COREWEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = (
            "--disable-features=HardwareMediaKeyHandling,MediaSessionService "
            "--disable-component-update"
        )

        window = webview.create_window(
            title=f"Pyxis Node Engine {PYXIS_ENGINE_VERSION}",
            url=html_url,
            js_api=api,
            width=init_width,
            height=init_height,
            background_color="#121212",
        )

        def _on_window_shown():
            try:
                _apply_pyxis_window_icon()
            except Exception:
                pass
            try:
                try:
                    from paths import get_web_path
                    ico_path = get_web_path("icon.ico")
                except Exception:
                    ico_path = os.path.join(script_dir, "..", "web", "icon.ico")
                    if not os.path.exists(ico_path):
                        ico_path = os.path.join(script_dir, "web", "icon.ico")
                if os.path.exists(ico_path) and hasattr(window, "native") and window.native:
                    import importlib
                    clr = importlib.import_module("clr")
                    clr.AddReference("System.Drawing")
                    sys_drawing = importlib.import_module("System.Drawing")
                    window.native.Icon = getattr(sys_drawing, "Icon")(ico_path)
            except Exception:
                pass
            if isinstance(saved_win_state, dict) and saved_win_state.get("maximized"):
                try:
                    window.maximize()
                except Exception:
                    pass
        window.events.shown += _on_window_shown

        def on_window_maximized():
            if not hasattr(api, "_saved_window_state") or not isinstance(api._saved_window_state, dict):
                api._saved_window_state = {}
            api._saved_window_state["maximized"] = True

        def on_window_restored():
            if not hasattr(api, "_saved_window_state") or not isinstance(api._saved_window_state, dict):
                api._saved_window_state = {}
            api._saved_window_state["maximized"] = False

        def on_window_resized(width, height):
            if not hasattr(api, "_saved_window_state") or not isinstance(api._saved_window_state, dict):
                api._saved_window_state = {}
            if not api._saved_window_state.get("maximized"):
                api._saved_window_state["width"] = width
                api._saved_window_state["height"] = height

        window.events.maximized += on_window_maximized
        window.events.restored += on_window_restored
        window.events.resized += on_window_resized

        daemon_server = PyxisDaemonServer(main_api=api, window=window)
        daemon_server.aegisub_pid = aegisub_pid
        daemon_server.start()
        api._daemon_server = daemon_server

        def on_closing():
            if getattr(api, "_is_handling_closing", False):
                return False
            api._is_handling_closing = True

            try:
                try:
                    api.cancel_generation()
                except Exception:
                    pass

                try:
                    api.release_lock()
                except Exception:
                    pass

                found_hwnd = None
                try:
                    import ctypes
                    from ctypes import wintypes
                    user32 = ctypes.windll.user32
                    kernel32 = ctypes.windll.kernel32
                    con_hwnd = kernel32.GetConsoleWindow() if hasattr(kernel32, "GetConsoleWindow") else None
                    my_pid = os.getpid()
                    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                    def enum_cb(h, l):
                        nonlocal found_hwnd
                        if con_hwnd and h == con_hwnd:
                            return True
                        cls_buff = ctypes.create_unicode_buffer(64)
                        user32.GetClassNameW(h, cls_buff, 64)
                        if cls_buff.value == "ConsoleWindowClass":
                            return True
                        lp = ctypes.c_ulong()
                        user32.GetWindowThreadProcessId(h, ctypes.byref(lp))
                        if lp.value == my_pid:
                            length = user32.GetWindowTextLengthW(h)
                            if length > 0:
                                buff = ctypes.create_unicode_buffer(length + 1)
                                user32.GetWindowTextW(h, buff, length + 1)
                                if buff.value == window.title or (getattr(window, "title", None) and str(window.title) in buff.value) or "Pyxis Node Engine" in buff.value:
                                    found_hwnd = h
                                    return False
                        return True
                    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
                    if not found_hwnd and getattr(window, "title", None):
                        found_hwnd = user32.FindWindowW(None, str(window.title))

                    if found_hwnd:
                        is_maximized = bool(user32.IsZoomed(found_hwnd))
                        rect = wintypes.RECT()
                        user32.GetWindowRect(found_hwnd, ctypes.byref(rect))
                        w = rect.right - rect.left
                        h = rect.bottom - rect.top
                        win_state = {
                            "maximized": is_maximized,
                            "width": w,
                            "height": h,
                            "x": rect.left,
                            "y": rect.top
                        }
                        api._saved_window_state = win_state
                        cfg_path = api._get_config_path()
                        if os.path.exists(cfg_path):
                            with open(cfg_path, "r", encoding="utf-8") as f:
                                saved_cfg = json.load(f)
                            if isinstance(saved_cfg, dict):
                                saved_cfg["window_state"] = win_state
                                with open(cfg_path, "w", encoding="utf-8") as f:
                                    json.dump(saved_cfg, f, indent=2)
                except Exception as e:
                    print(f"[Pyxis Window State Save Error] {e}", flush=True)

                config = api.get_user_config()
                is_daemon = config.get("daemon_mode", True)

                if is_daemon:
                    target_hwnd = found_hwnd

                    def _async_daemon_cleanup():
                        import time
                        time.sleep(0.03)
                        if target_hwnd:
                            try:
                                user32.ShowWindow(target_hwnd, 0)
                            except Exception:
                                pass
                        try:
                            window.hide()
                        except Exception:
                            pass
                        try:
                            window.evaluate_js("if (window.PyxisNodePlayerManager && typeof window.PyxisNodePlayerManager.suspendForDaemon === 'function') window.PyxisNodePlayerManager.suspendForDaemon();")
                        except Exception:
                            pass

                    import threading
                    threading.Thread(target=_async_daemon_cleanup, daemon=True).start()

                    api._is_handling_closing = False
                    return False
                else:
                    try:
                        api.shutdown_daemon()
                    except Exception:
                        pass
                    from node_engine import abort_global_multiprocessing
                    abort_global_multiprocessing()
                    api._is_handling_closing = False
                    return True
            except Exception as e:
                print(f"[Pyxis on_closing Error] {e}", flush=True)
                api._is_handling_closing = False
                return True

        window.events.closing += on_closing
        webview.settings['OPEN_DEVTOOLS_IN_DEBUG'] = False
        os.environ["PYWEBVIEW_GUI"] = "edgechromium"
        webview.start(debug=True, http_server=True, gui="edgechromium")
    except Exception:
        debug_file = result_file + "_debug.log"
        try:
            with open(debug_file, "w", encoding="utf-8") as error_file:
                error_file.write(traceback.format_exc())
        except OSError:
            pass
    finally:
        try:
            if 'api' in locals() and hasattr(api, 'release_lock'):
                api.release_lock()
            elif lock_file and os.path.exists(lock_file):
                os.remove(lock_file)
        except OSError:
            pass


if __name__ == "__main__":
    main()

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
import traceback
import uuid
from datetime import datetime, timezone

class _LogBufferStream:
    _buffer = []
    _max_buffer = 3000

    def __init__(self, original_stream=None):
        self.console_file = None
        self.original_stream = original_stream

    def write(self, s):
        if s:
            _LogBufferStream._buffer.append(s)
            if len(_LogBufferStream._buffer) > _LogBufferStream._max_buffer:
                _LogBufferStream._buffer.pop(0)
            if self.console_file:
                try:
                    self.console_file.write(s)
                    self.console_file.flush()
                except Exception:
                    pass
            if self.original_stream:
                try:
                    self.original_stream.write(s)
                    self.original_stream.flush()
                except Exception:
                    pass

    def flush(self):
        if self.console_file:
            try:
                self.console_file.flush()
            except Exception:
                pass
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

PYXIS_ENGINE_VERSION = "1.0.4"


def _setup_windows_job_object():
    """Asocia el proceso de Python a un Job Object de Windows con JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE.
    Garantiza que si el proceso de Python se cierra, muere o se cancela, Windows elimina automáticamente
    a todos los procesos hijos (workers de multiprocessing, ffmpeg, etc.) sin dejar procesos zombi.
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
    try:
        from node_engine import abort_global_multiprocessing
        abort_global_multiprocessing()
    except Exception:
        pass
atexit.register(_cleanup_at_exit)


def _atomic_write(path, data):
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
        # Fallback directo en Windows por bloqueos temporales de lectura
        try:
            with open(path, "w", encoding="utf-8") as file_handle:
                file_handle.write(data)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass


class PyxisAPI:
    def __init__(self, temp_ass, result_file, session_file, aegisub_version="unknown", lock_file=None):
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

        # Purga automática de temporales (> 72h) en segundo plano (0ms de impacto en arranque)
        try:
            import threading
            threading.Thread(target=self.cleanup_temp_files, kwargs={"max_age_hours": 72}, daemon=True).start()
        except Exception as e:
            print(f"[Pyxis] Error al iniciar hilo de purga de temporales: {e}", flush=True)

    def release_lock(self):
        """
        Libera de forma atómica y robusta el archivo lock para Aegisub en Windows.
        Incluye reintentos con micro-pausas para evitar colisiones [WinError 32]
        cuando el hilo de sondeo en Lua está inspeccionando el archivo en ese milisegundo.
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

    def toggle_python_console(self):
        """Muestra u oculta la consola nativa de comandos de Python a voluntad en Windows."""
        try:
            import ctypes
            import sys

            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            hwnd = kernel32.GetConsoleWindow()

            if hwnd and hwnd != 0:
                if user32.IsWindowVisible(hwnd):
                    user32.ShowWindow(hwnd, 0)  # SW_HIDE
                    return {"status": "hidden"}
                else:
                    user32.ShowWindow(hwnd, 5)  # SW_SHOW
                    user32.SetForegroundWindow(hwnd)
                    return {"status": "shown"}
            else:
                kernel32.AllocConsole()
                hwnd = kernel32.GetConsoleWindow()
                if hwnd and hwnd != 0:
                    # Desactivar el botón X (cerrar) de la ventana de la consola para evitar cerrar accidentalmente el proceso Python
                    hmenu = user32.GetSystemMenu(hwnd, False)
                    if hmenu:
                        user32.DeleteMenu(hmenu, 0xF060, 0x00000000)  # SC_CLOSE, MF_BYCOMMAND

                    conout = None
                    try:
                        conout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
                        GLOBAL_STDOUT_STREAM.console_file = conout
                        GLOBAL_STDERR_STREAM.console_file = conout
                    except Exception:
                        pass

                    print("==========================================================", flush=True)
                    print(" [Pyxis Engine v1.0.4] Consola de Python (Modo Depuración)", flush=True)
                    print(" Presione F1 en Pyxis Nodes para mostrar/ocultar esta consola.", flush=True)
                    print("==========================================================", flush=True)

                    # Volcar historial de logs acumulados desde el inicio
                    try:
                        hist = "".join(_LogBufferStream._buffer)
                        if hist and conout:
                            conout.write("\n--- HISTORIAL DE LOGS ACUMULADOS DESDE EL ARRANQUE ---\n")
                            conout.write(hist)
                            conout.write("\n--- FIN DEL HISTORIAL (LOGS EN TIEMPO REAL A CONTINUACIÓN) ---\n\n")
                            conout.flush()
                    except Exception:
                        pass

                    return {"status": "created"}
        except Exception as e:
            print(f"[Pyxis Error toggling console] {e}", flush=True)
        return {"status": "error"}

    @property
    def template_store(self):
        if self._store is None:
            from template_store import TemplateStore
            self._store = TemplateStore(
                templates_dir=self.system_templates_dir,
                aegisub_version=self.aegisub_version,
                user_templates_dir=self.user_templates_dir,
            )
        return self._store

    def _get_config_path(self):
        appdata_dir = os.environ.get("APPDATA")
        if not appdata_dir:
            appdata_dir = os.path.expanduser("~")
        pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
        os.makedirs(pyxis_config_dir, exist_ok=True)
        return os.path.join(pyxis_config_dir, "user_config.json")

    def _get_bg_media_dir(self):
        appdata_dir = os.environ.get("APPDATA")
        if not appdata_dir:
            appdata_dir = os.path.expanduser("~")
        bg_media_dir = os.path.join(appdata_dir, "PyxisNodes", "bg_media")
        os.makedirs(bg_media_dir, exist_ok=True)
        return bg_media_dir

    def _get_bg_image_path(self):
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
        script_dir = os.path.dirname(os.path.abspath(__file__))
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
        candidates = [
            os.path.join(script_dir, "web", "default_back.webp"),
            os.path.join(script_dir, "default_back.webp"),
            os.path.join(pyxis_config_dir, "default_back.webp")
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        return None

    def _get_bg_media_info(self):
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
                print("Pyxis: error al codificar imagen de fondo", e)

        # Si no se encuentra un fondo entre los archivos del usuario, tomar default_back.webp
        # a menos que el usuario haya solicitado explícitamente quitar el fondo (no_bg=True)
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
                    print("Pyxis: error al codificar fondo por defecto", e)

        return {
            "has_bg": False,
            "media_type": "none",
            "video_url": "",
            "poster_url": "",
            "data_url": "",
            "is_default": False
        }

    def get_user_config(self):
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
            "language": "es"
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

            # Si se está usando el fondo por defecto (default_back.webp),
            # asegurar modo rellenar (cover), opacidad al 85% y malla en modo puntos (1)
            if bg_info.get("is_default", False):
                if config.get("bg_image_opacity") in [0.5, "0.5", None]:
                    config["bg_image_opacity"] = 0.85
                if config.get("grid_mode") in [0, "0", None]:
                    config["grid_mode"] = 1
                if config.get("bg_image_mode") in ["contain", None]:
                    config["bg_image_mode"] = "cover"
        except Exception as e:
            print("Pyxis: error al leer user_config", e)
        return config

    def get_bg_image_data(self):
        try:
            info = self._get_bg_media_info()
            return info.get("data_url", "")
        except Exception as e:
            print("Pyxis: error al obtener datos de imagen de fondo", e)
        return ""

    def get_bg_media_data(self):
        try:
            return self._get_bg_media_info()
        except Exception as e:
            print("Pyxis: error al obtener datos multimedia de fondo", e)
            return {"has_bg": False, "media_type": "none", "video_url": "", "poster_url": "", "data_url": "", "is_default": False}

    def save_user_config(self, payload):
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

            is_daemon = bool(config_data.get("daemon_mode", True))
            saved_theme = config_data.get("theme", "teal")
            if saved_theme in ["obsidian", "cyber", "slate", "nordic"]:
                saved_theme = "teal"

            no_bg = is_removing_bg or (config_data.get("has_bg_image") is False and not is_removing_bg and config_data.get("no_bg", False))
            if config_data.get("has_bg_image") is True:
                no_bg = False

            if no_bg:
                bg_info = {"has_bg": False, "media_type": "none", "is_default": False}
            else:
                bg_info = self._get_bg_media_info()

            clean_config = {
                "theme": saved_theme,
                "grid_mode": config_data.get("grid_mode", 1),
                "undo_steps": config_data.get("undo_steps", 30),
                "bg_image_mode": config_data.get("bg_image_mode", "cover"),
                "bg_image_opacity": config_data.get("bg_image_opacity", 0.85),
                "has_bg_image": bg_info["has_bg"],
                "bg_media_type": bg_info["media_type"],
                "is_default_bg": bg_info.get("is_default", False),
                "no_bg": no_bg,
                "convert_video": bool(config_data.get("convert_video", True)),
                "daemon_mode": is_daemon,
                "language": config_data.get("language", "es"),
                "window_state": config_data.get("window_state", getattr(self, "_saved_window_state", {}))
            }
            config_path = self._get_config_path()
            _atomic_write(config_path, json.dumps(clean_config, ensure_ascii=False, indent=2))

            if hasattr(self, "_daemon_server") and self._daemon_server:
                self._daemon_server.daemon_mode = is_daemon

            return True
        except Exception as e:
            print("Pyxis: error al guardar user_config", e)
            return False

    def _get_themes_dir(self):
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        pyxis_themes_dir = os.path.join(appdata_dir, "PyxisNodes", "themes")
        os.makedirs(pyxis_themes_dir, exist_ok=True)
        return pyxis_themes_dir

    def _get_custom_themes_path(self):
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
        os.makedirs(pyxis_config_dir, exist_ok=True)
        return os.path.join(pyxis_config_dir, "custom_themes.json")

    def get_custom_themes(self):
        themes = {}
        try:
            # 1. Cargar custom_themes.json central si existe
            path = self._get_custom_themes_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                    if isinstance(c_data, dict):
                        for k, v in c_data.items():
                            if isinstance(v, dict) and v.get("id"):
                                v["isCustom"] = True
                                themes[v["id"]] = v

            # 2. Escanear directorio %APPDATA%/PyxisNodes/themes/*.json para fusionar temas en disco
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
                            print(f"Pyxis: error al cargar tema individual {fname}: {fe}")
        except Exception as e:
            print("Pyxis: error al leer custom_themes", e)
        return themes

    def save_custom_themes(self, payload):
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
            print("Pyxis: error al guardar custom_themes", e)
            return False

    def save_custom_theme(self, payload):
        try:
            theme_data = payload if isinstance(payload, dict) else json.loads(payload)
            theme_id = theme_data.get("id")
            if not theme_id:
                return False
            theme_data["isCustom"] = True
            
            # 1. Guardar en archivo individual en %APPDATA%/PyxisNodes/themes/<theme_id>.json
            themes_dir = self._get_themes_dir()
            safe_fn = "".join(c for c in theme_id if c.isalnum() or c in ("-", "_")) + ".json"
            ind_path = os.path.join(themes_dir, safe_fn)
            _atomic_write(ind_path, json.dumps(theme_data, ensure_ascii=False, indent=2))

            # 2. Actualizar custom_themes.json
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
            print("Pyxis: error al guardar custom_theme", e)
            return False

    def delete_custom_theme(self, theme_id):
        try:
            # 1. Eliminar de custom_themes.json
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

            # 2. Eliminar archivo individual por nombre y por ID en %APPDATA%/PyxisNodes/themes/
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
            print("Pyxis: error al eliminar custom_theme", e)
            return False

    @staticmethod
    def cleanup_temp_files(max_age_hours=72, force_all=False):
        """Elimina archivos temporales y fragmentos de caché con más de max_age_hours (72hs por defecto),
        protegiendo estrictamente las configuraciones, temas, plantillas y fondos del usuario."""
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

            # 1. temp_cache (%APPDATA%/PyxisNodes/temp_cache)
            temp_cache_dir = os.path.join(pyxis_dir, "temp_cache")
            if os.path.isdir(temp_cache_dir):
                for fname in os.listdir(temp_cache_dir):
                    fpath = os.path.join(temp_cache_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            mtime = os.path.getmtime(fpath)
                            if force_all or (now - mtime > cutoff_sec):
                                size = os.path.getsize(fpath)
                                os.remove(fpath)
                                cleaned_files += 1
                                freed_bytes += size
                        except Exception:
                            pass

            # 2. temp (%APPDATA%/PyxisNodes/temp)
            temp_dir = os.path.join(pyxis_dir, "temp")
            if os.path.isdir(temp_dir):
                for fname in os.listdir(temp_dir):
                    fpath = os.path.join(temp_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            mtime = os.path.getmtime(fpath)
                            if force_all or (now - mtime > cutoff_sec):
                                size = os.path.getsize(fpath)
                                os.remove(fpath)
                                cleaned_files += 1
                                freed_bytes += size
                        except Exception:
                            pass

            # 3. fonts (%APPDATA%/PyxisNodes/fonts)
            fonts_dir = os.path.join(pyxis_dir, "fonts")
            if os.path.isdir(fonts_dir):
                for fname in os.listdir(fonts_dir):
                    fpath = os.path.join(fonts_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            mtime = os.path.getmtime(fpath)
                            if force_all or (now - mtime > cutoff_sec):
                                size = os.path.getsize(fpath)
                                os.remove(fpath)
                                cleaned_files += 1
                                freed_bytes += size
                        except Exception:
                            pass

            # 4. bg_media (%APPDATA%/PyxisNodes/bg_media) - SÓLO clips preview_bg_* o export_bg_*
            bg_media_dir = os.path.join(pyxis_dir, "bg_media")
            if os.path.isdir(bg_media_dir):
                for fname in os.listdir(bg_media_dir):
                    # PROTECCIÓN ESTRICTA: Ignorar bg_video.*, bg_poster.* y cualquier archivo no temporal
                    if not (fname.startswith("preview_bg_") or fname.startswith("export_bg_")):
                        continue
                    fpath = os.path.join(bg_media_dir, fname)
                    if os.path.isfile(fpath):
                        try:
                            mtime = os.path.getmtime(fpath)
                            if force_all or (now - mtime > cutoff_sec):
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
        return self.cleanup_temp_files(max_age_hours=max_age_hours, force_all=force_all)

    def export_theme_dialog(self, payload):
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
                    file_types=("Archivo de Tema Pyxis (*.json)", "Todos los archivos (*.*)"),
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
                        title="Exportar Tema de Pyxis",
                        defaultextension=".json",
                        initialfile=default_fn,
                        filetypes=[("Archivo de Tema Pyxis", "*.json"), ("Todos los archivos", "*.*")]
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
        try:
            import time
            open_path = None
            if hasattr(webview, "windows") and webview.windows:
                window = webview.windows[0]
                open_flag = getattr(webview, 'FileDialog', None).OPEN if hasattr(webview, 'FileDialog') else webview.OPEN_DIALOG
                result = window.create_file_dialog(
                    open_flag,
                    file_types=("Archivo de Tema Pyxis (*.json)", "Todos los archivos (*.*)"),
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
                        title="Importar Tema de Pyxis",
                        filetypes=[("Archivo de Tema Pyxis", "*.json"), ("Todos los archivos", "*.*")]
                    )
                    root.destroy()
                except Exception as e:
                    print("[Pyxis import theme tkinter warning]", e, flush=True)

            if not open_path or not os.path.exists(open_path):
                return {"success": False, "cancelled": True}

            with open(open_path, "r", encoding="utf-8") as f:
                theme_data = json.load(f)

            if not isinstance(theme_data, dict) or ("canvasBg" not in theme_data and "categories" not in theme_data and "name" not in theme_data):
                return {"success": False, "error": "El archivo no contiene una estructura válida de tema Pyxis"}

            if "id" not in theme_data or not theme_data["id"]:
                theme_data["id"] = f"imported_{int(time.time() * 1000)}"
            theme_data["isCustom"] = True

            self.save_custom_theme(theme_data)
            return {"success": True, "theme": theme_data}
        except Exception as e:
            print("[Pyxis import_theme_dialog error]", e, flush=True)
            return {"success": False, "error": str(e)}

    def _get_code_templates_path(self):
        appdata_dir = os.environ.get("APPDATA")
        if not appdata_dir:
            appdata_dir = os.path.expanduser("~")
        pyxis_config_dir = os.path.join(appdata_dir, "PyxisNodes")
        os.makedirs(pyxis_config_dir, exist_ok=True)
        return os.path.join(pyxis_config_dir, "user_code_templates.json")

    def get_code_templates(self):
        try:
            path = self._get_code_templates_path()
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print("Pyxis: error al leer user_code_templates", e)
        return {}

    def save_code_templates(self, payload):
        try:
            templates = payload if isinstance(payload, dict) else json.loads(payload)
            path = self._get_code_templates_path()
            _atomic_write(path, json.dumps(templates, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            print("Pyxis: error al guardar user_code_templates", e)
            return False

    def _optimize_bg_image(self, input_path, output_path):
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
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_exe = os.path.join(script_dir, "ffmpeg.exe")
        if not os.path.exists(ffmpeg_exe):
            ffmpeg_exe = "ffmpeg"
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

    def _optimize_bg_video(self, input_path, output_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ffmpeg_exe = os.path.join(script_dir, "ffmpeg.exe")
        if not os.path.exists(ffmpeg_exe):
            ffmpeg_exe = "ffmpeg"
        
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
            print("Pyxis: error al optimizar video con ffmpeg, intentando transcodificación simple", e)
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
                print("Pyxis: fallo transcodificación simple, usando copia directa", e2)
                import shutil
                shutil.copyfile(input_path, output_path)
                self._generate_video_poster(output_path, poster_path)

    def select_bg_media(self, convert_video=True):
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
                        "Imágenes (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp)",
                        "Todos los archivos (*.*)"
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
                            ("Todos los archivos", "*.*")
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
            
            # Limpiar medios anteriores
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
            
            if is_video:
                # Si no es un formato web nativo (.mp4 o .webm), forzar conversión para que el navegador pueda reproducirlo
                should_convert = bool(convert_video) or ext not in (".mp4", ".webm")
                dest_video = os.path.join(bg_media_dir, f"bg_video{'.mp4' if should_convert else ext}")
                if should_convert:
                    self._optimize_bg_video(file_path, dest_video)
                else:
                    import shutil
                    shutil.copyfile(file_path, dest_video)
                    self._generate_video_poster(dest_video, poster_p)
                
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
                dest_image = os.path.join(pyxis_config_dir, "bg_image.webp")
                try:
                    self._optimize_bg_image(file_path, dest_image)
                except Exception as e:
                    print("Pyxis: compresión WEBP no disponible, usando copia directa", e)
                    import shutil
                    shutil.copyfile(file_path, dest_image)
                
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
            print("Pyxis: error al seleccionar fondo", e)
            return {"success": False, "error": str(e)}

    def select_bg_image(self):
        res = self.select_bg_media()
        if isinstance(res, dict):
            if res.get("media_type") == "image":
                return res.get("data_url", "")
            elif res.get("media_type") == "video":
                return res.get("video_url", "")
        return ""

    def select_image_dialog(self):
        try:
            if not webview.windows:
                return ""
            window = webview.windows[0]
            open_flag = getattr(webview, 'FileDialog', None).OPEN if hasattr(webview, 'FileDialog') else webview.OPEN_DIALOG
            result = window.create_file_dialog(
                open_flag,
                file_types=("Imágenes (*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp)", "Todos los archivos (*.*)"),
                allow_multiple=False,
            )
            if not result:
                return ""
            file_path = result if isinstance(result, str) else result[0]
            if not file_path or not os.path.exists(file_path):
                return ""
            return os.path.abspath(file_path)
        except Exception as e:
            print("Pyxis: error al abrir diálogo de selección de imagen", e)
            return ""

    def log_js_error(self, msg):
        print(f"[Pyxis JS ERROR] {msg}", flush=True)
        return True

    def log_js_info(self, msg):
        print(f"[Pyxis JS INFO] {msg}", flush=True)
        return True

    def get_manifest(self):
        from decorators import get_manifest
        import nodes_library
        return get_manifest()

    def get_session_graph(self):
        try:
            with open(self.session_file, "r", encoding="utf-8") as file_handle:
                return file_handle.read()
        except (FileNotFoundError, OSError):
            return ""

    def save_session(self, payload):
        try:
            graph_data = self._normalize_graph(payload)
            _atomic_write(
                self.session_file,
                json.dumps(graph_data, ensure_ascii=False, separators=(",", ":"), default=str),
            )
            return True
        except Exception as e:
            print(f"[Pyxis Warning] No se pudo guardar el archivo de sesión temporal ({e})", flush=True)
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
        graph_data = self._normalize_graph(payload)
        metadata = self.template_store.save_template(
            name, comment, graph_data, template_id=str(template_id) if template_id else None
        )
        return metadata

    def save_template_as(self, payload, default_name=None):
        try:
            graph_data = self._normalize_graph(payload)
            window = webview.windows[0]
            suggested_name = str(default_name or "template").strip()
            if not suggested_name.lower().endswith(".json"):
                suggested_name += ".json"
            save_flag = getattr(webview, 'FileDialog', None).SAVE if hasattr(webview, 'FileDialog') else webview.SAVE_DIALOG
            result = window.create_file_dialog(
                save_flag,
                file_types=("Pyxis Template (*.json)", "Todos los archivos (*.*)"),
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
                "comment": "Guardado en archivo externo",
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
            print("Pyxis: error al guardar como archivo", error)
            raise ValueError(f"No se pudo guardar el archivo: {error}")

    def list_templates(self):
        return self.template_store.list_templates()

    def load_template(self, template_id):
        document = self.template_store.load_template(str(template_id))
        return {
            "metadata": document.get("metadata", {}),
            "graph": document["graph"],
        }

    def delete_template(self, template_id):
        self.template_store.delete_template(str(template_id))
        return True

    def toggle_favorite(self, template_id):
        return self.template_store.toggle_favorite(str(template_id))

    def export_template(self, template_id):
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
                file_types=("Pyxis Template (*.json)", "Todos los archivos (*.*)"),
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
            print("Pyxis: error al exportar template", error)
            return False

    def import_template(self):
        try:
            window = webview.windows[0]
            save_flag = getattr(webview, 'FileDialog', None).OPEN if hasattr(webview, 'FileDialog') else webview.OPEN_DIALOG
            result = window.create_file_dialog(
                save_flag,
                file_types=("Pyxis Template (*.json)", "Todos los archivos (*.*)"),
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
                raise ValueError("Formato de archivo inválido (debe ser un objeto JSON)")
            if "graph" in document and isinstance(document["graph"], dict):
                graph = document["graph"]
                metadata = document.get("metadata", {})
            elif "nodes" in document and isinstance(document["nodes"], list):
                graph = document
                metadata = {}
            else:
                raise ValueError("Formato de archivo inválido (no contiene nodos de grafo)")

            name = metadata.get("name") or os.path.splitext(os.path.basename(load_path))[0] or "Template Importado"
            comment = metadata.get("comment", "Importado desde archivo")
            new_metadata = self.template_store.save_template(name, comment, graph)
            return new_metadata
        except Exception as error:
            print("Pyxis: error al importar template", error)
            raise ValueError(f"No se pudo importar el template: {error}")

    def estimate_workload_api(self, graph_payload):
        """
        API invocada por el frontend para obtener una estimación instantánea (< 1ms)
        del total de líneas a generar y nivel de complejidad del grafo.
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
                return engine.estimate_workload(dialogues, styles, allow_fallback_select_all=True)
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
        """Cancela de forma inmediata y forzosa la generación activa en curso en cualquier hilo o subproceso."""
        print("[Pyxis] Cancelación solicitada por el usuario desde la UI.", flush=True)
        if getattr(self, '_active_engine', None) is not None:
            self._active_engine.is_cancelled = True
            if getattr(self._active_engine, 'shared_cancel_flag', None) is not None:
                try:
                    self._active_engine.shared_cancel_flag.value = True
                except Exception:
                    pass
        from node_engine import abort_global_multiprocessing
        abort_global_multiprocessing()
        return {"success": True, "cancelled": True}

    def complete_and_hide(self):
        """Oculta la ventana de PyWebView o apaga el servidor una vez completada la retención visual en la UI."""
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

    def process_graph(self, payload):
        try:
            graph_data = self._normalize_graph(payload)
            try:
                self.save_session(graph_data)
            except Exception as se:
                print(f"[Pyxis Warning] save_session no crítico: {se}", flush=True)

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

            # Escanear nodos para preprocesar y cachear archivos de audio antes de procesar
            for n in graph_data.get("nodes", []):
                n_type = str(n.get("type", ""))
                if "Audio" in n_type or "audio" in n_type.lower() or "Waveform" in n_type or "Modulador" in n_type:
                    node_audio = str(n.get("properties", {}).get("audio_path", "")).strip()
                    src_to_check = node_audio if node_audio else default_audio_source
                    if src_to_check:
                        try:
                            report_progress({"percent": 5, "phase": "Procesando..."})
                            wav_path = AudioPreprocessor.ensure_audio_wav(
                                src_to_check,
                                progress_callback=lambda msg: report_progress({"percent": 12, "phase": "Procesando..."})
                            )
                            report_progress({"percent": 18, "phase": "Procesando..."})
                            AudioEngine.load_wav(wav_path)
                            report_progress({"percent": 24, "phase": "Procesando..."})
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
                print("[Pyxis] Generación abortada por cancelación.", flush=True)
                return {"success": False, "cancelled": True, "lines_generated": 0}

            generated_count = len(generated_lines)
            with open(self.result_file, "w", encoding="utf-8") as result_file:
                result_file.writelines(generated_lines)
                result_file.flush()
                os.fsync(result_file.fileno())

            # Liberar lock_file para que Aegisub empiece a leer el resultado
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
        try:
            from img_tracer_engine import trace_image
            if not isinstance(node_props, dict):
                node_props = {}
            image_path = str(node_props.get("image_path", "")).strip()
            if not image_path or not os.path.exists(image_path):
                return {"shape": "", "width": 0, "height": 0, "points": 0}

            mode = str(node_props.get("modo", "Potrace")).strip()
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
            invert = invert_str.lower() in ["invertido", "invert", "true", "1", "si", "yes"]
            bin_mode = str(node_props.get("bin_mode", "Luminancia")).strip()
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
            use_inverted_img = invert_img_str.lower() in ["invertido", "invert", "true", "1", "si", "yes"]

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
        local_ffmpeg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe")
        if os.path.isfile(local_ffmpeg):
            return local_ffmpeg
        from shutil import which
        sys_ffmpeg = which("ffmpeg")
        if sys_ffmpeg:
            return sys_ffmpeg
        return "ffmpeg"

    @staticmethod
    def _shift_ass_timestamp(time_str: str, shift_ms: int) -> str:
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
        """Ajusta los campos Start y End de una línea Dialogue o Comment restando shift_ms."""
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
    def _clean_and_resolve_media_path(raw_path, base_ass_path=None):
        """Limpia prefijos de proyectos Aegisub (?video:, ?audio:, etc.) y resuelve rutas relativas/absolutas."""
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

        if base_ass_path and os.path.exists(base_ass_path):
            ass_dir = os.path.dirname(os.path.abspath(base_ass_path))
            rel = os.path.join(ass_dir, p)
            if os.path.isfile(rel):
                return os.path.abspath(rel)

        return None

    def _ensure_preview_media_clip(self, info, is_export=False):
        """Garantiza la presencia del clip de previsualización con vídeo y audio sincronizados en %APPDATA%/PyxisNodes/bg_media/.
        Si is_export es False (vista desde el nodo), se utiliza preset 'fast', crf '21' y deblocking reducido ('-1:-1').
        Si is_export es True (exportación de clip/video), se mantiene la máxima calidad con preset 'ultrafast' y crf '18'."""
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
            real_video = info.get("real_video_file")
            real_audio = info.get("real_audio_file")
            dummy_info = info.get("dummy_info") or {}
            color_hex = str(dummy_info.get("color_hex") or "969696").lower()

            ffmpeg_exe = self._find_ffmpeg()
            import subprocess
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) if os.name == 'nt' else 0

            # Diferenciación: Exportación (alta calidad) vs Vista en Nodo (rápido, crf 21, preset fast, deblock reducido)
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

            key_src = (
                f"v:{real_video}:{v_mtime}:{v_size}|"
                f"a:{real_audio}:{a_mtime}:{a_size}|"
                f"{clip_start_sec:.3f}:{clip_dur_sec:.3f}:{res_x}x{res_y}:{fps:.2f}:{color_hex}|"
                f"mode:{clip_prefix}:{v_preset}:{v_crf}"
            )
            hash_16 = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:16]
            clip_type = "real" if real_video else ("audio" if real_audio else "dummy")
            clip_filename = f"{clip_prefix}_{clip_type}_{hash_16}_{res_x}x{res_y}_{clip_start_sec:.2f}s_{clip_dur_sec:.2f}s.mp4"
            clip_path = os.path.join(bg_media_dir, clip_filename)

            if os.path.exists(clip_path) and os.path.getsize(clip_path) > 1024:
                return clip_path

            v_codec = ["-c:v", "libx264", "-preset", v_preset, "-crf", v_crf]
            if deblock_args:
                v_codec.extend(deblock_args)

            # Caso 1: Vídeo Real + Audio Real (Mismo archivo)
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
                    clip_path
                ]
            # Caso 2: Vídeo Real + Audio Real (Archivos Diferentes)
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
                    clip_path
                ]
            # Caso 3: Fondo Dummy + Audio Real
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
                    clip_path
                ]
            # Caso 4: Fondo Dummy + Audio Silencio (Fallback)
            else:
                cmd = [
                    ffmpeg_exe, "-y",
                    "-f", "lavfi", "-i", f"color=c=0x{color_hex}:s={res_x}x{res_y}:r={fps:.3f}:d={clip_dur_sec:.3f}",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    *v_codec,
                    "-tune", "stillimage",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "64k",
                    "-shortest",
                    "-movflags", "+faststart",
                    clip_path
                ]

            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creationflags)
            if proc.returncode == 0 and os.path.exists(clip_path):
                print(f"[Pyxis Smart Cache] Clip {clip_prefix} generado ({clip_type}): {clip_filename} ({clip_dur_sec:.2f}s)", flush=True)
                return clip_path
            else:
                print(f"[Pyxis FFmpeg Clip Error] {proc.stderr}", flush=True)

        except Exception as e:
            print(f"[Pyxis Error in _ensure_preview_media_clip] {e}", flush=True)

        return None

    def _matches_output_node(self, node, target_ids, all_salida_nodes=None):
        if not node:
            return False
        n_type = str(node.get('type', '')).lower()
        if 'salida' not in n_type and 'output' not in n_type:
            return False

        if not target_ids:
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

        if not target_strs or any(x.lower() in ('all', '*', 'todos', 'all_outputs', 'todas') for x in target_strs):
            return True

        nid_str = str(node.get('id', ''))
        nid_int = node.get('id')
        props = node.get('properties', {}) or {}
        out_id = str(props.get('output_id') or props.get('salida_id') or '').strip()
        queue_id = str(props.get('queue_id') or '').strip()

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
        if out_id and (out_id in target_strs or (_to_int_or_default(out_id, None) in numeric_targets)):
            return True
        if queue_id and (queue_id in target_strs or (_to_int_or_default(queue_id, None) in numeric_targets)):
            return True
        if 'default' in (x.lower() for x in target_strs) and (not out_id or out_id.lower() == 'default'):
            return True

        if all_salida_nodes and node in all_salida_nodes:
            idx_1based = all_salida_nodes.index(node) + 1
            if (str(idx_1based) in target_strs or 
                idx_1based in numeric_targets or 
                f"Salida {idx_1based}".lower() in (x.lower() for x in target_strs) or 
                f"Salida_{idx_1based}".lower() in (x.lower() for x in target_strs)):
                return True

        return False

    def _calculate_effective_dialogue_range(self, dialogues, payload=None, target_output_id=None):
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

        graph_data = self._normalize_graph(payload) if payload else {}
        nodes_dict = graph_data.get("nodes", {}) or {}
        if isinstance(nodes_dict, list):
            nodes_dict = {n.get("id"): n for n in nodes_dict if isinstance(n, dict)}

        all_salida_nodes = [n for n in nodes_dict.values() if 'salida' in str(n.get('type', '')).lower() or 'output' in str(n.get('type', '')).lower()]
        matching_salidas = [n for n in all_salida_nodes if self._matches_output_node(n, target_ids, all_salida_nodes)]

        use_all_lines = False
        use_style_lines = False
        target_styles = set()

        if matching_salidas:
            for s_node in matching_salidas:
                props = s_node.get('properties', {}) or {}
                apply_to = str(props.get('apply_to', 'Selected Lines')).strip().lower()
                if apply_to in ['all lines', 'todas las líneas', 'todas las lineas', 'all', 'todas']:
                    use_all_lines = True
                    break
                elif apply_to in ['style lines', 'líneas de estilo', 'lineas de estilo', 'style', 'estilo']:
                    use_style_lines = True
                    st_name = str(props.get('style', '') or props.get('estilo', '')).strip()
                    if st_name:
                        target_styles.add(st_name)
        elif not all_salida_nodes:
            use_all_lines = True

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
                st = d.get('start_time')
                et = d.get('end_time')
                is_sel = bool(d.get('is_selected', False) or (d.get('metrics') and d['metrics'].get('sel')))
                style_name = str(d.get('style_name', ''))
                if st is None or et is None:
                    raw = str(d.get('raw', ''))
                    if raw.startswith('Dialogue:') or raw.startswith('Dialogue :'):
                        fields = raw.split(',', 9)
                        if len(fields) >= 4:
                            st = self._parse_ass_time(fields[1])
                            et = self._parse_ass_time(fields[2])
                            style_name = fields[3].strip()
            elif hasattr(d, 'start_time') and hasattr(d, 'end_time'):
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
                        if raw.startswith('Dialogue:') or raw.startswith('Dialogue :'):
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
        self._cached_aegisub_info = None
        self._cached_aegisub_parsed = None
        self._aegisub_temp_hash = None
        self._aegisub_temp_mtime = None
        self._aegisub_temp_path = None

    def _load_and_cache_aegisub_source(self, payload=None, target_output_id=None, force_reload=False):
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

            real_video = None
            if not is_dummy_video:
                real_video = self._clean_and_resolve_media_path(video_file, self.temp_ass)

            real_audio = None
            if not is_dummy_audio:
                real_audio = self._clean_and_resolve_media_path(audio_file, self.temp_ass)

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
                "dummy_info": dummy_info,
                "font_name": primary_font_name,
                "font_size": primary_font_size,
            }

            clip_path = self._ensure_preview_media_clip(info_dict)
            info_dict["clip_path"] = clip_path

            self._cached_aegisub_info = info_dict
            return info_dict
        except Exception as e:
            print(f"[Pyxis Error in _load_and_cache_aegisub_source] {e}", flush=True)
            return {"has_aegisub": False, "source": "aegisub"}

    def get_preview_video_data_url(self, source="base", target_output_id=None, payload=None):
        try:
            info = self.get_preview_info(source=source, target_output_id=target_output_id, payload=payload)
            clip_path = info.get("clip_path") or self._ensure_preview_media_clip(info)
            if clip_path and os.path.exists(clip_path):
                import urllib.parse
                quoted_path = urllib.parse.quote(clip_path)
                return f"http://127.0.0.1:28723/media_file?path={quoted_path}"
        except Exception as e:
            print(f"[Pyxis Error getting preview video URL] {e}", flush=True)
        return "/bg_media/preview_bg_15s_23.98fps.mp4"

    def get_preview_audio_data_url(self, source="base", target_output_id=None, payload=None):
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

    def get_preview_info(self, source="base", target_output_id=None, payload=None):
        has_aegisub = bool(self.temp_ass and os.path.isfile(self.temp_ass))
        if str(source).lower() == "aegisub" and has_aegisub:
            info = self._load_and_cache_aegisub_source(payload=payload, target_output_id=target_output_id)
            if info.get("has_aegisub"):
                info["has_aegisub"] = True
                return info

        info = self._load_and_cache_preview_base()
        info["has_aegisub"] = has_aegisub
        info["source"] = "base"
        res_x = info.get("res_x", 1280)
        res_y = info.get("res_y", 720)
        aspect = info.get("aspect_ratio") or ((res_x / res_y) if res_y > 0 else (16 / 9))
        return {
            "source": info.get("source", "base"),
            "has_aegisub": has_aegisub,
            "res_x": res_x,
            "res_y": res_y,
            "aspect_ratio": aspect,
            "fps": info.get("fps", 23.976),
            "frame_dur": info.get("frame_dur", 41.708),
            "clip_start_sec": info.get("clip_start_sec", 0.0),
            "clip_end_sec": info.get("clip_end_sec", 15.0),
            "clip_duration_sec": info.get("clip_duration_sec", 15.0),
            "clip_start_ms": info.get("clip_start_ms", 0),
            "render_start_sec": info.get("render_start_sec", 0.0),
            "has_custom_video": bool(info.get("real_video_file")),
            "has_custom_audio": bool(info.get("real_audio_file")),
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
            "dialogues": info.get("dialogues", [])
        }

    def _get_temp_dir(self):
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        temp_dir = os.path.join(appdata_dir, "PyxisNodes", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def log_player_event(self, msg):
        try:
            log_path = os.path.join(self._get_temp_dir(), "player_debug.log")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}] {msg}\n")
            print(f"[PYXIS PLAYER LOG] {msg}", flush=True)
            return True
        except Exception as e:
            print(f"[Pyxis Log Error] {e}", flush=True)
            return False

    def _extract_font_data_from_gdi(self, font_name: str):
        """Extrae los bytes binarios puros del archivo de fuente (.ttf/.otf/.ttc) directamente
        desde la memoria GDI de Windows, compatible con fuentes instaladas, de FontBase,
        Adobe Type Manager o cargadas temporalmente."""
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
                        print(f"[Pyxis Font GDI] GDI seleccionó fallback '{selected_face}' para '{font_name}' (descartado)", flush=True)
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
                    print(f"[Pyxis Font GDI] ¡ÉXITO! Extraídos {read_b} bytes directamente de Windows GDI para '{font_name}' (Face: '{selected_face}')", flush=True)
                    return font_bytes, selected_face
            finally:
                user32.ReleaseDC(None, hdc)
        except Exception as e:
            print(f"[Pyxis Font GDI Error] {e}", flush=True)
        return None

    def _find_font_file(self, font_name: str):
        if not font_name:
            print("[Pyxis Font] _find_font_file llamado con nombre vacío", flush=True)
            return None
        
        font_name_clean = str(font_name).strip().lower()
        print(f"[Pyxis Font] Buscando archivo en el sistema para la fuente: '{font_name}' (limpio: '{font_name_clean}')", flush=True)

        # 0. Probar extracción binaria directa desde Windows GDI (cubre FontBase, NexusFont, fuentes cargadas en memoria)
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
                print(f"[Pyxis Font] Fuente de GDI guardada en caché: '{cached_file}'", flush=True)
                return cached_file
            except Exception as e:
                print(f"[Pyxis Font Cache Error] {e}", flush=True)

        candidates_from_reg = []
        
        # 1. Escanear registro de fuentes de Windows (HKCU y HKLM)
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
                            print(f"[Pyxis Font] Coincidencia EXACTA en {root_name} Fonts: '{reg_name}' -> '{reg_val}'", flush=True)
                        elif font_name_clean in clean_reg:
                            candidates_from_reg.append(reg_val)
                            print(f"[Pyxis Font] Coincidencia parcial en {root_name} Fonts: '{reg_name}' -> '{reg_val}'", flush=True)
                    winreg.CloseKey(key)
                except Exception as e:
                    print(f"[Pyxis Font] Error leyendo registro {root_name}: {e}", flush=True)
        except Exception as e:
            print(f"[Pyxis Font] Excepción general escaneando registro: {e}", flush=True)

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
        print(f"[Pyxis Font] Directorios de búsqueda de fuentes: {search_dirs}", flush=True)

        # 2. Probar candidatos obtenidos del Registro
        for val in candidates_from_reg:
            if os.path.isabs(val) and os.path.exists(val):
                print(f"[Pyxis Font] ¡ENCONTRADA vía registro (ruta absoluta)! '{font_name}' -> '{val}'", flush=True)
                return val
            for s_dir in search_dirs:
                if s_dir and os.path.isdir(s_dir):
                    p = os.path.join(s_dir, val)
                    if os.path.exists(p):
                        print(f"[Pyxis Font] ¡ENCONTRADA vía registro en carpeta! '{font_name}' -> '{p}'", flush=True)
                        return p

        # 3. Búsqueda directa por coincidencia de nombre de archivo
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
                        print(f"[Pyxis Font] ¡ENCONTRADA por nombre directo! '{font_name}' -> '{p}'", flush=True)
                        return p
                try:
                    for fn in os.listdir(s_dir):
                        fn_lower = fn.lower()
                        if clean_nosp in fn_lower and any(fn_lower.endswith(ext) for ext in ['.ttf', '.otf', '.ttc']):
                            p = os.path.join(s_dir, fn)
                            print(f"[Pyxis Font] ¡ENCONTRADA por búsqueda difusa de archivo! '{font_name}' -> '{p}'", flush=True)
                            return p
                except Exception as e:
                    print(f"[Pyxis Font] Error listando directorio {s_dir}: {e}", flush=True)

        # 4. Fallback a Arial en directorios de fuentes
        print(f"[Pyxis Font] AVISO: No se encontró archivo específico para '{font_name}'. Recurriendo a Arial...", flush=True)
        for s_dir in search_dirs:
            if s_dir and os.path.isdir(s_dir):
                for af in ["arial.ttf", "Arial.ttf", "ARIAL.TTF"]:
                    p = os.path.join(s_dir, af)
                    if os.path.exists(p):
                        print(f"[Pyxis Font] Fallback a Arial resuelto en: '{p}'", flush=True)
                        return p
        print(f"[Pyxis Font] ERROR: Ni siquiera se encontró Arial en {search_dirs}", flush=True)
        return None

    def get_preview_fonts_map(self, source="base"):
        """Retorna un diccionario { nombre_fuente: { 'data': data_url, 'http_url': url, 'path': path } } con todas las fuentes requeridas."""
        font_map = {}
        try:
            info = self.get_preview_info(source=source)
            styles = info.get("styles", {}) or {}
            print(f"[Pyxis Font] get_preview_fonts_map invocado para fuente '{source}'. Estilos disponibles en ASS: {list(styles.keys())}", flush=True)
            requested_fonts = set()
            for s_name, s in styles.items():
                if isinstance(s, dict):
                    fn = s.get("Fontname") or s.get("fontname")
                    print(f"[Pyxis Font] Estilo '{s_name}' usa fuente: '{fn}'", flush=True)
                    if fn:
                        requested_fonts.add(str(fn).strip())
            
            primary_fn = str(info.get("font_name") or "Arial").strip()
            print(f"[Pyxis Font] Fuente primaria detectada de la línea activa: '{primary_fn}'", flush=True)
            if primary_fn:
                requested_fonts.add(primary_fn)
            if not requested_fonts:
                requested_fonts.add("Arial")

            print(f"[Pyxis Font] Conjunto total de fuentes a resolver: {requested_fonts}", flush=True)
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
                    print(f"[Pyxis Font] ERROR: No se pudo resolver archivo físico para '{fn}'", flush=True)
        except Exception as e:
            print(f"[Pyxis Error getting preview fonts map] {e}", flush=True)
        print(f"[Pyxis Font] Mapa final de fuentes generado con {len(font_map)} claves.", flush=True)
        return font_map

    def get_preview_font_data_url(self, source="base"):
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
        self._cached_preview_base_info = None
        self._preview_base_hash = None

    def ensure_preview_base_ass(self):
        """Garantiza la presencia de preview_base.ass en %APPDATA%/PyxisNodes/preview_base.ass.
        Si ya existe, respeta y preserva intactas todas las modificaciones manuales del usuario.
        Si NO existe, copia la plantilla maestra desde PyxisNodes/preview_base.ass por primera vez.
        """
        try:
            appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            pyxis_user_dir = os.path.join(appdata_dir, "PyxisNodes")
            os.makedirs(pyxis_user_dir, exist_ok=True)
            user_base_path = os.path.join(pyxis_user_dir, "preview_base.ass")
            master_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview_base.ass")

            if os.path.exists(user_base_path):
                return user_base_path
            elif os.path.exists(master_path):
                import shutil
                shutil.copyfile(master_path, user_base_path)
                print(f"[Pyxis] Copia inicial realizada de preview_base.ass master -> {user_base_path}", flush=True)
                return user_base_path
        except Exception as e:
            print(f"[Pyxis Error in ensure_preview_base_ass] {e}", flush=True)
        return None

    @staticmethod
    def _parse_ass_time(t_str: str) -> int:
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
        """Escanea preview_base.ass y almacena el resultado en memoria. Compara hash SHA-256 para recargar de forma infalible ante cualquier edición, restpyxisción o reemplazo del archivo."""
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
                "dummy_info": dummy_info,
                "font_name": primary_font_name,
                "font_size": primary_font_size,
            }

            clip_path = self._ensure_preview_media_clip(info_dict)
            info_dict["clip_path"] = clip_path

            self._cached_preview_base_info = info_dict
            print(f"[Pyxis Scan] preview_base.ass cargado: Res={res_x}x{res_y} ({res_x/res_y:.3f}), Diálogos={len(dialogues)}, Clip={clip_start_sec:.2f}s a {clip_end_sec:.2f}s ({clip_duration_sec:.2f}s)", flush=True)
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
                        output.append(self._shift_ass_line(line, clip_start_ms))
                    else:
                        output.append(line)
                return "".join(output)
        except Exception as e:
            print(f"[Pyxis Error reading initial ASS source={source}] {e}", flush=True)
        return ""

    def generate_preview_ass(self, payload, target_output_id=None, out_filename="preview_dummy.ass", preview_res_x=None, preview_res_y=None, source="base"):
        try:
            info = self.get_preview_info(source=source, target_output_id=target_output_id, payload=payload)
            res_x = preview_res_x if preview_res_x is not None else info.get("res_x", 1280)
            res_y = preview_res_y if preview_res_y is not None else info.get("res_y", 720)
            styles = info.get("styles", {})
            dialogues = info.get("dialogues", [])
            frame_dur = info.get("frame_dur", 41.708)
            clip_start_ms = info.get("clip_start_ms", 0)
            ass_path = info.get("path") or (self.ensure_preview_base_ass() if source == "base" else None)

            self.log_player_event(f"generate_preview_ass source={source} called with target_output_id: {target_output_id}, res: {res_x}x{res_y}, shift_ms: {clip_start_ms}")
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
            if ass_path and os.path.exists(ass_path):
                generated_lines = []
                if len(output_id_list) > 0:
                    engine = GraphEngine(graph_data, res_x, res_y, frame_dur, default_audio_source=default_audio)
                    engine.target_output_id = output_id_list
                    generated_lines = engine.process(dialogues, styles)
                    self.log_player_event(f"GraphEngine targets={output_id_list} (Res {res_x}x{res_y}) produced {len(generated_lines)} lines")

                with open(ass_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                    base_lines = f.readlines()

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
                
                all_salida_nodes = [n for n in nodes_dict.values() if 'salida' in str(n.get('type', '')).lower() or 'output' in str(n.get('type', '')).lower()]
                matching_salidas = [n for n in all_salida_nodes if self._matches_output_node(n, output_id_list, all_salida_nodes)]
                
                use_all_lines = False
                use_style_lines = False
                target_styles = set()
                for s_node in matching_salidas:
                    props = s_node.get('properties', {}) or {}
                    app = str(props.get('apply_to', 'Selected Lines')).strip().lower()
                    if app in ['all lines', 'todas las líneas', 'todas las lineas', 'all', 'todas']:
                        use_all_lines = True
                        break
                    elif app in ['style lines', 'líneas de estilo', 'lineas de estilo', 'style', 'estilo']:
                        use_style_lines = True
                        st_name = str(props.get('style', '') or props.get('estilo', '')).strip()
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
                            output_ass_lines.append(self._shift_ass_line(line, clip_start_ms))
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
                                output_ass_lines.append(self._shift_ass_line(comment_line, clip_start_ms))
                            else:
                                output_ass_lines.append(self._shift_ass_line(line, clip_start_ms))
                            last_was_selected_metric = False
                        elif is_comm:
                            output_ass_lines.append(self._shift_ass_line(line, clip_start_ms))
                        else:
                            output_ass_lines.append(line)

                if len(generated_lines) > 0:
                    for g_line in generated_lines:
                        output_ass_lines.append(self._shift_ass_line(g_line, clip_start_ms))

                full_ass_content = "".join(output_ass_lines)
            else:
                self.log_player_event("ass_path missing!")
                full_ass_content = ""

            self.log_player_event(f"generate_preview_ass finished, total ASS length: {len(full_ass_content)}")
            return {"success": True, "content": full_ass_content}
        except Exception as err:
            self.log_player_event(f"[Pyxis Error in generate_preview_ass] {err}")
            return {"success": False, "error": str(err)}

    def _select_save_video_path(self, default_filename="hardsub_clip.mp4"):
        try:
            if hasattr(webview, "windows") and webview.windows:
                window = webview.windows[0]
                save_flag = getattr(webview, 'FileDialog', None).SAVE if hasattr(webview, 'FileDialog') else webview.SAVE_DIALOG
                result = window.create_file_dialog(
                    save_flag,
                    save_filename=default_filename,
                    file_types=("Vídeo MP4 (*.mp4)", "Todos los archivos (*.*)"),
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
                title="Guardar Clip de Vídeo Hardsub",
                defaultextension=".mp4",
                initialfile=default_filename,
                filetypes=[("Vídeo MP4", "*.mp4"), ("Todos los archivos", "*.*")]
            )
            root.destroy()
            return file_path if file_path else None
        except Exception as e:
            print("[Pyxis tkinter save dialog warning]", e, flush=True)
            return None

    def render_preview_hardsub(self, payload, target_output_id=None, out_filename=None, source="base"):
        try:
            import time
            info = self.get_preview_info(source=source, target_output_id=target_output_id, payload=payload)
            clock_num = int(time.time() * 1000) % 1000000
            output_tag = f"multi_{len(target_output_id)}" if isinstance(target_output_id, list) else (target_output_id or "dummy")
            default_fn = out_filename or f"Mi_efecto_{clock_num:06d}.mp4"

            save_path = self._select_save_video_path(default_filename=default_fn)
            if not save_path:
                return {"success": False, "cancelled": True, "message": "Renderizado cancelado por el usuario"}

            ass_filename = f"preview_dummy_{output_tag}.ass"
            gen_res = self.generate_preview_ass(payload, target_output_id=target_output_id, out_filename=ass_filename, source=source)
            appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            pyxis_dir = os.path.join(appdata_dir, "PyxisNodes")
            temp_dir = os.path.join(pyxis_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            preview_ass_path = os.path.join(temp_dir, ass_filename)

            if isinstance(gen_res, dict) and gen_res.get("content"):
                with open(preview_ass_path, "w", encoding="utf-8") as f:
                    f.write(gen_res["content"])

            clip_path = self._ensure_preview_media_clip(info, is_export=True)
            if not clip_path or not os.path.exists(clip_path):
                return {"success": False, "error": "No se pudo generar ni localizar el clip de fondo para renderizar Hardsub"}

            ffmpeg_exe = self._find_ffmpeg()

            cmd = [
                ffmpeg_exe, "-y",
                "-i", clip_path,
                "-vf", f"subtitles='{ass_filename}'",
                "-c:v", "libx264",
                "-preset", "slow",
                "-crf", "15",
                "-tune", "animation",
                "-pix_fmt", "yuv420p",
                "-maxrate", "25M",
                "-bufsize", "25M",
                "-rc-lookahead", "40",
                "-c:a", "copy",
                "-movflags", "+faststart",
                save_path
            ]

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

    def shutdown_daemon(self):
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
        graph_data = payload if isinstance(payload, dict) else json.loads(payload)
        if "nodes" not in graph_data and "graph" in graph_data:
            graph_data = graph_data["graph"]
        if not isinstance(graph_data, dict):
            raise ValueError("El grafo debe ser un objeto JSON")
        if not isinstance(graph_data.get("nodes"), list):
            raise ValueError("El grafo debe contener una lista de nodos")
        if "links" in graph_data and not isinstance(graph_data["links"], list):
            raise ValueError("Los enlaces deben ser una lista")
        return graph_data


def main():
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

    # Comprobar si el Daemon en segundo plano ya está corriendo
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
            # Notificado con éxito, salir inmediatamente (Apertura 0ms)
            sys.exit(0)

    try:
        api = PyxisAPI(temp_ass, result_file, session_file, aegisub_version, lock_file=lock_file)
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

        window = webview.create_window(
            title=f"Pyxis Node Engine {PYXIS_ENGINE_VERSION}",
            url=html_url,
            js_api=api,
            width=init_width,
            height=init_height,
            background_color="#121212",
        )

        if isinstance(saved_win_state, dict):
            api._saved_window_state = dict(saved_win_state)
            if saved_win_state.get("maximized"):
                def _on_window_shown():
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
                return True
            api._is_handling_closing = True

            # Abortar y cancelar cualquier proceso en ejecución inmediatamente
            try:
                api.cancel_generation()
            except Exception:
                pass

            # Liberar siempre de forma prioritaria el lock de la sesión activa
            try:
                api.release_lock()
            except Exception:
                pass

            # Capturar formato y dimensiones actuales de la ventana de forma robusta
            try:
                import ctypes
                from ctypes import wintypes
                user32 = ctypes.windll.user32
                my_pid = os.getpid()
                found_hwnd = None
                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                def enum_cb(h, l):
                    nonlocal found_hwnd
                    lp = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(h, ctypes.byref(lp))
                    if lp.value == my_pid:
                        length = user32.GetWindowTextLengthW(h)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            user32.GetWindowTextW(h, buff, length + 1)
                            if "Pyxis" in buff.value or "Engine" in buff.value:
                                found_hwnd = h
                                return False
                    return True
                user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
                if not found_hwnd:
                    found_hwnd = user32.FindWindowW(None, window.title)

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
            except Exception:
                pass

            config = api.get_user_config()
            is_daemon = config.get("daemon_mode", True)

            if is_daemon:
                try:
                    window.hide()
                except Exception:
                    pass
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

        window.events.closing += on_closing
        webview.settings['OPEN_DEVTOOLS_IN_DEBUG'] = False
        webview.start(debug=True, http_server=True)
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

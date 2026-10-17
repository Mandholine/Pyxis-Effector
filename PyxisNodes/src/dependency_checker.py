# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc and Pyxis Effector contributors
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

"""Preflight dependency checker and one-time verification system for Pyxis Node Engine.

Windows: enforces Microsoft Edge WebView2 Runtime, blocks deprecated MSHTML (Internet Explorer).
Linux/macOS: verifies that a pywebview GUI backend (WebKitGTK or Qt WebEngine) is available.
Persists the validation state in %APPDATA%/PyxisNodes/user_config.json (XDG dirs on POSIX).
"""

import ctypes
import json
import logging
import os
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime

if sys.platform == "win32":
    import winreg
else:
    winreg = None

logger = logging.getLogger("pyxis.dependency_checker")

WEBVIEW2_RUNTIME_GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
WEBVIEW2_BOOTSTRAPPER_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
MIN_DOTNET_RELEASE = 394802  # .NET Framework 4.6.2


def check_dotnet_installed() -> tuple[bool, int]:
    """Verifies that .NET Framework 4.6.2 or higher is installed."""
    if winreg is None:
        return True, 0
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full"
        ) as key:
            release, _ = winreg.QueryValueEx(key, "Release")
            return int(release) >= MIN_DOTNET_RELEASE, int(release)
    except Exception as e:
        logger.warning("Failed to query .NET Framework release version: %s", e)
        return False, 0


def check_webview2_installed() -> tuple[bool, str]:
    """Checks the Windows Registry for Microsoft Edge WebView2 Runtime."""
    if winreg is None:
        return True, "n/a"
    candidate_paths = [
        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_RUNTIME_GUID}"),
        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_RUNTIME_GUID}"),
        (winreg.HKEY_CURRENT_USER, rf"SOFTWARE\Microsoft\EdgeUpdate\Clients\{WEBVIEW2_RUNTIME_GUID}"),
    ]

    for root_key, subkey in candidate_paths:
        try:
            with winreg.OpenKey(root_key, subkey) as reg_key:
                pv, _ = winreg.QueryValueEx(reg_key, "pv")
                pv_str = str(pv).strip()
                if pv_str and pv_str != "0.0.0.0" and pv_str != "0":
                    return True, pv_str
        except Exception:
            continue

    # Fallback: check if Edge browser Canary/Dev/Beta channels are present as valid WebView2 host
    channel_guids = [
        "{2CD8A007-E189-409D-A2C8-9AF4EF3C72AA}",  # Beta
        "{0D50BFEC-CD6A-4F9A-964C-C7416E3ACB10}",  # Dev
        "{65C35B14-6C1D-4122-AC46-7148CC9D6497}",  # Canary
    ]
    for ch_guid in channel_guids:
        for root_key, prefix in [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\EdgeUpdate\Clients"),
        ]:
            try:
                with winreg.OpenKey(root_key, rf"{prefix}\{ch_guid}") as reg_key:
                    pv, _ = winreg.QueryValueEx(reg_key, "pv")
                    pv_str = str(pv).strip()
                    if pv_str and pv_str != "0.0.0.0" and pv_str != "0":
                        return True, pv_str
            except Exception:
                continue

    return False, ""


def get_cached_dependency_status(config_path: str) -> dict | None:
    """Retrieves the cached dependency validation result from user_config.json."""
    if not config_path or not os.path.exists(config_path):
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            status = data.get("dependency_check")
            if isinstance(status, dict):
                return status
    except Exception as e:
        logger.warning("Failed to read dependency cache from %s: %s", config_path, e)
    return None


def save_dependency_status(config_path: str, status: dict) -> bool:
    """Persists the verified dependency validation status into user_config.json."""
    if not config_path:
        return False
    try:
        os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
        data = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        data = loaded
            except Exception:
                data = {}

        data["dependency_check"] = status
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.warning("Failed to persist dependency status to %s: %s", config_path, e)
        return False


def _show_native_message(title: str, text: str, style: int = 0) -> int:
    """Displays a native dialog: MessageBox on Windows, osascript on macOS, zenity/kdialog/tkinter on Linux.

    On POSIX the dialog is informational only (the Windows-style button flags in ``style`` are ignored).
    The message is always mirrored to stderr and to the user's debug log, because Aegisub launches
    Python with its output discarded and a failed preflight would otherwise be invisible.
    """
    if sys.platform == "win32":
        try:
            user32 = ctypes.windll.user32
            return int(user32.MessageBoxW(0, text, title, style))
        except Exception:
            pass
        print(f"[{title}] {text}", file=sys.stderr)
        return 0

    print(f"[{title}] {text}", file=sys.stderr)
    try:
        from paths import get_user_data_dir
        log_dir = os.path.join(get_user_data_dir(), "temp")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "preflight_debug.log"), "a", encoding="utf-8") as log_file:
            log_file.write(f"[{datetime.now().isoformat()}] {title}\n{text}\n\n")
    except Exception:
        pass

    try:
        import shutil
        if sys.platform == "darwin":
            def _esc(value: str) -> str:
                return value.replace("\\", "\\\\").replace('"', '\\"')
            subprocess.run(
                ["osascript", "-e",
                 f'display dialog "{_esc(text)}" with title "{_esc(title)}" buttons {{"OK"}} default button "OK" with icon stop'],
                capture_output=True, timeout=600,
            )
        elif shutil.which("zenity"):
            subprocess.run(["zenity", "--error", "--no-markup", f"--title={title}", f"--text={text}"],
                           capture_output=True, timeout=600)
        elif shutil.which("kdialog"):
            subprocess.run(["kdialog", "--title", title, "--error", text], capture_output=True, timeout=600)
        else:
            import tkinter
            from tkinter import messagebox
            root = tkinter.Tk()
            root.withdraw()
            messagebox.showerror(title, text, parent=root)
            root.destroy()
    except Exception:
        pass
    return 0


def install_webview2_bootstrapper(interactive: bool = True) -> bool:
    """Downloads and executes Microsoft's official WebView2 Evergreen Bootstrapper."""
    MB_YESNO = 0x00000004
    MB_ICONQUESTION = 0x00000020
    IDYES = 6

    if interactive:
        prompt_title = "Pyxis Effector — Requisito de Sistema"
        prompt_text = (
            "Pyxis Effector requiere Microsoft Edge WebView2 Runtime para renderizar su lienzo "
            "visual acelerado y el previsualizador WebAssembly.\n\n"
            "El componente no se encuentra instalado en tu sistema.\n\n"
            "¿Deseas descargar e instalar el componente oficial de Microsoft ahora? (~2 MB)"
        )
        resp = _show_native_message(prompt_title, prompt_text, MB_YESNO | MB_ICONQUESTION)
        if resp != IDYES:
            logger.info("User declined WebView2 installation.")
            return False

    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, "MicrosoftEdgeWebview2Setup.exe")

    try:
        logger.info("Downloading WebView2 bootstrapper from %s", WEBVIEW2_BOOTSTRAPPER_URL)
        urllib.request.urlretrieve(WEBVIEW2_BOOTSTRAPPER_URL, installer_path)
    except Exception as e:
        error_msg = f"No se pudo descargar el instalador de WebView2: {e}\nPor favor comprueba tu conexión a Internet."
        _show_native_message("Pyxis Effector — Error de Descarga", error_msg, 0x00000010)
        return False

    try:
        logger.info("Executing WebView2 installer: %s", installer_path)
        # Execute bootstrapper with /silent /install flag for seamless background installation
        proc = subprocess.run([installer_path, "/silent", "/install"], capture_output=True, timeout=300)
        # If silent returned non-zero, retry standard interactive execution
        if proc.returncode != 0:
            subprocess.run([installer_path, "/install"], capture_output=True, timeout=300)
    except Exception as e:
        logger.error("Error executing WebView2 setup: %s", e)
    finally:
        try:
            if os.path.exists(installer_path):
                os.remove(installer_path)
        except OSError:
            pass

    # Verify if installation succeeded
    installed, version = check_webview2_installed()
    if installed:
        logger.info("WebView2 successfully installed (version: %s)", version)
        _show_native_message(
            "Pyxis Effector",
            f"Microsoft Edge WebView2 Runtime ({version}) se instaló correctamente.\nPyxis se iniciará ahora.",
            0x00000040,
        )
        return True

    _show_native_message(
        "Pyxis Effector — Instalación Incompleta",
        "La instalación de WebView2 no pudo completarse.\n"
        "Pyxis no puede iniciarse sin este componente ya que el motor antiguo (Internet Explorer) está bloqueado.\n\n"
        "Puedes instalarlo manualmente desde: https://developer.microsoft.com/en-us/microsoft-edge/webview2/",
        0x00000010,
    )
    return False


def _check_posix_gui_backend() -> tuple[bool, str, str]:
    """Verifica que exista un backend gráfico usable por pywebview en Linux/macOS.

    Devuelve (ok, backend, detalle). Prefiere GTK + WebKit2GTK, luego Qt WebEngine.
    """
    # macOS usa Cocoa nativo (siempre disponible en pywebview)
    if sys.platform == "darwin":
        try:
            import AppKit  # noqa: F401  (pyobjc, instalado con pywebview)
            import WebKit  # noqa: F401
            return True, "cocoa", "Cocoa"
        except Exception:
            return False, "", (
                "Faltan los bindings de Cocoa para la interfaz de Pyxis (pyobjc).\n\n"
                "Reinstala el motor de Pyxis desde GitHub Releases, o ejecuta:\n"
                "  python3 -m pip install -r requirements.txt"
            )

    # GTK + WebKit2GTK (backend 'gtk' de pywebview)
    try:
        import gi
        for webkit_ver in ("4.1", "4.0"):
            try:
                gi.require_version("WebKit2", webkit_ver)
                from gi.repository import WebKit2  # noqa: F401
                return True, "gtk", f"WebKit2GTK {webkit_ver}"
            except Exception:
                continue
    except Exception:
        pass

    # Qt WebEngine (backend 'qt' de pywebview)
    for qt_mod in ("PyQt6", "PySide6", "PyQt5"):
        try:
            __import__(f"{qt_mod}.QtWebEngineWidgets")
            return True, "qt", qt_mod
        except Exception:
            continue

    return False, "", (
        "No se encontró ningún backend gráfico para la interfaz de Pyxis.\n\n"
        "Instala una de estas dependencias según tu distribución:\n"
        "  • GTK (recomendado): python3-gi, gir1.2-webkit2-4.1 (Debian/Ubuntu)\n"
        "    o python-gobject, webkit2gtk-4.1 (Arch/Fedora)\n"
        "  • Qt: python3-pyqt6.qtwebengine / python3-pyqt5.qtwebengine (Debian/Ubuntu)\n"
        "    o python-pyqt6-webengine (Arch)\n\n"
        "Además necesita: python3-tk (diálogos de archivo de respaldo)."
    )


def ensure_dependencies(config_path: str, interactive: bool = True) -> bool:
    """Performs the one-time dependency check with persistent caching.

    Windows: enforces EdgeChromium (WebView2) and blocks Internet Explorer.
    Linux/macOS: verifies a pywebview GUI backend (WebKitGTK / Qt WebEngine).
    Returns True if environment is valid, False otherwise.
    """
    if sys.platform != "win32":
        # 1. Quick Cache Check
        cached = get_cached_dependency_status(config_path)
        if cached and cached.get("verified") is True:
            return True

        ok, backend, detail = _check_posix_gui_backend()
        if not ok:
            _show_native_message("Pyxis Effector — Requisito no cumplido", detail, 0x00000010)
            return False

        status_record = {
            "verified": True,
            "gui_backend": backend,
            "gui_detail": detail,
            "last_checked": datetime.now().isoformat(),
        }
        save_dependency_status(config_path, status_record)
        return True

    # 1. Quick Cache Check: 0 ms overhead on subsequent launches
    cached = get_cached_dependency_status(config_path)
    if cached and cached.get("verified") is True:
        # Fast confirmation: ensure registry key was not deleted by user debloat
        installed, version = check_webview2_installed()
        if installed:
            return True

    # 2. Verify .NET Framework
    dotnet_ok, dotnet_release = check_dotnet_installed()
    if not dotnet_ok:
        _show_native_message(
            "Pyxis Effector — Requisito no cumplido",
            f"Pyxis Effector requiere Microsoft .NET Framework 4.6.2 o superior (detectado release: {dotnet_release}).\n"
            "Por favor actualiza .NET Framework para poder ejecutar Pyxis.",
            0x00000010,
        )
        return False

    # 3. Verify WebView2 Runtime
    wv2_ok, wv2_version = check_webview2_installed()
    if not wv2_ok:
        logger.warning("Microsoft Edge WebView2 Runtime is missing. Triggering installer.")
        if not install_webview2_bootstrapper(interactive=interactive):
            return False
        wv2_ok, wv2_version = check_webview2_installed()
        if not wv2_ok:
            return False

    # 4. Save persistent verified status to AppData
    status_record = {
        "verified": True,
        "webview2_version": wv2_version,
        "dotnet_release": dotnet_release,
        "last_checked": datetime.now().isoformat(),
    }
    save_dependency_status(config_path, status_record)
    return True

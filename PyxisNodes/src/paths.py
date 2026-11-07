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

"""
Module: paths.py
Architectural Role: Canonical absolute path manager and binary/asset resolution engine.

Upstream Dependencies:
    - os, shutil, sys: Standard library modules for filesystem inspection and PATH searches.

Downstream Callers:
    - main.py: Resolves web GUI, bundled templates and preview ASS base files.
    - dependency_checker.py: Verifies presence of auxiliary system executables.
    - img_tracer_engine.py: Resolves potrace.exe binary.
    - audio_engine.py / audio_preprocessor.py: Resolves ffmpeg.exe binary.
    - template_store.py: Accesses templates/ directory and preset serialisation.
    - pyxis_daemon.py: Resolves execution root directory and IPC sockets.

Side Effects and State:
    - Passive filesystem inspection via os.path.exists() and shutil.which().
    - Invariant: Always returns normalised canonical absolute paths, avoiding
      relative current working directory (CWD) pitfalls in frozen environments or Aegisub automation.
"""

import os
import shutil
import sys

IS_WINDOWS = os.name == "nt"
IS_MACOS = sys.platform == "darwin"


def ensure_tool_path() -> None:
    """
    Ensures standard CLI tool directories (e.g. Homebrew, MacPorts) are in PATH on macOS.
    """
    if not IS_MACOS:
        return
    current_path = os.environ.get("PATH", "")
    existing_paths = current_path.split(os.path.pathsep) if current_path else []
    extra_dirs = [
        "/opt/homebrew/bin",
        "/opt/homebrew/sbin",
        "/usr/local/bin",
    ]
    to_add = [d for d in extra_dirs if os.path.isdir(d) and d not in existing_paths]
    if to_add:
        os.environ["PATH"] = current_path + (os.path.pathsep if current_path else "") + os.path.pathsep.join(to_add)


ensure_tool_path()

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PYXIS_ROOT_DIR = os.path.dirname(SRC_DIR)
BIN_DIR = os.path.join(PYXIS_ROOT_DIR, "bin")
WEB_DIR = os.path.join(PYXIS_ROOT_DIR, "web")
DOCS_DIR = os.path.join(PYXIS_ROOT_DIR, "docs")
TEMPLATES_DIR = os.path.join(PYXIS_ROOT_DIR, "templates")
PREVIEW_BASE_ASS = os.path.join(PYXIS_ROOT_DIR, "preview_base.ass")


def get_user_data_dir() -> str:
    """
    Resolves the canonical user data directory across platforms.

    On Windows: %APPDATA%/PyxisNodes (with fallback to ~/PyxisNodes).
    On POSIX (Linux/macOS): $XDG_DATA_HOME/PyxisNodes or ~/.local/share/PyxisNodes.

    Returns:
        str: Normalised path to the Pyxis user data directory.
    """
    if IS_WINDOWS:
        appdata = os.environ.get("APPDATA")
        if appdata:
            return os.path.join(appdata, "PyxisNodes")
        return os.path.join(os.path.expanduser("~"), "PyxisNodes")

    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return os.path.join(xdg_data, "PyxisNodes")
    return os.path.join(os.path.expanduser("~"), ".local", "share", "PyxisNodes")


def get_bin_path(binary_name: str) -> str:
    """
    Resolves the absolute path to an executable binary using a 3-tier fallback strategy.

    Search Strategy:
        1. Isolated bin/ directory (standard Pyxis distribution).
        2. PyxisNodes root folder (legacy or portable environments without bin/).
        3. Operating system global PATH (shutil.which).
        4. Default fallback to bin/<target_name> if not found.

    Args:
        binary_name (str): Base name of the binary (e.g. 'ffmpeg', 'potrace', 'libass_profiler').
                           On Windows, automatically ensures the '.exe' extension.
                           On POSIX, strips '.exe' if passed and searches clean name.

    Returns:
        str: Resolved absolute path towards the executable file or expected target.

    Dependencies & Couplings:
        - Called by img_tracer_engine.py for potrace.
        - Called by audio_engine.py for ffmpeg.
        - Called by ass_telemetry_engine.py for libass_profiler.
    """
    if IS_WINDOWS:
        clean_name = binary_name[:-4] if binary_name.lower().endswith(".exe") else binary_name
        target_name = f"{clean_name}.exe"
    else:
        target_name = binary_name[:-4] if binary_name.lower().endswith(".exe") else binary_name

    # 1. Search in bin/
    bin_target = os.path.join(BIN_DIR, target_name)
    if os.path.exists(bin_target):
        return bin_target

    # 2. Search in PyxisNodes root
    root_target = os.path.join(PYXIS_ROOT_DIR, target_name)
    if os.path.exists(root_target):
        return root_target

    # 3. Search in user data directory (e.g. %APPDATA%/PyxisNodes/bin/ or ~/.local/share/PyxisNodes/bin/)
    try:
        user_data_dir = get_user_data_dir()
        user_bin_target = os.path.join(user_data_dir, "bin", target_name)
        if os.path.exists(user_bin_target):
            return user_bin_target
        user_root_target = os.path.join(user_data_dir, target_name)
        if os.path.exists(user_root_target):
            return user_root_target
    except Exception:
        pass

    # 4. Search in system PATH
    system_path = shutil.which(target_name)
    if system_path:
        return system_path

    # Fallback to bin/ target
    return bin_target


def get_web_path(resource: str = "") -> str:
    """
    Returns the absolute path to the frontend resource directory (web/) or an internal asset.

    Args:
        resource (str, optional): Subpath relative to web/ (e.g. 'index.html', 'i18n.js').
                                  If empty, returns the root path of the web/ directory.

    Returns:
        str: Normalised absolute path to the requested web resource.

    Dependencies & Couplings:
        - Called by main.py to initialise the URL/file loaded by PyWebView.
        - Called by pyxis_daemon.py to serve static assets via HTTP where applicable.
    """
    if resource:
        return os.path.join(WEB_DIR, resource)
    return WEB_DIR


def get_docs_path(resource: str = "") -> str:
    """
    Returns the absolute path to the technical manual directory (docs/) or an internal chapter.

    Args:
        resource (str, optional): Subpath relative to docs/ (e.g. 'en/03 Basics.md', 'img/banner.png').
                                  If empty, returns the root path of the docs/ directory.

    Returns:
        str: Normalised absolute path to the requested technical document.

    Dependencies & Couplings:
        - Called by help_viewer.js and main.py to serve the offline manual in the UI.
    """
    if resource:
        return os.path.join(DOCS_DIR, resource)
    return DOCS_DIR


def get_templates_path(resource: str = "") -> str:
    """
    Returns the absolute path to the templates directory (templates/) or a preset file.

    Args:
        resource (str, optional): Preset template filename (e.g. 'default.json').
                                  If empty, returns the path of the templates/ directory.

    Returns:
        str: Normalised absolute path to the requested template.

    Dependencies & Couplings:
        - Called by template_store.py to list and load predefined system graphs.
    """
    if resource:
        return os.path.join(TEMPLATES_DIR, resource)
    return TEMPLATES_DIR


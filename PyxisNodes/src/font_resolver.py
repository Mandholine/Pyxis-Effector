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

"""Resolución de fuentes del sistema a archivos .ttf/.otf/.ttc (fontconfig en POSIX).

Provee resolución de nombres de familia tipográfica (p. ej. "Arial") a rutas de
archivo, para que los motores de métrica (FreeType/PIL) funcionen en Linux/macOS
de la misma forma que Win32 GDI en Windows.
"""

import os
import shutil
import subprocess
import threading
from typing import Dict, List, Optional, Tuple

_FONT_EXTS = (".ttf", ".otf", ".ttc", ".otc")

_FONT_SEARCH_DIRS_POSIX = [
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    "/usr/share/fonts/truetype",
    "/usr/share/fonts/opentype",
    os.path.join(os.path.expanduser("~"), ".local", "share", "fonts"),
    os.path.join(os.path.expanduser("~"), ".fonts"),
]

_FILE_SCAN_CACHE: Dict[str, List[str]] = {}
_RESOLVE_CACHE: Dict[Tuple[str, bool, bool], Optional[str]] = {}
_CACHE_LOCK = threading.Lock()


def _norm(name: str) -> str:
    return str(name).strip().lower().replace(" ", "").replace("-", "").replace("_", "")


def _fc_match(font_name: str, bold: bool, italic: bool) -> Optional[str]:
    """Resuelve un nombre de familia vía fontconfig (fc-match), verificando la familia."""
    fc = shutil.which("fc-match")
    if not fc:
        return None
    props = ""
    if bold:
        props += ":bold"
    if italic:
        props += ":italic"
    query = f"{font_name}{props}"
    try:
        out = subprocess.run(
            [fc, "-f", "%{file}\\n%{family[0]}", query],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip().splitlines()
        if not out or not out[0]:
            return None
        file_path = out[0].strip()
        family = out[1].strip() if len(out) > 1 else ""
        if not os.path.isfile(file_path):
            return None
        # Verifica que la familia devuelta coincida razonablemente con la pedida.
        req = _norm(font_name)
        got = _norm(family)
        if req and got and req not in got and got not in req:
            return None
        return file_path
    except Exception:
        return None


def _fc_match_anyway(font_name: str) -> Optional[str]:
    """Fallback de fontconfig sin verificar familia (último recurso)."""
    fc = shutil.which("fc-match")
    if not fc:
        return None
    try:
        out = subprocess.run(
            [fc, "-f", "%{file}", font_name],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        return out if out and os.path.isfile(out) else None
    except Exception:
        return None


def _scan_dir_files(base_dir: str) -> List[str]:
    with _CACHE_LOCK:
        cached = _FILE_SCAN_CACHE.get(base_dir)
        if cached is not None:
            return cached
    found: List[str] = []
    try:
        for root, _dirs, files in os.walk(base_dir):
            for fn in files:
                if fn.lower().endswith(_FONT_EXTS):
                    found.append(os.path.join(root, fn))
    except Exception:
        pass
    with _CACHE_LOCK:
        _FILE_SCAN_CACHE[base_dir] = found
    return found


def _search_font_dirs(font_name: str, extra_dirs: Optional[List[str]] = None) -> Optional[str]:
    """Búsqueda directa y difusa por nombre de archivo en los directorios de fuentes."""
    req = _norm(font_name)
    if not req:
        return None
    dirs = list(extra_dirs or [])
    dirs.extend(_FONT_SEARCH_DIRS_POSIX)

    all_files: List[str] = []
    for d in dirs:
        if d and os.path.isdir(d):
            all_files.extend(_scan_dir_files(d))

    # 1. Coincidencia exacta de nombre de archivo (sin extensión)
    for p in all_files:
        base = os.path.splitext(os.path.basename(p))[0]
        if _norm(base) == req:
            return p

    # 2. Coincidencia difusa (prefiere fuentes cuyo nombre contenga el pedido)
    candidates = [p for p in all_files if req in _norm(os.path.splitext(os.path.basename(p))[0])]
    if candidates:
        # Prioriza variantes regulares sobre bold/italic cuando no se piden
        candidates.sort(key=lambda p: ("bold" in os.path.basename(p).lower(), "italic" in os.path.basename(p).lower(), len(p)))
        return candidates[0]
    return None


def resolve_font_file(font_name: str, bold: bool = False, italic: bool = False,
                      extra_dirs: Optional[List[str]] = None) -> Optional[str]:
    """Resuelve un nombre tipográfico a la ruta de un archivo de fuente instalada.

    Orden: fontconfig (fc-match con estilo) -> búsqueda en directorios de fuentes
    -> fc-match genérico. Devuelve None si no hay resolución posible.
    """
    if not font_name:
        return None
    key = (str(font_name).strip().lower(), bool(bold), bool(italic))
    with _CACHE_LOCK:
        if key in _RESOLVE_CACHE:
            return _RESOLVE_CACHE[key]

    result = _fc_match(font_name, bold, italic)
    if not result:
        result = _search_font_dirs(font_name, extra_dirs)
    if not result:
        result = _fc_match_anyway(font_name)

    with _CACHE_LOCK:
        if len(_RESOLVE_CACHE) >= 512:
            _RESOLVE_CACHE.clear()
        _RESOLVE_CACHE[key] = result
    return result


def clear_resolver_cache() -> None:
    with _CACHE_LOCK:
        _RESOLVE_CACHE.clear()
        _FILE_SCAN_CACHE.clear()

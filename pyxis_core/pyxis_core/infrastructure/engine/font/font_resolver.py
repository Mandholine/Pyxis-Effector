# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 Pyxis Effector contributors
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

"""Resolución de fuentes del sistema a archivos .ttf/.otf/.ttc.

Provee resolución de nombres de familia tipográfica (p. ej. "Arial") a rutas de
archivo, para que los motores de métrica (FreeType/PIL) funcionen en Linux/macOS
de la misma forma que Win32 GDI en Windows.

Orden: fontconfig (si existe) -> índice de familias leído con FreeType de los
directorios de fuentes de la plataforma -> búsqueda por nombre de archivo.
"""

import os
import shutil
import subprocess
import sys
import threading
from typing import Dict, List, Optional, Tuple

_FONT_EXTS = (".ttf", ".otf", ".ttc", ".otc", ".dfont")

_FT_STYLE_FLAG_ITALIC = 1
_FT_STYLE_FLAG_BOLD = 2

_FILE_SCAN_CACHE: Dict[str, List[str]] = {}
_RESOLVE_CACHE: Dict[Tuple[str, bool, bool], Optional[str]] = {}
_FAMILY_INDEX_CACHE: Dict[Tuple[str, ...], Dict[str, List[Tuple[str, bool, bool]]]] = {}
_CACHE_LOCK = threading.Lock()


def font_search_dirs() -> List[str]:
    """Directorios donde cada plataforma instala fuentes (sistema y usuario)."""
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        dirs = [
            "/System/Library/Fonts",
            "/System/Library/Fonts/Supplemental",
            "/Library/Fonts",
            os.path.join(home, "Library", "Fonts"),
        ]
    elif sys.platform == "win32":
        dirs = [
            os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
        ]
    else:
        dirs = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            os.path.join(os.environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share"), "fonts"),
            os.path.join(home, ".fonts"),
        ]
    try:
        from paths import get_user_data_dir
        dirs.append(os.path.join(get_user_data_dir(), "fonts"))
    except Exception:
        pass
    return [d for d in dirs if d]


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


def _decode_ft_name(value) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value or "")


def _build_family_index(dirs: List[str]) -> Dict[str, List[Tuple[str, bool, bool]]]:
    """Lee con FreeType la familia y el estilo de cada fuente: {familia normalizada: [(ruta, bold, italic)]}."""
    key = tuple(dirs)
    with _CACHE_LOCK:
        cached = _FAMILY_INDEX_CACHE.get(key)
        if cached is not None:
            return cached
    index: Dict[str, List[Tuple[str, bool, bool]]] = {}
    try:
        import freetype
    except Exception:
        freetype = None
    if freetype is not None:
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for path in _scan_dir_files(d):
                try:
                    first = freetype.Face(path)
                    for i in range(max(1, int(first.num_faces or 1))):
                        face = first if i == 0 else freetype.Face(path, i)
                        family = _norm(_decode_ft_name(face.family_name))
                        if not family:
                            continue
                        flags = int(face.style_flags or 0)
                        index.setdefault(family, []).append(
                            (path, bool(flags & _FT_STYLE_FLAG_BOLD), bool(flags & _FT_STYLE_FLAG_ITALIC))
                        )
                except Exception:
                    continue
    with _CACHE_LOCK:
        _FAMILY_INDEX_CACHE[key] = index
    return index


def _family_index_lookup(font_name: str, bold: bool, italic: bool,
                         extra_dirs: Optional[List[str]] = None) -> Optional[str]:
    """Resuelve por nombre de familia real (no por nombre de archivo); no requiere fontconfig."""
    req = _norm(font_name)
    if not req:
        return None
    dirs = list(extra_dirs or []) + font_search_dirs()
    index = _build_family_index(dirs)
    entries = index.get(req)
    if not entries:
        return None
    # Mejor coincidencia de estilo; ante empate, la ruta más corta (variante base)
    entries = sorted(entries, key=lambda e: ((e[1] != bold) + (e[2] != italic), len(e[0])))
    return entries[0][0]


def _search_font_dirs(font_name: str, extra_dirs: Optional[List[str]] = None) -> Optional[str]:
    """Búsqueda directa y difusa por nombre de archivo en los directorios de fuentes."""
    req = _norm(font_name)
    if not req:
        return None
    dirs = list(extra_dirs or [])
    dirs.extend(font_search_dirs())

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

    Orden: fontconfig (fc-match con estilo) -> índice de familias (FreeType) ->
    búsqueda por nombre de archivo -> fc-match genérico. Devuelve None si no hay
    resolución posible.
    """
    if not font_name:
        return None
    key = (str(font_name).strip().lower(), bool(bold), bool(italic))
    with _CACHE_LOCK:
        if key in _RESOLVE_CACHE:
            return _RESOLVE_CACHE[key]

    result = _fc_match(font_name, bold, italic)
    if not result:
        result = _family_index_lookup(font_name, bold, italic, extra_dirs)
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
        _FAMILY_INDEX_CACHE.clear()

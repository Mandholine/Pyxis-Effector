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
Module: font_resolver.py
Architectural Role: Cross-platform font file discovery, Fontconfig resolution, and FreeType family indexer.

Upstream Dependencies:
    - os, sys, shutil, subprocess, threading: Standard filesystem inspection and process spawning.
    - paths: Canonical user data dir resolution via paths.get_user_data_dir().
    - freetype: Optional FreeType font engine bindings (freetype-py) for reading font metadata.

Downstream Callers:
    - font_engine.py: Resolves font file paths for FreeType metrics on Linux/macOS.
    - font_vector_engine.py: Resolves font files for FreeType glyph outline vectorisation.
    - main.py: Cross-platform fallback in PyxisAPI._find_font_file for preview rendering.

Side Effects and State:
    - Thread-safe in-memory caching of resolved font paths and parsed font family indexes.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
from typing import Dict, List, Optional, Tuple

try:
    import freetype
except ImportError:
    freetype = None

from paths import get_user_data_dir

_RESOLVE_CACHE: Dict[Tuple[str, bool, bool], str] = {}
_FAMILY_INDEX: Dict[str, Dict[Tuple[bool, bool], str]] = {}
_INDEX_BUILT: bool = False
_LOCK = threading.Lock()

_FONT_EXTENSIONS = (".ttf", ".otf", ".ttc", ".dfont")


def font_search_dirs() -> List[str]:
    """
    Returns standard system font directories for the active platform, plus user font dirs.

    Directories Scanned:
        - macOS: /System/Library/Fonts, /System/Library/Fonts/Supplemental,
                 /Library/Fonts, ~/Library/Fonts.
        - Linux: /usr/share/fonts, /usr/local/share/fonts, $XDG_DATA_HOME/fonts
                 (or ~/.local/share/fonts), ~/.fonts.
        - Windows: %WINDIR%/Fonts, %LOCALAPPDATA%/Microsoft/Windows/Fonts.
        - Pyxis User Data: <get_user_data_dir()>/fonts.

    Returns:
        List[str]: Existing canonical directory paths on the local filesystem.
    """
    dirs: List[str] = []
    home = os.path.expanduser("~")

    if sys.platform == "darwin":
        candidates = [
            "/System/Library/Fonts",
            "/System/Library/Fonts/Supplemental",
            "/Library/Fonts",
            os.path.join(home, "Library", "Fonts"),
        ]
    elif sys.platform == "win32":
        windir = os.environ.get("WINDIR", r"C:\Windows")
        localapp = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            os.path.join(windir, "Fonts"),
            os.path.join(localapp, "Microsoft", "Windows", "Fonts") if localapp else "",
        ]
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME", os.path.join(home, ".local", "share"))
        candidates = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            os.path.join(xdg_data, "fonts"),
            os.path.join(home, ".fonts"),
        ]

    # Always include Pyxis user fonts directory
    pyxis_fonts = os.path.join(get_user_data_dir(), "fonts")
    candidates.append(pyxis_fonts)

    for c in candidates:
        if c and os.path.isdir(c) and c not in dirs:
            dirs.append(c)

    return dirs


def _fc_match(font_name: str, bold: bool = False, italic: bool = False) -> Optional[str]:
    """
    Queries Fontconfig via `fc-match` command line utility if installed.

    Args:
        font_name (str): Font family name.
        bold (bool, optional): Bold weight flag.
        italic (bool, optional): Italic slant flag.

    Returns:
        Optional[str]: Verified absolute path to font file, or None if fc-match fails.
    """
    fc_bin = shutil.which("fc-match")
    if not fc_bin:
        return None

    # Construct pattern: e.g. "Arial:weight=bold:slant=italic"
    pattern = font_name
    modifiers = []
    if bold:
        modifiers.append("weight=bold")
    if italic:
        modifiers.append("slant=italic")
    if modifiers:
        pattern = f"{font_name}:{':'.join(modifiers)}"

    try:
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0
        res = subprocess.run(
            [fc_bin, "-f", "%{file}\\n", pattern],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=2.0,
            creationflags=creationflags,
        )
        if res.returncode == 0:
            out_path = res.stdout.strip().split("\n")[0].strip()
            if out_path and os.path.isfile(out_path):
                return out_path
    except Exception:
        pass

    return None


def _build_family_index(extra_dirs: Optional[List[str]] = None) -> None:
    """
    Builds an in-memory index mapping normalised font family names and styles to filepaths.

    Scans font directories using FreeType face inspection (with filename fallback).
    """
    global _INDEX_BUILT
    if _INDEX_BUILT:
        return

    search_dirs = font_search_dirs()
    if extra_dirs:
        for ed in extra_dirs:
            if ed and os.path.isdir(ed) and ed not in search_dirs:
                search_dirs.append(ed)

    for base_dir in search_dirs:
        try:
            for root, _, files in os.walk(base_dir):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext not in _FONT_EXTENSIONS:
                        continue
                    full_path = os.path.join(root, f)
                    _index_single_font_file(full_path)
        except Exception:
            continue

    _INDEX_BUILT = True


def _index_single_font_file(full_path: str) -> None:
    """
    Extracts font family and style from a single file and registers it in _FAMILY_INDEX.
    """
    if freetype is not None:
        try:
            face = freetype.Face(full_path)
            fam = face.family_name
            if isinstance(fam, bytes):
                fam = fam.decode("utf-8", errors="replace")
            if not fam:
                return

            fam_key = str(fam).strip().lower()

            # Inspect style flags
            style_flags = getattr(face, "style_flags", 0)
            is_bold = bool(style_flags & getattr(freetype, "FT_STYLE_FLAG_BOLD", 1))
            is_italic = bool(style_flags & getattr(freetype, "FT_STYLE_FLAG_ITALIC", 2))

            # Style name fallback check
            sname = getattr(face, "style_name", "")
            if isinstance(sname, bytes):
                sname = sname.decode("utf-8", errors="replace")
            sname_lower = str(sname).strip().lower()
            if "bold" in sname_lower:
                is_bold = True
            if "italic" in sname_lower or "oblique" in sname_lower:
                is_italic = True

            if fam_key not in _FAMILY_INDEX:
                _FAMILY_INDEX[fam_key] = {}
            _FAMILY_INDEX[fam_key][(is_bold, is_italic)] = full_path
            return
        except Exception:
            pass

    # Fallback filename heuristic if FreeType is missing or failed to parse
    fname = os.path.basename(full_path)
    stem, _ = os.path.splitext(fname)
    stem_lower = stem.lower()

    is_bold = "bold" in stem_lower or stem_lower.endswith("bd") or "b" in stem_lower.split("-")
    is_italic = "italic" in stem_lower or "oblique" in stem_lower or "it" in stem_lower.split("-")

    # Clean family name heuristic
    clean_fam = stem_lower.replace("bold", "").replace("italic", "").replace("oblique", "").replace("-", "").strip()
    if clean_fam:
        if clean_fam not in _FAMILY_INDEX:
            _FAMILY_INDEX[clean_fam] = {}
        _FAMILY_INDEX[clean_fam][(is_bold, is_italic)] = full_path


def _family_index_lookup(font_name: str, bold: bool = False, italic: bool = False) -> Optional[str]:
    """
    Queries _FAMILY_INDEX for a matching font family and style.
    """
    fam_key = font_name.strip().lower()
    styles = _FAMILY_INDEX.get(fam_key)
    if not styles:
        # Try stripping punctuation or common prefixes/suffixes
        clean_key = fam_key.replace(" ", "").replace("-", "")
        for k, s in _FAMILY_INDEX.items():
            if k.replace(" ", "").replace("-", "") == clean_key:
                styles = s
                break

    if not styles:
        return None

    # 1. Exact match
    if (bold, italic) in styles:
        return styles[(bold, italic)]

    # 2. Bold fallback
    if bold and not italic and (True, False) in styles:
        return styles[(True, False)]

    # 3. Regular fallback
    if (False, False) in styles:
        return styles[(False, False)]

    # 4. Any available style in family
    return next(iter(styles.values()))


def _search_font_dirs_by_name(font_name: str, bold: bool = False, italic: bool = False, extra_dirs: Optional[List[str]] = None) -> Optional[str]:
    """
    Performs direct filename scanning across font directories.
    """
    dirs = font_search_dirs()
    if extra_dirs:
        for ed in extra_dirs:
            if ed and os.path.isdir(ed) and ed not in dirs:
                dirs.append(ed)

    name_clean = font_name.strip().lower().replace(" ", "")

    candidates_suffixes: List[str] = []
    if bold and italic:
        candidates_suffixes.extend(["bi", "bolditalic", "z", "ib"])
    elif bold:
        candidates_suffixes.extend(["bd", "bold", "b"])
    elif italic:
        candidates_suffixes.extend(["i", "italic", "it"])
    candidates_suffixes.append("")

    for d in dirs:
        try:
            for root, _, files in os.walk(d):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext not in _FONT_EXTENSIONS:
                        continue
                    stem = os.path.splitext(f)[0].lower().replace(" ", "").replace("-", "")
                    for suff in candidates_suffixes:
                        target = f"{name_clean}{suff}"
                        if stem == target:
                            return os.path.join(root, f)
        except Exception:
            continue

    return None


def resolve_font_file(
    font_name: str,
    bold: bool = False,
    italic: bool = False,
    extra_dirs: Optional[List[str]] = None,
) -> Optional[str]:
    """
    Resolves the canonical local filesystem path of a font by family name and style.

    Resolution Strategy:
        1. Direct path check: If font_name is an existing file path, returns it.
        2. In-memory cache hit (_RESOLVE_CACHE).
        3. Fontconfig lookup via fc-match (fastest on Linux/macOS when available).
        4. FreeType in-memory family index search (_FAMILY_INDEX).
        5. Directory filename search (_search_font_dirs_by_name).

    Args:
        font_name (str): Font family name (e.g. 'Arial', 'Noto Sans', 'Liberation Serif').
        bold (bool, optional): True if bold weight is requested. Defaults to False.
        italic (bool, optional): True if italic/oblique slant is requested. Defaults to False.
        extra_dirs (Optional[List[str]], optional): Additional search directories. Defaults to None.

    Returns:
        Optional[str]: Normalised absolute path to font file, or None if not found.
    """
    if not font_name or not str(font_name).strip():
        return None

    font_str = str(font_name).strip()

    # 1. Direct path check
    if os.path.isfile(font_str):
        return os.path.abspath(font_str)

    cache_key = (font_str.lower(), bool(bold), bool(italic))
    with _LOCK:
        if cache_key in _RESOLVE_CACHE:
            cached = _RESOLVE_CACHE[cache_key]
            if os.path.isfile(cached):
                return cached

        # 2. Fontconfig lookup
        fc_res = _fc_match(font_str, bold=bold, italic=italic)
        if fc_res and os.path.isfile(fc_res):
            _RESOLVE_CACHE[cache_key] = fc_res
            return fc_res

        # 3. FreeType family index lookup
        if not _INDEX_BUILT:
            _build_family_index(extra_dirs=extra_dirs)

        idx_res = _family_index_lookup(font_str, bold=bold, italic=italic)
        if idx_res and os.path.isfile(idx_res):
            _RESOLVE_CACHE[cache_key] = idx_res
            return idx_res

        # 4. Filename pattern scanning
        dir_res = _search_font_dirs_by_name(font_str, bold=bold, italic=italic, extra_dirs=extra_dirs)
        if dir_res and os.path.isfile(dir_res):
            _RESOLVE_CACHE[cache_key] = dir_res
            return dir_res

    return None


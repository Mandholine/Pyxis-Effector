# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Engine: Font Subsystem
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from .font_engine import FontEngine
from .font_vector_engine import FontVectorEngine
from .font_resolver import resolve_font_file, font_search_dirs, clear_resolver_cache


class FontResolver:
    """Helper facade for resolving system font files."""
    resolve = staticmethod(resolve_font_file)
    search_dirs = staticmethod(font_search_dirs)
    clear_cache = staticmethod(clear_resolver_cache)


__all__ = [
    "FontEngine",
    "FontResolver",
    "FontVectorEngine",
    "resolve_font_file",
    "font_search_dirs",
    "clear_resolver_cache",
]

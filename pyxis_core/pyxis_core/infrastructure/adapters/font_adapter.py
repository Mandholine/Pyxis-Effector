# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Adapters (Font Adapter)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from typing import Any, Dict, Optional
from ..engine.font_engine import FontEngine
from ..engine.font_resolver import FontResolver
from ..engine.font_vector_engine import FontVectorEngine


class FontAdapter:
    """Adapter for font resolution, glyph vectorization, and text metrics."""

    @staticmethod
    def resolve_font_path(font_name: str) -> Optional[str]:
        return FontResolver.resolve(font_name)

    @staticmethod
    def get_text_metrics(text: str, font_name: str, font_size: float) -> Dict[str, Any]:
        return FontEngine.get_text_metrics(text, font_name, font_size)

    @staticmethod
    def vectorize_glyph(char: str, font_name: str, font_size: float) -> str:
        return FontVectorEngine.char_to_ass_drawing(char, font_name, font_size)

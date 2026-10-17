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

"""Typography font engine for text extent measurement matching aegisub.text_extents in C++.

Supports Win32 GDI on Windows with FreeType 26.6 sub-pixel normalization and high-performance caching.
"""

import ctypes
from ctypes import wintypes
import platform
from typing import Dict, Any, Tuple, List, Optional

class SIZE(ctypes.Structure):
    _fields_ = [("cx", wintypes.LONG), ("cy", wintypes.LONG)]

class TEXTMETRICW(ctypes.Structure):
    _fields_ = [
        ("tmHeight", wintypes.LONG),
        ("tmAscent", wintypes.LONG),
        ("tmDescent", wintypes.LONG),
        ("tmInternalLeading", wintypes.LONG),
        ("tmExternalLeading", wintypes.LONG),
        ("tmAveCharWidth", wintypes.LONG),
        ("tmMaxCharWidth", wintypes.LONG),
        ("tmWeight", wintypes.LONG),
        ("tmOverhang", wintypes.LONG),
        ("tmDigitizedAspectX", wintypes.LONG),
        ("tmDigitizedAspectY", wintypes.LONG),
        ("tmFirstChar", wintypes.WCHAR),
        ("tmLastChar", wintypes.WCHAR),
        ("tmDefaultChar", wintypes.WCHAR),
        ("tmBreakChar", wintypes.WCHAR),
        ("tmItalic", wintypes.BYTE),
        ("tmUnderlined", wintypes.BYTE),
        ("tmStruckOut", wintypes.BYTE),
        ("tmPitchAndFamily", wintypes.BYTE),
        ("tmCharSet", wintypes.BYTE)
    ]


def _to_bool(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        val_str = val.strip().lower()
        return val_str not in ("0", "false", "no", "")
    return bool(val)


class FontEngine:
    """Text and typographic font measurement engine (aegisub.text_extents equivalent)."""

    _dc_cache: Optional[int] = None
    _font_cache: Dict[Tuple[str, float, bool, bool, bool, bool], Tuple[int, TEXTMETRICW]] = {}
    _extent_cache: Dict[Tuple[str, float, bool, bool, bool, bool, float, float, str], Tuple[float, float, float, float]] = {}

    @staticmethod
    def snap_26_6(val: float) -> float:
        """Quantizes a pixel value to FreeType 26.6 subpixel grid (1/64 pixel)."""
        return round(val * 64.0) / 64.0

    @classmethod
    def clear_cache(cls) -> None:
        """Clears text extents cache."""
        cls._extent_cache.clear()
        cls._font_cache.clear()

    @classmethod
    def _get_dc(cls) -> int:
        if cls._dc_cache is None and platform.system() == "Windows":
            cls._dc_cache = ctypes.windll.gdi32.CreateCompatibleDC(None)
        return cls._dc_cache or 0

    @classmethod
    def _get_scaled_font(cls, font_name: str, font_size: float, bold: bool, italic: bool, underline: bool, strikeout: bool) -> Tuple[int, TEXTMETRICW]:
        fs_key = round(float(font_size), 2)
        key = (str(font_name).lower(), fs_key, bool(bold), bool(italic), bool(underline), bool(strikeout))
        if key in cls._font_cache:
            return cls._font_cache[key]

        gdi32 = ctypes.windll.gdi32
        hdc = cls._get_dc()
        FW_BOLD = 700
        FW_NORMAL = 400
        weight = FW_BOLD if bold else FW_NORMAL

        # Resolución sub-píxel exacta de 64 sub-unidades por píxel (rejilla 26.6 idéntica a FreeType y GDI en font_vector_engine)
        height = abs(int(round(float(font_size) * 64.0)))

        hfont = gdi32.CreateFontW(
            height, 0, 0, 0, weight,
            1 if italic else 0, 1 if underline else 0, 1 if strikeout else 0,
            1, 0, 0, 4, 0, str(font_name)
        )

        old_font = gdi32.SelectObject(hdc, hfont)
        tm = TEXTMETRICW()
        gdi32.GetTextMetricsW(hdc, ctypes.byref(tm))
        gdi32.SelectObject(hdc, old_font)

        if len(cls._font_cache) >= 512:
            cls._font_cache.clear()

        cls._font_cache[key] = (hfont, tm)
        return hfont, tm

    @classmethod
    def get_text_extents(cls, style: Dict[str, Any], text: str) -> Tuple[float, float, float, float]:
        """Calculates (width, height, descent, extlead) for text according to ASS style.

        Uses a result caching system to avoid re-measuring identical strings/characters.
        Matches FreeType 26.6 sub-pixel format of aegisub.text_extents in C++.
        """
        font_name = str(style.get("fontname") or style.get("Fontname") or "Arial")
        font_size = float(style.get("fontsize") or style.get("Fontsize") or 35.0)
        bold = _to_bool(style.get("bold") if "bold" in style else style.get("Bold"))
        italic = _to_bool(style.get("italic") if "italic" in style else style.get("Italic"))
        underline = _to_bool(style.get("underline") if "underline" in style else style.get("Underline"))
        strikeout = _to_bool(style.get("strikeout") if "strikeout" in style else style.get("StrikeOut"))
        scale_x = float(style.get("scale_x") or style.get("ScaleX") or 100.0)
        spacing = float(style.get("spacing") or style.get("Spacing") or 0.0)

        cache_key = (font_name.lower(), font_size, bold, italic, underline, strikeout, scale_x, spacing, text)
        if cache_key in cls._extent_cache:
            return cls._extent_cache[cache_key]

        if not text:
            height, descent, extlead = cls.get_font_metrics(style)
            res_empty = (0.0, height, descent, extlead)
            cls._extent_cache[cache_key] = res_empty
            return res_empty

        if platform.system() == "Windows":
            try:
                res = cls._get_text_extents_gdi(text, font_name, font_size, bold, italic, underline, strikeout, scale_x, spacing)
                snapped = (cls.snap_26_6(res[0]), cls.snap_26_6(res[1]), cls.snap_26_6(res[2]), cls.snap_26_6(res[3]))
                cls._extent_cache[cache_key] = snapped
                return snapped
            except Exception:
                pass

        res_fb = cls._get_text_extents_fallback(text, font_name, font_size, bold, italic, scale_x, spacing)
        snapped_fb = (cls.snap_26_6(res_fb[0]), cls.snap_26_6(res_fb[1]), cls.snap_26_6(res_fb[2]), cls.snap_26_6(res_fb[3]))
        cls._extent_cache[cache_key] = snapped_fb
        return snapped_fb

    @classmethod
    def get_font_metrics(cls, style: Dict[str, Any]) -> Tuple[float, float, float]:
        """Calculates (height, descent, extlead) of style with 26.6 quantization."""
        font_name = str(style.get("fontname") or style.get("Fontname") or "Arial")
        font_size = float(style.get("fontsize") or style.get("Fontsize") or 35.0)
        bold = _to_bool(style.get("bold") if "bold" in style else style.get("Bold"))
        italic = _to_bool(style.get("italic") if "italic" in style else style.get("Italic"))
        underline = _to_bool(style.get("underline") if "underline" in style else style.get("Underline"))
        strikeout = _to_bool(style.get("strikeout") if "strikeout" in style else style.get("StrikeOut"))

        if platform.system() == "Windows":
            try:
                hfont, tm = cls._get_scaled_font(font_name, font_size, bold, italic, underline, strikeout)
                h = cls.snap_26_6(font_size)
                d = cls.snap_26_6(float(tm.tmDescent) / 64.0)
                e = cls.snap_26_6(float(tm.tmExternalLeading) / 64.0)
                return h, d, e
            except Exception:
                pass

        res_fb = cls._get_font_metrics_freetype(font_name, font_size, bold, italic)
        if res_fb is not None:
            h, d, e = res_fb
            return cls.snap_26_6(h), cls.snap_26_6(d), cls.snap_26_6(e)

        return cls.snap_26_6(font_size), cls.snap_26_6(font_size * 0.2), 0.0

    @classmethod
    def get_char_widths(cls, style: Dict[str, Any], text: str) -> List[float]:
        """Calcula el ancho individual de cada carácter cuantizado a la rejilla de 26.6 sub-píxeles."""
        if not text:
            return []
        
        widths = []
        for char in text:
            w, _, _, _ = cls.get_text_extents(style, char)
            widths.append(w)
        return widths

    @classmethod
    def _get_text_extents_gdi(cls, text: str, font_name: str, font_size: float, bold: bool, italic: bool,
                              underline: bool, strikeout: bool, scale_x: float, spacing: float) -> Tuple[float, float, float, float]:
        gdi32 = ctypes.windll.gdi32
        hdc = cls._get_dc()

        hfont, tm = cls._get_scaled_font(font_name, font_size, bold, italic, underline, strikeout)
        old_font = gdi32.SelectObject(hdc, hfont)

        sz = SIZE()
        gdi32.GetTextExtentPoint32W(hdc, text, len(text), ctypes.byref(sz))
        gdi32.SelectObject(hdc, old_font)

        # Conversión directa en escala 26.6 subpíxel (64x)
        base_w = (float(sz.cx) / 64.0) * (scale_x / 100.0)
        extra_spacing = float(spacing) * max(0, len(text) - 1) * (scale_x / 100.0)
        final_w = base_w + extra_spacing

        height = float(font_size)
        descent = float(tm.tmDescent) / 64.0
        extlead = float(tm.tmExternalLeading) / 64.0

        return final_w, height, descent, extlead

    # ------------------------------------------------------------------
    # FreeType / Pillow paths (Linux, macOS y fallback universal)
    # ------------------------------------------------------------------

    _font_file_cache: Dict[str, Optional[str]] = {}

    @classmethod
    def _resolve_font_path(cls, font_name: str, bold: bool = False, italic: bool = False) -> Optional[str]:
        try:
            from font_resolver import resolve_font_file
            return resolve_font_file(font_name, bold=bold, italic=italic)
        except Exception:
            return None

    @classmethod
    def _get_font_metrics_freetype(cls, font_name: str, font_size: float, bold: bool, italic: bool) -> Optional[Tuple[float, float, float]]:
        """Métricas (height, descent, extlead) vía FreeType/Pillow para fuentes resueltas."""
        try:
            font_path = cls._resolve_font_path(font_name, bold, italic)
            if not font_path:
                return None
            try:
                import freetype
                face = freetype.Face(font_path)
                face.set_char_size(int(round(float(font_size) * 64.0)))
                ascent = (face.size.ascender / 64.0)
                descent = abs(face.size.descender / 64.0)
                line_gap = (face.size.height / 64.0) - ascent - descent
                return float(font_size), float(descent), max(0.0, float(line_gap))
            except Exception:
                pass
            from PIL import ImageFont
            font = ImageFont.truetype(font_path, int(round(float(font_size))))
            ascent, descent = font.getmetrics()
            return float(font_size), float(descent), 0.0
        except Exception:
            return None

    @classmethod
    def _get_text_extents_freetype(cls, text: str, font_name: str, font_size: float, bold: bool, italic: bool,
                                   scale_x: float, spacing: float) -> Optional[Tuple[float, float, float, float]]:
        """Anchos reales (advance) vía FreeType/Pillow para fuentes resueltas."""
        try:
            font_path = cls._resolve_font_path(font_name, bold, italic)
            if not font_path:
                return None
            try:
                import freetype
                face = freetype.Face(font_path)
                face.set_char_size(int(round(float(font_size) * 64.0)))
                total = 0.0
                for ch in text:
                    face.load_char(ch, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)
                    total += face.glyph.metrics.horiAdvance / 64.0
                base_w = total
                descent = abs(face.size.descender / 64.0)
                line_gap = (face.size.height / 64.0) - (face.size.ascender / 64.0) - descent
                extlead = max(0.0, line_gap)
            except Exception:
                from PIL import ImageFont
                font = ImageFont.truetype(font_path, int(round(float(font_size))))
                base_w = float(font.getlength(text))
                ascent, descent_i = font.getmetrics()
                descent = float(descent_i)
                extlead = 0.0

            final_w = base_w * (scale_x / 100.0) + float(spacing) * max(0, len(text) - 1) * (scale_x / 100.0)
            return float(final_w), float(font_size), float(descent), float(extlead)
        except Exception:
            return None

    @classmethod
    def _get_text_extents_fallback(cls, text: str, font_name: str, font_size: float, bold: bool, italic: bool,
                                   scale_x: float, spacing: float) -> Tuple[float, float, float, float]:
        res_ft = cls._get_text_extents_freetype(text, font_name, font_size, bold, italic, scale_x, spacing)
        if res_ft is not None:
            return res_ft
        try:
            from PIL import ImageFont
            font = ImageFont.truetype(font_name, int(font_size))
            bbox = font.getbbox(text)
            w = (bbox[2] - bbox[0]) * (scale_x / 100.0) + spacing * max(0, len(text) - 1)
            h = float(font_size)
            return float(w), h, float(h * 0.2), 0.0
        except Exception:
            w = len(text) * font_size * 0.5 * (scale_x / 100.0) + spacing * max(0, len(text) - 1)
            h = float(font_size)
            return float(w), h, float(font_size * 0.2), 0.0

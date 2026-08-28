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

# font_engine.py
"""Motor de fuentes tipográficas para medición de extents de texto idéntico a aegisub.text_extents en C++.

Soporta Win32 GDI en Windows con normalización sub-pixel 26.6 de FreeType y sistema de caché de alto rendimiento.
"""

import ctypes
from ctypes import wintypes
import platform
from typing import Dict, Any, Tuple, List, Optional

# Definiciones Win32 GDI Structs
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
    """Motor de medición de texto y fuentes tipográficas (aegisub.text_extents equivalent)."""

    _dc_cache: Optional[int] = None
    _font_cache: Dict[Tuple[str, bool, bool, bool, bool], Tuple[int, TEXTMETRICW]] = {}
    _extent_cache: Dict[Tuple[str, float, bool, bool, bool, bool, float, float, str], Tuple[float, float, float, float]] = {}

    @staticmethod
    def snap_26_6(val: float) -> float:
        """Cuantiza un valor de píxel a la rejilla de subpíxel 26.6 de FreeType (1/64 de píxel)."""
        return round(val * 64.0) / 64.0

    @classmethod
    def clear_cache(cls) -> None:
        """Limpia el caché de extents de texto."""
        cls._extent_cache.clear()

    @classmethod
    def _get_dc(cls) -> int:
        if cls._dc_cache is None and platform.system() == "Windows":
            cls._dc_cache = ctypes.windll.gdi32.CreateCompatibleDC(None)
        return cls._dc_cache or 0

    @classmethod
    def _get_scaled_font(cls, font_name: str, bold: bool, italic: bool, underline: bool, strikeout: bool) -> Tuple[int, TEXTMETRICW]:
        key = (font_name.lower(), bold, italic, underline, strikeout)
        if key in cls._font_cache:
            return cls._font_cache[key]

        gdi32 = ctypes.windll.gdi32
        hdc = cls._get_dc()
        FW_BOLD = 700
        FW_NORMAL = 400
        weight = FW_BOLD if bold else FW_NORMAL

        hfont = gdi32.CreateFontW(
            -1000, 0, 0, 0, weight,
            1 if italic else 0, 1 if underline else 0, 1 if strikeout else 0,
            1, 0, 0, 4, 0, str(font_name)
        )

        old_font = gdi32.SelectObject(hdc, hfont)
        tm = TEXTMETRICW()
        gdi32.GetTextMetricsW(hdc, ctypes.byref(tm))
        gdi32.SelectObject(hdc, old_font)

        cls._font_cache[key] = (hfont, tm)
        return hfont, tm

    @classmethod
    def get_text_extents(cls, style: Dict[str, Any], text: str) -> Tuple[float, float, float, float]:
        """Calcula (width, height, descent, extlead) para un texto según el estilo ASS.
        
        Utiliza un sistema de caché de resultados para evitar volver a medir cadenas/caracteres idénticos.
        Coincide exactamente con el formato sub-pixel 26.6 de aegisub.text_extents en C++.
        """
        font_name = str(style.get("fontname") or style.get("Fontname") or "Arial")
        font_size = float(style.get("fontsize") or style.get("Fontsize") or 35.0)
        bold = _to_bool(style.get("bold") if "bold" in style else style.get("Bold"))
        italic = _to_bool(style.get("italic") if "italic" in style else style.get("Italic"))
        underline = _to_bool(style.get("underline") if "underline" in style else style.get("Underline"))
        strikeout = _to_bool(style.get("strikeout") if "strikeout" in style else style.get("StrikeOut"))
        scale_x = float(style.get("scale_x") or style.get("ScaleX") or 100.0)
        spacing = float(style.get("spacing") or style.get("Spacing") or 0.0)

        # Clave de caché para consulta instantánea (0 nanosegundos)
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
        """Calcula (height, descent, extlead) del estilo con cuantización 26.6."""
        font_name = str(style.get("fontname") or style.get("Fontname") or "Arial")
        font_size = float(style.get("fontsize") or style.get("Fontsize") or 35.0)
        bold = _to_bool(style.get("bold") if "bold" in style else style.get("Bold"))
        italic = _to_bool(style.get("italic") if "italic" in style else style.get("Italic"))
        underline = _to_bool(style.get("underline") if "underline" in style else style.get("Underline"))
        strikeout = _to_bool(style.get("strikeout") if "strikeout" in style else style.get("StrikeOut"))

        if platform.system() == "Windows":
            try:
                hfont, tm = cls._get_scaled_font(font_name, bold, italic, underline, strikeout)
                scale_factor = font_size / float(tm.tmHeight)
                h = cls.snap_26_6(font_size)
                d = cls.snap_26_6(float(tm.tmDescent) * scale_factor)
                e = cls.snap_26_6(float(tm.tmExternalLeading) * scale_factor)
                return h, d, e
            except Exception:
                pass

        return cls.snap_26_6(font_size), cls.snap_26_6(font_size * 0.2), 0.0

    @classmethod
    def get_char_widths(cls, style: Dict[str, Any], text: str) -> List[float]:
        """Calcula el ancho individual de cada carácter utilizando el sistema de caché."""
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

        hfont, tm = cls._get_scaled_font(font_name, bold, italic, underline, strikeout)
        old_font = gdi32.SelectObject(hdc, hfont)

        sz = SIZE()
        gdi32.GetTextExtentPoint32W(hdc, text, len(text), ctypes.byref(sz))
        gdi32.SelectObject(hdc, old_font)

        scale_factor = font_size / float(tm.tmHeight)

        base_w = float(sz.cx) * scale_factor * (scale_x / 100.0)
        extra_spacing = spacing * max(0, len(text) - 1)
        final_w = base_w + extra_spacing

        height = font_size
        descent = float(tm.tmDescent) * scale_factor
        extlead = float(tm.tmExternalLeading) * scale_factor

        return final_w, height, descent, extlead

    @classmethod
    def _get_text_extents_fallback(cls, text: str, font_name: str, font_size: float, bold: bool, italic: bool,
                                   scale_x: float, spacing: float) -> Tuple[float, float, float, float]:
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

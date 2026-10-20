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

"""Typography font engine for text extent measurement matching aegisub.text_extents in C++.

Supports Win32 GDI on Windows with FreeType 26.6 sub-pixel normalization and high-performance caching.
"""

import ctypes
from ctypes import wintypes
import platform
import struct
from typing import Dict, Any, Tuple, List, Optional

class SIZE(ctypes.Structure):
    _fields_ = [("cx", wintypes.LONG), ("cy", wintypes.LONG)]

class SCRIPT_ANALYSIS(ctypes.Structure):
    _fields_ = [
        ("eScript", wintypes.WORD, 10),
        ("fRTL", wintypes.WORD, 1),
        ("fLayoutRTL", wintypes.WORD, 1),
        ("fLinkBefore", wintypes.WORD, 1),
        ("fLinkAfter", wintypes.WORD, 1),
        ("fLogicalOrder", wintypes.WORD, 1),
        ("fNoGlyphIndex", wintypes.WORD, 1),
        ("s", wintypes.WORD)
    ]

class SCRIPT_ITEM(ctypes.Structure):
    _fields_ = [
        ("iCharPos", wintypes.INT),
        ("a", SCRIPT_ANALYSIS)
    ]

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
    _font_ratio_cache: Dict[Tuple[str, float], float] = {}
    _shaped_advances_cache: Dict[Tuple[str, float, bool, bool, bool, bool, str], Tuple[List[float], bool]] = {}
    _char_layout_cache: Dict[Tuple[str, float, bool, bool, bool, bool, float, float, str], List[Dict[str, Any]]] = {}

    @staticmethod
    def snap_26_6(val: float) -> float:
        """Quantizes a pixel value to FreeType 26.6 subpixel grid (1/64 pixel)."""
        return round(val * 64.0) / 64.0

    @classmethod
    def clear_cache(cls) -> None:
        """Clears text extents, GDI font handle, shaped advances, and calibration ratio caches."""
        cls._extent_cache.clear()
        cls._font_cache.clear()
        cls._font_ratio_cache.clear()
        cls._shaped_advances_cache.clear()
        cls._char_layout_cache.clear()

    @classmethod
    def _get_dc(cls) -> int:
        """Retrieves or initialises a cached Win32 GDI Device Context handle."""
        if cls._dc_cache is None and platform.system() == "Windows":
            cls._dc_cache = ctypes.windll.gdi32.CreateCompatibleDC(None)
        return cls._dc_cache or 0

    @classmethod
    def _get_scaled_font(cls, font_name: str, font_size: float, bold: bool, italic: bool, underline: bool, strikeout: bool) -> Tuple[int, TEXTMETRICW]:
        """
        Retrieves or creates a 64x sub-pixel scaled Win32 HFONT handle and its TEXTMETRICW structure.

        Args:
            font_name: Font typeface family name.
            font_size: Point size in typographic units.
            bold: True if bold weight (FW_BOLD 700) is enabled.
            italic: True if italic styling is enabled.
            underline: True if underline styling is enabled.
            strikeout: True if strikeout styling is enabled.

        Returns:
            A tuple of (HFONT handle integer, populated TEXTMETRICW structure).
        """
        fs_key = round(float(font_size), 2)
        key = (str(font_name).lower(), fs_key, bool(bold), bool(italic), bool(underline), bool(strikeout))
        if key in cls._font_cache:
            return cls._font_cache[key]

        gdi32 = ctypes.windll.gdi32
        hdc = cls._get_dc()
        FW_BOLD = 700
        FW_NORMAL = 400
        weight = FW_BOLD if bold else FW_NORMAL

        # Exact sub-pixel resolution of 64 sub-units per pixel (26.6 grid identical to FreeType and GDI in font_vector_engine)
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

        Args:
            style: ASS style dictionary containing font properties.
            text: Text string to measure.

        Returns:
            Tuple of (width, height, descent, extlead) quantised to 26.6 sub-pixels.
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
        """
        Calculates (height, descent, extlead) of style with FreeType 26.6 quantization.

        Args:
            style: ASS style dictionary containing typeface attributes.

        Returns:
            Tuple of (height, descent, extlead).
        """
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

        return cls.snap_26_6(font_size), cls.snap_26_6(font_size * 0.2), 0.0

    @classmethod
    def get_char_widths(cls, style: Dict[str, Any], text: str) -> List[float]:
        """
        Calculates individual character widths quantised to the FreeType 26.6 sub-pixel grid.

        If spacing is zero and text contains OpenType ligatures, projects shaped character
        advances to ensure individual characters align seamlessly with continuous shaped text runs.

        Args:
            style: ASS style dictionary.
            text: Character sequence to measure.

        Returns:
            List of advance widths per glyph.
        """
        if not text:
            return []

        spacing = float(style.get("spacing") or style.get("Spacing") or 0.0)
        if abs(spacing) < 1e-4 and platform.system() == "Windows" and len(text) > 1:
            try:
                font_name = str(style.get("fontname") or style.get("Fontname") or "Arial")
                font_size = float(style.get("fontsize") or style.get("Fontsize") or 35.0)
                bold = _to_bool(style.get("bold") if "bold" in style else style.get("Bold"))
                italic = _to_bool(style.get("italic") if "italic" in style else style.get("Italic"))
                underline = _to_bool(style.get("underline") if "underline" in style else style.get("Underline"))
                strikeout = _to_bool(style.get("strikeout") if "strikeout" in style else style.get("StrikeOut"))
                advs, has_liga = cls.get_shaped_char_advances(font_name, font_size, bold, italic, underline, strikeout, text)
                if has_liga and len(advs) == len(text):
                    scale_x = float(style.get("scale_x") or style.get("ScaleX") or 100.0)
                    return [cls.snap_26_6(a * (scale_x / 100.0)) for a in advs]
            except Exception:
                pass

        widths = []
        for char in text:
            w, _, _, _ = cls.get_text_extents(style, char)
            widths.append(w)
        return widths

    @classmethod
    def get_char_layout_metrics(cls, style: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """
        Calculates individual character layout metrics including isolated width, shaped advance,
        and ligature flags.

        If spacing is zero and text contains OpenType ligatures, accurately partitions cluster
        advances and preserves isolated widths so that characters rendered individually align
        seamlessly with continuous shaped text runs down to sub-pixel precision.

        Args:
            style: ASS style dictionary.
            text: Character sequence to measure.

        Returns:
            List of dictionaries with keys:
                - "advance": float advance width to next character cursor.
                - "isolated_width": float nominal glyph width for isolated centering/bounding.
                - "is_ligature": bool flag indicating ligature participation.
        """
        if not text:
            return []

        font_name = str(style.get("fontname") or style.get("Fontname") or "Arial")
        font_size = float(style.get("fontsize") or style.get("Fontsize") or 35.0)
        bold = _to_bool(style.get("bold") if "bold" in style else style.get("Bold"))
        italic = _to_bool(style.get("italic") if "italic" in style else style.get("Italic"))
        underline = _to_bool(style.get("underline") if "underline" in style else style.get("Underline"))
        strikeout = _to_bool(style.get("strikeout") if "strikeout" in style else style.get("StrikeOut"))
        scale_x = float(style.get("scale_x") or style.get("ScaleX") or 100.0)
        spacing = float(style.get("spacing") or style.get("Spacing") or 0.0)

        cache_key = (font_name.lower(), font_size, bold, italic, underline, strikeout, scale_x, spacing, text)
        if cache_key in cls._char_layout_cache:
            return cls._char_layout_cache[cache_key]

        cInChars = len(text)
        if abs(spacing) < 1e-4 and platform.system() == "Windows" and cInChars > 1:
            try:
                usp10 = ctypes.windll.usp10
                gdi32 = ctypes.windll.gdi32
                hdc = cls._get_dc()
                hfont, _ = cls._get_scaled_font(font_name, font_size, bold, italic, underline, strikeout)
                old_font = gdi32.SelectObject(hdc, hfont)

                items = (SCRIPT_ITEM * (cInChars + 2))()
                cItems = wintypes.INT()
                hr = usp10.ScriptItemize(text, cInChars, cInChars + 2, None, None, items, ctypes.byref(cItems))
                if hr == 0 and cItems.value > 0:
                    calib = cls.get_font_calibration_ratio(font_name, font_size)
                    sc = ctypes.c_void_p()
                    char_advances = [0.0] * cInChars
                    char_isolated = [0.0] * cInChars
                    is_liga_list = [False] * cInChars
                    has_ligatures = False

                    for idx in range(cItems.value):
                        sc_pos = items[idx].iCharPos
                        ec_pos = items[idx + 1].iCharPos
                        l = ec_pos - sc_pos
                        if l <= 0:
                            continue
                        it = text[sc_pos:ec_pos]
                        mg = l * 2 + 16
                        g = (wintypes.WORD * mg)()
                        cl = (wintypes.WORD * l)()
                        at = (wintypes.BYTE * mg)()
                        pg = wintypes.INT()

                        hr_s = usp10.ScriptShape(hdc, ctypes.byref(sc), it, l, mg, ctypes.byref(items[idx].a), g, cl, at, ctypes.byref(pg))
                        if hr_s != 0 or pg.value <= 0:
                            for k in range(l):
                                sz = SIZE()
                                gdi32.GetTextExtentPoint32W(hdc, it[k], 1, ctypes.byref(sz))
                                w_k = (float(sz.cx) / 64.0) * calib
                                char_advances[sc_pos + k] = w_k
                                char_isolated[sc_pos + k] = w_k
                            continue

                        if pg.value < l or any(cl[k] == cl[k + 1] for k in range(l - 1)):
                            has_ligatures = True

                        gw = (wintypes.INT * pg.value)()
                        gdi32.GetCharWidthI(hdc, g[0], pg.value, g, gw)

                        cluster_chars: Dict[int, List[int]] = {}
                        for c_idx in range(l):
                            c_cluster = cl[c_idx]
                            if c_cluster not in cluster_chars:
                                cluster_chars[c_cluster] = []
                            cluster_chars[c_cluster].append(c_idx)

                        for g_idx, c_indices in cluster_chars.items():
                            if g_idx < pg.value:
                                w = (float(gw[g_idx]) / 64.0) * calib
                                if len(c_indices) > 1:
                                    w_isos = []
                                    for ci in c_indices:
                                        sz_i = SIZE()
                                        gdi32.GetTextExtentPoint32W(hdc, it[ci], 1, ctypes.byref(sz_i))
                                        w_isos.append((float(sz_i.cx) / 64.0) * calib)
                                    w_last = w_isos[-1]
                                    if w >= w_last:
                                        lead_w = w - w_last
                                        sum_lead = sum(w_isos[:-1]) or 1.0
                                        for k in range(len(c_indices) - 1):
                                            ci_k = c_indices[k]
                                            char_advances[sc_pos + ci_k] = lead_w * (w_isos[k] / sum_lead)
                                            char_isolated[sc_pos + ci_k] = w_isos[k]
                                            is_liga_list[sc_pos + ci_k] = True
                                        ci_last = c_indices[-1]
                                        char_advances[sc_pos + ci_last] = w_last
                                        char_isolated[sc_pos + ci_last] = w_last
                                        is_liga_list[sc_pos + ci_last] = True
                                    else:
                                        sum_all = sum(w_isos) or 1.0
                                        for k in range(len(c_indices)):
                                            ci_k = c_indices[k]
                                            char_advances[sc_pos + ci_k] = w * (w_isos[k] / sum_all)
                                            char_isolated[sc_pos + ci_k] = w_isos[k]
                                            is_liga_list[sc_pos + ci_k] = True
                                else:
                                    ci = c_indices[0]
                                    char_advances[sc_pos + ci] = w
                                    char_isolated[sc_pos + ci] = w

                    usp10.ScriptFreeCache(ctypes.byref(sc))
                    gdi32.SelectObject(hdc, old_font)

                    if has_ligatures:
                        sc_factor = scale_x / 100.0
                        res = [
                            {
                                "advance": cls.snap_26_6(char_advances[i] * sc_factor),
                                "isolated_width": cls.snap_26_6(char_isolated[i] * sc_factor),
                                "is_ligature": is_liga_list[i]
                            }
                            for i in range(cInChars)
                        ]
                        if len(cls._char_layout_cache) >= 1024:
                            cls._char_layout_cache.clear()
                        cls._char_layout_cache[cache_key] = res
                        return res
            except Exception:
                pass

        widths = cls.get_char_widths(style, text)
        res = [
            {
                "advance": w,
                "isolated_width": w,
                "is_ligature": False
            }
            for w in widths
        ]
        if len(cls._char_layout_cache) >= 1024:
            cls._char_layout_cache.clear()
        cls._char_layout_cache[cache_key] = res
        return res

    @classmethod
    def get_font_calibration_ratio(cls, font_name: str, font_size: float) -> float:
        """
        Calculates the selective FreeType-to-GDI calibration ratio.

        For standard fonts where cell height equals typographic box height (cell == hhea),
        returns strictly 1.0 (zero alteration). For fonts with metric divergence (e.g. Joan,
        Calibri), calculates FreeType's continuous ppem quantization ratio to match libass rendering.

        Args:
            font_name: Typographic font family name.
            font_size: Typographic point size.

        Returns:
            Multiplicative calibration ratio for text advances (strictly 1.0 for standard fonts).
        """
        fs_key = round(float(font_size), 2)
        key = (str(font_name).lower(), fs_key)
        if key in cls._font_ratio_cache:
            return cls._font_ratio_cache[key]

        if platform.system() != "Windows":
            cls._font_ratio_cache[key] = 1.0
            return 1.0

        try:
            gdi32 = ctypes.windll.gdi32
            hdc = cls._get_dc()
            hfont, _ = cls._get_scaled_font(font_name, font_size, False, False, False, False)
            old_font = gdi32.SelectObject(hdc, hfont)

            tag_os2 = int.from_bytes(b'2/SO', 'big')
            tag_head = int.from_bytes(b'daeh', 'big')
            tag_hhea = int.from_bytes(b'aehh', 'big')

            sz_os2 = gdi32.GetFontData(hdc, tag_os2, 0, None, 0)
            sz_head = gdi32.GetFontData(hdc, tag_head, 0, None, 0)
            sz_hhea = gdi32.GetFontData(hdc, tag_hhea, 0, None, 0)

            if sz_os2 >= 78 and sz_head >= 20 and sz_hhea >= 8:
                buf_os2 = ctypes.create_string_buffer(sz_os2)
                buf_head = ctypes.create_string_buffer(sz_head)
                buf_hhea = ctypes.create_string_buffer(sz_hhea)

                gdi32.GetFontData(hdc, tag_os2, 0, buf_os2, sz_os2)
                gdi32.GetFontData(hdc, tag_head, 0, buf_head, sz_head)
                gdi32.GetFontData(hdc, tag_hhea, 0, buf_hhea, sz_hhea)
                gdi32.SelectObject(hdc, old_font)

                ascent, descent = struct.unpack('>HH', buf_os2.raw[74:78])
                cell = ascent + descent

                h_asc, h_desc = struct.unpack('>hh', buf_hhea.raw[4:8])
                hhea_h = h_asc - h_desc

                upem = struct.unpack('>H', buf_head.raw[18:20])[0]

                if cell == hhea_h or not cell or not hhea_h or not upem:
                    ratio = 1.0
                else:
                    cont_ppem = (upem * font_size) / cell
                    ratio = (round(cont_ppem) / cont_ppem) if cont_ppem > 0 else 1.0

                if len(cls._font_ratio_cache) >= 512:
                    cls._font_ratio_cache.clear()
                cls._font_ratio_cache[key] = ratio
                return ratio
            else:
                gdi32.SelectObject(hdc, old_font)
        except Exception:
            pass

        if len(cls._font_ratio_cache) >= 512:
            cls._font_ratio_cache.clear()
        cls._font_ratio_cache[key] = 1.0
        return 1.0

    @classmethod
    def get_shaped_char_advances(cls, font_name: str, font_size: float, bold: bool, italic: bool,
                                 underline: bool, strikeout: bool, text: str) -> Tuple[List[float], bool]:
        """Calculates character advances accounting for OpenType ligatures and glyph substitutions via Uniscribe.

        Args:
            font_name: Font family name.
            font_size: Typographic point size.
            bold: Bold weight flag.
            italic: Italic styling flag.
            underline: Underline flag.
            strikeout: Strikeout flag.
            text: Character sequence to shape.

        Returns:
            Tuple of (list of sub-pixel advances per character in FreeType 26.6 grid, boolean has_ligatures).
        """
        fs_key = round(float(font_size), 2)
        cache_key = (str(font_name).lower(), fs_key, bool(bold), bool(italic), bool(underline), bool(strikeout), str(text))
        if cache_key in cls._shaped_advances_cache:
            return cls._shaped_advances_cache[cache_key]

        cInChars = len(text)
        if cInChars == 0 or platform.system() != "Windows":
            return [0.0] * cInChars, False

        try:
            usp10 = ctypes.windll.usp10
            gdi32 = ctypes.windll.gdi32
            hdc = cls._get_dc()
            hfont, _ = cls._get_scaled_font(font_name, font_size, bold, italic, underline, strikeout)
            old_font = gdi32.SelectObject(hdc, hfont)

            items = (SCRIPT_ITEM * (cInChars + 2))()
            cItems = wintypes.INT()
            hr = usp10.ScriptItemize(text, cInChars, cInChars + 2, None, None, items, ctypes.byref(cItems))
            if hr != 0:
                gdi32.SelectObject(hdc, old_font)
                return [0.0] * cInChars, False

            char_advances = [0.0] * cInChars
            has_ligatures = False
            calib = cls.get_font_calibration_ratio(font_name, font_size)
            sc = ctypes.c_void_p()

            for idx in range(cItems.value):
                sc_pos = items[idx].iCharPos
                ec_pos = items[idx + 1].iCharPos
                l = ec_pos - sc_pos
                if l <= 0:
                    continue
                it = text[sc_pos:ec_pos]
                mg = l * 2 + 16
                g = (wintypes.WORD * mg)()
                cl = (wintypes.WORD * l)()
                at = (wintypes.BYTE * mg)()
                pg = wintypes.INT()

                hr_shape = usp10.ScriptShape(hdc, ctypes.byref(sc), it, l, mg, ctypes.byref(items[idx].a), g, cl, at, ctypes.byref(pg))
                if hr_shape != 0:
                    for k in range(l):
                        sz = SIZE()
                        gdi32.GetTextExtentPoint32W(hdc, it[k], 1, ctypes.byref(sz))
                        char_advances[sc_pos + k] = (float(sz.cx) / 64.0) * calib
                    continue

                if pg.value < l or any(cl[k] == cl[k + 1] for k in range(l - 1)):
                    has_ligatures = True

                gw = (wintypes.INT * pg.value)()
                gdi32.GetCharWidthI(hdc, g[0], pg.value, g, gw)

                cluster_chars: Dict[int, List[int]] = {}
                for c_idx in range(l):
                    c_cluster = cl[c_idx]
                    if c_cluster not in cluster_chars:
                        cluster_chars[c_cluster] = []
                    cluster_chars[c_cluster].append(c_idx)

                for g_idx, c_indices in cluster_chars.items():
                    if g_idx < pg.value:
                        w = (float(gw[g_idx]) / 64.0) * calib
                        if len(c_indices) > 1:
                            w_isos = []
                            for ci in c_indices:
                                sz_i = SIZE()
                                gdi32.GetTextExtentPoint32W(hdc, it[ci], 1, ctypes.byref(sz_i))
                                w_isos.append((float(sz_i.cx) / 64.0) * calib)
                            w_last = w_isos[-1]
                            if w >= w_last:
                                lead_w = w - w_last
                                sum_lead = sum(w_isos[:-1]) or 1.0
                                for k in range(len(c_indices) - 1):
                                    char_advances[sc_pos + c_indices[k]] = lead_w * (w_isos[k] / sum_lead)
                                char_advances[sc_pos + c_indices[-1]] = w_last
                            else:
                                sum_all = sum(w_isos) or 1.0
                                for k in range(len(c_indices)):
                                    char_advances[sc_pos + c_indices[k]] = w * (w_isos[k] / sum_all)
                        else:
                            char_advances[sc_pos + c_indices[0]] = w

            usp10.ScriptFreeCache(ctypes.byref(sc))
            gdi32.SelectObject(hdc, old_font)

            if len(cls._shaped_advances_cache) >= 1024:
                cls._shaped_advances_cache.clear()
            res = (char_advances, has_ligatures)
            cls._shaped_advances_cache[cache_key] = res
            return res
        except Exception:
            pass

        return [0.0] * cInChars, False

    @classmethod
    def _get_text_extents_gdi(cls, text: str, font_name: str, font_size: float, bold: bool, italic: bool,
                              underline: bool, strikeout: bool, scale_x: float, spacing: float) -> Tuple[float, float, float, float]:
        """Measures text extents using Win32 GDI GetTextExtentPoint32W at 64x sub-pixel resolution."""
        gdi32 = ctypes.windll.gdi32
        hdc = cls._get_dc()

        hfont, tm = cls._get_scaled_font(font_name, font_size, bold, italic, underline, strikeout)

        # Selective Capa 2: If spacing is zero and text has OpenType ligatures, use shaped metrics
        if abs(spacing) < 1e-4 and len(text) > 1:
            try:
                advs, has_liga = cls.get_shaped_char_advances(font_name, font_size, bold, italic, underline, strikeout, text)
                if has_liga:
                    base_w = sum(advs) * (scale_x / 100.0)
                    height = float(font_size)
                    descent = float(tm.tmDescent) / 64.0
                    extlead = float(tm.tmExternalLeading) / 64.0
                    return base_w, height, descent, extlead
            except Exception:
                pass

        old_font = gdi32.SelectObject(hdc, hfont)

        sz = SIZE()
        gdi32.GetTextExtentPoint32W(hdc, text, len(text), ctypes.byref(sz))
        gdi32.SelectObject(hdc, old_font)

        # Direct conversion on 26.6 sub-pixel scale (64x)
        base_w = (float(sz.cx) / 64.0) * (scale_x / 100.0)
        calib = cls.get_font_calibration_ratio(font_name, font_size)
        base_w *= calib
        extra_spacing = float(spacing) * max(0, len(text) - 1) * (scale_x / 100.0)
        final_w = base_w + extra_spacing

        height = float(font_size)
        descent = float(tm.tmDescent) / 64.0
        extlead = float(tm.tmExternalLeading) / 64.0

        return final_w, height, descent, extlead

    @classmethod
    def _get_text_extents_fallback(cls, text: str, font_name: str, font_size: float, bold: bool, italic: bool,
                                   scale_x: float, spacing: float) -> Tuple[float, float, float, float]:
        """Fallback measuring text extents via PIL ImageFont or analytical bounding approximations."""
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

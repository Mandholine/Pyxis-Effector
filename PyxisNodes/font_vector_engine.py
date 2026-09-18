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

"""Canonical font vector extraction engine to ASSdraw format (m ... l ... b ...).
Supports Win32 GDI via ctypes on Windows with smooth fallback, normalized cache, and comprehensive context resolution.
"""

import ctypes
from ctypes import wintypes
import platform
import re
from typing import Optional, Dict, Any

PT_MOVETO = 0x06
PT_LINETO = 0x02
PT_BEZIERTO = 0x04
PT_CLOSEFIGURE = 0x01

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class SIZE(ctypes.Structure):
    _fields_ = [("cx", wintypes.LONG), ("cy", wintypes.LONG)]


class FontVectorEngine:
    """Canonical font-to-vector ASSdraw engine with normalized cache and context resolution."""

    MAX_CACHE_SIZE: int = 4096
    _cache: Dict[tuple, str] = {}

    @classmethod
    def clear_cache(cls):
        """Clears internal vector shapes cache."""
        cls._cache.clear()

    @classmethod
    def get_cache_size(cls) -> int:
        """Returns current number of cached items."""
        return len(cls._cache)

    @classmethod
    def extract_font_params(
        cls,
        text: str = "",
        context: Optional[dict] = None,
        font_name: Optional[str] = None,
        font_size: Optional[float] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        scale: float = 1.0,
        scale_x: Optional[float] = None,
        scale_y: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Canonically extracts typographic properties from text and context.

Hierarchically inspects:
1. Explicit user parameters.
2. Inline override tags (\\fn, \\fs, \\fscx, \\fscy, \\b, \\i) in unit or line text.
3. `styleref` object in `active_line`, `active_unit`, `line`, or `context`.
4. Size metrics (`unit.height`, `line.height`).
5. Standard guaranteed fallbacks.
"""
        unit = context.get('active_unit') if isinstance(context, dict) else (context.get('unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None))
        line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)

        txt_val = str(text) if (text is not None and str(text).strip() != "") else ""
        if not txt_val:
            if unit:
                txt_val = str(getattr(unit, 'text_stripped', getattr(unit, 'text', '')) or "")
            elif line:
                txt_val = str(getattr(line, 'text_stripped', getattr(line, 'text', '')) or "")

        if "{" in txt_val and "}" in txt_val:
            txt_val = re.sub(r'\{[^}]*\}', '', txt_val).strip()
        if r'\N' in txt_val or r'\n' in txt_val or r'\h' in txt_val:
            txt_val = txt_val.replace(r'\N', ' ').replace(r'\n', ' ').replace(r'\h', ' ')

        styleref = getattr(line, 'styleref', None) if line else None
        if not styleref and unit:
            styleref = getattr(unit, 'styleref', None)
            if not styleref and hasattr(unit, 'line') and getattr(unit, 'line', None):
                styleref = getattr(unit.line, 'styleref', None)
        if not styleref and isinstance(context, dict):
            styleref = context.get('styleref')

        if isinstance(styleref, dict):
            base_fn = str(styleref.get('Fontname', styleref.get('fontname', 'Arial')))
            try:
                base_fs = float(styleref.get('Fontsize', styleref.get('fontsize', 40.0)))
            except Exception:
                base_fs = float(getattr(unit, 'height', getattr(line, 'height', 40.0)) or 40.0)
            raw_b = styleref.get('Bold', styleref.get('bold', False))
            base_b = str(raw_b).strip() in ['1', '-1', 'true', 'True'] if not isinstance(raw_b, bool) else raw_b
            raw_i = styleref.get('Italic', styleref.get('italic', False))
            base_i = str(raw_i).strip() in ['1', '-1', 'true', 'True'] if not isinstance(raw_i, bool) else raw_i
            try:
                base_sc_x = float(styleref.get('ScaleX', styleref.get('scale_x', 100.0)))
            except Exception:
                base_sc_x = 100.0
            try:
                base_sc_y = float(styleref.get('ScaleY', styleref.get('scale_y', 100.0)))
            except Exception:
                base_sc_y = 100.0
        elif styleref:
            base_fn = str(getattr(styleref, 'fontname', 'Arial'))
            try:
                base_fs = float(getattr(styleref, 'fontsize', 40.0))
            except Exception:
                base_fs = float(getattr(unit, 'height', getattr(line, 'height', 40.0)) or 40.0)
            base_b = bool(getattr(styleref, 'bold', False))
            base_i = bool(getattr(styleref, 'italic', False))
            try:
                base_sc_x = float(getattr(styleref, 'scale_x', 100.0))
            except Exception:
                base_sc_x = 100.0
            try:
                base_sc_y = float(getattr(styleref, 'scale_y', 100.0))
            except Exception:
                base_sc_y = 100.0
        else:
            base_fn = "Arial"
            base_fs = float(getattr(unit, 'height', getattr(line, 'height', 40.0)) or 40.0)
            base_b = False
            base_i = False
            base_sc_x = 100.0
            base_sc_y = 100.0

        raw_text_src = (getattr(unit, 'text', '') or getattr(line, 'raw_text', '') or getattr(line, 'text', '') or '') if (unit or line) else ''
        if raw_text_src and '\\' in raw_text_src:
            fn_m = re.search(r'\\fn([^\\}]+)', raw_text_src)
            if fn_m:
                base_fn = fn_m.group(1).strip()
            fs_m = re.search(r'\\fs(\d+(?:\.\d+)?)', raw_text_src)
            if fs_m:
                try: base_fs = float(fs_m.group(1))
                except Exception: pass
            fscx_m = re.search(r'\\fscx(\d+(?:\.\d+)?)', raw_text_src)
            if fscx_m:
                try: base_sc_x = float(fscx_m.group(1))
                except Exception: pass
            fscy_m = re.search(r'\\fscy(\d+(?:\.\d+)?)', raw_text_src)
            if fscy_m:
                try: base_sc_y = float(fscy_m.group(1))
                except Exception: pass
            b_m = re.search(r'\\b([01])', raw_text_src)
            if b_m:
                base_b = (b_m.group(1) == '1')
            i_m = re.search(r'\\i([01])', raw_text_src)
            if i_m:
                base_i = (i_m.group(1) == '1')

        fn_final = str(font_name).strip() if (font_name is not None and str(font_name).strip() != "") else base_fn
        try:
            fs_final = float(font_size) if (font_size is not None and str(font_size).strip() != "") else base_fs
        except Exception:
            fs_final = base_fs
        b_final = bool(bold) if bold is not None else base_b
        i_final = bool(italic) if italic is not None else base_i
        try:
            sc_x_final = float(scale_x) if (scale_x is not None and str(scale_x).strip() != "") else base_sc_x
        except Exception:
            sc_x_final = base_sc_x
        try:
            sc_y_final = float(scale_y) if (scale_y is not None and str(scale_y).strip() != "") else base_sc_y
        except Exception:
            sc_y_final = base_sc_y
        try:
            scale_final = float(scale) if scale is not None else 1.0
        except Exception:
            scale_final = 1.0

        return {
            "text": txt_val,
            "font_name": fn_final,
            "font_size": fs_final,
            "bold": b_final,
            "italic": i_final,
            "scale": scale_final,
            "scale_x": sc_x_final,
            "scale_y": sc_y_final,
        }

    @classmethod
    def from_context(
        cls,
        text: str = "",
        context: Optional[dict] = None,
        font_name: Optional[str] = None,
        font_size: Optional[float] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        scale: float = 1.0,
        scale_x: Optional[float] = None,
        scale_y: Optional[float] = None,
    ) -> str:
        """Función canónica y especializada para convertir texto a vector ASSdraw usando el contexto completo."""
        params = cls.extract_font_params(
            text=text,
            context=context,
            font_name=font_name,
            font_size=font_size,
            bold=bold,
            italic=italic,
            scale=scale,
            scale_x=scale_x,
            scale_y=scale_y
        )
        if not params["text"]:
            return ""

        return cls.text_to_shape(
            text=params["text"],
            font_name=params["font_name"],
            font_size=params["font_size"],
            bold=params["bold"],
            italic=params["italic"],
            scale=params["scale"],
            scale_x=params["scale_x"],
            scale_y=params["scale_y"]
        )

    text_to_shape_from_context = from_context

    @classmethod
    def text_to_shape(
        cls,
        text: str,
        font_name: str = "Arial",
        font_size: float = 100.0,
        bold: bool = False,
        italic: bool = False,
        scale: float = 1.0,
        scale_x: float = 100.0,
        scale_y: float = 100.0
    ) -> str:
        """Convierte una cadena de texto a forma vectorial ASSdraw centrada con caché normalizado."""
        if not text or not str(text).strip():
            return ""

        text_str = str(text)
        fn_str = str(font_name or "Arial").strip().lower()
        try:
            fs_val = round(float(font_size), 2)
        except Exception:
            fs_val = 100.0
        b_val = bool(bold)
        i_val = bool(italic)
        try:
            sc_val = round(float(scale), 4)
        except Exception:
            sc_val = 1.0
        try:
            sc_x_val = round(float(scale_x), 2)
        except Exception:
            sc_x_val = 100.0
        try:
            sc_y_val = round(float(scale_y), 2)
        except Exception:
            sc_y_val = 100.0

        cache_key = (text_str, fn_str, fs_val, b_val, i_val, sc_val, sc_x_val, sc_y_val)
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        res = ""
        if platform.system() == "Windows":
            try:
                shape = cls._text_to_shape_gdi(text_str, font_name, fs_val, b_val, i_val, sc_val, sc_x_val, sc_y_val)
                if shape and shape != "m 0 0":
                    res = shape
            except Exception as e:
                print(f"[FontVectorEngine GDI Warning] {e}")

        if not res:
            res = cls._text_to_shape_fallback(text_str, fs_val, sc_val)

        if len(cls._cache) >= cls.MAX_CACHE_SIZE:
            keys_to_remove = list(cls._cache.keys())[:cls.MAX_CACHE_SIZE // 4]
            for k in keys_to_remove:
                cls._cache.pop(k, None)

        cls._cache[cache_key] = res
        return res

    @staticmethod
    def _text_to_shape_gdi(
        text: str,
        font_name: str,
        font_size: float,
        bold: bool,
        italic: bool,
        scale: float,
        scale_x: float = 100.0,
        scale_y: float = 100.0
    ) -> str:
        gdi32 = ctypes.windll.gdi32
        user32 = ctypes.windll.user32

        hdc = gdi32.CreateCompatibleDC(None)
        if not hdc:
            return ""

        gdi32.SetBkMode(hdc, 1)

        FW_BOLD = 700
        FW_NORMAL = 400
        weight = FW_BOLD if bold else FW_NORMAL
        height = abs(int(float(font_size) * 64))

        hfont = gdi32.CreateFontW(
            height, 0, 0, 0, weight, 1 if italic else 0, 0, 0,
            1, 0, 0, 4, 0, str(font_name)
        )
        if not hfont:
            gdi32.DeleteDC(hdc)
            return ""

        old_font = gdi32.SelectObject(hdc, hfont)

        text_w = str(text).rstrip()
        if not text_w:
            gdi32.SelectObject(hdc, old_font)
            gdi32.DeleteObject(hfont)
            gdi32.DeleteDC(hdc)
            return ""

        sz_c = SIZE()
        dx_array = None
        total_cx = 0.0

        if len(text_w) > 1:
            dx_list = []
            total_adv = 0
            for c in text_w:
                gdi32.GetTextExtentPoint32W(hdc, c, 1, ctypes.byref(sz_c))
                adv = int(round(sz_c.cx / 64.0))
                dx_list.append(adv * 64)
                total_adv += adv
            dx_array = (ctypes.c_int * len(text_w))(*dx_list)
            total_cx = float(total_adv) * 64.0
        else:
            sz_single = SIZE()
            gdi32.GetTextExtentPoint32W(hdc, text_w, len(text_w), ctypes.byref(sz_single))
            adv_single = int(round(sz_single.cx / 64.0))
            total_cx = float(adv_single) * 64.0

        gdi32.BeginPath(hdc)
        gdi32.ExtTextOutW(hdc, 0, 0, 0, None, text_w, len(text_w), dx_array)
        gdi32.EndPath(hdc)

        sz = SIZE()
        gdi32.GetTextExtentPoint32W(hdc, text_w, len(text_w), ctypes.byref(sz))

        num_points = gdi32.GetPath(hdc, None, None, 0)
        if num_points <= 0:
            gdi32.SelectObject(hdc, old_font)
            gdi32.DeleteObject(hfont)
            gdi32.DeleteDC(hdc)
            return ""

        points = (POINT * num_points)()
        types = (ctypes.c_byte * num_points)()

        gdi32.GetPath(hdc, points, types, num_points)

        gdi32.SelectObject(hdc, old_font)
        gdi32.DeleteObject(hfont)
        gdi32.DeleteDC(hdc)

        ass_parts = []
        i = 0
        scale_factor_x = (1.0 / 64.0) * float(scale) * (float(scale_x) / 100.0)
        scale_factor_y = (1.0 / 64.0) * float(scale) * (float(scale_y) / 100.0)

        layout_cx = (total_cx * scale_factor_x) / 2.0
        layout_cy = (sz.cy * scale_factor_y) / 2.0

        while i < num_points:
            pt_type = types[i]
            base_type = pt_type & ~PT_CLOSEFIGURE
            x = round(points[i].x * scale_factor_x - layout_cx, 2)
            y = round(points[i].y * scale_factor_y - layout_cy, 2)

            if base_type == PT_MOVETO:
                ass_parts.append(f"m {x} {y}")
                i += 1
            elif base_type == PT_LINETO:
                ass_parts.append(f"l {x} {y}")
                i += 1
            elif base_type == PT_BEZIERTO:
                if i + 2 < num_points:
                    x1, y1 = round(points[i].x * scale_factor_x - layout_cx, 2), round(points[i].y * scale_factor_y - layout_cy, 2)
                    x2, y2 = round(points[i+1].x * scale_factor_x - layout_cx, 2), round(points[i+1].y * scale_factor_y - layout_cy, 2)
                    x3, y3 = round(points[i+2].x * scale_factor_x - layout_cx, 2), round(points[i+2].y * scale_factor_y - layout_cy, 2)
                    ass_parts.append(f"b {x1} {y1} {x2} {y2} {x3} {y3}")
                    i += 3
                else:
                    ass_parts.append(f"l {x} {y}")
                    i += 1
            else:
                i += 1

        raw_shape = " ".join(ass_parts)
        return raw_shape

    @staticmethod
    def _text_to_shape_fallback(text: str, font_size: float, scale: float) -> str:
        """Fallback aproximado de caja contenedora vectorial centrado en (0, 0)."""
        width = float(len(text) * float(font_size) * 0.6 * float(scale))
        height = float(float(font_size) * float(scale))
        hw, hh = round(width * 0.5, 2), round(height * 0.5, 2)
        return f"m {-hw} {-hh} l {hw} {-hh} l {hw} {hh} l {-hw} {hh}"

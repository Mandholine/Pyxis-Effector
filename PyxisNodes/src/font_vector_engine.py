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

from dataclasses import dataclass
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
        ("tmCharSet", wintypes.BYTE),
    ]

@dataclass(frozen=True)
class FontVectorMetrics:
    """Retiene la ficha métrica completa y no destructiva de la fuente y de la forma vectorial."""
    shape: str = ""
    advance_width: float = 0.0
    cell_height: float = 0.0
    ascent: float = 0.0
    descent: float = 0.0
    spacing: float = 0.0
    lsb: float = 0.0
    rsb: float = 0.0
    ink_min_x: float = 0.0
    ink_min_y: float = 0.0
    ink_max_x: float = 0.0
    ink_max_y: float = 0.0
    ink_width: float = 0.0
    ink_height: float = 0.0
    delta_x: float = 0.0
    delta_y: float = 0.0

class FontVectorEngine:
    """Canonical font-to-vector ASSdraw engine with normalized cache and context resolution."""

    MAX_CACHE_SIZE: int = 4096
    _cache: Dict[tuple, FontVectorMetrics] = {}

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
        spacing: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Canonically extracts typographic properties from text and context.

Hierarchically inspects:
1. Explicit user parameters.
2. Inline override tags (\\fn, \\fs, \\fscx, \\fscy, \\fsp, \\b, \\i) in unit or line text.
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
            styleref = context.get('styleref') or context.get('style')

        style_override = getattr(unit, 'style_override', None) or getattr(line, 'style_override', None)
        if style_override is not None:
            base_fn = style_override.fontname
            base_fs = style_override.fontsize
            base_b = style_override.bold
            base_i = style_override.italic
            base_sc_x = style_override.scale_x
            base_sc_y = style_override.scale_y
            base_spacing = style_override.spacing
        elif isinstance(styleref, dict):
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
            try:
                base_spacing = float(styleref.get('Spacing', styleref.get('spacing', 0.0)))
            except Exception:
                base_spacing = 0.0
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
            try:
                base_spacing = float(getattr(styleref, 'spacing', 0.0))
            except Exception:
                base_spacing = 0.0
        else:
            base_fn = "Arial"
            base_fs = float(getattr(unit, 'height', getattr(line, 'height', 40.0)) or 40.0)
            base_b = False
            base_i = False
            base_sc_x = 100.0
            base_sc_y = 100.0
            base_spacing = 0.0

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
            fsp_m = re.search(r'\\fsp(-?\d+(?:\.\d+)?)', raw_text_src)
            if fsp_m:
                try: base_spacing = float(fsp_m.group(1))
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
            spacing_final = float(spacing) if (spacing is not None and str(spacing).strip() != "") else base_spacing
        except Exception:
            spacing_final = base_spacing
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
            "spacing": spacing_final,
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
        spacing: Optional[float] = None,
        anchor: str = "typographic"
    ) -> str:
        """Función canónica para convertir texto a vector ASSdraw usando el contexto completo."""
        metrics = cls.get_metrics_from_context(
            text=text,
            context=context,
            font_name=font_name,
            font_size=font_size,
            bold=bold,
            italic=italic,
            scale=scale,
            scale_x=scale_x,
            scale_y=scale_y,
            spacing=spacing,
            anchor=anchor
        )
        return metrics.shape if metrics else ""

    text_to_shape_from_context = from_context

    @classmethod
    def get_metrics_from_context(
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
        spacing: Optional[float] = None,
        anchor: str = "typographic"
    ) -> FontVectorMetrics:
        """Extrae la ficha métrica completa y no destructiva de la fuente y de la forma vectorial."""
        params = cls.extract_font_params(
            text=text,
            context=context,
            font_name=font_name,
            font_size=font_size,
            bold=bold,
            italic=italic,
            scale=scale,
            scale_x=scale_x,
            scale_y=scale_y,
            spacing=spacing
        )
        if not params["text"]:
            return FontVectorMetrics()

        return cls.get_metrics(
            text=params["text"],
            font_name=params["font_name"],
            font_size=params["font_size"],
            bold=params["bold"],
            italic=params["italic"],
            scale=params["scale"],
            scale_x=params["scale_x"],
            scale_y=params["scale_y"],
            spacing=params["spacing"],
            anchor=anchor
        )

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
        scale_y: float = 100.0,
        spacing: float = 0.0,
        anchor: str = "typographic"
    ) -> str:
        """Convierte una cadena de texto a forma vectorial ASSdraw con caché normalizado."""
        metrics = cls.get_metrics(
            text=text,
            font_name=font_name,
            font_size=font_size,
            bold=bold,
            italic=italic,
            scale=scale,
            scale_x=scale_x,
            scale_y=scale_y,
            spacing=spacing,
            anchor=anchor
        )
        return metrics.shape if metrics else ""

    @classmethod
    def get_metrics(
        cls,
        text: str,
        font_name: str = "Arial",
        font_size: float = 100.0,
        bold: bool = False,
        italic: bool = False,
        scale: float = 1.0,
        scale_x: float = 100.0,
        scale_y: float = 100.0,
        spacing: float = 0.0,
        anchor: str = "typographic"
    ) -> FontVectorMetrics:
        """Retorna la ficha métrica completa de vector y tipografía con caché normalizado."""
        if not text or not str(text).strip():
            return FontVectorMetrics()

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
        try:
            sp_val = round(float(spacing), 3)
        except Exception:
            sp_val = 0.0
        anchor_val = str(anchor or "typographic").strip().lower()

        cache_key = (text_str, fn_str, fs_val, b_val, i_val, sc_val, sc_x_val, sc_y_val, sp_val, anchor_val)
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        res_metrics: Optional[FontVectorMetrics] = None
        if platform.system() == "Windows":
            try:
                res_metrics = cls._text_to_shape_gdi(
                    text_str, font_name, fs_val, b_val, i_val, sc_val, sc_x_val, sc_y_val, sp_val, anchor_val
                )
            except Exception as e:
                print(f"[FontVectorEngine GDI Warning] {e}")

        if not res_metrics or not res_metrics.shape or res_metrics.shape == "m 0 0":
            try:
                res_metrics = cls._text_to_shape_freetype(
                    text_str, font_name, fs_val, b_val, i_val, sc_val, sc_x_val, sc_y_val, sp_val, anchor_val
                )
            except Exception as e:
                print(f"[FontVectorEngine FreeType Warning] {e}")
                res_metrics = None

        if not res_metrics or not res_metrics.shape or res_metrics.shape == "m 0 0":
            res_metrics = cls._text_to_shape_fallback(
                text_str, fs_val, sc_val, sc_x_val, sc_y_val, sp_val, anchor_val
            )

        if len(cls._cache) >= cls.MAX_CACHE_SIZE:
            keys_to_remove = list(cls._cache.keys())[:cls.MAX_CACHE_SIZE // 4]
            for k in keys_to_remove:
                cls._cache.pop(k, None)

        cls._cache[cache_key] = res_metrics
        return res_metrics

    @staticmethod
    def _text_to_shape_gdi(
        text: str,
        font_name: str,
        font_size: float,
        bold: bool,
        italic: bool,
        scale: float,
        scale_x: float = 100.0,
        scale_y: float = 100.0,
        spacing: float = 0.0,
        anchor: str = "typographic"
    ) -> FontVectorMetrics:
        gdi32 = ctypes.windll.gdi32

        hdc = gdi32.CreateCompatibleDC(None)
        if not hdc:
            return FontVectorMetrics()

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
            return FontVectorMetrics()

        old_font = gdi32.SelectObject(hdc, hfont)

        text_w = str(text).rstrip()
        if not text_w:
            gdi32.SelectObject(hdc, old_font)
            gdi32.DeleteObject(hfont)
            gdi32.DeleteDC(hdc)
            return FontVectorMetrics()

        tm = TEXTMETRICW()
        gdi32.GetTextMetricsW(hdc, ctypes.byref(tm))

        sz_c = SIZE()
        dx_array = None
        total_cx = 0.0
        sp_subpixel = float(spacing) * 64.0

        if len(text_w) > 1:
            dx_list = []
            total_adv = 0.0
            for idx, c in enumerate(text_w):
                gdi32.GetTextExtentPoint32W(hdc, c, 1, ctypes.byref(sz_c))
                adv_64 = float(sz_c.cx)
                if idx < len(text_w) - 1:
                    adv_with_sp = adv_64 + sp_subpixel
                else:
                    adv_with_sp = adv_64
                adv_int = int(round(adv_with_sp))
                dx_list.append(adv_int)
                total_adv += adv_with_sp
            dx_array = (ctypes.c_int * len(text_w))(*dx_list)
            total_cx = total_adv
        else:
            sz_single = SIZE()
            gdi32.GetTextExtentPoint32W(hdc, text_w, len(text_w), ctypes.byref(sz_single))
            total_cx = float(sz_single.cx)

        gdi32.BeginPath(hdc)
        gdi32.ExtTextOutW(hdc, 0, 0, 0, None, text_w, len(text_w), dx_array)
        gdi32.EndPath(hdc)

        sz = SIZE()
        gdi32.GetTextExtentPoint32W(hdc, text_w, len(text_w), ctypes.byref(sz))

        num_points = gdi32.GetPath(hdc, None, None, 0)
        scale_factor_x = (1.0 / 64.0) * float(scale) * (float(scale_x) / 100.0)
        scale_factor_y = (1.0 / 64.0) * float(scale) * (float(scale_y) / 100.0)

        adv_w = round(total_cx * scale_factor_x, 3)
        cell_h = round(tm.tmHeight * scale_factor_y, 3)
        ascent_val = round(tm.tmAscent * scale_factor_y, 3)
        descent_val = round(tm.tmDescent * scale_factor_y, 3)

        if num_points <= 0:
            gdi32.SelectObject(hdc, old_font)
            gdi32.DeleteObject(hfont)
            gdi32.DeleteDC(hdc)
            return FontVectorMetrics(
                shape="",
                advance_width=adv_w,
                cell_height=cell_h,
                ascent=ascent_val,
                descent=descent_val,
                spacing=float(spacing)
            )

        points = (POINT * num_points)()
        types = (ctypes.c_byte * num_points)()

        gdi32.GetPath(hdc, points, types, num_points)

        gdi32.SelectObject(hdc, old_font)
        gdi32.DeleteObject(hfont)
        gdi32.DeleteDC(hdc)

        min_px = min(points[i].x for i in range(num_points))
        max_px = max(points[i].x for i in range(num_points))
        min_py = min(points[i].y for i in range(num_points))
        max_py = max(points[i].y for i in range(num_points))

        lsb_val = round(min_px * scale_factor_x, 3)
        rsb_val = round(adv_w - (max_px * scale_factor_x), 3)
        ink_w = round(max(0.0, (max_px - min_px) * scale_factor_x), 3)
        ink_h = round(max(0.0, (max_py - min_py) * scale_factor_y), 3)

        typographic_cx = (total_cx * scale_factor_x) / 2.0
        typographic_cy = (sz.cy * scale_factor_y) / 2.0

        ink_cx = ((min_px + max_px) * scale_factor_x) / 2.0
        ink_cy = ((min_py + max_py) * scale_factor_y) / 2.0

        delta_x = round(ink_cx - typographic_cx, 3)
        delta_y = round(ink_cy - typographic_cy, 3)

        ink_min_x = round(min_px * scale_factor_x - typographic_cx, 3)
        ink_max_x = round(max_px * scale_factor_x - typographic_cx, 3)
        ink_min_y = round(min_py * scale_factor_y - typographic_cy, 3)
        ink_max_y = round(max_py * scale_factor_y - typographic_cy, 3)

        anchor_clean = str(anchor).strip().lower()
        if anchor_clean == "ink":
            layout_cx = ink_cx
            layout_cy = ink_cy
        elif anchor_clean in ("origin", "baseline"):
            layout_cx = 0.0
            layout_cy = tm.tmAscent * scale_factor_y
        else:
            # Default: typographic
            layout_cx = typographic_cx
            layout_cy = typographic_cy

        ass_parts = []
        i = 0
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

        return FontVectorMetrics(
            shape=raw_shape,
            advance_width=adv_w,
            cell_height=cell_h,
            ascent=ascent_val,
            descent=descent_val,
            spacing=float(spacing),
            lsb=lsb_val,
            rsb=rsb_val,
            ink_min_x=ink_min_x,
            ink_min_y=ink_min_y,
            ink_max_x=ink_max_x,
            ink_max_y=ink_max_y,
            ink_width=ink_w,
            ink_height=ink_h,
            delta_x=delta_x,
            delta_y=delta_y
        )

    # ------------------------------------------------------------------
    # FreeType outline extraction (Linux / macOS / fallback universal)
    # ------------------------------------------------------------------

    @staticmethod
    def _decompose_contour(pts, tgs):
        """Descompone un contorno TrueType en segmentos ('l', p) / ('q', ctrl, p) / ('c', c1, c2, p).

        Reproduce la semántica de FT_Outline_Decompose: puntos ON=1, CONIC=0, CUBIC=2.
        """
        ON, CONIC, CUBIC = 1, 0, 2

        def mid(a, b):
            return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5)

        n = len(pts)
        if n == 0:
            return [], None
        if n == 1:
            return [], pts[0]

        segs = []
        # Resolución del punto inicial (puede ser virtual)
        if tgs[0] == ON:
            start = pts[0]
            i0 = 1
        elif tgs[0] == CONIC:
            if tgs[n - 1] == ON:
                start = pts[n - 1]; n -= 1; i0 = 1
            elif tgs[n - 1] == CONIC:
                start = mid(pts[n - 1], pts[0]); n -= 1; i0 = 1
            else:
                start = pts[0]; i0 = 1
        else:  # CUBIC inicial (raro)
            if tgs[n - 1] == ON:
                start = pts[n - 1]; n -= 1; i0 = 1
            else:
                start = pts[0]; i0 = 1

        pend_conic = None
        pend_cubic = []

        for i in range(i0, n):
            tag = tgs[i]
            p = pts[i]
            if tag == ON:
                if pend_conic is not None:
                    segs.append(("q", pend_conic, p))
                    pend_conic = None
                elif pend_cubic:
                    c1 = pend_cubic[0]
                    c2 = pend_cubic[1] if len(pend_cubic) > 1 else pend_cubic[0]
                    segs.append(("c", c1, c2, p))
                    pend_cubic = []
                else:
                    segs.append(("l", p))
            elif tag == CONIC:
                if pend_conic is not None:
                    mp = mid(pend_conic, p)
                    segs.append(("q", pend_conic, mp))
                pend_conic = p
            else:  # CUBIC
                pend_cubic.append(p)

        # Cierre del contorno (segmento implícito final hacia el inicio)
        if pend_conic is not None:
            segs.append(("q", pend_conic, start))
        elif pend_cubic:
            c1 = pend_cubic[0]
            c2 = pend_cubic[1] if len(pend_cubic) > 1 else pend_cubic[0]
            segs.append(("c", c1, c2, start))
        return segs, start

    @staticmethod
    def _conic_to_cubic(p0, q, p2):
        """Elevación exacta de curva cuadrática (quadratic) a cúbica para ASS 'b'."""
        c1 = (p0[0] + 2.0 / 3.0 * (q[0] - p0[0]), p0[1] + 2.0 / 3.0 * (q[1] - p0[1]))
        c2 = (p2[0] + 2.0 / 3.0 * (q[0] - p2[0]), p2[1] + 2.0 / 3.0 * (q[1] - p2[1]))
        return c1, c2

    @classmethod
    def _text_to_shape_freetype(
        cls,
        text: str,
        font_name: str,
        font_size: float,
        bold: bool,
        italic: bool,
        scale: float,
        scale_x: float = 100.0,
        scale_y: float = 100.0,
        spacing: float = 0.0,
        anchor: str = "typographic"
    ) -> FontVectorMetrics:
        """Extrae contornos reales de glifos vía FreeType, equivalente al camino GDI.

        Requiere freetype-py (opcional) y una fuente resuelta (fontconfig).
        Coordina exactamente la misma notación de salida ASS y el sistema de
        anclas que _text_to_shape_gdi.
        """
        import freetype
        from font_resolver import resolve_font_file

        text_w = str(text).rstrip()
        if not text_w:
            return FontVectorMetrics()

        font_path = resolve_font_file(font_name, bold=bold, italic=italic)
        if not font_path:
            return FontVectorMetrics()

        face = freetype.Face(font_path)
        face.set_char_size(int(round(float(font_size) * 64.0)))

        tm_height = float(face.size.height)      # 26.6
        tm_ascent = float(face.size.ascender)    # 26.6
        tm_descent = abs(float(face.size.descender))

        sp_subpixel = float(spacing) * 64.0
        pen_x = 0.0
        total_cx = 0.0
        all_points = []   # (x, y) en unidades 26.6, y positivo hacia ABAJO (convención GDI)

        for idx, ch in enumerate(text_w):
            face.load_char(ch, freetype.FT_LOAD_NO_BITMAP | freetype.FT_LOAD_NO_HINTING)
            glyph = face.glyph
            outline = glyph.outline

            pts = [(float(p[0]), -float(p[1])) for p in outline.points]  # invertir eje Y (FreeType y-up -> GDI y-down)
            tgs = []
            for t in outline.tags:
                t = int(t)
                if t & 1:
                    tgs.append(1)        # ON
                elif t & 2:
                    tgs.append(2)        # CUBIC
                else:
                    tgs.append(0)        # CONIC

            offset_pts = [(x + pen_x, y) for (x, y) in pts]

            c_start = 0
            for c_end in list(outline.contours):
                contour_pts = offset_pts[c_start:c_end + 1]
                contour_tgs = tgs[c_start:c_end + 1]
                segs, start = cls._decompose_contour(contour_pts, contour_tgs)
                if start is not None:
                    all_points.append(start)
                    for seg in segs:
                        if seg[0] == "l":
                            all_points.append(seg[1])
                        elif seg[0] == "q":
                            all_points.append(seg[1])
                            all_points.append(seg[2])
                        else:
                            all_points.append(seg[1])
                            all_points.append(seg[2])
                            all_points.append(seg[3])
                c_start = c_end + 1

            adv_64 = float(glyph.metrics.horiAdvance)
            if idx < len(text_w) - 1:
                pen_x += adv_64 + sp_subpixel
                total_cx += adv_64 + sp_subpixel
            else:
                pen_x += adv_64
                total_cx += adv_64

        if not all_points:
            return FontVectorMetrics()

        scale_factor_x = (1.0 / 64.0) * float(scale) * (float(scale_x) / 100.0)
        scale_factor_y = (1.0 / 64.0) * float(scale) * (float(scale_y) / 100.0)

        adv_w = round(total_cx * scale_factor_x, 3)
        cell_h = round(tm_height * scale_factor_y, 3)
        ascent_val = round(tm_ascent * scale_factor_y, 3)
        descent_val = round(tm_descent * scale_factor_y, 3)

        min_px = min(p[0] for p in all_points)
        max_px = max(p[0] for p in all_points)
        min_py = min(p[1] for p in all_points)
        max_py = max(p[1] for p in all_points)

        lsb_val = round(min_px * scale_factor_x, 3)
        rsb_val = round(adv_w - (max_px * scale_factor_x), 3)
        ink_w = round(max(0.0, (max_px - min_px) * scale_factor_x), 3)
        ink_h = round(max(0.0, (max_py - min_py) * scale_factor_y), 3)

        typographic_cx = (total_cx * scale_factor_x) / 2.0
        typographic_cy = (tm_height * scale_factor_y) / 2.0

        ink_cx = ((min_px + max_px) * scale_factor_x) / 2.0
        ink_cy = ((min_py + max_py) * scale_factor_y) / 2.0

        delta_x = round(ink_cx - typographic_cx, 3)
        delta_y = round(ink_cy - typographic_cy, 3)

        ink_min_x = round(min_px * scale_factor_x - typographic_cx, 3)
        ink_max_x = round(max_px * scale_factor_x - typographic_cx, 3)
        ink_min_y = round(min_py * scale_factor_y - typographic_cy, 3)
        ink_max_y = round(max_py * scale_factor_y - typographic_cy, 3)

        anchor_clean = str(anchor).strip().lower()
        if anchor_clean == "ink":
            layout_cx = ink_cx
            layout_cy = ink_cy
        elif anchor_clean in ("origin", "baseline"):
            layout_cx = 0.0
            layout_cy = tm_ascent * scale_factor_y
        else:
            layout_cx = typographic_cx
            layout_cy = typographic_cy

        # Segunda pasada: emisión de la polilínea ASS con la misma semántica GDI
        pen_x = 0.0
        ass_parts = []
        for idx, ch in enumerate(text_w):
            face.load_char(ch, freetype.FT_LOAD_NO_BITMAP | freetype.FT_LOAD_NO_HINTING)
            glyph = face.glyph
            outline = glyph.outline

            pts = [(float(p[0]), -float(p[1])) for p in outline.points]
            tgs = []
            for t in outline.tags:
                t = int(t)
                if t & 1:
                    tgs.append(1)
                elif t & 2:
                    tgs.append(2)
                else:
                    tgs.append(0)

            offset_pts = [(x + pen_x, y) for (x, y) in pts]

            c_start = 0
            for c_end in list(outline.contours):
                contour_pts = offset_pts[c_start:c_end + 1]
                contour_tgs = tgs[c_start:c_end + 1]
                segs, start = cls._decompose_contour(contour_pts, contour_tgs)
                if start is not None:
                    sx = round(start[0] * scale_factor_x - layout_cx, 2)
                    sy = round(start[1] * scale_factor_y - layout_cy, 2)
                    ass_parts.append(f"m {sx} {sy}")
                    for seg in segs:
                        if seg[0] == "l":
                            x = round(seg[1][0] * scale_factor_x - layout_cx, 2)
                            y = round(seg[1][1] * scale_factor_y - layout_cy, 2)
                            ass_parts.append(f"l {x} {y}")
                        elif seg[0] == "q":
                            c1, c2 = cls._conic_to_cubic(start, seg[1], seg[2])
                            start_q = seg[2]
                            x1 = round(c1[0] * scale_factor_x - layout_cx, 2); y1 = round(c1[1] * scale_factor_y - layout_cy, 2)
                            x2 = round(c2[0] * scale_factor_x - layout_cx, 2); y2 = round(c2[1] * scale_factor_y - layout_cy, 2)
                            x3 = round(start_q[0] * scale_factor_x - layout_cx, 2); y3 = round(start_q[1] * scale_factor_y - layout_cy, 2)
                            ass_parts.append(f"b {x1} {y1} {x2} {y2} {x3} {y3}")
                            start = start_q
                        else:
                            x1 = round(seg[1][0] * scale_factor_x - layout_cx, 2); y1 = round(seg[1][1] * scale_factor_y - layout_cy, 2)
                            x2 = round(seg[2][0] * scale_factor_x - layout_cx, 2); y2 = round(seg[2][1] * scale_factor_y - layout_cy, 2)
                            x3 = round(seg[3][0] * scale_factor_x - layout_cx, 2); y3 = round(seg[3][1] * scale_factor_y - layout_cy, 2)
                            ass_parts.append(f"b {x1} {y1} {x2} {y2} {x3} {y3}")
                            start = seg[3]
                c_start = c_end + 1

            adv_64 = float(glyph.metrics.horiAdvance)
            if idx < len(text_w) - 1:
                pen_x += adv_64 + sp_subpixel

        raw_shape = " ".join(ass_parts)

        return FontVectorMetrics(
            shape=raw_shape,
            advance_width=adv_w,
            cell_height=cell_h,
            ascent=ascent_val,
            descent=descent_val,
            spacing=float(spacing),
            lsb=lsb_val,
            rsb=rsb_val,
            ink_min_x=ink_min_x,
            ink_min_y=ink_min_y,
            ink_max_x=ink_max_x,
            ink_max_y=ink_max_y,
            ink_width=ink_w,
            ink_height=ink_h,
            delta_x=delta_x,
            delta_y=delta_y
        )

    @staticmethod
    def _text_to_shape_fallback(
        text: str,
        font_size: float,
        scale: float,
        scale_x: float = 100.0,
        scale_y: float = 100.0,
        spacing: float = 0.0,
        anchor: str = "typographic"
    ) -> FontVectorMetrics:
        """Fallback aproximado de caja contenedora vectorial centrado en (0, 0) con métricas."""
        extra_sp = float(spacing) * max(0, len(text) - 1)
        width = (float(len(text) * float(font_size) * 0.6) + extra_sp) * (float(scale_x) / 100.0) * float(scale)
        height = float(float(font_size) * (float(scale_y) / 100.0) * float(scale))
        hw, hh = round(width * 0.5, 2), round(height * 0.5, 2)
        shape_str = f"m {-hw} {-hh} l {hw} {-hh} l {hw} {hh} l {-hw} {hh}"
        return FontVectorMetrics(
            shape=shape_str,
            advance_width=round(width, 3),
            cell_height=round(height, 3),
            ascent=round(height * 0.8, 3),
            descent=round(height * 0.2, 3),
            spacing=float(spacing),
            lsb=0.0,
            rsb=0.0,
            ink_min_x=-hw,
            ink_min_y=-hh,
            ink_max_x=hw,
            ink_max_y=hh,
            ink_width=round(width, 3),
            ink_height=round(height, 3),
            delta_x=0.0,
            delta_y=0.0
        )

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

# font_vector_engine.py
"""Motor de extracción vectorial de fuentes a formato ASSdraw (m ... l ... b ...).
Soporta GDI Win32 mediante ctypes en Windows con fallback suavizado.
"""

import ctypes
from ctypes import wintypes
import platform

# Constantes GDI Win32
PT_MOVETO = 0x06
PT_LINETO = 0x02
PT_BEZIERTO = 0x04
PT_CLOSEFIGURE = 0x01

# GDI Structs
class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class FontVectorEngine:
    """Motor de fuentes a vectores ASSdraw."""

    _cache = {}

    @staticmethod
    def text_to_shape(text: str, font_name: str = "Arial", font_size: int = 100, bold: bool = False, italic: bool = False, scale: float = 1.0, scale_x: float = 100.0, scale_y: float = 100.0) -> str:
        if not text or not str(text).strip():
            return ""

        text_str = str(text)
        cache_key = (text_str, str(font_name), int(font_size), bool(bold), bool(italic), float(scale), float(scale_x), float(scale_y))
        if cache_key in FontVectorEngine._cache:
            return FontVectorEngine._cache[cache_key]

        res = ""
        if platform.system() == "Windows":
            try:
                shape = FontVectorEngine._text_to_shape_gdi(text_str, font_name, font_size, bold, italic, scale, scale_x, scale_y)
                if shape and shape != "m 0 0":
                    res = shape
            except Exception as e:
                print(f"[FontVectorEngine GDI Warning] {e}")

        if not res:
            res = FontVectorEngine._text_to_shape_fallback(text_str, font_size, scale)

        FontVectorEngine._cache[cache_key] = res
        return res

    @staticmethod
    def _text_to_shape_gdi(text: str, font_name: str, font_size: int, bold: bool, italic: bool, scale: float, scale_x: float = 100.0, scale_y: float = 100.0) -> str:
        gdi32 = ctypes.windll.gdi32
        user32 = ctypes.windll.user32

        hdc = gdi32.CreateCompatibleDC(None)
        if not hdc:
            return ""

        # Modo transparente para evitar dibujar el cuadro del fondo
        gdi32.SetBkMode(hdc, 1) # TRANSPARENT = 1

        # LogFont (idéntico a FONT_PRECISION = 64 en newkara_library.lua de Kara Effector)
        FW_BOLD = 700
        FW_NORMAL = 400
        weight = FW_BOLD if bold else FW_NORMAL
        height = abs(int(font_size * 64))

        hfont = gdi32.CreateFontW(
            height, 0, 0, 0, weight, 1 if italic else 0, 0, 0,
            1, 0, 0, 4, 0, str(font_name)
        )
        if not hfont:
            gdi32.DeleteDC(hdc)
            return ""

        old_font = gdi32.SelectObject(hdc, hfont)

        # Draw path (eliminar espacios finales igual a newkara_library.lua para evitar desplazamiento horizontal)
        text_w = str(text).rstrip()
        if not text_w:
            gdi32.SelectObject(hdc, old_font)
            gdi32.DeleteObject(hfont)
            gdi32.DeleteDC(hdc)
            return ""

        gdi32.BeginPath(hdc)
        gdi32.ExtTextOutW(hdc, 0, 0, 0, None, text_w, len(text_w), None)
        gdi32.EndPath(hdc)

        # Obtener dimensiones de la caja tipográfica (Layout Box) mediante GetTextExtentPoint32W
        class SIZE(ctypes.Structure):
            _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]
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

        # Parse points into ASSdraw string (m x y l x y b x y x y x y)
        ass_parts = []
        i = 0
        scale_factor_x = (1.0 / 64.0) * float(scale) * (float(scale_x) / 100.0)
        scale_factor_y = (1.0 / 64.0) * float(scale) * (float(scale_y) / 100.0)

        while i < num_points:
            pt_type = types[i]
            base_type = pt_type & ~PT_CLOSEFIGURE
            x = round(points[i].x * scale_factor_x, 2)
            y = round(points[i].y * scale_factor_y, 2)

            if base_type == PT_MOVETO:
                ass_parts.append(f"m {x} {y}")
                i += 1
            elif base_type == PT_LINETO:
                ass_parts.append(f"l {x} {y}")
                i += 1
            elif base_type == PT_BEZIERTO:
                if i + 2 < num_points:
                    x1, y1 = round(points[i].x * scale_factor_x, 2), round(points[i].y * scale_factor_y, 2)
                    x2, y2 = round(points[i+1].x * scale_factor_x, 2), round(points[i+1].y * scale_factor_y, 2)
                    x3, y3 = round(points[i+2].x * scale_factor_x, 2), round(points[i+2].y * scale_factor_y, 2)
                    ass_parts.append(f"b {x1} {y1} {x2} {y2} {x3} {y3}")
                    i += 3
                else:
                    ass_parts.append(f"l {x} {y}")
                    i += 1
            else:
                i += 1

        raw_shape = " ".join(ass_parts)
        if not raw_shape:
            return ""

        # Centrado automático en (0, 0) según el Layout Box (idéntico a text.to_shape_ill de Seijitsu Extensions)
        layout_cx = (sz.cx * scale_factor_x) / 2.0
        layout_cy = (sz.cy * scale_factor_y) / 2.0
        from clipper_engine import ClipperEngine
        raw_shape = ClipperEngine.transform_shape(raw_shape, mode="Offset", offset_x=-layout_cx, offset_y=-layout_cy)

        return raw_shape

    @staticmethod
    def _text_to_shape_fallback(text: str, font_size: int, scale: float) -> str:
        """Fallback aproximado de caja contenedora vectorial centrado en (0, 0)."""
        width = float(len(text) * font_size * 0.6 * scale)
        height = float(font_size * scale)
        hw, hh = round(width * 0.5, 2), round(height * 0.5, 2)
        return f"m {-hw} {-hh} l {hw} {-hh} l {hw} {hh} l {-hw} {hh}"

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

# PyxisNodes/nodes/shape_nodes.py
"""Nodos de figuras vectoriales fijas (~100x100) de Kara Effector (sin entradas, 1 salida Dato)."""

import re
from decorators import pyxis_node

# -----------------------------------------------------------------------------
# SHAPE FUNCIONES INTERNAS PARA SHAPES LIB
# -----------------------------------------------------------------------------
def shape_circulo(context):
    return "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 "

def shape_cuadrado(context):
    return "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0 "

def shape_rectangulo(context):
    return "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0 "

def shape_triangulo(context):
    return "m 50 0 l 0 86 l 100 86 l 50 0 "

def shape_rombo(context):
    return "m 50 0 l 0 50 l 50 100 l 100 50 l 50 0 "

def shape_esquinas_redondeadas(context):
    return "m 20 0 b 8 0 0 8 0 20 l 0 80 b 0 92 8 100 20 100 l 80 100 b 92 100 100 92 100 80 l 100 20 b 100 8 92 0 80 0 l 20 0 "

def shape_pentagono(context):
    return "m 50 0 l 0 36 l 19 95 l 81 95 l 100 36 l 50 0 "

def shape_hexagono(context):
    return "m 100 43.301 l 75 0 l 25 0 l 0 43.301 l 25 86.602 l 75 86.602 l 100 43.301 "

def shape_octagono(context):
    return "m 29 0 l 0 29 l 0 71 l 29 100 l 71 100 l 100 71 l 100 29 l 71 0 l 29 0 "

def shape_estrella(context):
    return "m 38 36 l 0 36 l 31 59 l 20 95 l 50 72 l 81 94 l 69 59 l 100 36 l 62 36 l 50 0 l 38 36 "

def shape_corazon(context):
    return "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 106 b 75 71 100 68 100 40 b 100 16 68 0 50 25 "

# -----------------------------------------------------------------------------
# SHAPE/ESTRELLAS
# -----------------------------------------------------------------------------
def shape_estrella_1t(context):
    return "m 0 35 l 29 56 l 33 55 b 37 44 42 66 34 58 l 30 60 l 18 95 l 48 73 l 48 69 b 38 63 60 63 51 69 l 51 73 l 81 95 l 70 60 l 65 58 b 57 65 63 44 66 55 l 71 56 l 100 35 l 63 35 l 61 39 b 64 48 47 36 59 36 l 61 33 l 50 0 l 38 33 l 40 36 b 52 36 36 49 38 39 l 36 35 l 0 35 "

def shape_estrella_2t(context):
    return "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26 l 33 29 b 50 16 50 16 67 29 b 86 37 86 37 83 58 b 86 79 86 79 67 87 b 50 100 50 100 33 87 b 14 79 14 79 17 58 b 14 37 14 37 33 29 "

def shape_estrella_3t(context):
    return "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26 "

def shape_estrella_4t(context):
    return "m 25 72 l 18 61 l 0 87 l 33 87 b 42 72 53 53 25 72 m 50 87 l 37 87 l 50 116 l 67 87 b 58 72 47 53 50 87 m 75 72 l 69 83 l 100 87 l 83 58 b 66 58 45 58 75 72 m 75 43 l 82 54 l 100 29 l 67 29 b 58 45 47 63 75 43 m 50 29 l 63 29 l 50 0 l 33 29 b 42 45 53 63 50 29 m 25 43 l 31 32 l 0 29 l 16 58 b 34 58 54 58 25 43 "

def shape_estrella_5t(context):
    return "m 33 29 l 0 29 l 50 116 l 100 29 l 33 29 l 50 0 l 100 87 l 0 87 l 33 29 "

def shape_estrella_6t(context):
    return "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33 m 61 35 b 95 38 95 38 69 59 b 78 90 78 90 50 73 b 23 90 23 90 31 59 b 6 38 6 38 39 35 b 50 6 50 6 61 35 "

def shape_estrella_7t(context):
    return "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33 "

def shape_estrella_8t(context):
    return "m 39 36 b 0 36 0 36 31 59 b 20 95 20 95 50 72 b 81 95 81 95 69 59 b 100 36 100 36 62 36 b 50 0 50 0 39 36 "

def shape_estrella_9t(context):
    return "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29 l 10 35 l 37 35 l 50 12 l 63 35 l 90 35 l 77 58 l 90 81 l 63 81 l 50 104 l 37 81 l 10 81 l 23 58 l 10 35 "

def shape_estrella_10t(context):
    return "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29 "

# -----------------------------------------------------------------------------
# SHAPE/ESPECIALES
# -----------------------------------------------------------------------------
def shape_corazon_2t(context):
    return "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 m 79 27 b 74 25 76 20 81 22 b 90 26 93 36 93 43 b 93 48 87 48 87 43 b 87 39 86 30 79 27 "

def shape_corazon_borde(context):
    return "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 l 50 28 b 69 2 98 18 98 40 b 98 66 74 69 50 97 b 25 69 2 66 2 40 b 2 18 31 2 50 28 "

def shape_destello_1t(context):
    return "m 0 0 l 47 50 l 0 100 l 50 53 l 100 100 l 53 50 l 100 0 l 50 47 l 0 0 m 42 50 b 42 61 58 61 58 50 b 58 39 42 39 42 50 "

def shape_destello_2t(context):
    return "m 0 0 l 45 50 l 0 100 l 50 55 l 100 100 l 55 50 l 100 0 l 50 45 l 0 0 m 40 50 b 40 64 60 64 60 50 b 60 36 40 36 40 50 "

def shape_destello_3t(context):
    return "m 0 0 b 35 39 61 65 100 100 b 65 61 39 35 0 0 m 100 0 b 61 35 35 61 0 100 b 39 65 65 39 100 0 "

def shape_destello_4t(context):
    return "m 50 100 b 52 69 52 31 50 0 b 48 31 48 69 50 100 m 0 50 b 31 52 69 52 100 50 b 69 48 31 48 0 50 "

def shape_trebol(context):
    return "m 1 99 l 4 106 b 21 99 44 83 53 56 b 51 73 40 88 56 98 b 72 106 80 90 77 82 b 85 86 100 82 100 69 b 100 58 87 52 64 54 b 52 55 51 50 68 48 b 85 46 94 40 95 29 b 96 18 80 10 70 19 b 70 0 40 0 40 21 b 40 33 47 37 50 43 b 54 50 52 54 47 47 b 39 38 31 26 19 27 b 0 29 0 49 13 53 b 0 58 3 80 19 79 b 39 78 40 62 51 55 b 42 79 23 92 1 99 "

def shape_pluma(context):
    return "m 0 0 b 0 20 10 28 27 34 b 10 33 47 49 54 55 b 62 62 72 77 78 75 l 80 78 l 90 79 b 94 86 96 94 97 100 l 100 100 b 99 93 96 84 93 78 b 100 56 88 41 73 30 l 73 39 l 69 28 b 62 24 55 23 49 19 l 48 24 l 45 19 b 31 10 13 12 0 0 m 91 74 l 88 75 b 79 49 57 40 46 35 b 22 25 8 15 2 5 b 11 17 22 23 48 34 b 64 41 82 51 91 74 "

def shape_pluma_2(context):
    return "m 99 8 l 87 18 b 83 13 75 18 75 23 b 69 19 68 29 62 27 b 53 27 50 21 44 21 b 38 15 31 11 21 8 b 14 2 7 0 4 2 b 0 16 11 37 29 43 b 40 49 65 50 78 31 b 83 34 93 29 89 20 l 100 9 "

def shape_engranaje(context):
    return "m 3 70 l 3 70 l 17 69 l 25 78 l 22 92 l 30 97 l 40 86 l 53 86 l 60 99 l 70 96 l 68 82 l 79 73 l 92 78 l 97 69 l 86 60 l 86 46 l 100 38 l 96 29 l 82 31 l 74 21 l 77 7 l 70 3 l 60 14 l 46 13 l 38 0 l 30 2 l 30 18 l 20 26 l 6 23 l 1 31 l 13 41 l 12 53 l 0 61 l 3 70 m 24 49 b 24 15 74 15 74 49 b 74 83 24 83 24 49 "

def shape_burbuja(context):
    return "m 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 m 50 1 b 79 1 99 21 99 50 b 99 76 80 93 68 96 b 62 98 66 94 50 94 b 34 94 38 98 32 96 b 20 93 1 78 1 50 b 1 22 22 1 50 1 m 88 22 b 79 11 75 14 85 24 b 92 38 94 33 88 22 m 12 15 b 12 19 18 19 18 15 b 18 11 12 11 12 15 m 14 16 l 15 30 l 16 16 l 30 15 l 16 14 l 15 0 l 14 14 l 0 15 m 50 94 b 63 94 61 100 52 100 b 42 100 38 94 50 94 "

def shape_pixel(context):
    return "m 0 0 l 0 1 l 1 1 l 1 0 "

# -----------------------------------------------------------------------------
# SHAPE/NOTAS
# -----------------------------------------------------------------------------
def shape_nota_musical_1(context):
    return "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 15 b 46 18 53 25 56 36 b 56 18 48 8 33 0 l 33 70 "

def shape_nota_musical_2(context):
    return "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 27 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 "

def shape_nota_musical_3(context):
    return "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 36 l 93 27 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 40 29 l 40 18 l 93 8 l 93 20 l 40 29 "

def shape_nota_musical_4(context):
    return "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 28 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 35 73 l 35 13 l 98 2 l 98 59 b 98 77 87 83 79 83 b 70 83 62 77 62 67 b 62 53 76 44 95 58 l 95 16 l 38 27 l 38 74 b 38 91 27 98 19 98 b 10 98 2 91 2 82 b 2 68 16 59 35 73 "

# -----------------------------------------------------------------------------
# SHAPE/SAKURA
# -----------------------------------------------------------------------------
def shape_flor_sakura(context):
    return "m 50 40 l 35 0 b 10 10 0 32 0 61 b 0 88 15 117 50 130 b 85 117 100 88 100 61 b 100 32 90 10 65 0 l 50 40 "

def shape_flor_sakura_1t(context):
    return "m 41 57 b 23 57 1 53 0 82 b 26 97 34 76 44 60 l 11 76 l 41 57 m 47 62 b 38 78 23 95 50 110 b 76 95 62 78 52 62 l 50 99 l 47 62 m 56 60 b 66 76 73 97 100 82 b 99 53 77 57 58 57 l 89 76 l 56 60 m 44 50 b 34 33 26 13 0 27 b 1 57 23 53 41 53 l 11 33 l 44 50 m 52 47 b 62 32 76 15 50 0 b 23 15 38 32 47 47 l 50 12 l 52 47 m 58 53 b 77 53 99 57 100 27 b 73 13 66 33 56 50 l 89 33 l 58 53 "

def shape_flor_sakura_2t(context):
    return "m 50 52 l 50 40 l 16 20 l 0 28 l 0 46 l 15 55 l 27 46 l 14 36 l 50 52 m 46 54 l 35 48 l 0 67 l 0 86 l 16 94 l 30 86 l 30 72 l 14 79 l 46 54 m 46 59 l 34 67 l 34 104 l 50 114 l 66 104 l 66 88 l 52 81 l 50 100 l 46 59 m 50 62 l 50 75 l 84 94 l 100 86 l 100 67 l 85 60 l 73 67 l 87 79 l 50 62 m 54 60 l 66 65 l 100 46 l 100 28 l 84 20 l 69 28 l 70 44 l 87 36 l 54 60 m 54 55 l 66 47 l 66 10 l 50 0 l 34 10 l 34 26 l 48 34 l 50 14 l 54 55 "

def shape_flor_sakura_3t(context):
    return "m 47 49 b 25 49 10 52 0 63 l 0 78 l 12 85 b 21 85 26 80 31 75 b 33 69 36 63 39 58 l 18 67 l 47 49 m 44 55 b 35 70 30 84 32 102 l 47 110 l 60 102 b 61 92 61 85 59 80 b 54 76 50 70 48 65 l 47 89 l 44 55 m 48 58 b 55 73 66 88 82 92 l 95 84 l 95 69 b 90 64 85 62 78 60 b 73 61 66 62 60 61 l 79 75 l 48 58 m 53 57 b 71 60 91 54 100 46 l 100 31 l 86 22 b 79 24 72 28 68 33 b 67 39 65 45 61 50 l 80 40 l 53 57 m 56 53 b 65 39 69 24 68 8 l 53 0 l 39 8 b 38 15 38 21 41 27 b 45 31 49 36 52 41 l 53 20 l 56 53 m 52 49 b 47 34 31 21 18 15 l 4 24 l 4 39 b 9 44 15 47 23 48 b 29 46 35 46 41 46 l 22 33 l 52 49 "


# -----------------------------------------------------------------------------
# TRANSFORMADOR DE FORMAS VECTORIALES
# -----------------------------------------------------------------------------
import math

def shape_transform(context, drawing="", scale_x=1.0, scale_y=1.0, rot=0.0, offset_x=0.0, offset_y=0.0, offset_border=0.0, mode="center"):
    """Aplica escala, rotación, desplazamiento y offsetting de contorno vectorial real (PyClipperOffset) a un dibujo vectorial ASS (m ...).
    Modos de alineación:
      - 'center': Centra el shape alrededor de (0,0).
      - 'topleft': Alinea el 0,0 a la esquina superior izquierda del bounding box.
      - 'absolute': Escribe el shape centrado y le suma la posición absoluta del contexto (fx.pos_x, fx.pos_y) listo para clips.
      - 'original': Conserva las coordenadas originales del dibujo antes del transform.
    """
    raw_shp = resolve_shape_value(drawing, context)
    if not raw_shp:
        return ""

    if not raw_shp.lower().startswith("m ") and not raw_shp.lower().startswith("m-") and not raw_shp.lower().startswith("m0"):
        from font_vector_engine import FontVectorEngine
        unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
        line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
        styleref = getattr(line, 'styleref', None) if line else None
        if not styleref and unit:
            styleref = getattr(unit, 'styleref', None)
            if not styleref and hasattr(unit, 'line') and getattr(unit, 'line', None):
                styleref = getattr(unit.line, 'styleref', None)
        fn = str(getattr(styleref, 'fontname', 'Arial')) if styleref else "Arial"
        fs = int(float(getattr(styleref, 'fontsize', 40))) if (styleref and getattr(styleref, 'fontsize', None)) else int(getattr(unit, 'height', getattr(line, 'height', 40)) or 40)
        b_val = bool(getattr(styleref, 'bold', False)) if styleref else False
        i_val = bool(getattr(styleref, 'italic', False)) if styleref else False
        v_shp = FontVectorEngine.text_to_shape(raw_shp, font_name=fn, font_size=fs, bold=b_val, italic=i_val)
        if v_shp and v_shp.strip():
            raw_shp = v_shp

    try: delta = float(offset_border) if (offset_border is not None and offset_border != "") else 0.0
    except: delta = 0.0

    if abs(delta) > 0.0001:
        from clipper_engine import ClipperEngine
        off_shp = ClipperEngine.offset_shape(raw_shp, delta)
        if off_shp and off_shp.strip():
            raw_shp = off_shp

    try: sx = float(scale_x) if scale_x != "" else 1.0
    except: sx = 1.0
    try: sy = float(scale_y) if scale_y != "" else 1.0
    except: sy = 1.0
    try: angle = float(rot) if rot != "" else 0.0
    except: angle = 0.0
    try: tx = float(offset_x) if offset_x != "" else 0.0
    except: tx = 0.0
    try: ty = float(offset_y) if offset_y != "" else 0.0
    except: ty = 0.0

    mode_str = str(mode or "center").strip().lower()

    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    tokens = raw_shp.split()

    coords = []
    for token in tokens:
        try:
            coords.append(float(token))
        except ValueError:
            pass

    min_x, max_x = 0.0, 0.0
    min_y, max_y = 0.0, 0.0
    cx, cy = 0.0, 0.0

    if coords and len(coords) >= 2:
        xs = coords[0::2]
        ys = coords[1::2]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0

    pos_x, pos_y = 0.0, 0.0
    if mode_str in ["absolute", "absoluto", "clip"]:
        unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
        try:
            pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line'), 'x', 0.0)))))
        except: pos_x = 0.0
        try:
            pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line'), 'y', 0.0)))))
        except: pos_y = 0.0
        ref_x, ref_y = cx, cy
    elif mode_str in ["topleft", "top_left", "esquina", "7"]:
        ref_x, ref_y = min_x, min_y
    elif mode_str in ["topright", "top_right", "9"]:
        ref_x, ref_y = max_x, min_y
    elif mode_str in ["bottomleft", "bottom_left", "1"]:
        ref_x, ref_y = min_x, max_y
    elif mode_str in ["bottomright", "bottom_right", "3"]:
        ref_x, ref_y = max_x, max_y
    elif mode_str in ["original", "raw", "ninguno", "0"]:
        ref_x, ref_y = 0.0, 0.0
    else:  # "center", "centro", "centrado", "5" (default)
        ref_x, ref_y = cx, cy

    out_tokens = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        try:
            x_val = float(token)
            if i + 1 < len(tokens):
                try:
                    y_val = float(tokens[i + 1])
                    rel_x = (x_val - ref_x) * sx
                    rel_y = (y_val - ref_y) * sy

                    if angle != 0.0:
                        rot_x = rel_x * cos_a - rel_y * sin_a
                        rot_y = rel_x * sin_a + rel_y * cos_a
                    else:
                        rot_x = rel_x
                        rot_y = rel_y

                    final_x = pos_x + rot_x + tx
                    final_y = pos_y + rot_y + ty

                    fmt_x = int(final_x) if final_x.is_integer() else round(final_x, 2)
                    fmt_y = int(final_y) if final_y.is_integer() else round(final_y, 2)

                    out_tokens.append(str(fmt_x))
                    out_tokens.append(str(fmt_y))
                    i += 2
                    continue
                except ValueError:
                    pass
            out_tokens.append(token)
            i += 1
        except ValueError:
            out_tokens.append(token)
            i += 1

    return " ".join(out_tokens) + " "

# -----------------------------------------------------------------------------
# BORDES CONCÉNTRICOS (shape.borders / shape.filled_borders)
# -----------------------------------------------------------------------------
def shape_concentric_borders_node(
    context,
    shape="",
    separation=5.0,
    overlap=0.5,
    scale=1.0,
    mode="Hueco (borders)",
    loop_count=5,
    out_mode="Shape",
    anchor="relativo"
):
    """Genera anillos y rebordes vectoriales concéntricos continuos capa a capa con Clipper (shape.borders / shape.filled_borders).
    Soporta salidas como Forma (relativa o absoluta), \\clip(drawing) o \\iclip(drawing) para máscaras vectoriales.
    """
    from node_engine import _eval_num_expr
    from clipper_engine import ClipperEngine
    from font_vector_engine import FontVectorEngine

    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)

    parent_x = float(getattr(unit, 'center', getattr(unit, 'x', getattr(line, 'center', getattr(line, 'x', 0))))) if (unit or line) else 0.0
    parent_y = float(getattr(unit, 'middle', getattr(unit, 'y', getattr(line, 'middle', getattr(line, 'y', 0))))) if (unit or line) else 0.0

    shp_val = resolve_shape_value(shape, context)
    if not shp_val:
        shp_val = getattr(unit, 'text_stripped', getattr(unit, 'text', '')) or getattr(line, 'text_stripped', getattr(line, 'text', 'm 0 0 l 100 0 l 100 100 l 0 100'))

    # Si es texto plano, convertir a vector con FontVectorEngine
    if shp_val and not shp_val.lower().startswith("m ") and not shp_val.lower().startswith("m-"):
        fn = "Arial"
        fs = 40
        b_val = False
        i_val = False
        styleref = getattr(line, 'styleref', None) if line else None
        if not styleref and unit and hasattr(unit, 'line') and getattr(unit, 'line', None):
            styleref = getattr(unit.line, 'styleref', None)
        if styleref:
            fn = str(getattr(styleref, 'fontname', fn))
            try: fs = int(float(getattr(styleref, 'fontsize', fs)))
            except: pass
            b_val = bool(getattr(styleref, 'bold', False))
            i_val = bool(getattr(styleref, 'italic', False))
        v_shp = FontVectorEngine.text_to_shape(shp_val, font_name=fn, font_size=fs, bold=b_val, italic=i_val)
        if v_shp and v_shp.strip():
            shp_val = v_shp

    sc_val = max(0.01, float(_eval_num_expr(scale, context, 1.0)))
    if sc_val != 1.0:
        shp_val = ClipperEngine.transform_shape(shp_val, mode="Escalar", factor=sc_val)

    # Parsear separaciones (puede ser float o lista "5, 10, 15")
    sep_str = str(separation).strip()
    try:
        if "," in sep_str:
            sep_list = [max(0.5, float(x.strip())) for x in sep_str.split(",") if x.strip()]
        else:
            sep_list = [max(0.5, float(_eval_num_expr(separation, context, 5.0)))]
    except Exception:
        sep_list = [5.0]
    if not sep_list:
        sep_list = [5.0]

    ov_val = max(0.0, float(_eval_num_expr(overlap, context, 0.5)))
    loops_n = max(1, int(_eval_num_expr(loop_count, context, 5.0)))
    mode_str = str(mode).strip().lower()
    is_filled_base = "relleno" in mode_str or "filled" in mode_str

    # Índices de iteración
    loops_n = max(1, int(_eval_num_expr(loop_count, context, 5.0)))
    total_rings = loops_n

    if isinstance(context, dict):
        j = int(context.get('j', context.get('fx_i', 1)))
        context['j_max'] = total_rings
        context['maxloop'] = total_rings
    else:
        j = 1

    # Generación y caché de anillos concéntricos
    prev_dist = 0.0
    cumulative_dist = 0.0
    rings = {}

    for i in range(1, total_rings + 1):
        if is_filled_base and i == 1:
            # Loop 1 en modo Relleno Base: forma base rellena
            rings[i] = ClipperEngine.offset_shape(shp_val, ov_val) if ov_val > 0 else shp_val
        else:
            sep_idx = (i - 2) if is_filled_base else (i - 1)
            dist = sep_list[sep_idx % len(sep_list)]
            cumulative_dist = prev_dist + dist

            outer_dist = cumulative_dist + ov_val
            inner_dist = max(0.0, prev_dist - ov_val)

            outer_shp = ClipperEngine.offset_shape(shp_val, outer_dist)
            inner_shp = ClipperEngine.offset_shape(shp_val, inner_dist) if inner_dist > 0 else shp_val
            diff_shp = ClipperEngine.boolean_difference(outer_shp, inner_shp)
            rings[i] = diff_shp if diff_shp and diff_shp.strip() else outer_shp
            prev_dist = cumulative_dist

    ring_idx = max(1, min(j, total_rings))
    current_ring_shape = rings.get(ring_idx, shp_val)

    # Calcular centroide BBox
    contours = ClipperEngine.parse_assdraw(current_ring_shape)
    _, _, _, _, cx, cy, _, _ = ClipperEngine.get_bbox(contours)

    # Procesar Tipo de Salida y Anclaje (Forma, \clip, \iclip, Relativo / Absoluto)
    out_mode_str = str(out_mode).strip().lower()
    anchor_str = str(anchor).strip().lower()

    if "iclip" in out_mode_str:
        abs_shp = ClipperEngine.transform_shape(current_ring_shape, mode="Offset", offset_x=parent_x, offset_y=parent_y)
        final_output = f"\\iclip({abs_shp})"
    elif "clip" in out_mode_str:
        abs_shp = ClipperEngine.transform_shape(current_ring_shape, mode="Offset", offset_x=parent_x, offset_y=parent_y)
        final_output = f"\\clip({abs_shp})"
    else:
        if "abs" in anchor_str or "absoluto" in anchor_str:
            final_output = ClipperEngine.transform_shape(current_ring_shape, mode="Offset", offset_x=parent_x, offset_y=parent_y)
        else:
            final_output = current_ring_shape

    pos_str = f"\\pos({cx:.2f},{cy:.2f})".rstrip('0').rstrip('.') if (cx != 0 or cy != 0) else ""
    return final_output, pos_str, ring_idx, total_rings


# -----------------------------------------------------------------------------
# CLIP GRADIENT (text.gradienth / text.gradientv / text.gradientangle optimizado Libass)
# -----------------------------------------------------------------------------
def clip_gradient_node(context, num_clips="5", angle="0", padding="4", overlap="0.5", order="Normal", out_mode="Clip"):
    """
    Nodo Clip Gradient:
    Genera franjas rectangulares de alto rendimiento (Libass) escalonadas para degradados.
    - Ángulo == 0°: Franjas rectangulares AABB horizontales \\clip(x1,y1,x2,y2).
    - Ángulo == 90°: Franjas rectangulares AABB verticales \\clip(x1,y1,x2,y2).
    - Ángulo != 0° y != 90°: Franjas poligonales vectoriales \\clip(m x1 y1 l x2 y2 l x3 y3 l x4 y4).
    """
    from node_engine import _eval_num_expr
    import random

    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)

    # Dimensiones y posición del contexto
    parent_x = float(getattr(unit, 'center', getattr(unit, 'x', getattr(line, 'center', getattr(line, 'x', 0.0))))) if (unit or line) else 0.0
    parent_y = float(getattr(unit, 'middle', getattr(unit, 'y', getattr(line, 'middle', getattr(line, 'y', 0.0))))) if (unit or line) else 0.0
    w_val = float(getattr(unit, 'width', getattr(line, 'width', 50.0))) if (unit or line) else 50.0
    h_val = float(getattr(unit, 'height', getattr(line, 'height', 35.0))) if (unit or line) else 35.0

    left = float(getattr(unit, 'left', parent_x - w_val / 2.0))
    top = float(getattr(unit, 'top', parent_y - h_val / 2.0))
    right = float(getattr(unit, 'right', left + w_val))
    bottom = float(getattr(unit, 'bottom', top + h_val))

    N = max(1, int(_eval_num_expr(num_clips, context, 5.0)))
    pad = float(_eval_num_expr(padding, context, 4.0))
    ov = float(_eval_num_expr(overlap, context, 0.5))
    ang = float(_eval_num_expr(angle, context, 0.0)) % 360.0

    if isinstance(context, dict):
        j = int(context.get('j', context.get('fx_i', 1)))
        context['j_max'] = N
        context['maxloop'] = N
    else:
        j = 1

    out_mode_str = str(out_mode).strip().lower()
    is_iclip = "iclip" in out_mode_str
    is_shape = "shape" in out_mode_str or "forma" in out_mode_str or "vector" in out_mode_str or "assdraw" in out_mode_str

    # Bounding box: relativo centrado en (0, 0) para Forma, absoluto para \clip / \iclip
    if is_shape:
        b_left = -w_val / 2.0 - pad
        b_right = w_val / 2.0 + pad
        b_top = -h_val / 2.0 - pad
        b_bottom = h_val / 2.0 + pad
        cx = 0.0
        cy = 0.0
    else:
        b_left = left - pad
        b_right = right + pad
        b_top = top - pad
        b_bottom = bottom + pad
        cx = (b_left + b_right) / 2.0
        cy = (b_top + b_bottom) / 2.0

    b_w = max(1.0, b_right - b_left)
    b_h = max(1.0, b_bottom - b_top)

    # Mapeo de secuencia / orden
    order_str = str(order).strip().lower()
    indices = list(range(N)) # 0 to N-1
    if "invert" in order_str or "rev" in order_str:
        indices.reverse()
    elif "centro" in order_str and "extremo" in order_str: # Centro a Extremos
        mid = (N - 1) / 2.0
        indices.sort(key=lambda idx: abs(idx - mid))
    elif "extremo" in order_str and "centro" in order_str: # Extremos al Centro
        mid = (N - 1) / 2.0
        indices.sort(key=lambda idx: -abs(idx - mid))
    elif "aleat" in order_str or "rand" in order_str:
        rnd = random.Random(42 + N)
        rnd.shuffle(indices)

    curr_j = max(1, min(j, N))
    k = indices[curr_j - 1] # Índice geométrico de la franja (0 a N-1)

    progress = 0.0 if N == 1 else round(k / (N - 1), 4)

    # Condicional: 0° (horizontal) y 90° (vertical) son rectangulares nativos AABB
    if ang in (0.0, 180.0, 360.0):
        strip_w = b_w / N
        k_eff = (N - 1 - k) if ang == 180.0 else k
        x1 = round(b_left + k_eff * strip_w - ov, 1)
        x2 = round(b_left + (k_eff + 1) * strip_w + ov, 1)
        y1 = round(b_top, 1)
        y2 = round(b_bottom, 1)

        if is_shape:
            clip_res = f"m {x1} {y1} l {x2} {y1} l {x2} {y2} l {x1} {y2}"
        elif is_iclip:
            clip_res = f"\\iclip({x1},{y1},{x2},{y2})"
        else:
            clip_res = f"\\clip({x1},{y1},{x2},{y2})"

    elif ang in (90.0, 270.0):
        strip_h = b_h / N
        k_eff = (N - 1 - k) if ang == 270.0 else k
        x1 = round(b_left, 1)
        x2 = round(b_right, 1)
        y1 = round(b_top + k_eff * strip_h - ov, 1)
        y2 = round(b_top + (k_eff + 1) * strip_h + ov, 1)

        if is_shape:
            clip_res = f"m {x1} {y1} l {x2} {y1} l {x2} {y2} l {x1} {y2}"
        elif is_iclip:
            clip_res = f"\\iclip({x1},{y1},{x2},{y2})"
        else:
            clip_res = f"\\clip({x1},{y1},{x2},{y2})"

    else:
        # Ángulo arbitrario / diagonal -> Polígono rectangular rotado de 4 vértices
        rad = math.radians(ang)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        span = math.hypot(b_w, b_h)
        strip_len = span / N

        u_min = -span / 2.0
        u1 = u_min + k * strip_len - ov
        u2 = u_min + (k + 1) * strip_len + ov
        v_half = span / 2.0 + ov

        def rot_pt(u, v):
            px = cx + u * cos_a - v * sin_a
            py = cy + u * sin_a + v * cos_a
            return round(px, 1), round(py, 1)

        p1_x, p1_y = rot_pt(u1, -v_half)
        p2_x, p2_y = rot_pt(u2, -v_half)
        p3_x, p3_y = rot_pt(u2, v_half)
        p4_x, p4_y = rot_pt(u1, v_half)

        ass_draw = f"m {p1_x} {p1_y} l {p2_x} {p2_y} l {p3_x} {p3_y} l {p4_x} {p4_y}"
        if is_shape:
            clip_res = ass_draw
        elif is_iclip:
            clip_res = f"\\iclip({ass_draw})"
        else:
            clip_res = f"\\clip({ass_draw})"

    return clip_res, progress, curr_j, N


from decorators import NODE_REGISTRY
NODE_REGISTRY["Shape/Shape Transform"] = shape_transform
NODE_REGISTRY["Shape Transform"] = shape_transform
NODE_REGISTRY["Shape/Concentric Borders"] = shape_concentric_borders_node
NODE_REGISTRY["Concentric Borders"] = shape_concentric_borders_node
NODE_REGISTRY["Functions/Clip Gradient"] = clip_gradient_node
NODE_REGISTRY["Clip Gradient"] = clip_gradient_node


# -----------------------------------------------------------------------------
# NODO MAESTRO UNIFICADO SHAPES LIB
# -----------------------------------------------------------------------------
RAW_PRESET_SHAPES = {
    "Circulo": "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0",
    "circle": "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0",
    "Triangulo": "m 50 0 l 0 86 l 100 86 l 50 0",
    "triangle": "m 50 0 l 0 86 l 100 86 l 50 0",
    "Rectangulo": "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0",
    "rectangle": "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0",
    "Esq. Curva": "m 20 0 b 8 0 0 8 0 20 l 0 80 b 0 92 8 100 20 100 l 80 100 b 92 100 100 92 100 80 l 100 20 b 100 8 92 0 80 0 l 20 0",
    "Esquinas Redondeadas": "m 20 0 b 8 0 0 8 0 20 l 0 80 b 0 92 8 100 20 100 l 80 100 b 92 100 100 92 100 80 l 100 20 b 100 8 92 0 80 0 l 20 0",
    "circangle": "m 20 0 b 8 0 0 8 0 20 l 0 80 b 0 92 8 100 20 100 l 80 100 b 92 100 100 92 100 80 l 100 20 b 100 8 92 0 80 0 l 20 0",
    "Pixel": "m 0 0 l 0 1 l 1 1 l 1 0",
    "pixel": "m 0 0 l 0 1 l 1 1 l 1 0",
    "Pentagono": "m 50 0 l 0 36 l 19 95 l 81 95 l 100 36 l 50 0",
    "pentagon": "m 50 0 l 0 36 l 19 95 l 81 95 l 100 36 l 50 0",
    "Hexagono": "m 100 43.301 l 75 0 l 25 0 l 0 43.301 l 25 86.602 l 75 86.602 l 100 43.301",
    "hexagon": "m 100 43.301 l 75 0 l 25 0 l 0 43.301 l 25 86.602 l 75 86.602 l 100 43.301",
    "Octagono": "m 29 0 l 0 29 l 0 71 l 29 100 l 71 100 l 100 71 l 100 29 l 71 0 l 29 0",
    "octagon": "m 29 0 l 0 29 l 0 71 l 29 100 l 71 100 l 100 71 l 100 29 l 71 0 l 29 0",
    "Corazon": "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 106 b 75 71 100 68 100 40 b 100 16 68 0 50 25",
    "heart": "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 106 b 75 71 100 68 100 40 b 100 16 68 0 50 25",
    "Corazon 2T": "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 m 79 27 b 74 25 76 20 81 22 b 90 26 93 36 93 43 b 93 48 87 48 87 43 b 87 39 86 30 79 27",
    "heart2t": "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 m 79 27 b 74 25 76 20 81 22 b 90 26 93 36 93 43 b 93 48 87 48 87 43 b 87 39 86 30 79 27",
    "Corazon B": "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 l 50 28 b 69 2 98 18 98 40 b 98 66 74 69 50 97 b 25 69 2 66 2 40 b 2 18 31 2 50 28",
    "Corazon Borde": "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 l 50 28 b 69 2 98 18 98 40 b 98 66 74 69 50 97 b 25 69 2 66 2 40 b 2 18 31 2 50 28",
    "heart_b": "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 l 50 28 b 69 2 98 18 98 40 b 98 66 74 69 50 97 b 25 69 2 66 2 40 b 2 18 31 2 50 28",
    "Brillo 1T": "m 0 0 l 47 50 l 0 100 l 50 53 l 100 100 l 53 50 l 100 0 l 50 47 l 0 0 m 42 50 b 42 61 58 61 58 50 b 58 39 42 39 42 50",
    "shine1t": "m 0 0 l 47 50 l 0 100 l 50 53 l 100 100 l 53 50 l 100 0 l 50 47 l 0 0 m 42 50 b 42 61 58 61 58 50 b 58 39 42 39 42 50",
    "Brillo 2T": "m 0 0 l 45 50 l 0 100 l 50 55 l 100 100 l 55 50 l 100 0 l 50 45 l 0 0 m 40 50 b 40 64 60 64 60 50 b 60 36 40 36 40 50",
    "shine2t": "m 0 0 l 45 50 l 0 100 l 50 55 l 100 100 l 55 50 l 100 0 l 50 45 l 0 0 m 40 50 b 40 64 60 64 60 50 b 60 36 40 36 40 50",
    "Brillo 3T": "m 0 0 b 35 39 61 65 100 100 b 65 61 39 35 0 0 m 100 0 b 61 35 35 61 0 100 b 39 65 65 39 100 0",
    "shine3t": "m 0 0 b 35 39 61 65 100 100 b 65 61 39 35 0 0 m 100 0 b 61 35 35 61 0 100 b 39 65 65 39 100 0",
    "Brillo 4T": "m 50 100 b 52 69 52 31 50 0 b 48 31 48 69 50 100 m 0 50 b 31 52 69 52 100 50 b 69 48 31 48 0 50",
    "shine4t": "m 50 100 b 52 69 52 31 50 0 b 48 31 48 69 50 100 m 0 50 b 31 52 69 52 100 50 b 69 48 31 48 0 50",
    "Trebol": "m 1 99 l 4 106 b 21 99 44 83 53 56 b 51 73 40 88 56 98 b 72 106 80 90 77 82 b 85 86 100 82 100 69 b 100 58 87 52 64 54 b 52 55 51 50 68 48 b 85 46 94 40 95 29 b 96 18 80 10 70 19 b 70 0 40 0 40 21 b 40 33 47 37 50 43 b 54 50 52 54 47 47 b 39 38 31 26 19 27 b 0 29 0 49 13 53 b 0 58 3 80 19 79 b 39 78 40 62 51 55 b 42 79 23 92 1 99",
    "trebol": "m 1 99 l 4 106 b 21 99 44 83 53 56 b 51 73 40 88 56 98 b 72 106 80 90 77 82 b 85 86 100 82 100 69 b 100 58 87 52 64 54 b 52 55 51 50 68 48 b 85 46 94 40 95 29 b 96 18 80 10 70 19 b 70 0 40 0 40 21 b 40 33 47 37 50 43 b 54 50 52 54 47 47 b 39 38 31 26 19 27 b 0 29 0 49 13 53 b 0 58 3 80 19 79 b 39 78 40 62 51 55 b 42 79 23 92 1 99",
    "Pluma": "m 0 0 b 0 20 10 28 27 34 b 10 33 47 49 54 55 b 62 62 72 77 78 75 l 80 78 l 90 79 b 94 86 96 94 97 100 l 100 100 b 99 93 96 84 93 78 b 100 56 88 41 73 30 l 73 39 l 69 28 b 62 24 55 23 49 19 l 48 24 l 45 19 b 31 10 13 12 0 0 m 91 74 l 88 75 b 79 49 57 40 46 35 b 22 25 8 15 2 5 b 11 17 22 23 48 34 b 64 41 82 51 91 74",
    "feather": "m 0 0 b 0 20 10 28 27 34 b 10 33 47 49 54 55 b 62 62 72 77 78 75 l 80 78 l 90 79 b 94 86 96 94 97 100 l 100 100 b 99 93 96 84 93 78 b 100 56 88 41 73 30 l 73 39 l 69 28 b 62 24 55 23 49 19 l 48 24 l 45 19 b 31 10 13 12 0 0 m 91 74 l 88 75 b 79 49 57 40 46 35 b 22 25 8 15 2 5 b 11 17 22 23 48 34 b 64 41 82 51 91 74",
    "Pluma 2": "m 99 8 l 87 18 b 83 13 75 18 75 23 b 69 19 68 29 62 27 b 53 27 50 21 44 21 b 38 15 31 11 21 8 b 14 2 7 0 4 2 b 0 16 11 37 29 43 b 40 49 65 50 78 31 b 83 34 93 29 89 20 l 100 9",
    "feather2": "m 99 8 l 87 18 b 83 13 75 18 75 23 b 69 19 68 29 62 27 b 53 27 50 21 44 21 b 38 15 31 11 21 8 b 14 2 7 0 4 2 b 0 16 11 37 29 43 b 40 49 65 50 78 31 b 83 34 93 29 89 20 l 100 9",
    "Rombo": "m 50 0 l 0 50 l 50 100 l 100 50 l 50 0",
    "diamond": "m 50 0 l 0 50 l 50 100 l 100 50 l 50 0",
    "Engranaje": "m 3 70 l 3 70 l 17 69 l 25 78 l 22 92 l 30 97 l 40 86 l 53 86 l 60 99 l 70 96 l 68 82 l 79 73 l 92 78 l 97 69 l 86 60 l 86 46 l 100 38 l 96 29 l 82 31 l 74 21 l 77 7 l 70 3 l 60 14 l 46 13 l 38 0 l 30 2 l 30 18 l 20 26 l 6 23 l 1 31 l 13 41 l 12 53 l 0 61 l 3 70 m 24 49 b 24 15 74 15 74 49 b 74 83 24 83 24 49",
    "gear": "m 3 70 l 3 70 l 17 69 l 25 78 l 22 92 l 30 97 l 40 86 l 53 86 l 60 99 l 70 96 l 68 82 l 79 73 l 92 78 l 97 69 l 86 60 l 86 46 l 100 38 l 96 29 l 82 31 l 74 21 l 77 7 l 70 3 l 60 14 l 46 13 l 38 0 l 30 2 l 30 18 l 20 26 l 6 23 l 1 31 l 13 41 l 12 53 l 0 61 l 3 70 m 24 49 b 24 15 74 15 74 49 b 74 83 24 83 24 49",
    "Burbuja": "m 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 m 50 1 b 79 1 99 21 99 50 b 99 76 80 93 68 96 b 62 98 66 94 50 94 b 34 94 38 98 32 96 b 20 93 1 78 1 50 b 1 22 22 1 50 1 m 88 22 b 79 11 75 14 85 24 b 92 38 94 33 88 22 m 12 15 b 12 19 18 19 18 15 b 18 11 12 11 12 15 m 14 16 l 15 30 l 16 16 l 30 15 l 16 14 l 15 0 l 14 14 l 0 15 m 50 94 b 63 94 61 100 52 100 b 42 100 38 94 50 94",
    "bubble": "m 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 m 50 1 b 79 1 99 21 99 50 b 99 76 80 93 68 96 b 62 98 66 94 50 94 b 34 94 38 98 32 96 b 20 93 1 78 1 50 b 1 22 22 1 50 1 m 88 22 b 79 11 75 14 85 24 b 92 38 94 33 88 22 m 12 15 b 12 19 18 19 18 15 b 18 11 12 11 12 15 m 14 16 l 15 30 l 16 16 l 30 15 l 16 14 l 15 0 l 14 14 l 0 15 m 50 94 b 63 94 61 100 52 100 b 42 100 38 94 50 94",
    "Nota 1T": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 15 b 46 18 53 25 56 36 b 56 18 48 8 33 0 l 33 70",
    "note1t": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 15 b 46 18 53 25 56 36 b 56 18 48 8 33 0 l 33 70",
    "Nota 2T": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 27 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70",
    "note2t": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 27 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70",
    "Nota 3T": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 36 l 93 27 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 40 29 l 40 18 l 93 8 l 93 20 l 40 29",
    "note3t": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 36 l 93 27 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 40 29 l 40 18 l 93 8 l 93 20 l 40 29",
    "Nota 4T": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 28 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 35 73 l 35 13 l 98 2 l 98 59 b 98 77 87 83 79 83 b 70 83 62 77 62 67 b 62 53 76 44 95 58 l 95 16 l 38 27 l 38 74 b 38 91 27 98 19 98 b 10 98 2 91 2 82 b 2 68 16 59 35 73",
    "note4t": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 28 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 35 73 l 35 13 l 98 2 l 98 59 b 98 77 87 83 79 83 b 70 83 62 77 62 67 b 62 53 76 44 95 58 l 95 16 l 38 27 l 38 74 b 38 91 27 98 19 98 b 10 98 2 91 2 82 b 2 68 16 59 35 73",
    "Estrella": "m 38 36 l 0 36 l 31 59 l 20 95 l 50 72 l 81 94 l 69 59 l 100 36 l 62 36 l 50 0 l 38 36",
    "star": "m 38 36 l 0 36 l 31 59 l 20 95 l 50 72 l 81 94 l 69 59 l 100 36 l 62 36 l 50 0 l 38 36",
    "Estrella 1T": "m 0 35 l 29 56 l 33 55 b 37 44 42 66 34 58 l 30 60 l 18 95 l 48 73 l 48 69 b 38 63 60 63 51 69 l 51 73 l 81 95 l 70 60 l 65 58 b 57 65 63 44 66 55 l 71 56 l 100 35 l 63 35 l 61 39 b 64 48 47 36 59 36 l 61 33 l 50 0 l 38 33 l 40 36 b 52 36 36 49 38 39 l 36 35 l 0 35",
    "star1t": "m 0 35 l 29 56 l 33 55 b 37 44 42 66 34 58 l 30 60 l 18 95 l 48 73 l 48 69 b 38 63 60 63 51 69 l 51 73 l 81 95 l 70 60 l 65 58 b 57 65 63 44 66 55 l 71 56 l 100 35 l 63 35 l 61 39 b 64 48 47 36 59 36 l 61 33 l 50 0 l 38 33 l 40 36 b 52 36 36 49 38 39 l 36 35 l 0 35",
    "Estrella 2T": "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26 l 33 29 b 50 16 50 16 67 29 b 86 37 86 37 83 58 b 86 79 86 79 67 87 b 50 100 50 100 33 87 b 14 79 14 79 17 58 b 14 37 14 37 33 29",
    "star2t": "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26 l 33 29 b 50 16 50 16 67 29 b 86 37 86 37 83 58 b 86 79 86 79 67 87 b 50 100 50 100 33 87 b 14 79 14 79 17 58 b 14 37 14 37 33 29",
    "Estrella 3T": "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26",
    "star3t": "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26",
    "Estrella 4T": "m 25 72 l 18 61 l 0 87 l 33 87 b 42 72 53 53 25 72 m 50 87 l 37 87 l 50 116 l 67 87 b 58 72 47 53 50 87 m 75 72 l 69 83 l 100 87 l 83 58 b 66 58 45 58 75 72 m 75 43 l 82 54 l 100 29 l 67 29 b 58 45 47 63 75 43 m 50 29 l 63 29 l 50 0 l 33 29 b 42 45 53 63 50 29 m 25 43 l 31 32 l 0 29 l 16 58 b 34 58 54 58 25 43",
    "star4t": "m 25 72 l 18 61 l 0 87 l 33 87 b 42 72 53 53 25 72 m 50 87 l 37 87 l 50 116 l 67 87 b 58 72 47 53 50 87 m 75 72 l 69 83 l 100 87 l 83 58 b 66 58 45 58 75 72 m 75 43 l 82 54 l 100 29 l 67 29 b 58 45 47 63 75 43 m 50 29 l 63 29 l 50 0 l 33 29 b 42 45 53 63 50 29 m 25 43 l 31 32 l 0 29 l 16 58 b 34 58 54 58 25 43",
    "Estrella 5T": "m 33 29 l 0 29 l 50 116 l 100 29 l 33 29 l 50 0 l 100 87 l 0 87 l 33 29",
    "star5t": "m 33 29 l 0 29 l 50 116 l 100 29 l 33 29 l 50 0 l 100 87 l 0 87 l 33 29",
    "Estrella 6T": "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33 m 61 35 b 95 38 95 38 69 59 b 78 90 78 90 50 73 b 23 90 23 90 31 59 b 6 38 6 38 39 35 b 50 6 50 6 61 35",
    "star6t": "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33 m 61 35 b 95 38 95 38 69 59 b 78 90 78 90 50 73 b 23 90 23 90 31 59 b 6 38 6 38 39 35 b 50 6 50 6 61 35",
    "Estrella 7T": "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33",
    "star7t": "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33",
    "Estrella 8T": "m 39 36 b 0 36 0 36 31 59 b 20 95 20 95 50 72 b 81 95 81 95 69 59 b 100 36 100 36 62 36 b 50 0 50 0 39 36",
    "star8t": "m 39 36 b 0 36 0 36 31 59 b 20 95 20 95 50 72 b 81 95 81 95 69 59 b 100 36 100 36 62 36 b 50 0 50 0 39 36",
    "Estrella 9T": "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29 l 10 35 l 37 35 l 50 12 l 63 35 l 90 35 l 77 58 l 90 81 l 63 81 l 50 104 l 37 81 l 10 81 l 23 58 l 10 35",
    "star9t": "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29 l 10 35 l 37 35 l 50 12 l 63 35 l 90 35 l 77 58 l 90 81 l 63 81 l 50 104 l 37 81 l 10 81 l 23 58 l 10 35",
    "Estrella 10T": "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29",
    "star10t": "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29",
    "Sakura": "m 50 40 l 35 0 b 10 10 0 32 0 61 b 0 88 15 117 50 130 b 85 117 100 88 100 61 b 100 32 90 10 65 0 l 50 40",
    "sakura": "m 50 40 l 35 0 b 10 10 0 32 0 61 b 0 88 15 117 50 130 b 85 117 100 88 100 61 b 100 32 90 10 65 0 l 50 40",
    "Sakura 1T": "m 41 57 b 23 57 1 53 0 82 b 26 97 34 76 44 60 l 11 76 l 41 57 m 47 62 b 38 78 23 95 50 110 b 76 95 62 78 52 62 l 50 99 l 47 62 m 56 60 b 66 76 73 97 100 82 b 99 53 77 57 58 57 l 89 76 l 56 60 m 44 50 b 34 33 26 13 0 27 b 1 57 23 53 41 53 l 11 33 l 44 50 m 52 47 b 62 32 76 15 50 0 b 23 15 38 32 47 47 l 50 12 l 52 47 m 58 53 b 77 53 99 57 100 27 b 73 13 66 33 56 50 l 89 33 l 58 53",
    "sakura1t": "m 41 57 b 23 57 1 53 0 82 b 26 97 34 76 44 60 l 11 76 l 41 57 m 47 62 b 38 78 23 95 50 110 b 76 95 62 78 52 62 l 50 99 l 47 62 m 56 60 b 66 76 73 97 100 82 b 99 53 77 57 58 57 l 89 76 l 56 60 m 44 50 b 34 33 26 13 0 27 b 1 57 23 53 41 53 l 11 33 l 44 50 m 52 47 b 62 32 76 15 50 0 b 23 15 38 32 47 47 l 50 12 l 52 47 m 58 53 b 77 53 99 57 100 27 b 73 13 66 33 56 50 l 89 33 l 58 53",
    "Sakura 2T": "m 50 52 l 50 40 l 16 20 l 0 28 l 0 46 l 15 55 l 27 46 l 14 36 l 50 52 m 46 54 l 35 48 l 0 67 l 0 86 l 16 94 l 30 86 l 30 72 l 14 79 l 46 54 m 46 59 l 34 67 l 34 104 l 50 114 l 66 104 l 66 88 l 52 81 l 50 100 l 46 59 m 50 62 l 50 75 l 84 94 l 100 86 l 100 67 l 85 60 l 73 67 l 87 79 l 50 62 m 54 60 l 66 65 l 100 46 l 100 28 l 84 20 l 69 28 l 70 44 l 87 36 l 54 60 m 54 55 l 66 47 l 66 10 l 50 0 l 34 10 l 34 26 l 48 34 l 50 14 l 54 55",
    "sakura2t": "m 50 52 l 50 40 l 16 20 l 0 28 l 0 46 l 15 55 l 27 46 l 14 36 l 50 52 m 46 54 l 35 48 l 0 67 l 0 86 l 16 94 l 30 86 l 30 72 l 14 79 l 46 54 m 46 59 l 34 67 l 34 104 l 50 114 l 66 104 l 66 88 l 52 81 l 50 100 l 46 59 m 50 62 l 50 75 l 84 94 l 100 86 l 100 67 l 85 60 l 73 67 l 87 79 l 50 62 m 54 60 l 66 65 l 100 46 l 100 28 l 84 20 l 69 28 l 70 44 l 87 36 l 54 60 m 54 55 l 66 47 l 66 10 l 50 0 l 34 10 l 34 26 l 48 34 l 50 14 l 54 55",
    "Sakura 3T": "m 47 49 b 25 49 10 52 0 63 l 0 78 l 12 85 b 21 85 26 80 31 75 b 33 69 36 63 39 58 l 18 67 l 47 49 m 44 55 b 35 70 30 84 32 102 l 47 110 l 60 102 b 61 92 61 85 59 80 b 54 76 50 70 48 65 l 47 89 l 44 55 m 48 58 b 55 73 66 88 82 92 l 95 84 l 95 69 b 90 64 85 62 78 60 b 73 61 66 62 60 61 l 79 75 l 48 58 m 53 57 b 71 60 91 54 100 46 l 100 31 l 86 22 b 79 24 72 28 68 33 b 67 39 65 45 61 50 l 80 40 l 53 57 m 56 53 b 65 39 69 24 68 8 l 53 0 l 39 8 b 38 15 38 21 41 27 b 45 31 49 36 52 41 l 53 20 l 56 53 m 52 49 b 47 34 31 21 18 15 l 4 24 l 4 39 b 9 44 15 47 23 48 b 29 46 35 46 41 46 l 22 33 l 52 49",
    "sakura3t": "m 47 49 b 25 49 10 52 0 63 l 0 78 l 12 85 b 21 85 26 80 31 75 b 33 69 36 63 39 58 l 18 67 l 47 49 m 44 55 b 35 70 30 84 32 102 l 47 110 l 60 102 b 61 92 61 85 59 80 b 54 76 50 70 48 65 l 47 89 l 44 55 m 48 58 b 55 73 66 88 82 92 l 95 84 l 95 69 b 90 64 85 62 78 60 b 73 61 66 62 60 61 l 79 75 l 48 58 m 53 57 b 71 60 91 54 100 46 l 100 31 l 86 22 b 79 24 72 28 68 33 b 67 39 65 45 61 50 l 80 40 l 53 57 m 56 53 b 65 39 69 24 68 8 l 53 0 l 39 8 b 38 15 38 21 41 27 b 45 31 49 36 52 41 l 53 20 l 56 53 m 52 49 b 47 34 31 21 18 15 l 4 24 l 4 39 b 9 44 15 47 23 48 b 29 46 35 46 41 46 l 22 33 l 52 49",
    "Sakura 4T": "m 42 59 l 18 59 b 0 59 0 74 0 86 l 25 86 b 36 86 40 70 47 62 l 25 73 l 42 59 m 48 65 l 35 86 b 26 101 38 107 50 114 l 63 93 b 69 85 57 71 53 62 l 51 87 l 48 65 m 57 62 l 69 85 b 77 100 89 92 100 85 l 89 64 b 83 55 67 57 56 57 l 78 71 l 57 62 m 58 55 l 84 55 b 100 55 100 40 100 29 l 76 29 b 65 29 61 43 53 53 l 76 42 l 58 55 m 52 49 l 64 30 b 75 14 62 7 50 0 l 38 18 b 32 29 43 40 47 53 l 50 27 l 52 49 m 44 53 l 33 30 b 24 15 10 23 0 30 l 12 50 b 19 59 35 57 44 57 l 25 43 l 44 53",
    "sakura4t": "m 42 59 l 18 59 b 0 59 0 74 0 86 l 25 86 b 36 86 40 70 47 62 l 25 73 l 42 59 m 48 65 l 35 86 b 26 101 38 107 50 114 l 63 93 b 69 85 57 71 53 62 l 51 87 l 48 65 m 57 62 l 69 85 b 77 100 89 92 100 85 l 89 64 b 83 55 67 57 56 57 l 78 71 l 57 62 m 58 55 l 84 55 b 100 55 100 40 100 29 l 76 29 b 65 29 61 43 53 53 l 76 42 l 58 55 m 52 49 l 64 30 b 75 14 62 7 50 0 l 38 18 b 32 29 43 40 47 53 l 50 27 l 52 49 m 44 53 l 33 30 b 24 15 10 23 0 30 l 12 50 b 19 59 35 57 44 57 l 25 43 l 44 53",
    "Sakura 5T": "m 43 55 b 33 49 4 55 4 65 b 4 76 14 90 24 90 b 33 90 27 74 43 61 l 23 68 l 43 55 m 49 61 b 38 65 27 93 35 99 b 44 105 61 104 66 96 b 72 89 55 85 54 64 l 49 85 l 49 61 m 55 59 b 55 70 75 93 85 88 b 93 83 100 66 96 59 b 91 50 80 63 61 56 l 77 69 l 55 59 m 58 52 b 68 58 98 52 98 41 b 98 31 87 18 77 18 b 68 18 74 33 58 46 l 78 39 l 58 52 m 52 46 b 63 41 74 12 66 6 b 57 0 39 2 33 10 b 29 18 45 22 48 43 l 52 21 l 52 46 m 45 46 b 46 36 25 12 15 18 b 6 24 0 41 5 49 b 10 58 20 43 40 50 l 23 38 l 45 46",
    "sakura5t": "m 43 55 b 33 49 4 55 4 65 b 4 76 14 90 24 90 b 33 90 27 74 43 61 l 23 68 l 43 55 m 49 61 b 38 65 27 93 35 99 b 44 105 61 104 66 96 b 72 89 55 85 54 64 l 49 85 l 49 61 m 55 59 b 55 70 75 93 85 88 b 93 83 100 66 96 59 b 91 50 80 63 61 56 l 77 69 l 55 59 m 58 52 b 68 58 98 52 98 41 b 98 31 87 18 77 18 b 68 18 74 33 58 46 l 78 39 l 58 52 m 52 46 b 63 41 74 12 66 6 b 57 0 39 2 33 10 b 29 18 45 22 48 43 l 52 21 l 52 46 m 45 46 b 46 36 25 12 15 18 b 6 24 0 41 5 49 b 10 58 20 43 40 50 l 23 38 l 45 46",
    "Sakura 6T": "m 46 75 b 29 79 37 99 50 110 b 64 99 72 79 53 75 l 50 90 l 46 75 m 30 61 b 19 48 4 65 0 81 b 15 87 39 85 33 68 l 18 71 l 30 61 m 67 68 b 61 85 85 87 100 81 b 96 65 81 48 70 61 l 82 71 l 67 68 m 53 34 b 72 31 64 10 50 0 b 37 10 29 32 46 34 l 50 21 l 53 34 m 69 48 b 79 60 96 43 100 28 b 85 22 61 25 67 41 l 82 38 l 69 48 m 34 41 b 39 25 15 22 0 28 b 3 43 22 60 31 48 l 18 38 l 34 41",
    "sakura6t": "m 46 75 b 29 79 37 99 50 110 b 64 99 72 79 53 75 l 50 90 l 46 75 m 30 61 b 19 48 4 65 0 81 b 15 87 39 85 33 68 l 18 71 l 30 61 m 67 68 b 61 85 85 87 100 81 b 96 65 81 48 70 61 l 82 71 l 67 68 m 53 34 b 72 31 64 10 50 0 b 37 10 29 32 46 34 l 50 21 l 53 34 m 69 48 b 79 60 96 43 100 28 b 85 22 61 25 67 41 l 82 38 l 69 48 m 34 41 b 39 25 15 22 0 28 b 3 43 22 60 31 48 l 18 38 l 34 41",
    "Sakura 7T": "m 46 75 b 28 79 37 99 50 110 b 64 99 72 79 53 75 l 50 90 l 46 75 m 30 61 b 19 48 4 65 0 81 b 15 87 39 85 33 68 l 18 71 l 30 61 m 66 68 b 61 85 85 87 100 81 b 96 65 81 48 69 61 l 82 71 l 66 68 m 53 34 b 72 31 64 10 50 0 b 37 10 28 31 46 34 l 50 21 l 53 34 m 69 48 b 81 60 96 43 100 28 b 85 22 61 25 66 41 l 82 38 l 69 48 m 33 41 b 39 25 15 22 0 28 b 4 43 19 60 30 48 l 18 38 l 33 41 m 55 42 b 55 34 44 34 44 42 b 44 50 55 50 55 42 m 55 67 b 55 59 44 59 44 67 b 44 75 55 75 55 67 m 44 48 b 44 40 33 40 33 48 b 33 56 44 56 44 48 m 44 61 b 44 53 33 53 33 61 b 33 69 44 69 44 61 m 66 48 b 66 40 55 40 55 48 b 55 56 66 56 66 48 m 66 61 b 66 53 55 53 55 61 b 55 69 66 69 66 61",
    "sakura7t": "m 46 75 b 28 79 37 99 50 110 b 64 99 72 79 53 75 l 50 90 l 46 75 m 30 61 b 19 48 4 65 0 81 b 15 87 39 85 33 68 l 18 71 l 30 61 m 66 68 b 61 85 85 87 100 81 b 96 65 81 48 69 61 l 82 71 l 66 68 m 53 34 b 72 31 64 10 50 0 b 37 10 28 31 46 34 l 50 21 l 53 34 m 69 48 b 81 60 96 43 100 28 b 85 22 61 25 66 41 l 82 38 l 69 48 m 33 41 b 39 25 15 22 0 28 b 4 43 19 60 30 48 l 18 38 l 33 41 m 55 42 b 55 34 44 34 44 42 b 44 50 55 50 55 42 m 55 67 b 55 59 44 59 44 67 b 44 75 55 75 55 67 m 44 48 b 44 40 33 40 33 48 b 33 56 44 56 44 48 m 44 61 b 44 53 33 53 33 61 b 33 69 44 69 44 61 m 66 48 b 66 40 55 40 55 48 b 55 56 66 56 66 48 m 66 61 b 66 53 55 53 55 61 b 55 69 66 69 66 61",
    "Copo 1T": "m 30 45 l 30 52 l 20 52 l 20 55 l 30 55 l 30 62 l 16 70 l 2 61 l 0 64 l 13 72 l 1 79 l 3 82 l 15 75 l 15 90 l 18 90 l 18 73 l 32 65 l 39 69 l 33 78 l 36 80 l 42 71 l 48 74 l 48 89 l 32 98 l 34 101 l 48 93 l 48 108 l 52 108 l 52 93 l 66 101 l 67 98 l 52 89 l 52 74 l 58 71 l 64 80 l 67 78 l 61 69 l 67 65 l 82 73 l 82 90 l 85 90 l 85 75 l 97 82 l 99 79 l 87 72 l 100 64 l 98 61 l 84 70 l 70 62 l 70 55 l 80 55 l 80 52 l 70 52 l 70 45 l 84 37 l 98 46 l 100 43 l 87 35 l 99 28 l 97 25 l 85 32 l 85 16 l 82 17 l 82 34 l 68 42 l 61 38 l 67 30 l 64 28 l 58 36 l 52 33 l 52 18 l 68 9 l 66 6 l 52 14 l 52 0 l 48 0 l 48 14 l 34 6 l 32 9 l 48 18 l 48 33 l 42 36 l 36 28 l 33 30 l 39 38 l 32 42 l 18 34 l 18 17 l 15 16 l 15 32 l 3 25 l 1 28 l 13 35 l 0 43 l 2 46 l 16 37 l 30 45 l 35 45 l 50 37 l 65 45 l 65 62 l 50 70 l 35 62 l 35 45",
    "snow1t": "m 30 45 l 30 52 l 20 52 l 20 55 l 30 55 l 30 62 l 16 70 l 2 61 l 0 64 l 13 72 l 1 79 l 3 82 l 15 75 l 15 90 l 18 90 l 18 73 l 32 65 l 39 69 l 33 78 l 36 80 l 42 71 l 48 74 l 48 89 l 32 98 l 34 101 l 48 93 l 48 108 l 52 108 l 52 93 l 66 101 l 67 98 l 52 89 l 52 74 l 58 71 l 64 80 l 67 78 l 61 69 l 67 65 l 82 73 l 82 90 l 85 90 l 85 75 l 97 82 l 99 79 l 87 72 l 100 64 l 98 61 l 84 70 l 70 62 l 70 55 l 80 55 l 80 52 l 70 52 l 70 45 l 84 37 l 98 46 l 100 43 l 87 35 l 99 28 l 97 25 l 85 32 l 85 16 l 82 17 l 82 34 l 68 42 l 61 38 l 67 30 l 64 28 l 58 36 l 52 33 l 52 18 l 68 9 l 66 6 l 52 14 l 52 0 l 48 0 l 48 14 l 34 6 l 32 9 l 48 18 l 48 33 l 42 36 l 36 28 l 33 30 l 39 38 l 32 42 l 18 34 l 18 17 l 15 16 l 15 32 l 3 25 l 1 28 l 13 35 l 0 43 l 2 46 l 16 37 l 30 45 l 35 45 l 50 37 l 65 45 l 65 62 l 50 70 l 35 62 l 35 45",
    "Copo 2T": "m 18 45 l 14 29 l 6 31 l 8 39 l 0 41 l 2 49 l 18 45 l 21 44 l 32 42 l 42 47 l 32 53 l 21 51 l 19 59 l 27 60 l 23 62 l 8 59 l 5 66 l 13 68 l 11 76 l 19 77 l 23 62 l 27 60 l 25 68 l 33 70 l 35 60 l 46 54 l 46 65 l 38 72 l 35 75 l 22 87 l 28 93 l 35 87 l 42 93 l 48 87 l 35 75 l 38 72 l 45 78 l 50 73 l 56 78 l 62 72 l 65 75 l 52 87 l 59 93 l 65 87 l 71 93 l 78 86 l 65 75 l 62 72 l 54 65 l 54 54 l 65 60 l 67 70 l 75 68 l 73 60 l 77 62 l 80 77 l 89 76 l 87 68 l 95 67 l 93 59 l 77 62 l 73 60 l 80 59 l 78 51 l 68 53 l 58 47 l 68 42 l 78 44 l 81 45 l 97 49 l 100 41 l 92 39 l 94 31 l 86 29 l 81 45 l 78 44 l 80 37 l 73 35 l 75 26 l 67 24 l 67 21 l 84 26 l 86 18 l 77 15 l 79 7 l 71 5 l 67 21 l 67 24 l 65 35 l 54 40 l 54 29 l 63 22 l 57 16 l 50 22 l 50 17 l 62 6 l 56 0 l 50 6 l 44 0 l 38 6 l 50 17 l 50 22 l 43 16 l 37 22 l 46 29 l 46 40 l 35 35 l 33 24 l 33 21 l 29 5 l 21 7 l 23 15 l 14 18 l 16 26 l 33 21 l 33 24 l 25 26 l 27 35 l 19 37 l 21 44",
    "snow2t": "m 18 45 l 14 29 l 6 31 l 8 39 l 0 41 l 2 49 l 18 45 l 21 44 l 32 42 l 42 47 l 32 53 l 21 51 l 19 59 l 27 60 l 23 62 l 8 59 l 5 66 l 13 68 l 11 76 l 19 77 l 23 62 l 27 60 l 25 68 l 33 70 l 35 60 l 46 54 l 46 65 l 38 72 l 35 75 l 22 87 l 28 93 l 35 87 l 42 93 l 48 87 l 35 75 l 38 72 l 45 78 l 50 73 l 56 78 l 62 72 l 65 75 l 52 87 l 59 93 l 65 87 l 71 93 l 78 86 l 65 75 l 62 72 l 54 65 l 54 54 l 65 60 l 67 70 l 75 68 l 73 60 l 77 62 l 80 77 l 89 76 l 87 68 l 95 67 l 93 59 l 77 62 l 73 60 l 80 59 l 78 51 l 68 53 l 58 47 l 68 42 l 78 44 l 81 45 l 97 49 l 100 41 l 92 39 l 94 31 l 86 29 l 81 45 l 78 44 l 80 37 l 73 35 l 75 26 l 67 24 l 67 21 l 84 26 l 86 18 l 77 15 l 79 7 l 71 5 l 67 21 l 67 24 l 65 35 l 54 40 l 54 29 l 63 22 l 57 16 l 50 22 l 50 17 l 62 6 l 56 0 l 50 6 l 44 0 l 38 6 l 50 17 l 50 22 l 43 16 l 37 22 l 46 29 l 46 40 l 35 35 l 33 24 l 33 21 l 29 5 l 21 7 l 23 15 l 14 18 l 16 26 l 33 21 l 33 24 l 25 26 l 27 35 l 19 37 l 21 44",
    "Copo 3T": "m 25 39 l 11 35 l 0 47 l 11 59 l 25 55 l 19 64 l 17 61 l 6 66 l 14 68 l 11 75 l 22 69 l 20 66 l 32 65 l 22 74 l 24 90 l 39 86 l 44 74 l 49 83 l 44 83 l 44 94 l 50 87 l 56 94 l 56 83 l 51 83 l 56 74 l 61 86 l 76 90 l 78 74 l 68 65 l 80 66 l 78 69 l 88 75 l 86 68 l 94 67 l 83 61 l 81 64 l 75 55 l 88 59 l 100 47 l 88 35 l 75 39 l 81 30 l 83 33 l 94 27 l 86 26 l 88 18 l 78 24 l 80 28 l 68 29 l 78 19 l 76 4 l 61 8 l 56 20 l 51 11 l 56 11 l 56 0 l 50 7 l 44 0 l 44 11 l 49 11 l 43 20 l 39 8 l 24 4 l 22 19 l 32 29 l 20 28 l 22 24 l 11 18 l 14 26 l 6 27 l 17 33 l 19 30 l 25 39 l 46 47 b 38 47 29 57 19 47 l 28 41 l 46 47 l 48 43 b 43 36 29 35 34 19 l 42 24 l 48 43 l 52 43 l 58 24 l 66 19 b 71 35 56 36 52 43 l 54 47 l 72 41 l 81 46 b 71 57 62 47 54 47 l 52 51 b 57 58 71 59 66 75 l 58 70 l 52 51 l 48 51 l 42 70 l 34 75 b 29 59 42 58 48 51 l 46 47",
    "snow3t": "m 25 39 l 11 35 l 0 47 l 11 59 l 25 55 l 19 64 l 17 61 l 6 66 l 14 68 l 11 75 l 22 69 l 20 66 l 32 65 l 22 74 l 24 90 l 39 86 l 44 74 l 49 83 l 44 83 l 44 94 l 50 87 l 56 94 l 56 83 l 51 83 l 56 74 l 61 86 l 76 90 l 78 74 l 68 65 l 80 66 l 78 69 l 88 75 l 86 68 l 94 67 l 83 61 l 81 64 l 75 55 l 88 59 l 100 47 l 88 35 l 75 39 l 81 30 l 83 33 l 94 27 l 86 26 l 88 18 l 78 24 l 80 28 l 68 29 l 78 19 l 76 4 l 61 8 l 56 20 l 51 11 l 56 11 l 56 0 l 50 7 l 44 0 l 44 11 l 49 11 l 43 20 l 39 8 l 24 4 l 22 19 l 32 29 l 20 28 l 22 24 l 11 18 l 14 26 l 6 27 l 17 33 l 19 30 l 25 39 l 46 47 b 38 47 29 57 19 47 l 28 41 l 46 47 l 48 43 b 43 36 29 35 34 19 l 42 24 l 48 43 l 52 43 l 58 24 l 66 19 b 71 35 56 36 52 43 l 54 47 l 72 41 l 81 46 b 71 57 62 47 54 47 l 52 51 b 57 58 71 59 66 75 l 58 70 l 52 51 l 48 51 l 42 70 l 34 75 b 29 59 42 58 48 51 l 46 47",
    "Flor 1T": "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44",
    "flower1t": "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44",
    "Flor 2T": "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44 m 43 15 b 43 6 55 6 55 15 b 55 24 43 24 43 15 m 9 42 b 9 33 21 33 21 42 b 21 51 9 51 9 42 m 23 82 b 23 73 35 73 35 82 b 35 91 23 91 23 82 m 66 82 b 66 73 78 73 78 82 b 78 91 66 91 66 82 m 78 40 b 78 31 90 31 90 40 b 90 49 78 49 78 40",
    "flower2t": "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44 m 43 15 b 43 6 55 6 55 15 b 55 24 43 24 43 15 m 9 42 b 9 33 21 33 21 42 b 21 51 9 51 9 42 m 23 82 b 23 73 35 73 35 82 b 35 91 23 91 23 82 m 66 82 b 66 73 78 73 78 82 b 78 91 66 91 66 82 m 78 40 b 78 31 90 31 90 40 b 90 49 78 49 78 40",
    "Flor 3T": "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44 m 19 23 b 19 14 31 14 31 23 b 31 32 19 32 19 23 m 8 69 b 8 60 20 60 20 69 b 20 78 8 78 8 69 m 48 91 b 48 82 60 82 60 91 b 60 100 48 100 48 91 m 83 62 b 83 53 95 53 95 62 b 95 71 83 71 83 62 m 64 17 b 64 8 76 8 76 17 b 76 26 64 26 64 17 m 44 52 b 44 43 56 43 56 52 b 56 61 44 61 44 52",
    "flower3t": "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44 m 19 23 b 19 14 31 14 31 23 b 31 32 19 32 19 23 m 8 69 b 8 60 20 60 20 69 b 20 78 8 78 8 69 m 48 91 b 48 82 60 82 60 91 b 60 100 48 100 48 91 m 83 62 b 83 53 95 53 95 62 b 95 71 83 71 83 62 m 64 17 b 64 8 76 8 76 17 b 76 26 64 26 64 17 m 44 52 b 44 43 56 43 56 52 b 56 61 44 61 44 52",
    "Flor 4T": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53 m 5 39 b 5 32 15 32 15 39 b 15 46 5 46 5 39 m 84 39 b 84 32 94 32 94 39 b 94 46 84 46 84 39 m 45 11 b 45 4 55 4 55 11 b 55 18 45 18 45 11 m 21 87 b 21 80 31 80 31 87 b 31 94 21 94 21 87 m 70 87 b 70 80 80 80 80 87 b 80 94 70 94 70 87",
    "flower4t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53 m 5 39 b 5 32 15 32 15 39 b 15 46 5 46 5 39 m 84 39 b 84 32 94 32 94 39 b 94 46 84 46 84 39 m 45 11 b 45 4 55 4 55 11 b 55 18 45 18 45 11 m 21 87 b 21 80 31 80 31 87 b 31 94 21 94 21 87 m 70 87 b 70 80 80 80 80 87 b 80 94 70 94 70 87",
    "Flor 5T": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53",
    "flower5t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53",
    "Flor 6T": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53 m 44 19 b 44 28 56 28 56 19 b 56 10 44 10 44 19 m 24 80 b 24 89 36 89 36 80 b 36 71 24 71 24 80 m 64 80 b 64 89 76 89 76 80 b 76 71 64 71 64 80 m 12 42 b 12 51 24 51 24 42 b 24 33 12 33 12 42 m 76 42 b 76 51 88 51 88 42 b 88 33 76 33 76 42 m 40 53 b 40 67 60 67 60 53 b 60 40 40 40 40 53",
    "flower6t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53 m 44 19 b 44 28 56 28 56 19 b 56 10 44 10 44 19 m 24 80 b 24 89 36 89 36 80 b 36 71 24 71 24 80 m 64 80 b 64 89 76 89 76 80 b 76 71 64 71 64 80 m 12 42 b 12 51 24 51 24 42 b 24 33 12 33 12 42 m 76 42 b 76 51 88 51 88 42 b 88 33 76 33 76 42 m 40 53 b 40 67 60 67 60 53 b 60 40 40 40 40 53",
    "Flor 7T": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53 m 44 19 b 44 28 56 28 56 19 b 56 10 44 10 44 19 m 24 80 b 24 89 36 89 36 80 b 36 71 24 71 24 80 m 64 80 b 64 89 76 89 76 80 b 76 71 64 71 64 80 m 12 42 b 12 51 24 51 24 42 b 24 33 12 33 12 42 m 76 42 b 76 51 88 51 88 42 b 88 33 76 33 76 42",
    "flower7t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53 m 44 19 b 44 28 56 28 56 19 b 56 10 44 10 44 19 m 24 80 b 24 89 36 89 36 80 b 36 71 24 71 24 80 m 64 80 b 64 89 76 89 76 80 b 76 71 64 71 64 80 m 12 42 b 12 51 24 51 24 42 b 24 33 12 33 12 42 m 76 42 b 76 51 88 51 88 42 b 88 33 76 33 76 42",
    "Flor 8T": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53",
    "flower8t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53",
    "Flor 9T": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53",
    "flower9t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53",
    "Flor 10T": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53 m 11 64 b 11 71 21 71 21 64 b 21 57 11 57 11 64 m 80 64 b 80 71 90 71 90 64 b 90 57 80 57 80 64 m 45 89 b 45 96 55 96 55 89 b 55 82 45 82 45 89 m 24 23 b 24 30 34 30 34 23 b 34 16 24 16 24 23 m 66 23 b 66 30 76 30 76 23 b 76 16 66 16 66 23",
    "flower10t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53 m 11 64 b 11 71 21 71 21 64 b 21 57 11 57 11 64 m 80 64 b 80 71 90 71 90 64 b 90 57 80 57 80 64 m 45 89 b 45 96 55 96 55 89 b 55 82 45 82 45 89 m 24 23 b 24 30 34 30 34 23 b 34 16 24 16 24 23 m 66 23 b 66 30 76 30 76 23 b 76 16 66 16 66 23",
    "Flor 11T": "m 100 88 b 79 99 57 89 57 62 b 80 75 100 37 100 88 m 49 66 b 49 92 92 92 49 116 b 28 104 25 80 49 66 m 41 62 b 19 75 38 110 0 88 b 0 65 18 48 41 62 m 41 54 b 20 40 0 77 0 28 b 19 17 41 26 41 54 m 49 49 b 49 23 8 23 49 0 b 68 11 71 36 49 49 m 57 54 b 80 40 58 5 100 28 b 100 54 81 67 57 54",
    "flower11t": "m 100 88 b 79 99 57 89 57 62 b 80 75 100 37 100 88 m 49 66 b 49 92 92 92 49 116 b 28 104 25 80 49 66 m 41 62 b 19 75 38 110 0 88 b 0 65 18 48 41 62 m 41 54 b 20 40 0 77 0 28 b 19 17 41 26 41 54 m 49 49 b 49 23 8 23 49 0 b 68 11 71 36 49 49 m 57 54 b 80 40 58 5 100 28 b 100 54 81 67 57 54",
    "Flor 12T": "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58 m 24 82 b 24 90 12 90 12 82 b 12 74 24 74 24 82 m 60 97 b 60 105 48 105 48 97 b 48 89 60 89 60 97 m 93 76 b 93 84 81 84 81 76 b 81 68 93 68 93 76 m 91 34 b 91 42 79 42 79 34 b 79 26 91 26 91 34 m 54 17 b 54 25 42 25 42 17 b 42 9 54 9 54 17 m 20 39 b 20 47 8 47 8 39 b 8 31 20 31 20 39",
    "flower12t": "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58 m 24 82 b 24 90 12 90 12 82 b 12 74 24 74 24 82 m 60 97 b 60 105 48 105 48 97 b 48 89 60 89 60 97 m 93 76 b 93 84 81 84 81 76 b 81 68 93 68 93 76 m 91 34 b 91 42 79 42 79 34 b 79 26 91 26 91 34 m 54 17 b 54 25 42 25 42 17 b 42 9 54 9 54 17 m 20 39 b 20 47 8 47 8 39 b 8 31 20 31 20 39",
    "Flor 13T": "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58",
    "flower13t": "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58",
    "Flor 14T": "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58",
    "flower14t": "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58",
    "Flor 15T": "m 30 71 l 33 62 b 16 59 0 59 0 88 b 24 102 33 88 38 74 l 30 71 m 50 84 l 44 77 b 33 88 24 102 50 117 b 76 102 68 88 56 77 l 50 84 m 70 71 l 62 74 b 68 88 76 102 100 88 b 100 59 84 59 67 62 l 70 71 m 70 47 l 67 56 b 84 59 100 59 100 30 b 76 16 67 30 62 45 l 70 47 m 50 35 l 56 42 b 67 30 76 16 50 1 b 24 16 33 30 44 42 l 50 35 m 30 47 l 38 45 b 33 30 24 16 0 30 b 0 59 16 59 33 56 l 30 47 m 0 35 b 0 25 14 25 14 35 b 14 45 0 45 0 35 m 0 83 b 0 73 14 73 14 83 b 14 93 0 93 0 83 m 43 108 b 43 98 57 98 57 108 b 57 118 43 118 43 108 m 43 10 b 43 0 57 0 57 10 b 57 20 43 20 43 10 m 86 83 b 86 73 100 73 100 83 b 100 93 86 93 86 83 m 86 35 b 86 25 100 25 100 35 b 100 45 86 45 86 35",
    "flower15t": "m 30 71 l 33 62 b 16 59 0 59 0 88 b 24 102 33 88 38 74 l 30 71 m 50 84 l 44 77 b 33 88 24 102 50 117 b 76 102 68 88 56 77 l 50 84 m 70 71 l 62 74 b 68 88 76 102 100 88 b 100 59 84 59 67 62 l 70 71 m 70 47 l 67 56 b 84 59 100 59 100 30 b 76 16 67 30 62 45 l 70 47 m 50 35 l 56 42 b 67 30 76 16 50 1 b 24 16 33 30 44 42 l 50 35 m 30 47 l 38 45 b 33 30 24 16 0 30 b 0 59 16 59 33 56 l 30 47 m 0 35 b 0 25 14 25 14 35 b 14 45 0 45 0 35 m 0 83 b 0 73 14 73 14 83 b 14 93 0 93 0 83 m 43 108 b 43 98 57 98 57 108 b 57 118 43 118 43 108 m 43 10 b 43 0 57 0 57 10 b 57 20 43 20 43 10 m 86 83 b 86 73 100 73 100 83 b 100 93 86 93 86 83 m 86 35 b 86 25 100 25 100 35 b 100 45 86 45 86 35",
    "Flor 16T": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 83 l 44 76 b 33 87 24 102 50 116 b 76 102 68 87 56 76 l 50 83 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 56 41 b 67 29 76 14 50 0 b 24 14 33 29 44 41 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 26 29 b 26 19 40 19 40 29 b 40 39 26 39 26 29 m 60 29 b 60 19 74 19 74 29 b 74 39 60 39 60 29 m 9 58 b 9 48 23 48 23 58 b 23 68 9 68 9 58 m 77 58 b 77 48 91 48 91 58 b 91 68 77 68 77 58 m 26 87 b 26 77 40 77 40 87 b 40 97 26 97 26 87 m 60 87 b 60 77 74 77 74 87 b 74 97 60 97 60 87",
    "flower16t": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 83 l 44 76 b 33 87 24 102 50 116 b 76 102 68 87 56 76 l 50 83 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 56 41 b 67 29 76 14 50 0 b 24 14 33 29 44 41 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 26 29 b 26 19 40 19 40 29 b 40 39 26 39 26 29 m 60 29 b 60 19 74 19 74 29 b 74 39 60 39 60 29 m 9 58 b 9 48 23 48 23 58 b 23 68 9 68 9 58 m 77 58 b 77 48 91 48 91 58 b 91 68 77 68 77 58 m 26 87 b 26 77 40 77 40 87 b 40 97 26 97 26 87 m 60 87 b 60 77 74 77 74 87 b 74 97 60 97 60 87",
    "Flor 17T": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 83 l 44 76 b 33 87 24 102 50 116 b 76 102 68 87 56 76 l 50 83 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 56 41 b 67 29 76 14 50 0 b 24 14 33 29 44 41 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46",
    "flower17t": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 83 l 44 76 b 33 87 24 102 50 116 b 76 102 68 87 56 76 l 50 83 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 56 41 b 67 29 76 14 50 0 b 24 14 33 29 44 41 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46",
    "Flor 18T": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 82 l 43 75 b 33 87 24 102 50 116 b 76 102 68 87 57 75 l 50 82 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 57 42 b 67 29 76 14 50 0 b 24 14 33 29 43 42 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 58 34 l 42 34 l 50 21 l 58 34 m 82 40 l 74 53 l 66 40 l 82 40 m 34 40 l 26 53 l 18 40 l 34 40 m 58 82 l 50 95 l 42 82 l 58 82 m 34 76 l 18 76 l 26 63 l 34 76 m 82 76 l 66 76 l 74 63 l 82 76 m 5 35 b 5 28 15 28 15 35 b 15 42 5 42 5 35 m 5 81 b 5 74 15 74 15 81 b 15 88 5 88 5 81 m 85 81 b 85 74 95 74 95 81 b 95 88 85 88 85 81 m 85 35 b 85 28 95 28 95 35 b 95 42 85 42 85 35 m 45 104 b 45 97 55 97 55 104 b 55 111 45 111 45 104 m 45 12 b 45 5 55 5 55 12 b 55 19 45 19 45 12",
    "flower18t": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 82 l 43 75 b 33 87 24 102 50 116 b 76 102 68 87 57 75 l 50 82 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 57 42 b 67 29 76 14 50 0 b 24 14 33 29 43 42 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 58 34 l 42 34 l 50 21 l 58 34 m 82 40 l 74 53 l 66 40 l 82 40 m 34 40 l 26 53 l 18 40 l 34 40 m 58 82 l 50 95 l 42 82 l 58 82 m 34 76 l 18 76 l 26 63 l 34 76 m 82 76 l 66 76 l 74 63 l 82 76 m 5 35 b 5 28 15 28 15 35 b 15 42 5 42 5 35 m 5 81 b 5 74 15 74 15 81 b 15 88 5 88 5 81 m 85 81 b 85 74 95 74 95 81 b 95 88 85 88 85 81 m 85 35 b 85 28 95 28 95 35 b 95 42 85 42 85 35 m 45 104 b 45 97 55 97 55 104 b 55 111 45 111 45 104 m 45 12 b 45 5 55 5 55 12 b 55 19 45 19 45 12",
    "Flor 19T": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 82 l 43 75 b 33 87 24 102 50 116 b 76 102 68 87 57 75 l 50 82 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 57 42 b 67 29 76 14 50 0 b 24 14 33 29 43 42 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 58 34 l 42 34 l 50 21 l 58 34 m 82 40 l 74 53 l 66 40 l 82 40 m 34 40 l 26 53 l 18 40 l 34 40 m 58 82 l 50 95 l 42 82 l 58 82 m 34 76 l 18 76 l 26 63 l 34 76 m 82 76 l 66 76 l 74 63 l 82 76",
    "flower19t": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 82 l 43 75 b 33 87 24 102 50 116 b 76 102 68 87 57 75 l 50 82 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 57 42 b 67 29 76 14 50 0 b 24 14 33 29 43 42 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 58 34 l 42 34 l 50 21 l 58 34 m 82 40 l 74 53 l 66 40 l 82 40 m 34 40 l 26 53 l 18 40 l 34 40 m 58 82 l 50 95 l 42 82 l 58 82 m 34 76 l 18 76 l 26 63 l 34 76 m 82 76 l 66 76 l 74 63 l 82 76",
    "Flor 20T": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 19 43 b 19 35 31 35 31 43 b 31 51 19 51 19 43 m 19 73 b 19 65 31 65 31 73 b 31 81 19 81 19 73 m 69 43 b 69 35 81 35 81 43 b 81 51 69 51 69 43 m 69 73 b 69 65 81 65 81 73 b 81 81 69 81 69 73 m 44 87 b 44 79 56 79 56 87 b 56 95 44 95 44 87 m 44 28 b 44 20 56 20 56 28 b 56 36 44 36 44 28 m 44 58 b 44 50 56 50 56 58 b 56 66 44 66 44 58 m 0 58 b 0 50 12 50 12 58 b 12 66 0 66 0 58 m 88 58 b 88 50 100 50 100 58 b 100 66 88 66 88 58 m 22 96 b 22 88 34 88 34 96 b 34 104 22 104 22 96 m 66 20 b 66 12 78 12 78 20 b 78 28 66 28 66 20 m 22 20 b 22 12 34 12 34 20 b 34 28 22 28 22 20 m 67 96 b 67 88 79 88 79 96 b 79 104 67 104 67 96",
    "flower20t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 19 43 b 19 35 31 35 31 43 b 31 51 19 51 19 43 m 19 73 b 19 65 31 65 31 73 b 31 81 19 81 19 73 m 69 43 b 69 35 81 35 81 43 b 81 51 69 51 69 43 m 69 73 b 69 65 81 65 81 73 b 81 81 69 81 69 73 m 44 87 b 44 79 56 79 56 87 b 56 95 44 95 44 87 m 44 28 b 44 20 56 20 56 28 b 56 36 44 36 44 28 m 44 58 b 44 50 56 50 56 58 b 56 66 44 66 44 58 m 0 58 b 0 50 12 50 12 58 b 12 66 0 66 0 58 m 88 58 b 88 50 100 50 100 58 b 100 66 88 66 88 58 m 22 96 b 22 88 34 88 34 96 b 34 104 22 104 22 96 m 66 20 b 66 12 78 12 78 20 b 78 28 66 28 66 20 m 22 20 b 22 12 34 12 34 20 b 34 28 22 28 22 20 m 67 96 b 67 88 79 88 79 96 b 79 104 67 104 67 96",
    "Flor 21T": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 0 58 b 0 50 12 50 12 58 b 12 66 0 66 0 58 m 88 58 b 88 50 100 50 100 58 b 100 66 88 66 88 58 m 22 96 b 22 88 34 88 34 96 b 34 104 22 104 22 96 m 66 20 b 66 12 78 12 78 20 b 78 28 66 28 66 20 m 22 20 b 22 12 34 12 34 20 b 34 28 22 28 22 20 m 67 96 b 67 88 79 88 79 96 b 79 104 67 104 67 96",
    "flower21t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 0 58 b 0 50 12 50 12 58 b 12 66 0 66 0 58 m 88 58 b 88 50 100 50 100 58 b 100 66 88 66 88 58 m 22 96 b 22 88 34 88 34 96 b 34 104 22 104 22 96 m 66 20 b 66 12 78 12 78 20 b 78 28 66 28 66 20 m 22 20 b 22 12 34 12 34 20 b 34 28 22 28 22 20 m 67 96 b 67 88 79 88 79 96 b 79 104 67 104 67 96",
    "Flor 22T": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 19 43 b 19 35 31 35 31 43 b 31 51 19 51 19 43 m 19 73 b 19 65 31 65 31 73 b 31 81 19 81 19 73 m 69 43 b 69 35 81 35 81 43 b 81 51 69 51 69 43 m 69 73 b 69 65 81 65 81 73 b 81 81 69 81 69 73 m 44 87 b 44 79 56 79 56 87 b 56 95 44 95 44 87 m 44 28 b 44 20 56 20 56 28 b 56 36 44 36 44 28 m 44 58 b 44 50 56 50 56 58 b 56 66 44 66 44 58",
    "flower22t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 19 43 b 19 35 31 35 31 43 b 31 51 19 51 19 43 m 19 73 b 19 65 31 65 31 73 b 31 81 19 81 19 73 m 69 43 b 69 35 81 35 81 43 b 81 51 69 51 69 43 m 69 73 b 69 65 81 65 81 73 b 81 81 69 81 69 73 m 44 87 b 44 79 56 79 56 87 b 56 95 44 95 44 87 m 44 28 b 44 20 56 20 56 28 b 56 36 44 36 44 28 m 44 58 b 44 50 56 50 56 58 b 56 66 44 66 44 58",
    "Flor 23T": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 56 48 l 78 42 l 61 58 l 78 75 l 56 67 l 50 88 l 44 67 l 23 75 l 39 58 l 23 42 l 44 48 l 50 28 l 56 48",
    "flower23t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 56 48 l 78 42 l 61 58 l 78 75 l 56 67 l 50 88 l 44 67 l 23 75 l 39 58 l 23 42 l 44 48 l 50 28 l 56 48",
    "Flor 24T": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 56 48 l 94 33 l 61 58 l 94 84 l 56 67 l 50 109 l 44 67 l 6 84 l 39 58 l 6 33 l 44 48 l 50 8 l 56 48",
    "flower24t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 56 48 l 94 33 l 61 58 l 94 84 l 56 67 l 50 109 l 44 67 l 6 84 l 39 58 l 6 33 l 44 48 l 50 8 l 56 48",
    "Flor 25T": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46",
    "flower25t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46",
    "Flor 26T": "m 50 55 b 33 98 44 110 50 110 b 54 110 64 98 50 55 b 78 88 95 86 97 83 b 100 79 94 63 50 55 b 6 63 0 79 2 83 b 4 86 21 88 50 55 b 21 23 4 25 2 28 b 0 31 6 46 50 55 b 94 46 100 31 97 28 b 95 25 78 23 50 55 b 64 14 53 0 50 0 b 45 0 33 14 50 55 m 100 55 b 100 42 83 42 83 55 b 83 68 100 68 100 55 m 17 55 b 17 42 0 42 0 55 b 0 68 17 68 17 55 m 78 91 b 78 78 61 78 61 91 b 61 103 78 103 78 91 m 37 91 b 37 78 20 78 20 91 b 20 103 37 103 37 91 m 78 19 b 78 7 61 7 61 19 b 61 32 78 32 78 19 m 37 19 b 37 7 20 7 20 19 b 20 32 37 32 37 19 m 62 55 b 62 38 38 38 38 55 b 38 72 62 72 62 55",
    "flower26t": "m 50 55 b 33 98 44 110 50 110 b 54 110 64 98 50 55 b 78 88 95 86 97 83 b 100 79 94 63 50 55 b 6 63 0 79 2 83 b 4 86 21 88 50 55 b 21 23 4 25 2 28 b 0 31 6 46 50 55 b 94 46 100 31 97 28 b 95 25 78 23 50 55 b 64 14 53 0 50 0 b 45 0 33 14 50 55 m 100 55 b 100 42 83 42 83 55 b 83 68 100 68 100 55 m 17 55 b 17 42 0 42 0 55 b 0 68 17 68 17 55 m 78 91 b 78 78 61 78 61 91 b 61 103 78 103 78 91 m 37 91 b 37 78 20 78 20 91 b 20 103 37 103 37 91 m 78 19 b 78 7 61 7 61 19 b 61 32 78 32 78 19 m 37 19 b 37 7 20 7 20 19 b 20 32 37 32 37 19 m 62 55 b 62 38 38 38 38 55 b 38 72 62 72 62 55",
    "Flor 27T": "m 50 55 b 35 98 45 110 50 110 b 55 110 65 98 50 55 b 79 88 96 87 98 83 b 100 80 95 63 50 55 b 7 63 0 80 2 83 b 4 87 21 88 50 55 b 21 23 4 25 2 28 b 0 31 7 47 50 55 b 95 47 100 31 98 28 b 96 25 79 23 50 55 b 65 14 55 0 50 0 b 45 0 35 14 50 55 m 62 55 b 62 38 38 38 38 55 b 38 72 62 72 62 55",
    "flower27t": "m 50 55 b 35 98 45 110 50 110 b 55 110 65 98 50 55 b 79 88 96 87 98 83 b 100 80 95 63 50 55 b 7 63 0 80 2 83 b 4 87 21 88 50 55 b 21 23 4 25 2 28 b 0 31 7 47 50 55 b 95 47 100 31 98 28 b 96 25 79 23 50 55 b 65 14 55 0 50 0 b 45 0 35 14 50 55 m 62 55 b 62 38 38 38 38 55 b 38 72 62 72 62 55",
    "Flor 28T": "m 50 55 b 35 98 45 110 50 110 b 55 110 65 98 50 55 b 79 88 96 87 98 83 b 100 80 95 63 50 55 b 7 63 0 80 2 83 b 4 87 21 88 50 55 b 21 23 4 25 2 28 b 0 31 7 47 50 55 b 95 47 100 31 98 28 b 96 25 79 23 50 55 b 65 14 55 0 50 0 b 45 0 35 14 50 55",
    "flower28t": "m 50 55 b 35 98 45 110 50 110 b 55 110 65 98 50 55 b 79 88 96 87 98 83 b 100 80 95 63 50 55 b 7 63 0 80 2 83 b 4 87 21 88 50 55 b 21 23 4 25 2 28 b 0 31 7 47 50 55 b 95 47 100 31 98 28 b 96 25 79 23 50 55 b 65 14 55 0 50 0 b 45 0 35 14 50 55",
    "Flor 29T": "m 50 55 b 33 98 44 110 50 110 b 54 110 64 98 50 55 b 78 88 95 86 97 83 b 100 79 94 63 50 55 b 6 63 0 79 2 83 b 4 86 21 88 50 55 b 21 23 4 25 2 28 b 0 31 6 46 50 55 b 94 46 100 31 97 28 b 95 25 78 23 50 55 b 64 14 53 0 50 0 b 45 0 33 14 50 55 m 100 55 b 100 42 83 42 83 55 b 83 68 100 68 100 55 m 17 55 b 17 42 0 42 0 55 b 0 68 17 68 17 55 m 78 91 b 78 78 61 78 61 91 b 61 103 78 103 78 91 m 37 91 b 37 78 20 78 20 91 b 20 103 37 103 37 91 m 78 19 b 78 7 61 7 61 19 b 61 32 78 32 78 19 m 37 19 b 37 7 20 7 20 19 b 20 32 37 32 37 19",
    "flower29t": "m 50 55 b 33 98 44 110 50 110 b 54 110 64 98 50 55 b 78 88 95 86 97 83 b 100 79 94 63 50 55 b 6 63 0 79 2 83 b 4 86 21 88 50 55 b 21 23 4 25 2 28 b 0 31 6 46 50 55 b 94 46 100 31 97 28 b 95 25 78 23 50 55 b 64 14 53 0 50 0 b 45 0 33 14 50 55 m 100 55 b 100 42 83 42 83 55 b 83 68 100 68 100 55 m 17 55 b 17 42 0 42 0 55 b 0 68 17 68 17 55 m 78 91 b 78 78 61 78 61 91 b 61 103 78 103 78 91 m 37 91 b 37 78 20 78 20 91 b 20 103 37 103 37 91 m 78 19 b 78 7 61 7 61 19 b 61 32 78 32 78 19 m 37 19 b 37 7 20 7 20 19 b 20 32 37 32 37 19",
    "Cristal 17": "m 56 50 l 64 100 l 38 78 l 56 50 m 56 50 l 24 100 l 0 65 l 56 50 m 56 50 l 0 65 l 28 39 l 56 50 m 56 50 l 31 0 l 0 28 l 56 50 m 56 50 l 78 0 l 42 22 l 56 50 m 56 50 l 100 40 l 68 23 l 56 50 m 56 50 l 100 40 l 61 80 l 56 50 m 100 40 l 61 80 l 56 50 m 100 40 l 77 64 l 100 100 l 100 40 m 61 80 l 100 100 l 77 64 l 61 80 m 61 80 l 64 100 l 100 100 l 61 80 m 38 78 l 24 100 l 64 100 l 38 78 m 0 65 l 0 100 l 24 100 l 0 65 m 0 28 l 0 65 l 28 39 l 0 28 m 31 0 l 0 0 l 0 28 l 31 0 m 78 0 l 31 0 l 42 22 l 78 0 m 100 0 l 68 23 l 100 40 l 100 0 m 100 0 l 78 0 l 68 23 l 100 0",
    "cristal17": "m 56 50 l 64 100 l 38 78 l 56 50 m 56 50 l 24 100 l 0 65 l 56 50 m 56 50 l 0 65 l 28 39 l 56 50 m 56 50 l 31 0 l 0 28 l 56 50 m 56 50 l 78 0 l 42 22 l 56 50 m 56 50 l 100 40 l 68 23 l 56 50 m 56 50 l 100 40 l 61 80 l 56 50 m 100 40 l 61 80 l 56 50 m 100 40 l 77 64 l 100 100 l 100 40 m 61 80 l 100 100 l 77 64 l 61 80 m 61 80 l 64 100 l 100 100 l 61 80 m 38 78 l 24 100 l 64 100 l 38 78 m 0 65 l 0 100 l 24 100 l 0 65 m 0 28 l 0 65 l 28 39 l 0 28 m 31 0 l 0 0 l 0 28 l 31 0 m 78 0 l 31 0 l 42 22 l 78 0 m 100 0 l 68 23 l 100 40 l 100 0 m 100 0 l 78 0 l 68 23 l 100 0",
    "Geom. 10": "m 0 50 l 0 100 l 100 100 l 100 50 l 90 50 l 90 90 l 10 90 l 10 50 l 0 50 m 0 50 l 10 50 l 10 10 l 90 10 l 90 50 l 100 50 l 100 0 l 0 0 l 0 50 m 50 90 l 50 80 l 20 80 l 20 20 l 50 20 l 50 10 l 10 10 l 10 90 l 50 90 m 50 90 l 90 90 l 90 10 l 50 10 l 50 20 l 80 20 l 80 80 l 50 80 l 50 90 m 20 50 l 20 80 l 80 80 l 80 50 l 70 50 l 70 70 l 30 70 l 30 50 l 20 50 m 20 50 l 30 50 l 30 30 l 70 30 l 70 50 l 80 50 l 80 20 l 20 20 l 20 50 m 50 70 l 50 60 l 40 60 l 40 40 l 50 40 l 50 30 l 30 30 l 30 70 l 50 70 m 50 70 l 70 70 l 70 30 l 50 30 l 50 40 l 60 40 l 60 60 l 50 60 l 50 70 m 40 50 l 40 60 l 60 60 l 60 50 l 40 50 m 40 50 l 60 50 l 60 40 l 40 40 l 40 50",
    "Geometrico 10": "m 0 50 l 0 100 l 100 100 l 100 50 l 90 50 l 90 90 l 10 90 l 10 50 l 0 50 m 0 50 l 10 50 l 10 10 l 90 10 l 90 50 l 100 50 l 100 0 l 0 0 l 0 50 m 50 90 l 50 80 l 20 80 l 20 20 l 50 20 l 50 10 l 10 10 l 10 90 l 50 90 m 50 90 l 90 90 l 90 10 l 50 10 l 50 20 l 80 20 l 80 80 l 50 80 l 50 90 m 20 50 l 20 80 l 80 80 l 80 50 l 70 50 l 70 70 l 30 70 l 30 50 l 20 50 m 20 50 l 30 50 l 30 30 l 70 30 l 70 50 l 80 50 l 80 20 l 20 20 l 20 50 m 50 70 l 50 60 l 40 60 l 40 40 l 50 40 l 50 30 l 30 30 l 30 70 l 50 70 m 50 70 l 70 70 l 70 30 l 50 30 l 50 40 l 60 40 l 60 60 l 50 60 l 50 70 m 40 50 l 40 60 l 60 60 l 60 50 l 40 50 m 40 50 l 60 50 l 60 40 l 40 40 l 40 50",
    "geometric10": "m 0 50 l 0 100 l 100 100 l 100 50 l 90 50 l 90 90 l 10 90 l 10 50 l 0 50 m 0 50 l 10 50 l 10 10 l 90 10 l 90 50 l 100 50 l 100 0 l 0 0 l 0 50 m 50 90 l 50 80 l 20 80 l 20 20 l 50 20 l 50 10 l 10 10 l 10 90 l 50 90 m 50 90 l 90 90 l 90 10 l 50 10 l 50 20 l 80 20 l 80 80 l 50 80 l 50 90 m 20 50 l 20 80 l 80 80 l 80 50 l 70 50 l 70 70 l 30 70 l 30 50 l 20 50 m 20 50 l 30 50 l 30 30 l 70 30 l 70 50 l 80 50 l 80 20 l 20 20 l 20 50 m 50 70 l 50 60 l 40 60 l 40 40 l 50 40 l 50 30 l 30 30 l 30 70 l 50 70 m 50 70 l 70 70 l 70 30 l 50 30 l 50 40 l 60 40 l 60 60 l 50 60 l 50 70 m 40 50 l 40 60 l 60 60 l 60 50 l 40 50 m 40 50 l 60 50 l 60 40 l 40 40 l 40 50",
    "Diag. 13R": "m 15 0 l 0 0 l 0 15 l 15 0 m 15 0 l 0 15 l 0 30 l 30 0 l 15 0 m 30 0 l 0 30 l 0 45 l 45 0 l 30 0 m 45 0 l 0 45 l 0 60 l 60 0 l 45 0 m 60 0 l 0 60 l 0 75 l 75 0 l 60 0 m 75 0 l 0 75 l 0 90 l 90 0 l 75 0 m 90 0 l 0 90 l 0 100 l 5 100 l 100 5 l 100 0 l 90 0 m 100 5 l 5 100 l 20 100 l 100 20 l 100 5 m 100 20 l 20 100 l 35 100 l 100 35 l 100 20 m 100 35 l 35 100 l 50 100 l 100 50 l 100 35 m 100 50 l 50 100 l 65 100 l 100 65 l 100 50 m 100 65 l 65 100 l 80 100 l 100 80 l 100 65 m 100 80 l 80 100 l 100 100 l 100 80",
    "Diagonal 13R": "m 15 0 l 0 0 l 0 15 l 15 0 m 15 0 l 0 15 l 0 30 l 30 0 l 15 0 m 30 0 l 0 30 l 0 45 l 45 0 l 30 0 m 45 0 l 0 45 l 0 60 l 60 0 l 45 0 m 60 0 l 0 60 l 0 75 l 75 0 l 60 0 m 75 0 l 0 75 l 0 90 l 90 0 l 75 0 m 90 0 l 0 90 l 0 100 l 5 100 l 100 5 l 100 0 l 90 0 m 100 5 l 5 100 l 20 100 l 100 20 l 100 5 m 100 20 l 20 100 l 35 100 l 100 35 l 100 20 m 100 35 l 35 100 l 50 100 l 100 50 l 100 35 m 100 50 l 50 100 l 65 100 l 100 65 l 100 50 m 100 65 l 65 100 l 80 100 l 100 80 l 100 65 m 100 80 l 80 100 l 100 100 l 100 80",
    "diagonal13r": "m 15 0 l 0 0 l 0 15 l 15 0 m 15 0 l 0 15 l 0 30 l 30 0 l 15 0 m 30 0 l 0 30 l 0 45 l 45 0 l 30 0 m 45 0 l 0 45 l 0 60 l 60 0 l 45 0 m 60 0 l 0 60 l 0 75 l 75 0 l 60 0 m 75 0 l 0 75 l 0 90 l 90 0 l 75 0 m 90 0 l 0 90 l 0 100 l 5 100 l 100 5 l 100 0 l 90 0 m 100 5 l 5 100 l 20 100 l 100 20 l 100 5 m 100 20 l 20 100 l 35 100 l 100 35 l 100 20 m 100 35 l 35 100 l 50 100 l 100 50 l 100 35 m 100 50 l 50 100 l 65 100 l 100 65 l 100 50 m 100 65 l 65 100 l 80 100 l 100 80 l 100 65 m 100 80 l 80 100 l 100 100 l 100 80",
    "Diag. 13L": "m 0 85 l 0 100 l 15 100 l 0 85 m 0 85 l 15 100 l 30 100 l 0 70 l 0 85 m 0 70 l 30 100 l 45 100 l 0 55 l 0 70 m 0 55 l 45 100 l 60 100 l 0 40 l 0 55 m 0 40 l 60 100 l 75 100 l 0 25 l 0 40 m 0 25 l 75 100 l 90 100 l 0 10 l 0 25 m 0 10 l 90 100 l 100 100 l 100 95 l 5 0 l 0 0 l 0 10 m 5 0 l 100 95 l 100 80 l 20 0 l 5 0 m 20 0 l 100 80 l 100 65 l 35 0 l 20 0 m 35 0 l 100 65 l 100 50 l 50 0 l 35 0 m 50 0 l 100 50 l 100 35 l 65 0 l 50 0 m 65 0 l 100 35 l 100 20 l 80 0 l 65 0 m 80 0 l 100 20 l 100 0 l 80 0",
    "Diagonal 13L": "m 0 85 l 0 100 l 15 100 l 0 85 m 0 85 l 15 100 l 30 100 l 0 70 l 0 85 m 0 70 l 30 100 l 45 100 l 0 55 l 0 70 m 0 55 l 45 100 l 60 100 l 0 40 l 0 55 m 0 40 l 60 100 l 75 100 l 0 25 l 0 40 m 0 25 l 75 100 l 90 100 l 0 10 l 0 25 m 0 10 l 90 100 l 100 100 l 100 95 l 5 0 l 0 0 l 0 10 m 5 0 l 100 95 l 100 80 l 20 0 l 5 0 m 20 0 l 100 80 l 100 65 l 35 0 l 20 0 m 35 0 l 100 65 l 100 50 l 50 0 l 35 0 m 50 0 l 100 50 l 100 35 l 65 0 l 50 0 m 65 0 l 100 35 l 100 20 l 80 0 l 65 0 m 80 0 l 100 20 l 100 0 l 80 0",
    "diagonal13l": "m 0 85 l 0 100 l 15 100 l 0 85 m 0 85 l 15 100 l 30 100 l 0 70 l 0 85 m 0 70 l 30 100 l 45 100 l 0 55 l 0 70 m 0 55 l 45 100 l 60 100 l 0 40 l 0 55 m 0 40 l 60 100 l 75 100 l 0 25 l 0 40 m 0 25 l 75 100 l 90 100 l 0 10 l 0 25 m 0 10 l 90 100 l 100 100 l 100 95 l 5 0 l 0 0 l 0 10 m 5 0 l 100 95 l 100 80 l 20 0 l 5 0 m 20 0 l 100 80 l 100 65 l 35 0 l 20 0 m 35 0 l 100 65 l 100 50 l 50 0 l 35 0 m 50 0 l 100 50 l 100 35 l 65 0 l 50 0 m 65 0 l 100 35 l 100 20 l 80 0 l 65 0 m 80 0 l 100 20 l 100 0 l 80 0",
}

SHAPES_LIB_MAP = {}
for _k, _v in RAW_PRESET_SHAPES.items():
    SHAPES_LIB_MAP[_k] = lambda ctx=None, p=_v: p

# Aliases adicionales con acentos y variaciones
for _k, _v in list(RAW_PRESET_SHAPES.items()):
    clean = _k.lower().replace(" ", "").replace(".", "").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
    SHAPES_LIB_MAP[clean] = lambda ctx=None, p=_v: p

def resolve_shape_value(shp_val, context=None):
    """Resuelve cualquier referencia a forma vectorial, incluyendo sintaxis 'shape.nombre' o nombres de la librería."""
    if not shp_val:
        return ""
    s_val = str(shp_val).strip()
    if s_val.lower().startswith("shape."):
        shape_name = s_val[6:].strip()
        clean = shape_name.lower().replace(" ", "").replace(".", "").replace("_", "").replace("-", "")
        clean_no_acc = clean.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        if clean in SHAPES_LIB_MAP:
            return SHAPES_LIB_MAP[clean](context)
        if clean_no_acc in SHAPES_LIB_MAP:
            return SHAPES_LIB_MAP[clean_no_acc](context)
        if shape_name in RAW_PRESET_SHAPES:
            return RAW_PRESET_SHAPES[shape_name]
        for k, v in RAW_PRESET_SHAPES.items():
            k_clean = k.lower().replace(" ", "").replace(".", "").replace("_", "").replace("-", "")
            k_clean_no_acc = k_clean.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
            if k_clean == clean or k_clean_no_acc == clean_no_acc:
                return v
        return RAW_PRESET_SHAPES.get("Circulo", "")
    return s_val

def eval_shapes_lib_node(context=None, **kwargs):
    """Manejador unificado para el Nodo Maestro Shapes Lib con soporte para 80 formas."""
    forma = str(kwargs.get("forma", kwargs.get("shape", kwargs.get("modo", "Circulo")))).strip()
    if forma.lower().startswith("shape."):
        return resolve_shape_value(forma, context)
    if forma in SHAPES_LIB_MAP:
        return SHAPES_LIB_MAP[forma](context)
    
    clean_search = forma.lower().replace(" ", "").replace(".", "").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
    if clean_search in SHAPES_LIB_MAP:
        return SHAPES_LIB_MAP[clean_search](context)
        
    for k, v in RAW_PRESET_SHAPES.items():
        if k.lower().replace(" ", "").replace(".", "").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u") == clean_search:
            return v
            
    return RAW_PRESET_SHAPES.get("Circulo", "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 ")

NODE_REGISTRY["Shape/Shapes Library"] = eval_shapes_lib_node
NODE_REGISTRY["Shapes Library"] = eval_shapes_lib_node

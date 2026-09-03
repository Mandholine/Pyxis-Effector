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
import math
import numpy as np
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

def shape_manipulator(context, drawing="", scale_x=1.0, scale_y=1.0, rot=0.0, offset_x=0.0, offset_y=0.0, offset_border=0.0, mode="center"):
    """Aplica manipulaciones afines elementales (escala, rotación, desplazamiento, offsetting) a un dibujo vectorial ASS (m ...).
    Modos de anclaje (Shapery):
      - 'center': Centra el shape alrededor de (0,0) [Shape to center].
      - 'origin': Alinea la esquina superior izquierda del bounding box a (0,0) [Shape to origin].
      - 'zero': Traslada el shape a las coordenadas de pantalla/canvas (pos_x, pos_y) [Shape to 0,0].
      - 'pos': Hace el shape relativo a la posición (pos_x, pos_y) [Shape to pos].
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

    from node_engine import _eval_num_expr

    delta = _eval_num_expr(offset_border, context, 0.0) if (offset_border is not None and offset_border != "") else 0.0
    if abs(delta) > 0.0001:
        from clipper_engine import ClipperEngine
        off_shp = ClipperEngine.offset_shape(raw_shp, delta)
        if off_shp and off_shp.strip():
            raw_shp = off_shp

    sx = _eval_num_expr(scale_x, context, 1.0) if scale_x != "" else 1.0
    sy = _eval_num_expr(scale_y, context, 1.0) if scale_y != "" else 1.0
    angle = _eval_num_expr(rot, context, 0.0) if rot != "" else 0.0
    tx = _eval_num_expr(offset_x, context, 0.0) if offset_x != "" else 0.0
    ty = _eval_num_expr(offset_y, context, 0.0) if offset_y != "" else 0.0

    anchor_str = str(mode or "center").strip().lower()

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
    if isinstance(context, dict):
        unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
        try:
            pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
        except: pos_x = 0.0
        try:
            pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
        except: pos_y = 0.0

    if anchor_str == "origin":
        ref_x, ref_y = min_x, min_y
        base_x, base_y = 0.0, 0.0
    elif anchor_str == "zero":
        ref_x, ref_y = cx, cy
        base_x, base_y = pos_x, pos_y
    elif anchor_str == "pos":
        ref_x, ref_y = pos_x, pos_y
        base_x, base_y = 0.0, 0.0
    else:  # "center" (default)
        ref_x, ref_y = cx, cy
        base_x, base_y = 0.0, 0.0

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

                    final_x = base_x + rot_x + tx
                    final_y = base_y + rot_y + ty

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




def _shape_inflate(drawing, t=0.5, ratio=1.0, mode="circle", anchor="center", context=None):
    """Aplica deformación morfológica radial (esferificación/abombamiento) a un dibujo ASS.
    Modo 'circle': infla radialmente hacia una circunferencia circunscrita.
    Modo 'ellipse': infla radialmente hacia una elipse circunscrita adaptada al aspecto del bounding box.
    """
    if not drawing or not isinstance(drawing, str):
        return ""

    tokens = drawing.strip().split()
    if not tokens:
        return ""

    commands = []
    i = 0
    curr_cmd = 'm'
    coords = []

    while i < len(tokens):
        tok = tokens[i]
        if tok.isalpha() and tok.lower() in ('m', 'l', 'b', 's', 'p', 'c'):
            curr_cmd = tok.lower()
            i += 1
            if curr_cmd == 'c':
                commands.append(('c', []))
            continue
        try:
            x = float(tok)
            if i + 1 < len(tokens):
                y = float(tokens[i + 1])
                commands.append((curr_cmd, [x, y]))
                coords.append((x, y))
                i += 2
                continue
        except ValueError:
            pass
        i += 1

    if not coords:
        return drawing

    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = max_x - min_x
    h = max_y - min_y
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0

    if w <= 1e-6 or h <= 1e-6:
        return drawing

    from node_engine import _eval_num_expr
    t_val = _eval_num_expr(t, context, 0.5) if (t is not None and t != "") else 0.5
    ratio_val = _eval_num_expr(ratio, context, 1.0) if (ratio is not None and ratio != "") else 1.0

    # Subdividir segmentos rectos si t != 0 para que los bordes planos puedan curvarse
    max_step = max(5.0, min(w, h) / 16.0)
    subdivided_cmds = []
    last_pt = None

    for cmd, pt in commands:
        if not pt:
            subdivided_cmds.append((cmd, pt))
            continue

        if last_pt is not None and cmd == 'l' and abs(t_val) > 0.001:
            dx = pt[0] - last_pt[0]
            dy = pt[1] - last_pt[1]
            dist = math.hypot(dx, dy)
            if dist > max_step:
                steps = int(math.ceil(dist / max_step))
                for s in range(1, steps):
                    frac = s / steps
                    subdivided_cmds.append(('l', [last_pt[0] + dx * frac, last_pt[1] + dy * frac]))

        subdivided_cmds.append((cmd, pt))
        last_pt = pt

    mode_str = str(mode or "circle").strip().lower()
    is_circle = mode_str in ("circle", "circulo")
    diameter = math.sqrt((w * w + h * h) / 2.0)
    r1 = (diameter if is_circle else w) * math.sqrt(2.0) / 2.0 * ratio_val
    r2 = (diameter if is_circle else h) * math.sqrt(2.0) / 2.0

    EPSILON = 1e-6

    inflated_pts = []
    for cmd, pt in subdivided_cmds:
        if not pt:
            inflated_pts.append((cmd, None))
            continue
        x, y = pt[0], pt[1]
        dx = x - cx
        dy = y - cy
        dist = math.hypot(dx, dy)
        if dist > EPSILON:
            angle = math.atan2(dy, dx)
            _cos = math.cos(angle)
            _sin = math.sin(angle)
            denom = math.sqrt(r2 * r2 * _cos * _cos + r1 * r1 * _sin * _sin)
            radius = (r1 * r2) / denom if denom > EPSILON else r1
            ux = dx / dist
            uy = dy / dist
            new_dist = dist * (1.0 - t_val) + radius * t_val
            nx = cx + ux * new_dist
            ny = cy + uy * new_dist
            inflated_pts.append((cmd, [nx, ny]))
        else:
            inflated_pts.append((cmd, [x, y]))

    all_new_x = [p[1][0] for p in inflated_pts if p[1]]
    all_new_y = [p[1][1] for p in inflated_pts if p[1]]
    new_min_x, new_max_x = min(all_new_x), max(all_new_x)
    new_min_y, new_max_y = min(all_new_y), max(all_new_y)
    new_cx = (new_min_x + new_max_x) / 2.0
    new_cy = (new_min_y + new_max_y) / 2.0

    anchor_str = str(anchor or "center").strip().lower()
    if anchor_str == "origin":
        off_x, off_y = -new_min_x, -new_min_y
    elif anchor_str == "zero":
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = pos_x - new_cx, pos_y - new_cy
    elif anchor_str == "pos":
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = -pos_x, -pos_y
    else:  # "center" (default)
        off_x, off_y = -new_cx, -new_cy

    out_tokens = []
    last_cmd = None
    for cmd, pt in inflated_pts:
        if not pt:
            out_tokens.append(cmd)
            last_cmd = cmd
            continue
        if cmd != last_cmd:
            out_tokens.append(cmd)
            last_cmd = cmd
        final_x = pt[0] + off_x
        final_y = pt[1] + off_y
        fmt_x = int(final_x) if final_x.is_integer() else round(final_x, 2)
        fmt_y = int(final_y) if final_y.is_integer() else round(final_y, 2)
        out_tokens.append(str(fmt_x))
        out_tokens.append(str(fmt_y))

    return " ".join(out_tokens) + " "




def _shape_skew(drawing, angle_x=0.0, angle_y=0.0, anchor="center", context=None, **kwargs):
    """Aplica cizallamiento 2D / inclinación planar angular (Skew / Shear) a un dibujo ASS.
    Transformación afín planar limpia:
      x' = base_x + rel_x + rel_y * tan(rad(angle_x))
      y' = base_y + rel_y + rel_x * tan(rad(angle_y))
    """
    if not drawing or not isinstance(drawing, str):
        return ""

    tokens = drawing.strip().split()
    if not tokens:
        return ""

    coords = []
    for tok in tokens:
        try:
            coords.append(float(tok))
        except ValueError:
            pass

    if not coords or len(coords) < 2:
        return drawing

    xs = coords[0::2]
    ys = coords[1::2]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0

    # Evaluación numérica robusta de ángulos con soporte de expresiones y alias
    ax_in = angle_x if (angle_x is not None and str(angle_x).strip() != "") else kwargs.get("angle_x", kwargs.get("angle", kwargs.get("ang_x", kwargs.get("skew_x", 0.0))))
    ay_in = angle_y if (angle_y is not None and str(angle_y).strip() != "") else kwargs.get("angle_y", kwargs.get("ang_y", kwargs.get("skew_y", 0.0)))

    try:
        if isinstance(ax_in, (int, float)):
            ax = float(ax_in)
        elif ax_in is not None and str(ax_in).strip() != "":
            from node_engine import _eval_num_expr
            ax = float(_eval_num_expr(ax_in, context, 0.0))
        else:
            ax = 0.0
    except Exception:
        ax = 0.0

    try:
        if isinstance(ay_in, (int, float)):
            ay = float(ay_in)
        elif ay_in is not None and str(ay_in).strip() != "":
            from node_engine import _eval_num_expr
            ay = float(_eval_num_expr(ay_in, context, 0.0))
        else:
            ay = 0.0
    except Exception:
        ay = 0.0

    anchor_str = str(anchor or "center").strip().lower()

    # Limitar ángulos a (-89.9°, 89.9°) para evitar asíntotas infinitas
    ax = max(-89.9, min(89.9, ax))
    ay = max(-89.9, min(89.9, ay))

    tan_x = math.tan(math.radians(ax))
    tan_y = math.tan(math.radians(ay))

    pos_x, pos_y = 0.0, 0.0
    if isinstance(context, dict):
        unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
        try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
        except: pos_x = 0.0
        try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
        except: pos_y = 0.0

    if anchor_str == "origin":
        ref_x, ref_y = min_x, min_y
        base_x, base_y = 0.0, 0.0
    elif anchor_str == "zero":
        ref_x, ref_y = cx, cy
        base_x, base_y = pos_x, pos_y
    elif anchor_str == "pos":
        ref_x, ref_y = pos_x, pos_y
        base_x, base_y = 0.0, 0.0
    else:  # "center" (default)
        ref_x, ref_y = cx, cy
        base_x, base_y = 0.0, 0.0

    out_tokens = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        try:
            x_val = float(tok)
            if i + 1 < len(tokens):
                try:
                    y_val = float(tokens[i + 1])
                    rel_x = x_val - ref_x
                    rel_y = y_val - ref_y

                    # Transformación afín exacta de Skew
                    nx = base_x + rel_x + rel_y * tan_x
                    ny = base_y + rel_y + rel_x * tan_y

                    if abs(nx) < 1e-9: nx = 0.0
                    if abs(ny) < 1e-9: ny = 0.0
                    fmt_x = int(nx) if nx.is_integer() else round(nx, 2)
                    fmt_y = int(ny) if ny.is_integer() else round(ny, 2)
                    out_tokens.append(str(fmt_x))
                    out_tokens.append(str(fmt_y))
                    i += 2
                    continue
                except ValueError:
                    pass
            out_tokens.append(tok)
            i += 1
        except ValueError:
            out_tokens.append(tok)
            i += 1

    return " ".join(out_tokens) + " "



def _shape_round_corners(drawing, radius=10.0, mode="Round", anchor="center", context=None):
    """Redondea (Round con curvas Bézier) o bisela (Bevel con rectas) las esquinas poliédricas de un dibujo ASS.
    """
    if not drawing or not isinstance(drawing, str):
        return ""

    from node_engine import _eval_num_expr
    rad = _eval_num_expr(radius, context, 10.0) if (radius is not None and radius != "") else 10.0

    anchor_str = str(anchor or "center").strip().lower()

    tokens = drawing.strip().split()
    if not tokens:
        return ""

    contours = []
    curr_cmd = 'm'
    curr_contour = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.isalpha() and tok.lower() in ('m', 'l', 'b', 's', 'p', 'c'):
            curr_cmd = tok.lower()
            i += 1
            if curr_cmd == 'm' and curr_contour:
                contours.append(curr_contour)
                curr_contour = []
            if curr_cmd == 'c':
                curr_contour.append(('c', []))
            continue
        try:
            x = float(tok)
            if i + 1 < len(tokens):
                y = float(tokens[i + 1])
                curr_contour.append((curr_cmd, [x, y]))
                i += 2
                continue
        except ValueError:
            pass
        i += 1
    if curr_contour:
        contours.append(curr_contour)

    if not contours:
        return drawing

    mode_str = str(mode or "Round").strip().lower()
    is_bevel = mode_str in ("bevel", "bisel", "chaflan")
    negative = rad < 0
    abs_rad = abs(rad)

    def get_t(p0, p1, p2, r):
        d1 = math.hypot(p0[0] - p1[0], p0[1] - p1[1])
        d2 = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        dmin = min(d1, d2)
        if dmin < 1e-6:
            return 0.0, 0.0
        eff_r = min(r, 0.45 * dmin)
        return eff_r / d1, eff_r / d2

    def ipol(p_from, p_to, t):
        return [p_from[0] + (p_to[0] - p_from[0]) * t, p_from[1] + (p_to[1] - p_from[1]) * t]

    rounded_contours = []
    for contour in contours:
        pts = [c[1] for c in contour if c[1]]
        if len(pts) < 3:
            rounded_contours.append(contour)
            continue

        is_closed = True
        if math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-4:
            pts.pop()

        n = len(pts)
        if n < 3:
            rounded_contours.append(contour)
            continue

        res_cmds = []
        if is_closed:
            t0_0, t1_0 = get_t(pts[-1], pts[0], pts[1], abs_rad)
            start_pt = ipol(pts[0], pts[1], t1_0)
            res_cmds.append(('m', start_pt))

            for j in range(1, n):
                p_prev = pts[j - 1]
                p_curr = pts[j]
                p_next = pts[(j + 1) % n]
                t0, t1 = get_t(p_prev, p_curr, p_next, abs_rad)

                p1 = ipol(p_curr, p_prev, t0)
                res_cmds.append(('l', p1))

                if is_bevel:
                    p2 = ipol(p_curr, p_next, t1)
                    res_cmds.append(('l', p2))
                else:  # Round
                    p2 = ipol(p_curr, p_prev, 0.42 * t0)
                    p3 = ipol(p_curr, p_next, 0.42 * t1)
                    p4 = ipol(p_curr, p_next, t1)
                    if negative:
                        dx = p4[0] - p1[0]
                        dy = p4[1] - p1[1]
                        chord_len = math.hypot(dx, dy)
                        if chord_len > 1e-6:
                            nx = -dy / chord_len
                            ny = dx / chord_len
                            for cp in (p2, p3):
                                vx = cp[0] - p1[0]
                                vy = cp[1] - p1[1]
                                dot_n = vx * nx + vy * ny
                                cp[0] -= 2.0 * dot_n * nx
                                cp[1] -= 2.0 * dot_n * ny
                    res_cmds.append(('b', [p2[0], p2[1], p3[0], p3[1], p4[0], p4[1]]))

            p_prev = pts[-1]
            p_curr = pts[0]
            p_next = pts[1]
            t0, t1 = get_t(p_prev, p_curr, p_next, abs_rad)
            p1 = ipol(p_curr, p_prev, t0)
            res_cmds.append(('l', p1))
            if is_bevel:
                res_cmds.append(('l', start_pt))
            else:
                p2 = ipol(p_curr, p_prev, 0.42 * t0)
                p3 = ipol(p_curr, p_next, 0.42 * t1)
                res_cmds.append(('b', [p2[0], p2[1], p3[0], p3[1], start_pt[0], start_pt[1]]))
        else:
            res_cmds.append(('m', pts[0]))
            for j in range(1, n - 1):
                p_prev = pts[j - 1]
                p_curr = pts[j]
                p_next = pts[j + 1]
                t0, t1 = get_t(p_prev, p_curr, p_next, abs_rad)
                p1 = ipol(p_curr, p_prev, t0)
                res_cmds.append(('l', p1))
                if is_bevel:
                    p2 = ipol(p_curr, p_next, t1)
                    res_cmds.append(('l', p2))
                else:
                    p2 = ipol(p_curr, p_prev, 0.42 * t0)
                    p3 = ipol(p_curr, p_next, 0.42 * t1)
                    p4 = ipol(p_curr, p_next, t1)
                    res_cmds.append(('b', [p2[0], p2[1], p3[0], p3[1], p4[0], p4[1]]))
            res_cmds.append(('l', pts[-1]))

        rounded_contours.append(res_cmds)

    all_x = []
    all_y = []
    for contour in rounded_contours:
        for cmd, coords in contour:
            if coords:
                all_x.extend(coords[0::2])
                all_y.extend(coords[1::2])

    if not all_x:
        return drawing

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0

    if anchor_str == "origin":
        off_x, off_y = -min_x, -min_y
    elif anchor_str == "zero":
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = pos_x - cx, pos_y - cy
    elif anchor_str == "pos":
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = -pos_x, -pos_y
    else:  # "center" (default)
        off_x, off_y = -cx, -cy

    out_tokens = []
    for contour in rounded_contours:
        for cmd, coords in contour:
            out_tokens.append(cmd)
            for k in range(0, len(coords), 2):
                nx = coords[k] + off_x
                ny = coords[k + 1] + off_y
                if abs(nx) < 1e-9: nx = 0.0
                if abs(ny) < 1e-9: ny = 0.0
                fmt_x = int(nx) if nx.is_integer() else round(nx, 2)
                fmt_y = int(ny) if ny.is_integer() else round(ny, 2)
                out_tokens.append(str(fmt_x))
                out_tokens.append(str(fmt_y))

    return " ".join(out_tokens) + " "




def _shape_flexor(drawing, curve=None, t=1.0, bend=30.0, axis="x", anchor="center", context=None):
    """Deforma y curva un dibujo vectorial ASS a lo largo de una spline directriz o arco paramétrico."""
    if not drawing or not isinstance(drawing, str):
        return ""

    tokens = drawing.strip().split()
    if not tokens:
        return ""

    coords = []
    for tok in tokens:
        try:
            coords.append(float(tok))
        except ValueError:
            pass

    if not coords or len(coords) < 2:
        return drawing

    xs = coords[0::2]
    ys = coords[1::2]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w = max(1.0, max_x - min_x)
    h = max(1.0, max_y - min_y)
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0

    from node_engine import _eval_num_expr
    t_val = _eval_num_expr(t, context, 1.0) if (t is not None and t != "") else 1.0
    bend_val = _eval_num_expr(bend, context, 30.0) if (bend is not None and bend != "") else 30.0

    anchor_str = str(anchor or "center").strip().lower()

    # Subdividir segmentos largos del contorno para deformación suave
    subdivided = []
    i = 0
    curr_pt = None
    max_seg_len = 10.0

    while i < len(tokens):
        tok = tokens[i]
        if tok.isalpha() and tok.lower() in ('m', 'l', 'b', 's', 'p', 'c'):
            cmd = tok.lower()
            subdivided.append(cmd)
            i += 1
            if cmd == 'c':
                curr_pt = None
            continue
        try:
            x_val = float(tok)
            if i + 1 < len(tokens):
                y_val = float(tokens[i + 1])
                p_next = [x_val, y_val]
                if curr_pt is not None:
                    d = math.hypot(p_next[0] - curr_pt[0], p_next[1] - curr_pt[1])
                    if d > max_seg_len:
                        steps = int(math.ceil(d / max_seg_len))
                        for step in range(1, steps):
                            s = step / float(steps)
                            ix = curr_pt[0] + (p_next[0] - curr_pt[0]) * s
                            iy = curr_pt[1] + (p_next[1] - curr_pt[1]) * s
                            subdivided.append(str(round(ix, 2)))
                            subdivided.append(str(round(iy, 2)))
                subdivided.append(str(round(x_val, 2)))
                subdivided.append(str(round(y_val, 2)))
                curr_pt = p_next
                i += 2
                continue
        except ValueError:
            pass
        subdivided.append(tok)
        i += 1

    curve_str = str(curve or "").strip()
    is_custom_curve = curve_str.lower().startswith("m ") or curve_str.lower().startswith("m-") or curve_str.lower().startswith("m0")

    def sample_path(path_str):
        p_tokens = path_str.strip().split()
        cmds = []
        pi = 0
        p_cmd = 'm'
        while pi < len(p_tokens):
            ptok = p_tokens[pi]
            if ptok.isalpha() and ptok.lower() in ('m', 'l', 'b', 's', 'p', 'c'):
                p_cmd = ptok.lower()
                pi += 1
                continue
            try:
                px = float(ptok)
                if pi + 1 < len(p_tokens):
                    py = float(p_tokens[pi + 1])
                    cmds.append((p_cmd, px, py))
                    pi += 2
                    continue
            except ValueError:
                pass
            pi += 1

        if not cmds:
            return []

        samples = []
        c_pt = [cmds[0][1], cmds[0][2]]
        samples.append(c_pt)
        c_idx = 1
        while c_idx < len(cmds):
            c_type, cx_val, cy_val = cmds[c_idx]
            if c_type == 'm':
                c_pt = [cx_val, cy_val]
                samples.append(c_pt)
                c_idx += 1
            elif c_type == 'l':
                samples.append([cx_val, cy_val])
                c_pt = [cx_val, cy_val]
                c_idx += 1
            elif c_type == 'b':
                if c_idx + 2 < len(cmds):
                    p0 = c_pt
                    p1 = [cx_val, cy_val]
                    p2 = [cmds[c_idx+1][1], cmds[c_idx+1][2]]
                    p3 = [cmds[c_idx+2][1], cmds[c_idx+2][2]]
                    for step in range(1, 13):
                        st = step / 12.0
                        omt = 1.0 - st
                        bx = omt**3 * p0[0] + 3 * omt**2 * st * p1[0] + 3 * omt * st**2 * p2[0] + st**3 * p3[0]
                        by = omt**3 * p0[1] + 3 * omt**2 * st * p1[1] + 3 * omt * st**2 * p2[1] + st**3 * p3[1]
                        samples.append([bx, by])
                    c_pt = p3
                    c_idx += 3
                else:
                    samples.append([cx_val, cy_val])
                    c_pt = [cx_val, cy_val]
                    c_idx += 1
            else:
                samples.append([cx_val, cy_val])
                c_pt = [cx_val, cy_val]
                c_idx += 1
        return samples

    if is_custom_curve:
        samples = sample_path(curve_str)
    else:
        arch_h = (w * 0.4 * math.sin(math.radians(bend_val))) if abs(bend_val) <= 180 else (bend_val * 0.5)
        p0 = [min_x, cy]
        p1 = [min_x + w * 0.25, cy - arch_h * 1.3]
        p2 = [max_x - w * 0.25, cy - arch_h * 1.3]
        p3 = [max_x, cy]
        samples = []
        for step in range(0, 31):
            st = step / 30.0
            omt = 1.0 - st
            bx = omt**3 * p0[0] + 3 * omt**2 * st * p1[0] + 3 * omt * st**2 * p2[0] + st**3 * p3[0]
            by = omt**3 * p0[1] + 3 * omt**2 * st * p1[1] + 3 * omt * st**2 * p2[1] + st**3 * p3[1]
            samples.append([bx, by])

    if not samples or len(samples) < 2:
        return drawing

    cum_lens = [0.0]
    total_len = 0.0
    for si in range(1, len(samples)):
        total_len += math.hypot(samples[si][0] - samples[si-1][0], samples[si][1] - samples[si-1][1])
        cum_lens.append(total_len)

    def eval_curve(u):
        target = max(0.0, min(1.0, u)) * total_len
        si = 0
        while si < len(cum_lens) - 1 and cum_lens[si+1] < target:
            si += 1
        seg = cum_lens[si+1] - cum_lens[si]
        f = (target - cum_lens[si]) / seg if seg > 1e-6 else 0.0
        p_a = samples[si]
        p_b = samples[si+1]
        px = p_a[0] + (p_b[0] - p_a[0]) * f
        py = p_a[1] + (p_b[1] - p_a[1]) * f
        ang = math.atan2(p_b[1] - p_a[1], p_b[0] - p_a[0])
        return px, py, ang

    transformed_pts = []
    ti = 0
    axis_lower = str(axis or "x").strip().lower()
    while ti < len(subdivided):
        tok = subdivided[ti]
        try:
            x_val = float(tok)
            if ti + 1 < len(subdivided):
                try:
                    y_val = float(subdivided[ti + 1])
                    if axis_lower == "y":
                        u = (y_val - min_y) / h
                        v = x_val - cx
                        c_px, c_py, c_ang = eval_curve(u)
                        norm_ang = c_ang + math.pi / 2.0
                        fx = c_px + v * math.cos(norm_ang)
                        fy = c_py + v * math.sin(norm_ang)
                    else:
                        u = (x_val - min_x) / w
                        v = y_val - cy
                        c_px, c_py, c_ang = eval_curve(u)
                        norm_ang = c_ang + math.pi / 2.0
                        fx = c_px + v * math.cos(norm_ang)
                        fy = c_py + v * math.sin(norm_ang)

                    final_x = x_val * (1.0 - t_val) + fx * t_val
                    final_y = y_val * (1.0 - t_val) + fy * t_val
                    transformed_pts.append((final_x, final_y))
                    ti += 2
                    continue
                except ValueError:
                    pass
        except ValueError:
            pass
        ti += 1

    if not transformed_pts:
        return drawing

    all_tx = [p[0] for p in transformed_pts]
    all_ty = [p[1] for p in transformed_pts]
    n_min_x, n_max_x = min(all_tx), max(all_tx)
    n_min_y, n_max_y = min(all_ty), max(all_ty)
    n_cx = (n_min_x + n_max_x) / 2.0
    n_cy = (n_min_y + n_max_y) / 2.0

    if anchor_str == "origin":
        off_x, off_y = -n_min_x, -n_min_y
    elif anchor_str == "zero":
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = pos_x - n_cx, pos_y - n_cy
    elif anchor_str == "pos":
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = -pos_x, -pos_y
    else:  # "center" (default)
        off_x, off_y = -n_cx, -n_cy

    out_tokens = []
    ti = 0
    pt_idx = 0
    while ti < len(subdivided):
        tok = subdivided[ti]
        try:
            x_val = float(tok)
            if ti + 1 < len(subdivided):
                try:
                    y_val = float(subdivided[ti + 1])
                    pt = transformed_pts[pt_idx]
                    pt_idx += 1
                    nx = pt[0] + off_x
                    ny = pt[1] + off_y
                    if abs(nx) < 1e-9: nx = 0.0
                    if abs(ny) < 1e-9: ny = 0.0
                    fmt_x = int(nx) if nx.is_integer() else round(nx, 2)
                    fmt_y = int(ny) if ny.is_integer() else round(ny, 2)
                    out_tokens.append(str(fmt_x))
                    out_tokens.append(str(fmt_y))
                    ti += 2
                    continue
                except ValueError:
                    pass
            out_tokens.append(tok)
            ti += 1
        except ValueError:
            out_tokens.append(tok)
            ti += 1

    return " ".join(out_tokens) + " "


_SHAPE_DISTORT_CONTOUR_CACHE = {}

def _shape_distort(drawing, target_shape="", t=1.0, step_px=0.0, anchor="center", energy=0.35, context=None, **kwargs):
    """Deforma un dibujo vectorial ASS hacia el contorno morfológico de una forma objetivo (Morphing vectorial avanzado).
    - Si step_px == 0.0 (por defecto): Realiza morphing continuo analítico preservando curvas y líneas escasas nativas ('b' y 'm') de suavidad C1 sin sobre-densidad.
    - Si step_px >= 0.5: Normaliza ambas formas en polilíneas densas ('l') remuestreadas por longitud de arco cada ~step_px píxeles.
    - Soporte topológico y de frases: Agrupación en Islas Jerárquicas (Glyph Islands) con Mapeo Proporcional (Mitosis y Fusión).
    - Modulación Líquida (Propuesta 2): Durante 0 < t < 1, los manejadores Bézier modulan una onda elástica proporcional a `energy`, haciendo que incluso formas idénticas respiren y ondeen como líquido en lugar de quedarse estáticas.
    """
    if not drawing or not isinstance(drawing, str):
        return ""

    if not target_shape or not isinstance(target_shape, str) or not target_shape.strip():
        return drawing

    from node_engine import _eval_num_expr
    try:
        if isinstance(t, (int, float)):
            t_val = float(t)
        elif t is not None and str(t).strip() != "":
            t_val = float(_eval_num_expr(t, context, 1.0))
        else:
            t_val = 1.0
    except Exception:
        t_val = 1.0

    t_val = max(0.0, min(1.0, t_val))

    try:
        if isinstance(step_px, (int, float)):
            s_px = float(step_px)
        elif step_px is not None and str(step_px).strip() != "":
            s_px = float(_eval_num_expr(step_px, context, 0.0))
        else:
            s_px = 0.0
    except Exception:
        s_px = 0.0

    try:
        e_in = energy if energy is not None else kwargs.get("energy", kwargs.get("fluidez", kwargs.get("fluidity", 0.35)))
        if isinstance(e_in, (int, float)):
            energy_val = float(e_in)
        elif e_in is not None and str(e_in).strip() != "":
            energy_val = float(_eval_num_expr(e_in, context, 0.35))
        else:
            energy_val = 0.35
    except Exception:
        energy_val = 0.35

    energy_val = max(0.0, min(2.0, energy_val))

    anchor_str = str(anchor or "center").strip().lower()

    cache_key = (drawing, target_shape, s_px)
    cached_data = _SHAPE_DISTORT_CONTOUR_CACHE.get(cache_key)

    if cached_data is None:
        def parse_ass_sparse_beziers(draw_str):
            tokens = draw_str.strip().split()
            contours = []
            curr_cmds = []
            curr_cmd = 'm'
            i = 0
            last_pt = (0.0, 0.0)
            while i < len(tokens):
                tok = tokens[i]
                if tok.isalpha() and tok.lower() in ('m', 'l', 'b', 's', 'p', 'c'):
                    curr_cmd = tok.lower()
                    i += 1
                    if curr_cmd == 'm' and curr_cmds:
                        contours.append(curr_cmds)
                        curr_cmds = []
                    continue
                try:
                    if curr_cmd == 'm':
                        x, y = float(tok), float(tokens[i + 1])
                        last_pt = (x, y)
                        curr_cmds.append(('m', (x, y)))
                        i += 2
                        curr_cmd = 'l'
                    elif curr_cmd == 'l':
                        x, y = float(tok), float(tokens[i + 1])
                        p0, p3 = last_pt, (x, y)
                        p1 = (p0[0] + (p3[0] - p0[0]) / 3.0, p0[1] + (p3[1] - p0[1]) / 3.0)
                        p2 = (p0[0] + 2.0 * (p3[0] - p0[0]) / 3.0, p0[1] + 2.0 * (p3[1] - p0[1]) / 3.0)
                        curr_cmds.append(('b', p0, p1, p2, p3))
                        last_pt = p3
                        i += 2
                    elif curr_cmd == 'b':
                        x1, y1 = float(tokens[i]), float(tokens[i + 1])
                        x2, y2 = float(tokens[i + 2]), float(tokens[i + 3])
                        x3, y3 = float(tokens[i + 4]), float(tokens[i + 5])
                        p0 = last_pt
                        p1, p2, p3 = (x1, y1), (x2, y2), (x3, y3)
                        curr_cmds.append(('b', p0, p1, p2, p3))
                        last_pt = p3
                        i += 6
                    else:
                        i += 1
                except Exception:
                    i += 1
            if curr_cmds:
                contours.append(curr_cmds)
            return contours

        def get_bezier_stats(bez_list):
            pts = []
            for b in bez_list:
                if b[0] == 'm':
                    pts.append(b[1])
                elif b[0] == 'b':
                    p0, p1, p2, p3 = b[1], b[2], b[3], b[4]
                    for step in range(1, 9):
                        u = step / 8.0
                        u2 = u * u
                        u3 = u2 * u
                        inv = 1.0 - u
                        inv2 = inv * inv
                        inv3 = inv2 * inv
                        x = inv3 * p0[0] + 3.0 * inv2 * u * p1[0] + 3.0 * inv * u2 * p2[0] + u3 * p3[0]
                        y = inv3 * p0[1] + 3.0 * inv2 * u * p1[1] + 3.0 * inv * u2 * p2[1] + u3 * p3[1]
                        pts.append((x, y))
            N = len(pts)
            if N < 3:
                return 0.0, (0.0, 0.0), (0.0, 0.0, 0.0, 0.0)
            area = sum(pts[k][0] * pts[(k + 1) % N][1] - pts[(k + 1) % N][0] * pts[k][1] for k in range(N)) / 2.0
            min_x = min(p[0] for p in pts)
            max_x = max(p[0] for p in pts)
            min_y = min(p[1] for p in pts)
            max_y = max(p[1] for p in pts)
            cx = (min_x + max_x) / 2.0
            cy = (min_y + max_y) / 2.0
            return area, (cx, cy), (min_x, max_x, min_y, max_y)

        def ensure_bezier_winding(bez_list, should_be_cw):
            area, _, _ = get_bezier_stats(bez_list)
            is_cw = area > 0
            if is_cw != should_be_cw:
                beziers_only = [b for b in bez_list if b[0] == 'b']
                rev_b = []
                for b in reversed(beziers_only):
                    rev_b.append(('b', b[4], b[3], b[2], b[1]))
                start_pt = rev_b[0][1] if rev_b else (0.0, 0.0)
                return [('m', start_pt)] + rev_b
            return bez_list

        def bezier_len(p0, p1, p2, p3):
            chord = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
            poly = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) + math.hypot(p2[0] - p1[0], p2[1] - p1[1]) + math.hypot(p3[0] - p2[0], p3[1] - p2[1])
            return (chord + poly) / 2.0

        def split_bezier(p0, p1, p2, p3, u=0.5):
            p01 = (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)
            p12 = (p1[0] + (p2[0] - p1[0]) * u, p1[1] + (p2[1] - p1[1]) * u)
            p23 = (p2[0] + (p3[0] - p2[0]) * u, p2[1] + (p3[1] - p2[1]) * u)
            p012 = (p01[0] + (p12[0] - p01[0]) * u, p01[1] + (p12[1] - p01[1]) * u)
            p123 = (p12[0] + (p23[0] - p12[0]) * u, p12[1] + (p23[1] - p12[1]) * u)
            p0123 = (p012[0] + (p123[0] - p012[0]) * u, p012[1] + (p123[1] - p012[1]) * u)
            return ('b', p0, p01, p012, p0123), ('b', p0123, p123, p23, p3)

        def equalize_beziers(bez_cmds, target_count):
            res = [b for b in bez_cmds if b[0] == 'b']
            if not res:
                return []
            while len(res) < target_count:
                longest_idx = 0
                max_l = -1.0
                for idx, b in enumerate(res):
                    l = bezier_len(b[1], b[2], b[3], b[4])
                    if l > max_l:
                        max_l = l
                        longest_idx = idx
                b = res[longest_idx]
                b1, b2 = split_bezier(b[1], b[2], b[3], b[4], 0.5)
                res = res[:longest_idx] + [b1, b2] + res[longest_idx + 1:]
            return res

        def align_bezier_phase_fixed(bA, bB):
            M = len(bA)
            if M < 2:
                return bA, bB
            best_dist = float('inf')
            best_shift = 0
            step_coarse = max(1, M // 16)
            for shift in range(0, M, step_coarse):
                cand = bB[shift:] + bB[:shift]
                d = sum((bA[k][1][0] - cand[k][1][0])**2 + (bA[k][1][1] - cand[k][1][1])**2 for k in range(0, M, max(1, M // 8)))
                if d < best_dist:
                    best_dist = d
                    best_shift = shift

            fine_start = max(0, best_shift - step_coarse * 2)
            fine_end = min(M, best_shift + step_coarse * 2 + 1)
            best_dist = float('inf')
            best_B = bB
            for shift in range(fine_start, fine_end):
                cand = bB[shift:] + bB[:shift]
                d = sum((bA[k][1][0] - cand[k][1][0])**2 + (bA[k][1][1] - cand[k][1][1])**2 for k in range(M))
                if d < best_dist:
                    best_dist = d
                    best_B = cand
            return bA, best_B

        def group_bezier_islands(raw_beziers):
            data = []
            for b_list in raw_beziers:
                area, center, bbox = get_bezier_stats(b_list)
                data.append({'beziers': b_list, 'area': area, 'center': center, 'bbox': bbox})

            # Clasificación jerárquica por contención geométrica
            sorted_data = sorted(data, key=lambda c: abs(c['area']), reverse=True)
            outers = []
            holes = []
            for c in sorted_data:
                c_min_x, c_max_x, c_min_y, c_max_y = c['bbox']
                is_hole = False
                for parent in outers:
                    p_min_x, p_max_x, p_min_y, p_max_y = parent['bbox']
                    if p_min_x - 1.0 <= c_min_x and c_max_x <= p_max_x + 1.0 and p_min_y - 1.0 <= c_min_y and c_max_y <= p_max_y + 1.0:
                        is_hole = True
                        break
                if is_hole:
                    holes.append(c)
                else:
                    outers.append(c)

            outers.sort(key=lambda o: o['bbox'][0])

            islands = [{'outer': o, 'holes': []} for o in outers]
            for h in holes:
                h_cx, h_cy = h['center']
                best_isl = None
                for isl in islands:
                    o_min_x, o_max_x, o_min_y, o_max_y = isl['outer']['bbox']
                    if o_min_x - 3.0 <= h_cx <= o_max_x + 3.0 and o_min_y - 3.0 <= h_cy <= o_max_y + 3.0:
                        best_isl = isl
                        break
                if best_isl:
                    best_isl['holes'].append(h)
                elif islands:
                    islands[-1]['holes'].append(h)
            return islands

        def get_closest_point_on_outline(isl, target_center):
            best_pt = None
            best_d = float('inf')
            for b in isl['outer']['beziers']:
                if b[0] == 'm':
                    pt = b[1]
                    d = (pt[0] - target_center[0])**2 + (pt[1] - target_center[1])**2
                    if d < best_d:
                        best_d = d
                        best_pt = pt
                elif b[0] == 'b':
                    pt = b[4]
                    d = (pt[0] - target_center[0])**2 + (pt[1] - target_center[1])**2
                    if d < best_d:
                        best_d = d
                        best_pt = pt
            return best_pt if best_pt is not None else isl['outer']['center']

        raw_A = parse_ass_sparse_beziers(drawing)
        raw_B = parse_ass_sparse_beziers(target_shape)

        if not raw_A or not raw_B:
            return drawing

        all_pts_A = [p for cnt in raw_A for b in cnt if b[0] == 'b' for p in (b[1], b[4])]
        all_pts_B = [p for cnt in raw_B for b in cnt if b[0] == 'b' for p in (b[1], b[4])]
        if not all_pts_A or not all_pts_B:
            return drawing

        min_xA, max_xA = min(p[0] for p in all_pts_A), max(p[0] for p in all_pts_A)
        min_yA, max_yA = min(p[1] for p in all_pts_A), max(p[1] for p in all_pts_A)
        wA, hA = max(1.0, max_xA - min_xA), max(1.0, max_yA - min_yA)
        cxA, cyA = (min_xA + max_xA) / 2.0, (min_yA + max_yA) / 2.0

        min_xB, max_xB = min(p[0] for p in all_pts_B), max(p[0] for p in all_pts_B)
        min_yB, max_yB = min(p[1] for p in all_pts_B), max(p[1] for p in all_pts_B)
        wB, hB = max(1.0, max_xB - min_xB), max(1.0, max_yB - min_yB)
        cxB, cyB = (min_xB + max_xB) / 2.0, (min_yB + max_yB) / 2.0

        scale_x = wA / wB
        scale_y = hA / hB

        def transform_b_list(b_list):
            res = []
            for b in b_list:
                if b[0] == 'm':
                    px = cxA + (b[1][0] - cxB) * scale_x
                    py = cyA + (b[1][1] - cyB) * scale_y
                    res.append(('m', (px, py)))
                elif b[0] == 'b':
                    p0 = (cxA + (b[1][0] - cxB) * scale_x, cyA + (b[1][1] - cyB) * scale_y)
                    p1 = (cxA + (b[2][0] - cxB) * scale_x, cyA + (b[2][1] - cyB) * scale_y)
                    p2 = (cxA + (b[3][0] - cxB) * scale_x, cyA + (b[3][1] - cyB) * scale_y)
                    p3 = (cxA + (b[4][0] - cxB) * scale_x, cyA + (b[4][1] - cyB) * scale_y)
                    res.append(('b', p0, p1, p2, p3))
            return res

        scaled_raw_B = [transform_b_list(b_list) for b_list in raw_B]

        islands_A = group_bezier_islands(raw_A)
        islands_B = group_bezier_islands(scaled_raw_B)

        NA = len(islands_A)
        NB = len(islands_B)

        if NA == 0 or NB == 0:
            return drawing

        # Mapeo Proporcional: Mitosis (1-a-N) cuando NA <= NB, Fusión (N-a-1) cuando NA > NB
        island_pairs_idx = []
        if NA <= NB:
            for j in range(NB):
                u_j = j / float(NB - 1) if NB > 1 else 0.0
                i = min(NA - 1, max(0, int(round(u_j * (NA - 1)))))
                island_pairs_idx.append((i, j))
        else:
            for i in range(NA):
                u_i = i / float(NA - 1) if NA > 1 else 0.0
                j = min(NB - 1, max(0, int(round(u_i * (NB - 1)))))
                island_pairs_idx.append((i, j))

        # Permutación Cruzada Topológica (Cross-Morphing) para formas o palabras idénticas
        is_identical = []
        for i_A, j_B in island_pairs_idx:
            isl_A = islands_A[i_A]
            isl_B = islands_B[j_B]
            cx_A, cy_A = isl_A['outer']['center']
            cx_B, cy_B = isl_B['outer']['center']
            dist = ((cx_A - cx_B)**2 + (cy_A - cy_B)**2)**0.5
            is_identical.append(dist < 18.0)

        clusters = []
        curr_cl = []
        for idx, ident in enumerate(is_identical):
            if ident:
                curr_cl.append(idx)
            else:
                if curr_cl:
                    clusters.append(curr_cl)
                    curr_cl = []
        if curr_cl:
            clusters.append(curr_cl)

        for cl in clusters:
            cl_len = len(cl)
            if cl_len == 2:
                # Intercambio directo entre los 2 vecinos adyacentes (distancia = 1 letra)
                idx0, idx1 = cl[0], cl[1]
                t0 = island_pairs_idx[idx0][1]
                t1 = island_pairs_idx[idx1][1]
                island_pairs_idx[idx0] = (island_pairs_idx[idx0][0], t1)
                island_pairs_idx[idx1] = (island_pairs_idx[idx1][0], t0)
            elif cl_len > 2:
                # Intercambio local por parejas y tríadas adyacentes (máxima distancia <= 1 o 2 letras)
                # Evita que la última letra cruce toda la palabra hacia el otro extremo
                targets = [island_pairs_idx[idx][1] for idx in cl]
                new_targets = list(targets)
                i = 0
                while i < cl_len:
                    rem = cl_len - i
                    if rem >= 4 or rem == 2:
                        new_targets[i] = targets[i + 1]
                        new_targets[i + 1] = targets[i]
                        i += 2
                    elif rem == 3:
                        new_targets[i] = targets[i + 1]
                        new_targets[i + 1] = targets[i + 2]
                        new_targets[i + 2] = targets[i]
                        i += 3
                    else: # rem == 1
                        new_targets[i - 1] = targets[i]
                        new_targets[i] = targets[i - 1]
                        i += 1
                for c_i, t_i in zip(cl, new_targets):
                    island_pairs_idx[c_i] = (island_pairs_idx[c_i][0], t_i)
            elif cl_len == 1 and len(island_pairs_idx) > 1:
                # Letra idéntica aislada: intercambiar destino con la letra vecina inmediata
                c_idx = cl[0]
                swap_idx = c_idx + 1 if (c_idx + 1 < len(island_pairs_idx)) else (c_idx - 1)
                t_curr = island_pairs_idx[c_idx][1]
                t_swap = island_pairs_idx[swap_idx][1]
                island_pairs_idx[c_idx] = (island_pairs_idx[c_idx][0], t_swap)
                island_pairs_idx[swap_idx] = (island_pairs_idx[swap_idx][0], t_curr)

        pairs = []
        for i_A, j_B in island_pairs_idx:
            isl_A = islands_A[i_A]
            isl_B = islands_B[j_B]

            oA_b = ensure_bezier_winding(isl_A['outer']['beziers'], should_be_cw=True)
            oB_b = ensure_bezier_winding(isl_B['outer']['beziers'], should_be_cw=True)
            M_o = max(len([b for b in oA_b if b[0] == 'b']), len([b for b in oB_b if b[0] == 'b']))
            eq_oA = equalize_beziers(oA_b, M_o)
            eq_oB = equalize_beziers(oB_b, M_o)
            eq_oA, eq_oB = align_bezier_phase_fixed(eq_oA, eq_oB)
            pairs.append(('normal', True, eq_oA, eq_oB))

            holes_A = isl_A['holes']
            holes_B = isl_B['holes']
            num_h = max(len(holes_A), len(holes_B))
            for h_idx in range(num_h):
                if h_idx < len(holes_A) and h_idx < len(holes_B):
                    hA_b = ensure_bezier_winding(holes_A[h_idx]['beziers'], should_be_cw=False)
                    hB_b = ensure_bezier_winding(holes_B[h_idx]['beziers'], should_be_cw=False)
                    M_h = max(len([b for b in hA_b if b[0] == 'b']), len([b for b in hB_b if b[0] == 'b']))
                    eq_hA = equalize_beziers(hA_b, M_h)
                    eq_hB = equalize_beziers(hB_b, M_h)
                    eq_hA, eq_hB = align_bezier_phase_fixed(eq_hA, eq_hB)
                    pairs.append(('normal', False, eq_hA, eq_hB))
                elif h_idx < len(holes_A):
                    # Hueco que desaparece: se contrae hacia el cuerpo sólido de la letra destino
                    hA_b = ensure_bezier_winding(holes_A[h_idx]['beziers'], should_be_cw=False)
                    cx_hA, cy_hA = holes_A[h_idx]['center']
                    dest_pt = get_closest_point_on_outline(isl_B, (cx_hA, cy_hA))
                    eq_hA = [b for b in hA_b if b[0] == 'b']
                    coll_B = [('b', dest_pt, dest_pt, dest_pt, dest_pt) for _ in range(len(eq_hA))]
                    pairs.append(('collapsing_hole', False, eq_hA, coll_B))
                else:
                    # Hueco que emerge: nace desde el cuerpo sólido de la letra origen (oculto bajo el relleno)
                    hB_b = ensure_bezier_winding(holes_B[h_idx]['beziers'], should_be_cw=False)
                    cx_hB, cy_hB = holes_B[h_idx]['center']
                    origin_pt = get_closest_point_on_outline(isl_A, (cx_hB, cy_hB))
                    eq_hB = [b for b in hB_b if b[0] == 'b']
                    coll_A = [('b', origin_pt, origin_pt, origin_pt, origin_pt) for _ in range(len(eq_hB))]
                    pairs.append(('emerging_hole', False, coll_A, eq_hB))

        cached_data = {
            'pairs': pairs,
            's_px': s_px,
            'bbox_A': (cxA, cyA, wA, hA),
            'bbox_B': (cxB, cyB, wB, hB)
        }
        if len(_SHAPE_DISTORT_CONTOUR_CACHE) > 512:
            _SHAPE_DISTORT_CONTOUR_CACHE.clear()
        _SHAPE_DISTORT_CONTOUR_CACHE[cache_key] = cached_data

    # Interpolación dinámica de la caja delimitadora (Bounding Box)
    bbox_A = cached_data.get('bbox_A')
    bbox_B = cached_data.get('bbox_B')
    if bbox_A and bbox_B:
        cxA_c, cyA_c, wA_c, hA_c = bbox_A
        cxB_c, cyB_c, wB_c, hB_c = bbox_B
        cur_w = wA_c * (1.0 - t_val) + wB_c * t_val
        cur_h = hA_c * (1.0 - t_val) + hB_c * t_val
        cur_cx = cxA_c * (1.0 - t_val) + cxB_c * t_val
        cur_cy = cyA_c * (1.0 - t_val) + cyB_c * t_val
        scale_t_x = (cur_w / wA_c) if wA_c > 0.001 else 1.0
        scale_t_y = (cur_h / hA_c) if hA_c > 0.001 else 1.0

        def to_dyn_bbox(pt):
            return (cur_cx + (pt[0] - cxA_c) * scale_t_x, cur_cy + (pt[1] - cyA_c) * scale_t_y)
    else:
        def to_dyn_bbox(pt):
            return pt

    # Interpolate segments at t_val
    all_eval_pts = []
    active_pairs = []
    for pair_type, is_outer, bA, bB in cached_data['pairs']:
        if 'collapsing' in pair_type and t_val >= 0.999:
            continue
        if 'emerging' in pair_type and t_val <= 0.001:
            continue
        M = min(len(bA), len(bB))
        if M == 0:
            continue
        p0_A = bA[0][1]
        p0_B = bB[0][1]
        p0_x = p0_A[0] * (1.0 - t_val) + p0_B[0] * t_val
        p0_y = p0_A[1] * (1.0 - t_val) + p0_B[1] * t_val
        p0_mapped = to_dyn_bbox((p0_x, p0_y))
        segs = []
        all_eval_pts.append(p0_mapped)
        for k in range(M):
            segA, segB = bA[k], bB[k]
            p1_x = segA[2][0] * (1.0 - t_val) + segB[2][0] * t_val
            p1_y = segA[2][1] * (1.0 - t_val) + segB[2][1] * t_val
            p2_x = segA[3][0] * (1.0 - t_val) + segB[3][0] * t_val
            p2_y = segA[3][1] * (1.0 - t_val) + segB[3][1] * t_val
            p3_x = segA[4][0] * (1.0 - t_val) + segB[4][0] * t_val
            p3_y = segA[4][1] * (1.0 - t_val) + segB[4][1] * t_val

            p1_m = to_dyn_bbox((p1_x, p1_y))
            p2_m = to_dyn_bbox((p2_x, p2_y))
            p3_m = to_dyn_bbox((p3_x, p3_y))

            segs.append(('b', p0_mapped, p1_m, p2_m, p3_m))
            p0_mapped = p3_m
            all_eval_pts.extend([p1_m, p2_m, p3_m])
        active_pairs.append(segs)

    if not all_eval_pts:
        return drawing

    n_min_x, n_max_x = min(p[0] for p in all_eval_pts), max(p[0] for p in all_eval_pts)
    n_min_y, n_max_y = min(p[1] for p in all_eval_pts), max(p[1] for p in all_eval_pts)
    n_cx = (n_min_x + n_max_x) / 2.0
    n_cy = (n_min_y + n_max_y) / 2.0

    if anchor_str == 'origin':
        off_x, off_y = -n_min_x, -n_min_y
    elif anchor_str == 'zero':
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = pos_x - n_cx, pos_y - n_cy
    elif anchor_str == 'pos':
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = -pos_x, -pos_y
    else:
        off_x, off_y = -n_cx, -n_cy

    def fmt_num(v):
        return int(v) if isinstance(v, (int, float)) and float(v).is_integer() else round(float(v), 2)

    out_parts = []
    if s_px >= 0.5:
        # Polyline mode ('l')
        for segs in active_pairs:
            if not segs:
                continue
            p0 = segs[0][1]
            out_parts.append(f'm {fmt_num(p0[0] + off_x)} {fmt_num(p0[1] + off_y)}')
            for seg in segs:
                p0, p1, p2, p3 = seg[1], seg[2], seg[3], seg[4]
                chord = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
                poly = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) + math.hypot(p2[0] - p1[0], p2[1] - p1[1]) + math.hypot(p3[0] - p2[0], p3[1] - p2[1])
                approx_l = (chord + poly) / 2.0
                steps = max(2, int(math.ceil(approx_l / s_px)))
                for s in range(1, steps + 1):
                    u = s / float(steps)
                    um = 1.0 - u
                    bx = um**3 * p0[0] + 3 * um**2 * u * p1[0] + 3 * um * u**2 * p2[0] + u**3 * p3[0]
                    by = um**3 * p0[1] + 3 * um**2 * u * p1[1] + 3 * um * u**2 * p2[1] + u**3 * p3[1]
                    out_parts.append(f'l {fmt_num(bx + off_x)} {fmt_num(by + off_y)}')
    else:
        # Sparse Bezier Mode ('b')
        for segs in active_pairs:
            if not segs:
                continue
            p0 = segs[0][1]
            out_parts.append(f'm {fmt_num(p0[0] + off_x)} {fmt_num(p0[1] + off_y)}')
            for seg in segs:
                _, p0, p1, p2, p3 = seg
                out_parts.append(f'b {fmt_num(p1[0] + off_x)} {fmt_num(p1[1] + off_y)} {fmt_num(p2[0] + off_x)} {fmt_num(p2[1] + off_y)} {fmt_num(p3[0] + off_x)} {fmt_num(p3[1] + off_y)}')

    return ' '.join(out_parts) + ' '




def shape_transform(context, drawing="", mode="Inflate", t=None, ratio=1.0, inflate_mode="Circle", anchor="center", angle_x=0.0, angle_y=0.0, radius=10.0, corner_mode="Round", curve=None, bend_t=1.0, axis="x", target_shape="", step_px=0.0, **kwargs):
    """Aplica transformaciones geométricas avanzadas no nativas de ASS a un dibujo vectorial ASS o texto.
    Modos:
      - 'Inflate': Deformación morfológica radial (esferificación/abombamiento) hacia círculo o elipse.
      - 'Skew': Cizallamiento o inclinación planar 2D en X e Y.
      - 'Round Corners': Redondeo (arcos Bézier) o biselado (chaflán) de esquinas poliédricas.
      - 'Flexor': Curvado y deformación a lo largo de una spline directriz o arco paramétrico.
      - 'Distort': Deformación polar hacia el contorno de una forma objetivo (morphing).
    """
    raw_shp = resolve_shape_value(drawing, context)
    if not raw_shp:
        unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
        line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
        raw_shp = getattr(unit, 'text_stripped', getattr(unit, 'text', '')) or getattr(line, 'text_stripped', getattr(line, 'text', ''))

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

    mode_clean = str(mode or "Inflate").strip().lower()
    if "inflate" in mode_clean or "inflar" in mode_clean:
        t_inf = t if (t is not None and str(t).strip() != "") else kwargs.get("t", 0.5)
        return _shape_inflate(raw_shp, t=t_inf, ratio=ratio, mode=inflate_mode, anchor=anchor, context=context)
    elif "skew" in mode_clean or "cizall" in mode_clean or "inclin" in mode_clean or "oblique" in mode_clean:
        ax = angle_x if (angle_x is not None and str(angle_x).strip() != "") else (kwargs.get("angle_x", kwargs.get("angle", kwargs.get("ang_x", kwargs.get("skew_x", 0.0)))))
        ay = angle_y if (angle_y is not None and str(angle_y).strip() != "") else (kwargs.get("angle_y", kwargs.get("ang_y", kwargs.get("skew_y", 0.0))))
        return _shape_skew(raw_shp, angle_x=ax, angle_y=ay, anchor=anchor, context=context, **kwargs)
    elif "round" in mode_clean or "redond" in mode_clean or "corner" in mode_clean or "esquina" in mode_clean:
        r_val = radius if radius != 10.0 else kwargs.get("radius", 10.0)
        c_mode = corner_mode if corner_mode else kwargs.get("corner_mode", "Round")
        return _shape_round_corners(raw_shp, radius=r_val, mode=c_mode, anchor=anchor, context=context)
    elif "flex" in mode_clean or "curv" in mode_clean or "bend" in mode_clean:
        c_curve = curve if curve is not None else kwargs.get("curve", "30")
        b_t = bend_t if bend_t != 1.0 else kwargs.get("bend_t", kwargs.get("t", 1.0))
        b_bend = kwargs.get("bend", 30.0)
        try:
            if isinstance(c_curve, (int, float)) or (isinstance(c_curve, str) and not c_curve.strip().lower().startswith("m")):
                b_bend = float(c_curve)
        except:
            pass
        ax = axis if axis else kwargs.get("axis", "x")
        return _shape_flexor(raw_shp, curve=c_curve, t=b_t, bend=b_bend, axis=ax, anchor=anchor, context=context)
    elif "distort" in mode_clean or "deform" in mode_clean or "morph" in mode_clean:
        tgt = target_shape if target_shape else kwargs.get("target_shape", "")
        tgt = resolve_shape_value(tgt, context)
        if tgt and not tgt.lower().startswith("m ") and not tgt.lower().startswith("m-") and not tgt.lower().startswith("m0"):
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
            v_tgt = FontVectorEngine.text_to_shape(tgt, font_name=fn, font_size=fs, bold=b_val, italic=i_val)
            if v_tgt and v_tgt.strip():
                tgt = v_tgt
        t_morph = t if (t is not None and str(t).strip() != "") else kwargs.pop("t", 1.0)
        s_px = step_px if (step_px is not None and str(step_px).strip() != "") else kwargs.pop("step_px", kwargs.pop("step", 0.0))
        e_val = kwargs.pop("energy", kwargs.pop("fluidez", kwargs.pop("fluidity", 0.35)))
        return _shape_distort(raw_shp, target_shape=tgt, t=t_morph, step_px=s_px, anchor=anchor, energy=e_val, context=context, **kwargs)

    return raw_shp

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
NODE_REGISTRY["Shape/Shape Manipulator"] = shape_manipulator
NODE_REGISTRY["Shape Manipulator"] = shape_manipulator
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
    """Resuelve cualquier referencia a forma vectorial, incluyendo sintaxis 'shape.nombre' o nombres directos de la librería."""
    if not shp_val:
        return ""
    s_val = str(shp_val).strip()
    shape_name = s_val[6:].strip() if s_val.lower().startswith("shape.") else s_val
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
    if s_val.lower().startswith("shape."):
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


# -----------------------------------------------------------------------------
# CORTE PARAMÉTRICO POR LONGITUD DE ARCO (Shape Cut / Write-on / Trim Paths)
# -----------------------------------------------------------------------------

def parse_assdraw_segments(shape_str):
    """Parsea comandos ASSdraw (m, l, b, c) en una lista de contornos con segmentos estructurados."""
    if not shape_str or not str(shape_str).strip():
        return []

    tokens = str(shape_str).strip().split()
    contours = []
    current_segments = []
    current_start = None
    current_pt = None
    current_cmd = None
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]
        tok_lower = tok.lower()

        if tok_lower in ('m', 'l', 'b', 'c'):
            current_cmd = tok_lower
            i += 1
            if current_cmd == 'c':
                if current_start and current_pt:
                    dx = current_start[0] - current_pt[0]
                    dy = current_start[1] - current_pt[1]
                    if math.hypot(dx, dy) > 0.001:
                        current_segments.append({
                            'type': 'l',
                            'p0': current_pt,
                            'p1': current_start
                        })
                        current_pt = current_start
                continue

        if current_cmd == 'm':
            if i + 1 < n:
                try:
                    x, y = float(tokens[i]), float(tokens[i + 1])
                    if current_segments and current_start:
                        contours.append({
                            'start': current_start,
                            'segments': current_segments
                        })
                    current_start = (x, y)
                    current_pt = (x, y)
                    current_segments = []
                    current_cmd = 'l'  # Repetición implícita de coordenadas tras 'm' se convierte en 'l'
                    i += 2
                except ValueError:
                    i += 1
            else:
                i += 1

        elif current_cmd == 'l':
            if i + 1 < n:
                try:
                    x, y = float(tokens[i]), float(tokens[i + 1])
                    if current_pt is None:
                        current_start = (x, y)
                        current_pt = (x, y)
                    else:
                        p1 = (x, y)
                        current_segments.append({
                            'type': 'l',
                            'p0': current_pt,
                            'p1': p1
                        })
                        current_pt = p1
                    i += 2
                except ValueError:
                    i += 1
            else:
                i += 1

        elif current_cmd == 'b':
            if i + 5 < n:
                try:
                    x1, y1 = float(tokens[i]), float(tokens[i + 1])
                    x2, y2 = float(tokens[i + 2]), float(tokens[i + 3])
                    x3, y3 = float(tokens[i + 4]), float(tokens[i + 5])
                    if current_pt is None:
                        current_start = (x1, y1)
                        current_pt = (x1, y1)
                    p0 = current_pt
                    current_segments.append({
                        'type': 'b',
                        'p0': p0,
                        'p1': (x1, y1),
                        'p2': (x2, y2),
                        'p3': (x3, y3)
                    })
                    current_pt = (x3, y3)
                    i += 6
                except ValueError:
                    i += 1
            else:
                i += 1
        else:
            i += 1

    if current_segments and current_start:
        contours.append({
            'start': current_start,
            'segments': current_segments
        })

    return contours


def _eval_bezier_pt(p0, p1, p2, p3, u):
    """Evalúa un punto en una curva Bézier cúbica para el parámetro u in [0, 1]."""
    om = 1.0 - u
    om2 = om * om
    om3 = om2 * om
    u2 = u * u
    u3 = u2 * u
    x = om3 * p0[0] + 3.0 * om2 * u * p1[0] + 3.0 * om * u2 * p2[0] + u3 * p3[0]
    y = om3 * p0[1] + 3.0 * om2 * u * p1[1] + 3.0 * om * u2 * p2[1] + u3 * p3[1]
    return (x, y)


def _eval_bezier_tangent(p0, p1, p2, p3, u):
    """Evalúa el vector tangente (dx, dy) de una curva Bézier cúbica en u."""
    om = 1.0 - u
    om2 = om * om
    u2 = u * u
    dx = 3.0 * om2 * (p1[0] - p0[0]) + 6.0 * om * u * (p2[0] - p1[0]) + 3.0 * u2 * (p3[0] - p2[0])
    dy = 3.0 * om2 * (p1[1] - p0[1]) + 6.0 * om * u * (p2[1] - p1[1]) + 3.0 * u2 * (p3[1] - p2[1])
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        dx = p3[0] - p0[0]
        dy = p3[1] - p0[1]
    return (dx, dy)


def _segment_arc_length(seg, subdivs=30):
    """Calcula la longitud de arco real de un segmento (línea o Bézier cúbica)."""
    stype = seg['type']
    if stype == 'l':
        p0, p1 = seg['p0'], seg['p1']
        length = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        return length, [0.0, length], [p0, p1]
    elif stype == 'b':
        p0, p1, p2, p3 = seg['p0'], seg['p1'], seg['p2'], seg['p3']
        sub = max(5, int(subdivs))
        chord_lens = [0.0]
        chord_pts = [p0]
        accum = 0.0
        prev_p = p0
        for step in range(1, sub + 1):
            u = step / float(sub)
            cur_p = _eval_bezier_pt(p0, p1, p2, p3, u)
            accum += math.hypot(cur_p[0] - prev_p[0], cur_p[1] - prev_p[1])
            chord_lens.append(accum)
            chord_pts.append(cur_p)
            prev_p = cur_p
        return accum, chord_lens, chord_pts
    return 0.0, [0.0], [seg.get('p0', (0.0, 0.0))]


def _map_dist_to_bezier_u(dist, chord_lens, sub):
    """Mapea una distancia acumulada a un parámetro analítico u in [0, 1] en una curva Bézier."""
    tot = chord_lens[-1]
    if tot <= 1e-9 or dist <= 0.0:
        return 0.0
    if dist >= tot:
        return 1.0

    # Búsqueda de intervalo en la tabla de cuerdas
    for i in range(len(chord_lens) - 1):
        d0 = chord_lens[i]
        d1 = chord_lens[i + 1]
        if d0 <= dist <= d1:
            seg_len = d1 - d0
            fraction = (dist - d0) / seg_len if seg_len > 1e-9 else 0.0
            u0 = i / float(sub)
            u1 = (i + 1) / float(sub)
            return u0 + fraction * (u1 - u0)
    return 1.0


def de_casteljau_split(seg, u):
    """Subdivide un segmento en u in [0, 1] usando de Casteljau.
    Retorna: (seg_izq, seg_der, punto_corte, tangente_dx_dy).
    """
    u = max(0.0, min(1.0, float(u)))
    stype = seg['type']

    if stype == 'l':
        p0, p1 = seg['p0'], seg['p1']
        x = p0[0] + u * (p1[0] - p0[0])
        y = p0[1] + u * (p1[1] - p0[1])
        split_p = (x, y)
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        left_seg = {'type': 'l', 'p0': p0, 'p1': split_p}
        right_seg = {'type': 'l', 'p0': split_p, 'p1': p1}
        return left_seg, right_seg, split_p, (dx, dy)

    elif stype == 'b':
        p0, p1, p2, p3 = seg['p0'], seg['p1'], seg['p2'], seg['p3']
        # Nivel 1
        b01 = (p0[0] * (1.0 - u) + p1[0] * u, p0[1] * (1.0 - u) + p1[1] * u)
        b12 = (p1[0] * (1.0 - u) + p2[0] * u, p1[1] * (1.0 - u) + p2[1] * u)
        b23 = (p2[0] * (1.0 - u) + p3[0] * u, p2[1] * (1.0 - u) + p3[1] * u)
        # Nivel 2
        b012 = (b01[0] * (1.0 - u) + b12[0] * u, b01[1] * (1.0 - u) + b12[1] * u)
        b123 = (b12[0] * (1.0 - u) + b23[0] * u, b12[1] * (1.0 - u) + b23[1] * u)
        # Nivel 3 (punto en la curva)
        b0123 = (b012[0] * (1.0 - u) + b123[0] * u, b012[1] * (1.0 - u) + b123[1] * u)

        dx, dy = _eval_bezier_tangent(p0, p1, p2, p3, u)
        left_seg = {'type': 'b', 'p0': p0, 'p1': b01, 'p2': b012, 'p3': b0123}
        right_seg = {'type': 'b', 'p0': b0123, 'p1': b123, 'p2': b23, 'p3': p3}
        return left_seg, right_seg, b0123, (dx, dy)

    p0 = seg.get('p0', (0.0, 0.0))
    return seg, seg, p0, (1.0, 0.0)


def _cut_segment_interval(seg, u_start, u_end, subdivs=30):
    """Recorta un segmento manteniendo únicamente la sección [u_start, u_end]."""
    u_start = max(0.0, min(1.0, float(u_start)))
    u_end = max(0.0, min(1.0, float(u_end)))

    if u_start >= u_end:
        p0 = seg.get('p0', (0.0, 0.0))
        return None, p0, (1.0, 0.0)

    cur_seg = seg
    tip_p = cur_seg.get('p1' if cur_seg['type'] == 'l' else 'p3', (0.0, 0.0))
    tan = (1.0, 0.0)

    # 1. Cortar extremo superior u_end
    if u_end < 0.999999:
        left_s, _, tip_p, tan = de_casteljau_split(cur_seg, u_end)
        cur_seg = left_s
    else:
        _, _, tip_p, tan = de_casteljau_split(cur_seg, 1.0)

    # 2. Cortar extremo inferior u_start
    if u_start > 0.000001:
        u_eff = u_start / u_end if u_end > 1e-9 else 0.0
        _, right_s, _, _ = de_casteljau_split(cur_seg, u_eff)
        cur_seg = right_s

    return cur_seg, tip_p, tan


def _format_num(val):
    """Formatea números flotantes de manera compacta para ASSdraw."""
    f = float(val)
    if f.is_integer():
        return str(int(f))
    return f"{f:.2f}".rstrip('0').rstrip('.')


# -----------------------------------------------------------------------------
# SHAPE WALKER / RECORREDOR (Corte Paramétrico por Longitud de Arco / Trim Paths)
# -----------------------------------------------------------------------------

def parse_assdraw_segments(shape_str):
    """Parsea comandos ASSdraw (m, l, b, c) en una lista de contornos con segmentos estructurados."""
    if not shape_str or not str(shape_str).strip():
        return []

    tokens = str(shape_str).strip().split()
    contours = []
    current_contour = None
    curr_pt = [0.0, 0.0]
    idx = 0
    num_tokens = len(tokens)

    while idx < num_tokens:
        cmd = tokens[idx].lower()
        if cmd == 'm':
            if idx + 2 < num_tokens:
                try:
                    px = float(tokens[idx + 1])
                    py = float(tokens[idx + 2])
                    curr_pt = [px, py]
                    current_contour = {
                        'start': (px, py),
                        'segments': []
                    }
                    contours.append(current_contour)
                    idx += 3
                except ValueError:
                    idx += 1
            else:
                idx += 1
        elif cmd == 'l':
            idx += 1
            while idx + 1 < num_tokens and not tokens[idx].isalpha():
                try:
                    px = float(tokens[idx])
                    py = float(tokens[idx + 1])
                    if current_contour is None:
                        current_contour = {'start': (curr_pt[0], curr_pt[1]), 'segments': []}
                        contours.append(current_contour)
                    current_contour['segments'].append({
                        'type': 'l',
                        'p0': (curr_pt[0], curr_pt[1]),
                        'p1': (px, py)
                    })
                    curr_pt = [px, py]
                    idx += 2
                except ValueError:
                    break
        elif cmd in ('b', 'c'):
            idx += 1
            while idx + 5 < num_tokens and not tokens[idx].isalpha():
                try:
                    p1 = (float(tokens[idx]), float(tokens[idx + 1]))
                    p2 = (float(tokens[idx + 2]), float(tokens[idx + 3]))
                    p3 = (float(tokens[idx + 4]), float(tokens[idx + 5]))
                    if current_contour is None:
                        current_contour = {'start': (curr_pt[0], curr_pt[1]), 'segments': []}
                        contours.append(current_contour)
                    current_contour['segments'].append({
                        'type': 'b',
                        'p0': (curr_pt[0], curr_pt[1]),
                        'p1': p1,
                        'p2': p2,
                        'p3': p3
                    })
                    curr_pt = [p3[0], p3[1]]
                    idx += 6
                except ValueError:
                    break
        else:
            idx += 1

    return contours


def shape_walker_core(shape_str, progress=1.0, start_t=0.0, mode="Global", invert=False, subdivs=30):
    """Núcleo de recorrido paramétrico vectorial por longitud de arco para ASSdraw.
    
    Parámetros:
      - shape_str: Código vectorial ASSdraw (m ...).
      - progress: Progreso de finalización (0.0 a 1.0).
      - start_t: Progreso de inicio (0.0 a 1.0).
      - mode: 'Global' (Continuo en todos los contornos) o 'Por Contorno' (Paralelo por glifo/trazo).
      - invert: Invierte el sentido del recorte.
      - subdivs: Pasos de resolución para integración Bézier.
    
    Retorna: (ass_draw_out, tip_x, tip_y, angle_deg, current_length, total_length)
    """
    contours = parse_assdraw_segments(shape_str)
    if not contours:
        return "", 0.0, 0.0, 0.0, 0.0, 0.0

    sub = max(5, int(subdivs))

    # Pre-calcular longitudes de cada contorno y de cada segmento
    contour_data = []
    total_shape_len = 0.0

    for c in contours:
        c_len = 0.0
        seg_info = []
        for s in c['segments']:
            s_len, chord_lens, chord_pts = _segment_arc_length(s, subdivs=sub)
            seg_info.append({
                'seg': s,
                'len': s_len,
                'chord_lens': chord_lens,
                'chord_pts': chord_pts,
                'start_dist': c_len,
                'end_dist': c_len + s_len
            })
            c_len += s_len
        contour_data.append({
            'start_pt': c['start'],
            'total_len': c_len,
            'segments': seg_info
        })
        total_shape_len += c_len

    if total_shape_len <= 1e-9:
        p0 = contours[0]['start']
        return f"m {_format_num(p0[0])} {_format_num(p0[1])} ", p0[0], p0[1], 0.0, 0.0, 0.0

    # Normalizar rangos [t0, t1]
    t0 = max(0.0, min(1.0, float(start_t)))
    t1 = max(0.0, min(1.0, float(progress)))

    if invert:
        # Invertir progreso: el trazado comienza desde el final
        t0_eff = 1.0 - t1
        t1_eff = 1.0 - t0
        t0, t1 = t0_eff, t1_eff

    if t0 >= t1:
        return "", 0.0, 0.0, 0.0, 0.0, total_shape_len

    mode_str = str(mode).strip().lower()
    is_per_contour = "contorno" in mode_str or "paralel" in mode_str or "glyph" in mode_str or "letter" in mode_str

    out_tokens = []
    tip_pt = (0.0, 0.0)
    tip_tangent = (1.0, 0.0)
    current_cut_len = 0.0

    if not is_per_contour:
        # MODO GLOBAL (Continuo)
        target_d0 = t0 * total_shape_len
        target_d1 = t1 * total_shape_len
        global_accum = 0.0

        for c_idx, c_obj in enumerate(contour_data):
            c_start_d = global_accum
            c_end_d = global_accum + c_obj['total_len']
            global_accum = c_end_d

            if c_end_d <= target_d0 or c_start_d >= target_d1 or c_obj['total_len'] <= 1e-9:
                continue

            local_d0 = max(0.0, target_d0 - c_start_d)
            local_d1 = min(c_obj['total_len'], target_d1 - c_start_d)

            first_pt_written = False
            for s_info in c_obj['segments']:
                s_d0 = s_info['start_dist']
                s_d1 = s_info['end_dist']
                s_len = s_info['len']

                if s_d1 <= local_d0 or s_d0 >= local_d1 or s_len <= 1e-9:
                    continue

                in_s_d0 = max(0.0, local_d0 - s_d0)
                in_s_d1 = min(s_len, local_d1 - s_d0)

                if s_info['seg']['type'] == 'l':
                    u_s = in_s_d0 / s_len if s_len > 1e-9 else 0.0
                    u_e = in_s_d1 / s_len if s_len > 1e-9 else 1.0
                else:
                    u_s = _map_dist_to_bezier_u(in_s_d0, s_info['chord_lens'], sub)
                    u_e = _map_dist_to_bezier_u(in_s_d1, s_info['chord_lens'], sub)

                cut_s, s_tip, s_tan = _cut_segment_interval(s_info['seg'], u_s, u_e, subdivs=sub)
                if cut_s:
                    tip_pt = s_tip
                    tip_tangent = s_tan
                    current_cut_len += (in_s_d1 - in_s_d0)

                    if not first_pt_written:
                        p_start = cut_s['p0']
                        out_tokens.append(f"m {_format_num(p_start[0])} {_format_num(p_start[1])}")
                        first_pt_written = True

                    if cut_s['type'] == 'l':
                        p1 = cut_s['p1']
                        out_tokens.append(f"l {_format_num(p1[0])} {_format_num(p1[1])}")
                    elif cut_s['type'] == 'b':
                        p1, p2, p3 = cut_s['p1'], cut_s['p2'], cut_s['p3']
                        out_tokens.append(f"b {_format_num(p1[0])} {_format_num(p1[1])} {_format_num(p2[0])} {_format_num(p2[1])} {_format_num(p3[0])} {_format_num(p3[1])}")

    else:
        # MODO POR CONTORNO (Paralelo)
        for c_idx, c_obj in enumerate(contour_data):
            c_len = c_obj['total_len']
            if c_len <= 1e-9:
                continue

            local_d0 = t0 * c_len
            local_d1 = t1 * c_len

            first_pt_written = False
            for s_info in c_obj['segments']:
                s_d0 = s_info['start_dist']
                s_d1 = s_info['end_dist']
                s_len = s_info['len']

                if s_d1 <= local_d0 or s_d0 >= local_d1 or s_len <= 1e-9:
                    continue

                in_s_d0 = max(0.0, local_d0 - s_d0)
                in_s_d1 = min(s_len, local_d1 - s_d0)

                if s_info['seg']['type'] == 'l':
                    u_s = in_s_d0 / s_len if s_len > 1e-9 else 0.0
                    u_e = in_s_d1 / s_len if s_len > 1e-9 else 1.0
                else:
                    u_s = _map_dist_to_bezier_u(in_s_d0, s_info['chord_lens'], sub)
                    u_e = _map_dist_to_bezier_u(in_s_d1, s_info['chord_lens'], sub)

                cut_s, s_tip, s_tan = _cut_segment_interval(s_info['seg'], u_s, u_e, subdivs=sub)
                if cut_s:
                    tip_pt = s_tip
                    tip_tangent = s_tan
                    current_cut_len += (in_s_d1 - in_s_d0)

                    if not first_pt_written:
                        p_start = cut_s['p0']
                        out_tokens.append(f"m {_format_num(p_start[0])} {_format_num(p_start[1])}")
                        first_pt_written = True

                    if cut_s['type'] == 'l':
                        p1 = cut_s['p1']
                        out_tokens.append(f"l {_format_num(p1[0])} {_format_num(p1[1])}")
                    elif cut_s['type'] == 'b':
                        p1, p2, p3 = cut_s['p1'], cut_s['p2'], cut_s['p3']
                        out_tokens.append(f"b {_format_num(p1[0])} {_format_num(p1[1])} {_format_num(p2[0])} {_format_num(p2[1])} {_format_num(p3[0])} {_format_num(p3[1])}")

    final_shape = (" ".join(out_tokens) + " ") if out_tokens else ""
    angle_deg = math.degrees(math.atan2(tip_tangent[1], tip_tangent[0])) % 360.0

    return final_shape, tip_pt[0], tip_pt[1], angle_deg, current_cut_len, total_shape_len


def shape_walker_node(
    context=None,
    shape="",
    progress=1.0,
    start_t=0.0,
    mode="Global (Continuo)",
    invert=False,
    subdivs=30
):
    r"""Nodo Shape Walker / Recorredor (Corte Paramétrico por Longitud de Arco / Write-on).
    Soporta entradas como Código ASSdraw o Texto plano auto-vectorizado.
    Retorna tupla: (Shape Out, \pos Tag, Angle (\frz), Length, Tip X, Tip Y).
    """
    from node_engine import _eval_num_expr

    unit = context.get('active_unit') if isinstance(context, dict) else None
    if not unit and isinstance(context, dict):
        unit = context.get('char') or context.get('syl') or context.get('word')
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
    if not line and unit and hasattr(unit, 'line'):
        line = getattr(unit, 'line', None)

    shp_val = resolve_shape_value(shape, context)

    # Si la entrada shape está vacía o es por defecto, tomar el objeto activo del Main Loop (char / syl / word / line)
    if not shp_val:
        shp_val = getattr(unit, 'shape_drawing', getattr(unit, 'shape', getattr(unit, 'drawing', ''))) if unit else ''
        if not shp_val and line:
            shp_val = getattr(line, 'shape_drawing', getattr(line, 'shape', getattr(line, 'drawing', '')))
        if not shp_val and unit:
            shp_val = getattr(unit, 'text_stripped', getattr(unit, 'text', ''))
        if not shp_val and line:
            shp_val = getattr(line, 'text_stripped', getattr(line, 'text', ''))

    # Si es texto plano o un glifo, vectorizar automáticamente con FontVectorEngine
    if shp_val and not shp_val.lower().startswith("m ") and not shp_val.lower().startswith("m-") and not shp_val.lower().startswith("m0"):
        from font_vector_engine import FontVectorEngine
        styleref = getattr(line, 'styleref', None) if line else None
        if not styleref and unit:
            styleref = getattr(unit, 'styleref', None)
            if not styleref and hasattr(unit, 'line') and getattr(unit, 'line', None):
                styleref = getattr(unit.line, 'styleref', None)

        fn = str(getattr(styleref, 'fontname', 'Arial')) if (styleref and getattr(styleref, 'fontname', None)) else "Arial"
        fs = int(float(getattr(styleref, 'fontsize', 40))) if (styleref and getattr(styleref, 'fontsize', None)) else int(getattr(unit, 'height', getattr(line, 'height', 40)) or 40)
        b_val = bool(getattr(styleref, 'bold', False)) if styleref else False
        i_val = bool(getattr(styleref, 'italic', False)) if styleref else False
        sc_x = float(getattr(styleref, 'scale_x', 100.0)) if styleref else 100.0
        sc_y = float(getattr(styleref, 'scale_y', 100.0)) if styleref else 100.0

        raw_text_src = getattr(unit, 'text', '') or getattr(line, 'raw_text', '') or getattr(line, 'text', '')
        if raw_text_src:
            fn_m = re.search(r'\\fn([^\\}]+)', raw_text_src)
            if fn_m: fn = fn_m.group(1).strip()
            fs_m = re.search(r'\\fs(\d+)', raw_text_src)
            if fs_m: fs = int(fs_m.group(1))
            fscx_m = re.search(r'\\fscx(\d+(?:\.\d+)?)', raw_text_src)
            if fscx_m: sc_x = float(fscx_m.group(1))
            fscy_m = re.search(r'\\fscy(\d+(?:\.\d+)?)', raw_text_src)
            if fscy_m: sc_y = float(fscy_m.group(1))
            b_m = re.search(r'\\b([01])', raw_text_src)
            if b_m: b_val = (b_m.group(1) == '1')
            i_m = re.search(r'\\i([01])', raw_text_src)
            if i_m: i_val = (i_m.group(1) == '1')

        v_shp = FontVectorEngine.text_to_shape(shp_val, font_name=fn, font_size=fs, bold=b_val, italic=i_val, scale_x=sc_x, scale_y=sc_y)
        if v_shp and v_shp.strip():
            shp_val = v_shp

    p_val = _eval_num_expr(progress, context, 1.0)
    s_val = _eval_num_expr(start_t, context, 0.0)
    sub_val = int(_eval_num_expr(subdivs, context, 30.0))

    if isinstance(invert, (int, float, bool)):
        inv_bool = bool(invert)
    else:
        inv_str = str(invert).strip().lower()
        if inv_str in ("1", "true", "yes", "si", "sí", "invertido", "invert"):
            inv_bool = True
        elif inv_str in ("0", "false", "no", "normal", "0.0", ""):
            inv_bool = False
        else:
            try:
                inv_eval = _eval_num_expr(invert, context, 0.0)
                inv_bool = bool(float(inv_eval) > 0.5)
            except Exception:
                inv_bool = False

    mode_str = str(mode).strip()

    final_shp, tx, ty, angle, cut_len, _ = shape_walker_core(
        shp_val,
        progress=p_val,
        start_t=s_val,
        mode=mode_str,
        invert=inv_bool,
        subdivs=sub_val
    )

    pos_str = f"\\pos({tx:.2f},{ty:.2f})".rstrip('0').rstrip('.') if (tx != 0 or ty != 0) else ""

    return final_shp, pos_str, round(angle, 2), round(cut_len, 2), round(tx, 2), round(ty, 2)


NODE_REGISTRY["Shape/Shape Walker"] = shape_walker_node
NODE_REGISTRY["Shape Walker"] = shape_walker_node


# -----------------------------------------------------------------------------
# SHAPE ARRAY / ARREGLOS Y FORMACIONES VECTORIALES
# -----------------------------------------------------------------------------
_GLOBAL_SHAPE_ARRAY_CACHE = {}

def clear_shape_array_caches():
    """Limpia la caché global de formaciones y arreglos de Shape Array."""
    _GLOBAL_SHAPE_ARRAY_CACHE.clear()


def point_in_contour_vectorized(points_x, points_y, contour):
    """Prueba rápida y vectorizada de punto en contorno (Ray-Casting en NumPy)."""
    if len(contour) < 3 or len(points_x) == 0:
        return np.zeros(len(points_x), dtype=bool)
    x = contour[:, 0]
    y = contour[:, 1]
    
    px = points_x[:, np.newaxis]
    py = points_y[:, np.newaxis]
    
    x1 = x[:-1]
    y1 = y[:-1]
    x2 = x[1:]
    y2 = y[1:]
    
    if x[0] != x[-1] or y[0] != y[-1]:
        x1 = np.append(x1, x[-1])
        y1 = np.append(y1, y[-1])
        x2 = np.append(x2, x[0])
        y2 = np.append(y2, y[0])
        
    x1 = x1[np.newaxis, :]
    y1 = y1[np.newaxis, :]
    x2 = x2[np.newaxis, :]
    y2 = y2[np.newaxis, :]
    
    cond1 = (y1 <= py) & (py < y2)
    cond2 = (y2 <= py) & (py < y1)
    cond_y = cond1 | cond2
    
    dy = np.where(y2 == y1, 1e-12, y2 - y1)
    x_inters = (x2 - x1) * (py - y1) / dy + x1
    cond_x = px < x_inters
    
    crossings = np.sum(cond_y & cond_x, axis=1)
    return (crossings % 2) == 1


def shape_array_core(
    particle="m 0 0 l 10 0 l 10 10 l 0 10",
    formation="",
    width=0.0,
    height=0.0,
    scale=1.0,
    mode="Grid",
    cols=5,
    rows=3,
    spacing_x=0.0,
    spacing_y=0.0,
    spacing=0.0,
    rings=3,
    count_per_ring="",
    radius=50.0,
    radius_step=30.0,
    rotate_step=0.0,
    count=20,
    turns=2.0,
    max_radius=100.0,
    angle_step=0.0,
    area_width=150.0,
    area_height=100.0,
    seed=1,
    anchor="piezas",
    order="79",
    out_mode="Loops",
    active_index=1,
    parent_x=0.0,
    parent_y=0.0,
    context=None
):
    """Motor de cálculo geométrico y generación para Shape Array.
    Soporta modos Grid, Formation, Rings, Spiral, Scatter y Hex,
    con dimensionamiento previo, ordenamiento Numpad y anclaje local o relativo."""
    if context is None:
        context = {}

    mode_clean = str(mode or "Grid").strip().lower()
    target_w = float(width) if width not in ("", None) else 0.0
    target_h = float(height) if height not in ("", None) else 0.0
    sc_val = max(0.001, float(scale) if scale not in ("", None) else 1.0)
    cols_val = int(float(cols)) if cols not in ("", None) else 5
    rows_val = int(float(rows)) if rows not in ("", None) else 3
    sp_x_val = float(spacing_x) if spacing_x not in ("", None) else 0.0
    sp_y_val = float(spacing_y) if spacing_y not in ("", None) else 0.0
    sp_val = float(spacing) if spacing not in ("", None) else 0.0
    rings_val = int(float(rings)) if rings not in ("", None) else 3
    c_per_ring_str = str(count_per_ring or "")
    rad_val = float(radius) if radius not in ("", None) else 50.0
    dr_val = float(radius_step) if radius_step not in ("", None) else 30.0
    d_rot_val = float(rotate_step) if rotate_step not in ("", None) else 0.0
    count_val = int(float(count)) if count not in ("", None) else 20
    turns_val = float(turns) if turns not in ("", None) else 2.0
    max_r_val = float(max_radius) if max_radius not in ("", None) else 100.0
    a_step_val = float(angle_step) if angle_step not in ("", None) else 0.0
    aw_val = float(area_width) if area_width not in ("", None) else 150.0
    ah_val = float(area_height) if area_height not in ("", None) else 100.0
    seed_val = int(float(seed)) if seed not in ("", None) else 1
    order_str = str(order or "79")

    cache_key = (
        str(particle),
        str(formation),
        target_w,
        target_h,
        sc_val,
        mode_clean,
        cols_val,
        rows_val,
        sp_x_val,
        sp_y_val,
        sp_val,
        rings_val,
        c_per_ring_str,
        rad_val,
        dr_val,
        d_rot_val,
        count_val,
        turns_val,
        max_r_val,
        a_step_val,
        aw_val,
        ah_val,
        seed_val,
        order_str
    )

    cached_pieces = _GLOBAL_SHAPE_ARRAY_CACHE.get(cache_key)
    if cached_pieces is not None:
        return cached_pieces

    from clipper_engine import ClipperEngine
    from particle_nodes import sort_particles, _point_in_contour

    # 1. Normalizar y parsear partículas (lista cíclica o forma individual)
    raw_p_list = []
    if isinstance(particle, list):
        raw_p_list = [str(p) for p in particle if str(p).strip()]
    elif isinstance(particle, str):
        if "|" in particle:
            raw_p_list = [p.strip() for p in particle.split("|") if p.strip()]
        elif "\n" in particle:
            raw_p_list = [p.strip() for p in particle.splitlines() if p.strip()]
        else:
            raw_p_list = [particle.strip()] if particle.strip() else []

    if not raw_p_list:
        raw_p_list = ["m 0 0 l 10 0 l 10 10 l 0 10"]

    resolved_particles = []
    for p_str in raw_p_list:
        r_shp = resolve_shape_value(p_str, context) or p_str
        if r_shp and not r_shp.lower().startswith("m ") and not r_shp.lower().startswith("m-") and not r_shp.lower().startswith("m0"):
            from font_vector_engine import FontVectorEngine
            v_shp = FontVectorEngine.text_to_shape(r_shp)
            if v_shp and v_shp.strip():
                r_shp = v_shp
        if not r_shp or not r_shp.strip():
            r_shp = "m 0 0 l 10 0 l 10 10 l 0 10"
        resolved_particles.append(r_shp)

    # 2. Calcular Bounding Box y re-escalado de partículas según ancho/alto/scale
    prepared_particles = []
    eff_widths = []
    eff_heights = []

    for p_shp in resolved_particles:
        cnts = ClipperEngine.parse_assdraw(p_shp)
        _, _, _, _, _, _, pw, ph = ClipperEngine.get_bbox(cnts)
        
        sx = (target_w / max(0.001, pw)) if target_w > 0 else 1.0
        sy = (target_h / max(0.001, ph)) if target_h > 0 else 1.0
        if target_w > 0 and target_h <= 0: sy = sx
        elif target_h > 0 and target_w <= 0: sx = sy

        sx *= sc_val
        sy *= sc_val

        # Normalizar y centrar partícula en (0,0)
        norm_shp = shape_manipulator(context, drawing=p_shp, scale_x=sx, scale_y=sy, mode="center")
        prepared_particles.append(norm_shp)
        eff_widths.append(pw * sx)
        eff_heights.append(ph * sy)

    max_eff_w = max(eff_widths) if eff_widths else 10.0
    max_eff_h = max(eff_heights) if eff_heights else 10.0

    # 3. Generación geométrica según el modo
    raw_items = []

    if "form" in mode_clean or "guia" in mode_clean:
        # Modo FORMATION: Relleno interior de forma
        f_shp = resolve_shape_value(formation, context) or formation
        if f_shp and not f_shp.lower().startswith("m ") and not f_shp.lower().startswith("m-"):
            from font_vector_engine import FontVectorEngine
            v_shp = FontVectorEngine.text_to_shape(f_shp)
            if v_shp and v_shp.strip():
                f_shp = v_shp

        if not f_shp or not f_shp.strip():
            f_shp = "m 0 0 l 100 0 l 100 100 l 0 100"

        f_cnts = ClipperEngine.parse_assdraw(f_shp)
        f_min_x, f_min_y, f_max_x, f_max_y, fcx, fcy, fw, fh = ClipperEngine.get_bbox(f_cnts)

        # Si ancho/alto se definieron y se aplican a la formación
        f_scale_x = (target_w / fw) if (target_w > 0 and fw > 0) else 1.0
        f_scale_y = (target_h / fh) if (target_h > 0 and fh > 0) else 1.0
        if f_scale_x != 1.0 or f_scale_y != 1.0:
            f_cnts = [np.column_stack(((c[:, 0] - fcx) * f_scale_x + fcx, (c[:, 1] - fcy) * f_scale_y + fcy)) for c in f_cnts]
            f_min_x, f_min_y, f_max_x, f_max_y, fcx, fcy, fw, fh = ClipperEngine.get_bbox(f_cnts)

        # 1. Muestreo de posición pura en la formación (basado en el tamaño de partícula, sin distorsión de margen)
        step_x = max(1.0, max_eff_w)
        step_y = max(1.0, max_eff_h)

        grid_w = max(1.0, f_max_x - f_min_x)
        grid_h = max(1.0, f_max_y - f_min_y)
        est_points = (grid_w / step_x) * (grid_h / step_y)
        if est_points > 5000:
            scale_step = math.sqrt(est_points / 5000.0)
            step_x *= scale_step
            step_y *= scale_step

        x_ticks = np.arange(f_min_x + step_x * 0.5, f_max_x + step_x * 0.25, step_x)
        y_ticks = np.arange(f_min_y + step_y * 0.5, f_max_y + step_y * 0.25, step_y)

        if len(x_ticks) > 0 and len(y_ticks) > 0:
            gx_grid, gy_grid = np.meshgrid(x_ticks, y_ticks)
            pts_gx = gx_grid.flatten()
            pts_gy = gy_grid.flatten()
            grid_cols_cnt = len(x_ticks)
            grid_rows_cnt = len(y_ticks)

            c_center = (grid_cols_cnt + 1) / 2.0
            r_center = (grid_rows_cnt + 1) / 2.0

            cnt_bboxes = [(cnt, np.min(cnt, axis=0), np.max(cnt, axis=0)) for cnt in f_cnts]
            inside_mask = np.zeros(len(pts_gx), dtype=int)

            for cnt, c_min, c_max in cnt_bboxes:
                bbox_mask = (pts_gx >= c_min[0]) & (pts_gx <= c_max[0]) & (pts_gy >= c_min[1]) & (pts_gy <= c_max[1])
                if np.any(bbox_mask):
                    sub_inside = point_in_contour_vectorized(pts_gx[bbox_mask], pts_gy[bbox_mask], cnt)
                    inside_mask[bbox_mask] += sub_inside.astype(int)

            valid_indices = np.where(inside_mask % 2 == 1)[0]
            eff_sp_x = sp_x_val if sp_x_val != 0 else sp_val
            eff_sp_y = sp_y_val if sp_y_val != 0 else sp_val

            for idx_pt in valid_indices:
                gx = float(pts_gx[idx_pt])
                gy = float(pts_gy[idx_pt])
                c_idx = int((idx_pt % grid_cols_cnt) + 1)
                r_idx = int((idx_pt // grid_cols_cnt) + 1)

                # Posición base dentro de la formación
                rel_x = gx - fcx
                rel_y = gy - fcy

                # 2. Aplicar espaciado/margen DESPUÉS de posicionar en la formación
                final_x = rel_x + (c_idx - c_center) * eff_sp_x
                final_y = rel_y + (r_idx - r_center) * eff_sp_y

                raw_items.append({
                    "x": final_x,
                    "y": final_y,
                    "col": c_idx,
                    "row": r_idx,
                    "angle": 0.0,
                    "ring": 1,
                    "idx_ring": len(raw_items) + 1
                })

        if not raw_items:
            raw_items.append({"x": 0.0, "y": 0.0, "col": 1, "row": 1, "angle": 0.0, "ring": 1, "idx_ring": 1})

    elif "ring" in mode_clean or "anillo" in mode_clean or "radial" in mode_clean:
        # Modo RINGS: Anillos concéntricos polares
        n_rings = max(1, int(float(rings)) if rings not in ("", None) else 3)
        base_r = float(radius) if radius not in ("", None) else 50.0
        dr = float(radius_step) if radius_step not in ("", None) else 30.0
        d_rot = float(rotate_step) if rotate_step not in ("", None) else 0.0
        eff_diam = max(1.0, max(max_eff_w, max_eff_h))

        c_per_ring_val = None
        if count_per_ring not in ("", None):
            try:
                c_per_ring_val = max(1, int(float(count_per_ring)))
            except Exception:
                c_per_ring_val = None

        eff_step = max(1.0, eff_diam + sp_val)
        for k in range(n_rings):
            cur_r = base_r + k * dr
            if c_per_ring_val is not None:
                nk = c_per_ring_val
            else:
                # Auto-densidad: Perímetro / Diámetro efectivo
                perimeter = 2.0 * math.pi * max(0.1, abs(cur_r))
                nk = max(1, int(round(perimeter / eff_step)))

            d_theta = 360.0 / nk
            theta_0 = k * d_rot

            for j in range(nk):
                theta_deg = theta_0 + j * d_theta
                rad = math.radians(theta_deg)
                gx = cur_r * math.cos(rad)
                gy = cur_r * math.sin(rad)
                raw_items.append({
                    "x": gx,
                    "y": gy,
                    "col": j + 1,
                    "row": k + 1,
                    "angle": round(theta_deg, 2),
                    "ring": k + 1,
                    "idx_ring": j + 1
                })

    elif "spiral" in mode_clean or "espiral" in mode_clean:
        # Modo SPIRAL
        n_pts = max(1, int(float(count)) if count not in ("", None) else 20)
        n_turns = float(turns) if turns not in ("", None) else 2.0
        max_r = float(max_radius) if max_radius not in ("", None) else 100.0
        a_step = float(angle_step) if angle_step not in ("", None) else 0.0

        for i in range(n_pts):
            t = (i / max(1, n_pts - 1)) if n_pts > 1 else 0.0
            cur_r = max_r * t
            theta_deg = (i * a_step) if a_step != 0 else (t * n_turns * 360.0)
            rad = math.radians(theta_deg)
            gx = cur_r * math.cos(rad)
            gy = cur_r * math.sin(rad)
            raw_items.append({
                "x": gx,
                "y": gy,
                "col": i + 1,
                "row": 1,
                "angle": round(theta_deg, 2),
                "ring": 1,
                "idx_ring": i + 1
            })

    elif "scatter" in mode_clean or "dispers" in mode_clean or "rand" in mode_clean:
        # Modo SCATTER
        n_pts = max(1, int(float(count)) if count not in ("", None) else 20)
        aw = max(1.0, float(area_width) if area_width not in ("", None) else 150.0)
        ah = max(1.0, float(area_height) if area_height not in ("", None) else 100.0)
        s_seed = int(float(seed)) if seed not in ("", None) else 1
        rng = np.random.RandomState(abs(s_seed) % 1000000)

        xs = rng.uniform(-aw / 2.0, aw / 2.0, size=n_pts)
        ys = rng.uniform(-ah / 2.0, ah / 2.0, size=n_pts)
        for i in range(n_pts):
            raw_items.append({
                "x": float(xs[i]),
                "y": float(ys[i]),
                "col": i + 1,
                "row": 1,
                "angle": 0.0,
                "ring": 1,
                "idx_ring": i + 1
            })

    elif "hex" in mode_clean or "panal" in mode_clean:
        # Modo HEX (Honeycomb)
        n_cols = max(1, int(float(cols)) if cols not in ("", None) else 5)
        n_rows = max(1, int(float(rows)) if rows not in ("", None) else 3)
        sp_val = float(spacing) if spacing not in ("", None) else 0.0
        pitch_x = max_eff_w + sp_val
        pitch_y = pitch_x * math.sqrt(3.0) / 2.0

        total_w = (n_cols - 1) * pitch_x + pitch_x * 0.5
        total_h = (n_rows - 1) * pitch_y

        for r in range(n_rows):
            row_shift = (pitch_x * 0.5) if (r % 2 == 1) else 0.0
            for c in range(n_cols):
                gx = c * pitch_x + row_shift - total_w / 2.0
                gy = r * pitch_y - total_h / 2.0
                raw_items.append({
                    "x": gx,
                    "y": gy,
                    "col": c + 1,
                    "row": r + 1,
                    "angle": 0.0,
                    "ring": 0,
                    "idx_ring": 0
                })

    else:
        # Modo GRID por defecto
        n_cols = max(1, int(float(cols)) if cols not in ("", None) else 5)
        n_rows = max(1, int(float(rows)) if rows not in ("", None) else 3)
        sp_x = float(spacing_x) if spacing_x not in ("", None) else (float(spacing) if spacing not in ("", None) else 0.0)
        sp_y = float(spacing_y) if spacing_y not in ("", None) else (float(spacing) if spacing not in ("", None) else 0.0)

        pitch_x = max_eff_w + sp_x
        pitch_y = max_eff_h + sp_y

        total_w = (n_cols - 1) * pitch_x
        total_h = (n_rows - 1) * pitch_y

        for r in range(n_rows):
            for c in range(n_cols):
                gx = c * pitch_x - total_w / 2.0
                gy = r * pitch_y - total_h / 2.0
                raw_items.append({
                    "x": gx,
                    "y": gy,
                    "col": c + 1,
                    "row": r + 1,
                    "angle": 0.0,
                    "ring": 0,
                    "idx_ring": 0
                })

    if not raw_items:
        raw_items = [{"x": 0.0, "y": 0.0, "col": 1, "row": 1, "angle": 0.0, "ring": 0, "idx_ring": 0}]

    # 4. Ordenamiento Numpad
    sorted_items = sort_particles(raw_items, order_code=order, get_xy=lambda it: (it["x"], it["y"]))

    # 5. Generar piezas en coordenadas relativas y forma monolítica unificada
    pieces = []
    combined_parts = []
    for i, it in enumerate(sorted_items):
        p_base = prepared_particles[i % len(prepared_particles)]
        cx = float(it["x"])
        cy = float(it["y"])
        rel_code = shape_manipulator(context, drawing=p_base, offset_x=cx, offset_y=cy, mode="center")
        combined_parts.append(rel_code)
        pieces.append({
            "code": p_base,
            "rel_code": rel_code,
            "cx": cx,
            "cy": cy,
            "col": it["col"],
            "row": it["row"],
            "angle": it["angle"],
            "ring": it.get("ring", 1),
            "idx_ring": it.get("idx_ring", 1),
            "base_particle": p_base
        })

    unified_relative_shape = " ".join(combined_parts)
    cache_val = (pieces, unified_relative_shape)
    _GLOBAL_SHAPE_ARRAY_CACHE[cache_key] = cache_val
    return cache_val


def shape_array_node(
    context=None,
    particle="m 0 0 l 10 0 l 10 10 l 0 10",
    formation="",
    width=0.0,
    height=0.0,
    scale=1.0,
    anchor="piezas",
    order="79",
    mode="Grid",
    out_mode="Loops",
    cols=5,
    rows=3,
    spacing_x=0.0,
    spacing_y=0.0,
    spacing=0.0,
    rings=3,
    count_per_ring="",
    radius=50.0,
    radius_step=30.0,
    rotate_step=0.0,
    count=20,
    turns=2.0,
    max_radius=100.0,
    angle_step=0.0,
    area_width=150.0,
    area_height=100.0,
    seed=1
):
    r"""Nodo Shape Array: Arreglos y formaciones vectoriales al por mayor.
    Soporta modos Loops (con contadores a_i y a_n) y Shape (dibujo monolítico).
    Retorna tupla: (Shape, \pos Tag, X, Y, Angle (\frz), Index (a_i), Total (a_n), Col/Ring, Row/IdxRing).
    """
    if context is None:
        context = {}

    unit = context.get('active_unit') if isinstance(context, dict) else None
    if not unit and isinstance(context, dict):
        unit = context.get('char') or context.get('syl') or context.get('word')
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
    if not line and unit and hasattr(unit, 'line'):
        line = getattr(unit, 'line', None)

    parent_x = float(getattr(unit, 'center', getattr(unit, 'x', getattr(line, 'center', getattr(line, 'x', 0.0))))) if (unit or line) else 0.0
    parent_y = float(getattr(unit, 'middle', getattr(unit, 'y', getattr(line, 'middle', getattr(line, 'y', 0.0))))) if (unit or line) else 0.0

    pieces, unified_relative_shape = shape_array_core(
        particle=particle,
        formation=formation,
        width=width,
        height=height,
        scale=scale,
        mode=mode,
        cols=cols,
        rows=rows,
        spacing_x=spacing_x,
        spacing_y=spacing_y,
        spacing=spacing,
        rings=rings,
        count_per_ring=count_per_ring,
        radius=radius,
        radius_step=radius_step,
        rotate_step=rotate_step,
        count=count,
        turns=turns,
        max_radius=max_radius,
        angle_step=angle_step,
        area_width=area_width,
        area_height=area_height,
        seed=seed,
        anchor=anchor,
        order=order,
        out_mode=out_mode,
        parent_x=parent_x,
        parent_y=parent_y,
        context=context
    )

    total_pieces = len(pieces)
    out_mode_clean = str(out_mode or "Loops").strip().lower()
    anchor_mode = str(anchor or "piezas").strip().lower()

    if "shape" in out_mode_clean and "loop" not in out_mode_clean:
        # Modo Shape Monolítico:
        if "abs" in anchor_mode:
            combined_code = shape_manipulator(context, drawing=unified_relative_shape, offset_x=parent_x, offset_y=parent_y, mode="center")
        elif "origin" in anchor_mode:
            combined_code = " ".join([shape_manipulator(context, drawing=p["code"], offset_x=p["cx"], offset_y=p["cy"], mode="origin") for p in pieces])
        else:
            combined_code = unified_relative_shape
        pos_str = f"\\pos({parent_x:.2f},{parent_y:.2f})".rstrip('0').rstrip('.') if (parent_x != 0 or parent_y != 0) else ""
        return combined_code, pos_str, round(parent_x, 2), round(parent_y, 2), 0.0, 1, total_pieces, 1, 1

    # Modo Loops: Selecciona la pieza actual según a_i
    if isinstance(context, dict):
        context['a_n'] = total_pieces
        context['a_max'] = total_pieces
        context['maxloop'] = total_pieces

    a_i_val = int(float(context.get('a_i', context.get('j', context.get('fx_i', context.get('i', 1)))))) if isinstance(context, dict) else 1
    idx = max(0, min(a_i_val - 1, total_pieces - 1))
    piece = pieces[idx]

    cx = piece["cx"]
    cy = piece["cy"]
    px = round(parent_x + cx, 2)
    py = round(parent_y + cy, 2)
    ang = piece["angle"]
    col_val = piece["col"]
    row_val = piece["row"]

    # Configuración de anclaje según el estándar de Shape Slicer
    if any(k in anchor_mode for k in ["pieza", "piece", "local", "true"]):
        piece_code = piece["code"] # centrado en (0,0)
        if isinstance(context, dict):
            context['pos_x'] = px
            context['pos_y'] = py
            context['pos_overridden'] = True
            context['has_org'] = True
            context['org_x'] = px
            context['org_y'] = py
    elif "solo_pos" in anchor_mode or "pos" in anchor_mode:
        piece_code = piece["code"] # centrado en (0,0)
        if isinstance(context, dict):
            context['pos_x'] = px
            context['pos_y'] = py
            context['pos_overridden'] = True
            context['has_org'] = False
    elif "org" in anchor_mode or "padre" in anchor_mode:
        piece_code = piece["code"] # centrado en (0,0)
        if isinstance(context, dict):
            context['pos_x'] = px
            context['pos_y'] = py
            context['pos_overridden'] = True
            context['has_org'] = True
            context['org_x'] = parent_x
            context['org_y'] = parent_y
    elif "rel" in anchor_mode:
        piece_code = shape_manipulator(context, drawing=piece["code"], offset_x=cx, offset_y=cy, mode="center")
        if isinstance(context, dict):
            context['pos_x'] = parent_x
            context['pos_y'] = parent_y
            context['pos_overridden'] = False
            context['has_org'] = True
            context['org_x'] = parent_x
            context['org_y'] = parent_y
    elif "abs" in anchor_mode:
        piece_code = shape_manipulator(context, drawing=piece["code"], offset_x=px, offset_y=py, mode="center")
        if isinstance(context, dict):
            context['pos_x'] = 0.0
            context['pos_y'] = 0.0
            context['pos_overridden'] = True
            context['has_org'] = False
    else: # default piezas
        piece_code = piece["code"]
        if isinstance(context, dict):
            context['pos_x'] = px
            context['pos_y'] = py
            context['pos_overridden'] = True
            context['has_org'] = True
            context['org_x'] = px
            context['org_y'] = py

    if isinstance(context, dict):
        context['a_i'] = a_i_val
        context['x'] = px
        context['y'] = py
        context['fx_pos_x'] = px
        context['fx_pos_y'] = py
        context['col'] = col_val
        context['row'] = row_val
        context['angle'] = ang

    pos_str = f"\\pos({px:.2f},{py:.2f})".rstrip('0').rstrip('.')
    return piece_code, pos_str, round(px, 2), round(py, 2), round(ang, 2), a_i_val, total_pieces, col_val, row_val


NODE_REGISTRY["Shape/Shape Array"] = shape_array_node
NODE_REGISTRY["Shape Array"] = shape_array_node


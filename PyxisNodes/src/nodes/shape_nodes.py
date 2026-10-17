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

"""Vector shape library and shape manipulation nodes."""

import re
import math
from collections import OrderedDict
import numpy as np
from decorators import pyxis_node, NODE_REGISTRY

_SHAPE_BBOX_CACHE = OrderedDict()
_SHAPE_BBOX_MAX_CACHE = 2048

_PARSE_SEGMENTS_CACHE = OrderedDict()
_PARSE_SEGMENTS_MAX_CACHE = 1024

_WALKER_PARAM_CACHE = OrderedDict()
_WALKER_PARAM_MAX_CACHE = 1024

_CONCENTRIC_RINGS_CACHE = OrderedDict()
_CONCENTRIC_RINGS_MAX_CACHE = 512

_SHAPE_REDRAW_CACHE = OrderedDict()
_SHAPE_REDRAW_MAX_CACHE = 512

def shape_circle(context):
    return "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 "

def shape_square(context):
    return "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0 "

def shape_rectangle(context):
    return "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0 "

def shape_triangle(context):
    return "m 50 0 l 0 86 l 100 86 l 50 0 "

def shape_rhombus(context):
    return "m 50 0 l 0 50 l 50 100 l 100 50 l 50 0 "

def shape_rounded_corners(context):
    return "m 20 0 b 8 0 0 8 0 20 l 0 80 b 0 92 8 100 20 100 l 80 100 b 92 100 100 92 100 80 l 100 20 b 100 8 92 0 80 0 l 20 0 "

def shape_pentagon(context):
    return "m 50 0 l 0 36 l 19 95 l 81 95 l 100 36 l 50 0 "

def shape_hexagon(context):
    return "m 100 43.301 l 75 0 l 25 0 l 0 43.301 l 25 86.602 l 75 86.602 l 100 43.301 "

def shape_octagon(context):
    return "m 29 0 l 0 29 l 0 71 l 29 100 l 71 100 l 100 71 l 100 29 l 71 0 l 29 0 "

def shape_star(context):
    return "m 38 36 l 0 36 l 31 59 l 20 95 l 50 72 l 81 94 l 69 59 l 100 36 l 62 36 l 50 0 l 38 36 "

def shape_heart(context):
    return "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 106 b 75 71 100 68 100 40 b 100 16 68 0 50 25 "

def shape_star_1t(context):
    return "m 0 35 l 29 56 l 33 55 b 37 44 42 66 34 58 l 30 60 l 18 95 l 48 73 l 48 69 b 38 63 60 63 51 69 l 51 73 l 81 95 l 70 60 l 65 58 b 57 65 63 44 66 55 l 71 56 l 100 35 l 63 35 l 61 39 b 64 48 47 36 59 36 l 61 33 l 50 0 l 38 33 l 40 36 b 52 36 36 49 38 39 l 36 35 l 0 35 "

def shape_star_2t(context):
    return "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26 l 33 29 b 50 16 50 16 67 29 b 86 37 86 37 83 58 b 86 79 86 79 67 87 b 50 100 50 100 33 87 b 14 79 14 79 17 58 b 14 37 14 37 33 29 "

def shape_star_3t(context):
    return "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26 "

def shape_star_4t(context):
    return "m 25 72 l 18 61 l 0 87 l 33 87 b 42 72 53 53 25 72 m 50 87 l 37 87 l 50 116 l 67 87 b 58 72 47 53 50 87 m 75 72 l 69 83 l 100 87 l 83 58 b 66 58 45 58 75 72 m 75 43 l 82 54 l 100 29 l 67 29 b 58 45 47 63 75 43 m 50 29 l 63 29 l 50 0 l 33 29 b 42 45 53 63 50 29 m 25 43 l 31 32 l 0 29 l 16 58 b 34 58 54 58 25 43 "

def shape_star_5t(context):
    return "m 33 29 l 0 29 l 50 116 l 100 29 l 33 29 l 50 0 l 100 87 l 0 87 l 33 29 "

def shape_star_6t(context):
    return "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33 m 61 35 b 95 38 95 38 69 59 b 78 90 78 90 50 73 b 23 90 23 90 31 59 b 6 38 6 38 39 35 b 50 6 50 6 61 35 "

def shape_star_7t(context):
    return "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33 "

def shape_star_8t(context):
    return "m 39 36 b 0 36 0 36 31 59 b 20 95 20 95 50 72 b 81 95 81 95 69 59 b 100 36 100 36 62 36 b 50 0 50 0 39 36 "

def shape_star_9t(context):
    return "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29 l 10 35 l 37 35 l 50 12 l 63 35 l 90 35 l 77 58 l 90 81 l 63 81 l 50 104 l 37 81 l 10 81 l 23 58 l 10 35 "

def shape_star_10t(context):
    return "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29 "

def shape_heart_2t(context):
    return "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 m 79 27 b 74 25 76 20 81 22 b 90 26 93 36 93 43 b 93 48 87 48 87 43 b 87 39 86 30 79 27 "

def shape_heart_border(context):
    return "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 l 50 28 b 69 2 98 18 98 40 b 98 66 74 69 50 97 b 25 69 2 66 2 40 b 2 18 31 2 50 28 "

def shape_flare_1t(context):
    return "m 0 0 l 47 50 l 0 100 l 50 53 l 100 100 l 53 50 l 100 0 l 50 47 l 0 0 m 42 50 b 42 61 58 61 58 50 b 58 39 42 39 42 50 "

def shape_flare_2t(context):
    return "m 0 0 l 45 50 l 0 100 l 50 55 l 100 100 l 55 50 l 100 0 l 50 45 l 0 0 m 40 50 b 40 64 60 64 60 50 b 60 36 40 36 40 50 "

def shape_flare_3t(context):
    return "m 0 0 b 35 39 61 65 100 100 b 65 61 39 35 0 0 m 100 0 b 61 35 35 61 0 100 b 39 65 65 39 100 0 "

def shape_flare_4t(context):
    return "m 50 100 b 52 69 52 31 50 0 b 48 31 48 69 50 100 m 0 50 b 31 52 69 52 100 50 b 69 48 31 48 0 50 "

def shape_clover(context):
    return "m 1 99 l 4 106 b 21 99 44 83 53 56 b 51 73 40 88 56 98 b 72 106 80 90 77 82 b 85 86 100 82 100 69 b 100 58 87 52 64 54 b 52 55 51 50 68 48 b 85 46 94 40 95 29 b 96 18 80 10 70 19 b 70 0 40 0 40 21 b 40 33 47 37 50 43 b 54 50 52 54 47 47 b 39 38 31 26 19 27 b 0 29 0 49 13 53 b 0 58 3 80 19 79 b 39 78 40 62 51 55 b 42 79 23 92 1 99 "

def shape_feather(context):
    return "m 0 0 b 0 20 10 28 27 34 b 10 33 47 49 54 55 b 62 62 72 77 78 75 l 80 78 l 90 79 b 94 86 96 94 97 100 l 100 100 b 99 93 96 84 93 78 b 100 56 88 41 73 30 l 73 39 l 69 28 b 62 24 55 23 49 19 l 48 24 l 45 19 b 31 10 13 12 0 0 m 91 74 l 88 75 b 79 49 57 40 46 35 b 22 25 8 15 2 5 b 11 17 22 23 48 34 b 64 41 82 51 91 74 "

def shape_feather_2(context):
    return "m 99 8 l 87 18 b 83 13 75 18 75 23 b 69 19 68 29 62 27 b 53 27 50 21 44 21 b 38 15 31 11 21 8 b 14 2 7 0 4 2 b 0 16 11 37 29 43 b 40 49 65 50 78 31 b 83 34 93 29 89 20 l 100 9 "

def shape_gear(context):
    return "m 3 70 l 3 70 l 17 69 l 25 78 l 22 92 l 30 97 l 40 86 l 53 86 l 60 99 l 70 96 l 68 82 l 79 73 l 92 78 l 97 69 l 86 60 l 86 46 l 100 38 l 96 29 l 82 31 l 74 21 l 77 7 l 70 3 l 60 14 l 46 13 l 38 0 l 30 2 l 30 18 l 20 26 l 6 23 l 1 31 l 13 41 l 12 53 l 0 61 l 3 70 m 24 49 b 24 15 74 15 74 49 b 74 83 24 83 24 49 "

def shape_bubble(context):
    return "m 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 m 50 1 b 79 1 99 21 99 50 b 99 76 80 93 68 96 b 62 98 66 94 50 94 b 34 94 38 98 32 96 b 20 93 1 78 1 50 b 1 22 22 1 50 1 m 88 22 b 79 11 75 14 85 24 b 92 38 94 33 88 22 m 12 15 b 12 19 18 19 18 15 b 18 11 12 11 12 15 m 14 16 l 15 30 l 16 16 l 30 15 l 16 14 l 15 0 l 14 14 l 0 15 m 50 94 b 63 94 61 100 52 100 b 42 100 38 94 50 94 "

def shape_pixel(context):
    return "m 0 0 l 0 1 l 1 1 l 1 0 "

def shape_musical_note_1(context):
    return "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 15 b 46 18 53 25 56 36 b 56 18 48 8 33 0 l 33 70 "

def shape_musical_note_2(context):
    return "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 27 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 "

def shape_musical_note_3(context):
    return "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 36 l 93 27 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 40 29 l 40 18 l 93 8 l 93 20 l 40 29 "

def shape_musical_note_4(context):
    return "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 28 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 35 73 l 35 13 l 98 2 l 98 59 b 98 77 87 83 79 83 b 70 83 62 77 62 67 b 62 53 76 44 95 58 l 95 16 l 38 27 l 38 74 b 38 91 27 98 19 98 b 10 98 2 91 2 82 b 2 68 16 59 35 73 "

def shape_sakura_flower(context):
    return "m 50 40 l 35 0 b 10 10 0 32 0 61 b 0 88 15 117 50 130 b 85 117 100 88 100 61 b 100 32 90 10 65 0 l 50 40 "

def shape_sakura_flower_1t(context):
    return "m 41 57 b 23 57 1 53 0 82 b 26 97 34 76 44 60 l 11 76 l 41 57 m 47 62 b 38 78 23 95 50 110 b 76 95 62 78 52 62 l 50 99 l 47 62 m 56 60 b 66 76 73 97 100 82 b 99 53 77 57 58 57 l 89 76 l 56 60 m 44 50 b 34 33 26 13 0 27 b 1 57 23 53 41 53 l 11 33 l 44 50 m 52 47 b 62 32 76 15 50 0 b 23 15 38 32 47 47 l 50 12 l 52 47 m 58 53 b 77 53 99 57 100 27 b 73 13 66 33 56 50 l 89 33 l 58 53 "

def shape_sakura_flower_2t(context):
    return "m 50 52 l 50 40 l 16 20 l 0 28 l 0 46 l 15 55 l 27 46 l 14 36 l 50 52 m 46 54 l 35 48 l 0 67 l 0 86 l 16 94 l 30 86 l 30 72 l 14 79 l 46 54 m 46 59 l 34 67 l 34 104 l 50 114 l 66 104 l 66 88 l 52 81 l 50 100 l 46 59 m 50 62 l 50 75 l 84 94 l 100 86 l 100 67 l 85 60 l 73 67 l 87 79 l 50 62 m 54 60 l 66 65 l 100 46 l 100 28 l 84 20 l 69 28 l 70 44 l 87 36 l 54 60 m 54 55 l 66 47 l 66 10 l 50 0 l 34 10 l 34 26 l 48 34 l 50 14 l 54 55 "

def shape_sakura_flower_3t(context):
    return "m 47 49 b 25 49 10 52 0 63 l 0 78 l 12 85 b 21 85 26 80 31 75 b 33 69 36 63 39 58 l 18 67 l 47 49 m 44 55 b 35 70 30 84 32 102 l 47 110 l 60 102 b 61 92 61 85 59 80 b 54 76 50 70 48 65 l 47 89 l 44 55 m 48 58 b 55 73 66 88 82 92 l 95 84 l 95 69 b 90 64 85 62 78 60 b 73 61 66 62 60 61 l 79 75 l 48 58 m 53 57 b 71 60 91 54 100 46 l 100 31 l 86 22 b 79 24 72 28 68 33 b 67 39 65 45 61 50 l 80 40 l 53 57 m 56 53 b 65 39 69 24 68 8 l 53 0 l 39 8 b 38 15 38 21 41 27 b 45 31 49 36 52 41 l 53 20 l 56 53 m 52 49 b 47 34 31 21 18 15 l 4 24 l 4 39 b 9 44 15 47 23 48 b 29 46 35 46 41 46 l 22 33 l 52 49 "


import math


def get_shape_bbox_metrics(drawing: str):
    """Calculates or retrieves cached bounding box metrics (min_x, min_y, max_x, max_y, cx, cy)."""
    shp_key = str(drawing or "").strip()
    if not shp_key:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    if shp_key in _SHAPE_BBOX_CACHE:
        val = _SHAPE_BBOX_CACHE[shp_key]
        _SHAPE_BBOX_CACHE.move_to_end(shp_key)
        return val

    tokens = shp_key.split()
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

    res = (min_x, min_y, max_x, max_y, cx, cy)
    if len(_SHAPE_BBOX_CACHE) >= _SHAPE_BBOX_MAX_CACHE:
        _SHAPE_BBOX_CACHE.popitem(last=False)
    _SHAPE_BBOX_CACHE[shp_key] = res
    return res


def resolve_shape_anchor(drawing, anchor="center", context=None):
    """Calculates canonical Shape Anchor reference and base offsets for monolithic shapes:
    - 'center': Centers local bounding box around (0, 0) [ref = (cx, cy), base = (0, 0)].
    - 'origin': Aligns top-left corner of ink bounding box to (0, 0) [ref = (min_x, min_y), base = (0, 0)].
    - 'absolute': Translates shape to canvas context position (fx.pos_x, fx.pos_y) [ref = (cx, cy), base = (pos_x, pos_y)].
    Returns (ref_x, ref_y, base_x, base_y, min_x, min_y, max_x, max_y, cx, cy).
    """
    min_x, min_y, max_x, max_y, cx, cy = get_shape_bbox_metrics(drawing)

    pos_x, pos_y = 0.0, 0.0
    if isinstance(context, dict):
        unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
        try:
            pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
        except: pos_x = 0.0
        try:
            pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
        except: pos_y = 0.0

    anchor_str = str(anchor or "center").strip().lower()

    if anchor_str == "origin":
        ref_x, ref_y = min_x, min_y
        base_x, base_y = 0.0, 0.0
    elif anchor_str == "absolute":
        ref_x, ref_y = 0.0, 0.0
        base_x, base_y = pos_x, pos_y
    elif anchor_str == "relative":
        ref_x, ref_y = 0.0, 0.0
        base_x, base_y = 0.0, 0.0
    else:  # "center" fallback
        ref_x, ref_y = cx, cy
        base_x, base_y = 0.0, 0.0

    return ref_x, ref_y, base_x, base_y, min_x, min_y, max_x, max_y, cx, cy


def resolve_piece_anchor(piece_code, piece_cx=0.0, piece_cy=0.0, parent_x=0.0, parent_y=0.0, anchor="pieces", context=None):
    """Calculates canonical Piece Anchor coordinates and shape transformation for piece/slicer/array elements:
    - 'pieces': Recenters piece to local (0, 0) [-cx, -cy], pos = (parent_x + cx, parent_y + cy), org = (pos_x, pos_y), has_org = True.
    - 'relative': Keeps relative offset to parent center [code unmodified], pos = (parent_x, parent_y), org = (parent_x, parent_y), has_org = True.
    - 'parent_org': Recenters piece to local (0, 0) [-cx, -cy], pos = (parent_x + cx, parent_y + cy), org = (parent_x, parent_y), has_org = True.
    - 'pos': Recenters piece to local (0, 0) [-cx, -cy], pos = (parent_x + cx, parent_y + cy), org = None, has_org = False.
    - 'absolute': Bakes absolute screen coordinates into shape [offset +parent_x, +parent_y], pos = (parent_x, parent_y), org = None, has_org = False.
    Returns a dict with:
        'formatted_code': str,
        'pos_x': float,
        'pos_y': float,
        'org_x': float,
        'org_y': float,
        'has_org': bool,
        'pos_overridden': bool
    """
    from clipper_engine import ClipperEngine

    anchor_str = str(anchor or "pieces").strip().lower()
    raw_code = str(piece_code or "")
    cx = float(piece_cx or 0.0)
    cy = float(piece_cy or 0.0)
    px = float(parent_x or 0.0)
    py = float(parent_y or 0.0)
    abs_x = px + cx
    abs_y = py + cy

    if anchor_str == "absolute":
        formatted_code = ClipperEngine.transform_shape(raw_code, mode="Offset", offset_x=px, offset_y=py) if raw_code else ""
        pos_x = px
        pos_y = py
        org_x = 0.0
        org_y = 0.0
        has_org = False
        pos_overridden = False
    elif anchor_str == "relative":
        formatted_code = raw_code
        pos_x = px
        pos_y = py
        org_x = px
        org_y = py
        has_org = True
        pos_overridden = False
    elif anchor_str == "parent_org":
        formatted_code = ClipperEngine.transform_shape(raw_code, mode="Offset", offset_x=-cx, offset_y=-cy) if raw_code else ""
        pos_x = abs_x
        pos_y = abs_y
        org_x = px
        org_y = py
        has_org = True
        pos_overridden = True
    elif anchor_str == "pos":
        formatted_code = ClipperEngine.transform_shape(raw_code, mode="Offset", offset_x=-cx, offset_y=-cy) if raw_code else ""
        pos_x = abs_x
        pos_y = abs_y
        org_x = 0.0
        org_y = 0.0
        has_org = False
        pos_overridden = True
    else:  # "pieces" (default canonical)
        formatted_code = ClipperEngine.transform_shape(raw_code, mode="Offset", offset_x=-cx, offset_y=-cy) if raw_code else ""
        pos_x = abs_x
        pos_y = abs_y
        org_x = abs_x
        org_y = abs_y
        has_org = True
        pos_overridden = True

    if isinstance(context, dict):
        context['pos_x'] = pos_x
        context['pos_y'] = pos_y
        context['pos_overridden'] = pos_overridden
        context['has_org'] = has_org
        if pos_overridden:
            context['x'] = pos_x
            context['y'] = pos_y
            context['val_x'] = pos_x
            context['val_y'] = pos_y
            context['fx_pos_x'] = pos_x
            context['fx_pos_y'] = pos_y
        if has_org:
            context['org_x'] = org_x
            context['org_y'] = org_y
            context['fx_org_x'] = org_x
            context['fx_org_y'] = org_y

    return {
        'formatted_code': formatted_code,
        'pos_x': pos_x,
        'pos_y': pos_y,
        'org_x': org_x,
        'org_y': org_y,
        'has_org': has_org,
        'pos_overridden': pos_overridden
    }


def shape_manipulator(context, drawing="", scale_x=1.0, scale_y=1.0, rot=0.0, offset_x=0.0, offset_y=0.0, offset_border=0.0, mode="center", op_mode="scale", density=2.0, angle_x=0.0, angle_y=0.0, angle_z=0.0, axis=None, t=1.0, skew_x=0.0, skew_y=0.0, **kwargs):
    """Applies advanced vector manipulations (Scale, Borders, Deform, Position, Redraw, 3D Rotation, Reflect, Matrix).
    Canonical Shape Anchor modes:
      - 'center': Centers shape around (0,0) [ref = (cx, cy), base = (0, 0)].
      - 'origin': Aligns top-left corner of bounding box to (0,0) [ref = (min_x, min_y), base = (0, 0)].
      - 'absolute': Translates shape to screen/canvas coordinates (pos_x, pos_y) [ref = (cx, cy), base = (pos_x, pos_y)].
    """
    raw_shp = resolve_shape_value(drawing if drawing else kwargs.get("shape", ""), context)
    if not raw_shp:
        return ""

    from node_engine import _eval_num_expr
    try:
        t_val = float(_eval_num_expr(t if t is not None else kwargs.get("t", 1.0), context, 1.0))
    except Exception:
        t_val = 1.0

    op = str(op_mode or kwargs.get("operation", kwargs.get("mode", "Scale"))).strip().lower()

    if "matrix" in op or "matriz" in op:
        sx = scale_x if (scale_x is not None and str(scale_x).strip() != "") else kwargs.get("sx", kwargs.get("scale_x", 100.0))
        sy = scale_y if (scale_y is not None and str(scale_y).strip() != "") else kwargs.get("sy", kwargs.get("scale_y", 100.0))
        skx = skew_x if (skew_x is not None and str(skew_x).strip() != "") else kwargs.get("skx", kwargs.get("skew_x", 0.0))
        sky = skew_y if (skew_y is not None and str(skew_y).strip() != "") else kwargs.get("sky", kwargs.get("skew_y", 0.0))
        ax = angle_x if (angle_x is not None and str(angle_x).strip() != "") else kwargs.get("ang_x", kwargs.get("rotate_x", 0.0))
        ay = angle_y if (angle_y is not None and str(angle_y).strip() != "") else kwargs.get("ang_y", kwargs.get("rotate_y", 0.0))
        az = angle_z if (angle_z is not None and str(angle_z).strip() != "") else kwargs.get("ang_z", kwargs.get("rotate_z", kwargs.get("rot", kwargs.get("angle", rot))))
        ox = offset_x if (offset_x is not None and str(offset_x).strip() != "") else kwargs.get("off_x", 0.0)
        oy = offset_y if (offset_y is not None and str(offset_y).strip() != "") else kwargs.get("off_y", 0.0)
        ob = offset_border if (offset_border is not None and str(offset_border).strip() != "") else kwargs.get("off_border", kwargs.get("offset_border", kwargs.get("delta", 0.0)))
        ax_val = axis if axis is not None else kwargs.get("axis", "none")
        dens = kwargs.get("density", density if density not in (None, "", 2.0, "2.0", "2") else 0.0)
        return _shape_matrix_transform(raw_shp, scale_x=sx, scale_y=sy, skew_x=skx, skew_y=sky,
                                      angle_x=ax, angle_y=ay, angle_z=az, offset_x=ox, offset_y=oy,
                                      offset_border=ob, axis=ax_val, density=dens, anchor=mode, t=t_val, context=context)
    elif "redibuj" in op or "redraw" in op:
        d = density if (density is not None and str(density).strip() != "") else kwargs.get("factor", 2.0)
        return _shape_redraw_bezier(raw_shp, factor=d, anchor=mode, t=t_val, context=context)
    elif "giro" in op or "3d" in op or "rot" in op or "rotate" in op:
        ax = angle_x if (angle_x is not None and str(angle_x).strip() != "") else kwargs.get("ang_x", 0.0)
        ay = angle_y if (angle_y is not None and str(angle_y).strip() != "") else kwargs.get("ang_y", 0.0)
        az = angle_z if (angle_z is not None and str(angle_z).strip() != "") else kwargs.get("ang_z", kwargs.get("rot", kwargs.get("angle", rot)))
        return _shape_rotate_3d(raw_shp, angle_x=ax, angle_y=ay, angle_z=az, anchor=mode, t=t_val, context=context)
    elif "refle" in op or "reflect" in op or "espejo" in op:
        ax_val = axis if axis is not None else kwargs.get("axis", "y")
        ox = offset_x if (offset_x is not None and str(offset_x).strip() != "") else kwargs.get("off_x", 0.0)
        oy = offset_y if (offset_y is not None and str(offset_y).strip() != "") else kwargs.get("off_y", 0.0)
        return _shape_reflect(raw_shp, axis=ax_val, offset_x=ox, offset_y=oy, anchor=mode, t=t_val, context=context)

    delta = _eval_num_expr(offset_border, context, 0.0) if (offset_border is not None and offset_border != "") else 0.0
    delta = delta * t_val
    if abs(delta) > 0.0001:
        from clipper_engine import ClipperEngine
        off_shp = ClipperEngine.offset_shape(raw_shp, delta)
        if off_shp and off_shp.strip():
            raw_shp = off_shp

    raw_sx = _eval_num_expr(scale_x, context, 1.0) if scale_x != "" else 1.0
    raw_sy = _eval_num_expr(scale_y, context, 1.0) if scale_y != "" else 1.0
    raw_angle = _eval_num_expr(rot, context, 0.0) if rot != "" else 0.0
    raw_tx = _eval_num_expr(offset_x, context, 0.0) if offset_x != "" else 0.0
    raw_ty = _eval_num_expr(offset_y, context, 0.0) if offset_y != "" else 0.0

    sx = 1.0 + (raw_sx - 1.0) * t_val
    sy = 1.0 + (raw_sy - 1.0) * t_val
    angle = raw_angle * t_val
    tx = raw_tx * t_val
    ty = raw_ty * t_val

    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    tokens = raw_shp.split()
    ref_x, ref_y, base_x, base_y, _, _, _, _, _, _ = resolve_shape_anchor(raw_shp, anchor=mode, context=context)

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


def _shape_matrix_transform(drawing, scale_x=100.0, scale_y=100.0, skew_x=0.0, skew_y=0.0,
                           angle_x=0.0, angle_y=0.0, angle_z=0.0, offset_x=0.0, offset_y=0.0,
                           offset_border=0.0, axis="none", density=0.0, anchor="center", t=1.0, context=None):
    """Applies a master spatial matrix pipeline combining:
    1. Clipper geometric offset (offset_border) if offset_border != 0.0
    2. Redraw / subdivision (density) if density > 0.0 or < 0.0
    3. Anamorphic scale (scale_x, scale_y)
    4. Shear / Skew (skew_x, skew_y)
    5. 3D Euler rotation with perspective projection (angle_x, angle_y, angle_z)
    6. Specular reflection (axis: 'none', 'x', 'y', 'xy')
    7. Position offset / translation (offset_x, offset_y)
    All modulated by interpolation parameter t in [0.0, 1.0] and anchored to anchor.
    """
    raw_shp = resolve_shape_value(drawing, context)
    if not raw_shp:
        return ""

    from node_engine import _eval_num_expr
    try:
        t_val = float(_eval_num_expr(t if t is not None else 1.0, context, 1.0))
    except Exception:
        t_val = 1.0

    try:
        off_border_val = float(_eval_num_expr(offset_border, context, 0.0)) if (offset_border is not None and str(offset_border).strip() != "") else 0.0
    except Exception:
        off_border_val = 0.0

    delta = off_border_val * t_val
    if abs(delta) > 0.0001:
        from clipper_engine import ClipperEngine
        off_shp = ClipperEngine.offset_shape(raw_shp, delta)
        if off_shp and off_shp.strip():
            raw_shp = off_shp

    try:
        dens_val = float(_eval_num_expr(density, context, 0.0)) if density not in (None, "") else 0.0
    except Exception:
        dens_val = 0.0

    if abs(dens_val) > 1e-4 and t_val > 1e-4:
        raw_shp = _shape_redraw_bezier(raw_shp, factor=dens_val, anchor=anchor, t=t_val, context=context)
        if not raw_shp:
            return ""

    raw_sx = float(_eval_num_expr(scale_x, context, 100.0)) if scale_x not in (None, "") else 100.0
    raw_sy = float(_eval_num_expr(scale_y, context, 100.0)) if scale_y not in (None, "") else 100.0
    raw_skx = float(_eval_num_expr(skew_x, context, 0.0)) if skew_x not in (None, "") else 0.0
    raw_sky = float(_eval_num_expr(skew_y, context, 0.0)) if skew_y not in (None, "") else 0.0
    raw_ax = float(_eval_num_expr(angle_x, context, 0.0)) if angle_x not in (None, "") else 0.0
    raw_ay = float(_eval_num_expr(angle_y, context, 0.0)) if angle_y not in (None, "") else 0.0
    raw_az = float(_eval_num_expr(angle_z, context, 0.0)) if angle_z not in (None, "") else 0.0
    raw_tx = float(_eval_num_expr(offset_x, context, 0.0)) if offset_x not in (None, "") else 0.0
    raw_ty = float(_eval_num_expr(offset_y, context, 0.0)) if offset_y not in (None, "") else 0.0

    sx_factor = raw_sx / 100.0 if abs(raw_sx) > 5.0 and raw_sx != 1.0 else raw_sx
    sy_factor = raw_sy / 100.0 if abs(raw_sy) > 5.0 and raw_sy != 1.0 else raw_sy

    sx = 1.0 + (sx_factor - 1.0) * t_val
    sy = 1.0 + (sy_factor - 1.0) * t_val
    sk_x = raw_skx * t_val
    sk_y = raw_sky * t_val
    ax_deg = raw_ax * t_val
    ay_deg = raw_ay * t_val
    az_deg = raw_az * t_val
    tx = raw_tx * t_val
    ty = raw_ty * t_val

    axis_str = str(axis or "none").strip().lower()
    if "none" in axis_str or axis_str == "" or axis_str == "0":
        axis_mode = "none"
    elif "x" in axis_str and "y" not in axis_str:
        axis_mode = "x"
    elif "y" in axis_str and "x" not in axis_str:
        axis_mode = "y"
    else:
        axis_mode = "xy"

    rad_x = math.radians(ax_deg)
    rad_y = math.radians(ay_deg)
    rad_z = math.radians(az_deg)
    cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
    cos_z, sin_z = math.cos(rad_z), math.sin(rad_z)

    ref_x, ref_y, base_x, base_y, _, _, _, _, _, _ = resolve_shape_anchor(raw_shp, anchor=anchor, context=context)

    tokens = raw_shp.split()
    out_tokens = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        try:
            x_val = float(token)
            if i + 1 < len(tokens):
                try:
                    y_val = float(tokens[i + 1])
                    rx = x_val - ref_x
                    ry = y_val - ref_y

                    # 1. Scale & Skew
                    x0 = rx * sx + ry * sk_x
                    y0 = rx * sk_y + ry * sy

                    # 2. 3D Euler Rotation
                    if az_deg != 0.0:
                        x_z = x0 * cos_z - y0 * sin_z
                        y_z = x0 * sin_z + y0 * cos_z
                    else:
                        x_z = x0
                        y_z = y0

                    if ax_deg != 0.0:
                        y_x = y_z * cos_x
                        z_x = y_z * sin_x
                        x_x = x_z
                    else:
                        x_x = x_z
                        y_x = y_z
                        z_x = 0.0

                    if ay_deg != 0.0:
                        x_y = x_x * cos_y + z_x * sin_y
                        z_y = -x_x * sin_y + z_x * cos_y
                        y_y = y_x
                    else:
                        x_y = x_x
                        y_y = y_x
                        z_y = z_x

                    # 3. Perspective Projection
                    if z_y != 0.0:
                        dist = 1000.0
                        denom = dist + z_y
                        fov = dist / denom if denom > 1.0 else 1.0
                    else:
                        fov = 1.0

                    x_rot = x_y * fov
                    y_rot = y_y * fov

                    # 4. Specular Reflection
                    if axis_mode == "x":
                        x_refl = -x_rot
                        x_blend = x_rot + t_val * (x_refl - x_rot)
                        y_blend = y_rot
                    elif axis_mode == "y":
                        y_refl = -y_rot
                        x_blend = x_rot
                        y_blend = y_rot + t_val * (y_refl - y_rot)
                    elif axis_mode == "xy":
                        x_refl = -x_rot
                        y_refl = -y_rot
                        x_blend = x_rot + t_val * (x_refl - x_rot)
                        y_blend = y_rot + t_val * (y_refl - y_rot)
                    else:  # "none" (default for Matrix mode: leaves shape original/unmirrored)
                        x_blend = x_rot
                        y_blend = y_rot

                    # 5. Base anchor + offset
                    final_x = base_x + x_blend + tx
                    final_y = base_y + y_blend + ty

                    out_tokens.append(_format_num(final_x))
                    out_tokens.append(_format_num(final_y))
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


def _shape_redraw_bezier(drawing, factor=2.0, anchor="center", t=1.0, context=None):
    """Redraws a vector shape:
    - factor > 0: Densifies / refines by subdividing Bézier curves and lines preserving C1 continuity.
    - factor < 0: Simplifies / Low-Poly by converting curves into faceted polylines with fewer vertices.
    """
    raw_shp = resolve_shape_value(drawing, context)
    if not raw_shp:
        return ""
    from node_engine import _eval_num_expr
    try:
        f_val = float(_eval_num_expr(factor, context, 2.0))
    except Exception:
        f_val = 2.0

    try:
        t_val = float(_eval_num_expr(t, context, 1.0))
    except Exception:
        t_val = 1.0

    if abs(f_val) < 1e-6 or t_val <= 0.0001:
        return raw_shp

    redraw_key = (raw_shp.strip(), round(f_val, 4), round(t_val, 4))
    if redraw_key in _SHAPE_REDRAW_CACHE:
        val = _SHAPE_REDRAW_CACHE[redraw_key]
        _SHAPE_REDRAW_CACHE.move_to_end(redraw_key)
        return val

    contours = parse_assdraw_segments(raw_shp)
    if not contours:
        return raw_shp

    out_tokens = []

    for c in contours:
        start_pt = c.get('start', (0.0, 0.0))
        out_tokens.append(f"m {_format_num(start_pt[0])} {_format_num(start_pt[1])}")

        for seg in c.get('segments', []):
            stype = seg.get('type', 'l')
            if stype == 'l':
                p0 = seg['p0']
                p1 = seg['p1']
                length = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                if f_val > 0:
                    step = max(0.5, f_val / max(0.001, t_val))
                    n_parts = max(1, int(round(length / step))) if length > step else 1
                    if n_parts <= 1:
                        out_tokens.append(f"l {_format_num(p1[0])} {_format_num(p1[1])}")
                    else:
                        for k in range(1, n_parts + 1):
                            u = k / float(n_parts)
                            xk = p0[0] + u * (p1[0] - p0[0])
                            yk = p0[1] + u * (p1[1] - p0[1])
                            out_tokens.append(f"l {_format_num(xk)} {_format_num(yk)}")
                else:
                    out_tokens.append(f"l {_format_num(p1[0])} {_format_num(p1[1])}")

            elif stype in ('b', 'c'):
                p0, p1, p2, p3 = seg['p0'], seg['p1'], seg['p2'], seg['p3']
                sub_pts = []
                for s_idx in range(17):
                    u = s_idx / 16.0
                    us = 1.0 - u
                    bx = us**3 * p0[0] + 3 * us**2 * u * p1[0] + 3 * us * u**2 * p2[0] + u**3 * p3[0]
                    by = us**3 * p0[1] + 3 * us**2 * u * p1[1] + 3 * us * u**2 * p2[1] + u**3 * p3[1]
                    sub_pts.append((bx, by))

                b_len = sum(math.hypot(sub_pts[k+1][0] - sub_pts[k][0], sub_pts[k+1][1] - sub_pts[k][1]) for k in range(16))

                if f_val > 0:
                    step = max(0.5, f_val / max(0.001, t_val))
                    n_sub = max(1, int(round(b_len / step))) if b_len > step else 1
                    if n_sub <= 1:
                        out_tokens.append(f"b {_format_num(p1[0])} {_format_num(p1[1])} {_format_num(p2[0])} {_format_num(p2[1])} {_format_num(p3[0])} {_format_num(p3[1])}")
                    else:
                        cur_curve = seg
                        for k in range(1, n_sub):
                            frac = 1.0 / float(n_sub - k + 1)
                            left_s, right_s, _, _ = de_casteljau_split(cur_curve, frac)
                            lp1, lp2, lp3 = left_s['p1'], left_s['p2'], left_s['p3']
                            out_tokens.append(f"b {_format_num(lp1[0])} {_format_num(lp1[1])} {_format_num(lp2[0])} {_format_num(lp2[1])} {_format_num(lp3[0])} {_format_num(lp3[1])}")
                            cur_curve = right_s
                        rp1, rp2, rp3 = cur_curve['p1'], cur_curve['p2'], cur_curve['p3']
                        out_tokens.append(f"b {_format_num(rp1[0])} {_format_num(rp1[1])} {_format_num(rp2[0])} {_format_num(rp2[1])} {_format_num(rp3[0])} {_format_num(rp3[1])}")
                else:
                    step = max(1.0, abs(f_val))
                    n_poly = max(1, int(round(b_len / step)))
                    for k in range(1, n_poly + 1):
                        u = k / float(n_poly)
                        us = 1.0 - u
                        bx = us**3 * p0[0] + 3 * us**2 * u * p1[0] + 3 * us * u**2 * p2[0] + u**3 * p3[0]
                        by = us**3 * p0[1] + 3 * us**2 * u * p1[1] + 3 * us * u**2 * p2[1] + u**3 * p3[1]
                        out_tokens.append(f"l {_format_num(bx)} {_format_num(by)}")

    res_str = " ".join(out_tokens) + " "
    if len(_SHAPE_REDRAW_CACHE) >= _SHAPE_REDRAW_MAX_CACHE:
        _SHAPE_REDRAW_CACHE.popitem(last=False)
    _SHAPE_REDRAW_CACHE[redraw_key] = res_str
    return res_str


def _shape_rotate_3d(drawing, angle_x=0.0, angle_y=0.0, angle_z=0.0, anchor="center", t=1.0, context=None):
    """Applies 3D rotation (Euler X/Y/Z like frx, fry, and frz) to an ASS vector shape with perspective projection."""
    raw_shp = resolve_shape_value(drawing, context)
    if not raw_shp:
        return ""

    from node_engine import _eval_num_expr
    try:
        t_val = float(_eval_num_expr(t, context, 1.0))
    except Exception:
        t_val = 1.0

    ax_deg = float(_eval_num_expr(angle_x, context, 0.0)) * t_val
    ay_deg = float(_eval_num_expr(angle_y, context, 0.0)) * t_val
    az_deg = float(_eval_num_expr(angle_z, context, 0.0)) * t_val
    if ax_deg == 0.0 and ay_deg == 0.0 and az_deg == 0.0:
        return raw_shp

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

    anchor_str = str(anchor or "center").strip().lower()
    if anchor_str == "origin":
        ref_x, ref_y = min_x, min_y
    else:
        ref_x, ref_y = cx, cy

    rad_x = math.radians(ax_deg)
    rad_y = math.radians(ay_deg)
    rad_z = math.radians(az_deg)
    cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
    cos_z, sin_z = math.cos(rad_z), math.sin(rad_z)

    out_tokens = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        try:
            x_val = float(token)
            if i + 1 < len(tokens):
                try:
                    y_val = float(tokens[i + 1])
                    rx = x_val - ref_x
                    ry = y_val - ref_y

                    if az_deg != 0.0:
                        x0 = rx * cos_z - ry * sin_z
                        y0 = rx * sin_z + ry * cos_z
                    else:
                        x0 = rx
                        y0 = ry

                    if ax_deg != 0.0:
                        y1 = y0 * cos_x
                        z1 = y0 * sin_x
                        x1 = x0
                    else:
                        x1 = x0
                        y1 = y0
                        z1 = 0.0

                    if ay_deg != 0.0:
                        x2 = x1 * cos_y + z1 * sin_y
                        z2 = -x1 * sin_y + z1 * cos_y
                        y2 = y1
                    else:
                        x2 = x1
                        y2 = y1
                        z2 = z1

                    if z2 != 0.0:
                        dist = 1000.0
                        denom = dist + z2
                        fov = dist / denom if denom > 1.0 else 1.0
                    else:
                        fov = 1.0

                    final_x = ref_x + x2 * fov
                    final_y = ref_y + y2 * fov

                    out_tokens.append(_format_num(final_x))
                    out_tokens.append(_format_num(final_y))
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


def _shape_reflect(drawing, axis="y", offset_x=0.0, offset_y=0.0, anchor="center", t=1.0, context=None):
    """Applies specular reflection along X, Y, or XY axes with pivot offset and interpolation t."""
    raw_shp = resolve_shape_value(drawing, context)
    if not raw_shp:
        return ""

    from node_engine import _eval_num_expr
    try:
        t_val = float(_eval_num_expr(t, context, 1.0))
    except Exception:
        t_val = 1.0

    if abs(t_val) < 1e-6:
        return raw_shp

    off_x = float(_eval_num_expr(offset_x, context, 0.0))
    off_y = float(_eval_num_expr(offset_y, context, 0.0))

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

    anchor_str = str(anchor or "center").strip().lower()
    if anchor_str == "origin":
        ref_x, ref_y = min_x, min_y
    else:
        ref_x, ref_y = cx, cy

    piv_x = ref_x + off_x
    piv_y = ref_y + off_y

    axis_str = str(axis or "y").strip().lower()
    if axis_str in ("none", "nada", "off", "0", ""):
        return raw_shp
    if "x" in axis_str and "y" not in axis_str:
        axis_mode = "x"
    elif "y" in axis_str and "x" not in axis_str:
        axis_mode = "y"
    else:
        axis_mode = "xy"

    out_tokens = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        try:
            x_val = float(token)
            if i + 1 < len(tokens):
                try:
                    y_val = float(tokens[i + 1])
                    if axis_mode == "x":
                        refl_x = 2.0 * piv_x - x_val
                        refl_y = y_val
                    elif axis_mode == "y":
                        refl_x = x_val
                        refl_y = 2.0 * piv_y - y_val
                    else:
                        refl_x = 2.0 * piv_x - x_val
                        refl_y = 2.0 * piv_y - y_val

                    final_x = x_val + t_val * (refl_x - x_val)
                    final_y = y_val + t_val * (refl_y - y_val)

                    out_tokens.append(_format_num(final_x))
                    out_tokens.append(_format_num(final_y))
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




def _shape_inflate(drawing, t=1.0, ratio=1.0, mode="circle", anchor="center", context=None):
    """Applies radial morphological deformation (spherification/bulge) to an ASS drawing.
    Mode 'circle': radially inflates toward a circumscribed circle.
    Mode 'ellipse': radially inflates toward a circumscribed ellipse adapted to bounding box aspect.
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
    t_val = _eval_num_expr(t, context, 1.0) if (t is not None and str(t).strip() != "") else 1.0
    ratio_val = _eval_num_expr(ratio, context, 1.0) if (ratio is not None and str(ratio).strip() != "") else 1.0

    k = t_val * ratio_val

    max_step = max(5.0, min(w, h) / 16.0)
    subdivided_cmds = []
    last_pt = None

    for cmd, pt in commands:
        if not pt:
            subdivided_cmds.append((cmd, pt))
            continue

        if last_pt is not None and cmd == 'l' and abs(k) > 0.001:
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
    is_circle = (mode_str == "circle")
    diameter = math.sqrt((w * w + h * h) / 2.0)
    r1 = (diameter if is_circle else w) * math.sqrt(2.0) / 2.0
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
            target_radius = (r1 * r2) / denom if denom > EPSILON else r1
            ux = dx / dist
            uy = dy / dist
            new_dist = dist * (1.0 - k) + target_radius * k
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
    elif anchor_str == "absolute":
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = pos_x, pos_y
    else:  # "center" fallback
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




def _shape_skew(drawing, angle_x=0.0, angle_y=0.0, anchor="center", t=1.0, context=None, **kwargs):
    """Applies 2D skew / angular planar shear (Skew / Shear) to an ASS drawing with modulation t.
    Clean planar affine transformation:
      x' = base_x + rel_x + rel_y * tan(rad(angle_x * t))
      y' = base_y + rel_y + rel_x * tan(rad(angle_y * t))
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

    from node_engine import _eval_num_expr
    try:
        t_val = float(_eval_num_expr(t if t is not None else kwargs.get("t", 1.0), context, 1.0))
    except Exception:
        t_val = 1.0

    if abs(t_val) < 1e-6:
        return drawing

    ax_in = angle_x if (angle_x is not None and str(angle_x).strip() != "") else kwargs.get("angle_x", kwargs.get("angle", kwargs.get("ang_x", kwargs.get("skew_x", 0.0))))
    ay_in = angle_y if (angle_y is not None and str(angle_y).strip() != "") else kwargs.get("angle_y", kwargs.get("ang_y", kwargs.get("skew_y", 0.0)))

    try:
        if isinstance(ax_in, (int, float)):
            ax = float(ax_in)
        elif ax_in is not None and str(ax_in).strip() != "":
            ax = float(_eval_num_expr(ax_in, context, 0.0))
        else:
            ax = 0.0
    except Exception:
        ax = 0.0

    try:
        if isinstance(ay_in, (int, float)):
            ay = float(ay_in)
        elif ay_in is not None and str(ay_in).strip() != "":
            ay = float(_eval_num_expr(ay_in, context, 0.0))
        else:
            ay = 0.0
    except Exception:
        ay = 0.0

    ax = ax * t_val
    ay = ay * t_val

    if ax == 0.0 and ay == 0.0:
        return drawing

    anchor_str = str(anchor or "center").strip().lower()

    ax = max(-89.9, min(89.9, ax))
    ay = max(-89.9, min(89.9, ay))

    tan_x = math.tan(math.radians(ax))
    tan_y = math.tan(math.radians(ay))

    ref_x, ref_y, base_x, base_y, _, _, _, _, _, _ = resolve_shape_anchor(drawing, anchor=anchor, context=context)

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

                    nx = base_x + rel_x + rel_y * tan_x
                    ny = base_y + rel_y + rel_x * tan_y

                    if abs(nx) < 1e-9: nx = 0.0
                    if abs(ny) < 1e-9: ny = 0.0
                    rx = round(nx, 2)
                    ry = round(ny, 2)
                    fmt_x = int(rx) if rx.is_integer() else rx
                    fmt_y = int(ry) if ry.is_integer() else ry
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




def _shape_round_corners(drawing, radius=10.0, mode="Round", anchor="center", t=1.0, context=None, **kwargs):
    """Rounds (Round with Bézier curves) or bevels (Bevel with lines) polyhedral corners of an ASS drawing with modulation t.
    """
    if not drawing or not isinstance(drawing, str):
        return ""

    from node_engine import _eval_num_expr
    try:
        t_val = float(_eval_num_expr(t if t is not None else kwargs.get("t", 1.0), context, 1.0))
    except Exception:
        t_val = 1.0

    if abs(t_val) < 1e-6:
        return drawing

    rad_raw = _eval_num_expr(radius, context, 10.0) if (radius is not None and radius != "") else 10.0
    rad = float(rad_raw) * t_val

    if abs(rad) < 1e-6:
        return drawing

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
    is_miter = mode_str in ("miter", "square", "filoso", "lowpoly", "esquina", "recto", "facet", "faceta")
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
                elif is_miter:
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
                    p_mid = [
                        0.125 * p1[0] + 0.375 * p2[0] + 0.375 * p3[0] + 0.125 * p4[0],
                        0.125 * p1[1] + 0.375 * p2[1] + 0.375 * p3[1] + 0.125 * p4[1]
                    ]
                    res_cmds.append(('l', p_mid))
                    res_cmds.append(('l', p4))
                else:
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
            elif is_miter:
                p2 = ipol(p_curr, p_prev, 0.42 * t0)
                p3 = ipol(p_curr, p_next, 0.42 * t1)
                p4 = start_pt
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
                p_mid = [
                    0.125 * p1[0] + 0.375 * p2[0] + 0.375 * p3[0] + 0.125 * p4[0],
                    0.125 * p1[1] + 0.375 * p2[1] + 0.375 * p3[1] + 0.125 * p4[1]
                ]
                res_cmds.append(('l', p_mid))
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
                elif is_miter:
                    p2 = ipol(p_curr, p_prev, 0.42 * t0)
                    p3 = ipol(p_curr, p_next, 0.42 * t1)
                    p4 = ipol(p_curr, p_next, t1)
                    p_mid = [
                        0.125 * p1[0] + 0.375 * p2[0] + 0.375 * p3[0] + 0.125 * p4[0],
                        0.125 * p1[1] + 0.375 * p2[1] + 0.375 * p3[1] + 0.125 * p4[1]
                    ]
                    res_cmds.append(('l', p_mid))
                    res_cmds.append(('l', p4))
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

    anchor_str = str(anchor or "center").strip().lower()
    if anchor_str == "origin":
        off_x, off_y = -min_x, -min_y
    elif anchor_str == "absolute":
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = pos_x, pos_y
    else:  # "center" fallback
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
    """Bends and curves an ASS vector shape along a guide spline or parametric arc."""
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

    anchor_str = str(anchor or "center").strip().lower()
    if anchor_str == "origin":
        off_x, off_y = -n_min_x, -n_min_y
    elif anchor_str == "absolute":
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = pos_x, pos_y
    else:  # "center" fallback
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
    """Deforms an ASS vector drawing toward the morphological contour of a target shape (advanced vector morphing).
    - If step_px == 0.0 (default): Continuous analytical morphing preserving native curves and lines ('b' and 'm') with C1 smoothness.
    - If step_px >= 0.5: Normalizes both shapes into dense polylines ('l') resampled by arc length every ~step_px pixels.
    - Topological and phrase support: Hierarchical Glyph Islands with Proportional Mapping (Mitosis and Fusion).
    - Fluid modulation: During 0 < t < 1, Bézier handles modulate an elastic wave proportional to energy.
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
                idx0, idx1 = cl[0], cl[1]
                t0 = island_pairs_idx[idx0][1]
                t1 = island_pairs_idx[idx1][1]
                island_pairs_idx[idx0] = (island_pairs_idx[idx0][0], t1)
                island_pairs_idx[idx1] = (island_pairs_idx[idx1][0], t0)
            elif cl_len > 2:
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
                    else:
                        new_targets[i - 1] = targets[i]
                        new_targets[i] = targets[i - 1]
                        i += 1
                for c_i, t_i in zip(cl, new_targets):
                    island_pairs_idx[c_i] = (island_pairs_idx[c_i][0], t_i)
            elif cl_len == 1 and len(island_pairs_idx) > 1:
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
                    hA_b = ensure_bezier_winding(holes_A[h_idx]['beziers'], should_be_cw=False)
                    cx_hA, cy_hA = holes_A[h_idx]['center']
                    dest_pt = get_closest_point_on_outline(isl_B, (cx_hA, cy_hA))
                    eq_hA = [b for b in hA_b if b[0] == 'b']
                    coll_B = [('b', dest_pt, dest_pt, dest_pt, dest_pt) for _ in range(len(eq_hA))]
                    pairs.append(('collapsing_hole', False, eq_hA, coll_B))
                else:
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

    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    active_pairs = []
    has_pts = False

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

        has_pts = True
        px0, py0 = p0_mapped
        if px0 < min_x: min_x = px0
        if px0 > max_x: max_x = px0
        if py0 < min_y: min_y = py0
        if py0 > max_y: max_y = py0

        wave_t = math.sin(math.pi * t_val) if (0.0 < t_val < 1.0) else 0.0

        segs = []
        for k in range(M):
            segA, segB = bA[k], bB[k]
            p1_raw_x = segA[2][0] * (1.0 - t_val) + segB[2][0] * t_val
            p1_raw_y = segA[2][1] * (1.0 - t_val) + segB[2][1] * t_val
            p2_raw_x = segA[3][0] * (1.0 - t_val) + segB[3][0] * t_val
            p2_raw_y = segA[3][1] * (1.0 - t_val) + segB[3][1] * t_val
            p3_raw_x = segA[4][0] * (1.0 - t_val) + segB[4][0] * t_val
            p3_raw_y = segA[4][1] * (1.0 - t_val) + segB[4][1] * t_val

            if wave_t > 0.0 and energy_val > 0.0:
                p0_seg_x = segA[1][0] * (1.0 - t_val) + segB[1][0] * t_val
                p0_seg_y = segA[1][1] * (1.0 - t_val) + segB[1][1] * t_val
                dx = p3_raw_x - p0_seg_x
                dy = p3_raw_y - p0_seg_y
                chord_l = math.hypot(dx, dy)
                if chord_l > 0.01:
                    nx = -dy / chord_l
                    ny = dx / chord_l
                    h1_x = p1_raw_x - p0_seg_x
                    h1_y = p1_raw_y - p0_seg_y
                    h2_x = p2_raw_x - p3_raw_x
                    h2_y = p2_raw_y - p3_raw_y
                    
                    swell_norm = wave_t * energy_val * min(chord_l * 0.25, 25.0)
                    handle_scale = 1.0 + wave_t * energy_val * 0.35
                    
                    p1_raw_x = p0_seg_x + h1_x * handle_scale + nx * swell_norm
                    p1_raw_y = p0_seg_y + h1_y * handle_scale + ny * swell_norm
                    p2_raw_x = p3_raw_x + h2_x * handle_scale + nx * swell_norm
                    p2_raw_y = p3_raw_y + h2_y * handle_scale + ny * swell_norm

            p1_m = to_dyn_bbox((p1_raw_x, p1_raw_y))
            p2_m = to_dyn_bbox((p2_raw_x, p2_raw_y))
            p3_m = to_dyn_bbox((p3_raw_x, p3_raw_y))

            for pmx, pmy in (p1_m, p2_m, p3_m):
                if pmx < min_x: min_x = pmx
                if pmx > max_x: max_x = pmx
                if pmy < min_y: min_y = pmy
                if pmy > max_y: max_y = pmy

            segs.append(('b', p0_mapped, p1_m, p2_m, p3_m))
            p0_mapped = p3_m
        active_pairs.append(segs)

    if not has_pts:
        return drawing

    n_min_x, n_max_x = min_x, max_x
    n_min_y, n_max_y = min_y, max_y
    n_cx = (n_min_x + n_max_x) / 2.0
    n_cy = (n_min_y + n_max_y) / 2.0

    anchor_str = str(anchor or "center").strip().lower()
    if anchor_str == "origin":
        off_x, off_y = -n_min_x, -n_min_y
    elif anchor_str == "absolute":
        pos_x, pos_y = 0.0, 0.0
        if isinstance(context, dict):
            unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
            try: pos_x = float(context.get('fx_pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(context.get('line', None), 'x', 0.0)))))
            except: pos_x = 0.0
            try: pos_y = float(context.get('fx_pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(context.get('line', None), 'y', 0.0)))))
            except: pos_y = 0.0
        off_x, off_y = pos_x, pos_y
    else:  # "center" fallback
        off_x, off_y = -n_cx, -n_cy

    def fmt_num(v):
        iv = int(v)
        return iv if v == iv else round(v, 2)

    out_parts = []
    if s_px > 0.05:
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
                steps = max(1, int(round(approx_l / s_px)))
                for s in range(1, steps + 1):
                    u = s / float(steps)
                    um = 1.0 - u
                    bx = um**3 * p0[0] + 3 * um**2 * u * p1[0] + 3 * um * u**2 * p2[0] + u**3 * p3[0]
                    by = um**3 * p0[1] + 3 * um**2 * u * p1[1] + 3 * um * u**2 * p2[1] + u**3 * p3[1]
                    out_parts.append(f'l {fmt_num(bx + off_x)} {fmt_num(by + off_y)}')
    else:
        for segs in active_pairs:
            if not segs:
                continue
            p0 = segs[0][1]
            out_parts.append(f'm {fmt_num(p0[0] + off_x)} {fmt_num(p0[1] + off_y)}')
            for seg in segs:
                _, p0, p1, p2, p3 = seg
                out_parts.append(f'b {fmt_num(p1[0] + off_x)} {fmt_num(p1[1] + off_y)} {fmt_num(p2[0] + off_x)} {fmt_num(p2[1] + off_y)} {fmt_num(p3[0] + off_x)} {fmt_num(p3[1] + off_y)}')

    return ' '.join(out_parts) + ' '




def shape_transform(context, drawing="", mode="inflate", t=None, ratio=1.0, inflate_mode="circle", anchor="center", angle_x=0.0, angle_y=0.0, radius=10.0, corner_mode="round", curve=None, bend_t=1.0, axis="x", target_shape="", mid_shape="", step_px=0.0, **kwargs):
    """Applies advanced non-native ASS geometric transformations to an ASS vector drawing or text.
    Modes:
      - 'Inflate': Radial morphological deformation (spherification/bulge) toward circle or ellipse.
      - 'Skew': 2D planar shear or tilt along X and Y.
      - 'Round Corners': Rounding (Bézier arcs) or beveling (chamfer) of polyhedral corners.
      - 'Flexor': Bending and deformation along a guide spline or parametric arc.
      - 'Distort': Polar deformation toward target shape contour (2-shape morphing: t0 -> t1).
      - 'Distort2': 3-stage morphological deformation (t0: source -> t0.5: intermediate -> t1: target).
    """
    raw_shp = resolve_shape_value(drawing, context)
    if not raw_shp:
        return ""

    mode_clean = str(mode or "Inflate").strip().lower()
    if "inflate" in mode_clean or "inflar" in mode_clean:
        t_inf = t if (t is not None and str(t).strip() != "") else kwargs.get("t", 1.0)
        ratio_inf = ratio if (ratio is not None and str(ratio).strip() != "") else kwargs.get("ratio", 1.0)
        return _shape_inflate(raw_shp, t=t_inf, ratio=ratio_inf, mode=inflate_mode, anchor=anchor, context=context)
    elif "skew" in mode_clean or "cizall" in mode_clean or "inclin" in mode_clean or "oblique" in mode_clean:
        t_skew = t if (t is not None and str(t).strip() != "") else kwargs.get("t", 1.0)
        ax = angle_x if (angle_x is not None and str(angle_x).strip() != "") else (kwargs.get("angle_x", kwargs.get("angle", kwargs.get("ang_x", kwargs.get("skew_x", 0.0)))))
        ay = angle_y if (angle_y is not None and str(angle_y).strip() != "") else (kwargs.get("angle_y", kwargs.get("ang_y", kwargs.get("skew_y", 0.0))))
        return _shape_skew(raw_shp, angle_x=ax, angle_y=ay, anchor=anchor, t=t_skew, context=context, **kwargs)
    elif "round" in mode_clean or "redond" in mode_clean or "corner" in mode_clean or "esquina" in mode_clean:
        t_rc = t if (t is not None and str(t).strip() != "") else kwargs.get("t", 1.0)
        r_val = radius if radius != 10.0 else kwargs.get("radius", 10.0)
        c_mode = corner_mode if corner_mode else kwargs.get("corner_mode", "Round")
        return _shape_round_corners(raw_shp, radius=r_val, mode=c_mode, anchor=anchor, t=t_rc, context=context, **kwargs)
    elif "flex" in mode_clean or "curv" in mode_clean or "bend" in mode_clean:
        c_curve = curve if curve is not None else kwargs.get("curve", "30")
        b_t = t if (t is not None and str(t).strip() != "") else (bend_t if bend_t != 1.0 else kwargs.get("bend_t", kwargs.get("t", 1.0)))
        b_bend = kwargs.get("bend", 30.0)
        try:
            if isinstance(c_curve, (int, float)) or (isinstance(c_curve, str) and not c_curve.strip().lower().startswith("m")):
                b_bend = float(c_curve)
        except:
            pass
        ax = axis if axis else kwargs.get("axis", "x")
        return _shape_flexor(raw_shp, curve=c_curve, t=b_t, bend=b_bend, axis=ax, anchor=anchor, context=context)
    elif "distort2" in mode_clean or "distort 2" in mode_clean or "distort_2" in mode_clean:
        mid = mid_shape if mid_shape else kwargs.get("mid_shape", kwargs.get("shape_mid", kwargs.get("shape2", "")))
        mid = resolve_shape_value(mid, context)

        tgt = target_shape if target_shape else kwargs.get("target_shape", "")
        tgt = resolve_shape_value(tgt, context)

        t_morph = t if (t is not None and str(t).strip() != "") else kwargs.pop("t", 1.0)
        from node_engine import _eval_num_expr
        try:
            if isinstance(t_morph, (int, float)):
                t_num = float(t_morph)
            elif t_morph is not None and str(t_morph).strip() != "":
                t_num = float(_eval_num_expr(t_morph, context, 1.0))
            else:
                t_num = 1.0
        except Exception:
            t_num = 1.0

        t_num = max(0.0, min(1.0, t_num))
        s_px = step_px if (step_px is not None and str(step_px).strip() != "") else kwargs.pop("step_px", kwargs.pop("step", 0.0))
        e_val = kwargs.pop("energy", kwargs.pop("fluidez", kwargs.pop("fluidity", 0.35)))

        if not mid:
            return _shape_distort(raw_shp, target_shape=tgt, t=t_num, step_px=s_px, anchor=anchor, energy=e_val, context=context, **kwargs)

        if not tgt:
            return _shape_distort(raw_shp, target_shape=mid, t=t_num, step_px=s_px, anchor=anchor, energy=e_val, context=context, **kwargs)

        if t_num <= 0.5:
            t_local = t_num * 2.0
            return _shape_distort(raw_shp, target_shape=mid, t=t_local, step_px=s_px, anchor=anchor, energy=e_val, context=context, **kwargs)
        else:
            t_local = (t_num - 0.5) * 2.0
            return _shape_distort(mid, target_shape=tgt, t=t_local, step_px=s_px, anchor=anchor, energy=e_val, context=context, **kwargs)

    elif "distort" in mode_clean or "deform" in mode_clean or "morph" in mode_clean:
        tgt = target_shape if target_shape else kwargs.get("target_shape", "")
        tgt = resolve_shape_value(tgt, context)
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
    mode="hollow",
    loop_count=5,
    out_mode="shape",
    anchor="relative"
):
    """Generates continuous concentric rings and outlines layer-by-layer using Clipper (shape.borders / shape.filled_borders).
    Supports outputs as Shape (relative or absolute), \\clip(drawing), or \\iclip(drawing) for vector masks.
    """
    from node_engine import _eval_num_expr
    from clipper_engine import ClipperEngine

    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)

    parent_x = float(getattr(unit, 'center', getattr(unit, 'x', getattr(line, 'center', getattr(line, 'x', 0))))) if (unit or line) else 0.0
    parent_y = float(getattr(unit, 'middle', getattr(unit, 'y', getattr(line, 'middle', getattr(line, 'y', 0))))) if (unit or line) else 0.0
    if isinstance(context, dict) and context.get('pos_overridden'):
        parent_x = float(context.get('pos_x', parent_x))
        parent_y = float(context.get('pos_y', parent_y))

    shp_val = resolve_shape_value(shape, context)
    if not shp_val:
        return ""

    sc_val = max(0.01, float(_eval_num_expr(scale, context, 1.0)))
    if sc_val != 1.0:
        shp_val = ClipperEngine.transform_shape(shp_val, mode="Escalar", factor=sc_val)

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
    mode_str = str(mode or "hollow").strip().lower()
    is_filled_base = "relleno" in mode_str or "filled" in mode_str or "solid" in mode_str

    loops_n = max(1, int(_eval_num_expr(loop_count, context, 5.0)))
    total_rings = loops_n

    if isinstance(context, dict):
        b_i_val = int(context.get('b_i', context.get('ring_i', context.get('j', context.get('fx_i', 1)))))
        context['b_i'] = b_i_val
        context['b_n'] = total_rings
        context['b_max'] = total_rings
        context['ring_i'] = b_i_val
        context['ring_n'] = total_rings
        context['ring_max'] = total_rings
        context['maxloop'] = total_rings
        j = b_i_val
    else:
        j = 1

    rings_cache_key = (shp_val, tuple(sep_list), ov_val, total_rings, is_filled_base)
    if rings_cache_key in _CONCENTRIC_RINGS_CACHE:
        rings = _CONCENTRIC_RINGS_CACHE[rings_cache_key]
        _CONCENTRIC_RINGS_CACHE.move_to_end(rings_cache_key)
    else:
        prev_dist = 0.0
        cumulative_dist = 0.0
        rings = {}

        for i in range(1, total_rings + 1):
            if is_filled_base and i == 1:
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

        if len(_CONCENTRIC_RINGS_CACHE) >= _CONCENTRIC_RINGS_MAX_CACHE:
            _CONCENTRIC_RINGS_CACHE.popitem(last=False)
        _CONCENTRIC_RINGS_CACHE[rings_cache_key] = rings

    ring_idx = max(1, min(j, total_rings))
    current_ring_shape = rings.get(ring_idx, shp_val)

    contours = ClipperEngine.parse_assdraw(current_ring_shape)
    _, _, _, _, cx, cy, _, _ = ClipperEngine.get_bbox(contours)

    out_mode_str = str(out_mode or "shape").strip().lower()
    anchor_str = str(anchor or "relative").strip().lower()

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


NODE_REGISTRY["Shape/Concentric Borders"] = shape_concentric_borders_node
NODE_REGISTRY["Concentric Borders"] = shape_concentric_borders_node


def sort_1d_indices(count: int, order: str = "normal", seed: int = 42) -> list:
    """Genera la lista de índices permutados para ordenamientos 1D (franjas y secuencias).

    Modos Canónicos:
    - 'normal': [0, 1, 2, ..., count-1]
    - 'reverse': [count-1, ..., 2, 1, 0]
    - 'center_to_edges': inicia en el centro y se abre simétricamente hacia los extremos.
    - 'edges_to_center': inicia en los extremos y converge simétricamente al centro.
    - 'random': distribución pseudoaleatoria determinista.
    """
    import random
    N = max(1, int(count))
    indices = list(range(N))
    order_str = str(order).strip().lower()

    if "invert" in order_str or "rev" in order_str:
        indices.reverse()
    elif "center_to_edges" in order_str or (order_str.startswith("centr") and ("extremo" in order_str or "edge" in order_str or "end" in order_str or "out" in order_str)):
        mid = (N - 1) / 2.0
        indices.sort(key=lambda idx: abs(idx - mid))
    elif "edges_to_center" in order_str or ((order_str.startswith("extrem") or order_str.startswith("edge") or order_str.startswith("out")) and ("centr" in order_str or "center" in order_str)):
        mid = (N - 1) / 2.0
        indices.sort(key=lambda idx: -abs(idx - mid))
    elif "centr" in order_str or "center" in order_str:
        mid = (N - 1) / 2.0
        indices.sort(key=lambda idx: abs(idx - mid))
    elif "extrem" in order_str or "edge" in order_str or "out" in order_str:
        mid = (N - 1) / 2.0
        indices.sort(key=lambda idx: -abs(idx - mid))
    elif "aleat" in order_str or "rand" in order_str:
        rnd = random.Random(seed + N)
        rnd.shuffle(indices)

    return indices


def sort_2d_grid_indices(cols: int, rows: int, order: str = "79", seed: int = 42) -> list:
    """Genera la permutación de tuplas (col, row) (0-indexed) según el orden espacial 2D canónico.

    Modos Canónicos 2D:
    - Numpad: '79', '97', '13', '31', '71', '17', '93', '39'
    - Radiales: '5' (centro a extremos), '-5' (extremos a centro), 'cw' (horario), 'ccw' (antihorario)
    - Aleatorio: 'rand'
    """
    import math
    import random

    C = max(1, int(cols))
    R = max(1, int(rows))
    all_cells = [(c, r) for r in range(R) for c in range(C)]
    order_clean = str(order or "79").strip().lower()

    if order_clean in ("79", "normal", "forward"):
        return [(c, r) for r in range(R) for c in range(C)]
    elif order_clean in ("97",):
        return [(c, r) for r in range(R) for c in reversed(range(C))]
    elif order_clean in ("13",):
        return [(c, r) for r in reversed(range(R)) for c in range(C)]
    elif order_clean in ("31", "invert", "reverse"):
        return [(c, r) for r in reversed(range(R)) for c in reversed(range(C))]
    elif order_clean in ("71",):
        return [(c, r) for c in range(C) for r in range(R)]
    elif order_clean in ("17",):
        return [(c, r) for c in range(C) for r in reversed(range(R))]
    elif order_clean in ("93",):
        return [(c, r) for c in reversed(range(C)) for r in range(R)]
    elif order_clean in ("39",):
        return [(c, r) for c in reversed(range(C)) for r in reversed(range(R))]
    elif order_clean in ("5", "center", "center_to_edges"):
        mid_c = (C - 1) / 2.0
        mid_r = (R - 1) / 2.0
        return sorted(all_cells, key=lambda cr: (cr[0] - mid_c) ** 2 + (cr[1] - mid_r) ** 2)
    elif order_clean in ("-5", "edges", "edges_to_center"):
        mid_c = (C - 1) / 2.0
        mid_r = (R - 1) / 2.0
        return sorted(all_cells, key=lambda cr: -((cr[0] - mid_c) ** 2 + (cr[1] - mid_r) ** 2))
    elif order_clean in ("cw", "radial"):
        mid_c = (C - 1) / 2.0
        mid_r = (R - 1) / 2.0
        return sorted(all_cells, key=lambda cr: math.atan2(cr[0] - mid_c, mid_r - cr[1]) % (2 * math.pi))
    elif order_clean in ("ccw",):
        mid_c = (C - 1) / 2.0
        mid_r = (R - 1) / 2.0
        return sorted(all_cells, key=lambda cr: (-math.atan2(cr[0] - mid_c, mid_r - cr[1])) % (2 * math.pi))
    elif "rand" in order_clean or "aleat" in order_clean:
        cells_copy = list(all_cells)
        rnd = random.Random(seed + C * 1000 + R)
        rnd.shuffle(cells_copy)
        return cells_copy
    else:
        return [(c, r) for r in range(R) for c in range(C)]


@pyxis_node("Functions", "Clip Gradient", ["Cols", "Rows", "Angle", "Overlap", "Order"])
def clip_gradient_node(context=None, cols="5", rows="1", angle="0", padding="0", pad_top="0", pad_bottom="0", pad_left="0", pad_right="0", overlap="0.5", order="79", out_mode="clip", **kwargs):
    """
    Nodo Clip Gradient:
    Genera mallas y franjas escalonadas (1D/2D) para degradados continuos en libass.
    - Cols / Rows: División en cuadrícula matricial (C x R). Si rows=1 opera como franjas verticales; si cols=1 como horizontales.
    - Padding en cruceta: Expansión central uniforme (padding) sumada a cada dirección (pad_top, pad_bottom, pad_left, pad_right).
    - Ángulo == 0°: Rectángulos ortogonales AABB \\clip(x1,y1,x2,y2).
    - Ángulo != 0°: Cuadriláteros poligonales rotados \\clip(m x1 y1 l x2 y2 l x3 y3 l x4 y4).
    - Emite: Output (clip/iclip/shape), Progress (0.0..1.0), Index (1..N), Total (N), Col (1..C), Row (1..R).
    """
    from node_engine import _eval_num_expr
    import math

    if context is None:
        context = {}

    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)

    # Identificar el objeto retornado en la salida (Return del nodo Output)
    ret_raw = context.get('return_raw', '') if isinstance(context, dict) else ''

    clean_ret = str(ret_raw or "").strip()
    explicit_pos = None
    explicit_an = None
    while clean_ret.startswith("{"):
        cb = clean_ret.find("}")
        if cb == -1:
            break
        block = clean_ret[1:cb]
        m_p = re.search(r'\\pos\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)', block)
        if m_p:
            try:
                explicit_pos = (float(m_p.group(1)), float(m_p.group(2)))
            except Exception:
                pass
        m_a = re.search(r'\\an([1-9])', block)
        if m_a:
            try:
                explicit_an = int(m_a.group(1))
            except Exception:
                pass
        clean_ret = clean_ret[cb + 1:].strip()

    while clean_ret.startswith(r"\clip") or clean_ret.startswith(r"\iclip"):
        m_c = re.match(r'^\\i?clip\([^)]*\)\s*', clean_ret)
        if m_c:
            clean_ret = clean_ret[m_c.end():].strip()
        else:
            break

    # Determinar la alineación \an estipulada (default canónico: 5)
    an = kwargs.get('an', kwargs.get('align'))
    an_val = None
    if an is not None and str(an).strip() != "":
        try:
            v_an = int(float(str(an).strip()))
            if 1 <= v_an <= 9:
                an_val = v_an
        except Exception:
            pass

    if an_val is None and isinstance(context, dict):
        for k in ('an', 'align', '_active_an', 'origin_align', 'alignment'):
            if k in context and context[k] not in (None, ""):
                try:
                    v_int = int(float(str(context[k]).strip()))
                    if 1 <= v_int <= 9:
                        an_val = v_int
                        break
                except Exception:
                    pass

        if an_val is None:
            if explicit_an is not None:
                an_val = explicit_an
            else:
                tags_to_check = []
                for tk in ('_active_tags', 'tags_str', 'loop_tags', 'script_tags', 'tags', 'return_raw'):
                    if tk in context and context[tk]:
                        tags_to_check.append(str(context[tk]))
                for tc in tags_to_check:
                    m_all = re.findall(r'\\an([1-9])', tc)
                    if m_all:
                        an_val = int(m_all[-1])

    if an_val is None or an_val < 1 or an_val > 9:
        an_val = 5

    # Determinar si el objeto retornado es un Shape (vector/dibujo ASS) o Texto
    is_shape_return = False
    if isinstance(context, dict) and context.get('_return_node_is_shape'):
        is_shape_return = True
    elif clean_ret:
        low_ret = clean_ret.lower()
        if low_ret.startswith("shape.") or low_ret in RAW_PRESET_SHAPES:
            is_shape_return = True
        elif re.match(r'^[mclbsp]\s+-?\d+', clean_ret, re.IGNORECASE) or clean_ret.startswith(('m ', 'm-', 'm0')):
            is_shape_return = True

    if is_shape_return and clean_ret:
        shp_code = resolve_shape_value(clean_ret, context)
        min_x, min_y, max_x, max_y, sh_cx, sh_cy = get_shape_bbox_metrics(shp_code)
        w_val = max(1.0, float(max_x - min_x))
        h_val = max(1.0, float(max_y - min_y))

        # Posicionamiento en pantalla
        source = unit or line
        default_x = float(context.get('fx_pos_x', getattr(source, 'center', getattr(source, 'x', 0.0)))) if isinstance(context, dict) else 0.0
        default_y = float(context.get('fx_pos_y', getattr(source, 'middle', getattr(source, 'y', 0.0)))) if isinstance(context, dict) else 0.0

        if explicit_pos is not None:
            pos_x, pos_y = explicit_pos
        elif isinstance(context, dict) and context.get('pos_overridden'):
            pos_x = float(context.get('pos_x', context.get('x', default_x)))
            pos_y = float(context.get('pos_y', context.get('y', default_y)))
        else:
            pos_x = default_x
            pos_y = default_y

        sc_cx = sh_cx if (abs(pos_x) < 1e-4 and abs(pos_y) < 1e-4 and (abs(sh_cx) > 1e-4 or abs(sh_cy) > 1e-4)) else pos_x
        sc_cy = sh_cy if (abs(pos_x) < 1e-4 and abs(pos_y) < 1e-4 and (abs(sh_cx) > 1e-4 or abs(sh_cy) > 1e-4)) else pos_y

        if min_x < -1e-4 or min_y < -1e-4:
            # Shapes generated in local/centered coordinates (Slicer, Text to Shape, Particles, etc.)
            # place their (0, 0) origin directly at (sc_cx, sc_cy) on screen
            left = sc_cx + min_x
            right = sc_cx + max_x
            top = sc_cy + min_y
            bottom = sc_cy + max_y
        else:
            if an_val in (7, 4, 1):
                left = sc_cx + min_x
            elif an_val in (9, 6, 3):
                left = sc_cx - w_val
            else:
                left = sc_cx - w_val / 2.0

            if an_val in (7, 8, 9):
                top = sc_cy + min_y
            elif an_val in (1, 2, 3):
                top = sc_cy - h_val
            else:
                top = sc_cy - h_val / 2.0

            right = left + w_val
            bottom = top + h_val
    else:
        # Modo texto: medir tinta visual glyph ink contour (o vectorizar texto personalizado)
        unit_text = getattr(unit, 'text_stripped', getattr(unit, 'text', '')) if unit else ''
        line_text = getattr(line, 'text_stripped', getattr(line, 'text', '')) if line else ''
        is_default_text = (not clean_ret) or (clean_ret == unit_text) or (clean_ret == line_text)

        measured = False
        if not is_default_text and clean_ret:
            try:
                from font_vector_engine import FontVectorEngine
                v_shp = FontVectorEngine.from_context(text=clean_ret, context=context)
                if v_shp and v_shp.strip():
                    min_x, min_y, max_x, max_y, _, _ = get_shape_bbox_metrics(v_shp)
                    w_val = max(1.0, float(max_x - min_x))
                    h_val = max(1.0, float(max_y - min_y))
                    source = unit or line
                    parent_x = float(context.get('fx_pos_x', getattr(source, 'center', getattr(source, 'x', 0.0)))) if isinstance(context, dict) else 0.0
                    parent_y = float(context.get('fx_pos_y', getattr(source, 'middle', getattr(source, 'y', 0.0)))) if isinstance(context, dict) else 0.0
                    if an_val in (7, 4, 1):
                        left = parent_x
                    elif an_val in (9, 6, 3):
                        left = parent_x - w_val
                    else:
                        left = parent_x - w_val / 2.0
                    if an_val in (7, 8, 9):
                        top = parent_y
                    elif an_val in (1, 2, 3):
                        top = parent_y - h_val
                    else:
                        top = parent_y - h_val / 2.0
                    right = left + w_val
                    bottom = top + h_val
                    measured = True
            except Exception:
                measured = False

        if not measured:
            ink_target = getattr(unit, 'ink', None) or getattr(line, 'ink', None)
            if ink_target is not None and getattr(ink_target, 'width', 0) > 0 and getattr(ink_target, 'height', 0) > 0:
                parent_x = float(getattr(ink_target, 'center', getattr(ink_target, 'x', 0.0)))
                parent_y = float(getattr(ink_target, 'middle', getattr(ink_target, 'y', 0.0)))
                w_val = float(getattr(ink_target, 'width', 50.0))
                h_val = float(getattr(ink_target, 'height', 35.0))
                if an_val == 5:
                    left = float(getattr(ink_target, 'left', parent_x - w_val / 2.0))
                    top = float(getattr(ink_target, 'top', parent_y - h_val / 2.0))
                else:
                    source = unit or line
                    px = float(context.get('pos_x', context.get('fx_pos_x', getattr(source, 'left' if an_val in (7, 4, 1) else 'center', parent_x))))
                    py = float(context.get('pos_y', context.get('fx_pos_y', getattr(source, 'top' if an_val in (7, 8, 9) else 'middle', parent_y))))
                    if an_val in (7, 4, 1):
                        left = px
                    elif an_val in (9, 6, 3):
                        left = px - w_val
                    else:
                        left = px - w_val / 2.0
                    if an_val in (7, 8, 9):
                        top = py
                    elif an_val in (1, 2, 3):
                        top = py - h_val
                    else:
                        top = py - h_val / 2.0
            else:
                source = unit or line
                parent_x = float(getattr(source, 'center', getattr(source, 'x', 0.0))) if source else 0.0
                parent_y = float(getattr(source, 'middle', getattr(source, 'y', 0.0))) if source else 0.0
                w_val = float(getattr(source, 'width', 50.0)) if source else 50.0
                h_val = float(getattr(source, 'height', 35.0)) if source else 35.0
                if an_val in (7, 4, 1):
                    left = parent_x
                elif an_val in (9, 6, 3):
                    left = parent_x - w_val
                else:
                    left = parent_x - w_val / 2.0
                if an_val in (7, 8, 9):
                    top = parent_y
                elif an_val in (1, 2, 3):
                    top = parent_y - h_val
                else:
                    top = parent_y - h_val / 2.0

            right = left + w_val
            bottom = top + h_val

    C = max(1, int(_eval_num_expr(cols, context, 5.0)))
    R = max(1, int(_eval_num_expr(rows, context, 1.0)))
    N = C * R
    pad = float(_eval_num_expr(padding, context, 0.0))
    p_top = float(_eval_num_expr(pad_top, context, 0.0))
    p_bottom = float(_eval_num_expr(pad_bottom, context, 0.0))
    p_left = float(_eval_num_expr(pad_left, context, 0.0))
    p_right = float(_eval_num_expr(pad_right, context, 0.0))

    eff_top = pad + p_top
    eff_bottom = pad + p_bottom
    eff_left = pad + p_left
    eff_right = pad + p_right

    ov = float(_eval_num_expr(overlap, context, 0.5))
    ang = float(_eval_num_expr(angle, context, 0.0)) % 360.0

    if isinstance(context, dict):
        c_i_val = int(context.get('c_i', context.get('clip_i', context.get('j', context.get('fx_i', 1)))))
    else:
        c_i_val = 1

    curr_j = max(1, min(c_i_val, N))
    k = curr_j - 1

    sorted_cells = sort_2d_grid_indices(C, R, order=order)
    active_c, active_r = sorted_cells[k]
    active_col = active_c + 1
    active_row = active_r + 1

    if isinstance(context, dict):
        context['c_i'] = curr_j
        context['c_n'] = N
        context['c_max'] = N
        context['clip_i'] = curr_j
        context['clip_n'] = N
        context['clip_max'] = N
        context['maxloop'] = N
        context['c_col'] = active_col
        context['c_row'] = active_row
        context['col'] = active_col
        context['row'] = active_row

    out_mode_str = str(out_mode).strip().lower()
    is_iclip = "iclip" in out_mode_str
    is_shape = "shape" in out_mode_str or "forma" in out_mode_str or "vector" in out_mode_str or "assdraw" in out_mode_str

    if is_shape:
        if an_val in (7, 4, 1):
            b_left = 0.0 - eff_left
            b_right = w_val + eff_right
        elif an_val in (9, 6, 3):
            b_left = -w_val - eff_left
            b_right = 0.0 + eff_right
        else:
            b_left = -w_val / 2.0 - eff_left
            b_right = w_val / 2.0 + eff_right

        if an_val in (7, 8, 9):
            b_top = 0.0 - eff_top
            b_bottom = h_val + eff_bottom
        elif an_val in (1, 2, 3):
            b_top = -h_val - eff_top
            b_bottom = 0.0 + eff_bottom
        else:
            b_top = -h_val / 2.0 - eff_top
            b_bottom = h_val / 2.0 + eff_bottom

        cx = (b_left + b_right) / 2.0
        cy = (b_top + b_bottom) / 2.0
    else:
        b_left = left - eff_left
        b_right = right + eff_right
        b_top = top - eff_top
        b_bottom = bottom + eff_bottom
        cx = (b_left + b_right) / 2.0
        cy = (b_top + b_bottom) / 2.0

    b_w = max(1.0, b_right - b_left)
    b_h = max(1.0, b_bottom - b_top)

    progress = 0.0 if N == 1 else round(k / (N - 1), 4)

    if ang == 0.0:
        cell_w = b_w / C
        cell_h = b_h / R
        x1 = round(b_left + active_c * cell_w - ov, 1)
        x2 = round(b_left + (active_c + 1) * cell_w + ov, 1)
        y1 = round(b_top + active_r * cell_h - ov, 1)
        y2 = round(b_top + (active_r + 1) * cell_h + ov, 1)

        if is_shape:
            clip_res = f"m {x1} {y1} l {x2} {y1} l {x2} {y2} l {x1} {y2}"
        elif is_iclip:
            clip_res = f"\\iclip({x1},{y1},{x2},{y2})"
        else:
            clip_res = f"\\clip({x1},{y1},{x2},{y2})"
    else:
        rad = math.radians(ang)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        span_u = b_w * abs(cos_a) + b_h * abs(sin_a)
        span_v = b_w * abs(sin_a) + b_h * abs(cos_a)

        cell_w = span_u / C
        cell_h = span_v / R

        u_min = -span_u / 2.0
        v_min = -span_v / 2.0

        u1 = u_min + active_c * cell_w - ov
        u2 = u_min + (active_c + 1) * cell_w + ov
        v1 = v_min + active_r * cell_h - ov
        v2 = v_min + (active_r + 1) * cell_h + ov

        def rot_pt(u, v):
            px = cx + u * cos_a - v * sin_a
            py = cy + u * sin_a + v * cos_a
            return round(px, 1), round(py, 1)

        p1_x, p1_y = rot_pt(u1, v1)
        p2_x, p2_y = rot_pt(u2, v1)
        p3_x, p3_y = rot_pt(u2, v2)
        p4_x, p4_y = rot_pt(u1, v2)

        ass_draw = f"m {p1_x} {p1_y} l {p2_x} {p2_y} l {p3_x} {p3_y} l {p4_x} {p4_y}"
        if is_shape:
            clip_res = ass_draw
        elif is_iclip:
            clip_res = f"\\iclip({ass_draw})"
        else:
            clip_res = f"\\clip({ass_draw})"

    return clip_res, progress, curr_j, N, active_col, active_row


from decorators import NODE_REGISTRY
NODE_REGISTRY["Shape/Manipulator"] = shape_manipulator
NODE_REGISTRY["Manipulator"] = shape_manipulator
NODE_REGISTRY["Shape/Manipulator"] = shape_manipulator
NODE_REGISTRY["Manipulator"] = shape_manipulator
NODE_REGISTRY["Shape/Transform"] = shape_transform
NODE_REGISTRY["Transform"] = shape_transform
NODE_REGISTRY["Shape/Transform"] = shape_transform
NODE_REGISTRY["Transform"] = shape_transform
NODE_REGISTRY["Shape/Concentric Borders"] = shape_concentric_borders_node
NODE_REGISTRY["Concentric Borders"] = shape_concentric_borders_node
NODE_REGISTRY["Functions/Clip Gradient"] = clip_gradient_node
NODE_REGISTRY["Clip Gradient"] = clip_gradient_node


RAW_PRESET_SHAPES = {
    "circle": "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0",
    "triangle": "m 50 0 l 0 86 l 100 86 l 50 0",
    "rectangle": "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0",
    "circangle": "m 20 0 b 8 0 0 8 0 20 l 0 80 b 0 92 8 100 20 100 l 80 100 b 92 100 100 92 100 80 l 100 20 b 100 8 92 0 80 0 l 20 0",
    "pixel": "m 0 0 l 0 1 l 1 1 l 1 0",
    "pentagon": "m 50 0 l 0 36 l 19 95 l 81 95 l 100 36 l 50 0",
    "hexagon": "m 100 43.301 l 75 0 l 25 0 l 0 43.301 l 25 86.602 l 75 86.602 l 100 43.301",
    "octagon": "m 29 0 l 0 29 l 0 71 l 29 100 l 71 100 l 100 71 l 100 29 l 71 0 l 29 0",
    "diamond": "m 50 0 l 0 50 l 50 100 l 100 50 l 50 0",
    "heart": "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 106 b 75 71 100 68 100 40 b 100 16 68 0 50 25",
    "heart2t": "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 m 79 27 b 74 25 76 20 81 22 b 90 26 93 36 93 43 b 93 48 87 48 87 43 b 87 39 86 30 79 27",
    "heartb": "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 100 b 75 71 100 68 100 40 b 100 16 68 0 50 25 l 50 28 b 69 2 98 18 98 40 b 98 66 74 69 50 97 b 25 69 2 66 2 40 b 2 18 31 2 50 28",
    "shine1t": "m 0 0 l 47 50 l 0 100 l 50 53 l 100 100 l 53 50 l 100 0 l 50 47 l 0 0 m 42 50 b 42 61 58 61 58 50 b 58 39 42 39 42 50",
    "shine2t": "m 0 0 l 45 50 l 0 100 l 50 55 l 100 100 l 55 50 l 100 0 l 50 45 l 0 0 m 40 50 b 40 64 60 64 60 50 b 60 36 40 36 40 50",
    "shine3t": "m 0 0 b 35 39 61 65 100 100 b 65 61 39 35 0 0 m 100 0 b 61 35 35 61 0 100 b 39 65 65 39 100 0",
    "shine4t": "m 50 100 b 52 69 52 31 50 0 b 48 31 48 69 50 100 m 0 50 b 31 52 69 52 100 50 b 69 48 31 48 0 50",
    "clover": "m 1 99 l 4 106 b 21 99 44 83 53 56 b 51 73 40 88 56 98 b 72 106 80 90 77 82 b 85 86 100 82 100 69 b 100 58 87 52 64 54 b 52 55 51 50 68 48 b 85 46 94 40 95 29 b 96 18 80 10 70 19 b 70 0 40 0 40 21 b 40 33 47 37 50 43 b 54 50 52 54 47 47 b 39 38 31 26 19 27 b 0 29 0 49 13 53 b 0 58 3 80 19 79 b 39 78 40 62 51 55 b 42 79 23 92 1 99",
    "feather": "m 0 0 b 0 20 10 28 27 34 b 10 33 47 49 54 55 b 62 62 72 77 78 75 l 80 78 l 90 79 b 94 86 96 94 97 100 l 100 100 b 99 93 96 84 93 78 b 100 56 88 41 73 30 l 73 39 l 69 28 b 62 24 55 23 49 19 l 48 24 l 45 19 b 31 10 13 12 0 0 m 91 74 l 88 75 b 79 49 57 40 46 35 b 22 25 8 15 2 5 b 11 17 22 23 48 34 b 64 41 82 51 91 74",
    "feather2": "m 99 8 l 87 18 b 83 13 75 18 75 23 b 69 19 68 29 62 27 b 53 27 50 21 44 21 b 38 15 31 11 21 8 b 14 2 7 0 4 2 b 0 16 11 37 29 43 b 40 49 65 50 78 31 b 83 34 93 29 89 20 l 100 9",
    "gear": "m 3 70 l 3 70 l 17 69 l 25 78 l 22 92 l 30 97 l 40 86 l 53 86 l 60 99 l 70 96 l 68 82 l 79 73 l 92 78 l 97 69 l 86 60 l 86 46 l 100 38 l 96 29 l 82 31 l 74 21 l 77 7 l 70 3 l 60 14 l 46 13 l 38 0 l 30 2 l 30 18 l 20 26 l 6 23 l 1 31 l 13 41 l 12 53 l 0 61 l 3 70 m 24 49 b 24 15 74 15 74 49 b 74 83 24 83 24 49",
    "bubble": "m 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 m 50 1 b 79 1 99 21 99 50 b 99 76 80 93 68 96 b 62 98 66 94 50 94 b 34 94 38 98 32 96 b 20 93 1 78 1 50 b 1 22 22 1 50 1 m 88 22 b 79 11 75 14 85 24 b 92 38 94 33 88 22 m 12 15 b 12 19 18 19 18 15 b 18 11 12 11 12 15 m 14 16 l 15 30 l 16 16 l 30 15 l 16 14 l 15 0 l 14 14 l 0 15 m 50 94 b 63 94 61 100 52 100 b 42 100 38 94 50 94",
    "note1t": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 15 b 46 18 53 25 56 36 b 56 18 48 8 33 0 l 33 70",
    "note2t": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 27 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70",
    "note3t": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 36 l 93 27 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 40 29 l 40 18 l 93 8 l 93 20 l 40 29",
    "note4t": "m 33 70 b 16 57 0 67 0 82 b 0 93 9 100 19 100 b 28 100 40 93 40 73 l 40 28 l 93 18 l 93 55 b 76 42 60 52 60 67 b 60 78 69 85 79 85 b 88 85 100 78 100 58 l 100 0 l 33 12 l 33 70 m 35 73 l 35 13 l 98 2 l 98 59 b 98 77 87 83 79 83 b 70 83 62 77 62 67 b 62 53 76 44 95 58 l 95 16 l 38 27 l 38 74 b 38 91 27 98 19 98 b 10 98 2 91 2 82 b 2 68 16 59 35 73",
    "star": "m 38 36 l 0 36 l 31 59 l 20 95 l 50 72 l 81 94 l 69 59 l 100 36 l 62 36 l 50 0 l 38 36",
    "star1t": "m 0 35 l 29 56 l 33 55 b 37 44 42 66 34 58 l 30 60 l 18 95 l 48 73 l 48 69 b 38 63 60 63 51 69 l 51 73 l 81 95 l 70 60 l 65 58 b 57 65 63 44 66 55 l 71 56 l 100 35 l 63 35 l 61 39 b 64 48 47 36 59 36 l 61 33 l 50 0 l 38 33 l 40 36 b 52 36 36 49 38 39 l 36 35 l 0 35",
    "star2t": "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26 l 33 29 b 50 16 50 16 67 29 b 86 37 86 37 83 58 b 86 79 86 79 67 87 b 50 100 50 100 33 87 b 14 79 14 79 17 58 b 14 37 14 37 33 29",
    "star3t": "m 31 26 b 0 29 0 29 14 58 b 0 87 0 87 31 89 b 50 116 50 116 69 89 b 100 87 100 87 86 58 b 100 29 100 29 69 26 b 50 0 50 0 31 26",
    "star4t": "m 25 72 l 18 61 l 0 87 l 33 87 b 42 72 53 53 25 72 m 50 87 l 37 87 l 50 116 l 67 87 b 58 72 47 53 50 87 m 75 72 l 69 83 l 100 87 l 83 58 b 66 58 45 58 75 72 m 75 43 l 82 54 l 100 29 l 67 29 b 58 45 47 63 75 43 m 50 29 l 63 29 l 50 0 l 33 29 b 42 45 53 63 50 29 m 25 43 l 31 32 l 0 29 l 16 58 b 34 58 54 58 25 43",
    "star5t": "m 33 29 l 0 29 l 50 116 l 100 29 l 33 29 l 50 0 l 100 87 l 0 87 l 33 29",
    "star6t": "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33 m 61 35 b 95 38 95 38 69 59 b 78 90 78 90 50 73 b 23 90 23 90 31 59 b 6 38 6 38 39 35 b 50 6 50 6 61 35",
    "star7t": "m 36 33 b 0 36 0 36 27 60 b 20 95 20 95 50 77 b 81 95 81 95 73 60 b 100 36 100 36 64 33 b 50 0 50 0 36 33",
    "star8t": "m 39 36 b 0 36 0 36 31 59 b 20 95 20 95 50 72 b 81 95 81 95 69 59 b 100 36 100 36 62 36 b 50 0 50 0 39 36",
    "star9t": "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29 l 10 35 l 37 35 l 50 12 l 63 35 l 90 35 l 77 58 l 90 81 l 63 81 l 50 104 l 37 81 l 10 81 l 23 58 l 10 35",
    "star10t": "m 0 29 l 16 58 l 0 87 l 33 87 l 50 116 l 67 87 l 100 87 l 84 58 l 100 29 l 67 29 l 50 0 l 33 29 l 0 29",
    "sakura": "m 50 40 l 35 0 b 10 10 0 32 0 61 b 0 88 15 117 50 130 b 85 117 100 88 100 61 b 100 32 90 10 65 0 l 50 40",
    "sakura1t": "m 41 57 b 23 57 1 53 0 82 b 26 97 34 76 44 60 l 11 76 l 41 57 m 47 62 b 38 78 23 95 50 110 b 76 95 62 78 52 62 l 50 99 l 47 62 m 56 60 b 66 76 73 97 100 82 b 99 53 77 57 58 57 l 89 76 l 56 60 m 44 50 b 34 33 26 13 0 27 b 1 57 23 53 41 53 l 11 33 l 44 50 m 52 47 b 62 32 76 15 50 0 b 23 15 38 32 47 47 l 50 12 l 52 47 m 58 53 b 77 53 99 57 100 27 b 73 13 66 33 56 50 l 89 33 l 58 53",
    "sakura2t": "m 50 52 l 50 40 l 16 20 l 0 28 l 0 46 l 15 55 l 27 46 l 14 36 l 50 52 m 46 54 l 35 48 l 0 67 l 0 86 l 16 94 l 30 86 l 30 72 l 14 79 l 46 54 m 46 59 l 34 67 l 34 104 l 50 114 l 66 104 l 66 88 l 52 81 l 50 100 l 46 59 m 50 62 l 50 75 l 84 94 l 100 86 l 100 67 l 85 60 l 73 67 l 87 79 l 50 62 m 54 60 l 66 65 l 100 46 l 100 28 l 84 20 l 69 28 l 70 44 l 87 36 l 54 60 m 54 55 l 66 47 l 66 10 l 50 0 l 34 10 l 34 26 l 48 34 l 50 14 l 54 55",
    "sakura3t": "m 47 49 b 25 49 10 52 0 63 l 0 78 l 12 85 b 21 85 26 80 31 75 b 33 69 36 63 39 58 l 18 67 l 47 49 m 44 55 b 35 70 30 84 32 102 l 47 110 l 60 102 b 61 92 61 85 59 80 b 54 76 50 70 48 65 l 47 89 l 44 55 m 48 58 b 55 73 66 88 82 92 l 95 84 l 95 69 b 90 64 85 62 78 60 b 73 61 66 62 60 61 l 79 75 l 48 58 m 53 57 b 71 60 91 54 100 46 l 100 31 l 86 22 b 79 24 72 28 68 33 b 67 39 65 45 61 50 l 80 40 l 53 57 m 56 53 b 65 39 69 24 68 8 l 53 0 l 39 8 b 38 15 38 21 41 27 b 45 31 49 36 52 41 l 53 20 l 56 53 m 52 49 b 47 34 31 21 18 15 l 4 24 l 4 39 b 9 44 15 47 23 48 b 29 46 35 46 41 46 l 22 33 l 52 49",
    "sakura4t": "m 42 59 l 18 59 b 0 59 0 74 0 86 l 25 86 b 36 86 40 70 47 62 l 25 73 l 42 59 m 48 65 l 35 86 b 26 101 38 107 50 114 l 63 93 b 69 85 57 71 53 62 l 51 87 l 48 65 m 57 62 l 69 85 b 77 100 89 92 100 85 l 89 64 b 83 55 67 57 56 57 l 78 71 l 57 62 m 58 55 l 84 55 b 100 55 100 40 100 29 l 76 29 b 65 29 61 43 53 53 l 76 42 l 58 55 m 52 49 l 64 30 b 75 14 62 7 50 0 l 38 18 b 32 29 43 40 47 53 l 50 27 l 52 49 m 44 53 l 33 30 b 24 15 10 23 0 30 l 12 50 b 19 59 35 57 44 57 l 25 43 l 44 53",
    "sakura5t": "m 43 55 b 33 49 4 55 4 65 b 4 76 14 90 24 90 b 33 90 27 74 43 61 l 23 68 l 43 55 m 49 61 b 38 65 27 93 35 99 b 44 105 61 104 66 96 b 72 89 55 85 54 64 l 49 85 l 49 61 m 55 59 b 55 70 75 93 85 88 b 93 83 100 66 96 59 b 91 50 80 63 61 56 l 77 69 l 55 59 m 58 52 b 68 58 98 52 98 41 b 98 31 87 18 77 18 b 68 18 74 33 58 46 l 78 39 l 58 52 m 52 46 b 63 41 74 12 66 6 b 57 0 39 2 33 10 b 29 18 45 22 48 43 l 52 21 l 52 46 m 45 46 b 46 36 25 12 15 18 b 6 24 0 41 5 49 b 10 58 20 43 40 50 l 23 38 l 45 46",
    "sakura6t": "m 46 75 b 29 79 37 99 50 110 b 64 99 72 79 53 75 l 50 90 l 46 75 m 30 61 b 19 48 4 65 0 81 b 15 87 39 85 33 68 l 18 71 l 30 61 m 67 68 b 61 85 85 87 100 81 b 96 65 81 48 70 61 l 82 71 l 67 68 m 53 34 b 72 31 64 10 50 0 b 37 10 29 32 46 34 l 50 21 l 53 34 m 69 48 b 79 60 96 43 100 28 b 85 22 61 25 67 41 l 82 38 l 69 48 m 34 41 b 39 25 15 22 0 28 b 3 43 22 60 31 48 l 18 38 l 34 41",
    "sakura7t": "m 46 75 b 28 79 37 99 50 110 b 64 99 72 79 53 75 l 50 90 l 46 75 m 30 61 b 19 48 4 65 0 81 b 15 87 39 85 33 68 l 18 71 l 30 61 m 66 68 b 61 85 85 87 100 81 b 96 65 81 48 69 61 l 82 71 l 66 68 m 53 34 b 72 31 64 10 50 0 b 37 10 28 31 46 34 l 50 21 l 53 34 m 69 48 b 81 60 96 43 100 28 b 85 22 61 25 66 41 l 82 38 l 69 48 m 33 41 b 39 25 15 22 0 28 b 4 43 19 60 30 48 l 18 38 l 33 41 m 55 42 b 55 34 44 34 44 42 b 44 50 55 50 55 42 m 55 67 b 55 59 44 59 44 67 b 44 75 55 75 55 67 m 44 48 b 44 40 33 40 33 48 b 33 56 44 56 44 48 m 44 61 b 44 53 33 53 33 61 b 33 69 44 69 44 61 m 66 48 b 66 40 55 40 55 48 b 55 56 66 56 66 48 m 66 61 b 66 53 55 53 55 61 b 55 69 66 69 66 61",
    "snowflake1t": "m 30 45 l 30 52 l 20 52 l 20 55 l 30 55 l 30 62 l 16 70 l 2 61 l 0 64 l 13 72 l 1 79 l 3 82 l 15 75 l 15 90 l 18 90 l 18 73 l 32 65 l 39 69 l 33 78 l 36 80 l 42 71 l 48 74 l 48 89 l 32 98 l 34 101 l 48 93 l 48 108 l 52 108 l 52 93 l 66 101 l 67 98 l 52 89 l 52 74 l 58 71 l 64 80 l 67 78 l 61 69 l 67 65 l 82 73 l 82 90 l 85 90 l 85 75 l 97 82 l 99 79 l 87 72 l 100 64 l 98 61 l 84 70 l 70 62 l 70 55 l 80 55 l 80 52 l 70 52 l 70 45 l 84 37 l 98 46 l 100 43 l 87 35 l 99 28 l 97 25 l 85 32 l 85 16 l 82 17 l 82 34 l 68 42 l 61 38 l 67 30 l 64 28 l 58 36 l 52 33 l 52 18 l 68 9 l 66 6 l 52 14 l 52 0 l 48 0 l 48 14 l 34 6 l 32 9 l 48 18 l 48 33 l 42 36 l 36 28 l 33 30 l 39 38 l 32 42 l 18 34 l 18 17 l 15 16 l 15 32 l 3 25 l 1 28 l 13 35 l 0 43 l 2 46 l 16 37 l 30 45 l 35 45 l 50 37 l 65 45 l 65 62 l 50 70 l 35 62 l 35 45",
    "snowflake2t": "m 18 45 l 14 29 l 6 31 l 8 39 l 0 41 l 2 49 l 18 45 l 21 44 l 32 42 l 42 47 l 32 53 l 21 51 l 19 59 l 27 60 l 23 62 l 8 59 l 5 66 l 13 68 l 11 76 l 19 77 l 23 62 l 27 60 l 25 68 l 33 70 l 35 60 l 46 54 l 46 65 l 38 72 l 35 75 l 22 87 l 28 93 l 35 87 l 42 93 l 48 87 l 35 75 l 38 72 l 45 78 l 50 73 l 56 78 l 62 72 l 65 75 l 52 87 l 59 93 l 65 87 l 71 93 l 78 86 l 65 75 l 62 72 l 54 65 l 54 54 l 65 60 l 67 70 l 75 68 l 73 60 l 77 62 l 80 77 l 89 76 l 87 68 l 95 67 l 93 59 l 77 62 l 73 60 l 80 59 l 78 51 l 68 53 l 58 47 l 68 42 l 78 44 l 81 45 l 97 49 l 100 41 l 92 39 l 94 31 l 86 29 l 81 45 l 78 44 l 80 37 l 73 35 l 75 26 l 67 24 l 67 21 l 84 26 l 86 18 l 77 15 l 79 7 l 71 5 l 67 21 l 67 24 l 65 35 l 54 40 l 54 29 l 63 22 l 57 16 l 50 22 l 50 17 l 62 6 l 56 0 l 50 6 l 44 0 l 38 6 l 50 17 l 50 22 l 43 16 l 37 22 l 46 29 l 46 40 l 35 35 l 33 24 l 33 21 l 29 5 l 21 7 l 23 15 l 14 18 l 16 26 l 33 21 l 33 24 l 25 26 l 27 35 l 19 37 l 21 44",
    "snowflake3t": "m 25 39 l 11 35 l 0 47 l 11 59 l 25 55 l 19 64 l 17 61 l 6 66 l 14 68 l 11 75 l 22 69 l 20 66 l 32 65 l 22 74 l 24 90 l 39 86 l 44 74 l 49 83 l 44 83 l 44 94 l 50 87 l 56 94 l 56 83 l 51 83 l 56 74 l 61 86 l 76 90 l 78 74 l 68 65 l 80 66 l 78 69 l 88 75 l 86 68 l 94 67 l 83 61 l 81 64 l 75 55 l 88 59 l 100 47 l 88 35 l 75 39 l 81 30 l 83 33 l 94 27 l 86 26 l 88 18 l 78 24 l 80 28 l 68 29 l 78 19 l 76 4 l 61 8 l 56 20 l 51 11 l 56 11 l 56 0 l 50 7 l 44 0 l 44 11 l 49 11 l 43 20 l 39 8 l 24 4 l 22 19 l 32 29 l 20 28 l 22 24 l 11 18 l 14 26 l 6 27 l 17 33 l 19 30 l 25 39 l 46 47 b 38 47 29 57 19 47 l 28 41 l 46 47 l 48 43 b 43 36 29 35 34 19 l 42 24 l 48 43 l 52 43 l 58 24 l 66 19 b 71 35 56 36 52 43 l 54 47 l 72 41 l 81 46 b 71 57 62 47 54 47 l 52 51 b 57 58 71 59 66 75 l 58 70 l 52 51 l 48 51 l 42 70 l 34 75 b 29 59 42 58 48 51 l 46 47",
    "flower1t": "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44",
    "flower2t": "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44 m 43 15 b 43 6 55 6 55 15 b 55 24 43 24 43 15 m 9 42 b 9 33 21 33 21 42 b 21 51 9 51 9 42 m 23 82 b 23 73 35 73 35 82 b 35 91 23 91 23 82 m 66 82 b 66 73 78 73 78 82 b 78 91 66 91 66 82 m 78 40 b 78 31 90 31 90 40 b 90 49 78 49 78 40",
    "flower3t": "m 44 44 b 30 41 25 18 0 36 b 10 66 22 68 40 56 b 33 69 10 66 20 95 b 50 95 56 84 50 62 b 61 75 50 95 81 95 b 90 66 81 56 60 56 b 76 50 90 66 100 36 b 75 18 65 22 56 44 b 57 26 75 18 50 0 b 25 18 28 33 44 44 m 19 23 b 19 14 31 14 31 23 b 31 32 19 32 19 23 m 8 69 b 8 60 20 60 20 69 b 20 78 8 78 8 69 m 48 91 b 48 82 60 82 60 91 b 60 100 48 100 48 91 m 83 62 b 83 53 95 53 95 62 b 95 71 83 71 83 62 m 64 17 b 64 8 76 8 76 17 b 76 26 64 26 64 17 m 44 52 b 44 43 56 43 56 52 b 56 61 44 61 44 52",
    "flower4t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53 m 5 39 b 5 32 15 32 15 39 b 15 46 5 46 5 39 m 84 39 b 84 32 94 32 94 39 b 94 46 84 46 84 39 m 45 11 b 45 4 55 4 55 11 b 55 18 45 18 45 11 m 21 87 b 21 80 31 80 31 87 b 31 94 21 94 21 87 m 70 87 b 70 80 80 80 80 87 b 80 94 70 94 70 87",
    "flower5t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53",
    "flower6t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53 m 44 19 b 44 28 56 28 56 19 b 56 10 44 10 44 19 m 24 80 b 24 89 36 89 36 80 b 36 71 24 71 24 80 m 64 80 b 64 89 76 89 76 80 b 76 71 64 71 64 80 m 12 42 b 12 51 24 51 24 42 b 24 33 12 33 12 42 m 76 42 b 76 51 88 51 88 42 b 88 33 76 33 76 42 m 40 53 b 40 67 60 67 60 53 b 60 40 40 40 40 53",
    "flower7t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53 m 44 19 b 44 28 56 28 56 19 b 56 10 44 10 44 19 m 24 80 b 24 89 36 89 36 80 b 36 71 24 71 24 80 m 64 80 b 64 89 76 89 76 80 b 76 71 64 71 64 80 m 12 42 b 12 51 24 51 24 42 b 24 33 12 33 12 42 m 76 42 b 76 51 88 51 88 42 b 88 33 76 33 76 42",
    "flower8t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 38 69 46 91 23 91 b 16 69 38 69 50 53 b 31 46 14 61 6 38 b 24 24 31 46 50 53 b 50 33 31 20 50 6 b 69 20 50 33 50 53 b 69 46 75 25 94 38 b 87 61 69 46 50 53 b 62 69 85 68 78 91 b 54 91 62 69 50 53",
    "flower9t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53",
    "flower10t": "m 50 53 b 31 59 10 66 20 95 b 50 95 50 73 50 53 b 50 73 50 95 81 95 b 90 66 69 59 50 53 b 69 59 90 66 100 36 b 75 18 62 36 50 53 b 62 36 75 18 50 0 b 25 18 38 36 50 53 b 38 36 25 18 0 36 b 10 66 31 59 50 53 b 0 55 12 20 50 53 b 31 7 70 7 50 53 b 87 20 100 55 50 53 b 93 79 62 100 50 53 b 38 100 7 79 50 53 m 11 64 b 11 71 21 71 21 64 b 21 57 11 57 11 64 m 80 64 b 80 71 90 71 90 64 b 90 57 80 57 80 64 m 45 89 b 45 96 55 96 55 89 b 55 82 45 82 45 89 m 24 23 b 24 30 34 30 34 23 b 34 16 24 16 24 23 m 66 23 b 66 30 76 30 76 23 b 76 16 66 16 66 23",
    "flower11t": "m 100 88 b 79 99 57 89 57 62 b 80 75 100 37 100 88 m 49 66 b 49 92 92 92 49 116 b 28 104 25 80 49 66 m 41 62 b 19 75 38 110 0 88 b 0 65 18 48 41 62 m 41 54 b 20 40 0 77 0 28 b 19 17 41 26 41 54 m 49 49 b 49 23 8 23 49 0 b 68 11 71 36 49 49 m 57 54 b 80 40 58 5 100 28 b 100 54 81 67 57 54",
    "flower12t": "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58 m 24 82 b 24 90 12 90 12 82 b 12 74 24 74 24 82 m 60 97 b 60 105 48 105 48 97 b 48 89 60 89 60 97 m 93 76 b 93 84 81 84 81 76 b 81 68 93 68 93 76 m 91 34 b 91 42 79 42 79 34 b 79 26 91 26 91 34 m 54 17 b 54 25 42 25 42 17 b 42 9 54 9 54 17 m 20 39 b 20 47 8 47 8 39 b 8 31 20 31 20 39",
    "flower13t": "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58",
    "flower14t": "m 0 87 b 21 99 43 89 43 62 b 20 75 0 38 0 87 m 50 66 b 50 92 8 92 50 116 b 71 103 74 80 50 66 m 57 62 b 80 75 61 109 100 87 b 100 65 81 49 57 62 m 57 54 b 79 41 100 77 100 29 b 80 17 57 27 57 54 m 50 50 b 50 24 92 24 50 0 b 30 11 27 37 50 50 m 43 54 b 20 41 42 4 0 29 b 0 54 19 67 43 54 m 44 58 b 44 66 56 66 56 58 b 56 50 44 50 44 58",
    "flower15t": "m 30 71 l 33 62 b 16 59 0 59 0 88 b 24 102 33 88 38 74 l 30 71 m 50 84 l 44 77 b 33 88 24 102 50 117 b 76 102 68 88 56 77 l 50 84 m 70 71 l 62 74 b 68 88 76 102 100 88 b 100 59 84 59 67 62 l 70 71 m 70 47 l 67 56 b 84 59 100 59 100 30 b 76 16 67 30 62 45 l 70 47 m 50 35 l 56 42 b 67 30 76 16 50 1 b 24 16 33 30 44 42 l 50 35 m 30 47 l 38 45 b 33 30 24 16 0 30 b 0 59 16 59 33 56 l 30 47 m 0 35 b 0 25 14 25 14 35 b 14 45 0 45 0 35 m 0 83 b 0 73 14 73 14 83 b 14 93 0 93 0 83 m 43 108 b 43 98 57 98 57 108 b 57 118 43 118 43 108 m 43 10 b 43 0 57 0 57 10 b 57 20 43 20 43 10 m 86 83 b 86 73 100 73 100 83 b 100 93 86 93 86 83 m 86 35 b 86 25 100 25 100 35 b 100 45 86 45 86 35",
    "flower16t": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 83 l 44 76 b 33 87 24 102 50 116 b 76 102 68 87 56 76 l 50 83 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 56 41 b 67 29 76 14 50 0 b 24 14 33 29 44 41 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 26 29 b 26 19 40 19 40 29 b 40 39 26 39 26 29 m 60 29 b 60 19 74 19 74 29 b 74 39 60 39 60 29 m 9 58 b 9 48 23 48 23 58 b 23 68 9 68 9 58 m 77 58 b 77 48 91 48 91 58 b 91 68 77 68 77 58 m 26 87 b 26 77 40 77 40 87 b 40 97 26 97 26 87 m 60 87 b 60 77 74 77 74 87 b 74 97 60 97 60 87",
    "flower17t": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 83 l 44 76 b 33 87 24 102 50 116 b 76 102 68 87 56 76 l 50 83 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 56 41 b 67 29 76 14 50 0 b 24 14 33 29 44 41 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46",
    "flower18t": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 82 l 43 75 b 33 87 24 102 50 116 b 76 102 68 87 57 75 l 50 82 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 57 42 b 67 29 76 14 50 0 b 24 14 33 29 43 42 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 58 34 l 42 34 l 50 21 l 58 34 m 82 40 l 74 53 l 66 40 l 82 40 m 34 40 l 26 53 l 18 40 l 34 40 m 58 82 l 50 95 l 42 82 l 58 82 m 34 76 l 18 76 l 26 63 l 34 76 m 82 76 l 66 76 l 74 63 l 82 76 m 5 35 b 5 28 15 28 15 35 b 15 42 5 42 5 35 m 5 81 b 5 74 15 74 15 81 b 15 88 5 88 5 81 m 85 81 b 85 74 95 74 95 81 b 95 88 85 88 85 81 m 85 35 b 85 28 95 28 95 35 b 95 42 85 42 85 35 m 45 104 b 45 97 55 97 55 104 b 55 111 45 111 45 104 m 45 12 b 45 5 55 5 55 12 b 55 19 45 19 45 12",
    "flower19t": "m 30 70 l 33 61 b 16 58 0 58 0 87 b 24 102 33 87 38 73 l 30 70 m 50 82 l 43 75 b 33 87 24 102 50 116 b 76 102 68 87 57 75 l 50 82 m 70 70 l 62 73 b 68 87 76 102 100 87 b 100 58 84 58 67 61 l 70 70 m 70 46 l 67 55 b 84 58 100 58 100 29 b 76 14 67 29 62 44 l 70 46 m 50 34 l 57 42 b 67 29 76 14 50 0 b 24 14 33 29 43 42 l 50 34 m 30 46 l 38 44 b 33 29 24 14 0 29 b 0 58 16 58 33 55 l 30 46 m 58 34 l 42 34 l 50 21 l 58 34 m 82 40 l 74 53 l 66 40 l 82 40 m 34 40 l 26 53 l 18 40 l 34 40 m 58 82 l 50 95 l 42 82 l 58 82 m 34 76 l 18 76 l 26 63 l 34 76 m 82 76 l 66 76 l 74 63 l 82 76",
    "flower20t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 19 43 b 19 35 31 35 31 43 b 31 51 19 51 19 43 m 19 73 b 19 65 31 65 31 73 b 31 81 19 81 19 73 m 69 43 b 69 35 81 35 81 43 b 81 51 69 51 69 43 m 69 73 b 69 65 81 65 81 73 b 81 81 69 81 69 73 m 44 87 b 44 79 56 79 56 87 b 56 95 44 95 44 87 m 44 28 b 44 20 56 20 56 28 b 56 36 44 36 44 28 m 44 58 b 44 50 56 50 56 58 b 56 66 44 66 44 58 m 0 58 b 0 50 12 50 12 58 b 12 66 0 66 0 58 m 88 58 b 88 50 100 50 100 58 b 100 66 88 66 88 58 m 22 96 b 22 88 34 88 34 96 b 34 104 22 104 22 96 m 66 20 b 66 12 78 12 78 20 b 78 28 66 28 66 20 m 22 20 b 22 12 34 12 34 20 b 34 28 22 28 22 20 m 67 96 b 67 88 79 88 79 96 b 79 104 67 104 67 96",
    "flower21t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 0 58 b 0 50 12 50 12 58 b 12 66 0 66 0 58 m 88 58 b 88 50 100 50 100 58 b 100 66 88 66 88 58 m 22 96 b 22 88 34 88 34 96 b 34 104 22 104 22 96 m 66 20 b 66 12 78 12 78 20 b 78 28 66 28 66 20 m 22 20 b 22 12 34 12 34 20 b 34 28 22 28 22 20 m 67 96 b 67 88 79 88 79 96 b 79 104 67 104 67 96",
    "flower22t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 19 43 b 19 35 31 35 31 43 b 31 51 19 51 19 43 m 19 73 b 19 65 31 65 31 73 b 31 81 19 81 19 73 m 69 43 b 69 35 81 35 81 43 b 81 51 69 51 69 43 m 69 73 b 69 65 81 65 81 73 b 81 81 69 81 69 73 m 44 87 b 44 79 56 79 56 87 b 56 95 44 95 44 87 m 44 28 b 44 20 56 20 56 28 b 56 36 44 36 44 28 m 44 58 b 44 50 56 50 56 58 b 56 66 44 66 44 58",
    "flower23t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 56 48 l 78 42 l 61 58 l 78 75 l 56 67 l 50 88 l 44 67 l 23 75 l 39 58 l 23 42 l 44 48 l 50 28 l 56 48",
    "flower24t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46 m 56 48 l 94 33 l 61 58 l 94 84 l 56 67 l 50 109 l 44 67 l 6 84 l 39 58 l 6 33 l 44 48 l 50 8 l 56 48",
    "flower25t": "m 30 70 l 33 58 b 16 58 0 58 0 87 b 24 102 33 87 41 72 l 30 70 m 50 81 l 41 72 b 33 87 24 102 50 116 b 76 102 68 87 59 72 l 50 81 m 70 70 l 59 72 b 68 87 76 102 100 87 b 100 58 84 58 67 58 l 70 70 m 70 46 l 67 58 b 84 58 100 58 100 29 b 76 14 67 29 59 43 l 70 46 m 50 34 l 59 43 b 67 29 76 14 50 0 b 24 14 33 29 41 43 l 50 34 m 30 46 l 41 43 b 33 29 24 14 0 29 b 0 58 16 58 33 58 l 30 46",
    "flower26t": "m 50 55 b 33 98 44 110 50 110 b 54 110 64 98 50 55 b 78 88 95 86 97 83 b 100 79 94 63 50 55 b 6 63 0 79 2 83 b 4 86 21 88 50 55 b 21 23 4 25 2 28 b 0 31 6 46 50 55 b 94 46 100 31 97 28 b 95 25 78 23 50 55 b 64 14 53 0 50 0 b 45 0 33 14 50 55 m 100 55 b 100 42 83 42 83 55 b 83 68 100 68 100 55 m 17 55 b 17 42 0 42 0 55 b 0 68 17 68 17 55 m 78 91 b 78 78 61 78 61 91 b 61 103 78 103 78 91 m 37 91 b 37 78 20 78 20 91 b 20 103 37 103 37 91 m 78 19 b 78 7 61 7 61 19 b 61 32 78 32 78 19 m 37 19 b 37 7 20 7 20 19 b 20 32 37 32 37 19 m 62 55 b 62 38 38 38 38 55 b 38 72 62 72 62 55",
    "flower27t": "m 50 55 b 35 98 45 110 50 110 b 55 110 65 98 50 55 b 79 88 96 87 98 83 b 100 80 95 63 50 55 b 7 63 0 80 2 83 b 4 87 21 88 50 55 b 21 23 4 25 2 28 b 0 31 7 47 50 55 b 95 47 100 31 98 28 b 96 25 79 23 50 55 b 65 14 55 0 50 0 b 45 0 35 14 50 55 m 62 55 b 62 38 38 38 38 55 b 38 72 62 72 62 55",
    "flower28t": "m 50 55 b 35 98 45 110 50 110 b 55 110 65 98 50 55 b 79 88 96 87 98 83 b 100 80 95 63 50 55 b 7 63 0 80 2 83 b 4 87 21 88 50 55 b 21 23 4 25 2 28 b 0 31 7 47 50 55 b 95 47 100 31 98 28 b 96 25 79 23 50 55 b 65 14 55 0 50 0 b 45 0 35 14 50 55",
    "flower29t": "m 50 55 b 33 98 44 110 50 110 b 54 110 64 98 50 55 b 78 88 95 86 97 83 b 100 79 94 63 50 55 b 6 63 0 79 2 83 b 4 86 21 88 50 55 b 21 23 4 25 2 28 b 0 31 6 46 50 55 b 94 46 100 31 97 28 b 95 25 78 23 50 55 b 64 14 53 0 50 0 b 45 0 33 14 50 55 m 100 55 b 100 42 83 42 83 55 b 83 68 100 68 100 55 m 17 55 b 17 42 0 42 0 55 b 0 68 17 68 17 55 m 78 91 b 78 78 61 78 61 91 b 61 103 78 103 78 91 m 37 91 b 37 78 20 78 20 91 b 20 103 37 103 37 91 m 78 19 b 78 7 61 7 61 19 b 61 32 78 32 78 19 m 37 19 b 37 7 20 7 20 19 b 20 32 37 32 37 19",
    "crystal17": "m 56 50 l 64 100 l 38 78 l 56 50 m 56 50 l 24 100 l 0 65 l 56 50 m 56 50 l 0 65 l 28 39 l 56 50 m 56 50 l 31 0 l 0 28 l 56 50 m 56 50 l 78 0 l 42 22 l 56 50 m 56 50 l 100 40 l 68 23 l 56 50 m 56 50 l 100 40 l 61 80 l 56 50 m 100 40 l 61 80 l 56 50 m 100 40 l 77 64 l 100 100 l 100 40 m 61 80 l 100 100 l 77 64 l 61 80 m 61 80 l 64 100 l 100 100 l 61 80 m 38 78 l 24 100 l 64 100 l 38 78 m 0 65 l 0 100 l 24 100 l 0 65 m 0 28 l 0 65 l 28 39 l 0 28 m 31 0 l 0 0 l 0 28 l 31 0 m 78 0 l 31 0 l 42 22 l 78 0 m 100 0 l 68 23 l 100 40 l 100 0 m 100 0 l 78 0 l 68 23 l 100 0",
    "geometric10": "m 0 50 l 0 100 l 100 100 l 100 50 l 90 50 l 90 90 l 10 90 l 10 50 l 0 50 m 0 50 l 10 50 l 10 10 l 90 10 l 90 50 l 100 50 l 100 0 l 0 0 l 0 50 m 50 90 l 50 80 l 20 80 l 20 20 l 50 20 l 50 10 l 10 10 l 10 90 l 50 90 m 50 90 l 90 90 l 90 10 l 50 10 l 50 20 l 80 20 l 80 80 l 50 80 l 50 90 m 20 50 l 20 80 l 80 80 l 80 50 l 70 50 l 70 70 l 30 70 l 30 50 l 20 50 m 20 50 l 30 50 l 30 30 l 70 30 l 70 50 l 80 50 l 80 20 l 20 20 l 20 50 m 50 70 l 50 60 l 40 60 l 40 40 l 50 40 l 50 30 l 30 30 l 30 70 l 50 70 m 50 70 l 70 70 l 70 30 l 50 30 l 50 40 l 60 40 l 60 60 l 50 60 l 50 70 m 40 50 l 40 60 l 60 60 l 60 50 l 40 50 m 40 50 l 60 50 l 60 40 l 40 40 l 40 50",
    "diagonal13r": "m 15 0 l 0 0 l 0 15 l 15 0 m 15 0 l 0 15 l 0 30 l 30 0 l 15 0 m 30 0 l 0 30 l 0 45 l 45 0 l 30 0 m 45 0 l 0 45 l 0 60 l 60 0 l 45 0 m 60 0 l 0 60 l 0 75 l 75 0 l 60 0 m 75 0 l 0 75 l 0 90 l 90 0 l 75 0 m 90 0 l 0 90 l 0 100 l 5 100 l 100 5 l 100 0 l 90 0 m 100 5 l 5 100 l 20 100 l 100 20 l 100 5 m 100 20 l 20 100 l 35 100 l 100 35 l 100 20 m 100 35 l 35 100 l 50 100 l 100 50 l 100 35 m 100 50 l 50 100 l 65 100 l 100 65 l 100 50 m 100 65 l 65 100 l 80 100 l 100 80 l 100 65 m 100 80 l 80 100 l 100 100 l 100 80",
    "diagonal13l": "m 0 85 l 0 100 l 15 100 l 0 85 m 0 85 l 15 100 l 30 100 l 0 70 l 0 85 m 0 70 l 30 100 l 45 100 l 0 55 l 0 70 m 0 55 l 45 100 l 60 100 l 0 40 l 0 55 m 0 40 l 60 100 l 75 100 l 0 25 l 0 40 m 0 25 l 75 100 l 90 100 l 0 10 l 0 25 m 0 10 l 90 100 l 100 100 l 100 95 l 5 0 l 0 0 l 0 10 m 5 0 l 100 95 l 100 80 l 20 0 l 5 0 m 20 0 l 100 80 l 100 65 l 35 0 l 20 0 m 35 0 l 100 65 l 100 50 l 50 0 l 35 0 m 50 0 l 100 50 l 100 35 l 65 0 l 50 0 m 65 0 l 100 35 l 100 20 l 80 0 l 65 0 m 80 0 l 100 20 l 100 0 l 80 0"
}

SHAPES_LIB_MAP = {k: (lambda ctx=None, p=v: p) for k, v in RAW_PRESET_SHAPES.items()}

def resolve_shape_value(shp_val, context=None):
    """Resuelve cualquier referencia a forma vectorial, incluyendo sintaxis 'shape.<nombre>' o nombres directos de la biblioteca."""
    if isinstance(shp_val, (list, tuple)):
        return [resolve_shape_value(item, context) for item in shp_val if item is not None and str(item).strip() != ""]

    if isinstance(shp_val, str) and shp_val.strip().startswith("[") and shp_val.strip().endswith("]"):
        try:
            import json as _json
            parsed = _json.loads(shp_val)
            if isinstance(parsed, list):
                return [resolve_shape_value(item, context) for item in parsed if item is not None and str(item).strip() != ""]
        except Exception:
            pass

    if not shp_val or str(shp_val).strip() == "":
        unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
        line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
        txt = ""
        if unit:
            txt = getattr(unit, 'text_stripped', getattr(unit, 'text', ''))
        elif line:
            txt = getattr(line, 'text_stripped', getattr(line, 'text', ''))
        if not txt:
            return ""
        shp_val = txt

    s_val = str(shp_val).strip()
    shape_name = s_val[6:].strip() if s_val.startswith("shape.") else s_val

    if shape_name in RAW_PRESET_SHAPES:
        return RAW_PRESET_SHAPES[shape_name]

    if s_val.startswith("shape."):
        return ""

    if s_val.startswith("m ") or s_val.startswith("m-") or s_val.startswith("m0"):
        return s_val

    try:
        from font_vector_engine import FontVectorEngine
        v_shp = FontVectorEngine.from_context(text=s_val, context=context)
        if v_shp and (v_shp.strip().startswith("m ") or v_shp.strip().startswith("m-") or v_shp.strip().startswith("m0")):
            return v_shp
        if v_shp and v_shp.strip():
            return v_shp
    except Exception:
        pass

    return s_val


def get_drawing_bbox(drawing_or_list):
    """Calculates (min_x, min_y, max_x, max_y) bounding box of one or more ASS vector drawings."""
    if not drawing_or_list:
        return None
    drawings = drawing_or_list if isinstance(drawing_or_list, (list, tuple)) else [drawing_or_list]
    all_xs = []
    all_ys = []
    for d in drawings:
        if not d or not isinstance(d, str):
            continue
        tokens = d.split()
        coords = []
        for token in tokens:
            try:
                coords.append(float(token))
            except ValueError:
                pass
        if coords and len(coords) >= 2:
            all_xs.extend(coords[0::2])
            all_ys.extend(coords[1::2])
    if all_xs and all_ys:
        return (min(all_xs), min(all_ys), max(all_xs), max(all_ys))
    return None


def apply_geometric_anchor(drawing, anchor="center", context=None, ref_bbox=None):
    """Relocates an ASS vector shape according to geometric anchor mode:
      - 'center': Centra el shape alrededor de (0,0) [Center] (usando ref_bbox si se provee, preservando la posición relativa de sub-piezas).
      - 'origin': Alinea la esquina superior izquierda del bounding box a (0,0) [Origin] (usando ref_bbox si se provee).
      - 'zero': Traslada el shape a las coordenadas de pantalla/canvas (pos_x, pos_y) [0,0].
      - 'pos': Hace el shape relativo a la posición (pos_x, pos_y) [Pos].
      - 'piece' / 'pieza' / 'local': Centra individualmente la pieza en (0,0) ignorando ref_bbox [Pieza].
    """
    if not drawing or not str(drawing).strip():
        return ""
    anchor_str = str(anchor or "center").strip().lower()

    tokens = str(drawing).split()
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

    if ref_bbox is not None and anchor_str != "pieces":
        if isinstance(ref_bbox, dict):
            min_x = float(ref_bbox.get("x1", ref_bbox.get("min_x", ref_bbox.get(0, min_x))))
            min_y = float(ref_bbox.get("y1", ref_bbox.get("min_y", ref_bbox.get(1, min_y))))
            max_x = float(ref_bbox.get("x2", ref_bbox.get("max_x", ref_bbox.get(2, max_x))))
            max_y = float(ref_bbox.get("y2", ref_bbox.get("max_y", ref_bbox.get(3, max_y))))
        elif isinstance(ref_bbox, (list, tuple)) and len(ref_bbox) >= 4:
            min_x, min_y, max_x, max_y = float(ref_bbox[0]), float(ref_bbox[1]), float(ref_bbox[2]), float(ref_bbox[3])
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
    elif anchor_str == "absolute":
        ref_x, ref_y = 0.0, 0.0
        base_x, base_y = pos_x, pos_y
    elif anchor_str == "pos":
        ref_x, ref_y = pos_x, pos_y
        base_x, base_y = 0.0, 0.0
    elif anchor_str == "relative":
        ref_x, ref_y = 0.0, 0.0
        base_x, base_y = 0.0, 0.0
    elif anchor_str == "pieces":
        ref_x, ref_y = cx, cy
        base_x, base_y = 0.0, 0.0
    else:  # "center" fallback
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
                    rel_x = (x_val - ref_x) + base_x
                    rel_y = (y_val - ref_y) + base_y
                    out_tokens.append(f"{rel_x:.2f}".rstrip('0').rstrip('.'))
                    out_tokens.append(f"{rel_y:.2f}".rstrip('0').rstrip('.'))
                    i += 2
                    continue
                except ValueError:
                    pass
            out_tokens.append(token)
            i += 1
        except ValueError:
            out_tokens.append(token)
            i += 1
    return " ".join(out_tokens)


def eval_shapes_lib_node(context=None, **kwargs):
    """Manejador unificado para Shape/Library con las 80 formas canónicas."""
    shape_name = str(kwargs.get("shape", "circle")).strip()
    if shape_name.startswith("shape."):
        shape_name = shape_name[6:].strip()
    return RAW_PRESET_SHAPES.get(shape_name, "")

NODE_REGISTRY["Shape/Library"] = eval_shapes_lib_node


def parse_assdraw_segments(shape_str):
    """Parsea comandos ASSdraw (m, l, b, c) en una lista de contornos con segmentos estructurados con caché LRU."""
    if not shape_str or not str(shape_str).strip():
        return []

    cache_key = str(shape_str).strip()
    if cache_key in _PARSE_SEGMENTS_CACHE:
        cached = _PARSE_SEGMENTS_CACHE[cache_key]
        _PARSE_SEGMENTS_CACHE.move_to_end(cache_key)
        return [
            {
                'start': c['start'],
                'segments': [dict(s) for s in c['segments']]
            }
            for c in cached
        ]

    tokens = cache_key.split()
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
            if cmd == 'c' and (idx + 1 >= num_tokens or tokens[idx + 1].isalpha()):
                # Close figure
                if current_contour and current_contour.get('start'):
                    start_pt = current_contour['start']
                    if math.hypot(curr_pt[0] - start_pt[0], curr_pt[1] - start_pt[1]) > 1e-4:
                        current_contour['segments'].append({
                            'type': 'l',
                            'p0': (curr_pt[0], curr_pt[1]),
                            'p1': (start_pt[0], start_pt[1])
                        })
                        curr_pt = [start_pt[0], start_pt[1]]
                idx += 1
                continue
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

    if len(_PARSE_SEGMENTS_CACHE) >= _PARSE_SEGMENTS_MAX_CACHE:
        _PARSE_SEGMENTS_CACHE.popitem(last=False)
    _PARSE_SEGMENTS_CACHE[cache_key] = contours

    return [
        {
            'start': c['start'],
            'segments': [dict(s) for s in c['segments']]
        }
        for c in contours
    ]


def _eval_bezier_pt(p0, p1, p2, p3, u):
    """Evaluates a point on a cubic Bézier curve for parameter u in [0, 1]."""
    om = 1.0 - u
    om2 = om * om
    om3 = om2 * om
    u2 = u * u
    u3 = u2 * u
    x = om3 * p0[0] + 3.0 * om2 * u * p1[0] + 3.0 * om * u2 * p2[0] + u3 * p3[0]
    y = om3 * p0[1] + 3.0 * om2 * u * p1[1] + 3.0 * om * u2 * p2[1] + u3 * p3[1]
    return (x, y)


def _eval_bezier_tangent(p0, p1, p2, p3, u):
    """Evaluates tangent vector (dx, dy) of a cubic Bézier curve at u."""
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
    """Calculates real arc length of a segment (line or cubic Bézier)."""
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
    """Maps accumulated distance to analytical parameter u in [0, 1] on a Bézier curve."""
    tot = chord_lens[-1]
    if tot <= 1e-9 or dist <= 0.0:
        return 0.0
    if dist >= tot:
        return 1.0

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
        b01 = (p0[0] * (1.0 - u) + p1[0] * u, p0[1] * (1.0 - u) + p1[1] * u)
        b12 = (p1[0] * (1.0 - u) + p2[0] * u, p1[1] * (1.0 - u) + p2[1] * u)
        b23 = (p2[0] * (1.0 - u) + p3[0] * u, p2[1] * (1.0 - u) + p3[1] * u)
        b012 = (b01[0] * (1.0 - u) + b12[0] * u, b01[1] * (1.0 - u) + b12[1] * u)
        b123 = (b12[0] * (1.0 - u) + b23[0] * u, b12[1] * (1.0 - u) + b23[1] * u)
        b0123 = (b012[0] * (1.0 - u) + b123[0] * u, b012[1] * (1.0 - u) + b123[1] * u)

        dx, dy = _eval_bezier_tangent(p0, p1, p2, p3, u)
        left_seg = {'type': 'b', 'p0': p0, 'p1': b01, 'p2': b012, 'p3': b0123}
        right_seg = {'type': 'b', 'p0': b0123, 'p1': b123, 'p2': b23, 'p3': p3}
        return left_seg, right_seg, b0123, (dx, dy)

    p0 = seg.get('p0', (0.0, 0.0))
    return seg, seg, p0, (1.0, 0.0)


def _cut_segment_interval(seg, u_start, u_end, subdivs=30):
    """Trims a segment keeping only section [u_start, u_end]."""
    u_start = max(0.0, min(1.0, float(u_start)))
    u_end = max(0.0, min(1.0, float(u_end)))

    if u_start >= u_end:
        p0 = seg.get('p0', (0.0, 0.0))
        return None, p0, (1.0, 0.0)

    cur_seg = seg
    tip_p = cur_seg.get('p1' if cur_seg['type'] == 'l' else 'p3', (0.0, 0.0))
    tan = (1.0, 0.0)

    if u_end < 0.999999:
        left_s, _, tip_p, tan = de_casteljau_split(cur_seg, u_end)
        cur_seg = left_s
    else:
        _, _, tip_p, tan = de_casteljau_split(cur_seg, 1.0)

    if u_start > 0.000001:
        u_eff = u_start / u_end if u_end > 1e-9 else 0.0
        _, right_s, _, _ = de_casteljau_split(cur_seg, u_eff)
        cur_seg = right_s

    return cur_seg, tip_p, tan


def _format_num(val):
    """Formats floating-point numbers compactly for ASSdraw."""
    f = float(val)
    if f.is_integer():
        return str(int(f))
    return f"{f:.2f}".rstrip('0').rstrip('.')



def shape_walker_core(shape_str, progress=1.0, start_t=0.0, mode="Global", invert=False, subdivs=30, close_path=False):
    """Parametric vector arc length traversal core for ASSdraw.
    
    Parámetros:
      - shape_str: Código vectorial ASSdraw (m ...).
      - progress: Progreso de finalización (0.0 a 1.0).
      - start_t: Progreso de inicio (0.0 a 1.0).
      - mode: 'Global' (Continuo en todos los contornos) o 'Por Contorno' (Paralelo por glifo/trazo).
      - invert: Invierte el sentido del recorte.
      - subdivs: Pasos de resolución para integración Bézier.
      - close_path: Si es True, cierra automáticamente contornos abiertos añadiendo un segmento de retorno al inicio.
    
    Retorna: (ass_draw_out, tip_x, tip_y, angle_deg, current_length, total_length)
    """
    if not shape_str or not str(shape_str).strip():
        return "", 0.0, 0.0, 0.0, 0.0, 0.0

    raw_shape_str = str(shape_str).strip()
    sub = max(5, int(subdivs))
    is_close = bool(close_path)
    cache_key = (raw_shape_str, sub, is_close)

    if cache_key in _WALKER_PARAM_CACHE:
        cached = _WALKER_PARAM_CACHE[cache_key]
        _WALKER_PARAM_CACHE.move_to_end(cache_key)
        contour_data = cached['contours']
        total_shape_len = cached['total_length']
        start_p0 = cached['start_p0']
    else:
        contours = parse_assdraw_segments(raw_shape_str)
        if not contours:
            return "", 0.0, 0.0, 0.0, 0.0, 0.0

        if is_close:
            for c in contours:
                if c['segments']:
                    last_seg = c['segments'][-1]
                    last_pt = last_seg['p1'] if last_seg['type'] == 'l' else last_seg['p3']
                    start_pt = c['start']
                    if math.hypot(last_pt[0] - start_pt[0], last_pt[1] - start_pt[1]) > 1e-4:
                        c['segments'].append({
                            'type': 'l',
                            'p0': (last_pt[0], last_pt[1]),
                            'p1': (start_pt[0], start_pt[1])
                        })

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

        start_p0 = contours[0]['start'] if contours else (0.0, 0.0)

        if len(_WALKER_PARAM_CACHE) >= _WALKER_PARAM_MAX_CACHE:
            _WALKER_PARAM_CACHE.popitem(last=False)
        _WALKER_PARAM_CACHE[cache_key] = {
            'contours': contour_data,
            'total_length': total_shape_len,
            'start_p0': start_p0
        }

    if total_shape_len <= 1e-9:
        p0 = start_p0
        return f"m {_format_num(p0[0])} {_format_num(p0[1])} ", p0[0], p0[1], 0.0, 0.0, 0.0

    t0 = max(0.0, min(1.0, float(start_t)))
    t1 = max(0.0, min(1.0, float(progress)))

    if invert:
        t0_eff = 1.0 - t1
        t1_eff = 1.0 - t0
        t0, t1 = t0_eff, t1_eff

    if t0 >= t1:
        return "", 0.0, 0.0, 0.0, 0.0, total_shape_len

    mode_str = str(mode).strip().lower()
    is_per_contour = "contorno" in mode_str or "paralel" in mode_str or "parallel" in mode_str or "outline" in mode_str or "glyph" in mode_str or "letter" in mode_str or "piece" in mode_str or "contour" in mode_str

    out_tokens = []
    tip_pt = (0.0, 0.0)
    tip_tangent = (1.0, 0.0)
    current_cut_len = 0.0

    if not is_per_contour:
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
    mode="global",
    invert=False,
    subdivs=30,
    close_path=False
):
    r"""Shape Walker Node (Parametric Arc-Length Trimming / Write-on).
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

    if not shp_val:
        return "", "", 0.0, 0.0, 0.0, 0.0

    p_val = _eval_num_expr(progress, context, 1.0)
    s_val = _eval_num_expr(start_t, context, 0.0)
    sub_val = int(_eval_num_expr(subdivs, context, 30.0))

    if isinstance(invert, (int, float, bool)):
        inv_bool = bool(invert)
    else:
        inv_str = str(invert).strip().lower()
        if inv_str in ("1", "true", "yes", "si", "sí", "invertido", "invert", "inverted"):
            inv_bool = True
        elif inv_str in ("0", "false", "no", "normal", "0.0", ""):
            inv_bool = False
        else:
            try:
                inv_eval = _eval_num_expr(invert, context, 0.0)
                inv_bool = bool(float(inv_eval) > 0.5)
            except Exception:
                inv_bool = False

    if isinstance(close_path, (int, float, bool)):
        close_bool = bool(close_path)
    else:
        close_str = str(close_path).strip().lower()
        if close_str in ("1", "true", "yes", "si", "sí", "cerrar", "closed", "close"):
            close_bool = True
        elif close_str in ("0", "false", "no", "abierto", "open", "0.0", ""):
            close_bool = False
        else:
            try:
                close_eval = _eval_num_expr(close_path, context, 0.0)
                close_bool = bool(float(close_eval) > 0.5)
            except Exception:
                close_bool = False

    mode_str = str(mode).strip()

    final_shp, tx, ty, angle, cut_len, _ = shape_walker_core(
        shp_val,
        progress=p_val,
        start_t=s_val,
        mode=mode_str,
        invert=inv_bool,
        subdivs=sub_val,
        close_path=close_bool
    )

    parent_x = 0.0
    parent_y = 0.0
    if isinstance(context, dict) and ('fx_pos_x' in context or 'pos_x' in context):
        try:
            parent_x = float(context.get('fx_pos_x', context.get('pos_x', 0.0)))
        except (ValueError, TypeError):
            parent_x = 0.0
    elif unit is not None:
        try:
            parent_x = float(getattr(unit, 'center', getattr(unit, 'x', 0.0)))
        except (ValueError, TypeError):
            parent_x = 0.0
    elif line is not None:
        try:
            parent_x = float(getattr(line, 'center', getattr(line, 'x', 0.0)))
        except (ValueError, TypeError):
            parent_x = 0.0

    if isinstance(context, dict) and ('fx_pos_y' in context or 'pos_y' in context):
        try:
            parent_y = float(context.get('fx_pos_y', context.get('pos_y', 0.0)))
        except (ValueError, TypeError):
            parent_y = 0.0
    elif unit is not None:
        try:
            parent_y = float(getattr(unit, 'middle', getattr(unit, 'y', 0.0)))
        except (ValueError, TypeError):
            parent_y = 0.0
    elif line is not None:
        try:
            parent_y = float(getattr(line, 'middle', getattr(line, 'y', 0.0)))
        except (ValueError, TypeError):
            parent_y = 0.0

    abs_x = round(parent_x + float(tx), 2)
    abs_y = round(parent_y + float(ty), 2)

    pos_str = f"\\pos({_format_num(abs_x)},{_format_num(abs_y)})" if (abs_x != 0 or abs_y != 0) else ""

    return final_shp, pos_str, round(angle, 2), round(cut_len, 2), abs_x, abs_y


NODE_REGISTRY["Shape/Walker"] = shape_walker_node
NODE_REGISTRY["Walker"] = shape_walker_node
NODE_REGISTRY["Shape/Walker"] = shape_walker_node
NODE_REGISTRY["Walker"] = shape_walker_node


def shape_stroke_node(
    context=None,
    shape="",
    width=4.0,
    join_mode="round",
    cap_mode="bezier",
    miter_limit=2.0
):
    """Shape Stroke Node / Outlined Stroke (Paridad 100% con ke.shape.line / shape:offset).
    Convierte cualquier línea, spline abierta o contorno cerrado en un polígono ASSDraw cerrado con grosor real.
    """
    from node_engine import _eval_num_expr
    from clipper_engine import ClipperEngine

    unit = context.get('active_unit') if isinstance(context, dict) else None
    if not unit and isinstance(context, dict):
        unit = context.get('char') or context.get('syl') or context.get('word')
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
    if not line and unit and hasattr(unit, 'line'):
        line = getattr(unit, 'line', None)

    shp_val = resolve_shape_value(shape, context)
    if not shp_val or not shp_val.strip():
        return ""

    w_val = max(0.01, _eval_num_expr(width, context, 4.0))
    miter_val = max(1.0, _eval_num_expr(miter_limit, context, 2.0))
    jm_str = str(join_mode).strip()
    cm_str = str(cap_mode).strip()

    return ClipperEngine.stroke_shape(
        shp_val,
        width=w_val,
        join_mode=jm_str,
        cap_mode=cm_str,
        miter_limit=miter_val
    )


NODE_REGISTRY["Shape/Stroke"] = shape_stroke_node
NODE_REGISTRY["Stroke"] = shape_stroke_node
NODE_REGISTRY["Shape/Stroke"] = shape_stroke_node
NODE_REGISTRY["Stroke"] = shape_stroke_node


_GLOBAL_SHAPE_ARRAY_CACHE = OrderedDict()
_GLOBAL_SHAPE_ARRAY_MAX_CACHE = 512

def clear_shape_array_caches():
    """Clears global formations and arrays cache for Shape Array."""
    _GLOBAL_SHAPE_ARRAY_CACHE.clear()


_GLOBAL_MULTI_GRID_CACHE = OrderedDict()
_GLOBAL_MULTI_GRID_MAX_CACHE = 512

def clear_multi_caches():
    """Clears global grid and sorting cache for Shape Multi."""
    _GLOBAL_MULTI_GRID_CACHE.clear()


def clear_all_shape_caches():
    """Clears all shape-related geometry, bbox, redraw, and array caches."""
    _SHAPE_BBOX_CACHE.clear()
    _PARSE_SEGMENTS_CACHE.clear()
    _WALKER_PARAM_CACHE.clear()
    _CONCENTRIC_RINGS_CACHE.clear()
    _SHAPE_REDRAW_CACHE.clear()
    _GLOBAL_SHAPE_ARRAY_CACHE.clear()
    _GLOBAL_MULTI_GRID_CACHE.clear()


def point_in_contour_vectorized(points_x, points_y, contour):
    """Fast vectorized point-in-polygon test (Ray-Casting in NumPy)."""
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
    mode="grid",
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
    anchor="pieces",
    order="79",
    out_mode="loops",
    active_index=1,
    parent_x=0.0,
    parent_y=0.0,
    context=None
):
    """Geometric calculation and generation engine for Shape Array.
    Soporta modos Grid, Formation, Rings, Spiral, Scatter y Hex,
    con dimensionamiento previo, ordenamiento Numpad y anclaje local o relativo."""
    if context is None:
        context = {}

    mode_clean = str(mode or "grid").strip().lower()
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
        r_shp = resolve_shape_value(p_str, context)
        if not r_shp or not r_shp.strip():
            r_shp = "m 0 0 l 10 0 l 10 10 l 0 10"
        resolved_particles.append(r_shp)

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

        norm_shp = shape_manipulator(context, drawing=p_shp, scale_x=sx, scale_y=sy, mode="center")
        prepared_particles.append(norm_shp)
        eff_widths.append(pw * sx)
        eff_heights.append(ph * sy)

    max_eff_w = max(eff_widths) if eff_widths else 10.0
    max_eff_h = max(eff_heights) if eff_heights else 10.0

    raw_items = []

    if "form" in mode_clean or "guia" in mode_clean:
        f_shp = resolve_shape_value(formation, context)
        if not f_shp or not f_shp.strip():
            f_shp = "m 0 0 l 100 0 l 100 100 l 0 100"

        f_cnts = ClipperEngine.parse_assdraw(f_shp)
        f_min_x, f_min_y, f_max_x, f_max_y, fcx, fcy, fw, fh = ClipperEngine.get_bbox(f_cnts)

        f_scale_x = (target_w / fw) if (target_w > 0 and fw > 0) else 1.0
        f_scale_y = (target_h / fh) if (target_h > 0 and fh > 0) else 1.0
        if f_scale_x != 1.0 or f_scale_y != 1.0:
            f_cnts = [np.column_stack(((c[:, 0] - fcx) * f_scale_x + fcx, (c[:, 1] - fcy) * f_scale_y + fcy)) for c in f_cnts]
            f_min_x, f_min_y, f_max_x, f_max_y, fcx, fcy, fw, fh = ClipperEngine.get_bbox(f_cnts)

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

                rel_x = gx - fcx
                rel_y = gy - fcy

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
        n_rings = max(1, int(float(rings)) if rings not in ("", None) else 3)
        base_r = float(radius) if radius not in ("", None) else 50.0
        dr = float(radius_step) if radius_step not in ("", None) else 30.0
        d_rot = float(rotate_step) if rotate_step not in ("", None) else 0.0
        eff_diam = max(1.0, max(max_eff_w, max_eff_h))

        counts_list = []
        if count_per_ring not in ("", None):
            if isinstance(count_per_ring, (list, tuple)):
                counts_list = [max(1, int(float(v))) for v in count_per_ring if str(v).strip()]
            else:
                s_c = str(count_per_ring).strip()
                if "," in s_c:
                    counts_list = [max(1, int(float(v.strip()))) for v in s_c.split(",") if v.strip()]
                else:
                    try:
                        counts_list = [max(1, int(float(s_c)))]
                    except Exception:
                        counts_list = []

        eff_step = max(1.0, eff_diam + sp_val)
        for k in range(n_rings):
            cur_r = base_r + k * dr
            if counts_list:
                nk = counts_list[k % len(counts_list)]
            else:
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

    sorted_items = sort_particles(raw_items, order_code=order, get_xy=lambda it: (it["x"], it["y"]))

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
    t=1.0,
    anchor="pieces",
    order="79",
    mode="grid",
    out_mode="loops",
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
    tags="",
    **kwargs
):
    r"""Shape Array Node: High-throughput vector formations and arrays.
    Soporta modos Loops (con contadores a_i y a_n) y Shape (dibujo monolítico) con factor t de progreso y fusión de tags.
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
    if isinstance(context, dict) and context.get('pos_overridden'):
        parent_x = float(context.get('pos_x', parent_x))
        parent_y = float(context.get('pos_y', parent_y))

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
    anchor_mode = str(anchor or "pieces").strip().lower()

    try:
        t_val = float(t) if t not in ("", None) else 1.0
    except Exception:
        t_val = 1.0
    t_clamped = max(0.0, min(1.0, t_val))
    visible_count = max(0, int(round(total_pieces * t_clamped)))

    if "shape" in out_mode_clean and "loop" not in out_mode_clean:
        if isinstance(context, dict):
            context['a_i'] = 1
            context['a_n'] = 1
            context['a_max'] = 1
            context['maxloop'] = 1

        if visible_count <= 0:
            pos_str = f"\\pos({parent_x:.2f},{parent_y:.2f})".rstrip('0').rstrip('.') if (parent_x != 0 or parent_y != 0) else ""
            return "", pos_str, round(parent_x, 2), round(parent_y, 2), 0.0, 0, total_pieces, 1, 1

        active_pieces = pieces[:visible_count]
        piece_drawings = []
        for p in active_pieces:
            anc_res = resolve_piece_anchor(p["code"], piece_cx=p["cx"], piece_cy=p["cy"], parent_x=parent_x, parent_y=parent_y, anchor=anchor_mode, context=context)
            piece_drawings.append(anc_res["formatted_code"])

        tags_val = tags if tags else (kwargs.get("tag") or "")
        if tags_val and str(tags_val).strip():
            from clipper_engine import ClipperEngine
            combined_code = ClipperEngine.fusion_shapes_tags(piece_drawings, tags=tags_val)
        else:
            combined_code = " ".join(piece_drawings)

        pos_str = f"\\pos({parent_x:.2f},{parent_y:.2f})".rstrip('0').rstrip('.') if (parent_x != 0 or parent_y != 0) else ""
        return combined_code, pos_str, round(parent_x, 2), round(parent_y, 2), 0.0, 1, total_pieces, 1, 1

    if isinstance(context, dict):
        context['a_n'] = total_pieces
        context['a_max'] = total_pieces
        context['maxloop'] = total_pieces

    a_i_val = int(float(context.get('a_i', context.get('j', context.get('fx_i', context.get('i', 1)))))) if isinstance(context, dict) else 1
    
    if visible_count <= 0 or a_i_val > visible_count:
        pos_str = f"\\pos({parent_x:.2f},{parent_y:.2f})".rstrip('0').rstrip('.') if (parent_x != 0 or parent_y != 0) else ""
        return "", pos_str, round(parent_x, 2), round(parent_y, 2), 0.0, a_i_val, total_pieces, 1, 1

    idx = max(0, min(a_i_val - 1, total_pieces - 1))
    piece = pieces[idx]

    cx = piece["cx"]
    cy = piece["cy"]
    ang = piece["angle"]
    col_val = piece["col"]
    row_val = piece["row"]

    anc_res = resolve_piece_anchor(piece["code"], piece_cx=cx, piece_cy=cy, parent_x=parent_x, parent_y=parent_y, anchor=anchor_mode, context=context)
    piece_code = anc_res["formatted_code"]
    px = round(anc_res["pos_x"], 2)
    py = round(anc_res["pos_y"], 2)

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


NODE_REGISTRY["Shape/Array"] = shape_array_node
NODE_REGISTRY["Array"] = shape_array_node
NODE_REGISTRY["Shape/Array"] = shape_array_node
NODE_REGISTRY["Array"] = shape_array_node



def _split_shape_contours(raw_shp):
    """Separa un dibujo ASS en sus subcontornos independientes (piezas que inician con 'm')."""
    if not raw_shp or not str(raw_shp).strip():
        return []
    tokens = str(raw_shp).strip().split()
    contours = []
    current_tokens = []
    for tok in tokens:
        if tok.lower() == 'm' and current_tokens:
            contours.append(" ".join(current_tokens) + " ")
            current_tokens = [tok]
        else:
            current_tokens.append(tok)
    if current_tokens:
        contours.append(" ".join(current_tokens) + " ")
    return contours


def _shape_filter_vertices(drawing, expr_x="x", expr_y="y", t=1.0, subdivs=0, context=None):
    """Vertices Mode: Evaluates analytical mathematical expressions for each vertex.
    Soporta Factor (t) para interpolación progresiva y subdivisión previa.
    """
    raw_shp = resolve_shape_value(drawing, context)
    if not raw_shp:
        return ""

    from node_engine import _eval_num_expr
    try:
        t_val = float(_eval_num_expr(t, context, 1.0))
    except Exception:
        t_val = 1.0

    try:
        sub_val = float(_eval_num_expr(subdivs, context, 0.0))
    except Exception:
        sub_val = 0.0

    if sub_val > 0:
        raw_shp = _shape_redraw_bezier(raw_shp, factor=sub_val, context=context)

    all_coords = []
    tokens = raw_shp.strip().split()
    cmd = None
    i = 0
    n_tok = len(tokens)
    coord_indices = []

    while i < n_tok:
        tok = tokens[i]
        tok_lower = tok.lower()
        if tok_lower in ('m', 'l', 'b', 'c'):
            cmd = tok_lower
            i += 1
            continue
        if i + 1 < n_tok:
            try:
                x_val = float(tokens[i])
                y_val = float(tokens[i + 1])
                coord_indices.append((i, i + 1, x_val, y_val))
                all_coords.append((x_val, y_val))
                i += 2
                continue
            except ValueError:
                pass
        i += 1

    if not all_coords:
        return raw_shp

    min_x = min(pt[0] for pt in all_coords)
    max_x = max(pt[0] for pt in all_coords)
    min_y = min(pt[1] for pt in all_coords)
    max_y = max(pt[1] for pt in all_coords)
    width = max(1e-6, max_x - min_x)
    height = max(1e-6, max_y - min_y)
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    total_pts = len(all_coords)

    base_env = {
        "cx": cx, "cy": cy, "Cx": cx, "Cy": cy,
        "width": width, "height": height,
        "minx": min_x, "miny": min_y,
        "maxx": max_x, "maxy": max_y,
        "n": total_pts, "Pn": total_pts,
        "t": t_val,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "asin": math.asin, "acos": math.acos, "atan2": math.atan2,
        "rad": math.radians, "deg": math.degrees,
        "pi": math.pi, "PI": math.pi,
        "sqrt": math.sqrt, "abs": abs,
        "min": min, "max": max,
        "exp": math.exp, "log": math.log,
        "floor": math.floor, "ceil": math.ceil, "round": round
    }
    if isinstance(context, dict):
        for k, v in context.items():
            if k not in base_env and isinstance(v, (int, float, str)):
                try:
                    base_env[k] = float(v)
                except Exception:
                    pass

    str_expr_x = str(expr_x).strip() if expr_x not in (None, "") else "x"
    str_expr_y = str(expr_y).strip() if expr_y not in (None, "") else "y"

    out_tokens = list(tokens)
    for k_idx, (idx_x, idx_y, x, y) in enumerate(coord_indices):
        k = k_idx + 1
        do = math.hypot(x, y)
        dc = math.hypot(x - cx, y - cy)
        ao = (math.degrees(math.atan2(-y, x)) + 360.0) % 360.0
        ac = (math.degrees(math.atan2(-(y - cy), x - cx)) + 360.0) % 360.0
        mx = (x - min_x) / width
        my = (y - min_y) / height
        mp = (k_idx) / float(total_pts - 1) if total_pts > 1 else 0.0

        pt_env = dict(base_env)
        pt_env.update({
            "x": x, "y": y,
            "i": k, "k": k, "Pk": k,
            "mx": mx, "my": my, "Mx": mx, "My": my,
            "mp": mp, "Mp": mp,
            "do": do, "Do": do,
            "dc": dc, "Dc": dc,
            "ao": ao, "Ao": ao,
            "ac": ac, "Ac": ac
        })

        try:
            res_x = float(eval(str_expr_x, {"__builtins__": {}}, pt_env))
        except Exception:
            res_x = x

        try:
            res_y = float(eval(str_expr_y, {"__builtins__": {}}, pt_env))
        except Exception:
            res_y = y

        final_x = x + t_val * (res_x - x)
        final_y = y + t_val * (res_y - y)

        out_tokens[idx_x] = _format_num(final_x)
        out_tokens[idx_y] = _format_num(final_y)

    return " ".join(out_tokens) + " "


def _shape_filter_group(drawing, rot_step=0.0, scale_step=100.0, offset_x=0.0, offset_y=0.0, t=1.0, anchor="center", context=None):
    """Group Mode: Iterates over sub-contours ('m ...') of a multi-contour shape
    aplicando rotación, escala y offset acumulados por pieza, modulados por Factor (t).
    """
    raw_shp = resolve_shape_value(drawing, context)
    if not raw_shp:
        return ""

    from node_engine import _eval_num_expr
    try:
        t_val = float(_eval_num_expr(t, context, 1.0))
    except Exception:
        t_val = 1.0

    try:
        r_step = float(_eval_num_expr(rot_step, context, 0.0))
    except Exception:
        r_step = 0.0

    try:
        s_step = float(_eval_num_expr(scale_step, context, 100.0))
    except Exception:
        s_step = 100.0

    try:
        off_x = float(_eval_num_expr(offset_x, context, 0.0))
    except Exception:
        off_x = 0.0

    try:
        off_y = float(_eval_num_expr(offset_y, context, 0.0))
    except Exception:
        off_y = 0.0

    sub_contours = _split_shape_contours(raw_shp)
    if not sub_contours:
        return raw_shp

    transformed_pieces = []
    for i_idx, piece_str in enumerate(sub_contours):
        cur_rot = i_idx * r_step * t_val
        scale_factor = 1.0 + i_idx * ((s_step - 100.0) / 100.0) * t_val
        scale_factor = max(0.001, scale_factor)
        cur_off_x = i_idx * off_x * t_val
        cur_off_y = i_idx * off_y * t_val

        p_res = piece_str
        if abs(scale_factor - 1.0) > 1e-4:
            p_res = shape_manipulator(context, drawing=p_res, scale_x=scale_factor, scale_y=scale_factor, mode=anchor)
        if abs(cur_rot) > 1e-4:
            p_res = shape_manipulator(context, drawing=p_res, rot=cur_rot, mode=anchor)
        if abs(cur_off_x) > 1e-4 or abs(cur_off_y) > 1e-4:
            p_res = shape_manipulator(context, drawing=p_res, offset_x=cur_off_x, offset_y=cur_off_y, mode="origin")

        transformed_pieces.append(p_res.strip())

    return " ".join(transformed_pieces) + " "


def _shape_filter_noise(drawing, radius_x=5.0, radius_y=5.0, subdivs=2.0, seed=0, context=None):
    """Noise Mode: Pseudo-randomly perturbs vertices dentro de [-rx, +rx] y [-ry, +ry].
    Soporta subdivisión previa y semilla determinista.
    """
    raw_shp = resolve_shape_value(drawing, context)
    if not raw_shp:
        return ""

    from node_engine import _eval_num_expr
    try:
        rx = float(_eval_num_expr(radius_x, context, 5.0))
    except Exception:
        rx = 5.0

    try:
        ry = float(_eval_num_expr(radius_y, context, 5.0))
    except Exception:
        ry = 5.0

    try:
        sub_val = float(_eval_num_expr(subdivs, context, 2.0))
    except Exception:
        sub_val = 2.0

    try:
        s_seed = int(float(_eval_num_expr(seed, context, 0)))
    except Exception:
        s_seed = 0

    if sub_val > 0:
        raw_shp = _shape_redraw_bezier(raw_shp, factor=sub_val, context=context)

    import random
    rng = random.Random(s_seed if s_seed != 0 else 42)

    tokens = raw_shp.strip().split()
    out_tokens = []
    i = 0
    n_tok = len(tokens)
    cmd = None

    while i < n_tok:
        tok = tokens[i]
        tok_lower = tok.lower()
        if tok_lower in ('m', 'l', 'b', 'c'):
            cmd = tok_lower
            out_tokens.append(tok)
            i += 1
            continue
        if i + 1 < n_tok:
            try:
                x = float(tokens[i])
                y = float(tokens[i + 1])
                dx = rng.uniform(-rx, rx) if rx > 0 else 0.0
                dy = rng.uniform(-ry, ry) if ry > 0 else 0.0
                out_tokens.append(_format_num(x + dx))
                out_tokens.append(_format_num(y + dy))
                i += 2
                continue
            except ValueError:
                pass
        out_tokens.append(tok)
        i += 1

    return " ".join(out_tokens) + " "


def shape_filter(
    context,
    drawing="",
    mode="vertices",
    expr_x="x",
    expr_y="y",
    t=1.0,
    subdivs=0.0,
    rot_step=0.0,
    scale_step=100.0,
    offset_x=0.0,
    offset_y=0.0,
    anchor="center",
    radius_x=5.0,
    radius_y=5.0,
    seed=0,
    **kwargs
):
    """Unified entry point for Shape Filter node with 3 operational modes:
    - Vértices: Expresiones analíticas por vértice con interpolación progresiva (t) y subdivisión.
    - Grupo: Iterador de transformaciones por subcontorno/pieza ('m ...') modulado por Factor (t).
    - Ruido: Perturbación aleatoria por vértice dentro de radio X/Y con semilla determinista.
    """
    mode_clean = str(mode or "Vértices").strip().lower().replace("é", "e").replace("á", "a").replace("í", "i").replace("ó", "o").replace("ú", "u")

    if "vert" in mode_clean or "expr" in mode_clean:
        return _shape_filter_vertices(
            drawing=drawing,
            expr_x=expr_x if expr_x is not None else kwargs.get("expr_x", "x"),
            expr_y=expr_y if expr_y is not None else kwargs.get("expr_y", "y"),
            t=t if t is not None else kwargs.get("t", 1.0),
            subdivs=subdivs if subdivs is not None else kwargs.get("subdivs", 0.0),
            context=context
        )

    elif "grup" in mode_clean or "group" in mode_clean or "piez" in mode_clean:
        return _shape_filter_group(
            drawing=drawing,
            rot_step=rot_step if rot_step is not None else kwargs.get("rot_step", 0.0),
            scale_step=scale_step if scale_step is not None else kwargs.get("scale_step", 100.0),
            offset_x=offset_x if offset_x is not None else kwargs.get("offset_x", 0.0),
            offset_y=offset_y if offset_y is not None else kwargs.get("offset_y", 0.0),
            t=t if t is not None else kwargs.get("t", 1.0),
            anchor=anchor if anchor is not None else kwargs.get("anchor", "center"),
            context=context
        )

    elif "ruid" in mode_clean or "noise" in mode_clean or "rand" in mode_clean:
        return _shape_filter_noise(
            drawing=drawing,
            radius_x=radius_x if radius_x is not None else kwargs.get("radius_x", 5.0),
            radius_y=radius_y if radius_y is not None else kwargs.get("radius_y", 5.0),
            subdivs=subdivs if subdivs is not None else kwargs.get("subdivs", 2.0),
            seed=seed if seed is not None else kwargs.get("seed", 0),
            context=context
        )

    return _shape_filter_vertices(drawing=drawing, expr_x=expr_x, expr_y=expr_y, t=t, subdivs=subdivs, context=context)


NODE_REGISTRY["Shape/Filter"] = shape_filter
NODE_REGISTRY["Filter"] = shape_filter
NODE_REGISTRY["Shape/Filter"] = shape_filter
NODE_REGISTRY["Filter"] = shape_filter



def _parse_multi_pattern(val, default_val=4.0):
    """
    Parsea patrones de números, listas o cadenas para generadores de franjas y bordes.
    Soporta números directos, listas, tuplas y cadenas con sintaxis de Effector 2:
    - "8, 2, 4, 3" -> [(8.0, False), (2.0, False), (4.0, False), (3.0, False)]
    - "8, {2}, 4, {3}" -> [(8.0, False), (2.0, True), (4.0, False), (3.0, True)]
    - "8, -2, 4, -3" -> [(8.0, False), (2.0, True), (4.0, False), (3.0, True)]
    Donde True en la tupla (val, is_gap) indica un espacio/hueco vacío (gap).
    """
    if val is None or val == "":
        return [(float(default_val), False)]
    if isinstance(val, (int, float)):
        v = float(val)
        return [(abs(v), v < 0)]
    if isinstance(val, (list, tuple)):
        res = []
        for item in val:
            if isinstance(item, dict):
                g = float(item.get("gap", item.get("space", item.get("val", default_val))))
                res.append((abs(g), True))
            elif isinstance(item, (list, tuple)) and len(item) > 0:
                res.append((abs(float(item[0])), True))
            else:
                try:
                    num = float(item)
                    res.append((abs(num), num < 0))
                except Exception:
                    pass
        return res if res else [(float(default_val), False)]

    s = str(val).strip()
    tokens = re.findall(r'\{[^}]+\}|[+-]?(?:\d+(?:\.\d*)?|\.\d+)', s)
    if not tokens:
        try:
            num = float(s)
            return [(abs(num), num < 0)]
        except Exception:
            return [(float(default_val), False)]

    res = []
    for tok in tokens:
        tok = tok.strip()
        if tok.startswith("{") and tok.endswith("}"):
            inner = tok[1:-1].strip()
            try:
                g = float(inner)
                res.append((abs(g), True))
            except Exception:
                pass
        else:
            try:
                num = float(tok)
                res.append((abs(num), num < 0))
            except Exception:
                pass
    return res if res else [(float(default_val), False)]


def _get_drawing_bbox(drawing):
    """Calculates bounding box (min_x, max_x, min_y, max_y) of an ASS drawing."""
    tokens = str(drawing).split()
    coords = []
    for tok in tokens:
        try:
            coords.append(float(tok))
        except ValueError:
            pass
    if coords and len(coords) >= 2:
        xs = coords[0::2]
        ys = coords[1::2]
        return min(xs), max(xs), min(ys), max(ys)
    return 0.0, 100.0, 0.0, 100.0


def _invert_shape_contour(raw_shp):
    """Inverts contour orientation for subtraction in ASS (empezando con nuevo subcamino m)."""
    contours = parse_assdraw_segments(raw_shp)
    if not contours:
        return ""
    out_tokens = []
    for c in contours:
        segs = c.get('segments', [])
        if not segs:
            continue
        rev_segs = []
        for s in reversed(segs):
            stype = s.get('type', 'l')
            if stype == 'l':
                rev_segs.append(f"l {_format_num(s['p0'][0])} {_format_num(s['p0'][1])}")
            elif stype in ('b', 'c'):
                rev_segs.append(f"b {_format_num(s['p2'][0])} {_format_num(s['p2'][1])} {_format_num(s['p1'][0])} {_format_num(s['p1'][1])} {_format_num(s['p0'][0])} {_format_num(s['p0'][1])}")
        
        last_seg = segs[-1]
        last_pt = last_seg['p3'] if last_seg.get('type') in ('b', 'c') else last_seg['p1']
        out_tokens.append(f"m {_format_num(last_pt[0])} {_format_num(last_pt[1])} " + " ".join(rev_segs))
    return " ".join(out_tokens) + " "


def _finish_multi_pieces(pieces, anchor="center", tags="", context=None, return_list=False, canonical_center=None, t=1.0):
    if not pieces:
        return [] if return_list else ""
    valid_pieces = [p for p in pieces if p and str(p).strip()]
    if not valid_pieces:
        return [] if return_list else ""

    anchor_str = str(anchor or "center").strip().lower()

    all_coords = []
    piece_tokens_list = []
    for p in valid_pieces:
        toks = p.split()
        piece_tokens_list.append(toks)
        for tok in toks:
            try:
                all_coords.append(float(tok))
            except ValueError:
                pass

    min_x, max_x, min_y, max_y = 0.0, 0.0, 0.0, 0.0
    cx, cy = 0.0, 0.0
    if all_coords and len(all_coords) >= 2:
        xs = all_coords[0::2]
        ys = all_coords[1::2]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0

    pos_x, pos_y = 0.0, 0.0
    if isinstance(context, dict):
        unit = context.get('syl') or context.get('char') or context.get('word') or context.get('line') or context.get('active_unit')
        line_obj = context.get('active_line') or context.get('line')
        try:
            pos_x = float(context.get('fx_pos_x', context.get('x', context.get('pos_x', getattr(unit, 'x', getattr(unit, 'center', getattr(line_obj, 'x', getattr(line_obj, 'center', 0.0))))))))
        except Exception: pos_x = 0.0
        try:
            pos_y = float(context.get('fx_pos_y', context.get('y', context.get('pos_y', getattr(unit, 'y', getattr(unit, 'middle', getattr(line_obj, 'y', getattr(line_obj, 'middle', 0.0))))))))
        except Exception: pos_y = 0.0

    if anchor_str == "origin":
        ref_x, ref_y = min_x, min_y
        base_x, base_y = 0.0, 0.0
    elif anchor_str == "absolute":
        ref_x, ref_y = 0.0, 0.0
        base_x, base_y = pos_x, pos_y
    else:  # "center" fallback
        if canonical_center is not None:
            ref_x, ref_y = canonical_center
        else:
            ref_x, ref_y = cx, cy
        base_x, base_y = 0.0, 0.0

    anchored_pieces = []
    for toks in piece_tokens_list:
        out_tokens = []
        i = 0
        while i < len(toks):
            token = toks[i]
            try:
                x_val = float(token)
                if i + 1 < len(toks):
                    try:
                        y_val = float(toks[i + 1])
                        rel_x = (x_val - ref_x) + base_x
                        rel_y = (y_val - ref_y) + base_y
                        out_tokens.append(f"{rel_x:.2f}".rstrip('0').rstrip('.'))
                        out_tokens.append(f"{rel_y:.2f}".rstrip('0').rstrip('.'))
                        i += 2
                        continue
                    except ValueError:
                        pass
                out_tokens.append(token)
                i += 1
            except ValueError:
                out_tokens.append(token)
                i += 1
        anchored_pieces.append(" ".join(out_tokens))

    if return_list:
        return anchored_pieces

    if tags and str(tags).strip():
        from clipper_engine import ClipperEngine
        return ClipperEngine.fusion_shapes_tags(anchored_pieces, tags=tags)
    return " ".join(anchored_pieces)


def _gen_multi1_concentric_squares(size=100.0, px_pattern="4", separation=0.0, t=1.0, anchor="center", context=None, tags="", return_list=False):
    """multi1: Concentric square frames with alternating thicknesses, gaps, and spacing."""
    s_val = float(size) if size is not None else 100.0
    sep_val = float(separation) if separation is not None else 0.0
    t_clamped = max(0.0, min(1.0, float(t)))
    target_size = max(1.0, s_val * t_clamped)

    pattern = _parse_multi_pattern(px_pattern, 4.0)
    px1, is_gap1 = pattern[0]
    px1 = max(0.1, px1)
    shpw = px1

    shp_parts = [f"m 0 0 l 0 {_format_num(px1)} l {_format_num(px1)} {_format_num(px1)} l {_format_num(px1)} 0 l 0 0 "]
    i = 1
    while 2 * shpw < target_size and i < 1000:
        pxi_val, is_gap = pattern[i % len(pattern)]
        shpw += pxi_val + sep_val
        if not is_gap and pxi_val > 0:
            p_a = -shpw + px1
            p_b = shpw
            p_c = -shpw + px1 + pxi_val
            p_d = shpw - pxi_val
            shp_parts.append(
                f"m {_format_num(p_a)} {_format_num(p_a)} "
                f"l {_format_num(p_a)} {_format_num(p_b)} "
                f"l {_format_num(p_b)} {_format_num(p_b)} "
                f"l {_format_num(p_b)} {_format_num(p_a)} "
                f"l {_format_num(p_a)} {_format_num(p_a)} "
                f"l {_format_num(p_c)} {_format_num(p_c)} "
                f"l {_format_num(p_d)} {_format_num(p_c)} "
                f"l {_format_num(p_d)} {_format_num(p_d)} "
                f"l {_format_num(p_c)} {_format_num(p_d)} "
                f"l {_format_num(p_c)} {_format_num(p_c)} "
            )
        i += 1

    return _finish_multi_pieces(shp_parts, anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(px1 / 2.0, px1 / 2.0), t=t_clamped)


def _gen_multi2_diagonal_stripes(width=70.0, height=50.0, px_pattern="6", separation=0.0, t=1.0, anchor="center", context=None, tags="", return_list=False):
    """multi2: 45° diagonal stripes inside rectangle with spacing or overlap."""
    w_val = max(1.0, float(width) if width is not None else 70.0)
    h_val = max(1.0, float(height) if height is not None else 50.0)
    sep_val = float(separation) if separation is not None else 0.0
    pattern = _parse_multi_pattern(px_pattern, 6.0)
    t_clamped = max(0.0, min(1.0, float(t)))
    total_diag = w_val + h_val
    max_c = total_diag * t_clamped

    if t_clamped < 0.0001:
        return _finish_multi_pieces([], anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(w_val / 2.0, h_val / 2.0), t=t_clamped)

    from clipper_engine import ClipperEngine

    period = sum([p[0] + sep_val for p in pattern])
    if period <= 0.001:
        period = 10.0
    c_mid = total_diag / 2.0
    first_px = pattern[0][0]

    num_periods = int((c_mid - first_px / 2.0) / period) + 3
    c_start_base = (c_mid - first_px / 2.0) - num_periods * period

    c = c_start_base
    i = 0
    bands = []
    extra_h = h_val + 50.0

    while c < total_diag + period and i < 4000:
        pxi, is_gap = pattern[i % len(pattern)]
        if pxi <= 0 or is_gap:
            c += pxi + sep_val
            i += 1
            continue
        c_band_start = c
        c_band_end = c + pxi
        if c_band_start < max_c:
            c_end_clipped = min(c_band_end, max_c)
            if c_end_clipped > c_band_start:
                p1 = (c_band_start, 0.0)
                p2 = (c_end_clipped, 0.0)
                p3 = (c_end_clipped - extra_h, extra_h)
                p4 = (c_band_start - extra_h, extra_h)
                band_ass = (
                    f"m {_format_num(p1[0])} {_format_num(p1[1])} "
                    f"l {_format_num(p2[0])} {_format_num(p2[1])} "
                    f"l {_format_num(p3[0])} {_format_num(p3[1])} "
                    f"l {_format_num(p4[0])} {_format_num(p4[1])} "
                )
                bands.append(band_ass)
        c += pxi + sep_val
        i += 1

    if not bands:
        return _finish_multi_pieces([], anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(w_val / 2.0, h_val / 2.0), t=t_clamped)

    clip_box = f"m 0 0 l {_format_num(w_val)} 0 l {_format_num(w_val)} {_format_num(h_val)} l 0 {_format_num(h_val)} "
    discrete_stripes = [ClipperEngine.boolean_intersection(b, clip_box) for b in bands]
    discrete_stripes = [s for s in discrete_stripes if s and s.strip()]
    return _finish_multi_pieces(discrete_stripes, anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(w_val / 2.0, h_val / 2.0), t=t_clamped)


def _gen_multi3_concentric_rings(base_shape=None, size=100.0, bord_pattern="4", separation=0.0, t=1.0, anchor="center", context=None, tags="", return_list=False):
    """multi3: Concentric rings with smooth Bezier preset scaling for geometric presets, and Clipper-offset contour rings for text and complex drawings."""
    is_preset_shape = False
    if not base_shape or not str(base_shape).strip():
        base_shape = RAW_PRESET_SHAPES["circle"]
        is_preset_shape = True
    else:
        resolved = resolve_shape_value(base_shape, context)
        if not resolved or not str(resolved).strip():
            base_shape = RAW_PRESET_SHAPES["circle"]
            is_preset_shape = True
        else:
            base_shape = resolved
            if base_shape in RAW_PRESET_SHAPES.values():
                is_preset_shape = True

    size_val = float(size) if size is not None else 100.0
    sep_val = max(0.0, float(separation)) if separation is not None else 0.0
    t_clamped = max(0.0, min(1.0, float(t)))
    target_size = max(1.0, size_val * t_clamped)

    pattern = _parse_multi_pattern(bord_pattern, 4.0)
    bi_val, is_gap1 = pattern[0]
    bi_val = max(0.1, bi_val)

    bounds = _get_drawing_bbox(base_shape)
    w = max(0.001, bounds[1] - bounds[0]) if bounds else 100.0
    h = max(0.001, bounds[3] - bounds[2]) if bounds else 100.0
    max_dim = max(w, h)
    cx = (bounds[0] + bounds[1]) / 2.0 if bounds else 0.0
    cy = (bounds[2] + bounds[3]) / 2.0 if bounds else 0.0

    manip_mode = anchor if ("rel" in str(anchor).lower() or "pieza" in str(anchor).lower()) else "center"

    if is_preset_shape:
        def _scale_to(shp_code, dim):
            sc = dim / max_dim
            return shape_manipulator(context, drawing=shp_code, scale_x=sc, scale_y=sc, mode=manip_mode)

        smax = bi_val
        shp_parts = []
        if not is_gap1 and bi_val > 0:
            shp_parts.append(_scale_to(base_shape, bi_val))

        i = 1
        while smax <= target_size and i < 1000:
            bi, is_gap = pattern[i % len(pattern)]
            smax += 2 * bi + sep_val
            if not is_gap and bi > 0:
                shp1 = _scale_to(base_shape, smax)
                inner_dim = max(0.1, smax - 2 * bi)
                shp2 = _scale_to(base_shape, inner_dim)
                scon = shp1.strip() + " " + _invert_shape_contour(shp2).strip() + " "
                shp_parts.append(scon)
            i += 1
        return _finish_multi_pieces(shp_parts, anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(0.0, 0.0), t=t_clamped)

    from clipper_engine import ClipperEngine

    shp_parts = []
    if not is_gap1 and bi_val > 0:
        shp_parts.append(base_shape)

    max_expansion = target_size / 2.0
    cumulative_dist = 0.0
    i = 1
    offset_cache = {0.0: base_shape}
    while cumulative_dist < max_expansion and i < 50:
        bi, is_gap = pattern[i % len(pattern)]
        if not is_gap and bi > 0:
            inner_dist = cumulative_dist + sep_val
            outer_dist = inner_dist + bi
            if outer_dist > max_expansion and i > 1:
                outer_dist = max_expansion
            if outer_dist > inner_dist:
                if inner_dist not in offset_cache:
                    offset_cache[inner_dist] = ClipperEngine.offset_shape(base_shape, inner_dist) if inner_dist > 0.01 else base_shape
                inner_shp = offset_cache[inner_dist]

                if outer_dist not in offset_cache:
                    offset_cache[outer_dist] = ClipperEngine.offset_shape(base_shape, outer_dist)
                outer_shp = offset_cache[outer_dist]

                diff_shp = ClipperEngine.boolean_difference(outer_shp, inner_shp)
                if diff_shp and diff_shp.strip():
                    shp_parts.append(diff_shp)
            cumulative_dist = outer_dist
        else:
            cumulative_dist += bi + sep_val
        i += 1

    if not shp_parts:
        shp_parts = [base_shape]

    return _finish_multi_pieces(shp_parts, anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(cx, cy), t=t_clamped)


def _polygon_centroid_2d(pts):
    n = len(pts)
    if n < 3:
        return sum(p[0] for p in pts) / float(n), sum(p[1] for p in pts) / float(n)
    area = 0.0
    cx = 0.0
    cy = 0.0
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    area *= 0.5
    if abs(area) < 1e-7:
        return sum(p[0] for p in pts) / float(n), sum(p[1] for p in pts) / float(n)
    cx /= (6.0 * area)
    cy /= (6.0 * area)
    return cx, cy


def _gen_multi4_polygonal_mosaic(size=64.0, sides=6, rings=1, n_layers=25, separation=0.0, t=1.0, anchor="center", context=None, tags="", return_list=False, order="Normal"):
    """multi4: Regular polygon segmented into sectors and rings with centroidal offset/shrink spacing for each piece and appearance ordering."""
    s_val = float(size) if size is not None else 64.0
    loop1 = max(3, int(sides)) if sides is not None else 6
    loop2 = max(1, int(rings)) if rings is not None else 1
    n_val = max(1, int(n_layers)) if n_layers is not None else 25
    sep_val = float(separation) if separation is not None else 0.0
    t_clamped = max(0.0, min(1.0, float(t)))

    if t_clamped < 0.0001:
        return _finish_multi_pieces([], anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(0.0, 0.0), t=t_clamped)

    sizer = 2 * math.ceil(s_val / 2.0)
    px = max(1.0, round(0.5 * sizer / loop2))

    def _shrink_piece(pts, sep):
        if abs(sep) <= 0.001:
            return pts
        cx, cy = _polygon_centroid_2d(pts)
        n = len(pts)
        avg_r = sum(math.hypot(p[0] - cx, p[1] - cy) for p in pts) / float(n)
        if avg_r <= 0.001:
            return pts
        scale = max(0.0, 1.0 - (sep / (2.0 * max(0.1, avg_r))))
        return [(cx + scale * (p[0] - cx), cy + scale * (p[1] - cy)) for p in pts]

    ring_specs = []
    pn = sizer / 2.0
    i = 0
    while pn > 0 and i < min(loop2, n_val):
        p_curr = pn if px >= pn else px
        ring_specs.append((pn * 2.0, p_curr))
        pn -= px
        i += 1

    ring_specs.reverse()

    total_sectors = len(ring_specs) * loop1
    visible_sectors = max(1, int(round(total_sectors * t_clamped))) if t_clamped > 0.001 else 0

    order_str = str(order or "Normal").strip().lower()
    is_custom_order = order_str not in ("normal", "raw", "none", "0", "")

    if is_custom_order:
        grid_key = ("multi4_custom", round(s_val, 2), loop1, loop2, n_val, round(sep_val, 2), order_str)
        full_tiles = _GLOBAL_MULTI_GRID_CACHE.get(grid_key)
        if full_tiles is None:
            all_entries = []
            for r_idx, (sz40, px40) in enumerate(ring_specs):
                s40 = 2 * math.ceil(sz40 / 2.0)
                p40 = s40 / 2.0 if px40 >= s40 / 2.0 else px40
                angle = 360.0 / loop1
                r_inner = s40 / 2.0 - p40
                r_outer = s40 / 2.0

                for k in range(1, loop1 + 1):
                    a_cur = angle * k
                    a_prev = angle * (k - 1)

                    if r_inner < 0.001:
                        pts = [
                            (0.0, 0.0),
                            (r_outer * math.cos(math.radians(a_cur)), r_outer * math.sin(math.radians(a_cur))),
                            (r_outer * math.cos(math.radians(a_prev)), r_outer * math.sin(math.radians(a_prev))),
                        ]
                    else:
                        pts = [
                            (r_inner * math.cos(math.radians(a_cur)), r_inner * math.sin(math.radians(a_cur))),
                            (r_outer * math.cos(math.radians(a_cur)), r_outer * math.sin(math.radians(a_cur))),
                            (r_outer * math.cos(math.radians(a_prev)), r_outer * math.sin(math.radians(a_prev))),
                            (r_inner * math.cos(math.radians(a_prev)), r_inner * math.sin(math.radians(a_prev))),
                        ]

                    shrunk_pts = _shrink_piece(pts, sep_val)
                    cmd_parts = [f"m {_format_num(shrunk_pts[0][0])} {_format_num(shrunk_pts[0][1])}"]
                    for p in shrunk_pts[1:]:
                        cmd_parts.append(f"l {_format_num(p[0])} {_format_num(p[1])}")
                    piece_str = " ".join(cmd_parts) + " "
                    if loop1 % 2 == 1:
                        rot_ang = ((-1.0) ** ((loop1 - 1) / 2.0)) * 90.0 / loop1
                        piece_str = shape_manipulator(context, drawing=piece_str, rot=rot_ang, mode="origin")
                    
                    c_x, c_y = _polygon_centroid_2d(shrunk_pts)
                    min_px = min(p[0] for p in shrunk_pts)
                    max_px = max(p[0] for p in shrunk_pts)
                    min_py = min(p[1] for p in shrunk_pts)
                    max_py = max(p[1] for p in shrunk_pts)
                    all_entries.append({
                        'figure': piece_str,
                        'min_x': min_px, 'min_y': min_py,
                        'max_x': max_px, 'max_y': max_py,
                        'cx': c_x, 'cy': c_y,
                        'w': max_px - min_px, 'h': max_py - min_py,
                        'row': r_idx, 'col': k
                    })

            from clipper_engine import ClipperEngine
            sorted_entries = ClipperEngine.sort_islands_by_order(all_entries, order=order)
            full_tiles = [e['figure'] for e in sorted_entries]
            if len(_GLOBAL_MULTI_GRID_CACHE) > 512:
                _GLOBAL_MULTI_GRID_CACHE.clear()
            _GLOBAL_MULTI_GRID_CACHE[grid_key] = full_tiles

        individual_tiles = full_tiles[:visible_sectors]
        parts_to_finish = individual_tiles
    else:
        grid_key = ("multi4_normal", round(s_val, 2), loop1, loop2, n_val, round(sep_val, 2))
        full_ring_data = _GLOBAL_MULTI_GRID_CACHE.get(grid_key)
        if full_ring_data is None:
            full_rings = []
            for sz40, px40 in ring_specs:
                s40 = 2 * math.ceil(sz40 / 2.0)
                p40 = s40 / 2.0 if px40 >= s40 / 2.0 else px40
                angle = 360.0 / loop1
                r_inner = s40 / 2.0 - p40
                r_outer = s40 / 2.0

                r_pieces = []
                for k in range(1, loop1 + 1):
                    a_cur = angle * k
                    a_prev = angle * (k - 1)

                    if r_inner < 0.001:
                        pts = [
                            (0.0, 0.0),
                            (r_outer * math.cos(math.radians(a_cur)), r_outer * math.sin(math.radians(a_cur))),
                            (r_outer * math.cos(math.radians(a_prev)), r_outer * math.sin(math.radians(a_prev))),
                        ]
                    else:
                        pts = [
                            (r_inner * math.cos(math.radians(a_cur)), r_inner * math.sin(math.radians(a_cur))),
                            (r_outer * math.cos(math.radians(a_cur)), r_outer * math.sin(math.radians(a_cur))),
                            (r_outer * math.cos(math.radians(a_prev)), r_outer * math.sin(math.radians(a_prev))),
                            (r_inner * math.cos(math.radians(a_prev)), r_inner * math.sin(math.radians(a_prev))),
                        ]

                    shrunk_pts = _shrink_piece(pts, sep_val)
                    cmd_parts = [f"m {_format_num(shrunk_pts[0][0])} {_format_num(shrunk_pts[0][1])}"]
                    for p in shrunk_pts[1:]:
                        cmd_parts.append(f"l {_format_num(p[0])} {_format_num(p[1])}")
                    piece_str = " ".join(cmd_parts) + " "
                    if loop1 % 2 == 1:
                        rot_ang = ((-1.0) ** ((loop1 - 1) / 2.0)) * 90.0 / loop1
                        piece_str = shape_manipulator(context, drawing=piece_str, rot=rot_ang, mode="origin")
                    r_pieces.append(piece_str)
                full_rings.append(r_pieces)
            if len(_GLOBAL_MULTI_GRID_CACHE) > 512:
                _GLOBAL_MULTI_GRID_CACHE.clear()
            _GLOBAL_MULTI_GRID_CACHE[grid_key] = full_rings
            full_ring_data = full_rings

        ring_drawings = []
        individual_tiles = []
        sectors_remaining = visible_sectors

        for r_pieces in full_ring_data:
            if sectors_remaining <= 0:
                break
            n_steps = min(len(r_pieces), sectors_remaining)
            taken_pieces = r_pieces[:n_steps]
            ring_drawings.append("".join(taken_pieces))
            individual_tiles.extend(taken_pieces)
            sectors_remaining -= n_steps

        parts_to_finish = ring_drawings if (tags and str(tags).strip()) else individual_tiles

    if return_list:
        return _finish_multi_pieces(individual_tiles, anchor=anchor, tags=tags, context=context, return_list=True, canonical_center=(0.0, 0.0), t=t_clamped)
    else:
        return _finish_multi_pieces(parts_to_finish, anchor=anchor, tags=tags, context=context, return_list=False, canonical_center=(0.0, 0.0), t=t_clamped)


def _gen_multi5_multi_shape_mosaic(shapes=None, width=60.0, height=50.0, dx=0.0, dy=0.0, t=1.0, anchor="center", context=None, tags="", return_list=False, order="Normal"):
    """multi5: Periodic cyclic permutation mosaic (Latin square) of shapes with X/Y spacing and appearance ordering."""
    t_clamped = max(0.0, min(1.0, float(t))) if t is not None else 1.0
    w_target = max(1.0, float(width)) if width is not None else 60.0
    h_target = max(1.0, float(height)) if height is not None else 50.0

    if t_clamped < 0.0001:
        return _finish_multi_pieces([], anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(w_target / 2.0, h_target / 2.0), t=t_clamped)

    if not shapes:
        shapes = [RAW_PRESET_SHAPES.get("rectangle", "m 0 0 l 0 8 8 8 8 0")]
    elif isinstance(shapes, (list, tuple)):
        shapes = [resolve_shape_value(s, context) for s in shapes if s]
    else:
        s_str = str(shapes).strip()
        if "," in s_str:
            raw_items = [s.strip() for s in s_str.split(",") if s.strip()]
            shapes = [resolve_shape_value(item, context) for item in raw_items if item]
        else:
            resolved = resolve_shape_value(s_str, context)
            cnts = _split_shape_contours(resolved)
            shapes = cnts if (cnts and len(cnts) > 1) else [resolved]

    if not shapes:
        shapes = [RAW_PRESET_SHAPES.get("rectangle", "m 0 0 l 0 8 8 8 8 0")]

    n = len(shapes)
    bboxes = [_get_drawing_bbox(s) for s in shapes]
    widths = [max(1.0, b[1] - b[0]) for b in bboxes]
    heights = [max(1.0, b[3] - b[2]) for b in bboxes]
    wmax = max(widths)
    hmax = max(heights)

    dx_val = float(dx) if dx is not None else 0.0
    dy_val = float(dy) if dy is not None else 0.0
    order_str = str(order or "Normal").strip()
    anchor_str = str(anchor or "center").strip()

    grid_key = ("multi5", tuple(shapes), round(w_target, 2), round(h_target, 2), round(dx_val, 2), round(dy_val, 2), order_str, anchor_str)
    sorted_shapes = _GLOBAL_MULTI_GRID_CACHE.get(grid_key)
    if sorted_shapes is None:
        n = len(shapes)
        bboxes = [_get_drawing_bbox(s) for s in shapes]
        widths = [max(1.0, b[1] - b[0]) for b in bboxes]
        heights = [max(1.0, b[3] - b[2]) for b in bboxes]
        wmax = max(widths)
        hmax = max(heights)

        cell_w = max(0.1, wmax + dx_val)
        cell_h = max(0.1, hmax + dy_val)

        cols = max(1, math.ceil(w_target / cell_w))
        rows = max(1, math.ceil(h_target / cell_h))

        manip_mode = anchor if ("rel" in str(anchor).lower() or "pieza" in str(anchor).lower()) else "center"
        placed_entries = []
        for r in range(rows):
            for c in range(cols):
                shp_idx = (r + c) % n
                base_s = shapes[shp_idx]
                off_x = c * cell_w
                off_y = r * cell_h
                placed = shape_manipulator(context, drawing=base_s, offset_x=off_x, offset_y=off_y, mode=manip_mode)
                cx_piece = off_x + cell_w / 2.0
                cy_piece = off_y + cell_h / 2.0
                placed_entries.append({
                    'figure': placed,
                    'min_x': off_x,
                    'min_y': off_y,
                    'max_x': off_x + cell_w,
                    'max_y': off_y + cell_h,
                    'cx': cx_piece,
                    'cy': cy_piece,
                    'w': cell_w,
                    'h': cell_h,
                    'row': r,
                    'col': c
                })

        from clipper_engine import ClipperEngine
        sorted_entries = ClipperEngine.sort_islands_by_order(placed_entries, order=order_str)
        sorted_shapes = [e['figure'] for e in sorted_entries]
        if len(_GLOBAL_MULTI_GRID_CACHE) > 512:
            _GLOBAL_MULTI_GRID_CACHE.clear()
        _GLOBAL_MULTI_GRID_CACHE[grid_key] = sorted_shapes

    total_shapes = len(sorted_shapes)
    visible_shapes = max(1, int(round(total_shapes * t_clamped))) if t_clamped > 0.001 else 0
    placed_shapes = sorted_shapes[:visible_shapes]

    return _finish_multi_pieces(placed_shapes, anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(w_target / 2.0, h_target / 2.0), t=t_clamped)


def _gen_multi6_segmented_border(base_shape=None, width=104.0, height=104.0, bord=4.0, space=0.0, length=20.0, separation=None, t=1.0, anchor="center", context=None, tags="", return_list=False):
    """multi6: Closed analytical rectangular segmented border or tracer along perimeter of any base shape."""
    xsize = max(1.0, float(width) if width is not None else 104.0)
    ysize = max(1.0, float(height) if height is not None else 104.0)
    bord_val = max(0.1, float(bord) if bord is not None else 4.0)
    space_val = float(separation if separation is not None else (space if space is not None else 0.0))
    len_val = max(0.1, float(length)) if length is not None else 20.0
    t_clamped = max(0.0, min(1.0, float(t)))

    resolved_base = resolve_shape_value(base_shape, context) if base_shape and str(base_shape).strip() else None

    if not resolved_base or not resolved_base.strip():
        xloop = max(1, math.ceil((xsize - bord_val) / max(0.1, len_val + space_val)))
        yloop = max(1, math.ceil((ysize - bord_val) / max(0.1, len_val + space_val)))

        eff_xsize = xloop * (len_val + space_val) + bord_val - space_val
        eff_ysize = yloop * (len_val + space_val) + bord_val - space_val

        blocks = []
        for k in range(xloop):
            bx = k * (len_val + space_val)
            by = 0.0
            blocks.append((bx, by, len_val, bord_val))

        for k in range(yloop):
            bx = eff_xsize - bord_val
            by = k * (len_val + space_val)
            blocks.append((bx, by, bord_val, len_val))

        for k in range(xloop):
            bx = eff_xsize - (k + 1) * (len_val + space_val) + space_val
            by = eff_ysize - bord_val
            blocks.append((bx, by, len_val, bord_val))

        for k in range(yloop):
            bx = 0.0
            by = eff_ysize - (k + 1) * (len_val + space_val) + space_val
            blocks.append((bx, by, bord_val, len_val))

        tot = len(blocks)
        vis_count = max(1, int(round(tot * t_clamped))) if t_clamped > 0.001 else 0

        shp_parts = []
        for i in range(vis_count):
            bx, by, bw, bh = blocks[i]
            shp_parts.append(
                f"m {_format_num(bx)} {_format_num(by)} "
                f"l {_format_num(bx + bw)} {_format_num(by)} "
                f"l {_format_num(bx + bw)} {_format_num(by + bh)} "
                f"l {_format_num(bx)} {_format_num(by + bh)} "
                f"l {_format_num(bx)} {_format_num(by)} "
            )

        return _finish_multi_pieces(shp_parts, anchor=anchor, tags=tags, context=context, return_list=return_list)

    from clipper_engine import ClipperEngine
    import pyclipper

    bb = _get_drawing_bbox(resolved_base)
    sw = max(0.001, bb[1] - bb[0])
    sh = max(0.001, bb[3] - bb[2])
    if xsize > 1.0 and ysize > 1.0 and (abs(xsize - 104.0) > 0.01 or abs(ysize - 104.0) > 0.01):
        manip_mode = anchor if ("rel" in str(anchor).lower() or "pieza" in str(anchor).lower()) else "center"
        resolved_base = shape_manipulator(context, drawing=resolved_base, scale_x=xsize / sw, scale_y=ysize / sh, mode=manip_mode)

    contours = ClipperEngine.parse_assdraw(resolved_base, bezier_steps=20, min_points=2)
    if not contours:
        return [] if return_list else ""

    scale = 1000.0
    all_dash_shapes = []

    for contour in contours:
        pts = [list(map(float, p)) for p in contour]
        if len(pts) < 2:
            continue
        is_closed = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-4
        if not is_closed:
            pts.append(list(pts[0]))

        cum_dist = [0.0]
        total_len = 0.0
        for i in range(len(pts) - 1):
            d = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
            total_len += d
            cum_dist.append(total_len)

        if total_len < 0.001:
            continue

        def _get_pt_at_dist(target_d):
            target_d = max(0.0, min(total_len, target_d))
            for i in range(len(cum_dist) - 1):
                if cum_dist[i] <= target_d <= cum_dist[i + 1]:
                    seg_len = cum_dist[i + 1] - cum_dist[i]
                    if seg_len < 1e-6:
                        return list(pts[i])
                    ratio = (target_d - cum_dist[i]) / seg_len
                    return [
                        pts[i][0] + ratio * (pts[i + 1][0] - pts[i][0]),
                        pts[i][1] + ratio * (pts[i + 1][1] - pts[i][1])
                    ]
            return list(pts[-1])

        period = len_val + space_val
        if period <= 0.001:
            period = 10.0

        num_dashes = max(1, math.ceil(total_len / period))
        visible_dashes = max(1, int(round(num_dashes * t_clamped))) if t_clamped > 0.001 else 0

        for k in range(visible_dashes):
            s_start = k * period
            s_end = min(total_len, s_start + len_val)
            if s_start >= total_len:
                break

            dash_pts = [_get_pt_at_dist(s_start)]
            for i in range(len(cum_dist)):
                if s_start < cum_dist[i] < s_end:
                    dash_pts.append(list(pts[i]))
            dash_pts.append(_get_pt_at_dist(s_end))

            cleaned = [dash_pts[0]]
            for p in dash_pts[1:]:
                if math.hypot(p[0] - cleaned[-1][0], p[1] - cleaned[-1][1]) > 0.01:
                    cleaned.append(p)

            if len(cleaned) < 2:
                continue

            pco = pyclipper.PyclipperOffset(miter_limit=2.0, arc_tolerance=0.25 * scale)
            c_path = [[int(round(p[0] * scale)), int(round(p[1] * scale))] for p in cleaned]
            pco.AddPath(c_path, pyclipper.JT_SQUARE, pyclipper.ET_OPENBUTT)
            sol = pco.Execute((bord_val / 2.0) * scale)
            if sol:
                dash_ass = ClipperEngine.contours_to_assdraw([[[pt[0] / scale, pt[1] / scale] for pt in poly] for poly in sol])
                all_dash_shapes.append(dash_ass)

    return _finish_multi_pieces(all_dash_shapes, anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(xsize / 2.0, ysize / 2.0), t=t_clamped)


def _gen_multi7_radial_rosette(parts=12, r_out=50.0, r_in=0.0, separation=0.0, t=1.0, anchor="center", context=None, tags="", return_list=False):
    """multi7: Radial sectors (pie slices) with smooth cubic ASS Bézier curves and radial separation."""
    part = max(2, int(round(abs(float(parts))))) if parts is not None else 12
    r_outer = float(r_out) if r_out is not None else 50.0
    r_inner = float(r_in) if r_in is not None else 0.0
    sep_val = float(separation) if separation is not None else 0.0
    t_clamped = max(0.0, min(1.0, float(t)))
    visible_parts = max(1, int(round(part * t_clamped))) if t_clamped > 0.001 else 0

    angle = 360.0 / part
    ang_b = angle * 0.295927
    cos_ang_b = math.cos(math.radians(ang_b))
    ratio = 1.0 / cos_ang_b if abs(cos_ang_b) > 1e-6 else 1.0

    shp_list = []
    if r_inner <= 0.001:
        for i in range(1, visible_parts + 1):
            a_start = angle * (i - 1)
            a_end = angle * i
            a_mid = (a_start + a_end) / 2.0

            off_x = sep_val * math.cos(math.radians(a_mid)) if abs(sep_val) > 0.001 else 0.0
            off_y = sep_val * math.sin(math.radians(a_mid)) if abs(sep_val) > 0.001 else 0.0

            x0 = r_outer * math.cos(math.radians(a_start)) + off_x
            y0 = r_outer * math.sin(math.radians(a_start)) + off_y
            x1 = (r_outer * ratio) * math.cos(math.radians(a_start + ang_b)) + off_x
            y1 = (r_outer * ratio) * math.sin(math.radians(a_start + ang_b)) + off_y
            x2 = (r_outer * ratio) * math.cos(math.radians(a_end - ang_b)) + off_x
            y2 = (r_outer * ratio) * math.sin(math.radians(a_end - ang_b)) + off_y
            x3 = r_outer * math.cos(math.radians(a_end)) + off_x
            y3 = r_outer * math.sin(math.radians(a_end)) + off_y

            shp_list.append(
                f"m {_format_num(off_x)} {_format_num(off_y)} "
                f"l {_format_num(x0)} {_format_num(y0)} "
                f"b {_format_num(x1)} {_format_num(y1)} {_format_num(x2)} {_format_num(y2)} {_format_num(x3)} {_format_num(y3)} "
                f"l {_format_num(off_x)} {_format_num(off_y)} "
            )
    else:
        for i in range(1, visible_parts + 1):
            a_start = angle * (i - 1)
            a_end = angle * i
            a_mid = (a_start + a_end) / 2.0

            off_x = sep_val * math.cos(math.radians(a_mid)) if abs(sep_val) > 0.001 else 0.0
            off_y = sep_val * math.sin(math.radians(a_mid)) if abs(sep_val) > 0.001 else 0.0

            x0 = r_outer * math.cos(math.radians(a_start)) + off_x
            y0 = r_outer * math.sin(math.radians(a_start)) + off_y
            x1 = (r_outer * ratio) * math.cos(math.radians(a_start + ang_b)) + off_x
            y1 = (r_outer * ratio) * math.sin(math.radians(a_start + ang_b)) + off_y
            x2 = (r_outer * ratio) * math.cos(math.radians(a_end - ang_b)) + off_x
            y2 = (r_outer * ratio) * math.sin(math.radians(a_end - ang_b)) + off_y
            x3 = r_outer * math.cos(math.radians(a_end)) + off_x
            y3 = r_outer * math.sin(math.radians(a_end)) + off_y

            x4 = r_inner * math.cos(math.radians(a_end)) + off_x
            y4 = r_inner * math.sin(math.radians(a_end)) + off_y
            x5 = (r_inner * ratio) * math.cos(math.radians(a_end - ang_b)) + off_x
            y5 = (r_inner * ratio) * math.sin(math.radians(a_end - ang_b)) + off_y
            x6 = (r_inner * ratio) * math.cos(math.radians(a_start + ang_b)) + off_x
            y6 = (r_inner * ratio) * math.sin(math.radians(a_start + ang_b)) + off_y
            x7 = r_inner * math.cos(math.radians(a_start)) + off_x
            y7 = r_inner * math.sin(math.radians(a_start)) + off_y
            x8 = x0
            y8 = y0

            shp_list.append(
                f"m {_format_num(x0)} {_format_num(y0)} "
                f"b {_format_num(x1)} {_format_num(y1)} {_format_num(x2)} {_format_num(y2)} {_format_num(x3)} {_format_num(y3)} "
                f"l {_format_num(x4)} {_format_num(y4)} "
                f"b {_format_num(x5)} {_format_num(y5)} {_format_num(x6)} {_format_num(y6)} {_format_num(x7)} {_format_num(y7)} "
                f"l {_format_num(x8)} {_format_num(y8)} "
            )

    return _finish_multi_pieces(shp_list, anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(0.0, 0.0), t=t_clamped)


def _resolve_direction_angle(angle_in, context=None, default=0.0):
    """Converts angle or cardinal/diagonal direction name to float degrees (0° = Arriba / Vertical Up, sentido horario)."""
    if angle_in is None or angle_in == "":
        return default
    if isinstance(angle_in, (int, float)):
        return float(angle_in)

    s = str(angle_in).strip().lower().replace(" ", "").replace("_", "-")
    cardinals = {
        "arriba": 0.0, "up": 0.0, "top": 0.0, "u": 0.0, "n": 0.0, "north": 0.0,
        "arriba-derecha": 45.0, "arribaderecha": 45.0, "top-right": 45.0, "topright": 45.0, "ne": 45.0, "northeast": 45.0,
        "derecha": 90.0, "right": 90.0, "d": 90.0, "r": 90.0, "e": 90.0, "east": 90.0,
        "abajo-derecha": 135.0, "abajoderecha": 135.0, "bottom-right": 135.0, "bottomright": 135.0, "se": 135.0, "southeast": 135.0, "diagonal": 135.0,
        "abajo": 180.0, "down": 180.0, "bottom": 180.0, "b": 180.0, "s": 180.0, "south": 180.0,
        "abajo-izquierda": 225.0, "abajoizquierda": 225.0, "bottom-left": 225.0, "bottomleft": 225.0, "sw": 225.0, "southwest": 225.0,
        "izquierda": 270.0, "left": 270.0, "izq": 270.0, "i": 270.0, "l": 270.0, "w": 270.0, "west": 270.0,
        "arriba-izquierda": 315.0, "arribaizquierda": 315.0, "top-left": 315.0, "topleft": 315.0, "nw": 315.0, "northwest": 315.0
    }
    if s in cardinals:
        return cardinals[s]

    from node_engine import _eval_num_expr
    try:
        return float(_eval_num_expr(angle_in, context, default))
    except Exception:
        return default


def _gen_multi8_tunnel_cascade(base_shape=None, size1=100.0, size2=10.0, loop=8, separation=0.0, angle=0.0, t=1.0, anchor="center", context=None, tags="", return_list=False):
    """multi8: Concentric progressive scaling cascade of any shape with spacing and angular direction with 270° offset (0° = Up)."""
    if not base_shape or not str(base_shape).strip():
        base_shape = RAW_PRESET_SHAPES["rectangle"]
    else:
        base_shape = resolve_shape_value(base_shape, context)
        if not base_shape:
            base_shape = RAW_PRESET_SHAPES["rectangle"]

    loop_val = max(2, int(round(abs(float(loop))))) if loop is not None else 8
    s1 = abs(float(size1)) if size1 is not None else 100.0
    s2 = abs(float(size2)) if size2 is not None else 10.0
    sep_val = float(separation) if separation is not None else 0.0
    ang_deg = _resolve_direction_angle(angle, context, default=0.0)
    rad = math.radians(ang_deg + 270.0)
    cos_ang = math.cos(rad)
    sin_ang = math.sin(rad)

    maxsize = max(s1, s2)
    minsize = min(s1, s2)
    t_clamped = max(0.0, min(1.0, float(t)))
    visible_loops = max(1, int(round(loop_val * t_clamped))) if t_clamped > 0.001 else 0

    bounds = _get_drawing_bbox(base_shape)
    w = max(0.001, bounds[1] - bounds[0])
    h = max(0.001, bounds[3] - bounds[2])
    max_dim = max(w, h)

    manip_mode = anchor if ("rel" in str(anchor).lower() or "pieza" in str(anchor).lower()) else "center"

    def _scale_to(shp_code, dim):
        sc = dim / max_dim
        return shape_manipulator(context, drawing=shp_code, scale_x=sc, scale_y=sc, mode=manip_mode)

    shp_max = _scale_to(base_shape, maxsize)

    result = []
    for i in range(1, visible_loops + 1):
        cur_size = maxsize - (maxsize - minsize) * (i - 1) / max(1, loop_val - 1)
        cur_scale = cur_size / max(0.001, maxsize)
        off_x = (i - 1) * sep_val * cos_ang
        off_y = (i - 1) * sep_val * sin_ang
        scaled = shape_manipulator(context, drawing=shp_max, scale_x=cur_scale, scale_y=cur_scale, offset_x=off_x, offset_y=off_y, mode=manip_mode)
        result.append(scaled)

    return _finish_multi_pieces(result, anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(0.0, 0.0), t=t_clamped)


def _gen_multi_banner(width=200.0, height=50.0, tip_style="Arrow", fold_w=0.0, bord=0.0, t=1.0, anchor="center", context=None, tags="", return_list=False):
    """Parametric procedural banner with 23 named terminal styles (Flat, Arrow, Notch, Round, Concave, Chamfer, Slant, Brace, Fishtail, Crown, etc.)."""
    W = max(1.0, float(width) if width is not None else 200.0)
    H = max(1.0, float(height) if height is not None else 50.0)
    t_clamped = max(0.0, min(1.0, float(t)))
    if t_clamped < 0.0001:
        return _finish_multi_pieces([], anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(W / 2.0, H / 2.0), t=t_clamped)

    eff_w = max(1.0, W * t_clamped)
    bord_val = max(0.0, float(bord) if bord is not None else 0.0)
    fold_val = float(fold_w) if fold_w is not None and float(fold_w) > 0.0 else (H * 0.3)
    F = min(fold_val, eff_w * 0.45)
    M = H / 2.0

    st = str(tip_style or "Arrow").strip().lower().replace("_", "").replace("-", "").replace(" ", "")

    # Alias mapping to canonical style key
    if st in ["flat", "plano", "rect", "square", "[]"]:
        key = "flat"
    elif st in ["notch", "vcut", "swallowtail", "muesca", "cut", "><"]:
        key = "notch"
    elif st in ["round", "capsula", "capsule", "pill", "redondo", "()"]:
        key = "round"
    elif st in ["concave", "concavo", ")("]:
        key = "concave"
    elif st in ["chamfer", "bevel", "bisel", "cyber"]:
        key = "chamfer"
    elif st in ["slant", "inclinado", "//"]:
        key = "slant"
    elif st in ["backslant", "slantinv", "\\\\"]:
        key = "backslant"
    elif st in ["trapezoid", "trapecio"]:
        key = "trapezoid"
    elif st in ["brace", "pergamino", "llave", "scrollbrace", "{}"]:
        key = "brace"
    elif st in ["fishtail", "colapez", "doublenotch"]:
        key = "fishtail"
    elif st in ["crown", "corona", "trident"]:
        key = "crown"
    elif st in ["shield", "escudo", "blason"]:
        key = "shield"
    elif st in ["wave", "onda", "sinusoidal", "scurve", "~~"]:
        key = "wave"
    elif st in ["sawtooth", "sierra", "dientes", "serration", "##"]:
        key = "sawtooth"
    elif st in ["step", "escalon", "almenado", "crenelated", "brick", "=="]:
        key = "step"
    elif st in ["hexagon", "hexagonal", "gem"]:
        key = "hexagon"
    elif st in ["ticket", "boleto", "tab"]:
        key = "ticket"
    elif st in ["diamond", "diamante", "rombo"]:
        key = "diamond"
    elif st in ["pennant", "banderin", "[>"]:
        key = "pennant"
    elif st in ["bannercut", "corte", "[<"]:
        key = "bannercut"
    elif st in ["scroll", "rollo"]:
        key = "scroll"
    elif st in ["flame", "fuego", "llama"]:
        key = "flame"
    else:
        key = "arrow"

    # Vector generation by key
    tokens = []
    pts_left = []
    pts_right = []
    left_bez = None
    right_bez = None

    if key == "flat":
        pts_left = [(0.0, 0.0), (0.0, H)]
        pts_right = [(eff_w, H), (eff_w, 0.0)]
    elif key == "arrow":
        pts_left = [(F, 0.0), (0.0, M), (F, H)]
        pts_right = [(eff_w - F, H), (eff_w, M), (eff_w - F, 0.0)]
    elif key == "notch":
        pts_left = [(0.0, 0.0), (F, M), (0.0, H)]
        pts_right = [(eff_w, H), (eff_w - F, M), (eff_w, 0.0)]
    elif key == "chamfer":
        cf = min(F, H * 0.35)
        pts_left = [(cf, 0.0), (0.0, cf), (0.0, H - cf), (cf, H)]
        pts_right = [(eff_w - cf, H), (eff_w, H - cf), (eff_w, cf), (eff_w - cf, 0.0)]
    elif key == "slant":
        pts_left = [(F, 0.0), (0.0, H)]
        pts_right = [(eff_w - F, H), (eff_w, 0.0)]
    elif key == "backslant":
        pts_left = [(0.0, 0.0), (F, H)]
        pts_right = [(eff_w, H), (eff_w - F, 0.0)]
    elif key == "trapezoid":
        pts_left = [(F, 0.0), (0.0, H)]
        pts_right = [(eff_w, H), (eff_w - F, 0.0)]
    elif key == "brace":
        pts_left = [(F, 0.0), (0.55 * F, 0.15 * H), (0.55 * F, 0.35 * H), (0.0, M), (0.55 * F, 0.65 * H), (0.55 * F, 0.85 * H), (F, H)]
        pts_right = [(eff_w - F, H), (eff_w - 0.55 * F, 0.85 * H), (eff_w - 0.55 * F, 0.65 * H), (eff_w, M), (eff_w - 0.55 * F, 0.35 * H), (eff_w - 0.55 * F, 0.15 * H), (eff_w - F, 0.0)]
    elif key == "fishtail":
        pts_left = [(0.0, 0.0), (F, 0.25 * H), (0.0, M), (F, 0.75 * H), (0.0, H)]
        pts_right = [(eff_w, H), (eff_w - F, 0.75 * H), (eff_w, M), (eff_w - F, 0.25 * H), (eff_w, 0.0)]
    elif key == "crown":
        pts_left = [(F, 0.0), (0.0, 0.25 * H), (F, M), (0.0, 0.75 * H), (F, H)]
        pts_right = [(eff_w - F, H), (eff_w, 0.75 * H), (eff_w - F, M), (eff_w, 0.25 * H), (eff_w - F, 0.0)]
    elif key == "shield":
        pts_left = [(0.0, 0.0), (0.0, 0.5 * H), (F, H)]
        pts_right = [(eff_w - F, H), (eff_w, 0.5 * H), (eff_w, 0.0)]
    elif key == "step":
        pts_left = [(0.0, 0.0), (0.0, 0.3 * H), (F, 0.3 * H), (F, 0.7 * H), (0.0, 0.7 * H), (0.0, H)]
        pts_right = [(eff_w, H), (eff_w, 0.7 * H), (eff_w - F, 0.7 * H), (eff_w - F, 0.3 * H), (eff_w, 0.3 * H), (eff_w, 0.0)]
    elif key == "hexagon":
        pts_left = [(F, 0.0), (0.0, 0.25 * H), (0.0, 0.75 * H), (F, H)]
        pts_right = [(eff_w - F, H), (eff_w, 0.75 * H), (eff_w, 0.25 * H), (eff_w - F, 0.0)]
    elif key == "sawtooth":
        pts_left = [(F, 0.0), (0.0, 0.125 * H), (F, 0.25 * H), (0.0, 0.375 * H), (F, M), (0.0, 0.625 * H), (F, 0.75 * H), (0.0, 0.875 * H), (F, H)]
        pts_right = [(eff_w - F, H), (eff_w, 0.875 * H), (eff_w - F, 0.75 * H), (eff_w, 0.625 * H), (eff_w - F, M), (eff_w, 0.375 * H), (eff_w - F, 0.25 * H), (eff_w, 0.125 * H), (eff_w - F, 0.0)]
    elif key == "diamond":
        pts_left = [(F, 0.0), (0.2 * F, 0.3 * H), (0.0, M), (0.2 * F, 0.7 * H), (F, H)]
        pts_right = [(eff_w - F, H), (eff_w - 0.2 * F, 0.7 * H), (eff_w, M), (eff_w - 0.2 * F, 0.3 * H), (eff_w - F, 0.0)]
    elif key == "pennant":
        pts_left = [(0.0, 0.0), (0.0, H)]
        pts_right = [(eff_w - F, H), (eff_w, M), (eff_w - F, 0.0)]
    elif key == "bannercut":
        pts_left = [(0.0, 0.0), (0.0, H)]
        pts_right = [(eff_w, H), (eff_w - F, M), (eff_w, 0.0)]
    elif key == "scroll":
        pts_left = [(0.0, 0.0), (0.8 * F, 0.1 * H), (F, 0.2 * H), (F, 0.8 * H), (0.8 * F, 0.9 * H), (0.0, H)]
        pts_right = [(eff_w, H), (eff_w - 0.8 * F, 0.9 * H), (eff_w - F, 0.8 * H), (eff_w - F, 0.2 * H), (eff_w - 0.8 * F, 0.1 * H), (eff_w, 0.0)]
    elif key == "flame":
        pts_left = [(F, 0.0), (0.2 * F, 0.2 * H), (0.6 * F, 0.35 * H), (0.0, M), (0.6 * F, 0.65 * H), (0.2 * F, 0.8 * H), (F, H)]
        pts_right = [(eff_w - F, H), (eff_w - 0.2 * F, 0.8 * H), (eff_w - 0.6 * F, 0.65 * H), (eff_w, M), (eff_w - 0.6 * F, 0.35 * H), (eff_w - 0.2 * F, 0.2 * H), (eff_w - F, 0.0)]
    elif key == "round":
        left_bez = "round"
        right_bez = "round"
        pts_left = [(F, 0.0), (F, H)]
        pts_right = [(eff_w - F, H), (eff_w - F, 0.0)]
    elif key == "concave":
        left_bez = "concave"
        right_bez = "concave"
        pts_left = [(0.0, 0.0), (0.0, H)]
        pts_right = [(eff_w, H), (eff_w, 0.0)]
    elif key == "ticket":
        left_bez = "ticket"
        right_bez = "ticket"
        pts_left = [(0.0, 0.0), (0.0, H)]
        pts_right = [(eff_w, H), (eff_w, 0.0)]
    elif key == "wave":
        left_bez = "wave"
        right_bez = "wave"
        pts_left = [(F, 0.0), (0.0, H)]
        pts_right = [(eff_w - F, H), (eff_w, 0.0)]
    else:
        pts_left = [(F, 0.0), (0.0, M), (F, H)]
        pts_right = [(eff_w - F, H), (eff_w, M), (eff_w - F, 0.0)]

    # Construir trazado perimetral ASSDraw
    if left_bez == "round":
        kx = F * 0.55
        ky = M * 0.55
        tokens.append(f"m {_format_num(F)} 0")
        tokens.append(f"b {_format_num(F - kx)} 0 0 {_format_num(M - ky)} 0 {_format_num(M)}")
        tokens.append(f"b 0 {_format_num(M + ky)} {_format_num(F - kx)} {_format_num(H)} {_format_num(F)} {_format_num(H)}")
    elif left_bez == "concave":
        kx = F * 0.55
        ky = M * 0.55
        tokens.append("m 0 0")
        tokens.append(f"b {_format_num(kx)} 0 {_format_num(F)} {_format_num(M - ky)} {_format_num(F)} {_format_num(M)}")
        tokens.append(f"b {_format_num(F)} {_format_num(M + ky)} {_format_num(kx)} {_format_num(H)} 0 {_format_num(H)}")
    elif left_bez == "ticket":
        r_t = min(F, M * 0.7)
        kt = r_t * 0.55
        tokens.append("m 0 0")
        tokens.append(f"l 0 {_format_num(M - r_t)}")
        tokens.append(f"b {_format_num(kt)} {_format_num(M - r_t)} {_format_num(r_t)} {_format_num(M - r_t + kt)} {_format_num(r_t)} {_format_num(M)}")
        tokens.append(f"b {_format_num(r_t)} {_format_num(M + r_t - kt)} {_format_num(kt)} {_format_num(M + r_t)} 0 {_format_num(M + r_t)}")
        tokens.append(f"l 0 {_format_num(H)}")
    elif left_bez == "wave":
        tokens.append(f"m {_format_num(F)} 0")
        tokens.append(f"b 0 0 0 {_format_num(M)} {_format_num(F/2)} {_format_num(M)}")
        tokens.append(f"b {_format_num(F)} {_format_num(M)} {_format_num(F)} {_format_num(H)} 0 {_format_num(H)}")
    else:
        tokens.append(f"m {_format_num(pts_left[0][0])} {_format_num(pts_left[0][1])}")
        for p in pts_left[1:]:
            tokens.append(f"l {_format_num(p[0])} {_format_num(p[1])}")

    # Borde inferior hacia inicio del extremo derecho
    tokens.append(f"l {_format_num(pts_right[0][0])} {_format_num(pts_right[0][1])}")

    if right_bez == "round":
        kx = F * 0.55
        ky = M * 0.55
        tokens.append(f"b {_format_num(eff_w - F + kx)} {_format_num(H)} {_format_num(eff_w)} {_format_num(M + ky)} {_format_num(eff_w)} {_format_num(M)}")
        tokens.append(f"b {_format_num(eff_w)} {_format_num(M - ky)} {_format_num(eff_w - F + kx)} 0 {_format_num(eff_w - F)} 0")
    elif right_bez == "concave":
        kx = F * 0.55
        ky = M * 0.55
        tokens.append(f"b {_format_num(eff_w - kx)} {_format_num(H)} {_format_num(eff_w - F)} {_format_num(M + ky)} {_format_num(eff_w - F)} {_format_num(M)}")
        tokens.append(f"b {_format_num(eff_w - F)} {_format_num(M - ky)} {_format_num(eff_w - kx)} 0 {_format_num(eff_w)} 0")
    elif right_bez == "ticket":
        r_t = min(F, M * 0.7)
        kt = r_t * 0.55
        tokens.append(f"l {_format_num(eff_w)} {_format_num(M + r_t)}")
        tokens.append(f"b {_format_num(eff_w - kt)} {_format_num(M + r_t)} {_format_num(eff_w - r_t)} {_format_num(M + r_t - kt)} {_format_num(eff_w - r_t)} {_format_num(M)}")
        tokens.append(f"b {_format_num(eff_w - r_t)} {_format_num(M - r_t + kt)} {_format_num(eff_w - kt)} {_format_num(M - r_t)} {_format_num(eff_w)} {_format_num(M - r_t)}")
        tokens.append(f"l {_format_num(eff_w)} 0")
    elif right_bez == "wave":
        tokens.append(f"b {_format_num(eff_w)} {_format_num(H)} {_format_num(eff_w)} {_format_num(M)} {_format_num(eff_w - F/2)} {_format_num(M)}")
        tokens.append(f"b {_format_num(eff_w - F)} {_format_num(M)} {_format_num(eff_w - F)} 0 {_format_num(eff_w)} 0")
    else:
        for p in pts_right[1:]:
            tokens.append(f"l {_format_num(p[0])} {_format_num(p[1])}")

    # Cierre del borde superior hacia el inicio del extremo izquierdo
    tokens.append(f"l {_format_num(pts_left[0][0])} {_format_num(pts_left[0][1])}")

    banner_shp = " ".join(tokens) + " "

    if bord_val > 0.0:
        from clipper_engine import ClipperEngine
        border_shp = ClipperEngine.stroke_shape(banner_shp, width=bord_val, join_mode="Miter", cap_mode="Square")
        if return_list:
            return _finish_multi_pieces([banner_shp, border_shp], anchor=anchor, tags=tags, context=context, return_list=True, canonical_center=(W / 2.0, H / 2.0), t=t_clamped)
        else:
            combined = f"{border_shp} {banner_shp}"
            return _finish_multi_pieces([combined], anchor=anchor, tags=tags, context=context, return_list=False, canonical_center=(W / 2.0, H / 2.0), t=t_clamped)

    if return_list:
        p1 = f"m {_format_num(pts_left[0][0])} {_format_num(pts_left[0][1])} " + " ".join([f"l {_format_num(p[0])} {_format_num(p[1])}" for p in pts_left[1:]]) + f" l {_format_num(F)} {_format_num(H)} l {_format_num(F)} 0 l {_format_num(pts_left[0][0])} {_format_num(pts_left[0][1])} "
        p2 = f"m {_format_num(F)} 0 l {_format_num(F)} {_format_num(H)} l {_format_num(eff_w - F)} {_format_num(H)} l {_format_num(eff_w - F)} 0 l {_format_num(F)} 0 "
        p3 = f"m {_format_num(eff_w - F)} 0 l {_format_num(eff_w - F)} {_format_num(H)} " + " ".join([f"l {_format_num(p[0])} {_format_num(p[1])}" for p in pts_right]) + f" l {_format_num(eff_w - F)} 0 "
        return _finish_multi_pieces([p1, p2, p3], anchor=anchor, tags=tags, context=context, return_list=True, canonical_center=(W / 2.0, H / 2.0), t=t_clamped)

    return _finish_multi_pieces([banner_shp], anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(W / 2.0, H / 2.0), t=t_clamped)


def _arc_bezier_segments(r, a_start, a_end):
    """Generates cubic Bézier segments ('b', cp1, cp2, cp3) for a circular arc of radius r
    desde a_start hasta a_end centrado en el origen (0, 0).
    """
    total_delta = a_end - a_start
    if abs(total_delta) < 1e-6 or r <= 0:
        return []
    n_seg = max(1, int(math.ceil(abs(total_delta) / (math.pi / 2.0))))
    d_step = total_delta / n_seg
    segments = []
    for s in range(n_seg):
        a1 = a_start + s * d_step
        a2 = a1 + d_step
        half = (a2 - a1) / 2.0
        k = (4.0 / 3.0) * math.tan(half / 2.0)
        cos1, sin1 = math.cos(a1), math.sin(a1)
        cos2, sin2 = math.cos(a2), math.sin(a2)
        p1 = (r * (cos1 - k * sin1), r * (sin1 + k * cos1))
        p2 = (r * (cos2 + k * sin2), r * (sin2 - k * cos2))
        p3 = (r * cos2, r * sin2)
        segments.append((p1, p2, p3))
    return segments


def _gen_multi_gear(teeth=8, r_out=60.0, r_in=45.0, r_hole=15.0, slant=0.35, t=1.0, anchor="center", context=None, tags="", return_list=False):
    """Parametric gear / sprocket: polar trapezoidal teeth, central hole cut and progressive construction with factor t."""
    n_teeth = max(3, int(round(abs(float(teeth))))) if teeth is not None else 8
    ro = max(1.0, float(r_out) if r_out is not None else 60.0)
    ri = max(0.5, float(r_in) if r_in is not None else 45.0)
    if ri >= ro:
        ri = ro * 0.75
    rh = max(0.0, float(r_hole) if r_hole is not None else 15.0)
    if rh >= ri:
        rh = ri * 0.5
    slant_val = max(0.0, min(0.9, float(slant) if slant is not None else 0.35))
    t_clamped = max(0.0, min(1.0, float(t)))
    if t_clamped < 0.0001:
        return _finish_multi_pieces([], anchor=anchor, tags=tags, context=context, return_list=return_list, canonical_center=(0.0, 0.0), t=t_clamped)

    d_theta = 2.0 * math.pi / n_teeth
    visible_teeth = max(1, int(round(n_teeth * t_clamped))) if t_clamped > 0.001 else 0

    if return_list:
        pieces = []
        for i in range(visible_teeth):
            th_base = i * d_theta
            t0 = th_base
            t1 = th_base + d_theta * (0.25 * slant_val)
            t2 = th_base + d_theta * (0.5 - 0.25 * slant_val)
            t3 = th_base + d_theta * 0.5
            t4 = th_base + d_theta

            p0 = (ri * math.cos(t0), ri * math.sin(t0))
            p1 = (ro * math.cos(t1), ro * math.sin(t1))
            p2 = (ro * math.cos(t2), ro * math.sin(t2))
            p3 = (ri * math.cos(t3), ri * math.sin(t3))
            p4 = (ri * math.cos(t4), ri * math.sin(t4))

            c_in_0 = (rh * math.cos(t0), rh * math.sin(t0)) if rh > 0 else (0.0, 0.0)
            c_in_4 = (rh * math.cos(t4), rh * math.sin(t4)) if rh > 0 else (0.0, 0.0)

            toks = [
                f"m {_format_num(c_in_0[0])} {_format_num(c_in_0[1])}",
                f"l {_format_num(p0[0])} {_format_num(p0[1])}",
                f"l {_format_num(p1[0])} {_format_num(p1[1])}",
                f"l {_format_num(p2[0])} {_format_num(p2[1])}",
                f"l {_format_num(p3[0])} {_format_num(p3[1])}",
                f"l {_format_num(p4[0])} {_format_num(p4[1])}",
                f"l {_format_num(c_in_4[0])} {_format_num(c_in_4[1])}"
            ]
            if rh > 0:
                inner_segs = _arc_bezier_segments(rh, t4, t0)
                for cp1, cp2, cp3 in inner_segs:
                    toks.append(f"b {_format_num(cp1[0])} {_format_num(cp1[1])} {_format_num(cp2[0])} {_format_num(cp2[1])} {_format_num(cp3[0])} {_format_num(cp3[1])}")
            else:
                toks.append(f"l {_format_num(c_in_0[0])} {_format_num(c_in_0[1])}")

            pieces.append(" ".join(toks) + " ")
        return _finish_multi_pieces(pieces, anchor=anchor, tags=tags, context=context, return_list=True, canonical_center=(0.0, 0.0), t=t_clamped)

    all_pts = []
    num_to_draw = visible_teeth if t_clamped < 0.999 else n_teeth
    for i in range(num_to_draw):
        th_base = i * d_theta
        t0 = th_base
        t1 = th_base + d_theta * (0.25 * slant_val)
        t2 = th_base + d_theta * (0.5 - 0.25 * slant_val)
        t3 = th_base + d_theta * 0.5
        t4 = th_base + d_theta

        p0 = (ri * math.cos(t0), ri * math.sin(t0))
        p1 = (ro * math.cos(t1), ro * math.sin(t1))
        p2 = (ro * math.cos(t2), ro * math.sin(t2))
        p3 = (ri * math.cos(t3), ri * math.sin(t3))
        p4 = (ri * math.cos(t4), ri * math.sin(t4))
        all_pts.extend([p0, p1, p2, p3, p4])

    tokens = [f"m {_format_num(all_pts[0][0])} {_format_num(all_pts[0][1])}"]
    for p in all_pts[1:]:
        tokens.append(f"l {_format_num(p[0])} {_format_num(p[1])}")

    if num_to_draw < n_teeth:
        # Engranaje parcial (t < 1.0): el arco interior avanza exactamente con los dientes visibles
        th_end = num_to_draw * d_theta
        if rh > 0:
            p_inner_end = (rh * math.cos(th_end), rh * math.sin(th_end))
            tokens.append(f"l {_format_num(p_inner_end[0])} {_format_num(p_inner_end[1])}")
            inner_segs = _arc_bezier_segments(rh, th_end, 0.0)
            for cp1, cp2, cp3 in inner_segs:
                tokens.append(f"b {_format_num(cp1[0])} {_format_num(cp1[1])} {_format_num(cp2[0])} {_format_num(cp2[1])} {_format_num(cp3[0])} {_format_num(cp3[1])}")
            tokens.append(f"l {_format_num(all_pts[0][0])} {_format_num(all_pts[0][1])}")
        else:
            tokens.append(f"l 0 0 l {_format_num(all_pts[0][0])} {_format_num(all_pts[0][1])}")
    else:
        # Engranaje completo 360 grados: contorno exterior cerrado + orificio central como contorno independiente
        tokens.append(f"l {_format_num(all_pts[0][0])} {_format_num(all_pts[0][1])}")
        if rh > 0:
            k = rh * 0.55228475
            hole = (
                f"m 0 {_format_num(-rh)} "
                f"b {_format_num(-k)} {_format_num(-rh)} {_format_num(-rh)} {_format_num(-k)} {_format_num(-rh)} 0 "
                f"b {_format_num(-rh)} {_format_num(k)} {_format_num(-k)} {_format_num(rh)} 0 {_format_num(rh)} "
                f"b {_format_num(k)} {_format_num(rh)} {_format_num(rh)} {_format_num(k)} {_format_num(rh)} 0 "
                f"b {_format_num(rh)} {_format_num(-k)} {_format_num(k)} {_format_num(-rh)} 0 {_format_num(-rh)}"
            )
            tokens.append(hole)

    gear_shp = " ".join(tokens) + " "
    return _finish_multi_pieces([gear_shp], anchor=anchor, tags=tags, context=context, return_list=False, canonical_center=(0.0, 0.0), t=t_clamped)


def shape_multi(
    context,
    drawing="",
    mode="concentric_squares",
    size=100.0,
    width=70.0,
    height=50.0,
    px="4",
    bord="4",
    space=0.0,
    length=20.0,
    sides=6,
    rings=1,
    n_layers=25,
    dx=0.0,
    dy=0.0,
    parts=12,
    r_out=50.0,
    r_in=0.0,
    size1=100.0,
    size2=10.0,
    loop=8,
    separation=0.0,
    angle=0.0,
    t=1.0,
    anchor="center",
    tags="",
    out_mode="shape",
    loop_mode="shape",
    tip_style="Arrow",
    fold_w=0.0,
    slant=0.35,
    r_hole=15.0,
    order="normal",
    **kwargs
):
    r"""Shape Multi master node: multi-purpose shape generators (multi1 to multi8, banner, gear) with spacing/overlap, anchor, and tag merging.
    Supports 'Shape' mode (monolithic single-line unified drawing) and 'Loops' mode (piece-by-piece using counter m_i and setting m_n).
    Supports 'Shape', '\clip', and '\iclip' formats at both individual piece and monolithic levels.
    """
    from node_engine import _eval_num_expr
    mode_str = str(mode or "concentric_squares").strip()
    mode_clean = mode_str.lower().replace("é", "e").replace("á", "a").replace("í", "i").replace("ó", "o").replace("ú", "u")

    t_val = _eval_num_expr(t, context, 1.0) if (t is not None and t != "") else 1.0
    sep_val = _eval_num_expr(separation if separation is not None else kwargs.get("sep", kwargs.get("space", 0.0)), context, 0.0)
    anc_val = str(anchor if (anchor is not None and str(anchor).strip() != "") else kwargs.get("anchor", kwargs.get("anchor_mode", "center"))).strip().lower()
    tags_val = str(tags if (tags is not None and str(tags).strip() != "") else kwargs.get("tags_str", kwargs.get("tag", ""))).strip()
    order_val = str(order if (order is not None and str(order).strip() != "") else kwargs.get("order", "normal")).strip()
    
    loop_mode_clean = str(loop_mode if (loop_mode is not None and str(loop_mode).strip() != "") else kwargs.get("loop_mode", "shape")).strip().lower()
    out_mode_clean = str(out_mode if (out_mode is not None and str(out_mode).strip() != "") else kwargs.get("out_mode", "shape")).strip().lower()
    return_list = ("loop" in loop_mode_clean) or bool(kwargs.get("return_list", False))

    res = None
    cache_dict = None
    multi_sig = None

    if return_list:
        unit = context.get('active_unit') if isinstance(context, dict) else None
        if not unit and isinstance(context, dict):
            unit = context.get('char') or context.get('syl') or context.get('word')
        if unit is not None:
            if not hasattr(unit, '_multi_cache') or not isinstance(unit._multi_cache, dict):
                unit._multi_cache = {}
            cache_dict = unit._multi_cache
        elif isinstance(context, dict):
            if not isinstance(context.get('_multi_pieces'), dict):
                context['_multi_pieces'] = {}
            cache_dict = context['_multi_pieces']

        if cache_dict is not None:
            unit_id = id(unit) if unit else (id(context.get('line')) if isinstance(context, dict) and context.get('line') else 0)
            multi_sig = (
                unit_id, mode_clean, str(drawing),
                str(size), str(width), str(height), str(px), str(bord),
                str(length), str(sides), str(rings), str(n_layers),
                str(dx), str(dy), str(parts), str(r_out), str(r_in),
                str(size1), str(size2), str(loop),
                round(float(sep_val), 2), str(angle),
                round(float(t_val), 3),
                anc_val, tags_val, out_mode_clean, loop_mode_clean,
                order_val, str(tip_style), str(fold_w), str(slant), str(r_hole),
                str(kwargs.get("space", ""))
            )
            if multi_sig in cache_dict:
                res = cache_dict[multi_sig]

    if res is not None:
        pass
    elif "cuadro" in mode_clean or "square" in mode_clean or "multi1" in mode_clean or "cuadrad" in mode_clean or "concentric_squares" in mode_clean or "pixel" in mode_clean:
        s_val = _eval_num_expr(size, context, 100.0) if (size is not None and size != "") else 100.0
        px_val = px if px is not None else kwargs.get("px_pattern", "4")
        res = _gen_multi1_concentric_squares(size=s_val, px_pattern=px_val, separation=sep_val, t=t_val, anchor=anc_val, context=context, tags=tags_val, return_list=return_list)

    elif "franja" in mode_clean or "diagonal" in mode_clean or "stripe" in mode_clean or "multi2" in mode_clean or "diagonal_stripes" in mode_clean:
        w_val = _eval_num_expr(width, context, 70.0) if (width is not None and width != "") else 70.0
        h_val = _eval_num_expr(height, context, 50.0) if (height is not None and height != "") else 50.0
        px_val = px if px is not None else kwargs.get("px_pattern", "6")
        res = _gen_multi2_diagonal_stripes(width=w_val, height=h_val, px_pattern=px_val, separation=sep_val, t=t_val, anchor=anc_val, context=context, tags=tags_val, return_list=return_list)

    elif "anillo" in mode_clean or "multi3" in mode_clean or "ring" in mode_clean or "concentric_rings" in mode_clean:
        base_shp = drawing if (drawing is not None and str(drawing).strip() != "") else kwargs.get("shape", "")
        s_val = _eval_num_expr(size, context, 100.0) if (size is not None and size != "") else 100.0
        bord_val = bord if bord is not None else kwargs.get("bord_pattern", "4")
        res = _gen_multi3_concentric_rings(base_shape=base_shp, size=s_val, bord_pattern=bord_val, separation=sep_val, t=t_val, anchor=anc_val, context=context, tags=tags_val, return_list=return_list)

    elif "multi-forma" in mode_clean or "multiforma" in mode_clean or "multi-shape" in mode_clean or "multishape" in mode_clean or "multi5" in mode_clean or "multi_shape_mosaic" in mode_clean:
        base_shp = drawing if (drawing is not None and str(drawing).strip() != "") else kwargs.get("shapes", kwargs.get("shape", ""))
        w_val = _eval_num_expr(width, context, 60.0) if (width is not None and width != "") else 60.0
        h_val = _eval_num_expr(height, context, 50.0) if (height is not None and height != "") else 50.0
        dx_val = _eval_num_expr(dx if dx is not None else kwargs.get("sep_x", 0.0), context, 0.0)
        dy_val = _eval_num_expr(dy if dy is not None else kwargs.get("sep_y", 0.0), context, 0.0)
        res = _gen_multi5_multi_shape_mosaic(shapes=base_shp, width=w_val, height=h_val, dx=dx_val, dy=dy_val, t=t_val, anchor=anc_val, context=context, tags=tags_val, return_list=return_list, order=order_val)

    elif "poligon" in mode_clean or "mosaic" in mode_clean or "polygon" in mode_clean or "multi4" in mode_clean or "honeycomb" in mode_clean or "polygonal_mosaic" in mode_clean:
        s_val = _eval_num_expr(size, context, 64.0) if (size is not None and size != "") else 64.0
        sides_val = int(_eval_num_expr(sides, context, 6)) if (sides is not None and sides != "") else 6
        rings_val = int(_eval_num_expr(rings, context, 1)) if (rings is not None and rings != "") else 1
        layers_val = int(_eval_num_expr(n_layers, context, 25)) if (n_layers is not None and n_layers != "") else 25
        res = _gen_multi4_polygonal_mosaic(size=s_val, sides=sides_val, rings=rings_val, n_layers=layers_val, separation=sep_val, t=t_val, anchor=anc_val, context=context, tags=tags_val, return_list=return_list, order=order_val)

    elif "segment" in mode_clean or "borde" in mode_clean or "border" in mode_clean or "multi6" in mode_clean:
        base_shp = drawing if (drawing is not None and str(drawing).strip() != "") else kwargs.get("shape", "")
        w_val = _eval_num_expr(width, context, 104.0) if (width is not None and width != "") else 104.0
        h_val = _eval_num_expr(height, context, 104.0) if (height is not None and height != "") else 104.0
        bord_val = _eval_num_expr(bord, context, 4.0) if (bord is not None and bord != "") else 4.0
        space_val = _eval_num_expr(separation if separation != 0.0 else space, context, 0.0)
        len_val = _eval_num_expr(length, context, 20.0) if (length is not None and length != "") else 20.0
        res = _gen_multi6_segmented_border(base_shape=base_shp, width=w_val, height=h_val, bord=bord_val, space=space_val, length=len_val, separation=space_val, t=t_val, anchor=anc_val, context=context, tags=tags_val, return_list=return_list)

    elif "roseta" in mode_clean or "rosette" in mode_clean or "pastel" in mode_clean or "radial" in mode_clean or "multi7" in mode_clean:
        parts_val = int(_eval_num_expr(parts, context, 12)) if (parts is not None and parts != "") else 12
        r_out_val = _eval_num_expr(r_out, context, 50.0) if (r_out is not None and r_out != "") else 50.0
        r_in_val = _eval_num_expr(r_in, context, 0.0) if (r_in is not None and r_in != "") else 0.0
        res = _gen_multi7_radial_rosette(parts=parts_val, r_out=r_out_val, r_in=r_in_val, separation=sep_val, t=t_val, anchor=anc_val, context=context, tags=tags_val, return_list=return_list)

    elif "tunel" in mode_clean or "cascada" in mode_clean or "multi8" in mode_clean or "tunnel" in mode_clean:
        base_shp = drawing if (drawing is not None and str(drawing).strip() != "") else kwargs.get("shape", "")
        s1_val = _eval_num_expr(size1, context, 100.0) if (size1 is not None and size1 != "") else 100.0
        s2_val = _eval_num_expr(size2, context, 10.0) if (size2 is not None and size2 != "") else 10.0
        loop_val = int(_eval_num_expr(loop, context, 8)) if (loop is not None and loop != "") else 8
        ang_val = angle if angle is not None else kwargs.get("direction", kwargs.get("ang", 0.0))
        res = _gen_multi8_tunnel_cascade(base_shape=base_shp, size1=s1_val, size2=s2_val, loop=loop_val, separation=sep_val, angle=ang_val, t=t_val, anchor=anc_val, context=context, tags=tags_val, return_list=return_list)

    elif "banner" in mode_clean or "cartela" in mode_clean:
        w_val = _eval_num_expr(width, context, 200.0) if (width is not None and width != "") else 200.0
        h_val = _eval_num_expr(height, context, 50.0) if (height is not None and height != "") else 50.0
        tip_val = str(tip_style if tip_style is not None else kwargs.get("style", "<>")).strip()
        fold_val = _eval_num_expr(fold_w if fold_w is not None else kwargs.get("fold_width", 0.0), context, 0.0)
        bord_param = kwargs.get("bord", None)
        if bord_param is None and "border" in kwargs:
            bord_param = kwargs.get("border")
        if bord_param is None:
            bord_param = bord if (bord is not None and str(bord).strip() not in ["", "4"]) else 0.0
        bord_val = _eval_num_expr(bord_param, context, 0.0)
        res = _gen_multi_banner(width=w_val, height=h_val, tip_style=tip_val, fold_w=fold_val, bord=bord_val, t=t_val, anchor=anc_val, context=context, tags=tags_val, return_list=return_list)

    elif "gear" in mode_clean or "engranaje" in mode_clean or "rueda" in mode_clean:
        teeth_val = int(_eval_num_expr(parts if parts is not None else kwargs.get("teeth", kwargs.get("n", 8)), context, 8))
        ro_val = _eval_num_expr(r_out if r_out is not None else kwargs.get("radius", kwargs.get("outer_radius", 60.0)), context, 60.0)
        ri_val = _eval_num_expr(r_in if r_in is not None else kwargs.get("root_radius", kwargs.get("inner_radius", 45.0)), context, 45.0)
        rh_val = _eval_num_expr(r_hole if r_hole is not None else kwargs.get("hole_radius", 15.0), context, 15.0)
        slant_val = _eval_num_expr(slant if slant is not None else kwargs.get("tooth_slant", 0.35), context, 0.35)
        res = _gen_multi_gear(teeth=teeth_val, r_out=ro_val, r_in=ri_val, r_hole=rh_val, slant=slant_val, t=t_val, anchor=anc_val, context=context, tags=tags_val, return_list=return_list)

    else:
        res = _gen_multi1_concentric_squares(size=100.0, px_pattern="4", separation=sep_val, t=t_val, anchor=anc_val, context=context, tags=tags_val, return_list=return_list)

    if return_list:
        pieces = res if isinstance(res, list) else ([res] if res else [])
        if cache_dict is not None and multi_sig is not None and multi_sig not in cache_dict:
            cache_dict[multi_sig] = pieces
        total_pieces = len(pieces)
        
        unit = context.get('active_unit') if isinstance(context, dict) else None
        if not unit and isinstance(context, dict):
            unit = context.get('char') or context.get('syl') or context.get('word')
        line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
        if not line and unit and hasattr(unit, 'line'):
            line = getattr(unit, 'line', None)

        parent_x = float(context.get('pos_x', context.get('line_x', context.get('syl_x', context.get('x', 0.0))))) if isinstance(context, dict) else 0.0
        parent_y = float(context.get('pos_y', context.get('line_y', context.get('syl_y', context.get('y', 0.0))))) if isinstance(context, dict) else 0.0
        if isinstance(context, dict) and context.get('pos_overridden'):
            parent_x = float(context.get('pos_x', parent_x))
            parent_y = float(context.get('pos_y', parent_y))
        elif unit:
            if hasattr(unit, 'center') and unit.center is not None: parent_x = float(unit.center)
            elif hasattr(unit, 'pos_x') and unit.pos_x is not None: parent_x = float(unit.pos_x)
            elif hasattr(unit, 'x') and unit.x is not None: parent_x = float(unit.x)

            if hasattr(unit, 'middle') and unit.middle is not None: parent_y = float(unit.middle)
            elif hasattr(unit, 'pos_y') and unit.pos_y is not None: parent_y = float(unit.pos_y)
            elif hasattr(unit, 'y') and unit.y is not None: parent_y = float(unit.y)
        elif line:
            if hasattr(line, 'center') and line.center is not None: parent_x = float(line.center)
            elif hasattr(line, 'x') and line.x is not None: parent_x = float(line.x)
            if hasattr(line, 'middle') and line.middle is not None: parent_y = float(line.middle)
            elif hasattr(line, 'y') and line.y is not None: parent_y = float(line.y)

        if total_pieces == 0:
            pos_str = f"\\pos({parent_x:.2f},{parent_y:.2f})".rstrip('0').rstrip('.') if (parent_x != 0 or parent_y != 0) else ""
            return "", pos_str, round(parent_x, 2), round(parent_y, 2), 0.0, 0, total_pieces, 1, 1

        if isinstance(context, dict):
            m_i_val = int(float(context.get('m_i', context.get('multi_i', context.get('j', context.get('J', 1))))))
            context['m_i'] = m_i_val
            context['m_n'] = total_pieces
            context['m_max'] = total_pieces
            context['multi_i'] = m_i_val
            context['multi_n'] = total_pieces
            context['multi_max'] = total_pieces
            context['maxloop'] = total_pieces
        else:
            m_i_val = 1

        idx = max(0, min(m_i_val - 1, total_pieces - 1))
        piece_code = pieces[idx]

        bbox_coords = []
        for tok in piece_code.split():
            try:
                bbox_coords.append(float(tok))
            except ValueError:
                pass
        if bbox_coords and len(bbox_coords) >= 2:
            piece_cx = (min(bbox_coords[0::2]) + max(bbox_coords[0::2])) / 2.0
            piece_cy = (min(bbox_coords[1::2]) + max(bbox_coords[1::2])) / 2.0
        else:
            piece_cx, piece_cy = 0.0, 0.0

        abs_x = parent_x + piece_cx
        abs_y = parent_y + piece_cy

        anc_clean = str(anc_val or "center").strip().lower()
        from clipper_engine import ClipperEngine

        if "abs" in anc_clean or "absoluto" in anc_clean:
            if isinstance(context, dict):
                context['pos_overridden'] = False
                context['has_org'] = False
                context['pos_x'] = parent_x
                context['pos_y'] = parent_y
                context['fx_pos_x'] = parent_x
                context['fx_pos_y'] = parent_y
            final_code = ClipperEngine.transform_shape(piece_code, mode="Offset", offset_x=parent_x, offset_y=parent_y)
        elif "rel" in anc_clean:
            if isinstance(context, dict):
                context['pos_overridden'] = False
                context['has_org'] = True
                context['org_x'] = parent_x
                context['org_y'] = parent_y
                context['pos_x'] = parent_x
                context['pos_y'] = parent_y
                context['fx_pos_x'] = parent_x
                context['fx_pos_y'] = parent_y
            final_code = piece_code
        elif any(k in anc_clean for k in ["pieza", "piece", "true"]):
            if isinstance(context, dict):
                context['x'] = abs_x
                context['y'] = abs_y
                context['fx_pos_x'] = abs_x
                context['fx_pos_y'] = abs_y
                context['pos_x'] = abs_x
                context['pos_y'] = abs_y
                context['pos_overridden'] = True
                context['has_org'] = True
                context['org_x'] = abs_x
                context['org_y'] = abs_y
            final_code = ClipperEngine.transform_shape(piece_code, mode="Offset", offset_x=-piece_cx, offset_y=-piece_cy)
        elif "org" in anc_clean:
            if isinstance(context, dict):
                context['x'] = abs_x
                context['y'] = abs_y
                context['fx_pos_x'] = abs_x
                context['fx_pos_y'] = abs_y
                context['pos_x'] = abs_x
                context['pos_y'] = abs_y
                context['pos_overridden'] = True
                context['has_org'] = True
                context['org_x'] = parent_x
                context['org_y'] = parent_y
            final_code = ClipperEngine.transform_shape(piece_code, mode="Offset", offset_x=-piece_cx, offset_y=-piece_cy)
        elif "pos" in anc_clean:
            if isinstance(context, dict):
                context['x'] = abs_x
                context['y'] = abs_y
                context['fx_pos_x'] = abs_x
                context['fx_pos_y'] = abs_y
                context['pos_x'] = abs_x
                context['pos_y'] = abs_y
                context['pos_overridden'] = True
                context['has_org'] = False
            final_code = ClipperEngine.transform_shape(piece_code, mode="Offset", offset_x=-piece_cx, offset_y=-piece_cy)
        else:  # "center" or default
            if isinstance(context, dict):
                context['pos_overridden'] = False
                context['has_org'] = False
                context['pos_x'] = parent_x
                context['pos_y'] = parent_y
                context['fx_pos_x'] = parent_x
                context['fx_pos_y'] = parent_y
            final_code = piece_code

        if "iclip" in out_mode_clean:
            abs_code = ClipperEngine.transform_shape(piece_code, mode="Offset", offset_x=parent_x, offset_y=parent_y)
            final_piece = f"{{\\iclip({abs_code})}}"
        elif "clip" in out_mode_clean:
            abs_code = ClipperEngine.transform_shape(piece_code, mode="Offset", offset_x=parent_x, offset_y=parent_y)
            final_piece = f"{{\\clip({abs_code})}}"
        else:
            final_piece = final_code

        pos_str = f"\\pos({abs_x:.2f},{abs_y:.2f})".rstrip('0').rstrip('.')
        return final_piece, pos_str, round(abs_x, 2), round(abs_y, 2), 0.0, m_i_val, total_pieces, 1, 1

    combined_code = str(res)
    if "iclip" in out_mode_clean:
        final_res = f"{{\\iclip({combined_code})}}"
    elif "clip" in out_mode_clean:
        final_res = f"{{\\clip({combined_code})}}"
    else:
        final_res = combined_code

    if isinstance(context, dict):
        context['m_i'] = 1
        context['m_n'] = 1
        context['m_max'] = 1
        context['maxloop'] = 1

    return final_res


NODE_REGISTRY["Shape/Multi"] = shape_multi
NODE_REGISTRY["Multi"] = shape_multi


def shape_union_divide_node(context, drawing="", shape_b="", mode=None, anchor=None, fill_type=None, clean_self_intersect=None, index_j=None, index_d=None, tags=None, tagmode=None, order=None, **kwargs):
    """Shape Union & Divide node: Decomposes complex vector shapes into real islands (PolyTree),
    merges multiple shapes using boolean Clipper, divides into naive subpaths or fuses with tags,
    with support for geometric anchor modes ('pieces', 'relative', 'origin', 'pos', 'zero')
    and numerical Numpad, radial and circular piece ordering (Order).
    """
    from clipper_engine import ClipperEngine
    from node_engine import _eval_num_expr

    raw_shp = resolve_shape_value(drawing if (drawing is not None and str(drawing).strip() != "") else kwargs.get("shape", kwargs.get("shape_in", kwargs.get("shape_a", ""))), context)
    
    _shp_b_in = shape_b if (shape_b is not None and str(shape_b).strip() != "") else kwargs.get("shape_2", kwargs.get("clip_shape", ""))
    raw_shp_b = resolve_shape_value(_shp_b_in, context) if (_shp_b_in is not None and str(_shp_b_in).strip() != "") else ""

    raw_mode = mode if (mode is not None and str(mode).strip() != "") else kwargs.get("mode", "divide")
    mode_clean = str(raw_mode).strip().lower()
    raw_anchor = anchor if (anchor is not None and str(anchor).strip() != "") else kwargs.get("anchor", "pieces")
    anchor_clean = str(raw_anchor).strip().lower()
    fill_clean = str(fill_type if (fill_type is not None and str(fill_type).strip() != "") else kwargs.get("fill_rule", kwargs.get("fill_type", "evenodd"))).strip().lower()
    order_val = str(order if (order is not None and str(order).strip() != "") else kwargs.get("order", "79")).strip()

    try:
        raw_idx = index_d if index_d is not None else (index_j if index_j is not None else kwargs.get("idx", kwargs.get("d_i", kwargs.get("j", None))))
        if raw_idx is None and isinstance(context, dict):
            raw_idx = context.get('d_i', 1)
        if raw_idx is None:
            raw_idx = 1
        idx_val = int(float(_eval_num_expr(raw_idx, context, 1)))
    except Exception:
        idx_val = 1

    auto_clean = bool(clean_self_intersect if clean_self_intersect is not None else kwargs.get("clean", 1))

    if "union" in mode_clean or "merge" in mode_clean:
        shapes_to_merge = []
        if isinstance(raw_shp, list):
            shapes_to_merge.extend(raw_shp)
        elif raw_shp:
            shapes_to_merge.append(raw_shp)

        if isinstance(raw_shp_b, list):
            shapes_to_merge.extend(raw_shp_b)
        elif raw_shp_b:
            shapes_to_merge.append(raw_shp_b)

        global_bbox = get_drawing_bbox(shapes_to_merge)
        merged = ClipperEngine.merge_multiple_shapes(shapes_to_merge, fill_rule=fill_clean)
        anchored_merged = apply_geometric_anchor(merged, anchor=anchor_clean, context=context, ref_bbox=global_bbox) if merged else ""
        if kwargs.get("return_all_pieces", False) or kwargs.get("return_list", False):
            return [anchored_merged] if anchored_merged else []
        return anchored_merged

    elif "fusi" in mode_clean or "fusion" in mode_clean:
        shapes_list = []
        if isinstance(raw_shp, list):
            for item in raw_shp:
                if isinstance(item, list):
                    shapes_list.extend([str(s).strip() for s in item if str(s).strip()])
                elif item and str(item).strip():
                    shapes_list.append(str(item).strip())
            if len(shapes_list) > 1 and order_val not in ("raw", "none", "0"):
                entries = []
                for s in shapes_list:
                    cnt = ClipperEngine.parse_assdraw(s)
                    if cnt:
                        f_min_x, f_min_y, f_max_x, f_max_y, f_cx, f_cy, f_w, f_h = ClipperEngine.get_bbox(cnt)
                    else:
                        f_min_x = f_min_y = f_max_x = f_max_y = f_cx = f_cy = f_w = f_h = 0.0
                    entries.append({'figure': s, 'min_x': f_min_x, 'min_y': f_min_y, 'max_x': f_max_y, 'max_y': f_max_y, 'cx': f_cx, 'cy': f_cy, 'w': f_w, 'h': f_h})
                sorted_entries = ClipperEngine.sort_islands_by_order(entries, order=order_val)
                shapes_list = [e['figure'] for e in sorted_entries]
        elif raw_shp:
            shapes_list.extend(ClipperEngine.decompose_shape_islands(raw_shp, fill_rule=fill_clean, bbox_mode="marco", clean_self_intersect=auto_clean, order=order_val))

        if "rel" in anchor_clean:
            anchored_list = shapes_list
        else:
            global_bbox = get_drawing_bbox(shapes_list)
            anchored_list = [apply_geometric_anchor(p, anchor=anchor_clean, context=context, ref_bbox=global_bbox) for p in shapes_list]
        tags_val = tags if (tags is not None and str(tags).strip() != "") else kwargs.get("tags_list", kwargs.get("tags", ""))
        tag_mode_val = tagmode if (tagmode is not None and str(tagmode).strip() != "") else kwargs.get("tag_mode", kwargs.get("tagmode", "ipol"))
        fused = ClipperEngine.fusion_shapes_tags(anchored_list, tags=tags_val, bbox_mode="marco", tag_mode=tag_mode_val)
        if kwargs.get("return_all_pieces", False) or kwargs.get("return_list", False):
            return [fused] if fused else []
        return fused

    elif "subpath" in mode_clean or "sub-path" in mode_clean or "naive" in mode_clean:
        if not raw_shp:
            return ""
        pieces = ClipperEngine.decompose_shape_subpaths(raw_shp, bbox_mode="marco", order=order_val)
        if not pieces:
            return ""
        global_bbox = get_drawing_bbox(raw_shp)
        anchor_effective = "center" if anchor_clean == "relative" else anchor_clean
        anchored_pieces = [apply_geometric_anchor(p, anchor=anchor_effective, context=context, ref_bbox=global_bbox) for p in pieces]
        if kwargs.get("return_all_pieces", False) or kwargs.get("return_list", False):
            return anchored_pieces
        target_idx = max(1, min(len(anchored_pieces), idx_val)) - 1
        return anchored_pieces[target_idx]

    else:
        if not raw_shp:
            return ""
        pieces = ClipperEngine.decompose_shape_islands(raw_shp, fill_rule=fill_clean, bbox_mode="marco", clean_self_intersect=auto_clean, order=order_val)
        if not pieces:
            return ""
        global_bbox = get_drawing_bbox(raw_shp)
        anchor_effective = "center" if anchor_clean == "relative" else anchor_clean
        anchored_pieces = [apply_geometric_anchor(p, anchor=anchor_effective, context=context, ref_bbox=global_bbox) for p in pieces]
        if kwargs.get("return_all_pieces", False) or kwargs.get("return_list", False):
            return anchored_pieces
        target_idx = max(1, min(len(anchored_pieces), idx_val)) - 1
        return anchored_pieces[target_idx]


NODE_REGISTRY["Shape/Union & Divide"] = shape_union_divide_node
NODE_REGISTRY["Union & Divide"] = shape_union_divide_node


@pyxis_node("Shape", "Clipper", ["Shape A", "Shape B", "Mode", "Delta (px)", "Subj Fill", "Clip Fill", "Join Mode", "End Mode", "Miter Limit", "Post-Offset", "Clean Dist", "Anchor"])
def shape_clipper_node(
    context,
    shape_a="",
    shape_b="",
    mode="difference",
    delta=0.0,
    subj_fill="evenodd",
    clip_fill="evenodd",
    join_type="round",
    end_type="closed_polygon",
    miter_limit=2.0,
    post_offset="",
    clean_dist=0.0,
    strictly_simple=0,
    reverse_subj=0,
    reverse_clip=0,
    anchor="center",
    out_mode="shape",
    scale=10000.0,
    arc_tolerance=0.25,
    **kwargs
):
    """Shape Clipper node: Dedicated advanced 2D vector boolean, offset, and Minkowski operations.
    Supports Difference, Intersection, Union, XOR, Offset/Inflate, Minkowski Sum and Difference,
    post-boolean offset dilation/contraction, independent fill rules (evenodd, nonzero, positive, negative),
    clean distance, strictly simple topology, path reversal, custom geometric anchors and ASS clip/iclip generation.
    """
    from clipper_engine import ClipperEngine
    from node_engine import _eval_num_expr

    raw_a = resolve_shape_value(
        shape_a if (shape_a is not None and str(shape_a).strip() != "")
        else kwargs.get("shape", kwargs.get("shape_in", kwargs.get("subject", kwargs.get("shape_1", "")))),
        context
    )
    if not raw_a or str(raw_a).strip() == "":
        unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
        line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
        if unit:
            raw_a = getattr(unit, 'text_stripped', getattr(unit, 'text', ''))
        elif line:
            raw_a = getattr(line, 'text_stripped', getattr(line, 'text', ''))

    raw_b = resolve_shape_value(
        shape_b if (shape_b is not None and str(shape_b).strip() != "")
        else kwargs.get("clip_shape", kwargs.get("pattern", kwargs.get("shape_2", ""))),
        context
    )

    raw_mode = mode if (mode is not None and str(mode).strip() != "") else kwargs.get("modo", "difference")
    mode_clean = str(raw_mode).strip().lower()

    raw_delta = delta if delta is not None else kwargs.get("d", kwargs.get("width", 0.0))
    try:
        delta_val = float(_eval_num_expr(raw_delta, context, 0.0))
    except Exception:
        delta_val = 0.0

    raw_post_offset = post_offset if (post_offset is not None and str(post_offset).strip() != "") else kwargs.get("post_offset", kwargs.get("post_delta", kwargs.get("post_desfase", "")))
    try:
        post_offset_val = float(_eval_num_expr(raw_post_offset, context, 0.0)) if str(raw_post_offset).strip() != "" else 0.0
    except Exception:
        post_offset_val = 0.0

    raw_miter = miter_limit if miter_limit is not None else kwargs.get("miter", 2.0)
    try:
        miter_val = float(_eval_num_expr(raw_miter, context, 2.0))
    except Exception:
        miter_val = 2.0

    raw_clean = clean_dist if clean_dist is not None else kwargs.get("clean", 0.0)
    try:
        clean_val = float(_eval_num_expr(raw_clean, context, 0.0))
    except Exception:
        clean_val = 0.0

    raw_arc = arc_tolerance if arc_tolerance is not None else kwargs.get("arc", 0.25)
    try:
        arc_val = float(_eval_num_expr(raw_arc, context, 0.25))
    except Exception:
        arc_val = 0.25

    raw_simple = strictly_simple if strictly_simple is not None else kwargs.get("simple", 0)
    is_simple = bool(int(float(_eval_num_expr(raw_simple, context, 0)))) if str(raw_simple).strip() != "" else False

    raw_rev_s = reverse_subj if reverse_subj is not None else kwargs.get("rev_subj", 0)
    is_rev_s = bool(int(float(_eval_num_expr(raw_rev_s, context, 0)))) if str(raw_rev_s).strip() != "" else False

    raw_rev_c = reverse_clip if reverse_clip is not None else kwargs.get("rev_clip", 0)
    is_rev_c = bool(int(float(_eval_num_expr(raw_rev_c, context, 0)))) if str(raw_rev_c).strip() != "" else False

    raw_anchor = anchor if (anchor is not None and str(anchor).strip() != "") else kwargs.get("anchor", "center")
    anchor_clean = str(raw_anchor).strip().lower()

    raw_out = out_mode if (out_mode is not None and str(out_mode).strip() != "") else kwargs.get("out_mode", "shape")
    out_mode_clean = str(raw_out).strip().lower()

    raw_scale = scale if scale is not None else 10000.0
    try:
        scale_val = float(raw_scale)
    except Exception:
        scale_val = 10000.0

    subj_fill_str = str(subj_fill if subj_fill is not None else "evenodd").strip().lower()
    clip_fill_str = str(clip_fill if clip_fill is not None else "evenodd").strip().lower()
    join_type_str = str(join_type if join_type is not None else "round").strip().lower()
    end_type_str = str(end_type if end_type is not None else "closed_polygon").strip().lower()

    combined_res, pieces_list = ClipperEngine.execute_clipper_advanced(
        subject_shape=raw_a,
        clip_shape=raw_b,
        mode=mode_clean,
        delta=delta_val,
        post_offset=post_offset_val,
        subj_fill=subj_fill_str,
        clip_fill=clip_fill_str,
        join_type=join_type_str,
        end_type=end_type_str,
        miter_limit=miter_val,
        arc_tolerance=arc_val,
        clean_dist=clean_val,
        strictly_simple=is_simple,
        reverse_subj=is_rev_s,
        reverse_clip=is_rev_c,
        scale=scale_val
    )

    if not combined_res:
        if kwargs.get("return_all_pieces", False) or kwargs.get("return_list", False):
            return []
        if kwargs.get("return_bbox", False):
            return {"x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0, "cx": 0.0, "cy": 0.0, "w": 0.0, "h": 0.0}
        return ""

    ref_bbox = get_drawing_bbox([raw_a, raw_b]) if (raw_a or raw_b) else None
    anchored_combined = apply_geometric_anchor(combined_res, anchor=anchor_clean, context=context, ref_bbox=ref_bbox)
    anchored_pieces = [apply_geometric_anchor(p, anchor=anchor_clean, context=context, ref_bbox=ref_bbox) for p in pieces_list]

    if kwargs.get("return_all_pieces", False) or kwargs.get("return_list", False):
        return anchored_pieces

    if kwargs.get("return_bbox", False):
        return ClipperEngine.calc_bbox_raw(anchored_combined)

    if "iclip" in out_mode_clean:
        return f"{{\\iclip({anchored_combined})}}"
    elif "clip" in out_mode_clean:
        return f"{{\\clip({anchored_combined})}}"

    return anchored_combined


NODE_REGISTRY["Shape/Clipper"] = shape_clipper_node
NODE_REGISTRY["Clipper"] = shape_clipper_node



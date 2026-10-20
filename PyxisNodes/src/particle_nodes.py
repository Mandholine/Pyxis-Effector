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

"""
Module: particle_nodes.py
Architectural Role: Vector Contour and Raster Image Particle Emission Engine.

This module provides the core particle generation and spatial distribution algorithms
for subtitle VFX in Pyxis Effector:
    - Text/Vector Particle Emission (`particle_text_node`): Discretises font outlines
      or ASSdraw paths into particles along boundary perimeters or internal grid tessellations.
    - Image Raster Particle Sampling (`particle_image_node`): Samples RGBA pixels from
      static or animated image frames (PNG, JPG, WEBP, GIF), converting colour values
      into ASS colour tags (`&HBBGGRR&`) and opacity channels (`&HAA&`).
    - Numpad Spatial Sorting (`sort_particles`): High-performance vectorised C-level
      ordering using NumPy lexicographical and radial angle transforms.
    - In-Memory LRU Caching: Maintains global bounded caches for sampled points and
      raster frames to optimise multi-pass rendering performance.

Upstream Dependencies:
    - font_vector_engine.py: FontVectorEngine for rasterising font glyphs to ASSdraw paths.
    - clipper_engine.py: ClipperEngine for parsing ASSdraw commands into polygon contours.
    - gpu_engine.py: GPUManager for hardware-accelerated 2D affine point transformations.
    - img_tracer_engine.py: Helper functions for animated GIF frame extraction.

Downstream Callers:
    - node_engine.GraphEngine: Invokes `particle_text_node` for 'Functions/Particles'
      and `particle_image_node` for 'Functions/IMG to pixels'.
"""

import os
import re
import math
import numpy as np
from font_vector_engine import FontVectorEngine
from clipper_engine import ClipperEngine
from gpu_engine import get_gpu_manager
try:
    from nodes.shape_nodes import resolve_shape_value
except (ImportError, ModuleNotFoundError):
    try:
        import importlib
        _mod = importlib.import_module("nodes.shape_nodes")
        resolve_shape_value = getattr(_mod, "resolve_shape_value", None)
    except Exception:
        resolve_shape_value = None

from collections import OrderedDict

_GLOBAL_PARTICLE_PTS_CACHE = OrderedDict()
_GLOBAL_PARTICLE_IMG_CACHE = OrderedDict()
_MAX_PARTICLE_CACHE = 512

def clear_particle_caches():
    """
    Clears all in-memory LRU point and image particle caches.

    Invoked between timeline render passes or upon project reloading to release
    cached coordinate buffers and prevent memory bloat.
    """
    _GLOBAL_PARTICLE_PTS_CACHE.clear()
    _GLOBAL_PARTICLE_IMG_CACHE.clear()


_ASS_COLOR_CACHE = {}

def rgb_to_ass_color(r, g, b):
    """
    Converts 8-bit RGB colour components to an ASS hexadecimal literal (&HBBGGRR&).

    Utilises a bounded global lookup cache to avoid repetitive string formatting
    for identical RGB triplets during dense pixel iterations.

    Args:
        r (int or float): Red channel intensity (0–255).
        g (int or float): Green channel intensity (0–255).
        b (int or float): Blue channel intensity (0–255).

    Returns:
        str: ASS-compatible colour string in BGR hexadecimal notation (e.g. '&HFFFFFF&').
    """
    rgb_key = (int(r), int(g), int(b))
    val = _ASS_COLOR_CACHE.get(rgb_key)
    if val is None:
        val = f"&H{rgb_key[2]:02X}{rgb_key[1]:02X}{rgb_key[0]:02X}&"
        if len(_ASS_COLOR_CACHE) < 65536:
            _ASS_COLOR_CACHE[rgb_key] = val
    return val


def _point_in_contour(x, y, poly):
    """
    Tests whether a 2D coordinate point (x, y) lies inside a closed polygon contour.

    Implements the Ray-Casting parity algorithm. Casts a horizontal semi-infinite ray
    towards positive infinity and counts boundary segment intersections.

    Args:
        x (float): Horizontal coordinate of the test point.
        y (float): Vertical coordinate of the test point.
        poly (list or np.ndarray): Sequence of (px, py) polygon vertices.

    Returns:
        bool: True if the point is strictly enclosed within the polygon; False otherwise.
    """
    n = len(poly)
    if n < 3:
        return False
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def sort_particles(items, order_code="79", get_xy=lambda item: (item[0], item[1])):
    """
    Sorts a collection of 2D particle coordinates according to canonical Numpad orders.

    Utilises vectorised NumPy lexicographical sorting (`np.lexsort`) and polar angle
    computations to achieve high performance across tens of thousands of coordinate points.

    Supported Canonical Order Codes:
        - Contour Trajectory: 'path' (preserves natural arc-length perimeter traversal without
          lexicographical disruption), 'path_inv' (reverses contour trajectory direction).
        - Numpad Directions: '79' (TL->BR), '97' (TR->BL), '13' (BL->TR), '31' (BR->TL),
          '71' (TL->BL by column), '17' (BL->TL by column), '93' (TR->BR by column),
          '39' (BR->TR by column).
        - Radial / Angular: '5' (centre outwards), '-5' (edges inwards), 'cw' (clockwise),
          'ccw' (counter-clockwise).
        - Stochastic: 'rand' / 'random' (in-place pseudo-random shuffling).

    Args:
        items (list or np.ndarray): Collection of particle items or coordinate rows.
        order_code (str): Canonical ordering enumeration code. Defaults to '79'.
        get_xy (Callable): Extraction function returning (x, y) tuple for each item.

    Returns:
        list or np.ndarray: Reordered particle collection matching input container type.
    """
    if items is None or len(items) == 0:
        return items

    order_str = str(order_code or "79").strip().lower()

    if order_str in ("path", "contour", "perimeter"):
        return list(items) if not isinstance(items, np.ndarray) else items.copy()

    if order_str in ("path_inv", "path_reverse", "contour_inv"):
        return list(reversed(items)) if not isinstance(items, np.ndarray) else items[::-1]

    if "rand" in order_str or "random" in order_str:
        items_copy = list(items)
        np.random.shuffle(items_copy)
        return items_copy

    try:
        if isinstance(items, np.ndarray):
            pts_arr = items[:, :2] if items.ndim == 2 else items
        else:
            pts_arr = np.array([get_xy(it) for it in items], dtype=np.float64)

        xs = pts_arr[:, 0]
        ys = pts_arr[:, 1]
    except Exception:
        return items

    if order_str == "5":
        cx, cy = np.mean(xs), np.mean(ys)
        dist_sq = (xs - cx)**2 + (ys - cy)**2
        indices = np.argsort(dist_sq)
    elif order_str in ["-5", "5_inv"]:
        cx, cy = np.mean(xs), np.mean(ys)
        dist_sq = (xs - cx)**2 + (ys - cy)**2
        indices = np.argsort(-dist_sq)
    elif order_str in ("cw", "clock", "clockwise"):
        cx, cy = np.mean(xs), np.mean(ys)
        angles = (np.degrees(np.arctan2(ys - cy, xs - cx)) + 90.0) % 360.0
        indices = np.argsort(angles)
    elif order_str in ("ccw", "counter", "counterclockwise"):
        cx, cy = np.mean(xs), np.mean(ys)
        angles = (360.0 - ((np.degrees(np.arctan2(ys - cy, xs - cx)) + 90.0) % 360.0)) % 360.0
        indices = np.argsort(angles)
    elif order_str == "13":
        indices = np.lexsort((xs, -ys))
    elif order_str == "97":
        indices = np.lexsort((-xs, ys))
    elif order_str == "31":
        indices = np.lexsort((-xs, -ys))
    elif order_str == "71":
        indices = np.lexsort((ys, xs))
    elif order_str == "17":
        indices = np.lexsort((-ys, xs))
    elif order_str == "93":
        indices = np.lexsort((ys, -xs))
    elif order_str == "39":
        indices = np.lexsort((-ys, -xs))
    else:
        indices = np.lexsort((xs, ys))

    if isinstance(items, list):
        return [items[i] for i in indices]
    elif isinstance(items, np.ndarray):
        return items[indices]
    return items


def particle_text_node(context, shape="", particle_shape="", density=10.0, redraw_dist=0.0, seed=1, scale=1.0, mode="outline_v2", order="79", anchor="pieces"):
    """
    Generates discrete particle coordinates from an ASSdraw vector shape or text outline.

    Samples points along continuous perimeter segments or inside polygon bounds,
    applying optional jitter displacement (`redraw_dist`), spatial ordering,
    canonical piece/particle anchor projection, and injecting loop counters (`p_i`, `p_n`, `p_max`)
    into the execution context.

    Args:
        context (dict or FxContext): Active iteration context containing line/unit metrics.
        shape (str): Inbound ASSdraw path or shape name. If empty, extracts from active text.
        particle_shape (str): Custom ASSdraw shape representing individual particle geometry.
        density (float or str): Step distance between sampled points in pixels.
        redraw_dist (float or str): Maximum random displacement applied to each coordinate.
        seed (int or str): Deterministic random number generator seed.
        scale (float or str): Uniform scaling factor applied to coordinates.
        mode (str): Generation mode: 'outline_v2'/'border' (perimeter) or 'inner_fill' (grid test).
        order (str): 2D spatial ordering or contour trajectory code (e.g. 'path', 'path_inv', '79', '5', 'cw', 'rand').
        anchor (str): Canonical anchor mode ('pieces', 'relative', 'parent_org', 'pos', 'absolute').

    Returns:
        tuple[float, float, str, int]:
            - abs_x (float): Absolute horizontal screen coordinate for active particle index.
            - abs_y (float): Absolute vertical screen coordinate for active particle index.
            - p_shape_str (str): ASSdraw path of the resolved particle geometry.
            - total_pts (int): Total number of discrete particles generated.
    """
    from node_engine import _eval_num_expr
    from clipper_engine import ClipperEngine
    from nodes.shape_nodes import resolve_shape_value, resolve_piece_anchor
    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
    
    shp_input = str(shape or "").strip()
    shp_val = ""

    if shp_input:
        if shp_input.lower().startswith("m ") or shp_input.lower().startswith("m-") or shp_input.lower().startswith("m0"):
            shp_val = shp_input
        else:
            shp_val = resolve_shape_value(shp_input, context)

    is_assdraw = bool(shp_val and (str(shp_val).strip().startswith("m ") or str(shp_val).strip().startswith("m-") or str(shp_val).strip().startswith("m0")))
    if not is_assdraw:
        from font_vector_engine import FontVectorEngine
        target_text = shp_input if shp_input else None
        shp_val = FontVectorEngine.from_context(text=target_text, context=context)
        if not shp_val or not (str(shp_val).strip().startswith("m ") or str(shp_val).strip().startswith("m-") or str(shp_val).strip().startswith("m0")):
            shp_val = "m 0 0 l 100 0 l 100 50 l 0 50"

    d_val = max(0.5, float(_eval_num_expr(density, context, 10.0)))
    r_val = max(0.0, float(_eval_num_expr(redraw_dist, context, 0.0)))
    s_val = int(_eval_num_expr(seed, context, 1.0))
    sc_val = float(_eval_num_expr(scale, context, 1.0))
    mode_clean = str(mode or "Contorno v2").strip().lower()

    cache_key = (id(unit) if unit else (id(line) if line else 0), shp_val, str(particle_shape or ""), d_val, r_val, s_val, sc_val, mode_clean, str(order))
    if cache_key in _GLOBAL_PARTICLE_PTS_CACHE:
        sampled_pts = _GLOBAL_PARTICLE_PTS_CACHE[cache_key]
        _GLOBAL_PARTICLE_PTS_CACHE.move_to_end(cache_key)
    else:
        contours = ClipperEngine.parse_assdraw(shp_val)
        if not contours:
            contours = [np.array([[0,0], [100,0], [100,50], [0,50]], dtype=np.float64)]

        np.random.seed(abs(s_val) % 100000)
        sampled_pts = []

        if "relleno" in mode_clean or "interior" in mode_clean or "fill" in mode_clean or "inner" in mode_clean:
            all_pts = np.vstack(contours)
            min_x, min_y = np.min(all_pts, axis=0)
            max_x, max_y = np.max(all_pts, axis=0)
            
            step_grid = max(1.0, d_val)
            x_ticks = np.arange(min_x, max_x + step_grid, step_grid)
            y_ticks = np.arange(min_y, max_y + step_grid, step_grid)
            
            cnt_bboxes = [(cnt, np.min(cnt, axis=0), np.max(cnt, axis=0)) for cnt in contours]
            
            for gy in y_ticks:
                for gx in x_ticks:
                    inside_count = 0
                    for cnt, c_min, c_max in cnt_bboxes:
                        if c_min[0] <= gx <= c_max[0] and c_min[1] <= gy <= c_max[1]:
                            if _point_in_contour(gx, gy, cnt):
                                inside_count += 1
                    if inside_count % 2 == 1:
                        pt = np.array([gx, gy], dtype=np.float64)
                        if r_val > 0:
                            pt = pt + np.random.uniform(-r_val, r_val, size=2)
                        sampled_pts.append(pt * sc_val)
        else:
            for cnt in contours:
                if len(cnt) < 2:
                    continue
                
                if np.linalg.norm(cnt[0] - cnt[-1]) > 1e-5:
                    pts = np.vstack([cnt, cnt[0:1]])
                else:
                    pts = cnt

                diffs = pts[1:] - pts[:-1]
                seg_dists = np.linalg.norm(diffs, axis=1)
                cum_dists = np.zeros(len(pts))
                cum_dists[1:] = np.cumsum(seg_dists)
                total_len = cum_dists[-1]

                if total_len < 1e-5:
                    continue

                step_d = max(0.5, d_val)
                targets = np.arange(0, total_len, step_d)
                
                num_segs = len(seg_dists)
                idx = 0
                for target in targets:
                    while idx < num_segs - 1 and cum_dists[idx + 1] < target:
                        idx += 1
                    seg_len = seg_dists[idx]
                    if seg_len < 1e-5:
                        pt = pts[idx]
                    else:
                        t = (target - cum_dists[idx]) / seg_len
                        pt = (1.0 - t) * pts[idx] + t * pts[idx + 1]
                    
                    if r_val > 0:
                        pt = pt + np.random.uniform(-r_val, r_val, size=2)
                    sampled_pts.append(pt * sc_val)

        if not sampled_pts:
            sampled_pts = [np.array([0.0, 0.0])]

        sampled_pts = sort_particles(sampled_pts, order_code=order, get_xy=lambda pt: (pt[0], pt[1]))
        if len(_GLOBAL_PARTICLE_PTS_CACHE) >= _MAX_PARTICLE_CACHE:
            _GLOBAL_PARTICLE_PTS_CACHE.popitem(last=False)
        _GLOBAL_PARTICLE_PTS_CACHE[cache_key] = sampled_pts

    total_pts = len(sampled_pts)
    if isinstance(context, dict):
        context['p_n'] = total_pts
        context['p_max'] = total_pts
        context['particle_n'] = total_pts
        context['particle_max'] = total_pts
        context['tp_n'] = total_pts
        context['tp_max'] = total_pts
        context['text_p_n'] = total_pts
        context['text_p_max'] = total_pts
        context['tp_loop_count'] = total_pts
        context['maxloop'] = total_pts

    parent_x = float(getattr(unit, 'center', getattr(unit, 'x', getattr(line, 'center', getattr(line, 'x', 0))))) if (unit or line) else 0.0
    parent_y = float(getattr(unit, 'middle', getattr(unit, 'y', getattr(line, 'middle', getattr(line, 'y', 0))))) if (unit or line) else 0.0
    if isinstance(context, dict) and context.get('pos_overridden'):
        parent_x = float(context.get('pos_x', parent_x))
        parent_y = float(context.get('pos_y', parent_y))

    tp_val = int(context.get('tp_i', context.get('p_i', context.get('text_p_i', context.get('fx_i', context.get('i', context.get('j', 1))))))) if isinstance(context, dict) else 1
    idx = max(0, min(tp_val - 1, total_pts - 1))
    pt = sampled_pts[idx]

    p_shape_clean = str(particle_shape or "").strip()
    if p_shape_clean:
        p_shape_str = resolve_shape_value(p_shape_clean, context)
    else:
        p_shape_str = "m 0 0 l 2 0 l 2 2 l 0 2"

    if not p_shape_str or not (str(p_shape_str).strip().startswith("m ") or str(p_shape_str).strip().startswith("m-") or str(p_shape_str).strip().startswith("m0")):
        p_shape_str = "m 0 0 l 2 0 l 2 2 l 0 2"

    cx = float(pt[0])
    cy = float(pt[1])

    anc_res = resolve_piece_anchor(
        piece_code="",
        piece_cx=cx,
        piece_cy=cy,
        parent_x=parent_x,
        parent_y=parent_y,
        anchor=anchor,
        context=context
    )

    anchor_str = str(anchor or "pieces").strip().lower()
    if anchor_str == "absolute":
        final_p_shape = ClipperEngine.transform_shape(p_shape_str, mode="Offset", offset_x=parent_x + cx, offset_y=parent_y + cy)
    else:
        final_p_shape = p_shape_str

    abs_x = round(anc_res['pos_x'], 2)
    abs_y = round(anc_res['pos_y'], 2)

    if isinstance(context, dict):
        context['p_i'] = tp_val
        context['particle_i'] = tp_val
        context['tp_i'] = tp_val
        context['text_p_i'] = tp_val
        context['x'] = abs_x
        context['y'] = abs_y
        context['fx_pos_x'] = abs_x
        context['fx_pos_y'] = abs_y
        context['pos_x'] = abs_x
        context['pos_y'] = abs_y

    return abs_x, abs_y, final_p_shape, total_pts


from decorators import pyxis_node, NODE_REGISTRY

@pyxis_node("Functions", "IMG to pixels", ["Image Path", "Particle", "Frame", "Step", "Alpha", "Scale", "Anchor", "Order"])
def particle_image_node(context, image_path="", particle_shape="", frame="1", step=2, alpha_threshold=128, scale=1.0, anchor="center", order="79", frame_idx=None, **kwargs):
    """
    Samples image raster files into colourised ASS particles with hardware acceleration.

    Parses static images (PNG, JPG, WEBP) or animated GIF frames, extracts pixel coordinates
    meeting alpha thresholds, sorts them using 2D spatial matrices, and formats ASS colour tags.

    Args:
        context (dict or FxContext): Active iteration context holding line and layout metrics.
        image_path (str): File system path to the target image or animated GIF.
        particle_shape (str): Custom ASSdraw geometry used as the pixel particle glyph.
        frame (str or int): 1-based frame index for animated image sources.
        step (int or str): Pixel sampling stride (e.g. 2 samples every second pixel).
        alpha_threshold (int or str): Opacity threshold (0–255) beneath which pixels are discarded.
        scale (float or str): Spatial scaling factor applied to image dimensions.
        anchor (str): Origin alignment mode ('center', 'topleft', 'topright', 'bottomleft', 'bottomright').
        order (str): 2D spatial ordering code (e.g. '79', '13', '5', 'cw', 'rand').
        frame_idx (int, optional): Explicit frame index override.
        **kwargs: Additional keyword arguments forwarded from GraphEngine dispatch.

    Returns:
        tuple[float, float, str, str, str, int]:
            - abs_x (float): Screen horizontal coordinate for active pixel particle.
            - abs_y (float): Screen vertical coordinate for active pixel particle.
            - col_ass (str): Hexadecimal primary colour tag formatted as &HBBGGRR&.
            - alpha_ass (str): Hexadecimal alpha transparency tag formatted as &HAA&.
            - p_shape_str (str): ASSdraw path of the individual pixel particle geometry.
            - total_pixels (int): Total count of valid sampled pixel particles.
    """
    from node_engine import _eval_num_expr
    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)

    parent_x = float(getattr(unit, 'center', getattr(unit, 'x', getattr(line, 'center', getattr(line, 'x', 0))))) if (unit or line) else 0.0
    parent_y = float(getattr(unit, 'middle', getattr(unit, 'y', getattr(line, 'middle', getattr(line, 'y', 0))))) if (unit or line) else 0.0
    if isinstance(context, dict) and context.get('pos_overridden'):
        parent_x = float(context.get('pos_x', parent_x))
        parent_y = float(context.get('pos_y', parent_y))

    path_str = str(image_path or "").strip()
    st = max(1, int(_eval_num_expr(step, context, 2.0)))
    th = int(_eval_num_expr(alpha_threshold, context, 128.0))
    sc = float(_eval_num_expr(scale, context, 1.0))
    anchor_clean = str(anchor or "Center").strip().lower()

    p_shape_clean = str(particle_shape or "").strip()
    box_size = round(st * sc, 2) if (st * sc) > 1.0 else 1.0
    fallback_p_shape = f"m 0 0 l {box_size} 0 l {box_size} {box_size} l 0 {box_size}"

    if not path_str or not os.path.exists(path_str):
        fallback_shape = (resolve_shape_value(p_shape_clean, context) if p_shape_clean else "") or fallback_p_shape
        if not fallback_shape or not (str(fallback_shape).strip().startswith("m ") or str(fallback_shape).strip().startswith("m-") or str(fallback_shape).strip().startswith("m0")):
            fallback_shape = fallback_p_shape
        if isinstance(context, dict):
            context['ip_n'] = 1
            context['ip_i'] = 1
        return parent_x, parent_y, "&HFFFFFF&", "&H00&", fallback_shape, 1

    target_frame = frame_idx if frame_idx is not None else kwargs.get("frame_idx", frame)
    fr_val = int(_eval_num_expr(target_frame, context, 1.0))
    raw_idx = max(0, fr_val - 1) if fr_val >= 1 else max(0, fr_val)

    from img_tracer_engine import _is_animated_gif, _get_or_extract_gif_frames
    target_image_path = path_str
    effective_frame = 0
    if _is_animated_gif(path_str):
        all_frames, n_frames = _get_or_extract_gif_frames(path_str)
        if n_frames > 0:
            effective_frame = raw_idx % n_frames
            target_image_path = all_frames[effective_frame]
    else:
        n_frames = 1

    cache_key = (path_str, effective_frame, st, th, sc, anchor_clean, str(order))
    if cache_key in _GLOBAL_PARTICLE_IMG_CACHE:
        items_data = _GLOBAL_PARTICLE_IMG_CACHE[cache_key]
        _GLOBAL_PARTICLE_IMG_CACHE.move_to_end(cache_key)
    else:
        try:
            from PIL import Image
            img = Image.open(target_image_path).convert("RGBA")
            arr = np.array(img)
            h, w, c = arr.shape

            if anchor_clean == "center":
                off_x, off_y = -w * sc / 2.0, -h * sc / 2.0
            elif anchor_clean == "topright":
                off_x, off_y = -w * sc, 0.0
            elif anchor_clean == "bottomleft":
                off_x, off_y = 0.0, -h * sc
            elif anchor_clean == "bottomright":
                off_x, off_y = -w * sc, -h * sc
            else:  # "topleft" fallback
                off_x, off_y = 0.0, 0.0

            y_indices, x_indices = np.where(arr[:, :, 3] >= th)
            if len(x_indices) == 0:
                items_data = ([(0.0, 0.0, 255, 255, 255, 255)], 0.0, 0.0)
            else:
                mask = (x_indices % st == 0) & (y_indices % st == 0)
                sx = x_indices[mask]
                sy = y_indices[mask]
                if len(sx) == 0:
                    items_data = ([(0.0, 0.0, 255, 255, 255, 255)], 0.0, 0.0)
                else:
                    sampled_rgba = arr[sy, sx]
                    coords_colors = np.column_stack((sx.astype(np.float64), sy.astype(np.float64), sampled_rgba))

                    gpu_mgr = get_gpu_manager()
                    if gpu_mgr.backend.startswith("OpenCL") or gpu_mgr.backend.startswith("CUDA"):
                        coords_colors = gpu_mgr.transform_particles_gpu(coords_colors, scale_x=1.0, scale_y=1.0, angle_deg=0.0)

                    sorted_arr = sort_particles(coords_colors, order_code=order, get_xy=lambda item: (item[0], item[1]))
                    items = [(float(row[0]), float(row[1]), int(row[2]), int(row[3]), int(row[4]), int(row[5])) for row in sorted_arr]
                    items_data = (items, off_x, off_y)
        except Exception as err:
            import traceback
            print(f"[particle_image_node Error] {traceback.format_exc()}", flush=True)
            items_data = ([(0.0, 0.0, 255, 255, 255, 255)], 0.0, 0.0)

        if len(_GLOBAL_PARTICLE_IMG_CACHE) >= _MAX_PARTICLE_CACHE:
            _GLOBAL_PARTICLE_IMG_CACHE.popitem(last=False)
        _GLOBAL_PARTICLE_IMG_CACHE[cache_key] = items_data

    items, off_x, off_y = items_data
    total_pixels = len(items)

    if isinstance(context, dict):
        context['ip_n'] = total_pixels
        context['ip_max'] = total_pixels
        context['img_p_n'] = total_pixels
        context['img_p_max'] = total_pixels
        context['p_n'] = total_pixels
        context['p_max'] = total_pixels
        context['particle_n'] = total_pixels
        context['particle_max'] = total_pixels
        context['total_pixels'] = total_pixels
        context['maxloop'] = total_pixels

    ip_val = int(context.get('ip_i', context.get('img_p_i', context.get('p_i', context.get('particle_i', context.get('fx_i', context.get('i', context.get('j', 1)))))))) if isinstance(context, dict) else 1
    idx = max(0, min(ip_val - 1, total_pixels - 1))

    item = items[idx]
    px = item[0] * sc + off_x
    py = item[1] * sc + off_y

    abs_x = round(parent_x + px, 2)
    abs_y = round(parent_y + py, 2)
    col_ass = rgb_to_ass_color(item[2], item[3], item[4])
    alpha_ass = f"&H{255 - int(item[5]):02X}&"

    if p_shape_clean:
        p_shape_str = resolve_shape_value(p_shape_clean, context)
    else:
        p_shape_str = fallback_p_shape
    if not p_shape_str or not (str(p_shape_str).strip().startswith("m ") or str(p_shape_str).strip().startswith("m-") or str(p_shape_str).strip().startswith("m0")):
        p_shape_str = fallback_p_shape

    if isinstance(context, dict):
        context['ip_i'] = ip_val
        context['img_p_i'] = ip_val
        context['p_i'] = ip_val
        context['particle_i'] = ip_val
        context['x'] = abs_x
        context['y'] = abs_y
        context['fx_pos_x'] = abs_x
        context['fx_pos_y'] = abs_y
        context['pos_x'] = abs_x
        context['pos_y'] = abs_y
        context['pos_overridden'] = True
    return abs_x, abs_y, col_ass, alpha_ass, p_shape_str, total_pixels
 
NODE_REGISTRY["Functions/IMG to pixels"] = particle_image_node
NODE_REGISTRY["IMG to pixels"] = particle_image_node
NODE_REGISTRY["Functions/IMG to Pixels"] = particle_image_node
NODE_REGISTRY["IMG to Pixels"] = particle_image_node

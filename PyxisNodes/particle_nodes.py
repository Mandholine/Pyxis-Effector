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

# particle_nodes.py
"""Nodos del motor de partículas desde contornos de texto (bord_to_pixels_v2) e imágenes raster (Pillow/NumPy)."""

import os
import re
import math
import numpy as np
from font_vector_engine import FontVectorEngine
from clipper_engine import ClipperEngine
from gpu_engine import get_gpu_manager
from nodes.shape_nodes import resolve_shape_value

_GLOBAL_PARTICLE_PTS_CACHE = {}
_GLOBAL_PARTICLE_IMG_CACHE = {}

def clear_particle_caches():
    _GLOBAL_PARTICLE_PTS_CACHE.clear()
    _GLOBAL_PARTICLE_IMG_CACHE.clear()


_ASS_COLOR_CACHE = {}

def rgb_to_ass_color(r, g, b):
    rgb_key = (int(r), int(g), int(b))
    val = _ASS_COLOR_CACHE.get(rgb_key)
    if val is None:
        val = f"&H{rgb_key[2]:02X}{rgb_key[1]:02X}{rgb_key[0]:02X}&"
        if len(_ASS_COLOR_CACHE) < 65536:
            _ASS_COLOR_CACHE[rgb_key] = val
    return val


def _point_in_contour(x, y, poly):
    """Prueba de inclusión Ray-Casting para determinar si (x, y) está dentro del polígono."""
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
    """Ordena una lista de partículas según la dirección del Numpad usando ordenamiento C vectorizado con NumPy."""
    if items is None or len(items) == 0:
        return items

    order_str = str(order_code or "79").strip().lower()
    
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

    if order_str == "5": # Centro -> Afuera (Explosión radial)
        cx, cy = np.mean(xs), np.mean(ys)
        dist_sq = (xs - cx)**2 + (ys - cy)**2
        indices = np.argsort(dist_sq)
    elif order_str in ["-5", "5_inv"]: # Afuera -> Centro (Implosión radial)
        cx, cy = np.mean(xs), np.mean(ys)
        dist_sq = (xs - cx)**2 + (ys - cy)**2
        indices = np.argsort(-dist_sq)
    elif order_str == "13": # Abajo-Izq -> Arriba-Der
        indices = np.lexsort((xs, -ys))
    elif order_str == "97": # Arriba-Der -> Abajo-Izq
        indices = np.lexsort((-xs, ys))
    elif order_str == "31": # Abajo-Der -> Arriba-Izq
        indices = np.lexsort((-xs, -ys))
    elif order_str == "71": # Arriba -> Abajo por columnas
        indices = np.lexsort((ys, xs))
    elif order_str == "17": # Abajo -> Arriba por columnas
        indices = np.lexsort((-ys, xs))
    else: # 79 (Default): Arriba-Izq -> Abajo-Der
        indices = np.lexsort((xs, ys))

    if isinstance(items, list):
        return [items[i] for i in indices]
    elif isinstance(items, np.ndarray):
        return items[indices]
    return items


def particle_text_node(context, shape="", particle_shape="", density=10.0, redraw_dist=0.0, seed=1, scale=1.0, mode="Contorno v2", order="79"):
    """Extrae coordenadas discretas de partículas desde contorno o forma ASSdraw con doble forma y ordenamiento Numpad."""
    from node_engine import _eval_num_expr
    from nodes.shape_nodes import resolve_shape_value
    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
    
    shp_val = resolve_shape_value(shape, context)
    if not shp_val:
        shp_val = getattr(unit, 'text_stripped', getattr(unit, 'text', '')) or getattr(line, 'text_stripped', getattr(line, 'text', 'm 0 0 l 100 0 l 100 100 l 0 100'))

    d_val = max(0.5, float(_eval_num_expr(density, context, 10.0)))
    r_val = max(0.0, float(_eval_num_expr(redraw_dist, context, 0.0)))
    s_val = int(_eval_num_expr(seed, context, 1.0))
    sc_val = float(_eval_num_expr(scale, context, 1.0))
    mode_clean = str(mode or "Contorno v2").strip().lower()

    cache_key = (id(unit) if unit else (id(line) if line else 0), shp_val, str(particle_shape or ""), d_val, r_val, s_val, sc_val, mode_clean, str(order))
    sampled_pts = _GLOBAL_PARTICLE_PTS_CACHE.get(cache_key)

    if sampled_pts is None:
        # Si es texto plano (no comando m x y), convertirlo a forma vectorial
        if shp_val and not shp_val.lower().startswith("m ") and not shp_val.lower().startswith("m-"):
            fn = "Arial"
            fs = int(getattr(unit, 'height', getattr(line, 'height', 40)) or 40)
            b_val = False
            i_val = False
            sc_x = 100.0
            sc_y = 100.0

            styleref = getattr(line, 'styleref', None) if line else None
            if not styleref and unit:
                styleref = getattr(unit, 'styleref', None)
                if not styleref and hasattr(unit, 'line') and getattr(unit, 'line', None):
                    styleref = getattr(unit.line, 'styleref', None)

            if styleref:
                fn = str(getattr(styleref, 'fontname', fn))
                try:
                    fs = int(float(getattr(styleref, 'fontsize', fs)))
                except Exception:
                    pass
                b_val = bool(getattr(styleref, 'bold', False))
                i_val = bool(getattr(styleref, 'italic', False))
                try:
                    sc_x = float(getattr(styleref, 'scale_x', 100.0))
                except Exception:
                    pass
                try:
                    sc_y = float(getattr(styleref, 'scale_y', 100.0))
                except Exception:
                    pass

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

        contours = ClipperEngine.parse_assdraw(shp_val)
        if not contours:
            contours = [np.array([[0,0], [100,0], [100,50], [0,50]], dtype=np.float64)]

        np.random.seed(abs(s_val) % 100000)
        sampled_pts = []

        if "relleno" in mode_clean or "interior" in mode_clean:
            # Modo Relleno Interior por Rejilla 2D con filtro previo de Bounding Box (40x+ aceleración)
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
            # Modo Contorno / Borde con muestreo por longitud de arco acumulada para densidad 100% uniforme
            for cnt in contours:
                if len(cnt) < 2:
                    continue
                
                # Cerrar el contorno si el último punto no es idéntico al primero
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

        # Aplicar Ordenamiento Numpad
        sampled_pts = sort_particles(sampled_pts, order_code=order, get_xy=lambda pt: (pt[0], pt[1]))
        _GLOBAL_PARTICLE_PTS_CACHE[cache_key] = sampled_pts

    total_pts = len(sampled_pts)
    if isinstance(context, dict):
        context['p_n'] = total_pts
        context['p_max'] = total_pts
        context['particle_n'] = total_pts
        context['particle_max'] = total_pts
        context['maxloop'] = total_pts
        if 'j' not in context or context.get('in_auto_slicer_loop'):
            context['maxj'] = total_pts
            context['j_max'] = total_pts

    parent_x = float(getattr(unit, 'center', getattr(unit, 'x', getattr(line, 'center', getattr(line, 'x', 0))))) if (unit or line) else 0.0
    parent_y = float(getattr(unit, 'middle', getattr(unit, 'y', getattr(line, 'middle', getattr(line, 'y', 0))))) if (unit or line) else 0.0

    j_val = int(context.get('p_i', context.get('particle_i', context.get('fx_i', context.get('i', context.get('j', 1)))))) if isinstance(context, dict) else 1
    idx = max(0, min(j_val - 1, total_pts - 1))
    pt = sampled_pts[idx]

    abs_x = round(parent_x + float(pt[0]), 2)
    abs_y = round(parent_y + float(pt[1]), 2)

    if isinstance(context, dict):
        context['p_i'] = j_val
        context['particle_i'] = j_val
        context['x'] = abs_x
        context['y'] = abs_y
        context['fx_pos_x'] = abs_x
        context['fx_pos_y'] = abs_y

    p_shape_str = resolve_shape_value(particle_shape, context)
    if not p_shape_str:
        p_shape_str = "m 0 0 l 2 0 l 2 2 l 0 2"

    return abs_x, abs_y, p_shape_str, total_pts


def particle_image_node(context, image_path="", particle_shape="", frame="1", step=2, alpha_threshold=128, scale=1.0, anchor="Center", order="79"):
    """Muestrea archivos de imagen (PNG, JPG, WEBP, GIF) en partículas ASS coloreadas usando Pillow, NumPy y Numpad ordering."""
    from node_engine import _eval_num_expr
    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)

    parent_x = float(getattr(unit, 'center', getattr(unit, 'x', getattr(line, 'center', getattr(line, 'x', 0))))) if (unit or line) else 0.0
    parent_y = float(getattr(unit, 'middle', getattr(unit, 'y', getattr(line, 'middle', getattr(line, 'y', 0))))) if (unit or line) else 0.0

    path_str = str(image_path or "").strip()
    st = max(1, int(_eval_num_expr(step, context, 2.0)))
    th = int(_eval_num_expr(alpha_threshold, context, 128.0))
    sc = float(_eval_num_expr(scale, context, 1.0))
    anchor_clean = str(anchor or "Center").strip().lower()

    if not path_str or not os.path.exists(path_str):
        box_size = round(st * sc, 2) if (st * sc) > 1.0 else 1.0
        fallback_shape = resolve_shape_value(particle_shape, context) or f"m 0 0 l {box_size} 0 l {box_size} {box_size} l 0 {box_size}"
        return parent_x, parent_y, "&HFFFFFF&", "&H00&", fallback_shape, 1

    fr_val = int(_eval_num_expr(frame, context, 1.0))
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
    items_data = _GLOBAL_PARTICLE_IMG_CACHE.get(cache_key)

    if items_data is None:
        try:
            from PIL import Image
            img = Image.open(target_image_path).convert("RGBA")
            arr = np.array(img)
            h, w, c = arr.shape

            # Cálculo de anclaje
            if "center" in anchor_clean or "centro" in anchor_clean:
                off_x, off_y = -w * sc / 2.0, -h * sc / 2.0
            elif "topright" in anchor_clean:
                off_x, off_y = -w * sc, 0.0
            elif "bottomleft" in anchor_clean:
                off_x, off_y = 0.0, -h * sc
            elif "bottomright" in anchor_clean:
                off_x, off_y = -w * sc, -h * sc
            else: # TopLeft / Default
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

        _GLOBAL_PARTICLE_IMG_CACHE[cache_key] = items_data

    items, off_x, off_y = items_data
    total_pixels = len(items)

    if isinstance(context, dict):
        context['p_n'] = total_pixels
        context['p_max'] = total_pixels
        context['particle_n'] = total_pixels
        context['particle_max'] = total_pixels
        context['total_pixels'] = total_pixels
        context['maxloop'] = total_pixels
        if 'j' not in context or context.get('in_auto_slicer_loop'):
            context['maxj'] = total_pixels
            context['j_max'] = total_pixels

    j_val = int(context.get('p_i', context.get('particle_i', context.get('fx_i', context.get('i', context.get('j', 1)))))) if isinstance(context, dict) else 1
    idx = max(0, min(j_val - 1, total_pixels - 1))

    item = items[idx]
    px = item[0] * sc + off_x
    py = item[1] * sc + off_y

    abs_x = round(parent_x + px, 2)
    abs_y = round(parent_y + py, 2)
    col_ass = rgb_to_ass_color(item[2], item[3], item[4])
    alpha_ass = f"&H{255 - int(item[5]):02X}&"

    p_shape_str = resolve_shape_value(particle_shape, context)
    if not p_shape_str:
        box_size = round(st * sc, 2) if (st * sc) > 1.0 else 1.0
        p_shape_str = f"m 0 0 l {box_size} 0 l {box_size} {box_size} l 0 {box_size}"

    if isinstance(context, dict):
        context['p_i'] = j_val
        context['particle_i'] = j_val
        context['x'] = abs_x
        context['y'] = abs_y
        context['fx_pos_x'] = abs_x
        context['fx_pos_y'] = abs_y
    return abs_x, abs_y, col_ass, alpha_ass, p_shape_str, total_pixels


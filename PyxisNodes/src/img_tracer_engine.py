# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc and Pyxis Effector contributors
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

"""
Image tracing engine to ASSDraw vector shapes (m, l, b) for PyxisNodes.
Supports:
1. Native Python Potrace Bézier engine (cubic curves b x1 y1 x2 y2 x3 y3 + lines l x y).
2. Polygonal engine (Douglas-Peucker) for clean geometry.
3. Sobel/Gradient edge tracer engine.
4. potrace.exe executable integration.
5. Anchor, scale, target dimension (out_w, out_h), threshold, and inversion adjustments.
6. Parameter & mtime caching for real-time execution.
"""

import os
import re
import math
import glob
import subprocess
import tempfile
import hashlib
from typing import Dict, List, Tuple, Any
from PIL import Image, ImageOps, ImageFilter
import numpy as np

from collections import OrderedDict

try:
    import pyclipper
except ImportError:
    pyclipper = None

_TRACER_CACHE: OrderedDict[str, Dict[str, Any]] = OrderedDict()
_MAX_TRACER_CACHE = 512

def clear_tracer_cache():
    """Clears the raster image vector tracing cache."""
    _TRACER_CACHE.clear()


def _get_potrace_exe_path() -> str:
    """Returns path to potrace executable if present and executable."""
    exe_name = "potrace.exe" if os.name == "nt" else "potrace"
    try:
        from paths import get_bin_path
        cand = get_bin_path("potrace")
        if os.path.isfile(cand) and os.path.getsize(cand) > 10000:
            return cand
    except Exception:
        pass
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "bin", exe_name),
        os.path.join(base_dir, "..", "bin", exe_name),
        os.path.join(base_dir, exe_name),
        exe_name
    ]
    for cand in candidates:
        if os.path.isfile(cand) and os.path.getsize(cand) > 10000:
            return cand
    import shutil
    system_potrace = shutil.which("potrace")
    if system_potrace:
        return system_potrace
    return ""


def _get_ffmpeg_exe_path() -> str:
    try:
        from paths import get_bin_path
        cand = get_bin_path("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if os.path.isfile(cand):
            return cand
    except Exception:
        pass
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "bin", "ffmpeg.exe" if os.name == "nt" else "ffmpeg"),
        os.path.join(base_dir, "..", "bin", "ffmpeg.exe" if os.name == "nt" else "ffmpeg"),
        os.path.join(base_dir, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    ]
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    import shutil
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    return ""


def _get_or_create_inverted_webp(image_path: str) -> str:
    if not image_path or not os.path.isfile(image_path):
        return image_path

    try:
        orig_img = Image.open(image_path)
        orig_w, orig_h = orig_img.size
        orig_img.close()
    except Exception:
        return image_path

    try:
        mtime = os.path.getmtime(image_path)
    except Exception:
        mtime = 0.0

    cache_dir = os.path.join(tempfile.gettempdir(), "pyxis_inverted_cache")
    os.makedirs(cache_dir, exist_ok=True)
    h = hashlib.md5(f"{image_path}_{mtime}".encode('utf-8')).hexdigest()
    inverted_webp_path = os.path.join(cache_dir, f"inv_{h}.webp")

    if os.path.isfile(inverted_webp_path) and os.path.getsize(inverted_webp_path) > 100:
        try:
            check_img = Image.open(inverted_webp_path)
            cw, ch = check_img.size
            check_img.close()
            if cw == orig_w and ch == orig_h:
                return inverted_webp_path
        except Exception:
            pass

    ffmpeg_exe = _get_ffmpeg_exe_path()
    if ffmpeg_exe and os.path.isfile(ffmpeg_exe):
        try:
            cmd = [
                ffmpeg_exe,
                "-y",
                "-i", image_path,
                "-vf", "negate",
                inverted_webp_path
            ]
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
            if os.path.isfile(inverted_webp_path) and os.path.getsize(inverted_webp_path) > 100:
                check_img = Image.open(inverted_webp_path)
                cw, ch = check_img.size
                check_img.close()
                if cw == orig_w and ch == orig_h:
                    return inverted_webp_path
        except Exception:
            pass

    try:
        img = Image.open(image_path)
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb_inv = ImageOps.invert(Image.merge('RGB', (r, g, b)))
            inv_img = Image.merge('RGBA', (*rgb_inv.split(), a))
        else:
            inv_img = ImageOps.invert(img.convert('RGB'))

        if inv_img.size != (orig_w, orig_h):
            inv_img = inv_img.resize((orig_w, orig_h), Image.Resampling.LANCZOS)

        inv_img.save(inverted_webp_path, 'WEBP')
        return inverted_webp_path
    except Exception:
        return image_path


def _is_animated_gif(image_path: str) -> bool:
    if not image_path or not os.path.isfile(image_path):
        return False
    ext = os.path.splitext(image_path)[1].lower()
    if ext in ['.gif', '.webp', '.apng']:
        try:
            with Image.open(image_path) as im:
                return getattr(im, "is_animated", False) and im.n_frames > 1
        except Exception:
            return ext == '.gif'
    return False


def _get_or_extract_gif_frames(image_path: str) -> Tuple[List[str], int]:
    if not image_path or not os.path.isfile(image_path):
        return [], 0

    try:
        mtime = os.path.getmtime(image_path)
    except Exception:
        mtime = 0.0

    cache_dir = os.path.join(tempfile.gettempdir(), "pyxis_gif_cache")
    os.makedirs(cache_dir, exist_ok=True)
    h = hashlib.md5(f"{image_path}_{mtime}".encode('utf-8')).hexdigest()
    gif_frame_dir = os.path.join(cache_dir, f"gif_{h}")
    os.makedirs(gif_frame_dir, exist_ok=True)

    existing_frames = sorted(glob.glob(os.path.join(gif_frame_dir, "frame_*.png")))
    if existing_frames and len(existing_frames) > 1:
        return existing_frames, len(existing_frames)

    ffmpeg_exe = _get_ffmpeg_exe_path()
    if ffmpeg_exe and os.path.isfile(ffmpeg_exe):
        try:
            out_pattern = os.path.join(gif_frame_dir, "frame_%04d.png")
            cmd = [
                ffmpeg_exe,
                "-y",
                "-i", image_path,
                out_pattern
            ]
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
            extracted = sorted(glob.glob(os.path.join(gif_frame_dir, "frame_*.png")))
            if extracted:
                return extracted, len(extracted)
        except Exception:
            pass

    try:
        from PIL import ImageSequence
        extracted = []
        with Image.open(image_path) as im:
            for idx, frame in enumerate(ImageSequence.Iterator(im)):
                f_path = os.path.join(gif_frame_dir, f"frame_{idx+1:04d}.png")
                frame.convert("RGBA").save(f_path, "PNG")
                extracted.append(f_path)
        if extracted:
            return extracted, len(extracted)
    except Exception:
        pass

    return [image_path], 1


def _parse_svg_path_to_ass(svg_d: str, img_h: float = 0.0, scale_factor: float = 1.0) -> str:
    """Converts SVG d commands (M, L, C, Z) to ASSDraw commands (m, l, b)."""
    if not svg_d:
        return ""

    tokens = re.findall(r'[a-zA-Z]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?', svg_d)
    if not tokens:
        return ""

    ass_tokens = []
    i = 0
    curr_cmd = ""
    curr_x, curr_y = 0.0, 0.0

    while i < len(tokens):
        tok = tokens[i]
        if tok.isalpha():
            curr_cmd = tok
            i += 1
            cmd_upper = curr_cmd.upper()
            is_relative = curr_cmd.islower()
            if cmd_upper == 'Z':
                continue
        else:
            cmd_upper = curr_cmd.upper()
            is_relative = curr_cmd.islower()

        if cmd_upper == 'M':
            raw_x = float(tokens[i]) * scale_factor
            raw_y = float(tokens[i+1]) * scale_factor
            i += 2
            if is_relative:
                x = curr_x + raw_x
                y = curr_y - raw_y
            else:
                x = raw_x
                y = (img_h - raw_y) if img_h > 0 else raw_y
            curr_x, curr_y = x, y
            ass_tokens.extend(["m", f"{round(x, 2):g}", f"{round(y, 2):g}"])
            curr_cmd = 'l' if is_relative else 'L'

        elif cmd_upper == 'L':
            raw_x = float(tokens[i]) * scale_factor
            raw_y = float(tokens[i+1]) * scale_factor
            i += 2
            if is_relative:
                x = curr_x + raw_x
                y = curr_y - raw_y
            else:
                x = raw_x
                y = (img_h - raw_y) if img_h > 0 else raw_y
            curr_x, curr_y = x, y
            ass_tokens.extend(["l", f"{round(x, 2):g}", f"{round(y, 2):g}"])

        elif cmd_upper == 'C':
            rx1 = float(tokens[i]) * scale_factor
            ry1 = float(tokens[i+1]) * scale_factor
            rx2 = float(tokens[i+2]) * scale_factor
            ry2 = float(tokens[i+3]) * scale_factor
            rx3 = float(tokens[i+4]) * scale_factor
            ry3 = float(tokens[i+5]) * scale_factor
            i += 6
            if is_relative:
                x1 = curr_x + rx1; y1 = curr_y - ry1
                x2 = curr_x + rx2; y2 = curr_y - ry2
                x3 = curr_x + rx3; y3 = curr_y - ry3
            else:
                x1 = rx1; y1 = (img_h - ry1) if img_h > 0 else ry1
                x2 = rx2; y2 = (img_h - ry2) if img_h > 0 else ry2
                x3 = rx3; y3 = (img_h - ry3) if img_h > 0 else ry3
            curr_x, curr_y = x3, y3
            ass_tokens.extend([
                "b",
                f"{round(x1, 2):g}", f"{round(y1, 2):g}",
                f"{round(x2, 2):g}", f"{round(y2, 2):g}",
                f"{round(x3, 2):g}", f"{round(y3, 2):g}"
            ])
        else:
            i += 1

    return " ".join(ass_tokens) + " " if ass_tokens else ""


def _rdp_simplify(points: List[Tuple[float, float]], epsilon: float) -> List[Tuple[float, float]]:
    """Ramer-Douglas-Peucker algorithm for polygon simplification."""
    if len(points) < 3:
        return points

    dmax = 0.0
    index = 0
    end = len(points) - 1

    p1 = np.array(points[0])
    p2 = np.array(points[end])

    line_vec = p2 - p1
    line_len = np.linalg.norm(line_vec)

    for i in range(1, end):
        p = np.array(points[i])
        if line_len == 0:
            d = np.linalg.norm(p - p1)
        else:
            d = np.abs(line_vec[0] * (p1[1] - p[1]) - line_vec[1] * (p1[0] - p[0])) / line_len

        if d > dmax:
            index = i
            dmax = d

    if dmax > epsilon:
        rec1 = _rdp_simplify(points[:index+1], epsilon)
        rec2 = _rdp_simplify(points[index:], epsilon)
        return rec1[:-1] + rec2
    else:
        return [points[0], points[end]]


def _fit_bezier_splines(pts: List[Tuple[float, float]], smooth_factor: float = 0.25) -> List[str]:
    """Converts vertices into smooth cubic ASSDraw Bézier curves (b x1 y1 x2 y2 x3 y3) or lines (l x y)."""
    n = len(pts)
    if n < 3:
        return [f"l {round(p[0], 2):g} {round(p[1], 2):g}" for p in pts[1:]]

    commands = []
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else p2

        v1 = np.array([p1[0] - p0[0], p1[1] - p0[1]])
        v2 = np.array([p2[0] - p1[0], p2[1] - p1[1]])
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        is_corner = False
        if norm1 > 0 and norm2 > 0:
            cos_angle = np.dot(v1, v2) / (norm1 * norm2)
            if cos_angle < 0.2:
                is_corner = True

        if is_corner:
            commands.append(f"l {round(p2[0], 2):g} {round(p2[1], 2):g}")
        else:
            cp1_x = p1[0] + (p2[0] - p0[0]) * smooth_factor
            cp1_y = p1[1] + (p2[1] - p0[1]) * smooth_factor
            cp2_x = p2[0] - (p3[0] - p1[0]) * smooth_factor
            cp2_y = p2[1] - (p3[1] - p1[1]) * smooth_factor
            commands.append(
                f"b {round(cp1_x, 2):g} {round(cp1_y, 2):g} {round(cp2_x, 2):g} {round(cp2_y, 2):g} {round(p2[0], 2):g} {round(p2[1], 2):g}"
            )
    return commands


def _trace_python_native(
    img: Image.Image,
    mode: str,
    threshold: int,
    invert: bool,
    tolerance: float,
    bin_mode: str = "Luminance",
    alphamax: float = 1.0
) -> str:
    """Motor de trazado nativo en Python usando Pillow + Numpy."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    arr = np.array(img)
    alpha = arr[:, :, 3]
    gray = np.array(img.convert('L'))

    binary = np.zeros_like(gray, dtype=np.uint8)

    b_m = str(bin_mode).strip().lower()
    if b_m == "silhouette":
        mask = alpha >= threshold
    elif b_m == "borders":
        gx = np.abs(np.diff(gray.astype(float), axis=1, prepend=0))
        gy = np.abs(np.diff(gray.astype(float), axis=0, prepend=0))
        grad = np.sqrt(gx**2 + gy**2)
        if np.any(alpha < 250):
            mask = (grad >= threshold) & (alpha >= 10)
        else:
            mask = grad >= threshold
    else:  # luminance
        if np.any(alpha < 250):
            mask = (gray < threshold) & (alpha >= 10)
            if not np.any(mask):
                mask = alpha >= 10
        else:
            mask = gray < threshold

    if invert:
        mask = ~mask

    binary[mask] = 255

    mode_clean = str(mode).strip().lower()
    if mode_clean == "borders":
        pil_bin = Image.fromarray(binary).filter(ImageFilter.FIND_EDGES)
        binary = np.array(pil_bin)
        binary = (binary > 50).astype(np.uint8) * 255

    padded = np.pad(binary, 1, mode='constant', constant_values=0)
    h, w = padded.shape
    visited = np.zeros_like(padded, dtype=bool)
    contours = []

    dx = [1, 1, 0, -1, -1, -1, 0, 1]
    dy = [0, 1, 1, 1, 0, -1, -1, -1]

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if padded[y, x] == 255 and not visited[y, x]:
                is_edge = False
                for d in range(8):
                    if padded[y + dy[d], x + dx[d]] == 0:
                        is_edge = True
                        break

                if is_edge:
                    contour_pts = []
                    cx, cy = x, y
                    start_x, start_y = x, y
                    dir_idx = 0
                    steps = 0
                    max_steps = w * h

                    while steps < max_steps:
                        visited[cy, cx] = True
                        contour_pts.append((float(cx - 1), float(cy - 1)))

                        found_next = False
                        for d in range(8):
                            nd = (dir_idx + d) % 8
                            nx, ny = cx + dx[nd], cy + dy[nd]
                            if 0 <= nx < w and 0 <= ny < h:
                                if padded[ny, nx] == 255:
                                    cx, cy = nx, ny
                                    dir_idx = (nd + 5) % 8
                                    found_next = True
                                    break
                        if not found_next or (cx == start_x and cy == start_y and len(contour_pts) > 2):
                            break
                        steps += 1

                    if len(contour_pts) >= 4:
                        contours.append(contour_pts)

    if not contours:
        return ""

    ass_parts = []
    epsilon = max(0.5, float(tolerance))

    s_factor = max(0.0, float(alphamax)) * 0.25

    for c_pts in contours:
        simple_pts = _rdp_simplify(c_pts, epsilon)
        if len(simple_pts) < 3:
            continue

        start_p = simple_pts[0]
        ass_parts.append(f"m {round(start_p[0], 2):g} {round(start_p[1], 2):g}")

        if mode_clean == "potrace":
            bezier_cmds = _fit_bezier_splines(simple_pts, smooth_factor=s_factor)
            ass_parts.extend(bezier_cmds)
        else:  # polygon, borders
            for p in simple_pts[1:]:
                ass_parts.append(f"l {round(p[0], 2):g} {round(p[1], 2):g}")

    return " ".join(ass_parts) + " " if ass_parts else ""


def _parse_ass_bbox(ass_str: str) -> Tuple[float, float, float, float, int]:
    """Calculates Bounding Box (min_x, min_y, max_x, max_y) and total points of an ASSDraw string."""
    tokens = ass_str.strip().split()
    min_x, min_y = 1e9, 1e9
    max_x, max_y = -1e9, -1e9
    pts_count = 0

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ['m', 'l']:
            x = float(tokens[i+1])
            y = float(tokens[i+2])
            i += 3
            pts_count += 1
            min_x = min(min_x, x); max_x = max(max_x, x)
            min_y = min(min_y, y); max_y = max(max_y, y)
        elif tok == 'b':
            x1, y1 = float(tokens[i+1]), float(tokens[i+2])
            x2, y2 = float(tokens[i+3]), float(tokens[i+4])
            x3, y3 = float(tokens[i+5]), float(tokens[i+6])
            i += 7
            pts_count += 3
            for px, py in [(x1, y1), (x2, y2), (x3, y3)]:
                min_x = min(min_x, px); max_x = max(max_x, px)
                min_y = min(min_y, py); max_y = max(max_y, py)
        else:
            i += 1

    if min_x > max_x:
        return 0.0, 0.0, 0.0, 0.0, 0
    return min_x, min_y, max_x, max_y, pts_count


def _transform_ass_shape(
    ass_str: str,
    out_scale: float,
    out_w: float,
    out_h: float,
    anchor: str,
    offset_x: float,
    offset_y: float,
    img_w: float = 0.0,
    img_h: float = 0.0
) -> Tuple[str, float, float, int]:
    """Applies scaling, dynamic resizing, anchor, and offsets to ASSDraw coordinates."""
    if not ass_str.strip():
        return "", 0.0, 0.0, 0

    min_x, min_y, max_x, max_y, pts_count = _parse_ass_bbox(ass_str)
    orig_w = max_x - min_x
    orig_h = max_y - min_y

    ref_canvas_w = img_w if img_w > 0 else orig_w
    ref_canvas_h = img_h if img_h > 0 else orig_h

    if ref_canvas_w <= 0 or ref_canvas_h <= 0:
        return "", 0.0, 0.0, 0

    scale_x = out_scale
    scale_y = out_scale

    if out_w > 0 and out_h > 0:
        scale_x = (out_w / ref_canvas_w) * out_scale
        scale_y = (out_h / ref_canvas_h) * out_scale
    elif out_w > 0:
        scale_x = (out_w / ref_canvas_w) * out_scale
        scale_y = scale_x
    elif out_h > 0:
        scale_y = (out_h / ref_canvas_h) * out_scale
        scale_x = scale_y

    final_w = ref_canvas_w * scale_x
    final_h = ref_canvas_h * scale_y

    anchor_clean = str(anchor).strip().lower()
    if anchor_clean in ("origin", "origen", "topleft"):
        ref_x = 0.0
        ref_y = 0.0
    elif anchor_clean == "bottomleft":
        ref_x = 0.0
        ref_y = ref_canvas_h
    elif anchor_clean == "topright":
        ref_x = ref_canvas_w
        ref_y = 0.0
    elif anchor_clean == "bottomright":
        ref_x = ref_canvas_w
        ref_y = ref_canvas_h
    else:  # "center", "absolute", "absoluto"
        ref_x = ref_canvas_w / 2.0
        ref_y = ref_canvas_h / 2.0

    tokens = ass_str.strip().split()
    out_tokens = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ['m', 'l']:
            raw_x = float(tokens[i+1])
            raw_y = float(tokens[i+2])
            x = (raw_x - ref_x) * scale_x + offset_x
            y = (raw_y - ref_y) * scale_y + offset_y
            out_tokens.extend([tok, f"{round(x, 2):g}", f"{round(y, 2):g}"])
            i += 3
        elif tok == 'b':
            raw_x1, raw_y1 = float(tokens[i+1]), float(tokens[i+2])
            raw_x2, raw_y2 = float(tokens[i+3]), float(tokens[i+4])
            raw_x3, raw_y3 = float(tokens[i+5]), float(tokens[i+6])
            
            x1 = (raw_x1 - ref_x) * scale_x + offset_x
            y1 = (raw_y1 - ref_y) * scale_y + offset_y
            x2 = (raw_x2 - ref_x) * scale_x + offset_x
            y2 = (raw_y2 - ref_y) * scale_y + offset_y
            x3 = (raw_x3 - ref_x) * scale_x + offset_x
            y3 = (raw_y3 - ref_y) * scale_y + offset_y

            out_tokens.extend([
                tok,
                f"{round(x1, 2):g}", f"{round(y1, 2):g}",
                f"{round(x2, 2):g}", f"{round(y2, 2):g}",
                f"{round(x3, 2):g}", f"{round(y3, 2):g}"
            ])
            i += 7
        else:
            out_tokens.append(tok)
            i += 1

    final_shape = " ".join(out_tokens) + " "
    return final_shape, round(final_w, 2), round(final_h, 2), pts_count


def _trace_single_image_file(
    image_path: str,
    mode: str = "Potrace",
    threshold: int = 128,
    invert: bool = False,
    tolerance: float = 1.0,
    out_scale: float = 1.0,
    out_w: float = 0.0,
    out_h: float = 0.0,
    anchor: str = "Center",
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    img_scale: float = 1.0,
    bin_mode: str = "Luminance",
    alphamax: float = 1.0,
    opttoler: float = 0.2,
    turnpolicy: str = "minority"
) -> Dict[str, Any]:
    try:
        mtime = os.path.getmtime(image_path)
    except Exception:
        mtime = 0.0

    cache_key_str = f"{image_path}_{mtime}_{mode}_{threshold}_{invert}_{tolerance}_{out_scale}_{out_w}_{out_h}_{anchor}_{offset_x}_{offset_y}_{img_scale}_{bin_mode}_{alphamax}_{opttoler}_{turnpolicy}"
    cache_key = hashlib.md5(cache_key_str.encode('utf-8')).hexdigest()

    if cache_key in _TRACER_CACHE:
        _TRACER_CACHE.move_to_end(cache_key)
        return _TRACER_CACHE[cache_key]

    try:
        img = Image.open(image_path)
        if img_scale != 1.0 and img_scale > 0:
            nw = max(1, int(img.width * img_scale))
            nh = max(1, int(img.height * img_scale))
            img = img.resize((nw, nh), Image.Resampling.BILINEAR)

        potrace_exe = _get_potrace_exe_path()
        raw_ass_str = ""

        mode_clean = str(mode).strip().lower()
        if mode_clean == "potrace" and potrace_exe:
            try:
                if img.mode != 'RGBA':
                    rgba = img.convert('RGBA')
                else:
                    rgba = img

                arr = np.array(rgba)
                alpha = arr[:, :, 3]
                gray = np.array(img.convert('L'))

                b_m = str(bin_mode).strip().lower()
                if b_m == "silhouette":
                    mask = alpha >= threshold
                elif b_m == "borders":
                    gx = np.abs(np.diff(gray.astype(float), axis=1, prepend=0))
                    gy = np.abs(np.diff(gray.astype(float), axis=0, prepend=0))
                    grad = np.sqrt(gx**2 + gy**2)
                    if np.any(alpha < 250):
                        mask = (grad >= threshold) & (alpha >= 10)
                    else:
                        mask = grad >= threshold
                else:  # luminance
                    if np.any(alpha < 250):
                        mask = (gray < threshold) & (alpha >= 10)
                        if not np.any(mask):
                            mask = alpha >= 10
                    else:
                        mask = gray < threshold

                if invert:
                    mask = ~mask

                bin_array = np.zeros_like(gray, dtype=np.uint8)
                bin_array[mask] = 255

                pgm_array = np.full_like(bin_array, 255)
                pgm_array[bin_array == 255] = 0

                bin_img = Image.fromarray(pgm_array)

                with tempfile.NamedTemporaryFile(suffix='.pgm', delete=False) as tmp_pgm:
                    pgm_path = tmp_pgm.name
                    bin_img.save(pgm_path)

                with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as tmp_svg:
                    svg_path = tmp_svg.name

                cmd = [
                    potrace_exe,
                    "--svg",
                    "-z", "black",
                    "--turdsize", str(int(max(0, tolerance))),
                    "--alphamax", str(float(max(0.0, min(1.33, float(alphamax))))),
                    "--opttoler", str(float(max(0.0, float(opttoler)))),
                    "-o", svg_path,
                    pgm_path
                ]
                if turnpolicy and str(turnpolicy).lower() in ['minority', 'majority', 'black', 'white', 'right', 'left']:
                    cmd.extend(["--turnpolicy", str(turnpolicy).lower()])
                creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)

                with open(svg_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()

                scale_factor = 1.0
                scale_match = re.search(r'scale\(([^,]+),([^)]+)\)', svg_content)
                if scale_match:
                    try:
                        scale_factor = abs(float(scale_match.group(1)))
                    except Exception:
                        scale_factor = 1.0

                paths_d = re.findall(r'd="([^"]+)"', svg_content)
                combined_d = " ".join(paths_d)
                raw_ass_str = _parse_svg_path_to_ass(combined_d, img_h=float(img.height), scale_factor=scale_factor)

                os.remove(pgm_path)
                os.remove(svg_path)
            except Exception:
                raw_ass_str = ""

        if not raw_ass_str:
            raw_ass_str = _trace_python_native(img, mode, threshold, invert, tolerance, bin_mode, alphamax)

        final_shape, width, height, pts_count = _transform_ass_shape(
            raw_ass_str, out_scale, out_w, out_h, anchor, offset_x, offset_y, img_w=float(img.width), img_h=float(img.height)
        )

        res = {
            "shape": final_shape,
            "width": width,
            "height": height,
            "points": pts_count,
            "error": ""
        }
        if len(_TRACER_CACHE) >= _MAX_TRACER_CACHE:
            _TRACER_CACHE.popitem(last=False)
        _TRACER_CACHE[cache_key] = res
        return res

    except Exception as e:
        return {"shape": "", "width": 0.0, "height": 0.0, "points": 0, "error": str(e)}


def trace_image(
    image_path: str,
    mode: str = "Potrace",
    threshold: int = 128,
    invert: bool = False,
    tolerance: float = 1.0,
    out_scale: float = 1.0,
    out_w: float = 0.0,
    out_h: float = 0.0,
    anchor: str = "Center",
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    img_scale: float = 1.0,
    bin_mode: str = "Luminance",
    alphamax: float = 1.0,
    opttoler: float = 0.2,
    turnpolicy: str = "minority",
    frame_index: int = 1,
    invert_img: bool = False
) -> Dict[str, Any]:
    """
    Main function for tracing an image or GIF animation into an ASSDraw shape.
    """
    if not image_path or not os.path.isfile(image_path):
        return {"shape": "", "width": 0.0, "height": 0.0, "points": 0, "total_frames": 1, "frame_index": 1, "shapes_array": "", "error": "Invalid image path"}

    target_image_path = image_path
    total_frames = 1
    target_frame_idx = 1
    all_frames = []

    if _is_animated_gif(image_path):
        all_frames, total_frames = _get_or_extract_gif_frames(image_path)
        if total_frames > 0:
            target_frame_idx = (max(1, int(frame_index)) - 1) % total_frames + 1
            target_image_path = all_frames[target_frame_idx - 1]

    if invert_img:
        target_image_path = _get_or_create_inverted_webp(target_image_path)

    res = _trace_single_image_file(
        image_path=target_image_path,
        mode=mode,
        threshold=threshold,
        invert=invert,
        tolerance=tolerance,
        out_scale=out_scale,
        out_w=out_w,
        out_h=out_h,
        anchor=anchor,
        offset_x=offset_x,
        offset_y=offset_y,
        img_scale=img_scale,
        bin_mode=bin_mode,
        alphamax=alphamax,
        opttoler=opttoler,
        turnpolicy=turnpolicy
    )

    res["total_frames"] = total_frames
    res["frame_index"] = target_frame_idx
    res["preview_image_path"] = target_image_path

    if total_frames > 1 and all_frames:
        shapes_list = []
        for f_path in all_frames:
            f_target = f_path
            if invert_img:
                f_target = _get_or_create_inverted_webp(f_target)
            f_res = _trace_single_image_file(
                image_path=f_target,
                mode=mode,
                threshold=threshold,
                invert=invert,
                tolerance=tolerance,
                out_scale=out_scale,
                out_w=out_w,
                out_h=out_h,
                anchor=anchor,
                offset_x=offset_x,
                offset_y=offset_y,
                img_scale=img_scale,
                bin_mode=bin_mode,
                alphamax=alphamax,
                opttoler=opttoler,
                turnpolicy=turnpolicy
            )
            shapes_list.append(f_res.get("shape", ""))
        res["shapes_array"] = ", ".join(shapes_list)
    else:
        res["shapes_array"] = res.get("shape", "")

    return res

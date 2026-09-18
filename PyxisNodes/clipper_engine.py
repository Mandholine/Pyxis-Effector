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

"""1D/2D slicing engine, 22 mesh generators, and ASSdraw polygon transformations.
Utilizes NumPy and PyClipper for native C-speed mathematical acceleration.
"""

import math
import numpy as np
import re
from collections import OrderedDict

try:
    import pyclipper
except ImportError:
    import subprocess, sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyclipper"])
        import pyclipper
    except Exception:
        pyclipper = None

_MAX_CACHE_SIZE = 1024
_SLICE_GRID_CACHE = OrderedDict()
_PARSE_ASSDRAW_CACHE = OrderedDict()

class ClipperEngine:
    """Vector cutting and slicing operations engine for ASSdraw."""

    MESH_ENGINES = [
        "hex", "tri", "dia", "diamond", "ring", "rings", "voronoi", "delaunay", "brick", "jigsaw",
        "circuit", "kagome", "rhombille", "cubes", "herringbone", "mondrian", "truchet",
        "scallop", "ashlar", "bez", "bezier", "octagon", "ray", "rays", "web", "quad", "pattern", "modular"
    ]

    @staticmethod
    def clear_cache():
        """Clears all in-memory cache stores in ClipperEngine."""
        _SLICE_GRID_CACHE.clear()
        _PARSE_ASSDRAW_CACHE.clear()

    @staticmethod
    def sample_cubic_bezier(p0, p1, p2, p3, steps=10):
        """Samples a cubic Bézier curve between p0 and p3 with control points p1 and p2."""
        pts = []
        x0, y0 = float(p0[0]), float(p0[1])
        x1, y1 = float(p1[0]), float(p1[1])
        x2, y2 = float(p2[0]), float(p2[1])
        x3, y3 = float(p3[0]), float(p3[1])
        for i in range(1, steps + 1):
            t = i / float(steps)
            u = 1.0 - t
            tt = t * t
            uu = u * u
            uuu = uu * u
            ttt = tt * t
            
            x = uuu * x0 + 3.0 * uu * t * x1 + 3.0 * u * tt * x2 + ttt * x3
            y = uuu * y0 + 3.0 * uu * t * y1 + 3.0 * u * tt * y2 + ttt * y3
            pts.append([x, y])
        return pts

    @staticmethod
    def hash_rand(c, r, offset=12345):
        """Deterministic pseudo-random generator by spatial coordinates."""
        s = abs(int(math.floor(c)) * 73856093 + int(math.floor(r)) * 19349663 + int(offset or 12345))
        s = (s * 1103515245 + 12345) % 2147483648
        return s / 2147483648.0

    @staticmethod
    def make_circle(cx, cy, r):
        """Generates a closed ASSDraw circle with smooth polygon approximation."""
        if r <= 0:
            return ""
        segments = max(16, min(64, int(math.ceil(r))))
        pts = []
        for i in range(segments):
            a = math.radians((i / float(segments)) * 360.0)
            pts.append(f"{cx + r * math.cos(a):.3f} {cy + r * math.sin(a):.3f}")
        return f"m {pts[0]} " + " ".join([f"l {p}" for p in pts[1:]]) + f" l {pts[0]}"

    @staticmethod
    def parse_assdraw(shape_str: str, bezier_steps: int = 10, min_points: int = 2):
        """Parses ASSdraw commands (m, l, b, c) into a list of point contours (N, 2),
        flattening Bézier curves into discrete linear segments.
        """
        if not shape_str or not str(shape_str).strip():
            return []

        shape_key = str(shape_str).strip()
        cache_key = (shape_key, int(bezier_steps), int(min_points))
        if cache_key in _PARSE_ASSDRAW_CACHE:
            cached = _PARSE_ASSDRAW_CACHE[cache_key]
            _PARSE_ASSDRAW_CACHE.move_to_end(cache_key)
            return [c.copy() for c in cached]

        tokens = shape_key.split()
        contours = []
        current_contour = []
        i = 0
        n = len(tokens)
        current_cmd = None

        while i < n:
            tok = tokens[i]
            tok_lower = tok.lower()

            if tok_lower in ('m', 'l', 'b', 'c'):
                current_cmd = tok_lower
                i += 1
                if current_cmd == 'c':
                    continue

            if current_cmd == 'm':
                if i + 1 < n:
                    try:
                        x, y = float(tokens[i]), float(tokens[i+1])
                        if len(current_contour) >= min_points:
                            contours.append(np.array(current_contour, dtype=np.float64))
                        current_contour = [[x, y]]
                        current_cmd = 'l'
                        i += 2
                    except ValueError:
                        i += 1
                else:
                    i += 1

            elif current_cmd == 'l':
                if i + 1 < n:
                    try:
                        x, y = float(tokens[i]), float(tokens[i+1])
                        current_contour.append([x, y])
                        i += 2
                    except ValueError:
                        i += 1
                else:
                    i += 1

            elif current_cmd == 'b':
                if i + 5 < n:
                    try:
                        x1, y1 = float(tokens[i]), float(tokens[i+1])
                        x2, y2 = float(tokens[i+2]), float(tokens[i+3])
                        x3, y3 = float(tokens[i+4]), float(tokens[i+5])
                        p0 = current_contour[-1] if current_contour else [0.0, 0.0]
                        sampled = ClipperEngine.sample_cubic_bezier(p0, [x1, y1], [x2, y2], [x3, y3], steps=bezier_steps)
                        current_contour.extend(sampled)
                        i += 6
                    except ValueError:
                        i += 1
                else:
                    i += 1
            else:
                i += 1

        if len(current_contour) >= min_points:
            contours.append(np.array(current_contour, dtype=np.float64))

        if len(_PARSE_ASSDRAW_CACHE) >= _MAX_CACHE_SIZE:
            _PARSE_ASSDRAW_CACHE.popitem(last=False)
        _PARSE_ASSDRAW_CACHE[cache_key] = [c.copy() for c in contours]

        return contours

    @staticmethod
    def get_bbox(contours):
        """Calcula el Bounding Box (min_x, min_y, max_x, max_y, cx, cy, w, h).
        Acepta tanto una lista de contornos numpy como una cadena ASSDraw.
        """
        if isinstance(contours, str):
            contours = ClipperEngine.parse_assdraw(contours)

        if not contours:
            return 0.0, 0.0, 100.0, 100.0, 50.0, 50.0, 100.0, 100.0

        valid_contours = [np.asarray(c, dtype=np.float64) for c in contours if len(c) > 0]
        if not valid_contours:
            return 0.0, 0.0, 100.0, 100.0, 50.0, 50.0, 100.0, 100.0

        all_pts = np.vstack(valid_contours)
        min_x, min_y = np.min(all_pts, axis=0)
        max_x, max_y = np.max(all_pts, axis=0)
        w = max(0.001, max_x - min_x)
        h = max(0.001, max_y - min_y)
        cx = min_x + w * 0.5
        cy = min_y + h * 0.5
        return float(min_x), float(min_y), float(max_x), float(max_y), float(cx), float(cy), float(w), float(h)

    @staticmethod
    def calc_bbox_raw(shape_or_contours):
        """Devuelve diccionario con x1, y1, x2, y2, cx, cy, w, h."""
        min_x, min_y, max_x, max_y, cx, cy, w, h = ClipperEngine.get_bbox(shape_or_contours)
        return {
            "x1": min_x, "y1": min_y,
            "x2": max_x, "y2": max_y,
            "cx": cx, "cy": cy,
            "w": w, "h": h
        }

    @staticmethod
    def boolean_intersection(subject_shape: str, clip_shape: str, scale: float = 10000.0) -> str:
        """Performs real boolean vector intersection between subject_shape and clip_shape using Clipper/pyclipper."""
        subj_contours = ClipperEngine.parse_assdraw(subject_shape)
        clip_contours = ClipperEngine.parse_assdraw(clip_shape)

        if not subj_contours or not clip_contours or pyclipper is None:
            return ""

        try:
            pc = pyclipper.Pyclipper()
            
            for c in subj_contours:
                if len(c) >= 3:
                    pc.AddPath([[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c], pyclipper.PT_SUBJECT, True)
            for c in clip_contours:
                if len(c) >= 3:
                    pc.AddPath([[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c], pyclipper.PT_CLIP, True)

            solution = pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
            if not solution:
                return ""

            code_parts = []
            for path in solution:
                if len(path) >= 3:
                    pts = [[round(x / scale, 2), round(y / scale, 2)] for x, y in path]
                    path_str = f"m {pts[0][0]} {pts[0][1]} " + " ".join([f"l {p[0]} {p[1]}" for p in pts[1:]])
                    code_parts.append(path_str)

            return " ".join(code_parts)
        except Exception:
            return ""

    @staticmethod
    def boolean_difference(subject_shape: str, clip_shape: str, scale: float = 10000.0) -> str:
        """Realiza la diferencia booleana vectorial real entre subject_shape y clip_shape usando Clipper/pyclipper."""
        subj_contours = ClipperEngine.parse_assdraw(subject_shape)
        clip_contours = ClipperEngine.parse_assdraw(clip_shape)

        if not subj_contours or not clip_contours or pyclipper is None:
            return subject_shape

        try:
            pc = pyclipper.Pyclipper()
            for c in subj_contours:
                if len(c) >= 3:
                    pc.AddPath([[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c], pyclipper.PT_SUBJECT, True)
            for c in clip_contours:
                if len(c) >= 3:
                    pc.AddPath([[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c], pyclipper.PT_CLIP, True)

            solution = pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
            if not solution:
                return ""

            code_parts = []
            for path in solution:
                if len(path) >= 3:
                    pts = [[round(x / scale, 2), round(y / scale, 2)] for x, y in path]
                    path_str = f"m {pts[0][0]} {pts[0][1]} " + " ".join([f"l {p[0]} {p[1]}" for p in pts[1:]])
                    code_parts.append(path_str)

            return " ".join(code_parts)
        except Exception:
            return ""

    @staticmethod
    def boolean_union(shape_a: str, shape_b: str, scale: float = 10000.0) -> str:
        """Performs real boolean vector union between shape_a and shape_b using Clipper/pyclipper."""
        a_contours = ClipperEngine.parse_assdraw(shape_a)
        b_contours = ClipperEngine.parse_assdraw(shape_b)

        if not a_contours and not b_contours:
            return ""
        if not a_contours:
            return shape_b
        if not b_contours:
            return shape_a
        if pyclipper is None:
            return shape_a + " " + shape_b

        try:
            pc = pyclipper.Pyclipper()
            for c in a_contours:
                if len(c) >= 3:
                    pc.AddPath([[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c], pyclipper.PT_SUBJECT, True)
            for c in b_contours:
                if len(c) >= 3:
                    pc.AddPath([[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c], pyclipper.PT_SUBJECT, True)

            solution = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
            if not solution:
                return ""

            code_parts = []
            for path in solution:
                if len(path) >= 3:
                    pts = [[round(x / scale, 2), round(y / scale, 2)] for x, y in path]
                    path_str = f"m {pts[0][0]} {pts[0][1]} " + " ".join([f"l {p[0]} {p[1]}" for p in pts[1:]])
                    code_parts.append(path_str)

            return " ".join(code_parts)
        except Exception:
            return shape_a + " " + shape_b

    @staticmethod
    def offset_shape(shape_str: str, delta: float, join_type=None, scale: float = 10000.0) -> str:
        """Expande (delta > 0) o contrae (delta < 0) el contorno de un ASSdraw shape usando PyClipperOffset."""
        if not shape_str or not str(shape_str).strip() or pyclipper is None:
            return shape_str
        if abs(float(delta)) < 0.0001:
            return shape_str

        contours = ClipperEngine.parse_assdraw(shape_str)
        if not contours:
            return shape_str

        try:
            pco = pyclipper.PyclipperOffset(miter_limit=2.0, arc_tolerance=0.25 * scale)
            jt = join_type if join_type is not None else pyclipper.JT_ROUND
            for c in contours:
                if len(c) >= 3:
                    path = [[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c]
                    pco.AddPath(path, jt, pyclipper.ET_CLOSEDPOLYGON)

            solution = pco.Execute(float(delta) * scale)
            if not solution:
                return ""

            try:
                clean_sol = pyclipper.CleanPolygons(solution, distance=0.1 * scale)
                if clean_sol:
                    solution = clean_sol
            except Exception:
                pass

            code_parts = []
            for path in solution:
                if len(path) >= 3:
                    pts = [[round(x / scale, 2), round(y / scale, 2)] for x, y in path]
                    path_str = f"m {pts[0][0]} {pts[0][1]} " + " ".join([f"l {p[0]} {p[1]}" for p in pts[1:]])
                    code_parts.append(path_str)

            return " ".join(code_parts)
        except Exception:
            return shape_str

    @staticmethod
    def contours_to_assdraw(contours) -> str:
        """Convierte una lista de contornos numpy / arrays de puntos a comandos ASSDraw (m x y l x y...)."""
        if not contours:
            return ""
        parts = []
        for cnt in contours:
            if len(cnt) == 0:
                continue
            pts = cnt if isinstance(cnt, (list, tuple)) else cnt.tolist()
            p0 = pts[0]
            seg = [f"m {round(float(p0[0]), 2)} {round(float(p0[1]), 2)}"]
            for p in pts[1:]:
                seg.append(f"l {round(float(p[0]), 2)} {round(float(p[1]), 2)}")
            parts.append(" ".join(seg))
        return " ".join(parts)

    @staticmethod
    def stroke_shape(shape_str: str, width: float = 4.0, join_mode: str = "Round", cap_mode: str = "Round", miter_limit: float = 2.0, scale: float = 10000.0) -> str:
        """Converts open lines or closed contours into closed ASSDraw polygons with uniform thickness.
        - For open lines/splines: generates a continuous strip with terminations (Round, Square, Flat/Butt).
        - For closed polygons: generates a hollow outline (boolean difference between outer and inner offset).
        """
        if not shape_str or not str(shape_str).strip() or pyclipper is None:
            return shape_str
        w = max(0.01, float(width))
        if w < 0.0001:
            return shape_str

        contours = ClipperEngine.parse_assdraw(shape_str, min_points=2)
        if not contours:
            return shape_str

        jm_clean = str(join_mode).strip().lower()
        if "miter" in jm_clean:
            jt = pyclipper.JT_MITER
        elif "bevel" in jm_clean or "square" in jm_clean:
            jt = pyclipper.JT_SQUARE
        else:
            jt = pyclipper.JT_ROUND

        cm_clean = str(cap_mode).strip().lower()
        if "square" in cm_clean:
            et_open = pyclipper.ET_OPENSQUARE
        elif "flat" in cm_clean or "butt" in cm_clean:
            et_open = pyclipper.ET_OPENBUTT
        elif "bezier" in cm_clean or "round" in cm_clean:
            et_open = pyclipper.ET_OPENROUND
        else:
            et_open = pyclipper.ET_OPENROUND

        results = []
        for c in contours:
            if len(c) < 2:
                continue
            is_closed = len(c) >= 3 and (abs(float(c[0][0]) - float(c[-1][0])) < 1e-4 and abs(float(c[0][1]) - float(c[-1][1])) < 1e-4)

            if is_closed:
                c_str = ClipperEngine.contours_to_assdraw([c])
                outer = ClipperEngine.offset_shape(c_str, delta=w / 2.0, join_type=jt, scale=scale)
                inner = ClipperEngine.offset_shape(c_str, delta=-w / 2.0, join_type=jt, scale=scale)
                diff = ClipperEngine.boolean_difference(outer, inner, scale=scale)
                if diff and diff.strip():
                    results.append(diff)
                elif outer and outer.strip():
                    results.append(outer)
            else:
                try:
                    pco = pyclipper.PyclipperOffset(miter_limit=float(miter_limit), arc_tolerance=0.25 * scale)
                    path = [[int(round(float(pt[0]) * scale)), int(round(float(pt[1]) * scale))] for pt in c]
                    pco.AddPath(path, jt, et_open)
                    solution = pco.Execute((w / 2.0) * scale)
                    if not solution:
                        continue
                    try:
                        clean_sol = pyclipper.CleanPolygons(solution, distance=0.1 * scale)
                        if clean_sol:
                            solution = clean_sol
                    except Exception:
                        pass
                    code_parts = []
                    for path in solution:
                        if len(path) >= 3:
                            pts = [[round(x / scale, 2), round(y / scale, 2)] for x, y in path]
                            path_str = f"m {pts[0][0]} {pts[0][1]} " + " ".join([f"l {p[0]} {p[1]}" for p in pts[1:]])
                            code_parts.append(path_str)
                    if code_parts:
                        results.append(" ".join(code_parts))
                except Exception:
                    continue

        return " ".join(results)

    @staticmethod
    def slice_grid(shape_str: str, cols: int = 2, rows: int = 2, size_x: float = 0.0, size_y: float = 0.0,
                   scale_x: float = 1.0, scale_y: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0,
                   angle: float = 0.0, overlap: float = 0.0, accel: float = 1.0, order: int = 79,
                   text_scale: float = 1.0, pre_offset: float = 0.0, engine_mode: str = "grid",
                   accel_x: float = 1.0, accel_y: float = 1.0, pattern_shape: str = ""):
        """Universal 1D/2D slicer and 22 mesh engines.
        Supports dual scaling (scale_x, scale_y), custom sizes (size_x, size_y), offsetting (offset_x, offset_y),
        and text pre-scaling (text_scale) along with original contour pre-offsetting (pre_offset).
        Returns a list of dictionaries with {code, cx, cy, col, row}.
        """
        if accel != 1.0:
            if accel_x == 1.0: accel_x = accel
            if accel_y == 1.0: accel_y = accel

        norm_mode = str(engine_mode).lower().strip()
        cache_key = (
            str(shape_str).strip(),
            norm_mode,
            int(cols), int(rows),
            round(float(size_x), 3), round(float(size_y), 3),
            round(float(scale_x), 3), round(float(scale_y), 3),
            round(float(offset_x), 3), round(float(offset_y), 3),
            round(float(angle), 2), round(float(overlap), 2),
            round(float(accel_x), 3), round(float(accel_y), 3),
            int(order),
            round(float(text_scale), 3), round(float(pre_offset), 3),
            str(pattern_shape).strip()
        )

        if cache_key in _SLICE_GRID_CACHE:
            cached = _SLICE_GRID_CACHE[cache_key]
            _SLICE_GRID_CACHE.move_to_end(cache_key)
            return [p.copy() for p in cached]

        if text_scale != 1.0:
            shape_str = ClipperEngine.transform_shape(shape_str, mode="Escalar", factor=text_scale)

        if pre_offset != 0.0:
            shape_str = ClipperEngine.offset_shape(shape_str, delta=pre_offset)

        contours = ClipperEngine.parse_assdraw(shape_str)
        if not contours:
            return []

        min_x, min_y, max_x, max_y, cx, cy, w, h = ClipperEngine.get_bbox(contours)

        cols = max(1, int(cols))
        rows = max(1, int(rows))
        ang_rad = math.radians(-angle)
        cos_a, sin_a = math.cos(ang_rad), math.sin(ang_rad)

        mode_key = str(engine_mode).lower().strip()

        D_w = (w * abs(cos_a) + h * abs(sin_a) + 0.1) * float(scale_x)
        D_h = (h * abs(cos_a) + w * abs(sin_a) + 0.1) * float(scale_y)

        def rot_point(lx, ly):
            return cx + lx * cos_a - ly * sin_a, cy + lx * sin_a + ly * cos_a

        masks = []

        if mode_key in ["hex", "hexagonal"]:
            R = max(2.0, float(size_x)) if (size_x and float(size_x) > 0) else max(5.0, h / 3.5)
            H = 1.73205081 * R
            c_start = int(math.floor(min_x / (1.5 * R))) - 1
            c_end = int(math.ceil(max_x / (1.5 * R))) + 1
            r_start = int(math.floor(min_y / H)) - 1
            r_end = int(math.ceil(max_y / H)) + 1
            for c in range(c_start, c_end + 1):
                for r in range(r_start, r_end + 1):
                    screen_cx = c * 1.5 * R
                    screen_cy = r * H
                    if abs(c % 2) == 1:
                        screen_cy += H / 2.0
                    hex_code = f"m {screen_cx + R:.3f} {screen_cy:.3f} l {screen_cx + R*0.5:.3f} {screen_cy + R*0.866025:.3f} l {screen_cx - R*0.5:.3f} {screen_cy + R*0.866025:.3f} l {screen_cx - R:.3f} {screen_cy:.3f} l {screen_cx - R*0.5:.3f} {screen_cy - R*0.866025:.3f} l {screen_cx + R*0.5:.3f} {screen_cy - R*0.866025:.3f} l {screen_cx + R:.3f} {screen_cy:.3f}"
                    masks.append({"code": hex_code, "cx": screen_cx, "cy": screen_cy, "col": c, "row": r})

        elif mode_key in ["tri", "triangular"]:
            R = max(2.0, float(size_x)) if (size_x and float(size_x) > 0) else max(5.0, h / 3.5)
            L = R * 2.0
            H = L * 0.86602540378
            c_start = int(math.floor(min_x / L)) - 1
            c_end = int(math.ceil(max_x / L)) + 1
            r_start = int(math.floor(min_y / H)) - 1
            r_end = int(math.ceil(max_y / H)) + 1
            for r in range(r_start, r_end + 1):
                y1, y2 = r * H, (r + 1) * H
                for c in range(c_start, c_end + 1):
                    base_x = c * L
                    if abs(r % 2) == 0:
                        up_cx, down_cx = base_x, base_x + L/2.0
                    else:
                        down_cx, up_cx = base_x, base_x + L/2.0
                    u_cx, u_cy = up_cx, y1
                    tri_up = f"m {u_cx:.3f} {u_cy:.3f} l {u_cx - L/2.0:.3f} {u_cy + H:.3f} l {u_cx + L/2.0:.3f} {u_cy + H:.3f} l {u_cx:.3f} {u_cy:.3f}"
                    masks.append({"code": tri_up, "cx": u_cx, "cy": u_cy + (2*H/3.0), "col": c, "row": r})
                    d_cx, d_cy = down_cx, y2
                    tri_down = f"m {d_cx - L/2.0:.3f} {d_cy - H:.3f} l {d_cx + L/2.0:.3f} {d_cy - H:.3f} l {d_cx:.3f} {d_cy:.3f} l {d_cx - L/2.0:.3f} {d_cy - H:.3f}"
                    masks.append({"code": tri_down, "cx": d_cx, "cy": d_cy - (2*H/3.0), "col": c, "row": r})

        elif mode_key in ["dia", "diamante", "diamond", "rombos"]:
            R = max(2.0, float(size_x)) if (size_x and float(size_x) > 0) else max(5.0, h / 3.5)
            H_step, W_step = R, R * 2.0
            c_start = int(math.floor(min_x / W_step)) - 1
            c_end = int(math.ceil(max_x / W_step)) + 1
            r_start = int(math.floor(min_y / H_step)) - 1
            r_end = int(math.ceil(max_y / H_step)) + 1
            for r in range(r_start, r_end + 1):
                for c in range(c_start, c_end + 1):
                    screen_cx = c * W_step
                    screen_cy = r * H_step
                    if abs(r % 2) == 1:
                        screen_cx += R
                    dia_code = f"m {screen_cx:.3f} {screen_cy - R:.3f} l {screen_cx + R:.3f} {screen_cy:.3f} l {screen_cx:.3f} {screen_cy + R:.3f} l {screen_cx - R:.3f} {screen_cy:.3f} l {screen_cx:.3f} {screen_cy - R:.3f}"
                    masks.append({"code": dia_code, "cx": screen_cx, "cy": screen_cy, "col": c, "row": r})

        elif mode_key in ["ring", "anillos", "rings"]:
            ring_w = max(2.0, float(size_x)) if (size_x and float(size_x) > 0) else max(4.0, h / 5.0)
            max_r = math.sqrt((w/2.0)**2 + (h/2.0)**2) + 20.0
            num_rings = int(math.ceil(max_r / ring_w))
            for i in range(num_rings):
                r_in = i * ring_w
                r_out = (i + 1) * ring_w
                c_out = ClipperEngine.make_circle(cx, cy, r_out)
                if r_in == 0:
                    masks.append({"code": c_out, "cx": cx, "cy": cy, "col": i+1, "row": 1})
                else:
                    c_in = ClipperEngine.make_circle(cx, cy, r_in)
                    ring_code = ClipperEngine.boolean_difference(c_out, c_in)
                    masks.append({"code": ring_code, "cx": cx, "cy": cy, "col": i+1, "row": 1})

        elif mode_key in ["ray", "radial", "rayos", "rays"]:
            ang_step = max(1.0, min(360.0, float(size_x) if (size_x and float(size_x) > 0) else 30.0))
            num_rays = int(math.ceil(360.0 / ang_step))
            max_polar_R = math.sqrt((w/2.0)**2 + (h/2.0)**2) + 20.0
            for i in range(num_rays):
                a1_deg = i * ang_step
                a2_deg = min(360.0, (i + 1) * ang_step)
                pts = [f"{cx:.3f} {cy:.3f}"]
                arc_steps = max(1, int(math.ceil((a2_deg - a1_deg) / 10.0)))
                for j in range(arc_steps + 1):
                    a = math.radians(a1_deg + (a2_deg - a1_deg) * (j / float(arc_steps)))
                    pts.append(f"{cx + max_polar_R * math.cos(a):.3f} {cy + max_polar_R * math.sin(a):.3f}")
                mask_code = "m " + " l ".join(pts) + f" l {cx:.3f} {cy:.3f}"
                mid_a = math.radians((a1_deg + a2_deg) / 2.0)
                v_dist = (2.0 / 3.0) * max_polar_R
                masks.append({"code": mask_code, "cx": cx + math.cos(mid_a)*v_dist, "cy": cy + math.sin(mid_a)*v_dist, "col": i+1, "row": 1})

        elif mode_key in ["quad", "quadtree"]:
            min_size = max(4.0, float(size_x) if (size_x and float(size_x) > 0) else 10.0)
            prob = float(accel_x) if (accel_x and float(accel_x) > 0) else 0.45
            base_size = min_size * 8.0
            c_start = int(math.floor(min_x / base_size)) - 1
            c_end = int(math.ceil(max_x / base_size)) + 1
            r_start = int(math.floor(min_y / base_size)) - 1
            r_end = int(math.ceil(max_y / base_size)) + 1
            
            def subdivide_quad(gx, gy, size, c_idx, r_idx):
                if gx + size < min_x or gx > max_x or gy + size < min_y or gy > max_y:
                    return
                if size <= min_size * 1.1 or ClipperEngine.hash_rand(gx, gy) <= prob:
                    quad_code = f"m {gx:.3f} {gy:.3f} l {gx + size:.3f} {gy:.3f} l {gx + size:.3f} {gy + size:.3f} l {gx:.3f} {gy + size:.3f} l {gx:.3f} {gy:.3f}"
                    masks.append({"code": quad_code, "cx": gx + size/2.0, "cy": gy + size/2.0, "col": c_idx, "row": r_idx})
                else:
                    half = size / 2.0
                    subdivide_quad(gx, gy, half, c_idx * 2, r_idx * 2)
                    subdivide_quad(gx + half, gy, half, c_idx * 2 + 1, r_idx * 2)
                    subdivide_quad(gx, gy + half, half, c_idx * 2, r_idx * 2 + 1)
                    subdivide_quad(gx + half, gy + half, half, c_idx * 2 + 1, r_idx * 2 + 1)
                    
            for c in range(c_start, c_end + 1):
                for r in range(r_start, r_end + 1):
                    subdivide_quad(c * base_size, r * base_size, base_size, c, r)

        elif mode_key in ["bez", "bézier", "bezier", "ondas"]:
            W = max(10.0, float(size_x) * 2.0 if (size_x and float(size_x) > 0) else 20.0)
            c_start = int(math.floor(min_x / W)) - 1
            c_end = int(math.ceil(max_x / W)) + 1
            r_start = int(math.floor(min_y / W)) - 1
            r_end = int(math.ceil(max_y / W)) + 1
            
            def get_bezier_edge(etype, c, r, x1, y1, x2, y2):
                rand1 = ClipperEngine.hash_rand(c, r, 1 if etype == "H" else 2)
                rand2 = ClipperEngine.hash_rand(c, r, 3 if etype == "H" else 4)
                amp1 = (rand1 - 0.5) * 1.5 * W
                amp2 = (rand2 - 0.5) * 1.5 * W
                dx, dy = x2 - x1, y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                if length == 0: length = 1.0
                nx, ny = -dy / length, dx / length
                cp1x, cp1y = x1 + dx * 0.33 + nx * amp1, y1 + dy * 0.33 + ny * amp1
                cp2x, cp2y = x1 + dx * 0.66 + nx * amp2, y1 + dy * 0.66 + ny * amp2
                return {
                    "fwd": f"b {cp1x:.3f} {cp1y:.3f} {cp2x:.3f} {cp2y:.3f} {x2:.3f} {y2:.3f}",
                    "bwd": f"b {cp2x:.3f} {cp2y:.3f} {cp1x:.3f} {cp1y:.3f} {x1:.3f} {y1:.3f}"
                }
                
            for c in range(c_start, c_end + 1):
                for r in range(r_start, r_end + 1):
                    tl_x, tl_y = c * W, r * W
                    tr_x, tr_y = (c + 1) * W, r * W
                    br_x, br_y = (c + 1) * W, (r + 1) * W
                    bl_x, bl_y = c * W, (r + 1) * W
                    top_edge = get_bezier_edge("H", c, r, tl_x, tl_y, tr_x, tr_y)["fwd"]
                    right_edge = get_bezier_edge("V", c + 1, r, tr_x, tr_y, br_x, br_y)["fwd"]
                    bottom_edge = get_bezier_edge("H", c, r + 1, bl_x, bl_y, br_x, br_y)["bwd"]
                    left_edge = get_bezier_edge("V", c, r, tl_x, tl_y, bl_x, bl_y)["bwd"]
                    cell_code = f"m {tl_x:.3f} {tl_y:.3f} {top_edge} {right_edge} {bottom_edge} {left_edge}"
                    masks.append({"code": cell_code, "cx": (tl_x + br_x)/2.0, "cy": (tl_y + br_y)/2.0, "col": c, "row": r})

        elif mode_key in ["vor", "voronoi", "cristales"]:
            cell_size = max(8.0, float(size_x) if (size_x and float(size_x) > 0) else 20.0)
            c_start = int(math.floor(min_x / cell_size)) - 1
            c_end = int(math.ceil(max_x / cell_size)) + 1
            r_start = int(math.floor(min_y / cell_size)) - 1
            r_end = int(math.ceil(max_y / cell_size)) + 1
            pts = []
            for c in range(c_start - 2, c_end + 3):
                for r in range(r_start - 2, r_end + 3):
                    rx = ClipperEngine.hash_rand(c, r, 777)
                    ry = ClipperEngine.hash_rand(r, c, 888)
                    p_x = c * cell_size + rx * cell_size
                    p_y = r * cell_size + ry * cell_size
                    pts.append({"x": p_x, "y": p_y, "c": c, "r": r})
            for p1 in pts:
                if c_start <= p1["c"] <= c_end and r_start <= p1["r"] <= r_end:
                    P = cell_size * 2.5
                    cell_code = f"m {p1['x'] - P:.3f} {p1['y'] - P:.3f} l {p1['x'] + P:.3f} {p1['y'] - P:.3f} l {p1['x'] + P:.3f} {p1['y'] + P:.3f} l {p1['x'] - P:.3f} {p1['y'] + P:.3f} l {p1['x'] - P:.3f} {p1['y'] - P:.3f}"
                    for p2 in pts:
                        if p1 is not p2:
                            dc, dr = abs(p1["c"] - p2["c"]), abs(p1["r"] - p2["r"])
                            if dc <= 2 and dr <= 2:
                                mx, my = (p1["x"] + p2["x"])/2.0, (p1["y"] + p2["y"])/2.0
                                nx, ny = p1["x"] - p2["x"], p1["y"] - p2["y"]
                                length = math.sqrt(nx*nx + ny*ny)
                                if length > 0.001:
                                    nx, ny = nx / length, ny / length
                                    tx, ty = -ny, nx
                                    L = P * 4.0
                                    hp_code = f"m {mx + tx*L:.3f} {my + ty*L:.3f} l {mx - tx*L:.3f} {my - ty*L:.3f} l {mx - tx*L + nx*L:.3f} {my - ty*L + ny*L:.3f} l {mx + tx*L + nx*L:.3f} {my + ty*L + ny*L:.3f} l {mx + tx*L:.3f} {my + ty*L:.3f}"
                                    res = ClipperEngine.boolean_intersection(cell_code, hp_code)
                                    if res and res.strip():
                                        cell_code = res
                    masks.append({"code": cell_code, "cx": p1["x"], "cy": p1["y"], "col": p1["c"], "row": p1["r"]})

        elif mode_key in ["ashlar", "mamposteria"]:
            min_w = max(2.0, float(size_x) if (size_x and float(size_x) > 0) else 10.0)
            max_w = max(min_w + 1.0, float(size_y) if (size_y and float(size_y) > min_w) else min_w * 4.0)
            row_h = max(2.0, float(size_x) if (size_x and float(size_x) > 0) else 15.0)
            S = (max_w + min_w) / 2.0
            J = (max_w - min_w) / 2.0
            c_start = int(math.floor(min_x / S)) - 1
            c_end = int(math.ceil(max_x / S)) + 1
            r_start = int(math.floor(min_y / row_h)) - 1
            r_end = int(math.ceil(max_y / row_h)) + 1
            for r in range(r_start, r_end + 1):
                screen_y = r * row_h
                for c in range(c_start, c_end + 1):
                    hash_l = ClipperEngine.hash_rand(c, r, 111)
                    screen_x_left = c * S + hash_l * J
                    hash_r = ClipperEngine.hash_rand(c + 1, r, 111)
                    screen_x_right = (c + 1) * S + hash_r * J
                    if screen_x_right >= min_x and screen_x_left <= max_x:
                        cx1, cx2 = screen_x_left, screen_x_right
                        cy1, cy2 = screen_y, screen_y + row_h
                        rect_code = f"m {cx1:.3f} {cy1:.3f} l {cx2:.3f} {cy1:.3f} l {cx2:.3f} {cy2:.3f} l {cx1:.3f} {cy2:.3f} l {cx1:.3f} {cy1:.3f}"
                        masks.append({"code": rect_code, "cx": (cx1 + cx2)/2.0, "cy": (cy1 + cy2)/2.0, "col": c, "row": r})

        elif mode_key in ["brick", "ladrillo"]:
            W = max(2.0, float(size_x) if (size_x and float(size_x) > 0) else 30.0)
            H = max(2.0, float(size_y) if (size_y and float(size_y) > 0) else 15.0)
            offset_ratio = 0.5
            r_start = int(math.floor(min_y / H)) - 1
            r_end = int(math.ceil(max_y / H)) + 1
            for r in range(r_start, r_end + 1):
                row_offset = (abs(r) % 2) * W * offset_ratio
                c_start = int(math.floor((min_x - row_offset) / W)) - 1
                c_end = int(math.ceil((max_x - row_offset) / W)) + 1
                for c in range(c_start, c_end + 1):
                    screen_x = c * W + row_offset
                    screen_y = r * H
                    brick_code = f"m {screen_x:.3f} {screen_y:.3f} l {screen_x + W:.3f} {screen_y:.3f} l {screen_x + W:.3f} {screen_y + H:.3f} l {screen_x:.3f} {screen_y + H:.3f} l {screen_x:.3f} {screen_y:.3f}"
                    masks.append({"code": brick_code, "cx": screen_x + W/2.0, "cy": screen_y + H/2.0, "col": c, "row": r})

        elif mode_key in ["mondrian"]:
            min_size = max(4.0, float(size_x) if (size_x and float(size_x) > 0) else 12.0)
            prob = float(accel_x) if (accel_x and float(accel_x) > 0) else 0.45
            base_size = min_size * 8.0
            c_start = int(math.floor(min_x / base_size)) - 1
            c_end = int(math.ceil(max_x / base_size)) + 1
            r_start = int(math.floor(min_y / base_size)) - 1
            r_end = int(math.ceil(max_y / base_size)) + 1
            
            def subdivide_mondrian(gx, gy, gw, gh, c_idx, r_idx):
                if gx + gw < min_x or gx > max_x or gy + gh < min_y or gy > max_y:
                    return
                stop = False
                if max(gw, gh) <= min_size * 1.5:
                    stop = True
                elif max(gw, gh) <= min_size * 4.0 and ClipperEngine.hash_rand(gx, gy, 99) <= prob:
                    stop = True
                if stop:
                    rect_code = f"m {gx:.3f} {gy:.3f} l {gx + gw:.3f} {gy:.3f} l {gx + gw:.3f} {gy + gh:.3f} l {gx:.3f} {gy + gh:.3f} l {gx:.3f} {gy:.3f}"
                    masks.append({"code": rect_code, "cx": gx + gw/2.0, "cy": gy + gh/2.0, "col": c_idx, "row": r_idx})
                else:
                    if gw > gh * 1.5:
                        split_x = True
                    elif gh > gw * 1.5:
                        split_x = False
                    else:
                        split_x = ClipperEngine.hash_rand(gx, gy, 123) > 0.5
                    ratio = 0.3 + 0.4 * ClipperEngine.hash_rand(gx, gy, 456)
                    if split_x:
                        w1 = gw * ratio
                        w2 = gw - w1
                        subdivide_mondrian(gx, gy, w1, gh, c_idx * 2, r_idx)
                        subdivide_mondrian(gx + w1, gy, w2, gh, c_idx * 2 + 1, r_idx)
                    else:
                        h1 = gh * ratio
                        h2 = gh - h1
                        subdivide_mondrian(gx, gy, gw, h1, c_idx, r_idx * 2)
                        subdivide_mondrian(gx, gy + h1, gw, h2, c_idx, r_idx * 2 + 1)
                        
            for c in range(c_start, c_end + 1):
                for r in range(r_start, r_end + 1):
                    subdivide_mondrian(c * base_size, r * base_size, base_size, base_size, c, r)

        elif mode_key in ["herringbone", "espiga"]:
            L = max(2.0, float(size_x) if (size_x and float(size_x) > 0) else 30.0)
            W = max(1.0, float(size_y) if (size_y and float(size_y) > 0) else 10.0)
            pad = max(L, W) * 2.0
            sx1, sx2 = min_x - pad, max_x + pad
            sy1, sy2 = min_y - pad, max_y + pad
            
            def get_cr(x, y):
                return (x - y) / (2.0 * L), (x + y) / (2.0 * W)
                
            c1, r1 = get_cr(sx1, sy1)
            c2, r2 = get_cr(sx2, sy1)
            c3, r3 = get_cr(sx1, sy2)
            c4, r4 = get_cr(sx2, sy2)
            c_start = int(math.floor(min(c1, c2, c3, c4)))
            c_end = int(math.ceil(max(c1, c2, c3, c4)))
            r_start = int(math.floor(min(r1, r2, r3, r4)))
            r_end = int(math.ceil(max(r1, r2, r3, r4)))
            
            for c in range(c_start, c_end + 1):
                for r in range(r_start, r_end + 1):
                    base_cx = c * L + r * W
                    base_cy = -c * L + r * W
                    hx, hy = base_cx, base_cy
                    h_code = f"m {hx:.3f} {hy:.3f} l {hx + L:.3f} {hy:.3f} l {hx + L:.3f} {hy + W:.3f} l {hx:.3f} {hy + W:.3f} l {hx:.3f} {hy:.3f}"
                    masks.append({"code": h_code, "cx": hx + L/2.0, "cy": hy + W/2.0, "col": c, "row": r})
                    vx, vy = base_cx + L, base_cy + W - L
                    v_code = f"m {vx:.3f} {vy:.3f} l {vx + W:.3f} {vy:.3f} l {vx + W:.3f} {vy + L:.3f} l {vx:.3f} {vy + L:.3f} l {vx:.3f} {vy:.3f}"
                    masks.append({"code": v_code, "cx": vx + W/2.0, "cy": vy + L/2.0, "col": c, "row": r})

        elif mode_key in ["delaunay", "low-poly", "lowpoly"]:
            cell_size = max(8.0, float(size_x) if (size_x and float(size_x) > 0) else 15.0)
            c_start = int(math.floor(min_x / cell_size)) - 1
            c_end = int(math.ceil(max_x / cell_size)) + 1
            r_start = int(math.floor(min_y / cell_size)) - 1
            r_end = int(math.ceil(max_y / cell_size)) + 1
            
            def get_delaunay_pt(c, r):
                rx = ClipperEngine.hash_rand(c, r, 2024)
                ry = ClipperEngine.hash_rand(r, c, 4202)
                return c * cell_size + rx * cell_size, r * cell_size + ry * cell_size
                
            def dist_sq(x1, y1, x2, y2):
                return (x2 - x1)**2 + (y2 - y1)**2
                
            for c in range(c_start, c_end + 1):
                for r in range(r_start, r_end + 1):
                    tl_x, tl_y = get_delaunay_pt(c, r)
                    tr_x, tr_y = get_delaunay_pt(c + 1, r)
                    bl_x, bl_y = get_delaunay_pt(c, r + 1)
                    br_x, br_y = get_delaunay_pt(c + 1, r + 1)
                    d1 = dist_sq(tl_x, tl_y, br_x, br_y)
                    d2 = dist_sq(tr_x, tr_y, bl_x, bl_y)
                    if d1 < d2:
                        tri1 = f"m {tl_x:.3f} {tl_y:.3f} l {tr_x:.3f} {tr_y:.3f} l {br_x:.3f} {br_y:.3f} l {tl_x:.3f} {tl_y:.3f}"
                        tri2 = f"m {tl_x:.3f} {tl_y:.3f} l {br_x:.3f} {br_y:.3f} l {bl_x:.3f} {bl_y:.3f} l {tl_x:.3f} {tl_y:.3f}"
                        masks.append({"code": tri1, "cx": (tl_x + tr_x + br_x)/3.0, "cy": (tl_y + tr_y + br_y)/3.0, "col": c, "row": r})
                        masks.append({"code": tri2, "cx": (tl_x + br_x + bl_x)/3.0, "cy": (tl_y + br_y + bl_y)/3.0, "col": c, "row": r})
                    else:
                        tri1 = f"m {tl_x:.3f} {tl_y:.3f} l {tr_x:.3f} {tr_y:.3f} l {bl_x:.3f} {bl_y:.3f} l {tl_x:.3f} {tl_y:.3f}"
                        tri2 = f"m {tr_x:.3f} {tr_y:.3f} l {br_x:.3f} {br_y:.3f} l {bl_x:.3f} {bl_y:.3f} l {tr_x:.3f} {tr_y:.3f}"
                        masks.append({"code": tri1, "cx": (tl_x + tr_x + bl_x)/3.0, "cy": (tl_y + tr_y + bl_y)/3.0, "col": c, "row": r})
                        masks.append({"code": tri2, "cx": (tr_x + br_x + bl_x)/3.0, "cy": (tr_y + br_y + bl_y)/3.0, "col": c, "row": r})

        elif mode_key in ["scallop", "escamas"]:
            R = max(2.0, float(size_x) if (size_x and float(size_x) > 0) else 12.0)
            k = R * 0.55228475
            H_step = R
            W_step = R * 2.0
            c_start = int(math.floor(min_x / W_step)) - 2
            c_end = int(math.ceil(max_x / W_step)) + 2
            r_start = int(math.floor(min_y / H_step)) - 2
            r_end = int(math.ceil(max_y / H_step)) + 2
            for r in range(r_start, r_end + 1):
                for c in range(c_start, c_end + 1):
                    screen_cx = c * W_step
                    screen_cy = r * H_step
                    if abs(r % 2) == 1:
                        screen_cx += R
                    scallop_code = (
                        f"m {screen_cx - R:.3f} {screen_cy:.3f} "
                        f"b {screen_cx - R:.3f} {screen_cy - k:.3f} {screen_cx - k:.3f} {screen_cy - R:.3f} {screen_cx:.3f} {screen_cy - R:.3f} "
                        f"b {screen_cx + k:.3f} {screen_cy - R:.3f} {screen_cx + R:.3f} {screen_cy - k:.3f} {screen_cx + R:.3f} {screen_cy:.3f} "
                        f"b {screen_cx + R - k:.3f} {screen_cy:.3f} {screen_cx:.3f} {screen_cy + R - k:.3f} {screen_cx:.3f} {screen_cy + R:.3f} "
                        f"b {screen_cx:.3f} {screen_cy + R - k:.3f} {screen_cx - R + k:.3f} {screen_cy:.3f} {screen_cx - R:.3f} {screen_cy:.3f}"
                    )
                    masks.append({"code": scallop_code, "cx": screen_cx, "cy": screen_cy, "col": c, "row": r})

        elif mode_key in ["web", "spiderweb", "telaraña"]:
            num_rings = max(1, int(float(cols) if cols > 1 else (float(size_x) if size_x and float(size_x) >= 1 else 5)))
            num_rays = max(3, int(float(rows) if rows > 1 else (float(size_y) if size_y and float(size_y) >= 3 else 12)))
            chaos = max(0.0, min(1.0, float(accel_x) if accel_x is not None else 0.2))
            epicenter_x = cx + float(offset_x)
            epicenter_y = cy + float(offset_y)
            corners = [[min_x, min_y], [max_x, min_y], [min_x, max_y], [max_x, max_y]]
            max_dist = max(math.sqrt((pt[0]-epicenter_x)**2 + (pt[1]-epicenter_y)**2) for pt in corners) + 10.0
            step_R = max_dist / float(num_rings)
            step_A = 360.0 / float(num_rays)
            
            def get_web_vertex(ring, ray):
                if ring == 0:
                    return epicenter_x, epicenter_y
                safe_ray = ray % num_rays
                a = safe_ray * step_A
                r_val = ring * step_R
                a_jit = (ClipperEngine.hash_rand(ring, safe_ray, 11) - 0.5) * step_A * chaos
                r_jit = (ClipperEngine.hash_rand(ring, safe_ray, 22) - 0.5) * step_R * chaos
                final_a = math.radians(a + a_jit)
                final_r = r_val + r_jit
                return epicenter_x + final_r * math.cos(final_a), epicenter_y + final_r * math.sin(final_a)
                
            for ring in range(1, num_rings + 1):
                for ray in range(num_rays):
                    x1, y1 = get_web_vertex(ring - 1, ray)
                    x2, y2 = get_web_vertex(ring, ray)
                    x3, y3 = get_web_vertex(ring, ray + 1)
                    x4, y4 = get_web_vertex(ring - 1, ray + 1)
                    if ring == 1:
                        cell_code = f"m {x1:.3f} {y1:.3f} l {x2:.3f} {y2:.3f} l {x3:.3f} {y3:.3f} l {x1:.3f} {y1:.3f}"
                        cent_x, cent_y = (x1+x2+x3)/3.0, (y1+y2+y3)/3.0
                    else:
                        cell_code = f"m {x1:.3f} {y1:.3f} l {x2:.3f} {y2:.3f} l {x3:.3f} {y3:.3f} l {x4:.3f} {y4:.3f} l {x1:.3f} {y1:.3f}"
                        cent_x, cent_y = (x1+x2+x3+x4)/4.0, (y1+y2+y3+y4)/4.0
                    masks.append({"code": cell_code, "cx": cent_x, "cy": cent_y, "col": ray + 1, "row": ring})

        elif mode_key in ["rhombille", "cubos", "cubes"]:
            R = max(2.0, float(size_x) if (size_x and float(size_x) > 0) else 20.0)
            W = 1.73205081 * R
            H_step = 1.5 * R
            c_start = int(math.floor(min_x / W)) - 1
            c_end = int(math.ceil(max_x / W)) + 1
            r_start = int(math.floor(min_y / H_step)) - 1
            r_end = int(math.ceil(max_y / H_step)) + 1
            for r in range(r_start, r_end + 1):
                screen_cy = r * H_step
                for c in range(c_start, c_end + 1):
                    screen_cx = c * W
                    if abs(r % 2) == 1:
                        screen_cx += W / 2.0
                    p_c = [screen_cx, screen_cy]
                    p_t = [screen_cx, screen_cy - R]
                    p_tr = [screen_cx + W/2.0, screen_cy - R/2.0]
                    p_br = [screen_cx + W/2.0, screen_cy + R/2.0]
                    p_b = [screen_cx, screen_cy + R]
                    p_bl = [screen_cx - W/2.0, screen_cy + R/2.0]
                    p_tl = [screen_cx - W/2.0, screen_cy - R/2.0]
                    r1 = f"m {p_c[0]:.3f} {p_c[1]:.3f} l {p_tl[0]:.3f} {p_tl[1]:.3f} l {p_t[0]:.3f} {p_t[1]:.3f} l {p_tr[0]:.3f} {p_tr[1]:.3f} l {p_c[0]:.3f} {p_c[1]:.3f}"
                    r2 = f"m {p_c[0]:.3f} {p_c[1]:.3f} l {p_tr[0]:.3f} {p_tr[1]:.3f} l {p_br[0]:.3f} {p_br[1]:.3f} l {p_b[0]:.3f} {p_b[1]:.3f} l {p_c[0]:.3f} {p_c[1]:.3f}"
                    r3 = f"m {p_c[0]:.3f} {p_c[1]:.3f} l {p_b[0]:.3f} {p_b[1]:.3f} l {p_bl[0]:.3f} {p_bl[1]:.3f} l {p_tl[0]:.3f} {p_tl[1]:.3f} l {p_c[0]:.3f} {p_c[1]:.3f}"
                    masks.append({"code": r1, "cx": screen_cx, "cy": screen_cy - R/2.0, "col": c, "row": r})
                    masks.append({"code": r2, "cx": screen_cx + W/4.0, "cy": screen_cy + R/4.0, "col": c, "row": r})
                    masks.append({"code": r3, "cx": screen_cx - W/4.0, "cy": screen_cy + R/4.0, "col": c, "row": r})

        elif mode_key in ["octagon", "mosaico"]:
            R = max(2.0, float(size_x) if (size_x and float(size_x) > 0) else 20.0)
            x_cut = R * (2.0 - math.sqrt(2.0))
            d = R - x_cut
            step = R * 2.0
            c_start = int(math.floor(min_x / step)) - 1
            c_end = int(math.ceil(max_x / step)) + 1
            r_start = int(math.floor(min_y / step)) - 1
            r_end = int(math.ceil(max_y / step)) + 1
            for r in range(r_start, r_end + 1):
                for c in range(c_start, c_end + 1):
                    screen_cx = c * step
                    screen_cy = r * step
                    oct_code = (
                        f"m {screen_cx - d:.3f} {screen_cy - R:.3f} "
                        f"l {screen_cx + d:.3f} {screen_cy - R:.3f} "
                        f"l {screen_cx + R:.3f} {screen_cy - d:.3f} "
                        f"l {screen_cx + R:.3f} {screen_cy + d:.3f} "
                        f"l {screen_cx + d:.3f} {screen_cy + R:.3f} "
                        f"l {screen_cx - d:.3f} {screen_cy + R:.3f} "
                        f"l {screen_cx - R:.3f} {screen_cy + d:.3f} "
                        f"l {screen_cx - R:.3f} {screen_cy - d:.3f} "
                        f"l {screen_cx - d:.3f} {screen_cy - R:.3f}"
                    )
                    masks.append({"code": oct_code, "cx": screen_cx, "cy": screen_cy, "col": c, "row": r})
                    sq_cx = screen_cx + R
                    sq_cy = screen_cy + R
                    sq_code = f"m {sq_cx:.3f} {sq_cy - x_cut:.3f} l {sq_cx + x_cut:.3f} {sq_cy:.3f} l {sq_cx:.3f} {sq_cy + x_cut:.3f} l {sq_cx - x_cut:.3f} {sq_cy:.3f} l {sq_cx:.3f} {sq_cy - x_cut:.3f}"
                    masks.append({"code": sq_code, "cx": sq_cx, "cy": sq_cy, "col": c, "row": r})

        elif mode_key in ["kagome"]:
            R = max(2.0, float(size_x) if (size_x and float(size_x) > 0) else 15.0)
            H_step = R * 1.73205081
            H_half = H_step / 2.0
            r_start = int(math.floor(min_y / H_step)) - 1
            r_end = int(math.ceil(max_y / H_step)) + 1
            for r in range(r_start, r_end + 1):
                c_start = int(math.floor((min_x - r * R) / (2.0 * R))) - 1
                c_end = int(math.ceil((max_x - r * R) / (2.0 * R))) + 1
                for c in range(c_start, c_end + 1):
                    screen_cx = c * 2.0 * R + r * R
                    screen_cy = r * H_step
                    hex_code = (
                        f"m {screen_cx + R:.3f} {screen_cy:.3f} "
                        f"l {screen_cx + R/2.0:.3f} {screen_cy + H_half:.3f} "
                        f"l {screen_cx - R/2.0:.3f} {screen_cy + H_half:.3f} "
                        f"l {screen_cx - R:.3f} {screen_cy:.3f} "
                        f"l {screen_cx - R/2.0:.3f} {screen_cy - H_half:.3f} "
                        f"l {screen_cx + R/2.0:.3f} {screen_cy - H_half:.3f} "
                        f"l {screen_cx + R:.3f} {screen_cy:.3f}"
                    )
                    masks.append({"code": hex_code, "cx": screen_cx, "cy": screen_cy, "col": c, "row": r})
                    td_code = f"m {screen_cx + R:.3f} {screen_cy:.3f} l {screen_cx + 1.5*R:.3f} {screen_cy + H_half:.3f} l {screen_cx + 0.5*R:.3f} {screen_cy + H_half:.3f} l {screen_cx + R:.3f} {screen_cy:.3f}"
                    masks.append({"code": td_code, "cx": screen_cx + R, "cy": screen_cy + H_step/3.0, "col": c, "row": r})
                    tu_code = f"m {screen_cx + R:.3f} {screen_cy:.3f} l {screen_cx + 0.5*R:.3f} {screen_cy - H_half:.3f} l {screen_cx + 1.5*R:.3f} {screen_cy - H_half:.3f} l {screen_cx + R:.3f} {screen_cy:.3f}"
                    masks.append({"code": tu_code, "cx": screen_cx + R, "cy": screen_cy - H_step/3.0, "col": c, "row": r})

        elif mode_key in ["jigsaw", "puzzle"]:
            W = max(10.0, float(size_x) * 2.0 if (size_x and float(size_x) >= 5.0) else 20.0)
            c_start = int(math.floor(min_x / W)) - 1
            c_end = int(math.ceil(max_x / W)) + 1
            r_start = int(math.floor(min_y / W)) - 1
            r_end = int(math.ceil(max_y / W)) + 1
            
            def get_jigsaw_edge(etype, c, r, x1, y1, x2, y2):
                rand1 = ClipperEngine.hash_rand(c, r, 1 if etype == "H" else 2)
                rand2 = ClipperEngine.hash_rand(c, r, 3 if etype == "H" else 4)
                direction = 1.0 if rand1 > 0.5 else -1.0
                offset = (rand2 - 0.5) * 0.2
                dx, dy = x2 - x1, y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                if length == 0: length = 1.0
                nx, ny = -dy / length * direction, dx / length * direction
                ux, uy = dx / length, dy / length
                p_neck_L = 0.38 + offset
                p_neck_R = 0.62 + offset
                def pt(u, n):
                    return [x1 + ux * (u * length) + nx * (n * length), y1 + uy * (u * length) + ny * (n * length)]
                pt_neck_L = pt(p_neck_L, 0.0)
                b1_c1, b1_c2, b1_end = pt(p_neck_L + 0.05, 0.0), pt(p_neck_L + 0.05, 0.1), pt(p_neck_L, 0.15)
                b2_c1, b2_c2, b2_end = pt(p_neck_L - 0.10, 0.3), pt(p_neck_R + 0.10, 0.3), pt(p_neck_R, 0.15)
                b3_c1, b3_c2, b3_end = pt(p_neck_R - 0.05, 0.1), pt(p_neck_R - 0.05, 0.0), pt(p_neck_R, 0.0)
                fwd = (
                    f"l {pt_neck_L[0]:.3f} {pt_neck_L[1]:.3f} "
                    f"b {b1_c1[0]:.3f} {b1_c1[1]:.3f} {b1_c2[0]:.3f} {b1_c2[1]:.3f} {b1_end[0]:.3f} {b1_end[1]:.3f} "
                    f"b {b2_c1[0]:.3f} {b2_c1[1]:.3f} {b2_c2[0]:.3f} {b2_c2[1]:.3f} {b2_end[0]:.3f} {b2_end[1]:.3f} "
                    f"b {b3_c1[0]:.3f} {b3_c1[1]:.3f} {b3_c2[0]:.3f} {b3_c2[1]:.3f} {b3_end[0]:.3f} {b3_end[1]:.3f} "
                    f"l {x2:.3f} {y2:.3f}"
                )
                bwd = (
                    f"l {b3_end[0]:.3f} {b3_end[1]:.3f} "
                    f"b {b3_c2[0]:.3f} {b3_c2[1]:.3f} {b3_c1[0]:.3f} {b3_c1[1]:.3f} {b2_end[0]:.3f} {b2_end[1]:.3f} "
                    f"b {b2_c2[0]:.3f} {b2_c2[1]:.3f} {b2_c1[0]:.3f} {b2_c1[1]:.3f} {b1_end[0]:.3f} {b1_end[1]:.3f} "
                    f"b {b1_c2[0]:.3f} {b1_c2[1]:.3f} {b1_c1[0]:.3f} {b1_c1[0]:.3f} {pt_neck_L[0]:.3f} {pt_neck_L[1]:.3f} "
                    f"l {x1:.3f} {y1:.3f}"
                )
                return {"fwd": fwd, "bwd": bwd}
                
            for c in range(c_start, c_end + 1):
                for r in range(r_start, r_end + 1):
                    tl_x, tl_y = c * W, r * W
                    tr_x, tr_y = (c + 1) * W, r * W
                    br_x, br_y = (c + 1) * W, (r + 1) * W
                    bl_x, bl_y = c * W, (r + 1) * W
                    top_edge = get_jigsaw_edge("H", c, r, tl_x, tl_y, tr_x, tr_y)["fwd"]
                    right_edge = get_jigsaw_edge("V", c + 1, r, tr_x, tr_y, br_x, br_y)["fwd"]
                    bottom_edge = get_jigsaw_edge("H", c, r + 1, bl_x, bl_y, br_x, br_y)["bwd"]
                    left_edge = get_jigsaw_edge("V", c, r, tl_x, tl_y, bl_x, bl_y)["bwd"]
                    cell_code = f"m {tl_x:.3f} {tl_y:.3f} {top_edge} {right_edge} {bottom_edge} {left_edge}"
                    masks.append({"code": cell_code, "cx": (tl_x + br_x)/2.0, "cy": (tl_y + br_y)/2.0, "col": c, "row": r})

        elif mode_key in ["truchet", "tuberias"]:
            W = max(10.0, float(size_x) if (size_x and float(size_x) > 0) else 20.0)
            k = (W / 2.0) * 0.55228475
            c_start = int(math.floor(min_x / W)) - 1
            c_end = int(math.ceil(max_x / W)) + 1
            r_start = int(math.floor(min_y / W)) - 1
            r_end = int(math.ceil(max_y / W)) + 1
            for c in range(c_start, c_end + 1):
                for r in range(r_start, r_end + 1):
                    cx_val = c * W
                    cy_val = r * W
                    config = 1 if ClipperEngine.hash_rand(c, r, 789) > 0.5 else 0
                    if config == 0:
                        m1 = f"m {cx_val:.3f} {cy_val + W/2:.3f} b {cx_val:.3f} {cy_val + W/2 - k:.3f} {cx_val + W/2 - k:.3f} {cy_val:.3f} {cx_val + W/2:.3f} {cy_val:.3f} l {cx_val:.3f} {cy_val:.3f} l {cx_val:.3f} {cy_val + W/2:.3f}"
                        m2 = f"m {cx_val + W/2:.3f} {cy_val + W:.3f} b {cx_val + W/2 + k:.3f} {cy_val + W:.3f} {cx_val + W:.3f} {cy_val + W/2 + k:.3f} {cx_val + W:.3f} {cy_val + W/2:.3f} l {cx_val + W:.3f} {cy_val + W:.3f} l {cx_val + W/2:.3f} {cy_val + W:.3f}"
                        m3 = f"m {cx_val + W/2:.3f} {cy_val:.3f} l {cx_val + W:.3f} {cy_val:.3f} l {cx_val + W:.3f} {cy_val + W/2:.3f} b {cx_val + W:.3f} {cy_val + W/2 + k:.3f} {cx_val + W/2 + k:.3f} {cy_val + W:.3f} {cx_val + W/2:.3f} {cy_val + W:.3f} l {cx_val:.3f} {cy_val + W:.3f} l {cx_val:.3f} {cy_val + W/2:.3f} b {cx_val:.3f} {cy_val + W/2 - k:.3f} {cx_val + W/2 - k:.3f} {cy_val + W:.3f} {cx_val + W/2:.3f} {cy_val:.3f}"
                        masks.append({"code": m1, "cx": cx_val + W/4.0, "cy": cy_val + W/4.0, "col": c, "row": r})
                        masks.append({"code": m2, "cx": cx_val + 3*W/4.0, "cy": cy_val + 3*W/4.0, "col": c, "row": r})
                        masks.append({"code": m3, "cx": cx_val + W/2.0, "cy": cy_val + W/2.0, "col": c, "row": r})
                    else:
                        m1 = f"m {cx_val + W/2:.3f} {cy_val:.3f} l {cx_val + W:.3f} {cy_val:.3f} l {cx_val + W:.3f} {cy_val + W/2:.3f} b {cx_val + W:.3f} {cy_val + W/2 - k:.3f} {cx_val + W/2 + k:.3f} {cy_val:.3f} {cx_val + W/2:.3f} {cy_val:.3f}"
                        m2 = f"m {cx_val:.3f} {cy_val + W/2:.3f} l {cx_val:.3f} {cy_val + W:.3f} l {cx_val + W/2:.3f} {cy_val + W:.3f} b {cx_val + W/2 - k:.3f} {cy_val + W:.3f} {cx_val:.3f} {cy_val + W/2 + k:.3f} {cx_val:.3f} {cy_val + W/2:.3f}"
                        m3 = f"m {cx_val:.3f} {cy_val:.3f} l {cx_val + W/2:.3f} {cy_val:.3f} b {cx_val + W/2 + k:.3f} {cy_val:.3f} {cx_val + W:.3f} {cy_val + W/2 - k:.3f} {cx_val + W:.3f} {cy_val + W/2:.3f} l {cx_val + W:.3f} {cy_val + W:.3f} l {cx_val + W/2:.3f} {cy_val + W:.3f} b {cx_val + W/2 - k:.3f} {cy_val + W:.3f} {cx_val:.3f} {cy_val + W/2 + k:.3f} {cx_val:.3f} {cy_val + W/2:.3f} l {cx_val:.3f} {cy_val:.3f}"
                        masks.append({"code": m1, "cx": cx_val + 3*W/4.0, "cy": cy_val + W/4.0, "col": c, "row": r})
                        masks.append({"code": m2, "cx": cx_val + W/4.0, "cy": cy_val + 3*W/4.0, "col": c, "row": r})
                        masks.append({"code": m3, "cx": cx_val + W/2.0, "cy": cy_val + W/2.0, "col": c, "row": r})

        elif mode_key in ["circuit", "circuito"]:
            W = max(10.0, float(size_x) if (size_x and float(size_x) > 0) else 20.0)
            T = max(2.0, float(size_y) if (size_y and float(size_y) > 0) else W * 0.25)
            prob_pad = max(0.0, min(1.0, float(accel_x) if (accel_x and float(accel_x) > 0) else 0.2))
            k = T / 2.0
            c_start = int(math.floor(min_x / W)) - 1
            c_end = int(math.ceil(max_x / W)) + 1
            r_start = int(math.floor(min_y / W)) - 1
            r_end = int(math.ceil(max_y / W)) + 1
            for c in range(c_start, c_end + 1):
                for r in range(r_start, r_end + 1):
                    cx_val = c * W
                    cy_val = r * W
                    cell_sq = f"m {cx_val:.3f} {cy_val:.3f} l {cx_val+W:.3f} {cy_val:.3f} l {cx_val+W:.3f} {cy_val+W:.3f} l {cx_val:.3f} {cy_val+W:.3f} l {cx_val:.3f} {cy_val:.3f}"
                    hash_v = ClipperEngine.hash_rand(c, r, 101)
                    is_pad = ClipperEngine.hash_rand(c, r, 202) < prob_pad
                    if hash_v < 0.15:
                        trace_code = ""
                    elif hash_v < 0.30:
                        trace_code = f"m {cx_val:.3f} {cy_val+W/2-k:.3f} l {cx_val+W:.3f} {cy_val+W/2-k:.3f} l {cx_val+W:.3f} {cy_val+W/2+k:.3f} l {cx_val:.3f} {cy_val+W/2+k:.3f} l {cx_val:.3f} {cy_val+W/2-k:.3f}"
                    elif hash_v < 0.45:
                        trace_code = f"m {cx_val+W/2-k:.3f} {cy_val:.3f} l {cx_val+W/2+k:.3f} {cy_val:.3f} l {cx_val+W/2+k:.3f} {cy_val+W:.3f} l {cx_val+W/2-k:.3f} {cy_val+W:.3f} l {cx_val+W/2-k:.3f} {cy_val:.3f}"
                    elif hash_v < 0.60:
                        trace_code = f"m {cx_val+W/2-k:.3f} {cy_val:.3f} l {cx_val+W/2+k:.3f} {cy_val:.3f} l {cx_val+W/2+k:.3f} {cy_val+W/2+k:.3f} l {cx_val:.3f} {cy_val+W/2+k:.3f} l {cx_val:.3f} {cy_val+W/2-k:.3f} l {cx_val+W/2-k:.3f} {cy_val+W/2-k:.3f} l {cx_val+W/2-k:.3f} {cy_val:.3f}"
                    elif hash_v < 0.75:
                        trace_code = f"m {cx_val+W/2-k:.3f} {cy_val:.3f} l {cx_val+W/2+k:.3f} {cy_val:.3f} l {cx_val+W/2+k:.3f} {cy_val+W/2-k:.3f} l {cx_val+W:.3f} {cy_val+W/2-k:.3f} l {cx_val:.3f} {cy_val+W/2+k:.3f} l {cx_val+W/2-k:.3f} {cy_val+W/2+k:.3f} l {cx_val+W/2-k:.3f} {cy_val:.3f}"
                    elif hash_v < 0.90:
                        trace_code = f"m {cx_val:.3f} {cy_val+W/2-k:.3f} l {cx_val+W/2+k:.3f} {cy_val+W/2-k:.3f} l {cx_val+W/2+k:.3f} {cy_val+W:.3f} l {cx_val+W/2-k:.3f} {cy_val+W:.3f} l {cx_val+W/2-k:.3f} {cy_val+W/2+k:.3f} l {cx_val:.3f} {cy_val+W/2+k:.3f} l {cx_val:.3f} {cy_val+W/2-k:.3f}"
                    else:
                        trace_code = f"m {cx_val+W/2-k:.3f} {cy_val+W/2-k:.3f} l {cx_val+W:.3f} {cy_val+W/2-k:.3f} l {cx_val+W:.3f} {cy_val+W/2+k:.3f} l {cx_val+W/2+k:.3f} {cy_val+W/2+k:.3f} l {cx_val+W/2+k:.3f} {cy_val+W:.3f} l {cx_val+W/2-k:.3f} {cy_val+W:.3f} l {cx_val+W/2-k:.3f} {cy_val+W/2-k:.3f}"
                    if is_pad and trace_code:
                        pad_code = ClipperEngine.make_circle(cx_val + W/2.0, cy_val + W/2.0, T * 1.1)
                        uni_res = ClipperEngine.boolean_union(trace_code, pad_code)
                        trace_code = uni_res if uni_res and uni_res.strip() else trace_code
                    final_cell = cell_sq
                    if trace_code:
                        diff_res = ClipperEngine.boolean_difference(cell_sq, trace_code)
                        if diff_res and diff_res.strip():
                            final_cell = diff_res
                    masks.append({"code": final_cell, "cx": cx_val + W/2.0, "cy": cy_val + W/2.0, "col": c, "row": r})

        elif mode_key in ["pattern", "patrón", "patron", "modular"]:
            custom_shape = str(pattern_shape) if (pattern_shape and str(pattern_shape).strip()) else (str(shape_str) if (shape_str and str(shape_str).strip()) else ClipperEngine.make_circle(0, 0, 10))
            S = max(4.0, float(size_x) if (size_x and float(size_x) > 0) else 20.0)
            shp_size = float(size_y) if (size_y and float(size_y) > 0) else S * 0.8
            stagger = True if float(accel_x) > 1.0 else False
            scaled_pat = ClipperEngine.transform_shape(custom_shape, mode="Escalar", factor=shp_size / 20.0 if shp_size > 0 else 1.0)
            c_start = int(math.floor(min_x / S)) - 1
            c_end = int(math.ceil(max_x / S)) + 1
            r_start = int(math.floor(min_y / S)) - 1
            r_end = int(math.ceil(max_y / S)) + 1
            for r in range(r_start, r_end + 1):
                offset_x_val = (S / 2.0) if (stagger and abs(r % 2) == 1) else 0.0
                for c in range(c_start, c_end + 1):
                    cx_val = c * S + offset_x_val
                    cy_val = r * S
                    placed_shape = ClipperEngine.transform_shape(scaled_pat, mode="Offset", offset_x=cx_val + S/2.0, offset_y=cy_val + S/2.0)
                    cell_sq = f"m {cx_val:.3f} {cy_val:.3f} l {cx_val+S:.3f} {cy_val:.3f} l {cx_val+S:.3f} {cy_val+S:.3f} l {cx_val:.3f} {cy_val+S:.3f} l {cx_val:.3f} {cy_val:.3f}"
                    diff_res = ClipperEngine.boolean_difference(cell_sq, placed_shape)
                    final_code = diff_res if (diff_res and diff_res.strip()) else cell_sq
                    masks.append({"code": final_code, "cx": cx_val + S/2.0, "cy": cy_val + S/2.0, "col": c, "row": r})

        else:
            for r in range(1, rows + 1):
                pct_start_y = ((r - 1) / rows) ** float(accel_y)
                pct_end_y = (r / rows) ** float(accel_y)
                l_top = -D_h / 2.0 + (D_h * pct_start_y) - float(overlap) + float(offset_y)
                l_bottom = -D_h / 2.0 + (D_h * pct_end_y) + float(overlap) + float(offset_y)

                for c in range(1, cols + 1):
                    pct_start_x = ((c - 1) / cols) ** float(accel_x)
                    pct_end_x = (c / cols) ** float(accel_x)
                    l_left = -D_w / 2.0 + (D_w * pct_start_x) - float(overlap) + float(offset_x)
                    l_right = -D_w / 2.0 + (D_w * pct_end_x) + float(overlap) + float(offset_x)

                    x1, y1 = rot_point(l_left, l_top)
                    x2, y2 = rot_point(l_right, l_top)
                    x3, y3 = rot_point(l_right, l_bottom)
                    x4, y4 = rot_point(l_left, l_bottom)

                    mask_code = f"m {x1:.3f} {y1:.3f} l {x2:.3f} {y2:.3f} l {x3:.3f} {y3:.3f} l {x4:.3f} {y4:.3f} l {x1:.3f} {y1:.3f}"
                    masks.append({"code": mask_code, "cx": (x1+x3)/2, "cy": (y1+y3)/2, "col": c, "row": r})

        scale = 10000.0
        subj_paths = []
        for c in contours:
            if len(c) >= 3:
                subj_paths.append([[int(round(float(pt[0]) * scale)), int(round(float(pt[1]) * scale))] for pt in c])

        pieces = []
        is_mesh_engine = mode_key in ClipperEngine.MESH_ENGINES
        for m_item in masks:
            m_code = m_item["code"]
            if float(overlap) != 0.0 and is_mesh_engine:
                off_code = ClipperEngine.offset_shape(m_code, delta=float(overlap))
                if off_code and off_code.strip():
                    m_code = off_code

            m_cnts = ClipperEngine.parse_assdraw(m_code)
            if not m_cnts:
                continue

            try:
                pc = pyclipper.Pyclipper()
                for sp in subj_paths:
                    pc.AddPath(sp, pyclipper.PT_SUBJECT, True)
                for c in m_cnts:
                    if len(c) >= 3:
                        pc.AddPath([[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c], pyclipper.PT_CLIP, True)

                solution = pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
                if not solution:
                    continue

                code_parts = []
                all_pts = []
                for path in solution:
                    if len(path) >= 3:
                        pts = [[round(x / scale, 2), round(y / scale, 2)] for x, y in path]
                        path_str = f"m {pts[0][0]} {pts[0][1]} " + " ".join([f"l {p[0]} {p[1]}" for p in pts[1:]])
                        code_parts.append(path_str)
                        all_pts.extend(pts)

                if code_parts and all_pts:
                    min_px = min(p[0] for p in all_pts)
                    max_px = max(p[0] for p in all_pts)
                    min_py = min(p[1] for p in all_pts)
                    max_py = max(p[1] for p in all_pts)
                    pcx = round((min_px + max_px) / 2.0, 2)
                    pcy = round((min_py + max_py) / 2.0, 2)

                    pieces.append({
                        "code": " ".join(code_parts),
                        "cx": pcx,
                        "cy": pcy,
                        "col": m_item["col"],
                        "row": m_item["row"]
                    })
            except Exception:
                continue

        order = int(order)
        if order == 5:
            pieces.sort(key=lambda p: (p["cx"] - cx)**2 + (p["cy"] - cy)**2)
        elif order == 97:
            pieces.sort(key=lambda p: (p["row"], -p["col"]))
        elif order == 13:
            pieces.sort(key=lambda p: (-p["row"], p["col"]))
        elif order == 31:
            pieces.sort(key=lambda p: (-p["row"], -p["col"]))
        elif order == 71:
            pieces.sort(key=lambda p: (p["col"], p["row"]))
        elif order == 17:
            pieces.sort(key=lambda p: (p["col"], -p["row"]))
        elif order == 39:
            pieces.sort(key=lambda p: (-p["col"], -p["row"]))
        else:
            pieces.sort(key=lambda p: (p["row"], p["col"]))

        if len(_SLICE_GRID_CACHE) >= _MAX_CACHE_SIZE:
            _SLICE_GRID_CACHE.popitem(last=False)
        _SLICE_GRID_CACHE[cache_key] = [p.copy() for p in pieces]

        return pieces

    @staticmethod
    def transform_shape(shape_str: str, mode: str = "Escalar", factor: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0) -> str:
        """Applies scale, rotation, and path offset (movevc) transformations to an ASSDraw code."""
        contours = ClipperEngine.parse_assdraw(shape_str)
        if not contours:
            return shape_str

        min_x, min_y, max_x, max_y, cx, cy, w, h = ClipperEngine.get_bbox(contours)
        mode_clean = str(mode).strip().lower()

        transformed = []
        for cnt in contours:
            pts = cnt.copy()
            if "escalar" in mode_clean:
                pts = (pts - [cx, cy]) * float(factor) + [cx, cy]
            elif "rotar" in mode_clean:
                rad = math.radians(float(factor))
                cos_a, sin_a = math.cos(rad), math.sin(rad)
                rel = pts - [cx, cy]
                rx = rel[:, 0] * cos_a - rel[:, 1] * sin_a
                ry = rel[:, 0] * sin_a + rel[:, 1] * cos_a
                pts = np.column_stack((rx, ry)) + [cx, cy]
            elif "offset" in mode_clean or "bordes" in mode_clean:
                pts = pts + [float(offset_x), float(offset_y)]

            parts = [f"m {round(pts[0][0], 2)} {round(pts[0][1], 2)}"]
            for p in pts[1:]:
                parts.append(f"l {round(p[0], 2)} {round(p[1], 2)}")
            transformed.append(" ".join(parts))

        return " ".join(transformed)

    @staticmethod
    def translate_shape(shape_str: str, dx: float, dy: float) -> str:
        """Displaces all coordinates of an ASSDraw code by (dx, dy)."""
        if not shape_str or (dx == 0 and dy == 0):
            return shape_str or ""
        
        def _shift_coord(match):
            x = float(match.group(1)) + float(dx)
            y = float(match.group(2)) + float(dy)
            return f"{round(x, 2)} {round(y, 2)}"

        return re.sub(r'(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)', _shift_coord, str(shape_str))

    @staticmethod
    def clean_self_intersections(shape_str: str, fill_rule=None, scale: float = 10000.0) -> str:
        """Planariza y limpia auto-intersecciones de una forma vectorial usando Clipper CT_UNION."""
        if not shape_str or pyclipper is None:
            return shape_str or ""
        contours = ClipperEngine.parse_assdraw(shape_str)
        if not contours:
            return shape_str
        
        fr = fill_rule
        if fr is None:
            fr = pyclipper.PFT_EVENODD
        elif isinstance(fr, str):
            fr_clean = fr.strip().lower()
            fr = pyclipper.PFT_NONZERO if "nonzero" in fr_clean or "no_zero" in fr_clean or "distinto" in fr_clean else pyclipper.PFT_EVENODD

        pc = pyclipper.Pyclipper()
        for c in contours:
            if len(c) >= 3:
                pc.AddPath([[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c], pyclipper.PT_SUBJECT, True)
        
        try:
            solution = pc.Execute(pyclipper.CT_UNION, fr, fr)
            if not solution:
                return shape_str
            code_parts = []
            for path in solution:
                if len(path) >= 3:
                    pts = [[round(x / scale, 2), round(y / scale, 2)] for x, y in path]
                    path_str = f"m {pts[0][0]} {pts[0][1]} " + " ".join([f"l {p[0]} {p[1]}" for p in pts[1:]]) + f" l {pts[0][0]} {pts[0][1]} "
                    code_parts.append(path_str)
            return "".join(code_parts)
        except Exception:
            return shape_str


    @staticmethod
    def sort_islands_by_order(island_entries, order="79"):
        """Sorts a list of island dictionaries with bounding boxes according to the ordering code (Numpad, Radial, Circular cw/ccw)."""
        if not island_entries or len(island_entries) <= 1:
            return island_entries

        order_str = str(order or "79").strip().lower()
        if "(" in order_str:
            order_str = order_str.split("(")[0].strip()

        if order_str in ("raw", "none", "0", "normal"):
            return island_entries

        if order_str in ("invertido", "inv", "reverse", "invert", "-1"):
            return list(reversed(island_entries))

        if "rand" in order_str or "random" in order_str or "aleator" in order_str:
            copy_entries = list(island_entries)
            import random
            random.shuffle(copy_entries)
            return copy_entries

        has_grid = len(island_entries) > 0 and all('row' in it and 'col' in it for it in island_entries)
        if has_grid:
            if order_str == "79":
                return sorted(island_entries, key=lambda it: (it['row'], it['col']))
            elif order_str == "97":
                return sorted(island_entries, key=lambda it: (it['row'], -it['col']))
            elif order_str == "13":
                return sorted(island_entries, key=lambda it: (-it['row'], it['col']))
            elif order_str == "31":
                return sorted(island_entries, key=lambda it: (-it['row'], -it['col']))
            elif order_str == "71":
                return sorted(island_entries, key=lambda it: (it['col'], it['row']))
            elif order_str == "17":
                return sorted(island_entries, key=lambda it: (it['col'], -it['row']))
            elif order_str == "93":
                return sorted(island_entries, key=lambda it: (-it['col'], it['row']))
            elif order_str == "39":
                return sorted(island_entries, key=lambda it: (-it['col'], -it['row']))

        try:
            import numpy as np
            cxs = np.array([it.get('cx', (it['min_x'] + it['max_x']) / 2.0) for it in island_entries], dtype=np.float64)
            cys = np.array([it.get('cy', (it['min_y'] + it['max_y']) / 2.0) for it in island_entries], dtype=np.float64)
            min_xs = np.array([it['min_x'] for it in island_entries], dtype=np.float64)
            min_ys = np.array([it['min_y'] for it in island_entries], dtype=np.float64)

            global_cx = float(np.mean(cxs))
            global_cy = float(np.mean(cys))
        except Exception:
            cxs = [(it.get('cx', (it['min_x'] + it['max_x']) / 2.0)) for it in island_entries]
            cys = [(it.get('cy', (it['min_y'] + it['max_y']) / 2.0)) for it in island_entries]
            min_xs = [it['min_x'] for it in island_entries]
            min_ys = [it['min_y'] for it in island_entries]
            global_cx = sum(cxs) / len(cxs) if cxs else 0.0
            global_cy = sum(cys) / len(cys) if cys else 0.0

        if order_str in ("5", "centro", "centro a extremos", "center", "center to edges"):
            dist_sq = [(x - global_cx)**2 + (y - global_cy)**2 for x, y in zip(cxs, cys)]
            indices = sorted(range(len(dist_sq)), key=lambda i: dist_sq[i])
            return [island_entries[i] for i in indices]
        elif order_str in ("-5", "5_inv", "extremos", "extremos al centro", "edges", "edges to center"):
            dist_sq = [(x - global_cx)**2 + (y - global_cy)**2 for x, y in zip(cxs, cys)]
            indices = sorted(range(len(dist_sq)), key=lambda i: -dist_sq[i])
            return [island_entries[i] for i in indices]

        if order_str in ("cw", "horario", "clock", "circle", "12", "radial"):
            import math
            angles = []
            for x, y in zip(cxs, cys):
                dx = x - global_cx
                dy = y - global_cy
                deg = (math.degrees(math.atan2(dy, dx)) + 90.0) % 360.0
                angles.append(deg)
            indices = sorted(range(len(angles)), key=lambda i: angles[i])
            return [island_entries[i] for i in indices]
        elif order_str in ("ccw", "antihorario", "counter"):
            import math
            angles = []
            for x, y in zip(cxs, cys):
                dx = x - global_cx
                dy = y - global_cy
                deg = (360.0 - ((math.degrees(math.atan2(dy, dx)) + 90.0) % 360.0)) % 360.0
                angles.append(deg)
            indices = sorted(range(len(angles)), key=lambda i: angles[i])
            return [island_entries[i] for i in indices]

        avg_w = sum(it.get('w', 10.0) for it in island_entries) / len(island_entries)
        col_threshold = max(5.0, avg_w * 0.5)

        if order_str == "71":
            sorted_by_x = sorted(island_entries, key=lambda it: it['min_x'])
            cols = []
            cur_col = []
            cur_x = None
            for it in sorted_by_x:
                x = it['min_x']
                if cur_x is None or abs(x - cur_x) <= col_threshold:
                    cur_col.append(it)
                    cur_x = x
                else:
                    cols.append(cur_col)
                    cur_col = [it]
                    cur_x = x
            if cur_col: cols.append(cur_col)
            res = []
            for col in cols:
                res.extend(sorted(col, key=lambda it: it['min_y']))
            return res

        elif order_str == "17":
            sorted_by_x = sorted(island_entries, key=lambda it: it['min_x'])
            cols = []
            cur_col = []
            cur_x = None
            for it in sorted_by_x:
                x = it['min_x']
                if cur_x is None or abs(x - cur_x) <= col_threshold:
                    cur_col.append(it)
                    cur_x = x
                else:
                    cols.append(cur_col)
                    cur_col = [it]
                    cur_x = x
            if cur_col: cols.append(cur_col)
            res = []
            for col in cols:
                res.extend(sorted(col, key=lambda it: -it['min_y']))
            return res

        elif order_str == "93":
            sorted_by_x = sorted(island_entries, key=lambda it: -it['min_x'])
            cols = []
            cur_col = []
            cur_x = None
            for it in sorted_by_x:
                x = it['min_x']
                if cur_x is None or abs(x - cur_x) <= col_threshold:
                    cur_col.append(it)
                    cur_x = x
                else:
                    cols.append(cur_col)
                    cur_col = [it]
                    cur_x = x
            if cur_col: cols.append(cur_col)
            res = []
            for col in cols:
                res.extend(sorted(col, key=lambda it: it['min_y']))
            return res

        elif order_str == "39":
            sorted_by_x = sorted(island_entries, key=lambda it: -it['min_x'])
            cols = []
            cur_col = []
            cur_x = None
            for it in sorted_by_x:
                x = it['min_x']
                if cur_x is None or abs(x - cur_x) <= col_threshold:
                    cur_col.append(it)
                    cur_x = x
                else:
                    cols.append(cur_col)
                    cur_col = [it]
                    cur_x = x
            if cur_col: cols.append(cur_col)
            res = []
            for col in cols:
                res.extend(sorted(col, key=lambda it: -it['min_y']))
            return res

        avg_h = sum(it.get('h', 10.0) for it in island_entries) / len(island_entries)
        line_threshold = max(5.0, avg_h * 0.5)

        if order_str == "13":
            sorted_by_y = sorted(island_entries, key=lambda it: -it['min_y'])
            lines = []
            cur_line = []
            cur_y = None
            for it in sorted_by_y:
                y = it['min_y']
                if cur_y is None or abs(y - cur_y) <= line_threshold:
                    cur_line.append(it)
                    cur_y = y
                else:
                    lines.append(cur_line)
                    cur_line = [it]
                    cur_y = y
            if cur_line: lines.append(cur_line)
            res = []
            for line in lines:
                res.extend(sorted(line, key=lambda it: it['min_x']))
            return res

        elif order_str == "31":
            sorted_by_y = sorted(island_entries, key=lambda it: -it['min_y'])
            lines = []
            cur_line = []
            cur_y = None
            for it in sorted_by_y:
                y = it['min_y']
                if cur_y is None or abs(y - cur_y) <= line_threshold:
                    cur_line.append(it)
                    cur_y = y
                else:
                    lines.append(cur_line)
                    cur_line = [it]
                    cur_y = y
            if cur_line: lines.append(cur_line)
            res = []
            for line in lines:
                res.extend(sorted(line, key=lambda it: -it['min_x']))
            return res

        elif order_str == "97":
            sorted_by_y = sorted(island_entries, key=lambda it: it['min_y'])
            lines = []
            cur_line = []
            cur_y = None
            for it in sorted_by_y:
                y = it['min_y']
                if cur_y is None or abs(y - cur_y) <= line_threshold:
                    cur_line.append(it)
                    cur_y = y
                else:
                    lines.append(cur_line)
                    cur_line = [it]
                    cur_y = y
            if cur_line: lines.append(cur_line)
            res = []
            for line in lines:
                res.extend(sorted(line, key=lambda it: -it['min_x']))
            return res

        else:
            sorted_by_y = sorted(island_entries, key=lambda it: it['min_y'])
            lines = []
            cur_line = []
            cur_y = None
            for it in sorted_by_y:
                y = it['min_y']
                if cur_y is None or abs(y - cur_y) <= line_threshold:
                    cur_line.append(it)
                    cur_y = y
                else:
                    lines.append(cur_line)
                    cur_line = [it]
                    cur_y = y
            if cur_line: lines.append(cur_line)
            res = []
            for line in lines:
                res.extend(sorted(line, key=lambda it: it['min_x']))
            return res

    @staticmethod
    def decompose_shape_islands(shape_str, fill_rule=None, bbox_mode: str = "marco", scale: float = 100.0, clean_self_intersect: bool = True, order: str = "79") -> list:
        """Descompone una forma vectorial ASS compleja en sus 'islas' o figuras independientes reales (PolyTree)."""
        if not shape_str:
            return []

        if isinstance(shape_str, (list, tuple)):
            res = []
            for item in shape_str:
                res.extend(ClipperEngine.decompose_shape_islands(item, fill_rule=fill_rule, bbox_mode=bbox_mode, scale=scale, clean_self_intersect=clean_self_intersect, order=order))
            return res

        if isinstance(shape_str, str) and shape_str.strip().startswith("[") and shape_str.strip().endswith("]"):
            try:
                import json
                parsed = json.loads(shape_str)
                if isinstance(parsed, list):
                    return ClipperEngine.decompose_shape_islands(parsed, fill_rule=fill_rule, bbox_mode=bbox_mode, scale=scale, clean_self_intersect=clean_self_intersect, order=order)
            except Exception:
                pass

        raw_str = str(shape_str).strip()
        contours = ClipperEngine.parse_assdraw(raw_str)
        if not contours:
            return [raw_str] if raw_str else []

        if pyclipper is None:
            return ClipperEngine.decompose_shape_subpaths(raw_str, bbox_mode=bbox_mode, order=order)

        fr = fill_rule
        if fr is None:
            fr = pyclipper.PFT_EVENODD
        elif isinstance(fr, str):
            fr_clean = fr.strip().lower()
            fr = pyclipper.PFT_NONZERO if "nonzero" in fr_clean or "no_zero" in fr_clean or "distinto" in fr_clean else pyclipper.PFT_EVENODD

        try:
            pc = pyclipper.Pyclipper()
            for c in contours:
                if len(c) >= 3:
                    pc.AddPath([[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c], pyclipper.PT_SUBJECT, True)

            poly_tree = pc.Execute2(pyclipper.CT_UNION, fr, fr)
            island_entries = []

            def traverse_node(node):
                for child in node.Childs:
                    if not child.IsHole:
                        outer_path = [[round(x / scale, 2), round(y / scale, 2)] for x, y in child.Contour]
                        if len(outer_path) < 3:
                            continue
                        outer_str = f"m {outer_path[0][0]} {outer_path[0][1]} " + " ".join([f"l {p[0]} {p[1]}" for p in outer_path[1:]]) + f" l {outer_path[0][0]} {outer_path[0][1]} "

                        holes_strs = []
                        for hole in child.Childs:
                            if hole.IsHole and len(hole.Contour) >= 3:
                                hole_path = [[round(x / scale, 2), round(y / scale, 2)] for x, y in hole.Contour]
                                h_str = f"m {hole_path[0][0]} {hole_path[0][1]} " + " ".join([f"l {p[0]} {p[1]}" for p in hole_path[1:]]) + f" l {hole_path[0][0]} {hole_path[0][1]} "
                                holes_strs.append(h_str)
                                traverse_node(hole)

                        raw_island_figure = outer_str + "".join(holes_strs)
                        f_cnt = ClipperEngine.parse_assdraw(raw_island_figure)
                        if f_cnt:
                            f_min_x, f_min_y, f_max_x, f_max_y, f_cx, f_cy, f_w, f_h = ClipperEngine.get_bbox(f_cnt)
                        else:
                            f_min_x = f_min_y = f_max_x = f_max_y = f_cx = f_cy = f_w = f_h = 0.0
                        island_entries.append({
                            'figure': raw_island_figure,
                            'min_x': f_min_x, 'min_y': f_min_y,
                            'max_x': f_max_x, 'max_y': f_max_y,
                            'cx': f_cx, 'cy': f_cy,
                            'w': f_w, 'h': f_h
                        })

            traverse_node(poly_tree)

            island_entries = ClipperEngine.sort_islands_by_order(island_entries, order=order)

            real_figures = []
            bbox_clean = str(bbox_mode).lower()
            for it in island_entries:
                full_fig = it['figure']
                if "origen" in bbox_clean:
                    full_fig = ClipperEngine.translate_shape(full_fig, -it['min_x'], -it['min_y'])
                elif "centro" in bbox_clean:
                    full_fig = ClipperEngine.translate_shape(full_fig, -it['cx'], -it['cy'])
                real_figures.append(full_fig)

            return real_figures if real_figures else [raw_str]
        except Exception:
            return ClipperEngine.decompose_shape_subpaths(raw_str, bbox_mode=bbox_mode, order=order)

    @staticmethod
    def decompose_shape_subpaths(shape_str, bbox_mode: str = "marco", order: str = "79") -> list:
        """Descompone un shape ASS en sub-rutas individuales por cada comando 'm' (modo naive compatible)."""
        if not shape_str:
            return []

        if isinstance(shape_str, (list, tuple)):
            res = []
            for item in shape_str:
                res.extend(ClipperEngine.decompose_shape_subpaths(item, bbox_mode=bbox_mode, order=order))
            return res

        if isinstance(shape_str, str) and shape_str.strip().startswith("[") and shape_str.strip().endswith("]"):
            try:
                import json
                parsed = json.loads(shape_str)
                if isinstance(parsed, list):
                    return ClipperEngine.decompose_shape_subpaths(parsed, bbox_mode=bbox_mode, order=order)
            except Exception:
                pass
        
        raw_str = str(shape_str).strip()
        contours = ClipperEngine.parse_assdraw(raw_str)
        if not contours:
            return [raw_str]

        min_x, min_y, max_x, max_y, cx, cy, w, h = ClipperEngine.get_bbox(contours)

        parts = re.split(r'(?=(?:^|\s)m\s+-?\d)', raw_str)
        tokens = [p.strip() for p in parts if p.strip()]
        if not tokens:
            tokens = [raw_str]

        sub_entries = []
        for t in tokens:
            sub = t.strip()
            if not sub:
                continue
            f_cnt = ClipperEngine.parse_assdraw(sub)
            if f_cnt:
                f_min_x, f_min_y, f_max_x, f_max_y, f_cx, f_cy, f_w, f_h = ClipperEngine.get_bbox(f_cnt)
            else:
                f_min_x = f_min_y = f_max_x = f_max_y = f_cx = f_cy = f_w = f_h = 0.0
            sub_entries.append({
                'figure': sub,
                'min_x': f_min_x, 'min_y': f_min_y,
                'max_x': f_max_x, 'max_y': f_max_y,
                'cx': f_cx, 'cy': f_cy,
                'w': f_w, 'h': f_h
            })

        sub_entries = ClipperEngine.sort_islands_by_order(sub_entries, order=order)

        subpaths = []
        bbox_clean = str(bbox_mode).lower()
        for it in sub_entries:
            sub = it['figure']
            if "origen" in bbox_clean:
                sub = ClipperEngine.translate_shape(sub, -it['min_x'], -it['min_y'])
            elif "centro" in bbox_clean:
                sub = ClipperEngine.translate_shape(sub, -it['cx'], -it['cy'])
            subpaths.append(sub)

        return subpaths if subpaths else [raw_str]

    @staticmethod
    def merge_multiple_shapes(shapes_list: list, fill_rule=None, scale: float = 10000.0) -> str:
        """
        Merges multiple vector shapes into a single clean closed geometry using Clipper CT_UNION.
        Removes redundant internal edges and preserves cutout orientation.
        """
        if not shapes_list:
            return ""
        
        valid_shapes = []
        for s in shapes_list:
            if isinstance(s, (list, tuple)):
                valid_shapes.extend([str(item).strip() for item in s if item and str(item).strip()])
            elif isinstance(s, str) and s.strip().startswith("[") and s.strip().endswith("]"):
                try:
                    import json
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        valid_shapes.extend([str(item).strip() for item in parsed if item and str(item).strip()])
                    else:
                        valid_shapes.append(s.strip())
                except Exception:
                    valid_shapes.append(s.strip())
            elif s and str(s).strip():
                valid_shapes.append(str(s).strip())

        if not valid_shapes:
            return ""
        if len(valid_shapes) == 1:
            return ClipperEngine.clean_self_intersections(valid_shapes[0], fill_rule=fill_rule, scale=scale)

        if pyclipper is None:
            return " ".join(valid_shapes)

        fr = fill_rule
        if fr is None:
            fr = pyclipper.PFT_NONZERO
        elif isinstance(fr, str):
            fr_clean = fr.strip().lower()
            fr = pyclipper.PFT_EVENODD if "evenodd" in fr_clean or "par" in fr_clean else pyclipper.PFT_NONZERO

        try:
            pc = pyclipper.Pyclipper()
            for shp in valid_shapes:
                contours = ClipperEngine.parse_assdraw(shp)
                for c in contours:
                    if len(c) >= 3:
                        pc.AddPath([[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c], pyclipper.PT_SUBJECT, True)

            solution = pc.Execute(pyclipper.CT_UNION, fr, fr)
            if not solution:
                return ""

            code_parts = []
            for path in solution:
                if len(path) >= 3:
                    pts = [[round(x / scale, 2), round(y / scale, 2)] for x, y in path]
                    path_str = f"m {pts[0][0]} {pts[0][1]} " + " ".join([f"l {p[0]} {p[1]}" for p in pts[1:]]) + f" l {pts[0][0]} {pts[0][1]} "
                    code_parts.append(path_str)

            return "".join(code_parts)
        except Exception:
            return " ".join(valid_shapes)

    @staticmethod
    def _split_tag_keyframes(tags_input):
        if tags_input is None:
            return []
        if isinstance(tags_input, (list, tuple)):
            res = []
            for item in tags_input:
                if isinstance(item, (list, tuple)):
                    res.extend(ClipperEngine._split_tag_keyframes(item))
                elif isinstance(item, str):
                    res.extend(ClipperEngine._split_tag_keyframes(item))
                elif item is not None:
                    res.append(str(item).strip())
            return [r for r in res if r]
        
        s = str(tags_input).strip()
        if not s:
            return []
        if s.startswith("[") and s.endswith("]"):
            try:
                import json
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return ClipperEngine._split_tag_keyframes(parsed)
            except Exception:
                pass
            try:
                import ast
                parsed = ast.literal_eval(s)
                if isinstance(parsed, list):
                    return ClipperEngine._split_tag_keyframes(parsed)
            except Exception:
                pass
            inner = s[1:-1].strip()
            return ClipperEngine._split_tag_keyframes(inner)
            
        tokens = []
        curr = []
        paren_depth = 0
        brace_depth = 0
        for ch in s:
            if ch == '(':
                paren_depth += 1
                curr.append(ch)
            elif ch == ')':
                paren_depth = max(0, paren_depth - 1)
                curr.append(ch)
            elif ch == '{':
                brace_depth += 1
                curr.append(ch)
            elif ch == '}':
                brace_depth = max(0, brace_depth - 1)
                curr.append(ch)
            elif ch in (',', ';', '\n') and paren_depth == 0 and brace_depth == 0:
                token = "".join(curr).strip()
                if token:
                    tokens.append(token)
                curr = []
            else:
                curr.append(ch)
        if curr:
            token = "".join(curr).strip()
            if token:
                tokens.append(token)
        return tokens

    @staticmethod
    def _parse_tag_keyframe(kf_str):
        from utils import parse_color_to_rgb, rgb_to_ass_color
        s = str(kf_str).strip().strip('{}').strip().strip('\'"').strip()
        s = re.sub(r'\\{2,}', r'\\', s)
        if not s:
            return {}
        
        if not s.startswith('\\'):
            clean_hex = s.lstrip('#').replace('&H', '').replace('&h', '').replace('&', '').strip()
            is_valid_color = (
                s.startswith('#') or 
                s.startswith('&H') or 
                s.startswith('&h') or 
                (len(clean_hex) in (6, 8) and all(c in '0123456789abcdefABCDEF' for c in clean_hex)) or
                s.lower() in ('white', 'black', 'red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'gray', 'grey')
            )
            if is_valid_color:
                try:
                    r, g, b = parse_color_to_rgb(s)
                    return {'1c': {'type': 'color', 'prefix': '\\1c', 'val': (r, g, b), 'raw': f'\\1c{rgb_to_ass_color(r, g, b)}'}}
                except Exception:
                    pass

        tag_pattern = r'(\\(?:pos|org|move|clip|iclip|fad|fade|t)\([^)]*\)|\\(?:[1-4]?c|[1-4]?a|alpha|an|a|fscx|fscy|frz|frx|fry|fr|fax|fay|xbord|ybord|bord|xshad|yshad|shad|blur|be|fsp|fs|fn|p|q|r|b|i|u|s|[kK]f?|ko?)(?:&H[0-9a-fA-F]+&|[^\\]*))'
        numeric_tag_re = re.compile(r'^(\\(?:fscx|fscy|frz|frx|fry|fr|fax|fay|xbord|ybord|bord|xshad|yshad|shad|blur|be|fsp|fs))(-?[\d.]+)$')
        global_tag_prefixes = ('\\pos', '\\move', '\\org', '\\an', '\\a', '\\fad', '\\fade', '\\clip', '\\iclip')

        matches = re.findall(tag_pattern, s)
        parsed_tags = {}
        disc_idx = 0
        for m in matches:
            m = m.strip()
            if not m:
                continue
            
            if m.startswith('\\1c') or m.startswith('\\c') or m.startswith('\\2c') or m.startswith('\\3c') or m.startswith('\\4c'):
                if m.startswith('\\2c'):
                    k = '2c'; pref = '\\2c'; col_str = m[3:]
                elif m.startswith('\\3c'):
                    k = '3c'; pref = '\\3c'; col_str = m[3:]
                elif m.startswith('\\4c'):
                    k = '4c'; pref = '\\4c'; col_str = m[3:]
                elif m.startswith('\\1c'):
                    k = '1c'; pref = '\\1c'; col_str = m[3:]
                else:
                    k = '1c'; pref = '\\1c'; col_str = m[2:]
                try:
                    rgb = parse_color_to_rgb(col_str)
                    parsed_tags[k] = {'type': 'color', 'prefix': pref, 'val': rgb, 'raw': m}
                    continue
                except Exception:
                    pass
                
            if m.startswith('\\1a') or m.startswith('\\2a') or m.startswith('\\3a') or m.startswith('\\4a') or m.startswith('\\alpha'):
                if m.startswith('\\alpha'):
                    k = 'alpha'; pref = '\\alpha'; a_str = m[6:]
                else:
                    k = m[1:3]; pref = '\\' + k; a_str = m[3:]
                a_clean = a_str.strip().strip('&').lstrip('Hh')
                try:
                    a_val = int(a_clean, 16) if a_clean else 0
                    parsed_tags[k] = {'type': 'alpha', 'prefix': pref, 'val': max(0, min(255, a_val)), 'raw': m}
                    continue
                except Exception:
                    pass
                
            is_global = False
            for g_pref in global_tag_prefixes:
                if m.startswith(g_pref):
                    k = g_pref.lstrip('\\')
                    parsed_tags[k] = {'type': 'global', 'prefix': g_pref, 'val': m, 'raw': m}
                    is_global = True
                    break
            if is_global:
                continue
                
            m_num = numeric_tag_re.match(m)
            if m_num:
                pref = m_num.group(1)
                k = pref.lstrip('\\')
                if k == 'fr':
                    k = 'frz'; pref = '\\frz'
                try:
                    num_val = float(m_num.group(2))
                    parsed_tags[k] = {'type': 'numeric', 'prefix': pref, 'val': num_val, 'raw': m}
                    continue
                except Exception:
                    pass
                
            k = f'disc_{disc_idx}'
            disc_idx += 1
            parsed_tags[k] = {'type': 'discrete', 'prefix': m, 'val': m, 'raw': m}
            
        return parsed_tags

    @staticmethod
    def _interpolate_tag_keyframes(keyframes, t_norm, is_first_piece=False):
        from utils import rgb_to_ass_color
        t_clamped = max(0.0, min(1.0, float(t_norm)))
        if not keyframes:
            return ""
            
        def _format_num(v):
            if float(v).is_integer():
                return str(int(v))
            return f"{v:.2f}".rstrip('0').rstrip('.')

        def _format_single_tag(t):
            tag_type = t['type']
            pref = t['prefix']
            if tag_type == 'color':
                r, g, b = t['val']
                return f"{pref}{rgb_to_ass_color(r, g, b)}"
            elif tag_type == 'alpha':
                a_v = t['val']
                return f"{pref}&H{a_v:02X}&"
            elif tag_type == 'numeric':
                return f"{pref}{_format_num(t['val'])}"
            return str(t.get('raw', t.get('val', '')))

        def _sort_and_join_tags(tag_dict):
            sorted_keys = sorted(tag_dict.keys(), key=lambda k: (
                0 if k == 'an' else
                1 if k in ('pos', 'move') else
                2 if k == 'org' else
                3 if k in ('1c', '2c', '3c', '4c', 'alpha', '1a', '2a', '3a', '4a') else
                9 if k == 'p' else 5
            ))
            return ''.join(tag_dict[k] for k in sorted_keys)

        tag_defaults = {
            'frz': 0.0, 'frx': 0.0, 'fry': 0.0,
            'fscx': 100.0, 'fscy': 100.0,
            'fax': 0.0, 'fay': 0.0,
            'blur': 0.0, 'be': 0.0,
            'bord': 0.0, 'xbord': 0.0, 'ybord': 0.0,
            'shad': 0.0, 'xshad': 0.0, 'yshad': 0.0,
            'fsp': 0.0,
            '1a': 0, '2a': 0, '3a': 0, '4a': 0, 'alpha': 0
        }

        if len(keyframes) == 1:
            kf = keyframes[0]
            res = {}
            for k, v in kf.items():
                if v['type'] == 'global' and not is_first_piece:
                    continue
                res[k] = _format_single_tag(v)
            return _sort_and_join_tags(res)
            
        n_segments = len(keyframes) - 1
        pos = t_clamped * n_segments
        idx = int(pos)
        if idx >= n_segments:
            idx = n_segments - 1
            local_t = 1.0
        else:
            local_t = pos - idx
            
        kf1 = keyframes[idx]
        kf2 = keyframes[idx + 1]
        
        all_keys = list(dict.fromkeys(list(kf1.keys()) + list(kf2.keys())))
        merged_tags = {}

        for k in all_keys:
            t1 = kf1.get(k)
            t2 = kf2.get(k)
            
            tag_type = (t1 or t2)['type']
            if tag_type == 'global':
                if is_first_piece:
                    chosen = t1 if t1 else t2
                    merged_tags[k] = _format_single_tag(chosen)
                continue
            
            if t1 and t2:
                pref = t1['prefix']
                if tag_type == 'color':
                    r1, g1, b1 = t1['val']
                    r2, g2, b2 = t2['val']
                    r = int(round(r1 + (r2 - r1) * local_t))
                    g = int(round(g1 + (g2 - g1) * local_t))
                    b = int(round(b1 + (b2 - b1) * local_t))
                    merged_tags[k] = f"{pref}{rgb_to_ass_color(r, g, b)}"
                elif tag_type == 'alpha':
                    a1, a2 = t1['val'], t2['val']
                    a = max(0, min(255, int(round(a1 + (a2 - a1) * local_t))))
                    merged_tags[k] = f"{pref}&H{a:02X}&"
                elif tag_type == 'numeric':
                    v1, v2 = t1['val'], t2['val']
                    v = v1 + (v2 - v1) * local_t
                    merged_tags[k] = f"{pref}{_format_num(v)}"
                else:
                    chosen = t1 if local_t < 0.5 else t2
                    merged_tags[k] = _format_single_tag(chosen)
            elif t1:
                pref = t1['prefix']
                if tag_type == 'numeric' and k in tag_defaults:
                    v1 = t1['val']
                    v2 = tag_defaults[k]
                    v = v1 + (v2 - v1) * local_t
                    merged_tags[k] = f"{pref}{_format_num(v)}"
                elif tag_type == 'alpha':
                    a1 = t1['val']
                    a2 = tag_defaults.get(k, 0)
                    a = max(0, min(255, int(round(a1 + (a2 - a1) * local_t))))
                    merged_tags[k] = f"{pref}&H{a:02X}&"
                else:
                    merged_tags[k] = _format_single_tag(t1)
            elif t2:
                pref = t2['prefix']
                if tag_type == 'numeric' and k in tag_defaults:
                    v1 = tag_defaults[k]
                    v2 = t2['val']
                    v = v1 + (v2 - v1) * local_t
                    merged_tags[k] = f"{pref}{_format_num(v)}"
                elif tag_type == 'alpha':
                    a1 = tag_defaults.get(k, 0)
                    a2 = t2['val']
                    a = max(0, min(255, int(round(a1 + (a2 - a1) * local_t))))
                    merged_tags[k] = f"{pref}&H{a:02X}&"
                else:
                    merged_tags[k] = _format_single_tag(t2)
                    
        return _sort_and_join_tags(merged_tags)
    @staticmethod
    def fusion_shapes_tags(shapes_list, tags="", bbox_mode="marco", tag_mode="ipol"):
        """Merges multiple shapes into a single ASS drawing block by assigning or interpolating tags.
        - In 'ipol' mode: Interpolates keyframes proportionally between generated pieces (0.0 -> 1.0).
        - In 'line' mode: Strictly assigns keyframes 1:1 in the order received (skips surplus and omits tagging if missing keyframes).
        - If tags is empty: Returns union of shapes without extra tag blocks.
        """
        if not shapes_list:
            return ""
        
        flat_shapes = []
        for s in shapes_list:
            if isinstance(s, (list, tuple)):
                flat_shapes.extend([str(item).strip() for item in s if item and str(item).strip()])
            elif isinstance(s, str) and s.strip().startswith("[") and s.strip().endswith("]"):
                try:
                    import json
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        flat_shapes.extend([str(item).strip() for item in parsed if item and str(item).strip()])
                    else:
                        flat_shapes.append(s.strip())
                except Exception:
                    flat_shapes.append(s.strip())
            elif s and str(s).strip():
                flat_shapes.append(str(s).strip())

        if not flat_shapes:
            return ""

        tags_str = str(tags or "").strip()
        if not tags_str:
            return "".join(flat_shapes)

        raw_tag_tokens = ClipperEngine._split_tag_keyframes(tags_str)
        if not raw_tag_tokens:
            return "".join(flat_shapes)

        n_shapes = len(flat_shapes)

        bboxes = []
        for s in flat_shapes:
            cnt = ClipperEngine.parse_assdraw(s)
            if cnt:
                bx = ClipperEngine.get_bbox(cnt)
                bboxes.append(bx)
            else:
                bboxes.append((0, 0, 0, 0, 0, 0, 0, 0))

        max_h = max((b[7] for b in bboxes), default=0.0)

        blended_shapes = []
        sum_w = 0.0
        for i, s in enumerate(flat_shapes):
            w_i = bboxes[i][6]
            h_i = bboxes[i][7]
            dx = -sum_w
            dy = -(max_h - h_i)
            shifted = ClipperEngine.transform_shape(s, mode="Offset", offset_x=dx, offset_y=dy)
            blended_shapes.append(shifted)
            sum_w += w_i

        result_parts = []
        if str(tag_mode).strip().lower() == "line":
            for i, shp in enumerate(blended_shapes):
                if i < len(raw_tag_tokens):
                    t = raw_tag_tokens[i].strip()
                    if t.startswith("{") and t.endswith("}"):
                        t = t[1:-1].strip()
                    if t:
                        result_parts.append(f"{{{t}}}{shp}")
                    else:
                        result_parts.append(f"{{\\p1}}{shp}")
                else:
                    result_parts.append(f"{{\\p1}}{shp}")
        else:
            keyframes = [ClipperEngine._parse_tag_keyframe(t) for t in raw_tag_tokens]
            keyframes = [kf for kf in keyframes if kf]
            if not keyframes:
                return "".join(flat_shapes)

            for i, shp in enumerate(blended_shapes):
                progress = i / (n_shapes - 1.0) if n_shapes > 1 else 0.0
                tag_str = ClipperEngine._interpolate_tag_keyframes(keyframes, progress, is_first_piece=(i == 0))
                if tag_str:
                    result_parts.append(f"{{{tag_str}}}{shp}")
                else:
                    result_parts.append(f"{{\\p1}}{shp}")

        return "".join(result_parts)

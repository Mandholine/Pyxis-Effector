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

# clipper_engine.py
"""Motor de slicing 1D/2D, 22 motores de mallas y transformaciones de polígonos ASSdraw.
Utiliza NumPy y PyClipper para aceleración matemática nativa a velocidad C.
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

# Almacenes de Caché LRU deterministas para máxima aceleración
_MAX_CACHE_SIZE = 1024
_SLICE_GRID_CACHE = OrderedDict()
_PARSE_ASSDRAW_CACHE = OrderedDict()

class ClipperEngine:
    """Motor de operaciones de corte y despiece vectorial para ASSdraw."""

    # Registro de los 22 motores de malla
    MESH_ENGINES = [
        "hex", "tri", "dia", "ring", "voronoi", "delaunay", "brick", "jigsaw",
        "circuit", "kagome", "rhombille", "herringbone", "mondrian", "truchet",
        "scallop", "ashlar", "bez", "octagon", "ray", "web", "quad", "pattern"
    ]

    @staticmethod
    def clear_cache():
        """Limpia todos los almacenes de caché en memoria de ClipperEngine."""
        _SLICE_GRID_CACHE.clear()
        _PARSE_ASSDRAW_CACHE.clear()

    @staticmethod
    def sample_cubic_bezier(p0, p1, p2, p3, steps=10):
        """Muestra una curva Bézier cúbica entre p0 y p3 con puntos de control p1 y p2."""
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
        """Generador pseudo-aleatorio determinista por coordenadas espaciales."""
        s = abs(int(math.floor(c)) * 73856093 + int(math.floor(r)) * 19349663 + int(offset or 12345))
        s = (s * 1103515245 + 12345) % 2147483648
        return s / 2147483648.0

    @staticmethod
    def make_circle(cx, cy, r):
        """Genera un círculo cerrado ASSDraw con suavidad poligonal."""
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
        """Parsea comandos ASSdraw (m, l, b, c) a una lista de contornos de puntos (N, 2),
        soportando repetición implícita de coordenadas para m, l, b y aplanando curvas Bézier.
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
        """Calcula el Bounding Box (min_x, min_y, max_x, max_y, cx, cy, w, h)."""
        if not contours:
            return 0.0, 0.0, 100.0, 100.0, 50.0, 50.0, 100.0, 100.0

        all_pts = np.vstack(contours)
        min_x, min_y = np.min(all_pts, axis=0)
        max_x, max_y = np.max(all_pts, axis=0)
        w = max(0.001, max_x - min_x)
        h = max(0.001, max_y - min_y)
        cx = min_x + w * 0.5
        cy = min_y + h * 0.5
        return float(min_x), float(min_y), float(max_x), float(max_y), float(cx), float(cy), float(w), float(h)

    @staticmethod
    def boolean_intersection(subject_shape: str, clip_shape: str, scale: float = 10000.0) -> str:
        """Realiza la intersección booleana vectorial real entre subject_shape y clip_shape usando Clipper/pyclipper."""
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
        """Realiza la unión booleana vectorial real entre shape_a y shape_b usando Clipper/pyclipper."""
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
            # Fijar arc_tolerance a 0.25px en coordenadas reales (0.25 * scale)
            # para evitar saturación de miles de puntos microscópicos en curvas horizontales.
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
        """Convierte líneas abiertas o contornos cerrados en polígonos cerrados ASSDraw con grosor uniforme.
        - Para líneas/splines abiertas: genera una tira continua con terminaciones (Round, Square, Flat/Butt).
        - Para polígonos cerrados: genera un contorno hueco (diferencia booleana entre offset exterior e interior).
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
        """Slicer universal 1D/2D y de 22 motores de malla.
        Soporta escalado dual (scale_x, scale_y), tamaños personalizados (size_x, size_y), offsetting (offset_x, offset_y),
        y pre-escalado de texto (text_scale) junto con pre-offsetting de contorno original (pre_offset) según la API de Seijitsu Extensions.
        Devuelve una lista de diccionarios con {code, cx, cy, col, row}.
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

        # Dimensiones de la malla considerando rotación del Bounding Box de la tinta del objeto
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

        elif mode_key in ["dia", "diamante"]:
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

        elif mode_key in ["ring", "anillos"]:
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

        elif mode_key in ["ray", "radial", "rayos"]:
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

        elif mode_key in ["rhombille", "cubos"]:
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

        elif mode_key in ["pattern", "patrón", "patron"]:
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

        else: # Default Grid 1D/2D
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

        # Ordenamiento direccional (Order keypad: 79, 5, 13, 31, 71, 17, 39, etc.)
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
        """Aplica transformaciones de escalado, rotación, offset de caminos (movevc) a un código ASSdraw."""
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

            # Convert to ASSdraw string
            parts = [f"m {round(pts[0][0], 2)} {round(pts[0][1], 2)}"]
            for p in pts[1:]:
                parts.append(f"l {round(p[0], 2)} {round(p[1], 2)}")
            transformed.append(" ".join(parts))

        return " ".join(transformed)

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

try:
    import pyclipper
except ImportError:
    import subprocess, sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyclipper"])
        import pyclipper
    except Exception:
        pyclipper = None

class ClipperEngine:
    """Motor de operaciones de corte y despiece vectorial para ASSdraw."""

    # Registro de los 22 motores de malla
    MESH_ENGINES = [
        "hex", "tri", "dia", "ring", "voronoi", "delaunay", "brick", "jigsaw",
        "circuit", "kagome", "rhombille", "herringbone", "mondrian", "truchet",
        "scallop", "ashlar", "bez", "octagon", "ray", "web", "quad", "pattern"
    ]

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
    def parse_assdraw(shape_str: str, bezier_steps: int = 10):
        """Parsea comandos ASSdraw (m, l, b, c) a una lista de contornos de puntos (N, 2),
        soportando repetición implícita de coordenadas para m, l, b y aplanando curvas Bézier.
        """
        if not shape_str or not str(shape_str).strip():
            return []

        tokens = str(shape_str).strip().split()
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
                        if len(current_contour) >= 3:
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

        if len(current_contour) >= 3:
            contours.append(np.array(current_contour, dtype=np.float64))

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
    def slice_grid(shape_str: str, cols: int = 2, rows: int = 2, size_x: float = 0.0, size_y: float = 0.0,
                   scale_x: float = 1.0, scale_y: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0,
                   angle: float = 0.0, overlap: float = 0.0, accel: float = 1.0, order: int = 79,
                   text_scale: float = 1.0, pre_offset: float = 0.0, engine_mode: str = "grid",
                   accel_x: float = 1.0, accel_y: float = 1.0):
        """Slicer universal 1D/2D y de 22 motores de malla.
        Soporta escalado dual (scale_x, scale_y), tamaños personalizados (size_x, size_y), offsetting (offset_x, offset_y),
        y pre-escalado de texto (text_scale) junto con pre-offsetting de contorno original (pre_offset) según la API de Seijitsu Extensions.
        Devuelve una lista de diccionarios con {code, cx, cy, col, row}.
        """
        if accel != 1.0:
            if accel_x == 1.0: accel_x = accel
            if accel_y == 1.0: accel_y = accel

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
            R = float(size_x) if (size_x and 0 < float(size_x) < 80.0) else max(5.0, h / 3.5)
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
            R = float(size_x) if (size_x and 0 < float(size_x) < 80.0) else max(5.0, h / 3.5)
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
            R = float(size_x) if (size_x and 0 < float(size_x) < 80.0) else max(5.0, h / 3.5)
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
            ring_w = float(size_x) if (size_x and 0 < float(size_x) < 80.0) else max(4.0, h / 5.0)
            max_r = math.sqrt((w/2.0)**2 + (h/2.0)**2) + 20.0
            num_rings = int(math.ceil(max_r / ring_w))
            for i in range(num_rings):
                r_in = i * ring_w
                r_out = (i + 1) * ring_w
                c_out = f"m {cx + r_out:.3f} {cy:.3f} b {cx + r_out:.3f} {cy + r_out*0.552:.3f} {cx + r_out*0.552:.3f} {cy + r_out:.3f} {cx:.3f} {cy + r_out:.3f} b {cx - r_out*0.552:.3f} {cy + r_out:.3f} {cx - r_out:.3f} {cy + r_out*0.552:.3f} {cx - r_out:.3f} {cy:.3f} b {cx - r_out:.3f} {cy - r_out*0.552:.3f} {cx - r_out*0.552:.3f} {cy - r_out:.3f} {cx:.3f} {cy - r_out:.3f} b {cx + r_out*0.552:.3f} {cy - r_out:.3f} {cx + r_out:.3f} {cy - r_out*0.552:.3f} {cx + r_out:.3f} {cy:.3f}"
                if r_in == 0:
                    masks.append({"code": c_out, "cx": cx, "cy": cy, "col": i+1, "row": 1})
                else:
                    c_in = f"m {cx + r_in:.3f} {cy:.3f} b {cx + r_in:.3f} {cy + r_in*0.552:.3f} {cx + r_in*0.552:.3f} {cy + r_in:.3f} {cx:.3f} {cy + r_in:.3f} b {cx - r_in*0.552:.3f} {cy + r_in:.3f} {cx - r_in:.3f} {cy + r_in*0.552:.3f} {cx - r_in:.3f} {cy:.3f} b {cx - r_in:.3f} {cy - r_in*0.552:.3f} {cx - r_in*0.552:.3f} {cy - r_in:.3f} {cx:.3f} {cy - r_in:.3f} b {cx + r_in*0.552:.3f} {cy - r_in:.3f} {cx + r_out:.3f} {cy - r_out*0.552:.3f} {cx + r_out:.3f} {cy:.3f}"
                    ring_code = ClipperEngine.boolean_difference(c_out, c_in)
                    masks.append({"code": ring_code, "cx": cx, "cy": cy, "col": i+1, "row": 1})

        elif mode_key in ["ray", "radial", "rayos"]:
            ang_step = max(1.0, min(360.0, float(size_x) if (size_x and float(size_x) > 0) else 30.0))
            num_rays = int(math.ceil(360.0 / ang_step))
            max_r = math.sqrt((w/2.0)**2 + (h/2.0)**2) + 20.0
            for i in range(num_rays):
                a1 = math.radians(i * ang_step)
                a2 = math.radians(min(360.0, (i + 1) * ang_step))
                x1, y1 = cx + max_r * math.cos(a1), cy + max_r * math.sin(a1)
                x2, y2 = cx + max_r * math.cos(a2), cy + max_r * math.sin(a2)
                ray_code = f"m {cx:.3f} {cy:.3f} l {x1:.3f} {y1:.3f} l {x2:.3f} {y2:.3f} l {cx:.3f} {cy:.3f}"
                mid_a = (a1 + a2) / 2.0
                masks.append({"code": ray_code, "cx": cx + math.cos(mid_a)*max_r*0.5, "cy": cy + math.sin(mid_a)*max_r*0.5, "col": i+1, "row": 1})

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
                pcx_sum, pcy_sum, pt_count = 0.0, 0.0, 0
                for path in solution:
                    if len(path) >= 3:
                        pts = [[round(x / scale, 2), round(y / scale, 2)] for x, y in path]
                        path_str = f"m {pts[0][0]} {pts[0][1]} " + " ".join([f"l {p[0]} {p[1]}" for p in pts[1:]])
                        code_parts.append(path_str)
                        for p in pts:
                            pcx_sum += p[0]
                            pcy_sum += p[1]
                            pt_count += 1

                if code_parts:
                    pieces.append({
                        "code": " ".join(code_parts),
                        "cx": round(pcx_sum / pt_count, 2) if pt_count else m_item["cx"],
                        "cy": round(pcy_sum / pt_count, 2) if pt_count else m_item["cy"],
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


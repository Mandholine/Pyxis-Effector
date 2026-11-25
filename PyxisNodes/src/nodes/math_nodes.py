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
Module: math_nodes.py
Architectural Role: Canonical `ke.math` Mathematical Computation Engine, Stochastic Dispatch, and Geometric Kinematics.

This module provides the numeric evaluation infrastructure for Pyxis Effector:
    - Master Math Evaluation (`eval_math_node`): Direct 1:1 canonical reflection of the
      `ke.math` module from Effector 2 (`newkara_library.lua`), organised into five categories
      (`numeric`, `sequence`, `geometry`, `algebra`, `data`) covering all 27 public operations
      plus the `KeMatrix` algebra class.
    - Stochastic Pseudo-Random Suite (`_pyxis_random_*`, `math_random_master`): Comprehensive deterministic
      and stepped pseudo-random generation supporting integer, signed, decimal, resolution-scaled, palette colour,
      boolean, and list-choice operations.
    - Scoped Randomness (`PyxisScopedRandom`, `PyxisByDispatcher`): Caches random seeds tied to specific
      syntactic iterations (`by.syl.R`, `by.char.Rs`, `by.line.Rcolor`), ensuring spatial consistency across render passes.
    - Kinematic Polar Projection (`math_polar`): Evaluates polar coordinate offsets into ASS `\\pos(x, y)` tags.
    - De Casteljau Bézier Interpolator (`math_bezier_node`): Computes quadratic and cubic Bézier splines
      returning evaluated coordinates at progress t in [0.0, 1.0] or formatted ASSdraw vector commands.

Upstream Dependencies:
    - decorators.py: `@pyxis_node`, `NODE_REGISTRY`.
    - node_engine.py: `_eval_num_expr` for dynamic expression evaluation in numeric fields.
    - utils.py: `parse_color_to_rgb`, `rgb_to_ass_color`, `rgb_to_hex_color` for colour interpolation.

Downstream Callers:
    - node_engine.GraphEngine: Dispatches `Basics/Math`, `Basics/MultiRandom`, `Functions/Polar`, and `Functions/Bezier`.
    - code_nodes.py & string_evaluator.py: Injects `by` dispatcher and random helpers into the scripting sandbox.
    - node_validator.GraphValidator: Validates mathematical expressions and random signatures.
"""

import math
import random
import re
import sys
import time
from decorators import pyxis_node, NODE_REGISTRY

ROUND_NUM = 3
ROUND_MATRIX = 6
EPSILON = 1e-6

_NUM_TOKEN_RE = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_ASS_PAIR_RE = re.compile(r"(-?\d[\d.]*)\s+(-?\d[\d.]*)")
_FMT_SPEC_RE = re.compile(r"%[-+#0 ]*\d*(?:\.\d+)?[aAcdeEfgGioqsuxX]")
_ASS_SHAPE_RE = re.compile(r"m\s+-?\d[\d.\-\smlb]*", re.IGNORECASE)


def _eval_num(val, context=None, default=0.0):
    """
    Safely evaluate and cast an input parameter into a floating-point numeric value.

    Supports raw numeric types, comma-delimited decimal notation (e.g. "3,14" -> 3.14),
    and dynamic mathematical formulas via `node_engine._eval_num_expr`.

    Args:
        val (Any): Value, literal string, or formula expression.
        context (dict | None): Context dictionary for variable evaluation.
        default (float): Fallback value if conversion fails or input is empty.

    Returns:
        float: Evaluated floating-point numeric representation.
    """
    if val is None or val == "":
        return float(default)
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)

    s_val = str(val).strip()
    if s_val == "":
        return float(default)
    if re.match(r"^[+-]?\d+,\d+$", s_val):
        s_val = s_val.replace(",", ".")

    try:
        from node_engine import _eval_num_expr
        return float(_eval_num_expr(s_val, context, default=default))
    except Exception:
        pass

    try:
        return float(s_val.replace(",", "."))
    except Exception:
        return float(default)


def _ke_bool(val, default=False):
    """Parse a boolean toggle value from UI checkbox properties or expressions."""
    if val is None or val == "":
        return bool(default)
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    return str(val).strip().lower() in ("true", "1", "yes", "on")


def _ke_round_scalar(val, decimal=0):
    """Round a scalar using Lua `ke.math.round` half-up semantics."""
    dec = int(math.floor(abs(float(decimal))))
    scale = 10.0 ** dec
    res = math.floor(float(val) * scale + 0.5) / scale
    if abs(res) < 1e-12:
        return 0.0
    return res


def _fmt_num(val, decimals=None):
    """Format a scalar number cleanly without trailing zeros or negative zero."""
    v = float(val)
    if decimals is not None:
        v = _ke_round_scalar(v, decimals)
    if abs(v) < 1e-12:
        return "0"
    if v.is_integer():
        return str(int(round(v)))
    prec = decimals if decimals is not None else 6
    return f"{v:.{prec}f}".rstrip("0").rstrip(".")


def _fmt_list(values, decimals=None):
    """Format a list of numbers or strings into a comma-separated string."""
    parts = []
    for item in values:
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            parts.append(_fmt_num(item, decimals))
        else:
            parts.append(str(item))
    return ", ".join(parts)


def _split_csv(raw):
    """Split a comma-separated string into stripped non-empty tokens."""
    if raw is None:
        return []
    s = str(raw).strip()
    if not s:
        return []
    return [tok.strip() for tok in s.split(",") if tok.strip() != ""]


def _ke_getnumbers(raw_items, context=None):
    """
    Canonical port of `ke.math.getnumbers`: extract all numeric values from
    scalars, comma-separated expressions, coordinate pairs, or ASSDraw strings.
    """
    nums = []
    items = raw_items if isinstance(raw_items, (list, tuple)) else [raw_items]
    for item in items:
        if item is None:
            continue
        if isinstance(item, (int, float)) and not isinstance(item, bool):
            nums.append(float(item))
            continue
        s = str(item).strip()
        if not s:
            continue
        if "," in s and not _ASS_SHAPE_RE.search(s):
            for part in s.split(","):
                part = part.strip()
                if not part:
                    continue
                if _NUM_TOKEN_RE.fullmatch(part):
                    nums.append(float(part))
                else:
                    try:
                        from node_engine import _eval_num_expr
                        nums.append(float(_eval_num_expr(part, context, default=0.0)))
                    except Exception:
                        for m in _NUM_TOKEN_RE.findall(part):
                            nums.append(float(m))
        else:
            if _NUM_TOKEN_RE.fullmatch(s):
                nums.append(float(s))
            elif not _ASS_SHAPE_RE.search(s) and " " not in s and ";" not in s:
                try:
                    from node_engine import _eval_num_expr
                    nums.append(float(_eval_num_expr(s, context, default=0.0)))
                except Exception:
                    for m in _NUM_TOKEN_RE.findall(s):
                        nums.append(float(m))
            else:
                for m in _NUM_TOKEN_RE.findall(s):
                    nums.append(float(m))
    return nums


def _ke_topoints(raw_items, context=None):
    """Group extracted numeric values into a list of 2D (x, y) tuples."""
    nums = _ke_getnumbers(raw_items, context)
    pts = []
    for idx in range(0, len(nums) - 1, 2):
        pts.append((nums[idx], nums[idx + 1]))
    return pts


def _ke_sample_shape_y_ratio(shape_str, t):
    """
    Sample a point at normalized arc-length `t` along an ASSDraw path and return
    its normalized Y ratio `|y - min_y| / height` matching `ke.math.normalize`.
    """
    tokens = re.findall(r"[mlb]|-?\d+(?:\.\d+)?", str(shape_str), flags=re.IGNORECASE)
    if not tokens:
        return t

    segments = []
    cmd = ""
    idx = 0
    cur = (0.0, 0.0)
    n_tok = len(tokens)

    def read_pt(pos):
        return (float(tokens[pos]), float(tokens[pos + 1]))

    while idx < n_tok:
        tok = tokens[idx].lower()
        if tok in ("m", "l", "b"):
            cmd = tok
            idx += 1
            continue
        if cmd == "m" and idx + 1 < n_tok:
            cur = read_pt(idx)
            idx += 2
        elif cmd == "l" and idx + 1 < n_tok:
            nxt = read_pt(idx)
            segments.append(("l", cur, nxt))
            cur = nxt
            idx += 2
        elif cmd == "b" and idx + 5 < n_tok:
            p1 = read_pt(idx)
            p2 = read_pt(idx + 2)
            p3 = read_pt(idx + 4)
            segments.append(("b", cur, p1, p2, p3))
            cur = p3
            idx += 6
        else:
            idx += 1

    if not segments:
        return t

    polyline = []
    for seg in segments:
        if seg[0] == "l":
            _, p0, p1 = seg
            if not polyline:
                polyline.append(p0)
            polyline.append(p1)
        else:
            _, p0, p1, p2, p3 = seg
            steps = 16
            if not polyline:
                polyline.append(p0)
            for s in range(1, steps + 1):
                u = s / float(steps)
                om = 1.0 - u
                bx = (om ** 3) * p0[0] + 3 * (om ** 2) * u * p1[0] + 3 * om * (u ** 2) * p2[0] + (u ** 3) * p3[0]
                by = (om ** 3) * p0[1] + 3 * (om ** 2) * u * p1[1] + 3 * om * (u ** 2) * p2[1] + (u ** 3) * p3[1]
                polyline.append((bx, by))

    if len(polyline) < 2:
        return t

    ys = [p[1] for p in polyline]
    min_y, max_y = min(ys), max(ys)
    height = max_y - min_y
    if height <= EPSILON:
        return 0.0

    cum = [0.0]
    total = 0.0
    for j in range(1, len(polyline)):
        dx = polyline[j][0] - polyline[j - 1][0]
        dy = polyline[j][1] - polyline[j - 1][1]
        total += math.hypot(dx, dy)
        cum.append(total)

    if total <= EPSILON:
        return 0.0

    target = max(0.0, min(1.0, float(t))) * total
    py = polyline[-1][1]
    for j in range(1, len(cum)):
        if cum[j] >= target:
            seg_len = cum[j] - cum[j - 1]
            u = (target - cum[j - 1]) / seg_len if seg_len > EPSILON else 0.0
            py = polyline[j - 1][1] + u * (polyline[j][1] - polyline[j - 1][1])
            break

    return max(0.0, min(1.0, abs(py - min_y) / height))


def ke_i(counter, seq_mode="+,-", a=1.0, b=1.0, c=1.0):
    """Canonical port of `ke.math.i`: discrete numerical sequence generator."""
    i_val = float(counter)
    a_val = float(a)
    b_val = float(b)
    c_val = float(c)
    d_val = a_val - b_val + 1.0
    e_val = b_val - a_val + 1.0

    def xt(v):
        return float(math.ceil(i_val / v)) if abs(v) > EPSILON else 1.0

    mode = str(seq_mode).strip()
    if mode == "+,-":
        res = (-1.0) ** (xt(a_val) + 1.0)
    elif mode == "A,B":
        res = a_val + ((b_val - a_val) / 2.0) * (1.0 + (-1.0) ** xt(c_val))
    elif mode == "mxA":
        res = a_val * xt(b_val)
    elif mode == "A>B":
        if a_val <= b_val:
            res = ((xt(c_val) - 1.0) % e_val) + a_val if abs(e_val) > EPSILON else a_val
        else:
            res = -1.0 * (((xt(c_val) - 1.0) % d_val) - a_val) if abs(d_val) > EPSILON else a_val
    elif mode == "ABA":
        if a_val > b_val:
            span = d_val - 1.0
            if abs(span) <= EPSILON:
                res = a_val
            else:
                x = xt(span)
                res = b_val + d_val - ((span - span * x + i_val) * ((-1.0) ** (x + 1.0)) + (d_val + 1.0) * (1.0 + (-1.0) ** x) / 2.0)
        else:
            span = e_val - 1.0
            if abs(span) <= EPSILON:
                res = a_val
            else:
                x = xt(span)
                res = a_val + (span - span * x + i_val) * ((-1.0) ** (x + 1.0)) + (e_val + 1.0) * (1.0 + (-1.0) ** x) / 2.0 - 1.0
    elif mode == "ABB":
        f_term = float(math.floor(1.0 / i_val)) if abs(i_val) > EPSILON else 1.0
        res = a_val * f_term + b_val * (1.0 - f_term)
    elif mode == "ABC":
        f_term = float(math.floor((c_val * xt(c_val) - i_val + 1.0) / c_val)) if abs(c_val) > EPSILON else 1.0
        res = a_val * f_term + b_val * (1.0 - f_term)
    elif mode == "ACB":
        f_term = float(math.floor((c_val - c_val * xt(c_val) + i_val) / c_val)) if abs(c_val) > EPSILON else 0.0
        res = a_val * (1.0 - f_term) + b_val * f_term
    elif mode == "N,n":
        res = float(math.floor((i_val - 1.0) / a_val) + 1.0) if abs(a_val) > EPSILON else 1.0
    else:
        res = i_val

    return 0.0 if abs(res) < 1e-12 else res


def ke_clamp_scalar(num, min_val=0.0, max_val=1.0, cycle=False):
    """Canonical port of `ke.math.clamp` for a single scalar value."""
    c_min = min(float(min_val), float(max_val))
    c_max = max(float(min_val), float(max_val))
    v = float(num)
    if cycle:
        v_i = _ke_round_scalar(v * 10000.0, 0)
        mn_i = _ke_round_scalar(c_min * 10000.0, 0)
        mx_i = _ke_round_scalar(c_max * 10000.0, 0)
        counter_val = (v_i - mn_i) + 1.0
        bounced = ke_i(counter_val, "ABA", mn_i, mx_i, 1.0)
        return _ke_round_scalar(bounced / 10000.0, ROUND_NUM)
    if v < c_min:
        return c_min
    if v > c_max:
        return c_max
    return v


def ke_rand(num1=None, num2=None, step=1.0, sign=False, range_spec=None, context=None):
    """Canonical port of `ke.math.rand` supporting list choice, step, sign, and weighted sub-range."""
    def fxrand(a=None, b=None):
        offset = int(str(int(time.time()))[-3:])
        if a is None and b is None:
            return _ke_round_scalar(random.random(), 5)
        if b is None:
            if a == 0:
                return 0.0
            a, b = 1.0, float(a)
        r1 = int(_ke_round_scalar(min(a, b), 0))
        r2 = int(_ke_round_scalar(max(a, b), 0))
        if r2 <= r1:
            return float(r1)
        return float(r1 + (random.randint(r1, r2) + offset - 1) % (r2 - r1 + 1))

    s_num1 = "" if num1 is None else str(num1).strip()
    s_num2 = "" if num2 is None else str(num2).strip()

    if s_num1 and "," in s_num1 and s_num2 == "":
        choices = _split_csv(s_num1)
        if choices:
            picked = random.choice(choices)
            try:
                return _eval_num(picked, context, 0.0)
            except Exception:
                return picked

    if s_num1 == "":
        return fxrand()
    n1_val = _eval_num(s_num1, context, 0.0)
    if s_num2 == "":
        return fxrand(n1_val)
    n2_val = _eval_num(s_num2, context, 100.0)

    n1, n2 = min(n1_val, n2_val), max(n1_val, n2_val)
    st = float(step) if step is not None and float(step) > 0 else 1.0

    if range_spec is not None and str(range_spec).strip() != "":
        r_nums = _ke_getnumbers(range_spec, context)
        if len(r_nums) >= 2:
            rmin, rmax = r_nums[0], r_nums[1]
            pct = ke_clamp_scalar(r_nums[2] if len(r_nums) >= 3 else 100.0, 0.0, 100.0, False)
            lsize = (rmin - n1) if rmin > n1 else 0.0
            rsize = (n2 - rmax) if rmax < n2 else 0.0
            if ke_rand(0, 100, 1.0, False, None, context) <= pct or (lsize + rsize) <= 0.0:
                return ke_rand(rmin, rmax, st, sign, None, context)
            pick = ke_rand(0, lsize + rsize, st, False, None, context)
            if pick <= lsize:
                return ke_rand(n1, rmin - 1.0, st, sign, None, context)
            return ke_rand(rmax + 1.0, n2, st, sign, None, context)

    max_steps = (n2 - n1) / st
    result = n1 + fxrand(0.0, max_steps) * st
    if result > n2:
        result = n2
    if sign:
        result = result * ((-1.0) ** random.randint(1, 2))
    return result


def ke_normalize_scalar(t_val, accel=1.0, shape_str=""):
    """Canonical port of `ke.math.normalize` for a single scalar `t`."""
    t = abs(float(t_val))
    if not (0.0 <= t <= 1.0):
        int_digits = len(str(int(math.floor(t))))
        t = t / (10.0 ** int_digits)
    t = ke_clamp_scalar(t ** float(accel), 0.0, 1.0, False)
    if shape_str and _ASS_SHAPE_RE.search(str(shape_str)):
        t = _ke_sample_shape_y_ratio(shape_str, t)
    return t


def ke_ipol_scalar(values, t_val, accel=1.0, shape_str=""):
    """Canonical port of `ke.math.ipol` for a single `t` across a numeric list."""
    if not values:
        return 0.0
    if len(values) == 1:
        values = [0.0, values[0]]
    t = ke_normalize_scalar(t_val, accel, shape_str)
    if t <= 0.0:
        return values[0]
    n = len(values)
    seg = min(n - 1, max(1, int(math.ceil(t * (n - 1)))))
    ini = values[seg - 1]
    fin = values[seg]
    u = t * (n - 1) - (seg - 1)
    return _ke_round_scalar(ini + u * (fin - ini), ROUND_NUM)


def ke_quadratic(c1, c2, c3):
    """Canonical port of `ke.math.quadratic`."""
    c1, c2, c3 = float(c1), float(c2), float(c3)
    if abs(c1) < EPSILON:
        return [-c3 / c2] if abs(c2) >= EPSILON else []
    d = c2 * c2 - 4.0 * c1 * c3
    if d > EPSILON:
        sq = math.sqrt(d)
        return sorted([(-c2 - sq) / (2.0 * c1), (-c2 + sq) / (2.0 * c1)])
    if abs(d) <= EPSILON:
        return [(-c2) / (2.0 * c1)]
    return []


def ke_cubic(c1, c2, c3, c4):
    """Canonical port of `ke.math.cubic` (Cardano / trigonometric real roots)."""
    c1, c2, c3, c4 = float(c1), float(c2), float(c3), float(c4)
    if abs(c1) < EPSILON:
        return ke_quadratic(c2, c3, c4)

    def cbrt(x):
        return (x ** (1.0 / 3.0)) if x >= 0.0 else -((-x) ** (1.0 / 3.0))

    inv_a = 1.0 / c1
    b, c, d = c2 * inv_a, c3 * inv_a, c4 * inv_a
    offset = b / 3.0
    p = c - (b * b) / 3.0
    q = (2.0 * b * b * b) / 27.0 - (b * c) / 3.0 + d
    disc = (q * q) / 4.0 + (p * p * p) / 27.0
    roots = []
    if disc > EPSILON:
        s_d = math.sqrt(disc)
        u = cbrt(-q / 2.0 + s_d)
        v = cbrt(-q / 2.0 - s_d)
        roots.append((u + v) - offset)
    elif abs(disc) <= EPSILON:
        u = cbrt(-q / 2.0)
        roots.append(2.0 * u - offset)
        roots.append(-u - offset)
    else:
        denom = math.sqrt(max(EPSILON, -(p * p * p) / 27.0))
        arg = max(-1.0, min(1.0, (-q / 2.0) / denom))
        phi = math.acos(arg)
        r = 2.0 * math.sqrt(max(0.0, -p / 3.0))
        roots.append(r * math.cos(phi / 3.0) - offset)
        roots.append(r * math.cos((2.0 * math.pi + phi) / 3.0) - offset)
        roots.append(r * math.cos((4.0 * math.pi + phi) / 3.0) - offset)
    return sorted(roots)


def ke_equation(coeffs, reals_only=True):
    """Canonical port of `ke.math.equation` (Aberth-Ehrlich solver, ascending coefficients)."""
    cx = [float(x) for x in coeffs]
    while len(cx) > 1 and abs(cx[-1]) < EPSILON:
        cx.pop()
    n = len(cx) - 1
    if n < 1:
        return []

    def horner(c_list, z):
        p = complex(c_list[-1], 0.0)
        dp = complex(0.0, 0.0)
        for idx in range(len(c_list) - 2, -1, -1):
            dp = dp * z + p
            p = p * z + complex(c_list[idx], 0.0)
        return p, dp

    radius = 1.0
    lead = cx[-1]
    for idx in range(n):
        radius = max(radius, 1.0 + abs(cx[idx] / lead))

    roots = []
    for idx in range(n):
        ang = (2.0 * math.pi * idx) / n + 0.001 * (idx + 1)
        roots.append(complex(radius * math.cos(ang), radius * math.sin(ang)))

    for _ in range(50):
        done = True
        for idx in range(n):
            z = roots[idx]
            p, dp = horner(cx, z)
            if abs(dp) < 1e-18:
                continue
            newton = p / dp
            s_term = complex(0.0, 0.0)
            for j in range(n):
                if idx != j and abs(z - roots[j]) > 1e-18:
                    s_term += 1.0 / (z - roots[j])
            denom = 1.0 - newton * s_term
            if abs(denom) < 1e-18:
                continue
            corr = newton / denom
            roots[idx] = z - corr
            if abs(corr) > 1e-14:
                done = False
        if done:
            break

    roots.sort(key=lambda c: c.real)
    out = []
    for r in roots:
        if abs(r.imag) < EPSILON:
            out.append(_fmt_num(r.real, ROUND_MATRIX))
        elif not reals_only:
            sign_ch = "+" if r.imag >= 0 else "-"
            out.append(f"{_fmt_num(r.real, ROUND_MATRIX)}{sign_ch}{_fmt_num(abs(r.imag), ROUND_MATRIX)}i")
    return out


def ke_gauss(rows):
    """Canonical port of `ke.math.gauss`: Gaussian elimination with partial pivoting."""
    n = len(rows)
    if n == 0:
        return "singular system"
    mat = [list(map(float, r)) for r in rows]
    for r in mat:
        if len(r) < n + 1:
            return "singular system"

    for k in range(n):
        max_val = abs(mat[k][k])
        pivot_row = k
        for i_r in range(k + 1, n):
            if abs(mat[i_r][k]) > max_val:
                max_val = abs(mat[i_r][k])
                pivot_row = i_r
        if max_val < EPSILON:
            return "singular system"
        if pivot_row != k:
            mat[k], mat[pivot_row] = mat[pivot_row], mat[k]
        pivot = mat[k][k]
        for j in range(k, n + 1):
            mat[k][j] /= pivot
        for i_r in range(k + 1, n):
            factor = mat[i_r][k]
            for j in range(k, n + 1):
                mat[i_r][j] -= factor * mat[k][j]

    sol = [0.0] * n
    for i_r in range(n - 1, -1, -1):
        s_val = sum(mat[i_r][j] * sol[j] for j in range(i_r + 1, n))
        sol[i_r] = _ke_round_scalar(mat[i_r][n] - s_val, ROUND_MATRIX)
    return sol


class KeMatrix:
    """Canonical port of `ke.math.matrix` supporting n x n matrices and row vectors."""

    def __init__(self, data, is_row=False):
        self.is_row = bool(is_row)
        nums = list(data)
        if self.is_row:
            self.data = [_ke_round_scalar(v, ROUND_MATRIX) for v in nums]
            self.n = len(self.data)
        else:
            side = max(1, int(math.ceil(math.sqrt(len(nums))))) if nums else 1
            padded = [_ke_round_scalar(nums[i] if i < len(nums) else 0.0, ROUND_MATRIX) for i in range(side * side)]
            self.n = side
            self.data = [padded[r * side:(r + 1) * side] for r in range(side)]

    @classmethod
    def identity(cls, n):
        side = max(1, int(math.ceil(float(n))))
        vals = [1.0 if r == c else 0.0 for r in range(side) for c in range(side)]
        return cls(vals, is_row=False)

    def to_array(self):
        if self.is_row:
            return list(self.data)
        return [v for row in self.data for v in row]

    def format_str(self):
        if self.is_row:
            return _fmt_list(self.data, ROUND_MATRIX)
        return "; ".join(_fmt_list(row, ROUND_MATRIX) for row in self.data)

    def determinant(self):
        if self.is_row:
            return 0.0
        n = self.n
        if n == 1:
            return self.data[0][0]
        if n == 2:
            return self.data[0][0] * self.data[1][1] - self.data[0][1] * self.data[1][0]
        det = 0.0
        sign = 1.0
        for col in range(n):
            elem = self.data[0][col]
            sub = [self.data[r][c] for r in range(1, n) for c in range(n) if c != col]
            det += sign * elem * KeMatrix(sub).determinant()
            sign = -sign
        return _ke_round_scalar(det, ROUND_MATRIX)

    def inverse(self):
        det = self.determinant()
        if abs(det) < EPSILON or self.is_row:
            return None
        n = self.n
        cof = [[0.0] * n for _ in range(n)]
        for i_r in range(n):
            for j_c in range(n):
                if n == 1:
                    c_val = 1.0
                else:
                    sub = [self.data[r][c] for r in range(n) if r != i_r for c in range(n) if c != j_c]
                    c_val = KeMatrix(sub).determinant()
                if (i_r + j_c) % 2 == 1:
                    c_val = -c_val
                cof[i_r][j_c] = c_val
        inv_flat = [cof[j_c][i_r] / det for i_r in range(n) for j_c in range(n)]
        return KeMatrix(inv_flat, is_row=False)

    def __add__(self, other):
        if isinstance(other, (int, float)):
            if self.is_row:
                return KeMatrix([v + other for v in self.data], is_row=True)
            return KeMatrix([v + other for row in self.data for v in row], is_row=False)
        if self.is_row and other.is_row:
            n = min(self.n, other.n)
            return KeMatrix([self.data[i] + other.data[i] for i in range(n)], is_row=True)
        n = min(self.n, other.n)
        return KeMatrix([self.data[r][c] + other.data[r][c] for r in range(n) for c in range(n)], is_row=False)

    def __sub__(self, other):
        if isinstance(other, (int, float)):
            if self.is_row:
                return KeMatrix([v - other for v in self.data], is_row=True)
            return KeMatrix([v - other for row in self.data for v in row], is_row=False)
        if self.is_row and other.is_row:
            n = min(self.n, other.n)
            return KeMatrix([self.data[i] - other.data[i] for i in range(n)], is_row=True)
        n = min(self.n, other.n)
        return KeMatrix([self.data[r][c] - other.data[r][c] for r in range(n) for c in range(n)], is_row=False)

    def __neg__(self):
        if self.is_row:
            return KeMatrix([-v for v in self.data], is_row=True)
        return KeMatrix([-v for row in self.data for v in row], is_row=False)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            if self.is_row:
                return KeMatrix([v * other for v in self.data], is_row=True)
            return KeMatrix([v * other for row in self.data for v in row], is_row=False)
        if self.is_row and not other.is_row:
            n = other.n
            res = [sum((self.data[k] if k < self.n else 0.0) * other.data[k][j] for k in range(n)) for j in range(n)]
            return KeMatrix(res, is_row=True)
        if not self.is_row and other.is_row:
            n = self.n
            res = [sum(self.data[i][k] * (other.data[k] if k < other.n else 0.0) for k in range(n)) for i in range(n)]
            return KeMatrix(res, is_row=True)
        n = min(self.n, other.n)
        res = [sum(self.data[i][k] * other.data[k][j] for k in range(n)) for i in range(n) for j in range(n)]
        return KeMatrix(res, is_row=False)

    def equals(self, other):
        if self.is_row != other.is_row or self.n != other.n:
            return False
        a_arr, b_arr = self.to_array(), other.to_array()
        return all(abs(x - y) < EPSILON for x, y in zip(a_arr, b_arr))

    def rotate_xyz(self, ax, ay, az):
        sx, sy, sz = math.sin(math.radians(ax)), math.sin(math.radians(ay)), math.sin(math.radians(az))
        cx, cy, cz = math.cos(math.radians(ax)), math.cos(math.radians(ay)), math.cos(math.radians(az))
        rot = KeMatrix([
            cy * cz, -cx * sz + sx * sy * cz, sx * sz + cx * sy * cz,
            cy * sz, cx * cz + sx * sy * sz, -sx * cz + cx * sy * sz,
            -sy, sx * cy, cx * cy
        ], is_row=False)
        return self * rot


def eval_math_node(context=None, node_id=None, **kwargs):
    """
    Canonical execution dispatcher for `Basics/Math` reflecting `ke.math` (`newkara_library.lua`)
    plus expandable multi-input arithmetic operations under `basic`.

    Categories and operations:
        - `basic`: `add`, `sub`, `mul`, `div`, `mod`, `pow`, `min`, `max`, `avg`
        - `numeric`: `round`, `clamp`, `rand`, `factk`, `to16`, `equality`, `between`
        - `sequence`: `i`, `count`, `normalize`, `ipol`
        - `geometry`: `angle`, `polar`, `distance`, `intersect`, `circle`, `rotate`
        - `algebra`: `quadratic`, `cubic`, `resolve`, `equation`, `evaluate`, `gauss`, `matrix`
        - `data`: `getpair`, `getnumbers`, `format`
    """
    ctx = context if isinstance(context, dict) else {}
    category = str(kwargs.get("category", "basic")).strip().lower()
    operation = str(kwargs.get("operation", "add" if category == "basic" else "round")).strip().lower()

    def get_num(key, default=0.0):
        return _eval_num(kwargs.get(key), ctx, default)

    # ------------------------------------------------------------------
    # Category 0: basic (expandable multi-input arithmetic: In1..InN)
    # ------------------------------------------------------------------
    if category == "basic":
        indexed_inputs = {}
        for k, v in kwargs.items():
            m = re.match(r"^(?:in|input)[_\s]*(\d+)$", str(k).strip(), re.IGNORECASE)
            if m:
                idx = int(m.group(1))
                # Prefer non-empty values if both lowercase and titlecase keys exist
                if idx not in indexed_inputs or (v is not None and str(v).strip() != ""):
                    indexed_inputs[idx] = v

        if not indexed_inputs:
            if "a" in kwargs or "A" in kwargs:
                indexed_inputs[1] = kwargs.get("a", kwargs.get("A"))
            if "b" in kwargs or "B" in kwargs:
                indexed_inputs[2] = kwargs.get("b", kwargs.get("B"))

        vals = []
        for idx in sorted(indexed_inputs.keys()):
            raw_v = indexed_inputs[idx]
            if raw_v is not None and str(raw_v).strip() != "":
                vals.append(_eval_num(raw_v, ctx, 0.0))

        if not vals:
            return 0.0

        if operation == "add":
            return sum(vals)
        if operation == "sub":
            res = vals[0]
            for v in vals[1:]:
                res -= v
            return res
        if operation == "mul":
            res = vals[0]
            for v in vals[1:]:
                res *= v
            return res
        if operation == "div":
            res = vals[0]
            for v in vals[1:]:
                if abs(v) < 1e-12:
                    return 0.0
                res /= v
            return res
        if operation == "mod":
            res = vals[0]
            for v in vals[1:]:
                if abs(v) < 1e-12:
                    return 0.0
                res %= v
            return res
        if operation == "pow":
            res = vals[0]
            for v in vals[1:]:
                try:
                    out_p = res ** v
                    if isinstance(out_p, complex) or not math.isfinite(out_p):
                        return 0.0
                    res = float(out_p)
                except Exception:
                    return 0.0
            return res
        if operation == "min":
            return min(vals)
        if operation == "max":
            return max(vals)
        if operation == "avg":
            return sum(vals) / float(len(vals))
        return 0.0

    # ------------------------------------------------------------------
    # Category 1: numeric
    # ------------------------------------------------------------------
    if category == "numeric":
        if operation == "round":
            raw = kwargs.get("value", "0")
            dec = get_num("decimal", 0.0)
            s_raw = str(raw).strip() if raw is not None else "0"
            if "," in s_raw and not re.match(r"^[+-]?\d+,\d+$", s_raw):
                vals = [_ke_round_scalar(_eval_num(tok, ctx, 0.0), dec) for tok in _split_csv(s_raw)]
                return _fmt_list(vals, int(math.floor(abs(dec))))
            return _ke_round_scalar(_eval_num(raw, ctx, 0.0), dec)

        if operation == "clamp":
            raw = kwargs.get("num", "0.5")
            mn = get_num("min_val", 0.0)
            mx = get_num("max_val", 1.0)
            cycle = _ke_bool(kwargs.get("cycle", False), False)
            s_raw = str(raw).strip() if raw is not None else "0.5"
            if "," in s_raw and not re.match(r"^[+-]?\d+,\d+$", s_raw):
                vals = [ke_clamp_scalar(_eval_num(tok, ctx, 0.5), mn, mx, cycle) for tok in _split_csv(s_raw)]
                return _fmt_list(vals, ROUND_NUM if cycle else None)
            return ke_clamp_scalar(_eval_num(raw, ctx, 0.5), mn, mx, cycle)

        if operation == "rand":
            num1 = kwargs.get("num1", None)
            num2 = kwargs.get("num2", None)
            step = get_num("step", 1.0)
            sign = _ke_bool(kwargs.get("sign", False), False)
            range_spec = kwargs.get("range", "")
            return ke_rand(num1, num2, step, sign, range_spec, ctx)

        if operation == "factk":
            n = int(abs(math.ceil(get_num("n", 0.0))))
            return math.factorial(min(n, 170))

        if operation == "to16":
            raw = kwargs.get("num", "0")
            s_raw = str(raw).strip() if raw is not None else "0"
            if "," in s_raw and not re.match(r"^[+-]?\d+,\d+$", s_raw):
                hexes = [f"{int(_ke_round_scalar(_eval_num(tok, ctx, 0.0), 0)):X}" for tok in _split_csv(s_raw)]
                return ", ".join(hexes)
            return f"{int(_ke_round_scalar(_eval_num(raw, ctx, 0.0), 0)):X}"

        if operation == "equality":
            n1 = get_num("n1", 0.0)
            n2 = get_num("n2", 0.0)
            tol = get_num("tolerance", 5.0)
            return abs(n1 - n2) < (0.1 ** tol)

        if operation == "between":
            val = get_num("num", 0.0)
            n1 = get_num("n1", 0.0)
            n2 = get_num("n2", 10.0)
            lo, hi = min(n1, n2), max(n1, n2)
            return lo <= val <= hi

    # ------------------------------------------------------------------
    # Category 2: sequence
    # ------------------------------------------------------------------
    elif category == "sequence":
        if operation == "i":
            counter = get_num("counter", 1.0)
            seq_mode = str(kwargs.get("seq_mode", "+,-")).strip()
            a = get_num("a", 1.0)
            b = get_num("b", 1.0)
            c = get_num("c", 1.0)
            return ke_i(counter, seq_mode, a, b, c)

        if operation == "count":
            init_raw = kwargs.get("init", "")
            step = get_num("step", 1.0)
            seq_mode = str(kwargs.get("seq_mode", "none")).strip()
            a = get_num("a", 1.0)
            b = get_num("b", 1.0)
            c = get_num("c", 1.0)
            counters = ctx.setdefault("_math_counters", {})
            c_key = str(node_id) if node_id is not None else "default"
            if c_key not in counters:
                if init_raw is not None and str(init_raw).strip() != "":
                    counters[c_key] = _eval_num(init_raw, ctx, 1.0) - step
                else:
                    counters[c_key] = 0.0
            counters[c_key] = counters[c_key] + step
            cur = counters[c_key]
            if seq_mode and seq_mode.lower() != "none":
                return ke_i(cur, seq_mode, a, b, c)
            return cur

        if operation == "normalize":
            raw_t = kwargs.get("t", "0.5")
            accel = get_num("accel", 1.0)
            shape_str = str(kwargs.get("shape", "") or "").strip()
            s_t = str(raw_t).strip() if raw_t is not None else "0.5"
            if "," in s_t and not re.match(r"^[+-]?\d+,\d+$", s_t):
                t_list = [_eval_num(tok, ctx, 0.0) for tok in _split_csv(s_t)]
                res_list = []
                last = 0.0
                for ti in t_list:
                    denom = (1.0 - last) if abs(1.0 - last) > EPSILON else 1.0
                    rel = (ti - last) / denom
                    last = ti
                    res_list.append(ke_normalize_scalar(rel, accel, shape_str))
                return _fmt_list(res_list, ROUND_NUM)
            return ke_normalize_scalar(_eval_num(raw_t, ctx, 0.5), accel, shape_str)

        if operation == "ipol":
            raw_vals = kwargs.get("values", "0, 100")
            vals = _ke_getnumbers(raw_vals, ctx)
            t_val = get_num("t", 0.5)
            accel = get_num("accel", 1.0)
            shape_str = str(kwargs.get("shape", "") or "").strip()
            raw_size = kwargs.get("size", "")
            if raw_size is not None and str(raw_size).strip() != "":
                sz = int(_eval_num(raw_size, ctx, 0.0))
                if sz >= 2:
                    batch = [ke_ipol_scalar(vals, idx / float(sz - 1), accel, shape_str) for idx in range(sz)]
                    return _fmt_list(batch, ROUND_NUM)
                if sz == 1:
                    return ke_ipol_scalar(vals, 0.0, accel, shape_str)
            return ke_ipol_scalar(vals, t_val, accel, shape_str)

    # ------------------------------------------------------------------
    # Category 3: geometry
    # ------------------------------------------------------------------
    elif category == "geometry":
        if operation == "angle":
            nums = _ke_getnumbers([kwargs.get("p1", ""), kwargs.get("p2", ""), kwargs.get("p3", "")], ctx)
            if len(nums) < 2:
                return 0.0
            if len(nums) < 4:
                x1, y1, x2, y2 = 0.0, 0.0, nums[0], nums[1]
                x3 = y3 = None
            else:
                x1, y1, x2, y2 = nums[0], nums[1], nums[2], nums[3]
                x3 = nums[4] if len(nums) >= 6 else None
                y3 = nums[5] if len(nums) >= 6 else None
            a1 = math.degrees(math.atan2(y1 - y2, x2 - x1))
            if a1 < 0.0:
                a1 += 360.0
            if x3 is not None and y3 is not None:
                a2 = math.degrees(math.atan2(y2 - y3, x3 - x2))
                if a2 < 0.0:
                    a2 += 360.0
                ang = 180.0 - a1 + a2
            else:
                ang = a1
            if ang < 0.0:
                ang += 360.0
            elif ang > 360.0:
                ang -= 360.0
            return _ke_round_scalar(ang, ROUND_NUM)

        if operation == "polar":
            ang = get_num("angle", 0.0)
            rad = get_num("radius", 0.0)
            get_mode = str(kwargs.get("get", "xy")).strip().lower()
            px = _ke_round_scalar(rad * math.cos(math.radians(ang)), ROUND_NUM)
            py = _ke_round_scalar(-rad * math.sin(math.radians(ang)), ROUND_NUM)
            if get_mode == "y":
                return (py, py)
            return (px, py)

        if operation == "distance":
            raw_list = [kwargs.get("p1", ""), kwargs.get("p2", "")]
            pts = _ke_topoints(raw_list, ctx)
            if len(pts) > 2:
                total = 0.0
                for idx in range(len(pts) - 1):
                    dx = pts[idx][0] - pts[idx + 1][0]
                    dy = pts[idx][1] - pts[idx + 1][1]
                    total += _ke_round_scalar(math.hypot(dx, dy), ROUND_NUM)
                return _ke_round_scalar(total, ROUND_NUM)
            nums = _ke_getnumbers(raw_list, ctx)
            if len(nums) < 2:
                return 0.0
            x1, y1 = nums[0], nums[1]
            x2 = nums[2] if len(nums) >= 3 else 0.0
            y2 = nums[3] if len(nums) >= 4 else 0.0
            return _ke_round_scalar(math.hypot(x1 - x2, y1 - y2), ROUND_NUM)

        if operation == "intersect":
            nums = _ke_getnumbers([kwargs.get("s1", ""), kwargs.get("s2", "")], ctx)
            if len(nums) < 8:
                return ("parallels", "", "")
            x1, y1, x2, y2, x3, y3, x4, y4 = nums[:8]
            if (x1 == x3 and y1 == y3) or (x1 == x4 and y1 == y4):
                return (_ke_round_scalar(x1, ROUND_NUM), _ke_round_scalar(y1, ROUND_NUM), 0.0)
            if (x2 == x3 and y2 == y3) or (x2 == x4 and y2 == y4):
                return (_ke_round_scalar(x2, ROUND_NUM), _ke_round_scalar(y2, ROUND_NUM), 1.0)
            denom = (x2 - x1) * (y3 - y4) - (x3 - x4) * (y2 - y1)
            if abs(denom) < 1e-12:
                return ("parallels", "", "")
            t = ((x3 - x1) * (y3 - y4) - (x3 - x4) * (y3 - y1)) / denom
            ix = _ke_round_scalar(x1 + t * (x2 - x1), ROUND_NUM)
            iy = _ke_round_scalar(y1 + t * (y2 - y1), ROUND_NUM)
            return (ix, iy, _ke_round_scalar(t, ROUND_NUM))

        if operation == "circle":
            pts = _ke_topoints([kwargs.get("p1", ""), kwargs.get("p2", ""), kwargs.get("p3", "")], ctx)
            if len(pts) < 3:
                return ("collineals", "", "")
            (x1, y1), (x2, y2), (x3, y3) = pts[0], pts[1], pts[2]
            det = x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)
            if abs(det) < EPSILON:
                return ("collineals", "", "")
            d1 = x1 * x1 + y1 * y1
            d2 = x2 * x2 + y2 * y2
            d3 = x3 * x3 + y3 * y3
            ux = (d1 * (y2 - y3) + d2 * (y3 - y1) + d3 * (y1 - y2)) / (2.0 * det)
            uy = (d1 * (x3 - x2) + d2 * (x1 - x3) + d3 * (x2 - x1)) / (2.0 * det)
            rad = math.hypot(ux - x1, uy - y1)
            return (_ke_round_scalar(ux, ROUND_NUM), _ke_round_scalar(uy, ROUND_NUM), _ke_round_scalar(rad, ROUND_NUM))

        if operation == "rotate":
            p_raw = str(kwargs.get("p", "") or "").strip()
            ang_rad = math.radians(get_num("angle", 0.0))
            axis = str(kwargs.get("axis", "z")).strip().lower()
            ca, sa = math.cos(ang_rad), math.sin(ang_rad)

            def rot_pt(x, y, z):
                if axis == "x":
                    return x, ca * y - sa * z, sa * y + ca * z
                if axis == "y":
                    return ca * x + sa * z, y, ca * z - sa * x
                return ca * x - sa * y, sa * x + ca * y, z

            if _ASS_SHAPE_RE.search(p_raw):
                def _sub_pair(m):
                    rx, ry, _ = rot_pt(float(m.group(1)), float(m.group(2)), 0.0)
                    return f"{_fmt_num(rx, ROUND_NUM)} {_fmt_num(ry, ROUND_NUM)}"
                rotated = _ASS_PAIR_RE.sub(_sub_pair, p_raw)
                return (rotated, "", "", "")

            nums = _ke_getnumbers(p_raw, ctx)
            x = nums[0] if len(nums) >= 1 else 0.0
            y = nums[1] if len(nums) >= 2 else 0.0
            z = nums[2] if len(nums) >= 3 else 0.0
            rx, ry, rz = rot_pt(x, y, z)
            rx_r = _ke_round_scalar(rx, ROUND_NUM)
            ry_r = _ke_round_scalar(ry, ROUND_NUM)
            rz_r = _ke_round_scalar(rz, ROUND_NUM)
            return (_fmt_list([rx_r, ry_r, rz_r], ROUND_NUM), rx_r, ry_r, rz_r)

    # ------------------------------------------------------------------
    # Category 4: algebra
    # ------------------------------------------------------------------
    elif category == "algebra":
        if operation == "quadratic":
            roots = ke_quadratic(get_num("c1", 1.0), get_num("c2", 0.0), get_num("c3", 0.0))
            return _fmt_list(roots, ROUND_MATRIX)

        if operation == "cubic":
            roots = ke_cubic(get_num("c1", 1.0), get_num("c2", 0.0), get_num("c3", 0.0), get_num("c4", 0.0))
            return _fmt_list(roots, ROUND_MATRIX)

        if operation == "resolve":
            coeffs = _ke_getnumbers(kwargs.get("coefficients", ""), ctx)
            while coeffs and abs(coeffs[0]) < EPSILON:
                coeffs.pop(0)
            if len(coeffs) <= 1:
                return ""
            if len(coeffs) >= 4:
                roots = ke_cubic(coeffs[0], coeffs[1], coeffs[2], coeffs[3])
            elif len(coeffs) == 3:
                roots = ke_quadratic(coeffs[0], coeffs[1], coeffs[2])
            else:
                roots = [-coeffs[1] / coeffs[0]]
            return _fmt_list(roots, ROUND_MATRIX)

        if operation == "equation":
            coeffs = _ke_getnumbers(kwargs.get("coefficients", ""), ctx)
            reals = _ke_bool(kwargs.get("reals", True), True)
            return ", ".join(ke_equation(coeffs, reals_only=reals))

        if operation == "evaluate":
            coeffs = _ke_getnumbers(kwargs.get("coefficients", ""), ctx)
            t_val = get_num("t", 0.0)
            if not coeffs:
                return 0.0
            res = coeffs[-1]
            for idx in range(len(coeffs) - 2, -1, -1):
                res = res * t_val + coeffs[idx]
            return res

        if operation == "gauss":
            raw_mat = str(kwargs.get("matrix", "") or "").strip()
            rows = [_ke_getnumbers(r_str, ctx) for r_str in raw_mat.split(";") if r_str.strip()]
            sol = ke_gauss(rows)
            if isinstance(sol, str):
                return sol
            return _fmt_list(sol, ROUND_MATRIX)

        if operation == "matrix":
            op = str(kwargs.get("matrix_op", "mul")).strip().lower()
            is_row = _ke_bool(kwargs.get("is_row", False), False)
            nums_a = _ke_getnumbers(kwargs.get("matrix_a", "1, 0, 0, 1"), ctx)
            raw_b = str(kwargs.get("matrix_b", "") or "").strip()
            nums_b = _ke_getnumbers(raw_b, ctx) if raw_b else []

            if op == "identity":
                size_n = nums_a[0] if nums_a else 3
                m = KeMatrix.identity(size_n)
                return (m.format_str(), m.determinant())

            m_a = KeMatrix(nums_a, is_row=is_row)

            if op == "det":
                d = m_a.determinant()
                return (d, d)
            if op == "toarray":
                return (_fmt_list(m_a.to_array(), ROUND_MATRIX), m_a.determinant())
            if op == "neg":
                res_m = -m_a
                return (res_m.format_str(), res_m.determinant())
            if op == "inverse":
                inv_m = m_a.inverse()
                if inv_m is None:
                    return ("singular matrix", 0.0)
                return (inv_m.format_str(), inv_m.determinant())
            if op == "rotate":
                ang_nums = _ke_getnumbers(kwargs.get("angles", "0, 0, 0"), ctx)
                ax = ang_nums[0] if len(ang_nums) >= 1 else 0.0
                ay = ang_nums[1] if len(ang_nums) >= 2 else 0.0
                az = ang_nums[2] if len(ang_nums) >= 3 else 0.0
                res_m = m_a.rotate_xyz(ax, ay, az)
                return (res_m.format_str(), res_m.determinant())

            # Binary operations: mul, add, sub, eq
            if len(nums_b) == 1 and op in ("mul", "add", "sub"):
                operand = nums_b[0]
            else:
                b_is_row = is_row if op != "mul" else (len(nums_b) == m_a.n and not m_a.is_row and ";" not in raw_b and len(nums_b) != m_a.n * m_a.n)
                operand = KeMatrix(nums_b, is_row=b_is_row)

            if op == "add":
                res_m = m_a + operand
                return (res_m.format_str(), res_m.determinant())
            if op == "sub":
                res_m = m_a - operand
                return (res_m.format_str(), res_m.determinant())
            if op == "eq":
                eq_res = m_a.equals(operand) if isinstance(operand, KeMatrix) else False
                return (eq_res, m_a.determinant())
            res_m = m_a * operand
            return (res_m.format_str(), res_m.determinant())

    # ------------------------------------------------------------------
    # Category 5: data
    # ------------------------------------------------------------------
    elif category == "data":
        if operation == "getpair":
            nums = _ke_getnumbers(kwargs.get("val", ""), ctx)
            defx = get_num("defx", 0.0)
            defy = get_num("defy", 0.0)
            vx = nums[0] if len(nums) >= 1 else defx
            if len(nums) >= 2:
                vy = nums[1]
            elif kwargs.get("defy") is not None and str(kwargs.get("defy")).strip() != "":
                vy = defy
            elif len(nums) >= 1:
                vy = nums[0]
            else:
                vy = 0.0
            return (vx, vy)

        if operation == "getnumbers":
            nums = _ke_getnumbers(kwargs.get("val", ""), ctx)
            return _fmt_list(nums)

        if operation == "format":
            fmt_str = str(kwargs.get("fmt", "%s") or "%s")
            raw_vals = kwargs.get("values", "1")
            val_tokens = _split_csv(raw_vals) if (raw_vals is not None and str(raw_vals).strip() != "") else ["1"]
            specs = _FMT_SPEC_RE.findall(fmt_str)
            if not specs:
                return fmt_str
            args = []
            for idx, spec in enumerate(specs):
                tok = val_tokens[idx % len(val_tokens)]
                conv = spec[-1]
                if conv in ("d", "i", "u", "o", "x", "X", "c"):
                    args.append(int(_ke_round_scalar(_eval_num(tok, ctx, 0.0), 0)))
                elif conv in ("e", "E", "f", "g", "G", "a", "A"):
                    args.append(_eval_num(tok, ctx, 0.0))
                else:
                    args.append(tok)
            try:
                return fmt_str % tuple(args)
            except Exception:
                return fmt_str

    return 0.0


NODE_REGISTRY["Basics/Math"] = eval_math_node


import random
def _resolve_bounds(min_val=None, max_val=None, default_min=0.0, default_max=100.0, context=None):
    """
    Normalise minimum and maximum numeric boundaries from parameters or context expressions.

    Args:
        min_val (float | str | None): Minimum boundary value or formula expression.
        max_val (float | str | None): Maximum boundary value or formula expression.
        default_min (float): Default lower bound if unspecified.
        default_max (float): Default upper bound if unspecified.
        context (dict | None): Context dictionary for expression evaluation.

    Returns:
        tuple[float, float]: Evaluated (minimum, maximum) numeric boundary pair.
    """
    if min_val is None and max_val is None:
        return default_min, default_max
    if max_val is None:
        val = _eval_num(min_val, context, default_max)
        return 0.0, float(val)
    mn = _eval_num(min_val, context, default_min)
    mx = _eval_num(max_val, context, default_max)
    return float(mn), float(mx)

def _pyxis_random_r(min_val=None, max_val=None, step=1.0, context=None):
    """
    Generate an integer or floating-point pseudo-random value within specified boundaries.

    If boundaries and step are integer values with step=1.0, utilises `random.randint`.
    Otherwise, computes stepped quantisation or continuous uniform random float.

    Args:
        min_val (float | str | None): Lower limit.
        max_val (float | str | None): Upper limit.
        step (float | str): Discrete quantisation step.
        context (dict | None): Context dictionary.

    Returns:
        int | float: Generated pseudo-random number.
    """
    mn, mx = _resolve_bounds(min_val, max_val, 0.0, 100.0, context)
    st = _eval_num(step, context, 1.0)
    if st == 0.0: st = 1.0
    
    low = min(mn, mx)
    high = max(mn, mx)
    if st == 1.0 and low.is_integer() and high.is_integer():
        return random.randint(int(low), int(high))
    
    steps_count = int((high - low) / abs(st)) if abs(st) > 0 else 0
    if steps_count > 0:
        rnd_step = random.randint(0, steps_count)
        val = low + rnd_step * abs(st)
        val = min(high, val)
        if isinstance(val, float) and val.is_integer():
            return int(val)
        return round(val, 4)
    else:
        val = random.uniform(low, high)
        if isinstance(val, float) and val.is_integer():
            return int(val)
        return round(val, 4)

def _pyxis_random_rs(min_val=None, max_val=None, step=1.0, context=None):
    """
    Generate a signed pseudo-random value with random polarity (positive or negative).

    Args:
        min_val (float | str | None): Lower magnitude limit.
        max_val (float | str | None): Upper magnitude limit.
        step (float | str): Quantisation step.
        context (dict | None): Context dictionary.

    Returns:
        int | float: Magnitude signed with +1 or -1.
    """
    val = _pyxis_random_r(min_val, max_val, step, context)
    sign = 1 if random.random() >= 0.5 else -1
    res = val * sign
    if isinstance(res, float) and res.is_integer():
        return int(res)
    return res

def _pyxis_random_rr(context=None, min_val=None, max_val=None, step=1.0):
    """
    Generate a pseudo-random value scaled proportionally to script horizontal resolution.

    Scales the base random number by `context['rx'] / 1280.0` (standard 720p base).

    Args:
        context (dict | None): Context containing `rx` resolution.
        min_val (float | str | None): Lower limit.
        max_val (float | str | None): Upper limit.
        step (float | str): Step size.

    Returns:
        int | float: Resolution-proportional random value.
    """
    val = _pyxis_random_r(min_val, max_val, step, context)
    ctx = context or {}
    rx = _eval_num(ctx.get("rx", 1280), ctx, 1280.0)
    ratio = rx / 1280.0
    res = round(val * ratio, 4)
    if isinstance(res, float) and res.is_integer():
        return int(res)
    return res

def _pyxis_random_rd(min_val=None, max_val=None, step=0.1, context=None):
    """
    Generate a decimal pseudo-random value rounded to tenths (0.1 precision).

    Args:
        min_val (float | str | None): Lower limit.
        max_val (float | str | None): Upper limit.
        step (float | str): Decimal step.
        context (dict | None): Context dictionary.

    Returns:
        int | float: Value rounded to 1 decimal place.
    """
    mn, mx = _resolve_bounds(min_val, max_val, 0.0, 100.0, context)
    st = _eval_num(step, context, 0.1) * 10.0
    val = float(_pyxis_random_r(mn * 10.0, mx * 10.0, st, context))
    res = round(val / 10.0, 1)
    return int(res) if res.is_integer() else res

def _pyxis_random_rc(min_val=None, max_val=None, step=0.01, context=None):
    """
    Generate a centesimal pseudo-random value rounded to hundredths (0.01 precision).

    Args:
        min_val (float | str | None): Lower limit.
        max_val (float | str | None): Upper limit.
        step (float | str): Centesimal step.
        context (dict | None): Context dictionary.

    Returns:
        int | float: Value rounded to 2 decimal places.
    """
    mn, mx = _resolve_bounds(min_val, max_val, 0.0, 100.0, context)
    st = _eval_num(step, context, 0.01) * 100.0
    val = float(_pyxis_random_r(mn * 100.0, mx * 100.0, st, context))
    res = round(val / 100.0, 2)
    return int(res) if res.is_integer() else res

def _pyxis_random_rm(min_val=None, max_val=None, step=0.001, context=None):
    """
    Generate a millesimal pseudo-random value rounded to thousandths (0.001 precision).

    Args:
        min_val (float | str | None): Lower limit.
        max_val (float | str | None): Upper limit.
        step (float | str): Millesimal step.
        context (dict | None): Context dictionary.

    Returns:
        int | float: Value rounded to 3 decimal places.
    """
    mn, mx = _resolve_bounds(min_val, max_val, 0.0, 100.0, context)
    st = _eval_num(step, context, 0.001) * 1000.0
    val = float(_pyxis_random_r(mn * 1000.0, mx * 1000.0, st, context))
    res = round(val / 1000.0, 3)
    return int(res) if res.is_integer() else res

def _pyxis_random_rds(min_val=None, max_val=None, step=0.1, context=None):
    """
    Generate a signed decimal pseudo-random value rounded to tenths (+/- 0.1 precision).

    Args:
        min_val (float | str | None): Lower limit.
        max_val (float | str | None): Upper limit.
        step (float | str): Step size.
        context (dict | None): Context dictionary.

    Returns:
        int | float: Signed value rounded to 1 decimal place.
    """
    sign = 1 if random.random() >= 0.5 else -1
    res = round(float(_pyxis_random_rd(min_val, max_val, step, context)) * sign, 1)
    return int(res) if res.is_integer() else res

def _pyxis_random_rcs(min_val=None, max_val=None, step=0.01, context=None):
    """
    Generate a signed centesimal pseudo-random value rounded to hundredths (+/- 0.01 precision).

    Args:
        min_val (float | str | None): Lower limit.
        max_val (float | str | None): Upper limit.
        step (float | str): Step size.
        context (dict | None): Context dictionary.

    Returns:
        int | float: Signed value rounded to 2 decimal places.
    """
    sign = 1 if random.random() >= 0.5 else -1
    res = round(float(_pyxis_random_rc(min_val, max_val, step, context)) * sign, 2)
    return int(res) if res.is_integer() else res

def _pyxis_random_rms(min_val=None, max_val=None, step=0.001, context=None):
    """
    Generate a signed millesimal pseudo-random value rounded to thousandths (+/- 0.001 precision).

    Args:
        min_val (float | str | None): Lower limit.
        max_val (float | str | None): Upper limit.
        step (float | str): Step size.
        context (dict | None): Context dictionary.

    Returns:
        int | float: Signed value rounded to 3 decimal places.
    """
    sign = 1 if random.random() >= 0.5 else -1
    res = round(float(_pyxis_random_rm(min_val, max_val, step, context)) * sign, 3)
    return int(res) if res.is_integer() else res

def _pyxis_random_re(options_str="", context=None):
    """
    Pick a pseudo-random option from a comma-separated list of candidate elements.

    Args:
        options_str (str): Comma-separated choices (e.g. "red, green, blue").
        context (dict | None): Context dictionary.

    Returns:
        str: Selected item trimmed of whitespace.
    """
    s = str(options_str or "").strip()
    if not s: return ""
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if not parts: return s
    return random.choice(parts)

def _pyxis_random_rfake(context=None, min_val=0.0, max_val=100.0, counter=None):
    """
    Compute a deterministic, seedless pseudo-random value derived from an iteration counter.

    Utilises a Linear Congruential Generator hash formula: `(ctr * 9301 + 49297) % 233280`.

    Args:
        context (dict | None): Context providing fallback counter `i` or `j`.
        min_val (float | str): Minimum value.
        max_val (float | str): Maximum value.
        counter (float | str | None): Explicit numeric counter.

    Returns:
        int | float: Deterministic pseudo-random number within bounds.
    """
    ctx = context or {}
    mn = _eval_num(min_val, ctx, 0.0)
    mx = _eval_num(max_val, ctx, 100.0)
    
    if counter is None or str(counter).strip() == "":
        ctr = _eval_num(ctx.get("i", ctx.get("j", 1)), ctx, 1.0)
    else:
        ctr = _eval_num(counter, ctx, 1.0)
    
    low = min(mn, mx)
    high = max(mn, mx)
    diff = int(high - low + 1)
    if diff <= 0: return int(low) if low.is_integer() else round(low, 2)
    
    fake_hash = int((ctr * 9301 + 49297) % 233280)
    val = low + (fake_hash % diff)
    if isinstance(val, float) and val.is_integer():
        return int(val)
    return round(val, 2)

def _pyxis_random_rcolor(min_val="&HFFFFFF&", max_val="&H000000&", context=None):
    """
    Generate an interpolated or chosen colour between two boundary colours or a palette list.

    Supports ASS colour notation (`&HBBGGRR&`) and web hex notation (`#RRGGBB`).

    Args:
        min_val (str): Starting colour or comma-separated palette list.
        max_val (str): Ending colour.
        context (dict | None): Context dictionary.

    Returns:
        str: Interpolated or randomly chosen colour string.
    """
    c1_str = str(min_val or "&HFFFFFF&").strip()
    c2_str = str(max_val or "&H000000&").strip()
    
    if "," in c1_str:
        opts = [c.strip() for c in c1_str.split(",") if c.strip()]
        if opts: return random.choice(opts)
        
    from utils import parse_color_to_rgb, rgb_to_ass_color, rgb_to_hex_color
    r1, g1, b1 = parse_color_to_rgb(c1_str)
    r2, g2, b2 = parse_color_to_rgb(c2_str)
    
    t = random.random()
    r = int(round(r1 + (r2 - r1) * t))
    g = int(round(g1 + (g2 - g1) * t))
    b = int(round(b1 + (b2 - b1) * t))
    
    if c1_str.startswith("#"):
        return rgb_to_hex_color(r, g, b)
    return rgb_to_ass_color(r, g, b)

def _pyxis_random_r2d(min_val=0.0, max_val=100.0, step=1.0, context=None):
    """
    Generate a 2D coordinate pair string with independent pseudo-random X and Y values.

    Args:
        min_val (float | str): Lower limit for both axes.
        max_val (float | str): Upper limit for both axes.
        step (float | str): Quantisation step.
        context (dict | None): Context dictionary.

    Returns:
        str: Formatted coordinate string `"x,y"`.
    """
    rx_val = _pyxis_random_r(min_val, max_val, step, context)
    ry_val = _pyxis_random_r(min_val, max_val, step, context)
    return f"{rx_val},{ry_val}"

def _pyxis_random_rbool(prob=50.0, context=None):
    """
    Evaluate a pseudo-random boolean test based on a percentage threshold (0.0 to 100.0).

    Args:
        prob (float | str): Success probability percentage (0-100) or ratio (0-1).
        context (dict | None): Context dictionary.

    Returns:
        str: `"True"` if random value satisfies probability, `"False"` otherwise.
    """
    p = _eval_num(prob, context, 50.0)
    p_norm = p / 100.0 if p > 1.0 else p
    return "True" if random.random() < p_norm else "False"

def _pyxis_random_rstep(min_val=0.0, max_val=360.0, step=45.0, context=None):
    """
    Generate a quantised pseudo-random number constrained to discrete step intervals.

    Args:
        min_val (float | str): Lower boundary.
        max_val (float | str): Upper boundary.
        step (float | str): Discrete angular or numeric interval.
        context (dict | None): Context dictionary.

    Returns:
        int | float: Value aligned to step increments.
    """
    val = _pyxis_random_r(min_val, max_val, step, context)
    st = _eval_num(step, context, 1.0)
    if st > 0 and float(st).is_integer():
        return int(val)
    return val

def get_iterator_scope_key(context, iterator_name: str):
    """Calculates canonical unique scope string for a given iterator or semantic unit.

    Resolves a deterministic scope key from the execution context based on the
    specified iterator category (e.g. 'global', 'line', 'syl', 'char', 'word',
    or custom index variables such as 'i', 'j', 'syl_i'). For sub-loop counters
    and custom variables, inherits parent unit hierarchy (line -> char/syl/word -> subloop)
    to ensure isolation across higher-level units.

    Args:
        context (dict): Runtime execution context supplied by the DAG evaluation engine.
        iterator_name (str): Identifier of the target iterator or semantic unit.

    Returns:
        str | None: Formatted canonical identifier (e.g. 'line_0_char_1_j_2') or None if invalid.
    """
    if not iterator_name or not str(iterator_name).strip():
        return None
    iter_key = str(iterator_name).strip()
    ctx = context or {}

    l = ctx.get("line")
    l_id = getattr(l, "i", getattr(l, "idx", id(l) if l else 0))

    if iter_key == "global":
        return "global"
    elif iter_key in ("line", "l"):
        return f"line_{l_id}"
    elif iter_key in ("syl", "syllable"):
        s = ctx.get("syl")
        s_id = getattr(s, "i", getattr(s, "syl_i", id(s) if s else 0))
        return f"line_{l_id}_syl_{s_id}"
    elif iter_key in ("char", "character"):
        c = ctx.get("char")
        c_id = getattr(c, "i", getattr(c, "char_i", id(c) if c else 0))
        return f"line_{l_id}_char_{c_id}"
    elif iter_key == "word":
        w = ctx.get("word")
        w_id = getattr(w, "i", getattr(w, "word_i", id(w) if w else 0))
        return f"line_{l_id}_word_{w_id}"
    else:
        parent_prefix = f"line_{l_id}"
        c = ctx.get("char")
        s = ctx.get("syl")
        w = ctx.get("word")
        u = ctx.get("active_unit") or ctx.get("unit")

        if c is not None and (hasattr(c, "i") or hasattr(c, "char_i") or u is c):
            c_id = getattr(c, "i", getattr(c, "char_i", 0))
            parent_prefix = f"line_{l_id}_char_{c_id}"
        elif s is not None and (hasattr(s, "i") or hasattr(s, "syl_i") or u is s):
            s_id = getattr(s, "i", getattr(s, "syl_i", 0))
            parent_prefix = f"line_{l_id}_syl_{s_id}"
        elif w is not None and (hasattr(w, "i") or hasattr(w, "word_i") or u is w):
            w_id = getattr(w, "i", getattr(w, "word_i", 0))
            parent_prefix = f"line_{l_id}_word_{w_id}"

        val = ctx.get(iter_key)
        if val is None:
            if u is not None and hasattr(u, iter_key):
                val = getattr(u, iter_key)
        if val is None:
            val = 0
        return f"{parent_prefix}_{iter_key}_{val}"


_WRAPPER_FUNC_NAMES = {
    "_call_scoped", "R", "Rs", "Rc", "Rcs", "Rd", "Rds", "Rm", "Rms",
    "Rr", "Rstep", "R2d", "Rbool", "Rcolor", "Re", "Rfake",
    "rand", "r", "rs", "rc", "rcs", "rm", "rms", "rd", "rds", "rcolor", "rstep", "rbool",
    "math_random_master", "_caller", "_make_rnd_caller", "_make_eval_rnd_caller"
}


def _get_callsite_id(kwargs, context):
    """Resolves a unique callsite discriminator for scoped random generation.

    Distinguishes independent invocations across nodes, expressions, and statements,
    while memoizing repeated queries within the same scope. Callers may explicitly
    provide 'tag', 'callsite', 'slot', or 'id' to link or isolate random draws.

    Args:
        kwargs (dict): Keyword arguments passed to the random call.
        context (dict | None): Active DAG evaluation context.

    Returns:
        tuple: Hashable identifier representing the execution point.
    """
    for explicit_key in ("tag", "callsite", "slot", "id"):
        if explicit_key in kwargs and kwargs[explicit_key] is not None:
            return (explicit_key, str(kwargs[explicit_key]))

    node_id = context.get("_active_node_id") if isinstance(context, dict) else None
    callsite_label = context.get("_active_callsite_label") if isinstance(context, dict) else None

    try:
        f = sys._getframe(2)
        while f:
            c_name = f.f_code.co_name
            if c_name not in _WRAPPER_FUNC_NAMES and "math_nodes.py" not in f.f_code.co_filename:
                return (node_id, callsite_label, hash(f.f_code.co_code), f.f_lasti)
            f = f.f_back
    except (AttributeError, ValueError):
        pass

    return (node_id, callsite_label, 0, 0)


class PyxisScopedRandom:
    """Wrapper providing scoped random generation tied to an iterator name or unit scope.

    Caches pseudo-random values across identical invocations within the same unit scope
    to guarantee visual stability (e.g. consistent displacement across frames for a syllable).

    Attributes:
        _context (dict): Active execution context.
        _iterator_name (str): Normalised iterator name identifying the scope boundary.
    """

    def __init__(self, context, iterator_name: str):
        """Initialises the scoped random wrapper for a specific iterator name.

        Args:
            context (dict): Active DAG execution context.
            iterator_name (str): Identifier of the target iterator scope.
        """
        self._context = context
        self._iterator_name = str(iterator_name).strip()

    def _get_scope_key(self):
        """Resolves the canonical scope key for the current iterator and context.

        Returns:
            str | None: Scope key representation or None if unresolvable.
        """
        return get_iterator_scope_key(self._context, self._iterator_name)

    def _call_scoped(self, mode_name, *args, **kwargs):
        """Executes a scoped random query, retrieving or updating the context cache.

        Args:
            mode_name (str): Generation mode identifier (e.g. 'R', 'Rs', 'Rc').
            *args: Positional bounds (min_val, max_val, step).
            **kwargs: Keyword arguments for random generation and options.

        Returns:
            int | float | str: Generated or cached pseudo-random value.
        """
        ctx = self._context
        if ctx is None or not isinstance(ctx, dict):
            return math_random_master(ctx, mode=mode_name, *args, **kwargs)

        scope_key = self._get_scope_key()
        if scope_key is None:
            return math_random_master(ctx, mode=mode_name, *args, **kwargs)

        if not isinstance(ctx.get("_scoped_rnd_cache"), dict):
            ctx["_scoped_rnd_cache"] = {}
        cache = ctx["_scoped_rnd_cache"]

        args_repr = tuple(str(a) for a in args)
        kwargs_repr = tuple(sorted((k, str(v)) for k, v in kwargs.items() if k not in ("by", "iter", "iterator", "tag", "callsite", "slot", "id")))
        callsite_id = _get_callsite_id(kwargs, ctx)
        cache_key = (callsite_id, self._iterator_name, scope_key, mode_name, args_repr, kwargs_repr)

        if cache_key in cache:
            return cache[cache_key]

        if len(args) == 0:
            mn = kwargs.get("min_val", kwargs.get("min", None))
            mx = kwargs.get("max_val", kwargs.get("max", None))
            st = kwargs.get("step", None)
        elif len(args) == 1:
            mn = args[0]
            mx = None
            st = kwargs.get("step", None)
        elif len(args) == 2:
            mn = args[0]
            mx = args[1]
            st = kwargs.get("step", None)
        else:
            mn = args[0]
            mx = args[1]
            st = args[2]

        clean_kwargs = {k: v for k, v in kwargs.items() if k not in ("by", "iter", "iterator", "min_val", "min", "max_val", "max", "step", "tag", "callsite", "slot", "id")}
        res = math_random_master(ctx, mode=mode_name, min_val=mn, max_val=mx, step=st, iterator="", by="", **clean_kwargs)
        cache[cache_key] = res
        return res

    def R(self, *args, **kwargs):
        """Scoped uniform integer random."""
        return self._call_scoped("R", *args, **kwargs)

    def Rs(self, *args, **kwargs):
        """Scoped signed uniform integer random."""
        return self._call_scoped("Rs", *args, **kwargs)

    def Rc(self, *args, **kwargs):
        """Scoped centesimal float random."""
        return self._call_scoped("Rc", *args, **kwargs)

    def Rcs(self, *args, **kwargs):
        """Scoped signed centesimal float random."""
        return self._call_scoped("Rcs", *args, **kwargs)

    def Rm(self, *args, **kwargs):
        """Scoped millesimal float random."""
        return self._call_scoped("Rm", *args, **kwargs)

    def Rms(self, *args, **kwargs):
        """Scoped signed millesimal float random."""
        return self._call_scoped("Rms", *args, **kwargs)

    def Rd(self, *args, **kwargs):
        """Scoped decimal float random."""
        return self._call_scoped("Rd", *args, **kwargs)

    def Rds(self, *args, **kwargs):
        """Scoped signed decimal float random."""
        return self._call_scoped("Rds", *args, **kwargs)

    def Rr(self, *args, **kwargs):
        """Scoped seed-based repeatable random."""
        return self._call_scoped("Rr", *args, **kwargs)

    def Rstep(self, *args, **kwargs):
        """Scoped discrete step-quantised random."""
        return self._call_scoped("Rstep", *args, **kwargs)

    def R2d(self, *args, **kwargs):
        """Scoped 2D coordinate pair random."""
        return self._call_scoped("R2d", *args, **kwargs)

    def Rbool(self, *args, **kwargs):
        """Scoped probabilistic boolean random."""
        return self._call_scoped("Rbool", *args, **kwargs)

    def Rcolor(self, *args, **kwargs):
        """Scoped ASS hex colour random."""
        return self._call_scoped("Rcolor", *args, **kwargs)

    def Re(self, *args, **kwargs):
        """Scoped categorical element selection random."""
        return self._call_scoped("Re", *args, **kwargs)

    def Rfake(self, *args, **kwargs):
        """Scoped pseudo-random golden-ratio sequence."""
        return self._call_scoped("Rfake", *args, **kwargs)

    def rand(self, *args, **kwargs):
        """Alias for scoped R()."""
        return self.R(*args, **kwargs)

    def r(self, *args, **kwargs):
        """Lowercase alias for scoped R()."""
        return self.R(*args, **kwargs)

    def rs(self, *args, **kwargs):
        """Lowercase alias for scoped Rs()."""
        return self.Rs(*args, **kwargs)

    def rc(self, *args, **kwargs):
        """Lowercase alias for scoped Rc()."""
        return self.Rc(*args, **kwargs)

    def rcs(self, *args, **kwargs):
        """Lowercase alias for scoped Rcs()."""
        return self.Rcs(*args, **kwargs)

    def rm(self, *args, **kwargs):
        """Lowercase alias for scoped Rm()."""
        return self.Rm(*args, **kwargs)

    def rms(self, *args, **kwargs):
        """Lowercase alias for scoped Rms()."""
        return self.Rms(*args, **kwargs)

    def rd(self, *args, **kwargs):
        """Lowercase alias for scoped Rd()."""
        return self.Rd(*args, **kwargs)

    def rds(self, *args, **kwargs):
        """Lowercase alias for scoped Rds()."""
        return self.Rds(*args, **kwargs)

    def rcolor(self, *args, **kwargs):
        """Lowercase alias for scoped Rcolor()."""
        return self.Rcolor(*args, **kwargs)

    def rstep(self, *args, **kwargs):
        """Lowercase alias for scoped Rstep()."""
        return self.Rstep(*args, **kwargs)

    def rbool(self, *args, **kwargs):
        """Lowercase alias for scoped Rbool()."""
        return self.Rbool(*args, **kwargs)


class PyxisByDispatcher:
    """Namespace dispatcher for 'by.<iterator>' syntax.

    Facilitates scoped random generation via attribute or key indexing
    (e.g. `by.s_i.Rms(0.01, 0.02)` or `by['j'].Rs(10)`).

    Attributes:
        _context (dict): Active DAG execution context.
    """

    def __init__(self, context):
        """Initialises the dispatcher with the given execution context.

        Args:
            context (dict): Active execution context.
        """
        self._context = context

    def __getattr__(self, name: str):
        """Dynamically instantiates a scoped random wrapper for the attribute name.

        Args:
            name (str): Name of the iterator or unit variable.

        Returns:
            PyxisScopedRandom: Scoped random wrapper bound to the given iterator.

        Raises:
            AttributeError: If attempting to access dunder methods.
        """
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        return PyxisScopedRandom(self._context, name)

    def __getitem__(self, item):
        """Dynamically instantiates a scoped random wrapper via dictionary item indexing.

        Args:
            item (Any): Identifier key of the iterator scope.

        Returns:
            PyxisScopedRandom: Scoped random wrapper bound to the given iterator key.
        """
        return PyxisScopedRandom(self._context, str(item))


def math_random_master(context, mode="R", min_val=None, max_val=None, step=None, options="", counter="", total=1, output_slot_index=0, iterator="", by="", **kwargs):
    """Universal dispatcher for the 'Basics/MultiRandom' node and expression-level random calls.

    Generates single values or batch sequences across integer, float, signed,
    discrete-step, colour, and categorical selection algorithms.

    Args:
        context (dict): DAG execution context containing active units, iterators, and state.
        mode (str): Random generation algorithm code (e.g. 'R', 'Rs', 'Rc', 'Rcolor', 'Re').
        min_val (int | float | str, optional): Lower bound or primary parameter.
        max_val (int | float | str, optional): Upper bound.
        step (int | float | str, optional): Step size or quantisation interval.
        options (str, optional): Comma-separated elements for categorical 'Re' selection.
        counter (str | int, optional): Explicit index counter for pseudo-random 'Rfake'.
        total (int | float | str, optional): Batch size when output_slot_index == 1 or batch requested.
        output_slot_index (int, optional): Port index (0: single value, 1: batch sequence).
        iterator (str, optional): Iterator scope identifier for deterministic caching.
        by (str, optional): Alias for iterator parameter.
        **kwargs: Additional parameters and legacy keyword arguments.

    Returns:
        int | float | str: Generated pseudo-random value or comma-separated batch string.
    """
    iter_name = str(kwargs.get("iterator", kwargs.get("by", iterator or by or ""))).strip()
    if iter_name:
        scoped = PyxisScopedRandom(context, iter_name)
        clean_kwargs = {k: v for k, v in kwargs.items() if k not in ("iterator", "by", "iter")}
        return scoped._call_scoped(mode, min_val=min_val, max_val=max_val, step=step, options=options, counter=counter, total=total, output_slot_index=output_slot_index, **clean_kwargs)

    m = str(kwargs.get("mode", mode or "R")).strip()
    mn = kwargs.get("min_val", kwargs.get("min", min_val))
    mx = kwargs.get("max_val", kwargs.get("max", max_val))
    st = kwargs.get("step", step)
    opt = kwargs.get("options", options)
    cnt = kwargs.get("counter", counter)

    def _gen_single():
        if m == "R":
            return _pyxis_random_r(mn, mx, st if st is not None else 1.0, context)
        elif m == "Rs":
            return _pyxis_random_rs(mn, mx, st if st is not None else 1.0, context)
        elif m == "Rr":
            return _pyxis_random_rr(context, mn, mx, st if st is not None else 1.0)
        elif m == "Rc":
            return _pyxis_random_rc(mn, mx, st if st is not None else 0.01, context)
        elif m == "Rd":
            return _pyxis_random_rd(mn, mx, st if st is not None else 0.1, context)
        elif m == "Rm":
            return _pyxis_random_rm(mn, mx, st if st is not None else 0.001, context)
        elif m == "Rds":
            return _pyxis_random_rds(mn, mx, st if st is not None else 0.1, context)
        elif m == "Rcs":
            return _pyxis_random_rcs(mn, mx, st if st is not None else 0.01, context)
        elif m == "Rms":
            return _pyxis_random_rms(mn, mx, st if st is not None else 0.001, context)
        elif m == "Re":
            return _pyxis_random_re(opt, context)
        elif m == "Rfake":
            return _pyxis_random_rfake(context, mn if mn is not None else 0.0, mx if mx is not None else 100.0, cnt)
        elif m in ("Rcolor", "Rcol"):
            return _pyxis_random_rcolor(mn or "&HFFFFFF&", mx or "&H000000&", context)
        elif m == "R2d":
            return _pyxis_random_r2d(mn if mn is not None else 0.0, mx if mx is not None else 100.0, st if st is not None else 1.0, context)
        elif m == "Rbool":
            return _pyxis_random_rbool(mn if mn is not None else 50.0, context)
        elif m == "Rstep":
            return _pyxis_random_rstep(mn if mn is not None else 0.0, mx if mx is not None else 360.0, st if st is not None else 45.0, context)
        else:
            return _pyxis_random_r(mn, mx, st if st is not None else 1.0, context)

    if output_slot_index == 1 or kwargs.get("return_batch", False):
        try:
            n_val = max(1, int(round(float(_eval_num(total, context, 1.0)))))
        except Exception:
            n_val = 1
        batch_res = [_gen_single() for _ in range(n_val)]
        return ", ".join(str(x) for x in batch_res)

    return _gen_single()
 
 
NODE_REGISTRY["MultiRandom"] = math_random_master
NODE_REGISTRY["Basics/MultiRandom"] = math_random_master


def math_polar(context, x=0, y=0, angle=0, radius=0):
    """Projects cartesian coordinates using polar angle and radial distance.

    Calculates $(x_0 + r \\cos(\\theta), y_0 + r \\sin(\\theta))$ and formats the
    resulting coordinates into an ASS `\\pos(x, y)` override tag.

    Args:
        context (dict): Active execution context.
        x (float | str): Origin abscissa (x0). Defaults to 0.
        y (float | str): Origin ordinate (y0). Defaults to 0.
        angle (float | str): Projection angle in degrees. Defaults to 0.
        radius (float | str): Radial distance from origin. Defaults to 0.

    Returns:
        str: Formatted ASS tag `\\pos(x, y)`.
    """
    import math
    from node_engine import _eval_num_expr
    x0 = _eval_num_expr(x, context, 0.0)
    y0 = _eval_num_expr(y, context, 0.0)
    ang = _eval_num_expr(angle, context, 0.0)
    r = _eval_num_expr(radius, context, 0.0)

    rad = math.radians(ang)
    res_x = x0 + r * math.cos(rad)
    res_y = y0 + r * math.sin(rad)

    fmt_x = int(res_x) if float(res_x).is_integer() else round(res_x, 2)
    fmt_y = int(res_y) if float(res_y).is_integer() else round(res_y, 2)

    return f"\\pos({fmt_x},{fmt_y})"


def math_bezier_node(context, p0="0,0", p1="50,100", p2="150,100", p3="200,0", t=0.5, subdivs=100, mode="Cubic 2D"):
    """Computes quadratic or cubic 2D Bézier curve interpolations using De Casteljau's algorithm.

    Evaluates a parametric point along a Bézier trajectory defined by control points
    p0, p1, p2 (and p3 for cubic curves). Can output either a discrete ASS `\\pos(x, y)` tag
    or a continuous ASSdraw vector spline command `m x0 y0 b ...`.

    Args:
        context (dict): Active execution context.
        p0 (str | tuple | list): Start point coordinate 'x,y'. Defaults to "0,0".
        p1 (str | tuple | list): First control point coordinate 'x,y'. Defaults to "50,100".
        p2 (str | tuple | list): Second control point coordinate 'x,y'. Defaults to "150,100".
        p3 (str | tuple | list): Third control point (end point for cubic). Defaults to "200,0".
        t (float | str): Parametric progression normalized in [0.0, 1.0]. Defaults to 0.5.
        subdivs (int | str): Subdivisions count (reserved for spline sampling). Defaults to 100.
        mode (str): Curve mode ('Cubic 2D', 'Quadratic 2D', 'Spline' / 'ASSDraw'). Defaults to 'Cubic 2D'.

    Returns:
        str: Formatted ASS tag `\\pos(x, y)` or vector path string `m ... b ...`.
    """
    import math
    from node_engine import _eval_num_expr
    ft = float(_eval_num_expr(t, context, 0.5))
    ft = max(0.0, min(1.0, ft))
    n_subdivs = max(0, min(2000, int(float(_eval_num_expr(subdivs, context, 100)))))

    def parse_pt(pt_val, default=(0.0, 0.0)):
        if isinstance(pt_val, (list, tuple)) and len(pt_val) >= 2:
            return float(_eval_num_expr(pt_val[0], context, default[0])), float(_eval_num_expr(pt_val[1], context, default[1]))
        s = str(pt_val).strip()
        depth = 0
        split_idx = -1
        for i, ch in enumerate(s):
            if ch in '([{':
                depth += 1
            elif ch in ')]}':
                depth -= 1
            elif ch == ',' and depth == 0:
                split_idx = i
                break
        if split_idx != -1:
            part0 = s[:split_idx].strip()
            part1 = s[split_idx+1:].strip()
            return float(_eval_num_expr(part0, context, default[0])), float(_eval_num_expr(part1, context, default[1]))
        elif ' ' in s and depth == 0:
            parts = s.split(None, 1)
            return float(_eval_num_expr(parts[0], context, default[0])), float(_eval_num_expr(parts[1], context, default[1]))
        try:
            v = float(_eval_num_expr(s, context, default[0]))
            return v, v
        except Exception:
            return default

    def _eval_de_casteljau(pts, t_param):
        if not pts:
            return 0.0, 0.0
        curr = [(float(p[0]), float(p[1])) for p in pts]
        t_val = float(t_param)
        u_val = 1.0 - t_val
        while len(curr) > 1:
            curr = [
                (curr[i][0] * u_val + curr[i + 1][0] * t_val,
                 curr[i][1] * u_val + curr[i + 1][1] * t_val)
                for i in range(len(curr) - 1)
            ]
        return curr[0]

    x0, y0 = parse_pt(p0, (0.0, 0.0))
    x1, y1 = parse_pt(p1, (50.0, 100.0))
    x2, y2 = parse_pt(p2, (150.0, 100.0))
    x3, y3 = parse_pt(p3, (200.0, 0.0))

    m = str(mode).strip().lower()
    if "quad" in m or "cuad" in m:
        pts = [(x0, y0), (x1, y1), (x2, y2)]
    else:
        pts = [(x0, y0), (x1, y1), (x2, y2), (x3, y3)]

    bx, by = _eval_de_casteljau(pts, ft)

    rbx = round(float(bx), 2)
    rby = round(float(by), 2)
    fmt_x = int(rbx) if rbx.is_integer() else rbx
    fmt_y = int(rby) if rby.is_integer() else rby

    if m in ("spline", "assdraw", "trazado assdraw", "b"):
        if len(pts) == 3:
            cp1_x = x0 + (2.0 / 3.0) * (x1 - x0)
            cp1_y = y0 + (2.0 / 3.0) * (y1 - y0)
            cp2_x = x2 + (2.0 / 3.0) * (x1 - x2)
            cp2_y = y2 + (2.0 / 3.0) * (y1 - y2)
            return f"m {round(x0,2)} {round(y0,2)} b {round(cp1_x,2)} {round(cp1_y,2)} {round(cp2_x,2)} {round(cp2_y,2)} {round(x2,2)} {round(y2,2)}"
        return f"m {round(x0,2)} {round(y0,2)} b {round(x1,2)} {round(y1,2)} {round(x2,2)} {round(y2,2)} {round(x3,2)} {round(y3,2)}"

    return f"\\pos({fmt_x},{fmt_y})"


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

"""Mathematical calculation and numeric transformation nodes."""

import math
import random
import re
from decorators import pyxis_node, NODE_REGISTRY


def _eval_num(val, context=None, default=0.0):
    if val is None or val == "":
        return float(default)
    if isinstance(val, (int, float)):
        return float(val)

    s_val = str(val).strip()
    if re.match(r"^[+-]?\d+,\d+$", s_val):
        s_val = s_val.replace(',', '.')

    try:
        from node_engine import _eval_num_expr
        return float(_eval_num_expr(s_val, context, default=default))
    except Exception:
        pass

    try:
        return float(s_val.replace(',', '.'))
    except Exception:
        return float(default)


def eval_math_node(context=None, **kwargs):
    """Unified handler for Master Math Node."""
    category = str(kwargs.get("category", kwargs.get("categoria", "Basic"))).strip()
    operation = str(kwargs.get("operation", kwargs.get("operacion", "Add"))).strip()
    
    ctx = context or {}

    def get_num(key, default=0.0):
        val = kwargs.get(key)
        if val is None:
            val = kwargs.get(key.lower())
        return _eval_num(val, ctx, default)

    cat_clean = category.lower()

    if cat_clean in ("basic", "basico", "rounding", "redondeo"):
        a = get_num("A", 0.0)
        b = get_num("B", 0.0)

        op_clean = operation.strip().lower()
        
        if op_clean in ("add", "suma", "+"):
            return a + b
        elif op_clean in ("sub", "subtract", "resta", "-"):
            return a - b
        elif op_clean in ("mul", "multiply", "multiplicacion", "*"):
            return a * b
        elif op_clean in ("div", "divide", "division", "/"):
            return a / b if b != 0 else 0.0
        elif op_clean in ("mod", "modulo", "%"):
            return a % b if b != 0 else 0.0
        elif op_clean in ("pow", "power", "potencia", "^"):
            try:
                return math.pow(a, b)
            except Exception:
                return 0.0
        elif op_clean in ("abs", "absolute", "absoluto"):
            return abs(a)
        elif op_clean in ("neg", "negative", "negativo"):
            return -a
        elif op_clean in ("round", "redondear"):
            return float(round(a))
        elif op_clean in ("floor", "piso"):
            return float(math.floor(a))
        elif op_clean in ("ceil", "techo"):
            return float(math.ceil(a))
        else:
            return a + b

    elif cat_clean in ("trig", "trigonometry", "trigono"):
        a = get_num("A", get_num("Degrees", get_num("Radians", get_num("Grados", get_num("Radianes", 0.0)))))
        op_clean = operation.lower()
        
        if op_clean in ("sin", "sine", "seno"):
            return math.sin(math.radians(a))
        elif op_clean in ("cos", "cosine", "coseno"):
            return math.cos(math.radians(a))
        elif op_clean in ("tan", "tangent", "tangente"):
            return math.tan(math.radians(a))
        elif op_clean in ("arcsin", "asin", "arcseno"):
            clamped = max(-1.0, min(1.0, a))
            return math.degrees(math.asin(clamped))
        elif op_clean in ("arccos", "acos", "arccoseno"):
            clamped = max(-1.0, min(1.0, a))
            return math.degrees(math.acos(clamped))
        elif op_clean in ("arctan", "atan", "arctangente"):
            return math.degrees(math.atan(a))
        elif op_clean in ("arctan2", "atan2", "arctangente2"):
            y = get_num("Y", get_num("A", 0.0))
            x = get_num("X", get_num("B", 1.0))
            return math.degrees(math.atan2(y, x))
        elif op_clean in ("radians", "rad", "radianes"):
            return math.radians(a)
        elif op_clean in ("degrees", "deg", "grados"):
            return math.degrees(a)
        else:
            return math.sin(math.radians(a))

    elif cat_clean in ("easing",):
        raw_t = get_num("t", get_num("A", 0.0))
        t = max(0.0, min(1.0, raw_t))
        op_clean = operation.lower()
        
        if op_clean in ("easein", "ease_in"):
            return t * t
        elif op_clean in ("easeout", "ease_out"):
            return 1.0 - (1.0 - t) * (1.0 - t)
        elif op_clean in ("easeinout", "ease_in_out"):
            if t < 0.5:
                return 2.0 * t * t
            else:
                return 1.0 - math.pow(-2.0 * t + 2.0, 2) / 2.0
        elif op_clean in ("cubicin", "cubic_in"):
            return t * t * t
        elif op_clean in ("cubicout", "cubic_out"):
            return 1.0 - (1.0 - t) ** 3
        elif op_clean in ("exponential", "expo", "exponencial"):
            if t <= 0.0:
                return 0.0
            if t >= 1.0:
                return 1.0
            return math.pow(2.0, 10.0 * (t - 1.0))
        elif op_clean in ("elastic", "elastico"):
            if t <= 0.0:
                return 0.0
            if t >= 1.0:
                return 1.0
            c4 = (2.0 * math.pi) / 3.0
            return -math.pow(2.0, 10.0 * t - 10.0) * math.sin((t * 10.0 - 10.75) * c4)
        elif op_clean in ("bounce", "rebote"):
            n1 = 7.5625
            d1 = 2.75
            if t < 1.0 / d1:
                return n1 * t * t
            elif t < 2.0 / d1:
                t -= 1.5 / d1
                return n1 * t * t + 0.75
            elif t < 2.5 / d1:
                t -= 2.25 / d1
                return n1 * t * t + 0.9375
            else:
                t -= 2.625 / d1
                return n1 * t * t + 0.984375
        elif op_clean in ("back", "retroceso"):
            c1 = 1.70158
            c3 = c1 + 1.0
            return c3 * (t ** 3) - c1 * (t ** 2)
        else:
            return t * t

    elif cat_clean in ("waves", "wave", "ondas"):
        t = get_num("t", 0.0)
        frec = get_num("freq", get_num("Frecuencia", 1.0))
        amp = get_num("amp", get_num("Amplitud", 1.0))
        offset = get_num("Offset", 0.0)
        op_clean = operation.lower()
        
        if op_clean in ("sine", "sin", "seno"):
            return amp * math.sin(2.0 * math.pi * frec * t) + offset
        elif op_clean in ("square", "cuadrada"):
            val = math.sin(2.0 * math.pi * frec * t)
            return (amp if val >= 0.0 else -amp) + offset
        elif op_clean in ("triangle", "triangulo"):
            phase = (t * frec) % 1.0
            val = 2.0 * abs(2.0 * phase - 1.0) - 1.0
            return amp * val + offset
        elif op_clean in ("sawtooth", "dientesierra"):
            phase = (t * frec) % 1.0
            val = 2.0 * phase - 1.0
            return amp * val + offset
        else:
            return amp * math.sin(2.0 * math.pi * frec * t) + offset

    elif cat_clean in ("utilities", "utility", "utilidades", "clamping", "clamp", "random", "aleatorio"):
        op_clean = operation.lower()
        if op_clean in ("clamp",):
            val = get_num("Value", get_num("Valor", get_num("A", 0.0)))
            mn = get_num("Min", 0.0)
            mx = get_num("Max", 1.0)
            low = min(mn, mx)
            high = max(mn, mx)
            return max(low, min(high, val))
        elif op_clean in ("lerp",):
            a = get_num("A", 0.0)
            b = get_num("B", 1.0)
            t = get_num("t", 0.5)
            t_norm = max(0.0, min(1.0, t))
            return a + (b - a) * t_norm
        elif op_clean in ("min", "minimum", "minimo"):
            a = get_num("A", 0.0)
            b = get_num("B", 0.0)
            return min(a, b)
        elif op_clean in ("max", "maximum", "maximo"):
            a = get_num("A", 0.0)
            b = get_num("B", 0.0)
            return max(a, b)
        elif op_clean in ("random", "aleatorio"):
            mn = get_num("Min", 0.0)
            mx = get_num("Max", 1.0)
            seed = kwargs.get("Seed", kwargs.get("seed", kwargs.get("Semilla", kwargs.get("semilla"))))
            if seed is not None and str(seed).strip() != "":
                try:
                    s_val = int(_eval_num(seed, ctx, 0.0))
                    rng = random.Random(s_val)
                    return rng.uniform(min(mn, mx), max(mn, mx))
                except Exception:
                    pass
            return random.uniform(min(mn, mx), max(mn, mx))
        elif op_clean in ("maprange", "map_range", "map range", "mapearrango"):
            val = get_num("Value", get_num("Valor", 0.0))
            in_min = get_num("MinIn", 0.0)
            in_max = get_num("MaxIn", 1.0)
            out_min = get_num("MinOut", 0.0)
            out_max = get_num("MaxOut", 100.0)
            
            if in_max == in_min:
                return out_min
            t_ratio = (val - in_min) / (in_max - in_min)
            return out_min + t_ratio * (out_max - out_min)
        else:
            val = get_num("Value", 0.0)
            return val

    return 0.0


NODE_REGISTRY["Math"] = eval_math_node
NODE_REGISTRY["Basics/Math"] = eval_math_node


import random

def _pyxis_random_r(min_val=0.0, max_val=100.0, step=1.0, context=None):
    mn = _eval_num(min_val, context, 0.0)
    mx = _eval_num(max_val, context, 100.0)
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

def _pyxis_random_rs(min_val=0.0, max_val=100.0, step=1.0, context=None):
    val = _pyxis_random_r(min_val, max_val, step, context)
    sign = 1 if random.random() >= 0.5 else -1
    res = val * sign
    if isinstance(res, float) and res.is_integer():
        return int(res)
    return res

def _pyxis_random_rr(context=None, min_val=0.0, max_val=100.0, step=1.0):
    val = _pyxis_random_r(min_val, max_val, step, context)
    ctx = context or {}
    rx = _eval_num(ctx.get("rx", 1280), ctx, 1280.0)
    ratio = rx / 1280.0
    res = round(val * ratio, 4)
    if isinstance(res, float) and res.is_integer():
        return int(res)
    return res

def _pyxis_random_rd(min_val=0.0, max_val=100.0, step=0.1, context=None):
    mn = _eval_num(min_val, context, 0.0) * 10.0
    mx = _eval_num(max_val, context, 100.0) * 10.0
    st = _eval_num(step, context, 0.1) * 10.0
    val = float(_pyxis_random_r(mn, mx, st, context))
    res = round(val / 10.0, 1)
    return f"{res:.1f}"

def _pyxis_random_rc(min_val=0.0, max_val=100.0, step=0.01, context=None):
    mn = _eval_num(min_val, context, 0.0) * 100.0
    mx = _eval_num(max_val, context, 100.0) * 100.0
    st = _eval_num(step, context, 0.01) * 100.0
    val = float(_pyxis_random_r(mn, mx, st, context))
    res = round(val / 100.0, 2)
    return f"{res:.2f}"

def _pyxis_random_rm(min_val=0.0, max_val=100.0, step=0.001, context=None):
    mn = _eval_num(min_val, context, 0.0) * 1000.0
    mx = _eval_num(max_val, context, 100.0) * 1000.0
    st = _eval_num(step, context, 0.001) * 1000.0
    val = float(_pyxis_random_r(mn, mx, st, context))
    res = round(val / 1000.0, 3)
    return f"{res:.3f}"

def _pyxis_random_rds(min_val=0.0, max_val=100.0, step=0.1, context=None):
    sign = 1 if random.random() >= 0.5 else -1
    res = round(float(_pyxis_random_rd(min_val, max_val, step, context)) * sign, 1)
    return f"{res:.1f}"

def _pyxis_random_rcs(min_val=0.0, max_val=100.0, step=0.01, context=None):
    sign = 1 if random.random() >= 0.5 else -1
    res = round(float(_pyxis_random_rc(min_val, max_val, step, context)) * sign, 2)
    return f"{res:.2f}"

def _pyxis_random_rms(min_val=0.0, max_val=100.0, step=0.001, context=None):
    sign = 1 if random.random() >= 0.5 else -1
    res = round(float(_pyxis_random_rm(min_val, max_val, step, context)) * sign, 3)
    return f"{res:.3f}"

def _pyxis_random_re(options_str="", context=None):
    s = str(options_str or "").strip()
    if not s: return ""
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if not parts: return s
    return random.choice(parts)

def _pyxis_random_rfake(context=None, min_val=0.0, max_val=100.0, counter=None):
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
    rx_val = _pyxis_random_r(min_val, max_val, step, context)
    ry_val = _pyxis_random_r(min_val, max_val, step, context)
    return f"{rx_val},{ry_val}"

def _pyxis_random_rbool(prob=50.0, context=None):
    p = _eval_num(prob, context, 50.0)
    p_norm = p / 100.0 if p > 1.0 else p
    return "True" if random.random() < p_norm else "False"

def _pyxis_random_rstep(min_val=0.0, max_val=360.0, step=45.0, context=None):
    val = _pyxis_random_r(min_val, max_val, step, context)
    st = _eval_num(step, context, 1.0)
    if st > 0 and float(st).is_integer():
        return int(val)
    return val

def math_random_master(context, mode="R", min_val=0.0, max_val=100.0, step=1.0, options="", counter="", total=1, output_slot_index=0, **kwargs):
    m = str(kwargs.get("mode", mode or "R")).strip()
    mn = kwargs.get("min", kwargs.get("min_val", min_val))
    mx = kwargs.get("max", kwargs.get("max_val", max_val))
    st = kwargs.get("step", step)
    opt = kwargs.get("options", options)
    cnt = kwargs.get("counter", counter)

    def _gen_single():
        if m == "R":
            return _pyxis_random_r(mn, mx, st, context)
        elif m == "Rs":
            return _pyxis_random_rs(mn, mx, st, context)
        elif m == "Rr":
            return _pyxis_random_rr(context, mn, mx, st)
        elif m == "Rc":
            return _pyxis_random_rc(mn, mx, st, context)
        elif m == "Rd":
            return _pyxis_random_rd(mn, mx, st, context)
        elif m == "Rm":
            return _pyxis_random_rm(mn, mx, st, context)
        elif m == "Rds":
            return _pyxis_random_rds(mn, mx, st, context)
        elif m == "Rcs":
            return _pyxis_random_rcs(mn, mx, st, context)
        elif m == "Rms":
            return _pyxis_random_rms(mn, mx, st, context)
        elif m == "Re":
            return _pyxis_random_re(opt, context)
        elif m == "Rfake":
            return _pyxis_random_rfake(context, mn, mx, cnt)
        elif m in ("Rcolor", "Rcol"):
            return _pyxis_random_rcolor(mn, mx, context)
        elif m == "R2d":
            return _pyxis_random_r2d(mn, mx, st, context)
        elif m == "Rbool":
            return _pyxis_random_rbool(mn, context)
        elif m == "Rstep":
            return _pyxis_random_rstep(mn, mx, st, context)
        else:
            return _pyxis_random_r(mn, mx, st, context)

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

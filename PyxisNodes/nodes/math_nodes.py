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

# PyxisNodes/nodes/math_nodes.py
"""Nodo Math Maestro Unificado con soporte para 5 categorías y 35 sub-operaciones."""

import math
import random
from decorators import pyxis_node, NODE_REGISTRY


def _eval_num(val, context=None, default=0.0):
    if val is None:
        return float(default)
    if isinstance(val, (int, float)):
        return float(val)
    
    s_val = str(val).strip()
    if not s_val:
        return float(default)
    
    s_val = s_val.replace(',', '.')
    
    try:
        return float(s_val)
    except (ValueError, TypeError):
        pass
    
    ctx_dict = dict(context or {})
    if s_val in ctx_dict:
        try:
            return float(ctx_dict[s_val])
        except (ValueError, TypeError):
            pass
            
    if '.' in s_val:
        try:
            parts = s_val.split('.')
            if parts[0] in ctx_dict:
                curr = ctx_dict[parts[0]]
                for p in parts[1:]:
                    if isinstance(curr, dict):
                        curr = curr.get(p)
                    else:
                        curr = getattr(curr, p, None)
                if curr is not None:
                    return float(curr)
        except Exception:
            pass

    try:
        eval_scope = {}
        for k, v in ctx_dict.items():
            if isinstance(k, str) and k.isidentifier():
                eval_scope[k] = v
        if "syl" in eval_scope and "sili" not in eval_scope:
            eval_scope["sili"] = eval_scope["syl"]
        
        math_fns = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
        eval_scope.update(math_fns)
        eval_scope.update({"abs": abs, "min": min, "max": max, "round": round, "int": int, "float": float})
        
        s_eval = s_val.replace("^", "**")
        res = eval(s_eval, {"__builtins__": None}, eval_scope)
        return float(res)
    except Exception:
        pass

    return float(default)


def eval_math_node(context=None, **kwargs):
    """Manejador unificado para el Nodo Maestro Math."""
    categoria = str(kwargs.get("categoria", "Basico")).strip()
    operacion = str(kwargs.get("operacion", "Suma")).strip()
    
    ctx = context or {}

    def get_num(key, default=0.0):
        val = kwargs.get(key)
        if val is None:
            val = kwargs.get(key.lower())
        return _eval_num(val, ctx, default)

    # 1. CATEGORÍA: BASICO
    if categoria in ("Basico", "Básico", "basico", "básico"):
        a = get_num("A", 0.0)
        b = get_num("B", 0.0)

        op_clean = operacion.strip().lower().replace("ó", "o").replace("á", "a").replace("é", "e").replace("í", "i").replace("ú", "u")
        
        if op_clean in ("suma", "add", "+"):
            return a + b
        elif op_clean in ("resta", "sub", "-"):
            return a - b
        elif op_clean in ("multiplicacion", "mul", "*"):
            return a * b
        elif op_clean in ("division", "div", "/"):
            return a / b if b != 0 else 0.0
        elif op_clean in ("modulo", "mod", "%"):
            return a % b if b != 0 else 0.0
        elif op_clean in ("potencia", "pow", "^"):
            try:
                return math.pow(a, b)
            except Exception:
                return 0.0
        elif op_clean in ("absoluto", "abs"):
            return abs(a)
        elif op_clean in ("negativo", "neg"):
            return -a
        elif op_clean in ("redondear", "round"):
            return float(round(a))
        elif op_clean in ("piso", "floor"):
            return float(math.floor(a))
        elif op_clean in ("techo", "ceil"):
            return float(math.ceil(a))
        else:
            return a + b

    # 2. CATEGORÍA: TRIGONO
    elif categoria == "Trigono":
        a = get_num("A", get_num("Grados", get_num("Radianes", 0.0)))
        
        if operacion in ("Seno", "sin"):
            return math.sin(math.radians(a))
        elif operacion in ("Coseno", "cos"):
            return math.cos(math.radians(a))
        elif operacion in ("Tangente", "tan"):
            return math.tan(math.radians(a))
        elif operacion in ("ArcSeno", "asin"):
            clamped = max(-1.0, min(1.0, a))
            return math.degrees(math.asin(clamped))
        elif operacion in ("ArcCoseno", "acos"):
            clamped = max(-1.0, min(1.0, a))
            return math.degrees(math.acos(clamped))
        elif operacion in ("ArcTangente", "atan"):
            return math.degrees(math.atan(a))
        elif operacion in ("ArcTangente2", "atan2"):
            y = get_num("Y", get_num("A", 0.0))
            x = get_num("X", get_num("B", 1.0))
            return math.degrees(math.atan2(y, x))
        elif operacion in ("Radianes", "rad"):
            return math.radians(a)
        elif operacion in ("Grados", "deg"):
            return math.degrees(a)
        else:
            return math.sin(math.radians(a))

    # 3. CATEGORÍA: EASING
    elif categoria == "Easing":
        raw_t = get_num("t", get_num("A", 0.0))
        t = max(0.0, min(1.0, raw_t))
        
        if operacion in ("EaseIn", "ease_in"):
            return t * t
        elif operacion in ("EaseOut", "ease_out"):
            return 1.0 - (1.0 - t) * (1.0 - t)
        elif operacion in ("EaseInOut", "ease_in_out"):
            if t < 0.5:
                return 2.0 * t * t
            else:
                return 1.0 - math.pow(-2.0 * t + 2.0, 2) / 2.0
        elif operacion in ("CubicIn", "cubic_in"):
            return t * t * t
        elif operacion in ("CubicOut", "cubic_out"):
            return 1.0 - (1.0 - t) ** 3
        elif operacion in ("Exponencial", "expo"):
            if t <= 0.0:
                return 0.0
            if t >= 1.0:
                return 1.0
            return math.pow(2.0, 10.0 * (t - 1.0))
        elif operacion in ("Elastico", "elastic"):
            if t <= 0.0:
                return 0.0
            if t >= 1.0:
                return 1.0
            c4 = (2.0 * math.pi) / 3.0
            return -math.pow(2.0, 10.0 * t - 10.0) * math.sin((t * 10.0 - 10.75) * c4)
        elif operacion in ("Rebote", "bounce"):
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
        elif operacion in ("Retroceso", "back"):
            c1 = 1.70158
            c3 = c1 + 1.0
            return c3 * (t ** 3) - c1 * (t ** 2)
        else:
            return t * t

    # 4. CATEGORÍA: ONDAS
    elif categoria == "Ondas":
        t = get_num("t", 0.0)
        frec = get_num("Frecuencia", get_num("freq", 1.0))
        amp = get_num("Amplitud", get_num("amp", 1.0))
        offset = get_num("Offset", 0.0)
        
        if operacion in ("Seno", "sine"):
            return amp * math.sin(2.0 * math.pi * frec * t) + offset
        elif operacion in ("Cuadrada", "square"):
            val = math.sin(2.0 * math.pi * frec * t)
            return (amp if val >= 0.0 else -amp) + offset
        elif operacion in ("Triangulo", "triangle"):
            phase = (t * frec) % 1.0
            val = 2.0 * abs(2.0 * phase - 1.0) - 1.0
            return amp * val + offset
        elif operacion in ("DienteSierra", "sawtooth"):
            phase = (t * frec) % 1.0
            val = 2.0 * phase - 1.0
            return amp * val + offset
        else:
            return amp * math.sin(2.0 * math.pi * frec * t) + offset

    # 5. CATEGORÍA: UTILIDADES
    elif categoria == "Utilidades":
        if operacion == "Clamp":
            val = get_num("Value", get_num("Valor", get_num("A", 0.0)))
            mn = get_num("Min", 0.0)
            mx = get_num("Max", 1.0)
            low = min(mn, mx)
            high = max(mn, mx)
            return max(low, min(high, val))
        elif operacion == "Lerp":
            a = get_num("A", 0.0)
            b = get_num("B", 1.0)
            t = get_num("t", 0.5)
            t_norm = max(0.0, min(1.0, t))
            return a + (b - a) * t_norm
        elif operacion in ("Minimo", "min"):
            a = get_num("A", 0.0)
            b = get_num("B", 0.0)
            return min(a, b)
        elif operacion in ("Maximo", "max"):
            a = get_num("A", 0.0)
            b = get_num("B", 0.0)
            return max(a, b)
        elif operacion in ("Aleatorio", "random"):
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
        elif operacion in ("MapearRango", "map_range"):
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


# Registros en NODE_REGISTRY
NODE_REGISTRY["Math"] = eval_math_node


# -----------------------------------------------------------------------------
# HELPER UTILITIES: RANDOM (RESTPYXISDO DE BETA 2), POLARES Y BEZIER
# -----------------------------------------------------------------------------
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

def math_random_master(context, modo="R", min_val=0.0, max_val=100.0, step=1.0, options="", counter=""):
    m = str(modo or "R").strip()
    if m == "R":
        return _pyxis_random_r(min_val, max_val, step, context)
    elif m == "Rs":
        return _pyxis_random_rs(min_val, max_val, step, context)
    elif m == "Rr":
        return _pyxis_random_rr(context, min_val, max_val, step)
    elif m == "Rc":
        return _pyxis_random_rc(min_val, max_val, step, context)
    elif m == "Rd":
        return _pyxis_random_rd(min_val, max_val, step, context)
    elif m == "Rm":
        return _pyxis_random_rm(min_val, max_val, step, context)
    elif m == "Rds":
        return _pyxis_random_rds(min_val, max_val, step, context)
    elif m == "Rcs":
        return _pyxis_random_rcs(min_val, max_val, step, context)
    elif m == "Rms":
        return _pyxis_random_rms(min_val, max_val, step, context)
    elif m == "Re":
        return _pyxis_random_re(options, context)
    elif m == "Rfake":
        return _pyxis_random_rfake(context, min_val, max_val, counter)
    elif m in ("Rcolor", "Rcol"):
        return _pyxis_random_rcolor(min_val, max_val, context)
    elif m == "R2d":
        return _pyxis_random_r2d(min_val, max_val, step, context)
    elif m == "Rbool":
        return _pyxis_random_rbool(min_val, context)
    elif m == "Rstep":
        return _pyxis_random_rstep(min_val, max_val, step, context)
    else:
        return _pyxis_random_r(min_val, max_val, step, context)

from decorators import NODE_REGISTRY
NODE_REGISTRY["MultiRandom"] = math_random_master


def math_polar(context, x=0, y=0, angle=0, radius=0):
    from node_engine import _eval_num_expr
    x0 = _eval_num_expr(x, context, 0.0)
    y0 = _eval_num_expr(y, context, 0.0)
    ang = _eval_num_expr(angle, context, 0.0)
    r = _eval_num_expr(radius, context, 0.0)

    rad = math.radians(ang)
    res_x = x0 + r * math.cos(rad)
    res_y = y0 + r * math.sin(rad)

    fmt_x = int(res_x) if res_x.is_integer() else round(res_x, 2)
    fmt_y = int(res_y) if res_y.is_integer() else round(res_y, 2)

    return f"\\pos({fmt_x},{fmt_y})"


def math_bezier_node(context, p0="0,0", p1="50,100", p2="150,100", p3="200,0", t=0.5, mode="Cúbica 2D"):
    from node_engine import _eval_num_expr
    ft = float(_eval_num_expr(t, context, 0.5))
    ft = max(0.0, min(1.0, ft))

    def parse_pt(pt_str, default=(0.0, 0.0)):
        try:
            parts = str(pt_str).split(",")
            return float(_eval_num_expr(parts[0], context, default[0])), float(_eval_num_expr(parts[1], context, default[1]))
        except:
            return default

    x0, y0 = parse_pt(p0, (0.0, 0.0))
    x1, y1 = parse_pt(p1, (50.0, 100.0))
    x2, y2 = parse_pt(p2, (150.0, 100.0))
    x3, y3 = parse_pt(p3, (200.0, 0.0))

    u = 1.0 - ft
    bx = (u**3)*x0 + 3*(u**2)*ft*x1 + 3*u*(ft**2)*x2 + (ft**3)*x3
    by = (u**3)*y0 + 3*(u**2)*ft*y1 + 3*u*(ft**2)*y2 + (ft**3)*y3

    fmt_x = round(bx, 2)
    fmt_y = round(by, 2)

    m = str(mode).strip().lower()
    if m in ("spline", "assdraw", "trazado assdraw", "b"):
        return f"b {round(x1,2)} {round(y1,2)} {round(x2,2)} {round(y2,2)} {round(x3,2)} {round(y3,2)}"

    return f"\\pos({fmt_x},{fmt_y})"

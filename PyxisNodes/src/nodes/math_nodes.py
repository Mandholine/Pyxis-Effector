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
Architectural Role: Mathematical Computation, Waveform Modulation, Stochastic Dispatch, and Geometric Kinematics Engine.

This module provides the central numeric evaluation infrastructure for Pyxis Effector:
    - Master Math Evaluation (`eval_math_node`): Unifies arithmetic, modular, power,
      trigonometric, easing curve, periodic waveform, and clamping/range-mapping algorithms under `Basics/Math`.
    - Easing Formulas: Robert Penner standard animation curves (quad, cubic, exponential, elastic, bounce, back).
    - Periodic Oscillators: Continuous wave modulators (sine, square, triangle, sawtooth) with frequency, amplitude, and DC offset.
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
    - node_validator.GraphValidator: Validates mathematical expressions, easing names, and random signatures.
"""

import math
import random
import re
from decorators import pyxis_node, NODE_REGISTRY


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
    """
    Unified canonical execution dispatcher for the `Basics/Math` node.

    Dispatches calculations based on `category` and `operation`:
        - `Basic`: Arithmetic (+, -, *, /, %, ^), absolute, negation, and rounding (round, floor, ceil).
        - `Trigonometry`: Angular trigonometric ratios (sin, cos, tan, asin, acos, atan, atan2, rad, deg).
        - `Easing`: Normalized Penner curves (easein, easeout, easeinout, cubic, expo, elastic, bounce, back).
        - `Waves`: Periodic oscillators (sine, square, triangle, sawtooth) with frequency, amplitude, and offset.
        - `Utilities`: Numeric bounds (clamp, min, max), linear interpolation (lerp), random, and map range.

    Args:
        context (dict | None): Active execution context.
        **kwargs: Node parameters, input slots (A, B, t, freq, amp, etc.), and mode selectors.

    Returns:
        float: Computed scalar numeric result.
    """
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
    or custom index variables such as 'i', 'j', 'syl_i').

    Args:
        context (dict): Runtime execution context supplied by the DAG evaluation engine.
        iterator_name (str): Identifier of the target iterator or semantic unit.

    Returns:
        str | None: Formatted canonical identifier (e.g. 'line_0_syl_2') or None if invalid.
    """
    if not iterator_name or not str(iterator_name).strip():
        return None
    iter_key = str(iterator_name).strip()
    ctx = context or {}

    l = ctx.get("line")
    l_id = getattr(l, "i", getattr(l, "idx", id(l) if l else 0))

    if iter_key == "global":
        return "global"
    elif iter_key == "line":
        return f"line_{l_id}"
    elif iter_key == "syl":
        s = ctx.get("syl")
        s_id = getattr(s, "i", getattr(s, "syl_i", id(s) if s else 0))
        return f"line_{l_id}_syl_{s_id}"
    elif iter_key == "char":
        c = ctx.get("char")
        c_id = getattr(c, "i", getattr(c, "char_i", id(c) if c else 0))
        return f"line_{l_id}_char_{c_id}"
    elif iter_key == "word":
        w = ctx.get("word")
        w_id = getattr(w, "i", getattr(w, "word_i", id(w) if w else 0))
        return f"line_{l_id}_word_{w_id}"
    else:
        val = ctx.get(iter_key)
        if val is None:
            u = ctx.get("active_unit") or ctx.get("unit") or ctx.get("syl") or ctx.get("char") or ctx.get("word") or ctx.get("line")
            if u is not None and hasattr(u, iter_key):
                val = getattr(u, iter_key)
        if val is None:
            val = 0
        return f"line_{l_id}_{iter_key}_{val}"


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
        kwargs_repr = tuple(sorted((k, str(v)) for k, v in kwargs.items() if k not in ("by", "iter", "iterator")))
        cache_key = (self._iterator_name, scope_key, mode_name, args_repr, kwargs_repr)

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

        clean_kwargs = {k: v for k, v in kwargs.items() if k not in ("by", "iter", "iterator", "min_val", "min", "max_val", "max", "step")}
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


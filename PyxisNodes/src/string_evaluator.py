r"""
Pyxis Nodes Engine - String Template & Expression Evaluator
Modular evaluator for strings, expressions, and composite tags.

Supports:
1. Direct evaluation inside ASS tag parentheses: \pos(syl.center + 10, syl.middle), \frz(j * 15), \t(0, 10f, \fscxy(150))
2. Isolated parenthesized expressions and ternaries: (\blur3 if i == 1 else \blur0), (Colores())
3. Unit shortcuts: 10f (frames to ms), 1.5r (resolution ratio scaling)
4. Composite tag expansion (Dark Tags): \fscxy, \faxy, \frxyz, \xybord, \xyshad, \bs, \134c, \13c, \14c, \34c, \134a, \13a, \14a, \34a
5. Style restoration tags: \fscxy~, \1c~, \134c~, \bs~, etc.
6. Stochastic tags: \1cR(), \frzR(-30, 30), \fscxyR(120, 150), etc.
"""

from __future__ import annotations

import re
import math
import random
from collections import OrderedDict
from typing import Any, Dict, Optional

_AST_EXPR_CACHE: OrderedDict[str, Any] = OrderedDict()
_MAX_AST_EXPR_CACHE = 2048

def clear_string_eval_cache():
    """Clears cached compiled string evaluation expressions."""
    _AST_EXPR_CACHE.clear()
_STATIC_STRING_GLOBALS: Optional[Dict[str, Any]] = None


def _get_eval_globals() -> Dict[str, Any]:
    """
    Constructs and caches the secure global execution environment for string template evaluation.

    Provides a sandboxed namespace containing:
    1. Safe Python builtins (min, max, abs, round, math, etc.).
    2. ASS color and alpha generators and sanitizers (ass_color, ass_alpha, random_color, random_alpha).
    3. Kinematics, trajectory, and deformation helpers (move_tag, move_text).
    4. Stochastic and deterministic PRNG generators (R, Rs, Rc, Rd, Rm, Rstep, R2d, Rbool, Rcolor, etc.).
    5. Canonical ASS tag wrappers and easing curves (_pyxis_pos, _pyxis_move, ease_in, sine_wave, etc.).
    6. Acoustic telemetry and FFT functions (audio_rms, audio_peak, audio_band, audio_fft).
    7. Geometric shape presets catalog (shape.*, shape_circle, shape_star, resolve_shape).

    Returns:
        Dict[str, Any]: Static immutable shared dictionary reused across successive evaluations.
    """
    global _STATIC_STRING_GLOBALS
    if _STATIC_STRING_GLOBALS is not None:
        return _STATIC_STRING_GLOBALS

    import math
    safe_builtins = {
        "min": min, "max": max, "abs": abs, "round": round,
        "int": int, "float": float, "pow": pow, "sum": sum,
        "len": len, "str": str, "bool": bool, "range": range,
        "list": list, "dict": dict, "tuple": tuple, "set": set,
        "true": True, "false": False, "null": None, "nil": None
    }
    g: Dict[str, Any] = {"math": math, "__builtins__": safe_builtins}
    for k, v in safe_builtins.items():
        g[k] = v
    for fn in ("sin", "cos", "tan", "sqrt", "ceil", "floor", "atan2", "degrees", "radians", "hypot", "log", "exp", "pi"):
        if hasattr(math, fn):
            g[fn] = getattr(math, fn)

    def ass_color(r: int, g: int, b: int) -> str:
        r_c = max(0, min(255, int(r)))
        g_c = max(0, min(255, int(g)))
        b_c = max(0, min(255, int(b)))
        return f"&H{b_c:02X}{g_c:02X}{r_c:02X}&"

    def ass_alpha(a: Any) -> str:
        return _format_ass_alpha(a)

    def random_color() -> str:
        return f"&H{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}&"

    def random_alpha() -> str:
        return f"&H{random.randint(0, 255):02X}&"

    def clamp(val: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, val))

    g["ass_color"] = ass_color
    g["ass_alpha"] = ass_alpha
    g["color_random"] = random_color
    g["random_color"] = random_color
    g["alpha_random"] = random_alpha
    g["random_alpha"] = random_alpha
    g["clamp"] = clamp

    try:
        from nodes.tag_nodes import move_tag_node
        from nodes.text_nodes import move_text_node
        g["move_tag"] = move_tag_node
        g["move_text"] = move_text_node
    except ImportError:
        pass

    try:
        from nodes.math_nodes import math_random_master, PyxisByDispatcher
        g["math_random_master"] = math_random_master
        g["PyxisByDispatcher"] = PyxisByDispatcher
        g["R"] = math_random_master
        g["Rs"] = math_random_master
        g["Rc"] = math_random_master
        g["Rd"] = math_random_master
        g["Rm"] = math_random_master
        g["Rds"] = math_random_master
        g["Rcs"] = math_random_master
        g["Rms"] = math_random_master
        g["Rr"] = math_random_master
        g["Rstep"] = math_random_master
        g["R2d"] = math_random_master
        g["Rbool"] = math_random_master
        g["Rcolor"] = math_random_master
        g["Re"] = math_random_master
        g["Rfake"] = math_random_master
        g["rand"] = math_random_master
    except ImportError:
        def simple_r(min_v=0, max_v=100, step=1):
            return random.randint(int(min_v), int(max_v))
        g["R"] = simple_r
        g["Rs"] = simple_r
        g["Rc"] = simple_r
        g["rand"] = simple_r

    try:
        from nodes.code_nodes import (
            _pyxis_pos, _pyxis_move, _pyxis_org, _pyxis_fad, _pyxis_fade,
            _pyxis_clip, _pyxis_iclip, _pyxis_c1, _pyxis_c2, _pyxis_c3, _pyxis_c4,
            _pyxis_a1, _pyxis_a2, _pyxis_a3, _pyxis_a4, _pyxis_alpha, _pyxis_trans,
            _pyxis_fscx, _pyxis_fscy, _pyxis_fscxy, _pyxis_frz, _pyxis_frx, _pyxis_fry,
            _pyxis_fax, _pyxis_fay, _pyxis_bord, _pyxis_shad, _pyxis_blur, _pyxis_an,
            _pyxis_ass_color, _pyxis_ass_alpha, _pyxis_random_color, _pyxis_random_alpha,
            _pyxis_clamp, _pyxis_lerp, _pyxis_map_range, _pyxis_ease_in, _pyxis_ease_out,
            _pyxis_ease_in_out, _pyxis_cubic_in, _pyxis_cubic_out, _pyxis_elastic,
            _pyxis_bounce, _pyxis_back, _pyxis_sine_wave, _pyxis_square_wave,
            _pyxis_triangle_wave, _pyxis_sawtooth_wave, _pyxis_polar, _pyxis_bezier,
            _pyxis_ipol, _pyxis_time_to_frame, _pyxis_duration, _pyxis_parse_ass_time,
            _pyxis_format_ass_time, _pyxis_strip_tags, _pyxis_kana
        )
        g.update({
            "pos": _pyxis_pos, "move": _pyxis_move, "org": _pyxis_org, "fad": _pyxis_fad, "fade": _pyxis_fade,
            "clip": _pyxis_clip, "iclip": _pyxis_iclip, "c1": _pyxis_c1, "c2": _pyxis_c2, "c3": _pyxis_c3, "c4": _pyxis_c4,
            "color_1": _pyxis_c1, "color_2": _pyxis_c2, "color_3": _pyxis_c3, "color_4": _pyxis_c4,
            "a1": _pyxis_a1, "a2": _pyxis_a2, "a3": _pyxis_a3, "a4": _pyxis_a4, "alpha": _pyxis_alpha,
            "trans": _pyxis_trans, "fscx": _pyxis_fscx, "fscy": _pyxis_fscy, "fscxy": _pyxis_fscxy,
            "frz": _pyxis_frz, "frx": _pyxis_frx, "fry": _pyxis_fry, "fax": _pyxis_fax, "fay": _pyxis_fay,
            "bord": _pyxis_bord, "shad": _pyxis_shad, "blur": _pyxis_blur, "an": _pyxis_an,
            "ass_color": _pyxis_ass_color, "ass_alpha": _pyxis_ass_alpha,
            "random_color": _pyxis_random_color, "random_alpha": _pyxis_random_alpha,
            "clamp": _pyxis_clamp, "lerp": _pyxis_lerp, "map_range": _pyxis_map_range, "map_value": _pyxis_map_range,
            "ease_in": _pyxis_ease_in, "ease_out": _pyxis_ease_out, "ease_in_out": _pyxis_ease_in_out,
            "cubic_in": _pyxis_cubic_in, "cubic_out": _pyxis_cubic_out, "elastic": _pyxis_elastic,
            "bounce": _pyxis_bounce, "back": _pyxis_back,
            "sine_wave": _pyxis_sine_wave, "square_wave": _pyxis_square_wave,
            "triangle_wave": _pyxis_triangle_wave, "sawtooth_wave": _pyxis_sawtooth_wave,
            "polar": _pyxis_polar, "bezier": _pyxis_bezier, "ipol": _pyxis_ipol,
            "time_to_frame": _pyxis_time_to_frame, "duration": _pyxis_duration,
            "parse_ass_time": _pyxis_parse_ass_time, "format_ass_time": _pyxis_format_ass_time,
            "strip_tags": _pyxis_strip_tags, "kana": _pyxis_kana
        })
    except ImportError:
        pass

    try:
        from nodes.audio_nodes import audio_rms, audio_peak, audio_band, audio_fft
        g["audio_rms"] = audio_rms
        g["audio_peak"] = audio_peak
        g["audio_band"] = audio_band
        g["audio_fft"] = audio_fft
    except ImportError:
        pass

    try:
        from node_engine import ShapePresetsNamespace
        g["shape"] = ShapePresetsNamespace()
    except ImportError:
        pass

    try:
        from nodes.shape_nodes import (
            shape_circle, shape_square, shape_rectangle, shape_triangle, shape_rhombus,
            shape_rounded_corners, shape_pentagon, shape_hexagon, shape_octagon,
            shape_star, shape_heart, resolve_shape_value
        )
        g.update({
            "shape_circle": lambda ctx=None: shape_circle(ctx),
            "shape_square": lambda ctx=None: shape_square(ctx),
            "shape_rectangle": lambda ctx=None: shape_rectangle(ctx),
            "shape_triangle": lambda ctx=None: shape_triangle(ctx),
            "shape_rhombus": lambda ctx=None: shape_rhombus(ctx),
            "shape_rounded_corners": lambda ctx=None: shape_rounded_corners(ctx),
            "shape_pentagon": lambda ctx=None: shape_pentagon(ctx),
            "shape_hexagon": lambda ctx=None: shape_hexagon(ctx),
            "shape_octagon": lambda ctx=None: shape_octagon(ctx),
            "shape_star": lambda ctx=None: shape_star(ctx),
            "shape_heart": lambda ctx=None: shape_heart(ctx),
            "resolve_shape": lambda name, ctx=None: resolve_shape_value(name, ctx),
        })
    except ImportError:
        pass

    try:
        from registry import NODE_REGISTRY
        for fn_name, fn in NODE_REGISTRY.items():
            g.setdefault(fn_name, fn)
    except ImportError:
        pass

    _STATIC_STRING_GLOBALS = g
    return _STATIC_STRING_GLOBALS


def _format_ass_alpha(val: Any) -> str:
    """
    Formats an alpha value into canonical ASS alpha hex &HXX& (00 to FF).

    Supports multiple input representations:
    - Integers and floats (0 to 255), rounded and clamped.
    - Full color hex strings (&HAABBGGRR& or AABBGGRR), extracting the alpha byte AA.
    - Short hex strings (&HAA& or HAA).
    - Decimal string representations.

    Args:
        val: Source alpha value (numeric or string).

    Returns:
        str: Canonical '&HXX&' formatted string (uppercase with 2-digit padding). Returns '&H00&' if None or empty.
    """
    if val is None:
        return "&H00&"
    if isinstance(val, (int, float)):
        a_c = max(0, min(255, int(round(float(val)))))
        return f"&H{a_c:02X}&"
    s = str(val).strip()
    if not s:
        return "&H00&"

    m_color = re.match(r'^&?[hH]?([0-9a-fA-F]{2})[0-9a-fA-F]{6}&?$', s)
    if m_color:
        return f"&H{m_color.group(1).upper()}&"

    m_hex = re.match(r'^&?[hH]([0-9a-fA-F]{1,2})&?$', s)
    if m_hex:
        return f"&H{m_hex.group(1).upper().zfill(2)}&"

    try:
        f_val = float(s)
        a_c = max(0, min(255, int(round(f_val))))
        return f"&H{a_c:02X}&"
    except ValueError:
        pass

    m_raw_hex = re.match(r'^[0-9a-fA-F]{1,2}$', s)
    if m_raw_hex:
        return f"&H{m_raw_hex.group(0).upper().zfill(2)}&"

    return s


def _clean_ass_color(col: Any) -> str:
    """
    Normalises and formats any color representation into canonical ASS color hex &HBBGGRR&.

    Accepts:
    - Web hex strings (#RRGGBB or #RGB), transformed to ASS BGR order.
    - Direct integer values (masked with 0xFFFFFF).
    - RGB tuples or lists (r, g, b).
    - Pre-existing ASS hex strings with or without ampersands (&HBBGGRR&).

    Args:
        col: Color representation in numeric, RGB tuple, or text format.

    Returns:
        str: Formatted string strictly matching '&HBBGGRR&' in uppercase BGR order.
    """
    if col is None:
        return "&H00FFFFFF&"
    if isinstance(col, (int, float)):
        return f"&H{int(col) & 0xFFFFFF:06X}&"
    if isinstance(col, (tuple, list)) and len(col) >= 3:
        try:
            from utils import rgb_to_ass_color
            return rgb_to_ass_color(col[0], col[1], col[2])
        except Exception:
            pass
    s = str(col).strip()
    if not s:
        return "&H00FFFFFF&"
    if s.startswith("#"):
        try:
            from utils import parse_color_to_rgb, rgb_to_ass_color
            return rgb_to_ass_color(*parse_color_to_rgb(s))
        except ImportError:
            h = s[1:]
            if len(h) == 3 and re.match(r'^[0-9a-fA-F]{3}$', h):
                h = "".join(c * 2 for c in h)
            if len(h) >= 6 and re.match(r'^[0-9a-fA-F]{6}', h):
                r, g, b = h[0:2], h[2:4], h[4:6]
                return f"&H{b.upper()}{g.upper()}{r.upper()}&"
    if s.isdigit():
        return f"&H{int(s) & 0xFFFFFF:06X}&"
    m = re.findall(r'[0-9a-fA-F]{2}', s)
    if len(m) >= 4:
        return f"&H{''.join(m[-3:]).upper()}&"
    elif len(m) == 3:
        return f"&H{''.join(m).upper()}&"
    m_hex = re.search(r'([0-9a-fA-F]{6})', s)
    if m_hex:
        return f"&H{m_hex.group(1).upper()}&"
    return s


def _fmt_num(val: Any) -> str:
    """
    Formats integers and floating-point numbers cleanly for ASS tag insertion.

    Serialisation rules:
    - Booleans are converted to '1' or '0'.
    - Integers are represented without decimals ('10').
    - Floats with integer values are stripped of decimal points ('10.0' -> '10').
    - Floats with fractional parts are rounded up to 3 decimal places without trailing zeros ('10.500' -> '10.5').

    Args:
        val: Numeric value to format.

    Returns:
        str: Clean string representation optimised for libass rendering.
    """
    if val is None:
        return ""
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return f"{val:.3f}".rstrip('0').rstrip('.')
    return str(val)


def _prepare_eval_locals(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Constructs and populates the local evaluation dictionary with DAG runtime context.

    Binds all canonical context entities, proxies, and iterator namespaces:
    1. Hierarchical text entities: 'syl', 'char', 'word', 'line'/'l' (wrapped in AttrDict for dot-access).
    2. Loop counters and bounds: 'j' (default 1), 'maxj'/'maxloop' (default fx_n or 1).
    3. Multidimensional subloop iterators: 's_i'/'slice_i', 'd_i'/'divide_i', 'b_i'/'ring_i',
       'a_i'/'array_i', 'm_i'/'multi_i', 'p_i'/'particle_i', 'tp_i'/'text_p_i', 'ip_i'/'img_p_i',
       'c_i'/'clip_i', 'an_i'/'anim_i', and their respective '*_n' and '*_max' counts.
    4. Relative relational proxies: 'prev' and 'next' (wrapped in AdjacentUnitProxy), with boolean flags
       'is_first', 'is_last', 'has_prev', 'has_next'.
    5. Vector ink metrics: 'ink' (bound to InkNamespace).
    6. Particle and transformation state: 'fx' (bound to FxContext).
    7. Persistent cross-iteration memory: 'remember(key, val, cond)' and 'recall(key, default)'.
    8. Dynamic time modifiers: 'li', 'lo', 'm1', 'm2', 'l1', 'l2' (PyxisTimeModifier).
    9. Inter-line synchronisation helper: 'sync' (PyxisSyncHelper) and 'calculate_sync_gap'.
    10. Stochastic dispatchers: 'by' (PyxisByDispatcher) and iterator-coupled PRNG callers ('R', 'Rs', 'Rc', etc.).

    Args:
        context: Raw runtime dictionary supplied by the active DAG graph iteration.

    Returns:
        Dict[str, Any]: Fully initialised locals dictionary ready for AST evaluation.
    """
    eval_globals = _get_eval_globals()
    eval_locals: Dict[str, Any] = dict(context) if isinstance(context, dict) else {}
    eval_locals["context"] = eval_locals

    try:
        from node_engine import AttrDict, FxContext
    except ImportError:
        class AttrDict(dict):
            def __getattr__(self, name):
                if name in self:
                    val = self[name]
                    return AttrDict(val) if isinstance(val, dict) else val
                raise AttributeError(f"'dict' object has no attribute '{name}'")
            def __setattr__(self, name, value):
                self[name] = value
        class FxContext:
            def __init__(self, ctx): self._ctx = ctx
            def __getattr__(self, name): return self._ctx.get(name, 0.0)

    for k, v in list(eval_locals.items()):
        if isinstance(v, dict) and not isinstance(v, AttrDict):
            eval_locals[k] = AttrDict(v)

    eval_locals["audio_rms"] = lambda *args, **kwargs: eval_globals.get("audio_rms", lambda *a, **kw: 0.0)(*args, context=context, **kwargs)
    eval_locals["audio_peak"] = lambda *args, **kwargs: eval_globals.get("audio_peak", lambda *a, **kw: 0.0)(*args, context=context, **kwargs)
    eval_locals["audio_band"] = lambda *args, **kwargs: eval_globals.get("audio_band", lambda *a, **kw: 0.0)(*args, context=context, **kwargs)
    eval_locals["audio_fft"] = lambda *args, **kwargs: eval_globals.get("audio_fft", lambda *a, **kw: 0.0)(*args, context=context, **kwargs)

    by_cls = eval_globals.get("PyxisByDispatcher")
    if by_cls:
        eval_locals["by"] = by_cls(context)

    def _make_eval_rnd_caller(mode_name, default_step=None):
        def _caller(*args, **kwargs):
            by_val = kwargs.get("by", kwargs.get("iter", kwargs.get("iterator", None)))
            if len(args) == 0:
                mn = kwargs.get("min_val", kwargs.get("min", None))
                mx = kwargs.get("max_val", kwargs.get("max", None))
                st = kwargs.get("step", default_step)
            elif len(args) == 1:
                mn = args[0]
                mx = None
                st = kwargs.get("step", default_step)
            elif len(args) == 2:
                mn = args[0]
                mx = args[1]
                st = kwargs.get("step", default_step)
            else:
                mn = args[0]
                mx = args[1]
                st = args[2]
            fn = eval_globals.get("math_random_master", eval_globals.get(mode_name, eval_globals.get("R")))
            if callable(fn):
                clean_kwargs = {k: v for k, v in kwargs.items() if k not in ("min_val", "min", "max_val", "max", "step", "by", "iter", "iterator")}
                return fn(context, mode=mode_name, min_val=mn, max_val=mx, step=st, by=by_val, **clean_kwargs)
            return 0
        return _caller

    eval_locals["R"] = _make_eval_rnd_caller("R", 1.0)
    eval_locals["Rs"] = _make_eval_rnd_caller("Rs", 1.0)
    eval_locals["Rc"] = _make_eval_rnd_caller("Rc", 0.01)
    eval_locals["Rd"] = _make_eval_rnd_caller("Rd", 0.1)
    eval_locals["Rm"] = _make_eval_rnd_caller("Rm", 0.001)
    eval_locals["Rds"] = _make_eval_rnd_caller("Rds", 0.1)
    eval_locals["Rcs"] = _make_eval_rnd_caller("Rcs", 0.01)
    eval_locals["Rms"] = _make_eval_rnd_caller("Rms", 0.001)
    eval_locals["Rr"] = _make_eval_rnd_caller("Rr", 1.0)
    eval_locals["Rstep"] = _make_eval_rnd_caller("Rstep", 45.0)
    eval_locals["R2d"] = _make_eval_rnd_caller("R2d", 1.0)
    eval_locals["Rbool"] = lambda prob=50.0, **kwargs: eval_globals.get("math_random_master", lambda *a, **kw: True)(context, mode="Rbool", min_val=prob, **kwargs)
    eval_locals["Rcolor"] = lambda c1="#FFFFFF", c2="#000000", **kwargs: eval_globals.get("math_random_master", lambda *a, **kw: "#FFFFFF")(context, mode="Rcolor", min_val=c1, max_val=c2, **kwargs)
    eval_locals["Re"] = lambda options="", **kwargs: eval_globals.get("math_random_master", lambda *a, **kw: "")(context, mode="Re", options=options, **kwargs)
    eval_locals["Rfake"] = lambda *args, **kwargs: eval_globals.get("math_random_master", lambda *a, **kw: 0)(context, mode="Rfake", *args, **kwargs)
    eval_locals["rand"] = eval_locals["R"]

    if "active_unit" in eval_locals and eval_locals["active_unit"]:
        unit_obj = eval_locals["active_unit"]
        if "syl" not in eval_locals or eval_locals["syl"] is None or isinstance(eval_locals["syl"], int):
            syl_candidate = getattr(unit_obj, "_syl_obj", None)
            if syl_candidate is not None and not isinstance(syl_candidate, int):
                eval_locals["syl"] = syl_candidate
            else:
                eval_locals["syl"] = unit_obj
        if "char" not in eval_locals and getattr(unit_obj, "char", None) is not None:
            eval_locals["char"] = getattr(unit_obj, "char")
        if "word" not in eval_locals and getattr(unit_obj, "word", None) is not None:
            eval_locals["word"] = getattr(unit_obj, "word")
        if "line" not in eval_locals and hasattr(unit_obj, "line") and unit_obj.line:
            eval_locals["line"] = unit_obj.line

    if "line" in eval_locals and eval_locals["line"] is not None:
        eval_locals.setdefault("l", eval_locals["line"])
    elif "l" in eval_locals and eval_locals["l"] is not None:
        eval_locals.setdefault("line", eval_locals["l"])

    val_max_j = eval_locals.get("maxj", eval_locals.get("fx_n", 1))
    eval_locals["maxj"] = val_max_j
    if "maxloop" not in eval_locals:
        eval_locals["maxloop"] = val_max_j
    if "j" not in eval_locals and "fx_i" in eval_locals:
        eval_locals["j"] = eval_locals["fx_i"]
    eval_locals.setdefault("j", 1)

    _fx_i_def = eval_locals.get("fx_i", 1)
    _fx_n_def = eval_locals.get("fx_n", eval_locals.get("maxloop", 1))
    _subloop_pairs = (
        ("s", "slice"),
        ("d", "divide"),
        ("b", "ring"),
        ("a", "array"),
        ("m", "multi"),
        ("p", "particle"),
        ("tp", "text_p"),
        ("ip", "img_p"),
        ("c", "clip"),
        ("an", "anim"),
    )
    for short_p, long_p in _subloop_pairs:
        si_k, sn_k, sm_k = f"{short_p}_i", f"{short_p}_n", f"{short_p}_max"
        li_k, ln_k, lm_k = f"{long_p}_i", f"{long_p}_n", f"{long_p}_max"
        i_val_p = eval_locals.get(si_k, eval_locals.get(li_k, _fx_i_def if short_p in ("s", "d") and "fx_i" in eval_locals else 1))
        n_val_p = eval_locals.get(sn_k, eval_locals.get(ln_k, _fx_n_def if short_p in ("s", "d") and "fx_n" in eval_locals else 1))
        m_val_p = eval_locals.get(sm_k, eval_locals.get(lm_k, n_val_p))
        eval_locals.setdefault(si_k, i_val_p)
        eval_locals.setdefault(li_k, i_val_p)
        eval_locals.setdefault(sn_k, n_val_p)
        eval_locals.setdefault(ln_k, n_val_p)
        eval_locals.setdefault(sm_k, m_val_p)
        eval_locals.setdefault(lm_k, m_val_p)
    eval_locals.setdefault("total_pixels", eval_locals.get("ip_n", 1))
    eval_locals.setdefault("c_col", 1)
    eval_locals.setdefault("c_row", 1)
    eval_locals.setdefault("an_j", eval_locals.get("an_i", 1))

    active_unit = eval_locals.get("active_unit") or eval_locals.get("syl") or eval_locals.get("char") or eval_locals.get("word")
    raw_prev = getattr(active_unit, "prev", None) if active_unit and hasattr(active_unit, "prev") else eval_locals.get("prev")
    raw_next = getattr(active_unit, "next", None) if active_unit and hasattr(active_unit, "next") else eval_locals.get("next")
    try:
        from models import AdjacentUnitProxy
        prev_proxy = AdjacentUnitProxy("prev", raw_prev)
        next_proxy = AdjacentUnitProxy("next", raw_next)
        prev_exists = bool(prev_proxy)
        next_exists = bool(next_proxy)
        eval_locals["prev"] = prev_proxy
        eval_locals["next"] = next_proxy
    except Exception:
        prev_exists = (raw_prev is not None)
        next_exists = (raw_next is not None)
        eval_locals["prev"] = raw_prev
        eval_locals["next"] = raw_next

    i_val = int(eval_locals.get("i", getattr(active_unit, "i", 1) if active_unit else 1))
    n_val = int(eval_locals.get("n", getattr(active_unit, "n", 1) if active_unit else 1))
    eval_locals["is_first"] = (i_val == 1) or (not prev_exists)
    eval_locals["is_last"] = (i_val == n_val) or (not next_exists)
    eval_locals["has_prev"] = prev_exists
    eval_locals["has_next"] = next_exists

    try:
        from models import InkNamespace
        eval_locals["ink"] = InkNamespace(eval_locals)
    except Exception:
        pass

    if "fx" not in eval_locals or eval_locals["fx"] is None or not isinstance(eval_locals["fx"], FxContext):
        eval_locals["fx"] = FxContext(eval_locals)

    if isinstance(context, dict) and callable(context.get("remember")) and callable(context.get("recall")):
        eval_locals["remember"] = context["remember"]
        eval_locals["recall"] = context["recall"]
    else:
        target_ctx = context if isinstance(context, dict) else eval_locals
        mem_store = target_ctx.get("_memory")
        if not isinstance(mem_store, dict):
            mem_store = target_ctx.get("memory")
        if not isinstance(mem_store, dict):
            mem_store = {}
        target_ctx["_memory"] = mem_store
        target_ctx["memory"] = mem_store
        eval_locals["_memory"] = mem_store
        eval_locals["memory"] = mem_store

        def _remember(key, val, cond=True):
            if cond:
                mem_store[str(key)] = val
            return val

        def _recall(key, default=""):
            return mem_store.get(str(key), default)

        eval_locals["remember"] = _remember
        eval_locals["recall"] = _recall

    try:
        from nodes.code_nodes import PyxisTimeModifier
        from nodes.time_nodes import (
            time_lead_in, time_lead_out, time_middle_1, time_middle_2,
            time_loop_1, time_loop_2, PyxisSyncHelper, calculate_sync_gap
        )
        eval_locals["time_lead_in"] = lambda delay=40, base=None: time_lead_in(context, delay=delay, base=base)
        eval_locals["time_lead_out"] = lambda delay=40, base=None: time_lead_out(context, delay=delay, base=base)
        eval_locals["time_middle_1"] = lambda delay=30, base=None: time_middle_1(context, delay=delay, base=base)
        eval_locals["time_middle_2"] = lambda delay=30, base=None: time_middle_2(context, delay=delay, base=base)
        eval_locals["time_loop_1"] = lambda delay=30, mode="leadin", base=None: time_loop_1(context, delay=delay, mode=mode, base=base)
        eval_locals["time_loop_2"] = lambda delay=30, mode="leadin", base=None: time_loop_2(context, delay=delay, mode=mode, base=base)

        eval_locals["li"] = PyxisTimeModifier(time_lead_in, context, default_delay=40.0)
        eval_locals["lo"] = PyxisTimeModifier(time_lead_out, context, default_delay=40.0)
        eval_locals["m1"] = PyxisTimeModifier(time_middle_1, context, default_delay=30.0)
        eval_locals["m2"] = PyxisTimeModifier(time_middle_2, context, default_delay=30.0)
        eval_locals["l1"] = PyxisTimeModifier(time_loop_1, context, default_delay=30.0, mode="leadin")
        eval_locals["l2"] = PyxisTimeModifier(time_loop_2, context, default_delay=30.0, mode="leadin")

        sync_helper = PyxisSyncHelper(eval_locals)
        eval_locals["sync"] = sync_helper
        eval_locals["calculate_sync_gap"] = lambda *a, **kw: calculate_sync_gap(eval_locals, *a, **kw)
        eval_locals.setdefault("order", "order")
        eval_locals.setdefault("style", "style")
        eval_locals.setdefault("actor", "actor")
        eval_locals.setdefault("effect", "effect")
        eval_locals.setdefault("layer", "layer")
    except Exception:
        pass

    return eval_locals


def _transform_outside_quotes(expr_str: str, transform_fn) -> str:
    """Applies transform_fn only to segments of expr_str outside single or double quotes."""
    if not expr_str or ('"' not in expr_str and "'" not in expr_str):
        return transform_fn(expr_str)
    out = []
    n = len(expr_str)
    i = 0
    seg_start = 0
    in_quote = None
    while i < n:
        ch = expr_str[i]
        if in_quote:
            if ch == '\\' and i + 1 < n:
                i += 2
                continue
            elif ch == in_quote:
                out.append(expr_str[seg_start : i + 1])
                in_quote = None
                seg_start = i + 1
        elif ch in ('"', "'"):
            if i > seg_start:
                out.append(transform_fn(expr_str[seg_start:i]))
            in_quote = ch
            seg_start = i
        i += 1
    if seg_start < n:
        if in_quote:
            out.append(expr_str[seg_start:])
        else:
            out.append(transform_fn(expr_str[seg_start:]))
    return "".join(out)


_AST_EXPR_SENTINEL = object()


def eval_python_expr(expr_str: str, context: Optional[Dict[str, Any]] = None, default: Any = "") -> Any:
    """
    Safely compiles and evaluates an arbitrary Python expression with AST caching and contextual variables.

    Execution Pipeline:
    1. Top-level Lua ternary detection ('COND and A or B'): Evaluates the condition first to avoid
       falsy fall-through (e.g. 0 or empty string) in ternary branches.
    2. Lexical pre-processing outside quoted literals:
       - Substitutes Lua inequality operator '~=' with Python '!='.
       - Converts ASS hex literals '&H<hex>&' or '&h<hex>&' into Python hex integers '0x<hex>'.
       - Expands frame time shortcuts '<num>f' into '(<num> * frame_dur)'.
       - Expands resolution ratio shortcuts '<num>r' into '(<num> * ratio)'.
       - Expands time modifier product syntax '<num>li', '<num>lo', '<num>m1', etc. into '<num> * li'.
    3. Compilation and LRU AST Cache: Checks '_AST_EXPR_CACHE'; compiles with mode='eval' on miss.
    4. Sandboxed execution: Invocates 'eval(code_obj, eval_globals, eval_locals)'.

    Args:
        expr_str: Raw expression string to evaluate.
        context: Runtime DAG context dictionary.
        default: Fallback return value if the expression fails or evaluates to None.

    Returns:
        Any: Evaluated result object (numeric, string, boolean, or fallback default).
    """
    if not expr_str:
        return default
    expr_clean = expr_str.strip()
    if not expr_clean:
        return default

    # Handle top-level Lua ternary ('COND and A or B') safely so falsy A (e.g. 0) does not fall through to B
    if " and " in expr_clean and " or " in expr_clean:
        parsed_lua = _split_top_level_ternary(expr_clean)
        if parsed_lua and parsed_lua[0] == "lua":
            _, val_true, cond, val_false = parsed_lua
            cond_val = eval_python_expr(cond, context, default=False)
            chosen = val_true if bool(cond_val) else val_false
            if re.match(r'^&[hH][0-9a-fA-F]+&?$', chosen):
                return chosen
            return eval_python_expr(chosen, context, default=chosen)

    frame_dur = 41.708
    ratio = 1.0
    if isinstance(context, dict):
        frame_dur = float(context.get("frame_dur", context.get("fd", 41.708)))
        ratio = float(context.get("ratio", context.get("module", 1.0)))

    def _preprocess_code_segment(seg: str) -> str:
        seg = seg.replace("~=", "!=")
        seg = re.sub(r'&[hH]([0-9a-fA-F]+)&?', r'0x\1', seg)
        seg = re.sub(r'(?<![a-zA-Z0-9_#&.%])([+-]?\d+(?:\.\d+)?)\s*f\b', rf'(\1 * {frame_dur})', seg)
        seg = re.sub(r'(?<![a-zA-Z0-9_#&.%])([+-]?\d+(?:\.\d+)?)\s*r\b', rf'(\1 * {ratio})', seg)
        seg = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*(li|lo|m1|m2|l1|l2)\b', r'\1 * \2', seg)
        return seg

    expr_clean = _transform_outside_quotes(expr_clean, _preprocess_code_segment)

    try:
        if expr_clean in _AST_EXPR_CACHE:
            code_obj = _AST_EXPR_CACHE[expr_clean]
            _AST_EXPR_CACHE.move_to_end(expr_clean)
        else:
            code_obj = compile(expr_clean, "<pyxis_string_eval>", "eval")
            if len(_AST_EXPR_CACHE) >= _MAX_AST_EXPR_CACHE:
                _AST_EXPR_CACHE.popitem(last=False)
            _AST_EXPR_CACHE[expr_clean] = code_obj

        eval_globals = _get_eval_globals()
        eval_locals = _prepare_eval_locals(context)
        res = eval(code_obj, eval_globals, eval_locals)
        if res is None:
            return default if default is not _AST_EXPR_SENTINEL else ""
        return res
    except Exception:
        return default


def expand_unit_shortcuts(text: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Expande atajos de unidades numéricas en texto libre o tags:
    - 10f -> 10 * frame_dur (ms)
    - 2r -> 2 * ratio (px)
    """
    if not text:
        return ""
    frame_dur = 41.708
    ratio = 1.0
    if isinstance(context, dict):
        frame_dur = float(context.get("frame_dur", context.get("fd", 41.708)))
        ratio = float(context.get("ratio", context.get("module", 1.0)))

    def _replace_unit(match: re.Match) -> str:
        num_str = match.group(1)
        unit = match.group(2)
        try:
            val = float(num_str)
            if unit == "f":
                res = val * frame_dur
            elif unit == "r":
                res = val * ratio
            else:
                return match.group(0)
            return _fmt_num(res)
        except ValueError:
            return match.group(0)

    pattern = r'(?<![a-zA-Z0-9_#&.%])([+-]?\d+(?:\.\d+)?)([fr])(?![a-zA-Z0-9_])'
    return re.sub(pattern, _replace_unit, text)


def _split_top_level_commas(s: str) -> list[str]:
    """Splits a string by top-level commas, ignoring commas inside parentheses, brackets, braces, or quotes."""
    if not s:
        return []
    parts: list[str] = []
    depth_paren = 0
    depth_bracket = 0
    depth_brace = 0
    in_quote = None
    start = 0
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if in_quote:
            if ch == '\\' and i + 1 < n:
                i += 2
                continue
            elif ch == in_quote:
                in_quote = None
        elif ch in ('"', "'"):
            in_quote = ch
        elif ch == '(':
            depth_paren += 1
        elif ch == ')':
            depth_paren = max(0, depth_paren - 1)
        elif ch == '[':
            depth_bracket += 1
        elif ch == ']':
            depth_bracket = max(0, depth_bracket - 1)
        elif ch == '{':
            depth_brace += 1
        elif ch == '}':
            depth_brace = max(0, depth_brace - 1)
        elif ch == ',' and depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
            part = s[start:i].strip()
            if part != "":
                parts.append(part)
            start = i + 1
        i += 1
    last_part = s[start:].strip()
    if last_part != "":
        parts.append(last_part)
    return parts


def _split_top_level_ternary(s: str) -> Optional[tuple[str, str, str, str]]:
    """
    Detects whether string 's' contains a top-level ternary expression in Python or Lua syntax.

    Supports:
    - Python format: 'val_true if COND else val_false'
    - Lua format: 'COND and val_true or val_false'

    Uses depth tracking across parentheses, brackets, braces, and quotes to ignore
    nested conditionals inside sub-expressions or function arguments.

    Args:
        s: Candidate conditional string.

    Returns:
        Optional[tuple[str, str, str, str]]: Tupled breakdown '(format_type, val_true, cond, val_false)'
        where format_type is 'python' or 'lua', or None if no top-level ternary matches.
    """
    s_clean = s.strip()
    if not s_clean:
        return None

    # Check for Python ' if ' ... ' else '
    depth_paren = 0
    depth_bracket = 0
    depth_brace = 0
    in_quote = None
    i = 0
    n = len(s_clean)
    if_idx = -1
    else_idx = -1

    while i < n:
        ch = s_clean[i]
        if in_quote:
            if ch == '\\' and i + 1 < n:
                i += 2
                continue
            elif ch == in_quote:
                in_quote = None
            i += 1
            continue
        if ch in ('"', "'"):
            in_quote = ch
            i += 1
            continue
        if ch == '(':
            depth_paren += 1
        elif ch == ')':
            depth_paren = max(0, depth_paren - 1)
        elif ch == '[':
            depth_bracket += 1
        elif ch == ']':
            depth_bracket = max(0, depth_bracket - 1)
        elif ch == '{':
            depth_brace += 1
        elif ch == '}':
            depth_brace = max(0, depth_brace - 1)
        elif depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
            if s_clean[i:i+4] == " if " or (i > 0 and s_clean[i:i+3] == "if " and (s_clean[i-1].isspace() or s_clean[i-1] in ')]}')):
                if if_idx == -1:
                    kw_len = 4 if s_clean[i:i+4] == " if " else 3
                    if_idx = i
                    i += kw_len
                    continue
            elif s_clean[i:i+6] == " else " or (i > 0 and s_clean[i:i+5] == "else " and (s_clean[i-1].isspace() or s_clean[i-1] in ')]}')):
                if if_idx != -1 and else_idx == -1:
                    kw_len = 6 if s_clean[i:i+6] == " else " else 5
                    else_idx = i
                    i += kw_len
                    continue
        i += 1

    if if_idx != -1 and else_idx != -1 and if_idx < else_idx:
        val_true = s_clean[:if_idx].strip()
        cond = s_clean[if_idx + (4 if s_clean[if_idx:if_idx+4] == " if " else 3):else_idx].strip()
        val_false = s_clean[else_idx + (6 if s_clean[else_idx:else_idx+6] == " else " else 5):].strip()
        if val_true and cond and val_false:
            return ("python", val_true, cond, val_false)

    # Check for Lua 'COND and A or B'
    depth_paren = 0
    depth_bracket = 0
    depth_brace = 0
    in_quote = None
    i = 0
    and_matches: list[tuple[int, int]] = []
    or_idx = -1
    or_len = 0

    while i < n:
        ch = s_clean[i]
        if in_quote:
            if ch == '\\' and i + 1 < n:
                i += 2
                continue
            elif ch == in_quote:
                in_quote = None
            i += 1
            continue
        if ch in ('"', "'"):
            in_quote = ch
            i += 1
            continue
        if ch == '(':
            depth_paren += 1
        elif ch == ')':
            depth_paren = max(0, depth_paren - 1)
        elif ch == '[':
            depth_bracket += 1
        elif ch == ']':
            depth_bracket = max(0, depth_bracket - 1)
        elif ch == '{':
            depth_brace += 1
        elif ch == '}':
            depth_brace = max(0, depth_brace - 1)
        elif depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
            if s_clean[i:i+5] == " and " or (i > 0 and s_clean[i:i+4] == "and " and (s_clean[i-1].isspace() or s_clean[i-1] in ')]}')):
                kw_len = 5 if s_clean[i:i+5] == " and " else 4
                and_matches.append((i, kw_len))
                i += kw_len
                continue
            elif s_clean[i:i+4] == " or " or (i > 0 and s_clean[i:i+3] == "or " and (s_clean[i-1].isspace() or s_clean[i-1] in ')]}')):
                if and_matches and or_idx == -1:
                    or_len = 4 if s_clean[i:i+4] == " or " else 3
                    or_idx = i
                    i += or_len
                    continue
        i += 1

    if and_matches and or_idx != -1:
        # Choose the last 'and' before 'or' so compound conditions (e.g. c1 and c2 and A or B) separate properly
        last_and = None
        for a_pos, a_len in and_matches:
            if a_pos < or_idx:
                last_and = (a_pos, a_len)
        if last_and is not None:
            and_idx, and_len = last_and
            cond = s_clean[:and_idx].strip()
            val_true = s_clean[and_idx + and_len:or_idx].strip()
            val_false = s_clean[or_idx + or_len:].strip()
            if cond and val_true and val_false:
                return ("lua", val_true, cond, val_false)

    return None


def _resolve_ternary_branch(branch_str: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Recursively resolves the selected branch of an evaluated ternary expression.

    Handles:
    - Stripping enclosing single or double quotes for literal text outputs.
    - Preserving ASS hexadecimal colour literals (&HBBGGRR&).
    - Unrolling chained or nested ternaries without outer parentheses (e.g. '\\blur2 if i == 2 else \\blur0').
    - Evaluating nested isolated parenthesised expressions via 'evaluate_isolated_ternaries'.
    - Evaluating mathematical formulas or numeric variables in non-tag branches.

    Args:
        branch_str: The raw branch string chosen by condition evaluation.
        context: Active DAG context dictionary.

    Returns:
        str: Fully evaluated and formatted string representation of the branch.
    """
    b = branch_str.strip()
    if not b:
        return ""
    if (b.startswith('"') and b.endswith('"')) or (b.startswith("'") and b.endswith("'")):
        return b[1:-1]
    if re.match(r'^&[hH][0-9a-fA-F]+&?$', b):
        return b

    # Check for chained/nested ternary without parentheses (e.g. \blur2 if i == 2 else \blur0)
    parsed = _split_top_level_ternary(b)
    if parsed:
        _, val_true, cond, val_false = parsed
        try:
            cond_clean = cond.strip()
            cond_res = eval_python_expr(cond_clean, context, default=None)
            if cond_res is None:
                eval_globals = _get_eval_globals()
                eval_locals = _prepare_eval_locals(context)
                cond_res = eval(compile(cond_clean, "<ternary_cond>", "eval"), eval_globals, eval_locals)
            is_true = bool(cond_res)
        except Exception:
            is_true = False
        chosen = val_true if is_true else val_false
        return _resolve_ternary_branch(chosen, context)

    # Evaluate nested isolated ternaries if present
    nested = evaluate_isolated_ternaries(b, context)
    if nested != b:
        b = nested

    # If it's a numeric expression, math function or simple variable, evaluate it
    if "\\" not in b:
        try:
            res = eval_python_expr(b, context, default=None)
            if res is not None:
                return _fmt_num(res) if isinstance(res, (int, float)) else str(res)
        except Exception:
            pass

    return b


def _evaluate_single_ternary_expr(content: str, context: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Evaluates an isolated parenthesised expression not preceded by an ASS tag name:
    1. Ternary conditionals: '(A if COND else B)' or '(COND and A or B)'.
    2. Function and method invocations: '(Func())'.
    3. Context variables and attributes: '(syl.text)', '(syl.dur)', '(fx.dur)', '(line.text)', '(j)'.
    4. Mathematical and logical expressions: '(syl.dur / 2)', '(j * 15)', '(10 + 20)'.

    Safeguards:
    - Ignores pure numeric literals and atomic quoted strings to preserve subtitle text like '(1999)' or '("word")'.
    - Suppresses raw uninvoked callables, types, or modules (e.g. '(min)' or '(math)').
    - Unpacks text-bearing objects (such as PyxisUnit) via 'text_stripped' or 'text'.

    Args:
        content: Inner string within the isolated parentheses.
        context: Active DAG context dictionary.

    Returns:
        Optional[str]: Formatted string result, or None if content is not a valid evaluable expression.
    """
    c_clean = content.strip()
    if not c_clean:
        return None

    # 1. Comprobar ternarios de nivel superior
    parsed = _split_top_level_ternary(c_clean)
    if parsed:
        _, val_true, cond, val_false = parsed
        try:
            cond_clean = cond.strip()
            cond_res = eval_python_expr(cond_clean, context, default=None)
            if cond_res is None:
                eval_globals = _get_eval_globals()
                eval_locals = _prepare_eval_locals(context)
                cond_res = eval(compile(cond_clean, "<ternary_cond>", "eval"), eval_globals, eval_locals)
            is_true = bool(cond_res)
        except Exception:
            is_true = False
        chosen = val_true if is_true else val_false
        return _resolve_ternary_branch(chosen, context)

    # 2. Ignorar números puros y cadenas literales atómicas para preservar subtítulos literales como '(1999)' o '("palabra")'
    if re.match(r'^[+-]?\d+(?:\.\d+)?$', c_clean):
        return None
    try:
        import ast
        node = ast.parse(c_clean, mode='eval')
        if isinstance(node.body, ast.Constant) and isinstance(node.body.value, str):
            return None
    except Exception:
        pass

    # 3. Evaluar como expresión de Python con contexto
    res = eval_python_expr(c_clean, context, default=_AST_EXPR_SENTINEL)
    if res is _AST_EXPR_SENTINEL:
        return None

    # No serializar funciones, tipos o módulos que hayan quedado sin invocar (ej. '(min)' o '(math)')
    if callable(res) or isinstance(res, type) or hasattr(res, "__file__"):
        return None

    # Si es una unidad con texto (ej. PyxisUnit)
    if hasattr(res, "text_stripped") and not isinstance(res, (int, float, str, bool)):
        return str(getattr(res, "text_stripped", getattr(res, "text", "")))

    if res is None:
        return ""
    if isinstance(res, bool):
        return "1" if res else "0"
    if isinstance(res, (int, float)):
        return _fmt_num(res)
    if isinstance(res, str):
        return res
    if isinstance(res, (list, tuple, dict, set)):
        return None

    return str(res)


def evaluate_isolated_ternaries(text: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Performs iterative reduction of strictly isolated parenthesised ternary expressions and calls.

    Evaluates:
    - '( value if cond else value2 )' / '( cond and value or value2 )'
    - '( FuncReturningTags() )'
    - Arbitrarily nested expressions evaluated from innermost to outermost (up to depth 25).

    Invariants:
    - Bare or un-parenthesised text is never modified.
    - Parentheses preceded by ASS tag identifiers (e.g. '\\pos(...)', '\\t(...)') are strictly bypassed.

    Args:
        text: Subtitle text or template containing possible isolated parenthesised expressions.
        context: Active DAG context dictionary.

    Returns:
        str: String with all isolated evaluable parenthesised expressions reduced to their computed values.
    """
    if not text or not isinstance(text, str) or "(" not in text:
        return text

    curr = text
    # Iterative reduction from innermost to outermost parenthesized expressions
    for _ in range(25):  # Max nesting depth safeguard
        found_any = False
        n = len(curr)
        i = 0
        in_quote = None
        new_chars = []
        replaced = False

        while i < n:
            ch = curr[i]
            if in_quote:
                if ch == '\\' and i + 1 < n:
                    new_chars.append(curr[i:i+2])
                    i += 2
                    continue
                elif ch == in_quote:
                    in_quote = None
                new_chars.append(ch)
                i += 1
                continue
            if ch in ('"', "'"):
                in_quote = ch
                new_chars.append(ch)
                i += 1
                continue

            # Check for parenthesis delimiters: ( ... ) not preceded by a tag name \tag
            if ch == '(' and not (i > 0 and re.search(r'\\[a-zA-Z0-9]+$', curr[:i])):
                d = 1
                j = i + 1
                in_q = None
                while j < n:
                    ch_j = curr[j]
                    if in_q:
                        if ch_j == '\\' and j + 1 < n:
                            j += 2
                            continue
                        elif ch_j == in_q:
                            in_q = None
                    elif ch_j in ('"', "'"):
                        in_q = ch_j
                    elif ch_j == '(':
                        d += 1
                    elif ch_j == ')':
                        d -= 1
                        if d == 0:
                            break
                    j += 1
                if j < n and d == 0:
                    inner = curr[i+1:j]
                    tern_res = _evaluate_single_ternary_expr(inner, context)
                    if tern_res is not None:
                        new_chars.append(tern_res)
                        i = j + 1
                        replaced = True
                        found_any = True
                        continue

            new_chars.append(ch)
            i += 1

        curr = "".join(new_chars)
        if not found_any or not replaced:
            break

    return curr


def _get_context_origin(context: Optional[Dict[str, Any]]) -> tuple[str, str]:
    """Retrieves Cartesian origin / pivot coordinates (X, Y) from the active context."""
    if not isinstance(context, dict):
        return ("0", "0")
    active_unit = context.get("active_unit") or context.get("syl") or context.get("char") or context.get("word")
    fx_obj = context.get("fx")

    ox: Any = 0.0
    if "fx_pos_x" in context:
        ox = context["fx_pos_x"]
    elif fx_obj and hasattr(fx_obj, "pos_x"):
        ox = getattr(fx_obj, "pos_x")
    elif "pos_x" in context:
        ox = context["pos_x"]
    elif "x" in context:
        ox = context["x"]
    elif active_unit and hasattr(active_unit, "center"):
        ox = getattr(active_unit, "center")
    elif active_unit and hasattr(active_unit, "x"):
        ox = getattr(active_unit, "x")

    oy: Any = 0.0
    if "fx_pos_y" in context:
        oy = context["fx_pos_y"]
    elif fx_obj and hasattr(fx_obj, "pos_y"):
        oy = getattr(fx_obj, "pos_y")
    elif "pos_y" in context:
        oy = context["pos_y"]
    elif "y" in context:
        oy = context["y"]
    elif active_unit and hasattr(active_unit, "middle"):
        oy = getattr(active_unit, "middle")
    elif active_unit and hasattr(active_unit, "y"):
        oy = getattr(active_unit, "y")

    return (_fmt_num(ox), _fmt_num(oy))


def _get_context_style_props(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Safely extracts normalized metric and style properties from the active context."""
    if not isinstance(context, dict):
        context = {}
    active_unit = context.get("active_unit") or context.get("syl") or context.get("char") or context.get("word")
    active_line = context.get("active_line", context.get("line"))
    if not active_line and hasattr(active_unit, "line") and getattr(active_unit, "line", None):
        active_line = getattr(active_unit, "line")
    if not active_line and active_unit and hasattr(active_unit, "style_name"):
        active_line = active_unit

    styleref = getattr(active_line, "styleref", None) if active_line else None

    def _get_prop(prop: str, default: Any = "") -> Any:
        if styleref and hasattr(styleref, prop):
            val = getattr(styleref, prop)
            return val() if callable(val) else val
        if active_line and hasattr(active_line, prop):
            val = getattr(active_line, prop)
            return val() if callable(val) else val
        return default

    scale_x_raw = _get_prop("scale_x", 100.0)
    scale_y_raw = _get_prop("scale_y", 100.0)
    fontsize_raw = _get_prop("fontsize", 25.0)

    try:
        scale_x = float(scale_x_raw) if scale_x_raw is not None else 100.0
    except (ValueError, TypeError):
        scale_x = 100.0

    try:
        scale_y = float(scale_y_raw) if scale_y_raw is not None else 100.0
    except (ValueError, TypeError):
        scale_y = 100.0

    try:
        fontsize = float(fontsize_raw) if fontsize_raw is not None else 25.0
    except (ValueError, TypeError):
        fontsize = 25.0

    angle_val = _get_prop("angle", None)
    if angle_val is None or angle_val == "":
        angle_val = _get_prop("frz", 0)

    bold_val = _get_prop("bold", False)
    italic_val = _get_prop("italic", False)
    underline_val = _get_prop("underline", False)
    strikeout_val = _get_prop("strikeout", False)

    def _to_flag_str(v: Any) -> str:
        if isinstance(v, bool):
            return "1" if v else "0"
        return "1" if str(v).strip() in ("1", "-1", "true", "True") else "0"

    return {
        "scale_x": scale_x,
        "scale_y": scale_y,
        "fontsize": fontsize,
        "scale_x_str": _fmt_num(scale_x),
        "scale_y_str": _fmt_num(scale_y),
        "fontsize_str": _fmt_num(fontsize),
        "color1": str(_get_prop("color1", "&H00FFFFFF&")),
        "color2": str(_get_prop("color2", "&H000000FF&")),
        "color3": str(_get_prop("color3", "&H00000000&")),
        "color4": str(_get_prop("color4", "&H00000000&")),
        "alpha1": _format_ass_alpha(_get_prop("alpha1", "&H00&")),
        "alpha2": _format_ass_alpha(_get_prop("alpha2", "&H00&")),
        "alpha3": _format_ass_alpha(_get_prop("alpha3", "&H00&")),
        "alpha4": _format_ass_alpha(_get_prop("alpha4", "&H00&")),
        "spacing": _fmt_num(_get_prop("spacing", 0)),
        "outline": _fmt_num(_get_prop("outline", 2)),
        "shadow": _fmt_num(_get_prop("shadow", 2)),
        "angle": _fmt_num(angle_val),
        "fontname": str(_get_prop("fontname", "Arial")),
        "align": _fmt_num(_get_prop("align", 2)),
        "bold": _to_flag_str(bold_val),
        "italic": _to_flag_str(italic_val),
        "underline": _to_flag_str(underline_val),
        "strikeout": _to_flag_str(strikeout_val),
    }


def _replace_balanced_parens_tags(text: str, tag_start_re: re.Pattern, handler_fn) -> str:
    """
    Robustly locates and substitutes ASS tags with parenthesized arguments using balance depth tracking.
    Supports arbitrary nested parentheses (function calls, Python ternaries, and sub-expressions).
    """
    out = []
    pos = 0
    text_len = len(text)
    while pos < text_len:
        m = tag_start_re.search(text, pos)
        if not m:
            out.append(text[pos:])
            break

        tag_name = m.group(1)
        start_idx = m.start()
        open_paren_idx = m.end() - 1

        depth = 1
        i = open_paren_idx + 1
        in_quote = None
        while i < text_len and depth > 0:
            ch = text[i]
            if in_quote:
                if ch == '\\' and i + 1 < text_len:
                    i += 2
                    continue
                elif ch == in_quote:
                    in_quote = None
            elif ch in ('"', "'"):
                in_quote = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            i += 1

        if depth == 0:
            body = text[open_paren_idx + 1 : i - 1]
            out.append(text[pos:start_idx])
            repl = handler_fn(tag_name, body)
            out.append(repl)
            pos = i
        else:
            out.append(text[pos : open_paren_idx + 1])
            pos = open_paren_idx + 1

    return "".join(out)


def expand_custom_dark_tags(text: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Expands composite tags, style restoration tags (~), stochastic tags (\\tagR),
    auto-origin rotation Dark Tags, and style ratio tags to pure canonical ASS syntax.
    """
    if not text or "\\" not in text:
        return text

    if not isinstance(context, dict):
        context = {}

    style_props = _get_context_style_props(context)
    ox, oy = _get_context_origin(context)

    style_color1 = style_props["color1"]
    style_color2 = style_props["color2"]
    style_color3 = style_props["color3"]
    style_color4 = style_props["color4"]
    style_alpha1 = style_props["alpha1"]
    style_alpha2 = style_props["alpha2"]
    style_alpha3 = style_props["alpha3"]
    style_alpha4 = style_props["alpha4"]
    style_scale_x = style_props["scale_x_str"]
    style_scale_y = style_props["scale_y_str"]
    style_fontsize = style_props["fontsize_str"]
    style_spacing = style_props["spacing"]
    style_outline = style_props["outline"]
    style_shadow = style_props["shadow"]
    style_angle = style_props["angle"]
    style_fontname = style_props["fontname"]
    style_align = style_props["align"]
    style_bold = style_props["bold"]
    style_italic = style_props["italic"]
    style_underline = style_props["underline"]
    style_strikeout = style_props["strikeout"]

    style_scale_x_num = style_props["scale_x"]
    style_scale_y_num = style_props["scale_y"]
    style_fontsize_num = style_props["fontsize"]

    style_color1_clean = _clean_ass_color(style_color1)
    style_color2_clean = _clean_ass_color(style_color2)
    style_color3_clean = _clean_ass_color(style_color3)
    style_color4_clean = _clean_ass_color(style_color4)

    s = text

    def _replace_stochastic_tag(tag_name: str, body: str) -> str:
        args_str = body.strip()
        args = _split_top_level_commas(args_str) if args_str else []

        eval_globals = _get_eval_globals()
        eval_locals = _prepare_eval_locals(context)

        m_multi_c = re.match(r'^([1-4]+)c$', tag_name)
        if m_multi_c or tag_name == "c":
            if len(args) >= 2:
                v1 = eval_python_expr(args[0], context, args[0])
                v2 = eval_python_expr(args[1], context, args[1])
                c1_arg = f"&H{int(v1):06X}&" if isinstance(v1, (int, float)) else str(v1)
                c2_arg = f"&H{int(v2):06X}&" if isinstance(v2, (int, float)) else str(v2)
                rcol_fn = eval_locals.get("Rcolor")
                col = _clean_ass_color(rcol_fn(c1_arg, c2_arg)) if callable(rcol_fn) else eval_globals["random_color"]()
            else:
                col = eval_globals["random_color"]()
            if tag_name == "c":
                return f"\\c{col}"
            return "".join(f"\\{digit}c{col}" for digit in m_multi_c.group(1))

        m_multi_a = re.match(r'^([1-4]+)a$', tag_name)
        if m_multi_a or tag_name in ("a", "alpha"):
            if args:
                min_v = float(eval_python_expr(args[0], context, 0)) if len(args) > 0 else 0.0
                max_v = float(eval_python_expr(args[1], context, 255)) if len(args) > 1 else 255.0
                step_v = float(eval_python_expr(args[2], context, 1)) if len(args) > 2 else 1.0
                r_fn = eval_locals.get("R", lambda a, b, c: random.randint(int(a), int(b)))
                val = r_fn(min_v, max_v, step_v)
                alp = _format_ass_alpha(val)
            else:
                alp = eval_globals["random_alpha"]()
            if tag_name in ("a", "alpha"):
                return f"\\alpha{alp}"
            return "".join(f"\\{digit}a{alp}" for digit in m_multi_a.group(1))

        min_v = float(eval_python_expr(args[0], context, 0)) if len(args) > 0 else 0.0
        max_v = float(eval_python_expr(args[1], context, 100)) if len(args) > 1 else 100.0
        step_v = float(eval_python_expr(args[2], context, 1)) if len(args) > 2 else 1.0

        r_fn = eval_locals.get("R", lambda a, b, c: random.randint(int(a), int(b)))
        rand_num = r_fn(min_v, max_v, step_v)
        rand_val = _fmt_num(rand_num)

        if tag_name == "fscxy": return f"\\fscx{rand_val}\\fscy{rand_val}"
        if tag_name == "faxy": return f"\\fax{rand_val}\\fay{rand_val}"
        if tag_name == "frxyz": return f"\\frx{rand_val}\\fry{rand_val}\\frz{rand_val}"
        if tag_name == "frxy": return f"\\frx{rand_val}\\fry{rand_val}"
        if tag_name == "frxz": return f"\\frx{rand_val}\\frz{rand_val}"
        if tag_name == "fryz": return f"\\fry{rand_val}\\frz{rand_val}"
        if tag_name == "xybord": return f"\\xbord{rand_val}\\ybord{rand_val}"
        if tag_name == "xyshad": return f"\\xshad{rand_val}\\yshad{rand_val}"
        if tag_name == "bs": return f"\\bord{rand_val}\\shad{rand_val}"

        # Auto-origin stochastic rotations
        if tag_name in ("fro", "frzo"): return f"\\org({ox},{oy})\\frz{rand_val}"
        if tag_name == "frxo": return f"\\org({ox},{oy})\\frx{rand_val}"
        if tag_name == "fryo": return f"\\org({ox},{oy})\\fry{rand_val}"
        if tag_name == "frxyo": return f"\\org({ox},{oy})\\frx{rand_val}\\fry{rand_val}"
        if tag_name == "frxzo": return f"\\org({ox},{oy})\\frx{rand_val}\\frz{rand_val}"
        if tag_name == "fryzo": return f"\\org({ox},{oy})\\fry{rand_val}\\frz{rand_val}"
        if tag_name == "frxyzo": return f"\\org({ox},{oy})\\frx{rand_val}\\fry{rand_val}\\frz{rand_val}"

        # Style ratio stochastic tags
        if tag_name == "fscxyr":
            ratio = float(rand_num)
            return f"\\fscx{_fmt_num(style_scale_x_num * ratio)}\\fscy{_fmt_num(style_scale_y_num * ratio)}"
        if tag_name == "fscxr":
            ratio = float(rand_num)
            return f"\\fscx{_fmt_num(style_scale_x_num * ratio)}"
        if tag_name == "fscyr":
            ratio = float(rand_num)
            return f"\\fscy{_fmt_num(style_scale_y_num * ratio)}"
        if tag_name == "fsr":
            ratio = float(rand_num)
            return f"\\fs{_fmt_num(style_fontsize_num * ratio)}"

        return f"\\{tag_name}{rand_val}"

    s = _replace_balanced_parens_tags(s, re.compile(r'\\([a-zA-Z0-9]+)R\('), _replace_stochastic_tag)

    tag_restorations = [
        (r'\c~', f"\\c{style_color1_clean}"),
        (r'\alpha~', r"\alpha&H00&"),
        (r'\fscxy~', f"\\fscx{style_scale_x}\\fscy{style_scale_y}"),
        (r'\fscx~', f"\\fscx{style_scale_x}"),
        (r'\fscy~', f"\\fscy{style_scale_y}"),
        (r'\fs~', f"\\fs{style_fontsize}"),
        (r'\fsp~', f"\\fsp{style_spacing}"),
        (r'\fn~', f"\\fn{style_fontname}"),
        (r'\an~', f"\\an{style_align}"),
        (r'\xybord~', f"\\xbord{style_outline}\\ybord{style_outline}"),
        (r'\xbord~', f"\\xbord{style_outline}"),
        (r'\ybord~', f"\\ybord{style_outline}"),
        (r'\bord~', f"\\bord{style_outline}"),
        (r'\xyshad~', f"\\xshad{style_shadow}\\yshad{style_shadow}"),
        (r'\xshad~', f"\\xshad{style_shadow}"),
        (r'\yshad~', f"\\yshad{style_shadow}"),
        (r'\shad~', f"\\shad{style_shadow}"),
        (r'\bs~', f"\\bord{style_outline}\\shad{style_shadow}"),
        (r'\frxyz~', f"\\frx0\\fry0\\frz{style_angle}"),
        (r'\frxy~', r"\frx0\fry0"),
        (r'\frxz~', f"\\frx0\\frz{style_angle}"),
        (r'\fryz~', f"\\fry0\\frz{style_angle}"),
        (r'\frz~', f"\\frz{style_angle}"),
        (r'\fr~', f"\\fr{style_angle}"),
        (r'\frx~', r"\frx0"),
        (r'\fry~', r"\fry0"),
        (r'\blur~', r"\blur0"),
        (r'\be~', r"\be0"),
        (r'\faxy~', r"\fax0\fay0"),
        (r'\fax~', r"\fax0"),
        (r'\fay~', r"\fay0"),
        (r'\b~', f"\\b{style_bold}"),
        (r'\i~', f"\\i{style_italic}"),
        (r'\u~', f"\\u{style_underline}"),
        (r'\s~', f"\\s{style_strikeout}"),
    ]

    for literal_pat, repl in tag_restorations:
        s = s.replace(literal_pat, repl)

    style_colors = {"1": style_color1_clean, "2": style_color2_clean, "3": style_color3_clean, "4": style_color4_clean}
    style_alphas = {"1": style_alpha1, "2": style_alpha2, "3": style_alpha3, "4": style_alpha4}

    s = re.sub(r'\\([1-4]+)c~', lambda m: "".join(f"\\{d}c{style_colors.get(d, style_color1_clean)}" for d in m.group(1)), s)
    s = re.sub(r'\\([1-4]+)a~', lambda m: "".join(f"\\{d}a{style_alphas.get(d, '&H00&')}" for d in m.group(1)), s)

    # Style ratio tags (direct numeric value)
    s = re.sub(r'\\fscxyr([+-]?\d+(?:\.\d+)?)', lambda m: f"\\fscx{_fmt_num(style_scale_x_num * float(m.group(1)))}\\fscy{_fmt_num(style_scale_y_num * float(m.group(1)))}", s)
    s = re.sub(r'\\fscxr([+-]?\d+(?:\.\d+)?)', lambda m: f"\\fscx{_fmt_num(style_scale_x_num * float(m.group(1)))}", s)
    s = re.sub(r'\\fscyr([+-]?\d+(?:\.\d+)?)', lambda m: f"\\fscy{_fmt_num(style_scale_y_num * float(m.group(1)))}", s)
    s = re.sub(r'\\fsr([+-]?\d+(?:\.\d+)?)', lambda m: f"\\fs{_fmt_num(style_fontsize_num * float(m.group(1)))}", s)

    # Auto-origin rotations (direct numeric value)
    s = re.sub(r'\\frxyzo([+-]?\d+(?:\.\d+)?)', lambda m: f"\\org({ox},{oy})\\frx{m.group(1)}\\fry{m.group(1)}\\frz{m.group(1)}", s)
    s = re.sub(r'\\frxyo([+-]?\d+(?:\.\d+)?)', lambda m: f"\\org({ox},{oy})\\frx{m.group(1)}\\fry{m.group(1)}", s)
    s = re.sub(r'\\frxzo([+-]?\d+(?:\.\d+)?)', lambda m: f"\\org({ox},{oy})\\frx{m.group(1)}\\frz{m.group(1)}", s)
    s = re.sub(r'\\fryzo([+-]?\d+(?:\.\d+)?)', lambda m: f"\\org({ox},{oy})\\fry{m.group(1)}\\frz{m.group(1)}", s)
    s = re.sub(r'\\frxo([+-]?\d+(?:\.\d+)?)', lambda m: f"\\org({ox},{oy})\\frx{m.group(1)}", s)
    s = re.sub(r'\\fryo([+-]?\d+(?:\.\d+)?)', lambda m: f"\\org({ox},{oy})\\fry{m.group(1)}", s)
    s = re.sub(r'\\frzo([+-]?\d+(?:\.\d+)?)', lambda m: f"\\org({ox},{oy})\\frz{m.group(1)}", s)
    s = re.sub(r'\\fro([+-]?\d+(?:\.\d+)?)', lambda m: f"\\org({ox},{oy})\\frz{m.group(1)}", s)

    # Standard composite tags
    s = re.sub(r'\\fscxy([+-]?\d+(?:\.\d+)?)', lambda m: f"\\fscx{m.group(1)}\\fscy{m.group(1)}", s)
    s = re.sub(r'\\faxy([+-]?\d+(?:\.\d+)?)', lambda m: f"\\fax{m.group(1)}\\fay{m.group(1)}", s)
    s = re.sub(r'\\frxyz([+-]?\d+(?:\.\d+)?)', lambda m: f"\\frx{m.group(1)}\\fry{m.group(1)}\\frz{m.group(1)}", s)
    s = re.sub(r'\\frxy([+-]?\d+(?:\.\d+)?)', lambda m: f"\\frx{m.group(1)}\\fry{m.group(1)}", s)
    s = re.sub(r'\\frxz([+-]?\d+(?:\.\d+)?)', lambda m: f"\\frx{m.group(1)}\\frz{m.group(1)}", s)
    s = re.sub(r'\\fryz([+-]?\d+(?:\.\d+)?)', lambda m: f"\\fry{m.group(1)}\\frz{m.group(1)}", s)
    s = re.sub(r'\\xybord([+-]?\d+(?:\.\d+)?)', lambda m: f"\\xbord{m.group(1)}\\ybord{m.group(1)}", s)
    s = re.sub(r'\\xyshad([+-]?\d+(?:\.\d+)?)', lambda m: f"\\xshad{m.group(1)}\\yshad{m.group(1)}", s)
    s = re.sub(r'\\bs([+-]?\d+(?:\.\d+)?)', lambda m: f"\\bord{m.group(1)}\\shad{m.group(1)}", s)

    color_val_pat = r'(&[hH]?[0-9a-fA-F]+&?|[0-9a-fA-F]{6})(?=[\\\}\s]|$)'
    s = re.sub(rf'\\([1-4])c{color_val_pat}', lambda m: f"\\{m.group(1)}c{_clean_ass_color(m.group(2))}", s)

    dark_color_val_pat = r'(#[0-9a-fA-F]{3,8}|&[hH]?[0-9a-fA-F]+&?|[0-9a-fA-F]{6})(?=[\\\}\s]|$)'
    s = re.sub(rf'\\([1-4]{{2,}})c{dark_color_val_pat}', lambda m: "".join(f"\\{d}c{_clean_ass_color(m.group(2))}" for d in m.group(1)), s)

    alpha_val_pat = r'(&[hH]?[0-9a-fA-F]+&?|[0-9a-fA-F]{2}|\d+)(?=[\\\}\s]|$)'
    s = re.sub(rf'\\([1-4]+)a{alpha_val_pat}', lambda m: "".join(f"\\{d}a{_format_ass_alpha(m.group(2))}" for d in m.group(1)), s)

    # Convert standalone decimal alpha tags (e.g. \4a100, \alpha255, \1a0, \2a128) to canonical ASS &HXX&
    s = re.sub(r'\\(alpha|[1-4]a)(\d{1,3})(?=[\\\}\s]|$)', lambda m: f"\\{m.group(1)}{_format_ass_alpha(m.group(2))}", s)

    return s


def evaluate_tag_parentheses(text: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Evaluates dynamic expressions, formulas, and functions within ASS tag parentheses.

    Handles specialised tag families:
    1. Temporal context transforms:
       - '\\te([st,] et, [accel,] \\tags)': End-relative transform calculating start/end times
         relative to total duration ('total_dur - t2', 'total_dur - t1').
       - '\\ts(...)', '\\tc(...)', '\\tw(...)': Relative transforms anchored to syllable start,
         character start, or word start respectively.
    2. Standard ASS transforms ('\\t(...)') and recursive Dark Tag evaluation:
       - Supports both standard time keyframes ('\\t(t1, t2, \\tags)') and parameterless transforms ('\\t(\\tags)').
    3. Rectangular and vector clipping tags ('\\clip(...)', '\\iclip(...)'):
       - Substitutes the 'center' keyword with active unit coordinates ('center, middle').
       - Preserves raw ASSdraw drawing commands ('m ...') intact.
    4. Coordinate and positioning tags ('\\pos(...)', '\\move(...)', '\\org(...)', '\\fad(...)', '\\fade(...)'):
       - Evaluates numeric expressions for each comma-separated argument.
    5. Single and composite tags with embedded expressions:
       - Symmetrical pairs: '\\fscxy(...)', '\\faxy(...)', '\\xybord(...)', '\\xyshad(...)', '\\bs(...)'.
       - 3D rotations: '\\frxyz(...)', '\\frxy(...)', '\\frxz(...)', '\\fryz(...)'.
       - Auto-origin rotations: '\\fro(...)', '\\frzo(...)', '\\frxyzo(...)'.
       - Style ratio scaling: '\\fscxyr(...)', '\\fscxr(...)', '\\fscyr(...)', '\\fsr(...)'.
       - Multi-channel colour and alpha: '\\134c(...)', '\\13a(...)'.

    Args:
        text: Subtitle string or tag block containing parenthesised ASS tags.
        context: Active DAG context dictionary providing metrics, origins, and style properties.

    Returns:
        str: String with all parenthesised tag arguments evaluated to canonical ASS numeric or hex values.
    """
    if not text or "\\" not in text or "(" not in text:
        return text

    if not isinstance(context, dict):
        context = {}

    style_props = _get_context_style_props(context)
    ox, oy = _get_context_origin(context)
    style_scale_x_num = style_props["scale_x"]
    style_scale_y_num = style_props["scale_y"]
    style_fontsize_num = style_props["fontsize"]

    active_unit = context.get("active_unit") or context.get("syl") or context.get("char") or context.get("word")
    unit_dur = getattr(active_unit, "dur", getattr(active_unit, "duration", context.get("dur", context.get("duration", 0.0)))) if active_unit else context.get("dur", context.get("duration", 0.0))
    fx_obj = context.get("fx")
    total_dur = getattr(fx_obj, "dur", unit_dur) if fx_obj else unit_dur

    s = text

    def _eval_context_time_transform(tag_prefix: str, body: str) -> str:
        tag_start_idx = body.find("\\")
        if tag_start_idx != -1:
            times_part = body[:tag_start_idx].strip().rstrip(",")
            tags_part = body[tag_start_idx:].strip()

            eval_tags = expand_custom_dark_tags(tags_part, context)
            eval_tags = evaluate_tag_parentheses(eval_tags, context)

            if not times_part:
                return f"\\t({eval_tags})"

            time_args = _split_top_level_commas(times_part)
            eval_nums = [float(eval_python_expr(arg, context, default=0)) for arg in time_args]

            if tag_prefix == "te":
                if len(eval_nums) >= 2:
                    t1, t2 = eval_nums[0], eval_nums[1]
                    st = max(0.0, float(total_dur) - t2)
                    et = max(0.0, float(total_dur) - t1)
                    if len(eval_nums) >= 3:
                        return f"\\t({_fmt_num(st)}, {_fmt_num(et)}, {_fmt_num(eval_nums[2])}, {eval_tags})"
                    return f"\\t({_fmt_num(st)}, {_fmt_num(et)}, {eval_tags})"
                elif len(eval_nums) == 1:
                    t = eval_nums[0]
                    st = max(0.0, float(total_dur) - t)
                    return f"\\t({_fmt_num(st)}, {_fmt_num(total_dur)}, {eval_tags})"
            elif tag_prefix in ("ts", "tc", "tw"):
                target_obj = context.get("syl" if tag_prefix == "ts" else ("char" if tag_prefix == "tc" else "word"), active_unit)
                if tag_prefix == "ts":
                    base_st = float(getattr(target_obj, "syl_start", getattr(target_obj, "start_time", 0.0)) if target_obj else 0.0)
                elif tag_prefix == "tc":
                    base_st = float(getattr(target_obj, "char_start", getattr(target_obj, "start_time", 0.0)) if target_obj else 0.0)
                else:
                    base_st = float(getattr(target_obj, "word_start", getattr(target_obj, "start_time", 0.0)) if target_obj else 0.0)
                if len(eval_nums) >= 2:
                    st = base_st + eval_nums[0]
                    et = base_st + eval_nums[1]
                    if len(eval_nums) >= 3:
                        return f"\\t({_fmt_num(st)}, {_fmt_num(et)}, {_fmt_num(eval_nums[2])}, {eval_tags})"
                    return f"\\t({_fmt_num(st)}, {_fmt_num(et)}, {eval_tags})"
                elif len(eval_nums) == 1:
                    st = base_st
                    et = base_st + eval_nums[0]
                    return f"\\t({_fmt_num(st)}, {_fmt_num(et)}, {eval_tags})"

            eval_times = [_fmt_num(n) for n in eval_nums]
            return f"\\t({', '.join(eval_times)}, {eval_tags})"
        else:
            args = _split_top_level_commas(body)
            eval_args = [_fmt_num(eval_python_expr(a, context, default=a)) for a in args]
            return f"\\t({', '.join(eval_args)})"

    s = _replace_balanced_parens_tags(s, re.compile(r'\\(te|ts|tc|tw)\('), _eval_context_time_transform)

    def _eval_t_tag(tag_name: str, body: str) -> str:
        body_clean = body.strip()
        tag_start_idx = body_clean.find("\\")
        if tag_start_idx != -1:
            times_part = body_clean[:tag_start_idx].strip().rstrip(",")
            tags_part = body_clean[tag_start_idx:].strip()

            eval_tags = expand_custom_dark_tags(tags_part, context)
            eval_tags = evaluate_tag_parentheses(eval_tags, context)

            if not times_part:
                return f"\\t({eval_tags})"

            time_args = _split_top_level_commas(times_part)
            eval_times = []
            for arg in time_args:
                res = eval_python_expr(arg, context, default=arg)
                eval_times.append(_fmt_num(res))

            return f"\\t({', '.join(eval_times)}, {eval_tags})"
        else:
            args = _split_top_level_commas(body_clean)
            eval_args = []
            for arg in args:
                res = eval_python_expr(arg, context, default=arg)
                eval_args.append(_fmt_num(res))
            return f"\\t({', '.join(eval_args)})"

    s = _replace_balanced_parens_tags(s, re.compile(r'\\(t)\('), _eval_t_tag)

    def _eval_clip_tag(tag_name: str, body: str) -> str:
        args_str = body.strip()
        if "center" in args_str.lower() and ("m " in args_str or "," not in args_str):
            center_x = getattr(active_unit, "center", context.get("x", 0.0))
            middle_y = getattr(active_unit, "middle", context.get("y", 0.0))
            args_clean = re.sub(r'\bcenter\b', f"{center_x}, {middle_y}", args_str, flags=re.IGNORECASE)
            return f"\\{tag_name}({args_clean})"

        args = _split_top_level_commas(args_str)
        has_space = ", " in args_str
        sep = ", " if has_space else ","

        if len(args) == 4:
            eval_args = [_fmt_num(eval_python_expr(a, context, a)) for a in args]
            return f"\\{tag_name}({sep.join(eval_args)})"
        elif len(args) == 2:
            eval_args = []
            for a in args:
                if "m " in a:
                    eval_args.append(a)
                else:
                    eval_args.append(_fmt_num(eval_python_expr(a, context, a)))
            return f"\\{tag_name}({sep.join(eval_args)})"
        elif len(args) == 1:
            if "m " in args[0]:
                return f"\\{tag_name}({args[0]})"
            res_0 = eval_python_expr(args[0], context, args[0])
            return f"\\{tag_name}({_fmt_num(res_0)})"

        return f"\\{tag_name}({args_str})"

    s = _replace_balanced_parens_tags(s, re.compile(r'\\(i?clip)\('), _eval_clip_tag)

    def _eval_multi_arg_tag(tag_name: str, body: str) -> str:
        args_str = body.strip()
        has_space = ", " in args_str
        sep = ", " if has_space else ","
        args = _split_top_level_commas(args_str)
        eval_args = [_fmt_num(eval_python_expr(a, context, a)) for a in args]
        return f"\\{tag_name}({sep.join(eval_args)})"

    s = _replace_balanced_parens_tags(s, re.compile(r'\\(pos|move|org|fad|fade)\('), _eval_multi_arg_tag)

    def _eval_single_tag(tag_name: str, body: str) -> str:
        expr = body.strip()
        top_args = _split_top_level_commas(expr)

        if len(top_args) > 1:
            eval_vals = [eval_python_expr(a, context, default=a) for a in top_args]
            fmt_vals = [_fmt_num(v) if isinstance(v, (int, float)) else str(v) for v in eval_vals]
            v0 = fmt_vals[0]
            v1 = fmt_vals[1] if len(fmt_vals) > 1 else v0
            v2 = fmt_vals[2] if len(fmt_vals) > 2 else v1

            if tag_name == "fscxy": return f"\\fscx{v0}\\fscy{v1}"
            if tag_name == "faxy": return f"\\fax{v0}\\fay{v1}"
            if tag_name == "xybord": return f"\\xbord{v0}\\ybord{v1}"
            if tag_name == "xyshad": return f"\\xshad{v0}\\yshad{v1}"
            if tag_name == "bs": return f"\\bord{v0}\\shad{v1}"
            if tag_name == "frxy": return f"\\frx{v0}\\fry{v1}"
            if tag_name == "frxz": return f"\\frx{v0}\\frz{v1}"
            if tag_name == "fryz": return f"\\fry{v0}\\frz{v1}"
            if tag_name == "frxyz": return f"\\frx{v0}\\fry{v1}\\frz{v2}"
            if tag_name == "frxyo": return f"\\org({ox},{oy})\\frx{v0}\\fry{v1}"
            if tag_name == "frxzo": return f"\\org({ox},{oy})\\frx{v0}\\frz{v1}"
            if tag_name == "fryzo": return f"\\org({ox},{oy})\\fry{v0}\\frz{v1}"
            if tag_name == "frxyzo": return f"\\org({ox},{oy})\\frx{v0}\\fry{v1}\\frz{v2}"
            if tag_name == "fscxyr":
                try:
                    rx = float(eval_vals[0])
                    ry = float(eval_vals[1])
                    return f"\\fscx{_fmt_num(style_scale_x_num * rx)}\\fscy{_fmt_num(style_scale_y_num * ry)}"
                except (ValueError, TypeError):
                    pass

        res = eval_python_expr(expr, context, default=expr)

        m_multi_c = re.match(r'^([1-4]+)c$', tag_name)
        if m_multi_c or tag_name == "c":
            c_val = _clean_ass_color(res)
            if tag_name == "c":
                return f"\\c{c_val}"
            return "".join(f"\\{digit}c{c_val}" for digit in m_multi_c.group(1))

        m_multi_a = re.match(r'^([1-4]+)a$', tag_name)
        if m_multi_a or tag_name in ("a", "alpha"):
            a_val = _format_ass_alpha(res)
            if tag_name in ("a", "alpha"):
                return f"\\alpha{a_val}"
            return "".join(f"\\{digit}a{a_val}" for digit in m_multi_a.group(1))

        fmt_res = _fmt_num(res) if isinstance(res, (int, float)) else str(res)

        # Auto-origin rotations (evaluated)
        if tag_name in ("fro", "frzo"): return f"\\org({ox},{oy})\\frz{fmt_res}"
        if tag_name == "frxo": return f"\\org({ox},{oy})\\frx{fmt_res}"
        if tag_name == "fryo": return f"\\org({ox},{oy})\\fry{fmt_res}"
        if tag_name == "frxyo": return f"\\org({ox},{oy})\\frx{fmt_res}\\fry{fmt_res}"
        if tag_name == "frxzo": return f"\\org({ox},{oy})\\frx{fmt_res}\\frz{fmt_res}"
        if tag_name == "fryzo": return f"\\org({ox},{oy})\\fry{fmt_res}\\frz{fmt_res}"
        if tag_name == "frxyzo": return f"\\org({ox},{oy})\\frx{fmt_res}\\fry{fmt_res}\\frz{fmt_res}"

        # Style ratio tags (evaluated)
        try:
            f_ratio = float(res)
            if tag_name == "fscxyr": return f"\\fscx{_fmt_num(style_scale_x_num * f_ratio)}\\fscy{_fmt_num(style_scale_y_num * f_ratio)}"
            if tag_name == "fscxr": return f"\\fscx{_fmt_num(style_scale_x_num * f_ratio)}"
            if tag_name == "fscyr": return f"\\fscy{_fmt_num(style_scale_y_num * f_ratio)}"
            if tag_name == "fsr": return f"\\fs{_fmt_num(style_fontsize_num * f_ratio)}"
        except (ValueError, TypeError):
            pass

        # Standard composite tags
        if tag_name == "fscxy": return f"\\fscx{fmt_res}\\fscy{fmt_res}"
        if tag_name == "faxy": return f"\\fax{fmt_res}\\fay{fmt_res}"
        if tag_name == "frxyz": return f"\\frx{fmt_res}\\fry{fmt_res}\\frz{fmt_res}"
        if tag_name == "frxy": return f"\\frx{fmt_res}\\fry{fmt_res}"
        if tag_name == "frxz": return f"\\frx{fmt_res}\\frz{fmt_res}"
        if tag_name == "fryz": return f"\\fry{fmt_res}\\frz{fmt_res}"
        if tag_name == "xybord": return f"\\xbord{fmt_res}\\ybord{fmt_res}"
        if tag_name == "xyshad": return f"\\xshad{fmt_res}\\yshad{fmt_res}"
        if tag_name == "bs": return f"\\bord{fmt_res}\\shad{fmt_res}"

        return f"\\{tag_name}{fmt_res}"

    single_tag_re = re.compile(r'\\(?!(?:pos|move|org|fad|fade|clip|iclip|t|te|ts|tc|tw)\b)([a-zA-Z0-9]+)\(')
    s = _replace_balanced_parens_tags(s, single_tag_re, _eval_single_tag)

    return s


def clean_tag_block_whitespace(block_str: str) -> str:
    """
    Cleans redundant whitespace within ASS override tag blocks {...} or tag sequences.

    Processing Rules:
    1. Trims leading and trailing whitespace immediately following '{' and preceding '}'.
    2. Removes whitespace separating contiguous tags (e.g. '\\pos(10,10)   \\blur2' -> '\\pos(10,10)\\blur2').
    3. Collapses spaces around commas and inside parentheses for non-vector tags
       (e.g. '\\pos( 10 , 20 )' -> '\\pos(10,20)', '\\t( 0 , 150 , \\blur2 )' -> '\\t(0,150,\\blur2)').
    4. Strictly preserves required spatial whitespace in vector clipping paths within '\\clip(m ...)' or '\\iclip(m ...)'.

    Args:
        block_str: ASS tag block or segment to sanitise.

    Returns:
        str: Compacted ASS tag block optimising file size and libass parsing efficiency.
    """
    if not block_str or "\\" not in block_str:
        return block_str

    s = block_str

    # Determine if 's' is a single contiguous block enclosed in {...}
    has_outer_braces = False
    if s.startswith("{") and s.endswith("}"):
        d = 0
        in_q = None
        match_idx = -1
        for idx, ch in enumerate(s):
            if in_q:
                if ch == '\\' and idx + 1 < len(s):
                    continue
                elif ch == in_q:
                    in_q = None
            elif ch in ('"', "'"):
                in_q = ch
            elif ch == '{':
                d += 1
            elif ch == '}':
                d -= 1
                if d == 0:
                    match_idx = idx
                    break
        if match_idx == len(s) - 1:
            has_outer_braces = True

    if has_outer_braces:
        inner = s[1:-1].strip()
    else:
        inner = s.strip()

    def _clean_parens(tag_name: str, args_str: str) -> str:
        args_clean_body = args_str.strip()
        if tag_name in ("clip", "iclip") and re.search(r'\bm\s+-?\d+', args_clean_body):
            args_clean = re.sub(r'[ \t]+', ' ', args_clean_body)
            return f"\\{tag_name}({args_clean})"

        args_clean = _replace_balanced_parens_tags(args_clean_body, re.compile(r'\\([a-zA-Z0-9]+)\('), _clean_parens)
        # Protect quoted function arguments from comma/space stripping
        args_clean = _transform_outside_quotes(args_clean, lambda txt: re.sub(r'\s*,\s*', ',', re.sub(r'\s*\\\s*', r'\\', txt)))
        return f"\\{tag_name}({args_clean})"

    inner = _replace_balanced_parens_tags(inner, re.compile(r'\\([a-zA-Z0-9]+)\('), _clean_parens)
    inner = _transform_outside_quotes(inner, lambda txt: re.sub(r'\s*\\\s*', r'\\', txt))
    inner = inner.strip()

    if has_outer_braces:
        return f"{{{inner}}}"
    return inner


def eval_string_template(template_str: Any, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Master pipeline evaluator for strings, expressions, and composite tags in Pyxis Nodes.

    Executes the 5-stage canonical evaluation pipeline:
    1. Unit shortcut expansion: Converts '10f' (frames to ms) and '2r' (resolution ratio scaling).
    2. Isolated ternary and callable reduction: Evaluates '(...)' expressions not preceded by ASS tags.
    3. Dark Tag expansion: Unrolls composite tags, style restoration ('~'), and stochastic calls ('\\tagR').
    4. Parenthesised tag evaluation: Computes formulas inside '\\pos(...)', '\\t(...)', '\\te(...)', etc.
    5. Tag block whitespace cleanup: Compacts whitespace between tags and within tag brackets.

    Args:
        template_str: Source template string or expression.
        context: Active DAG runtime context dictionary.

    Returns:
        str: Fully evaluated and sanitised ASS override string ready for dialogue rendering.
    """
    if template_str is None:
        return ""
    raw = str(template_str)
    if not raw:
        return ""

    if not isinstance(context, dict):
        context = {}

    res = expand_unit_shortcuts(raw, context)

    res = evaluate_isolated_ternaries(res, context)

    res = expand_custom_dark_tags(res, context)

    res = evaluate_tag_parentheses(res, context)

    res = clean_tag_block_whitespace(res)

    return res


def evaluate_ass_line_tag_blocks(ass_text: Any, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Evaluates exclusively the contents of override blocks {...} within a full ASS line.

    Features:
    - Robust brace-depth parser ignoring braces embedded inside quotes or sub-expressions.
    - Routes the interior of each '{...}' block through 'eval_string_template'.
    - Leaves plain text, punctuation, and external ASSdraw vector commands outside braces 100% untouched.

    Args:
        ass_text: Full ASS dialogue line or text string containing override tag blocks.
        context: Active DAG runtime context dictionary.

    Returns:
        str: Processed ASS line with evaluated override blocks and preserved dialogue text.
    """
    if ass_text is None:
        return ""
    raw = str(ass_text)
    if not raw or "{" not in raw:
        return raw

    if not isinstance(context, dict):
        context = {}

    out = []
    n = len(raw)
    i = 0
    while i < n:
        if raw[i] == '{':
            start = i
            d_paren = 0
            d_bracket = 0
            d_brace = 1
            in_q = None
            j = i + 1
            while j < n:
                ch = raw[j]
                if in_q:
                    if ch == '\\' and j + 1 < n:
                        j += 2
                        continue
                    elif ch == in_q:
                        in_q = None
                elif ch in ('"', "'"):
                    in_q = ch
                elif ch == '(':
                    d_paren += 1
                elif ch == ')':
                    d_paren = max(0, d_paren - 1)
                elif ch == '[':
                    d_bracket += 1
                elif ch == ']':
                    d_bracket = max(0, d_bracket - 1)
                elif ch == '{':
                    d_brace += 1
                elif ch == '}':
                    if d_paren == 0 and d_bracket == 0 and d_brace == 1:
                        d_brace = 0
                        j += 1
                        break
                    else:
                        d_brace = max(0, d_brace - 1)
                j += 1

            block = raw[start:j]
            out.append(eval_string_template(block, context))
            i = j
        else:
            out.append(raw[i])
            i += 1

    return "".join(out)


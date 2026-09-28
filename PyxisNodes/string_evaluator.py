r"""
Pyxis Nodes Engine - String Template & Expression Evaluator
Modular evaluator for strings, expressions, and composite tags.

Supports:
1. Direct evaluation inside ASS tag parentheses: \pos(syl.center + 10, syl.middle), \frz(j * 15), \t(0, 10f, \fscxy(150))
2. Dollar-prefixed variable substitution: $center, $middle, $syl.center, $line.color1, $start, $dur, $j, $maxj, etc.
3. Optional inline expressions: !expression! (e.g., !char.text.upper()!, !syl.duration / 2!)
4. Unit shortcuts: 10f (frames to ms), 1.5r (resolution ratio scaling)
5. Composite tag expansion (Dark Tags): \fscxy, \faxy, \frxyz, \xybord, \xyshad, \bs, \134c, \13c, \14c, \34c, \134a, \13a, \14a, \34a
6. Style restoration tags: \fscxy~, \1c~, \134c~, \bs~, etc.
7. Stochastic tags: \1cR(), \frzR(-30, 30), \fscxyR(120, 150), etc.
"""

from __future__ import annotations

import re
import math
import random
from typing import Any, Dict, Optional

_AST_EXPR_CACHE: Dict[str, Any] = {}
_STATIC_STRING_GLOBALS: Optional[Dict[str, Any]] = None


def _get_eval_globals() -> Dict[str, Any]:
    global _STATIC_STRING_GLOBALS
    if _STATIC_STRING_GLOBALS is not None:
        return _STATIC_STRING_GLOBALS

    import math
    safe_builtins = {
        "min": min, "max": max, "abs": abs, "round": round,
        "int": int, "float": float, "pow": pow, "sum": sum,
        "len": len, "str": str, "bool": bool, "range": range,
        "list": list, "dict": dict, "tuple": tuple, "set": set
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
        from nodes.math_nodes import math_random_master
        g["R"] = math_random_master
        g["Rs"] = math_random_master
        g["Rc"] = math_random_master
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

    _STATIC_STRING_GLOBALS = g
    return _STATIC_STRING_GLOBALS


def _format_ass_alpha(val: Any) -> str:
    """Formats an alpha value into canonical ASS alpha hex &HXX& (00 to FF)."""
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
    """Formats a color value into canonical ASS color hex &HBBGGRR&."""
    if col is None:
        return "&H00FFFFFF&"
    s = str(col).strip()
    if not s:
        return "&H00FFFFFF&"
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
    """Formats numbers cleanly for ASS tags (integers without .0, floats up to 3 decimals)."""
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

    eval_locals["audio_rms"] = lambda *args, **kwargs: eval_globals.get("audio_rms", lambda **kw: 0.0)(*args, context=context, **kwargs)
    eval_locals["audio_peak"] = lambda *args, **kwargs: eval_globals.get("audio_peak", lambda **kw: 0.0)(*args, context=context, **kwargs)
    eval_locals["audio_band"] = lambda *args, **kwargs: eval_globals.get("audio_band", lambda **kw: 0.0)(*args, context=context, **kwargs)
    eval_locals["audio_fft"] = lambda *args, **kwargs: eval_globals.get("audio_fft", lambda **kw: 0.0)(*args, context=context, **kwargs)

    if "R" in eval_globals:
        eval_locals["R"] = lambda min_v=0, max_v=100, step_v=1: eval_globals["R"](context, modo="R", min_val=min_v, max_val=max_v, step=step_v) if callable(eval_globals["R"]) and "modo" in eval_globals["R"].__code__.co_varnames else eval_globals["R"](min_v, max_v, step_v)
        eval_locals["Rs"] = lambda min_v=0, max_v=100: eval_globals["Rs"](context, modo="Rs", min_val=min_v, max_val=max_v) if callable(eval_globals["Rs"]) and "modo" in eval_globals["Rs"].__code__.co_varnames else eval_globals["Rs"](min_v, max_v)
        eval_locals["Rc"] = lambda min_v=0, max_v=100: eval_globals["Rc"](context, modo="Rc", min_val=min_v, max_val=max_v) if callable(eval_globals["Rc"]) and "modo" in eval_globals["Rc"].__code__.co_varnames else eval_globals["Rc"](min_v, max_v)
        eval_locals["rand"] = eval_locals["R"]

    if "active_unit" in eval_locals and eval_locals["active_unit"]:
        unit_obj = eval_locals["active_unit"]
        if "syl" not in eval_locals or eval_locals["syl"] is None:
            eval_locals["syl"] = unit_obj
        if "line" not in eval_locals and hasattr(unit_obj, "line") and unit_obj.line:
            eval_locals["line"] = unit_obj.line

    val_max_j = eval_locals.get("maxj", eval_locals.get("fx_n", 1))
    eval_locals["maxj"] = val_max_j
    if "maxloop" not in eval_locals:
        eval_locals["maxloop"] = eval_locals.get("max_loop", val_max_j)
    if "max_loop" not in eval_locals:
        eval_locals["max_loop"] = eval_locals["maxloop"]
    if "j" not in eval_locals and "fx_i" in eval_locals:
        eval_locals["j"] = eval_locals["fx_i"]
    if "d_i" not in eval_locals and "fx_i" in eval_locals:
        eval_locals["d_i"] = eval_locals["fx_i"]
    if "d_n" not in eval_locals and "fx_n" in eval_locals:
        eval_locals["d_n"] = eval_locals["fx_n"]
    if "d_max" not in eval_locals:
        eval_locals["d_max"] = eval_locals.get("d_n", eval_locals.get("maxloop", 1))

    if "fx" not in eval_locals or eval_locals["fx"] is None or not isinstance(eval_locals["fx"], FxContext):
        eval_locals["fx"] = FxContext(eval_locals)

    def _remember(key, val, cond=True):
        if cond:
            mem = eval_locals.setdefault("memory", {})
            mem[str(key)] = val
        return val

    def _recall(key, default=""):
        mem = eval_locals.get("memory", {})
        return mem.get(str(key), default)

    eval_locals["remember"] = _remember
    eval_locals["recall"] = _recall

    try:
        from nodes.code_nodes import PyxisTimeModifier
        from nodes.time_nodes import time_lead_in, time_lead_out, time_middle_1, time_middle_2, time_loop_1, time_loop_2
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
    except Exception:
        pass

    return eval_locals


def eval_python_expr(expr_str: str, context: Optional[Dict[str, Any]] = None, default: Any = "") -> Any:
    """Safely evaluates a Python expression with AST cache and contextual variables."""
    if not expr_str:
        return default
    expr_clean = expr_str.strip()
    if not expr_clean:
        return default

    expr_clean = re.sub(r'&[hH]([0-9a-fA-F]+)&?', r'0x\1', expr_clean)

    frame_dur = 41.708
    ratio = 1.0
    if isinstance(context, dict):
        frame_dur = float(context.get("frame_dur", 41.708))
        ratio = float(context.get("ratio", context.get("module", 1.0)))

    expr_clean = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*f\b', rf'(\1 * {frame_dur})', expr_clean)
    expr_clean = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*r\b', rf'(\1 * {ratio})', expr_clean)
    expr_clean = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*(li|lo|m1|m2|l1|l2)\b', r'\1 * \2', expr_clean)

    try:
        code_obj = _AST_EXPR_CACHE.get(expr_clean)
        if code_obj is None:
            code_obj = compile(expr_clean, "<pyxis_string_eval>", "eval")
            _AST_EXPR_CACHE[expr_clean] = code_obj

        eval_globals = _get_eval_globals()
        eval_locals = _prepare_eval_locals(context)
        res = eval(code_obj, eval_globals, eval_locals)
        return res if res is not None else default
    except Exception as e:
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
        frame_dur = float(context.get("frame_dur", 41.708))
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

    pattern = r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)([fr])(?![a-zA-Z0-9_])'
    return re.sub(pattern, _replace_unit, text)


def substitute_dollar_vars(text: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Sustituye variables con sintaxis $var o ${var}.
    Soporta aliases de auto4, propiedades con punto ($syl.center, $line.color1)
    y escape con \\$ o $$.
    """
    if not text or "$" not in text:
        return text

    escaped_text = text.replace(r"\$", "\x01ESC_DOLLAR\x01").replace("$$", "\x01ESC_DOLLAR\x01")

    if not isinstance(context, dict):
        context = {}

    active_unit = context.get("active_unit") or context.get("syl") or context.get("char") or context.get("word")
    active_line = context.get("active_line", context.get("line"))
    if not active_line and hasattr(active_unit, "line") and getattr(active_unit, "line", None):
        active_line = getattr(active_unit, "line")
    if not active_line and active_unit and hasattr(active_unit, "style_name"):
        active_line = active_unit

    def _clean_color_str(col: Any) -> str:
        s_col = str(col).strip()
        m = re.findall(r'[0-9a-fA-F]{2}', s_col)
        if len(m) >= 4:
            return f"&H{''.join(m[-3:])}&"
        return s_col

    def _get_var_value(var_name: str) -> str:
        v = var_name.strip()
        v_lower = v.lower()

        if v in context:
            val = context[v]
            if isinstance(val, (int, float)):
                if "alpha" in v_lower or v_lower in ("a1", "a2", "a3", "a4"):
                    return _format_ass_alpha(val)
                return _fmt_num(val)
            if "color" in v_lower:
                return _clean_ass_color(val)
            if "alpha" in v_lower or v_lower in ("a1", "a2", "a3", "a4"):
                return _format_ass_alpha(val)
            return str(val)

        if v_lower in ("start", "st"):
            st = getattr(active_unit, "start_time", context.get("start_time", context.get("st", 0.0))) if active_unit else context.get("start_time", context.get("st", 0.0))
            return _fmt_num(st)
        if v_lower in ("end", "et"):
            et = getattr(active_unit, "end_time", context.get("end_time", context.get("et", 0.0))) if active_unit else context.get("end_time", context.get("et", 0.0))
            return _fmt_num(et)
        if v_lower == "dur":
            dur = getattr(active_unit, "dur", getattr(active_unit, "duration", context.get("dur", context.get("duration", 0.0)))) if active_unit else context.get("dur", context.get("duration", 0.0))
            return _fmt_num(dur)
        if v_lower == "kdur":
            dur = getattr(active_unit, "dur", getattr(active_unit, "duration", context.get("dur", context.get("duration", 0.0)))) if active_unit else context.get("dur", context.get("duration", 0.0))
            return _fmt_num(dur / 10.0)
        if v_lower == "mid":
            st = getattr(active_unit, "start_time", context.get("start_time", 0.0)) if active_unit else context.get("start_time", 0.0)
            dur = getattr(active_unit, "dur", getattr(active_unit, "duration", context.get("dur", 0.0))) if active_unit else context.get("dur", 0.0)
            return _fmt_num(st + dur / 2.0)
        if v_lower in ("left", "right", "center", "top", "middle", "bottom", "width", "height", "x", "y"):
            val = getattr(active_unit, v_lower, context.get(v_lower, context.get(f"val_{v_lower}", 0.0))) if active_unit else context.get(v_lower, context.get(f"val_{v_lower}", 0.0))
            return _fmt_num(val)
        if v_lower == "si":
            syl_obj = context.get("syl", active_unit)
            return str(getattr(syl_obj, "i", 1) if syl_obj else 1)
        if v_lower == "ci":
            char_obj = context.get("char", active_unit)
            return str(getattr(char_obj, "i", 1) if char_obj else 1)
        if v_lower == "wi":
            word_obj = context.get("word", active_unit)
            return str(getattr(word_obj, "i", 1) if word_obj else 1)
        if v_lower == "li":
            line_obj = active_line if active_line else active_unit
            return str(getattr(line_obj, "i", 1) if line_obj else 1)

        try:
            from node_engine import _eval_sys_var
            res = _eval_sys_var(v, context)
            if res != "":
                if isinstance(res, (int, float)):
                    if "alpha" in v_lower or v_lower in ("a1", "a2", "a3", "a4"):
                        return _format_ass_alpha(res)
                    return _fmt_num(res)
                if "color" in v_lower:
                    return _clean_ass_color(res)
                if "alpha" in v_lower or v_lower in ("a1", "a2", "a3", "a4"):
                    return _format_ass_alpha(res)
                return str(res)
        except ImportError:
            pass

        return f"${var_name}"

    def _replace_var(match: re.Match) -> str:
        var_name = match.group(1) or match.group(2)
        return _get_var_value(var_name)

    pattern = r'\$(?:\{([a-zA-Z0-9_\.]+)\}|([a-zA-Z0-9_\.]+))'
    result = re.sub(pattern, _replace_var, escaped_text)

    return result.replace("\x01ESC_DOLLAR\x01", "$")


def evaluate_inline_bang_expressions(text: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Evalúa expresiones inline delimitadas por signos de exclamación !expresion!.
    Soporta escape con \\! o !!.
    """
    if not text or "!" not in text:
        return text

    escaped_text = text.replace(r"\!", "\x01ESC_BANG\x01").replace("!!", "\x01ESC_BANG\x01")

    def _replace_bang(match: re.Match) -> str:
        expr = match.group(1)
        res = eval_python_expr(expr, context, default="")
        return _fmt_num(res) if isinstance(res, (int, float)) else str(res)

    pattern = r'!(.*?)!'
    result = re.sub(pattern, _replace_bang, escaped_text)
    return result.replace("\x01ESC_BANG\x01", "!")


def _get_context_origin(context: Optional[Dict[str, Any]]) -> tuple[str, str]:
    """Obtiene las coordenadas cartesianas (X, Y) del origen / pivote del contexto activo."""
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
    """Extrae de manera segura las propiedades métricas del estilo del contexto activo."""
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
        "angle": _fmt_num(_get_prop("angle", 0)),
    }


def expand_custom_dark_tags(text: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Expande tags compuestos, tags de restauración (~), tags estocásticos (\\tagR)
    y Dark Tags de rotación auto-origen y ratio al estándar ASS puro.
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

    style_scale_x_num = style_props["scale_x"]
    style_scale_y_num = style_props["scale_y"]
    style_fontsize_num = style_props["fontsize"]

    style_color1_clean = _clean_ass_color(style_color1)
    style_color2_clean = _clean_ass_color(style_color2)
    style_color3_clean = _clean_ass_color(style_color3)
    style_color4_clean = _clean_ass_color(style_color4)

    s = text

    def _replace_stochastic_tag(match: re.Match) -> str:
        tag_name = match.group(1)
        args_str = match.group(2).strip()
        args = [a.strip() for a in args_str.split(",") if a.strip()] if args_str else []

        eval_globals = _get_eval_globals()
        eval_locals = _prepare_eval_locals(context)

        m_multi_c = re.match(r'^([1-4]+)c$', tag_name)
        if m_multi_c or tag_name == "c":
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

    s = re.sub(r'\\([a-zA-Z0-9]+)R\((.*?)\)', _replace_stochastic_tag, s)

    tag_restorations = [
        (r'\c~', f"\\c{style_color1_clean}"),
        (r'\alpha~', r"\alpha&H00&"),
        (r'\fscxy~', f"\\fscx{style_scale_x}\\fscy{style_scale_y}"),
        (r'\fscx~', f"\\fscx{style_scale_x}"),
        (r'\fscy~', f"\\fscy{style_scale_y}"),
        (r'\fs~', f"\\fs{style_fontsize}"),
        (r'\fsp~', f"\\fsp{style_spacing}"),
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
        (r'\frxy~', r"\frx0\\fry0"),
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
    s = re.sub(rf'\\([1-4]+)c{color_val_pat}', lambda m: "".join(f"\\{d}c{_clean_ass_color(m.group(2))}" for d in m.group(1)), s)

    alpha_val_pat = r'(&[hH]?[0-9a-fA-F]+&?|[0-9a-fA-F]{2}|\d+)(?=[\\\}\s]|$)'
    s = re.sub(rf'\\([1-4]+)a{alpha_val_pat}', lambda m: "".join(f"\\{d}a{_format_ass_alpha(m.group(2))}" for d in m.group(1)), s)

    # Convert standalone decimal alpha tags (e.g. \4a100, \alpha255, \1a0, \2a128) to canonical ASS &HXX&
    s = re.sub(r'\\(alpha|[1-4]a)(\d{1,3})(?=[\\\}\s]|$)', lambda m: f"\\{m.group(1)}{_format_ass_alpha(m.group(2))}", s)

    return s


def evaluate_tag_parentheses(text: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Evalúa automáticamente cualquier expresión matemática, función o variable
    dentro de paréntesis de tags ASS: \\pos(...), \\move(...), \\frz(...), \\fscxy(...), \\t(...), \\te(...), etc.
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

            time_args = [a.strip() for a in times_part.split(",") if a.strip()]
            eval_nums = [float(eval_python_expr(arg, context, default=0)) for arg in time_args]

            if tag_prefix == "te":
                if len(eval_nums) >= 2:
                    t1, t2 = eval_nums[0], eval_nums[1]
                    st = max(0.0, float(total_dur) - t2)
                    et = max(0.0, float(total_dur) - t1)
                    return f"\\t({_fmt_num(st)}, {_fmt_num(et)}, {eval_tags})"
                elif len(eval_nums) == 1:
                    t = eval_nums[0]
                    st = max(0.0, float(total_dur) - t)
                    return f"\\t({_fmt_num(st)}, {_fmt_num(total_dur)}, {eval_tags})"
            elif tag_prefix in ("ts", "tc", "tw"):
                target_obj = context.get("syl" if tag_prefix == "ts" else ("char" if tag_prefix == "tc" else "word"), active_unit)
                base_st = float(getattr(target_obj, "start_time", 0.0) if target_obj else 0.0)
                if len(eval_nums) >= 2:
                    st = base_st + eval_nums[0]
                    et = base_st + eval_nums[1]
                    return f"\\t({_fmt_num(st)}, {_fmt_num(et)}, {eval_tags})"
                elif len(eval_nums) == 1:
                    st = base_st
                    et = base_st + eval_nums[0]
                    return f"\\t({_fmt_num(st)}, {_fmt_num(et)}, {eval_tags})"

            eval_times = [_fmt_num(n) for n in eval_nums]
            return f"\\t({', '.join(eval_times)}, {eval_tags})"
        else:
            args = [a.strip() for a in body.split(",") if a.strip()]
            eval_args = [_fmt_num(eval_python_expr(a, context, default=a)) for a in args]
            return f"\\t({', '.join(eval_args)})"

    s = re.sub(r'\\(te|ts|tc|tw)\((.*?)\)(?=[\\\}\s]|$)', lambda m: _eval_context_time_transform(m.group(1), m.group(2)), s)

    def _eval_t_tag(match: re.Match) -> str:
        body = match.group(1).strip()
        tag_start_idx = body.find("\\")
        if tag_start_idx != -1:
            times_part = body[:tag_start_idx].strip().rstrip(",")
            tags_part = body[tag_start_idx:].strip()

            eval_tags = expand_custom_dark_tags(tags_part, context)
            eval_tags = evaluate_tag_parentheses(eval_tags, context)

            if not times_part:
                return f"\\t({eval_tags})"

            time_args = [a.strip() for a in times_part.split(",") if a.strip()]
            eval_times = []
            for arg in time_args:
                res = eval_python_expr(arg, context, default=arg)
                eval_times.append(_fmt_num(res))

            return f"\\t({', '.join(eval_times)}, {eval_tags})"
        else:
            args = [a.strip() for a in body.split(",") if a.strip()]
            eval_args = []
            for arg in args:
                res = eval_python_expr(arg, context, default=arg)
                eval_args.append(_fmt_num(res))
            return f"\\t({', '.join(eval_args)})"

    s = re.sub(r'\\t\((.*?)\)(?=[\\\}\s]|$)', _eval_t_tag, s)

    def _eval_clip_tag(match: re.Match) -> str:
        tag_name = match.group(1)
        args_str = match.group(2).strip()

        if "m " in args_str or "center" in args_str.lower():
            if "center" in args_str.lower():
                center_x = getattr(active_unit, "center", context.get("x", 0.0))
                middle_y = getattr(active_unit, "middle", context.get("y", 0.0))
                args_clean = re.sub(r'\bcenter\b', f"{center_x}, {middle_y}", args_str, flags=re.IGNORECASE)
                return f"\\{tag_name}({args_clean})"
            return f"\\{tag_name}({args_str})"

        has_space = ", " in args_str
        sep = ", " if has_space else ","
        args = [a.strip() for a in args_str.split(",") if a.strip()]
        if len(args) in (2, 4):
            eval_args = [_fmt_num(eval_python_expr(a, context, a)) for a in args]
            return f"\\{tag_name}({sep.join(eval_args)})"

        return f"\\{tag_name}({args_str})"

    s = re.sub(r'\\(i?clip)\((.*?)\)', _eval_clip_tag, s)

    def _eval_multi_arg_tag(match: re.Match) -> str:
        tag_name = match.group(1)
        args_str = match.group(2)
        has_space = ", " in args_str
        sep = ", " if has_space else ","
        args = [a.strip() for a in args_str.split(",") if a.strip()]
        eval_args = [_fmt_num(eval_python_expr(a, context, a)) for a in args]
        return f"\\{tag_name}({sep.join(eval_args)})"

    s = re.sub(r'\\(pos|move|org|fad|fade)\((.*?)\)', _eval_multi_arg_tag, s)

    def _eval_single_tag(match: re.Match) -> str:
        tag_name = match.group(1)
        expr = match.group(2).strip()
        res = eval_python_expr(expr, context, default=expr)

        m_multi_c = re.match(r'^([1-4]+)c$', tag_name)
        if m_multi_c or tag_name == "c":
            c_val = _clean_ass_color(str(res)) if not isinstance(res, (int, float)) else _clean_ass_color(f"&H{int(res):06X}&")
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

    single_tag_pat = r'\\(?!(?:pos|move|org|fad|fade|clip|iclip|t|te|ts|tc|tw)\b)([a-zA-Z0-9]+)\(([^()]*?)\)'
    s = re.sub(single_tag_pat, _eval_single_tag, s)

    return s


def clean_tag_block_whitespace(block_str: str) -> str:
    """
    Limpia los espacios en blanco innecesarios dentro de bloques de etiquetas ASS {...} o secuencias de tags:
    1. Limpia espacios iniciales/finales tras '{' y antes de '}'.
    2. Elimina espacios en blanco entre etiquetas continuas (ej. '\\pos(10,10)   \\blur2' -> '\\pos(10,10)\\blur2').
    3. Limpia espacios dentro de paréntesis y alrededor de comas en tags no vectoriales (ej. '\\pos( 10 , 20 )' -> '\\pos(10,20)', '\\t( 0 , 150 , \\blur2 )' -> '\\t(0,150,\\blur2)').
    4. Preserva intactos los espacios necesarios en dibujos vectoriales dentro de \\clip(m ...) o \\iclip(m ...).
    """
    if not block_str or "\\" not in block_str:
        return block_str

    s = block_str

    has_outer_braces = s.startswith("{") and s.endswith("}")
    if has_outer_braces:
        inner = s[1:-1].strip()
    else:
        inner = s.strip()

    def _clean_parens(match: re.Match) -> str:
        tag_name = match.group(1)
        args_str = match.group(2).strip()
        if tag_name in ("clip", "iclip") and re.search(r'\bm\s+-?\d+', args_str):
            args_clean = re.sub(r'[ \t]+', ' ', args_str)
            return f"\\{tag_name}({args_clean})"
        
        args_clean = re.sub(r'\s*,\s*', ',', args_str)
        args_clean = re.sub(r'\s*\\\s*', r'\\', args_clean)
        args_clean = re.sub(r'\s*([a-zA-Z0-9&]+)\s*\\', r'\1\\', args_clean)
        return f"\\{tag_name}({args_clean})"

    inner = re.sub(r'\\([a-zA-Z0-9]+)\((.*?)\)', _clean_parens, inner)
    inner = re.sub(r'\s*\\\s*', r'\\', inner)
    inner = inner.strip()

    if has_outer_braces:
        return f"{{{inner}}}"
    return inner


def eval_string_template(template_str: Any, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Función maestra de evaluación de plantillas y cadenas para Pyxis Nodes.
    Ejecuta el pipeline completo:
    1. Preprocesamiento de atajos de unidad (10f, 2r).
    2. Sustitución de variables ($center, $line.color1, etc.).
    3. Evaluación de expresiones inline (!expresion!).
    4. Expansión de Dark Tags, Restauración (~) y Estocásticos (\\tagR).
    5. Evaluación de expresiones directas en paréntesis ASS (\\pos(syl.center + 10, ...)).
    6. Limpieza final de espacios en blanco entre tags y dentro de paréntesis.
    """
    if template_str is None:
        return ""
    raw = str(template_str)
    if not raw:
        return ""

    if not isinstance(context, dict):
        context = {}

    res = expand_unit_shortcuts(raw, context)

    res = substitute_dollar_vars(res, context)

    res = evaluate_inline_bang_expressions(res, context)

    res = expand_custom_dark_tags(res, context)

    res = evaluate_tag_parentheses(res, context)

    res = clean_tag_block_whitespace(res)

    return res


_TAG_BLOCK_BRACKETS_RE = re.compile(r'\{[^{}]*\}')


def evaluate_ass_line_tag_blocks(ass_text: Any, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Evalúa de forma segura y exclusiva el contenido de los bloques de etiquetas {...}
    en una línea ASS final, resolviendo variables, expresiones y tags dinámicos,
    limpiando espacios innecesarios y dejando el texto plano y los trazados
    de ASSdraw fuera de las llaves 100% intactos.
    """
    if ass_text is None:
        return ""
    raw = str(ass_text)
    if not raw or "{" not in raw:
        return raw

    if not isinstance(context, dict):
        context = {}

    def _eval_block(match: re.Match) -> str:
        block = match.group(0)
        return eval_string_template(block, context)

    return _TAG_BLOCK_BRACKETS_RE.sub(_eval_block, raw)


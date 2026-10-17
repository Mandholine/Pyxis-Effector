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

"""Inline script code and variable execution nodes."""

import math
import sys
from collections import OrderedDict
from decorators import system_node

_COMPILED_SCRIPT_CACHE = OrderedDict()
_MAX_COMPILED_SCRIPT_CACHE = 512

def clear_compiled_script_cache():
    """Clears cached compiled script code and AST structures."""
    _COMPILED_SCRIPT_CACHE.clear()
_STATIC_BASE_SCOPE = None

def _get_static_base_scope():
    global _STATIC_BASE_SCOPE
    if _STATIC_BASE_SCOPE is not None:
        return _STATIC_BASE_SCOPE

    scope = {}
    import builtins
    math_fns = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    scope.update(math_fns)
    scope.update({
        "abs": abs, "min": min, "max": max, "round": round,
        "int": int, "float": float, "str": str, "len": len, "bool": bool,
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

    try:
        from nodes.shape_nodes import (
            shape_circle, shape_square, shape_rectangle, shape_triangle, shape_rhombus,
            shape_rounded_corners, shape_pentagon, shape_hexagon, shape_octagon,
            shape_star, shape_heart, resolve_shape_value
        )
        scope.update({
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
            "resolve_shape": lambda name, ctx=None: resolve_shape_value(name, ctx)
        })
    except ImportError:
        pass

    from decorators import NODE_REGISTRY
    for k, v in NODE_REGISTRY.items():
        fn_name = v.__name__
        scope[fn_name] = v

    _STATIC_BASE_SCOPE = scope
    return _STATIC_BASE_SCOPE


def _pyxis_fmt_num(val):
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


def _pyxis_pos(x, y):
    return f"\\pos({_pyxis_fmt_num(x)},{_pyxis_fmt_num(y)})"


def _pyxis_move(x1, y1, x2, y2, t1=None, t2=None):
    if t1 is None:
        return f"\\move({_pyxis_fmt_num(x1)},{_pyxis_fmt_num(y1)},{_pyxis_fmt_num(x2)},{_pyxis_fmt_num(y2)})"
    return f"\\move({_pyxis_fmt_num(x1)},{_pyxis_fmt_num(y1)},{_pyxis_fmt_num(x2)},{_pyxis_fmt_num(y2)},{_pyxis_fmt_num(t1)},{_pyxis_fmt_num(t2)})"


def _pyxis_org(x, y):
    return f"\\org({_pyxis_fmt_num(x)},{_pyxis_fmt_num(y)})"


def _pyxis_fad(in_dur, out_dur):
    return f"\\fad({_pyxis_fmt_num(in_dur)},{_pyxis_fmt_num(out_dur)})"


def _pyxis_fade(a1, a2, a3, t1, t2, t3, t4):
    return f"\\fade({_pyxis_fmt_num(a1)},{_pyxis_fmt_num(a2)},{_pyxis_fmt_num(a3)},{_pyxis_fmt_num(t1)},{_pyxis_fmt_num(t2)},{_pyxis_fmt_num(t3)},{_pyxis_fmt_num(t4)})"


def _pyxis_clip(*args):
    if len(args) == 4:
        return f"\\clip({_pyxis_fmt_num(args[0])},{_pyxis_fmt_num(args[1])},{_pyxis_fmt_num(args[2])},{_pyxis_fmt_num(args[3])})"
    elif len(args) == 2:
        return f"\\clip({_pyxis_fmt_num(args[0])},{args[1]})"
    elif len(args) == 1:
        return f"\\clip({args[0]})"
    return "\\clip()"


def _pyxis_iclip(*args):
    if len(args) == 4:
        return f"\\iclip({_pyxis_fmt_num(args[0])},{_pyxis_fmt_num(args[1])},{_pyxis_fmt_num(args[2])},{_pyxis_fmt_num(args[3])})"
    elif len(args) == 2:
        return f"\\iclip({_pyxis_fmt_num(args[0])},{args[1]})"
    elif len(args) == 1:
        return f"\\iclip({args[0]})"
    return "\\iclip()"


def _pyxis_c1(color):
    from nodes.tag_nodes import _clean_color
    return f"\\1c{_clean_color(color)}"


def _pyxis_c2(color):
    from nodes.tag_nodes import _clean_color
    return f"\\2c{_clean_color(color)}"


def _pyxis_c3(color):
    from nodes.tag_nodes import _clean_color
    return f"\\3c{_clean_color(color)}"


def _pyxis_c4(color):
    from nodes.tag_nodes import _clean_color
    return f"\\4c{_clean_color(color)}"


def _pyxis_a1(val):
    from nodes.tag_nodes import _clean_alpha
    return f"\\1a{_clean_alpha(val)}"


def _pyxis_a2(val):
    from nodes.tag_nodes import _clean_alpha
    return f"\\2a{_clean_alpha(val)}"


def _pyxis_a3(val):
    from nodes.tag_nodes import _clean_alpha
    return f"\\3a{_clean_alpha(val)}"


def _pyxis_a4(val):
    from nodes.tag_nodes import _clean_alpha
    return f"\\4a{_clean_alpha(val)}"


def _pyxis_alpha(val):
    from nodes.tag_nodes import _clean_alpha
    return f"\\alpha{_clean_alpha(val)}"


def _pyxis_trans(*args):
    if len(args) == 1:
        return f"\\t({args[0]})"
    elif len(args) == 3:
        return f"\\t({_pyxis_fmt_num(args[0])},{_pyxis_fmt_num(args[1])},{args[2]})"
    elif len(args) >= 4:
        return f"\\t({_pyxis_fmt_num(args[0])},{_pyxis_fmt_num(args[1])},{_pyxis_fmt_num(args[2])},{args[3]})"
    return "\\t()"


def _pyxis_fscx(v):
    return f"\\fscx({_pyxis_fmt_num(v)})"


def _pyxis_fscy(v):
    return f"\\fscy({_pyxis_fmt_num(v)})"


def _pyxis_fscxy(x, y=None):
    if y is None:
        return f"\\fscx({_pyxis_fmt_num(x)})\\fscy({_pyxis_fmt_num(x)})"
    return f"\\fscx({_pyxis_fmt_num(x)})\\fscy({_pyxis_fmt_num(y)})"


def _pyxis_frz(v):
    return f"\\frz({_pyxis_fmt_num(v)})"


def _pyxis_frx(v):
    return f"\\frx({_pyxis_fmt_num(v)})"


def _pyxis_fry(v):
    return f"\\fry({_pyxis_fmt_num(v)})"


def _pyxis_fax(v):
    return f"\\fax({_pyxis_fmt_num(v)})"


def _pyxis_fay(v):
    return f"\\fay({_pyxis_fmt_num(v)})"


def _pyxis_bord(v):
    return f"\\bord({_pyxis_fmt_num(v)})"


def _pyxis_shad(v):
    return f"\\shad({_pyxis_fmt_num(v)})"


def _pyxis_blur(v):
    return f"\\blur({_pyxis_fmt_num(v)})"


def _pyxis_an(v):
    return f"\\an({_pyxis_fmt_num(v)})"


def _pyxis_ass_color(r, g=None, b=None):
    if g is not None and b is not None:
        from utils import rgb_to_ass_color
        return rgb_to_ass_color(int(r), int(g), int(b))
    from nodes.tag_nodes import _clean_color
    return _clean_color(r)


def _pyxis_ass_alpha(a):
    from nodes.tag_nodes import _clean_alpha
    return _clean_alpha(a)


def _pyxis_random_color():
    import random
    return f"&H{random.randint(0, 255):02X}{random.randint(0, 255):02X}{random.randint(0, 255):02X}&"


def _pyxis_random_alpha():
    import random
    return f"&H{random.randint(0, 255):02X}&"


def _pyxis_map_range(val, in_min, in_max, out_min, out_max):
    try:
        v = float(val)
        imn, imx = float(in_min), float(in_max)
        omn, omx = float(out_min), float(out_max)
        if imx == imn:
            return omn
        t = (v - imn) / (imx - imn)
        return omn + t * (omx - omn)
    except Exception:
        return float(out_min)


def _pyxis_ease_in(t):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Easing", operation="ease_in", t=t)


def _pyxis_ease_out(t):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Easing", operation="ease_out", t=t)


def _pyxis_ease_in_out(t):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Easing", operation="ease_in_out", t=t)


def _pyxis_cubic_in(t):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Easing", operation="cubic_in", t=t)


def _pyxis_cubic_out(t):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Easing", operation="cubic_out", t=t)


def _pyxis_elastic(t):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Easing", operation="elastic", t=t)


def _pyxis_bounce(t):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Easing", operation="bounce", t=t)


def _pyxis_back(t):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Easing", operation="back", t=t)


def _pyxis_sine_wave(t, freq=1.0, amp=1.0, offset=0.0):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Waves", operation="sine", t=t, freq=freq, amp=amp, Offset=offset)


def _pyxis_square_wave(t, freq=1.0, amp=1.0, offset=0.0):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Waves", operation="square", t=t, freq=freq, amp=amp, Offset=offset)


def _pyxis_triangle_wave(t, freq=1.0, amp=1.0, offset=0.0):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Waves", operation="triangle", t=t, freq=freq, amp=amp, Offset=offset)


def _pyxis_sawtooth_wave(t, freq=1.0, amp=1.0, offset=0.0):
    from nodes.math_nodes import eval_math_node
    return eval_math_node(category="Waves", operation="sawtooth", t=t, freq=freq, amp=amp, Offset=offset)


def _pyxis_polar(angle, dist):
    rad = math.radians(float(angle))
    d = float(dist)
    return d * math.cos(rad), d * math.sin(rad)


def _pyxis_bezier(t, p0, p1, p2, p3):
    tf = float(t)
    u = 1.0 - tf
    return u**3 * float(p0) + 3 * u**2 * tf * float(p1) + 3 * u * tf**2 * float(p2) + tf**3 * float(p3)


def _pyxis_ipol(t, a, b, curve="linear"):
    tf = max(0.0, min(1.0, float(t)))
    af, bf = float(a), float(b)
    c = str(curve).lower()
    if c in ("easein", "ease_in"):
        factor = tf * tf
    elif c in ("easeout", "ease_out"):
        factor = 1.0 - (1.0 - tf) ** 2
    elif c in ("easeinout", "ease_in_out"):
        factor = 2.0 * tf * tf if tf < 0.5 else 1.0 - math.pow(-2.0 * tf + 2.0, 2) / 2.0
    elif c in ("cubicin", "cubic_in"):
        factor = tf ** 3
    elif c in ("cubicout", "cubic_out"):
        factor = 1.0 - (1.0 - tf) ** 3
    else:
        factor = tf
    return af + (bf - af) * factor


def _pyxis_time_to_frame(ms, fps=23.976):
    try:
        return int(float(ms) / (1000.0 / float(fps)))
    except Exception:
        return 0


def _pyxis_duration(obj=None, context=None):
    if obj is not None:
        if hasattr(obj, "duration"):
            return float(getattr(obj, "duration"))
        if hasattr(obj, "dur"):
            return float(getattr(obj, "dur"))
    if isinstance(context, dict):
        return float(context.get("dur", context.get("duration", 0.0)))
    return 0.0


def _pyxis_parse_ass_time(time_str):
    try:
        s = str(time_str).strip()
        parts = s.split(":")
        if len(parts) == 3:
            h = int(parts[0])
            m = int(parts[1])
            s_cs = parts[2].split(".")
            sec = int(s_cs[0])
            cs = int(s_cs[1]) if len(s_cs) > 1 else 0
            return (h * 3600 + m * 60 + sec) * 1000 + cs * 10
    except Exception:
        pass
    return 0


def _pyxis_format_ass_time(ms):
    try:
        total_cs = int(round(float(ms) / 10.0))
        cs = total_cs % 100
        total_sec = total_cs // 100
        sec = total_sec % 60
        total_min = total_sec // 60
        mins = total_min % 60
        hours = total_min // 60
        return f"{hours}:{mins:02d}:{sec:02d}.{cs:02d}"
    except Exception:
        return "0:00:00.00"


def _pyxis_strip_tags(text):
    import re
    return re.sub(r'\{[^}]*\}', '', str(text or ""))


def _pyxis_kana(text):
    try:
        from nodes.text_nodes import text_strip_and_clean
        return text_strip_and_clean(context=None, text=text)
    except Exception:
        return str(text or "")


def _build_unit_lua_table(lua, unit_obj, line_tbl=None):
    if not unit_obj:
        return None
    st = getattr(unit_obj, "start_time", 0)
    et = getattr(unit_obj, "end_time", 0)
    dur = getattr(unit_obj, "duration", getattr(unit_obj, "dur", max(0, et - st)))
    mid = getattr(unit_obj, "mid_time", st + dur / 2.0)

    d = {
        "i": getattr(unit_obj, "i", getattr(unit_obj, "syl_i", getattr(unit_obj, "char_i", getattr(unit_obj, "word_i", 1)))),
        "n": getattr(unit_obj, "n", 1),
        "dur": dur,
        "duration": dur,
        "start_time": st,
        "end_time": et,
        "mid_time": mid,
        "syl_start": getattr(unit_obj, "syl_start", 0),
        "syl_end": getattr(unit_obj, "syl_end", 0),
        "syl_mid": getattr(unit_obj, "syl_mid", 0),
        "char_start": getattr(unit_obj, "char_start", 0),
        "char_end": getattr(unit_obj, "char_end", 0),
        "char_mid": getattr(unit_obj, "char_mid", 0),
        "word_start": getattr(unit_obj, "word_start", 0),
        "word_end": getattr(unit_obj, "word_end", 0),
        "word_mid": getattr(unit_obj, "word_mid", 0),
        "prespace": getattr(unit_obj, "prespace", ""),
        "postspace": getattr(unit_obj, "postspace", ""),
        "syl_i": getattr(unit_obj, "syl_i", getattr(unit_obj, "i", 1)),
        "char_i": getattr(unit_obj, "char_i", getattr(unit_obj, "i", 1)),
        "word_i": getattr(unit_obj, "word_i", getattr(unit_obj, "i", 1)),
        "x": getattr(unit_obj, "x", getattr(unit_obj, "center", 0.0)),
        "y": getattr(unit_obj, "y", getattr(unit_obj, "middle", 0.0)),
        "left": getattr(unit_obj, "left", 0.0),
        "center": getattr(unit_obj, "center", 0.0),
        "right": getattr(unit_obj, "right", 0.0),
        "top": getattr(unit_obj, "top", 0.0),
        "middle": getattr(unit_obj, "middle", 0.0),
        "bottom": getattr(unit_obj, "bottom", 0.0),
        "width": getattr(unit_obj, "width", 0.0),
        "height": getattr(unit_obj, "height", 0.0),
        "descent": getattr(unit_obj, "descent", 0.0),
        "extlead": getattr(unit_obj, "extlead", 0.0),
        "text": getattr(unit_obj, "text", ""),
        "text_stripped": getattr(unit_obj, "text_stripped", getattr(unit_obj, "text", ""))
    }
    ink_obj = getattr(unit_obj, "ink", None)
    if ink_obj is not None:
        d["ink"] = lua.table_from({
            "left": ink_obj.left,
            "right": ink_obj.right,
            "top": ink_obj.top,
            "bottom": ink_obj.bottom,
            "width": ink_obj.width,
            "height": ink_obj.height,
            "center": ink_obj.center,
            "middle": ink_obj.middle,
            "x": ink_obj.x,
            "y": ink_obj.y
        })
    if line_tbl is not None:
        d["line"] = line_tbl
    return lua.table_from(d)


VAR_ALIAS_GROUPS = {
    # Position X group
    "x": ["x", "pos_x", "fx_pos_x", "val_x"],
    "pos_x": ["x", "pos_x", "fx_pos_x", "val_x"],
    "fx_pos_x": ["x", "pos_x", "fx_pos_x", "val_x"],
    "val_x": ["x", "pos_x", "fx_pos_x", "val_x"],

    # Position Y group
    "y": ["y", "pos_y", "fx_pos_y", "val_y"],
    "pos_y": ["y", "pos_y", "fx_pos_y", "val_y"],
    "fx_pos_y": ["y", "pos_y", "fx_pos_y", "val_y"],
    "val_y": ["y", "pos_y", "fx_pos_y", "val_y"],

    # Start time group (Unit relative)
    "start_time": ["start_time", "st", "val_start"],
    "st": ["start_time", "st", "val_start"],
    "val_start": ["start_time", "st", "val_start"],

    # End time group (Unit relative)
    "end_time": ["end_time", "et", "val_end"],
    "et": ["end_time", "et", "val_end"],
    "val_end": ["end_time", "et", "val_end"],

    # Duration group
    "dur": ["dur", "duration", "val_dur", "time_dur"],
    "duration": ["dur", "duration", "val_dur", "time_dur"],
    "val_dur": ["dur", "duration", "val_dur", "time_dur"],
    "time_dur": ["dur", "duration", "val_dur", "time_dur"],

    # Origin group
    "org_x": ["org_x", "fx_org_x"],
    "fx_org_x": ["org_x", "fx_org_x"],
    "org_y": ["org_y", "fx_org_y"],
    "fx_org_y": ["org_y", "fx_org_y"],

    # Line & Queue group
    "layer": ["layer", "line_layer"],
    "actor": ["actor", "queue_id", "line_actor"],
    "queue_id": ["actor", "queue_id", "line_actor"],
    "queue_order": ["queue_order"],
    "style": ["style", "style_name", "line_style", "line_style_name"],
    "style_name": ["style", "style_name", "line_style", "line_style_name"],
    "effect": ["effect", "line_effect"]
}


def _propagate_alias_changes(context, user_modified_keys, active_unit=None, line_obj=None):
    raw_modified_keys = set(user_modified_keys)
    all_modified_aliases = set(raw_modified_keys)

    for mod_key in list(raw_modified_keys):
        val = context.get(mod_key)
        if val is not None and mod_key in VAR_ALIAS_GROUPS:
            for alias in VAR_ALIAS_GROUPS[mod_key]:
                all_modified_aliases.add(alias)
                all_modified_aliases.add(f"line_{alias}")
                all_modified_aliases.add(f"syl_{alias}")
                all_modified_aliases.add(f"char_{alias}")
                all_modified_aliases.add(f"word_{alias}")
                context[alias] = val
                if active_unit and hasattr(active_unit, alias):
                    try: setattr(active_unit, alias, val)
                    except Exception: pass
                if line_obj and hasattr(line_obj, alias) and alias not in ("start_time", "end_time", "st", "et", "start", "end", "val_start", "val_end", "dur", "duration", "val_dur"):
                    try: setattr(line_obj, alias, val)
                    except Exception: pass
        elif val is not None and active_unit and hasattr(active_unit, mod_key):
            try: setattr(active_unit, mod_key, val)
            except Exception: pass
        elif val is not None and line_obj and hasattr(line_obj, mod_key):
            try: setattr(line_obj, mod_key, val)
            except Exception: pass

    if any(k in all_modified_aliases for k in ("x", "pos_x", "fx_pos_x", "val_x", "y", "pos_y", "fx_pos_y", "val_y", "syl_x", "syl_y", "char_x", "char_y", "word_x", "word_y", "line_x", "line_y")):
        context["pos_overridden"] = True

    if any(k in all_modified_aliases for k in ("org_x", "org_y", "fx_org_x", "fx_org_y", "syl_org_x", "syl_org_y", "char_org_x", "char_org_y", "word_org_x", "word_org_y", "line_org_x", "line_org_y")):
        context["has_org"] = True

    if any(k in all_modified_aliases for k in ("start_time", "st", "val_start", "start", "end_time", "et", "val_end", "end")):
        st_val = float(context.get("start_time", context.get("st", getattr(active_unit, "start_time", 0.0))))
        et_val = float(context.get("end_time", context.get("et", getattr(active_unit, "end_time", 0.0))))
        dur_val = round(et_val - st_val, 3)
        for d_alias in ("dur", "duration", "val_dur", "fx_dur", "time_dur"):
            context[d_alias] = dur_val
            all_modified_aliases.add(d_alias)
        if active_unit:
            try:
                setattr(active_unit, "duration", dur_val)
                setattr(active_unit, "dur", dur_val)
            except Exception:
                pass

    return all_modified_aliases


def _sync_python_scope_to_context(eval_scope, context, initial_vals=None):
    if not isinstance(context, dict):
        return
    base_scope = _get_static_base_scope()
    excluded_keys = set(base_scope.keys()) | {
        "__builtins__", "inputs", "outputs", "out", "active_unit", "syl", "char", "word", "line", "l", "fx", "ink",
        "prev", "next", "is_first", "is_last", "has_prev", "has_next",
        "frame_dur", "ratio", "R", "Rs", "Rc", "Rd", "Rm", "Re", "Rfake", "Rcolor", "Rds", "Rcs",
        "Rms", "R2d", "Rbool", "Rstep", "Rr", "clamp", "lerp", "tag_only", "time_lead_in",
        "time_lead_out", "time_middle_1", "time_middle_2", "time_loop_1", "time_loop_2",
        "li", "lo", "m1", "m2", "l1", "l2", "audio_rms", "audio_peak", "audio_band", "audio_fft", "result"
    }
    for i in range(1, 17):
        excluded_keys.update({f"in{i}", f"in_{i}", f"In{i}", f"out{i}", f"out_{i}", f"Out{i}"})

    user_modified_keys = set()
    for k, v in eval_scope.items():
        if isinstance(k, str) and not k.startswith("_") and k not in excluded_keys:
            context[k] = v
            if not callable(v):
                if initial_vals is None or k not in initial_vals or initial_vals[k] != v:
                    user_modified_keys.add(k)
    for unit_key in ("syl", "char", "word"):
        unit_obj = eval_scope.get(unit_key)
        if unit_obj:
            for attr in ("x", "y", "center", "middle", "left", "right", "top", "bottom", "start_time", "end_time", "st", "et", "start", "end", "val_start", "val_end", "dur", "duration", "val_dur", "text", "text_stripped"):
                if hasattr(unit_obj, attr):
                    val = getattr(unit_obj, attr)
                    init_key = f"{unit_key}_{attr}"
                    if initial_vals is not None and (init_key in initial_vals and initial_vals[init_key] != val):
                        user_modified_keys.add(attr)
                        user_modified_keys.add(init_key)
                        context[attr] = val
                        context[init_key] = val

    py_fx = eval_scope.get("fx")
    if py_fx is not None:
        for attr in ("pos_x", "x", "pos_y", "y", "start_time", "st", "end_time", "et", "dur", "duration", "align", "i", "n"):
            try:
                val = getattr(py_fx, attr, None)
                if val is not None:
                    init_key = f"fx_{attr}"
                    if initial_vals is not None and (init_key in initial_vals and initial_vals[init_key] != val):
                        from node_engine import _apply_fx_setting
                        _apply_fx_setting(attr, val, context)
                        user_modified_keys.add(attr)
                        user_modified_keys.add(init_key)
            except Exception:
                pass

    active_unit = context.get("active_unit") or eval_scope.get("active_unit")
    line_obj = eval_scope.get("line") or context.get("line")

    all_modified_aliases = _propagate_alias_changes(context, user_modified_keys, active_unit, line_obj)

    for unit_key in ("syl", "char", "word"):
        unit_obj = eval_scope.get(unit_key)
        if unit_obj:
            is_active = (active_unit is unit_obj) or (active_unit is None and unit_key == "syl")
            for attr in ("x", "y", "center", "middle", "left", "right", "top", "bottom", "start_time", "end_time", "dur", "duration", "text", "text_stripped"):
                if hasattr(unit_obj, attr):
                    if attr in all_modified_aliases or f"{unit_key}_{attr}" in all_modified_aliases:
                        continue
                    val = getattr(unit_obj, attr)
                    context[f"{unit_key}_{attr}"] = val
                    if is_active:
                        if attr in ("x", "y", "center", "middle") and context.get("pos_overridden"):
                            pass
                        else:
                            context[f"val_{attr}"] = val
                            context[attr] = val

    if line_obj:
        for attr in ("text", "raw_text", "style_name", "style", "layer", "start_time", "end_time", "duration", "dur", "margin_l", "margin_r", "margin_v", "actor", "effect"):
            if hasattr(line_obj, attr):
                if attr in all_modified_aliases or f"line_{attr}" in all_modified_aliases:
                    continue
                val = getattr(line_obj, attr)
                if attr in ("style", "style_name"):
                    setattr(line_obj, "style_name", str(val))
                    setattr(line_obj, "style", str(val))
                    context["line_style_name"] = str(val)
                    context["line_style"] = str(val)
                else:
                    context[f"line_{attr}"] = val


def _get_val_safe(obj, field):
    if obj is None:
        return None
    try:
        val = obj[field]
        if val is not None:
            return val
    except Exception:
        pass
    try:
        return getattr(obj, field, None)
    except Exception:
        return None


def _is_lua_callable_or_fn(val):
    if val is None:
        return False
    if type(val).__name__ == "_LuaTable":
        return False
    try:
        import lupa
        if lupa.lua_type(val) == "table":
            return False
        if lupa.lua_type(val) == "function":
            return True
    except Exception:
        pass
    if type(val).__name__ == "_LuaFunction":
        return True
    return callable(val)


def _lua_val_to_python(val, seen=None):
    if val is None:
        return None
    if isinstance(val, (int, float, str, bool)):
        return val
    type_name = type(val).__name__
    if type_name == "_LuaTable":
        if seen is None:
            seen = set()
        ptr = id(val)
        if ptr in seen:
            return None
        seen.add(ptr)
        try:
            keys = list(val.keys())
            is_seq = len(keys) > 0 and all(isinstance(k, int) and 1 <= k <= len(keys) for k in keys)
            if is_seq:
                return [_lua_val_to_python(val[k], seen) for k in sorted(keys)]
            else:
                return {str(k): _lua_val_to_python(val[k], seen) for k in keys}
        except Exception:
            return str(val)
    if type_name == "_LuaFunction" or callable(val):
        return val
    return val


def _sync_lua_globals_to_context(g, context, ctx_dict, initial_vals=None):
    if not isinstance(context, dict):
        return

    if initial_vals is None:
        initial_vals = {}

    active_unit = context.get("active_unit") or ctx_dict.get("active_unit")
    line_obj = ctx_dict.get("line") or ctx_dict.get("l") or context.get("line") or context.get("l")

    lua_builtins = {
        "_G", "_VERSION", "assert", "collectgarbage", "dofile", "error", "getmetatable",
        "ipairs", "load", "loadfile", "loadstring", "module", "next", "pairs", "pcall",
        "print", "rawequal", "rawget", "rawlen", "rawset", "require", "setmetatable",
        "tonumber", "tostring", "type", "unpack", "xpcall", "coroutine", "debug", "io",
        "math", "os", "package", "string", "table", "utf8", "bit32"
    }
    injected_keys = {
        "inputs", "outputs", "out", "result", "_pyxis_main", "g", "syl", "char", "word", "line", "l", "fx", "ink",
        "prev", "next", "is_first", "is_last", "has_prev", "has_next",
        "order", "style", "actor", "effect", "layer",
        "context", "frame_dur", "ratio", "active_unit", "all_lines", "selected_lines", "engine", "processor",
        "format", "floor", "ceil", "deg", "rad", "round",
        "R", "Rs", "Rc", "Rd", "Rm", "Re", "Rfake", "Rcolor",
        "Rds", "Rcs", "Rms", "R2d", "Rbool", "Rstep", "Rr", "clamp", "lerp", "tag_only",
        "pos", "move", "org", "fad", "fade", "clip", "iclip", "c1", "c2", "c3", "c4",
        "color_1", "color_2", "color_3", "color_4", "a1", "a2", "a3", "a4", "alpha",
        "trans", "fscx", "fscy", "fscxy", "frz", "frx", "fry", "fax", "fay", "bord",
        "shad", "blur", "an", "ass_color", "ass_alpha", "random_color", "random_alpha",
        "map_range", "map_value", "ease_in", "ease_out", "ease_in_out", "cubic_in", "cubic_out",
        "elastic", "bounce", "back", "sine_wave", "square_wave", "triangle_wave", "sawtooth_wave",
        "polar", "bezier", "ipol", "time_to_frame", "duration", "parse_ass_time", "format_ass_time",
        "strip_tags", "kana", "shape_circle", "shape_square", "shape_rectangle", "shape_triangle",
        "shape_rhombus", "shape_rounded_corners", "shape_pentagon", "shape_hexagon", "shape_octagon",
        "shape_star", "shape_heart", "resolve_shape", "time_lead_in", "time_lead_out",
        "time_middle_1", "time_middle_2", "time_loop_1", "time_loop_2", "li", "lo", "m1", "m2",
        "l1", "l2", "remember", "recall", "audio_rms", "audio_peak", "audio_band", "audio_fft"
    }
    for i in range(1, 17):
        injected_keys.update({f"in{i}", f"in_{i}", f"In{i}", f"out{i}", f"out_{i}", f"Out{i}"})

    user_modified_keys = set()
    for k in g:
        if isinstance(k, str) and not k.startswith("_") and k not in lua_builtins and k not in injected_keys:
            try:
                val = g[k]
                if val is not None:
                    should_sync = False
                    if k not in initial_vals:
                        should_sync = True
                    else:
                        init_v = initial_vals[k]
                        try:
                            if init_v is not val and init_v != val:
                                should_sync = True
                        except Exception:
                            should_sync = True
                    if should_sync:
                        py_val = _lua_val_to_python(val)
                        if py_val is not None:
                            context[k] = py_val
                            if not _is_lua_callable_or_fn(val):
                                user_modified_keys.add(k)
            except Exception:
                pass

    for unit_key in ("syl", "char", "word"):
        unit_obj = ctx_dict.get(unit_key) or (active_unit if unit_key == "syl" else None)
        if unit_obj and hasattr(g, unit_key):
            lua_unit = getattr(g, unit_key)
            for field in ("x", "y", "center", "middle", "left", "right", "top", "bottom", "start_time", "end_time", "st", "et", "start", "end", "val_start", "val_end", "dur", "duration", "val_dur", "text", "text_stripped"):
                try:
                    val = _get_val_safe(lua_unit, field)
                    if val is not None:
                        init_key = f"{unit_key}_{field}"
                        if init_key not in initial_vals or initial_vals[init_key] != val:
                            user_modified_keys.add(field)
                            user_modified_keys.add(init_key)
                            setattr(unit_obj, field, val)
                            context[init_key] = val
                            context[field] = val
                except Exception:
                    pass

    lua_line = getattr(g, "line", getattr(g, "l", getattr(g, "L", None)))
    if lua_line and line_obj:
        for field in ("text", "raw_text", "style_name", "style", "layer", "start_time", "end_time", "st", "et", "start", "end", "val_start", "val_end", "duration", "dur", "val_dur", "margin_l", "margin_r", "margin_v", "actor", "effect"):
            try:
                val = _get_val_safe(lua_line, field)
                if val is not None:
                    init_key = f"line_{field}"
                    if init_key not in initial_vals or initial_vals[init_key] != val:
                        user_modified_keys.add(field)
                        user_modified_keys.add(init_key)
                        if field in ("style", "style_name"):
                            setattr(line_obj, "style_name", str(val))
                            setattr(line_obj, "style", str(val))
                            context["line_style_name"] = str(val)
                            context["line_style"] = str(val)
                        else:
                            setattr(line_obj, field, val)
                            context[f"line_{field}"] = val
            except Exception:
                pass

    if hasattr(g, "fx") and g.fx is not None:
        from node_engine import _apply_fx_setting
        lua_fx = g.fx
        for field in ("pos_x", "x", "pos_y", "y", "org_x", "org_y", "start_time", "st", "time_start", "end_time", "et", "time_end", "dur", "duration", "time_dur", "align", "i", "n"):
            try:
                val = _get_val_safe(lua_fx, field)
                if val is not None:
                    init_key = f"fx_{field}"
                    if init_key not in initial_vals or initial_vals[init_key] != val:
                        _apply_fx_setting(field, val, context)
                        user_modified_keys.add(field)
                        user_modified_keys.add(init_key)
            except Exception:
                pass

    all_modified_aliases = _propagate_alias_changes(context, user_modified_keys, active_unit, line_obj)

    for unit_key in ("syl", "char", "word"):
        unit_obj = ctx_dict.get(unit_key)
        if not unit_obj and active_unit:
            unit_type = getattr(active_unit, 'unit_type', '')
            if unit_type == unit_key or (unit_key == 'syl' and type(active_unit).__name__ == 'PyxisSyllable'):
                unit_obj = active_unit
        if unit_obj and hasattr(g, unit_key):
            lua_unit = getattr(g, unit_key)
            is_active = (active_unit is unit_obj)
            for field in ("x", "y", "center", "middle", "left", "right", "top", "bottom", "start_time", "end_time", "st", "et", "start", "end", "val_start", "val_end", "dur", "duration", "val_dur", "text", "text_stripped"):
                try:
                    if field in all_modified_aliases or f"{unit_key}_{field}" in all_modified_aliases:
                        continue
                    val = _get_val_safe(lua_unit, field)
                    if val is not None:
                        setattr(unit_obj, field, val)
                        context[f"{unit_key}_{field}"] = val
                        if is_active:
                            context[f"val_{field}"] = val
                            context[field] = val
                except Exception:
                    pass

    if lua_line and line_obj:
        for field in ("text", "raw_text", "style_name", "style", "layer", "start_time", "end_time", "st", "et", "start", "end", "duration", "dur", "val_dur", "margin_l", "margin_r", "margin_v", "actor", "effect"):
            try:
                if f"line_{field}" in all_modified_aliases or field in all_modified_aliases:
                    continue
                val = _get_val_safe(lua_line, field)
                if val is not None:
                    if field in ("style", "style_name"):
                        setattr(line_obj, "style_name", str(val))
                        setattr(line_obj, "style", str(val))
                        context["line_style_name"] = str(val)
                        context["line_style"] = str(val)
                    else:
                        setattr(line_obj, field, val)
                        context[f"line_{field}"] = val
            except Exception:
                pass



def _pyxis_clamp(val, min_val=0.0, max_val=1.0):
    try:
        v = float(val)
        mn = float(min_val)
        mx = float(max_val)
        low = min(mn, mx)
        high = max(mn, mx)
        return max(low, min(high, v))
    except Exception:
        return val


def _pyxis_lerp(a, b, t):
    try:
        a_f = float(a)
        b_f = float(b)
        t_f = float(t)
        return a_f + (b_f - a_f) * t_f
    except Exception:
        return a


def _pyxis_tag_only(cond, tag):
    return str(tag) if cond else ""


class PyxisTimeModifier:
    """Wrapper for short time modifiers (li, lo, m1, m2, l1, l2) in code nodes."""
    def __init__(self, func, context, default_delay=40.0, **default_kwargs):
        self.func = func
        self.context = context
        self.default_delay = default_delay
        self.default_kwargs = default_kwargs

    def __call__(self, delay=None, *args, **kwargs):
        d = self.default_delay if delay is None else delay
        kw = dict(self.default_kwargs)
        kw.update(kwargs)
        return self.func(self.context, d, *args, **kw)

    def _eval(self, delay=None):
        d = self.default_delay if delay is None else delay
        return float(self.func(self.context, d, **self.default_kwargs))

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return self.func(self.context, float(other), **self.default_kwargs)
        try:
            return self._eval() * float(other)
        except Exception:
            return self._eval()

    def __rmul__(self, other):
        if isinstance(other, (int, float)):
            return self.func(self.context, float(other), **self.default_kwargs)
        try:
            return float(other) * self._eval()
        except Exception:
            return self._eval()

    def __add__(self, other):
        try:
            return self._eval() + float(other)
        except Exception:
            return self._eval()

    def __radd__(self, other):
        try:
            return float(other) + self._eval()
        except Exception:
            return self._eval()

    def __sub__(self, other):
        try:
            return self._eval() - float(other)
        except Exception:
            return self._eval()

    def __rsub__(self, other):
        try:
            return float(other) - self._eval()
        except Exception:
            return self._eval()

    def __truediv__(self, other):
        try:
            return self._eval() / float(other)
        except Exception:
            return self._eval()

    def __rtruediv__(self, other):
        try:
            return float(other) / self._eval()
        except Exception:
            return self._eval()

    def __neg__(self):
        return -self._eval()

    def __pos__(self):
        return self._eval()

    def __abs__(self):
        return abs(self._eval())

    def __float__(self):
        return self._eval()

    def __int__(self):
        return int(self._eval())

    def __round__(self, n=None):
        return round(self._eval(), n)

    def __repr__(self):
        return str(self._eval())

    def __str__(self):
        return str(self._eval())


def execute_python_script(context, script, inputs_map):
    """Executes an optimized Python script with cached bytecode compilation."""
    if not script:
        return ""

    script_str = str(script).strip()
    if not script_str:
        return ""

    frame_dur = float(context.get("frame_dur", 41.708333333333336)) if isinstance(context, dict) else 41.708333333333336
    ratio = float(context.get("ratio", context.get("module", 1.0))) if isinstance(context, dict) else 1.0

    import re
    script_str = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*(li|lo|m1|m2|l1|l2)\b', r'\1 * \2', script_str)
    script_str = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*f\b', rf'(\1 * {frame_dur})', script_str)
    script_str = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*r\b', rf'(\1 * {ratio})', script_str)

    eval_scope = _get_static_base_scope().copy()
    if context and isinstance(context, dict):
        eval_scope.update(context)

    eval_scope["frame_dur"] = frame_dur
    eval_scope["ratio"] = ratio

    active_unit = eval_scope.get("active_unit")
    if active_unit:
        eval_scope.setdefault("syl", getattr(active_unit, "syl", active_unit))
        eval_scope.setdefault("char", getattr(active_unit, "char", None))
        eval_scope.setdefault("word", getattr(active_unit, "word", None))
        eval_scope.setdefault("line", getattr(active_unit, "line", None))

    eval_scope["l"] = eval_scope.get("line")
    from node_engine import FxContext
    eval_scope["fx"] = FxContext(eval_scope)
    from models import InkNamespace
    eval_scope["ink"] = InkNamespace(eval_scope)

    prev_obj = getattr(active_unit, "prev", None) if active_unit else eval_scope.get("prev")
    next_obj = getattr(active_unit, "next", None) if active_unit else eval_scope.get("next")
    eval_scope["prev"] = prev_obj
    eval_scope["next"] = next_obj
    i_val = int(eval_scope.get("i", getattr(active_unit, "i", 1)))
    n_val = int(eval_scope.get("n", getattr(active_unit, "n", 1)))
    eval_scope["is_first"] = (i_val == 1) or (prev_obj is None)
    eval_scope["is_last"] = (i_val == n_val) or (next_obj is None)
    eval_scope["has_prev"] = (prev_obj is not None)
    eval_scope["has_next"] = (next_obj is not None)

    eval_scope["outputs"] = {}
    eval_scope["out"] = eval_scope["outputs"]
    for i in range(1, 17):
        eval_scope[f"out{i}"] = None
        eval_scope[f"out_{i}"] = None
        eval_scope[f"Out{i}"] = None

    if inputs_map and isinstance(inputs_map, dict):
        eval_scope["inputs"] = inputs_map
        for k, v in inputs_map.items():
            if isinstance(k, str):
                eval_scope[k] = v
                eval_scope[k.lower()] = v

    from nodes.math_nodes import math_random_master, PyxisByDispatcher

    eval_scope["by"] = PyxisByDispatcher(context)

    def _make_rnd_caller(mode_name, default_step=None):
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
            clean_kwargs = {k: v for k, v in kwargs.items() if k not in ("min_val", "min", "max_val", "max", "step", "by", "iter", "iterator")}
            return math_random_master(context, mode=mode_name, min_val=mn, max_val=mx, step=st, by=by_val, **clean_kwargs)
        return _caller

    eval_scope["R"] = _make_rnd_caller("R", 1.0)
    eval_scope["Rs"] = _make_rnd_caller("Rs", 1.0)
    eval_scope["Rc"] = _make_rnd_caller("Rc", 0.01)
    eval_scope["Rd"] = _make_rnd_caller("Rd", 0.1)
    eval_scope["Rm"] = _make_rnd_caller("Rm", 0.001)
    eval_scope["Rds"] = _make_rnd_caller("Rds", 0.1)
    eval_scope["Rcs"] = _make_rnd_caller("Rcs", 0.01)
    eval_scope["Rms"] = _make_rnd_caller("Rms", 0.001)
    eval_scope["Rr"] = _make_rnd_caller("Rr", 1.0)
    eval_scope["Rstep"] = _make_rnd_caller("Rstep", 45.0)
    eval_scope["R2d"] = _make_rnd_caller("R2d", 1.0)
    eval_scope["Rbool"] = lambda prob=50.0, **kwargs: math_random_master(context, mode="Rbool", min_val=prob, **kwargs)
    eval_scope["Rcolor"] = lambda c1="#FFFFFF", c2="#000000", **kwargs: math_random_master(context, mode="Rcolor", min_val=c1, max_val=c2, **kwargs)
    eval_scope["Re"] = lambda options="", **kwargs: math_random_master(context, mode="Re", options=options, **kwargs)
    eval_scope["Rfake"] = lambda *args, **kwargs: math_random_master(context, mode="Rfake", *args, **kwargs)
    eval_scope["rand"] = eval_scope["R"]

    eval_scope["clamp"] = _pyxis_clamp
    eval_scope["lerp"] = _pyxis_lerp
    eval_scope["tag_only"] = _pyxis_tag_only

    from nodes.time_nodes import time_lead_in, time_lead_out, time_middle_1, time_middle_2, time_loop_1, time_loop_2
    eval_scope["time_lead_in"] = lambda delay=40, base=None: time_lead_in(context, delay=delay, base=base)
    eval_scope["time_lead_out"] = lambda delay=40, base=None: time_lead_out(context, delay=delay, base=base)
    eval_scope["time_middle_1"] = lambda delay=30, base=None: time_middle_1(context, delay=delay, base=base)
    eval_scope["time_middle_2"] = lambda delay=30, base=None: time_middle_2(context, delay=delay, base=base)
    eval_scope["time_loop_1"] = lambda delay=30, mode="leadin", base=None: time_loop_1(context, delay=delay, mode=mode, base=base)
    eval_scope["time_loop_2"] = lambda delay=30, mode="leadin", base=None: time_loop_2(context, delay=delay, mode=mode, base=base)

    eval_scope["li"] = PyxisTimeModifier(time_lead_in, context, default_delay=40.0)
    eval_scope["lo"] = PyxisTimeModifier(time_lead_out, context, default_delay=40.0)
    eval_scope["m1"] = PyxisTimeModifier(time_middle_1, context, default_delay=30.0)
    eval_scope["m2"] = PyxisTimeModifier(time_middle_2, context, default_delay=30.0)
    eval_scope["l1"] = PyxisTimeModifier(time_loop_1, context, default_delay=30.0, mode="leadin")
    eval_scope["l2"] = PyxisTimeModifier(time_loop_2, context, default_delay=30.0, mode="leadin")

    from nodes.time_nodes import PyxisSyncHelper, calculate_sync_gap
    from models import AdjacentUnitProxy
    eval_scope["sync"] = PyxisSyncHelper(context)
    eval_scope["calculate_sync_gap"] = lambda *a, **kw: calculate_sync_gap(context, *a, **kw)
    eval_scope["prev"] = AdjacentUnitProxy("prev", eval_scope.get("prev"))
    eval_scope["next"] = AdjacentUnitProxy("next", eval_scope.get("next"))
    for k_alias in ("order", "style", "actor", "effect", "layer"):
        eval_scope[k_alias] = k_alias

    from nodes.audio_nodes import audio_rms, audio_peak, audio_band, audio_fft
    eval_scope["audio_rms"] = lambda *args, **kwargs: audio_rms(*args, context=context, **kwargs)
    eval_scope["audio_peak"] = lambda *args, **kwargs: audio_peak(*args, context=context, **kwargs)
    eval_scope["audio_band"] = lambda *args, **kwargs: audio_band(*args, context=context, **kwargs)
    eval_scope["audio_fft"] = lambda *args, **kwargs: audio_fft(*args, context=context, **kwargs)

    eval_scope["result"] = ""

    initial_vals = {k: eval_scope[k] for k in eval_scope if isinstance(k, str) and not callable(eval_scope[k])}
    for unit_key in ("syl", "char", "word"):
        u_obj = eval_scope.get(unit_key)
        if u_obj:
            for attr in ("x", "y", "center", "middle", "left", "right", "top", "bottom", "start_time", "end_time", "st", "et", "start", "end", "dur", "duration", "text", "text_stripped"):
                val = getattr(u_obj, attr, None)
                if val is not None:
                    initial_vals[f"{unit_key}_{attr}"] = val

    if script_str in _COMPILED_SCRIPT_CACHE:
        compiled_entry = _COMPILED_SCRIPT_CACHE[script_str]
        _COMPILED_SCRIPT_CACHE.move_to_end(script_str)
    else:
        import builtins
        import ast
        try:
            tree = ast.parse(script_str, "<pyxis_script>", "exec")
            if tree.body and isinstance(tree.body[-1], ast.Expr):
                exec_body = tree.body[:-1]
                eval_expr = ast.Expression(tree.body[-1].value)
                code_exec = compile(ast.Module(body=exec_body, type_ignores=[]), "<pyxis_script>", "exec") if exec_body else None
                code_eval = compile(eval_expr, "<pyxis_script>", "eval")
                compiled_entry = ("ast_split", (code_exec, code_eval))
            else:
                code_exec = compile(tree, "<pyxis_script>", "exec")
                compiled_entry = ("exec", code_exec)
        except Exception:
            try:
                code_eval = compile(script_str, "<pyxis_script>", "eval")
                compiled_entry = ("eval", code_eval)
            except Exception:
                try:
                    code_exec = compile(script_str, "<pyxis_script>", "exec")
                    compiled_entry = ("exec", code_exec)
                except Exception as comp_err:
                    compiled_entry = ("err", str(comp_err))
        if len(_COMPILED_SCRIPT_CACHE) >= _MAX_COMPILED_SCRIPT_CACHE:
            _COMPILED_SCRIPT_CACHE.popitem(last=False)
        _COMPILED_SCRIPT_CACHE[script_str] = compiled_entry

    kind, code_obj = compiled_entry
    import builtins
    eval_scope["__builtins__"] = builtins
    res_str = ""
    res = None
    res_eval = None
    explicit_res = None
    if kind == "ast_split":
        code_exec, code_eval = code_obj
        try:
            if code_exec:
                exec(code_exec, eval_scope)
            res_eval = eval(code_eval, eval_scope)
            explicit_res = eval_scope.get("result", "")
            if explicit_res != "":
                res_str = str(explicit_res)
            elif res_eval is not None:
                res_str = str(res_eval)
            else:
                res_str = ""
        except Exception as e:
            res_str = f"[Err Python Script: {e}]"
    elif kind == "eval":
        try:
            res = eval(code_obj, eval_scope)
            res_str = str(res) if res is not None else str(eval_scope.get("result", ""))
        except Exception as e:
            res_str = f"[Err Python Script: {e}]"
    elif kind == "exec":
        try:
            exec(code_obj, eval_scope)
            res = eval_scope.get("result", "")
            res_str = str(res) if res is not None else ""
        except Exception as e:
            res_str = f"[Err Python Script: {e}]"
    else:
        res_str = f"[Err Python Script: {code_obj}]"

    _sync_python_scope_to_context(eval_scope, context, initial_vals=initial_vals)

    script_outputs = {}
    py_outputs = eval_scope.get("outputs")
    if isinstance(py_outputs, dict):
        for k, v in py_outputs.items():
            script_outputs[k] = v
            if isinstance(k, int):
                script_outputs[f"out{k}"] = v
    py_out = eval_scope.get("out")
    if isinstance(py_out, dict) and py_out is not py_outputs:
        for k, v in py_out.items():
            script_outputs[k] = v
    for i in range(1, 17):
        for prefix in (f"out{i}", f"out_{i}", f"Out{i}"):
            v = eval_scope.get(prefix)
            if v is not None:
                script_outputs[f"out{i}"] = v
                script_outputs[i] = v
                break

    if kind == "ast_split":
        if isinstance(eval_scope.get("result"), dict):
            for k, v in eval_scope["result"].items():
                script_outputs[k] = v
        elif isinstance(res_eval, dict):
            for k, v in res_eval.items():
                script_outputs[k] = v
    elif kind in ("eval", "exec"):
        res_raw = eval_scope.get("result") if kind == "exec" else res
        if isinstance(res_raw, dict):
            for k, v in res_raw.items():
                script_outputs[k] = v

    if isinstance(context, dict):
        context["_script_outputs"] = script_outputs
        context["outputs"] = script_outputs
        if res_str and not res_str.startswith("[Err"):
            context["script_result"] = res_str
            if '\\' in res_str or '{' in res_str:
                existing = str(context.get("loop_tags") or context.get("tags") or "")
                try:
                    from node_engine import merge_ass_tags
                    context["loop_tags"] = merge_ass_tags(existing, res_str)
                    context["tags"] = context["loop_tags"]
                except Exception:
                    context["loop_tags"] = (existing + res_str).strip()
                    context["tags"] = context["loop_tags"]

    return res_str


def execute_lua_script(context, script, inputs_map):
    """Executes a Lua script via lupa with injected Pyxis Nodes context."""
    try:
        import lupa
    except ImportError:
        return "[Err Lua: 'lupa' library not installed in Python]"

    try:
        frame_dur = float(context.get("frame_dur", 41.708333333333336)) if isinstance(context, dict) else 41.708333333333336
        ratio = float(context.get("ratio", context.get("module", 1.0))) if isinstance(context, dict) else 1.0

        import re
        script_str = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*(li|lo|m1|m2|l1|l2)\b', r'\1 * \2', str(script or ""))
        script_str = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*f\b', rf'(\1 * {frame_dur})', script_str)
        script_str = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*r\b', rf'(\1 * {ratio})', script_str)
        script_str = re.sub(r'\b(l|line|syl|char|word|L|S|C|W)\.end\b', r'\1.end_time', script_str)
        script_str = re.sub(r'\b(l|line|syl|char|word|L|S|C|W)\.start\b', r'\1.start_time', script_str)

        lua = lupa.LuaRuntime(unpack_returned_tuples=True)
        g = lua.globals()

        lua.execute("format = string.format")
        lua.execute("floor = math.floor; ceil = math.ceil; deg = math.deg; rad = math.rad")
        lua.execute("""
        math.round = function(num, idp)
            if not num then return 0 end
            local mult = 10^(idp or 0)
            return math.floor(num * mult + 0.5) / mult
        end
        round = math.round
        """)

        g.frame_dur = frame_dur
        g.ratio = ratio

        for i in range(1, 17):
            g[f"in{i}"] = ""
            g[f"in_{i}"] = ""
            g[f"In{i}"] = ""

        g.inputs = lua.table_from(inputs_map)
        for k, v in inputs_map.items():
            if isinstance(k, str):
                g[k] = v
                g[k.lower()] = v

        ctx_dict = dict(context or {})
        for k, v in ctx_dict.items():
            if isinstance(k, str) and not k.startswith("_"):
                if hasattr(v, '__class__') and ('lupa' in str(type(v)) or type(v).__name__.startswith('_Lua')):
                    continue
                if isinstance(v, (int, float, str, bool)):
                    g[k] = v
                elif isinstance(v, (list, tuple)):
                    try:
                        g[k] = lua.table_from(v)
                    except Exception:
                        pass
                elif isinstance(v, dict):
                    try:
                        g[k] = lua.table_from(v)
                    except Exception:
                        pass

        from nodes.math_nodes import math_random_master, PyxisByDispatcher

        g.by = PyxisByDispatcher(context)

        def _make_lua_rnd_caller(mode_name, default_step=None):
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
                clean_kwargs = {k: v for k, v in kwargs.items() if k not in ("min_val", "min", "max_val", "max", "step", "by", "iter", "iterator")}
                return math_random_master(context, mode=mode_name, min_val=mn, max_val=mx, step=st, by=by_val, **clean_kwargs)
            return _caller

        g.R = _make_lua_rnd_caller("R", 1.0)
        g.Rs = _make_lua_rnd_caller("Rs", 1.0)
        g.Rc = _make_lua_rnd_caller("Rc", 0.01)
        g.Rd = _make_lua_rnd_caller("Rd", 0.1)
        g.Rm = _make_lua_rnd_caller("Rm", 0.001)
        g.Rds = _make_lua_rnd_caller("Rds", 0.1)
        g.Rcs = _make_lua_rnd_caller("Rcs", 0.01)
        g.Rms = _make_lua_rnd_caller("Rms", 0.001)
        g.Rr = _make_lua_rnd_caller("Rr", 1.0)
        g.Rstep = _make_lua_rnd_caller("Rstep", 45.0)
        g.R2d = _make_lua_rnd_caller("R2d", 1.0)
        g.Rbool = lambda prob=50.0, **kwargs: math_random_master(context, mode="Rbool", min_val=prob, **kwargs)
        g.Rcolor = lambda c1="#FFFFFF", c2="#000000", **kwargs: math_random_master(context, mode="Rcolor", min_val=c1, max_val=c2, **kwargs)
        g.Re = lambda options="", **kwargs: math_random_master(context, mode="Re", options=options, **kwargs)
        g.Rfake = lambda *args, **kwargs: math_random_master(context, mode="Rfake", *args, **kwargs)
        g.rand = g.R

        g.clamp = _pyxis_clamp
        g.lerp = _pyxis_lerp
        g.tag_only = _pyxis_tag_only
        g.pos = _pyxis_pos
        g.move = _pyxis_move
        g.org = _pyxis_org
        g.fad = _pyxis_fad
        g.fade = _pyxis_fade
        g.clip = _pyxis_clip
        g.iclip = _pyxis_iclip
        g.c1 = _pyxis_c1
        g.c2 = _pyxis_c2
        g.c3 = _pyxis_c3
        g.c4 = _pyxis_c4
        g.color_1 = _pyxis_c1
        g.color_2 = _pyxis_c2
        g.color_3 = _pyxis_c3
        g.color_4 = _pyxis_c4
        g.a1 = _pyxis_a1
        g.a2 = _pyxis_a2
        g.a3 = _pyxis_a3
        g.a4 = _pyxis_a4
        g.alpha = _pyxis_alpha
        g.trans = _pyxis_trans
        g.fscx = _pyxis_fscx
        g.fscy = _pyxis_fscy
        g.fscxy = _pyxis_fscxy
        g.frz = _pyxis_frz
        g.frx = _pyxis_frx
        g.fry = _pyxis_fry
        g.fax = _pyxis_fax
        g.fay = _pyxis_fay
        g.bord = _pyxis_bord
        g.shad = _pyxis_shad
        g.blur = _pyxis_blur
        g.an = _pyxis_an
        g.ass_color = _pyxis_ass_color
        g.ass_alpha = _pyxis_ass_alpha
        g.random_color = _pyxis_random_color
        g.random_alpha = _pyxis_random_alpha
        g.map_range = _pyxis_map_range
        g.map_value = _pyxis_map_range
        g.ease_in = _pyxis_ease_in
        g.ease_out = _pyxis_ease_out
        g.ease_in_out = _pyxis_ease_in_out
        g.cubic_in = _pyxis_cubic_in
        g.cubic_out = _pyxis_cubic_out
        g.elastic = _pyxis_elastic
        g.bounce = _pyxis_bounce
        g.back = _pyxis_back
        g.sine_wave = _pyxis_sine_wave
        g.square_wave = _pyxis_square_wave
        g.triangle_wave = _pyxis_triangle_wave
        g.sawtooth_wave = _pyxis_sawtooth_wave
        g.polar = _pyxis_polar
        g.bezier = _pyxis_bezier
        g.ipol = _pyxis_ipol
        g.time_to_frame = _pyxis_time_to_frame
        g.duration = lambda obj=None: _pyxis_duration(obj, context)
        g.parse_ass_time = _pyxis_parse_ass_time
        g.format_ass_time = _pyxis_format_ass_time
        g.strip_tags = _pyxis_strip_tags
        g.kana = _pyxis_kana

        try:
            from nodes.shape_nodes import (
                shape_circle, shape_square, shape_rectangle, shape_triangle, shape_rhombus,
                shape_rounded_corners, shape_pentagon, shape_hexagon, shape_octagon,
                shape_star, shape_heart, resolve_shape_value
            )
            g.shape_circle = lambda: shape_circle(context)
            g.shape_square = lambda: shape_square(context)
            g.shape_rectangle = lambda: shape_rectangle(context)
            g.shape_triangle = lambda: shape_triangle(context)
            g.shape_rhombus = lambda: shape_rhombus(context)
            g.shape_rounded_corners = lambda: shape_rounded_corners(context)
            g.shape_pentagon = lambda: shape_pentagon(context)
            g.shape_hexagon = lambda: shape_hexagon(context)
            g.shape_octagon = lambda: shape_octagon(context)
            g.shape_star = lambda: shape_star(context)
            g.shape_heart = lambda: shape_heart(context)
            g.resolve_shape = lambda name: resolve_shape_value(name, context)
        except ImportError:
            pass

        from nodes.time_nodes import time_lead_in, time_lead_out, time_middle_1, time_middle_2, time_loop_1, time_loop_2
        g.time_lead_in = lambda delay=40, base=None: time_lead_in(context, delay=delay, base=base)
        g.time_lead_out = lambda delay=40, base=None: time_lead_out(context, delay=delay, base=base)
        g.time_middle_1 = lambda delay=30, base=None: time_middle_1(context, delay=delay, base=base)
        g.time_middle_2 = lambda delay=30, base=None: time_middle_2(context, delay=delay, base=base)
        g.time_loop_1 = lambda delay=30, mode="leadin", base=None: time_loop_1(context, delay=delay, mode=mode, base=base)
        g.time_loop_2 = lambda delay=30, mode="leadin", base=None: time_loop_2(context, delay=delay, mode=mode, base=base)

        lua.execute("""
        local function _make_mod(fn, def_d)
            local obj = {}
            setmetatable(obj, {
                __call = function(t, d, base)
                    return fn(d or def_d, base)
                end,
                __mul = function(a, b)
                    if type(a) == "number" then return fn(a)
                    elseif type(b) == "number" then return fn(b)
                    else
                        local va = (type(a) == "number") and a or fn(def_d)
                        local vb = (type(b) == "number") and b or fn(def_d)
                        return va * vb
                    end
                end,
                __add = function(a, b)
                    local va = (type(a) == "number") and a or fn(def_d)
                    local vb = (type(b) == "number") and b or fn(def_d)
                    return va + vb
                end,
                __sub = function(a, b)
                    local va = (type(a) == "number") and a or fn(def_d)
                    local vb = (type(b) == "number") and b or fn(def_d)
                    return va - vb
                end,
                __unm = function(t) return -fn(def_d) end
            })
            return obj
        end
        li = _make_mod(time_lead_in, 40)
        lo = _make_mod(time_lead_out, 40)
        m1 = _make_mod(time_middle_1, 30)
        m2 = _make_mod(time_middle_2, 30)
        l1 = _make_mod(time_loop_1, 30)
        l2 = _make_mod(time_loop_2, 30)
        """)

        from nodes.time_nodes import calculate_sync_gap
        g._py_calculate_sync_gap = lambda d="next", m="order", mg=None: calculate_sync_gap(context, direction=d, mode=m, max_gap=mg)
        for k_alias in ("prev", "next", "order", "style", "actor", "effect", "layer"):
            setattr(g, k_alias, k_alias)

        lua.execute("""
        local _sync_obj = {}
        setmetatable(_sync_obj, {
            __call = function(t, d, m, mg)
                return _py_calculate_sync_gap(d or "next", m or "order", mg)
            end,
            __index = function(t, k)
                local name = string.lower(tostring(k))
                local d = "next"
                local m = "order"
                if string.find(name, "prev") or name == "p" then d = "prev" end
                if string.find(name, "next") or name == "n" then d = "next" end
                for _, mode_name in ipairs({"style", "actor", "effect", "layer", "order"}) do
                    if string.find(name, mode_name) then
                        m = mode_name
                        break
                    end
                end
                return _py_calculate_sync_gap(d, m, nil)
            end
        })
        sync = _sync_obj
        """)

        remember_fn = ctx_dict.get("remember")
        recall_fn = ctx_dict.get("recall")
        g.remember = lambda k, v: remember_fn(k, v) if callable(remember_fn) else v
        g.recall = lambda k, default=None: recall_fn(k, default) if callable(recall_fn) else default

        from nodes.audio_nodes import audio_rms, audio_peak, audio_band, audio_fft
        g.audio_rms = lambda start_ms=None, end_ms=None, path=None: audio_rms(start_ms, end_ms, path, context=context)
        g.audio_peak = lambda start_ms=None, end_ms=None, path=None: audio_peak(start_ms, end_ms, path, context=context)
        g.audio_band = lambda start_ms=None, end_ms=None, min_hz=20, max_hz=250, path=None: audio_band(start_ms, end_ms, min_hz, max_hz, path, context=context)
        g.audio_fft = lambda start_ms=None, end_ms=None, num_bands=16, min_hz=20, max_hz=16000, path=None: lua.table_from(audio_fft(start_ms, end_ms, num_bands, min_hz, max_hz, path, context=context))

        line_tbl = None
        line_ink_tbl = None
        line_obj = ctx_dict.get("line") or ctx_dict.get("l") or ctx_dict.get("L")
        if line_obj:
            line_ink = getattr(line_obj, "ink", None)
            if line_ink is not None:
                line_ink_tbl = lua.table_from({
                    "left": line_ink.left,
                    "right": line_ink.right,
                    "top": line_ink.top,
                    "bottom": line_ink.bottom,
                    "width": line_ink.width,
                    "height": line_ink.height,
                    "center": line_ink.center,
                    "middle": line_ink.middle,
                    "x": line_ink.x,
                    "y": line_ink.y
                })
            line_dict = {
                "layer": getattr(line_obj, "layer", 0),
                "style_name": getattr(line_obj, "style_name", getattr(line_obj, "style", "Default")),
                "style": getattr(line_obj, "style", getattr(line_obj, "style_name", "Default")),
                "text": getattr(line_obj, "text", ""),
                "raw_text": getattr(line_obj, "raw_text", getattr(line_obj, "text", "")),
                "start_time": getattr(line_obj, "start_time", 0),
                "end_time": getattr(line_obj, "end_time", 0),
                "start": getattr(line_obj, "start_time", 0),
                "end": getattr(line_obj, "end_time", 0),
                "st": getattr(line_obj, "start_time", 0),
                "et": getattr(line_obj, "end_time", 0),
                "duration": getattr(line_obj, "duration", 0),
                "dur": getattr(line_obj, "dur", getattr(line_obj, "duration", 0)),
                "width": getattr(line_obj, "width", 0.0),
                "height": getattr(line_obj, "height", 0.0),
                "left": getattr(line_obj, "left", 0.0),
                "right": getattr(line_obj, "right", 0.0),
                "top": getattr(line_obj, "top", 0.0),
                "bottom": getattr(line_obj, "bottom", 0.0),
                "center": getattr(line_obj, "center", 0.0),
                "middle": getattr(line_obj, "middle", 0.0),
                "x": getattr(line_obj, "x", getattr(line_obj, "center", 0.0)),
                "y": getattr(line_obj, "y", getattr(line_obj, "middle", 0.0)),
                "margin_l": getattr(line_obj, "margin_l", 0),
                "margin_r": getattr(line_obj, "margin_r", 0),
                "margin_v": getattr(line_obj, "margin_v", 0),
                "actor": getattr(line_obj, "actor", ""),
                "effect": getattr(line_obj, "effect", ""),
                "i": getattr(line_obj, "i", 1),
                "n": getattr(line_obj, "n", 1)
            }
            if line_ink_tbl is not None:
                line_dict["ink"] = line_ink_tbl
            line_tbl = lua.table_from(line_dict)
            g.line = line_tbl
            g.l = line_tbl

        active_unit_obj = ctx_dict.get("active_unit")
        syl_tbl = None
        syl_unit = ctx_dict.get("syl") or active_unit_obj
        if syl_unit:
            syl_tbl = _build_unit_lua_table(lua, syl_unit, line_tbl)
            g.syl = syl_tbl
        word_tbl = None
        word_unit = ctx_dict.get("word") or getattr(active_unit_obj, "word", None)
        if word_unit:
            word_tbl = _build_unit_lua_table(lua, word_unit, line_tbl)
            g.word = word_tbl
        char_tbl = None
        char_unit = ctx_dict.get("char") or getattr(active_unit_obj, "char", None)
        if char_unit:
            char_tbl = _build_unit_lua_table(lua, char_unit, line_tbl)
            g.char = char_tbl

        prev_tbl = None
        prev_obj = getattr(active_unit_obj, "prev", None) if active_unit_obj else ctx_dict.get("prev")
        if prev_obj:
            prev_tbl = _build_unit_lua_table(lua, prev_obj, line_tbl)
            g.prev = prev_tbl
        else:
            g.prev = None

        next_tbl = None
        next_obj = getattr(active_unit_obj, "next", None) if active_unit_obj else ctx_dict.get("next")
        if next_obj:
            next_tbl = _build_unit_lua_table(lua, next_obj, line_tbl)
            g.next = next_tbl
        else:
            g.next = None

        i_val = int(ctx_dict.get("i", getattr(active_unit_obj, "i", 1)))
        n_val = int(ctx_dict.get("n", getattr(active_unit_obj, "n", 1)))
        g.is_first = (i_val == 1) or (prev_obj is None)
        g.is_last = (i_val == n_val) or (next_obj is None)
        g.has_prev = (prev_obj is not None)
        g.has_next = (next_obj is not None)

        g.outputs = lua.table_from({})
        g.out = g.outputs
        for i in range(1, 17):
            g[f"out{i}"] = None
            g[f"out_{i}"] = None
            g[f"Out{i}"] = None

        ink_tbl_dict = {
            "l": line_ink_tbl,
            "line": line_ink_tbl,
            "syl": syl_tbl["ink"] if (syl_tbl and "ink" in syl_tbl) else None,
            "char": char_tbl["ink"] if (char_tbl and "ink" in char_tbl) else None,
            "word": word_tbl["ink"] if (word_tbl and "ink" in word_tbl) else None,
        }
        active_ink = getattr(active_unit_obj or syl_unit or line_obj, "ink", None)
        if active_ink is not None:
            ink_tbl_dict.update({
                "left": active_ink.left,
                "right": active_ink.right,
                "top": active_ink.top,
                "bottom": active_ink.bottom,
                "width": active_ink.width,
                "height": active_ink.height,
                "center": active_ink.center,
                "middle": active_ink.middle,
                "x": active_ink.x,
                "y": active_ink.y
            })
        g.ink = lua.table_from(ink_tbl_dict)

        fx_pos_x = ctx_dict.get("fx_pos_x", ctx_dict.get("x", 0.0))
        fx_pos_y = ctx_dict.get("fx_pos_y", ctx_dict.get("y", 0.0))
        fx_st = ctx_dict.get("fx_start_time", ctx_dict.get("start_time", 0.0))
        fx_et = ctx_dict.get("fx_end_time", ctx_dict.get("end_time", 0.0))
        fx_dur = ctx_dict.get("fx_dur", ctx_dict.get("dur", 0.0))
        fx_align = ctx_dict.get("fx_align", 5)
        fx_i = ctx_dict.get("fx_i", ctx_dict.get("i", 1))
        fx_n = ctx_dict.get("fx_n", ctx_dict.get("n", 1))

        g.fx = lua.table_from({
            "pos_x": fx_pos_x,
            "pos_y": fx_pos_y,
            "x": fx_pos_x,
            "y": fx_pos_y,
            "i": fx_i,
            "n": fx_n,
            "start_time": fx_st,
            "st": fx_st,
            "time_start": fx_st,
            "end_time": fx_et,
            "et": fx_et,
            "time_end": fx_et,
            "dur": fx_dur,
            "duration": fx_dur,
            "time_dur": fx_dur,
            "align": fx_align
        })

        g.result = ""

        initial_vals = {
            "fx_pos_x": fx_pos_x,
            "fx_x": fx_pos_x,
            "fx_pos_y": fx_pos_y,
            "fx_y": fx_pos_y,
            "fx_start_time": fx_st,
            "fx_st": fx_st,
            "fx_time_start": fx_st,
            "fx_end_time": fx_et,
            "fx_et": fx_et,
            "fx_time_end": fx_et,
            "fx_dur": fx_dur,
            "fx_duration": fx_dur,
            "fx_time_dur": fx_dur,
            "fx_align": fx_align,
            "fx_i": fx_i,
            "fx_n": fx_n
        }
        for k, v in ctx_dict.items():
            if isinstance(k, str) and not _is_lua_callable_or_fn(v):
                if isinstance(v, (int, float, str, bool)):
                    initial_vals[k] = v

        for unit_key in ("syl", "char", "word"):
            u_obj = ctx_dict.get(unit_key) or (active_unit_obj if unit_key == "syl" else getattr(active_unit_obj, unit_key, None))
            if u_obj:
                st_u = getattr(u_obj, "start_time", getattr(u_obj, "start", getattr(u_obj, "st", None)))
                et_u = getattr(u_obj, "end_time", getattr(u_obj, "end", getattr(u_obj, "et", None)))
                dur_u = getattr(u_obj, "duration", getattr(u_obj, "dur", None))
                for attr in ("x", "y", "center", "middle", "left", "right", "top", "bottom", "text", "text_stripped"):
                    val = getattr(u_obj, attr, None)
                    if val is not None:
                        initial_vals[f"{unit_key}_{attr}"] = val
                        if attr not in initial_vals:
                            initial_vals[attr] = val
                if st_u is not None:
                    for alias in ("start_time", "st", "val_start", "start"):
                        initial_vals[f"{unit_key}_{alias}"] = st_u
                        if alias not in initial_vals:
                            initial_vals[alias] = st_u
                if et_u is not None:
                    for alias in ("end_time", "et", "val_end", "end"):
                        initial_vals[f"{unit_key}_{alias}"] = et_u
                        if alias not in initial_vals:
                            initial_vals[alias] = et_u
                if dur_u is not None:
                    for alias in ("dur", "duration", "val_dur"):
                        initial_vals[f"{unit_key}_{alias}"] = dur_u
                        if alias not in initial_vals:
                            initial_vals[alias] = dur_u

        line_obj_init = ctx_dict.get("line") or ctx_dict.get("l") or ctx_dict.get("L")
        if line_obj_init:
            st_l = getattr(line_obj_init, "start_time", getattr(line_obj_init, "start", getattr(line_obj_init, "st", None)))
            et_l = getattr(line_obj_init, "end_time", getattr(line_obj_init, "end", getattr(line_obj_init, "et", None)))
            dur_l = getattr(line_obj_init, "duration", getattr(line_obj_init, "dur", None))
            for attr in ("text", "raw_text", "style_name", "style", "layer", "margin_l", "margin_r", "margin_v", "actor", "effect"):
                val = getattr(line_obj_init, attr, None)
                if val is not None:
                    initial_vals[f"line_{attr}"] = val
                    if attr not in initial_vals:
                        initial_vals[attr] = val
            if st_l is not None:
                for alias in ("start_time", "st", "val_start", "start"):
                    initial_vals[f"line_{alias}"] = st_l
            if et_l is not None:
                for alias in ("end_time", "et", "val_end", "end"):
                    initial_vals[f"line_{alias}"] = et_l
            if dur_l is not None:
                for alias in ("dur", "duration", "val_dur"):
                    initial_vals[f"line_{alias}"] = dur_l

        lua_wrapper = f"function _pyxis_main()\n{script_str}\nend"
        lua.execute(lua_wrapper)
        res = lua.globals()._pyxis_main()
        if res is None:
            res = lua.globals().result
        res_str = str(res) if res is not None else ""

        _sync_lua_globals_to_context(g, context, ctx_dict, initial_vals=initial_vals)

        script_outputs = {}
        lua_outputs = getattr(g, "outputs", getattr(g, "out", None))
        if lua_outputs is not None:
            try:
                for k, v in lua_outputs.items():
                    script_outputs[k] = v
                    if isinstance(k, int):
                        script_outputs[f"out{k}"] = v
            except Exception:
                pass
        for i in range(1, 17):
            for prefix in (f"out{i}", f"out_{i}", f"Out{i}"):
                v = getattr(g, prefix, None)
                if v is not None:
                    script_outputs[f"out{i}"] = v
                    script_outputs[i] = v
                    break

        if type(res).__name__ == "_LuaTable":
            try:
                for k, v in res.items():
                    script_outputs[k] = v
            except Exception:
                pass
        elif isinstance(res, dict):
            for k, v in res.items():
                script_outputs[k] = v

        if isinstance(context, dict):
            context["_script_outputs"] = script_outputs
            context["outputs"] = script_outputs
            if res_str and not res_str.startswith("[Err"):
                context["script_result"] = res_str
                if '\\' in res_str or '{' in res_str:
                    existing = str(context.get("loop_tags") or context.get("tags") or "")
                    try:
                        from node_engine import merge_ass_tags
                        context["loop_tags"] = merge_ass_tags(existing, res_str)
                        context["tags"] = context["loop_tags"]
                    except Exception:
                        context["loop_tags"] = (existing + res_str).strip()
                        context["tags"] = context["loop_tags"]

        return res_str
    except Exception as e:
        err_msg = str(e)
        import re
        m = re.search(r':(\d+):', err_msg)
        if m:
            raw_ln = int(m.group(1))
            adj_ln = max(1, raw_ln - 1)
            err_msg = err_msg.replace(f":{raw_ln}:", f":{adj_ln}:", 1)
        return f"[Err Lua Script: {err_msg}]"

def code_script_master(context, script="", language="Python", **inputs_map):
    """Dispatch function for the Script Code master node."""
    script_str = str(script or "").strip()
    if not script_str:
        return ""

    chosen_lang = language or "Python"
    lang = str(chosen_lang).strip().lower()
    if lang == "lua":
        return execute_lua_script(context, script_str, inputs_map)
    else:
        return execute_python_script(context, script_str, inputs_map)

system_node(
    "System", "Script Code", node_kind="step", color="#3B82F6",
    inputs=["Loop In", "In1", "In2"],
    outputs=["Loop Out", "Result"],
    properties={
        "language": "Python",
        "script": "result = 'Hello Pyxis ' + str(in1 if in1 else syl.text)",
        "inputs_count": 2
    },
    widgets=[
        {"type": "combo", "name": "Language", "property": "language", "values": ["Python", "Lua"]}
    ]
)

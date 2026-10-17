# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc and Pyxis Effector contributors
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

"""Master ASS tag generation node (MultiTag)."""

import re
import math
import random
from utils import parse_color_to_rgb, rgb_to_ass_color

def _clean_num(val, default=0.0, decimals=2, context=None):
    if val is None or str(val).strip() == "":
        return default
    try:
        f = float(val)
        if f.is_integer():
            return int(f)
        return round(f, decimals)
    except:
        pass
    try:
        from node_engine import _eval_num_expr
        res = _eval_num_expr(val, context=context, default=default)
        f = float(res)
        if f.is_integer():
            return int(f)
        return round(f, decimals)
    except:
        return default

def _clean_alpha(val, default=0, context=None):
    v_str = str(val).strip()
    if not v_str:
        return f"&H{default:02X}&"
    if v_str.startswith("&H") or v_str.endswith("&"):
        clean = v_str.replace("&H", "").replace("&", "").strip()
        if len(clean) <= 2 and all(c in "0123456789abcdefABCDEF" for c in clean):
            return f"&H{clean.upper():>02}&"
        try:
            num = int(clean, 16)
            return f"&H{max(0, min(255, num)):02X}&"
        except:
            pass
    try:
        num = int(float(v_str))
        num = max(0, min(255, num))
        return f"&H{num:02X}&"
    except:
        pass
    try:
        from node_engine import _eval_num_expr
        res = _eval_num_expr(v_str, context=context, default=default)
        num = int(round(float(res)))
        num = max(0, min(255, num))
        return f"&H{num:02X}&"
    except:
        return "&H00&"

def _clean_color(val, default="&HFFFFFF&"):
    v_str = str(val).strip()
    if not v_str:
        return default
    if v_str.startswith("&H") or v_str.startswith("&h"):
        return v_str.upper()
    r, g, b = parse_color_to_rgb(v_str)
    return rgb_to_ass_color(r, g, b)


def tag_master(context, tag_type="pos", **kwargs):
    tag = str(tag_type or "pos").strip().lower().lstrip("\\")
    
    def clean_n(v, d=0.0, dec=2):
        return _clean_num(v, default=d, decimals=dec, context=context)

    def clean_a(v, d=0):
        return _clean_alpha(v, default=d, context=context)

    def get_val(keys, default="", pos_idx=None):
        if pos_idx is not None:
            for k in [str(pos_idx), pos_idx, f"in_{pos_idx}", f"in{pos_idx}", f"in_{pos_idx+1}", f"in{pos_idx+1}"]:
                if k in kwargs and kwargs[k] is not None and str(kwargs[k]).strip() != "":
                    return kwargs[k]

        if isinstance(keys, str):
            key_list = [keys]
        else:
            key_list = list(keys)
        
        for k_target in key_list:
            if k_target in kwargs and kwargs[k_target] is not None and str(kwargs[k_target]).strip() != "":
                return kwargs[k_target]

        for k_target in key_list:
            target_clean = str(k_target).lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", "").replace("-", "").replace("/", "")
            for k, v in kwargs.items():
                if v is not None and str(v).strip() != "":
                    k_clean = str(k).lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", "").replace("-", "").replace("/", "")
                    if k_clean == target_clean:
                        return v
        return default

    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
    ctx_pos_x = context.get('fx_pos_x', context.get('x', getattr(unit, 'center', getattr(unit, 'x', getattr(line, 'center', getattr(line, 'x', 0.0)))) if (unit or line) else 0.0)) if isinstance(context, dict) else 0.0
    ctx_pos_y = context.get('fx_pos_y', context.get('y', getattr(unit, 'middle', getattr(unit, 'y', getattr(line, 'middle', getattr(line, 'y', 0.0)))) if (unit or line) else 0.0)) if isinstance(context, dict) else 0.0

    if tag == "pos":
        x = get_val(["x", "pos_x", "x_val", "x / valor", "x (px)", "valor", "value", "val", "0"], ctx_pos_x, pos_idx=0)
        y = get_val(["y", "pos_y", "y_val", "y / valor b", "y (px)", "valor b", "val b", "1"], ctx_pos_y, pos_idx=1)
        return f"\\pos({clean_n(x)},{clean_n(y)})"
    elif tag == "move":
        x1 = get_val(["x1", "x_start", "x1_val", "x1 (px)", "x_inicio", "0"], ctx_pos_x, pos_idx=0)
        y1 = get_val(["y1", "y_start", "y1_val", "y1 (px)", "y_inicio", "1"], ctx_pos_y, pos_idx=1)
        x2 = get_val(["x2", "x_end", "x2_val", "x2 (px)", "x_fin", "2"], ctx_pos_x, pos_idx=2)
        y2 = get_val(["y2", "y_end", "y2_val", "y2 (px)", "y_fin", "3"], ctx_pos_y, pos_idx=3)
        t1 = get_val(["t1", "time1", "start_time", "t1 (ms)", "tiempo 1", "4"], "", pos_idx=4)
        t2 = get_val(["t2", "time2", "end_time", "t2 (ms)", "tiempo 2", "5"], "", pos_idx=5)
        if t1 != "" and t2 != "":
            return f"\\move({clean_n(x1)},{clean_n(y1)},{clean_n(x2)},{clean_n(y2)},{int(clean_n(t1))},{int(clean_n(t2))})"
        return f"\\move({clean_n(x1)},{clean_n(y1)},{clean_n(x2)},{clean_n(y2)})"
    elif tag == "org":
        x = get_val(["x", "org_x", "x_val", "x / valor", "x (px)", "valor", "value", "val", "0"], ctx_pos_x, pos_idx=0)
        y = get_val(["y", "org_y", "y_val", "y / valor b", "y (px)", "valor b", "val b", "1"], ctx_pos_y, pos_idx=1)
        return f"\\org({clean_n(x)},{clean_n(y)})"
    
    elif tag == "fad":
        t1 = get_val(["fade_in", "fadein", "fade in (ms)", "in", "t1"], 0, pos_idx=0)
        t2 = get_val(["fade_out", "fadeout", "fade out (ms)", "out", "t2"], 0, pos_idx=1)
        return f"\\fad({int(clean_n(t1))},{int(clean_n(t2))})"
    elif tag == "fade":
        a1 = get_val(["a1", "alpha1"], 255, pos_idx=0)
        a2 = get_val(["a2", "alpha2"], 0, pos_idx=1)
        a3 = get_val(["a3", "alpha3"], 255, pos_idx=2)
        t1 = get_val(["t1", "time1"], 0, pos_idx=3)
        t2 = get_val(["t2", "time2"], 100, pos_idx=4)
        t3 = get_val(["t3", "time3"], 200, pos_idx=5)
        t4 = get_val(["t4", "time4"], 300, pos_idx=6)
        return f"\\fade({int(clean_n(a1))},{int(clean_n(a2))},{int(clean_n(a3))},{int(clean_n(t1))},{int(clean_n(t2))},{int(clean_n(t3))},{int(clean_n(t4))})"

    elif tag == "clip":
        val = str(get_val(["value", "valor", "clip", "val", "shape", "drawing"], "", pos_idx=0)).strip()
        from nodes.shape_nodes import resolve_shape_value
        val = resolve_shape_value(val, context)
        return f"\\clip({val})"
    elif tag == "iclip":
        val = str(get_val(["value", "valor", "iclip", "val", "shape", "drawing"], "", pos_idx=0)).strip()
        from nodes.shape_nodes import resolve_shape_value
        val = resolve_shape_value(val, context)
        return f"\\iclip({val})"

    elif tag in ("c", "1c"):
        c = get_val(["value", "valor", "color", "1c", "c1", "val"], "&HFFFFFF&", pos_idx=0)
        return f"\\1c{_clean_color(c)}"
    elif tag == "2c":
        c = get_val(["value", "valor", "color", "2c", "c2", "val"], "&HFFFFFF&", pos_idx=0)
        return f"\\2c{_clean_color(c)}"
    elif tag == "3c":
        c = get_val(["value", "valor", "color", "3c", "c3", "val"], "&H000000&", pos_idx=0)
        return f"\\3c{_clean_color(c)}"
    elif tag == "4c":
        c = get_val(["value", "valor", "color", "4c", "c4", "val"], "&H000000&", pos_idx=0)
        return f"\\4c{_clean_color(c)}"

    elif tag == "alpha":
        a = get_val(["value", "valor", "alpha", "val"], 0, pos_idx=0)
        return f"\\alpha{clean_a(a)}"
    elif tag == "1a":
        a = get_val(["value", "valor", "alpha", "1a", "a1", "val"], 0, pos_idx=0)
        return f"\\1a{clean_a(a)}"
    elif tag == "2a":
        a = get_val(["value", "valor", "alpha", "2a", "a2", "val"], 0, pos_idx=0)
        return f"\\2a{clean_a(a)}"
    elif tag == "3a":
        a = get_val(["value", "valor", "alpha", "3a", "a3", "val"], 0, pos_idx=0)
        return f"\\3a{clean_a(a)}"
    elif tag == "4a":
        a = get_val(["value", "valor", "alpha", "4a", "a4", "val"], 0, pos_idx=0)
        return f"\\4a{clean_a(a)}"

    elif tag == "t":
        stags = str(get_val(["tags", "tag", "efecto", "anim"], "", pos_idx=0)).strip()
        t1 = get_val(["t1", "start", "time1"], "", pos_idx=1)
        t2 = get_val(["t2", "end", "time2"], "", pos_idx=2)
        accel = get_val(["accel", "aceleracion"], "", pos_idx=3)
        if t1 != "" and t2 != "":
            st1, st2 = int(clean_n(t1)), int(clean_n(t2))
            if accel != "":
                return f"\\t({st1},{st2},{clean_n(accel)},{stags})"
            return f"\\t({st1},{st2},{stags})"
        elif accel != "":
            return f"\\t({clean_n(accel)},{stags})"
        return f"\\t({stags})"

    else:
        val = get_val(["value", "valor", "val", "value", "v"], "", pos_idx=0)
        if tag in ("fscx", "fscy", "frz", "frx", "fry", "fax", "fay", "bord", "xbord", "ybord", "shad", "xshad", "yshad", "blur", "be", "fs", "fsp"):
            return f"\\{tag}{clean_n(val)}"
        elif tag in ("an", "b", "i", "u", "s", "k", "kf", "ko", "p", "pbo", "q"):
            return f"\\{tag}{int(clean_n(val))}"
        else:
            return f"\\{tag}{str(val).strip()}"


from decorators import pyxis_node

def eval_condition_bool(condition, context=None) -> bool:
    """Safely evaluates a boolean conditional expression in the Pyxis context."""
    if isinstance(condition, bool):
        return condition
    if isinstance(condition, (int, float)):
        return (float(condition) != 0.0)
    if isinstance(condition, str):
        v = str(condition).strip()
        v_lower = v.lower()
        if v_lower in ("true", "1", "yes", "t"):
            return True
        elif v_lower in ("false", "0", "no", "nil", "f", ""):
            return False
        else:
            try:
                from string_evaluator import eval_python_expr, _transform_outside_quotes
                v_eval = _transform_outside_quotes(v, lambda seg: seg.replace("^", "**"))
                res = eval_python_expr(v_eval, context, default=None)
                if res is not None:
                    return bool(res)
                return len(v) > 0
            except Exception:
                return len(v) > 0
    return bool(condition)


@pyxis_node("Functions", "Conditioner", ["Condition", "If True", "If False"])
def node_conditioner(context, condition=True, if_true="", if_false="", **kwargs):
    """Evaluates the condition and returns the corresponding complete item ('If True' or 'If False').
    Supports single strings, lists, or full sequences.
    """
    cond = kwargs.get("condition", kwargs.get("condicion", condition))
    t_val = kwargs.get("if_true", kwargs.get("si_verdadero", if_true))
    f_val = kwargs.get("if_false", kwargs.get("si_falso", if_false))
    cond_bool = eval_condition_bool(cond, context)
    chosen = t_val if cond_bool else f_val
    if isinstance(chosen, (list, tuple)):
        return ", ".join(str(x) for x in chosen if x is not None)
    return str(chosen)

node_tag_only = node_conditioner
node_condicionador = node_conditioner


@pyxis_node("Functions", "Color Gradient", ["Progress (0-1)", "Color List", "Total (N)", "Accel"])
def node_color_gradient(context, prog="char.i / char.n", colors_str="#95E648,#3E750C,#ED38CA", total=1, accel=1.0, tag_type="\\1c", output_slot_index=0, **kwargs):
    """Multi-stop color interpolator (Effector color.gradient style) with batch list outputs."""
    from node_engine import _eval_num_expr

    raw_str = str(colors_str if (colors_str is not None and str(colors_str).strip() != "") else kwargs.get("colors", "#95E648,#3E750C,#ED38CA")).strip()
    if not raw_str:
        return "&HFFFFFF&"

    raw_tokens = [t.strip() for t in raw_str.replace(";", ",").replace("\n", ",").split(",") if t.strip()]
    if not raw_tokens:
        raw_tokens = [t.strip() for t in raw_str.split() if t.strip()]

    if not raw_tokens:
        return "&HFFFFFF&"

    tag_clean = str(tag_type if (tag_type is not None and str(tag_type).strip() != "") else kwargs.get("tag", "\\1c")).strip()
    if not tag_clean.startswith("\\"):
        tag_clean = "\\" + tag_clean

    try:
        accel_val = max(0.001, float(_eval_num_expr(accel, context, 1.0)))
    except Exception:
        accel_val = 1.0

    def _apply_easing(t_norm):
        if accel_val != 1.0 and 0.0 < t_norm < 1.0:
            if accel_val > 1.0:
                return t_norm ** accel_val
            elif accel_val > 0.0:
                p = 1.0 / accel_val
                return 1.0 - ((1.0 - t_norm) ** p)
        return t_norm

    def _eval_at_t(t_in):
        t_clamped = max(0.0, min(1.0, _apply_easing(t_in)))
        if len(raw_tokens) == 1:
            return _clean_color(raw_tokens[0])

        n_segments = len(raw_tokens) - 1
        pos = t_clamped * n_segments
        idx = int(pos)
        if idx >= n_segments:
            idx = n_segments - 1
            local_t = 1.0
        else:
            local_t = pos - idx

        c1_str = raw_tokens[idx]
        c2_str = raw_tokens[idx + 1]

        r1, g1, b1 = parse_color_to_rgb(c1_str)
        r2, g2, b2 = parse_color_to_rgb(c2_str)

        r = int(round(r1 + (r2 - r1) * local_t))
        g = int(round(g1 + (g2 - g1) * local_t))
        b = int(round(b1 + (b2 - b1) * local_t))

        return rgb_to_ass_color(r, g, b)

    try:
        raw_prog = prog if prog is not None else kwargs.get("progress", 0.0)
        pct = float(_eval_num_expr(raw_prog, context, 0.0))
    except (ValueError, TypeError):
        pct = 0.0

    try:
        raw_total = total if total is not None else kwargs.get("n", kwargs.get("count", 1))
        n_val = max(1, int(round(float(_eval_num_expr(raw_total, context, 1)))))
    except Exception:
        n_val = 1

    if output_slot_index == 0:
        return _eval_at_t(pct)

    if output_slot_index == 1:
        if n_val > 1 or kwargs.get("return_batch", False):
            colors_batch = []
            for k in range(1, n_val + 1):
                tk = (k - 1.0) / (n_val - 1.0) if n_val > 1 else 0.0
                colors_batch.append(_eval_at_t(tk))
            return ", ".join(colors_batch)
        return _eval_at_t(pct)

    if output_slot_index == 2 or kwargs.get("return_tags", False):
        if n_val > 1 or kwargs.get("return_batch", False):
            tags_batch = []
            for k in range(1, n_val + 1):
                tk = (k - 1.0) / (n_val - 1.0) if n_val > 1 else 0.0
                tags_batch.append(f"{tag_clean}{_eval_at_t(tk)}")
            return ", ".join(tags_batch)
        return f"{tag_clean}{_eval_at_t(pct)}"

    return _eval_at_t(pct)

import random

@pyxis_node("Functions", "Tag Oscillator", [
    "Start Time", "End Time", "Step (ms)", "Trans (ms)",
    "Duty Cycle", "Tags", "Accel", "Dilate Step",
    "Dilate Trans", "Seq Offset", "Rhythm Pattern"
])
def tag_oscillator_node(
    context=None,
    start_time=None,
    end_time=None,
    step_ms=200.0,
    trans_ms=50.0,
    duty_cycle=None,
    tags=r"\frz30\fry20,\frz-20\fry-20",
    accel=1.0,
    dilat_step_ms=0.0,
    dilat_trans_ms=0.0,
    offset_seq_ms=0.0,
    rhythm_pattern="",
    oscillation_mode=None,
    order_mode=None,
    output_slot_index=0,
    **kwargs
):
    """Master continuous ASS oscillation generator (Standard Polars)."""
    from node_engine import _eval_num_expr

    ctx = context if isinstance(context, dict) else {}
    unit = ctx.get("active_unit")
    line = ctx.get("line")

    if start_time is None or str(start_time).strip() == "":
        st = 0.0
    else:
        st = float(_eval_num_expr(start_time, ctx, 0.0))

    if end_time is None or str(end_time).strip() == "":
        if "effect_dur" in ctx and float(ctx.get("effect_dur", 0)) > 0:
            et = float(ctx["effect_dur"])
        elif unit is not None and hasattr(unit, "duration") and float(getattr(unit, "duration", 0)) > 0:
            et = float(unit.duration)
        elif unit is not None and hasattr(unit, "end_time") and hasattr(unit, "start_time"):
            et = float(unit.end_time - unit.start_time)
        elif "fx_dur" in ctx and float(ctx.get("fx_dur", 0)) > 0:
            et = float(ctx["fx_dur"])
        elif line is not None and hasattr(line, "duration") and float(getattr(line, "duration", 0)) > 0:
            et = float(line.duration)
        else:
            et = float(ctx.get("end_time", getattr(unit, "end_time", 1000.0)))
    else:
        et = float(_eval_num_expr(end_time, ctx, 1000.0))

    dur = max(1.0, et - st)

    p_step = float(_eval_num_expr(step_ms, ctx, 200.0))
    p_trans = float(_eval_num_expr(trans_ms, ctx, 50.0))
    p_accel = float(_eval_num_expr(accel, ctx, 1.0))
    p_dilat_step = float(_eval_num_expr(dilat_step_ms, ctx, 0.0))
    p_dilat_trans = float(_eval_num_expr(dilat_trans_ms, ctx, 0.0))
    p_offset_seq = float(_eval_num_expr(offset_seq_ms, ctx, 0.0))

    if isinstance(tags, (list, tuple)):
        tag_list = [str(x).strip() for x in tags if str(x).strip()]
    else:
        raw_s = str(tags or r"\frz30\fry20,\frz-20\fry-20").strip()
        tag_list = [x.strip() for x in raw_s.replace(";", ",").replace("\n", ",").split(",") if x.strip()]

    if not tag_list:
        tag_list = [r"\fscx100\fscy100"]

    rhythm_steps = []
    if rhythm_pattern:
        if isinstance(rhythm_pattern, (list, tuple)):
            rhythm_steps = [float(x) for x in rhythm_pattern if float(x) > 0]
        else:
            raw_r = str(rhythm_pattern).replace(";", ",").split(",")
            for p in raw_r:
                try:
                    v = float(p.strip())
                    if v > 0:
                        rhythm_steps.append(v)
                except Exception:
                    pass

    mode_osc = str(oscillation_mode if (oscillation_mode is not None and str(oscillation_mode).strip() != "") else kwargs.get("modo_oscilacion", kwargs.get("mode", "wave"))).strip().lower()
    mode_ord = str(order_mode if (order_mode is not None and str(order_mode).strip() != "") else kwargs.get("modo_orden", kwargs.get("order_mode", kwargs.get("order", "sequential")))).strip().lower()
    is_strobe = ("strobe" in mode_osc or "destello" in mode_osc or "step" in mode_osc or "flashes" in mode_osc)

    keyframes = []
    t_curr = 0.0
    i = 0
    prev_idx = -1

    while t_curr < dur:
        if rhythm_steps:
            curr_step = rhythm_steps[i % len(rhythm_steps)]
        else:
            curr_step = max(5.0, p_step + p_dilat_step * i)

        if is_strobe:
            curr_trans = 0.0
        elif duty_cycle is not None and str(duty_cycle).strip() != "":
            dc_val = float(_eval_num_expr(duty_cycle, ctx, 0.5))
            curr_trans = curr_step * max(0.01, min(1.0, dc_val))
        else:
            curr_trans = p_trans + p_dilat_trans * i
            if curr_trans <= 0 and ("onda" in mode_osc or "wave" in mode_osc):
                curr_trans = curr_step
            elif curr_trans <= 0 and ("pulso" in mode_osc or "pulse" in mode_osc):
                curr_trans = curr_step * 0.5
            elif curr_trans <= 0 and not is_strobe:
                curr_trans = curr_step

        curr_trans = min(curr_step, max(0.0, curr_trans))

        n_tags = len(tag_list)
        if "pong" in mode_ord or "ping" in mode_ord:
            cycle = (2 * n_tags - 2) if n_tags > 1 else 1
            mod = i % cycle
            tag_idx = mod if mod < n_tags else (2 * n_tags - 2 - mod)
        elif "rand" in mode_ord or "aleatorio" in mode_ord:
            rnd = random.Random(42 + i)
            tag_idx = rnd.randint(0, n_tags - 1)
        elif "shuff" in mode_ord:
            rnd = random.Random(42 + i)
            candidates = [k for k in range(n_tags) if k != prev_idx] or [0]
            tag_idx = rnd.choice(candidates)
        else:
            tag_idx = i % n_tags

        prev_idx = tag_idx
        tag_str = tag_list[tag_idx]

        t1 = int(round(st + t_curr))
        if is_strobe or curr_trans <= 0:
            t2 = t1
        else:
            t2 = int(round(st + t_curr + curr_trans))
            if t2 > st + dur:
                t2 = int(round(st + dur))
            elif (t_curr + curr_step >= dur) and (p_trans <= 0 or curr_trans >= curr_step * 0.99):
                t2 = int(round(st + dur))

        keyframes.append((t1, t2, tag_str, p_accel))

        t_next = t_curr + curr_step
        if (i + 1) % n_tags == 0 and p_offset_seq > 0:
            t_next += p_offset_seq

        if t_next <= t_curr:
            t_next = t_curr + 1.0

        t_curr = t_next
        i += 1

    if output_slot_index == 2:
        return keyframes

    if output_slot_index == 3:
        return [k[2] for k in keyframes]

    if output_slot_index == 1:
        current_time = float(ctx.get("frame_time", ctx.get("fx_start_time", st)))
        rel_t = max(0.0, min(dur, current_time - st))
        active_tag = keyframes[0][2] if keyframes else ""
        for t1, t2, tag_str, acc in keyframes:
            if rel_t >= t1:
                active_tag = tag_str
            if rel_t <= t2:
                break
        return active_tag

    parts = []
    for t1, t2, tag_str, acc in keyframes:
        if t2 <= t1 or is_strobe:
            parts.append(f"\\t({t1},{t1+1},{tag_str})")
        else:
            if abs(acc - 1.0) > 0.001:
                parts.append(f"\\t({t1},{t2},{acc:.2f},{tag_str})")
            else:
                parts.append(f"\\t({t1},{t2},{tag_str})")

    return "".join(parts)


@pyxis_node("Functions", "Glitter", [
    "Start Time", "End Time", "Density", "In 1"
])
def glitter_node(
    context=None,
    start_time=None,
    end_time=None,
    density=1.0,
    random_profile=None,
    seed=0,
    tags=None,
    mins=None,
    maxs=None,
    output_slot_index=0,
    **kwargs
):
    """Dynamic stochastic generator for flashes (Glitter), waves, and pulses for ASS tags."""
    from node_engine import _eval_num_expr
    from utils import parse_color_to_rgb, rgb_to_ass_color

    ctx = context if isinstance(context, dict) else {}
    unit = ctx.get("active_unit")
    line = ctx.get("line")

    if start_time is None or str(start_time).strip() == "":
        st = 0.0
    else:
        try:
            st = float(_eval_num_expr(start_time, ctx, 0.0))
        except Exception:
            st = 0.0

    if end_time is None or str(end_time).strip() == "":
        end_time = "fx.dur"

    try:
        et = float(_eval_num_expr(end_time, ctx, 1000.0))
        if et <= 0.0 and str(end_time).strip().lower() in ("fx.dur", "fx_dur", "dur"):
            et = 1000.0
    except Exception:
        et = 1000.0

    dur = max(1.0, et - st)

    if tags is None:
        tags = [kwargs.get("tag_0", kwargs.get("tag", r"\fscx"))]
    elif not isinstance(tags, list):
        tags = [tags]

    if mins is None:
        mins = [kwargs.get("min_0", kwargs.get("min", "150"))]
    elif not isinstance(mins, list):
        mins = [mins]

    if maxs is None:
        maxs = [kwargs.get("max_0", kwargs.get("max", "250"))]
    elif not isinstance(maxs, list):
        maxs = [maxs]

    idx = 0
    clean_tags = []
    clean_mins = []
    clean_maxs = []
    while f"tag_{idx}" in kwargs or idx < len(tags):
        t_val = kwargs.get(f"tag_{idx}", tags[idx] if idx < len(tags) else r"\fscx")
        m_val = kwargs.get(f"min_{idx}", mins[idx] if idx < len(mins) else "150")
        x_val = kwargs.get(f"max_{idx}", maxs[idx] if idx < len(maxs) else "250")
        clean_tags.append(str(t_val if t_val is not None else "").strip())
        clean_mins.append(str(m_val if m_val is not None else "").strip())
        clean_maxs.append(str(x_val if x_val is not None else "").strip())
        idx += 1

    if not clean_tags:
        clean_tags = [r"\fscx"]
        clean_mins = ["150"]
        clean_maxs = ["250"]

    expanded_tags = []
    expanded_mins = []
    expanded_maxs = []
    for t_raw, m_raw, x_raw in zip(clean_tags, clean_mins, clean_maxs):
        sub_tags = re.findall(r"\\[a-zA-Z0-9]+", t_raw)
        if len(sub_tags) > 1:
            m_parts = [p.strip() for p in m_raw.replace(";", ",").split(",") if p.strip()]
            x_parts = [p.strip() for p in x_raw.replace(";", ",").split(",") if p.strip()]
            for s_i, stg in enumerate(sub_tags):
                expanded_tags.append(stg)
                expanded_mins.append(m_parts[s_i] if s_i < len(m_parts) else (m_parts[0] if m_parts else "150"))
                expanded_maxs.append(x_parts[s_i] if s_i < len(x_parts) else (x_parts[0] if x_parts else "250"))
        else:
            expanded_tags.append(t_raw)
            expanded_mins.append(m_raw)
            expanded_maxs.append(x_raw)

    clean_tags = expanded_tags
    clean_mins = expanded_mins
    clean_maxs = expanded_maxs

    profile_mode = str(random_profile if (random_profile is not None and str(random_profile).strip() != "") else kwargs.get("modo_oscilacion", kwargs.get("mode", kwargs.get("profile", "flashes")))).strip().lower()
    is_destello = ("destello" in profile_mode or "strobe" in profile_mode or "flash" in profile_mode or "glitter" in profile_mode)
    is_pulso = ("pulso" in profile_mode or "pulse" in profile_mode or "beat" in profile_mode)
    is_oleaje = ("oleaje" in profile_mode or "onda" in profile_mode or "wave" in profile_mode or "smooth" in profile_mode)

    try:
        dens_val = max(0.05, float(_eval_num_expr(density, ctx, 1.0)))
    except Exception:
        dens_val = 1.0

    unit_i = getattr(unit, "i", ctx.get("fx_i", ctx.get("j", ctx.get("i", 0)))) if unit else ctx.get("fx_i", ctx.get("j", ctx.get("i", 0)))
    try:
        seed_val = int(float(_eval_num_expr(seed, ctx, 0.0)))
    except Exception:
        seed_val = 0
    rng = random.Random(seed_val * 1000 + int(unit_i or 0) + 1337)

    DARK_TAGS_EXPANSION = {
        r"\fscxy": (r"\fscx", r"\fscy"),
        r"\faxy": (r"\fax", r"\fay"),
        r"\frxyz": (r"\frx", r"\fry", r"\frz"),
        r"\frxy": (r"\frx", r"\fry"),
        r"\frxz": (r"\frx", r"\frz"),
        r"\fryz": (r"\fry", r"\frz"),
        r"\xybord": (r"\xbord", r"\ybord"),
        r"\xyshad": (r"\xshad", r"\yshad"),
        r"\bs": (r"\bord", r"\shad"),
        r"\134c": (r"\1c", r"\3c", r"\4c"),
        r"\13c": (r"\1c", r"\3c"),
        r"\14c": (r"\1c", r"\4c"),
        r"\34c": (r"\3c", r"\4c"),
        r"\134a": (r"\1a", r"\3a", r"\4a"),
        r"\13a": (r"\1a", r"\3a"),
        r"\14a": (r"\1a", r"\4a"),
        r"\34a": (r"\3a", r"\4a"),
    }

    def _format_tag_with_val(t_name, val):
        clean_t = str(t_name or "").strip()
        if not clean_t.startswith("\\"):
            clean_t = "\\" + clean_t
        lower_t = clean_t.lower()
        if lower_t in DARK_TAGS_EXPANSION:
            target_tags = DARK_TAGS_EXPANSION[lower_t]
            return "".join(f"{stg}{val}" for stg in target_tags)
        return f"{clean_t}{val}"

    def _get_random_value(min_str, max_str, rnd_factor, tag_hint=""):
        min_s = str(min_str).strip()
        max_s = str(max_str).strip()
        is_color = (min_s.startswith("&H") or min_s.startswith("&h") or min_s.startswith("#") or
                    max_s.startswith("&H") or max_s.startswith("&h") or max_s.startswith("#") or
                    tag_hint.lower().endswith("c"))
        if is_color:
            r1, g1, b1 = parse_color_to_rgb(min_s)
            r2, g2, b2 = parse_color_to_rgb(max_s)
            r_int = int(round(r1 + (r2 - r1) * rnd_factor))
            g_int = int(round(g1 + (g2 - g1) * rnd_factor))
            b_int = int(round(b1 + (b2 - b1) * rnd_factor))
            return rgb_to_ass_color(r_int, g_int, b_int)
        else:
            try:
                v1 = float(_eval_num_expr(min_s, ctx, 0.0))
                v2 = float(_eval_num_expr(max_s, ctx, 100.0))
                val = v1 + (v2 - v1) * rnd_factor
                if "." not in min_s and "." not in max_s:
                    return str(int(round(val)))
                if abs(val - round(val)) < 1e-4:
                    return str(int(round(val)))
                return f"{val:.2f}"
            except Exception:
                return min_s

    row_results = [[] for _ in range(len(clean_tags))]
    combined_results = []
    t_curr = 0.0

    while t_curr < dur:
        if is_destello:
            pause_len = rng.uniform(20.0, max(40.0, dur * 0.35)) / dens_val
            rise_len = rng.uniform(1.0, 3.0)
            hold_len = rng.uniform(5.0, 15.0)
            decay_len = rng.uniform(40.0, 100.0)

            t1 = int(round(st + t_curr + pause_len))
            t2 = int(round(t1 + rise_len))
            t3 = int(round(t2 + hold_len))
            t4 = int(round(t3 + decay_len))

            if t1 >= st + dur:
                break
            t2 = min(t2, int(round(st + dur)))
            t3 = min(t3, int(round(st + dur)))
            t4 = min(t4, int(round(st + dur)))

            step_peak_tags = []
            step_base_tags = []

            for r_idx in range(len(clean_tags)):
                t_name = clean_tags[r_idx]
                if not t_name:
                    continue
                if not t_name.startswith("\\"):
                    t_name = "\\" + t_name

                mn = clean_mins[r_idx]
                mx = clean_maxs[r_idx]

                rnd_f1 = rng.uniform(0.65, 1.0)
                rnd_f2 = rng.uniform(0.0, 0.25)
                val_peak = _get_random_value(mn, mx, rnd_f1, t_name)
                val_base = _get_random_value(mn, mx, rnd_f2, t_name)

                peak_str = _format_tag_with_val(t_name, val_peak)
                base_str = _format_tag_with_val(t_name, val_base)
                step_peak_tags.append(peak_str)
                step_base_tags.append(base_str)

                if t4 > t3:
                    row_results[r_idx].append(f"\\t({t1},{t2},{peak_str})\\t({t3},{t4},{base_str})")
                else:
                    row_results[r_idx].append(f"\\t({t1},{t2},{peak_str})")

            if step_peak_tags:
                all_peak = "".join(step_peak_tags)
                all_base = "".join(step_base_tags)
                if t4 > t3:
                    combined_results.append(f"\\t({t1},{t2},{all_peak})\\t({t3},{t4},{all_base})")
                else:
                    combined_results.append(f"\\t({t1},{t2},{all_peak})")

            t_curr = max(t_curr + 10.0, (t4 - st))

        elif is_pulso:
            pause_len = rng.uniform(30.0, 100.0) / dens_val
            rise_len = rng.uniform(150.0, 250.0)
            hold_len = rng.uniform(10.0, 30.0)
            decay_len = rng.uniform(150.0, 250.0)
            accel_val = rng.uniform(0.75, 1.35)

            t1 = int(round(st + t_curr + pause_len))
            t2 = int(round(t1 + rise_len))
            t3 = int(round(t2 + hold_len))
            t4 = int(round(t3 + decay_len))

            if t1 >= st + dur:
                break
            t2 = min(t2, int(round(st + dur)))
            t3 = min(t3, int(round(st + dur)))
            t4 = min(t4, int(round(st + dur)))

            step_peak_tags = []
            step_base_tags = []

            for r_idx in range(len(clean_tags)):
                t_name = clean_tags[r_idx]
                if not t_name:
                    continue
                if not t_name.startswith("\\"):
                    t_name = "\\" + t_name

                mn = clean_mins[r_idx]
                mx = clean_maxs[r_idx]

                rnd_f1 = rng.uniform(0.7, 1.0)
                rnd_f2 = rng.uniform(0.0, 0.2)
                val_peak = _get_random_value(mn, mx, rnd_f1, t_name)
                val_base = _get_random_value(mn, mx, rnd_f2, t_name)

                peak_str = _format_tag_with_val(t_name, val_peak)
                base_str = _format_tag_with_val(t_name, val_base)
                step_peak_tags.append(peak_str)
                step_base_tags.append(base_str)

                accel_prefix = f"{accel_val:.2f}," if abs(accel_val - 1.0) > 0.05 else ""
                if t4 > t3:
                    row_results[r_idx].append(f"\\t({t1},{t2},{accel_prefix}{peak_str})\\t({t3},{t4},{base_str})")
                else:
                    row_results[r_idx].append(f"\\t({t1},{t2},{accel_prefix}{peak_str})")

            if step_peak_tags:
                all_peak = "".join(step_peak_tags)
                all_base = "".join(step_base_tags)
                accel_prefix = f"{accel_val:.2f}," if abs(accel_val - 1.0) > 0.05 else ""
                if t4 > t3:
                    combined_results.append(f"\\t({t1},{t2},{accel_prefix}{all_peak})\\t({t3},{t4},{all_base})")
                else:
                    combined_results.append(f"\\t({t1},{t2},{accel_prefix}{all_peak})")

            t_curr = max(t_curr + 10.0, (t4 - st))

        elif is_oleaje:
            pause_len = rng.uniform(0.0, 10.0) / dens_val
            rise_len = rng.uniform(250.0, 400.0)
            decay_len = rng.uniform(250.0, 400.0)

            t1 = int(round(st + t_curr + pause_len))
            t2 = int(round(t1 + rise_len))
            t3 = int(round(t2 + decay_len))

            if t1 >= st + dur:
                break
            t2 = min(t2, int(round(st + dur)))
            t3 = min(t3, int(round(st + dur)))

            step_peak_tags = []
            step_base_tags = []

            for r_idx in range(len(clean_tags)):
                t_name = clean_tags[r_idx]
                if not t_name:
                    continue
                if not t_name.startswith("\\"):
                    t_name = "\\" + t_name

                mn = clean_mins[r_idx]
                mx = clean_maxs[r_idx]

                rnd_f1 = rng.uniform(0.75, 1.0)
                rnd_f2 = rng.uniform(0.0, 0.25)
                val_peak = _get_random_value(mn, mx, rnd_f1, t_name)
                val_base = _get_random_value(mn, mx, rnd_f2, t_name)

                peak_str = _format_tag_with_val(t_name, val_peak)
                base_str = _format_tag_with_val(t_name, val_base)
                step_peak_tags.append(peak_str)
                step_base_tags.append(base_str)

                if t3 > t2:
                    row_results[r_idx].append(f"\\t({t1},{t2},{peak_str})\\t({t2},{t3},{base_str})")
                else:
                    row_results[r_idx].append(f"\\t({t1},{t2},{peak_str})")

            if step_peak_tags:
                all_peak = "".join(step_peak_tags)
                all_base = "".join(step_base_tags)
                if t3 > t2:
                    combined_results.append(f"\\t({t1},{t2},{all_peak})\\t({t2},{t3},{all_base})")
                else:
                    combined_results.append(f"\\t({t1},{t2},{all_peak})")

            t_curr = max(t_curr + 10.0, (t3 - st))

        else:
            pause_len = rng.uniform(0.0, 15.0) / dens_val
            trans_len = rng.uniform(15.0, 50.0)
            accel_val = rng.uniform(0.5, 2.0)

            t1 = int(round(st + t_curr + pause_len))
            t2 = int(round(t1 + trans_len))

            if t1 >= st + dur:
                break
            t2 = min(t2, int(round(st + dur)))

            step_tags = []
            for r_idx in range(len(clean_tags)):
                t_name = clean_tags[r_idx]
                if not t_name:
                    continue
                if not t_name.startswith("\\"):
                    t_name = "\\" + t_name

                mn = clean_mins[r_idx]
                mx = clean_maxs[r_idx]
                rnd_f = rng.random()
                val_rnd = _get_random_value(mn, mx, rnd_f, t_name)
                tag_str = _format_tag_with_val(t_name, val_rnd)
                step_tags.append(tag_str)
                accel_prefix = f"{accel_val:.2f}," if abs(accel_val - 1.0) > 0.05 else ""
                row_results[r_idx].append(f"\\t({t1},{t2},{accel_prefix}{tag_str})")

            if step_tags:
                all_tags = "".join(step_tags)
                accel_prefix = f"{accel_val:.2f}," if abs(accel_val - 1.0) > 0.05 else ""
                combined_results.append(f"\\t({t1},{t2},{accel_prefix}{all_tags})")

            t_curr = max(t_curr + 10.0, (t2 - st))

    comb_str = "".join(combined_results)
    row_strs = ["".join(r) for r in row_results]

    try:
        from string_evaluator import expand_custom_dark_tags
        comb_str = expand_custom_dark_tags(comb_str, ctx)
        row_strs = [expand_custom_dark_tags(r, ctx) for r in row_strs]
    except Exception:
        pass

    if output_slot_index == -1:
        return (comb_str, row_strs)
    if output_slot_index == 0 or output_slot_index is None:
        return comb_str
    else:
        target_r = output_slot_index - 1
        if 0 <= target_r < len(row_strs):
            return row_strs[target_r]
        return ""


from decorators import NODE_REGISTRY
NODE_REGISTRY["MultiTag"] = tag_master
NODE_REGISTRY["Basics/MultiTag"] = tag_master
NODE_REGISTRY["Functions/Conditioner"] = node_conditioner
NODE_REGISTRY["Conditioner"] = node_conditioner
NODE_REGISTRY["Functions/Tag Oscillator"] = tag_oscillator_node
NODE_REGISTRY["Tag Oscillator"] = tag_oscillator_node
NODE_REGISTRY["Functions/Glitter"] = glitter_node
NODE_REGISTRY["Glitter"] = glitter_node


def _resample_shape_arc_length(shape_str, step_px=7.5):
    if not shape_str or not isinstance(shape_str, str):
        return []

    tokens = shape_str.strip().split()
    i = 0
    cmd = 'm'
    curr_x, curr_y = 0.0, 0.0
    segments = []
    
    while i < len(tokens):
        tok = tokens[i]
        if tok in ('m', 'l', 'b', 's', 'p', 'c'):
            cmd = tok
            i += 1
            continue
        if cmd == 'm':
            try:
                curr_x = float(tokens[i])
                curr_y = float(tokens[i+1])
                i += 2
            except (ValueError, IndexError):
                i += 1
        elif cmd == 'l':
            try:
                next_x = float(tokens[i])
                next_y = float(tokens[i+1])
                segments.append(('l', curr_x, curr_y, next_x, next_y))
                curr_x, curr_y = next_x, next_y
                i += 2
            except (ValueError, IndexError):
                i += 1
        elif cmd == 'b':
            try:
                x1, y1 = float(tokens[i]), float(tokens[i+1])
                x2, y2 = float(tokens[i+2]), float(tokens[i+3])
                x3, y3 = float(tokens[i+4]), float(tokens[i+5])
                segments.append(('b', curr_x, curr_y, x1, y1, x2, y2, x3, y3))
                curr_x, curr_y = x3, y3
                i += 6
            except (ValueError, IndexError):
                i += 1
        else:
            i += 1

    if not segments:
        return [(curr_x, curr_y, 0.0)]

    step_px = max(0.5, float(step_px or 7.5))
    resampled = []
    
    start_x, start_y = segments[0][1], segments[0][2]
    resampled.append((start_x, start_y, 0.0))
    cum_dist = 0.0

    for seg in segments:
        stype = seg[0]
        if stype == 'l':
            _, x0, y0, x1, y1 = seg
            seg_len = math.hypot(x1 - x0, y1 - y0)
            if seg_len < 1e-6:
                continue
            n_sub = max(1, int(round(seg_len / step_px)))
            for k in range(1, n_sub + 1):
                t = k / n_sub
                px = x0 + (x1 - x0) * t
                py = y0 + (y1 - y0) * t
                step_d = math.hypot(px - resampled[-1][0], py - resampled[-1][1])
                cum_dist += step_d
                resampled.append((px, py, cum_dist))
        elif stype == 'b':
            _, x0, y0, x1, y1, x2, y2, x3, y3 = seg
            fine_steps = 30
            b_len = 0.0
            prev_bx, prev_by = x0, y0
            for k in range(1, fine_steps + 1):
                t = k / fine_steps
                mt = 1 - t
                bx = mt**3 * x0 + 3*mt**2*t * x1 + 3*mt*t**2 * x2 + t**3 * x3
                by = mt**3 * y0 + 3*mt**2*t * y1 + 3*mt*t**2 * y2 + t**3 * y3
                b_len += math.hypot(bx - prev_bx, by - prev_by)
                prev_bx, prev_by = bx, by

            n_sub = max(1, int(round(b_len / step_px)))
            for k in range(1, n_sub + 1):
                t = k / n_sub
                mt = 1 - t
                px = mt**3 * x0 + 3*mt**2*t * x1 + 3*mt*t**2 * x2 + t**3 * x3
                py = mt**3 * y0 + 3*mt**2*t * y1 + 3*mt*t**2 * y2 + t**3 * y3
                step_d = math.hypot(px - resampled[-1][0], py - resampled[-1][1])
                cum_dist += step_d
                resampled.append((px, py, cum_dist))

    return resampled


def _parse_points_input(points_raw, step_px=7.5):
    if isinstance(points_raw, str):
        cleaned = points_raw.strip()
        if cleaned.lower().startswith('m ') or re.search(r'\b[mlbc]\s+[-?\d]', cleaned, re.IGNORECASE):
            shp_pts = _resample_shape_arc_length(cleaned, step_px=step_px)
            if shp_pts:
                return shp_pts

    pairs = []
    if isinstance(points_raw, (list, tuple)):
        for item in points_raw:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                try:
                    pairs.append((float(item[0]), float(item[1])))
                except (ValueError, TypeError):
                    pass
            elif isinstance(item, dict) and 'x' in item and 'y' in item:
                try:
                    pairs.append((float(item['x']), float(item['y'])))
                except (ValueError, TypeError):
                    pass
    elif isinstance(points_raw, str):
        for chunk in re.split(r'[;\n]+', points_raw):
            parts = [p.strip() for p in chunk.replace(',', ' ').split() if p.strip()]
            if len(parts) >= 2:
                try:
                    pairs.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    pass

    if not pairs and isinstance(points_raw, str) and points_raw.strip():
        shp_pts = _resample_shape_arc_length(points_raw.strip(), step_px=step_px)
        if shp_pts:
            return shp_pts

    if not pairs:
        return []

    if len(pairs) == 1:
        return [(pairs[0][0], pairs[0][1], 0.0)]

    step_px = max(0.5, float(step_px or 7.5))
    resampled = [(pairs[0][0], pairs[0][1], 0.0)]
    cum_dist = 0.0

    for i in range(1, len(pairs)):
        x0, y0 = pairs[i-1]
        x1, y1 = pairs[i]
        seg_len = math.hypot(x1 - x0, y1 - y0)
        if seg_len < 1e-6:
            continue
        n_sub = max(1, int(round(seg_len / step_px)))
        for k in range(1, n_sub + 1):
            t = k / n_sub
            px = x0 + (x1 - x0) * t
            py = y0 + (y1 - y0) * t
            step_d = math.hypot(px - resampled[-1][0], py - resampled[-1][1])
            cum_dist += step_d
            resampled.append((px, py, cum_dist))

    return resampled


def _get_shape_add_y(shape_str):
    """Calculates vertical compensation required to align shape center
    with ASS drawing baseline: add_y = (max_y - min_y) - cy."""
    if not shape_str or not isinstance(shape_str, str):
        return 0.0
    tokens = shape_str.replace(",", " ").split()
    ys = []
    i = 0
    while i < len(tokens):
        t_token = tokens[i]
        if t_token in ("m", "l", "b", "s", "p", "c"):
            i += 1
            continue
        try:
            x_val = float(tokens[i])
            if i + 1 < len(tokens):
                y_val = float(tokens[i+1])
                ys.append(y_val)
                i += 2
                continue
        except ValueError:
            pass
        i += 1
    if not ys:
        return 0.0
    min_y = min(ys)
    max_y = max(ys)
    cy = (min_y + max_y) / 2.0
    return (max_y - min_y) - cy


def _relocate_points(points, anchor="center", context=None, is_text_vector=False):
    if not points:
        return []

    anchor_str = str(anchor or "center").strip().lower()
    if anchor_str == "origin":
        return points

    cx, cy = 0.0, 0.0
    if context:
        active_unit = getattr(context, "active_unit", None) or (context.get("active_unit") if isinstance(context, dict) else None)
        if active_unit:
            cx = float(getattr(active_unit, "center", 0.0) or getattr(active_unit, "pos_x", 0.0) or getattr(active_unit, "x", 0.0) or 0.0)
            cy = float(getattr(active_unit, "middle", 0.0) or getattr(active_unit, "pos_y", 0.0) or getattr(active_unit, "y", 0.0) or 0.0)

    if is_text_vector:
        # FontVectorEngine typographical vectors are already centered at (0, 0)
        # in direct alignment with the typographical bounding box (center, middle).
        return [(p[0] + cx, p[1] + cy, p[2]) for p in points]

    if anchor_str == "first_point":
        p0_x, p0_y = points[0][0], points[0][1]
        dx = cx - p0_x
        dy = cy - p0_y
    else:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        bx = (min(xs) + max(xs)) / 2.0
        by = (min(ys) + max(ys)) / 2.0
        dx = cx - bx
        dy = cy - by

    return [(p[0] + dx, p[1] + dy, p[2]) for p in points]


def _get_default_dur(context, default_val=300.0):
    if context:
        fx = getattr(context, "fx", None) or (context.get("fx") if isinstance(context, dict) else None)
        if fx:
            dur = getattr(fx, "dur", None) or (fx.get("dur") if isinstance(fx, dict) else None)
            if dur is not None:
                try:
                    return float(dur)
                except (ValueError, TypeError):
                    pass
        try:
            val = _clean_num("fx.dur", default=None, context=context)
            if val is not None and isinstance(val, (int, float)):
                return float(val)
        except Exception:
            pass
    return float(default_val)


def _get_style_prop(context, prop_name, default_val=0.0):
    if context and isinstance(context, dict):
        style = context.get('style') or context.get('active_style')
        if style:
            val = getattr(style, prop_name, None) if not isinstance(style, dict) else style.get(prop_name)
            if val is None:
                cap_name = prop_name.capitalize() if prop_name.islower() else prop_name
                val = getattr(style, cap_name, None) if not isinstance(style, dict) else style.get(cap_name)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass
    return float(default_val)


def _format_single_line_scale_trajectory(pts, t1, t2, accel=1.0, tags="", context=None, is_shape=None):
    clean_tags = str(tags or "").strip()
    if clean_tags.startswith("{") and clean_tags.endswith("}"):
        clean_tags = clean_tags[1:-1].strip()
    clean_tags = clean_tags.replace(r"\\", "\\")
    if clean_tags and not clean_tags.startswith("\\"):
        clean_tags = "\\" + clean_tags
    add_str = clean_tags if clean_tags.startswith(r"\r") else (f"\\r{clean_tags}" if clean_tags else "\\r")

    if not pts:
        return f"\\an7\\q2\\pos(0,0)\\fscx0.00\\fscy0.00\\p1}}m 0 0 m 100 100 {{\\p0{add_str}"

    n = len(pts)

    # Extract metrics from context
    fx_width = 0.0
    fx_height = 0.0
    l_descent = 0.0
    if context:
        active_unit = getattr(context, "active_unit", None) or (context.get("active_unit") if isinstance(context, dict) else None)
        l = getattr(context, "l", None) or getattr(context, "line", None) or (context.get("l") if isinstance(context, dict) else (context.get("line") if isinstance(context, dict) else None))
        fx = getattr(context, "fx", None) or (context.get("fx") if isinstance(context, dict) else None)
        if active_unit:
            fx_width = float(getattr(active_unit, "width", 0.0) or 0.0)
            fx_height = float(getattr(active_unit, "height", 0.0) or 0.0)
            l_descent = float(getattr(active_unit, "descent", 0.0) or 0.0)
        elif fx:
            try:
                fx_width = float(fx.get("width", 0.0) if isinstance(fx, dict) else getattr(fx, "width", 0.0))
                fx_height = float(fx.get("height", 0.0) if isinstance(fx, dict) else getattr(fx, "height", 0.0))
            except Exception:
                pass
        if l and l_descent == 0.0:
            l_descent = float(getattr(l, "descent", 0.0) or 0.0)

    # Check if target is a shape (drawing)
    if is_shape is None:
        is_shape = False
        if context and isinstance(context, dict):
            if context.get("_return_node_is_shape"):
                is_shape = True
            elif context.get("_return_port_connected"):
                ret_raw = str(context.get("return_raw", "") or "")
                if ret_raw.startswith("m ") or re.search(r'\bm\s+-?\d+', ret_raw):
                    is_shape = True

    if is_shape and (fx_height > 0.0 or fx_width > 0.0):
        # Shape trajectory: vector drawings are anchored at their center (0, 0)
        ret_raw = ""
        if context and isinstance(context, dict):
            ret_raw = str(context.get("return_raw", "") or "")
        shape_comp_y = _get_shape_add_y(ret_raw)

        min_x = min(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        x0 = 0.0 if min_x >= 0 else min_x
        y0 = 0.0 if min_y >= 0 else min_y
        posxy = f"\\an7\\q2\\pos({x0:.2f},{y0:.2f})"
        fsc_pts = [[p[0] - x0, p[1] - y0 + shape_comp_y, p[2] if len(p) > 2 else 0.0] for p in pts]
    else:
        # Effector 2 exact logic for text typesetting along trajectory
        add_x = -fx_width / 2.0 if fx_width > 0 else 0.0
        add_y = (1.5 * fx_height - l_descent) if fx_height > 0 else 0.0
        eff_pts = [[p[0] + add_x, p[1] + add_y, p[2] if len(p) > 2 else 0.0] for p in pts]

        min_x = min(p[0] for p in eff_pts)
        min_y = min(p[1] for p in eff_pts)
        x0 = 0.0 if min_x >= 0 else min_x
        if 0 < min_y <= fx_height and fx_height > 0:
            y0 = -min_y
        elif min_y >= 0:
            y0 = 0.0
        else:
            y0 = min_y

        pos_y_val = (y0 - fx_height) if fx_height > 0 else y0
        posxy = f"\\an7\\q2\\pos({x0:.2f},{pos_y_val:.2f})"
        fsc_pts = [[p[0] - x0, p[1] - y0, p[2] if len(p) > 2 else 0.0] for p in eff_pts]

    initial_fsc = f"\\fscx{fsc_pts[0][0]:.2f}\\fscy{fsc_pts[0][1]:.2f}"

    if n == 1:
        return f"{posxy}{initial_fsc}\\p1}}m 0 0 m 100 100 {{\\p0{add_str}"

    tot_time = max(1.0, t2 - t1)
    has_dist = len(fsc_pts[0]) >= 3 and fsc_pts[-1][2] > 0
    total_dist = max(1e-6, fsc_pts[-1][2]) if has_dist else float(n - 1)

    tag_list = [posxy, initial_fsc]
    for i in range(1, n):
        if has_dist:
            norm_d1 = (fsc_pts[i-1][2] / total_dist) ** accel
            norm_d2 = (fsc_pts[i][2] / total_dist) ** accel
        else:
            norm_d1 = ((i - 1) / (n - 1)) ** accel
            norm_d2 = (i / (n - 1)) ** accel

        st = int(round(t1 + tot_time * norm_d1))
        et = int(round(t1 + tot_time * norm_d2))
        px = fsc_pts[i][0]
        py = fsc_pts[i][1]

        acc_str = f"{accel:.2f}," if abs(accel - 1.0) > 0.05 else ""
        tag_list.append(f"\\t({st},{et},{acc_str}\\fscx{px:.2f}\\fscy{py:.2f})")

    tag_list.append(f"\\p1}}m 0 0 m 100 100 {{\\p0{add_str}")
    return "".join(tag_list)


def move_tag_node(context=None, mode="Trajectory", tags=None, **kwargs):
    r"""
    Genera tags ASS de movimiento o trayectoria (\pos, \fscx, \fscy, \t).
    Soporta modos Trajectory, Waypoints y Jitter, e inyecta tags ASS adicionales
    especificados por el usuario (parámetro 'tags').
    """
    raw_tags = tags if tags is not None else kwargs.get("tags") or kwargs.get("add_tags") or ""
    if not raw_tags and context and isinstance(context, dict):
        raw_tags = context.get("tags") or context.get("add_tags") or ""

    mode_raw = kwargs.get("mode") or kwargs.get("modo") or mode or "Trajectory"
    mode_str = str(mode_raw).strip().upper()
    step_px = float(_clean_num(kwargs.get("step_px") or kwargs.get("step"), default=7.5, context=context))
    anchor = str(kwargs.get("anchor") or "center")
    accel = float(_clean_num(kwargs.get("accel"), default=1.0, context=context))
    if accel <= 0:
        accel = 1.0

    is_shape = kwargs.get("is_shape")
    def_dur = _get_default_dur(context)

    if mode_str in ("TRAJECTORY", "SMOVE"):
        shape_str = str(kwargs.get("shape") or kwargs.get("drawing") or kwargs.get("points") or "").strip()
        from_text_fallback = False
        if not shape_str:
            try:
                from font_vector_engine import FontVectorEngine
                shape_str = FontVectorEngine.from_context(context=context) or ""
                if shape_str:
                    from_text_fallback = True
            except Exception:
                shape_str = ""
        if not shape_str:
            shape_str = "m 0 0 l 100 0"

        t1 = float(_clean_num(kwargs.get("t1") or kwargs.get("time_start"), default=0, context=context))
        t2_val = kwargs.get("t2") or kwargs.get("time_end")
        t2 = float(_clean_num(t2_val, default=def_dur, context=context)) if t2_val is not None else def_dur

        pts = _parse_points_input(shape_str, step_px=step_px) if not (shape_str.lower().startswith("m ") or re.search(r'\b[mlbc]\s+[-?\d]', shape_str, re.IGNORECASE)) else _resample_shape_arc_length(shape_str, step_px=step_px)
        if not pts:
            pts = _resample_shape_arc_length(shape_str, step_px=step_px)
        pts = _relocate_points(pts, anchor=anchor, context=context, is_text_vector=from_text_fallback)

        return _format_single_line_scale_trajectory(pts, t1, t2, accel=accel, tags=raw_tags, context=context, is_shape=is_shape)

    elif mode_str in ("WAYPOINTS", "PMOVE"):
        points_raw = kwargs.get("points") or kwargs.get("shape") or kwargs.get("drawing") or ""
        t1 = float(_clean_num(kwargs.get("t1") or kwargs.get("time_start"), default=0, context=context))
        t2_val = kwargs.get("t2") or kwargs.get("time_end")
        t2 = float(_clean_num(t2_val, default=def_dur, context=context)) if t2_val is not None else def_dur

        from_text_fallback = False
        pts = _parse_points_input(points_raw, step_px=step_px)
        if not pts:
            try:
                from font_vector_engine import FontVectorEngine
                fallback_shp = FontVectorEngine.from_context(context=context) or ""
                if fallback_shp:
                    pts = _resample_shape_arc_length(fallback_shp, step_px=step_px)
                    from_text_fallback = True
            except Exception:
                pass
        if not pts:
            pts = [(0.0, 0.0, 0.0), (100.0, 50.0, 111.8), (200.0, 0.0, 223.6)]

        pts = _relocate_points(pts, anchor=anchor, context=context, is_text_vector=from_text_fallback)

        return _format_single_line_scale_trajectory(pts, t1, t2, accel=accel, tags=raw_tags, context=context, is_shape=is_shape)

    elif mode_str in ("JITTER", "RANDOM", "RMOVE"):
        dx = float(_clean_num(kwargs.get("dx") or kwargs.get("delta_x"), default=10.0, context=context))
        dy = float(_clean_num(kwargs.get("dy") or kwargs.get("delta_y"), default=10.0, context=context))
        dur = float(_clean_num(kwargs.get("dur") or kwargs.get("step_dur"), default=50.0, context=context))
        seed = int(_clean_num(kwargs.get("seed"), default=0, context=context))
        t1 = float(_clean_num(kwargs.get("t1") or kwargs.get("time_start"), default=0, context=context))
        t2_val = kwargs.get("t2") or kwargs.get("time_end")
        t2 = float(_clean_num(t2_val, default=def_dur, context=context)) if t2_val is not None else def_dur

        tot_time = max(1.0, t2 - t1)
        dur = max(10.0, dur)
        n_steps = max(1, int(math.ceil(tot_time / dur)))

        rng = random.Random(seed) if seed != 0 else random.Random()
        raw_pts = [(0.0, 0.0)]
        for _ in range(n_steps - 1):
            rx = rng.uniform(-dx, dx)
            ry = rng.uniform(-dy, dy)
            raw_pts.append((rx, ry))
        raw_pts.append((0.0, 0.0))

        pts_input = _parse_points_input(raw_pts, step_px=999999.0)
        pts = _relocate_points(pts_input, anchor=anchor, context=context)

        return _format_single_line_scale_trajectory(pts, t1, t2, accel=accel, tags=raw_tags, context=context, is_shape=is_shape)

    return ""


# ==============================================================================
# Tag Manipulator (ASS Tag Algebra & Introspection)
# ==============================================================================

def _get_context_style_ref(context):
    """Safely retrieves the active style reference from context."""
    if not isinstance(context, dict):
        return None
    unit = context.get('active_unit')
    line = context.get('active_line') or context.get('line')
    styleref = None
    if unit and hasattr(unit, 'styleref') and getattr(unit, 'styleref', None):
        styleref = getattr(unit, 'styleref')
    elif line and hasattr(line, 'styleref') and getattr(line, 'styleref', None):
        styleref = getattr(line, 'styleref')
    elif 'styleref' in context:
        styleref = context.get('styleref')
    elif 'style' in context:
        styleref = context.get('style')
    return styleref


def _format_clean_scalar(val):
    try:
        f = float(val)
        if f.is_integer():
            return str(int(f))
        return f"{round(f, 2):.2f}".rstrip('0').rstrip('.')
    except:
        return str(val)


def _clean_ass_hex_color(val):
    c = str(val).strip().upper()
    clean = c.replace("&H", "").replace("&", "").strip()
    if len(clean) == 8:
        clean = clean[2:8]
    elif len(clean) == 6:
        pass
    else:
        r, g, b = parse_color_to_rgb(c)
        return f"&H{b:02X}{g:02X}{r:02X}&"
    return f"&H{clean}&"


def _invert_single_tag(tag_name, tag_val, styleref=None):
    """Inverts an individual ASS tag according to its algebraic rules."""
    tn = tag_name.lower()
    tv = str(tag_val).strip()

    # Colors (\c, \1c, \2c, \3c, \4c) -> Negative RGB (255-R, 255-G, 255-B)
    if tn in (r"\c", r"\1c", r"\2c", r"\3c", r"\4c"):
        r, g, b = parse_color_to_rgb(tv)
        inv_r, inv_g, inv_b = 255 - r, 255 - g, 255 - b
        return f"{tag_name}{rgb_to_ass_color(inv_r, inv_g, inv_b)}"

    # Alphas (\alpha, \1a, \2a, \3a, \4a) -> Hex complement (255 - alpha)
    elif tn in (r"\alpha", r"\1a", r"\2a", r"\3a", r"\4a"):
        clean_hex = tv.replace("&H", "").replace("&h", "").replace("&", "").strip()
        try:
            alpha_int = int(clean_hex, 16) if clean_hex else 0
        except:
            try:
                alpha_int = int(float(tv))
            except:
                alpha_int = 0
        inv_alpha = max(0, min(255, 255 - alpha_int))
        return f"{tag_name}&H{inv_alpha:02X}&"

    # Rotations, shear, spacing, and directional shadow -> Algebraic sign inversion
    elif tn in (r"\frz", r"\frx", r"\fry", r"\fr", r"\fax", r"\fay", r"\fsp", r"\xshad", r"\yshad"):
        try:
            num = float(tv)
            inv_num = -num
            return f"{tag_name}{_format_clean_scalar(inv_num)}"
        except:
            return f"{tag_name}{tv}"

    # Borders, blur, and scalar shadow -> Reset to 0
    elif tn in (r"\bord", r"\xbord", r"\ybord", r"\blur", r"\be", r"\shad"):
        return f"{tag_name}0"

    # Scales (\fscx, \fscy) -> Style scale or 100
    elif tn in (r"\fscx", r"\fscy"):
        def_sc = 100.0
        if styleref:
            if tn == r"\fscx":
                def_sc = float(getattr(styleref, 'scale_x', getattr(styleref, 'ScaleX', 100.0)))
            else:
                def_sc = float(getattr(styleref, 'scale_y', getattr(styleref, 'ScaleY', 100.0)))
        return f"{tag_name}{_format_clean_scalar(def_sc)}"

    # Clip masks (\clip <-> \iclip)
    elif tn == r"\clip":
        return f"\\iclip{tv}"
    elif tn == r"\iclip":
        return f"\\clip{tv}"

    return f"{tag_name}{tv}"


def _invert_ass_tags(tag_str, styleref=None):
    """Recursively inverts an ASS tag string, including nested \\t(...) blocks."""
    if not tag_str:
        return ""
    str_val = str(tag_str)

    # 1. Process \t(...) blocks
    def _invert_t_block(match):
        inner = match.group(0)
        t_body = inner[3:-1]  # Strip \t( and )
        parts = t_body.split("\\", 1)
        if len(parts) == 2:
            time_part = parts[0]
            tags_part = "\\" + parts[1]
            inv_inner_tags = _invert_ass_tags(tags_part, styleref=styleref)
            return f"\\t({time_part}{inv_inner_tags})"
        return inner

    t_pattern = re.compile(r'\\t\([^)]*\)')
    t_blocks = []
    def _save_t(m):
        t_blocks.append(_invert_t_block(m))
        return f"__T_BLOCK_{len(t_blocks)-1}__"

    str_no_t = t_pattern.sub(_save_t, str_val)

    # 2. Process remaining atomic tags
    # Regex to capture tags with parenthesized arguments or scalar values
    tag_regex = re.compile(r'(\\[0-9]*[a-zA-Z]+)(\([^)]*\)|-?[0-9&]+[0-9a-zA-Z.&]*)?')

    def _replace_atomic_tag(m):
        t_name = m.group(1)
        t_val = m.group(2) or ""
        return _invert_single_tag(t_name, t_val, styleref=styleref)

    result = tag_regex.sub(_replace_atomic_tag, str_no_t)

    # 3. Restore \t blocks
    for idx, tb in enumerate(t_blocks):
        result = result.replace(f"__T_BLOCK_{idx}__", tb)

    return result


def _default_style_tags(tags_filter="", styleref=None):
    """Genera tags de reseteo al estilo base para los tags especificados o el conjunto completo."""
    c1 = getattr(styleref, 'color1', '&H00FFFFFF&') if styleref else '&H00FFFFFF&'
    c2 = getattr(styleref, 'color2', '&H000000FF&') if styleref else '&H000000FF&'
    c3 = getattr(styleref, 'color3', '&H00000000&') if styleref else '&H00000000&'
    c4 = getattr(styleref, 'color4', '&H00000000&') if styleref else '&H00000000&'

    c1_ass = _clean_ass_hex_color(c1)
    c2_ass = _clean_ass_hex_color(c2)
    c3_ass = _clean_ass_hex_color(c3)
    c4_ass = _clean_ass_hex_color(c4)

    a1 = getattr(styleref, 'alpha1', '&H00&') if styleref else '&H00&'
    a2 = getattr(styleref, 'alpha2', '&H00&') if styleref else '&H00&'
    a3 = getattr(styleref, 'alpha3', '&H00&') if styleref else '&H00&'
    a4 = getattr(styleref, 'alpha4', '&H00&') if styleref else '&H00&'

    a1_ass = f"&H{a1.replace('&H','').replace('&',''):>02}&" if str(a1).startswith('&H') else '&H00&'
    a2_ass = f"&H{a2.replace('&H','').replace('&',''):>02}&" if str(a2).startswith('&H') else '&H00&'
    a3_ass = f"&H{a3.replace('&H','').replace('&',''):>02}&" if str(a3).startswith('&H') else '&H00&'
    a4_ass = f"&H{a4.replace('&H','').replace('&',''):>02}&" if str(a4).startswith('&H') else '&H00&'

    fs = _format_clean_scalar(getattr(styleref, 'fontsize', 40.0) if styleref else 40.0)
    scx = _format_clean_scalar(getattr(styleref, 'scale_x', 100.0) if styleref else 100.0)
    scy = _format_clean_scalar(getattr(styleref, 'scale_y', 100.0) if styleref else 100.0)
    fsp = _format_clean_scalar(getattr(styleref, 'spacing', 0.0) if styleref else 0.0)
    bord = _format_clean_scalar(getattr(styleref, 'outline', 2.0) if styleref else 2.0)
    shad = _format_clean_scalar(getattr(styleref, 'shadow', 0.0) if styleref else 0.0)
    angle = _format_clean_scalar(getattr(styleref, 'angle', 0.0) if styleref else 0.0)

    defaults_map = {
        r"\1c": f"\\1c{c1_ass}",
        r"\2c": f"\\2c{c2_ass}",
        r"\3c": f"\\3c{c3_ass}",
        r"\4c": f"\\4c{c4_ass}",
        r"\c": f"\\1c{c1_ass}",
        r"\1a": f"\\1a{a1_ass}",
        r"\2a": f"\\2a{a2_ass}",
        r"\3a": f"\\3a{a3_ass}",
        r"\4a": f"\\4a{a4_ass}",
        r"\alpha": r"\alpha&H00&",
        r"\fs": f"\\fs{fs}",
        r"\fscx": f"\\fscx{scx}",
        r"\fscy": f"\\fscy{scy}",
        r"\fsp": f"\\fsp{fsp}",
        r"\bord": f"\\bord{bord}",
        r"\xbord": f"\\xbord{bord}",
        r"\ybord": f"\\ybord{bord}",
        r"\shad": f"\\shad{shad}",
        r"\xshad": f"\\xshad{shad}",
        r"\yshad": f"\\yshad{shad}",
        r"\frz": f"\\frz{angle}",
        r"\fr": f"\\fr{angle}",
        r"\frx": r"\frx0",
        r"\fry": r"\fry0",
        r"\fax": r"\fax0",
        r"\fay": r"\fay0",
        r"\blur": r"\blur0",
        r"\be": r"\be0",
    }

    tf = str(tags_filter or "").strip()
    if not tf or tf.lower() == "all" or tf.lower() == "todo":
        # Returns the full default set
        return (
            f"\\1c{c1_ass}\\2c{c2_ass}\\3c{c3_ass}\\4c{c4_ass}"
            f"\\1a{a1_ass}\\2a{a2_ass}\\3a{a3_ass}\\4a{a4_ass}\\alpha&H00&"
            f"\\fscx{scx}\\fscy{scy}\\fs{fs}\\fsp{fsp}"
            f"\\bord{bord}\\shad{shad}\\frz{angle}\\frx0\\fry0\\fax0\\fay0\\blur0\\be0"
        )

    # Identifies which tags are present in tags_filter
    found_resets = []
    seen = set()
    tag_regex = re.compile(r'(\\[0-9]*[a-zA-Z]+)')
    for match in tag_regex.finditer(tf):
        tn = match.group(1).lower()
        if tn in defaults_map and tn not in seen:
            seen.add(tn)
            found_resets.append(defaults_map[tn])

    if not found_resets:
        return defaults_map.get(r"\1c", "")
    return "".join(found_resets)


def _get_kwarg(kwargs, *keys, default=""):
    """Extracts first non-empty value from kwargs matching given keys."""
    for k in keys:
        if k in kwargs and kwargs[k] is not None and str(kwargs[k]).strip() != "":
            return str(kwargs[k]).strip()
    return default


def _extract_tag_value(tag_str, target_tag):
    """Extracts numeric and text values of the specified ASS tag within string."""
    if not tag_str or not target_tag:
        return "", 0.0, ""

    tt = str(target_tag).strip().lstrip('\\').strip()
    if not tt:
        return "", 0.0, ""

    # Handle standard ASS aliases (\c <-> \1c, \fr <-> \frz)
    if tt in ("c", "1c"):
        pattern_str = r'\\(?:1c|c)(?![a-zA-Z])(\([^)]*\)|-?[0-9&]+[0-9a-zA-Z.&]*)?'
    elif tt in ("fr", "frz"):
        pattern_str = r'\\(?:frz|fr)(?![xya-zA-Z])(\([^)]*\)|-?[0-9&]+[0-9a-zA-Z.&]*)?'
    else:
        escaped_target = re.escape("\\" + tt)
        pattern_str = rf'{escaped_target}(\([^)]*\)|-?[0-9&]+[0-9a-zA-Z.&]*)?'

    pattern = re.compile(pattern_str, re.IGNORECASE)
    matches = list(pattern.finditer(str(tag_str)))

    if not matches:
        return "", 0.0, ""

    last_match = matches[-1]
    raw_val = last_match.group(1) or ""
    full_tag = last_match.group(0)

    # Extract clean value
    clean_val = raw_val.strip()
    if clean_val.startswith("(") and clean_val.endswith(")"):
        clean_val = clean_val[1:-1].strip()

    num_val = 0.0
    # Attempt numeric conversion
    if clean_val.startswith("&H") or clean_val.startswith("&h"):
        # Color or alpha
        hex_clean = clean_val.replace("&H", "").replace("&h", "").replace("&", "").strip()
        if len(hex_clean) <= 2:
            try:
                num_val = float(int(hex_clean, 16))
            except:
                num_val = 0.0
        else:
            num_val = 0.0
    else:
        try:
            # If comma-separated (e.g., coordinates pos x, y), take the first number
            if "," in clean_val:
                first_part = clean_val.split(",")[0].strip()
                num_val = float(first_part)
            else:
                num_val = float(clean_val)
        except:
            num_val = 0.0

    return clean_val, num_val, full_tag


def eval_tag_manipulator_node(context=None, *args, **kwargs):
    """Evaluates master Tag Manipulator node in Invert, Reset, or Extractor modes."""
    if len(args) > 0 and isinstance(args[0], dict) and context is None:
        context = args[0]

    raw_mode = _get_kwarg(kwargs, "mode", "modo", default="Invert").lower()
    raw_tags = _get_kwarg(kwargs, "Tags In", "tags_in", "tags", "in_0", "0", "in", default="")
    target_tag = _get_kwarg(kwargs, "Target Tag", "target_tag", "target", "tag", "in_1", "1", default="frz")
    output_slot_index = int(kwargs.get("output_slot_index", 0))

    styleref = _get_context_style_ref(context)

    if raw_mode in ("invert", "inverso", "inv", "negative", "negativo"):
        inverted = _invert_ass_tags(raw_tags, styleref=styleref)
        return inverted

    elif raw_mode in ("reset", "default", "restablecer", "estilo", "style"):
        reset_tags = _default_style_tags(tags_filter=raw_tags, styleref=styleref)
        return reset_tags

    elif raw_mode in ("extractor", "extract", "extraer", "inspect", "inspector"):
        str_val, num_val, full_tag = _extract_tag_value(raw_tags, target_tag)
        if output_slot_index == 1:
            return num_val
        elif output_slot_index == 2:
            return full_tag
        return str_val

    # Modo Invert por defecto
    return _invert_ass_tags(raw_tags, styleref=styleref)


def node_animation(
    context=None,
    frames="",
    step_ms=41.7,
    start_time="",
    end_time="",
    mode="FBF",
    alpha_tag=r"\alpha",
    var_name="an",
    output_slot_index=0,
    **kwargs
):
    """Animation node supporting Frame-by-Frame (FBF) and Synchronized Alpha Transformation modes.
    Accepts lists, Lua tables, JSON arrays, or strings of shapes and texts (converted via FontVectorEngine).
    Injects internal loop iterators ({var_name}_i, {var_name}_n) and returns appropriate outputs per mode.
    """
    from node_engine import _eval_num_expr
    from font_vector_engine import FontVectorEngine
    from nodes.shape_nodes import resolve_shape_value

    ctx = context if isinstance(context, dict) else {}
    var_prefix = str(var_name or "an").strip() or "an"

    # 1. Parse and extract frames
    raw_input = frames if frames is not None and str(frames).strip() != "" else kwargs.get("shape", kwargs.get("shapes", kwargs.get("text", "")))
    
    # If raw_input is a variable name in context (e.g. "Shapes1", "$my_var", Lua tables)
    if isinstance(raw_input, str):
        s_candidate = raw_input.strip()
        if s_candidate in ctx:
            raw_input = ctx[s_candidate]
        elif s_candidate.startswith("$") and s_candidate[1:] in ctx:
            raw_input = ctx[s_candidate[1:]]

    raw_items = []
    if isinstance(raw_input, (list, tuple)):
        raw_items = list(raw_input)
    elif hasattr(raw_input, "values") and callable(getattr(raw_input, "values")):
        try:
            raw_items = list(raw_input.values())
        except Exception:
            raw_items = [v for k, v in getattr(raw_input, "items")()]
    elif hasattr(raw_input, "__iter__") and not isinstance(raw_input, (str, bytes)):
        try:
            raw_items = [raw_input[k] for k in raw_input]
        except Exception:
            raw_items = list(raw_input)
    elif isinstance(raw_input, str):
        s = raw_input.strip()
        if not s:
            unit = ctx.get('active_unit') or ctx.get('syl') or ctx.get('char') or ctx.get('word')
            txt = getattr(unit, 'text_stripped', getattr(unit, 'text', '')) if unit else ""
            if not txt:
                line = ctx.get('active_line') or ctx.get('line')
                txt = getattr(line, 'text_stripped', getattr(line, 'text', '')) if line else ""
            s = txt if txt else "circle"

        if (s.startswith("[") and s.endswith("]")) or (s.startswith("{") and s.endswith("}")):
            try:
                import json
                json_str = s
                if json_str.startswith("{") and json_str.endswith("}"):
                    json_str = "[" + json_str[1:-1] + "]"
                parsed = json.loads(json_str)
                if isinstance(parsed, list):
                    raw_items = parsed
                else:
                    raw_items = [parsed]
            except Exception:
                inner = s[1:-1].strip()
                raw_items = [x.strip().strip('"').strip("'") for x in re.split(r'[,;\n]+', inner) if x.strip()]
        elif "\n" in s:
            raw_items = [x.strip() for x in s.split("\n") if x.strip()]
        elif ";" in s:
            raw_items = [x.strip() for x in s.split(";") if x.strip()]
        elif "," in s and not (s.startswith("m ") or s.startswith("m-") or s.startswith("m0")):
            raw_items = [x.strip() for x in s.split(",") if x.strip()]
        else:
            raw_items = [s]
    else:
        raw_items = [str(raw_input)]

    processed_shapes = []
    for item in raw_items:
        if item is None:
            continue
        item_val = item
        if isinstance(item, str):
            item_cand = item.strip()
            if item_cand in ctx:
                item_val = ctx[item_cand]
            elif item_cand.startswith("$") and item_cand[1:] in ctx:
                item_val = ctx[item_cand[1:]]
        
        item_str = str(item_val).strip()
        if not item_str:
            continue
        shp = resolve_shape_value(item_str, ctx)
        if shp and (shp.startswith("m ") or shp.startswith("m-") or shp.startswith("m0")):
            processed_shapes.append(shp)
        else:
            vec = FontVectorEngine.from_context(text=item_str, context=ctx)
            if vec and vec.strip():
                processed_shapes.append(vec.strip())
            else:
                processed_shapes.append(shp if shp else item_str)

    if not processed_shapes:
        processed_shapes = [resolve_shape_value("circle", ctx) or "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 "]

    num_frames = len(processed_shapes)

    # Resolve timing
    try:
        f_dur = max(1.0, float(_eval_num_expr(step_ms, ctx, 41.7)))
    except Exception:
        f_dur = 41.7

    mode_str = str(kwargs.get("mode", kwargs.get("modo", mode or "FBF"))).strip().lower()
    is_alpha_mode = "alpha" in mode_str or "alfa" in mode_str or "tag" in mode_str

    unit = ctx.get('active_unit') or ctx.get('syl') or ctx.get('char') or ctx.get('word')
    line = ctx.get('active_line') or ctx.get('line')
    
    # Use effect-calculated timing from Output (Salida) / fx context
    eff_st = float(ctx.get("effect_st", ctx.get("fx_start_time", ctx.get("fx_st", ctx.get("start_time", getattr(unit, "start_time", getattr(line, "start_time", 0.0)))))))
    eff_et = float(ctx.get("effect_et", ctx.get("fx_end_time", ctx.get("fx_et", ctx.get("end_time", getattr(unit, "end_time", getattr(line, "end_time", 0.0)))))))
    eff_dur = float(ctx.get("effect_dur", ctx.get("fx_dur", ctx.get("dur", ctx.get("duration", eff_et - eff_st)))))
    if eff_dur <= 0:
        eff_dur = max(eff_et - eff_st, float(num_frames * f_dur))

    st_raw = start_time if start_time is not None and str(start_time).strip() != "" else kwargs.get("st", "")
    et_raw = end_time if end_time is not None and str(end_time).strip() != "" else kwargs.get("et", "")

    st_raw_clean = str(st_raw).strip().lower()
    et_raw_clean = str(et_raw).strip().lower()

    # Start time: local 0 means eff_st (relative to the effect calculated by Salida)
    if st_raw_clean in ["", "0", "0.0", "start_time", "st", "effect_st", "fx_st", "fx_start_time", "fx.start_time", "fx.st"]:
        st_val = eff_st
    else:
        try:
            val = float(_eval_num_expr(st_raw, ctx, 0.0))
            if 0.0 < val <= eff_dur and (eff_st > 0 and val < eff_st):
                st_val = eff_st + val
            elif val < 0.0:
                st_val = eff_st + val
            else:
                st_val = val
        except Exception:
            st_val = eff_st

    # End time: local fx.dur means eff_st + eff_dur (relative to the effect calculated by Salida)
    if et_raw_clean in ["", "fx.dur", "dur", "duration", "effect_dur", "fx_dur", "end_time", "et", "effect_et", "fx_et", "fx_end_time", "fx.end_time", "fx.et"]:
        et_val = eff_st + eff_dur
    else:
        try:
            val = float(_eval_num_expr(et_raw, ctx, eff_dur))
            if 0.0 < val <= eff_dur and (eff_st > 0 and val < eff_st):
                et_val = eff_st + val
            elif val <= st_val and 0.0 < val:
                et_val = eff_st + val
            else:
                et_val = val
        except Exception:
            et_val = eff_st + eff_dur

    dur = max(f_dur, et_val - st_val)
    total_frames = max(1, int(math.ceil(dur / f_dur)))

    # 2. Register loop counts in context
    if isinstance(context, dict):
        context[f"{var_prefix}_n"] = num_frames
        context[f"{var_prefix}_max"] = num_frames
        context["an_n"] = num_frames
        context["an_max"] = num_frames
        context["anim_n"] = num_frames
        context["anim_max"] = num_frames
        context["anim_base_st"] = st_val
        context["anim_base_et"] = et_val
        context["an_total_cycles"] = total_frames
        if not is_alpha_mode:
            context["an_loop_count"] = total_frames
            context["maxloop"] = total_frames
            context["anim_step_ms"] = f_dur
        else:
            context["an_loop_count"] = num_frames
            context["maxloop"] = num_frames
            context.pop("anim_step_ms", None)

    # 3. Resolve current iterator / index (cycles 1..num_frames continuously like a GIF)
    iter_val = ctx.get(f"{var_prefix}_i") or ctx.get("an_i") or ctx.get("anim_i") or ctx.get("j") or ctx.get("fx_i") or ctx.get("i") or 1
    try:
        cur_idx = int(float(iter_val))
    except Exception:
        cur_idx = 1

    active_frame_idx = (cur_idx - 1) % num_frames

    current_shape = processed_shapes[active_frame_idx]
    current_frame_num = active_frame_idx + 1

    if isinstance(context, dict):
        context[f"{var_prefix}_i"] = current_frame_num
        context["an_i"] = current_frame_num
        context["anim_i"] = current_frame_num
        context["an_j"] = cur_idx

    # 5. Handle output slots per mode
    output_slot = int(output_slot_index or 0)

    if not is_alpha_mode:
        # FBF Mode
        # Slot 0: Shape
        # Slot 1: Frame number (1-based)
        # Slot 2: Frames List
        if output_slot == 1:
            return current_frame_num
        elif output_slot == 2:
            return processed_shapes
        shp_str = str(current_shape)
        if not shp_str.startswith(r"{\an") and not shp_str.startswith(r"\an"):
            return f"{{\\an7}}{current_shape}"
        return current_shape

    else:
        # Alpha Transformation Mode
        raw_tag = str(alpha_tag or r"\alpha").strip()
        if not raw_tag.startswith("\\"):
            raw_tag = "\\" + raw_tag
        if not (re.match(r'^\\[1-4]+a$', raw_tag) or raw_tag.lower() == r"\alpha"):
            raw_tag = r"\alpha"

        tag_prefix = raw_tag
        tag_fx_parts = [r"\an7", f"{tag_prefix}&HFF&"]

        num_loops = max(1, int(math.ceil(dur / (num_frames * f_dur))))
        for k in range(num_loops + 1):
            t1_f = f_dur * (num_frames * k + active_frame_idx)
            t2_f = t1_f + 1.0
            t3_f = f_dur * (num_frames * k + active_frame_idx + 1)
            t4_f = t3_f + 1.0

            if t1_f >= dur:
                break

            t1 = int(t1_f) if t1_f.is_integer() else round(t1_f, 2)
            t2 = int(t2_f) if t2_f.is_integer() else round(t2_f, 2)
            t3 = int(t3_f) if t3_f.is_integer() else round(t3_f, 2)
            t4 = int(t4_f) if t4_f.is_integer() else round(t4_f, 2)

            last_a = f"{tag_prefix}&H00&" if t2_f >= dur else f"{tag_prefix}&HFF&"
            t_end_hide_f = min(dur, t4_f)
            t_end_hide = int(t_end_hide_f) if t_end_hide_f.is_integer() else round(t_end_hide_f, 2)

            tag_fx_parts.append(f"\\t({t1},{t2},{tag_prefix}&H00&)\\t({t3},{t_end_hide},{last_a})")

        tag_fx = "".join(tag_fx_parts)
        shape_with_tags = f"{{{tag_fx}\\p1}}{current_shape}"

        # Slot 0: Shape with Tags
        # Slot 1: Tags alone
        # Slot 2: Frame number
        # Slot 3: Frames List
        if output_slot == 1:
            return tag_fx
        elif output_slot == 2:
            return current_frame_num
        elif output_slot == 3:
            return processed_shapes
        return shape_with_tags


from decorators import pyxis_node, NODE_REGISTRY

@pyxis_node("Functions", "Move Tag", [])
def MoveTagNode(context=None, *args, **kwargs):
    return move_tag_node(context=context, *args, **kwargs)

NODE_REGISTRY["Functions/Move Tag"] = MoveTagNode
NODE_REGISTRY["Move Tag"] = MoveTagNode

@pyxis_node("Functions", "Tag Manipulator", ["Tags In"])
def TagManipulatorNode(context=None, *args, **kwargs):
    return eval_tag_manipulator_node(context=context, *args, **kwargs)

NODE_REGISTRY["Functions/Tag Manipulator"] = TagManipulatorNode
NODE_REGISTRY["Tag Manipulator"] = TagManipulatorNode

@pyxis_node("Functions", "Animation", ["Frames / Text", "Step ms", "Start Time", "End Time"])
def AnimationNode(context=None, *args, **kwargs):
    return node_animation(context=context, *args, **kwargs)

NODE_REGISTRY["Functions/Animation"] = AnimationNode
NODE_REGISTRY["Animation"] = AnimationNode








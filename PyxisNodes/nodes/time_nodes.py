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

"""Temporal manipulation, delays, and time conversion nodes."""

import math
import re
from decorators import pyxis_node, NODE_REGISTRY
from utils import parse_time, format_time

def _num(val, default=0.0):
    try: return float(val)
    except: return default


def _eval_val(val, context, default=0.0):
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if not val_str:
        return default
    try:
        from node_engine import _eval_num_expr
        return float(_eval_num_expr(val_str, context, default=default))
    except Exception:
        pass
    try:
        return float(val_str)
    except (ValueError, TypeError):
        return default


def _get_base_time(context, is_end_time=False, base=None):
    if base is not None and str(base).strip() != "":
        try: return float(_eval_val(base, context, 0.0))
        except: pass
    return 0.0


@pyxis_node("Time", "Lead In", ["Delay (ms)"])
def time_lead_in(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 40)))
        base = args[2] if len(args) > 2 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 40)))
        base = args[1] if len(args) > 1 else kwargs.get("base", None)

    delay_val = _eval_val(delay, context, 40.0)
    unit = context.get('active_unit') if isinstance(context, dict) else None
    i = float(getattr(unit, 'i', 1) if unit else 1)
    base_val = _get_base_time(context, is_end_time=False, base=base)
    return round(base_val + delay_val * (i - 1.0) - 200.0, 3)


@pyxis_node("Time", "Lead Out", ["Delay (ms)"])
def time_lead_out(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 40)))
        base = args[2] if len(args) > 2 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 40)))
        base = args[1] if len(args) > 1 else kwargs.get("base", None)

    delay_val = _eval_val(delay, context, 40.0)
    unit = context.get('active_unit') if isinstance(context, dict) else None
    i = float(getattr(unit, 'i', 1) if unit else 1)
    n = float(getattr(unit, 'n', 1) if unit else 1)
    base_val = _get_base_time(context, is_end_time=True, base=base)
    return round(base_val + delay_val * (i - n - 1.0) + 200.0, 3)


@pyxis_node("Time", "Middle 1", ["Delay (ms)"])
def time_middle_1(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 30)))
        base = args[2] if len(args) > 2 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 30)))
        base = args[1] if len(args) > 1 else kwargs.get("base", None)

    delay_val = _eval_val(delay, context, 30.0)
    unit = context.get('active_unit') if isinstance(context, dict) else None
    i = float(getattr(unit, 'i', 1) if unit else 1)
    n = float(getattr(unit, 'n', 1) if unit else 1)
    base_val = _get_base_time(context, is_end_time=False, base=base)
    if i <= (n + 1.0) / 2.0:
        offset = delay_val * (i - 1.0) - 200.0
    else:
        offset = delay_val * (n - i + 0.5) - 200.0
    return round(base_val + offset, 3)


@pyxis_node("Time", "Middle 2", ["Delay (ms)"])
def time_middle_2(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 30)))
        base = args[2] if len(args) > 2 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 30)))
        base = args[1] if len(args) > 1 else kwargs.get("base", None)

    delay_val = _eval_val(delay, context, 30.0)
    unit = context.get('active_unit') if isinstance(context, dict) else None
    i = float(getattr(unit, 'i', 1) if unit else 1)
    n = float(getattr(unit, 'n', 1) if unit else 1)
    base_val = _get_base_time(context, is_end_time=True, base=base)
    if i >= (n + 1.0) / 2.0:
        offset = delay_val * (i - n - 1.0) - 200.0
    else:
        offset = delay_val * (-i + 0.5) - 200.0
    return round(base_val + offset, 3)


@pyxis_node("Time", "Loop 1", ["Delay (ms)"])
def time_loop_1(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 30)))
        mode = args[2] if len(args) > 2 else kwargs.get("mode", kwargs.get("modo", "leadin"))
        base = args[3] if len(args) > 3 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 30)))
        mode = args[1] if len(args) > 1 else kwargs.get("mode", kwargs.get("modo", "leadin"))
        base = args[2] if len(args) > 2 else kwargs.get("base", None)

    delay_val = _eval_val(delay, context, 30.0)
    mode_str = str(mode).strip().lower()
    j = float(context.get('fx_i', context.get('j', 1))) if isinstance(context, dict) else 1.0
    maxj = float(context.get('maxj', context.get('fx_n', 1))) if isinstance(context, dict) else 1.0
    is_end = mode_str in ["leadout", "lo"]
    base_val = _get_base_time(context, is_end_time=is_end, base=base)

    if mode_str in ["leadin", "li"]:
        offset = delay_val * (j - 1.0) - 200.0
    elif mode_str in ["leadout", "lo"]:
        offset = delay_val * (j - maxj - 1.0) + 200.0
    elif mode_str in ["middle1", "middle", "mid1"]:
        if j <= (maxj + 1.0) / 2.0:
            offset = delay_val * (j - 1.0) - 200.0
        else:
            offset = delay_val * (maxj - j + 0.5) - 200.0
    elif mode_str in ["middle2", "mid2"]:
        if j >= (maxj + 1.0) / 2.0:
            offset = delay_val * (j - maxj - 1.0) - 200.0
        else:
            offset = delay_val * (-j + 0.5) - 200.0
    else:
        offset = delay_val

    return round(base_val + offset, 3)


@pyxis_node("Time", "Loop 2", ["Delay (ms)"])
def time_loop_2(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 30)))
        mode = args[2] if len(args) > 2 else kwargs.get("mode", kwargs.get("modo", "leadin"))
        base = args[3] if len(args) > 3 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay_ms", kwargs.get("delay", kwargs.get("retraso", 30)))
        mode = args[1] if len(args) > 1 else kwargs.get("mode", kwargs.get("modo", "leadin"))
        base = args[2] if len(args) > 2 else kwargs.get("base", None)

    delay_val = _eval_val(delay, context, 30.0)
    mode_str = str(mode).strip().lower()
    J = float(context.get('J', 1)) if isinstance(context, dict) else 1.0
    maxJ = float(context.get('maxJ', context.get('max_J', 1))) if isinstance(context, dict) else 1.0
    is_end = mode_str in ["leadout", "lo"]
    base_val = _get_base_time(context, is_end_time=is_end, base=base)

    if mode_str in ["leadin", "li"]:
        offset = delay_val * (J - 1.0) - 200.0
    elif mode_str in ["leadout", "lo"]:
        offset = delay_val * (J - maxJ - 1.0) + 200.0
    elif mode_str in ["middle1", "middle", "mid1"]:
        if J <= (maxJ + 1.0) / 2.0:
            offset = delay_val * (J - 1.0) - 200.0
        else:
            offset = delay_val * (maxJ - J + 0.5) - 200.0
    elif mode_str in ["middle2", "mid2"]:
        if J >= (maxJ + 1.0) / 2.0:
            offset = delay_val * (J - maxJ - 1.0) - 200.0
        else:
            offset = delay_val * (-J + 0.5) - 200.0
    else:
        offset = delay_val

    return round(base_val + offset, 3)


@pyxis_node("Time", "Ipol", ["Duration (ms)", "Points / Values", "Acceleration"])
def time_ipol(*args, **kwargs):
    if len(args) > 0 and (isinstance(args[0], dict) or args[0] is None):
        context = args[0] or {}
        dur = args[1] if len(args) > 1 else kwargs.get("dur_ms", kwargs.get("dur", kwargs.get("duration", None)))
        points = args[2] if len(args) > 2 else kwargs.get("points", "0, 100")
        accel = args[3] if len(args) > 3 else kwargs.get("accel", kwargs.get("acceleration", 1.0))
    else:
        context = kwargs.get("context", {})
        dur = args[0] if len(args) > 0 else kwargs.get("dur_ms", kwargs.get("dur", kwargs.get("duration", None)))
        points = args[1] if len(args) > 1 else kwargs.get("points", "0, 100")
        accel = args[2] if len(args) > 2 else kwargs.get("accel", kwargs.get("acceleration", 1.0))

    unit = context.get('active_unit') if isinstance(context, dict) else None
    default_dur = getattr(unit, 'duration', getattr(unit, 'dur', 1000)) if unit else 1000
    if dur is None or str(dur).strip() == "":
        dur = default_dur
    d_val = max(1.0, _eval_val(dur, context, default_dur))
    a_val = max(0.01, _eval_val(accel, context, 1.0))
    
    pts_str = str(points).strip()
    try:
        raw_vals = [float(_eval_val(x.strip(), context, 0.0)) for x in pts_str.split(',') if x.strip()]
    except Exception:
        raw_vals = [0.0, 100.0]
    if len(raw_vals) < 2:
        raw_vals = [0.0, 100.0]

    n_segments = len(raw_vals) - 1
    t0 = 0.0
    segments = []
    for k in range(1, n_segments + 1):
        u = k / float(n_segments)
        t_next = d_val * (u ** a_val)
        segments.append(f"[{round(t0, 1)}, {round(t_next, 1)}]")
        t0 = t_next
    return ", ".join(segments)


@pyxis_node("Time", "Offset", ["Base (ms)"])
def time_offset(*args, **kwargs):
    if len(args) > 0 and (isinstance(args[0], dict) or args[0] is None):
        context = args[0] or {}
        base = args[1] if len(args) > 1 else kwargs.get("time_in", kwargs.get("base", kwargs.get("time", 0)))
        offset = args[2] if len(args) > 2 else kwargs.get("offset_ms", kwargs.get("offset", 0))
    else:
        context = kwargs.get("context", {})
        base = args[0] if len(args) > 0 else kwargs.get("time_in", kwargs.get("base", kwargs.get("time", 0)))
        offset = args[1] if len(args) > 1 else kwargs.get("offset_ms", kwargs.get("offset", 0))

    if base is None or str(base).strip() == "":
        unit = context.get('active_unit') if isinstance(context, dict) else None
        line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
        if unit and getattr(unit, 'start_time', None) is not None:
            base = unit.start_time
        elif line and getattr(line, 'start_time', None) is not None:
            base = line.start_time
        else:
            base = 0.0

    base_val = _eval_val(base, context, 0.0)
    offset_val = _eval_val(offset, context, 0.0)
    return int(round(base_val + offset_val))

@pyxis_node("Time", "Duration", ["Start Time (ms)", "End Time (ms)"])
def time_duration(*args, **kwargs):
    if len(args) > 0 and (isinstance(args[0], dict) or args[0] is None):
        context = args[0] or {}
        st = args[1] if len(args) > 1 else kwargs.get("time_in", kwargs.get("start_time", kwargs.get("st", kwargs.get("start", None))))
        et = args[2] if len(args) > 2 else kwargs.get("time_out", kwargs.get("end_time", kwargs.get("et", kwargs.get("end", None))))
    else:
        context = kwargs.get("context", {})
        st = args[0] if len(args) > 0 else kwargs.get("time_in", kwargs.get("start_time", kwargs.get("st", kwargs.get("start", None))))
        et = args[1] if len(args) > 1 else kwargs.get("time_out", kwargs.get("end_time", kwargs.get("et", kwargs.get("end", None))))

    if (st is None or str(st).strip() == "") and (et is None or str(et).strip() == ""):
        unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
        if unit and getattr(unit, 'duration', None) is not None:
            return int(unit.duration)
        line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
        if line and getattr(line, 'duration', None) is not None:
            return int(line.duration)
    st_val = _eval_val(st, context, 0.0) if st is not None and str(st).strip() != "" else 0.0
    et_val = _eval_val(et, context, 0.0) if et is not None and str(et).strip() != "" else 0.0
    return max(0, int(round(et_val - st_val)))

NODE_REGISTRY["Time/Ipol"] = time_ipol
NODE_REGISTRY["Ipol"] = time_ipol
NODE_REGISTRY["Time/Offset"] = time_offset
NODE_REGISTRY["Offset"] = time_offset
NODE_REGISTRY["Time/Duration"] = time_duration
NODE_REGISTRY["Duration"] = time_duration
NODE_REGISTRY["Time/Duración"] = time_duration
NODE_REGISTRY["Duración"] = time_duration

@pyxis_node("Time", "Parse ASS Time", ["ASS Time"])
def time_parse_ass(*args, **kwargs):
    if len(args) > 0 and (isinstance(args[0], dict) or args[0] is None):
        context = args[0] or {}
        ass_str = args[1] if len(args) > 1 else kwargs.get("ass_time", kwargs.get("ass_str", ""))
    else:
        context = kwargs.get("context", {})
        ass_str = args[0] if len(args) > 0 else kwargs.get("ass_time", kwargs.get("ass_str", ""))

    raw = str(ass_str).strip()
    if not raw and isinstance(context, dict):
        unit = context.get('active_unit') or context.get('syl')
        line = context.get('active_line') or context.get('line')
        if unit and getattr(unit, 'start_str', None):
            raw = str(unit.start_str)
        elif line:
            raw = str(getattr(line, 'start_str', getattr(line, 'start', '0:00:00.00')))
    return int(parse_time(raw))

@pyxis_node("Time", "Format ASS Time", ["Time (ms)"])
def time_format_ass(*args, **kwargs):
    if len(args) > 0 and (isinstance(args[0], dict) or args[0] is None):
        context = args[0] or {}
        ms = args[1] if len(args) > 1 else kwargs.get("time", kwargs.get("ms", None))
    else:
        context = kwargs.get("context", {})
        ms = args[0] if len(args) > 0 else kwargs.get("time", kwargs.get("ms", None))

    if ms is None or str(ms).strip() == "":
        unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
        if unit and getattr(unit, 'start_time', None) is not None:
            ms = unit.start_time
        else:
            line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
            if line and getattr(line, 'start_time', None) is not None:
                ms = line.start_time
            else:
                ms = 0
    val_num = _eval_val(ms, context, 0.0)
    return format_time(int(round(val_num)))

@pyxis_node("Time", "Synced", ["Constant", "Fade (ms)", "Max Extra", "Delay Line", "Threshold"])
def time_synchronized_extra_node(context=None, *args, **kwargs):
    """Dynamic calculation of synchronized inter-line time extension (calculate.synchronized_extratime_3)."""
    if len(args) > 0 and (isinstance(args[0], dict) or args[0] is None) and context is None:
        context = args[0]
        arg_offset = 1
    else:
        arg_offset = 0

    progression_const = args[arg_offset] if len(args) > arg_offset else kwargs.get("progression_const", kwargs.get("constant", kwargs.get("p_const", 0)))
    fade_dur = args[arg_offset + 1] if len(args) > arg_offset + 1 else kwargs.get("fade_dur", kwargs.get("fade", kwargs.get("fade_ms", 300)))
    max_added_time = args[arg_offset + 2] if len(args) > arg_offset + 2 else kwargs.get("max_added_time", kwargs.get("max_extra", 2000))
    delay = args[arg_offset + 3] if len(args) > arg_offset + 3 else kwargs.get("delay_ms", kwargs.get("delay_line", kwargs.get("delay", 250)))
    max_gap_threshold = args[arg_offset + 4] if len(args) > arg_offset + 4 else kwargs.get("max_gap_threshold", kwargs.get("threshold", 3000))
    avg_char_width = kwargs.get("avg_char_width", 15.0)
    output_slot_index = int(kwargs.get("output_slot_index", 0))

    line = None
    if isinstance(context, dict):
        line = context.get('line') or context.get('active_line')
        if not line and context.get('active_unit'):
            line = getattr(context['active_unit'], 'line', None)
    if not line:
        return 0.0

    p_const = max(0.0, float(_eval_val(progression_const, context, 0.0)))
    fade_ms = max(0.0, float(_eval_val(fade_dur, context, 300.0)))
    cap_max = max(0.0, float(_eval_val(max_added_time, context, 2000.0)))
    delay_val = max(0.0, float(_eval_val(delay, context, 250.0)))
    gap_thresh = max(0.0, float(_eval_val(max_gap_threshold, context, 3000.0)))
    avg_w = max(1.0, float(_eval_val(avg_char_width, context, 15.0)))

    text_stripped = str(getattr(line, 'text_stripped', getattr(line, 'text', ''))).replace(" ", "")
    
    is_syl_loop = isinstance(context, dict) and ('syl' in context or (context.get('active_unit') and getattr(context.get('active_unit'), 'syl', None) is not None)) and ('char' not in context)
    is_char_loop = isinstance(context, dict) and ('char' in context)
    is_word_loop = isinstance(context, dict) and ('word' in context) and not is_syl_loop and not is_char_loop

    if is_syl_loop:
        syls_list = getattr(line, 'syls', [])
        char_count = len(syls_list) if syls_list else len(text_stripped)
    elif is_word_loop:
        words_list = getattr(line, 'words', [])
        char_count = len(words_list) if words_list else 1
    else:
        char_count = len(text_stripped) if text_stripped else 1

    char_count = max(1, char_count)
    p2_current = p_const * (char_count - 1 if char_count > 1 else 0) + delay_val

    mode = str(kwargs.get("mode", "order")).strip().lower()

    next_line = None
    if isinstance(context, dict):
        lines_list = context.get('target_lines') or context.get('selected_lines') or context.get('all_lines') or []
        valid_lines = [l for l in lines_list if not getattr(l, 'is_comment', False)]
        if valid_lines:
            curr_idx = -1
            for idx, l in enumerate(valid_lines):
                if l is line:
                    curr_idx = idx
                    break
            if curr_idx == -1:
                for idx, l in enumerate(valid_lines):
                    if hasattr(line, 'i') and hasattr(l, 'i') and l.i == line.i:
                        curr_idx = idx
                        break
            if curr_idx != -1:
                remaining = valid_lines[curr_idx + 1:]
                if mode == "style":
                    cur_style = getattr(line, 'style_name', getattr(line, 'style', ''))
                    next_line = next((l for l in remaining if getattr(l, 'style_name', getattr(l, 'style', '')) == cur_style), None)
                elif mode == "actor":
                    cur_actor = getattr(line, 'actor', '')
                    next_line = next((l for l in remaining if getattr(l, 'actor', '') == cur_actor), None)
                elif mode == "layer":
                    cur_layer = getattr(line, 'layer', 0)
                    next_line = next((l for l in remaining if getattr(l, 'layer', 0) == cur_layer), None)
                elif mode == "effect":
                    cur_effect = getattr(line, 'effect', '')
                    next_line = next((l for l in remaining if getattr(l, 'effect', '') == cur_effect), None)
                else: # "order"
                    if curr_idx + 1 < len(valid_lines):
                        next_line = valid_lines[curr_idx + 1]
        if not next_line and context.get('next_line'):
            next_line = context.get('next_line')

    curr_end = float(getattr(line, 'end_time', getattr(line, 'end', 0)))

    if not next_line:
        final_extra = round(min(cap_max, max(0.0, p2_current)), 2)
        if output_slot_index == 1:
            return round(curr_end + final_extra, 2)
        return final_extra

    next_start = float(getattr(next_line, 'start_time', getattr(next_line, 'start', 0)))
    gap_between_lines = next_start - curr_end

    if gap_between_lines < delay_val:
        if output_slot_index == 1:
            return curr_end
        return 0.0

    if gap_between_lines > gap_thresh:
        final_extra = round(min(cap_max, max(0.0, p2_current)), 2)
        if output_slot_index == 1:
            return round(curr_end + final_extra, 2)
        return final_extra

    next_text = str(getattr(next_line, 'text_stripped', getattr(next_line, 'text', ''))).replace(" ", "")
    if is_syl_loop:
        next_syls = getattr(next_line, 'syls', [])
        next_char_count = len(next_syls) if next_syls else len(next_text)
    elif is_word_loop:
        next_words = getattr(next_line, 'words', [])
        next_char_count = len(next_words) if next_words else 1
    else:
        next_char_count = len(next_text) if next_text else 1

    next_char_count = max(1, next_char_count)
    p2_next = p_const * (next_char_count - 1 if next_char_count > 1 else 0)
    transition_duration = (p2_current + p2_next) / 2.0

    curr_right = float(getattr(line, 'right', getattr(line, 'x', 0) + getattr(line, 'width', 0) / 2.0))
    next_left = float(getattr(next_line, 'left', getattr(next_line, 'x', 0) - getattr(next_line, 'width', 0) / 2.0))
    spatial_jump = next_left - curr_right
    spatial_compensation_time = (spatial_jump / avg_w) * p_const if spatial_jump > 0 else 0.0

    ideal_end_time = next_start + transition_duration + spatial_compensation_time - fade_ms
    extra_time_needed = ideal_end_time - curr_end
    final_extra_time = min(cap_max, max(0.0, extra_time_needed))

    if output_slot_index == 1:
        return round(curr_end + final_extra_time, 2)
    return round(final_extra_time, 2)



@pyxis_node("Time", "Time to Frame", ["Time (ms)", "Frame Dur (ms)"])
def time_to_frame_node(*args, **kwargs):
    """Converts time to frame count or frame index (time_to_frame).
    
    Modes:
      - Ceil: round up (duration / frame count).
      - Floor: round down (0-based timeline index).
      - Round: round to nearest frame.
      
    Sources:
      - Custom: input value 'time_val' or property 'time'.
      - Start: active unit or line start time.
      - End: active unit or line end time.
      - Dur: active unit or line duration.
    """
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        time_val = args[1] if len(args) > 1 else kwargs.get("time_val", kwargs.get("time", 0))
        frame_dur = args[2] if len(args) > 2 else kwargs.get("frame_dur", None)
    else:
        context = kwargs.get("context", {})
        time_val = args[0] if len(args) > 0 else kwargs.get("time_val", kwargs.get("time", 0))
        frame_dur = args[1] if len(args) > 1 else kwargs.get("frame_dur", None)

    if time_val == "" or time_val is None:
        time_val = kwargs.get("time_val", kwargs.get("time", 0))
    if frame_dur == "" or frame_dur is None:
        frame_dur = kwargs.get("frame_dur", None)

    mode = str(kwargs.get("mode", "Ceil")).strip().lower()
    source = str(kwargs.get("source", "Custom")).strip().lower()

    unit = context.get('active_unit') if isinstance(context, dict) else None
    line = context.get('active_line') or (context.get('line') if isinstance(context, dict) else None)

    resolved_time = None
    if source in ("start", "start time", "inicio", "st"):
        if unit and getattr(unit, 'start_time', None) is not None:
            resolved_time = float(unit.start_time)
        elif line and getattr(line, 'start_time', None) is not None:
            resolved_time = float(line.start_time)
    elif source in ("end", "end time", "fin", "et"):
        if unit and getattr(unit, 'end_time', None) is not None:
            resolved_time = float(unit.end_time)
        elif line and getattr(line, 'end_time', None) is not None:
            resolved_time = float(line.end_time)
    elif source in ("dur", "duration", "duración"):
        if unit and getattr(unit, 'duration', getattr(unit, 'dur', None)) is not None:
            resolved_time = float(getattr(unit, 'duration', getattr(unit, 'dur', 0)))
        elif line and getattr(line, 'duration', None) is not None:
            resolved_time = float(line.duration)

    if resolved_time is None:
        raw_val = time_val if (time_val is not None and str(time_val).strip() != "") else kwargs.get("time", 0)
        raw_str = str(raw_val).strip()
        if ":" in raw_str and "." in raw_str:
            resolved_time = float(parse_time(raw_str))
        else:
            resolved_time = float(_eval_val(raw_val, context, 0.0))

    raw_fd = frame_dur if (frame_dur is not None and str(frame_dur).strip() != "") else kwargs.get("frame_dur", None)
    if raw_fd is not None and str(raw_fd).strip() != "":
        fd = float(_eval_val(raw_fd, context, 41.708))
    else:
        fd = float(context.get("frame_dur", 41.708)) if isinstance(context, dict) else 41.708

    fd = max(0.001, fd)

    if "floor" in mode or "pos" in mode or "suelo" in mode:
        return int(math.floor(resolved_time / fd))
    elif "round" in mode or "cercano" in mode or "redondeo" in mode:
        return int(round(resolved_time / fd))
    else:
        return int(math.ceil(resolved_time / fd))


@pyxis_node("Time", "Frame to Time", ["Frames (f)", "Frame Dur (ms)"])
def frame_to_time_node(*args, **kwargs):
    """Converts frames to time in ms, ASS format or seconds (frame_to_time).
    
    Formats (format):
      - MS: numeric milliseconds (e.g. 2502.48).
      - HMS: ASS subtitle timestamp string (e.g. 0:00:02.50).
      - SEC: floating-point seconds (e.g. 2.502).
      
    Sources (source):
      - Custom: input value 'frames' from properties or socket.
      - j: current loop counter context['j'].
      - J: global loop counter context['J'].
      - i: active unit index unit.i.
    """
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        frames = args[1] if len(args) > 1 else kwargs.get("frames", 1)
        frame_dur = args[2] if len(args) > 2 else kwargs.get("frame_dur", None)
    else:
        context = kwargs.get("context", {})
        frames = args[0] if len(args) > 0 else kwargs.get("frames", 1)
        frame_dur = args[1] if len(args) > 1 else kwargs.get("frame_dur", None)

    if frames == "" or frames is None:
        frames = kwargs.get("frames", 1)
    if frame_dur == "" or frame_dur is None:
        frame_dur = kwargs.get("frame_dur", None)

    format_mode = str(kwargs.get("format", "MS")).strip().lower()
    output_slot_index = kwargs.get("output_slot_index", 0)
    raw_source = str(kwargs.get("source", "Custom")).strip()
    source_lower = raw_source.lower()

    unit = context.get('active_unit') if isinstance(context, dict) else None

    resolved_frames = None
    if source_lower in ("iter", "iterador", "iterator", "loop", "bucle"):
        iter_key = str(kwargs.get("iter_name", "")).strip()
        if not iter_key:
            iter_key = "j"
        if isinstance(context, dict) and iter_key in context:
            resolved_frames = float(_num(context[iter_key], 1.0))
        else:
            resolved_frames = float(_eval_val(iter_key, context, 1.0))
    elif raw_source == "J" or "(J)" in raw_source:
        resolved_frames = float(context.get('J', 1)) if isinstance(context, dict) else 1.0
    elif raw_source == "j" or "(j)" in raw_source or source_lower in ("j", "loop (j)", "bucle (j)"):
        resolved_frames = float(context.get('j', context.get('fx_i', 1))) if isinstance(context, dict) else 1.0
    elif source_lower in ("i", "índice (i)", "indice (i)", "index"):
        resolved_frames = float(getattr(unit, 'i', context.get('i', 1))) if unit else float(context.get('i', 1) if isinstance(context, dict) else 1.0)

    if resolved_frames is None:
        raw_val = frames if (frames is not None and str(frames).strip() != "") else kwargs.get("frames", 1)
        resolved_frames = float(_eval_val(raw_val, context, 1.0))

    raw_fd = frame_dur if (frame_dur is not None and str(frame_dur).strip() != "") else kwargs.get("frame_dur", None)
    if raw_fd is not None and str(raw_fd).strip() != "":
        fd = float(_eval_val(raw_fd, context, 41.708))
    else:
        fd = float(context.get("frame_dur", 41.708)) if isinstance(context, dict) else 41.708

    fd = max(0.001, fd)
    ms = resolved_frames * fd

    if output_slot_index == 1:
        return format_time(int(round(ms)))

    if "hms" in format_mode or "ass" in format_mode or "timestamp" in format_mode:
        return format_time(int(round(ms)))
    elif "ms" in format_mode or "mili" in format_mode:
        return round(ms, 2)
    elif "sec" in format_mode or "seg" in format_mode or format_mode == "s":
        return round(ms / 1000.0, 3)
    else:
        return round(ms, 2)


# ==============================================================================
# Retime (Phonetic Re-timing & \t Mapping)
# ==============================================================================

def _format_clean_scalar(val):
    try:
        f = float(val)
        if f.is_integer():
            return str(int(f))
        return f"{round(f, 2):.2f}".rstrip('0').rstrip('.')
    except:
        return str(val)

def _resolve_unit_and_line_times(context):
    """Extracts phonetic timestamps both globally (video timeline) and locally (relative to eff_line_st / line.start_time)."""
    unit = context.get('active_unit') if isinstance(context, dict) else None
    line = context.get('active_line') or (context.get('line') if isinstance(context, dict) else None)

    line_st = float(getattr(line, 'start_time', getattr(line, 'st', 0.0))) if line else 0.0
    line_et = float(getattr(line, 'end_time', getattr(line, 'et', 0.0))) if line else 0.0
    line_dur = float(getattr(line, 'duration', max(0.0, line_et - line_st))) if line else 0.0

    eff_line_st = line_st
    eff_line_et = line_et
    eff_line_dur = line_dur

    if isinstance(context, dict):
        for k in ('fx_st', 'effect_st', 'fx_start_time'):
            if k in context and context[k] is not None:
                eff_line_st = float(context[k])
                break
        for k in ('fx_et', 'effect_et', 'fx_end_time'):
            if k in context and context[k] is not None:
                eff_line_et = float(context[k])
                break
        for k in ('fx_dur', 'effect_dur', 'dur', 'duration'):
            if k in context and context[k] is not None:
                eff_line_dur = float(context[k])
                break

    if eff_line_dur <= 0.0:
        eff_line_dur = max(0.0, eff_line_et - eff_line_st) if (eff_line_et > eff_line_st) else line_dur
    if eff_line_dur <= 0.0:
        eff_line_dur = 1000.0

    if line_dur <= 0.0:
        line_dur = eff_line_dur

    syl = context.get('syl') if isinstance(context, dict) else None
    if not syl and unit and getattr(unit, 'unit_type', None) in ('syl', 'syllable'):
        syl = unit

    raw_syl_st = float(getattr(syl, 'start_time', getattr(syl, 'st', getattr(unit, 'start_time', line_st)))) if (syl or unit) else line_st
    raw_syl_et = float(getattr(syl, 'end_time', getattr(syl, 'et', getattr(unit, 'end_time', raw_syl_st)))) if (syl or unit) else raw_syl_st

    if line_st > 0 and raw_syl_st >= line_st:
        syl_st_global = raw_syl_st
        syl_et_global = raw_syl_et
    else:
        syl_st_global = line_st + raw_syl_st
        syl_et_global = line_st + raw_syl_et

    syl_st_local = syl_st_global - eff_line_st
    syl_et_local = syl_et_global - eff_line_st
    syl_dur = float(getattr(syl, 'duration', max(0.0, syl_et_global - syl_st_global))) if (syl or unit) else max(0.0, syl_et_global - syl_st_global)

    word = context.get('word') if isinstance(context, dict) else None
    if not word and unit and getattr(unit, 'unit_type', None) in ('word',):
        word = unit
    raw_word_st = float(getattr(word, 'start_time', getattr(word, 'st', raw_syl_st))) if word else raw_syl_st
    raw_word_et = float(getattr(word, 'end_time', getattr(word, 'et', raw_syl_et))) if word else raw_syl_et
    if line_st > 0 and raw_word_st >= line_st:
        word_st_global = raw_word_st
        word_et_global = raw_word_et
    else:
        word_st_global = line_st + raw_word_st
        word_et_global = line_st + raw_word_et
    word_st_local = word_st_global - eff_line_st
    word_et_local = word_et_global - eff_line_st

    char = context.get('char') if isinstance(context, dict) else None
    if not char and unit and getattr(unit, 'unit_type', None) in ('char', 'character'):
        char = unit
    raw_char_st = float(getattr(char, 'start_time', getattr(char, 'st', raw_syl_st))) if char else raw_syl_st
    raw_char_et = float(getattr(char, 'end_time', getattr(char, 'et', raw_syl_et))) if char else raw_syl_et
    if line_st > 0 and raw_char_st >= line_st:
        char_st_global = raw_char_st
        char_et_global = raw_char_et
    else:
        char_st_global = line_st + raw_char_st
        char_et_global = line_st + raw_char_et
    char_st_local = char_st_global - eff_line_st
    char_et_local = char_et_global - eff_line_st

    return {
        'line_st': line_st,
        'line_et': line_et,
        'line_dur': line_dur,
        'eff_line_st': eff_line_st,
        'eff_line_et': eff_line_et,
        'eff_line_dur': eff_line_dur,
        'syl_st_global': syl_st_global, 'syl_et_global': syl_et_global,
        'syl_st_local': syl_st_local, 'syl_et_local': syl_et_local,
        'syl_dur': syl_dur,
        'word_st_global': word_st_global, 'word_et_global': word_et_global,
        'word_st_local': word_st_local, 'word_et_local': word_et_local,
        'char_st_global': char_st_global, 'char_et_global': char_et_global,
        'char_st_local': char_st_local, 'char_et_local': char_et_local,
    }


def _resolve_phase_interval(phase_name, times_dict, custom_st=0.0, custom_et=0.0, off_in=0.0, off_out=0.0, is_global=False):
    """Resolves the final interval [T1, T2] according to retime modes.
    
    is_global=True: Returns absolute video timeline timestamps (for Start/End Time ports).
    is_global=False: Returns local line-relative timestamps to eff_line_st (for ASS \t(...) blocks).
    """
    p = str(phase_name or "syl").strip().lower().replace("_", "").replace(" ", "").replace("-", "")
    line_st = times_dict['line_st']
    line_et = times_dict['line_et']
    eff_line_st = times_dict['eff_line_st']
    eff_line_dur = times_dict['eff_line_dur']
    syl_dur = times_dict['syl_dur']

    if is_global:
        st_base = times_dict['syl_st_global']
        et_base = times_dict['syl_et_global']
        l_st = line_st
        l_et = line_et

        if p in ("syl", "sylactive", "syllable", "silaba", "sílaba", "active"):
            return round(st_base + off_in, 2), round(et_base + off_out, 2)
        elif p in ("presyl",):
            return round(st_base + off_in, 2), round(st_base + off_out, 2)
        elif p in ("postsyl",):
            return round(et_base + off_in, 2), round(et_base + off_out, 2)
        elif p in ("line", "linea", "línea"):
            return round(l_st + off_in, 2), round(l_et + off_out, 2)
        elif p in ("preline",):
            return round(l_st + off_in, 2), round(l_st + off_out, 2)
        elif p in ("postline",):
            return round(l_et + off_in, 2), round(l_et + off_out, 2)
        elif p in ("start2syl", "starttosyl", "leadin"):
            return round(l_st + off_in, 2), round(st_base + off_out, 2)
        elif p in ("syl2end", "syltoend", "leadout"):
            return round(et_base + off_in, 2), round(l_et + off_out, 2)
        elif p in ("set", "abs", "absolute", "absoluto"):
            return round(off_in, 2), round(off_out, 2)
        elif p in ("sylpct", "pct", "porcentaje"):
            return round(st_base + (off_in * syl_dur / 100.0), 2), round(st_base + (off_out * syl_dur / 100.0), 2)
        elif p in ("custom", "personalizado"):
            return round(float(custom_st) + off_in, 2), round(float(custom_et) + off_out, 2)
        else:
            return round(st_base + off_in, 2), round(et_base + off_out, 2)
    else:
        st_base = times_dict['syl_st_local']
        et_base = times_dict['syl_et_local']
        orig_st_rel = line_st - eff_line_st
        orig_et_rel = line_et - eff_line_st

        if p in ("syl", "sylactive", "syllable", "silaba", "sílaba", "active"):
            return round(st_base + off_in, 2), round(et_base + off_out, 2)
        elif p in ("presyl",):
            return round(st_base + off_in, 2), round(st_base + off_out, 2)
        elif p in ("postsyl",):
            return round(et_base + off_in, 2), round(et_base + off_out, 2)
        elif p in ("line", "linea", "línea"):
            return round(0.0 + off_in, 2), round(eff_line_dur + off_out, 2)
        elif p in ("preline",):
            return round(orig_st_rel + off_in, 2), round(orig_st_rel + off_out, 2)
        elif p in ("postline",):
            return round(orig_et_rel + off_in, 2), round(orig_et_rel + off_out, 2)
        elif p in ("start2syl", "starttosyl", "leadin"):
            return round(orig_st_rel + off_in, 2), round(st_base + off_out, 2)
        elif p in ("syl2end", "syltoend", "leadout"):
            return round(et_base + off_in, 2), round(orig_et_rel + off_out, 2)
        elif p in ("set", "abs", "absolute", "absoluto"):
            return round(off_in, 2), round(off_out, 2)
        elif p in ("sylpct", "pct", "porcentaje"):
            return round(st_base + (off_in * syl_dur / 100.0), 2), round(st_base + (off_out * syl_dur / 100.0), 2)
        elif p in ("custom", "personalizado"):
            return round(float(custom_st) + off_in, 2), round(float(custom_et) + off_out, 2)
        else:
            return round(st_base + off_in, 2), round(et_base + off_out, 2)


def eval_retime_node(context=None, *args, **kwargs):
    """Evaluates the Retime node, rescaling timestamps and \\t(...) blocks according to selected mode."""
    if len(args) > 0 and isinstance(args[0], dict) and context is None:
        context = args[0]

    raw_tags = str(kwargs.get("tags", kwargs.get("in_0", kwargs.get("in", kwargs.get("Tags or \\t", kwargs.get("tags or \\t", kwargs.get(r"\t In", kwargs.get(r"\t in", kwargs.get("t_in", kwargs.get("tags_in", "")))))))))).strip()
    if not raw_tags and len(args) > 0:
        if isinstance(args[0], str):
            raw_tags = args[0].strip()
        elif len(args) > 1 and isinstance(args[1], str):
            raw_tags = args[1].strip()
    raw_phase = str(kwargs.get("phase", kwargs.get("fase", kwargs.get("mode", "syl")))).strip()
    raw_off_in = kwargs.get("offset_in", kwargs.get("off_in", kwargs.get("in_1", 0.0)))
    raw_off_out = kwargs.get("offset_out", kwargs.get("off_out", kwargs.get("in_2", 0.0)))
    raw_accel = kwargs.get("accel", kwargs.get("acceleration", kwargs.get("in_3", 1.0)))
    custom_st = kwargs.get("custom_start", 0.0)
    custom_et = kwargs.get("custom_end", 0.0)
    output_slot_index = int(kwargs.get("output_slot_index", 0))

    off_in = float(_eval_val(raw_off_in, context, 0.0))
    off_out = float(_eval_val(raw_off_out, context, 0.0))
    accel = float(_eval_val(raw_accel, context, 1.0))

    times_dict = _resolve_unit_and_line_times(context or {})

    # Slots 1 & 2 (Start Time & End Time): return global times for Output ASS headers
    if output_slot_index in (1, 2, 3):
        global_t1, global_t2 = _resolve_phase_interval(raw_phase, times_dict, custom_st=custom_st, custom_et=custom_et, off_in=off_in, off_out=off_out, is_global=True)
        if output_slot_index == 1:
            return global_t1
        elif output_slot_index == 2:
            return global_t2
        elif output_slot_index == 3:
            return round(max(0.0, global_t2 - global_t1), 2)

    # Slot 0 (\t Out): always operates in the local space of the dialogue line
    local_t1, local_t2 = _resolve_phase_interval(raw_phase, times_dict, custom_st=custom_st, custom_et=custom_et, off_in=off_in, off_out=off_out, is_global=False)

    if not raw_tags:
        return ""

    # Re-timing of \t(...) blocks
    t_regex = re.compile(r'\\t\(\s*(?:(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,)?\s*(?:(-?\d+(?:\.\d+)?)\s*,)?\s*([^\)]*)\)')

    def _retime_t_match(m):
        orig_t1 = m.group(1)
        orig_t2 = m.group(2)
        orig_accel = m.group(3)
        inner_tags = (m.group(4) or "").strip()

        # If user specified accel in kwargs != 1.0, it takes priority; otherwise preserves orig_accel
        used_accel = accel if abs(accel - 1.0) > 1e-4 else (float(orig_accel) if orig_accel else 1.0)
        accel_str = f"{_format_clean_scalar(used_accel)}," if abs(used_accel - 1.0) > 1e-4 else ""

        if orig_t1 is not None and orig_t2 is not None:
            # Shift relative times to the local_t1 window
            mapped_t1 = round(local_t1 + float(orig_t1), 2)
            mapped_t2 = round(local_t1 + float(orig_t2), 2)
            t1_str = _format_clean_scalar(mapped_t1)
            t2_str = _format_clean_scalar(mapped_t2)
            return f"\\t({t1_str},{t2_str},{accel_str}{inner_tags})"
        else:
            # \t sin tiempos especificados: asigna la ventana completa de la fase
            t1_str = _format_clean_scalar(local_t1)
            t2_str = _format_clean_scalar(local_t2)
            return f"\\t({t1_str},{t2_str},{accel_str}{inner_tags})"

    if r"\t(" in raw_tags:
        retimed_tags = t_regex.sub(_retime_t_match, raw_tags)
        return retimed_tags
    else:
        # Cadena de tags planos: envuelve en \t(...)
        accel_str = f"{_format_clean_scalar(accel)}," if abs(accel - 1.0) > 1e-4 else ""
        t1_str = _format_clean_scalar(local_t1)
        t2_str = _format_clean_scalar(local_t2)
        return f"\\t({t1_str},{t2_str},{accel_str}{raw_tags})"


@pyxis_node("Time", "Retime", ["Tags or \\t", "Offset In (ms)", "Offset Out (ms)", "Accel"])
def RetimeNode(context=None, *args, **kwargs):
    return eval_retime_node(context=context, *args, **kwargs)

NODE_REGISTRY["Time/Parse ASS Time"] = time_parse_ass
NODE_REGISTRY["Parse ASS Time"] = time_parse_ass
NODE_REGISTRY["Time/Format ASS Time"] = time_format_ass
NODE_REGISTRY["Format ASS Time"] = time_format_ass
NODE_REGISTRY["Time/Time to Frame"] = time_to_frame_node
NODE_REGISTRY["Time to Frame"] = time_to_frame_node
NODE_REGISTRY["Time/Frame to Time"] = frame_to_time_node
NODE_REGISTRY["Frame to Time"] = frame_to_time_node
NODE_REGISTRY["Time/Retime"] = RetimeNode
NODE_REGISTRY["Retime"] = RetimeNode
NODE_REGISTRY["Time/Lead In"] = time_lead_in
NODE_REGISTRY["Lead In"] = time_lead_in
NODE_REGISTRY["Time/Lead Out"] = time_lead_out
NODE_REGISTRY["Lead Out"] = time_lead_out
NODE_REGISTRY["Time/Synced"] = time_synchronized_extra_node
NODE_REGISTRY["Synced"] = time_synchronized_extra_node




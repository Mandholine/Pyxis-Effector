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

# PyxisNodes/nodes/time_nodes.py
"""Nodos de tiempo y desplazamientos temporales basados en Effector 2 (ke.time)."""

import math
from decorators import pyxis_node
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


@pyxis_node("Time", "Lead In", ["Delay (ms)", "Base (ms)"])
def time_lead_in(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay", 40)
        base = args[2] if len(args) > 2 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay", 40)
        base = args[1] if len(args) > 1 else kwargs.get("base", None)

    delay_val = _eval_val(delay, context, 40.0)
    unit = context.get('active_unit') if isinstance(context, dict) else None
    i = float(getattr(unit, 'i', 1) if unit else 1)
    base_val = _get_base_time(context, is_end_time=False, base=base)
    return round(base_val + delay_val * (i - 1.0) - 200.0, 3)


@pyxis_node("Time", "Lead Out", ["Delay (ms)", "Base (ms)"])
def time_lead_out(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay", 40)
        base = args[2] if len(args) > 2 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay", 40)
        base = args[1] if len(args) > 1 else kwargs.get("base", None)

    delay_val = _eval_val(delay, context, 40.0)
    unit = context.get('active_unit') if isinstance(context, dict) else None
    i = float(getattr(unit, 'i', 1) if unit else 1)
    n = float(getattr(unit, 'n', 1) if unit else 1)
    base_val = _get_base_time(context, is_end_time=True, base=base)
    return round(base_val + delay_val * (i - n - 1.0) + 200.0, 3)


@pyxis_node("Time", "Middle 1", ["Delay (ms)", "Base (ms)"])
def time_middle_1(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay", 30)
        base = args[2] if len(args) > 2 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay", 30)
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


@pyxis_node("Time", "Middle 2", ["Delay (ms)", "Base (ms)"])
def time_middle_2(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay", 30)
        base = args[2] if len(args) > 2 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay", 30)
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


@pyxis_node("Time", "Loop 1", ["Delay (ms)", "Modo", "Base (ms)"])
def time_loop_1(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay", 30)
        mode = args[2] if len(args) > 2 else kwargs.get("mode", "leadin")
        base = args[3] if len(args) > 3 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay", 30)
        mode = args[1] if len(args) > 1 else kwargs.get("mode", "leadin")
        base = args[2] if len(args) > 2 else kwargs.get("base", None)

    delay_val = _eval_val(delay, context, 30.0)
    mode_str = str(mode).strip().lower()
    j = float(context.get('fx_i', context.get('j', 1))) if isinstance(context, dict) else 1.0
    maxj = float(context.get('fx_n', context.get('j_max', context.get('maxj', 1)))) if isinstance(context, dict) else 1.0
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


@pyxis_node("Time", "Loop 2", ["Delay (ms)", "Modo", "Base (ms)"])
def time_loop_2(*args, **kwargs):
    if len(args) > 0 and isinstance(args[0], dict):
        context = args[0]
        delay = args[1] if len(args) > 1 else kwargs.get("delay", 30)
        mode = args[2] if len(args) > 2 else kwargs.get("mode", "leadin")
        base = args[3] if len(args) > 3 else kwargs.get("base", None)
    else:
        context = kwargs.get("context", {})
        delay = args[0] if len(args) > 0 else kwargs.get("delay", 30)
        mode = args[1] if len(args) > 1 else kwargs.get("mode", "leadin")
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


@pyxis_node("Time", "Time Ipol", ["Duration (ms)", "Points / Values", "Acceleration"])
def time_ipol(context, dur=1000, points="0, 100", accel=1.0):
    unit = context.get('active_unit')
    default_dur = getattr(unit, 'duration', getattr(unit, 'dur', 1000)) if unit else 1000
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


@pyxis_node("Time", "Offset", ["Base (ms)", "Offset (ms)"])
def time_offset(context, base=0, offset=0):
    return int(_num(base) + _num(offset))

@pyxis_node("Time", "Duración", ["Start Time (ms)", "End Time (ms)"])
def time_duration(context, st=None, et=None):
    if (st is None or str(st).strip() == "") and (et is None or str(et).strip() == ""):
        unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
        if unit and getattr(unit, 'duration', None) is not None:
            return int(unit.duration)
        line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
        if line and getattr(line, 'duration', None) is not None:
            return int(line.duration)
    return max(0, int(_num(et) - _num(st)))

@pyxis_node("Time", "Parse ASS Time", ["ASS Time"])
def time_parse_ass(context, ass_str=""):
    raw = str(ass_str).strip()
    if not raw and isinstance(context, dict):
        line = context.get('active_line') or context.get('line')
        if line:
            raw = str(getattr(line, 'start_str', getattr(line, 'start', '0:00:00.00')))
    return parse_time(raw)

@pyxis_node("Time", "Format ASS Time", ["Time (ms)"])
def time_format_ass(context, ms=None):
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
    return format_time(int(_num(ms)))

# -----------------------------------------------------------------------------
# NODOS DINÁMICOS DE TIEMPO INTER-LÍNEAS (FASE 4 - SEIJITSU SYNCHRONIZATION)
# -----------------------------------------------------------------------------
def time_synchronized_extra_node(context, progression_const=0, fade_dur=300, max_added_time=2000, delay=250, max_gap_threshold=3000, avg_char_width=15.0):
    """Cálculo dinámico de extensión temporal inter-líneas sincronizada (calculate.synchronized_extratime_3)."""
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

    # 1. Determinar conteo de unidades según el dominio de bucle activo (Auto-Detección syl / char / word)
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

    # 2. Localizar la siguiente línea para análisis de brecha inter-línea
    next_line = None
    if isinstance(context, dict):
        next_line = context.get('next_line')
        if not next_line:
            lines_list = context.get('selected_lines') or context.get('all_lines') or []
            if lines_list and line in lines_list:
                curr_idx = lines_list.index(line)
                if curr_idx + 1 < len(lines_list):
                    next_line = lines_list[curr_idx + 1]

    # Si es la última línea o no hay siguiente línea, devolver el tiempo extra simple limitado por el cap
    if not next_line:
        return round(min(cap_max, max(0.0, p2_current)), 2)

    # 3. Calcular la brecha temporal entre esta línea y la siguiente
    curr_end = float(getattr(line, 'end_time', getattr(line, 'end', 0)))
    next_start = float(getattr(next_line, 'start_time', getattr(next_line, 'start', 0)))
    gap_between_lines = next_start - curr_end

    # Si están demasiado pegadas (menos que el delay), no se añade tiempo extra
    if gap_between_lines < delay_val:
        return 0.0

    # Si están muy separadas (más que el umbral), se devuelve el tiempo estándar
    if gap_between_lines > gap_thresh:
        return round(min(cap_max, max(0.0, p2_current)), 2)

    # 4. Compensación espacial y temporal inter-líneas (algoritmo Seijitsu v3 adaptativo)
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

    return round(final_extra_time, 2)


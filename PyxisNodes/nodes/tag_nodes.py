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

# PyxisNodes/nodes/tag_nodes.py
"""Nodo maestro de generación de etiquetas ASS (MultiTag)."""

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


# -----------------------------------------------------------------------------
# NODO MAESTRO: TAG DINÁMICO
# -----------------------------------------------------------------------------
def tag_master(context, tag_type="pos", **kwargs):
    tag = str(tag_type or "pos").strip().lower().lstrip("\\")
    
    def clean_n(v, d=0.0, dec=2):
        return _clean_num(v, default=d, decimals=dec, context=context)

    def clean_a(v, d=0):
        return _clean_alpha(v, default=d, context=context)

    def get_val(keys, default="", pos_idx=None):
        # 1. El índice de slot posicional tiene máxima prioridad para el puerto
        if pos_idx is not None:
            for k in [str(pos_idx), pos_idx, f"in_{pos_idx}", f"in{pos_idx}", f"in_{pos_idx+1}", f"in{pos_idx+1}"]:
                if k in kwargs and kwargs[k] is not None and str(kwargs[k]).strip() != "":
                    return kwargs[k]

        if isinstance(keys, str):
            key_list = [keys]
        else:
            key_list = list(keys)
        
        # 2. Coincidencia exacta de clave en kwargs
        for k_target in key_list:
            if k_target in kwargs and kwargs[k_target] is not None and str(kwargs[k_target]).strip() != "":
                return kwargs[k_target]

        # 3. Búsqueda normalizada insensible a mayúsculas/espacios/caracteres especiales
        for k_target in key_list:
            target_clean = str(k_target).lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", "").replace("-", "").replace("/", "")
            for k, v in kwargs.items():
                if v is not None and str(v).strip() != "":
                    k_clean = str(k).lower().replace(" ", "").replace("_", "").replace("(", "").replace(")", "").replace("-", "").replace("/", "")
                    if k_clean == target_clean:
                        return v
        return default

    # Context position defaults
    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
    ctx_pos_x = getattr(unit, 'center', getattr(unit, 'x', getattr(line, 'center', getattr(line, 'x', 0.0)))) if (unit or line) else 0.0
    ctx_pos_y = getattr(unit, 'middle', getattr(unit, 'y', getattr(line, 'middle', getattr(line, 'y', 0.0)))) if (unit or line) else 0.0

    # 1. Coordenadas / Posición
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
    
    # 2. Desvanecimientos
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

    # 3. Clips y Dibujos
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

    # 4. Colores
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

    # 5. Transparencias / Alpha
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

    # 6. Transformación Animada
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

    # 7. Tags de 1 argumento numérico o texto
    else:
        val = get_val(["value", "valor", "val", "value", "v"], "", pos_idx=0)
        if tag in ("fscx", "fscy", "frz", "frx", "fry", "fax", "fay", "bord", "xbord", "ybord", "shad", "xshad", "yshad", "blur", "be", "fs", "fsp"):
            return f"\\{tag}{clean_n(val)}"
        elif tag in ("an", "b", "i", "u", "s", "k", "kf", "ko", "p", "pbo", "q"):
            return f"\\{tag}{int(clean_n(val))}"
        else:
            return f"\\{tag}{str(val).strip()}"


# -----------------------------------------------------------------------------
# NODO: CONDICIONADOR (INYECCIÓN CONDICIONAL DE TAGS ASS Y VALORES)
# -----------------------------------------------------------------------------
from decorators import pyxis_node

@pyxis_node("Functions", "Conditioner", ["Condition", "If True", "If False"])
def node_condicionador(context, condicion=True, si_verdadero="", si_falso=""):
    cond_bool = False
    if isinstance(condicion, bool):
        cond_bool = condicion
    elif isinstance(condicion, (int, float)):
        cond_bool = (float(condicion) != 0.0)
    elif isinstance(condicion, str):
        v = str(condicion).strip()
        if v.startswith("!") and v.endswith("!"):
            v = v[1:-1].strip()
        
        v_lower = v.lower()
        if v_lower in ("true", "1", "yes", "si", "sí", "t"):
            cond_bool = True
        elif v_lower in ("false", "0", "no", "nil", "f", ""):
            cond_bool = False
        else:
            try:
                import math
                eval_scope = dict(context or {})
                if "line" in eval_scope and "l" not in eval_scope:
                    eval_scope["l"] = eval_scope["line"]
                if "active_unit" in eval_scope and eval_scope["active_unit"]:
                    u = eval_scope["active_unit"]
                    eval_scope.setdefault("syl", getattr(u, "syl", u))
                    eval_scope.setdefault("char", getattr(u, "char", None))
                    eval_scope.setdefault("word", getattr(u, "word", None))
                    eval_scope.setdefault("line", getattr(u, "line", None))
                    if "l" not in eval_scope:
                        eval_scope["l"] = eval_scope.get("line")
                if "syl" in eval_scope and "sili" not in eval_scope:
                    eval_scope["sili"] = eval_scope["syl"]
                if "fx" not in eval_scope:
                    from node_engine import FxContext
                    eval_scope["fx"] = FxContext(eval_scope)

                math_fns = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
                eval_globals = {"math": math, "__builtins__": {
                    "abs": abs, "min": min, "max": max, "round": round, "int": int, "float": float, "bool": bool, "len": len, "str": str
                }}
                eval_globals.update(math_fns)

                from nodes.math_nodes import math_random_master
                eval_scope["R"] = lambda min_v=0, max_v=100, step_v=1: math_random_master(context, modo="R", min_val=min_v, max_val=max_v, step=step_v)
                eval_scope["Rs"] = lambda min_v=0, max_v=100: math_random_master(context, modo="Rs", min_val=min_v, max_val=max_v)
                eval_scope["Rc"] = lambda min_v=0, max_v=100: math_random_master(context, modo="Rc", min_val=min_v, max_val=max_v)

                v_eval = v.replace("^", "**")
                res = eval(v_eval, eval_globals, eval_scope)
                cond_bool = bool(res)
            except Exception:
                cond_bool = len(v) > 0
    
    return str(si_verdadero) if cond_bool else str(si_falso)

node_tag_only = node_condicionador


# -----------------------------------------------------------------------------
# NODO: GRADIENTE COLOR MULTI-STOP
# -----------------------------------------------------------------------------
@pyxis_node("Functions", "Color Gradient", ["Progress (0-1)", "Color List"])
def node_gradiente_color(context, prog="char.i / char.n", colors_str="#95E648,#3E750C,#ED38CA"):
    """Interpolador de color multi-stop (estilo color.gradient de Effector)."""
    try:
        from node_engine import _eval_num_expr
        pct = _eval_num_expr(prog, context, 0.0)
    except (ValueError, TypeError):
        pct = 0.0

    pct = max(0.0, min(1.0, pct))

    raw_str = str(colors_str or "").strip()
    if not raw_str:
        return "&HFFFFFF&"

    raw_tokens = [t.strip() for t in raw_str.replace(";", ",").replace("\n", ",").split(",") if t.strip()]
    if not raw_tokens:
        raw_tokens = [t.strip() for t in raw_str.split() if t.strip()]

    if not raw_tokens:
        return "&HFFFFFF&"

    if len(raw_tokens) == 1:
        return _clean_color(raw_tokens[0])

    n_segments = len(raw_tokens) - 1
    pos = pct * n_segments
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

# -----------------------------------------------------------------------------
# NODO MAESTRO: TAG OSCILADOR UNIFICADO (POLARES STANDARD)
# -----------------------------------------------------------------------------
import random

@pyxis_node("Functions", "Tag Oscillator", [
    "Start Time (ms)", "End Time (ms)", "Paso / Periodo (ms)", "Transicion (ms)",
    "Duty Cycle (0-1)", "Tags / Estados", "Accel / Easing", "Dilatacion Paso (ms)",
    "Dilatacion Trans (ms)", "Offset Secuencia (ms)", "Patron Ritmo (ms)",
    "Modo Oscilacion", "Modo Orden", "Slot Salida"
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
    modo_oscilacion="Onda",
    modo_orden="Secuencial",
    output_slot_index=0,
    **kwargs
):
    """Generador maestro de oscilaciones ASS continuas (Polares Standard)."""
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

    # Parse tags
    if isinstance(tags, (list, tuple)):
        tag_list = [str(x).strip() for x in tags if str(x).strip()]
    else:
        raw_s = str(tags or r"\frz30\fry20,\frz-20\fry-20").strip()
        tag_list = [x.strip() for x in raw_s.replace(";", ",").replace("\n", ",").split(",") if x.strip()]

    if not tag_list:
        tag_list = [r"\fscx100\fscy100"]

    # Parse rhythm pattern
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

    mode_osc = str(modo_oscilacion or "Onda").strip().lower()
    mode_ord = str(modo_orden or "Secuencial").strip().lower()
    is_strobe = ("strobe" in mode_osc or "destello" in mode_osc)

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

    # Format outputs
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

    # Default output slot 0: ASS string
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


from decorators import NODE_REGISTRY
NODE_REGISTRY["MultiTag"] = tag_master
NODE_REGISTRY["Functions/Color Gradient"] = node_gradiente_color
NODE_REGISTRY["Color Gradient"] = node_gradiente_color
NODE_REGISTRY["Functions/Tag Oscillator"] = tag_oscillator_node
NODE_REGISTRY["Tag Oscillator"] = tag_oscillator_node




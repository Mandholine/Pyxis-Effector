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

# node_engine.py (v1.0.5)
import math
import os
import re
import time
import threading
import multiprocessing
import concurrent.futures
from typing import Any
from utils import format_time
from decorators import NODE_REGISTRY, PYXIS_DB
import nodes_library
from models import PyxisLine, PyxisUnit

_AN_RE = re.compile(r'\\an\d+')
_POS_RE = re.compile(r'\\pos\(')
_MOVE_RE = re.compile(r'\\move\(')
_TAG_BLOCK_RE = re.compile(r'\{.*?\}')


def _has_visible_content(unit) -> bool:
    return bool(str(getattr(unit, 'text_stripped', '')).strip())


def _final_text_has_content(rendered: str) -> bool:
    stripped = _TAG_BLOCK_RE.sub('', str(rendered))
    stripped = stripped.replace(r'\N', ' ').replace(r'\n', ' ').replace(r'\h', ' ')
    return stripped.strip() != ""


def _is_empty_value(value) -> bool:
    return value is None or str(value).strip() == ""


def _to_int_or_default(value, default, context=None):
    if _is_empty_value(value):
        if isinstance(default, (int, float)):
            return int(round(default))
        if context is not None and isinstance(default, str) and default.strip():
            try:
                res_def = _eval_num_expr(default, context, default=0.0)
                return int(round(float(res_def)))
            except Exception:
                pass
        try:
            return int(round(float(default)))
        except (TypeError, ValueError):
            return 0

    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        pass
    if context is not None:
        try:
            res = _eval_num_expr(value, context, default=default)
            return int(round(float(res)))
        except Exception:
            pass
    try:
        return int(round(float(default)))
    except (TypeError, ValueError):
        return 0


def merge_ass_tags(return_tags_str: str, port_tags_str: str) -> str:
    """Combina y desduplica limpiamente las etiquetas ASS de Return y Tags port.
    Las etiquetas del puerto Tags tienen prioridad absoluta y reemplazan a las de Return en caso de colisión.
    """
    if not return_tags_str and not port_tags_str:
        return ""

    def _parse_tag_dict(s_raw):
        if not s_raw: return {}
        s = re.sub(r'[\{\}]', '', str(s_raw)).strip()
        pattern = r'(\\(?:pos|org|move|clip|iclip|fad|fade|t)\([^)]*\)|\\(?:[1-4]?c|[1-4]?a|alpha|an|a|fscx|fscy|frz|frx|fry|fr|fax|fay|xbord|ybord|bord|xshad|yshad|shad|blur|be|fsp|fs|fn|p|q|r|b|i|u|s|[kK]f?|ko?)(?:&H[0-9a-fA-F]+&|[^\\]*))'
        matches = re.findall(pattern, s)
        t_dict = {}
        t_cnt = 0
        for m in matches:
            m_str = m.strip()
            if not m_str: continue
            if m_str.startswith('\\pos'): k = 'pos'
            elif m_str.startswith('\\org'): k = 'org'
            elif m_str.startswith('\\move'): k = 'move'
            elif m_str.startswith('\\iclip'): k = 'iclip'
            elif m_str.startswith('\\clip'): k = 'clip'
            elif m_str.startswith('\\fad') or m_str.startswith('\\fade'): k = 'fad'
            elif m_str.startswith('\\t'):
                k = f't_{t_cnt}'
                t_cnt += 1
            elif m_str.startswith('\\an') or (m_str.startswith('\\a') and not m_str.startswith('\\alpha')): k = 'an'
            elif m_str.startswith('\\1c') or m_str.startswith('\\c'): k = '1c'
            elif m_str.startswith('\\2c'): k = '2c'
            elif m_str.startswith('\\3c'): k = '3c'
            elif m_str.startswith('\\4c'): k = '4c'
            elif m_str.startswith('\\1a'): k = '1a'
            elif m_str.startswith('\\2a'): k = '2a'
            elif m_str.startswith('\\3a'): k = '3a'
            elif m_str.startswith('\\4a'): k = '4a'
            elif m_str.startswith('\\alpha'): k = 'alpha'
            elif m_str.startswith('\\fscx'): k = 'fscx'
            elif m_str.startswith('\\fscy'): k = 'fscy'
            elif m_str.startswith('\\frz') or m_str.startswith('\\fr'): k = 'frz'
            elif m_str.startswith('\\frx'): k = 'frx'
            elif m_str.startswith('\\fry'): k = 'fry'
            elif m_str.startswith('\\fax'): k = 'fax'
            elif m_str.startswith('\\fay'): k = 'fay'
            elif m_str.startswith('\\xbord'): k = 'xbord'
            elif m_str.startswith('\\ybord'): k = 'ybord'
            elif m_str.startswith('\\bord'): k = 'bord'
            elif m_str.startswith('\\xshad'): k = 'xshad'
            elif m_str.startswith('\\yshad'): k = 'yshad'
            elif m_str.startswith('\\shad'): k = 'shad'
            elif m_str.startswith('\\blur'): k = 'blur'
            elif m_str.startswith('\\be'): k = 'be'
            elif m_str.startswith('\\p'): k = 'p'
            elif m_str.startswith('\\q'): k = 'q'
            elif m_str.startswith('\\fn'): k = 'fn'
            elif m_str.startswith('\\fs'): k = 'fs'
            elif m_str.startswith('\\fsp'): k = 'fsp'
            elif m_str.startswith('\\b'): k = 'b'
            elif m_str.startswith('\\i'): k = 'i'
            elif m_str.startswith('\\u'): k = 'u'
            elif m_str.startswith('\\s'): k = 's'
            elif m_str.startswith('\\r'): k = 'r'
            else: k = m_str
            t_dict[k] = m_str
        return t_dict

    ret_dict = _parse_tag_dict(return_tags_str)
    port_dict = _parse_tag_dict(port_tags_str)

    # Las etiquetas del puerto Tags reemplazan a las de Return en caso de colisión
    ret_dict.update(port_dict)

    # Ordenar limpiamente: \an primero, \pos/\move, \org, colores, transformaciones, \p al final
    sorted_keys = sorted(ret_dict.keys(), key=lambda k: (
        0 if k == 'an' else
        1 if k in ('pos', 'move') else
        2 if k == 'org' else
        3 if k in ('1c', '2c', '3c', '4c', 'alpha', '1a', '2a', '3a', '4a') else
        9 if k == 'p' else 5
    ))

    return ''.join(ret_dict[k] for k in sorted_keys)


def _clean_key(k):
    s = str(k).lower().strip()
    s = s.replace('ñ', 'n').replace('º', '').replace('°', '').replace('(', '').replace(')', '').replace(',', '')
    s = s.replace('[', '').replace(']', '').replace('\\', '').replace('/', '_').replace('-', '_').replace('.', '')
    s = s.replace('ión', 'ion').replace('í', 'i').replace('á', 'a').replace('é', 'e').replace('ó', 'o').replace('ú', 'u')
    s = re.sub(r'\s+', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')

ALIAS_GROUPS = [
    ["text", "texto", "txt", "valor", "value", "string", "str"],
    ["delay", "delay_ms", "delay_line", "delay_inter_lineas", "retraso"],
    ["base", "base_ms", "tiempo_base"],
    ["density", "densidad"],
    ["redraw_dist", "redrawdist", "distorsion"],
    ["seed", "semilla"],
    ["scale", "escala", "scale_x", "scale_y"],
    ["shape", "forma", "drawing", "shp", "shape_texto"],
    ["font_name", "fuente", "fontname", "font"],
    ["font_size", "tamano", "fontsize", "size", "tamano_fuente"],
    ["bold", "negrita"],
    ["italic", "cursiva"],
    ["image_path", "ruta_img", "ruta_imagen", "img_path", "ruta"],
    ["step", "paso", "paso_muestreo"],
    ["alpha_threshold", "alpha", "umbral_alpha", "threshold", "umbral"],
    ["tag_name", "tag", "tag_opcional", "nombre_tag"],
    ["amp", "amplitud", "amplitud_valor_a", "valor_a"],
    ["freq", "frecuencia", "frecuencia_valor_b", "valor_b"],
    ["t_ms", "time", "tiempo", "tiempo_ms", "t", "t_01", "t_0_1"],
    ["p0", "p0_xy", "p0_x_y", "punto0"],
    ["p1", "p1_xy", "p1_x_y", "punto1"],
    ["p2", "p2_xy", "p2_x_y", "punto2"],
    ["p3", "p3_xy", "p3_x_y", "punto3"],
    ["progression_const", "constante", "constante_progresion"],
    ["fade_dur", "duracion_fade", "fade_ms", "fade"],
    ["max_added_time", "max_extra", "max_tiempo_anadido"],
    ["max_gap_threshold", "threshold", "threshold_brecha", "brecha"],
    ["dur", "duration", "duracion", "duracion_ms"],
    ["points", "puntos", "puntos_valores", "valores"],
    ["accel", "aceleracion", "accel_x", "aceleracion_x"],
    ["iterations", "iteraciones", "veces", "vueltas"],
    ["complexity", "complejidad"],
    ["condicion", "condition"],
    ["si_verdadero", "true_val", "verdadero"],
    ["si_falso", "false_val", "falso"],
    ["modo", "mode"],
    ["formato", "format", "fmt"],
    ["separador", "separator", "sep"],
    ["var_name", "nombre", "variable"],
    ["clave", "key"],
    ["x", "x_origen", "x0", "pos_x"],
    ["y", "y_origen", "y0", "pos_y"],
    ["angle", "angulo", "ang", "rot", "rotacion"],
    ["radius", "radio", "r"],
    ["prog", "progreso", "pct", "progreso_01", "progreso_0_1"],
    ["colors_str", "colors", "colores", "lista_colores", "lista_de_colores", "color_list"],
    ["anclaje", "anchor"],
    ["out_mode", "tipo_salida"],
    ["overlap", "sangrado"],
    ["offset", "offset_ms", "desplazamiento", "desfase"],
    ["st", "start_time", "start_time_ms", "inicio", "tiempo_inicio", "st_ms"],
    ["et", "end_time", "end_time_ms", "fin", "tiempo_fin", "et_ms"],
    ["ass_time", "ass_str", "time_str", "ass", "tiempo_ass"],
    ["ms", "time_ms", "t_ms", "milisegundos", "tiempo_milisegundos"],
    ["search", "buscar", "patron", "query"],
    ["replace", "reemplazar_por", "remplazo", "sustituto", "replacement"],
    ["start", "inicio", "pos_inicio"],
    ["length", "longitud", "len", "tamano_longitud"],
    ["gain", "ganancia", "vol", "volumen", "volumen_audio"],
    ["x", "pos_x", "x_val", "x_pos", "x_valor", "x / valor", "x (px)", "x1"],
    ["y", "pos_y", "y_val", "y_pos", "y_valor", "y / valor b", "y (px)", "y1"],
    ["val", "valor", "value", "v", "angle", "rot", "rot_z", "valor_b"]
]

PROP_ALIAS_MAP = {}
for _group in ALIAS_GROUPS:
    _clean_group = [_clean_key(_item) for _item in _group]
    for _item in _clean_group:
        PROP_ALIAS_MAP[_item] = _clean_group


def _get_prop_value(props, key, default=""):
    if not isinstance(props, dict):
        return default
    if key in props and props[key] is not None and str(props[key]).strip() != "":
        return props[key]

    ck = _clean_key(key)
    possible_keys = PROP_ALIAS_MAP.get(ck, [ck])

    for p, v in props.items():
        if v is not None and str(v).strip() != "":
            clean_p = _clean_key(p)
            if clean_p == ck or clean_p in possible_keys or ck in PROP_ALIAS_MAP.get(clean_p, []):
                return v

    if key in props:
        return props[key]
    return default


class ShapePresetsNamespace:
    """Helper namespace para exponer formas prediseñadas vía sintaxis shape.nombre (ej. shape.corazon, shape.circulo, shape.estrella_5t)."""
    def __getattr__(self, name):
        from nodes.shape_nodes import resolve_shape_value
        return resolve_shape_value(f"shape.{name}")

    def __getitem__(self, name):
        return getattr(self, name)

    def get(self, name, default=""):
        res = getattr(self, name)
        return res if res else default

    def __str__(self):
        return "ShapePresetsNamespace"


class FxContext:
    """Helper class para exponer variables de efectos (fx.pos_x, fx.pos_y, fx.i, fx.n, etc.)."""
    def __init__(self, ctx):
        self._ctx = ctx if isinstance(ctx, dict) else {}

    def __getattr__(self, name):
        if name in self._ctx:
            return self._ctx[name]
        if name == "shape":
            return ShapePresetsNamespace()
        if name.startswith("shape."):
            return getattr(ShapePresetsNamespace(), name[6:])
        fx_name = f"fx_{name}"
        if fx_name in self._ctx:
            return self._ctx[fx_name]
        if name in ("x", "pos_x"):
            return self._ctx.get("fx_pos_x", self._ctx.get("x", 0.0))
        if name in ("y", "pos_y"):
            return self._ctx.get("fx_pos_y", self._ctx.get("y", 0.0))
        if name in ("val_left", "left"):
            return self._ctx.get("val_left", getattr(self._ctx.get("active_unit"), "left", 0.0))
        if name in ("val_center", "center"):
            return self._ctx.get("val_center", getattr(self._ctx.get("active_unit"), "center", 0.0))
        if name in ("val_right", "right"):
            return self._ctx.get("val_right", getattr(self._ctx.get("active_unit"), "right", 0.0))
        if name in ("val_top", "top"):
            return self._ctx.get("val_top", getattr(self._ctx.get("active_unit"), "top", 0.0))
        if name in ("val_middle", "middle"):
            return self._ctx.get("val_middle", getattr(self._ctx.get("active_unit"), "middle", 0.0))
        if name in ("val_bottom", "bottom"):
            return self._ctx.get("val_bottom", getattr(self._ctx.get("active_unit"), "bottom", 0.0))
        if name in ("val_width", "width"):
            return self._ctx.get("val_width", getattr(self._ctx.get("active_unit"), "width", 0.0))
        if name in ("val_height", "height"):
            return self._ctx.get("val_height", getattr(self._ctx.get("active_unit"), "height", 0.0))
        if name in ("val_start", "val_st"):
            return self._ctx.get("val_start", 0.0)
        if name in ("val_end", "val_et"):
            return self._ctx.get("val_end", 0.0)
        if name in ("val_dur",):
            return self._ctx.get("val_dur", 0.0)
        if name in ("val_mid",):
            return self._ctx.get("val_mid", 0.0)
        if name in ("val_i",):
            return self._ctx.get("val_i", 1)
        if name in ("val_n",):
            return self._ctx.get("val_n", 1)
        if name == "i":
            return self._ctx.get("fx_i", self._ctx.get("i", 1))
        if name == "n":
            return self._ctx.get("fx_n", self._ctx.get("n", 1))
        if name in ("start_time", "st"):
            return self._ctx.get("fx_start_time", self._ctx.get("start_time", 0.0))
        if name in ("end_time", "et"):
            return self._ctx.get("fx_end_time", self._ctx.get("end_time", 0.0))
        if name in ("dur", "duration"):
            return self._ctx.get("fx_dur", self._ctx.get("dur", 0.0))
        if name == "align":
            return self._ctx.get("fx_align", 5)
        return self._ctx.get(name, 0.0)

    def __getitem__(self, name):
        return getattr(self, name)


def _eval_sys_var(var_name: Any, context: Any) -> Any:
    if not var_name:
        return ""
    if not isinstance(context, dict):
        context = {}

    var_str = str(var_name).strip()

    if var_str.lower().startswith("shape."):
        from nodes.shape_nodes import resolve_shape_value
        return resolve_shape_value(var_str, context)

    # Globales / Standalone
    if var_str == "frame_dur":
        return context.get("frame_dur", 40.0)
    if var_str == "ratio":
        return context.get("ratio", context.get("module", 0.0))

    active_unit = context.get("active_unit")
    active_line = context.get("active_line", context.get("line"))
    if not active_line and hasattr(active_unit, "line") and getattr(active_unit, "line", None):
        active_line = getattr(active_unit, "line")
    if not active_line and active_unit and hasattr(active_unit, "style_name"):
        active_line = active_unit

    # val_* variables (Kara Effector active unit geometry and timing)
    if var_str.startswith("val_"):
        attr_name = var_str[4:]
        if var_str in context:
            return context[var_str]
        if attr_name in ("left", "right", "center", "top", "middle", "bottom", "width", "height", "x", "y"):
            return getattr(active_unit, attr_name, 0.0) if active_unit else 0.0
        if attr_name in ("start", "st"):
            return getattr(active_unit, "start_time", 0.0) if active_unit else 0.0
        if attr_name in ("end", "et"):
            return getattr(active_unit, "end_time", 0.0) if active_unit else 0.0
        if attr_name == "dur":
            return getattr(active_unit, "dur", getattr(active_unit, "duration", 0.0)) if active_unit else 0.0
        if attr_name == "mid":
            st = getattr(active_unit, "start_time", 0.0) if active_unit else 0.0
            dur = getattr(active_unit, "dur", getattr(active_unit, "duration", 0.0)) if active_unit else 0.0
            return st + (dur / 2.0)
        if attr_name == "i":
            return getattr(active_unit, "i", 1) if active_unit else 1
        if attr_name == "n":
            return getattr(active_unit, "n", 1) if active_unit else 1

    # Normalizar alias l. -> line.
    lookup_str = var_str
    if lookup_str.startswith("l."):
        lookup_str = "line." + lookup_str[2:]

    # Normalizar style_name -> style
    if lookup_str == "line.style_name":
        lookup_str = "line.style"

    # FX variables
    if lookup_str.startswith("fx."):
        attr_name = lookup_str[3:]
        if attr_name == "start_time":
            return context.get("fx_start_time", context.get("start_time", getattr(active_unit, "start_time", 0.0)))
        if attr_name in ("end_time", "et"):
            return context.get("fx_end_time", context.get("end_time", getattr(active_unit, "end_time", 0.0)))
        if attr_name in ("dur", "duration"):
            return context.get("fx_dur", context.get("dur", getattr(active_unit, "dur", getattr(active_unit, "duration", 0.0))))
        if attr_name == "i":
            return context.get("fx_i", context.get("i", getattr(active_unit, "i", 1)))
        if attr_name == "n":
            return context.get("fx_n", context.get("n", getattr(active_unit, "n", 1)))
        if attr_name in ("x", "pos_x"):
            return context.get("fx_pos_x", context.get("x", getattr(active_unit, "x", 0.0)))
        if attr_name in ("y", "pos_y"):
            return context.get("fx_pos_y", context.get("y", getattr(active_unit, "y", 0.0)))
        if attr_name in ("module", "m"):
            return context.get("module", 0.0)
        return context.get(f"fx_{attr_name}", context.get(attr_name, 0.0))

    # Time variables
    if lookup_str.startswith("time."):
        time_type = lookup_str[5:]
        from nodes.time_nodes import time_lead_in, time_lead_out, time_middle_1, time_middle_2, time_loop_1, time_loop_2
        if time_type == "lead_in": return time_lead_in(context)
        if time_type == "lead_out": return time_lead_out(context)
        if time_type == "middle_1": return time_middle_1(context)
        if time_type == "middle_2": return time_middle_2(context)
        if time_type == "loop_1": return time_loop_1(context)
        if time_type == "loop_2": return time_loop_2(context)

    # Line / l. variables
    if lookup_str.startswith("line."):
        attr_name = lookup_str[5:]
        target_obj = active_line if active_line else active_unit
        if not target_obj:
            return ""
        if attr_name == "text":
            return getattr(target_obj, "text_stripped", getattr(target_obj, "text", ""))
        if attr_name in ("dur", "duration"):
            return getattr(target_obj, "dur", getattr(target_obj, "duration", 0))
        if attr_name == "style":
            return getattr(target_obj, "style", getattr(target_obj, "style_name", "Default"))
        if hasattr(target_obj, attr_name):
            val = getattr(target_obj, attr_name)
            return val() if callable(val) else val
        styleref = getattr(target_obj, "styleref", None)
        if styleref and hasattr(styleref, attr_name):
            val = getattr(styleref, attr_name)
            return val() if callable(val) else val
        return ""

    # Syl variables
    if lookup_str.startswith("syl."):
        attr_name = lookup_str[4:]
        target_obj = context.get("syl", active_unit)
        if not target_obj: return ""
        if attr_name == "text":
            return getattr(target_obj, "text_stripped", getattr(target_obj, "text", ""))
        if attr_name in ("dur", "duration"):
            return getattr(target_obj, "dur", getattr(target_obj, "duration", 0))
        if hasattr(target_obj, attr_name):
            val = getattr(target_obj, attr_name)
            return val() if callable(val) else val
        return ""

    # Char variables
    if lookup_str.startswith("char."):
        attr_name = lookup_str[5:]
        target_obj = context.get("char", active_unit)
        if not target_obj: return ""
        if attr_name in ("dur", "duration"):
            return getattr(target_obj, "dur", getattr(target_obj, "duration", 0))
        if hasattr(target_obj, attr_name):
            val = getattr(target_obj, attr_name)
            return val() if callable(val) else val
        return ""

    # Word variables
    if lookup_str.startswith("word."):
        attr_name = lookup_str[5:]
        target_obj = context.get("word", active_unit)
        if not target_obj: return ""
        if attr_name == "text":
            return getattr(target_obj, "text_stripped", getattr(target_obj, "text", ""))
        if attr_name in ("dur", "duration"):
            return getattr(target_obj, "dur", getattr(target_obj, "duration", 0))
        if hasattr(target_obj, attr_name):
            val = getattr(target_obj, attr_name)
            return val() if callable(val) else val
        return ""

    # Meta variables
    if lookup_str.startswith("meta."):
        attr_name = lookup_str[5:]
        if attr_name == "res_x":
            proc = context.get("processor")
            return proc.res_x if proc else context.get("res_x", 1280)
        if attr_name == "res_y":
            proc = context.get("processor")
            return proc.res_y if proc else context.get("res_y", 720)

    # Standalone variables / Bucles fallbacks
    if lookup_str in context:
        return context[lookup_str]
    if active_unit and hasattr(active_unit, lookup_str):
        val = getattr(active_unit, lookup_str)
        return val() if callable(val) else val

    return ""

_EVAL_EXPR_CACHE = {}
_STATIC_EVAL_GLOBALS = None

def _get_static_eval_globals():
    global _STATIC_EVAL_GLOBALS
    if _STATIC_EVAL_GLOBALS is not None:
        return _STATIC_EVAL_GLOBALS
    
    import math
    safe_builtins = {
        "min": min, "max": max, "abs": abs, "round": round,
        "int": int, "float": float, "pow": pow, "sum": sum,
        "len": len, "str": str, "bool": bool
    }
    g = {"math": math, "__builtins__": safe_builtins}
    for k, v in safe_builtins.items():
        g[k] = v
    for fn in ("sin", "cos", "tan", "sqrt", "ceil", "floor", "atan2", "degrees", "radians", "hypot", "log", "exp", "pi"):
        if hasattr(math, fn):
            g[fn] = getattr(math, fn)
    from decorators import NODE_REGISTRY
    for k, v in NODE_REGISTRY.items():
        fn_name = v.__name__
        g[fn_name] = v

    from nodes.audio_nodes import audio_rms, audio_peak, audio_band, audio_fft
    g["audio_rms"] = audio_rms
    g["audio_peak"] = audio_peak
    g["audio_band"] = audio_band
    g["audio_fft"] = audio_fft

    from nodes.math_nodes import math_random_master
    g["R"] = math_random_master
    g["Rs"] = math_random_master
    g["Rc"] = math_random_master
    g["shape"] = ShapePresetsNamespace()

    _STATIC_EVAL_GLOBALS = g
    return _STATIC_EVAL_GLOBALS


class AttrDict(dict):
    """Permite acceso por atributo (.campo) a diccionarios en expresiones de eval()."""
    def __getattr__(self, name):
        if name in self:
            val = self[name]
            return AttrDict(val) if isinstance(val, dict) else val
        raise AttributeError(f"'dict' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        self[name] = value


def _eval_num_expr(val, context=None, default=0.0):
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if not val_str:
        return default

    # Convertir formato decimal con coma (ej. "0,5" o "-3,14") a float si es literal simple
    m_comma = re.match(r"^([+-]?\d+),(\d+)$", val_str)
    if m_comma:
        try:
            return float(f"{m_comma.group(1)}.{m_comma.group(2)}")
        except Exception:
            pass

    # Convertir formato hex ASS (&HAA& o &HAA) a decimal float si es un valor literal simple
    m_hex = re.match(r"^&[hH]([0-9a-fA-F]+)&?$", val_str)
    if m_hex:
        try:
            return float(int(m_hex.group(1), 16))
        except Exception:
            pass

    try:
        return float(val_str)
    except (ValueError, TypeError):
        pass

    try:
        code_obj = _EVAL_EXPR_CACHE.get(val_str)
        if code_obj is None:
            # Reemplazar tokens hexadecimales &H...& por 0x... para compatibilidad con eval()
            clean_expr = re.sub(r'&[hH]([0-9a-fA-F]+)&?', r'0x\1', val_str)
            code_obj = compile(clean_expr, "<eval_expr>", "eval")
            _EVAL_EXPR_CACHE[val_str] = code_obj

        eval_globals = _get_static_eval_globals()
        eval_locals = dict(context) if isinstance(context, dict) else {}
        for k, v in list(eval_locals.items()):
            if isinstance(v, dict) and not isinstance(v, AttrDict):
                eval_locals[k] = AttrDict(v)
        
        # Inyectar funciones adaptadoras al contexto local para closure de contexto
        eval_locals["audio_rms"] = lambda *args, **kwargs: eval_globals["audio_rms"](*args, context=context, **kwargs)
        eval_locals["audio_peak"] = lambda *args, **kwargs: eval_globals["audio_peak"](*args, context=context, **kwargs)
        eval_locals["audio_band"] = lambda *args, **kwargs: eval_globals["audio_band"](*args, context=context, **kwargs)
        eval_locals["audio_fft"] = lambda *args, **kwargs: eval_globals["audio_fft"](*args, context=context, **kwargs)
        eval_locals["R"] = lambda min_v=0, max_v=100, step_v=1: eval_globals["R"](context, modo="R", min_val=min_v, max_val=max_v, step=step_v)
        eval_locals["Rs"] = lambda min_v=0, max_v=100: eval_globals["Rs"](context, modo="Rs", min_val=min_v, max_val=max_v)
        eval_locals["Rc"] = lambda min_v=0, max_v=100: eval_globals["Rc"](context, modo="Rc", min_val=min_v, max_val=max_v)

        if "active_unit" in eval_locals and eval_locals["active_unit"]:
            unit_obj = eval_locals["active_unit"]
            if "syl" not in eval_locals or eval_locals["syl"] is None:
                eval_locals["syl"] = unit_obj
            if "line" not in eval_locals and hasattr(unit_obj, "line") and unit_obj.line:
                eval_locals["line"] = unit_obj.line

        if "line" in eval_locals and ("l" not in eval_locals or eval_locals["l"] is None):
            eval_locals["l"] = eval_locals["line"]

        if "maxloop" not in eval_locals:
            eval_locals["maxloop"] = eval_locals.get("j_max", eval_locals.get("fx_n", 1))
        if "max_loop" not in eval_locals:
            eval_locals["max_loop"] = eval_locals.get("j_max", eval_locals.get("fx_n", 1))
        if "j" not in eval_locals and "fx_i" in eval_locals:
            eval_locals["j"] = eval_locals["fx_i"]
        if "j_max" not in eval_locals and "fx_n" in eval_locals:
            eval_locals["j_max"] = eval_locals["fx_n"]

        if "fx" not in eval_locals or eval_locals["fx"] is None or not isinstance(eval_locals["fx"], FxContext):
            eval_locals["fx"] = FxContext(eval_locals)

        res = eval(code_obj, eval_globals, eval_locals)
        return float(res) if res is not None else float(default)
    except Exception:
        return default


_PROFILER_ENABLED = False
_GLOBAL_ACTIVE_EXECUTOR = None
_WORKER_LINE_COUNTER = None
_WORKER_CANCEL_FLAG = None

def _worker_init(line_counter, cancel_flag):
    global _WORKER_LINE_COUNTER, _WORKER_CANCEL_FLAG
    _WORKER_LINE_COUNTER = line_counter
    _WORKER_CANCEL_FLAG = cancel_flag

def abort_global_multiprocessing():
    global _GLOBAL_ACTIVE_EXECUTOR
    if _GLOBAL_ACTIVE_EXECUTOR is not None:
        try:
            _GLOBAL_ACTIVE_EXECUTOR.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        _GLOBAL_ACTIVE_EXECUTOR = None


class GraphEngine:
    def __init__(self, graph_data, rx=1280, ry=720, fd=41.708, default_audio_source=""):
        self.raw_graph = graph_data
        self.nodes = {n['id']: n for n in graph_data.get('nodes', [])}
        self.links = graph_data.get('links', [])
        self.all_generated_lines = []
        self.rx, self.ry, self.fd = rx, ry, fd
        self.default_audio_source = default_audio_source
        self.is_cancelled = False
        self._cancel_check_counter = 0
        self.memory = {}
        self._has_audio_nodes = any(
            'audio' in str(n.get('type', '')).lower() or 
            'waveform' in str(n.get('type', '')).lower() or 
            'modulador' in str(n.get('type', '')).lower()
            for n in self.nodes.values()
        )

    def remember(self, key, val):
        self.memory[str(key)] = val
        return val

    def recall(self, key, default=""):
        return self.memory.get(str(key), default)

    def is_port_connected(self, target_node, input_index):
        inputs = target_node.get('inputs', [])
        if len(inputs) <= input_index: return False
        inp = inputs[input_index]
        return bool(inp.get('link') is not None or (isinstance(inp.get('links'), list) and len(inp.get('links')) > 0))

    def get_input_value(self, target_node, input_index, context):
        if not self.is_port_connected(target_node, input_index):
            inputs = target_node.get('inputs', [])
            if input_index < len(inputs):
                inp = inputs[input_index]
                p_name = inp.get('property') or inp.get('name')
                props = target_node.get('properties', {})
                if p_name:
                    val = _get_prop_value(props, p_name, default="")
                    if val != "":
                        if str(val).strip().lower().startswith("shape."):
                            from nodes.shape_nodes import resolve_shape_value
                            return resolve_shape_value(val, context)
                        return str(val)
                if inp.get('name'):
                    val = _get_prop_value(props, inp.get('name'), default="")
                    if val != "":
                        if str(val).strip().lower().startswith("shape."):
                            from nodes.shape_nodes import resolve_shape_value
                            return resolve_shape_value(val, context)
                        return str(val)
                if 'value' in inp and inp['value'] is not None and str(inp['value']).strip() != "":
                    raw_val = str(inp['value']).strip()
                    if raw_val.lower().startswith("shape."):
                        from nodes.shape_nodes import resolve_shape_value
                        return resolve_shape_value(raw_val, context)
                    return raw_val
            return ""
        inputs = target_node.get('inputs', [])
        if input_index < len(inputs):
            inp = inputs[input_index]
            link_ids = []
            if isinstance(inp.get('links'), list) and len(inp['links']) > 0:
                link_ids = inp['links']
            elif inp.get('link') is not None:
                link_ids = [inp['link']]

            results = []
            for l_id in link_ids:
                link = next((l for l in self.links if l[0] == l_id), None)
                if link:
                    val = self.evaluate_data_node(link[1], context, output_slot_index=link[2])
                    if val is not None and str(val) != "":
                        results.append(str(val))
            if len(results) > 1:
                return "".join(results)
            elif len(results) == 1:
                return results[0]
        return ""

    def bind_active_unit(self, context, unit, is_noblank=True):
        context['active_unit'] = unit
        context['default_audio_source'] = self.default_audio_source
        if unit:
            if not context.get('syl'):
                context['syl'] = getattr(unit, 'syl', unit)
            if not context.get('sili'):
                context['sili'] = context['syl']
            if not context.get('char') and hasattr(unit, 'char'):
                context['char'] = getattr(unit, 'char', None)
            if not context.get('word') and hasattr(unit, 'word'):
                context['word'] = getattr(unit, 'word', None)

            if is_noblank:
                ci_val = int(getattr(unit, 'ci', getattr(unit, 'i', 1)))
                cn_val = int(getattr(unit, 'cn', getattr(unit, 'n', 1)))
                unit.i = ci_val
                unit.n = cn_val
                context['i'] = ci_val
                context['n'] = cn_val
                context['fx_i'] = ci_val
                context['fx_n'] = cn_val
            else:
                i_val = int(getattr(unit, 'i', 1))
                n_val = int(getattr(unit, 'n', 1))
                context['i'] = i_val
                context['n'] = n_val
                context['fx_i'] = i_val
                context['fx_n'] = n_val

            u_center = float(getattr(unit, 'center', 0.0))
            u_middle = float(getattr(unit, 'middle', 0.0))
            u_left = float(getattr(unit, 'left', u_center))
            u_right = float(getattr(unit, 'right', u_center))
            u_top = float(getattr(unit, 'top', u_middle))
            u_bottom = float(getattr(unit, 'bottom', u_middle))
            u_width = float(getattr(unit, 'width', max(0.0, u_right - u_left)))
            u_height = float(getattr(unit, 'height', max(0.0, u_bottom - u_top)))
            u_x = float(getattr(unit, 'x', u_center))
            u_y = float(getattr(unit, 'y', u_middle))

            final_x = u_center if u_center != 0.0 else u_x
            final_y = u_middle if u_middle != 0.0 else u_y
            context['fx_pos_x'] = round(final_x, 3)
            context['fx_pos_y'] = round(final_y, 3)
            context['x'] = final_x
            context['y'] = final_y
            context['fx_start_time'] = getattr(unit, 'start_time', 0)
            context['fx_end_time'] = getattr(unit, 'end_time', 0)
            context['fx_dur'] = getattr(unit, 'dur', getattr(unit, 'duration', 0))

            # Variables val_* de unidad activa idénticas a Kara Effector
            context['val_left'] = round(u_left, 3)
            context['val_center'] = round(u_center, 3)
            context['val_right'] = round(u_right, 3)
            context['val_top'] = round(u_top, 3)
            context['val_middle'] = round(u_middle, 3)
            context['val_bottom'] = round(u_bottom, 3)
            context['val_width'] = round(u_width, 3)
            context['val_height'] = round(u_height, 3)
            context['val_x'] = round(final_x, 3)
            context['val_y'] = round(final_y, 3)

        line_obj = context.get('line')
        line_st = float(getattr(line_obj, 'start_time', 0.0)) if line_obj else 0.0
        line_et = float(getattr(line_obj, 'end_time', 0.0)) if line_obj else 0.0
        context['line_start_time'] = line_st
        context['line_end_time'] = line_et
        context['line_dur'] = max(0.0, line_et - line_st)

        unit_st = float(getattr(unit, 'start_time', line_st)) if unit else line_st
        unit_et = float(getattr(unit, 'end_time', line_et)) if unit else line_et
        unit_dur = float(getattr(unit, 'dur', getattr(unit, 'duration', max(0.0, unit_et - unit_st)))) if unit else max(0.0, unit_et - unit_st)

        context['start_time'] = unit_st
        context['end_time'] = unit_et
        context['st'] = unit_st
        context['et'] = unit_et
        context['dur'] = unit_dur
        context['duration'] = unit_dur
        context['val_start'] = unit_st
        context['val_end'] = unit_et
        context['val_dur'] = unit_dur
        context['val_mid'] = round(unit_st + (unit_dur / 2.0), 3)
        context['val_i'] = context.get('i', 1)
        context['val_n'] = context.get('n', 1)
        context['syl_start_time'] = float(getattr(getattr(unit, 'syl', unit), 'start_time', unit_st))
        context['syl_end_time'] = float(getattr(getattr(unit, 'syl', unit), 'end_time', unit_et))
        context['fx_align'] = 5
        if 'line' in context and context['line']:
            context['l'] = context['line']
        context['fx'] = FxContext(context)
        context['engine'] = self
        context['remember'] = self.remember
        context['recall'] = self.recall
        self._update_module_context(context)
        return context

    def _update_module_context(self, context):
        j = float(context.get('j', context.get('fx_i', 1)))
        maxj = float(context.get('j_max', context.get('fx_n', context.get('maxj', 1))))
        
        module = round((j - 1.0) / (maxj - 1.0), 4) if maxj > 1 else 0.0
        context['module'] = module
        context['m'] = module
        return context

    def _apply_defaults(self, active_unit, layer_raw, st_raw, et_raw, tags_raw, return_raw, context=None):
        default_st = context.get('start_time', getattr(active_unit, 'start_time', 0)) if (context and 'start_time' in context) else getattr(active_unit, 'start_time', 0)
        default_et = context.get('end_time', getattr(active_unit, 'end_time', 0)) if (context and 'end_time' in context) else getattr(active_unit, 'end_time', 0)
        layer = _to_int_or_default(layer_raw, 0, context=context)
        st = _to_int_or_default(st_raw, default_st, context=context)
        et = _to_int_or_default(et_raw, default_et, context=context)

        tags_raw = "" if _is_empty_value(tags_raw) else str(tags_raw).strip()
        return_raw = getattr(active_unit, 'text_stripped', '') if _is_empty_value(return_raw) else str(return_raw).strip()

        # If return_raw contains override tags or \clip / \iclip, extract inner tags cleanly
        if return_raw:
            if '{' in return_raw and '}' in return_raw:
                for inner in re.findall(r'\{([^}]+)\}', return_raw):
                    tags_raw = (tags_raw + inner).strip()
                return_raw = re.sub(r'\{[^}]+\}', '', return_raw).strip()

            m_clips = re.findall(r'\\i?clip\([^)]+\)', return_raw)
            for clip_str in m_clips:
                tags_raw = (tags_raw + clip_str).strip()
                return_raw = return_raw.replace(clip_str, '').strip()

        # If return_raw was solely a clip tag and is now empty, restore active_unit text if available
        if not return_raw and active_unit:
            return_raw = getattr(active_unit, 'text_stripped', getattr(active_unit, 'text', ''))

        # Detect ASSDraw vector shape in Return and inject \p1 tag automatically if missing
        if return_raw and (return_raw.startswith("m ") or re.search(r'\bm\s+-?\d+', return_raw)):
            if not re.search(r'\\p\d+', tags_raw):
                tags_raw += "\\p1"

        ctx = context if isinstance(context, dict) else {}
        origin_align = 5
        try:
            origin_align = int(ctx.get('origin_align', 5))
            if origin_align < 1 or origin_align > 9:
                origin_align = 5
        except Exception:
            origin_align = 5

        # Inyección de \\an5 por defecto si no existe ningún tag \\an ni \\move
        if not _AN_RE.search(tags_raw) and not _MOVE_RE.search(tags_raw): 
            tags_raw = "\\an5" + tags_raw

        # Normalize duplicate backslashes in tags_raw (e.g. \\1c -> \1c)
        tags_raw = re.sub(r'\\{2,}', r'\\', tags_raw)
        
        # Determinar coordenadas de origen base según origin_align y active_unit / context
        u_left = float(ctx.get('val_left', getattr(active_unit, 'left', getattr(active_unit, 'center', 0.0)) if active_unit else 0.0))
        u_center = float(ctx.get('val_center', getattr(active_unit, 'center', 0.0) if active_unit else 0.0))
        u_right = float(ctx.get('val_right', getattr(active_unit, 'right', getattr(active_unit, 'center', 0.0)) if active_unit else 0.0))
        u_top = float(ctx.get('val_top', getattr(active_unit, 'top', getattr(active_unit, 'middle', 0.0)) if active_unit else 0.0))
        u_middle = float(ctx.get('val_middle', getattr(active_unit, 'middle', 0.0) if active_unit else 0.0))
        u_bottom = float(ctx.get('val_bottom', getattr(active_unit, 'bottom', getattr(active_unit, 'middle', 0.0)) if active_unit else 0.0))

        if origin_align in (7, 4, 1):
            default_orig_x = u_left
        elif origin_align in (9, 6, 3):
            default_orig_x = u_right
        else:
            default_orig_x = u_center

        if origin_align in (7, 8, 9):
            default_orig_y = u_top
        elif origin_align in (1, 2, 3):
            default_orig_y = u_bottom
        else:
            default_orig_y = u_middle

        def _fmt_coord(v):
            try:
                fv = float(v)
                return f"{fv:.2f}".rstrip('0').rstrip('.') if (fv % 1 != 0) else f"{int(fv)}"
            except Exception:
                return str(v)

        # Handle \pos tag formatting
        if ctx.get('pos_overridden'):
            pos_x = ctx.get('x', default_orig_x)
            pos_y = ctx.get('y', default_orig_y)
            pos_str = f"\\pos({_fmt_coord(pos_x)},{_fmt_coord(pos_y)})"
            if _POS_RE.search(tags_raw):
                tags_raw = _POS_RE.sub(lambda m: pos_str, tags_raw)
            elif not _MOVE_RE.search(tags_raw):
                tags_raw += pos_str
        elif not _POS_RE.search(tags_raw) and not _MOVE_RE.search(tags_raw):
            pos_x = default_orig_x
            pos_y = default_orig_y
            tags_raw += f"\\pos({_fmt_coord(pos_x)},{_fmt_coord(pos_y)})"

        # Handle \org tag formatting inside the tag group
        if ctx.get('has_org'):
            org_x = ctx.get('org_x', ctx.get('x', default_orig_x))
            org_y = ctx.get('org_y', ctx.get('y', default_orig_y))
            org_str = f"\\org({_fmt_coord(org_x)},{_fmt_coord(org_y)})"
            if re.search(r'\\org\([^)]*\)', tags_raw):
                tags_raw = re.sub(r'\\org\([^)]*\)', lambda m: org_str, tags_raw)
            else:
                tags_raw = re.sub(r'(\\pos\([^)]*\))', lambda m: m.group(1) + org_str, tags_raw)
        elif ctx.get('has_org') is False and re.search(r'\\org\([^)]*\)', tags_raw):
            tags_raw = re.sub(r'\\org\([^)]*\)', '', tags_raw)

        return layer, st, et, tags_raw, return_raw

    def trace_loop_chain(self, output_node):
        chain = []
        current_node = output_node
        input_port_index = 0 
        visited = set()
        
        while current_node and current_node['id'] not in visited:
            visited.add(current_node['id'])
            if not self.is_port_connected(current_node, input_port_index):
                found_idx = None
                for idx, inp in enumerate(current_node.get('inputs', [])):
                    if self.is_port_connected(current_node, idx):
                        found_idx = idx
                        break
                if found_idx is not None:
                    input_port_index = found_idx
                else:
                    break

            inputs = current_node.get('inputs', [])
            if input_port_index >= len(inputs):
                break
            link_id = inputs[input_port_index].get('link')
            link = next((l for l in self.links if l[0] == link_id), None)
            if not link:
                break
            
            origin_node = self.nodes.get(link[1])
            if not origin_node:
                break
            node_type = origin_node.get('type', '')
            props = origin_node.get('properties', {})

            if node_type in ["Loops/Main Loop", "Main Loop"]:
                chain.append({'type': 'base', 'val': props.get('iterador', 'syl')})
                break 
            elif node_type in ["Loops/MaxLoop", "MaxLoop"]:
                chain.append({
                    'type': 'maxloop',
                    'node': origin_node,
                    'modo': props.get('modo', props.get('mode', 'Normal')),
                    'val': props.get('veces', '1'),
                    'step_ms': props.get('step_ms', props.get('paso_ms', props.get('paso', '41.7'))),
                    'start_time': props.get('start_time', props.get('inicio', '')),
                    'end_time': props.get('end_time', props.get('fin', '')),
                    'var_name': props.get('var_name', 'j')
                })
                current_node = origin_node
                input_port_index = 0
            elif node_type in ["Variables/Define Vars", "Define Vars"]:
                chain.append({'type': 'set_vars', 'val': props.get('variables', '')})
                current_node = origin_node
                input_port_index = 0
            elif node_type in ["System/Script Code", "Script Code"]:
                chain.append({'type': 'code_script', 'node': origin_node})
                current_node = origin_node
                input_port_index = 0
            else:
                current_node = origin_node
                input_port_index = 0

        res_chain = list(reversed(chain))
        has_base = any(c.get('type') == 'base' for c in res_chain)
        if not has_base:
            res_chain.insert(0, {'type': 'base', 'val': 'syl'})

        return res_chain

    def evaluate_data_node(self, node_id, context, output_slot_index=0):
        if _PROFILER_ENABLED:
            _t0 = time.perf_counter()
            res = self._evaluate_data_node_body(node_id, context, output_slot_index)
            _dur = time.perf_counter() - _t0
            try:
                from pyxis_profiler import PyxisProfiler
                prof = PyxisProfiler.get_active()
                if prof:
                    prof.record_node_eval(node_id, self.nodes[node_id].get('type', ''), _dur)
            except Exception:
                pass
            return res
        return self._evaluate_data_node_body(node_id, context, output_slot_index)

    def _evaluate_data_node_body(self, node_id, context, output_slot_index=0):
        node = self.nodes[node_id]
        node_type = node['type']
        props = node.get('properties', {})
        if '/' in node_type:
            category, name = node_type.rsplit('/', 1)
        else:
            category, name = "", node_type
        
        # ---------------------------------------------------------------------
        # EVALUADORES DE NODOS CON LÓGICA ESPECIAL / ENTRADAS DINÁMICAS
        # ---------------------------------------------------------------------
        if node_type in ["MultiTag"]:
            tag_type = str(_get_prop_value(props, "tag_type", _get_prop_value(props, "tag", "pos"))).strip()
            from nodes.tag_nodes import tag_master
            kwargs = {str(k): v for k, v in props.items()}
            kwargs.pop("tag_type", None)
            inputs_list = node.get("inputs", [])
            for i, input_obj in enumerate(inputs_list):
                input_name = input_obj.get("name", "")
                prop_key = input_obj.get("property") or input_name
                val = self.get_input_value(node, i, context)
                if val == "":
                    prop_val = str(_get_prop_value(props, prop_key, _get_prop_value(props, input_name, ""))).strip()
                    if prop_val == "" and "value" in input_obj and input_obj["value"] is not None:
                        prop_val = str(input_obj["value"]).strip()
                    if prop_val != "":
                        val = prop_val
                if val != "":
                    if input_name:
                        kwargs[str(input_name)] = val
                    if prop_key:
                        kwargs[str(prop_key)] = val
                    kwargs[str(i)] = val
                    kwargs[f"in_{i}"] = val
                    kwargs[f"in{i+1}"] = val
            return tag_master(context, tag_type=tag_type, **kwargs)

        elif node_type in ["MultiRandom"]:
            modo = str(_get_prop_value(props, "modo", _get_prop_value(props, "mode", "R"))).strip()
            
            inputs_list = node.get("inputs", [])
            connected_vals = {}
            for i, input_obj in enumerate(inputs_list):
                input_name = input_obj.get("name", "")
                val = self.get_input_value(node, i, context)
                if val != "":
                    connected_vals[input_name] = val
                    connected_vals[i] = val
            
            def get_rnd_param(name, prop_key, pos_idx, default):
                if name in connected_vals:
                    return connected_vals[name]
                if prop_key in connected_vals:
                    return connected_vals[prop_key]
                if pos_idx >= 0 and pos_idx in connected_vals:
                    return connected_vals[pos_idx]
                return _get_prop_value(props, prop_key, _get_prop_value(props, name, default))

            min_val = get_rnd_param("Min", "min", 0 if modo not in ("Re",) else -1, "0")
            max_val = get_rnd_param("Max", "max", 1 if modo not in ("Re", "Rbool") else -1, "100")
            step = get_rnd_param("Step", "step", 2 if modo not in ("Re", "Rfake", "Rcolor", "Rbool") else -1, "1")
            options = get_rnd_param("Options", "options", 0 if modo == "Re" else -1, "")
            counter = get_rnd_param("Contador", "counter", 2 if modo == "Rfake" else -1, "")
            
            from nodes.math_nodes import math_random_master
            return str(math_random_master(context, modo=modo, min_val=min_val, max_val=max_val, step=step, options=options, counter=counter))

        elif node_type in ["Math"]:
            try:
                inputs_list = node.get("inputs", [])
                kwargs = {}
                for i, inp_obj in enumerate(inputs_list):
                    inp_name = inp_obj.get("name", "")
                    inp_prop = inp_obj.get("property") or inp_name
                    val = self.get_input_value(node, i, context)
                    if val == "":
                        prop_val = str(_get_prop_value(props, inp_prop, _get_prop_value(props, inp_name, ""))).strip()
                        if prop_val == "" and "value" in inp_obj and inp_obj["value"] is not None:
                            prop_val = str(inp_obj["value"]).strip()
                        val = prop_val
                    if val != "":
                        if inp_name:
                            kwargs[str(inp_name)] = val
                        if inp_prop:
                            kwargs[str(inp_prop)] = val

                for k, v in props.items():
                    if k not in kwargs:
                        kwargs[k] = v

                from nodes.math_nodes import eval_math_node
                res_num = eval_math_node(context, **kwargs)
                if isinstance(res_num, (int, float)):
                    if float(res_num).is_integer():
                        return str(int(res_num))
                    return f"{res_num:.4f}".rstrip('0').rstrip('.')
                return str(res_num)
            except Exception as e:
                import traceback
                print(f"[Pyxis Engine Error] Math node evaluation failed: {e}")
                traceback.print_exc()
                return "0"

        elif node_type in ["Text"]:
            try:
                inputs_list = node.get("inputs", [])
                kwargs = {}
                for i, inp_obj in enumerate(inputs_list):
                    inp_name = inp_obj.get("name", "")
                    inp_prop = inp_obj.get("property") or inp_name
                    val = self.get_input_value(node, i, context)
                    if val == "":
                        prop_val = str(_get_prop_value(props, inp_prop, _get_prop_value(props, inp_name, ""))).strip()
                        if prop_val == "" and "value" in inp_obj and inp_obj["value"] is not None:
                            prop_val = str(inp_obj["value"]).strip()
                        val = prop_val
                    if val != "":
                        if inp_name:
                            kwargs[str(inp_name)] = val
                        if inp_prop:
                            kwargs[str(inp_prop)] = val

                for k, v in props.items():
                    if k not in kwargs:
                        kwargs[k] = v

                from nodes.text_nodes import eval_text_node
                return str(eval_text_node(context, **kwargs))
            except Exception as e:
                import traceback
                print(f"[Pyxis Engine Error] Text node evaluation failed: {e}")
                traceback.print_exc()
                return ""

        elif node_type in ["Shape/Shapes Library", "Shapes Library"]:
            try:
                inputs_list = node.get("inputs", [])
                kwargs = {}
                for i, inp_obj in enumerate(inputs_list):
                    inp_name = inp_obj.get("name", "")
                    inp_prop = inp_obj.get("property") or inp_name
                    val = self.get_input_value(node, i, context)
                    if val == "":
                        prop_val = str(_get_prop_value(props, inp_prop, _get_prop_value(props, inp_name, ""))).strip()
                        if prop_val == "" and "value" in inp_obj and inp_obj["value"] is not None:
                            prop_val = str(inp_obj["value"]).strip()
                        val = prop_val
                    if val != "":
                        if inp_name:
                            kwargs[str(inp_name)] = val
                        if inp_prop:
                            kwargs[str(inp_prop)] = val

                for k, v in props.items():
                    if k not in kwargs:
                        kwargs[k] = v

                from nodes.shape_nodes import eval_shapes_lib_node
                return str(eval_shapes_lib_node(context, **kwargs))
            except Exception as e:
                import traceback
                print(f"[Pyxis Engine Error] Shapes Lib node evaluation failed: {e}")
                traceback.print_exc()
                return ""

        elif node_type in ["Functions/Conditioner", "Conditioner"]:
            cond_raw = self.get_input_value(node, 0, context)
            if cond_raw == "": cond_raw = _get_prop_value(props, "condicion", _get_prop_value(props, "condition", "True"))
            si_verdadero = self.get_input_value(node, 1, context)
            if si_verdadero == "": si_verdadero = _get_prop_value(props, "si_verdadero", _get_prop_value(props, "true_val", ""))
            si_falso = self.get_input_value(node, 2, context)
            if si_falso == "": si_falso = _get_prop_value(props, "si_falso", _get_prop_value(props, "false_val", ""))
            from nodes.tag_nodes import node_condicionador
            return str(node_condicionador(context, condicion=cond_raw, si_verdadero=si_verdadero, si_falso=si_falso))

        elif node_type in ["Dynamic Format"]:
            try:
                fmt = str(_get_prop_value(props, "Formato", "%s"))
                inputs_list = node.get('inputs', [])
                inputs_count = len(inputs_list)

                values = []
                for i in range(inputs_count):
                    val = self.get_input_value(node, i, context)
                    if val is None or str(val) == "":
                        prop_name = f"In{i + 1}"
                        val = props.get(prop_name, "")
                    values.append(str(val) if val is not None else "")

                if not values and "%" not in fmt:
                    return fmt

                specifiers = re.findall(r'%[0-9.-]*[sdfixX]', fmt)
                if specifiers:
                    converted_values = []
                    for j, spec in enumerate(specifiers):
                        val_str = values[j] if j < len(values) else ""
                        if spec.endswith(('d', 'i', 'x', 'X')):
                            try:
                                converted_values.append(int(float(_eval_num_expr(val_str, context, 0))))
                            except Exception:
                                converted_values.append(0)
                        elif spec.endswith('f'):
                            try:
                                converted_values.append(float(_eval_num_expr(val_str, context, 0.0)))
                            except Exception:
                                converted_values.append(0.0)
                        else:
                            converted_values.append(str(val_str))

                    while len(converted_values) < len(specifiers):
                        converted_values.append("")

                    try:
                        return fmt % tuple(converted_values[:len(specifiers)])
                    except Exception:
                        pass

                # Fallback secuencial para %s
                res = fmt
                for val in values:
                    if "%s" in res:
                        res = res.replace("%s", str(val), 1)
                    else:
                        break
                return res
            except Exception as e:
                return f"[Err Format: {e}]"

        elif node_type in ["System/Script Code", "Script Code"]:
            script = props.get("script", "")
            lenguaje = props.get("lenguaje", "Python")
            inputs_list = node.get("inputs", [])
            inputs_map = {}
            for idx in range(1, 17):
                inputs_map[f"in{idx}"] = ""
                inputs_map[f"in_{idx}"] = ""

            data_port_idx = 1
            for i, input_obj in enumerate(inputs_list):
                input_name = input_obj.get("name", "")
                if input_name in ["Loop In", "In (bucle)", "Loop / Domain", "bucle", "Loop", "Bucle", "Bucle In"]:
                    continue
                val = self.get_input_value(node, i, context)
                if val == "":
                    val = str(_get_prop_value(props, input_name, "")).strip()
                if input_name:
                    inputs_map[input_name] = val
                    inputs_map[input_name.lower()] = val
                inputs_map[f"in{data_port_idx}"] = val
                inputs_map[f"in_{data_port_idx}"] = val
                data_port_idx += 1

            from nodes.code_nodes import code_script_master
            return code_script_master(context, script=script, lenguaje=lenguaje, **inputs_map)

        # ---------------------------------------------------------------------
        # EVALUADORES DINÁMICOS ESPECIALES (Shape Slicer, Polares, etc.)
        # ---------------------------------------------------------------------
        if "Shape Slicer" in node_type or node_type in ["Shape/Shape Slicer", "Shape Slicer", "Shape/Corte/Shape Slicer", "Corte/Shape Slicer"]:
            try:
                modo_alias_map = {
                    "hex": "hex", "hexagonal": "hex", "malla hexagonal": "hex",
                    "tri": "tri", "triangular": "tri", "malla triangular": "tri",
                    "dia": "dia", "diamante": "dia", "rombos": "dia",
                    "ring": "ring", "anillos": "ring",
                    "ray": "ray", "radial": "ray", "rayos": "ray",
                    "quad": "quad", "quadtree": "quad",
                    "bez": "bez", "bézier": "bez", "bezier": "bez", "ondas": "bez",
                    "jigsaw": "jigsaw", "puzzle": "jigsaw", "rompecabezas": "jigsaw",
                    "voronoi": "voronoi", "vor": "voronoi", "cristales": "voronoi",
                    "ashlar": "ashlar", "mamposteria": "ashlar",
                    "brick": "brick", "ladrillo": "brick", "ladrillos": "brick",
                    "mondrian": "mondrian",
                    "herringbone": "herringbone", "espiga": "herringbone", "zig-zag": "herringbone",
                    "delaunay": "delaunay", "low-poly": "delaunay", "lowpoly": "delaunay",
                    "scallop": "scallop", "escamas": "scallop",
                    "web": "web", "spiderweb": "web", "telaraña": "web",
                    "rhombille": "rhombille", "cubos": "rhombille",
                    "octagon": "octagon", "mosaico": "octagon", "octogonos": "octagon",
                    "kagome": "kagome", "trihexagonal": "kagome",
                    "truchet": "truchet", "tuberias": "truchet", "laberinto": "truchet",
                    "circuit": "circuit", "circuito": "circuit", "tech": "circuit",
                    "pattern": "pattern", "patrón": "pattern", "patron": "pattern",
                    "rejilla 1d/2d": "Rejilla 1D/2D", "grid": "Rejilla 1D/2D"
                }

                modo = props.get("modo", props.get("mode", "Rejilla 1D/2D"))
                modo_str = str(modo).strip()
                modo_key = modo_str.lower()
                norm_engine_mode = modo_alias_map.get(modo_key, modo_str)

                inputs_list = node.get("inputs", [])

                def get_val(port_name_or_aliases, default_val=""):
                    if isinstance(port_name_or_aliases, str):
                        aliases = [port_name_or_aliases]
                    else:
                        aliases = list(port_name_or_aliases)
                    
                    for alias in aliases:
                        clean_alias = _clean_key(alias)
                        for i, inp_obj in enumerate(inputs_list):
                            inp_name = inp_obj.get("name", "")
                            if _clean_key(inp_name) == clean_alias or clean_alias in PROP_ALIAS_MAP.get(_clean_key(inp_name), []):
                                val = self.get_input_value(node, i, context)
                                if val != "": return val
                                if "value" in inp_obj and inp_obj["value"] is not None and str(inp_obj["value"]).strip() != "":
                                    return str(inp_obj["value"])
                                widget_obj = inp_obj.get("widget", {})
                                if isinstance(widget_obj, dict) and "value" in widget_obj and widget_obj["value"] is not None and str(widget_obj["value"]).strip() != "":
                                    return str(widget_obj["value"])

                    for alias in aliases:
                        clean_alias = _clean_key(alias)
                        prop_val = _get_prop_value(props, clean_alias, "")
                        if prop_val != "":
                            return str(prop_val)

                    return str(default_val)

                shp = get_val(["Shape", "shape", "texto", "drawing"], props.get("shape", ""))
                from nodes.shape_nodes import resolve_shape_value
                shp = resolve_shape_value(shp, context)
                if not shp:
                    unit = context.get('active_unit') if isinstance(context, dict) else None
                    if unit:
                        shp = getattr(unit, 'text_stripped', getattr(unit, 'text', 'm 0 0 l 100 0 l 100 100 l 0 100'))
                    else:
                        shp = 'm 0 0 l 100 0 l 100 100 l 0 100'

                if shp and not bool(re.match(r'^\s*m\s+-?\d+', str(shp), re.IGNORECASE)):
                    unit = context.get('active_unit') if isinstance(context, dict) else None
                    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
                    styleref = getattr(line, 'styleref', None) if line else None
                    if not styleref and unit:
                        styleref = getattr(unit, 'styleref', None)
                        if not styleref and hasattr(unit, 'line') and getattr(unit, 'line', None):
                            styleref = getattr(unit.line, 'styleref', None)

                    fn = str(styleref.fontname) if styleref and getattr(styleref, 'fontname', None) else "Arial"
                    fs = int(float(styleref.fontsize)) if (styleref and getattr(styleref, 'fontsize', None)) else int(getattr(unit, 'height', getattr(line, 'height', 40)) or 40)
                    b_val = bool(getattr(styleref, 'bold', False)) if styleref else False
                    i_val = bool(getattr(styleref, 'italic', False)) if styleref else False
                    sc_x = float(getattr(styleref, 'scale_x', 100.0)) if styleref else 100.0
                    sc_y = float(getattr(styleref, 'scale_y', 100.0)) if styleref else 100.0

                    raw_text_src = getattr(unit, 'text', '') if unit else (getattr(line, 'raw_text', '') if line else '')
                    if raw_text_src:
                        fn_m = re.search(r'\\fn([^\\}]+)', raw_text_src)
                        if fn_m: fn = fn_m.group(1).strip()
                        fs_m = re.search(r'\\fs(\d+)', raw_text_src)
                        if fs_m: fs = int(fs_m.group(1))
                        fscx_m = re.search(r'\\fscx(\d+(?:\.\d+)?)', raw_text_src)
                        if fscx_m: sc_x = float(fscx_m.group(1))
                        fscy_m = re.search(r'\\fscy(\d+(?:\.\d+)?)', raw_text_src)
                        if fscy_m: sc_y = float(fscy_m.group(1))
                        b_m = re.search(r'\\b([01])', raw_text_src)
                        if b_m: b_val = (b_m.group(1) == '1')
                        i_m = re.search(r'\\i([01])', raw_text_src)
                        if i_m: i_val = (i_m.group(1) == '1')
                    
                    from font_vector_engine import FontVectorEngine
                    v_shp = FontVectorEngine.text_to_shape(str(shp), font_name=fn, font_size=fs, bold=b_val, italic=i_val, scale_x=sc_x, scale_y=sc_y)
                    if v_shp and v_shp.strip():
                        shp = v_shp

                def safe_float(v, default=0.0):
                    if v is None or str(v).strip() == "": return default
                    try:
                        return float(v)
                    except Exception:
                        pass
                    return float(_eval_num_expr(v, context, default=default))

                def safe_int(v, default=1):
                    if v is None or str(v).strip() == "": return default
                    try:
                        return int(float(v))
                    except Exception:
                        pass
                    return int(round(float(_eval_num_expr(v, context, default=float(default)))))

                cols = safe_int(get_val(["Cols", "cols", "Rings", "rings", "columnas", "Num Anillos", "num_anillos"], "2"), 2)
                rows = safe_int(get_val(["Rows", "rows", "Rays", "rays", "filas", "Num Rayos", "num_rayos"], "2"), 2)
                size_x = safe_float(get_val([
                    "Radius", "radius", "Min Size", "min_size", "Grid Size", "grid_size",
                    "Piece Size", "piece_size", "Cell Size", "cell_size", "Min Width", "min_width",
                    "Width", "width", "Length", "length", "Ring Width", "ring_width",
                    "Step Angle", "step_angle", "Size X", "size_x", "radio", "Tamaño Celda",
                    "Tamaño Grid", "Tamaño Pieza", "Tamaño Min", "Ancho Min", "Longitud", "Paso (º)", "Paso (°)"
                ], 20.0), 20.0)
                size_y = safe_float(get_val([
                    "Max Width", "max_width", "Row Height", "row_height", "Height", "height",
                    "Thickness", "thickness", "Amplitude", "amplitude", "Trace Width", "trace_width",
                    "Shape Size", "shape_size", "Size Y", "size_y", "alto", "Alto Fila", "Ancho Max",
                    "Grosor Pista", "Grosor", "Amplitud", "Tamaño Forma"
                ], 20.0), 20.0)
                scale_x = safe_float(get_val(["Scale X", "scale_x", "Scale", "scale"], "1.0"), 1.0)
                scale_y = safe_float(get_val(["Scale Y", "scale_y"], "1.0"), 1.0)
                off_x = safe_float(get_val(["Center X", "center_x", "centerx", "cx", "Off X", "off_x", "offset_x"], "0"), 0.0)
                off_y = safe_float(get_val(["Center Y", "center_y", "centery", "cy", "Off Y", "off_y", "offset_y"], "0"), 0.0)
                angle = safe_float(get_val(["Angle", "angulo", "angle", "Step Angle", "step_angle", "Paso (º)", "Paso (°)", "paso_deg", "paso"], "0"), 0.0)
                overlap = safe_float(get_val(["Bleed", "sangrado", "overlap", "ov"], "0"), 0.0)
                
                stagger_raw = get_val(["Stagger", "stagger", "Intercalar", "intercalar"], "")
                if str(stagger_raw).lower() in ["true", "1", "yes"]:
                    accel_x_default = "2.0"
                else:
                    accel_x_default = "1.0"

                accel_x = safe_float(get_val([
                    "Stop Prob", "stop_prob", "Chaos", "chaos", "Via Prob", "via_prob",
                    "Accel X", "accel_x", "Accel", "accel", "Jitter", "jitter", "Caos", "caos",
                    "Prob Stop", "prob_stop", "Prob Vía", "prob_via"
                ], accel_x_default), float(accel_x_default))
                accel_y = safe_float(get_val(["Accel Y", "accel_y", "Accel", "accel"], "1.0"), 1.0)
                
                pattern_shape = get_val(["Pattern Shape", "pattern_shape", "Forma String", "forma_string"], "")
                
                text_scale = safe_float(get_val(["Text Scale", "text_scale"], "1.0"), 1.0)
                pre_offset = safe_float(get_val(["Pre-Offset", "pre_offset", "preoffset", "Pre Offset", "pre-offset"], "0"), 0.0)
                order = safe_int(get_val(["Order", "order", "orden"], "79"), 79)

                unit = context.get('active_unit') if isinstance(context, dict) else None
                parent_x = float(context.get('pos_x', context.get('line_x', context.get('syl_x', context.get('x', 0.0)))))
                parent_y = float(context.get('pos_y', context.get('line_y', context.get('syl_y', context.get('y', 0.0)))))
                if unit:
                    if hasattr(unit, 'center') and unit.center is not None: parent_x = float(unit.center)
                    elif hasattr(unit, 'pos_x') and unit.pos_x is not None: parent_x = float(unit.pos_x)
                    elif hasattr(unit, 'x') and unit.x is not None: parent_x = float(unit.x)
                    
                    if hasattr(unit, 'middle') and unit.middle is not None: parent_y = float(unit.middle)
                    elif hasattr(unit, 'pos_y') and unit.pos_y is not None: parent_y = float(unit.pos_y)
                    elif hasattr(unit, 'y') and unit.y is not None: parent_y = float(unit.y)

                from clipper_engine import ClipperEngine

                # Almacenar y reutilizar las piezas cortadas en la unidad activa o contexto de ejecución
                slicer_node_id = node.get('id', 0)
                slicer_sig = (
                    slicer_node_id,
                    str(shp),
                    norm_engine_mode,
                    cols, rows,
                    size_x, size_y,
                    scale_x, scale_y,
                    off_x, off_y,
                    angle, overlap,
                    accel_x, accel_y,
                    order, text_scale,
                    pre_offset,
                    pattern_shape
                )

                unit_cache = None
                if unit is not None:
                    if not hasattr(unit, '_slicer_cache') or not isinstance(unit._slicer_cache, dict):
                        unit._slicer_cache = {}
                    unit_cache = unit._slicer_cache
                elif isinstance(context.get('_global_slicer_cache'), dict):
                    unit_cache = context['_global_slicer_cache']
                else:
                    if not isinstance(context.get('_slicer_pieces'), dict):
                        context['_slicer_pieces'] = {}
                    unit_cache = context['_slicer_pieces']

                if slicer_sig in unit_cache:
                    pieces = unit_cache[slicer_sig]
                elif slicer_node_id in unit_cache and not isinstance(unit_cache[slicer_node_id], dict):
                    pieces = unit_cache[slicer_node_id]
                else:
                    pieces = ClipperEngine.slice_grid(
                        shp, cols=cols, rows=rows, size_x=size_x, size_y=size_y,
                        scale_x=scale_x, scale_y=scale_y, offset_x=off_x, offset_y=off_y,
                        angle=angle, overlap=overlap, accel=accel_x, accel_x=accel_x, accel_y=accel_y, order=order,
                        text_scale=text_scale, pre_offset=pre_offset, engine_mode=norm_engine_mode,
                        pattern_shape=pattern_shape
                    )
                    if not pieces:
                        pieces = [{"code": shp, "cx": 0, "cy": 0, "col": 1, "row": 1}]
                    unit_cache[slicer_sig] = pieces
                    unit_cache[slicer_node_id] = pieces

                if not isinstance(context.get('_slicer_pieces'), dict):
                    context['_slicer_pieces'] = {}
                context['_slicer_pieces'][slicer_node_id] = pieces

                total_pieces = len(pieces)

                # Auto-Loop Transparente: Obtener iteración actual j y ajustar maxloop del contexto
                j_val = int(context.get('j', context.get('J', 1)))
                
                # Auto-ajustar total de iteraciones maxloop del slicer
                context['j_max'] = total_pieces
                context['maxloop'] = total_pieces

                # Seleccionar la pieza correspondiente a la iteración j
                piece_idx = max(0, min(j_val - 1, total_pieces - 1))
                piece = pieces[piece_idx]
                cx, cy = float(piece.get("cx", 0)), float(piece.get("cy", 0))

                abs_x = parent_x + cx
                abs_y = parent_y + cy

                code_val = str(piece.get("code", ""))

                anchor_mode = get_val(["Anchor", "anchor", "anclaje"], props.get("anchor", "piezas")).lower()
                out_mode = get_val(["Output Type", "out_mode", "output_type", "tipo_salida"], props.get("out_mode", "Shape")).lower()

                # Configurar variables de origen (\org) y posición (\pos) en el contexto según el modo de anclaje
                if "abs" in anchor_mode or "absoluto" in anchor_mode:
                    context['pos_overridden'] = False
                    context['has_org'] = False
                    context['pos_x'] = parent_x
                    context['pos_y'] = parent_y
                    context['col'] = piece.get("col", 1)
                    context['row'] = piece.get("row", 1)
                    formatted_code = ClipperEngine.transform_shape(code_val, mode="Offset", offset_x=parent_x, offset_y=parent_y)
                elif "rel" in anchor_mode:
                    context['pos_overridden'] = False
                    context['has_org'] = True
                    context['org_x'] = parent_x
                    context['org_y'] = parent_y
                    context['pos_x'] = parent_x
                    context['pos_y'] = parent_y
                    context['col'] = piece.get("col", 1)
                    context['row'] = piece.get("row", 1)
                    formatted_code = code_val
                elif any(k in anchor_mode for k in ["pieza", "piece", "true"]):
                    context['x'] = abs_x
                    context['y'] = abs_y
                    context['fx_pos_x'] = abs_x
                    context['fx_pos_y'] = abs_y
                    context['pos_x'] = abs_x
                    context['pos_y'] = abs_y
                    context['pos_overridden'] = True
                    context['has_org'] = True
                    context['org_x'] = abs_x
                    context['org_y'] = abs_y
                    context['col'] = piece.get("col", 1)
                    context['row'] = piece.get("row", 1)
                    formatted_code = ClipperEngine.transform_shape(code_val, mode="Offset", offset_x=-cx, offset_y=-cy)
                elif "org" in anchor_mode:
                    context['x'] = abs_x
                    context['y'] = abs_y
                    context['fx_pos_x'] = abs_x
                    context['fx_pos_y'] = abs_y
                    context['pos_x'] = abs_x
                    context['pos_y'] = abs_y
                    context['pos_overridden'] = True
                    context['has_org'] = True
                    context['org_x'] = parent_x
                    context['org_y'] = parent_y
                    context['col'] = piece.get("col", 1)
                    context['row'] = piece.get("row", 1)
                    formatted_code = ClipperEngine.transform_shape(code_val, mode="Offset", offset_x=-cx, offset_y=-cy)
                elif "pos" in anchor_mode:
                    context['x'] = abs_x
                    context['y'] = abs_y
                    context['fx_pos_x'] = abs_x
                    context['fx_pos_y'] = abs_y
                    context['pos_x'] = abs_x
                    context['pos_y'] = abs_y
                    context['pos_overridden'] = True
                    context['has_org'] = False
                    context['col'] = piece.get("col", 1)
                    context['row'] = piece.get("row", 1)
                    formatted_code = ClipperEngine.transform_shape(code_val, mode="Offset", offset_x=-cx, offset_y=-cy)
                else: # "absoluto" fallback
                    context['pos_overridden'] = False
                    context['has_org'] = False
                    context['pos_x'] = parent_x
                    context['pos_y'] = parent_y
                    context['col'] = piece.get("col", 1)
                    context['row'] = piece.get("row", 1)
                    formatted_code = ClipperEngine.transform_shape(code_val, mode="Offset", offset_x=parent_x, offset_y=parent_y)

                # Aplicar Tipo Salida (Mode: Forma, Clip, iClip)
                if "iclip" in out_mode:
                    abs_code = ClipperEngine.transform_shape(code_val, mode="Offset", offset_x=parent_x, offset_y=parent_y)
                    final_res = f"{{\\iclip({abs_code})}}"
                elif "clip" in out_mode:
                    abs_code = ClipperEngine.transform_shape(code_val, mode="Offset", offset_x=parent_x, offset_y=parent_y)
                    final_res = f"{{\\clip({abs_code})}}"
                else:
                    final_res = formatted_code

                if output_slot_index == 1: return str(abs_x)
                elif output_slot_index == 2: return str(abs_y)
                elif output_slot_index == 3: return str(piece.get("col", 1))
                elif output_slot_index == 4: return str(piece.get("row", 1))
                return str(final_res)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return f"[Err Shape Slicer: {e}]"

        if node_type in ["Shape/Shape Manipulator", "Shape Manipulator", "Shape/Manipulador", "Manipulador"]:
            try:
                modo = str(props.get("mode", props.get("modo", "Escalar"))).strip()
                shp_val = self.get_input_value(node, 0, context)
                if shp_val == "": shp_val = str(_get_prop_value(props, "shape", "")).strip()
                from nodes.shape_nodes import resolve_shape_value, shape_manipulator
                shp_val = resolve_shape_value(shp_val, context)
                if not shp_val:
                    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
                    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
                    shp_val = getattr(unit, 'text_stripped', getattr(unit, 'text', '')) or getattr(line, 'text_stripped', getattr(line, 'text', ''))

                modo_clean = modo.lower()
                if "borde" in modo_clean:
                    offset_border = _eval_num_expr(self.get_input_value(node, 1, context) or _get_prop_value(props, "offset_border", "2.0"), context, 2.0)
                    scale_x = 100.0
                    scale_y = 100.0
                    angle = 0.0
                    offset_x = 0.0
                    offset_y = 0.0
                    anchor = str(_get_prop_value(props, "anchor", "center")).strip()
                elif "rotar" in modo_clean:
                    angle = _eval_num_expr(self.get_input_value(node, 1, context) or _get_prop_value(props, "angle", "0"), context, 0.0)
                    scale_x = 100.0
                    scale_y = 100.0
                    offset_x = 0.0
                    offset_y = 0.0
                    offset_border = 0.0
                    anchor = str(self.get_input_value(node, 2, context) or _get_prop_value(props, "anchor", "center")).strip()
                elif "deformar" in modo_clean:
                    offset_x = _eval_num_expr(self.get_input_value(node, 1, context) or _get_prop_value(props, "offset_x", "0"), context, 0.0)
                    offset_y = _eval_num_expr(self.get_input_value(node, 2, context) or _get_prop_value(props, "offset_y", "0"), context, 0.0)
                    factor = _eval_num_expr(self.get_input_value(node, 3, context) or _get_prop_value(props, "factor", "100"), context, 100.0)
                    scale_x = factor
                    scale_y = factor
                    angle = 0.0
                    offset_border = 0.0
                    anchor = str(_get_prop_value(props, "anchor", "center")).strip()
                elif "posici" in modo_clean or "posic" in modo_clean:
                    offset_x = _eval_num_expr(self.get_input_value(node, 1, context) or _get_prop_value(props, "offset_x", "0"), context, 0.0)
                    offset_y = _eval_num_expr(self.get_input_value(node, 2, context) or _get_prop_value(props, "offset_y", "0"), context, 0.0)
                    scale_x = 100.0
                    scale_y = 100.0
                    angle = 0.0
                    offset_border = 0.0
                    anchor = str(self.get_input_value(node, 3, context) or _get_prop_value(props, "anchor", "center")).strip()
                else:  # "Escalar" o modo completo
                    scale_x = _eval_num_expr(self.get_input_value(node, 1, context) or _get_prop_value(props, "scale_x", "100"), context, 100.0)
                    scale_y = _eval_num_expr(self.get_input_value(node, 2, context) or _get_prop_value(props, "scale_y", "100"), context, 100.0)
                    angle = _eval_num_expr(self.get_input_value(node, 3, context) or _get_prop_value(props, "angle", "0"), context, 0.0)
                    offset_x = _eval_num_expr(self.get_input_value(node, 4, context) or _get_prop_value(props, "offset_x", "0"), context, 0.0)
                    offset_y = _eval_num_expr(self.get_input_value(node, 5, context) or _get_prop_value(props, "offset_y", "0"), context, 0.0)
                    offset_border = _eval_num_expr(self.get_input_value(node, 6, context) or _get_prop_value(props, "offset_border", "0.0"), context, 0.0)
                    anchor = str(self.get_input_value(node, 7, context) or _get_prop_value(props, "anchor", "center")).strip()

                return shape_manipulator(context, drawing=shp_val, scale_x=scale_x / 100.0, scale_y=scale_y / 100.0, rot=angle, offset_x=offset_x, offset_y=offset_y, offset_border=offset_border, mode=anchor)
            except Exception as e:
                return f"[Err Shape Manipulator: {e}]"

        if node_type in ["Shape/Shape Transform", "Shape Transform", "Shape/Trans. Shape", "Trans. Shape"]:
            try:
                modo = str(props.get("mode", props.get("modo", "Inflate"))).strip()
                shp_val = self.get_input_value(node, 0, context)
                if shp_val == "": shp_val = str(_get_prop_value(props, "shape", "")).strip()
                from nodes.shape_nodes import resolve_shape_value, shape_transform
                shp_val = resolve_shape_value(shp_val, context)
                if not shp_val:
                    unit = context.get('active_unit') if isinstance(context, dict) else (context.get('syl') if isinstance(context, dict) else None)
                    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
                    shp_val = getattr(unit, 'text_stripped', getattr(unit, 'text', '')) or getattr(line, 'text_stripped', getattr(line, 'text', ''))

                modo_clean = modo.lower()
                if "skew" in modo_clean or "cizall" in modo_clean or "inclin" in modo_clean:
                    in_ax = self.get_input_value(node, 1, context)
                    if in_ax is None or in_ax == "": in_ax = _get_prop_value(props, "angle_x", _get_prop_value(props, "ang_x", _get_prop_value(props, "angle", "0")))
                    angle_x = _eval_num_expr(in_ax, context, 0.0)

                    in_ay = self.get_input_value(node, 2, context)
                    if in_ay is None or in_ay == "": in_ay = _get_prop_value(props, "angle_y", _get_prop_value(props, "ang_y", "0"))
                    angle_y = _eval_num_expr(in_ay, context, 0.0)

                    in_anc = self.get_input_value(node, 3, context)
                    if in_anc is None or in_anc == "": in_anc = _get_prop_value(props, "anchor", _get_prop_value(props, "anclaje", "center"))
                    anchor_val = str(in_anc).strip()
                    return shape_transform(context, drawing=shp_val, mode="Skew", angle_x=angle_x, angle_y=angle_y, anchor=anchor_val)
                elif "round" in modo_clean or "redond" in modo_clean or "esquina" in modo_clean:
                    in_rad = self.get_input_value(node, 1, context)
                    if in_rad is None or in_rad == "": in_rad = _get_prop_value(props, "radius", "10.0")
                    radius_val = _eval_num_expr(in_rad, context, 10.0)

                    in_anc = self.get_input_value(node, 2, context)
                    if in_anc is None or in_anc == "": in_anc = _get_prop_value(props, "anchor", "center")
                    anchor_val = str(in_anc).strip()

                    corner_mode = str(_get_prop_value(props, "corner_mode", "Round")).strip()
                    return shape_transform(context, drawing=shp_val, mode="Round Corners", radius=radius_val, corner_mode=corner_mode, anchor=anchor_val)
                elif "flexor" in modo_clean or "curv" in modo_clean or "dobl" in modo_clean:
                    curve_in = self.get_input_value(node, 1, context)
                    if curve_in is None or curve_in == "": curve_in = str(_get_prop_value(props, "curve", "30")).strip()

                    in_bt = self.get_input_value(node, 2, context)
                    if in_bt is None or in_bt == "": in_bt = _get_prop_value(props, "bend_t", "1.0")
                    bend_t = _eval_num_expr(in_bt, context, 1.0)

                    in_anc = self.get_input_value(node, 3, context)
                    if in_anc is None or in_anc == "": in_anc = _get_prop_value(props, "anchor", "center")
                    anchor_val = str(in_anc).strip()

                    axis_val = str(_get_prop_value(props, "axis", "x")).strip()
                    return shape_transform(context, drawing=shp_val, mode="Flexor", curve=curve_in, bend_t=bend_t, axis=axis_val, anchor=anchor_val)
                elif "distort" in modo_clean or "deform" in modo_clean or "morph" in modo_clean:
                    tgt_val = self.get_input_value(node, 1, context)
                    if tgt_val is None or tgt_val == "": tgt_val = str(_get_prop_value(props, "target_shape", "")).strip()
                    tgt_val = resolve_shape_value(tgt_val, context)

                    in_t = self.get_input_value(node, 2, context)
                    if in_t is None or in_t == "": in_t = _get_prop_value(props, "t", "1.0")
                    t_val = _eval_num_expr(in_t, context, 1.0)

                    in_slot_3 = self.get_input_value(node, 3, context)
                    in_slot_4 = self.get_input_value(node, 4, context)
                    in_slot_5 = self.get_input_value(node, 5, context)
                    known_anchors = {"center", "origin", "zero", "pos", "topleft", "bottomleft", "topright", "bottomright", "relativo", "absoluto"}

                    prop_energy = _get_prop_value(props, "energy", _get_prop_value(props, "fluidez", _get_prop_value(props, "fluidity", "0.35")))
                    prop_step = _get_prop_value(props, "step_px", _get_prop_value(props, "step", "0"))
                    prop_anchor = _get_prop_value(props, "anchor", "center")

                    energy_val = _eval_num_expr(prop_energy, context, 0.35)
                    step_val = _eval_num_expr(prop_step, context, 0.0)
                    anchor_val = str(prop_anchor).strip()

                    if in_slot_3 is not None and str(in_slot_3).strip() != "":
                        s3_str = str(in_slot_3).strip().lower()
                        if s3_str in known_anchors:
                            anchor_val = str(in_slot_3).strip()
                        else:
                            energy_val = _eval_num_expr(in_slot_3, context, energy_val)

                    if in_slot_4 is not None and str(in_slot_4).strip() != "":
                        s4_str = str(in_slot_4).strip().lower()
                        if s4_str in known_anchors:
                            anchor_val = str(in_slot_4).strip()
                        else:
                            step_val = _eval_num_expr(in_slot_4, context, step_val)

                    if in_slot_5 is not None and str(in_slot_5).strip() != "":
                        anchor_val = str(in_slot_5).strip()

                    return shape_transform(context, drawing=shp_val, mode="Distort", target_shape=tgt_val, t=t_val, step_px=step_val, energy=energy_val, anchor=anchor_val)
                else:  # "Inflate" default
                    in_t = self.get_input_value(node, 1, context)
                    if in_t is None or in_t == "": in_t = _get_prop_value(props, "t", "0.5")
                    t_val = _eval_num_expr(in_t, context, 0.5)

                    in_r = self.get_input_value(node, 2, context)
                    if in_r is None or in_r == "": in_r = _get_prop_value(props, "ratio", "1.0")
                    ratio_val = _eval_num_expr(in_r, context, 1.0)

                    in_anc = self.get_input_value(node, 3, context)
                    if in_anc is None or in_anc == "": in_anc = _get_prop_value(props, "anchor", "center")
                    anchor_val = str(in_anc).strip()

                    inf_mode = str(_get_prop_value(props, "inflate_mode", "Circle")).strip()
                    return shape_transform(context, drawing=shp_val, mode="Inflate", t=t_val, ratio=ratio_val, inflate_mode=inf_mode, anchor=anchor_val)
            except Exception as e:
                return f"[Err Shape Transform: {e}]"

        elif node_type in ["Functions/Polar to Cartesian", "Polar to Cartesian"]:
            try:
                import math
                x0_raw = self.get_input_value(node, 0, context)
                if x0_raw == "": x0_raw = _get_prop_value(props, "x", "0")
                y0_raw = self.get_input_value(node, 1, context)
                if y0_raw == "": y0_raw = _get_prop_value(props, "y", "0")
                ang_raw = self.get_input_value(node, 2, context)
                if ang_raw == "": ang_raw = _get_prop_value(props, "angle", "0")
                r_raw = self.get_input_value(node, 3, context)
                if r_raw == "": r_raw = _get_prop_value(props, "radius", "0")

                x0 = _eval_num_expr(x0_raw, context, 0.0)
                y0 = _eval_num_expr(y0_raw, context, 0.0)
                ang = _eval_num_expr(ang_raw, context, 0.0)
                r = _eval_num_expr(r_raw, context, 0.0)

                rad = math.radians(ang)
                dx = r * math.cos(rad)
                dy = r * math.sin(rad)
                res_x = x0 + dx
                res_y = y0 + dy

                fmt_x = int(res_x) if float(res_x).is_integer() else round(res_x, 2)
                fmt_y = int(res_y) if float(res_y).is_integer() else round(res_y, 2)
                fmt_dx = int(dx) if float(dx).is_integer() else round(dx, 2)
                fmt_dy = int(dy) if float(dy).is_integer() else round(dy, 2)

                if output_slot_index == 1: return str(fmt_x)
                elif output_slot_index == 2: return str(fmt_y)
                elif output_slot_index == 3: return str(fmt_dx)
                elif output_slot_index == 4: return str(fmt_dy)
                else: return f"\\pos({fmt_x},{fmt_y})"
            except Exception as e:
                return f"[Err Polares: {e}]"

        # ---------------------------------------------------------------------
        # 2. CURVA BÉZIER (Multi-Slot: \pos, X, Y, Tan, Norm, Spline)
        # ---------------------------------------------------------------------
        elif node_type in ["Functions/Bezier Curve", "Bezier Curve"]:
            try:
                import math

                def _get_val(name, default):
                    inputs = node.get('inputs', [])
                    for idx, inp in enumerate(inputs):
                        if inp.get('name') == name or inp.get('property') == name.lower():
                            v = self.get_input_value(node, idx, context)
                            if v != "":
                                return v
                    v = _get_prop_value(props, name.lower(), _get_prop_value(props, name, default))
                    return v if v != "" else default

                def _parse_pt(pt_val, default=(0.0, 0.0)):
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

                def _sample_polyline_arc_length(pts, progress_t):
                    if pts is None or len(pts) == 0:
                        return 0.0, 0.0, 1.0, 0.0
                    if len(pts) == 1:
                        return float(pts[0][0]), float(pts[0][1]), 1.0, 0.0
                    seg_lens = []
                    total_len = 0.0
                    for k in range(len(pts) - 1):
                        d = math.hypot(pts[k+1][0] - pts[k][0], pts[k+1][1] - pts[k][1])
                        seg_lens.append(d)
                        total_len += d
                    if total_len <= 1e-9:
                        return float(pts[0][0]), float(pts[0][1]), 1.0, 0.0
                    target_d = progress_t * total_len
                    accum = 0.0
                    chosen_idx = len(pts) - 2
                    frac = 0.0
                    for k, slen in enumerate(seg_lens):
                        if accum + slen >= target_d:
                            chosen_idx = k
                            frac = (target_d - accum) / slen if slen > 0 else 0.0
                            break
                        accum += slen
                    pA = pts[chosen_idx]
                    pB = pts[chosen_idx + 1]
                    cur_x = pA[0] + frac * (pB[0] - pA[0])
                    cur_y = pA[1] + frac * (pB[1] - pA[1])
                    cur_dx = pB[0] - pA[0]
                    cur_dy = pB[1] - pA[1]
                    return cur_x, cur_y, cur_dx, cur_dy

                modo = str(_get_prop_value(props, "modo", "Cúbica 2D")).strip()
                m_lower = modo.lower()

                t_raw = _get_val("t", "0.5")
                ft = float(_eval_num_expr(t_raw, context, 0.5))
                ft = max(0.0, min(1.0, ft))
                u = 1.0 - ft

                subdivs_raw = _get_val("Subdivs", "100")
                subdivs = max(0, min(2000, int(float(_eval_num_expr(subdivs_raw, context, 100)))))

                if any(k in m_lower for k in ("cuad", "quad")):
                    x0, y0 = _parse_pt(_get_val("P0", "0,0"), (0.0, 0.0))
                    x1, y1 = _parse_pt(_get_val("P1", "50,100"), (50.0, 100.0))
                    x2, y2 = _parse_pt(_get_val("P2", "100,0"), (100.0, 0.0))
                    cp1_x = x0 + (2.0 / 3.0) * (x1 - x0)
                    cp1_y = y0 + (2.0 / 3.0) * (y1 - y0)
                    cp2_x = x2 + (2.0 / 3.0) * (x1 - x2)
                    cp2_y = y2 + (2.0 / 3.0) * (y1 - y2)
                    spline_str = f"m {round(x0,2)} {round(y0,2)} b {round(cp1_x,2)} {round(cp1_y,2)} {round(cp2_x,2)} {round(cp2_y,2)} {round(x2,2)} {round(y2,2)}"
                    if subdivs >= 2:
                        pts = []
                        for j in range(subdivs + 1):
                            s = j / float(subdivs)
                            us = 1.0 - s
                            px = us * us * x0 + 2.0 * us * s * x1 + s * s * x2
                            py = us * us * y0 + 2.0 * us * s * y1 + s * s * y2
                            pts.append((px, py))
                        bx, by, dx, dy = _sample_polyline_arc_length(pts, ft)
                    else:
                        bx = u * u * x0 + 2.0 * u * ft * x1 + ft * ft * x2
                        by = u * u * y0 + 2.0 * u * ft * y1 + ft * ft * y2
                        dx = 2.0 * u * (x1 - x0) + 2.0 * ft * (x2 - x1)
                        dy = 2.0 * u * (y1 - y0) + 2.0 * ft * (y2 - y1)
                elif any(k in m_lower for k in ("trazado", "velocidad", "tangente", "assdraw", "spline")):
                    shape_raw = _get_val("Shape", "")
                    if str(shape_raw).strip().lower().startswith("shape."):
                        from nodes.shape_nodes import resolve_shape_value
                        shape_raw = resolve_shape_value(shape_raw, context)
                    shape_str = str(shape_raw).strip()
                    eff_subdivs = max(5, subdivs if subdivs >= 2 else 100)
                    from clipper_engine import ClipperEngine
                    contours = ClipperEngine.parse_assdraw(shape_str, bezier_steps=eff_subdivs)
                    if contours and len(contours) > 0 and len(contours[0]) > 1:
                        pts = contours[0]
                        bx, by, dx, dy = _sample_polyline_arc_length(pts, ft)
                        spline_str = shape_str
                    else:
                        x0, y0 = _parse_pt(_get_val("P0", "0,0"), (0.0, 0.0))
                        x1, y1 = _parse_pt(_get_val("P1", "50,100"), (50.0, 100.0))
                        x2, y2 = _parse_pt(_get_val("P2", "150,100"), (150.0, 100.0))
                        x3, y3 = _parse_pt(_get_val("P3", "200,0"), (200.0, 0.0))
                        spline_str = shape_str if shape_str else f"m {round(x0,2)} {round(y0,2)} b {round(x1,2)} {round(y1,2)} {round(x2,2)} {round(y2,2)} {round(x3,2)} {round(y3,2)}"
                        if subdivs >= 2:
                            pts = []
                            for j in range(subdivs + 1):
                                s = j / float(subdivs)
                                us = 1.0 - s
                                px = (us**3)*x0 + 3*(us**2)*s*x1 + 3*us*(s**2)*x2 + (s**3)*x3
                                py = (us**3)*y0 + 3*(us**2)*s*y1 + 3*us*(s**2)*y2 + (s**3)*y3
                                pts.append((px, py))
                            bx, by, dx, dy = _sample_polyline_arc_length(pts, ft)
                        else:
                            bx = (u**3)*x0 + 3*(u**2)*ft*x1 + 3*u*(ft**2)*x2 + (ft**3)*x3
                            by = (u**3)*y0 + 3*(u**2)*ft*y1 + 3*u*(ft**2)*y2 + (ft**3)*y3
                            dx = 3*(u**2)*(x1 - x0) + 6*u*ft*(x2 - x1) + 3*(ft**2)*(x3 - x2)
                            dy = 3*(u**2)*(y1 - y0) + 6*u*ft*(y2 - y1) + 3*(ft**2)*(y3 - y2)
                else: # Cúbica 2D
                    x0, y0 = _parse_pt(_get_val("P0", "0,0"), (0.0, 0.0))
                    x1, y1 = _parse_pt(_get_val("P1", "50,100"), (50.0, 100.0))
                    x2, y2 = _parse_pt(_get_val("P2", "150,100"), (150.0, 100.0))
                    x3, y3 = _parse_pt(_get_val("P3", "200,0"), (200.0, 0.0))
                    spline_str = f"m {round(x0,2)} {round(y0,2)} b {round(x1,2)} {round(y1,2)} {round(x2,2)} {round(y2,2)} {round(x3,2)} {round(y3,2)}"
                    if subdivs >= 2:
                        pts = []
                        for j in range(subdivs + 1):
                            s = j / float(subdivs)
                            us = 1.0 - s
                            px = (us**3)*x0 + 3*(us**2)*s*x1 + 3*us*(s**2)*x2 + (s**3)*x3
                            py = (us**3)*y0 + 3*(us**2)*s*y1 + 3*us*(s**2)*y2 + (s**3)*y3
                            pts.append((px, py))
                        bx, by, dx, dy = _sample_polyline_arc_length(pts, ft)
                    else:
                        bx = (u**3)*x0 + 3*(u**2)*ft*x1 + 3*u*(ft**2)*x2 + (ft**3)*x3
                        by = (u**3)*y0 + 3*(u**2)*ft*y1 + 3*u*(ft**2)*y2 + (ft**3)*y3
                        dx = 3*(u**2)*(x1 - x0) + 6*u*ft*(x2 - x1) + 3*(ft**2)*(x3 - x2)
                        dy = 3*(u**2)*(y1 - y0) + 6*u*ft*(y2 - y1) + 3*(ft**2)*(y3 - y2)

                tan_deg = math.degrees(math.atan2(dx, dy)) - 90.0
                while tan_deg > 180.0:
                    tan_deg -= 360.0
                while tan_deg <= -180.0:
                    tan_deg += 360.0
                norm_deg = tan_deg + 90.0
                while norm_deg > 180.0:
                    norm_deg -= 360.0
                while norm_deg <= -180.0:
                    norm_deg += 360.0

                rbx = round(float(bx), 2)
                rby = round(float(by), 2)
                fmt_x = int(rbx) if rbx.is_integer() else rbx
                fmt_y = int(rby) if rby.is_integer() else rby

                if output_slot_index == 1: return str(fmt_x)
                elif output_slot_index == 2: return str(fmt_y)
                elif output_slot_index == 3: return str(round(tan_deg, 2))
                elif output_slot_index == 4: return str(round(norm_deg, 2))
                elif output_slot_index == 5: return spline_str
                else:
                    return f"\\pos({fmt_x},{fmt_y})"
            except Exception as e:
                return f"[Err Curva Bézier: {e}]"

        # ---------------------------------------------------------------------
        # 3. TEXT TO SHAPE (Multi-Slot: Shape Out, Ancho, Alto)
        # ---------------------------------------------------------------------
        elif node_type in ["Functions/Text to Shape", "Text to Shape"]:
            try:
                unit = context.get('active_unit') if isinstance(context, dict) else None
                line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
                styleref = getattr(line, 'styleref', None) if line else None
                if not styleref and unit:
                    styleref = getattr(unit, 'styleref', None)
                    if not styleref and hasattr(unit, 'line') and getattr(unit, 'line', None):
                        styleref = getattr(unit.line, 'styleref', None)

                txt = self.get_input_value(node, 0, context)
                if txt == "": txt = _get_prop_value(props, "text", "")
                if not txt:
                    txt = getattr(unit, 'text_stripped', getattr(unit, 'text', '')) if unit else (getattr(line, 'text_stripped', getattr(line, 'text', '')) if line else "")

                font_name = self.get_input_value(node, 1, context)
                if font_name == "":
                    font_name_prop = _get_prop_value(props, "font_name", "")
                    if font_name_prop:
                        font_name = font_name_prop
                    elif styleref and getattr(styleref, 'fontname', None):
                        font_name = str(styleref.fontname)
                    else:
                        font_name = "Arial"

                font_size_raw = self.get_input_value(node, 2, context)
                if font_size_raw == "":
                    font_size_prop = _get_prop_value(props, "font_size", "")
                    if font_size_prop and font_size_prop != "100":
                        font_size_raw = font_size_prop
                    elif styleref and getattr(styleref, 'fontsize', None):
                        font_size_raw = str(int(float(styleref.fontsize)))
                    elif unit and getattr(unit, 'height', None):
                        font_size_raw = str(int(float(unit.height)))
                    else:
                        font_size_raw = "100"
                font_size = int(_eval_num_expr(font_size_raw, context, 100.0))

                scale_raw = self.get_input_value(node, 3, context)
                if scale_raw == "": scale_raw = _get_prop_value(props, "scale", "1.0")
                scale = float(_eval_num_expr(scale_raw, context, 1.0))

                bold_raw = _get_prop_value(props, "bold", "false")
                bold = str(bold_raw).lower() in ["true", "1", "yes"]
                italic_raw = _get_prop_value(props, "italic", "false")
                italic = str(italic_raw).lower() in ["true", "1", "yes"]

                from font_vector_engine import FontVectorEngine
                from clipper_engine import ClipperEngine
                shape_str = FontVectorEngine.text_to_shape(str(txt), font_name=str(font_name), font_size=font_size, bold=bold, italic=italic, scale=scale)
                contours = ClipperEngine.parse_assdraw(shape_str)
                _, _, _, _, _, _, w, h = ClipperEngine.get_bbox(contours)

                if output_slot_index == 1: return str(round(w, 2))
                elif output_slot_index == 2: return str(round(h, 2))
                return shape_str
            except Exception as e:
                return f"[Err Text to Shape: {e}]"

        # ---------------------------------------------------------------------
        # 3b. IMG TO SHAPE (Multi-Slot: Shape Out, Ancho, Alto, Puntos)
        # ---------------------------------------------------------------------
        elif node_type in ["Shape/IMG to Shape", "IMG to Shape"]:
            try:
                img_path = self.get_input_value(node, 0, context)
                if not img_path or str(img_path).strip() == "":
                    img_path = str(_get_prop_value(props, "image_path", "")).strip()

                frame_raw = self.get_input_value(node, 1, context)
                if not frame_raw or str(frame_raw).strip() == "":
                    frame_raw = _get_prop_value(props, "frame_idx", "1")
                
                from img_tracer_engine import _is_animated_gif
                if _is_animated_gif(img_path) and str(frame_raw).strip() in ["1", ""]:
                    frame_raw = "j"

                frame_index = int(_eval_num_expr(frame_raw, context, 1.0))

                threshold_raw = self.get_input_value(node, 2, context)
                if not threshold_raw or str(threshold_raw).strip() == "":
                    threshold_raw = _get_prop_value(props, "threshold", "128")
                threshold = int(_eval_num_expr(threshold_raw, context, 128.0))

                tolerance_raw = self.get_input_value(node, 3, context)
                if not tolerance_raw or str(tolerance_raw).strip() == "":
                    tolerance_raw = _get_prop_value(props, "tolerance", "1.0")
                tolerance = float(_eval_num_expr(tolerance_raw, context, 1.0))

                alphamax_raw = self.get_input_value(node, 4, context)
                if not alphamax_raw or str(alphamax_raw).strip() == "":
                    alphamax_raw = _get_prop_value(props, "alphamax", "1.0")
                alphamax = float(_eval_num_expr(alphamax_raw, context, 1.0))

                opttoler_raw = self.get_input_value(node, 5, context)
                if not opttoler_raw or str(opttoler_raw).strip() == "":
                    opttoler_raw = _get_prop_value(props, "opttoler", "0.2")
                opttoler = float(_eval_num_expr(opttoler_raw, context, 0.2))

                out_scale_raw = self.get_input_value(node, 6, context)
                if not out_scale_raw or str(out_scale_raw).strip() == "":
                    out_scale_raw = _get_prop_value(props, "out_scale", "1.0")
                out_scale = float(_eval_num_expr(out_scale_raw, context, 1.0))
                if out_scale <= 0: out_scale = 1.0

                out_w_raw = self.get_input_value(node, 7, context)
                if not out_w_raw or str(out_w_raw).strip() == "":
                    out_w_raw = _get_prop_value(props, "out_w", "0.0")
                out_w = float(_eval_num_expr(out_w_raw, context, 0.0))

                out_h_raw = self.get_input_value(node, 8, context)
                if not out_h_raw or str(out_h_raw).strip() == "":
                    out_h_raw = _get_prop_value(props, "out_h", "0.0")
                out_h = float(_eval_num_expr(out_h_raw, context, 0.0))

                offset_x_raw = self.get_input_value(node, 9, context)
                if not offset_x_raw or str(offset_x_raw).strip() == "":
                    offset_x_raw = _get_prop_value(props, "offset_x", "0.0")
                offset_x = float(_eval_num_expr(offset_x_raw, context, 0.0))

                offset_y_raw = self.get_input_value(node, 10, context)
                if not offset_y_raw or str(offset_y_raw).strip() == "":
                    offset_y_raw = _get_prop_value(props, "offset_y", "0.0")
                offset_y = float(_eval_num_expr(offset_y_raw, context, 0.0))

                img_scale_raw = self.get_input_value(node, 11, context)
                if not img_scale_raw or str(img_scale_raw).strip() == "":
                    img_scale_raw = _get_prop_value(props, "img_scale", "1.0")
                img_scale = float(_eval_num_expr(img_scale_raw, context, 1.0))

                bin_mode = self.get_input_value(node, 12, context)
                if not bin_mode or str(bin_mode).strip() == "":
                    bin_mode = str(_get_prop_value(props, "bin_mode", "Luminancia")).strip()

                mode = str(_get_prop_value(props, "modo", "Potrace")).strip()
                anchor = str(_get_prop_value(props, "anchor", "Center")).strip()
                invert_str = str(_get_prop_value(props, "invert", "Normal")).strip()
                invert = invert_str.lower() in ["invertido", "invert", "true", "1", "si", "yes"]

                invert_img_str = str(_get_prop_value(props, "invert_img", "Normal")).strip()
                use_inverted_img = invert_img_str.lower() in ["invertido", "invert", "true", "1", "si", "yes"]

                from img_tracer_engine import trace_image
                traced = trace_image(
                    image_path=img_path,
                    mode=mode,
                    threshold=threshold,
                    invert=invert,
                    tolerance=tolerance,
                    out_scale=out_scale,
                    out_w=out_w,
                    out_h=out_h,
                    anchor=anchor,
                    offset_x=offset_x,
                    offset_y=offset_y,
                    img_scale=img_scale,
                    bin_mode=bin_mode,
                    alphamax=alphamax,
                    opttoler=opttoler,
                    frame_index=frame_index,
                    invert_img=use_inverted_img
                )

                if output_slot_index == 1: return str(traced.get("width", 0.0))
                elif output_slot_index == 2: return str(traced.get("height", 0.0))
                elif output_slot_index == 3: return str(traced.get("points", 0))
                elif output_slot_index == 4: return str(traced.get("shapes_array", ""))
                elif output_slot_index == 5: return str(traced.get("total_frames", 1))
                return traced.get("shape", "")
            except Exception as e:
                return f"[Err IMG to Shape: {e}]"


        # ---------------------------------------------------------------------
        # 4. TIEMPO SINCRONIZADO (Multi-Slot: Extra ms, Sync End)
        # ---------------------------------------------------------------------
        elif node_type in ["Time/Synced Time", "Synced Time"]:
            try:
                line = None
                if isinstance(context, dict):
                    line = context.get('line') or context.get('active_line')
                    if not line and context.get('active_unit'):
                        line = getattr(context['active_unit'], 'line', None)
                
                p_const_raw = self.get_input_value(node, 0, context)
                if p_const_raw == "": p_const_raw = _get_prop_value(props, "progression_const", "0")
                p_const = _eval_num_expr(p_const_raw, context, 0.0)

                fade_raw = self.get_input_value(node, 1, context)
                if fade_raw == "": fade_raw = _get_prop_value(props, "fade_dur", "300")
                fade_dur = _eval_num_expr(fade_raw, context, 300.0)

                max_add_raw = self.get_input_value(node, 2, context)
                if max_add_raw == "": max_add_raw = _get_prop_value(props, "max_added_time", "2000")
                max_add = _eval_num_expr(max_add_raw, context, 2000.0)

                delay_raw = self.get_input_value(node, 3, context)
                if delay_raw == "": delay_raw = _get_prop_value(props, "delay", "250")
                delay = _eval_num_expr(delay_raw, context, 250.0)

                thresh_raw = self.get_input_value(node, 4, context)
                if thresh_raw == "": thresh_raw = _get_prop_value(props, "max_gap_threshold", "3000")
                max_gap = _eval_num_expr(thresh_raw, context, 3000.0)

                from nodes.time_nodes import time_synchronized_extra_node
                final_extra = time_synchronized_extra_node(
                    context,
                    progression_const=p_const,
                    fade_dur=fade_dur,
                    max_added_time=max_add,
                    delay=delay,
                    max_gap_threshold=max_gap
                )

                line_end = getattr(line, 'end_time', getattr(line, 'end', 0)) if line else 0
                sync_end = line_end + final_extra

                if output_slot_index == 1: return str(round(sync_end, 2))
                return str(round(final_extra, 2))
            except Exception as e:
                return f"[Err Tiempo Sincronizado: {e}]"

        # ---------------------------------------------------------------------
        # 4B. BORDES CONCÉNTRICOS (Multi-Slot: Forma, \pos, Índice, Total)
        # ---------------------------------------------------------------------
        elif node_type in ["Shape/Concentric Borders", "Concentric Borders"]:
            try:
                shp_raw = self.get_input_value(node, 0, context)
                if shp_raw == "": shp_raw = str(_get_prop_value(props, "shape", "")).strip()

                mode_raw = self.get_input_value(node, 1, context)
                if mode_raw == "": mode_raw = str(_get_prop_value(props, "modo", _get_prop_value(props, "mode", "Hueco (borders)"))).strip()

                loops_raw = self.get_input_value(node, 2, context)
                if loops_raw == "": loops_raw = str(_get_prop_value(props, "loop_count", _get_prop_value(props, "max_rings", "5"))).strip()

                sep_raw = self.get_input_value(node, 3, context)
                if sep_raw == "": sep_raw = str(_get_prop_value(props, "separation", "5")).strip()

                ov_raw = self.get_input_value(node, 4, context)
                if ov_raw == "": ov_raw = str(_get_prop_value(props, "overlap", _get_prop_value(props, "solape", "0.5"))).strip()

                anchor_raw = self.get_input_value(node, 5, context)
                if anchor_raw == "": anchor_raw = str(_get_prop_value(props, "anchor", _get_prop_value(props, "anclaje", "relativo"))).strip()

                out_mode_raw = str(_get_prop_value(props, "out_mode", _get_prop_value(props, "tipo_salida", "Shape"))).strip()

                from nodes.shape_nodes import shape_concentric_borders_node
                ring_shp, pos_str, idx_ring, total_rings = shape_concentric_borders_node(
                    context,
                    shape=shp_raw,
                    separation=sep_raw,
                    overlap=ov_raw,
                    mode=mode_raw,
                    loop_count=loops_raw,
                    out_mode=out_mode_raw,
                    anchor=anchor_raw
                )

                if output_slot_index == 1:
                    parent_x = float(getattr(context.get('active_unit'), 'center', getattr(context.get('line'), 'center', 0.0))) if context else 0.0
                    parent_y = float(getattr(context.get('active_unit'), 'middle', getattr(context.get('line'), 'middle', 0.0))) if context else 0.0
                    return f"\\pos({round(parent_x, 2)},{round(parent_y, 2)})" if (parent_x != 0 or parent_y != 0) else pos_str
                elif output_slot_index == 2:
                    return str(idx_ring)
                elif output_slot_index == 3:
                    return str(total_rings)
                return ring_shp
            except Exception as e:
                return f"[Err Bordes Concéntricos: {e}]"

        # ---------------------------------------------------------------------
        # 4B2. SHAPE WALKER (Multi-Slot: Shape Out, \pos Tag, Angle \frz, Length, Tip X, Tip Y)
        # ---------------------------------------------------------------------
        elif node_type in ["Shape/Shape Walker", "Shape Walker"]:
            try:
                shp_raw = self.get_input_value(node, 0, context)
                if shp_raw == "": shp_raw = str(_get_prop_value(props, "shape", "")).strip()

                prog_raw = self.get_input_value(node, 1, context)
                if prog_raw == "": prog_raw = str(_get_prop_value(props, "progress", _get_prop_value(props, "progreso", "1.0"))).strip()

                start_raw = self.get_input_value(node, 2, context)
                if start_raw == "": start_raw = str(_get_prop_value(props, "start_t", _get_prop_value(props, "inicio", "0.0"))).strip()

                sub_raw = self.get_input_value(node, 3, context)
                if sub_raw == "": sub_raw = str(_get_prop_value(props, "subdivs", _get_prop_value(props, "subdivisiones", "30"))).strip()

                mode_raw = str(_get_prop_value(props, "modo", _get_prop_value(props, "mode", "Global (Continuo)"))).strip()
                inv_raw = str(_get_prop_value(props, "invert", _get_prop_value(props, "invertir", "0"))).strip()

                from nodes.shape_nodes import shape_walker_node
                cut_shp, pos_str, angle_deg, cut_len, tip_x, tip_y = shape_walker_node(
                    context,
                    shape=shp_raw,
                    progress=prog_raw,
                    start_t=start_raw,
                    mode=mode_raw,
                    invert=inv_raw,
                    subdivs=sub_raw
                )

                if output_slot_index == 1:
                    return pos_str
                elif output_slot_index == 2:
                    frz_val = f"{angle_deg:.2f}".rstrip('0').rstrip('.')
                    if not frz_val or frz_val == "-0" or frz_val.endswith('.'):
                        frz_val = "0"
                    return f"\\frz{frz_val}"
                elif output_slot_index == 3:
                    return str(cut_len)
                elif output_slot_index == 4:
                    return str(tip_x)
                elif output_slot_index == 5:
                    return str(tip_y)
                return cut_shp
            except Exception as e:
                return f"[Err Shape Walker: {e}]"

        # ---------------------------------------------------------------------
        # TEXT ON PATH (Multi-Slot: Tag Out, \pos Tag, Angle (\frz), X, Y, Length)
        # ---------------------------------------------------------------------
        elif node_type in ["Functions/Text on Path", "Text on Path", "Text/Text on Path"]:
            try:
                shp_raw = self.get_input_value(node, 0, context)
                if shp_raw == "": shp_raw = str(_get_prop_value(props, "shape", "")).strip()

                offset_raw = self.get_input_value(node, 1, context)
                if offset_raw == "": offset_raw = str(_get_prop_value(props, "offset", _get_prop_value(props, "desfase", "0"))).strip()

                extra_ang_raw = self.get_input_value(node, 2, context)
                if extra_ang_raw == "": extra_ang_raw = str(_get_prop_value(props, "extra_angle", _get_prop_value(props, "angulo_extra", "0"))).strip()

                sub_raw = self.get_input_value(node, 3, context)
                if sub_raw == "": sub_raw = str(_get_prop_value(props, "subdivs", _get_prop_value(props, "subdivisiones", "30"))).strip()

                mode_raw = str(_get_prop_value(props, "modo", _get_prop_value(props, "mode", "Center (Centrado)"))).strip()

                from nodes.text_nodes import text_on_path_node
                tag_out, pos_str, frz_str, x_val, y_val, total_len = text_on_path_node(
                    context,
                    shape=shp_raw,
                    mode=mode_raw,
                    offset=offset_raw,
                    extra_angle=extra_ang_raw,
                    subdivs=sub_raw
                )

                if output_slot_index == 1:
                    return pos_str
                elif output_slot_index == 2:
                    return frz_str
                elif output_slot_index == 3:
                    return str(x_val)
                elif output_slot_index == 4:
                    return str(y_val)
                elif output_slot_index == 5:
                    return str(total_len)
                return tag_out
            except Exception as e:
                return f"[Err Text on Path: {e}]"

        # ---------------------------------------------------------------------
        # 4C. CLIP GRADIENT (Multi-Slot: Clip ASS, Progreso 0-1, Índice, Total)
        # ---------------------------------------------------------------------
        elif node_type in ["Functions/Clip Gradient", "Shape/Clip Gradient", "Clip Gradient"]:
            try:
                num_clips_raw = self.get_input_value(node, 0, context)
                if num_clips_raw == "": num_clips_raw = str(_get_prop_value(props, "num_clips", _get_prop_value(props, "franjas", "5"))).strip()

                angle_raw = self.get_input_value(node, 1, context)
                if angle_raw == "": angle_raw = str(_get_prop_value(props, "angle", _get_prop_value(props, "angulo", "0"))).strip()

                pad_raw = self.get_input_value(node, 2, context)
                if pad_raw == "": pad_raw = str(_get_prop_value(props, "padding", "4")).strip()

                ov_raw = self.get_input_value(node, 3, context)
                if ov_raw == "": ov_raw = str(_get_prop_value(props, "overlap", _get_prop_value(props, "solape", "0.5"))).strip()

                order_raw = self.get_input_value(node, 4, context)
                if order_raw == "": order_raw = str(_get_prop_value(props, "order", _get_prop_value(props, "orden", "Normal"))).strip()

                out_mode_raw = str(_get_prop_value(props, "out_mode", _get_prop_value(props, "salida", "Clip"))).strip()

                from nodes.shape_nodes import clip_gradient_node
                clip_tag, progress_val, idx_clip, total_clips = clip_gradient_node(
                    context,
                    num_clips=num_clips_raw,
                    angle=angle_raw,
                    padding=pad_raw,
                    overlap=ov_raw,
                    order=order_raw,
                    out_mode=out_mode_raw
                )

                if output_slot_index == 1:
                    return str(progress_val)
                elif output_slot_index == 2:
                    return str(idx_clip)
                elif output_slot_index == 3:
                    return str(total_clips)
                return clip_tag
            except Exception as e:
                return f"[Err Clip Gradient: {e}]"

        # ---------------------------------------------------------------------
        # 4D. AUDIO MODULADOR (Multi-Slot: Tags Out, Valor Actual, Array Valores, RMS Promedio)
        # ---------------------------------------------------------------------
        elif node_type in ["Audio/Audio Modulator", "Audio Modulator"]:
            try:
                inputs_list = node.get("inputs", [])
                def get_val(port_name_or_aliases, default_val=""):
                    if isinstance(port_name_or_aliases, str):
                        aliases = [port_name_or_aliases]
                    else:
                        aliases = list(port_name_or_aliases)
                    for alias in aliases:
                        clean_alias = _clean_key(alias)
                        for i, inp_obj in enumerate(inputs_list):
                            inp_name = inp_obj.get("name", "")
                            if _clean_key(inp_name) == clean_alias or clean_alias in PROP_ALIAS_MAP.get(_clean_key(inp_name), []):
                                val = self.get_input_value(node, i, context)
                                if val != "": return val
                                if "value" in inp_obj and inp_obj["value"] is not None and str(inp_obj["value"]).strip() != "":
                                    return str(inp_obj["value"])
                    for alias in aliases:
                        clean_alias = _clean_key(alias)
                        prop_val = _get_prop_value(props, clean_alias, "")
                        if prop_val != "":
                            return str(prop_val)
                    return str(default_val)

                audio_path_raw = get_val(["Audio Path", "audio_path", "ruta"], "")
                tag_raw = get_val(["Tag", "tag_name", "tag"], "fscy")
                min_raw = get_val(["Min Val", "min_val", "min"], "100")
                max_raw = get_val(["Max Val", "max_val", "max"], "160")
                gain_raw = get_val(["Ganancia", "gain", "ganancia"], "1.0")
                step_raw = get_val(["Step ms", "step_ms", "paso"], "41.7")
                smooth_raw = get_val(["Smoothing", "smoothing", "suavizado"], "0.2")
                min_hz_raw = get_val(["Min Hz", "min_hz", "f_min"], "20")
                max_hz_raw = get_val(["Max Hz", "max_hz", "f_max"], "250")
                start_time_raw = get_val(["Start Time", "start_time", "st", "t_inicio", "inicio"], "")
                end_time_raw = get_val(["End Time", "end_time", "et", "t_fin", "fin"], "")
                modo_raw = str(_get_prop_value(props, "modo", _get_prop_value(props, "mode", "RMS (Volumen)"))).strip()

                from nodes.audio_nodes import audio_modulator_master
                res = audio_modulator_master(
                    context=context,
                    audio_path=audio_path_raw,
                    tag_name=tag_raw,
                    min_val=min_raw,
                    max_val=max_raw,
                    ganancia=gain_raw,
                    step_ms=step_raw,
                    smoothing=smooth_raw,
                    modo=modo_raw,
                    min_hz=min_hz_raw,
                    max_hz=max_hz_raw,
                    start_time=start_time_raw,
                    end_time=end_time_raw,
                    output_slot_index=output_slot_index
                )
                if output_slot_index == 2 and isinstance(res, list):
                    return res
                return str(res)
            except Exception as e:
                return f"[Err Audio Modulador: {e}]"

        # ---------------------------------------------------------------------
        # 4E. AUDIO WAVEFORM (Multi-Slot: Shape Out, \pos Tag, X Array, Y Array, Bandas Array)
        # ---------------------------------------------------------------------
        elif node_type in ["Audio/Audio Waveform", "Audio Waveform"]:
            try:
                inputs_list = node.get("inputs", [])
                def get_val(port_name_or_aliases, default_val=""):
                    if isinstance(port_name_or_aliases, str):
                        aliases = [port_name_or_aliases]
                    else:
                        aliases = list(port_name_or_aliases)
                    for alias in aliases:
                        clean_alias = _clean_key(alias)
                        for i, inp_obj in enumerate(inputs_list):
                            inp_name = inp_obj.get("name", "")
                            if _clean_key(inp_name) == clean_alias or clean_alias in PROP_ALIAS_MAP.get(_clean_key(inp_name), []):
                                val = self.get_input_value(node, i, context)
                                if val != "": return val
                                if "value" in inp_obj and inp_obj["value"] is not None and str(inp_obj["value"]).strip() != "":
                                    return str(inp_obj["value"])
                    for alias in aliases:
                        clean_alias = _clean_key(alias)
                        prop_val = _get_prop_value(props, clean_alias, "")
                        if prop_val != "":
                            return str(prop_val)
                    return str(default_val)

                audio_path_raw = get_val(["Audio Path", "audio_path", "ruta"], "")
                ancho_raw = get_val(["Ancho (px)", "Width", "ancho", "width"], "400")
                alto_raw = get_val(["Alto (px)", "Height", "alto", "height"], "60")
                muestras_raw = get_val(["Muestras / Barras", "Samples", "muestras", "samples"], "32")
                gain_raw = get_val(["Ganancia", "gain", "ganancia"], "1.0")
                grosor_raw = get_val(["Grosor (px)", "Thickness", "grosor", "thickness"], "2")
                escala_raw = get_val(["Scale", "escala", "scale"], "1.0")
                min_hz_raw = get_val(["Min Hz", "min_hz", "f_min"], "20")
                max_hz_raw = get_val(["Max Hz", "max_hz", "f_max"], "16000")
                start_time_raw = get_val(["Start Time", "start_time", "st", "t_inicio", "inicio"], "")
                end_time_raw = get_val(["End Time", "end_time", "et", "t_fin", "fin"], "")
                modo_raw = str(_get_prop_value(props, "modo", _get_prop_value(props, "mode", "Osciloscopio"))).strip()

                from nodes.audio_nodes import audio_waveform_master
                res = audio_waveform_master(
                    context=context,
                    audio_path=audio_path_raw,
                    modo=modo_raw,
                    ancho=ancho_raw,
                    alto=alto_raw,
                    muestras=muestras_raw,
                    ganancia=gain_raw,
                    grosor=grosor_raw,
                    min_hz=min_hz_raw,
                    max_hz=max_hz_raw,
                    escala=escala_raw,
                    start_time=start_time_raw,
                    end_time=end_time_raw,
                    output_slot_index=output_slot_index
                )
                if output_slot_index in (2, 3, 4) and isinstance(res, list):
                    return res
                return str(res)
            except Exception as e:
                return f"[Err Audio Waveform: {e}]"

        # ---------------------------------------------------------------------
        # 4F. TAG OSCILADOR (Multi-Slot: ASS String, Current Val, Keyframes, Values)
        # ---------------------------------------------------------------------
        elif node_type in ["Functions/Tag Oscillator", "Tag Oscillator"]:
            try:
                inputs_list = node.get("inputs", [])

                def get_val_by_name_or_prop(port_name, prop_key, default_val=""):
                    clean_target = _clean_key(port_name)
                    clean_prop = _clean_key(prop_key)

                    # 1. Search connected link on matching input port
                    for i, inp_obj in enumerate(inputs_list):
                        inp_name = inp_obj.get("name", "")
                        inp_prop = inp_obj.get("property", "")

                        if _clean_key(inp_name) == clean_target or _clean_key(inp_prop) == clean_prop or clean_prop == _clean_key(inp_name):
                            val = self.get_input_value(node, i, context)
                            if val is not None and str(val).strip() != "":
                                return val
                            if "value" in inp_obj and inp_obj["value"] is not None and str(inp_obj["value"]).strip() != "":
                                return str(inp_obj["value"])

                    # 2. Search node properties dictionary
                    prop_val = _get_prop_value(props, prop_key, "")
                    if prop_val is not None and str(prop_val).strip() != "":
                        return str(prop_val)

                    return default_val

                st_val = get_val_by_name_or_prop("Start Time", "start_time", "")
                et_val = get_val_by_name_or_prop("End Time", "end_time", "")
                step_val = get_val_by_name_or_prop("Step (ms)", "step_ms", "200.0")
                trans_val = get_val_by_name_or_prop("Trans (ms)", "trans_ms", "50.0")
                dc_val = get_val_by_name_or_prop("Duty Cycle", "duty_cycle", "")
                tags_val = get_val_by_name_or_prop("Tags", "tags", r"\fscx140\fscy140,\fscx100\fscy100")
                accel_val = get_val_by_name_or_prop("Accel", "accel", "1.0")
                dilat_step_val = get_val_by_name_or_prop("Dilate Step", "dilat_step_ms", "0.0")
                dilat_trans_val = get_val_by_name_or_prop("Dilate Trans", "dilat_trans_ms", "0.0")
                offset_seq_val = get_val_by_name_or_prop("Seq Offset", "offset_seq_ms", "0.0")
                rhythm_val = get_val_by_name_or_prop("Rhythm Pattern", "rhythm_pattern", "")

                mode_osc = str(_get_prop_value(props, "modo_oscilacion", _get_prop_value(props, "modo", "Onda"))).strip()
                mode_ord = str(_get_prop_value(props, "modo_orden", "Secuencial")).strip()

                from nodes.tag_nodes import tag_oscillator_node
                res = tag_oscillator_node(
                    context=context,
                    start_time=st_val,
                    end_time=et_val,
                    step_ms=step_val,
                    trans_ms=trans_val,
                    duty_cycle=dc_val,
                    tags=tags_val,
                    accel=accel_val,
                    dilat_step_ms=dilat_step_val,
                    dilat_trans_ms=dilat_trans_val,
                    offset_seq_ms=offset_seq_val,
                    rhythm_pattern=rhythm_val,
                    modo_oscilacion=mode_osc,
                    modo_orden=mode_ord,
                    output_slot_index=output_slot_index
                )
                if output_slot_index in (2, 3) and isinstance(res, list):
                    return res
                return str(res)
            except Exception as e:
                import traceback
                print(f"[Err Tag Oscilador]: {e}")
                traceback.print_exc()
                return f"[Err Tag Oscilador: {e}]"

        # ---------------------------------------------------------------------
        # 5. BENCHMARK MATH (Multi-Slot: Out, Time ms)
        # ---------------------------------------------------------------------
        elif node_type in ["System/Benchmark Math", "Benchmark Math"]:
            try:
                val_in = self.get_input_value(node, 0, context)
                if val_in == "": val_in = str(_get_prop_value(props, "val_in", _get_prop_value(props, "valor", "")))

                iter_raw = self.get_input_value(node, 1, context)
                if iter_raw == "": iter_raw = _get_prop_value(props, "iterations", "10000")
                iterations = max(1, int(_eval_num_expr(iter_raw, context, 10000.0)))

                complexity = str(self.get_input_value(node, 2, context) or _get_prop_value(props, "complexity", "Trig (sin/cos)"))

                import math, time
                t0 = time.perf_counter()
                acc = 1.0

                if "Prime" in complexity:
                    count = 0
                    for n in range(2, iterations + 500):
                        is_prime = True
                        for i in range(2, int(math.isqrt(n)) + 1):
                            if n % i == 0:
                                is_prime = False
                                break
                        if is_prime: count += 1
                    acc = count
                elif "Matrix" in complexity:
                    dim = 25
                    A = [[(i + j * 0.1) for j in range(dim)] for i in range(dim)]
                    B = [[(i * 0.2 - j) for j in range(dim)] for i in range(dim)]
                    for _ in range(max(1, iterations // 200)):
                        C = [[sum(A[i][k] * B[k][j] for k in range(dim)) for j in range(dim)] for i in range(dim)]
                        acc += C[0][0]
                else:
                    for i in range(1, iterations + 1):
                        acc += math.sin(i) * math.cos(i) + math.sqrt(i)

                elapsed_ms = (time.perf_counter() - t0) * 1000.0

                if output_slot_index == 1: return f"{elapsed_ms:.2f}"
                return str(val_in) if val_in != "" else f"[Bench: {elapsed_ms:.2f}ms]"
            except Exception as e:
                return f"[Err Bench: {e}]"

        # ---------------------------------------------------------------------
        # 6. PARTÍCULAS / BORD TO PIXELS (Multi-Slot: Text Out, \pos Tag, X, Y, Total)
        # ---------------------------------------------------------------------
        elif node_type in ["Functions/Particles", "Particles"]:
            try:
                shp = self.get_input_value(node, 0, context)
                if shp == "": shp = str(_get_prop_value(props, "shape", "")).strip()

                p_shp = self.get_input_value(node, 1, context)
                if p_shp == "": p_shp = str(_get_prop_value(props, "particle_shape", "")).strip()

                density = self.get_input_value(node, 2, context)
                if density == "": density = str(_get_prop_value(props, "density", "5.0")).strip()

                redraw = self.get_input_value(node, 3, context)
                if redraw == "": redraw = str(_get_prop_value(props, "redraw_dist", "0")).strip()

                seed = self.get_input_value(node, 4, context)
                if seed == "": seed = str(_get_prop_value(props, "seed", "1")).strip()

                scale = self.get_input_value(node, 5, context)
                if scale == "": scale = str(_get_prop_value(props, "scale", "1.0")).strip()

                order = self.get_input_value(node, 6, context)
                if order == "": order = str(_get_prop_value(props, "order", "79")).strip()

                modo = str(_get_prop_value(props, "modo", "Contorno v2")).strip()

                from particle_nodes import particle_text_node
                abs_x, abs_y, particle_ass_shape, total_pts = particle_text_node(
                    context, shape=shp, particle_shape=p_shp, density=density, redraw_dist=redraw, seed=seed, scale=scale, mode=modo, order=order
                )

                if output_slot_index == 1: return f"\\pos({abs_x},{abs_y})"
                elif output_slot_index == 2: return str(abs_x)
                elif output_slot_index == 3: return str(abs_y)
                elif output_slot_index == 4: return str(total_pts)
                # Slot 0 (Text Out): Todo listo con \pos y forma vectorial
                return f"{{\\pos({abs_x},{abs_y})}}{particle_ass_shape}"
            except Exception as e:
                return f"[Err Partículas: {e}]"

        # ---------------------------------------------------------------------
        # 7. IMAGEN A PARTÍCULAS (Multi-Slot: Text Out, Color Arr, \pos Tag, X, Y, Total)
        # ---------------------------------------------------------------------
        elif node_type in ["Functions/IMG to Pixels", "IMG to pixels"]:
            try:
                img_path = self.get_input_value(node, 0, context)
                if img_path == "": img_path = str(_get_prop_value(props, "image_path", "")).strip()

                p_shp = self.get_input_value(node, 1, context)
                if p_shp == "": p_shp = str(_get_prop_value(props, "particle_shape", "")).strip()

                frame = self.get_input_value(node, 2, context)
                if frame == "": frame = str(_get_prop_value(props, "frame", "j")).strip()

                step = self.get_input_value(node, 3, context)
                if step == "": step = str(_get_prop_value(props, "step", "2")).strip()

                alpha_th = self.get_input_value(node, 4, context)
                if alpha_th == "": alpha_th = str(_get_prop_value(props, "alpha_threshold", "128")).strip()

                scale = self.get_input_value(node, 5, context)
                if scale == "": scale = str(_get_prop_value(props, "scale", "1.0")).strip()

                anchor = self.get_input_value(node, 6, context)
                if anchor == "": anchor = str(_get_prop_value(props, "anchor", "Center")).strip()

                order = self.get_input_value(node, 7, context)
                if order == "": order = str(_get_prop_value(props, "order", "79")).strip()

                from particle_nodes import particle_image_node
                abs_x, abs_y, col_ass, alpha_ass, p_shape, total_px = particle_image_node(
                    context, image_path=img_path, particle_shape=p_shp, frame=frame, step=step, alpha_threshold=alpha_th, scale=scale, anchor=anchor, order=order
                )

                if output_slot_index == 1: return col_ass
                elif output_slot_index == 2: return f"\\pos({abs_x},{abs_y})"
                elif output_slot_index == 3: return str(abs_x)
                elif output_slot_index == 4: return str(abs_y)
                elif output_slot_index == 5: return str(total_px)
                elif output_slot_index == 6:
                    return f"{{\\pos({abs_x},{abs_y})\\1c{col_ass}\\1a{alpha_ass}}}{p_shape}"
                # Slot 0 (Text Out): Combo completo con \pos, color fiel (\1c), alpha (\1a) y forma vectorial
                return f"{{\\pos({abs_x},{abs_y})\\1c{col_ass}\\1a{alpha_ass}}}{p_shape}"
            except Exception as e:
                return f"[Err Imagen Partículas: {e}]"

        if node_type in ["Loops/Module", "Module"]:
            in_i = self.get_input_value(node, 0, context)
            in_n = self.get_input_value(node, 1, context)
            in_m = self.get_input_value(node, 2, context)

            raw_i = in_i if (in_i is not None and str(in_i).strip() != "") else _get_prop_value(props, "iter", _get_prop_value(props, "i", "i"))
            raw_n = in_n if (in_n is not None and str(in_n).strip() != "") else _get_prop_value(props, "total", _get_prop_value(props, "N", "N"))
            raw_m = in_m if (in_m is not None and str(in_m).strip() != "") else _get_prop_value(props, "sub_m", _get_prop_value(props, "m", "0"))

            val_i = float(_eval_num_expr(raw_i, context, 1.0))
            val_n = float(_eval_num_expr(raw_n, context, 1.0))
            val_m = float(_eval_num_expr(raw_m, context, 0.0))

            denom = val_n + val_m - 1.0
            res = (val_i - 1.0 + val_m) / denom if (denom != 0 and val_n > 1.0) else val_m
            res_rounded = round(res, 4)
            if res_rounded == int(res_rounded):
                return str(int(res_rounded))
            return f"{res_rounded:.4f}".rstrip('0').rstrip('.')

        if node_type in ["Variables/Sys Var", "Sys Var"]:
            v_name = str(_get_prop_value(props, "var_name", _get_prop_value(props, "mode", _get_prop_value(props, "modo", "syl.text")))).strip()
            clean_v = v_name.lower().replace("fx.", "")

            if clean_v in ["module", "m"]:
                mod_val = round(float(context.get("module", 0.0)), 4)
                if mod_val == int(mod_val):
                    return str(int(mod_val))
                return f"{mod_val:.4f}".rstrip('0').rstrip('.')

            return str(_eval_sys_var(v_name, context))

        if node_type in ["String"]:
            val = _get_prop_value(props, "valor", _get_prop_value(props, "value", _get_prop_value(props, "text", _get_prop_value(props, "texto", ""))))
            return str(val) if val is not None else ""
            
        if node_type in ["Number"]:
            raw_val = _get_prop_value(props, "valor", _get_prop_value(props, "value", 0))
            res = _eval_num_expr(raw_val, context, default=0.0)
            if isinstance(res, float) and res.is_integer():
                return str(int(res))
            return f"{res:.4f}".rstrip('0').rstrip('.')

        # ---------------------------------------------------------------------
        # REGISTRO GENÉRICO DE NODOS PYXIS
        # ---------------------------------------------------------------------
        if node_type in NODE_REGISTRY:
            func = NODE_REGISTRY[node_type]
            expected_inputs = PYXIS_DB.get(category, {}).get(name, [])
            args = []
            for i, input_name in enumerate(expected_inputs):
                val = self.get_input_value(node, i, context)
                if val == "":
                    val_str = str(_get_prop_value(props, input_name, "")).strip()
                    if val_str in context: val = str(context[val_str])
                    else:
                        try:
                            if '.' in val_str:
                                obj_name, attr = val_str.split('.')
                                if obj_name in context and hasattr(context[obj_name], attr): val = str(getattr(context[obj_name], attr))
                                else: val = val_str
                            else: val = val_str
                        except Exception: val = val_str
                args.append(val)
                
            try:
                return str(func(context, *args))
            except Exception as e:
                import traceback
                print(f"[Pyxis Node Error] Exception in '{node_type}': {e}")
                traceback.print_exc()
                return f"[Err {name}]"

        if node_type == "Variables/Get Var":
            return context.get(props.get("var_name", ""), "")

        elif node_type in ["Variables/Memory", "Memory"]:
            mode = str(props.get("modo", props.get("mode", "Remember (Guardar)"))).strip()
            key_val = self.get_input_value(node, 0, context)
            if key_val == "": key_val = str(props.get("clave", props.get("key", "ref"))).strip()
            
            input_val = self.get_input_value(node, 1, context)
            if input_val == "": input_val = str(props.get("valor", props.get("default", ""))).strip()
            
            if "Remember" in mode or "Guardar" in mode:
                return str(self.remember(key_val, input_val))
            else:
                return str(self.recall(key_val, input_val))

        elif node_type in ["Loops/Main Loop", "Main Loop"] or (isinstance(node_type, str) and node_type.endswith("Main Loop")):
            unit = context.get('active_unit')
            if output_slot_index == 1:
                return str(getattr(unit, 'i', 1) if unit else 1)
            elif output_slot_index == 2:
                return str(getattr(unit, 'n', 1) if unit else 1)
            return ""

        elif node_type in ["Loops/MaxLoop", "MaxLoop"] or (isinstance(node_type, str) and node_type.endswith("MaxLoop")):
            props = node.get("properties", {})
            var_name = str(props.get("var_name", "j")).strip() or "j"
            if output_slot_index == 1:
                return str(context.get(var_name, context.get('j', context.get('fx_i', 1))))
            elif output_slot_index == 2:
                return str(context.get(var_name + '_max', context.get('j_max', context.get('fx_n', 1))))
            return ""

        elif node_type in ["Color Picker"]:
            try:
                from utils import parse_color_to_rgb, rgb_to_ass_color, rgb_to_hex_color
                colors = props.get("colors")
                if not isinstance(colors, list) or len(colors) == 0:
                    colors = []
                    idx = 0
                    while f"color_{idx}" in props:
                        colors.append(props[f"color_{idx}"])
                        idx += 1
                    if not colors:
                        colors = [props.get("color", "#FFFFFF")]

                formats = props.get("formats")
                if not isinstance(formats, list) or len(formats) == 0:
                    formats = []
                    idx = 0
                    while f"format_{idx}" in props:
                        formats.append(props[f"format_{idx}"])
                        idx += 1
                    if not formats:
                        formats = ["ASS"] * len(colors)

                slot_idx = output_slot_index if (output_slot_index is not None and output_slot_index < len(colors)) else 0
                hex_color = str(colors[slot_idx]).strip()
                r, g, b = parse_color_to_rgb(hex_color)

                slot_fmt = str(formats[slot_idx] if slot_idx < len(formats) else "ASS").upper()
                if slot_fmt in ["HEX", "HTML", "#"]:
                    return rgb_to_hex_color(r, g, b)
                else:
                    return rgb_to_ass_color(r, g, b)
            except Exception as e:
                import traceback
                print(f"[Pyxis Engine Error] Color Picker evaluation failed: {e}")
                traceback.print_exc()
                return "&HFFFFFF&"
        
        elif node_type in ["Concatenate"]: 
            inputs_count = len(node.get('inputs', []))
            values = []
            for i in range(inputs_count):
                val = self.get_input_value(node, i, context)
                if val == "":
                    val = props.get(f"In{i+1}", "")
                if val != "": 
                    values.append(str(val))
            sep = str(props.get("separador", "nil")).strip().lower()
            if sep in ("nil", "", "none"):
                sep = ""
            elif sep in ("espacio", "space", " "):
                sep = " "
            elif sep in ("coma", ","):
                sep = ","
            elif sep in ("punto_coma", "punto y coma", ";"):
                sep = ";"
            elif sep in ("salto", "\\n", "\n"):
                sep = "\n"
            return sep.join(values)

        elif node_type in ["Functions/Interpolator", "Interpolator"]:
            try:
                raw_i = self.get_input_value(node, 0, context)
                if raw_i == "": raw_i = _get_prop_value(props, "iterador", "i")
                str_i = str(raw_i).strip().lower()
                if str_i in ["i", "iterador"]:
                    val_i = float(context.get("i", context.get("fx_i", 1.0))) if isinstance(context, dict) else 1.0
                elif str_i in ["j", "loop"]:
                    val_i = float(context.get("j", context.get("fx_i", 1.0))) if isinstance(context, dict) else 1.0
                else:
                    val_i = float(_eval_num_expr(raw_i, context, 1.0))

                raw_n = self.get_input_value(node, 1, context)
                if raw_n == "": raw_n = _get_prop_value(props, "total", "N")
                str_n = str(raw_n).strip().lower()
                if str_n in ["n", "total", "max"]:
                    val_n = float(context.get("n", context.get("fx_n", context.get("maxloop", 1.0)))) if isinstance(context, dict) else 1.0
                elif str_n in ["j_max", "max_j", "maxloop"]:
                    val_n = float(context.get("j_max", context.get("maxloop", 1.0))) if isinstance(context, dict) else 1.0
                else:
                    val_n = float(_eval_num_expr(raw_n, context, 1.0))

                raw_accel = self.get_input_value(node, 2, context)
                if raw_accel == "": raw_accel = _get_prop_value(props, "accel", "1.0")
                accel_val = max(0.001, float(_eval_num_expr(raw_accel, context, 1.0)))

                # Determine progress t (0.0 to 1.0)
                if 0.0 <= val_i <= 1.0 and (raw_n == "" or val_n == 1.0):
                    t_val = val_i
                else:
                    if val_n > 1.0:
                        t_val = (val_i - 1.0) / (val_n - 1.0)
                    else:
                        t_val = 0.0

                t_val = max(0.0, min(1.0, t_val))

                # Apply smooth acceleration / deceleration (Penner conjugated power law):
                # accel > 1.0 -> ease-in: t^accel (starts at 0 speed, accelerates)
                # accel < 1.0 -> ease-out: 1 - (1 - t)^(1/accel) (finite slope at t=0, decelerates smoothly without gaps)
                # accel == 1.0 -> linear: t
                if accel_val != 1.0 and 0.0 < t_val < 1.0:
                    if accel_val > 1.0:
                        t_val = t_val ** accel_val
                    elif accel_val > 0.0:
                        p = 1.0 / accel_val
                        t_val = 1.0 - ((1.0 - t_val) ** p)

                inputs_count = len(node.get('inputs', []))
                val_list = []
                for i in range(3, inputs_count):
                    val = self.get_input_value(node, i, context)
                    if val == "":
                        inp = node['inputs'][i]
                        prop_name = inp.get('property') or inp.get('name', '').lower()
                        val = _get_prop_value(props, prop_name, "")
                    if val != "": val_list.append(val)

                if len(val_list) < 2:
                    p_v1 = str(_get_prop_value(props, "v1", "0")).strip()
                    p_v2 = str(_get_prop_value(props, "v2", "1")).strip()
                    val_list = [p_v1, p_v2]

                if not val_list:
                    return ""
                if len(val_list) == 1:
                    return str(val_list[0])
                
                n_segments = len(val_list) - 1
                scaled_t = t_val * n_segments
                seg_idx = int(scaled_t)
                if seg_idx >= n_segments:
                    seg_idx = n_segments - 1
                    local_t = 1.0
                else:
                    local_t = scaled_t - seg_idx
                
                v1, v2 = val_list[seg_idx], val_list[seg_idx + 1]
                str1, str2 = str(v1).strip(), str(v2).strip()
                
                # Alpha interpolation (&HAA&)
                if str1.startswith("&H") and str1.endswith("&") and len(str1) <= 6 and str2.startswith("&H") and str2.endswith("&") and len(str2) <= 6:
                    try:
                        a1 = int(str1[2:-1], 16)
                        a2 = int(str2[2:-1], 16)
                        a = max(0, min(255, int(round(a1 + (a2 - a1) * local_t))))
                        return f"&H{a:02X}&"
                    except Exception:
                        pass

                # Color interpolation
                if (str1.startswith("&H") or str1.startswith("#")) and (str2.startswith("&H") or str2.startswith("#")):
                    try:
                        from utils import parse_color_to_rgb, rgb_to_ass_color, rgb_to_hex_color
                        r1, g1, b1 = parse_color_to_rgb(str1)
                        r2, g2, b2 = parse_color_to_rgb(str2)
                        r = int(round(r1 + (r2 - r1) * local_t))
                        g = int(round(g1 + (g2 - g1) * local_t))
                        b = int(round(b1 + (b2 - b1) * local_t))
                        if str1.startswith("#"):
                            return rgb_to_hex_color(r, g, b)
                        else:
                            return rgb_to_ass_color(r, g, b)
                    except Exception:
                        pass

                # Vector Shape Continuous Morphing (ASS drawing commands m, l, b, c, n)
                if re.search(r'\bm\s+-?\d+', str1) or re.search(r'\bm\s+-?\d+', str2):
                    try:
                        from clipper_engine import ClipperEngine
                        import numpy as np
                        cnts1 = ClipperEngine.parse_assdraw(str1)
                        cnts2 = ClipperEngine.parse_assdraw(str2)
                        if cnts1 and cnts2:
                            all_pts1 = np.vstack(cnts1)
                            all_pts2 = np.vstack(cnts2)
                            target_count = max(len(all_pts1), len(all_pts2), 30)

                            def _resample(pts, count):
                                if len(pts) < 2:
                                    return np.repeat(pts, count, axis=0)
                                diffs = np.diff(pts, axis=0)
                                dists = np.hypot(diffs[:, 0], diffs[:, 1])
                                cum = np.insert(np.cumsum(dists), 0, 0.0)
                                tot = cum[-1]
                                if tot <= 1e-6:
                                    return np.repeat(pts[:1], count, axis=0)
                                sdists = np.linspace(0.0, tot, count)
                                rx = np.interp(sdists, cum, pts[:, 0])
                                ry = np.interp(sdists, cum, pts[:, 1])
                                return np.column_stack((rx, ry))

                            r1 = _resample(all_pts1, target_count)
                            r2 = _resample(all_pts2, target_count)
                            morphed = (1.0 - local_t) * r1 + local_t * r2
                            parts = [f"m {round(morphed[0,0],2)} {round(morphed[0,1],2)}"]
                            for p in morphed[1:]:
                                parts.append(f"l {round(p[0],2)} {round(p[1],2)}")
                            return " ".join(parts)
                    except Exception:
                        pass

                # Numeric interpolation (numbers or context expressions like l.left, l.left+l.width, syl.x)
                try:
                    def _to_num(val_raw):
                        try:
                            return float(val_raw)
                        except (ValueError, TypeError):
                            pass
                        res = _eval_num_expr(val_raw, context, default=None)
                        if res is not None:
                            try:
                                return float(res)
                            except (ValueError, TypeError):
                                pass
                        return None

                    n1 = _to_num(v1)
                    n2 = _to_num(v2)
                    if n1 is not None and n2 is not None:
                        res = n1 + (n2 - n1) * local_t
                        if float(n1).is_integer() and float(n2).is_integer() and float(res).is_integer():
                            return str(int(res))
                        return f"{res:.2f}".rstrip('0').rstrip('.')
                except Exception:
                    pass

                return str(v1 if local_t < 0.5 else v2)
            except Exception as e:
                return f"[Err Interpolador: {e}]"

    def _update_progress(self, progress_tracker, progress_callback):
        if not progress_tracker or not callable(progress_callback):
            return
        progress_tracker['current'] += 1
        curr = progress_tracker['current']
        total = max(1, progress_tracker.get('total', 1))

        has_audio = getattr(self, '_has_audio_nodes', False)
        base_min_pct = 25 if has_audio else 5
        pct = min(89, base_min_pct + int((curr / total) * (89 - base_min_pct)))

        now = time.time()
        last_pct = progress_tracker.get('last_pct', 0)
        last_time = progress_tracker.get('last_time', 0.0)
        t_start = progress_tracker.get('start_time')
        if not t_start:
            progress_tracker['start_time'] = now
            t_start = now

        current_lines = len(self.all_generated_lines)
        if (pct > last_pct and (now - last_time >= 0.02 or pct - last_pct >= 1)) or (now - last_time >= 0.05) or (current_lines > 0 and current_lines % 25 == 0) or total <= 30:
            progress_tracker['last_pct'] = pct
            progress_tracker['last_time'] = now
            elapsed = max(0.001, now - t_start)
            speed = int(current_lines / elapsed) if elapsed > 0.05 else 0
            progress_callback({
                "percent": max(base_min_pct, pct),
                "lines_generated": current_lines,
                "total_units": total,
                "current_unit": curr,
                "speed": speed,
                "phase": f"Generando... {current_lines:,} líneas ({speed} l/s)" if speed > 0 else f"Generando... {current_lines:,} líneas"
            })

    def execute_loops_recursive(self, chain, context, output_node, active_unit=None, check_cancel=None, progress_tracker=None, progress_callback=None):
        if self.is_cancelled:
            return
        if getattr(self, 'shared_cancel_flag', None) is not None and getattr(self.shared_cancel_flag, 'value', False):
            self.is_cancelled = True
            return

        if not chain:
            if not context.get('in_auto_slicer_loop'):
                dummy_ctx = context.copy()
                dummy_ctx['in_auto_slicer_loop'] = True
                self.get_input_value(output_node, 4, dummy_ctx)
                self.get_input_value(output_node, 5, dummy_ctx)
                auto_n = dummy_ctx.get('maxloop', 1)
                if auto_n > 1:
                    for auto_j in range(1, auto_n + 1):
                        if self.is_cancelled: break
                        loop_ctx = context.copy()
                        loop_ctx['in_auto_slicer_loop'] = True
                        loop_ctx['p_i'] = auto_j
                        loop_ctx['p_n'] = auto_n
                        loop_ctx['p_max'] = auto_n
                        loop_ctx['particle_i'] = auto_j
                        loop_ctx['particle_n'] = auto_n
                        loop_ctx['particle_max'] = auto_n
                        loop_ctx['total_pixels'] = auto_n
                        if 'j' not in context:
                            loop_ctx['j'] = auto_j
                            loop_ctx['j_max'] = auto_n
                        loop_ctx['fx_i'] = auto_j
                        loop_ctx['fx_n'] = auto_n
                        self.execute_loops_recursive([], loop_ctx, output_node, active_unit, check_cancel, progress_tracker, progress_callback)
                    return
            # Pre-evaluar nodos de Memoria y Código Script para la iteración del contexto actual
            for n_id, n_obj in self.nodes.items():
                node_type = n_obj.get('type', '')
                if node_type in ['Variables/Memory', 'Memory']:
                    mode = str(n_obj.get('properties', {}).get('modo', n_obj.get('properties', {}).get('mode', ''))).strip()
                    if 'Remember' in mode or 'Guardar' in mode:
                        self.evaluate_data_node(n_id, context)
                elif node_type in ['System/Script Code', 'Script Code']:
                    self.evaluate_data_node(n_id, context)

            props = output_node.get('properties', {})
            origin_align = 5
            try:
                origin_align = int(props.get('origin_align', 5))
                if origin_align < 1 or origin_align > 9:
                    origin_align = 5
            except Exception:
                origin_align = 5
            context['origin_align'] = origin_align
            context['fx_align'] = origin_align

            u_left = float(context.get('val_left', getattr(active_unit, 'left', getattr(active_unit, 'center', 0.0)) if active_unit else 0.0))
            u_center = float(context.get('val_center', getattr(active_unit, 'center', 0.0) if active_unit else 0.0))
            u_right = float(context.get('val_right', getattr(active_unit, 'right', getattr(active_unit, 'center', 0.0)) if active_unit else 0.0))
            u_top = float(context.get('val_top', getattr(active_unit, 'top', getattr(active_unit, 'middle', 0.0)) if active_unit else 0.0))
            u_middle = float(context.get('val_middle', getattr(active_unit, 'middle', 0.0) if active_unit else 0.0))
            u_bottom = float(context.get('val_bottom', getattr(active_unit, 'bottom', getattr(active_unit, 'middle', 0.0)) if active_unit else 0.0))

            if origin_align in (7, 4, 1):
                orig_x = u_left
            elif origin_align in (9, 6, 3):
                orig_x = u_right
            else:
                orig_x = u_center

            if origin_align in (7, 8, 9):
                orig_y = u_top
            elif origin_align in (1, 2, 3):
                orig_y = u_bottom
            else:
                orig_y = u_middle

            context['fx_pos_x'] = round(orig_x, 3)
            context['fx_pos_y'] = round(orig_y, 3)

            layer_in = self.get_input_value(output_node, 1, context)
            st_in = self.get_input_value(output_node, 2, context)
            et_in = self.get_input_value(output_node, 3, context)

            # Pre-evaluar y propagar el rango de tiempo del efecto de Salida para que los nodos (ej. Tag Oscilador) lo hereden por defecto
            _, st_tmp, et_tmp, _, _ = self._apply_defaults(
                active_unit, layer_in, st_in, et_in, "", "", context=context
            )
            eff_dur = max(1.0, float(et_tmp) - float(st_tmp))
            context["effect_st"] = float(st_tmp)
            context["effect_et"] = float(et_tmp)
            context["effect_dur"] = eff_dur
            context["fx_st"] = float(st_tmp)
            context["fx_et"] = float(et_tmp)
            context["fx_dur"] = eff_dur
            context["fx_start_time"] = float(st_tmp)
            context["fx_end_time"] = float(et_tmp)

            tags_str = self.get_input_value(output_node, 4, context)
            retorno_str = self.get_input_value(output_node, 5, context)
            queue_id = self.get_input_value(output_node, 6, context)
            if _is_empty_value(queue_id):
                for k in ['queue_id', 'actor', 'Queue ID', 'Queue_ID', 'queue']:
                    if k in props and not _is_empty_value(props[k]):
                        queue_id = str(props[k]).strip()
                        break

            queue_order = self.get_input_value(output_node, 7, context)
            if _is_empty_value(queue_order):
                for k in ['queue_order', 'orden_cola', 'orden', 'order', 'Queue Order', 'Queue_Order']:
                    if k in props and not _is_empty_value(props[k]):
                        queue_order = props[k]
                        break

            if not self.is_port_connected(output_node, 5): 
                retorno_str = getattr(active_unit, 'text_stripped', '')
            
            # Auto-extracción y fusión limpia (deduplicada) de TODOS los tags embebidos en retorno_str {\tag...}
            embedded_tags_list = []
            while retorno_str and str(retorno_str).strip().startswith("{"):
                ret_s = str(retorno_str).strip()
                close_brace = ret_s.find("}")
                if close_brace == -1: break
                embedded_tags_list.append(ret_s[1:close_brace])
                retorno_str = ret_s[close_brace + 1:]

            embedded_tags_combined = "".join(embedded_tags_list)
            tags_str = merge_ass_tags(return_tags_str=embedded_tags_combined, port_tags_str=tags_str)

            layer, st, et, tags_str, retorno_str = self._apply_defaults(
                active_unit, layer_in, st_in, et_in, tags_str, retorno_str, context=context
            )

            if not _final_text_has_content(retorno_str) and not str(tags_str).strip(): return

            queue_id = queue_id.strip() if queue_id else "default"
            queue_order = _to_int_or_default(queue_order, 0, context=context)

            pyxis_line = context['line']
            ass_line = {
                'layer': layer,
                'start_time': st,
                'end_time': et,
                'style_name': pyxis_line.style_name,
                'actor': queue_id,
                'margin_l': pyxis_line.margin_l,
                'margin_r': pyxis_line.margin_r,
                'margin_v': pyxis_line.margin_v,
                'effect': 'pyxis_fx',
                'text': f"{{{tags_str}}}{retorno_str}",
                'queue_id': queue_id,
                'queue_order': queue_order
            }
            self.all_generated_lines.append(ass_line)
            
            # Conteo de líneas por lotes en memoria compartida (IPC ultra-liviano a 30 FPS)
            self._local_line_batch = getattr(self, '_local_line_batch', 0) + 1
            if self._local_line_batch >= 25:
                if getattr(self, 'shared_line_counter', None) is not None:
                    try:
                        with self.shared_line_counter.get_lock():
                            self.shared_line_counter.value += self._local_line_batch
                    except Exception:
                        pass
                self._local_line_batch = 0
                if progress_tracker and callable(progress_callback):
                    self._update_progress(progress_tracker, progress_callback)

            # Comprobación de cancelación cada 10 líneas generadas
            if len(self.all_generated_lines) % 10 == 0:
                cancel_signal = False
                if getattr(self, 'shared_cancel_flag', None) is not None and getattr(self.shared_cancel_flag, 'value', False):
                    cancel_signal = True
                elif callable(check_cancel) and check_cancel():
                    cancel_signal = True
                if cancel_signal:
                    self.is_cancelled = True
            return

        current_loop = chain[0]
        rest_chain = chain[1:]

        is_noblank = "Con Blanks" not in str(
            current_loop.get('noblank') or 
            current_loop.get('properties', {}).get('noblank') or 
            output_node.get('properties', {}).get('noblank', 'No Blank')
        )

        if current_loop['type'] == 'base':
            base_type, pyxis_line = current_loop['val'], context['line']
            if base_type == "line":
                self.bind_active_unit(context, pyxis_line, is_noblank=is_noblank)
                self.execute_loops_recursive(rest_chain, context, output_node, pyxis_line, check_cancel, progress_tracker, progress_callback)
                self._update_progress(progress_tracker, progress_callback)
            elif base_type in ["syl", "word", "char"]:
                for unit in getattr(pyxis_line, base_type + "s", []):
                    if self.is_cancelled: break
                    if is_noblank and (getattr(unit, 'is_blank', False) or not _has_visible_content(unit)): continue
                    if not _has_visible_content(unit): continue
                    ctx = context.copy()
                    ctx[base_type] = unit
                    if base_type == 'char':
                        if getattr(unit, 'syl', None): ctx['syl'] = unit.syl
                        if getattr(unit, 'word', None):
                            ctx['word'] = unit.word
                        elif getattr(unit, 'syl', None) and getattr(unit.syl, 'word', None):
                            ctx['word'] = unit.syl.word
                    elif base_type == 'syl':
                        if getattr(unit, 'word', None):
                            ctx['word'] = unit.word
                        elif getattr(unit, 'chars', None) and len(unit.chars) > 0 and getattr(unit.chars[0], 'word', None):
                            ctx['word'] = unit.chars[0].word
                    elif base_type == 'word':
                        if getattr(unit, 'chars', None) and len(unit.chars) > 0 and getattr(unit.chars[0], 'syl', None):
                            ctx['syl'] = unit.chars[0].syl
                    self.bind_active_unit(ctx, unit, is_noblank=is_noblank)
                    self.execute_loops_recursive(rest_chain, ctx, output_node, unit, check_cancel, progress_tracker, progress_callback)
                    self._update_progress(progress_tracker, progress_callback)
                    
        elif current_loop['type'] == 'maxloop':
            modo = str(current_loop.get('modo', current_loop.get('mode', 'Normal'))).strip().lower()
            var_name = current_loop.get('var_name', 'j')
            
            is_fbf = ("fbf" in modo) or ("frame" in modo)
            
            if is_fbf:
                maxloop_node = current_loop.get('node')

                step_val = current_loop.get('step_ms') or current_loop.get('val') or 41.7
                try:
                    step_ms = max(1.0, float(_eval_num_expr(step_val, context, default=41.7)))
                except Exception:
                    step_ms = 41.7

                default_st = float(getattr(active_unit, 'start_time', context.get('start_time', 0.0)))
                default_et = float(getattr(active_unit, 'end_time', context.get('end_time', 0.0)))

                raw_st = ""
                if maxloop_node:
                    raw_st = self.get_input_value(maxloop_node, 1, context)
                if not raw_st:
                    raw_st = str(current_loop.get('start_time') or '').strip()

                if raw_st and raw_st.lower() not in ["start_time", "st", ""]:
                    try:
                        unit_st = float(_eval_num_expr(raw_st, context, default=default_st))
                    except Exception:
                        unit_st = default_st
                else:
                    unit_st = default_st

                raw_et = ""
                if maxloop_node:
                    raw_et = self.get_input_value(maxloop_node, 2, context)
                if not raw_et:
                    raw_et = str(current_loop.get('end_time') or '').strip()

                if raw_et and raw_et.lower() not in ["end_time", "et", ""]:
                    try:
                        unit_et = float(_eval_num_expr(raw_et, context, default=default_et))
                    except Exception:
                        unit_et = default_et
                else:
                    unit_et = default_et

                unit_dur = max(1.0, unit_et - unit_st)
                veces = max(1, int(math.ceil(unit_dur / step_ms)))

                for i in range(1, veces + 1):
                    if self.is_cancelled: break
                    ctx = context.copy()
                    ctx[var_name], ctx[var_name + '_max'] = i, veces 
                    ctx['fx_i'], ctx['fx_n'] = i, veces
                    ctx['j_max'] = veces
                    ctx['j'] = i

                    frame_st = unit_st + (i - 1) * step_ms
                    frame_et = frame_st + step_ms

                    ctx['st'] = frame_st
                    ctx['et'] = frame_et
                    ctx['start_time'] = frame_st
                    ctx['end_time'] = frame_et
                    ctx['frame_start_time'] = frame_st
                    ctx['frame_end_time'] = frame_et
                    ctx['frame_dur'] = step_ms
                    ctx['fd'] = step_ms
                    ctx['fx_start_time'] = frame_st
                    ctx['fx_end_time'] = frame_et
                    ctx['fx_dur'] = step_ms

                    self.bind_active_unit(ctx, active_unit)
                    # Forzar que los tiempos del fotograma prevalezcan en el contexto
                    ctx['start_time'] = frame_st
                    ctx['end_time'] = frame_et
                    ctx['st'] = frame_st
                    ctx['et'] = frame_et
                    ctx['frame_start_time'] = frame_st
                    ctx['frame_end_time'] = frame_et

                    self.execute_loops_recursive(rest_chain, ctx, output_node, active_unit, check_cancel, progress_tracker, progress_callback)
            else:
                try:
                    veces = int(float(_eval_num_expr(current_loop['val'], context, 1)))
                except Exception:
                    veces = 1
                for i in range(1, veces + 1):
                    if self.is_cancelled: break
                    ctx = context.copy()
                    ctx[var_name], ctx[var_name + '_max'] = i, veces 
                    ctx['fx_i'], ctx['fx_n'] = i, veces
                    ctx['j_max'] = veces
                    ctx['j'] = i
                    self.bind_active_unit(ctx, active_unit)
                    self.execute_loops_recursive(rest_chain, ctx, output_node, active_unit, check_cancel, progress_tracker, progress_callback)

        elif current_loop['type'] == 'set_vars':
            if self.is_cancelled: return
            ctx = context.copy()
            vars_str = str(current_loop.get('val') or '')
            
            from nodes.code_nodes import execute_python_script
            
            for part in vars_str.replace(';', '\n').split('\n'):
                part_clean = part.strip()
                if not part_clean or part_clean.startswith('#') or part_clean.startswith('--'):
                    continue
                if '=' in part_clean:
                    key, val_expr = part_clean.split('=', 1)
                    key = key.strip()
                    val_expr = val_expr.strip()
                    if key and val_expr:
                        eval_res = execute_python_script(ctx, val_expr, {})
                        if not str(eval_res).startswith("[Err Python Script:"):
                            try:
                                res_str = str(eval_res).strip()
                                if res_str.replace('.', '', 1).replace('-', '', 1).isdigit():
                                    ctx[key] = float(res_str) if '.' in res_str else int(res_str)
                                else:
                                    ctx[key] = eval_res
                            except Exception:
                                ctx[key] = eval_res
                        else:
                            ctx[key] = val_expr
                else:
                    execute_python_script(ctx, part_clean, {})

            self.execute_loops_recursive(rest_chain, ctx, output_node, active_unit, check_cancel, progress_tracker, progress_callback)

        elif current_loop['type'] == 'code_script':
            if self.is_cancelled: return
            ctx = context.copy()
            code_node = current_loop.get('node', {})
            if code_node and 'id' in code_node:
                res = self.evaluate_data_node(code_node['id'], ctx)
                ctx['script_result'] = res
            self.execute_loops_recursive(rest_chain, ctx, output_node, active_unit, check_cancel, progress_tracker, progress_callback)

    def estimate_workload(self, dialogue_items, styles, allow_fallback_select_all=True, global_selected_styles=None):
        """
        Calcula una estimación matemática ultrarrápida (< 1ms) del número total de líneas FX
        que generará el grafo actual sobre los subtítulos, así como el nivel de complejidad.
        """
        from ass_parser import KaraokeProcessor
        processor = KaraokeProcessor(self.rx, self.ry, self.fd)
        
        parsed_lines = []
        selected_styles = set(global_selected_styles) if global_selected_styles is not None else set()
        
        for item in dialogue_items:
            if hasattr(item, 'raw_text') and hasattr(item, 'syls'):
                pyxis_line = item
            else:
                raw_line = item['raw'] if isinstance(item, dict) else getattr(item, 'raw', '')
                metrics = item.get('metrics') if isinstance(item, dict) else getattr(item, 'metrics', None)
                style_name = raw_line.split(',')[3] if ',' in raw_line else ''
                pyxis_line = processor.process_line(raw_line, styles.get(style_name, {}), metrics)
            if pyxis_line:
                parsed_lines.append(pyxis_line)
                if pyxis_line.is_selected:
                    selected_styles.add(pyxis_line.style_name)

        selected_lines_list = [l for l in parsed_lines if l.is_selected]
        if not selected_lines_list and allow_fallback_select_all:
            for l in parsed_lines:
                l.is_selected = True
                selected_styles.add(l.style_name)
            selected_lines_list = list(parsed_lines)

        output_nodes = [n for n in self.nodes.values() if 'salida' in str(n.get('type', '')).lower() or 'output' in str(n.get('type', '')).lower()]
        
        total_estimated_lines = 0
        total_base_units = 0
        has_particles = False
        has_scripts = False
        has_potrace = False
        has_audio = False
        
        for n in self.nodes.values():
            nt = str(n.get('type', ''))
            if 'Audio' in nt or 'audio' in nt.lower() or 'Waveform' in nt or 'Modulador' in nt:
                has_audio = True
            if 'IMG to pixels' in nt or 'Particles' in nt or 'pixels' in nt.lower():
                has_particles = True
            if 'Script Code' in nt or 'Code' in nt:
                has_scripts = True
            if 'IMG to Shape' in nt or 'Potrace' in nt:
                has_potrace = True

        for out_node in output_nodes:
            props = out_node.get('properties', {})
            apply_to = props.get('apply_to', 'Selected Lines')
            loop_chain = self.trace_loop_chain(out_node)
            if not loop_chain: continue

            base_loop = next((l for l in loop_chain if l['type'] == 'base'), None)
            base_type = base_loop['val'] if base_loop else 'line'
            is_noblank = "Con Blanks" not in str(
                (base_loop.get('noblank') if base_loop else '') or 
                (base_loop.get('properties', {}).get('noblank') if base_loop else '') or 
                props.get('noblank', 'No Blank')
            )

            # Auto-bucle de partículas si no hay MaxLoop/AutoSlicer explícito en la cadena
            has_explicit_maxloop = any(l.get('type') in ['maxloop', 'auto_slicer_loop'] for l in loop_chain)
            particle_auto_multiplier = 1
            if not has_explicit_maxloop:
                dummy_ctx = {'in_auto_slicer_loop': False}
                try:
                    for slot_idx in range(len(out_node.get('inputs', []))):
                        self.get_input_value(out_node, slot_idx, dummy_ctx)
                    auto_n = dummy_ctx.get('maxloop', 1)
                    if auto_n > 1:
                        particle_auto_multiplier = int(auto_n)
                except Exception:
                    pass

            for pyxis_line in parsed_lines:
                if apply_to in ["Selected Lines", "Sel. Lines"] and not pyxis_line.is_selected: continue
                if apply_to == "Style Lines" and pyxis_line.style_name not in selected_styles: continue

                if base_type in ['syl', 'char', 'word']:
                    units = getattr(pyxis_line, base_type + "s", [])
                    if is_noblank:
                        active_units = [u for u in units if not getattr(u, 'is_blank', False)]
                    else:
                        active_units = list(units)
                    
                    total_base_units += len(active_units)
                    
                    for unit in active_units:
                        unit_mult = particle_auto_multiplier
                        for loop in loop_chain:
                            l_type = loop.get('type')
                            if l_type == 'maxloop':
                                modo = str(loop.get('modo', loop.get('mode', 'Normal'))).strip().lower()
                                if 'fbf' in modo or 'frame' in modo:
                                    step_val = loop.get('step_ms') or loop.get('val') or 41.7
                                    try: step_ms = max(1.0, float(step_val))
                                    except Exception: step_ms = 41.7
                                    u_st = float(getattr(unit, 'start_time', getattr(pyxis_line, 'start_time', 0.0)))
                                    u_et = float(getattr(unit, 'end_time', getattr(pyxis_line, 'end_time', 0.0)))
                                    u_dur = max(1.0, u_et - u_st)
                                    unit_mult *= max(1, int(math.ceil(u_dur / step_ms)))
                                else:
                                    val_raw = loop.get('val') or loop.get('veces') or loop.get('count') or 1
                                    try: veces = max(1, int(float(val_raw)))
                                    except Exception: veces = 1
                                    unit_mult *= veces
                            elif l_type == 'auto_slicer_loop':
                                auto_n = loop.get('slices') or 5
                                unit_mult *= max(1, int(auto_n))
                        total_estimated_lines += unit_mult
                else:
                    total_base_units += 1
                    unit_mult = particle_auto_multiplier
                    for loop in loop_chain:
                        l_type = loop.get('type')
                        if l_type == 'maxloop':
                            modo = str(loop.get('modo', loop.get('mode', 'Normal'))).strip().lower()
                            if 'fbf' in modo or 'frame' in modo:
                                step_val = loop.get('step_ms') or loop.get('val') or 41.7
                                try: step_ms = max(1.0, float(step_val))
                                except Exception: step_ms = 41.7
                                l_st = float(getattr(pyxis_line, 'start_time', 0.0))
                                l_et = float(getattr(pyxis_line, 'end_time', 0.0))
                                l_dur = max(1.0, l_et - l_st)
                                unit_mult *= max(1, int(math.ceil(l_dur / step_ms)))
                            else:
                                val_raw = loop.get('val') or loop.get('veces') or loop.get('count') or 1
                                try: veces = max(1, int(float(val_raw)))
                                except Exception: veces = 1
                                unit_mult *= veces
                        elif l_type == 'auto_slicer_loop':
                            auto_n = loop.get('slices') or 5
                            unit_mult *= max(1, int(auto_n))
                    total_estimated_lines += unit_mult

        if total_estimated_lines < 2000:
            complexity = "Baja"
            complexity_key = "low"
            complexity_color = "#34d399"
        elif total_estimated_lines < 15000:
            complexity = "Normal"
            complexity_key = "normal"
            complexity_color = "#60a5fa"
        elif total_estimated_lines < 50000:
            complexity = "Alta"
            complexity_key = "high"
            complexity_color = "#fbbf24"
        else:
            complexity = "Extrema"
            complexity_key = "extreme"
            complexity_color = "#f87171"

        return {
            "estimated_lines": total_estimated_lines,
            "input_lines": len(selected_lines_list),
            "base_units": total_base_units,
            "output_nodes_count": len(output_nodes),
            "has_particles": has_particles,
            "has_scripts": has_scripts,
            "has_audio": has_audio,
            "complexity": complexity,
            "complexity_key": complexity_key,
            "complexity_color": complexity_color,
            "is_heavy": total_estimated_lines >= 30000
        }

    def process_single(self, dialogue_items, styles, progress_callback=None, check_cancel_callback=None, allow_fallback_select_all=True, global_selected_styles=None):
        """Ejecución secuencial en un solo proceso/hilo para un bloque de líneas."""
        self.all_generated_lines = []
        self.is_cancelled = False
        from particle_nodes import clear_particle_caches
        clear_particle_caches()

        if hasattr(self, 'target_output_id') and self.target_output_id is not None:
            if isinstance(self.target_output_id, (list, tuple, set)):
                raw_list = []
                for item in self.target_output_id:
                    if item is not None:
                        for s in str(item).split(','):
                            s_clean = s.strip()
                            if s_clean:
                                raw_list.append(s_clean)
                target_ids = set(raw_list)
            else:
                raw_list = [s.strip() for s in str(self.target_output_id).split(',') if s.strip()]
                target_ids = set(raw_list)

            all_salida_nodes = [node for node in self.nodes.values() if 'salida' in str(node.get('type', '')).lower() or 'output' in str(node.get('type', '')).lower()]

            numeric_targets = set()
            for t in target_ids:
                try:
                    numeric_targets.add(int(t))
                except (ValueError, TypeError):
                    pass

            def _matches_output(n):
                n_type = str(n.get('type', '')).lower()
                if 'salida' not in n_type and 'output' not in n_type:
                    return False

                nid_str = str(n.get('id', ''))
                nid_int = n.get('id')
                node_title = str(n.get('title') or '').strip()
                props = n.get('properties', {}) or {}
                out_id = str(props.get('output_id') or props.get('salida_id') or '').strip()
                queue_id = str(props.get('queue_id') or '').strip()

                if any(x.lower() in ('all', '*', 'todos', 'all_outputs', 'todas') for x in target_ids):
                    return True

                if nid_str in target_ids:
                    return True
                if nid_int is not None and nid_int in numeric_targets:
                    return True
                if node_title and node_title in target_ids:
                    return True

                if out_id and (out_id in target_ids or (_to_int_or_default(out_id, None) in numeric_targets)):
                    return True
                if queue_id and (queue_id in target_ids or (_to_int_or_default(queue_id, None) in numeric_targets)):
                    return True

                if n in all_salida_nodes:
                    idx_1based = all_salida_nodes.index(n) + 1
                    if (str(idx_1based) in target_ids or 
                        idx_1based in numeric_targets or 
                        f"Salida {idx_1based}" in target_ids or 
                        f"Salida_{idx_1based}" in target_ids or 
                        f"Salida {idx_1based}".lower() in (x.lower() for x in target_ids) or 
                        f"Salida_{idx_1based}".lower() in (x.lower() for x in target_ids) or
                        f"Output {idx_1based}" in target_ids or 
                        f"Output_{idx_1based}" in target_ids or 
                        f"Output {idx_1based}".lower() in (x.lower() for x in target_ids) or 
                        f"Output_{idx_1based}".lower() in (x.lower() for x in target_ids)):
                        return True

                if 'default' in target_ids and (not out_id or out_id == 'default'):
                    return True

                return False

            output_nodes = [n for n in self.nodes.values() if _matches_output(n)]
        else:
            output_nodes = [n for n in self.nodes.values() if 'salida' in str(n.get('type', '')).lower() or 'output' in str(n.get('type', '')).lower()]

        def _get_node_sort_key(node):
            props = node.get('properties', {})
            q_ord = None
            for k in ['queue_order', 'orden_cola', 'orden', 'order', 'Queue Order', 'Queue_Order']:
                if k in props and not _is_empty_value(props[k]):
                    q_ord = props[k]
                    break
            return (_to_int_or_default(q_ord, 0), _to_int_or_default(node.get('id', 0), 0))

        output_nodes = sorted(output_nodes, key=_get_node_sort_key)
        
        from ass_parser import KaraokeProcessor
        processor = KaraokeProcessor(self.rx, self.ry, self.fd)
        
        parsed_lines = []
        selected_styles = set(global_selected_styles) if global_selected_styles is not None else set()
        
        for item in dialogue_items:
            raw_line = item['raw'] if isinstance(item, dict) else getattr(item, 'raw', '')
            metrics = item.get('metrics') if isinstance(item, dict) else getattr(item, 'metrics', None)
            style_name = raw_line.split(',')[3] if ',' in raw_line else ''
            pyxis_line = processor.process_line(raw_line, styles.get(style_name, {}), metrics)
            if pyxis_line:
                parsed_lines.append(pyxis_line)
                if pyxis_line.is_selected:
                    selected_styles.add(pyxis_line.style_name)

        selected_lines_list = [l for l in parsed_lines if l.is_selected]
        if not selected_lines_list and allow_fallback_select_all:
            for l in parsed_lines:
                l.is_selected = True
            selected_lines_list = list(parsed_lines)

        # ---------------------------------------------------------------------
        # Pre-conteo de unidades de trabajo reales para progreso continuo (Work Units)
        # ---------------------------------------------------------------------
        total_work_units = 0
        for out_node in output_nodes:
            props = out_node.get('properties', {})
            apply_to = props.get('apply_to', 'Selected Lines')
            loop_chain = self.trace_loop_chain(out_node)
            if not loop_chain: continue

            base_loop = next((l for l in loop_chain if l['type'] == 'base'), None)
            base_type = base_loop['val'] if base_loop else 'line'
            is_noblank = "Con Blanks" not in str(
                (base_loop.get('noblank') if base_loop else '') or 
                (base_loop.get('properties', {}).get('noblank') if base_loop else '') or 
                props.get('noblank', 'No Blank')
            )

            for pyxis_line in parsed_lines:
                if apply_to in ["Selected Lines", "Sel. Lines"] and not pyxis_line.is_selected: continue
                if apply_to == "Style Lines" and pyxis_line.style_name not in selected_styles: continue

                if base_type in ['syl', 'char', 'word']:
                    units = getattr(pyxis_line, base_type + "s", [])
                    if is_noblank:
                        cnt = sum(1 for u in units if not getattr(u, 'is_blank', False) and _has_visible_content(u))
                    else:
                        cnt = sum(1 for u in units if _has_visible_content(u))
                    total_work_units += max(1, cnt)
                else:
                    total_work_units += 1

        if total_work_units < 1:
            total_work_units = 1

        progress_tracker = {'current': 0, 'total': total_work_units, 'last_pct': 0, 'last_time': 0.0}

        for out_node in output_nodes:
            if self.is_cancelled: break
            props = out_node.get('properties', {})
            apply_to = props.get('apply_to', 'Selected Lines')
            loop_chain = self.trace_loop_chain(out_node)
            if not loop_chain: continue
            
            for pyxis_line in parsed_lines:
                if self.is_cancelled: break
                if apply_to in ["Selected Lines", "Sel. Lines"] and not pyxis_line.is_selected: continue
                if apply_to == "Style Lines" and pyxis_line.style_name not in selected_styles: continue
                self.execute_loops_recursive(
                    loop_chain,
                    {'line': pyxis_line, 'processor': processor, 'all_lines': parsed_lines, 'selected_lines': selected_lines_list},
                    out_node,
                    None,
                    check_cancel_callback,
                    progress_tracker,
                    progress_callback
                )

        # Vaciar lote restante de líneas en el contador atómico si existe
        if getattr(self, '_local_line_batch', 0) > 0:
            if getattr(self, 'shared_line_counter', None) is not None:
                try:
                    with self.shared_line_counter.get_lock():
                        self.shared_line_counter.value += self._local_line_batch
                except Exception:
                    pass
            self._local_line_batch = 0

    def process(self, dialogue_items, styles, progress_callback=None, check_cancel_callback=None, use_multiprocessing=True):
        self.all_generated_lines = []
        self.is_cancelled = False

        cpu_cores = os.cpu_count() or 1
        num_items = len(dialogue_items)

        # Pre-cargar nodos de partículas en el proceso principal (GPU Single Pass)
        from particle_nodes import _GLOBAL_PARTICLE_PTS_CACHE, _GLOBAL_PARTICLE_IMG_CACHE
        for n_id, n_obj in self.nodes.items():
            n_type = n_obj.get('type', '')
            if any(k in n_type for k in ['IMG to pixels', 'Imagen a Partículas', 'Particles', 'Contorno']):
                try:
                    self.evaluate_data_node(n_id, {'j': 1, 'i': 1})
                except Exception:
                    pass

        cached_particle_data = (_GLOBAL_PARTICLE_PTS_CACHE.copy(), _GLOBAL_PARTICLE_IMG_CACHE.copy())

        # Determinar si el lote completo de diálogos tiene alguna selección explícita
        has_any_selection = any(
            bool(
                (isinstance(d, dict) and (d.get('is_selected') or (isinstance(d.get('metrics'), dict) and d['metrics'].get('sel'))))
                or getattr(d, 'is_selected', False)
            )
            for d in dialogue_items
        )
        allow_fallback_select_all = not has_any_selection

        global_selected_styles = set()
        for item in dialogue_items:
            raw_line = item['raw'] if isinstance(item, dict) else getattr(item, 'raw', '')
            style_name = raw_line.split(',')[3] if ',' in raw_line else ''
            is_sel = bool(
                (isinstance(item, dict) and (item.get('is_selected') or (isinstance(item.get('metrics'), dict) and item['metrics'].get('sel'))))
                or getattr(item, 'is_selected', False)
            )
            if (is_sel or allow_fallback_select_all) and style_name:
                global_selected_styles.add(style_name)

        # Si hay más de 1 línea y múltiples núcleos CPU disponibles, ejecutar en paralelo a través de ProcessPoolExecutor
        if use_multiprocessing and num_items > 1 and cpu_cores > 1:
            stop_monitor = threading.Event()
            monitor_th = None
            try:
                max_workers = min(cpu_cores, num_items)
                chunk_size = max(1, math.ceil(num_items / max_workers))
                chunks = [dialogue_items[i:i + chunk_size] for i in range(0, num_items, chunk_size)]

                shared_line_counter = multiprocessing.Value('i', 0)
                shared_cancel_flag = multiprocessing.Value('b', False)
                self.shared_line_counter = shared_line_counter
                self.shared_cancel_flag = shared_cancel_flag

                target_out = getattr(self, 'target_output_id', None)
                payloads = [
                    (
                        getattr(self, 'raw_graph', {}),
                        self.rx,
                        self.ry,
                        self.fd,
                        self.default_audio_source,
                        chunk,
                        styles,
                        cached_particle_data,
                        target_out,
                        allow_fallback_select_all,
                        list(global_selected_styles)
                    )
                    for chunk in chunks
                ]

                # Estimar total de líneas esperadas para escala porcentual realista
                est_info = self.estimate_workload(dialogue_items, styles, allow_fallback_select_all=allow_fallback_select_all, global_selected_styles=global_selected_styles)
                est_lines = max(10, est_info.get('estimated_lines', 100))

                t_loop_start = time.perf_counter()

                def _monitor_progress_loop():
                    last_c = 0
                    while not stop_monitor.is_set():
                        stop_monitor.wait(0.033) # Muestreo a 30 FPS
                        if check_cancel_callback and check_cancel_callback():
                            shared_cancel_flag.value = True
                            self.is_cancelled = True
                        if self.is_cancelled:
                            shared_cancel_flag.value = True

                        c_lines = shared_line_counter.value
                        t_now = time.perf_counter()
                        elapsed = max(0.001, t_now - t_loop_start)
                        spd = int(c_lines / elapsed) if elapsed > 0.05 else 0
                        has_audio = getattr(self, '_has_audio_nodes', False)
                        base_p = 25 if has_audio else 5
                        pct = min(89, base_p + int((89 - base_p) * (c_lines / est_lines)))
                        if callable(progress_callback) and (c_lines != last_c or c_lines > 0):
                            last_c = c_lines
                            progress_callback({
                                "percent": max(base_p, pct),
                                "lines_generated": c_lines,
                                "speed": spd,
                                "phase": f"Generando... {c_lines:,} líneas ({spd} l/s)" if spd > 0 else f"Generando... {c_lines:,} líneas"
                            })

                monitor_th = threading.Thread(target=_monitor_progress_loop, daemon=True)
                monitor_th.start()

                completed_chunks = 0
                total_chunks = len(payloads)

                prof = None
                if _PROFILER_ENABLED:
                    try:
                        from pyxis_profiler import PyxisProfiler
                        prof = PyxisProfiler.get_active()
                    except Exception:
                        prof = None

                with concurrent.futures.ProcessPoolExecutor(
                    max_workers=max_workers,
                    initializer=_worker_init,
                    initargs=(shared_line_counter, shared_cancel_flag)
                ) as pool:
                    global _GLOBAL_ACTIVE_EXECUTOR
                    _GLOBAL_ACTIVE_EXECUTOR = pool

                    future_map = {
                        pool.submit(_process_line_chunk_worker, p): (i + 1, len(p[5]), time.perf_counter())
                        for i, p in enumerate(payloads)
                    }

                    for future in concurrent.futures.as_completed(future_map):
                        if self.is_cancelled or (shared_cancel_flag and shared_cancel_flag.value):
                            break
                        w_id, line_cnt, t_start = future_map[future]
                        t_end = time.perf_counter()
                        if prof:
                            prof.record_worker_chunk(w_id, line_cnt, t_end - t_start, t_start, t_end)
                        try:
                            lines_chunk = future.result()
                            if lines_chunk:
                                self.all_generated_lines.extend(lines_chunk)
                        except Exception as fe:
                            if not self.is_cancelled:
                                print(f"[Pyxis Worker Exception] {fe}", flush=True)
                        completed_chunks += 1

            except Exception as mp_err:
                print(f"[Pyxis Multiprocessing Warning] Fallback a modo secuencial: {mp_err}", flush=True)
                self.process_single(
                    dialogue_items,
                    styles,
                    progress_callback,
                    check_cancel_callback,
                    allow_fallback_select_all=allow_fallback_select_all,
                    global_selected_styles=global_selected_styles
                )
            finally:
                stop_monitor.set()
                if monitor_th and monitor_th.is_alive():
                    monitor_th.join(timeout=0.1)
                _GLOBAL_ACTIVE_EXECUTOR = None
        else:
            self.process_single(
                dialogue_items,
                styles,
                progress_callback,
                check_cancel_callback,
                allow_fallback_select_all=allow_fallback_select_all,
                global_selected_styles=global_selected_styles
            )

        total_final_lines = len(self.all_generated_lines)
        if callable(progress_callback):
            progress_callback({
                "percent": 90,
                "lines_generated": total_final_lines,
                "phase": f"Ordenando {total_final_lines} capas deterministas..."
            })

        prof = None
        if _PROFILER_ENABLED:
            try:
                from pyxis_profiler import PyxisProfiler
                prof = PyxisProfiler.get_active()
            except Exception:
                prof = None

        if prof:
            prof.start_phase('post_process_sort')

        # Ordenar y formatear líneas de forma totalmente determinista por queue_id, queue_order, layer, start_time
        queues = {}
        for line in self.all_generated_lines:
            qid = line['queue_id']
            if qid not in queues: queues[qid] = []
            queues[qid].append(line)
        
        final_lines = []
        if prof:
            prof.end_phase('post_process_sort')
            prof.start_phase('format_ass_lines')

        if callable(progress_callback):
            progress_callback({
                "percent": 95,
                "lines_generated": total_final_lines,
                "phase": f"Ensamblando texto ASS ({total_final_lines} líneas)..."
            })

        for qid in sorted(queues.keys()):
            queue = sorted(queues[qid], key=lambda x: (x['queue_order'], x['layer'], x['start_time']))
            for line in queue:
                st_val = format_time(int(round(line['start_time'])))
                et_val = format_time(int(round(line['end_time'])))
                ass_line = f"Dialogue: {line['layer']},{st_val},{et_val},{line['style_name']},{line['actor']},{line['margin_l']},{line['margin_r']},{line['margin_v']},{line['effect']},{line['text']}\n"
                final_lines.append(ass_line)
        
        if prof:
            prof.end_phase('format_ass_lines')

        if callable(progress_callback):
            progress_callback({
                "percent": 100,
                "lines_generated": len(final_lines),
                "phase": "Completado. Transfiriendo a Aegisub..."
            })

        return final_lines


def _process_line_chunk_worker(payload):
    """
    Función de punto de entrada a nivel de módulo para ejecutores secundarios de ProcessPoolExecutor.
    Recibe: (graph_data, rx, ry, fd, default_audio_source, chunk_items, styles, particle_caches, target_output_id, allow_fallback_select_all, global_selected_styles)
    Retorna: lista de diccionarios de líneas generadas por este bloque.
    """
    try:
        target_output_id = None
        allow_fallback_select_all = True
        global_selected_styles = None

        if len(payload) >= 11:
            graph_data, rx, ry, fd, default_audio_source, chunk_items, styles, particle_caches, target_output_id, allow_fallback_select_all, global_selected_styles = payload[:11]
        elif len(payload) >= 9:
            graph_data, rx, ry, fd, default_audio_source, chunk_items, styles, particle_caches, target_output_id = payload[:9]
        elif len(payload) >= 8:
            graph_data, rx, ry, fd, default_audio_source, chunk_items, styles, particle_caches = payload[:8]
        else:
            graph_data, rx, ry, fd, default_audio_source, chunk_items, styles = payload[:7]

        if particle_caches:
            from particle_nodes import _GLOBAL_PARTICLE_PTS_CACHE, _GLOBAL_PARTICLE_IMG_CACHE
            _GLOBAL_PARTICLE_PTS_CACHE.update(particle_caches[0])
            _GLOBAL_PARTICLE_IMG_CACHE.update(particle_caches[1])

        worker_engine = GraphEngine(graph_data, rx, ry, fd, default_audio_source=default_audio_source)
        worker_engine.shared_line_counter = _WORKER_LINE_COUNTER
        worker_engine.shared_cancel_flag = _WORKER_CANCEL_FLAG
        if target_output_id is not None:
            worker_engine.target_output_id = target_output_id

        def check_worker_cancelled():
            return bool(_WORKER_CANCEL_FLAG and _WORKER_CANCEL_FLAG.value)

        worker_engine.process_single(
            chunk_items,
            styles,
            check_cancel_callback=check_worker_cancelled,
            allow_fallback_select_all=allow_fallback_select_all,
            global_selected_styles=global_selected_styles
        )
        return worker_engine.all_generated_lines
    except Exception as e:
        import traceback
        print(f"[Pyxis Worker Exception] {traceback.format_exc()}", flush=True)
        return []
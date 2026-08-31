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

# PyxisNodes/nodes/code_nodes.py
"""Nodo Maestro Híbrido Código Script (Python & Lua vía lupa)."""

import math
import sys
from decorators import system_node

_COMPILED_SCRIPT_CACHE = {}
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
        "int": int, "float": float, "str": str, "len": len, "bool": bool
    })

    from decorators import NODE_REGISTRY
    for k, v in NODE_REGISTRY.items():
        fn_name = v.__name__
        scope[fn_name] = v

    _STATIC_BASE_SCOPE = scope
    return _STATIC_BASE_SCOPE


def execute_python_script(context, script, inputs_map):
    """Ejecuta un script en Python ultra-optimizado con compilación bytecode en caché."""
    if not script:
        return ""

    script_str = str(script).strip()
    if not script_str:
        return ""

    eval_scope = _get_static_base_scope().copy()
    if context and isinstance(context, dict):
        eval_scope.update(context)

    active_unit = eval_scope.get("active_unit")
    if active_unit:
        eval_scope.setdefault("syl", getattr(active_unit, "syl", active_unit))
        eval_scope.setdefault("sili", eval_scope.get("syl"))
        eval_scope.setdefault("char", getattr(active_unit, "char", None))
        eval_scope.setdefault("word", getattr(active_unit, "word", None))
        eval_scope.setdefault("line", getattr(active_unit, "line", None))

    eval_scope["l"] = eval_scope.get("line")
    from node_engine import FxContext
    eval_scope["fx"] = FxContext(eval_scope)

    if inputs_map and isinstance(inputs_map, dict):
        eval_scope["inputs"] = inputs_map
        for k, v in inputs_map.items():
            if isinstance(k, str):
                eval_scope[k] = v
                eval_scope[k.lower()] = v

    from nodes.math_nodes import math_random_master
    eval_scope["R"] = lambda min_v=0, max_v=100, step_v=1: math_random_master(context, modo="R", min_val=min_v, max_val=max_v, step=step_v)
    eval_scope["Rs"] = lambda min_v=0, max_v=100: math_random_master(context, modo="Rs", min_val=min_v, max_val=max_v)
    eval_scope["Rc"] = lambda min_v=0, max_v=100: math_random_master(context, modo="Rc", min_val=min_v, max_val=max_v)
    eval_scope["Rd"] = lambda min_v=0, max_v=100: math_random_master(context, modo="Rd", min_val=min_v, max_val=max_v)
    eval_scope["Rm"] = lambda min_v=0, max_v=100: math_random_master(context, modo="Rm", min_val=min_v, max_val=max_v)

    from nodes.audio_nodes import audio_rms, audio_peak, audio_band, audio_fft
    eval_scope["audio_rms"] = lambda *args, **kwargs: audio_rms(*args, context=context, **kwargs)
    eval_scope["audio_peak"] = lambda *args, **kwargs: audio_peak(*args, context=context, **kwargs)
    eval_scope["audio_band"] = lambda *args, **kwargs: audio_band(*args, context=context, **kwargs)
    eval_scope["audio_fft"] = lambda *args, **kwargs: audio_fft(*args, context=context, **kwargs)

    eval_scope["result"] = ""

    compiled_entry = _COMPILED_SCRIPT_CACHE.get(script_str)
    if compiled_entry is None:
        import builtins
        try:
            code_eval = compile(script_str, "<pyxis_script>", "eval")
            compiled_entry = ("eval", code_eval)
        except Exception:
            try:
                code_exec = compile(script_str, "<pyxis_script>", "exec")
                compiled_entry = ("exec", code_exec)
            except Exception as comp_err:
                compiled_entry = ("err", str(comp_err))
        _COMPILED_SCRIPT_CACHE[script_str] = compiled_entry

    kind, code_obj = compiled_entry
    import builtins
    if kind == "eval":
        try:
            res = eval(code_obj, {"__builtins__": builtins}, eval_scope)
            return str(res) if res is not None else str(eval_scope.get("result", ""))
        except Exception as e:
            return f"[Err Python Script: {e}]"
    elif kind == "exec":
        try:
            exec(code_obj, {"__builtins__": builtins}, eval_scope)
            res = eval_scope.get("result", "")
            return str(res) if res is not None else ""
        except Exception as e:
            return f"[Err Python Script: {e}]"
    else:
        return f"[Err Python Script: {code_obj}]"

def execute_lua_script(context, script, inputs_map):
    """Ejecuta un script en Lua vía lupa con el contexto inyectado de Pyxis Nodes."""
    try:
        import lupa
    except ImportError:
        return "[Err Lua: librería 'lupa' no instalada en Python]"

    try:
        lua = lupa.LuaRuntime(unpack_returned_tuples=True)
        g = lua.globals()

        # Inyectar entradas y variables de contexto
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
            if isinstance(k, (int, float, str, bool)):
                g[k] = v

        from nodes.audio_nodes import audio_rms, audio_peak, audio_band, audio_fft
        g.audio_rms = lambda start_ms=None, end_ms=None, path=None: audio_rms(start_ms, end_ms, path, context=context)
        g.audio_peak = lambda start_ms=None, end_ms=None, path=None: audio_peak(start_ms, end_ms, path, context=context)
        g.audio_band = lambda start_ms=None, end_ms=None, min_hz=20, max_hz=250, path=None: audio_band(start_ms, end_ms, min_hz, max_hz, path, context=context)
        g.audio_fft = lambda start_ms=None, end_ms=None, num_bands=16, min_hz=20, max_hz=16000, path=None: lua.table_from(audio_fft(start_ms, end_ms, num_bands, min_hz, max_hz, path, context=context))

        if "syl" in ctx_dict:
            syl_obj = ctx_dict["syl"]
            g.syl = lua.table_from({
                "i": getattr(syl_obj, "i", 1),
                "n": getattr(syl_obj, "n", 1),
                "dur": getattr(syl_obj, "dur", 0),
                "duration": getattr(syl_obj, "duration", 0),
                "start_time": getattr(syl_obj, "start_time", 0),
                "end_time": getattr(syl_obj, "end_time", 0),
                "x": getattr(syl_obj, "x", 0.0),
                "y": getattr(syl_obj, "y", 0.0),
                "left": getattr(syl_obj, "left", 0.0),
                "center": getattr(syl_obj, "center", 0.0),
                "right": getattr(syl_obj, "right", 0.0),
                "top": getattr(syl_obj, "top", 0.0),
                "middle": getattr(syl_obj, "middle", 0.0),
                "bottom": getattr(syl_obj, "bottom", 0.0),
                "text": getattr(syl_obj, "text", ""),
                "text_stripped": getattr(syl_obj, "text_stripped", "")
            })

        if "word" in ctx_dict and ctx_dict["word"]:
            word_obj = ctx_dict["word"]
            g.word = lua.table_from({
                "i": getattr(word_obj, "i", 1),
                "n": getattr(word_obj, "n", 1),
                "dur": getattr(word_obj, "dur", getattr(word_obj, "duration", 0)),
                "duration": getattr(word_obj, "duration", 0),
                "start_time": getattr(word_obj, "start_time", 0),
                "end_time": getattr(word_obj, "end_time", 0),
                "x": getattr(word_obj, "x", getattr(word_obj, "center", 0.0)),
                "y": getattr(word_obj, "y", getattr(word_obj, "middle", 0.0)),
                "left": getattr(word_obj, "left", 0.0),
                "center": getattr(word_obj, "center", 0.0),
                "right": getattr(word_obj, "right", 0.0),
                "top": getattr(word_obj, "top", 0.0),
                "middle": getattr(word_obj, "middle", 0.0),
                "bottom": getattr(word_obj, "bottom", 0.0),
                "text": getattr(word_obj, "text", ""),
                "text_stripped": getattr(word_obj, "text_stripped", "")
            })

        if "char" in ctx_dict and ctx_dict["char"]:
            char_obj = ctx_dict["char"]
            g.char = lua.table_from({
                "i": getattr(char_obj, "i", 1),
                "n": getattr(char_obj, "n", 1),
                "dur": getattr(char_obj, "dur", getattr(char_obj, "duration", 0)),
                "duration": getattr(char_obj, "duration", 0),
                "start_time": getattr(char_obj, "start_time", 0),
                "end_time": getattr(char_obj, "end_time", 0),
                "x": getattr(char_obj, "x", getattr(char_obj, "center", 0.0)),
                "y": getattr(char_obj, "y", getattr(char_obj, "middle", 0.0)),
                "left": getattr(char_obj, "left", 0.0),
                "center": getattr(char_obj, "center", 0.0),
                "right": getattr(char_obj, "right", 0.0),
                "top": getattr(char_obj, "top", 0.0),
                "middle": getattr(char_obj, "middle", 0.0),
                "bottom": getattr(char_obj, "bottom", 0.0),
                "text": getattr(char_obj, "text", ""),
                "text_stripped": getattr(char_obj, "text_stripped", "")
            })

        if "line" in ctx_dict:
            line_obj = ctx_dict["line"]
            line_tbl = lua.table_from({
                "layer": getattr(line_obj, "layer", 0),
                "style_name": getattr(line_obj, "style_name", "Default"),
                "text": getattr(line_obj, "text", ""),
                "raw_text": getattr(line_obj, "raw_text", getattr(line_obj, "text", "")),
                "start_time": getattr(line_obj, "start_time", 0),
                "end_time": getattr(line_obj, "end_time", 0),
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
            })
            g.line = line_tbl
            g.l = line_tbl

        g.fx = lua.table_from({
            "pos_x": ctx_dict.get("fx_pos_x", ctx_dict.get("x", 0.0)),
            "pos_y": ctx_dict.get("fx_pos_y", ctx_dict.get("y", 0.0)),
            "x": ctx_dict.get("fx_pos_x", ctx_dict.get("x", 0.0)),
            "y": ctx_dict.get("fx_pos_y", ctx_dict.get("y", 0.0)),
            "i": ctx_dict.get("fx_i", ctx_dict.get("i", 1)),
            "n": ctx_dict.get("fx_n", ctx_dict.get("n", 1)),
            "start_time": ctx_dict.get("fx_start_time", ctx_dict.get("start_time", 0.0)),
            "end_time": ctx_dict.get("fx_end_time", ctx_dict.get("end_time", 0.0)),
            "dur": ctx_dict.get("fx_dur", ctx_dict.get("dur", 0.0)),
            "align": ctx_dict.get("fx_align", 5)
        })

        g.result = ""

        # Ejecutar script encapsulado en función Lua para permitir return
        lua_wrapper = f"function _pyxis_main()\n{script}\nend"
        lua.execute(lua_wrapper)
        res = lua.globals()._pyxis_main()
        if res is None:
            res = lua.globals().result
        return str(res) if res is not None else ""
    except Exception as e:
        return f"[Err Lua Script: {e}]"

def code_script_master(context, script="", lenguaje="Python", **inputs_map):
    """Función de despacho para el nodo maestro Código Script."""
    script_str = str(script or "").strip()
    if not script_str:
        return ""

    lang = str(lenguaje or "Python").strip().lower()
    if lang == "lua":
        return execute_lua_script(context, script_str, inputs_map)
    else:
        return execute_python_script(context, script_str, inputs_map)

# Registro del nodo del sistema Híbrido
system_node(
    "System", "Script Code", node_kind="step", color="#3B82F6",
    inputs=["Loop In", "In1", "In2"],
    outputs=["Loop Out", "Result"],
    properties={
        "lenguaje": "Python",
        "script": "result = 'Hello Pyxis ' + str(in1 if in1 else syl.text)",
        "inputs_count": 2
    },
    widgets=[
        {"type": "combo", "name": "Lenguaje", "property": "lenguaje", "values": ["Python", "Lua"]}
    ]
)

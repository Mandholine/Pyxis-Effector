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
Module: variable_nodes.py
Architectural Role: Contextual Metrics, User Variable Definition, and Persistent Memory Nodes.

This module implements the functional computation nodes for the 'Variables' category:
    - Sys Var (`sys_var_node`): Extracts system and layout metrics from the active context.
    - Define Vars (`define_vars_node`): Evaluates and injects user-defined variable assignments
      into the local execution dictionary.
    - Get Var (`get_var_node`): Reads named local or iteration variables from context.
    - Memory (`memory_node`): Provides persistent key-value caching across multiple iterations
      via the shared `context['_memory']` partition.

Upstream Dependencies:
    - decorators.py: `@pyxis_node` decorator for registering evaluator functions.
    - node_engine.py: `_eval_sys_var`, `_apply_set_vars_to_context_helper` for dynamic evaluation.

Downstream Callers:
    - node_engine.GraphEngine: Invokes functions through `NODE_REGISTRY['Variables/...']`.
"""

from decorators import pyxis_node


@pyxis_node("Variables", "Sys Var", [])
def sys_var_node(context, var_name="syl.text"):
    """
    Extracts a dynamic system metric or layout property from the active iteration context.

    Real-time evaluation is prioritised inside `GraphEngine.evaluate_data_node` in
    `node_engine.py` for performance. This function serves as the canonical fallback
    and entry point registered in `NODE_REGISTRY`.

    Args:
        context (dict or FxContext): Active execution context containing line, syl,
            char, and layout metrics.
        var_name (str): Identifier of the variable to resolve (e.g. 'syl.text',
            'line.start_time', 'fx.pos_x', 'ink.width').

    Returns:
        str or float: Evaluated variable value, or empty string if unresolvable.
    """
    from node_engine import _eval_sys_var
    return _eval_sys_var(var_name, context)


@pyxis_node("Variables", "Define Vars", ["In"])
def define_vars_node(context, in_val=None, variables=""):
    """
    Parses and injects user-defined variable assignments into the active context dictionary.

    Evaluates statements line-by-line (e.g. `angle = syl.i * 15`) and binds resulting
    values into `context`, making them accessible to downstream nodes in the graph.
    Passes through the inbound cable data unmodified.

    Args:
        context (dict or FxContext): Active execution context to mutate.
        in_val (Any, optional): Incoming cable data passed along the data pipeline.
        variables (str): Multiline string containing variable assignments (`name = expression`).

    Returns:
        Any: Inbound `in_val` unchanged, or empty string if `None`.
    """
    if isinstance(context, dict) and variables:
        from node_engine import _apply_set_vars_to_context_helper
        _apply_set_vars_to_context_helper(variables, context, context.get("active_unit"))
    return in_val if in_val is not None else ""


@pyxis_node("Variables", "Get Var", [])
def get_var_node(context, var_name="j"):
    """
    Retrieves an arbitrary variable value directly from the active execution context.

    Provides a clean cable source for loop counters (`j`, `s_i`), user variables,
    or parameters injected by preceding nodes.

    Args:
        context (dict): Active iteration context dictionary.
        var_name (str): Name of the variable key to query. Defaults to 'j'.

    Returns:
        Any: Value stored under `var_name` in context, or empty string if missing.
    """
    if not isinstance(context, dict):
        return ""
    return context.get(str(var_name), "")


@pyxis_node("Variables", "Memory", ["Key", "Value"])
def memory_node(context, key_in=None, val_in=None, mode="remember", key="ref", value="", default=""):
    """
    Stores or retrieves persistent state across discrete graph execution iterations.

    Maintains a dictionary partition (`context['_memory']`) retained throughout the
    lifespan of the effect render pass, facilitating accumulation, historical tracking,
    and stateful calculations across syllables or frames.

    Args:
        context (dict): Active execution context hosting the `_memory` dictionary.
        key_in (str, optional): Key identifier provided via cable connection.
        val_in (Any, optional): Value payload provided via cable connection.
        mode (str): Operational mode: 'remember' (or 'save') to write; 'retrieve' to read.
        key (str): Fallback key identifier configured in node properties. Defaults to 'ref'.
        value (str): Fallback value string configured in node properties.
        default (str): Fallback default returned when retrieving a non-existent key.

    Returns:
        Any: The saved value in write mode, or the retrieved value (or default) in read mode.
    """
    k = str(key_in) if key_in not in (None, "") else str(key)
    v = val_in if val_in not in (None, "") else (value if value != "" else default)
    m = str(mode).strip().lower()
    mem = context.get("_memory") if isinstance(context, dict) else None
    if mem is None:
        if isinstance(context, dict):
            context["_memory"] = {}
            mem = context["_memory"]
        else:
            mem = {}
    if "remember" in m or m == "save":
        mem[k] = v
        return v
    else:
        return mem.get(k, v)


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
Module: loop_nodes.py
Architectural Role: Primary and Sub-loop Iteration and Modular Progression Nodes.

This module implements the functional computation nodes for the 'Loops' category:
    - Main Loop (`main_loop_node`): Represents the root iteration domain over ASS units
      (syllables, characters, words, or lines).
    - MaxLoop (`max_loop_node`): Governs nested inner loops, sub-frame generation,
      and frame-by-frame (fbf) stepping.
    - Module (`module_node`): Calculates normalised progression ratios `[0.0, 1.0]` across
      iteration counters and modular sub-steps.

Upstream Dependencies:
    - decorators.py: `@pyxis_node` decorator for registering evaluator functions.
    - node_engine.py: `_eval_num_expr` for resolving arithmetic expressions in iteration parameters.

Downstream Callers:
    - node_engine.GraphEngine: Dispatches evaluation in topological execution chains.
"""

from decorators import pyxis_node, system_node


@pyxis_node("Loops", "Main Loop", [])
def main_loop_node(context, iterator="syl", blank_mode="no_blank"):
    """
    Evaluates the primary unit iteration index or serves as the root entry point.

    Extracts the sequential index `i` from the active unit (`PyxisUnit`) bound in `context`.

    Args:
        context (dict or FxContext): Active execution context containing 'active_unit'.
        iterator (str): Unit iteration level ('syl', 'char', 'word', 'line').
        blank_mode (str): Blank unit filtering mode ('no_blank', 'with_blanks').

    Returns:
        str: 1-based unit index as a string (e.g. '1', '2'), defaulting to '1'.
    """
    unit = context.get('active_unit') if isinstance(context, dict) else None
    return str(getattr(unit, 'i', 1) if unit else 1)


@pyxis_node("Loops", "MaxLoop", ["Loop In", "Start", "End"])
def max_loop_node(context, loop_in=None, start=None, end=None, mode="normal", iterations="3", step_ms="41.7", start_time="start_time", end_time="end_time", var_name="j"):
    """
    Evaluates the inner loop iteration counter for multi-pass repetition.

    Reads the current sub-loop iteration value associated with `var_name` (defaulting to 'j')
    from the context during nested DAG execution passes.

    Args:
        context (dict or FxContext): Active execution context holding sub-loop state.
        loop_in (Any, optional): Upstream loop token or data payload.
        start (Any, optional): Dynamic start time override.
        end (Any, optional): Dynamic end time override.
        mode (str): Repetition mode: 'normal' for fixed count, 'fbf' for frame-by-frame.
        iterations (str): Total pass count when in 'normal' mode.
        step_ms (str): Millisecond time increment per pass.
        start_time (str): Base start timestamp property.
        end_time (str): Base end timestamp property.
        var_name (str): Identifier of the inner loop variable (e.g. 'j', 'idx').

    Returns:
        str: Current iteration index formatted as a string.
    """
    if not isinstance(context, dict):
        return "1"
    v_name = str(var_name).strip() or "j"
    return str(context.get(v_name, context.get('j', context.get('fx_i', 1))))


@pyxis_node("Loops", "Module", ["Iterator (i)", "Total (N)", "Sub-step (m)"])
def module_node(context, in_i=None, in_n=None, in_m=None, iter="i", total="N", sub_m="0"):
    """
    Calculates a normalised linear progression ratio between 0.0 and 1.0.

    Computes the fraction:
        progression = (val_i - 1.0 + val_m) / (val_n + val_m - 1.0)
    supporting sub-step offsets (`val_m`) and dynamic parameter expressions.

    Args:
        context (dict or FxContext): Active context for resolving expressions in parameters.
        in_i (Any, optional): Cable input for current index `i`.
        in_n (Any, optional): Cable input for total count `N`.
        in_m (Any, optional): Cable input for sub-step offset `m`.
        iter (str): Fallback property or formula for index `i`.
        total (str): Fallback property or formula for total `N`.
        sub_m (str): Fallback property or formula for sub-step `m`.

    Returns:
        str: Normalised floating-point ratio string rounded to 4 decimal places.
    """
    from node_engine import _eval_num_expr
    raw_i = in_i if (in_i is not None and str(in_i).strip() != "") else iter
    raw_n = in_n if (in_n is not None and str(in_n).strip() != "") else total
    raw_m = in_m if (in_m is not None and str(in_m).strip() != "") else sub_m

    val_i = float(_eval_num_expr(raw_i, context, default=1.0))
    val_n = float(_eval_num_expr(raw_n, context, default=1.0))
    val_m = float(_eval_num_expr(raw_m, context, default=0.0))

    denom = val_n + val_m - 1.0
    res = (val_i - 1.0 + val_m) / denom if (denom != 0 and val_n > 1.0) else val_m
    res_rounded = round(res, 4)
    if res_rounded == int(res_rounded):
        return str(int(res_rounded))
    return f"{res_rounded:.4f}".rstrip('0').rstrip('.')


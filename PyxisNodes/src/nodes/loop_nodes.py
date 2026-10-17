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

"""Loop execution and iteration nodes for Pyxis Nodes Engine."""

from decorators import pyxis_node, system_node


@pyxis_node("Loops", "Main Loop", [])
def main_loop_node(context, iterator="syl", blank_mode="no_blank"):
    """Main Loop master node.

    Yields unit iteration index or serves as entry point for line/syl processing.
    """
    unit = context.get('active_unit') if isinstance(context, dict) else None
    return str(getattr(unit, 'i', 1) if unit else 1)


@pyxis_node("Loops", "MaxLoop", ["Loop In", "Start", "End"])
def max_loop_node(context, loop_in=None, start=None, end=None, mode="normal", iterations="3", step_ms="41.7", start_time="start_time", end_time="end_time", var_name="j"):
    """MaxLoop repetition node.

    Evaluates iteration counter or inner loop state.
    """
    if not isinstance(context, dict):
        return "1"
    v_name = str(var_name).strip() or "j"
    return str(context.get(v_name, context.get('j', context.get('fx_i', 1))))


@pyxis_node("Loops", "Module", ["Iterator (i)", "Total (N)", "Sub-step (m)"])
def module_node(context, in_i=None, in_n=None, in_m=None, iter="i", total="N", sub_m="0"):
    """Normalized module progression calculation.

    Returns progression value between 0.0 and 1.0 (or step offset).
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

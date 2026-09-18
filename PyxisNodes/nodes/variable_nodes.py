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

"""Session and context variable nodes."""

from decorators import pyxis_node


@pyxis_node("Variables", "Sys Var", [])
def sys_var_node(context, var_name="syl.text"):
    """Sys Var master node.

    Real variable evaluation is optimized inside GraphEngine.evaluate_data_node
    in node_engine.py. This function serves as fallback or for direct execution
    registered in NODE_REGISTRY.
    """
    from node_engine import _eval_sys_var
    return _eval_sys_var(var_name, context)


@pyxis_node("Variables", "Define Vars", ["In"])
def define_vars_node(context, in_val=None, variables=""):
    """Define variables node for registration."""
    return in_val if in_val is not None else ""


@pyxis_node("Variables", "Get Var", [])
def get_var_node(context, var_name="j"):
    """Retrieve variable from context."""
    if not isinstance(context, dict):
        return ""
    return context.get(str(var_name), "")


@pyxis_node("Variables", "Memory", ["Key", "Value"])
def memory_node(context, key_in=None, val_in=None, mode="remember", key="ref", value="", default=""):
    """Memory store/recall node."""
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


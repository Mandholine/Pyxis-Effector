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

# PyxisNodes/nodes/variable_nodes.py
"""Nodo maestro de variables del sistema de Pyxis (Sys Var).

Sustituye a los nodos individuales de variables ofreciendo acceso completo
a todas las variables de line/l, syl, word, char, fx, bucles, tiempo y meta.
"""

from decorators import pyxis_node


@pyxis_node("Variables", "Sys Var", [])
def sys_var_node(context, var_name="syl.text"):
    """Nodo maestro Sys Var.

    La evaluación real de la variable se realiza de forma optimizada dentro de
    GraphEngine.evaluate_data_node en node_engine.py. Esta función sirve como
    fallback o para ejecuciones directas registradas en NODE_REGISTRY.
    """
    from node_engine import _eval_sys_var
    return _eval_sys_var(var_name, context)

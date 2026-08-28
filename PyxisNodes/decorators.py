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

# decorators.py (v0.8)
"""Registro central de nodos de Pyxis Nodes Engine.

Los nodos de datos se registran en PYXIS_DB/NODE_REGISTRY.
Los nodos de sistema solo describen su interfaz visual y se registran en
SYSTEM_NODE_DB; su ejecución continúa en node_engine.py.
"""

import json


PYXIS_DB = {}
NODE_REGISTRY = {}
SYSTEM_NODE_DB = {}


def pyxis_node(category, name, inputs):
    """Registra un nodo de datos evaluable por GraphEngine."""
    def decorator(func):
        if category not in PYXIS_DB:
            PYXIS_DB[category] = {}
        PYXIS_DB[category][name] = list(inputs)
        node_key = f"{category}/{name}" if category else name
        NODE_REGISTRY[node_key] = func
        return func

    return decorator


def system_node(
    category,
    name,
    node_kind,
    inputs=None,
    outputs=None,
    color="#444444",
    properties=None,
    widgets=None,
):
    """Registra la definición visual de un nodo de sistema.

    Los nodos de sistema no se agregan a NODE_REGISTRY ni a PYXIS_DB porque no
    son funciones de datos. GraphEngine los interpreta por su tipo serializado.
    """
    definition = {
        "node_kind": node_kind,
        "inputs": list(inputs or []),
        "outputs": list(outputs or []),
        "color": color,
        "properties": dict(properties or {}),
        "widgets": list(widgets or []),
    }

    def decorator(func=None):
        if category not in SYSTEM_NODE_DB:
            SYSTEM_NODE_DB[category] = {}
        SYSTEM_NODE_DB[category][name] = definition
        return func

    return decorator()


def get_manifest():
    """Devuelve un manifiesto explícito y compatible con la UI."""
    return json.dumps(
        {
            "data_nodes": PYXIS_DB,
            "system_nodes": SYSTEM_NODE_DB,
        }
    )

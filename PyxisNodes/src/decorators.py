# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc and Pyxis Effector contributors
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

"""Central node registry for Pyxis Nodes Engine.

Data nodes are registered in PYXIS_DB/NODE_REGISTRY.
System nodes only describe their visual interface and are registered in
SYSTEM_NODE_DB; their execution takes place in node_engine.py.
"""

import json


PYXIS_DB = {}
NODE_REGISTRY = {}
SYSTEM_NODE_DB = {}


def pyxis_node(category, name, inputs):
    """Registers an evaluable data node for GraphEngine."""
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
    """Registers the visual definition of a system node.

    System nodes are not added to NODE_REGISTRY or PYXIS_DB because they
    are not data functions. GraphEngine interprets them by their serialized type.
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
    """Returns an explicit UI-compatible manifest."""
    return json.dumps(
        {
            "data_nodes": PYXIS_DB,
            "system_nodes": SYSTEM_NODE_DB,
        }
    )

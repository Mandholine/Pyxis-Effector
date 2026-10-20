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
Module: decorators.py
Architectural Role: Central node registry and catalogue subsystem for the Pyxis engine.

Global Registry Structures:
    - PYXIS_DB (dict): Hierarchical mapping {category: {node_name: [inputs]}} for evaluable data nodes.
    - NODE_REGISTRY (dict): Flat mapping {'Category/Name': evaluator_func} utilized by GraphEngine
      as the dynamic dispatch table during runtime graph evaluation.
    - SYSTEM_NODE_DB (dict): Catalogue of system node visual specifications ({category: {node_name: definition}}),
      consumed by the frontend web interface (LiteGraph) to instantiate widgets, ports, colours, and properties.

Upstream Dependencies:
    - json: Serialisation of catalogues and manifests for frontend export.

Downstream Callers:
    - nodes_library.py: Formally registers each system node via system_node(...).
    - nodes/<category>_nodes.py: Decorates each computation evaluator function with @pyxis_node(...).
    - node_engine.py: Imports NODE_REGISTRY to dispatch data node execution in evaluate_data_node.
    - main.py / pyxis_daemon.py: Calls get_manifest() to synchronise the catalogue with the web UI.

Side Effects and State:
    - Process-level global mutable in-memory state (PYXIS_DB, NODE_REGISTRY, SYSTEM_NODE_DB).
    - Statically populated at module import time (controlled import side effects).
"""

import json


PYXIS_DB = {}
NODE_REGISTRY = {}
SYSTEM_NODE_DB = {}


def pyxis_node(category: str, name: str, inputs: list):
    """
    Decorator registering a computation function as an evaluable data node within the engine.

    Associates the decorated function with a canonical key 'Category/Name' (or 'Name' if uncategorised)
    inside NODE_REGISTRY and registers its input port names in PYXIS_DB.

    Args:
        category (str): Canonical category of the node (e.g. 'Basics', 'Shape', 'Time', 'Functions').
        name (str): Canonical node name in English (e.g. 'Math', 'Slicer', 'Retime').
        inputs (list): List of dictionaries or names describing the input ports.

    Returns:
        Callable: Decorator wrapping the original evaluator function without altering its signature.

    Dependencies & Couplings:
        - Used across all modules in nodes/<category>_nodes.py.
        - Read by node_engine.py during GraphEngine topological resolution.
    """
    def decorator(func):
        if category not in PYXIS_DB:
            PYXIS_DB[category] = {}
        PYXIS_DB[category][name] = list(inputs)
        node_key = f"{category}/{name}" if category else name
        NODE_REGISTRY[node_key] = func
        return func

    return decorator


def system_node(
    category: str,
    name: str,
    node_kind: str,
    inputs: list = None,
    outputs: list = None,
    color: str = "#444444",
    properties: dict = None,
    widgets: list = None,
):
    """
    Registers the visual definition, ports, and default properties of a node for LiteGraph.

    Structural or system nodes are not registered in NODE_REGISTRY because their execution logic
    is integrated directly into the topological flow of node_engine.py or secondary decorators.

    Args:
        category (str): Canonical node category (e.g. 'System', 'Loops', 'Variables').
        name (str): Canonical node name (e.g. 'Output', 'Main Loop', 'Sys Var').
        node_kind (str): Functional classification ('data', 'flow', 'system', 'terminal').
        inputs (list, optional): List of input port labels (e.g. ['Loop In', 'In1']).
        outputs (list, optional): List of output port labels (e.g. ['Loop Out', 'Result']).
        color (str, optional): Hexadecimal colour for canvas node headers (default '#444444').
        properties (dict, optional): Key-value dictionary containing internal properties and defaults.
        widgets (list, optional): List of widget configurations (combos, sliders, toggles, text).

    Returns:
        None: Executes immediate registration in SYSTEM_NODE_DB[category][name].

    Dependencies & Couplings:
        - Extensively used by nodes_library.py to declare system nodes.
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


def get_manifest() -> str:
    """
    Exports the complete registered node catalogue as a LiteGraph-compatible JSON string.

    Manifest Structure:
        {
            "data_nodes": PYXIS_DB,
            "system_nodes": SYSTEM_NODE_DB
        }

    Returns:
        str: Serialised JSON string containing all nodes registered in memory.

    Dependencies & Couplings:
        - Called by main.py and pyxis_daemon.py to supply the palette and context menus in web/index.html.
    """
    return json.dumps(
        {
            "data_nodes": PYXIS_DB,
            "system_nodes": SYSTEM_NODE_DB,
        }
    )


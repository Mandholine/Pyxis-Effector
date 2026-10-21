# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Engine: Graph & Node Runtime Subsystem
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from .node_engine import GraphEngine, abort_global_multiprocessing, NODE_REGISTRY
from .node_validator import GraphValidator

# Alias for backwards compatibility
NodeValidator = GraphValidator

__all__ = [
    "GraphEngine",
    "GraphValidator",
    "NodeValidator",
    "NODE_REGISTRY",
    "abort_global_multiprocessing",
]

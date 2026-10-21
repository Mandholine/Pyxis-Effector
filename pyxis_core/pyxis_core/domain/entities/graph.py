# -*- coding: utf-8 -*-
# Pyxis Effector — Domain Entities (Node Graph)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NodeConnection:
    """Represents a connection between an output socket and an input socket."""

    from_node_id: str
    from_socket: str
    to_node_id: str
    to_socket: str


@dataclass
class NodeItem:
    """Represents a single node in the effect graph."""

    id: str
    node_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    pos_x: float = 0.0
    pos_y: float = 0.0
    title: Optional[str] = None


@dataclass
class NodeGraph:
    """Domain model representing a complete node effect graph."""

    id: str = "default_graph"
    name: str = "Untitled Graph"
    version: str = "1.0"
    nodes: List[NodeItem] = field(default_factory=list)
    connections: List[NodeConnection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_node_by_id(self, node_id: str) -> Optional[NodeItem]:
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def find_nodes_by_type(self, node_type_prefix: str) -> List[NodeItem]:
        prefix_lower = node_type_prefix.lower()
        return [n for n in self.nodes if prefix_lower in n.node_type.lower()]

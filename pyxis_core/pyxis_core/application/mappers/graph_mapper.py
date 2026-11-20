# -*- coding: utf-8 -*-
# Pyxis Effector — Application Mappers (Graph)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

import json
from typing import Any, Dict, List, Union
from ...domain.entities.graph import NodeGraph, NodeItem, NodeConnection


class GraphMapper:
    """Maps between raw JSON/Dict payloads and NodeGraph domain entities."""

    @staticmethod
    def to_engine_dict(raw_data: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """Grafo listo para el motor. Si ya viene en el formato del motor (`links` + `inputs`/`outputs` por nodo, el que
        guardan las plantillas y genera la app) se conserva TAL CUAL: normalizarlo a la entidad de dominio descarta los
        enlaces y el motor recibiria nodos sin conexiones. Los grafos en formato de dominio (`connections`) se mapean."""
        payload = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        if isinstance(payload, dict) and isinstance(payload.get("links"), list):
            return payload
        return GraphMapper.to_dict(GraphMapper.to_domain(payload))

    @staticmethod
    def to_domain(raw_data: Union[Dict[str, Any], str]) -> NodeGraph:
        """Converts a dict or JSON string into a NodeGraph entity."""
        if isinstance(raw_data, str):
            payload = json.loads(raw_data)
        elif isinstance(raw_data, dict):
            payload = raw_data
        else:
            raise ValueError(f"Invalid graph payload type: {type(raw_data)}")

        nodes_list: List[NodeItem] = []
        for n in payload.get("nodes", []):
            if isinstance(n, dict):
                nodes_list.append(
                    NodeItem(
                        id=str(n.get("id", "")),
                        node_type=str(n.get("type", "")),
                        properties=dict(n.get("properties", {})),
                        pos_x=float(n.get("x", n.get("pos_x", 0.0))),
                        pos_y=float(n.get("y", n.get("pos_y", 0.0))),
                        title=n.get("title"),
                    )
                )

        connections_list: List[NodeConnection] = []
        for c in payload.get("connections", []):
            if isinstance(c, dict):
                connections_list.append(
                    NodeConnection(
                        from_node_id=str(c.get("from_node", c.get("from_node_id", ""))),
                        from_socket=str(c.get("from_socket", "")),
                        to_node_id=str(c.get("to_node", c.get("to_node_id", ""))),
                        to_socket=str(c.get("to_socket", "")),
                    )
                )

        return NodeGraph(
            id=str(payload.get("id", "graph")),
            name=str(payload.get("name", "Untitled Graph")),
            version=str(payload.get("version", "1.0")),
            nodes=nodes_list,
            connections=connections_list,
            metadata=dict(payload.get("metadata", {})),
        )

    @staticmethod
    def to_dict(graph: NodeGraph) -> Dict[str, Any]:
        """Converts a NodeGraph domain entity into the standard dictionary payload."""
        return {
            "id": graph.id,
            "name": graph.name,
            "version": graph.version,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.node_type,
                    "properties": n.properties,
                    "pos_x": n.pos_x,
                    "pos_y": n.pos_y,
                    "title": n.title,
                }
                for n in graph.nodes
            ],
            "connections": [
                {
                    "from_node": c.from_node_id,
                    "from_socket": c.from_socket,
                    "to_node": c.to_node_id,
                    "to_socket": c.to_socket,
                }
                for c in graph.connections
            ],
            "metadata": graph.metadata,
        }

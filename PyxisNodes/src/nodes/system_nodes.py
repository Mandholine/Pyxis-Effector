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
Module: system_nodes.py
Architectural Role: Declarative System Endpoints, Diagnostic Sinks, and Terminal Output Nodes.

This module registers the four architectural anchor nodes of the 'System' category:
    - Output: The mandatory terminal sink in every executable Pyxis graph. Receives generated
      tags and geometry, determines line application scope (`apply_to`), and compiles the final
      ASS Dialogue lines.
    - Previewer: Canvas monitoring sink allowing visual frame inspection directly within the
      LiteGraph web interface without writing to the ASS script.
    - Script Code: Multi-language embedded sandbox container (`Python` / `Lua`) enabling arbitrary
      algorithmic manipulation with dynamic input/output ports.
    - Benchmark Math: Diagnostic evaluation utility measuring computational performance and
      thread throughput across mathematical routines.

Upstream Dependencies:
    - decorators.py: `system_node` for visual registration in `SYSTEM_NODE_DB`.

Downstream Callers:
    - node_engine.GraphEngine: Identifies `Output` as the root sink during reverse DAG tracing.
    - code_nodes.py: Implements runtime evaluation for `Script Code`.
"""

from decorators import system_node

system_node(
    "System", "Output", node_kind="output", color="#8B0000",
    inputs=["Loop / Domain", "Layer", "Start Time", "End Time", "Tags", "Return", "Queue ID", "Queue Order"],
    outputs=["Preview"],
    properties={"apply_to": "Sel. Lines", "queue_id": "", "queue_order": "", "origin_align": 5},
    widgets=[
        {"type": "combo", "name": "Apply to:", "property": "apply_to", "values": ["Sel. Lines", "Selected Lines", "Style Lines", "All Lines"]}
    ]
)

system_node(
    "System", "Previewer", node_kind="preview", color="#2563EB",
    inputs=["Output"],
    outputs=[],
    properties={"output_ids": ""},
    widgets=[
        {"type": "text", "name": "Output IDs", "property": "output_ids"}
    ]
)

system_node(
    "System", "Script Code", node_kind="step", color="#3B82F6",
    inputs=["Loop In", "In1", "In2"],
    outputs=["Loop Out", "Result"],
    properties={
        "language": "Python",
        "script": "result = 'Hello Pyxis ' + str(in1 if in1 else syl.text)",
        "inputs_count": 2
    },
    widgets=[
        {"type": "combo", "name": "Language", "property": "language", "values": ["Python", "Lua"]}
    ]
)

system_node(
    "System", "Benchmark Math", node_kind="data", color="#D97706",
    inputs=["Iterations"], outputs=["Out", "Time ms"],
    properties={"iterations": "10000", "complexity": "Heavy Math (Trig + Sqrt)"},
    widgets=[
        {"type": "combo", "name": "Complexity", "property": "complexity", "values": ["Heavy Math (Trig + Sqrt)", "Prime Sieve", "Matrix Mult"]}
    ]
)

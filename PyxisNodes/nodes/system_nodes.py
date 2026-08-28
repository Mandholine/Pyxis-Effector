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

# PyxisNodes/nodes/system_nodes.py
"""Nodos de salida final del sistema y diagnósticos de rendimiento (Benchmark)."""

from decorators import system_node

system_node(
    "System", "Output", node_kind="output", color="#8B0000",
    inputs=["Loop / Domain", "Layer", "Start Time", "End Time", "Tags", "Return", "Queue ID", "Queue Order"],
    properties={"apply_to": "Sel. Lines"},
    widgets=[
        {"type": "combo", "name": "Aplicar a:", "property": "apply_to", "values": ["Sel. Lines", "Selected Lines", "Style Lines", "All Lines"]}
    ]
)

system_node(
    "Loops", "Main Loop", node_kind="bucle", color="#1E3A8A",
    outputs=["Loop"],
    properties={"iterador": "syl", "noblank": "No Blank (Ignorar Espacios)"},
    widgets=[
        {"type": "combo", "name": "Iterator:", "property": "iterador", "values": ["syl", "char", "word", "line"]},
        {"type": "combo", "name": "Modo Blank:", "property": "noblank", "values": ["No Blank (Ignorar Espacios)", "Con Blanks (Todos)"]}
    ]
)

system_node(
    "System", "Benchmark Math", node_kind="data", color="#D97706",
    inputs=["In"], outputs=["Out", "Time ms"],
    properties={"iterations": 10000, "complexity": "Heavy Math (Trig + Sqrt)"},
    widgets=[
        {"type": "combo", "name": "Iterations:", "property": "iterations", "values": [1000, 5000, 10000, 25000, 50000]},
        {"type": "combo", "name": "Complejidad:", "property": "complexity", "values": ["Heavy Math (Trig + Sqrt)", "Matrix Multiply", "Prime Factorization"]}
    ]
)

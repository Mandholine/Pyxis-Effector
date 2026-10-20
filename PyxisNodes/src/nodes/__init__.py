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
Package: nodes
Architectural Role: Central registry bootstrapping package for Pyxis computation evaluators.

This package initialises and exposes all modular node categories by importing each
sub-module upon load. When imported, the `@pyxis_node` and `system_node` decorators
execute at module level, populating the global runtime tables in `decorators.py`:
    - `NODE_REGISTRY`: Mapping 'Category/NodeName' to Python execution callables.
    - `PYXIS_DB`: Category-level index of input port configurations.
    - `SYSTEM_NODE_DB`: Visual interface metadata consumed by the LiteGraph frontend.

Imported Sub-modules:
    - tag_nodes: ASS tag manipulators, oscillators, Bézier paths, and kinematics.
    - math_nodes: Mathematical operators, trigonometrics, and easing curves.
    - shape_nodes: Vector manipulation, Clipper2 booleans, and procedural slicers.
    - text_nodes: String manipulation, typographic transformations, and sanitisation.
    - variable_nodes: Context variable extractors, user definitions, and persistent memory.
    - time_nodes: Temporal retiming, phase offsets, and frame conversions.
    - code_nodes: Embedded Python/Lua sandbox environments and pseudo-random generators.
    - audio_nodes: Acoustic envelope tracking and spectral waveform generation.
    - loop_nodes: Main unit loops, nested iterations, and modular progression.
    - system_nodes: Terminal generation sinks, previewers, and hardware benchmarks.

Upstream Dependencies:
    - decorators.py: Global registries `NODE_REGISTRY`, `PYXIS_DB`, and `SYSTEM_NODE_DB`.

Downstream Callers:
    - nodes_library.py: Imports `nodes` to ensure all evaluator functions are registered.
    - node_engine.py: Queries `NODE_REGISTRY` to dispatch node calculations during graph evaluation.
"""

from . import tag_nodes
from . import math_nodes
from . import shape_nodes
from . import text_nodes
from . import variable_nodes
from . import time_nodes
from . import code_nodes
from . import audio_nodes
from . import loop_nodes
from . import system_nodes


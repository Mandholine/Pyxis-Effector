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
Pyxis Effector - Synthetic Performance Diagnostic & Benchmarking Runner.

This module provides an end-to-end benchmarking utility to measure the latency,
throughput, and scalability of the graph evaluation engine (GraphEngine) under controlled workloads.

Architecture and Pipeline:
1. Synthetic or real ASS file parsing via `ASSParser`.
2. Preparation of a representative canonical test DAG (Main Loop + MaxLoop + Math + Tags + Output).
3. Graph compilation and dependency optimisation via `GraphEngine`.
4. Execution in sequential or parallel worker mode (`use_multiprocessing`).
5. Granular phase timing instrumentation (`parse_ass`, `graph_prep`, `workers_exec`)
   utilising `PyxisProfiler`.
6. Generation and export of diagnostic metrics report to disk (`pyxis_performance_report.txt`).

Upstream Dependencies:
    - `ass_parser.ASSParser`: Parsing and extraction of dialogues, styles, and resolution headers.
    - `node_engine.GraphEngine`: Execution engine and topological evaluation.
    - `pyxis_profiler.PyxisProfiler`: Profiling telemetry and metrics aggregation manager.

Downstream Callers:
    - Used by developers, CI/benchmarks, and profiling diagnostics to detect bottlenecks
      in multiprocessing versus sequential evaluation.
"""

import os
import sys
import time
from ass_parser import ASSParser
from node_engine import GraphEngine
from pyxis_profiler import PyxisProfiler

def run_performance_diagnostic(ass_path=None, custom_graph=None, use_mp=False, num_lines=10):
    """
    Executes a comprehensive performance diagnostic of the graph engine and exports a metrics report.

    Measures execution latency across three critical lifecycle phases:
    1. 'parse_ass': Reads the ASS file and clones dialogue data structures in memory.
    2. 'graph_prep': Instantiates `GraphEngine`, validates topology, and compiles dependencies.
    3. 'workers_exec': Complete processing of dialogue lines against the DAG (`engine.process`).

    Parameters:
        ass_path (str | None): Absolute or relative path to input ASS file. If None,
                               defaults to 'preview_base.ass' in the `src/` directory.
        custom_graph (dict | None): Serialised graph structure (nodes and links). If None,
                                    constructs an intensive synthetic stress graph (Main Loop with
                                    MaxLoop of 30 iterations, trigonometric calculations, and positioning).
        use_mp (bool): If True, enables multi-worker parallel processing in `GraphEngine`.
                       If False, evaluates sequentially on the main thread.
        num_lines (int): Number of synthetic dialogue lines to process (cyclically repeats
                         parsed lines). Defaults to 10.

    Returns:
        PyxisProfiler: Active profiler instance with recorded timestamps, input/output line counts,
                       and calculated throughput (lines/sec).

    Side Effects:
        - Prints detailed telemetry to `sys.stdout`.
        - Writes the generated textual diagnostic report to `pyxis_performance_report.txt` in the base directory.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if ass_path is None:
        ass_path = os.path.join(base_dir, "preview_base.ass")
    
    print("=" * 80)
    print("           STARTING PYXIS NODES PERFORMANCE DIAGNOSTIC             ")
    print("=" * 80)
    print(f" Test ASS File         : {ass_path}")
    print(f" Multiprocessing       : {'Enabled' if use_mp else 'Disabled (Sequential)'}")
    print(f" Lines to Process      : {num_lines}")
    print("-" * 80)
    
    profiler = PyxisProfiler(enabled=True)
    profiler.start()

    profiler.start_phase("parse_ass")
    parsed_ass = ASSParser.read_file(ass_path)
    styles, dialogues, rx, ry, fd = parsed_ass
    
    test_dialogues = []
    if dialogues:
        for i in range(num_lines):
            orig = dialogues[i % len(dialogues)]
            cloned = {'raw': orig['raw'], 'metrics': orig.get('metrics')}
            test_dialogues.append(cloned)
    profiler.end_phase("parse_ass")
    profiler.total_dialogue_inputs = len(test_dialogues)

    if custom_graph is None:
        custom_graph = {
            'nodes': [
                {'id': 1, 'type': 'Loops/Main Loop', 'properties': {'iterator': 'syl'}, 'inputs': []},
                {'id': 2, 'type': 'Loops/MaxLoop', 'properties': {'iterations': '30', 'var_name': 'j'}, 'inputs': [{'name': 'Loop In', 'link': 1}]},
                {'id': 3, 'type': 'Math/Calc', 'properties': {'expr': 'j * 2.5 + sin(j * 0.1) * 10'}, 'inputs': []},
                {'id': 4, 'type': 'Tags/Pos', 'properties': {'x': 'syl.center', 'y': 'syl.middle'}, 'inputs': [{'name': 'x', 'link': 3}, {'name': 'y'}]},
                {'id': 5, 'type': 'System/Output', 'properties': {'apply_to': 'Sel. Lines'}, 'inputs': [
                    {'name': 'Loop / Domain', 'link': 2},
                    {'name': 'Layer'},
                    {'name': 'Start Time'},
                    {'name': 'End Time'},
                    {'name': 'Tags', 'link': 4},
                    {'name': 'Return'}
                ]}
            ],
            'links': [
                [1, 1, 0, 2, 0, 'flow'],
                [2, 2, 0, 5, 0, 'flow'],
                [3, 3, 0, 4, 0, 'number'],
                [4, 4, 0, 5, 4, 'string']
            ]
        }

    profiler.start_phase("graph_prep")
    engine = GraphEngine(custom_graph, rx, ry, fd)
    profiler.end_phase("graph_prep")

    profiler.start_phase("workers_exec")
    lines = engine.process(test_dialogues, styles, use_multiprocessing=use_mp)
    profiler.end_phase("workers_exec")

    profiler.total_lines_generated = len(lines)
    profiler.stop()

    report = profiler.generate_report()
    print(report)

    out_file = os.path.join(base_dir, "pyxis_performance_report.txt")
    profiler.save_report(out_file)
    print(f"\n[OK] Performance report saved successfully to:\n{out_file}")
    return profiler

if __name__ == "__main__":
    run_performance_diagnostic(use_mp=False, num_lines=15)

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

import os
import sys
import time
from ass_parser import ASSParser
from node_engine import GraphEngine
from pyxis_profiler import PyxisProfiler

def run_performance_diagnostic(ass_path=None, custom_graph=None, use_mp=False, num_lines=10):
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

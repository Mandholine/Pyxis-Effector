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

import time
import os
import sys
from typing import Dict, List, Any, Optional

class PyxisProfiler:
    _ACTIVE_INSTANCE: Optional['PyxisProfiler'] = None

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.phase_times: Dict[str, float] = {}
        self.phase_starts: Dict[str, float] = {}
        self.node_stats: Dict[int, Dict[str, Any]] = {}
        self.worker_stats: Dict[int, Dict[str, Any]] = {}
        self.total_lines_generated: int = 0
        self.total_dialogue_inputs: int = 0
        self.start_time: float = time.perf_counter()
        self.end_time: float = 0.0

    @classmethod
    def get_active(cls) -> Optional['PyxisProfiler']:
        return cls._ACTIVE_INSTANCE

    def start(self):
        PyxisProfiler._ACTIVE_INSTANCE = self
        self.start_time = time.perf_counter()
        try:
            import node_engine
            node_engine._PROFILER_ENABLED = True
        except Exception:
            pass

    def stop(self):
        self.end_time = time.perf_counter()
        if PyxisProfiler._ACTIVE_INSTANCE is self:
            PyxisProfiler._ACTIVE_INSTANCE = None
        try:
            import node_engine
            node_engine._PROFILER_ENABLED = False
        except Exception:
            pass

    def start_phase(self, phase_name: str):
        if not self.enabled:
            return
        self.phase_starts[phase_name] = time.perf_counter()

    def end_phase(self, phase_name: str):
        if not self.enabled:
            return
        if phase_name in self.phase_starts:
            elapsed = time.perf_counter() - self.phase_starts.pop(phase_name)
            self.phase_times[phase_name] = self.phase_times.get(phase_name, 0.0) + elapsed

    def record_node_eval(self, node_id: int, node_type: str, elapsed_sec: float):
        if not self.enabled:
            return
        if node_id not in self.node_stats:
            self.node_stats[node_id] = {
                'type': node_type,
                'calls': 0,
                'total_time': 0.0
            }
        st = self.node_stats[node_id]
        st['calls'] += 1
        st['total_time'] += elapsed_sec

    def record_worker_chunk(self, worker_id: int, lines_count: int, duration_sec: float, start_t: float, end_t: float):
        if not self.enabled:
            return
        self.worker_stats[worker_id] = {
            'lines': lines_count,
            'duration': duration_sec,
            'start': start_t,
            'end': end_t
        }

    def generate_report(self) -> str:
        total_wall_time = (self.end_time or time.perf_counter()) - self.start_time
        lines_out = []
        lines_out.append('=' * 80)
        lines_out.append('           PYXIS NODES - PERFORMANCE & DIAGNOSTIC REPORT           ')
        lines_out.append('=' * 80)
        lines_out.append(' Total Execution Time     : {:10.2f} ms ({:.3f} s)'.format(total_wall_time * 1000.0, total_wall_time))
        lines_out.append(' ASS Dialogue Input Lines : {:10d}'.format(self.total_dialogue_inputs))
        lines_out.append(' Generated FX Lines       : {:10d}'.format(self.total_lines_generated))
        if total_wall_time > 0 and self.total_lines_generated > 0:
            rate = self.total_lines_generated / total_wall_time
            lines_out.append(' Generation Speed         : {:10.1f} FX lines/second'.format(rate))
        lines_out.append('-' * 80)

        lines_out.append(' [1] TIME BREAKDOWN BY PHASES:')
        h_phase, h_t, h_pct = 'Phase', 'Time (ms)', '% of Total'
        lines_out.append('  {:<38} | {:<15} | {:<12}'.format(h_phase, h_t, h_pct))
        lines_out.append('  ' + '-' * 68)
        
        phase_labels = {
            'parse_ass': 'Reading and Parsing ASS (Karaskel)',
            'audio_preprocess': 'Audio Preprocessing (FFmpeg/WAV)',
            'graph_prep': 'Compilation and Loop Chains',
            'workers_exec': 'Loop and Node Execution',
            'ipc_gather': 'IPC Gathering and Deserialization',
            'post_process_sort': 'Deterministic Sorting (Queues/Layer)',
            'format_ass_lines': 'ASS Subtitle String Formatting',
            'disk_io': 'Disk Writing (result.txt / fsync)'
        }

        sum_phases = sum(self.phase_times.values())
        for p_key, p_name in phase_labels.items():
            if p_key in self.phase_times:
                t_ms = self.phase_times[p_key] * 1000.0
                pct = (self.phase_times[p_key] / max(1e-6, total_wall_time)) * 100.0
                lines_out.append('  {:<38} | {:12.2f} ms | {:10.1f} %'.format(p_name, t_ms, pct))

        other_t = max(0.0, total_wall_time - sum_phases) * 1000.0
        other_pct = (max(0.0, total_wall_time - sum_phases) / max(1e-6, total_wall_time)) * 100.0
        if other_pct >= 1.0:
            lines_out.append('  {:<38} | {:12.2f} ms | {:10.1f} %'.format('Other operations / Overhead', other_t, other_pct))

        lines_out.append('-' * 80)

        if self.node_stats:
            lines_out.append(' [2] NODES WITH HIGHEST TIME CONSUMPTION (TOP BOTTLENECKS):')
            lines_out.append('  {:<5} | {:<30} | {:<10} | {:<12} | {:<10} | {:<8}'.format('ID', 'Node Type', 'Calls', 'Total (ms)', 'Avg (us)', '% Graph'))
            lines_out.append('  ' + '-' * 84)

            total_node_time = sum(st['total_time'] for st in self.node_stats.values())
            sorted_nodes = sorted(self.node_stats.items(), key=lambda kv: kv[1]['total_time'], reverse=True)

            for n_id, st in sorted_nodes[:15]:
                calls = st['calls']
                tot_ms = st['total_time'] * 1000.0
                avg_us = (st['total_time'] / max(1, calls)) * 1000000.0
                pct_graph = (st['total_time'] / max(1e-6, total_node_time)) * 100.0
                lines_out.append('  {:<5} | {:<30} | {:<10d} | {:10.2f} ms | {:8.1f} us | {:6.1f} %'.format(n_id, st['type'][:30], calls, tot_ms, avg_us, pct_graph))

            lines_out.append('-' * 80)

        if self.worker_stats:
            lines_out.append(' [3] LOAD DISTRIBUTION AMONG WORKERS (CPU CORES):')
            lines_out.append('  {:<12} | {:<15} | {:<15} | {:<15}'.format('Worker ID', 'Lines Proc.', 'Duration (ms)', 'Deviation'))
            lines_out.append('  ' + '-' * 65)

            durations = [w['duration'] for w in self.worker_stats.values()]
            avg_dur = sum(durations) / max(1, len(durations))

            for w_id, wst in sorted(self.worker_stats.items()):
                w_ms = wst['duration'] * 1000.0
                diff_pct = ((wst['duration'] - avg_dur) / max(1e-6, avg_dur)) * 100.0
                diff_str = '{:+.1f} %'.format(diff_pct)
                lines_out.append('  Worker #{:<4} | {:15d} | {:12.2f} ms | {:>12}'.format(w_id, wst['lines'], w_ms, diff_str))

            lines_out.append('-' * 80)

        lines_out.append(' [4] AUTOMATIC DIAGNOSTIC & RECOMMENDATIONS:')
        warnings_found = False

        if self.worker_stats:
            max_w = max(self.worker_stats.items(), key=lambda kv: kv[1]['duration'])
            min_w = min(self.worker_stats.items(), key=lambda kv: kv[1]['duration'])
            if max_w[1]['duration'] > 2.0 * max(0.01, min_w[1]['duration']):
                warnings_found = True
                lines_out.append('  * [IMBALANCE WARNING]: Worker #{} took {:.1f}ms while Worker #{} took only {:.1f}ms.'.format(
                    max_w[0], max_w[1]['duration']*1000, min_w[0], min_w[1]['duration']*1000))
                lines_out.append('    -> Cause: A chunk of lines has significantly denser loops than others.')
                lines_out.append('    -> This explains a pause in progress (80%-83%) while all cores await the last worker.')

        if self.node_stats:
            sorted_nodes = sorted(self.node_stats.items(), key=lambda kv: kv[1]['total_time'], reverse=True)
            for n_id, st in sorted_nodes[:3]:
                tot_ms = st['total_time'] * 1000.0
                if tot_ms > 200.0 and (st['total_time'] / max(1e-6, total_wall_time)) > 0.35:
                    warnings_found = True
                    lines_out.append('  * [BOTTLENECK IN NODE #{} ({})]:'.format(n_id, st['type']))
                    lines_out.append('    -> Consumed {:.1f}ms ({:.1f}% of total time).'.format(tot_ms, (st['total_time']/total_wall_time)*100))
                    if 'IMG to pixels' in st['type'] or 'Particles' in st['type'] or 'Particulas' in st['type']:
                        lines_out.append('    -> Recommendation: Increase Step or verify the frame is not being evaluated redundantly.')
                    elif 'Script Code' in st['type'] or 'Code' in st['type']:
                        lines_out.append('    -> Recommendation: Optimize the Python script inside the node to reduce operations per line.')

        sort_t = self.phase_times.get('post_process_sort', 0.0) + self.phase_times.get('format_ass_lines', 0.0)
        if sort_t > 0.3 and (sort_t / max(1e-6, total_wall_time)) > 0.20:
            warnings_found = True
            lines_out.append('  * [HEAVY POST-PROCESSING]: Text sorting and formatting took {:.1f}ms.'.format(sort_t*1000))
            lines_out.append('    -> Generated {} lines. Consider reducing generated event volume if possible.'.format(self.total_lines_generated))

        if not warnings_found:
            lines_out.append('  * Excellent: Graph and workers are balanced and executing at maximum efficiency.')

        lines_out.append('=' * 80)
        return '\n'.join(lines_out)

    def save_report(self, file_path: str = 'pyxis_performance_report.txt'):
        report_text = self.generate_report()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        return file_path

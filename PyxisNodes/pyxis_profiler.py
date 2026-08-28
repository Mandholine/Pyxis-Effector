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
        lines_out.append('           PYXIS NODES - INFORME DE RENDIMIENTO & DIAGNOSTICO           ')
        lines_out.append('=' * 80)
        lines_out.append(' Tiempo Total de Ejecucion: {:10.2f} ms ({:.3f} s)'.format(total_wall_time * 1000.0, total_wall_time))
        lines_out.append(' Lineas ASS de Entrada    : {:10d}'.format(self.total_dialogue_inputs))
        lines_out.append(' Lineas FX Generadas      : {:10d}'.format(self.total_lines_generated))
        if total_wall_time > 0 and self.total_lines_generated > 0:
            rate = self.total_lines_generated / total_wall_time
            lines_out.append(' Velocidad de Generacion  : {:10.1f} lineas FX/segundo'.format(rate))
        lines_out.append('-' * 80)

        # 1. DESGLOSE POR FASES
        lines_out.append(' [1] DESGLOSE TEMPORAL POR FASES:')
        h_fase, h_t, h_pct = 'Fase', 'Tiempo (ms)', '% del Total'
        lines_out.append('  {:<38} | {:<15} | {:<12}'.format(h_fase, h_t, h_pct))
        lines_out.append('  ' + '-' * 68)
        
        phase_labels = {
            'parse_ass': 'Lectura y Parsing ASS (Karaskel)',
            'audio_preprocess': 'Preprocesamiento Audio (FFmpeg/WAV)',
            'graph_prep': 'Compilacion y Cadenas de Bucles',
            'workers_exec': 'Ejecucion de Bucles y Nodos',
            'ipc_gather': 'Recoleccion y Deserializacion IPC',
            'post_process_sort': 'Ordenamiento Determinista (Colas/Layer)',
            'format_ass_lines': 'Formateo de Cadenas de Texto ASS',
            'disk_io': 'Escritura a Disco (result.txt / fsync)'
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
            lines_out.append('  {:<38} | {:12.2f} ms | {:10.1f} %'.format('Otras operaciones / Overhead', other_t, other_pct))

        lines_out.append('-' * 80)

        # 2. RENDIMIENTO POR NODO
        if self.node_stats:
            lines_out.append(' [2] NODOS CON MAYOR CONSUMO DE TIEMPO (TOP BOTTLENECKS):')
            lines_out.append('  {:<5} | {:<30} | {:<10} | {:<12} | {:<10} | {:<8}'.format('ID', 'Tipo de Nodo', 'Llamadas', 'Total (ms)', 'Prom (us)', '% Grafo'))
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

        # 3. DISTRIBUCION DE WORKERS
        if self.worker_stats:
            lines_out.append(' [3] DISTRIBUCION DE CARGA ENTRE WORKERS (NUCLEOS CPU):')
            lines_out.append('  {:<12} | {:<15} | {:<15} | {:<15}'.format('Worker ID', 'Lineas Proc.', 'Duracion (ms)', 'Desviacion'))
            lines_out.append('  ' + '-' * 65)

            durations = [w['duration'] for w in self.worker_stats.values()]
            avg_dur = sum(durations) / max(1, len(durations))

            for w_id, wst in sorted(self.worker_stats.items()):
                w_ms = wst['duration'] * 1000.0
                diff_pct = ((wst['duration'] - avg_dur) / max(1e-6, avg_dur)) * 100.0
                diff_str = '{:+.1f} %'.format(diff_pct)
                lines_out.append('  Worker #{:<4} | {:15d} | {:12.2f} ms | {:>12}'.format(w_id, wst['lines'], w_ms, diff_str))

            lines_out.append('-' * 80)

        # 4. DIAGNOSTICO AUTOMATICO
        lines_out.append(' [4] DIAGNOSTICO AUTOMATICO & RECOMENDACIONES:')
        warnings_found = False

        if self.worker_stats:
            max_w = max(self.worker_stats.items(), key=lambda kv: kv[1]['duration'])
            min_w = min(self.worker_stats.items(), key=lambda kv: kv[1]['duration'])
            if max_w[1]['duration'] > 2.0 * max(0.01, min_w[1]['duration']):
                warnings_found = True
                lines_out.append('  * [ALERTA DE DESBALANCE]: El Worker #{} tardo {:.1f}ms mientras que el Worker #{} tardo solo {:.1f}ms.'.format(
                    max_w[0], max_w[1]['duration']*1000, min_w[0], min_w[1]['duration']*1000))
                lines_out.append('    -> Causa: Un bloque de lineas tiene bucles significativamente mas densos que los demas.')
                lines_out.append('    -> Esto explica la pausa en el medidor (80%-83%) mientras todos los cores esperan al ultimo.')

        if self.node_stats:
            sorted_nodes = sorted(self.node_stats.items(), key=lambda kv: kv[1]['total_time'], reverse=True)
            for n_id, st in sorted_nodes[:3]:
                tot_ms = st['total_time'] * 1000.0
                if tot_ms > 200.0 and (st['total_time'] / max(1e-6, total_wall_time)) > 0.35:
                    warnings_found = True
                    lines_out.append('  * [CUELLO DE BOTELLA EN NODO #{} ({})]:'.format(n_id, st['type']))
                    lines_out.append('    -> Consumio {:.1f}ms ({:.1f}% del tiempo total).'.format(tot_ms, (st['total_time']/total_wall_time)*100))
                    if 'IMG to pixels' in st['type'] or 'Particulas' in st['type']:
                        lines_out.append('    -> Recomendacion: Aumentar el Paso (step) o verificar que el frame no este evaluandose redundantemente.')
                    elif 'Codigo Script' in st['type'] or 'Code' in st['type']:
                        lines_out.append('    -> Recomendacion: Optimizar el script de Python dentro del nodo para reducir operaciones por linea.')

        sort_t = self.phase_times.get('post_process_sort', 0.0) + self.phase_times.get('format_ass_lines', 0.0)
        if sort_t > 0.3 and (sort_t / max(1e-6, total_wall_time)) > 0.20:
            warnings_found = True
            lines_out.append('  * [POST-PROCESAMIENTO PESADO]: El ordenamiento y formateo de texto tomo {:.1f}ms.'.format(sort_t*1000))
            lines_out.append('    -> Se generaron {} lineas. Reducir la cantidad de eventos generados si es posible.'.format(self.total_lines_generated))

        if not warnings_found:
            lines_out.append('  * Excelente: El grafo y los workers estan balanceados y ejecutandose a maxima eficiencia.')

        lines_out.append('=' * 80)
        return '\n'.join(lines_out)

    def save_report(self, file_path: str = 'pyxis_performance_report.txt'):
        report_text = self.generate_report()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        return file_path

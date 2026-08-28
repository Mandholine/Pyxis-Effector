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

# PyxisNodes/tests/test_progress_v099.py
"""Pruebas unitarias para el contador y barra de progreso basada en unidades reales de procesamiento (v1.0.1)."""

import unittest
from models import PyxisLine, PyxisUnit
from node_engine import GraphEngine


class TestProgressV099(unittest.TestCase):

    def setUp(self):
        # 4 líneas de diálogo en total (simulando proyecto con 1 línea seleccionada)
        self.dialogues = []
        for line_num in range(1, 5):
            line = PyxisLine()
            line.text = f"Line {line_num}"
            line.style_name = "Default"
            line.syls = []
            for syl_num in range(1, 5):  # 4 sílabas por línea
                u = PyxisUnit()
                u.i = syl_num
                u.n = 4
                u.text = f"syl_{line_num}_{syl_num}"
                u.text_stripped = f"syl_{line_num}_{syl_num}"
                u.line = line
                line.syls.append(u)
            # Solo la línea 1 está seleccionada
            is_sel = (line_num == 1)
            line.is_selected = is_sel
            raw = f"Dialogue: 0,0:00:0{line_num}.00,0:00:0{line_num+2}.00,Default,,0,0,0,,{{\\k10}}a{{\\k10}}b{{\\k10}}c{{\\k10}}d"
            self.dialogues.append({"raw": raw, "line": line, "metrics": {"sel": is_sel}})

        self.styles = {"Default": {}}

        # Grafo con Main Loop en SYL y salida
        self.graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl", "bucle": "SYL", "noblank": "No Blank"},
                    "outputs": [{"name": "Loop", "type": "loop", "links": [10]}]
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [{"name": "Loop / Domain", "type": "loop", "link": 10}]
                }
            ],
            "links": [
                [10, 1, 0, 2, 0, "loop"]
            ]
        }

    def test_progress_reports_multiple_substeps_per_syllable(self):
        """Verifica que el progreso avance proporcionalmente por cada sílaba de la línea seleccionada en vez de clavarse en 25%."""
        recorded_progress = []

        def on_progress(pct):
            val = pct.get('percent', 0) if isinstance(pct, dict) else pct
            recorded_progress.append(val)

        engine = GraphEngine(self.graph)
        engine.process(self.dialogues, self.styles, progress_callback=on_progress)

        self.assertTrue(len(recorded_progress) >= 4, f"Se esperaban múltiples llamadas de progreso, recibidas: {recorded_progress}")
        self.assertIn(100, recorded_progress)
        # Verificar que haya pasos intermedios (ej. 25%, 50%, 75% o más)
        distinct_progress = sorted(list(set(recorded_progress)))
        self.assertGreater(len(distinct_progress), 2, f"Progreso demasiado estático: {distinct_progress}")
        # El progreso debe ser monotónicamente creciente
        for i in range(len(distinct_progress) - 1):
            self.assertLessEqual(distinct_progress[i], distinct_progress[i+1])


if __name__ == '__main__':
    unittest.main()

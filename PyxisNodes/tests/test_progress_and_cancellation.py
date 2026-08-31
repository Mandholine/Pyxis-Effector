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

import unittest
import time
import threading
from node_engine import GraphEngine, abort_global_multiprocessing

class TestProgressAndCancellation(unittest.TestCase):
    def setUp(self):
        self.graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl"},
                    "inputs": [],
                    "outputs": [{"name": "Loop Out", "type": "FLOW", "links": [1]}]
                },
                {
                    "id": 2,
                    "type": "Loops/MaxLoop",
                    "properties": {"veces": "100", "modo": "Normal", "var_name": "j"},
                    "inputs": [{"name": "Loop In", "type": "FLOW", "link": 1}],
                    "outputs": [{"name": "Loop Out", "type": "FLOW", "links": [2]}]
                },
                {
                    "id": 3,
                    "type": "Control/Salida",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [{"name": "Loop In", "type": "FLOW", "link": 2}],
                    "outputs": []
                }
            ],
            "links": [
                [1, 1, 0, 2, 0, "FLOW"],
                [2, 2, 0, 3, 0, "FLOW"]
            ]
        }
        self.raw = 'Dialogue: 1,0:00:01.00,0:00:05.00,Default,,0,0,0,,{\\k50}S1 {\\k50}S2 {\\k50}S3 {\\k50}S4 {\\k50}S5'
        self.metrics = {
            'h': 35, 'd': 0, 'e': 0, 'sel': True, 'rw': 500, 'l': 100, 'c': 350, 'r': 600, 't': 50, 'm': 65, 'b': 80,
            'syl_lefts': [100, 200, 300, 400, 500],
            'syl_centers': [150, 250, 350, 450, 550],
            'syl_rights': [200, 300, 400, 500, 600],
            'syl_widths': [100, 100, 100, 100, 100],
            'syl_starts': [1000, 1500, 2000, 2500, 3000],
            'syl_ends':   [1500, 2000, 2500, 3000, 3500],
            'w': [100, 100, 100, 100, 100]
        }

    def test_realtime_progress_callback(self):
        engine = GraphEngine(self.graph_data, 1280, 720, 41.708)
        progress_updates = []

        def on_prog(data):
            progress_updates.append(data)

        lines = engine.process([{'raw': self.raw, 'metrics': self.metrics}], {'Default': {}}, progress_callback=on_prog)
        self.assertEqual(len(lines), 500)
        self.assertGreater(len(progress_updates), 3)
        has_lines = any(isinstance(u, dict) and u.get('lines_generated', 0) > 0 for u in progress_updates)
        self.assertTrue(has_lines)

    def test_instant_cancellation(self):
        heavy_graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl"},
                    "inputs": [],
                    "outputs": [{"name": "Loop Out", "type": "FLOW", "links": [1]}]
                },
                {
                    "id": 2,
                    "type": "Loops/MaxLoop",
                    "properties": {"veces": "5000", "modo": "Normal", "var_name": "j"},
                    "inputs": [{"name": "Loop In", "type": "FLOW", "link": 1}],
                    "outputs": [{"name": "Loop Out", "type": "FLOW", "links": [2]}]
                },
                {
                    "id": 3,
                    "type": "Control/Salida",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [{"name": "Loop In", "type": "FLOW", "link": 2}],
                    "outputs": []
                }
            ],
            "links": [
                [1, 1, 0, 2, 0, "FLOW"],
                [2, 2, 0, 3, 0, "FLOW"]
            ]
        }
        engine = GraphEngine(heavy_graph, 1280, 720, 41.708)

        def cancel_trigger():
            time.sleep(0.02)
            engine.is_cancelled = True
            if getattr(engine, 'shared_cancel_flag', None) is not None:
                engine.shared_cancel_flag.value = True
            abort_global_multiprocessing()

        th = threading.Thread(target=cancel_trigger)
        th.start()

        t0 = time.perf_counter()
        lines = engine.process([{'raw': self.raw, 'metrics': self.metrics}], {'Default': {}})
        t1 = time.perf_counter()
        th.join()

        self.assertTrue(engine.is_cancelled)
        self.assertLess(t1 - t0, 0.8)
        self.assertLess(len(lines), 25000)

    def test_multiprocessing_progress_and_cancel(self):
        heavy_graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl"},
                    "inputs": [],
                    "outputs": [{"name": "Loop Out", "type": "FLOW", "links": [1]}]
                },
                {
                    "id": 2,
                    "type": "Loops/MaxLoop",
                    "properties": {"veces": "200", "modo": "Normal", "var_name": "j"},
                    "inputs": [{"name": "Loop In", "type": "FLOW", "link": 1}],
                    "outputs": [{"name": "Loop Out", "type": "FLOW", "links": [2]}]
                },
                {
                    "id": 3,
                    "type": "Control/Salida",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [{"name": "Loop In", "type": "FLOW", "link": 2}],
                    "outputs": []
                }
            ],
            "links": [
                [1, 1, 0, 2, 0, "FLOW"],
                [2, 2, 0, 3, 0, "FLOW"]
            ]
        }
        engine = GraphEngine(heavy_graph, 1280, 720, 41.708)
        items = [
            {'raw': self.raw, 'metrics': self.metrics},
            {'raw': self.raw, 'metrics': self.metrics},
            {'raw': self.raw, 'metrics': self.metrics},
            {'raw': self.raw, 'metrics': self.metrics}
        ]
        updates = []
        lines = engine.process(items, {'Default': {}}, progress_callback=lambda u: updates.append(u), use_multiprocessing=True)
        # 4 lines * 5 syls * 200 = 4000 lines
        self.assertEqual(len(lines), 4000)
        self.assertGreaterEqual(len(updates), 5)
        last_update = updates[-1]
        self.assertEqual(last_update.get('lines_generated'), 4000)

    def test_pyxis_api_cancel_preview_and_hardsub(self):
        from unittest.mock import MagicMock
        from main import PyxisAPI
        
        api = PyxisAPI("dummy.ass", "dummy_res.ass", "dummy_sess.json")
        
        # Test cancel_preview when engine is active
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        api._active_preview_engine = mock_engine
        
        res = api.cancel_preview("node_123")
        self.assertTrue(res.get("success"))
        self.assertTrue(res.get("cancelled"))
        self.assertTrue(mock_engine.is_cancelled)
        self.assertIsNone(api._active_preview_engine)
        
        # Test cancel_hardsub when engine and proc are active
        mock_hard_engine = MagicMock()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None # Process still running
        
        api._active_hardsub_engine = mock_hard_engine
        api._active_hardsub_proc = mock_proc
        
        res_h = api.cancel_hardsub("node_123")
        self.assertTrue(res_h.get("success"))
        self.assertTrue(res_h.get("cancelled"))
        self.assertTrue(mock_hard_engine.is_cancelled)
        mock_proc.kill.assert_called_once()
        self.assertIsNone(api._active_hardsub_engine)
        self.assertIsNone(api._active_hardsub_proc)

if __name__ == "__main__":
    unittest.main()

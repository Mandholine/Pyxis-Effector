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

import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from node_engine import GraphEngine
from models import PyxisLine, PyxisUnit


def create_mock_graph_with_maxloop(veces=25):
    """Crea un grafo con Main Loop -> MaxLoop(veces) -> Salida."""
    return {
        "nodes": [
            {
                "id": 1,
                "type": "Loops/Main Loop",
                "properties": {"iterador": "line"},
                "inputs": [],
                "outputs": [{"name": "bucle", "type": "bucle"}]
            },
            {
                "id": 2,
                "type": "Loops/MaxLoop",
                "properties": {"veces": str(veces), "var_name": "j"},
                "inputs": [{"name": "in", "link": 101}],
                "outputs": [{"name": "out", "type": "bucle"}]
            },
            {
                "id": 3,
                "type": "System/Output",
                "properties": {"apply_to": "Selected Lines"},
                "inputs": [
                    {"name": "bucle", "link": 102},
                    {"name": "layer", "link": None},
                    {"name": "st", "link": None},
                    {"name": "et", "link": None},
                    {"name": "tags", "link": None},
                    {"name": "retorno", "link": None}
                ],
                "outputs": []
            }
        ],
        "links": [
            [101, 1, 0, 2, 0],
            [102, 2, 0, 3, 0]
        ]
    }


def test_progress_callback():
    graph_data = create_mock_graph_with_maxloop(veces=10)
    engine = GraphEngine(graph_data)

    progress_reports = []

    def on_progress(percent):
        progress_reports.append(percent)

    dialogue_items = [
        {
            'raw': 'Dialogue: 0,0:00:01.00,0:00:05.00,Default,,0,0,0,,Hola mundo',
            'metrics': {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': True, 'w': [20.0]*10}
        }
    ]
    styles = {'Default': {}}

    lines = engine.process(dialogue_items, styles, progress_callback=on_progress)

    assert len(lines) == 10
    assert len(progress_reports) > 0
    assert 100 in progress_reports


def test_truncation_on_10_lines():
    """Prueba que la generación se trunca al alcanzar 10 líneas cuando el callback de cancelación devuelve True."""
    graph_data = create_mock_graph_with_maxloop(veces=35)
    engine = GraphEngine(graph_data)

    call_count = [0]

    def check_cancel():
        call_count[0] += 1
        return True

    dialogue_items = [
        {
            'raw': 'Dialogue: 0,0:00:01.00,0:00:05.00,Default,,0,0,0,,Prueba de truncado',
            'metrics': {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': True, 'w': [20.0]*18}
        }
    ]
    styles = {'Default': {}}

    lines = engine.process(dialogue_items, styles, check_cancel_callback=check_cancel)

    assert len(lines) == 10
    assert engine.is_cancelled is True
    assert call_count[0] == 1

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

# PyxisNodes/tests/test_audio_temporal_control.py
"""Tests unitarios para verificar el control de Tiempo Inicio y Tiempo Fin en Audio Modulador y Audio Waveform."""

import math
import os
import shutil
import struct
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from audio_engine import AudioEngine
from nodes.audio_nodes import audio_modulator_master, audio_waveform_master
from node_engine import GraphEngine


def create_test_wav(file_path: str, duration_s: float = 4.0, sample_rate: int = 44100) -> str:
    """Crea un WAV sintético de 4 segundos con modulación de volumen y tonos variables."""
    num_frames = int(duration_s * sample_rate)
    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_frames):
            t = float(i) / sample_rate
            amp = 0.5 * (1.0 + math.sin(2.0 * math.pi * 2.0 * t))
            val = int(amp * 0.8 * 32767.0 * math.sin(2.0 * math.pi * 120.0 * t))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return file_path


class TestAudioTemporalControl(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="pyxis_test_temp_audio_")
        self.wav_path = os.path.join(self.temp_dir, "test_track_4s.wav")
        create_test_wav(self.wav_path, duration_s=4.0)
        AudioEngine.clear_cache()

    def tearDown(self):
        AudioEngine.clear_cache()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_audio_modulator_default_blank_takes_fx_dur(self):
        """Si start_time y end_time están en blanco, debe tomar 0 a fx.dur (ej. 3000ms en contexto CHAR)."""
        context = {
            "start_time": 1000,
            "end_time": 1200,      # Unidad activa dura solo 200ms
            "fx_start_time": 1000,
            "fx_end_time": 4000,   # Efecto total dura 3000ms
            "fx_dur": 3000,
            "default_audio_source": self.wav_path
        }

        res = audio_modulator_master(
            context=context,
            audio_path=self.wav_path,
            tag_name="fscy",
            min_val=100,
            max_val=160,
            step_ms=41.7,
            start_time="",
            end_time="",
            output_slot_index=0
        )

        total_t = res.count(r"\t(")
        self.assertGreater(total_t, 50, f"Esperadas >50 transformaciones para 3000ms, obtenidas: {total_t}")
        self.assertIn(r"\fscy", res)

    def test_audio_modulator_custom_start_and_end_time(self):
        """Si start_time y end_time están especificados, debe muestrear en ese intervalo exacto."""
        context = {
            "start_time": 0,
            "end_time": 4000,
            "fx_start_time": 0,
            "fx_end_time": 4000,
            "fx_dur": 4000,
            "default_audio_source": self.wav_path
        }

        res_custom = audio_modulator_master(
            context=context,
            audio_path=self.wav_path,
            tag_name="fscy",
            min_val=100,
            max_val=160,
            step_ms=50.0,
            start_time="500",
            end_time="800",
            output_slot_index=0
        )

        total_t_custom = res_custom.count(r"\t(")
        self.assertLessEqual(total_t_custom, 8)
        self.assertGreaterEqual(total_t_custom, 4)

        vals = audio_modulator_master(
            context=context,
            audio_path=self.wav_path,
            tag_name="fscy",
            min_val=100,
            max_val=160,
            step_ms=50.0,
            start_time="500",
            end_time="800",
            output_slot_index=2
        )
        self.assertEqual(len(vals), 7)

    def test_audio_waveform_custom_start_and_end_time(self):
        """Audio Waveform debe respetar start_time y end_time personalizados cuando se proveen."""
        context = {
            "start_time": 0,
            "end_time": 4000,
            "fx_start_time": 0,
            "fx_end_time": 4000,
            "default_audio_source": self.wav_path
        }

        res_bands = audio_waveform_master(
            context=context,
            audio_path=self.wav_path,
            modo="Barras FFT",
            muestras=16,
            start_time="1000",
            end_time="1500",
            output_slot_index=4
        )
        self.assertIsInstance(res_bands, list)
        self.assertEqual(len(res_bands), 16)

    def test_graphengine_audio_modulator_with_time_ports(self):
        """Verifica la ejecución de un grafo completo en GraphEngine con Audio Modulador y puertos de tiempo."""
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "line", "noblank": "No Blank"},
                    "outputs": [{"name": "Loop", "links": [101]}]
                },
                {
                    "id": 2,
                    "type": "Audio/Audio Modulator",
                    "properties": {
                        "tag_name": "fscy",
                        "min_val": "100",
                        "max_val": "150",
                        "step_ms": "50",
                        "start_time": "",
                        "end_time": ""
                    },
                    "inputs": [
                        {"name": "Audio Path", "link": None, "value": ""},
                        {"name": "Tag", "link": None, "value": "fscy"},
                        {"name": "Min Val", "link": None, "value": "100"},
                        {"name": "Max Val", "link": None, "value": "150"},
                        {"name": "Ganancia", "link": None, "value": "1.0"},
                        {"name": "Step ms", "link": None, "value": "50"},
                        {"name": "Smoothing", "link": None, "value": "0.2"},
                        {"name": "Start Time", "link": None, "value": ""},
                        {"name": "End Time", "link": None, "value": ""}
                    ],
                    "outputs": [{"name": "Tags Out", "links": [102]}]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 101},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": 102},
                        {"name": "Return", "link": None}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 3, 0, "Loop"],
                [102, 2, 0, 3, 4, "Tags Out"]
            ]
        }

        engine = GraphEngine(graph_data, 1280, 720, 41.708, default_audio_source=self.wav_path)
        dialogues = [{
            "raw": "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Línea de prueba",
            "metrics": {
                "h": 35, "d": 0, "e": 0, "sel": True, "rw": 100, "l": 50, "c": 100, "r": 150, "t": 50, "m": 65, "b": 80,
                "syl_lefts": [50], "syl_centers": [100], "syl_rights": [150], "syl_widths": [100],
                "syl_starts": [1000], "syl_ends": [3000], "w": [100]
            }
        }]
        styles = {"Default": {}}

        lines = engine.process(dialogues, styles)
        self.assertEqual(len(lines), 1)
        line_ass = lines[0]
        self.assertTrue(line_ass.startswith("Dialogue:"))
        self.assertIn(r"\fscy", line_ass)
        self.assertIn(r"\t(", line_ass)
        self.assertGreater(line_ass.count(r"\t("), 30)


if __name__ == "__main__":
    unittest.main()

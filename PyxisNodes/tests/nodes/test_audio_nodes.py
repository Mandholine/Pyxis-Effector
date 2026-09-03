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

"""Pruebas unitarias completas para nodos de analisis, modulacion y renderizado de audio."""

import math
import os
import shutil
import struct
import tempfile
import unittest
import wave
from unittest.mock import patch, MagicMock

from audio_engine import AudioEngine
from nodes.audio_nodes import (
    audio_modulator_master,
    audio_waveform_master,
    audio_rms,
    audio_peak,
    audio_band,
    audio_fft,
    resolve_audio_data
)


def create_test_wav(
    file_path: str,
    duration_s: float = 1.0,
    sample_rate: int = 44100,
    freq: float = 440.0,
    amplitude: float = 0.8
) -> str:
    """Crea un WAV sintetico para pruebas unitarias."""
    num_frames = int(duration_s * sample_rate)
    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_frames):
            t = float(i) / sample_rate
            val = int(amplitude * 32767.0 * math.sin(2.0 * math.pi * freq * t))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return file_path


class TestAudioModulator(unittest.TestCase):
    """Pruebas para el motor de modulacion de audio (RMS, Peak, Bandas FFT)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.wav_path = os.path.join(self.temp_dir, "test_440hz.wav")
        create_test_wav(self.wav_path, duration_s=0.5, freq=440.0, amplitude=0.8)
        AudioEngine.clear_cache()
        self.context = {
            "start_time": 0,
            "end_time": 500,
            "st": 0,
            "et": 500,
            "default_audio_source": self.wav_path,
            "active_unit": type("Syl", (), {
                "i": 1,
                "n": 1,
                "start_time": 0,
                "end_time": 500,
                "duration": 500,
                "dur": 500,
                "text_stripped": "Test",
                "center": 100.0,
                "middle": 200.0
            })()
        }

    def tearDown(self):
        AudioEngine.clear_cache()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_audio_engine_load_and_rms(self):
        audio_data = AudioEngine.load_wav(self.wav_path)
        self.assertIsNotNone(audio_data)
        self.assertGreater(audio_data.duration_ms, 400)
        rms = audio_data.get_rms(0, 200)
        self.assertGreater(rms, 0.1)

    def test_audio_peak(self):
        audio_data = AudioEngine.load_wav(self.wav_path)
        peak = audio_data.get_peak(0, 200)
        self.assertGreater(peak, 0.5)

    def test_audio_fft_bands(self):
        audio_data = AudioEngine.load_wav(self.wav_path)
        bands = audio_data.get_fft_bands(0, 200, num_bands=8)
        self.assertEqual(len(bands), 8)
        self.assertTrue(any(b > 0.0 for b in bands))

    def test_audio_modulator_tag_chain(self):
        tag_chain = audio_modulator_master(
            context=self.context,
            audio_path=self.wav_path,
            tag_name="fscy",
            min_val="100",
            max_val="200",
            modo="RMS (Volumen)",
            step_ms="50"
        )
        self.assertIsNotNone(tag_chain)
        self.assertIn(r"\fscy", tag_chain)


class TestAudioWaveform(unittest.TestCase):
    """Pruebas de generacion vectorial de ondas de audio (ASSDraw y posicionamiento)."""

    def setUp(self):
        self.mock_audio = MagicMock()
        self.mock_audio.get_fft_bands.return_value = [0.1, 0.5, 0.8, 0.3]
        self.mock_audio.get_samples.return_value = [0.0, 0.5, -0.5, 0.0]

    @patch('nodes.audio_nodes.resolve_audio_data')
    def test_audio_waveform_fft_bars(self, mock_resolve):
        mock_resolve.return_value = self.mock_audio
        context = {'x': 100.0, 'y': 200.0, 'start_time': 0, 'end_time': 1000}

        shape_str = audio_waveform_master(
            context=context,
            audio_path="dummy.wav",
            modo="Barras FFT",
            ancho="400",
            alto="60",
            muestras="4",
            ganancia="1.0",
            output_slot_index=0
        )
        self.assertTrue(isinstance(shape_str, str))
        self.assertTrue(shape_str.startswith("m "))
        self.assertIn("l ", shape_str)

        pos_tag = audio_waveform_master(
            context=context,
            audio_path="dummy.wav",
            modo="Barras FFT",
            ancho="400",
            alto="60",
            muestras="4",
            ganancia="1.0",
            output_slot_index=1
        )
        self.assertEqual(pos_tag, r"\pos(100,200)")


if __name__ == "__main__":
    unittest.main()

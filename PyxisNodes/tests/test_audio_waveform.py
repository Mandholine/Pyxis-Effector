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
from unittest.mock import patch, MagicMock
from nodes.audio_nodes import audio_waveform_master


class TestAudioWaveform(unittest.TestCase):
    def setUp(self):
        self.mock_audio = MagicMock()
        self.mock_audio.get_fft_bands.return_value = [0.1, 0.5, 0.8, 0.3]
        self.mock_audio.get_samples.return_value = [0.0, 0.5, -0.5, 0.0]

    @patch('nodes.audio_nodes.resolve_audio_data')
    def test_audio_waveform_fft_bars(self, mock_resolve):
        mock_resolve.return_value = self.mock_audio

        context = {'x': 100.0, 'y': 200.0, 'start_time': 0, 'end_time': 1000}
        
        # Test Slot 0 (Shape string)
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

        # Test Slot 1 (\pos tag)
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

        # Test Slot 2 (X Array)
        x_coords = audio_waveform_master(
            context=context,
            audio_path="dummy.wav",
            modo="Barras FFT",
            ancho="400",
            alto="60",
            muestras="4",
            ganancia="1.0",
            output_slot_index=2
        )
        self.assertTrue(isinstance(x_coords, list))
        self.assertEqual(len(x_coords), 16) # 4 barras x 4 vértices cada una

        # Test Slot 3 (Y Array)
        y_coords = audio_waveform_master(
            context=context,
            audio_path="dummy.wav",
            modo="Barras FFT",
            ancho="400",
            alto="60",
            muestras="4",
            ganancia="1.0",
            output_slot_index=3
        )
        self.assertTrue(isinstance(y_coords, list))
        self.assertEqual(len(y_coords), 16)

        # Test Slot 4 (Bandas Array)
        raw_bands = audio_waveform_master(
            context=context,
            audio_path="dummy.wav",
            modo="Barras FFT",
            ancho="400",
            alto="60",
            muestras="4",
            ganancia="1.0",
            output_slot_index=4
        )
        self.assertEqual(raw_bands, [0.1, 0.5, 0.8, 0.3])

    @patch('nodes.audio_nodes.resolve_audio_data')
    def test_audio_waveform_oscilloscope(self, mock_resolve):
        mock_resolve.return_value = self.mock_audio

        context = {'x': 100.0, 'y': 200.0, 'start_time': 0, 'end_time': 1000}
        
        shape_str = audio_waveform_master(
            context=context,
            audio_path="dummy.wav",
            modo="Osciloscopio",
            ancho="400",
            alto="60",
            muestras="4",
            ganancia="2.0",
            grosor="4",
            output_slot_index=0
        )
        self.assertTrue(isinstance(shape_str, str))
        self.assertTrue(shape_str.startswith("m "))
        self.assertIn("l ", shape_str)

    @patch('nodes.audio_nodes.resolve_audio_data')
    def test_audio_waveform_radial(self, mock_resolve):
        mock_resolve.return_value = self.mock_audio

        context = {'x': 100.0, 'y': 200.0, 'start_time': 0, 'end_time': 1000}
        
        shape_str = audio_waveform_master(
            context=context,
            audio_path="dummy.wav",
            modo="Radial Circular",
            ancho="400",
            alto="60",
            muestras="4",
            output_slot_index=0
        )
        self.assertTrue(isinstance(shape_str, str))
        self.assertTrue(shape_str.startswith("m "))
        self.assertIn("l ", shape_str)

    @patch('nodes.audio_nodes.resolve_audio_data')
    def test_audio_waveform_filled(self, mock_resolve):
        mock_resolve.return_value = self.mock_audio

        context = {'x': 100.0, 'y': 200.0, 'start_time': 0, 'end_time': 1000}
        
        shape_str = audio_waveform_master(
            context=context,
            audio_path="dummy.wav",
            modo="Onda Rellena",
            ancho="400",
            alto="60",
            muestras="4",
            output_slot_index=0
        )
        self.assertTrue(isinstance(shape_str, str))
        self.assertTrue(shape_str.startswith("m 0 30"))
        self.assertIn("l ", shape_str)

    @patch('nodes.audio_nodes.resolve_audio_data')
    def test_audio_waveform_dots(self, mock_resolve):
        mock_resolve.return_value = self.mock_audio

        context = {'x': 100.0, 'y': 200.0, 'start_time': 0, 'end_time': 1000}
        
        shape_str = audio_waveform_master(
            context=context,
            audio_path="dummy.wav",
            modo="Puntos",
            ancho="400",
            alto="60",
            muestras="4",
            grosor="2",
            output_slot_index=0
        )
        self.assertTrue(isinstance(shape_str, str))
        self.assertTrue(shape_str.startswith("m "))
        self.assertIn("l ", shape_str)


if __name__ == '__main__':
    unittest.main()

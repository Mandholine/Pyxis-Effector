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

# PyxisNodes/tests/test_audio_preprocessor.py
"""Tests unitarios para el preprocesador de audio FFmpeg y el motor de análisis acústico AudioEngine."""

import math
import os
import shutil
import struct
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from audio_preprocessor import AudioPreprocessor
from audio_engine import AudioEngine, AudioData
from ass_parser import ASSParser, ASSParseResult


def create_synthetic_wav(
    file_path: str,
    duration_s: float = 1.0,
    sample_rate: int = 44100,
    freq: float = 440.0,
    amplitude: float = 0.8,
    channels: int = 1
) -> str:
    """Genera un archivo PCM WAV sintético con una onda sinusoidal pura para pruebas."""
    num_frames = int(duration_s * sample_rate)
    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(num_frames):
            t = float(i) / sample_rate
            val = int(amplitude * 32767.0 * math.sin(2.0 * math.pi * freq * t))
            for _ in range(channels):
                frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return file_path


class TestAudioPreprocessorAndEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="pyxis_test_audio_")
        self.sine_wav = os.path.join(self.temp_dir, "sine_440hz.wav")
        create_synthetic_wav(self.sine_wav, duration_s=1.0, sample_rate=44100, freq=440.0, amplitude=0.8)
        AudioEngine.clear_cache()

    def tearDown(self):
        AudioEngine.clear_cache()
        if os.path.isdir(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # PRUEBAS DEL PREPROCESADOR DE AUDIO (FFmpeg & Smart Cache)
    # -------------------------------------------------------------------------
    def test_ffmpeg_path_detection(self):
        """Verifica que se detecte el binario ffmpeg.exe."""
        ffmpeg_bin = AudioPreprocessor.get_ffmpeg_path()
        self.assertIsNotNone(ffmpeg_bin, "ffmpeg.exe debe ser localizado en PyxisNodes o PATH")
        self.assertTrue(os.path.isfile(ffmpeg_bin), f"El archivo {ffmpeg_bin} debe existir")

    def test_is_pcm_wav(self):
        """Verifica la detección de archivos WAV válidos."""
        self.assertTrue(AudioPreprocessor.is_pcm_wav(self.sine_wav))
        
        # Archivo falso / no WAV
        fake_file = os.path.join(self.temp_dir, "fake.mp4")
        with open(fake_file, "w", encoding="utf-8") as f:
            f.write("esto no es un archivo wav ni mp4 real")
        self.assertFalse(AudioPreprocessor.is_pcm_wav(fake_file))
        self.assertFalse(AudioPreprocessor.is_pcm_wav(""))

    def test_compute_cache_key(self):
        """Verifica la consistencia del hash de caché."""
        key1 = AudioPreprocessor.compute_cache_key(self.sine_wav, stream_idx=0)
        key2 = AudioPreprocessor.compute_cache_key(self.sine_wav, stream_idx=0)
        key_stream1 = AudioPreprocessor.compute_cache_key(self.sine_wav, stream_idx=1)
        
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key_stream1)
        self.assertEqual(len(key1), 16)

    def test_ensure_audio_wav_with_valid_wav(self):
        """Si el archivo ya es WAV, debe retornarlo directamente sin invocar FFmpeg."""
        res_wav = AudioPreprocessor.ensure_audio_wav(self.sine_wav)
        self.assertEqual(os.path.abspath(res_wav), os.path.abspath(self.sine_wav))

    def test_ensure_audio_wav_with_invalid_paths(self):
        """Valida que rutas inválidas o inexistentes lancen excepciones claras."""
        with self.assertRaises(ValueError):
            AudioPreprocessor.ensure_audio_wav("")
        with self.assertRaises(FileNotFoundError):
            AudioPreprocessor.ensure_audio_wav(os.path.join(self.temp_dir, "no_existe.mp4"))

    def test_ensure_audio_wav_transcode_and_cache(self):
        """Prueba la transcodificación con FFmpeg y la reutilización de caché (Cache Hit)."""
        ffmpeg_bin = AudioPreprocessor.get_ffmpeg_path()
        if not ffmpeg_bin:
            self.skipTest("ffmpeg.exe no disponible en este entorno")

        # 1. Crear un WAV que forzamos a procesar como si fuera un video/audio externo
        ext_audio = os.path.join(self.temp_dir, "input_track.mp3")
        create_synthetic_wav(ext_audio, duration_s=0.5, freq=880.0)

        # 2. Primera extracción (Cache Miss -> Transcode)
        cached_wav = AudioPreprocessor.ensure_audio_wav(ext_audio)
        self.assertTrue(os.path.isfile(cached_wav))
        self.assertTrue(AudioPreprocessor.is_pcm_wav(cached_wav))

        # 3. Segunda extracción (Cache Hit -> 0 ms)
        mtime_before = os.path.getmtime(cached_wav)
        cached_wav2 = AudioPreprocessor.ensure_audio_wav(ext_audio)
        self.assertEqual(cached_wav, cached_wav2)
        self.assertEqual(os.path.getmtime(cached_wav2), mtime_before)

    # -------------------------------------------------------------------------
    # PRUEBAS DEL MOTOR ACÚSTICO (AudioEngine & AudioData)
    # -------------------------------------------------------------------------
    def test_audio_engine_load_wav(self):
        """Verifica la carga y decodificación de WAV a memoria RAM."""
        audio_data = AudioEngine.load_wav(self.sine_wav)
        self.assertIsInstance(audio_data, AudioData)
        self.assertEqual(audio_data.sample_rate, 44100)
        self.assertAlmostEqual(audio_data.duration_ms, 1000.0, delta=5.0)

        # Caché en memoria
        audio_data2 = AudioEngine.load_wav(self.sine_wav)
        self.assertIs(audio_data, audio_data2)

    def test_audio_time_mapping(self):
        """Verifica la conversión entre milisegundos y muestras."""
        audio_data = AudioEngine.load_wav(self.sine_wav)
        idx_500ms = audio_data.sample_from_ms(500.0)
        self.assertEqual(idx_500ms, 22050)
        ms = audio_data.ms_from_sample(22050)
        self.assertAlmostEqual(ms, 500.0, delta=0.1)

    def test_audio_rms_and_peak(self):
        """Verifica el cálculo de energía RMS y pico de una onda sinusoidal de amplitud 0.8."""
        audio_data = AudioEngine.load_wav(self.sine_wav)
        peak = audio_data.get_peak(0, 1000)
        self.assertAlmostEqual(peak, 0.8, delta=0.05)

        # RMS de una onda seno con amplitud A es A / sqrt(2) -> 0.8 / 1.4142 = 0.565
        rms = audio_data.get_rms(0, 1000)
        self.assertAlmostEqual(rms, 0.565, delta=0.05)

        # Silencio
        empty_rms = audio_data.get_rms(5000, 6000)
        self.assertEqual(empty_rms, 0.0)

    def test_audio_get_samples_waveform(self):
        """Verifica la extracción de N muestras para dibujo de osciloscopio."""
        audio_data = AudioEngine.load_wav(self.sine_wav)
        points = audio_data.get_samples(0, 100, num_points=16)
        self.assertEqual(len(points), 16)
        for p in points:
            self.assertTrue(-1.0 <= p <= 1.0)

    def test_audio_fft_spectrum_and_bands(self):
        """Verifica el análisis de espectro FFT en torno a la frecuencia de 440 Hz."""
        audio_data = AudioEngine.load_wav(self.sine_wav)
        
        # 1. Band weight de 440 Hz debe ser significativamente mayor que en agudos (>4000 Hz)
        mid_weight = audio_data.get_band_weight(0, 500, min_hz=400, max_hz=500)
        high_weight = audio_data.get_band_weight(0, 500, min_hz=5000, max_hz=10000)
        self.assertGreater(mid_weight, high_weight)

        # 2. 16 bandas de ecualizador
        bands = audio_data.get_fft_bands(0, 500, num_bands=16)
        self.assertEqual(len(bands), 16)
        for b in bands:
            self.assertTrue(0.0 <= b <= 1.0)

    # -------------------------------------------------------------------------
    # PRUEBAS DEL PARSER ASS Y SERIALIZACIÓN DE METADATOS DE AUDIO
    # -------------------------------------------------------------------------
    def test_ass_parser_audio_and_video_metadata(self):
        """Verifica que ASSParser.read_file extraiga AudioFile y VideoFile manteniendo compatibilidad."""
        ass_content = (
            "[Script Info]\n"
            "PlayResX: 1920\n"
            "PlayResY: 1080\n\n"
            "[Pyxis Config]\n"
            "FrameDuration: 41.708\n"
            "AudioFile: C:/Music/Opening.mkv\n"
            "VideoFile: C:/Videos/Episodio_01.mp4\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,50,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:01.00,0:00:05.00,Default,,0,0,0,,{\\k10}Test {\\k20}Line\n"
        )
        ass_path = os.path.join(self.temp_dir, "test_audio_config.ass")
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        # Desempaquetado tradicional de 5 elementos (compatibilidad absoluta)
        styles, dialogues, rx, ry, fd = ASSParser.read_file(ass_path)
        self.assertEqual(rx, 1920)
        self.assertEqual(ry, 1080)
        self.assertEqual(len(dialogues), 1)

        # Acceso a los atributos extendidos
        res = ASSParser.read_file(ass_path)
        self.assertEqual(res.audio_file, "C:/Music/Opening.mkv")
        self.assertEqual(res.video_file, "C:/Videos/Episodio_01.mp4")


if __name__ == "__main__":
    unittest.main()

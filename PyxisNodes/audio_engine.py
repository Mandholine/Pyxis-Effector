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

# PyxisNodes/audio_engine.py
"""Motor de análisis acústico de alto rendimiento, decodificación PCM WAV en C y cálculo FFT/RMS para PyxisNodes."""

import math
import os
import wave
from typing import Dict, List, Optional, Tuple, Union

import numpy as np


# Tablas precalculadas de ventanas de análisis espectral (Hann)
_HANN_WINDOWS: Dict[int, np.ndarray] = {}


def _get_hann_window(n: int) -> np.ndarray:
    """Obtiene o precalcula la ventana de Hann como un array NumPy float32 contiguo en C."""
    win = _HANN_WINDOWS.get(n)
    if win is None:
        win = (0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(n, dtype=np.float32) / (n - 1)))).astype(np.float32)
        _HANN_WINDOWS[n] = win
    return win


class AudioData:
    """Representa un búfer de audio PCM en memoria normalizado con utilidades de análisis ultra-rápidas."""

    def __init__(self, sample_rate: int, channels: int, samples: np.ndarray):
        self.sample_rate = int(sample_rate)
        self.channels = int(channels)
        # Asegurar array 1D NumPy float32 contiguo
        if not isinstance(samples, np.ndarray) or samples.dtype != np.float32:
            self.samples = np.asarray(samples, dtype=np.float32)
        else:
            self.samples = samples

        self.num_samples = len(self.samples)
        self.duration_ms = (self.num_samples / float(self.sample_rate)) * 1000.0 if self.sample_rate > 0 else 0.0

        # Precalcular suma acumulativa de cuadrados (Prefix Sums) en float64 para cálculo RMS en O(1)
        if self.num_samples > 0:
            self._sq_cumsum = np.concatenate(
                ([0.0], np.cumsum(self.samples.astype(np.float64) ** 2))
            )
        else:
            self._sq_cumsum = np.array([0.0], dtype=np.float64)

        # Caché LRU en memoria para transformadas FFT por intervalo temporal
        self._fft_cache: Dict[Tuple[int, int, int], np.ndarray] = {}

    def sample_from_ms(self, ms: float) -> int:
        """Convierte milisegundos a índice de muestra."""
        if self.sample_rate <= 0:
            return 0
        idx = int(round((ms / 1000.0) * self.sample_rate))
        return max(0, min(self.num_samples, idx))

    def ms_from_sample(self, sample_idx: int) -> float:
        """Convierte índice de muestra a milisegundos."""
        if self.sample_rate <= 0:
            return 0.0
        return (sample_idx / float(self.sample_rate)) * 1000.0

    def get_chunk(self, start_ms: float, end_ms: float) -> np.ndarray:
        """Extrae el segmento de audio (view slice) entre start_ms y end_ms."""
        idx_start = self.sample_from_ms(start_ms)
        idx_end = self.sample_from_ms(end_ms)
        if idx_start >= self.num_samples:
            return np.empty(0, dtype=np.float32)
        if idx_start >= idx_end:
            idx_end = min(self.num_samples, idx_start + 1)
        return self.samples[idx_start:idx_end]

    def get_rms(self, start_ms: float, end_ms: float, gain: float = 1.0) -> float:
        """Calcula la energía acústica cuadrática media (RMS) en O(1) constante mediante Prefix Sums."""
        idx_start = self.sample_from_ms(start_ms)
        idx_end = self.sample_from_ms(end_ms)
        if idx_start >= idx_end:
            idx_end = min(self.num_samples, idx_start + 1)

        count = idx_end - idx_start
        if count <= 0 or idx_start >= self.num_samples:
            return 0.0

        # O(1) resta directa en el arreglo de energía acumulativa
        sum_sq = self._sq_cumsum[idx_end] - self._sq_cumsum[idx_start]
        raw_rms = math.sqrt(max(0.0, sum_sq / count))
        return min(1.0, raw_rms * max(0.0, float(gain)))

    def get_peak(self, start_ms: float, end_ms: float, gain: float = 1.0) -> float:
        """Calcula la amplitud pico absoluta máxima entre 0.0 y 1.0 con ganancia."""
        chunk = self.get_chunk(start_ms, end_ms)
        if len(chunk) == 0:
            return 0.0

        p = float(np.max(np.abs(chunk)))
        return min(1.0, p * max(0.0, float(gain)))

    def get_samples(self, start_ms: float, end_ms: float, num_points: int = 32, gain: float = 1.0) -> List[float]:
        """Submuestrea el intervalo temporal de manera vectorizada en N puntos equidistantes."""
        chunk = self.get_chunk(start_ms, end_ms)
        n = len(chunk)
        if n == 0 or num_points <= 0:
            return [0.0] * max(0, num_points)

        g = max(0.0, float(gain))
        if n == num_points:
            return (chunk * g).tolist() if g != 1.0 else chunk.tolist()

        if num_points == 1:
            return [float(chunk[0]) * g]

        # Vectorización con NumPy linspace
        indices = np.linspace(0, n - 1, num_points, dtype=np.intp)
        sampled = chunk[indices]
        if g != 1.0:
            sampled = sampled * g
        return sampled.tolist()

    def get_fft(self, start_ms: float, end_ms: float, n_fft: int = 2048) -> Tuple[np.ndarray, float]:
        """Calcula la FFT real optimizada con ventana de Hann precalculada y caché LRU por intervalo."""
        idx_start = self.sample_from_ms(start_ms)
        idx_end = self.sample_from_ms(end_ms)
        if idx_start >= idx_end:
            idx_end = min(self.num_samples, idx_start + 1)

        # Ajustar n_fft a potencia de 2
        if n_fft < 16:
            n_fft = 16
        n_pow2 = 1 << (n_fft - 1).bit_length()
        if n_pow2 != n_fft:
            n_fft = n_pow2

        freq_step = float(self.sample_rate) / float(n_fft) if n_fft else 1.0

        # Comprobar caché LRU por índices exactos
        cache_key = (idx_start, idx_end, n_fft)
        if cache_key in self._fft_cache:
            return self._fft_cache[cache_key], freq_step

        chunk = self.samples[idx_start:idx_end]
        chunk_len = len(chunk)
        if chunk_len == 0:
            zeros = np.zeros(n_fft // 2 + 1, dtype=np.float32)
            return zeros, freq_step

        # Vectorización: Hann window precalculada + zero padding directo
        window = _get_hann_window(n_fft)
        pad = np.zeros(n_fft, dtype=np.float32)
        valid_len = min(chunk_len, n_fft)
        pad[:valid_len] = chunk[:valid_len] * window[:valid_len]

        # Fast Real FFT
        fft_res = np.fft.rfft(pad)
        magnitudes = np.abs(fft_res).astype(np.float32)
        mag_sum = float(np.sum(magnitudes))
        if mag_sum > 0:
            magnitudes = magnitudes / (n_fft / 2.0)

        # Manejo de tamaño de caché LRU (máximo 512 entradas)
        if len(self._fft_cache) >= 512:
            old_keys = list(self._fft_cache.keys())[:128]
            for k in old_keys:
                del self._fft_cache[k]

        self._fft_cache[cache_key] = magnitudes
        return magnitudes, freq_step

    def get_band_weight(self, start_ms: float, end_ms: float, min_hz: float, max_hz: float, gain: float = 1.0) -> float:
        """Calcula la energía de frecuencia normalizada en una banda [min_hz, max_hz] con compensación espectral."""
        mags, freq_step = self.get_fft(start_ms, end_ms, n_fft=2048)
        num_mags = len(mags)
        if num_mags == 0 or freq_step <= 0:
            return 0.0

        f_min = float(min_hz)
        f_max = float(max_hz)
        f_center = math.sqrt(max(20.0, f_min) * max(20.0, f_max))
        spectral_boost = min(6.0, max(1.0, math.sqrt(f_center / 250.0)))

        k_start = f_min / freq_step
        k_end = f_max / freq_step

        if k_end - k_start < 1.0:
            k_center = f_center / freq_step
            k_idx = int(k_center)
            frac = k_center - k_idx
            if k_idx >= num_mags - 1:
                combined_energy = float(mags[-1]) if num_mags > 0 else 0.0
            else:
                combined_energy = float(mags[k_idx] * (1.0 - frac) + mags[k_idx + 1] * frac)
        else:
            idx_start = max(0, int(math.floor(k_start)))
            idx_end = min(num_mags, int(math.ceil(k_end)))
            if idx_start >= idx_end:
                idx_end = min(num_mags, idx_start + 1)

            band_slice = mags[idx_start:idx_end]
            if len(band_slice) == 0:
                return 0.0
            avg_mag = float(np.mean(band_slice))
            max_mag = float(np.max(band_slice))
            combined_energy = 0.5 * avg_mag + 0.5 * max_mag

        val = combined_energy * spectral_boost * 3.5 * max(0.0, float(gain))
        return min(1.0, val)

    def get_fft_bands(
        self,
        start_ms: float,
        end_ms: float,
        num_bands: int = 16,
        min_hz: float = 20.0,
        max_hz: float = 16000.0,
        gain: float = 1.0
    ) -> List[float]:
        """Divide el espectro en N bandas de frecuencia con escala logarítmica, interpolación y compensación espectral."""
        if num_bands <= 0:
            return []

        mags, freq_step = self.get_fft(start_ms, end_ms, n_fft=2048)
        num_mags = len(mags)
        if num_mags == 0 or freq_step <= 0:
            return [0.0] * num_bands

        bands = [0.0] * num_bands
        log_min = math.log10(max(10.0, min_hz))
        log_max = math.log10(max(min_hz + 10.0, max_hz))
        g = max(0.0, float(gain))

        for b in range(num_bands):
            f_start = 10.0 ** (log_min + (b / float(num_bands)) * (log_max - log_min))
            f_end = 10.0 ** (log_min + ((b + 1) / float(num_bands)) * (log_max - log_min))
            f_center = math.sqrt(f_start * f_end)
            spectral_boost = min(5.0, max(1.0, math.sqrt(f_center / 300.0)))

            k_start = f_start / freq_step
            k_end = f_end / freq_step

            if k_end - k_start < 1.0:
                k_center = f_center / freq_step
                k_idx = int(k_center)
                frac = k_center - k_idx
                if k_idx >= num_mags - 1:
                    val_mag = float(mags[-1]) if num_mags > 0 else 0.0
                else:
                    val_mag = float(mags[k_idx] * (1.0 - frac) + mags[k_idx + 1] * frac)
            else:
                idx_start = max(0, int(math.floor(k_start)))
                idx_end = min(num_mags, int(math.ceil(k_end)))
                if idx_start >= idx_end:
                    idx_end = min(num_mags, idx_start + 1)

                band_slice = mags[idx_start:idx_end]
                if len(band_slice) > 0:
                    val_mag = float(0.5 * np.mean(band_slice) + 0.5 * np.max(band_slice))
                else:
                    val_mag = 0.0

            val = val_mag * spectral_boost * 4.0 * g
            bands[b] = min(1.0, val)

        return bands


class AudioEngine:
    """Caché y decodificador central en memoria para archivos de audio en PyxisNodes."""

    _audio_cache: Dict[str, AudioData] = {}

    @classmethod
    def load_wav(cls, file_path: str) -> AudioData:
        """Carga y decodifica un archivo PCM WAV directamente a memoria RAM con vectorización en C."""
        clean_path = os.path.abspath(file_path).lower()
        if clean_path in cls._audio_cache:
            return cls._audio_cache[clean_path]

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Archivo WAV no encontrado: {file_path}")

        with wave.open(file_path, "rb") as wf:
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_data = wf.readframes(n_frames)

        if sampwidth == 2:  # 16-bit signed PCM (estándar de alta fidelidad)
            arr = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32)
            if channels > 1:
                arr = arr.reshape(-1, channels).mean(axis=1)
            samples = arr / 32768.0

        elif sampwidth == 1:  # 8-bit unsigned PCM
            arr = np.frombuffer(raw_data, dtype=np.uint8).astype(np.float32)
            if channels > 1:
                arr = arr.reshape(-1, channels).mean(axis=1)
            samples = (arr - 128.0) / 128.0

        elif sampwidth == 3:  # 24-bit signed PCM
            raw_bytes = np.frombuffer(raw_data, dtype=np.uint8)
            a = raw_bytes.reshape(-1, 3)
            padded = np.zeros((len(a), 4), dtype=np.uint8)
            padded[:, 1:] = a
            ints = padded.view(dtype=np.int32)[:, 0] >> 8
            arr = ints.astype(np.float32)
            if channels > 1:
                arr = arr.reshape(-1, channels).mean(axis=1)
            samples = arr / 8388608.0

        elif sampwidth == 4:  # 32-bit float o 32-bit int
            try:
                arr = np.frombuffer(raw_data, dtype=np.float32)
                if channels > 1:
                    arr = arr.reshape(-1, channels).mean(axis=1)
                samples = arr.copy()
            except Exception:
                arr = np.frombuffer(raw_data, dtype=np.int32).astype(np.float32)
                if channels > 1:
                    arr = arr.reshape(-1, channels).mean(axis=1)
                samples = arr / 2147483648.0
        else:
            raise ValueError(f"Ancho de muestra WAV no soportado: {sampwidth} bytes")

        audio_obj = AudioData(framerate, channels, samples)
        cls._audio_cache[clean_path] = audio_obj
        return audio_obj

    @classmethod
    def clear_cache(cls):
        """Limpia la caché de audio en memoria."""
        cls._audio_cache.clear()
        try:
            from nodes.audio_nodes import clear_resolved_audio_cache
            clear_resolved_audio_cache()
        except Exception:
            pass

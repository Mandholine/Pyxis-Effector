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
"""Motor de análisis acústico, decodificación PCM WAV y cálculo FFT/RMS para PyxisNodes."""

import math
import os
import struct
import wave
from typing import Dict, List, Optional, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False


class AudioData:
    """Representa un búfer de audio PCM en memoria normalizado con utilidades de análisis."""

    def __init__(self, sample_rate: int, channels: int, samples: List[float]):
        self.sample_rate = sample_rate
        self.channels = channels
        self.samples = samples  # Lista o array 1D de floats en rango [-1.0, 1.0]
        self.num_samples = len(samples)
        self.duration_ms = (self.num_samples / float(sample_rate)) * 1000.0 if sample_rate > 0 else 0.0

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

    def get_chunk(self, start_ms: float, end_ms: float):
        """Extrae el segmento de audio entre start_ms y end_ms."""
        idx_start = self.sample_from_ms(start_ms)
        idx_end = self.sample_from_ms(end_ms)
        if idx_start >= self.num_samples:
            return [] if not (HAS_NUMPY and isinstance(self.samples, np.ndarray)) else np.array([], dtype=np.float32)
        if idx_start >= idx_end:
            idx_end = min(self.num_samples, idx_start + 1)
        return self.samples[idx_start:idx_end]

    def get_rms(self, start_ms: float, end_ms: float, gain: float = 1.0) -> float:
        """Calcula la energía acústica cuadrática media (RMS) entre 0.0 y 1.0 con ganancia."""
        chunk = self.get_chunk(start_ms, end_ms)
        if len(chunk) == 0:
            return 0.0

        if HAS_NUMPY and isinstance(chunk, np.ndarray):
            mean_sq = np.mean(chunk ** 2)
            raw_rms = float(np.sqrt(mean_sq))
        else:
            sum_sq = sum(s * s for s in chunk)
            raw_rms = math.sqrt(sum_sq / len(chunk))

        return min(1.0, raw_rms * max(0.0, float(gain)))

    def get_peak(self, start_ms: float, end_ms: float, gain: float = 1.0) -> float:
        """Calcula la amplitud pico absoluta máxima entre 0.0 y 1.0 con ganancia."""
        chunk = self.get_chunk(start_ms, end_ms)
        if len(chunk) == 0:
            return 0.0

        if HAS_NUMPY and isinstance(chunk, np.ndarray):
            p = float(np.max(np.abs(chunk)))
        else:
            p = max(abs(s) for s in chunk)

        return min(1.0, p * max(0.0, float(gain)))

    def get_samples(self, start_ms: float, end_ms: float, num_points: int = 32, gain: float = 1.0) -> List[float]:
        """Submuestrea el intervalo temporal en N puntos equidistantes para dibujo de formas con ganancia."""
        chunk = self.get_chunk(start_ms, end_ms)
        if len(chunk) == 0 or num_points <= 0:
            return [0.0] * num_points

        n = len(chunk)
        g = max(0.0, float(gain))
        if n == num_points:
            return [float(s) * g for s in chunk]

        result = []
        for i in range(num_points):
            pos = int(round((i / float(num_points - 1)) * (n - 1))) if num_points > 1 else 0
            pos = max(0, min(n - 1, pos))
            result.append(float(chunk[pos]) * g)
        return result

    def get_fft(self, start_ms: float, end_ms: float, n_fft: int = 2048) -> Tuple[List[float], float]:
        """Calcula la transformada de Fourier FFT y retorna (magnitudes, freq_step_hz)."""
        chunk = self.get_chunk(start_ms, end_ms)
        if len(chunk) == 0:
            return ([0.0] * (n_fft // 2), float(self.sample_rate) / n_fft if n_fft else 1.0)

        # Ajustar n_fft a potencia de 2 más cercana
        if n_fft < 16:
            n_fft = 16
        n_pow2 = 1 << (n_fft - 1).bit_length()
        if n_pow2 != n_fft:
            n_fft = n_pow2

        # Rellenar o recortar chunk con ventana de Hann
        chunk_len = len(chunk)
        samples_win = []
        for i in range(n_fft):
            if i < chunk_len:
                # Hann window: 0.5 * (1 - cos(2*pi*i / (N-1)))
                w = 0.5 * (1.0 - math.cos(2.0 * math.pi * i / (n_fft - 1)))
                samples_win.append(float(chunk[i]) * w)
            else:
                samples_win.append(0.0)

        freq_step = float(self.sample_rate) / float(n_fft)

        if HAS_NUMPY:
            fft_res = np.fft.rfft(samples_win)
            magnitudes = np.abs(fft_res)
            # Normalizar
            mag_sum = np.sum(magnitudes)
            if mag_sum > 0:
                magnitudes = magnitudes / (n_fft / 2.0)
            return (magnitudes.tolist(), freq_step)

        # FFT pura en Python (Radix-2 Cooley-Tukey)
        magnitudes = self._fft_pure_python(samples_win)
        num_mags = len(magnitudes) // 2
        half_mags = [magnitudes[i] / (n_fft / 2.0) for i in range(num_mags)]
        return (half_mags, freq_step)

    @staticmethod
    def _fft_pure_python(x: List[float]) -> List[float]:
        """Implementación nativa pura de FFT Cooley-Tukey recursiva/iterativa."""
        N = len(x)
        if N <= 1:
            return [abs(v) for v in x]

        # Convertir a complejos (r, i)
        complex_x = [(v, 0.0) for v in x]

        def _fft_rec(a):
            n = len(a)
            if n <= 1:
                return a
            even = _fft_rec(a[0::2])
            odd = _fft_rec(a[1::2])
            combined = [(0.0, 0.0)] * n
            for k in range(n // 2):
                angle = -2.0 * math.pi * k / n
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                # odd[k] * exp(angle)
                odd_r, odd_i = odd[k]
                t_r = odd_r * cos_a - odd_i * sin_a
                t_i = odd_r * sin_a + odd_i * cos_a
                
                even_r, even_i = even[k]
                combined[k] = (even_r + t_r, even_i + t_i)
                combined[k + n // 2] = (even_r - t_r, even_i - t_i)
            return combined

        res_complex = _fft_rec(complex_x)
        return [math.sqrt(r * r + i * i) for r, i in res_complex]

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
                combined_energy = mags[-1] if num_mags > 0 else 0.0
            else:
                combined_energy = mags[k_idx] * (1.0 - frac) + mags[k_idx + 1] * frac
        else:
            idx_start = max(0, int(math.floor(k_start)))
            idx_end = min(num_mags, int(math.ceil(k_end)))
            band_energy = 0.0
            max_mag = 0.0
            bin_count = 0
            for i in range(idx_start, idx_end):
                mag = mags[i]
                band_energy += mag
                if mag > max_mag:
                    max_mag = mag
                bin_count += 1

            if bin_count == 0:
                return 0.0

            avg_mag = band_energy / bin_count
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
        """Divide el espectro en N bandas de frecuencia con escala logarítmica, interpolación continua y compensación espectral."""
        if num_bands <= 0:
            return []

        mags, freq_step = self.get_fft(start_ms, end_ms, n_fft=2048)
        num_mags = len(mags)
        if num_mags == 0 or freq_step <= 0:
            return [0.0] * num_bands

        bands = [0.0] * num_bands
        log_min = math.log10(max(10.0, min_hz))
        log_max = math.log10(max(min_hz + 10.0, max_hz))

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
                    val_mag = mags[-1] if num_mags > 0 else 0.0
                else:
                    val_mag = mags[k_idx] * (1.0 - frac) + mags[k_idx + 1] * frac
            else:
                idx_start = max(0, int(math.floor(k_start)))
                idx_end = min(num_mags, int(math.ceil(k_end)))
                b_energy = 0.0
                b_max = 0.0
                b_bins = 0
                for i in range(idx_start, idx_end):
                    mag = mags[i]
                    b_energy += mag
                    if mag > b_max:
                        b_max = mag
                    b_bins += 1

                if b_bins > 0:
                    avg_b = b_energy / b_bins
                    val_mag = 0.5 * avg_b + 0.5 * b_max
                else:
                    val_mag = 0.0

            val = val_mag * spectral_boost * 4.0 * max(0.0, float(gain))
            bands[b] = min(1.0, val)

        return bands


class AudioEngine:
    """Caché y decodificador central en memoria para archivos de audio en PyxisNodes."""

    _audio_cache: Dict[str, AudioData] = {}

    @classmethod
    def load_wav(cls, file_path: str) -> AudioData:
        """Carga y decodifica un archivo PCM WAV a memoria. Reutiliza caché si ya está cargado."""
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

        samples: List[float] = []

        if sampwidth == 2:  # 16-bit signed PCM
            total_samples = n_frames * channels
            fmt = f"<{total_samples}h"
            ints = struct.unpack(fmt, raw_data)
            if channels == 1:
                samples = [s / 32768.0 for s in ints]
            else:
                # Promedio de canales a mono
                samples = [
                    ((ints[i * channels] + ints[i * channels + 1]) / 2.0) / 32768.0
                    for i in range(n_frames)
                ]

        elif sampwidth == 1:  # 8-bit unsigned PCM
            total_samples = n_frames * channels
            fmt = f"<{total_samples}B"
            ints = struct.unpack(fmt, raw_data)
            if channels == 1:
                samples = [(s - 128) / 128.0 for s in ints]
            else:
                samples = [
                    (((ints[i * channels] + ints[i * channels + 1]) / 2.0) - 128) / 128.0
                    for i in range(n_frames)
                ]

        elif sampwidth == 3:  # 24-bit signed PCM
            # 3 bytes por muestra
            total_samples = n_frames * channels
            ints = []
            for i in range(total_samples):
                b = raw_data[i * 3:(i + 1) * 3]
                # Pad to 4 bytes signed int
                val = int.from_bytes(b, byteorder="little", signed=True)
                ints.append(val)
            max_24 = 8388608.0
            if channels == 1:
                samples = [s / max_24 for s in ints]
            else:
                samples = [
                    ((ints[i * channels] + ints[i * channels + 1]) / 2.0) / max_24
                    for i in range(n_frames)
                ]

        elif sampwidth == 4:  # 32-bit float o 32-bit signed int
            total_samples = n_frames * channels
            try:
                # Intentar primero float de 32 bits
                fmt = f"<{total_samples}f"
                floats = struct.unpack(fmt, raw_data)
                if channels == 1:
                    samples = list(floats)
                else:
                    samples = [
                        (floats[i * channels] + floats[i * channels + 1]) / 2.0
                        for i in range(n_frames)
                    ]
            except Exception:
                fmt = f"<{total_samples}i"
                ints = struct.unpack(fmt, raw_data)
                max_32 = 2147483648.0
                if channels == 1:
                    samples = [s / max_32 for s in ints]
                else:
                    samples = [
                        ((ints[i * channels] + ints[i * channels + 1]) / 2.0) / max_32
                        for i in range(n_frames)
                    ]
        else:
            raise ValueError(f"Ancho de muestra WAV no soportado: {sampwidth} bytes")

        if HAS_NUMPY and np is not None:
            samples_arr = np.array(samples, dtype=np.float32)
            audio_obj = AudioData(framerate, channels, samples_arr)
        else:
            audio_obj = AudioData(framerate, channels, samples)

        cls._audio_cache[clean_path] = audio_obj
        return audio_obj

    @classmethod
    def clear_cache(cls):
        """Limpia la caché de audio en memoria."""
        cls._audio_cache.clear()

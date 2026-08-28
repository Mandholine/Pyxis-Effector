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

# PyxisNodes/audio_preprocessor.py
"""Módulo de preprocesamiento, extracción y caché de audio universal mediante FFmpeg."""

import hashlib
import os
import shutil
import subprocess
from typing import Optional


class AudioPreprocessor:
    """Gestiona la detección, conversión a PCM WAV y caché inteligente de archivos de audio/video."""

    @staticmethod
    def get_ffmpeg_path() -> Optional[str]:
        """Localiza el ejecutable de ffmpeg en PyxisNodes o en el PATH del sistema."""
        # 1. Directorio local de PyxisNodes
        local_dir = os.path.dirname(os.path.abspath(__file__))
        local_ffmpeg = os.path.join(local_dir, "ffmpeg.exe")
        if os.path.isfile(local_ffmpeg):
            return local_ffmpeg

        # 2. Directorio de usuario en %APPDATA%/PyxisNodes
        appdata_dir = os.environ.get("APPDATA")
        if appdata_dir:
            user_ffmpeg = os.path.join(appdata_dir, "PyxisNodes", "ffmpeg.exe")
            if os.path.isfile(user_ffmpeg):
                return user_ffmpeg

        # 3. PATH del sistema operativo
        sys_ffmpeg = shutil.which("ffmpeg")
        if sys_ffmpeg:
            return sys_ffmpeg

        return None

    @staticmethod
    def get_cache_dir() -> str:
        """Obtiene y asegura el directorio temporal de caché de audio."""
        appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
        cache_dir = os.path.join(appdata_dir, "PyxisNodes", "temp", "audio_cache")
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    @staticmethod
    def is_pcm_wav(file_path: str) -> bool:
        """Verifica rápidamente si el archivo ya es un WAV RIFF válido sin necesidad de conversión."""
        if not file_path or not os.path.isfile(file_path):
            return False
        try:
            with open(file_path, "rb") as f:
                header = f.read(12)
                if len(header) >= 12 and header[0:4] == b"RIFF" and header[8:12] == b"WAVE":
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def compute_cache_key(source_path: str, stream_idx: int = 0) -> str:
        """Calcula una huella digital única (MD5) para el archivo de origen."""
        abs_path = os.path.abspath(source_path).lower()
        file_size = 0
        file_mtime = 0.0
        try:
            stat = os.stat(source_path)
            file_size = stat.st_size
            file_mtime = stat.st_mtime
        except Exception:
            pass

        key_data = f"{abs_path}_{file_size}_{file_mtime}_{stream_idx}".encode("utf-8")
        return hashlib.md5(key_data).hexdigest()[:16]

    @classmethod
    def ensure_audio_wav(
        cls,
        source_path: str,
        stream_idx: int = 0,
        target_sample_rate: int = 44100,
        progress_callback=None
    ) -> str:
        """Asegura que el archivo de entrada esté disponible como un archivo PCM WAV compatible.
        
        Si el archivo ya es un WAV válido, retorna la ruta original.
        Si es un contenedor (.mp4, .mkv) o formato comprimido (.mp3, .aac, .flac, .opus, .eac3),
        lo extrae y convierte usando FFmpeg guardándolo en caché.
        """
        if not source_path or not str(source_path).strip():
            raise ValueError("Ruta de audio no especificada.")

        clean_path = str(source_path).strip().strip('"').strip("'")
        if not os.path.isfile(clean_path):
            raise FileNotFoundError(f"Archivo de audio/video no encontrado: {clean_path}")

        # Si ya es un archivo WAV válido en disco, lo usamos directamente
        if cls.is_pcm_wav(clean_path):
            return clean_path

        # Comprobar caché inteligente
        cache_key = cls.compute_cache_key(clean_path, stream_idx)
        cached_wav = os.path.join(cls.get_cache_dir(), f"pyxis_audio_{cache_key}.wav")

        # Cache HIT: el archivo ya fue convertido y el original no ha cambiado
        if os.path.isfile(cached_wav) and os.path.getsize(cached_wav) > 44:
            return cached_wav

        # Cache MISS: requiere conversión con FFmpeg
        ffmpeg_bin = cls.get_ffmpeg_path()
        if not ffmpeg_bin:
            raise FileNotFoundError(
                "No se encontró 'ffmpeg.exe'. Coloque 'ffmpeg.exe' en la carpeta de PyxisNodes o agréguelo al PATH."
            )

        if progress_callback:
            try:
                progress_callback("Extrayendo y convirtiendo pista de audio con FFmpeg...")
            except Exception:
                pass

        temp_target = cached_wav + f".tmp_{os.getpid()}.wav"
        cmd = [
            ffmpeg_bin,
            "-y",
            "-v", "error",
            "-i", clean_path,
            "-vn",
            "-sn",
            "-dn",
            "-map", f"0:a:{stream_idx}?",
            "-acodec", "pcm_s16le",
            "-ar", str(target_sample_rate),
            "-ac", "2",
            temp_target
        ]

        try:
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0x08000000

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags,
                check=False
            )

            if result.returncode != 0:
                err_msg = result.stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(f"FFmpeg falló al procesar el audio (código {result.returncode}): {err_msg}")

            if not os.path.isfile(temp_target) or os.path.getsize(temp_target) <= 44:
                raise RuntimeError("FFmpeg no generó un archivo WAV válido o la pista de audio está vacía.")

            os.replace(temp_target, cached_wav)
            return cached_wav

        except Exception:
            if os.path.isfile(temp_target):
                try:
                    os.remove(temp_target)
                except OSError:
                    pass
            raise

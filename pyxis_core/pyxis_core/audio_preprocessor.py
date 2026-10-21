# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc and Pyxis Effector contributors
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

"""Universal audio preprocessing, extraction, and caching module via FFmpeg."""

import hashlib
import os
import shutil
import subprocess
from typing import Optional


class AudioPreprocessor:
    """Manages detection, conversion to PCM WAV, and smart caching of audio/video files."""

    @staticmethod
    def get_ffmpeg_path() -> Optional[str]:
        """Locates ffmpeg executable in PyxisNodes or system PATH."""
        exe_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        try:
            from paths import get_bin_path
            target = get_bin_path("ffmpeg")
            if os.path.isfile(target):
                return target
        except Exception:
            pass

        local_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(local_dir, "bin", exe_name),
            os.path.join(local_dir, "..", "bin", exe_name),
            os.path.join(local_dir, exe_name),
            os.path.join(local_dir, "..", exe_name),
        ]
        for cand in candidates:
            if os.path.isfile(cand):
                return cand

        try:
            from paths import get_user_data_dir
            user_ffmpeg = os.path.join(get_user_data_dir(), exe_name)
        except Exception:
            appdata_dir = os.environ.get("APPDATA")
            user_ffmpeg = os.path.join(appdata_dir, "PyxisNodes", exe_name) if appdata_dir else None
        if user_ffmpeg and os.path.isfile(user_ffmpeg):
            return user_ffmpeg

        sys_ffmpeg = shutil.which("ffmpeg")
        if sys_ffmpeg:
            return sys_ffmpeg

        return None

    @staticmethod
    def get_cache_dir() -> str:
        """Gets and ensures temporary audio cache directory."""
        try:
            from paths import get_user_data_dir
            base_dir = get_user_data_dir()
        except Exception:
            appdata_dir = os.environ.get("APPDATA") or os.path.expanduser("~")
            base_dir = os.path.join(appdata_dir, "PyxisNodes")
        cache_dir = os.path.join(base_dir, "temp", "audio_cache")
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    @staticmethod
    def is_pcm_wav(file_path: str) -> bool:
        """Quickly checks if file is already a valid RIFF WAV without conversion."""
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
        """Computes a unique digital fingerprint (MD5) for the source file."""
        abs_path = os.path.abspath(source_path)
        if os.name == "nt":
            abs_path = abs_path.lower()
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
        """Ensures input file is available as a compatible PCM WAV file."""
        if not source_path or not str(source_path).strip():
            raise ValueError("Audio path not specified.")

        clean_path = str(source_path).strip().strip('"').strip("'")
        if not os.path.isfile(clean_path):
            raise FileNotFoundError(f"Audio/video file not found: {clean_path}")

        if cls.is_pcm_wav(clean_path):
            return clean_path

        cache_key = cls.compute_cache_key(clean_path, stream_idx)
        cached_wav = os.path.join(cls.get_cache_dir(), f"pyxis_audio_{cache_key}.wav")

        if os.path.isfile(cached_wav) and os.path.getsize(cached_wav) > 44:
            return cached_wav

        ffmpeg_bin = cls.get_ffmpeg_path()
        if not ffmpeg_bin:
            raise FileNotFoundError("Could not find 'ffmpeg'. Please install ffmpeg (e.g. 'sudo apt install ffmpeg' / 'sudo pacman -S ffmpeg') or place the binary in the PyxisNodes folder or add it to PATH.")

        if progress_callback:
            try:
                progress_callback("Extracting and converting audio track with FFmpeg...")
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
                raise RuntimeError("FFmpeg did not generate a valid WAV file or audio track is empty.")

            os.replace(temp_target, cached_wav)
            return cached_wav

        except Exception:
            if os.path.isfile(temp_target):
                try:
                    os.remove(temp_target)
                except OSError:
                    pass
            raise

# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Adapters (Audio Adapter)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from typing import Callable, Optional
from ..engine.audio import AudioEngine, AudioPreprocessor


class AudioAdapter:
    """Adapter bridging audio preprocessing and waveform extraction."""

    @staticmethod
    def prepare_wav(
        source_path: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Converts or extracts audio to WAV format."""
        return AudioPreprocessor.ensure_audio_wav(
            source_path,
            progress_callback=progress_callback,
        )

    @staticmethod
    def load_wav(wav_path: str) -> None:
        """Loads audio waveform data into memory for audio-reactive nodes."""
        AudioEngine.load_wav(wav_path)

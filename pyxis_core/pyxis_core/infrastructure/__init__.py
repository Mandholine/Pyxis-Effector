# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Layer
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

"""Capa de Infraestructura de Pyxis Effector.

Implementa los repositorios (archivos ASS, plantillas JSON),
adaptadores multimedia (FFmpeg, FreeType) y motores pesados de cálculo.
"""

from .repositories import FileSubtitleRepository, FileTemplateRepository
from .adapters import AudioAdapter, FontAdapter, TelemetryAdapter

__all__ = [
    "FileSubtitleRepository",
    "FileTemplateRepository",
    "AudioAdapter",
    "FontAdapter",
    "TelemetryAdapter",
]

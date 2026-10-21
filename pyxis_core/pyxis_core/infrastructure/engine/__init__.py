# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Engine
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

import os
import sys

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
_SUBDIRS = [
    _ENGINE_DIR,
    os.path.join(_ENGINE_DIR, "graph"),
    os.path.join(_ENGINE_DIR, "audio"),
    os.path.join(_ENGINE_DIR, "font"),
    os.path.join(_ENGINE_DIR, "geometry"),
    os.path.join(_ENGINE_DIR, "subtitles"),
    os.path.join(_ENGINE_DIR, "system"),
    os.path.join(_ENGINE_DIR, "telemetry"),
]

for d in _SUBDIRS:
    if d not in sys.path:
        sys.path.insert(0, d)

from .graph import GraphEngine, NodeValidator, NODE_REGISTRY, abort_global_multiprocessing
from .subtitles import ASSParser, KaraokeProcessor
from .audio import AudioEngine, AudioPreprocessor
from .font import FontEngine, FontResolver, FontVectorEngine
from .geometry import trace_image, _get_potrace_exe_path
from .telemetry import ASSTelemetryManager, GLOBAL_TELEMETRY_MANAGER
from .system import (
    BIN_DIR,
    TEMPLATES_DIR,
    PREVIEW_BASE_ASS,
    get_bin_path,
    get_user_data_dir,
    PyxisLine,
    PyxisUnit,
)

__all__ = [
    # Graph & Nodes
    "GraphEngine",
    "NodeValidator",
    "NODE_REGISTRY",
    "abort_global_multiprocessing",
    # Subtitles
    "ASSParser",
    "KaraokeProcessor",
    # Audio
    "AudioEngine",
    "AudioPreprocessor",
    # Font
    "FontEngine",
    "FontResolver",
    "FontVectorEngine",
    # Geometry
    "trace_image",
    "_get_potrace_exe_path",
    # Telemetry
    "ASSTelemetryManager",
    "GLOBAL_TELEMETRY_MANAGER",
    # System
    "BIN_DIR",
    "TEMPLATES_DIR",
    "PREVIEW_BASE_ASS",
    "get_bin_path",
    "get_user_data_dir",
    "PyxisLine",
    "PyxisUnit",
]

# -*- coding: utf-8 -*-
# Pyxis Effector — Core Subtitle & Node Engine Library
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

"""pyxis_core — Motor y biblioteca pura de efectos y nodos para subtítulos ASS.

Desacoplada de interfaces de usuario (pywebview, Qt) para ser consumida
por scripts CLI, servidores backend (FastAPI) o plugins.
"""

import os
import sys

# Ensure this package directory is on sys.path so existing flat imports
# (e.g. `from node_engine import ...`) resolve cleanly.
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
if _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)

__version__ = "1.1.4"

# High-level pipeline runner
from .pipeline import PyxisPipeline, ProcessingResult

# Core processing engines
from .ass_parser import ASSParser, KaraokeProcessor
from .node_engine import GraphEngine, NODE_REGISTRY, abort_global_multiprocessing
from .node_validator import NodeValidator
from .ass_telemetry_engine import ASSTelemetryEngine

# Media & styling engines
from .audio_engine import AudioEngine
from .audio_preprocessor import AudioPreprocessor
from .font_engine import FontEngine
from .font_vector_engine import FontVectorEngine
from .font_resolver import FontResolver
from .clipper_engine import ClipperEngine

# Templates and storage
from .template_store import TemplateStore

__all__ = [
    "__version__",
    "PyxisPipeline",
    "ProcessingResult",
    "GraphEngine",
    "NODE_REGISTRY",
    "abort_global_multiprocessing",
    "ASSParser",
    "KaraokeProcessor",
    "ASSTelemetryEngine",
    "AudioEngine",
    "AudioPreprocessor",
    "FontEngine",
    "FontVectorEngine",
    "FontResolver",
    "ClipperEngine",
    "NodeValidator",
    "TemplateStore",
]

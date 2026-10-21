# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Engine
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

import os
import sys

_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)

from .node_engine import GraphEngine, NODE_REGISTRY, abort_global_multiprocessing
from .ass_parser import ASSParser, KaraokeProcessor
from .node_validator import NodeValidator
from .paths import get_user_data_dir, TEMPLATES_DIR, PREVIEW_BASE_ASS

__all__ = [
    "GraphEngine",
    "NODE_REGISTRY",
    "abort_global_multiprocessing",
    "ASSParser",
    "KaraokeProcessor",
    "NodeValidator",
    "get_user_data_dir",
    "TEMPLATES_DIR",
    "PREVIEW_BASE_ASS",
]

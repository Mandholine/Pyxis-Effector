# -*- coding: utf-8 -*-
# Pyxis Effector — Domain Layer
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

"""Dominio puro de Pyxis Effector.

Contiene entidades de negocio, objetos de valor e interfaces de repositorio,
completamente aisladas de frameworks, bases de datos o sistemas de archivos.
"""

from .entities import (
    SubtitleScript,
    DialogueLine,
    SubtitleStyle,
    NodeGraph,
    NodeItem,
    NodeConnection,
    EffectTemplate,
)
from .value_objects import Resolution, Timecode
from .repositories import ISubtitleRepository, ITemplateRepository

__all__ = [
    "SubtitleScript",
    "DialogueLine",
    "SubtitleStyle",
    "NodeGraph",
    "NodeItem",
    "NodeConnection",
    "EffectTemplate",
    "Resolution",
    "Timecode",
    "ISubtitleRepository",
    "ITemplateRepository",
]

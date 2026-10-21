# -*- coding: utf-8 -*-
# Pyxis Effector — Core Subtitle & Node Engine Library
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

"""pyxis_core — Clean Architecture Core Library for Subtitle Effects & Node Engine.

Capas:
- domain: Entidades puras (SubtitleScript, DialogueLine, NodeGraph), Objetos de Valor e Interfaces.
- application: Casos de Uso (ProcessGraphUseCase, ValidateGraphUseCase), DTOs y Mappers.
- infrastructure: Repositorios concretos (FileSubtitleRepository), Adaptadores y Motores de cálculo.
"""

import os
import sys

# Ensure package and engine directories are in sys.path for backward compatibility
_ROOT_PKG = os.path.dirname(os.path.abspath(__file__))
_ENGINE_DIR = os.path.join(_ROOT_PKG, "infrastructure", "engine")
for _p in (_ROOT_PKG, _ENGINE_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

__version__ = "0.1.0"

# 1. Domain Layer Exports
from .domain import (
    SubtitleScript,
    DialogueLine,
    SubtitleStyle,
    NodeGraph,
    NodeItem,
    NodeConnection,
    EffectTemplate,
    Resolution,
    Timecode,
    ISubtitleRepository,
    ITemplateRepository,
)

# 2. Application Layer Exports (DTOs, Mappers & Use Cases)
from .application import (
    ProgressEventDTO,
    ProcessGraphRequestDTO,
    ProcessGraphResponseDTO,
    ValidateGraphRequestDTO,
    ValidationResultDTO,
    TemplateDTO,
    TemplateListDTO,
    SubtitleMapper,
    GraphMapper,
    ProcessGraphUseCase,
    ValidateGraphUseCase,
    ManageTemplatesUseCase,
)

# 3. Infrastructure Layer Exports
from .infrastructure import (
    FileSubtitleRepository,
    FileTemplateRepository,
    AudioAdapter,
    FontAdapter,
    TelemetryAdapter,
)


class PyxisCore:
    """Facade / Service Container providing ready-to-use Clean Architecture use cases."""

    def __init__(
        self,
        subtitle_repo: ISubtitleRepository = None,
        template_repo: ITemplateRepository = None,
    ):
        self.subtitle_repo = subtitle_repo or FileSubtitleRepository()
        self.template_repo = template_repo or FileTemplateRepository()

        # Initialize Use Cases
        self.process_graph_use_case = ProcessGraphUseCase(self.subtitle_repo)
        self.validate_graph_use_case = ValidateGraphUseCase()
        self.templates_use_case = ManageTemplatesUseCase(self.template_repo)

    def process(
        self,
        graph,
        ass_path: str = None,
        ass_content: str = None,
        output_path: str = None,
        progress_callback=None,
        cancel_checker=None,
        default_audio_source: str = None,
    ) -> ProcessGraphResponseDTO:
        """Executes ProcessGraphUseCase with the given parameters."""
        req = ProcessGraphRequestDTO(
            graph=graph,
            ass_path=ass_path,
            ass_content=ass_content,
            output_path=output_path,
            default_audio_source=default_audio_source,
        )
        return self.process_graph_use_case.execute(
            req,
            progress_callback=progress_callback,
            cancel_checker=cancel_checker,
        )

    def validate(self, graph) -> ValidationResultDTO:
        """Executes ValidateGraphUseCase."""
        req = ValidateGraphRequestDTO(graph=graph)
        return self.validate_graph_use_case.execute(req)


__all__ = [
    "__version__",
    "PyxisCore",
    # Domain
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
    # Application
    "ProgressEventDTO",
    "ProcessGraphRequestDTO",
    "ProcessGraphResponseDTO",
    "ValidateGraphRequestDTO",
    "ValidationResultDTO",
    "TemplateDTO",
    "TemplateListDTO",
    "SubtitleMapper",
    "GraphMapper",
    "ProcessGraphUseCase",
    "ValidateGraphUseCase",
    "ManageTemplatesUseCase",
    # Infrastructure
    "FileSubtitleRepository",
    "FileTemplateRepository",
    "AudioAdapter",
    "FontAdapter",
    "TelemetryAdapter",
]

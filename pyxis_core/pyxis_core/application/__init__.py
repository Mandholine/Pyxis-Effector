# -*- coding: utf-8 -*-
# Pyxis Effector — Application Layer
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

"""Capa de Aplicación de Pyxis Effector.

Contiene los Casos de Uso (Interactors), DTOs (Serializers/Schemas)
y Mappers que transforman datos entre el mundo exterior (APIs, CLI) y el Dominio.
"""

from .dtos import (
    ProgressEventDTO,
    ProcessGraphRequestDTO,
    ProcessGraphResponseDTO,
    ValidateGraphRequestDTO,
    ValidationResultDTO,
    TemplateDTO,
    TemplateListDTO,
)
from .mappers import SubtitleMapper, GraphMapper
from .use_cases import (
    ProcessGraphUseCase,
    ValidateGraphUseCase,
    ManageTemplatesUseCase,
)

__all__ = [
    # DTOs
    "ProgressEventDTO",
    "ProcessGraphRequestDTO",
    "ProcessGraphResponseDTO",
    "ValidateGraphRequestDTO",
    "ValidationResultDTO",
    "TemplateDTO",
    "TemplateListDTO",
    # Mappers
    "SubtitleMapper",
    "GraphMapper",
    # Use cases
    "ProcessGraphUseCase",
    "ValidateGraphUseCase",
    "ManageTemplatesUseCase",
]

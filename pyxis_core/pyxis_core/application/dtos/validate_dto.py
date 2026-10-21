# -*- coding: utf-8 -*-
# Pyxis Effector — Application DTOs
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from dataclasses import dataclass, field
from typing import Any, Dict, List, Union


@dataclass
class ValidateGraphRequestDTO:
    """Request DTO to validate node graph syntax and connections."""

    graph: Union[Dict[str, Any], str]


@dataclass
class ValidationResultDTO:
    """Response DTO with validation errors and warnings."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
        }

# -*- coding: utf-8 -*-
# Pyxis Effector — Application DTOs
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class ProgressEventDTO:
    """DTO emitted during node processing to notify progress."""

    percent: int
    phase: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "percent": self.percent,
            "phase": self.phase,
            "details": self.details or {},
        }


@dataclass
class ProcessGraphRequestDTO:
    """Request DTO to initiate effect generation on a subtitle script."""

    graph: Union[Dict[str, Any], str]
    ass_path: Optional[str] = None
    ass_content: Optional[str] = None
    output_path: Optional[str] = None
    default_audio_source: Optional[str] = None


@dataclass
class ProcessGraphResponseDTO:
    """Response DTO returned after effect processing finishes."""

    success: bool
    lines_count: int = 0
    duration_seconds: float = 0.0
    lines: List[str] = field(default_factory=list)
    used_indices: List[int] = field(default_factory=list)
    cancelled: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "lines_count": self.lines_count,
            "duration_seconds": round(self.duration_seconds, 3),
            "used_indices": self.used_indices,
            "cancelled": self.cancelled,
            "error": self.error,
        }

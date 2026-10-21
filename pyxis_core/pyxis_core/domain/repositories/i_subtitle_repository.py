# -*- coding: utf-8 -*-
# Pyxis Effector — Domain Repository Interfaces
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.subtitle import SubtitleScript


class ISubtitleRepository(ABC):
    """Port interface for loading and storing subtitle scripts."""

    @abstractmethod
    def read_from_file(self, file_path: str) -> SubtitleScript:
        """Parses an ASS file from disk into a SubtitleScript entity."""
        pass

    @abstractmethod
    def read_from_text(self, text_content: str) -> SubtitleScript:
        """Parses raw ASS text content into a SubtitleScript entity."""
        pass

    @abstractmethod
    def write_to_file(
        self,
        file_path: str,
        generated_lines: List[str],
        used_indices: Optional[List[int]] = None,
    ) -> None:
        """Persists generated lines and telemetry indices to disk."""
        pass

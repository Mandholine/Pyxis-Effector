# -*- coding: utf-8 -*-
# Pyxis Effector — Domain Repository Interfaces
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.template import EffectTemplate


class ITemplateRepository(ABC):
    """Port interface for managing effect templates and presets."""

    @abstractmethod
    def list_templates(self) -> List[EffectTemplate]:
        """Returns all available effect templates."""
        pass

    @abstractmethod
    def get_template(self, identifier: str) -> Optional[EffectTemplate]:
        """Finds a template by its name or ID."""
        pass

    @abstractmethod
    def save_template(self, template: EffectTemplate) -> str:
        """Saves or updates a template, returning its ID."""
        pass

    @abstractmethod
    def delete_template(self, identifier: str) -> bool:
        """Removes a template by ID or name."""
        pass

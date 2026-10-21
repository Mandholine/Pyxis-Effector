# -*- coding: utf-8 -*-
# Pyxis Effector — Application DTOs
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TemplateDTO:
    """DTO representing an effect template."""

    id: str
    name: str
    comment: str = ""
    author: str = ""
    category: str = "General"
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "comment": self.comment,
            "author": self.author,
            "category": self.category,
            "payload": self.payload,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class TemplateListDTO:
    """DTO for template catalog listing."""

    templates: List[TemplateDTO] = field(default_factory=list)
    total: int = 0

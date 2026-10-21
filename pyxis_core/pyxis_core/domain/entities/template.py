# -*- coding: utf-8 -*-
# Pyxis Effector — Domain Entities (Templates)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from .graph import NodeGraph


@dataclass
class EffectTemplate:
    """Domain model for a saved effect template."""

    id: str
    name: str
    comment: str = ""
    author: str = ""
    category: str = "General"
    graph: Optional[NodeGraph] = None
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

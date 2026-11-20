# -*- coding: utf-8 -*-
"""Puerto de dominio: libreria de efectos de Kara Effector 3.6."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.fx_template import FxTemplate


class IFxLibraryRepository(ABC):
    """Lista, busca, guarda y elimina efectos de la libreria."""

    @abstractmethod
    def all(self) -> List[FxTemplate]:
        """Todos los efectos (los incluidos y los del usuario)."""

    @abstractmethod
    def by_kind(self, kind: str) -> List[FxTemplate]:
        """Efectos de un tipo (LIfx, HLfx, LOfx, SHfx, TLfx, FTfx), en orden."""

    @abstractmethod
    def get(self, name: str, kind: Optional[str] = None) -> Optional[FxTemplate]:
        """Busca por nombre exacto (o legible); `kind` desambigua si el nombre existe en varios tipos."""

    @abstractmethod
    def search(self, text: str = "", kind: Optional[str] = None, limit: Optional[int] = None) -> List[FxTemplate]:
        """Efectos cuyo nombre contiene `text` (sin distinguir mayusculas), opcionalmente de un tipo."""

    @abstractmethod
    def add(self, fx: FxTemplate) -> FxTemplate:
        """Guarda un efecto del usuario (si ya existe uno con ese nombre, lo reemplaza)."""

    @abstractmethod
    def remove(self, name: str, kind: Optional[str] = None) -> bool:
        """Elimina un efecto del usuario; los incluidos no se pueden eliminar. True si se elimino."""

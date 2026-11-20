# -*- coding: utf-8 -*-
"""Puerto de dominio: operaciones booleanas entre formas vectoriales (port de ke.shape.clipper.boolean)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

OPERATIONS = ("intersection", "union", "difference", "xor")
FILL_TYPES = ("evenodd", "nonzero", "positive", "negative")


class IShapeBooleanEngine(ABC):
    """Interfaz que implementa la infraestructura (p. ej. con pyclipper)."""

    @abstractmethod
    def boolean(self, subject: Any, clip: Any, operation: str = "union", filltype: str = "evenodd") -> Any:
        """Combina dos formas (`Shape` o codigo ASS) y devuelve una `Shape`.

        operation: intersection | union | difference | xor. filltype: evenodd | nonzero | positive | negative."""

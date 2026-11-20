# -*- coding: utf-8 -*-
# Formato de `effector.create_fx` de Kara Effector 3.6 legacy (c) 2012-2020 Vict8r, Karalaura, NatsuoKE & Itachi Akatsuki.

"""Entidad de la libreria de efectos de Kara Effector 3.6: un efecto = una llamada `effector.create_fx(...)`."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, List, Optional, Sequence, Tuple, Union

# Tipos de efecto (primer argumento de create_fx) y su significado.
FX_KINDS: Tuple[str, ...] = ("LIfx", "HLfx", "LOfx", "SHfx", "TLfx", "FTfx")
FX_KIND_NAMES = {
    "LIfx": "lead-in", "HLfx": "hi-light", "LOfx": "lead-out",
    "SHfx": "shape", "TLfx": "translation", "FTfx": "function",
}

Value = Union[str, int, float, bool, None]


@dataclass(frozen=True)
class FxTemplate:
    """Un efecto de Kara Effector 3.6. Los campos son expresiones del lenguaje de plantillas (cadenas) y se
    conservan tal cual; el orden de `to_sequence()` es el de los argumentos de `effector.create_fx`:

    kind, name, template, noblank, vertical, color1, color3, color4, alpha1, alpha3, alpha4, start, end,
    func_x, func_y, domain_i, domain_f, center_x, center_y, scale_x, scale_y, align, layer, pos_x, pos_y,
    time_move, loop, size, return_, add_tags, variables, language, modify, reverse, keeptags.
    """

    kind: str                      # LIfx | HLfx | LOfx | SHfx | TLfx | FTfx
    name: str
    template: str = "Syl"          # Syl | Word | Char | Line | "Translation Char"...
    noblank: Value = True
    vertical: Value = False
    color1: str = "#FFFFFF"        # colores/alfas de la forma (efectos shape)
    color3: str = "#848484"
    color4: str = "#454545"
    alpha1: Value = "0"
    alpha3: Value = "0"
    alpha4: Value = "0"
    start: str = "l.start_time"    # tiempo inicial de la linea de efecto
    end: str = "l.end_time"        # tiempo final
    func_x: str = ""               # funcion en x/y y dominio (formas parametricas)
    func_y: str = ""
    domain_i: str = ""
    domain_f: str = ""
    center_x: str = ""
    center_y: str = ""
    scale_x: str = ""
    scale_y: str = ""
    align: Value = "5"
    layer: Value = "0"
    pos_x: str = "fx.pos_x"
    pos_y: str = "fx.pos_y"
    time_move: str = ""
    loop: Value = "1"
    size: str = ""
    return_: str = "syl.text"      # texto o forma que devuelve
    add_tags: str = ""
    variables: str = ""
    language: str = "Lua"
    modify: Value = False          # "return or modify"
    reverse: Value = False
    keeptags: Value = None

    @classmethod
    def from_sequence(cls, values: Sequence[Any]) -> "FxTemplate":
        """Crea el efecto desde los argumentos posicionales de `create_fx` (lo que falte toma su defecto)."""
        names = [f.name for f in fields(cls)]
        if len(values) < 2:
            raise ValueError("un efecto necesita al menos tipo y nombre")
        data = dict(zip(names, values))
        data["name"] = str(data["name"])
        return cls(**data)

    def to_sequence(self) -> List[Any]:
        return [getattr(self, f.name) for f in fields(self)]

    @property
    def display_name(self) -> str:
        """Nombre legible ("Animated_Clip_VI" -> "Animated Clip VI")."""
        return self.name.replace("_", " ")

    @property
    def kind_name(self) -> str:
        return FX_KIND_NAMES.get(self.kind, self.kind)

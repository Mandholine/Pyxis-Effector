# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GraphBody(BaseModel):
    graph: Dict[str, Any]


class ProcessBody(BaseModel):
    graph: Dict[str, Any]
    ass_path: Optional[str] = None
    ass_content: Optional[str] = None
    output_path: Optional[str] = None
    default_audio_source: Optional[str] = None
    include_lines: bool = Field(False, description="Devolver tambien las lineas generadas")
    style: Optional[str] = Field(None, description="Procesar solo las lineas de este estilo")


class TemplateBody(BaseModel):
    id: Optional[str] = None
    name: str
    comment: str = ""
    author: str = ""
    category: str = "General"
    graph: Dict[str, Any]


class SessionOpenBody(BaseModel):
    ass_path: str
    style: Optional[str] = None


class CacheBody(BaseModel):
    key: str = "_all"
    graph: Dict[str, Any]


class EffectBody(BaseModel):
    code: str


class EffectCreateBody(BaseModel):
    name: str
    style: Optional[str] = None
    library_name: Optional[str] = Field(None, description="Efecto de la libreria en que basarse (vacio = en blanco)")
    library_kind: Optional[str] = None


class ChoiceBody(BaseModel):
    mode: str = Field(..., description="script | nodes")
    style: Optional[str] = None

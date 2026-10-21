# -*- coding: utf-8 -*-
# Pyxis Effector — Domain Entities (Subtitles)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from ..value_objects.resolution import Resolution
from ..value_objects.timecode import Timecode


@dataclass
class SubtitleStyle:
    """Represents a V4+ style definition in an ASS script."""

    name: str = "Default"
    fontname: str = "Arial"
    fontsize: float = 48.0
    primary_color: str = "&H00FFFFFF"
    secondary_color: str = "&H000000FF"
    outline_color: str = "&H00000000"
    back_color: str = "&H00000000"
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikeout: bool = False
    scale_x: float = 100.0
    scale_y: float = 100.0
    spacing: float = 0.0
    angle: float = 0.0
    border_style: int = 1
    outline: float = 2.0
    shadow: float = 0.0
    alignment: int = 2
    margin_l: int = 10
    margin_r: int = 10
    margin_v: int = 10
    encoding: int = 1


@dataclass
class DialogueLine:
    """Represents an individual subtitle event/dialogue line."""

    index: int = 0
    layer: int = 0
    start_time: Timecode = field(default_factory=Timecode)
    end_time: Timecode = field(default_factory=Timecode)
    style: str = "Default"
    actor: str = ""
    margin_l: int = 0
    margin_r: int = 0
    margin_v: int = 0
    effect: str = ""
    text: str = ""
    is_comment: bool = False

    @property
    def duration_ms(self) -> int:
        return max(0, self.end_time.milliseconds - self.start_time.milliseconds)

    def to_ass_line(self) -> str:
        line_type = "Comment" if self.is_comment else "Dialogue"
        return (
            f"{line_type}: {self.layer},{self.start_time.to_ass()},{self.end_time.to_ass()},"
            f"{self.style},{self.actor},{self.margin_l},{self.margin_r},{self.margin_v},"
            f"{self.effect},{self.text}\n"
        )


@dataclass
class SubtitleScript:
    """Complete domain representation of an ASS script."""

    title: str = "Untitled Script"
    script_type: str = "v4.00+"
    wrap_style: int = 0
    scaled_border_and_shadow: bool = True
    ycbcr_matrix: str = "None"
    resolution: Resolution = field(default_factory=Resolution)
    audio_file: str = ""
    video_file: str = ""
    styles: Dict[str, SubtitleStyle] = field(default_factory=dict)
    dialogues: List[DialogueLine] = field(default_factory=list)

    @property
    def lines_count(self) -> int:
        return len(self.dialogues)

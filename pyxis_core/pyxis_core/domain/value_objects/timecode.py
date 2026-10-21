# -*- coding: utf-8 -*-
# Pyxis Effector — Domain Value Objects
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from dataclasses import dataclass


@dataclass(frozen=True)
class Timecode:
    """Immutable value object representing ASS timecode in milliseconds."""

    milliseconds: int = 0

    @classmethod
    def from_ass(cls, time_str: str) -> "Timecode":
        """Converts an ASS time string ('H:MM:SS.cs') into Timecode (milliseconds)."""
        if not time_str or not isinstance(time_str, str):
            return cls(0)
        try:
            parts = time_str.strip().split(":")
            if len(parts) != 3:
                return cls(0)
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split(".")
            seconds = int(seconds_parts[0])
            centiseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            # 1 centisecond = 10 ms
            total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + centiseconds * 10
            return cls(total_ms)
        except Exception:
            return cls(0)

    def to_ass(self) -> str:
        """Converts Timecode back to ASS string format ('H:MM:SS.cs')."""
        total_cs = max(0, self.milliseconds // 10)
        cs = total_cs % 100
        total_seconds = total_cs // 100
        seconds = total_seconds % 60
        total_minutes = total_seconds // 60
        minutes = total_minutes % 60
        hours = total_minutes // 60
        return f"{hours}:{minutes:02d}:{seconds:02d}.{cs:02d}"

    def __add__(self, other: "Timecode") -> "Timecode":
        return Timecode(self.milliseconds + other.milliseconds)

    def __sub__(self, other: "Timecode") -> "Timecode":
        return Timecode(max(0, self.milliseconds - other.milliseconds))

# -*- coding: utf-8 -*-
# Pyxis Effector — Domain Value Objects
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from dataclasses import dataclass


@dataclass(frozen=True)
class Resolution:
    """Immutable value object representing canvas resolution and timing."""

    play_res_x: int = 1920
    play_res_y: int = 1080
    frame_duration: float = 41.7083  # default ~23.976 fps in ms

    @property
    def aspect_ratio(self) -> float:
        if self.play_res_y <= 0:
            return 16.0 / 9.0
        return self.play_res_x / self.play_res_y

    @property
    def fps(self) -> float:
        if self.frame_duration <= 0:
            return 23.976
        return 1000.0 / self.frame_duration

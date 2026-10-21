# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Adapters (Telemetry Adapter)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from typing import Any, Dict
from ..engine.ass_telemetry_engine import ASSTelemetryEngine


class TelemetryAdapter:
    """Adapter for extracting subtitle performance and styling telemetry."""

    @staticmethod
    def analyze(ass_file_path: str) -> Dict[str, Any]:
        return ASSTelemetryEngine.analyze(ass_file_path)

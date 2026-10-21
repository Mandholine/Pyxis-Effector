# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Adapters (Image Tracer Adapter)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

import os
from typing import Any, Dict, Optional

from ..engine.geometry import trace_image, _get_potrace_exe_path


class ImageTracerAdapter:
    """Adapter for converting raster images (PNG, JPG, BMP) into ASS vector shapes.

    Uses native Python contour & Bézier curve generation (zero external dependencies).
    Optionally accelerates using a system 'potrace' binary if installed on the host.
    """

    @staticmethod
    def get_potrace_path() -> str:
        return _get_potrace_exe_path()

    @staticmethod
    def is_potrace_installed() -> bool:
        path = _get_potrace_exe_path()
        return bool(path and os.path.isfile(path))

    @staticmethod
    def trace(
        image_path: str,
        mode: str = "Potrace",
        threshold: int = 128,
        tolerance: float = 1.0,
        out_scale: float = 1.0,
        out_w: float = 0.0,
        out_h: float = 0.0,
        anchor: str = "Center",
        bin_mode: str = "Luminance",
        invert: bool = False,
    ) -> Dict[str, Any]:
        """Converts an image into an ASSDraw vector shape string (m, l, b).

        Args:
            image_path: Path to the image file (e.g. PNG, JPG).
            mode: 'Potrace' (Bézier curves), 'Polygon', or 'Borders'.
            threshold: Luminance or alpha threshold (0-255).
            tolerance: Curve approximation tolerance.
            out_scale: Overall scale multiplier.
            out_w: Target width in pixels (0 to preserve aspect ratio).
            out_h: Target height in pixels (0 to preserve aspect ratio).
            anchor: Origin anchor ('Center', 'TopLeft', etc.).
            bin_mode: 'Luminance', 'Silhouette' (alpha), or 'Borders'.
            invert: Invert black and white mask.

        Returns:
            Dict containing:
            - 'shape': ASSDraw command string (e.g. 'm 10 20 b 30 40 ...')
            - 'width': float width in pixels
            - 'height': float height in pixels
            - 'points': total vector points
            - 'error': error message if failed
        """
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        return trace_image(
            image_path=image_path,
            mode=mode,
            threshold=threshold,
            invert=invert,
            tolerance=tolerance,
            out_scale=out_scale,
            out_w=out_w,
            out_h=out_h,
            anchor=anchor,
            bin_mode=bin_mode,
        )

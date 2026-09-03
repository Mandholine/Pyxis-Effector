# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any question you can visit: https://discord.gg/rYsARc3fB9

"""Pruebas unitarias para los recursos visuales del previsualizador y slicing en tiempo real."""

import os
import unittest
from clipper_engine import ClipperEngine


class TestPreviewVisualResources(unittest.TestCase):
    """Pruebas de integridad de recursos estaticos del previsualizador."""

    def test_default_back_asset_exists(self):
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidates = [
            os.path.join(script_dir, "web", "default_back.webp"),
            os.path.join(script_dir, "default_back.webp")
        ]
        found = any(os.path.isfile(c) for c in candidates)
        self.assertTrue(found, "El recurso default_back.webp no se encuentra en el directorio del plugin")

    def test_slicer_mesh_preview_modes(self):
        base_shape = "m 0 0 l 200 0 l 200 100 l 0 100"
        for engine_name in ["hex", "tri", "dia", "ring", "voronoi", "quad"]:
            pieces = ClipperEngine.slice_grid(base_shape, cols=2, rows=2, engine_mode=engine_name)
            self.assertGreater(len(pieces), 0, f"Fallo al generar malla de preview para: {engine_name}")


if __name__ == "__main__":
    unittest.main()

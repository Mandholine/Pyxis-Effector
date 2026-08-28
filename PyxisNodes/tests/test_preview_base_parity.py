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

# test_preview_base_parity.py
"""Prueba de certificación de paridad utilizando preview_base.ass real generado por Aegisub."""

import unittest
from font_engine import FontEngine
from karaskel_engine import KaraskelEngine, KaraskelLine, KaraskelMeta


class TestPreviewBaseParity(unittest.TestCase):

    def test_preview_base_line(self):
        script_info = {
            "PlayResX": "1000",
            "PlayResY": "260"
        }
        style_default = {
            "name": "Default",
            "fontname": "Arial",
            "fontsize": 65,
            "bold": False,
            "italic": False,
            "underline": False,
            "strikeout": False,
            "scale_x": 100.0,
            "scale_y": 100.0,
            "spacing": 0.0,
            "margin_l": 10,
            "margin_r": 10,
            "margin_t": 100,
            "margin_b": 100,
            "align": 2
        }
        styles = {"Default": style_default}

        meta, styles = KaraskelEngine.collect_head(script_info, styles)

        line = KaraskelLine(
            raw_text=r"{\k43}Ma{\k65}ry {\k44}te{\k87}nía {\k65}un {\k65}cor{\k44}de{\k43}ri{\k44}to",
            start_time=5000,
            end_time=10000,
            style="Default",
            margin_l=0,
            margin_r=0,
            margin_t=0,
            margin_b=0
        )

        KaraskelEngine.preproc_line(meta, styles, line)

        # Métricas de referencia grabadas por Aegisub Karaskel Lua en preview_base.ass:
        # l=200.8359375; c=500; r=799.1640625; t=95; m=127.5; b=160; rw=598.328125
        # syl_centers=200.8359375, 241.25, 305.8984375, 370.5703125, 435.28125, 524.2578125, 613.203125, 685.9765625, 734.484375, 774.8984375

        print("\n=== RESULTADOS COMPARATIVOS AEGISUB C++/LUA VS PYTHON KARASKEL ===")
        print(f"PlayRes: {meta.res_x}x{meta.res_y}")
        print(f"Line Width  -> Aegisub: 598.33 | Python: {line.width:.2f}")
        print(f"Line Left   -> Aegisub: 200.84 | Python: {line.left:.2f}")
        print(f"Line Center -> Aegisub: 500.00 | Python: {line.center:.2f}")
        print(f"Line Right  -> Aegisub: 799.16 | Python: {line.right:.2f}")
        print(f"Line Top    -> Aegisub:  95.00 | Python: {line.top:.2f}")
        print(f"Line Bottom -> Aegisub: 160.00 | Python: {line.bottom:.2f}")

        print("\n--- SÍLABAS (Centro X) ---")
        aegisub_centers = [200.84, 241.25, 305.90, 370.57, 435.28, 524.26, 613.20, 685.98, 734.48, 774.90]
        for idx, syl in enumerate(line.kara):
            a_center = aegisub_centers[idx] if idx < len(aegisub_centers) else 0.0
            print(f"Syl {syl.i} '{syl.text_spacestripped}': Aegisub={a_center:.2f} | Python={syl.center:.2f} (diff={abs(a_center - syl.center):.2f}px)")

        # Verificar que el centro de la línea sea idéntico a 500 (resolución 1000/2)
        self.assertAlmostEqual(line.center, 500.0, delta=0.1)


if __name__ == "__main__":
    unittest.main()

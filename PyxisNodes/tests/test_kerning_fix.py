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


# ============================================================
# test_kerning_fix.py - Tests para el fix de rw (ancho real)
# Agregar al final de test_pyxis_fase0.py o como archivo separado
# ============================================================

import pytest
from ass_parser import ASSParser, KaraokeProcessor
from models import PyxisLine


class TestRealWidth:
    """Tests para el campo rw (ancho real con kerning) en metricas."""

    def _process(self, raw, metrics=None, style=None):
        proc = KaraokeProcessor(1280, 720, 41.708)
        if style is None:
            style = {"MarginL": "10", "MarginR": "10", "MarginV": "30",
                      "Alignment": "2"}
        return proc.process_line(raw, style, metrics)

    def test_rw_used_when_available(self):
        """Cuando rw existe y es > 0, line.width debe usar rw."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'rw': 195.5, 'w': [50.0, 50.0, 50.0, 50.0]}
        line = self._process(raw, metrics)
        assert line.width == 195.5
        assert line.width != sum(metrics['w'])  # 200.0

    def test_fallback_to_sum_w_when_rw_missing(self):
        """Sin rw (metricas viejas), line.width debe usar sum(w)."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [50.0, 50.0, 50.0, 50.0]}
        line = self._process(raw, metrics)
        assert line.width == 200.0

    def test_fallback_to_sum_w_when_rw_zero(self):
        """rw=0 se trata como ausente (fallback a sum(w))."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'rw': 0, 'w': [50.0, 50.0, 50.0, 50.0]}
        line = self._process(raw, metrics)
        assert line.width == 200.0

    def test_line_left_uses_rw(self):
        """line.left debe calcularse con rw, no con sum(w)."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola"
        # an2 (bottom-center): left = (1280 + 10 - 10)/2 - width/2
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'rw': 195.5, 'w': [50.0, 50.0, 50.0, 50.0]}
        line = self._process(raw, metrics)
        expected_left = (1280 + 10 - 10) / 2 - (195.5 / 2)
        assert abs(line.left - expected_left) < 0.01

    def test_line_center_uses_rw(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'rw': 195.5, 'w': [50.0, 50.0, 50.0, 50.0]}
        line = self._process(raw, metrics)
        expected_center = line.left + (195.5 / 2)
        assert abs(line.center - expected_center) < 0.01

    def test_syl_positions_still_use_incremental_w(self):
        """syl.left/center se acumulan con w (incremental), no rw."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k50}ab{\\k50}cd"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'rw': 38.0, 'w': [10.0, 10.0, 10.0, 10.0]}
        line = self._process(raw, metrics)
        # syl 0: left = line.left, center = line.left + 20/2
        assert abs(line.syls[0].left - line.left) < 0.01
        assert abs(line.syls[0].center - (line.left + 10.0)) < 0.01
        # syl 1: left = line.left + 20, center = line.left + 30
        assert abs(line.syls[1].left - (line.left + 20.0)) < 0.01
        assert abs(line.syls[1].center - (line.left + 30.0)) < 0.01

    def test_kerning_scenario(self):
        """Simula el escenario real: rw < sum(w) por kerning negativo."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k42}Ma{\\k62}ry"
        # Kerning entre 'r' y 'y': extents("Mary") < extents("Mar") + w['y']
        metrics = {'h': 65.0, 'd': 8.0, 'e': 0.0, 'sel': False,
                   'rw': 118.3, 'w': [40.2, 30.1, 28.5, 22.0]}
        line = self._process(raw, metrics)
        # line.width usa rw (el ancho real que el renderer reporta)
        assert line.width == 118.3
        # Pero las silabas se posicionan con w incremental
        syl0_w = metrics['w'][0] + metrics['w'][1]  # 40.2 + 30.1 = 70.3
        syl1_w = metrics['w'][2] + metrics['w'][3]  # 28.5 + 22.0 = 50.5
        assert abs(line.syls[0].width - syl0_w) < 0.01
        assert abs(line.syls[1].width - syl1_w) < 0.01
        # La suma de syls puede diferir de line.width (eso es esperado con kerning)
        total_syl_w = sum(s.width for s in line.syls)
        assert abs(total_syl_w - sum(metrics['w'])) < 0.01
        # Pero line.left se basa en rw, asi que el bloque entero esta bien posicionado
        assert abs(line.left - ((1280 + 10 - 10) / 2 - 118.3 / 2)) < 0.01

    def test_parser_reads_rw(self, tmp_path):
        """ASSParser.read_file debe leer el campo rw de las metricas."""
        ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720

[Pyxis Config]
FrameDuration: 41.708

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Comment: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,PyxisMetrics,h=40;d=5;e=0;sel=1;rw=195.5;w=50,50,50,50
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,hola
"""
        f = tmp_path / "test_rw.ass"
        f.write_text(ass_content, encoding='utf-8')
        styles, dialogues, rx, ry, fd = ASSParser.read_file(str(f))
        metrics = dialogues[0]['metrics']
        assert metrics['rw'] == 195.5
        assert metrics['w'] == [50.0, 50.0, 50.0, 50.0]

    def test_parser_rw_defaults_to_zero(self, tmp_path):
        """Sin rw en las metricas (formato viejo), rw debe ser 0."""
        ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720

[Pyxis Config]
FrameDuration: 41.708

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Comment: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,PyxisMetrics,h=40;d=5;e=0;sel=1;w=50,50,50,50
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,hola
"""
        f = tmp_path / "test_no_rw.ass"
        f.write_text(ass_content, encoding='utf-8')
        styles, dialogues, rx, ry, fd = ASSParser.read_file(str(f))
        metrics = dialogues[0]['metrics']
        assert metrics['rw'] == 0.0

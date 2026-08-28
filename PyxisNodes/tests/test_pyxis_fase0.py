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

"""
Fase 0 - Suite de tests para Pyxis Node Engine
Ejecutar: pytest tests/ -v
Requiere: pip install pytest

Estructura esperada del proyecto:
    proyecto/
        models.py
        utils.py
        decorators.py
        ass_parser.py
        node_engine.py
        nodes_library.py
        tests/
            __init__.py
            conftest.py
            test_utils.py
            test_models.py
            test_ass_parser.py
            test_node_engine.py
            test_nodes_library.py
"""

# ============================================================
# conftest.py
# ============================================================

import pytest
import sys
import os

# Asegurar que el directorio raiz del proyecto este en sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import PyxisUnit, PyxisLine
from utils import parse_time, format_time


# --- FIXTURES DE MODELOS ---

@pytest.fixture
def pyxis_unit():
    """PyxisUnit basico con valores por defecto."""
    return PyxisUnit()


@pytest.fixture
def pyxis_line():
    """PyxisLine basico con valores por defecto."""
    return PyxisLine()


@pytest.fixture
def populated_line():
    """PyxisLine con datos realistas simulando una linea parseada."""
    line = PyxisLine()
    line.layer = 0
    line.style_name = "Default"
    line.actor = ""
    line.start_time = 1000
    line.end_time = 3000
    line.duration = 2000
    line.mid_time = 2000
    line.width = 200.0
    line.height = 40.0
    line.left = 100.0
    line.center = 200.0
    line.right = 300.0
    line.top = 600.0
    line.middle = 620.0
    line.bottom = 640.0
    line.margin_l = 10
    line.margin_r = 10
    line.margin_v = 30
    line.text_stripped = "hola mundo"
    line.is_selected = True
    return line


# --- FIXTURES DE ASS RAW ---

@pytest.fixture
def sample_ass_content():
    """Contenido ASS minimo viable para tests."""
    return """[Script Info]
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
Comment: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,PyxisMetrics,h=40;d=5;e=0;sel=1;w=20,20,20,20,20,20,20,20,20,20
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,hola mundo
"""


@pytest.fixture
def sample_ass_karaoke():
    """ASS con timing de karaoke (\\k tags)."""
    return """[Script Info]
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
Comment: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,PyxisMetrics,h=40;d=5;e=0;sel=1;w=20,20,20,20,20,20,20,20,20,20
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo
"""


@pytest.fixture
def tmp_ass_file(tmp_path, sample_ass_content):
    """Escribe el ASS de muestra en un archivo temporal."""
    f = tmp_path / "test.ass"
    f.write_text(sample_ass_content, encoding='utf-8')
    return str(f)


@pytest.fixture
def tmp_ass_karaoke(tmp_path, sample_ass_karaoke):
    """Escribe el ASS con karaoke en un archivo temporal."""
    f = tmp_path / "test_karaoke.ass"
    f.write_text(sample_ass_karaoke, encoding='utf-8')
    return str(f)


# --- FIXTURES DE GRAFOS ---

@pytest.fixture
def minimal_graph():
    """Grafo minimo: Main Loop (syl) -> Salida."""
    return {
        "nodes": [
            {
                "id": 1,
                "type": "Loops/Main Loop",
                "properties": {"iterador": "syl"},
                "inputs": [],
                "outputs": [{"links": [1]}]
            },
            {
                "id": 2,
                "type": "System/Output",
                "properties": {"apply_to": "Selected Lines"},
                "inputs": [
                    {"link": 1},
                    {"link": None},
                    {"link": None},
                    {"link": None},
                    {"link": None},
                    {"link": None}
                ],
                "outputs": []
            }
        ],
        "links": [
            [1, 1, 0, 2, 0]
        ]
    }


@pytest.fixture
def graph_with_tags(minimal_graph):
    """Grafo con nodo de tag blur conectado a la Salida."""
    graph = minimal_graph.copy()
    graph["nodes"] = list(graph["nodes"])
    graph["links"] = list(graph["links"])

    # Agregar nodo Tags/blur
    graph["nodes"].append({
        "id": 3,
        "type": "Tags/blur",
        "properties": {"Fuerza": "5"},
        "inputs": [{"link": None}],
        "outputs": [{"links": [2]}]
    })
    # Conectar blur (id=3) al puerto 4 (tags) de Salida (id=2)
    graph["links"].append([2, 3, 0, 2, 4])
    graph["nodes"][1]["inputs"][4] = {"link": 2}
    return graph


# ============================================================
# test_utils.py
# ============================================================

class TestParseTime:
    """Tests para utils.parse_time: ASS timestamp -> milisegundos."""

    def test_zero(self):
        assert parse_time("0:00:00.00") == 0

    def test_one_second(self):
        assert parse_time("0:00:01.00") == 1000

    def test_one_minute(self):
        assert parse_time("0:01:00.00") == 60000

    def test_one_hour(self):
        assert parse_time("1:00:00.00") == 3600000

    def test_centiseconds(self):
        assert parse_time("0:00:00.50") == 500

    def test_complex_time(self):
        assert parse_time("1:23:45.67") == (3600 + 23*60 + 45) * 1000 + 670

    def test_invalid_returns_zero(self):
        assert parse_time("not a time") == 0

    def test_empty_returns_zero(self):
        assert parse_time("") == 0

    def test_whitespace_stripped(self):
        assert parse_time("  0:00:01.00  ") == 1000


class TestFormatTime:
    """Tests para utils.format_time: milisegundos -> ASS timestamp."""

    def test_zero(self):
        assert format_time(0) == "0:00:00.00"

    def test_one_second(self):
        assert format_time(1000) == "0:00:01.00"

    def test_minutes_and_seconds(self):
        assert format_time(61500) == "0:01:01.50"

    def test_hours(self):
        assert format_time(3600000) == "1:00:00.00"

    def test_negative_clamps_to_zero(self):
        assert format_time(-500) == "0:00:00.00"

    def test_roundtrip(self):
        """parse_time y format_time son inversas."""
        for ms in [0, 100, 1000, 61500, 3600000, 5025670]:
            assert parse_time(format_time(ms)) == ms


# ============================================================
# test_models.py
# ============================================================

class TestPyxisUnit:
    """Tests para el modelo PyxisUnit."""

    def test_default_values(self, pyxis_unit):
        assert pyxis_unit.i == 1
        assert pyxis_unit.n == 1
        assert pyxis_unit.text == ""
        assert pyxis_unit.text_stripped == ""
        assert pyxis_unit.duration == 0
        assert pyxis_unit.start_time == 0
        assert pyxis_unit.end_time == 0
        assert pyxis_unit.mid_time == 0

    def test_default_geometry(self, pyxis_unit):
        assert pyxis_unit.width == 0.0
        assert pyxis_unit.height == 0.0
        assert pyxis_unit.left == 0.0
        assert pyxis_unit.center == 0.0
        assert pyxis_unit.right == 0.0
        assert pyxis_unit.top == 0.0
        assert pyxis_unit.middle == 0.0
        assert pyxis_unit.bottom == 0.0

    def test_default_references(self, pyxis_unit):
        assert pyxis_unit.line is None
        assert pyxis_unit.word is None
        assert pyxis_unit.syl is None
        assert pyxis_unit.chars == []


class TestPyxisLine:
    """Tests para el modelo PyxisLine."""

    def test_inherits_pyxis_unit(self, pyxis_line):
        assert isinstance(pyxis_line, PyxisUnit)

    def test_default_values(self, pyxis_line):
        assert pyxis_line.layer == 0
        assert pyxis_line.style_name == "Default"
        assert pyxis_line.actor == ""
        assert pyxis_line.effect == ""
        assert pyxis_line.is_selected is False

    def test_self_reference(self, pyxis_line):
        """PyxisLine.line debe apuntar a si misma."""
        assert pyxis_line.line is pyxis_line

    def test_default_margins(self, pyxis_line):
        assert pyxis_line.margin_l == 0
        assert pyxis_line.margin_r == 0
        assert pyxis_line.margin_v == 0


# ============================================================
# test_ass_parser.py
# ============================================================

from ass_parser import ASSParser, KaraokeProcessor


class TestASSParser:
    """Tests para ASSParser.read_file."""

    def test_reads_styles(self, tmp_ass_file):
        styles, dialogues, rx, ry, fd = ASSParser.read_file(tmp_ass_file)
        assert "Default" in styles
        assert styles["Default"]["Fontname"] == "Arial"
        assert styles["Default"]["Fontsize"] == "48"

    def test_reads_resolution(self, tmp_ass_file):
        _, _, rx, ry, _ = ASSParser.read_file(tmp_ass_file)
        assert rx == 1280
        assert ry == 720

    def test_reads_frame_duration(self, tmp_ass_file):
        _, _, _, _, fd = ASSParser.read_file(tmp_ass_file)
        assert abs(fd - 41.708) < 0.001

    def test_reads_dialogues(self, tmp_ass_file):
        _, dialogues, _, _, _ = ASSParser.read_file(tmp_ass_file)
        assert len(dialogues) == 1
        assert dialogues[0]['raw'].startswith("Dialogue:")

    def test_reads_metrics(self, tmp_ass_file):
        _, dialogues, _, _, _ = ASSParser.read_file(tmp_ass_file)
        metrics = dialogues[0].get('metrics')
        assert metrics is not None
        assert metrics['h'] == 40.0
        assert metrics['d'] == 5.0
        assert metrics['sel'] is True
        assert len(metrics['w']) == 10

    def test_missing_file_returns_defaults(self):
        styles, dialogues, rx, ry, fd = ASSParser.read_file("/nonexistent/path.ass")
        assert styles == {}
        assert dialogues == []
        assert rx == 1280
        assert ry == 720


class TestKaraokeProcessor:
    """Tests para KaraokeProcessor.process_line."""

    def _process(self, raw, metrics=None, style=None):
        proc = KaraokeProcessor(1280, 720, 41.708)
        if style is None:
            style = {"MarginL": "10", "MarginR": "10", "MarginV": "30",
                      "Alignment": "2"}
        return proc.process_line(raw, style, metrics)

    def test_parses_basic_dialogue(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,hola mundo"
        line = self._process(raw)
        assert line is not None
        assert line.start_time == 1000
        assert line.end_time == 3000
        assert line.duration == 2000
        assert line.style_name == "Default"

    def test_strips_tags(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\b1}hola{\\b0} mundo"
        line = self._process(raw)
        assert line.text_stripped == "hola mundo"

    def test_replaces_hardbreaks(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,hola\\Nmundo"
        line = self._process(raw)
        assert "\\N" not in line.text_stripped

    def test_with_metrics(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,hola mundo"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': True,
                   'w': [20.0]*10}
        line = self._process(raw, metrics)
        assert line.height == 40.0
        assert line.descent == 5.0
        assert line.is_selected is True
        assert line.width == 200.0

    def test_without_metrics(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,hola mundo"
        line = self._process(raw, None)
        assert line.width == 100
        assert line.height == 35
        assert line.is_selected is False

    def test_alignment_bottom_center(self):
        """an2 = bottom-center: left = (resX + ml - mr)/2 - w/2, top = resY - mv - h."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,test"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [20.0]*4}
        line = self._process(raw, metrics)
        expected_left = (1280 + 10 - 10) / 2 - (80.0 / 2)
        assert abs(line.left - expected_left) < 0.01

    def test_invalid_raw_returns_none(self):
        result = self._process("Not a dialogue line")
        assert result is None

    def test_untimed_creates_chars(self):
        """Sin \\k tags, debe crear chars y words pero no syls nativos."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,hola mundo"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [20.0]*10}
        line = self._process(raw, metrics)
        assert len(line.chars) == 10
        assert len(line.words) == 2
        assert line.words[0].text_stripped == "hola"
        assert line.words[1].text_stripped == "mundo"

    def test_untimed_syls_equal_words(self):
        """En untimed, syls = words."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,hola mundo"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [20.0]*10}
        line = self._process(raw, metrics)
        assert len(line.syls) == len(line.words)

    def test_untimed_n_updated(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,hola mundo"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [20.0]*10}
        line = self._process(raw, metrics)
        for w in line.words:
            assert w.n == 2
        for c in line.chars:
            assert c.n == 10


class TestKaraokeTimed:
    """Tests para lineas con \\k (timed karaoke)."""

    def _process(self, raw, metrics=None):
        proc = KaraokeProcessor(1280, 720, 41.708)
        style = {"MarginL": "10", "MarginR": "10", "MarginV": "30",
                  "Alignment": "2"}
        return proc.process_line(raw, style, metrics)

    def test_parses_k_tags(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [20.0]*10}
        line = self._process(raw, metrics)
        assert len(line.syls) == 2
        assert line.syls[0].text_stripped == "hola "
        assert line.syls[1].text_stripped == "mundo"

    def test_k_syllable_duration(self):
        """\\k100 = 1000ms = 1 segundo."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [20.0]*10}
        line = self._process(raw, metrics)
        assert line.syls[0].duration == 1000
        assert line.syls[1].duration == 1000

    def test_k_syllable_times(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [20.0]*10}
        line = self._process(raw, metrics)
        assert line.syls[0].start_time == 1000
        assert line.syls[0].end_time == 2000
        assert line.syls[1].start_time == 2000
        assert line.syls[1].end_time == 3000

    def test_k_chars_have_parent_syl(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [20.0]*10}
        line = self._process(raw, metrics)
        for syl in line.syls:
            for char in syl.chars:
                assert char.syl is syl

    def test_k_chars_distributed_width(self):
        """Los chars deben tener ancho proporcional dentro de la silaba."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [20.0]*10}
        line = self._process(raw, metrics)
        syl0 = line.syls[0]
        # "hola " = 5 chars, cada uno 20px -> syl.width = 100
        assert syl0.width == 100.0
        total_char_width = sum(c.width for c in syl0.chars)
        assert abs(total_char_width - syl0.width) < 0.01

    def test_kf_and_ko_tags(self):
        """\\kf y \\ko tambien deben detectarse como timing."""
        for tag in ["\\kf100", "\\ko100", "\\K100"]:
            raw = f"Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{{{tag}}}hola"
            metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                       'w': [20.0]*4}
            line = self._process(raw, metrics)
            assert len(line.syls) >= 1, f"Fallo con tag {tag}"

    def test_word_construction_from_timed(self):
        """Words deben construirse correctamente desde chars en modo timed."""
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [20.0]*10}
        line = self._process(raw, metrics)
        assert len(line.words) == 2
        assert line.words[0].text_stripped == "hola"
        assert line.words[1].text_stripped == "mundo"

    def test_n_values_updated(self):
        raw = "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo"
        metrics = {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                   'w': [20.0]*10}
        line = self._process(raw, metrics)
        for s in line.syls:
            assert s.n == 2
        for w in line.words:
            assert w.n == 2


# ============================================================
# test_node_engine.py
# ============================================================

from node_engine import GraphEngine


class TestGraphEngineInit:
    """Tests para la inicializacion del GraphEngine."""

    def test_stores_nodes(self, minimal_graph):
        engine = GraphEngine(minimal_graph)
        assert len(engine.nodes) == 2
        assert 1 in engine.nodes
        assert 2 in engine.nodes

    def test_stores_links(self, minimal_graph):
        engine = GraphEngine(minimal_graph)
        assert len(engine.links) == 1

    def test_default_resolution(self, minimal_graph):
        engine = GraphEngine(minimal_graph)
        assert engine.rx == 1280
        assert engine.ry == 720

    def test_custom_resolution(self, minimal_graph):
        engine = GraphEngine(minimal_graph, rx=1920, ry=1080, fd=33.33)
        assert engine.rx == 1920
        assert engine.ry == 1080
        assert abs(engine.fd - 33.33) < 0.01


class TestTraceLoopChain:
    """Tests para trace_loop_chain."""

    def test_simple_main_loop(self, minimal_graph):
        engine = GraphEngine(minimal_graph)
        output_node = engine.nodes[2]
        chain = engine.trace_loop_chain(output_node)
        assert len(chain) == 1
        assert chain[0]['type'] == 'base'
        assert chain[0]['val'] == 'syl'

    def test_maxloop_chain(self):
        """MaxLoop -> Main Loop -> Salida."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop",
                 "properties": {"iterador": "syl"}, "inputs": [],
                 "outputs": [{"links": [1]}]},
                {"id": 2, "type": "Loops/MaxLoop",
                 "properties": {"veces": "3", "var_name": "j"},
                 "inputs": [{"link": 2}],
                 "outputs": [{"links": [3]}]},
                {"id": 3, "type": "System/Output",
                 "properties": {}, "inputs": [{"link": 3}] + [{"link": None}]*5,
                 "outputs": []}
            ],
            "links": [
                [2, 1, 0, 2, 0],
                [3, 2, 0, 3, 0]
            ]
        }
        engine = GraphEngine(graph)
        chain = engine.trace_loop_chain(engine.nodes[3])
        assert len(chain) == 2
        assert chain[0]['type'] == 'base'
        assert chain[1]['type'] == 'maxloop'
        assert chain[1]['val'] == '3'

    def test_no_loop_returns_empty(self):
        """Salida sin loop conectado retorna cadena vacia."""
        graph = {
            "nodes": [
                {"id": 1, "type": "System/Output",
                 "properties": {}, "inputs": [{"link": None}]*6, "outputs": []}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        chain = engine.trace_loop_chain(engine.nodes[1])
        assert chain == []


class TestEvaluateDataNode:
    """Tests para evaluate_data_node."""

    def _make_context(self):
        """Contexto minimo con un processor mock."""
        class MockProcessor:
            res_x = 1280
            res_y = 720
            frame_dur = 41.708

        return {'processor': MockProcessor()}

    def test_meta_res_x(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Meta/meta.res_x", "properties": {},
                 "inputs": [], "outputs": []}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        result = engine.evaluate_data_node(1, self._make_context())
        assert result == "1280"

    def test_texto_libre(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Texto/Texto Libre",
                 "properties": {"Value": "hello"},
                 "inputs": [], "outputs": []}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        result = engine.evaluate_data_node(1, {})
        assert result == "hello"

    def test_math_add(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Math/Suma",
                 "properties": {"A": "5", "B": "3"},
                 "inputs": [{"link": None}, {"link": None}],
                 "outputs": []}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        result = engine.evaluate_data_node(1, self._make_context())
        assert float(result) == 8.0

    def test_math_divide_by_zero(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Math/Dividir",
                 "properties": {"A": "5", "B": "0"},
                 "inputs": [{"link": None}, {"link": None}],
                 "outputs": []}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        result = engine.evaluate_data_node(1, self._make_context())
        assert float(result) == 0.0

    def test_tag_blur(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Tags/blur",
                 "properties": {"Fuerza": "5"},
                 "inputs": [{"link": None}],
                 "outputs": []}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        result = engine.evaluate_data_node(1, self._make_context())
        assert result == "\\blur5.0"

    def test_tag_pos(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Tags/pos",
                 "properties": {"X": "640", "Y": "360"},
                 "inputs": [{"link": None}, {"link": None}],
                 "outputs": []}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        result = engine.evaluate_data_node(1, self._make_context())
        assert "\\pos(" in result
        assert "640" in result
        assert "360" in result

    def test_unknown_node_returns_empty(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Unknown/Node", "properties": {},
                 "inputs": [], "outputs": []}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        result = engine.evaluate_data_node(1, {})
        assert result == ""

    def test_context_variable_resolution(self):
        """Si el valor del input esta en el contexto, se resuelve."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Texto/Texto Libre",
                 "properties": {"Value": "syl"},
                 "inputs": [], "outputs": []}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        # Texto Libre no resuelve contexto, retorna el valor directo
        result = engine.evaluate_data_node(1, {'syl': 'resolved'})
        assert result == "syl"


class TestProcess:
    """Tests de integracion para GraphEngine.process."""

    def _make_dialogue_items(self):
        return [
            {
                'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo",
                'metrics': {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': True,
                            'w': [20.0]*10}
            }
        ]

    def _make_styles(self):
        return {
            "Default": {"MarginL": "10", "MarginR": "10", "MarginV": "30",
                        "Alignment": "2", "Fontname": "Arial", "Fontsize": "48"}
        }

    def test_generates_lines(self, minimal_graph):
        engine = GraphEngine(minimal_graph)
        lines = engine.process(self._make_dialogue_items(), self._make_styles())
        assert len(lines) > 0
        assert all(l.startswith("Dialogue:") for l in lines)

    def test_line_count_matches_syls(self, minimal_graph):
        """Un loop syl sobre una linea con 2 syls genera 2 lineas."""
        engine = GraphEngine(minimal_graph)
        lines = engine.process(self._make_dialogue_items(), self._make_styles())
        assert len(lines) == 2

    def test_lines_contain_pos(self, minimal_graph):
        """Lineas generadas deben tener \\pos automatico."""
        engine = GraphEngine(minimal_graph)
        lines = engine.process(self._make_dialogue_items(), self._make_styles())
        for l in lines:
            assert "\\pos(" in l

    def test_lines_contain_an5(self, minimal_graph):
        """Lineas sin \\an deben tener \\an5 automatico."""
        engine = GraphEngine(minimal_graph)
        lines = engine.process(self._make_dialogue_items(), self._make_styles())
        for l in lines:
            assert "\\an5" in l

    def test_effect_field_is_pyxis_fx(self, minimal_graph):
        engine = GraphEngine(minimal_graph)
        lines = engine.process(self._make_dialogue_items(), self._make_styles())
        for l in lines:
            parts = l.strip().split(',')
            assert parts[8] == "pyxis_fx"

    def test_apply_to_selected(self, minimal_graph):
        """Solo lineas seleccionadas deben procesarse."""
        items = [
            {
                'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo",
                'metrics': {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': True,
                            'w': [20.0]*10}
            },
            {
                'raw': "Dialogue: 0,0:00:04.00,0:00:06.00,Default,,0,0,0,,{\\k100}adios",
                'metrics': {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                            'w': [20.0]*5}
            }
        ]
        engine = GraphEngine(minimal_graph)
        lines = engine.process(items, self._make_styles())
        # Solo la primera linea (seleccionada) debe generar output
        assert len(lines) == 2

    def test_apply_to_all(self):
        """apply_to='All Lines' procesa todas las lineas."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop",
                 "properties": {"iterador": "syl"}, "inputs": [],
                 "outputs": [{"links": [1]}]},
                {"id": 2, "type": "System/Output",
                 "properties": {"apply_to": "All Lines"},
                 "inputs": [{"link": 1}] + [{"link": None}]*5,
                 "outputs": []}
            ],
            "links": [[1, 1, 0, 2, 0]]
        }
        items = [
            {
                'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola",
                'metrics': {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': True,
                            'w': [20.0]*4}
            },
            {
                'raw': "Dialogue: 0,0:00:04.00,0:00:06.00,Default,,0,0,0,,{\\k100}adios",
                'metrics': {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': False,
                            'w': [20.0]*5}
            }
        ]
        engine = GraphEngine(graph)
        lines = engine.process(items, self._make_styles())
        assert len(lines) == 2

    def test_maxloop_multiplies_output(self):
        """MaxLoop con veces=3 debe triplicar las lineas por syl."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop",
                 "properties": {"iterador": "syl"}, "inputs": [],
                 "outputs": [{"links": [1]}]},
                {"id": 2, "type": "Loops/MaxLoop",
                 "properties": {"veces": "3", "var_name": "j"},
                 "inputs": [{"link": 1}],
                 "outputs": [{"links": [2]}]},
                {"id": 3, "type": "System/Output",
                 "properties": {"apply_to": "All Lines"},
                 "inputs": [{"link": 2}] + [{"link": None}]*5,
                 "outputs": []}
            ],
            "links": [
                [1, 1, 0, 2, 0],
                [2, 2, 0, 3, 0]
            ]
        }
        items = [
            {
                'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo",
                'metrics': {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': True,
                            'w': [20.0]*10}
            }
        ]
        engine = GraphEngine(graph)
        lines = engine.process(items, self._make_styles())
        # 2 syls * 3 iterations = 6 lineas
        assert len(lines) == 6

    def test_char_loop(self):
        """Loop char itera sobre cada caracter."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop",
                 "properties": {"iterador": "char"}, "inputs": [],
                 "outputs": [{"links": [1]}]},
                {"id": 2, "type": "System/Output",
                 "properties": {"apply_to": "All Lines"},
                 "inputs": [{"link": 1}] + [{"link": None}]*5,
                 "outputs": []}
            ],
            "links": [[1, 1, 0, 2, 0]]
        }
        items = [
            {
                'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}ab",
                'metrics': {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': True,
                            'w': [20.0]*2}
            }
        ]
        engine = GraphEngine(graph)
        lines = engine.process(items, self._make_styles())
        # 2 chars = 2 lineas
        assert len(lines) == 2

    def test_word_loop(self):
        """Loop word itera sobre cada palabra."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop",
                 "properties": {"iterador": "word"}, "inputs": [],
                 "outputs": [{"links": [1]}]},
                {"id": 2, "type": "System/Output",
                 "properties": {"apply_to": "All Lines"},
                 "inputs": [{"link": 1}] + [{"link": None}]*5,
                 "outputs": []}
            ],
            "links": [[1, 1, 0, 2, 0]]
        }
        items = [
            {
                'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,hola mundo",
                'metrics': {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': True,
                            'w': [20.0]*10}
            }
        ]
        engine = GraphEngine(graph)
        lines = engine.process(items, self._make_styles())
        assert len(lines) == 2

    def test_line_loop(self):
        """Loop line genera una sola linea por linea de entrada."""
        graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop",
                 "properties": {"iterador": "line"}, "inputs": [],
                 "outputs": [{"links": [1]}]},
                {"id": 2, "type": "System/Output",
                 "properties": {"apply_to": "All Lines"},
                 "inputs": [{"link": 1}] + [{"link": None}]*5,
                 "outputs": []}
            ],
            "links": [[1, 1, 0, 2, 0]]
        }
        items = self._make_dialogue_items()
        engine = GraphEngine(graph)
        lines = engine.process(items, self._make_styles())
        assert len(lines) == 1

    def test_no_output_node_returns_empty(self):
        """Sin nodo Salida, no se genera nada."""
        graph = {"nodes": [], "links": []}
        engine = GraphEngine(graph)
        lines = engine.process(self._make_dialogue_items(), self._make_styles())
        assert lines == []

    def test_output_without_loop_returns_empty(self):
        """Salida sin loop conectado no genera lineas."""
        graph = {
            "nodes": [
                {"id": 1, "type": "System/Output",
                 "properties": {"apply_to": "All Lines"},
                 "inputs": [{"link": None}]*6, "outputs": []}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        lines = engine.process(self._make_dialogue_items(), self._make_styles())
        assert lines == []


class TestOutputContent:
    """Tests para el contenido de las lineas generadas."""

    def _make_items(self):
        return [
            {
                'raw': "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k100}hola {\\k100}mundo",
                'metrics': {'h': 40.0, 'd': 5.0, 'e': 0.0, 'sel': True,
                            'w': [20.0]*10}
            }
        ]

    def _make_styles(self):
        return {
            "Default": {"MarginL": "10", "MarginR": "10", "MarginV": "30",
                        "Alignment": "2", "Fontname": "Arial", "Fontsize": "48"}
        }

    def test_syl_times_propagate(self, minimal_graph):
        """Los tiempos de cada syl deben aparecer en las lineas generadas."""
        engine = GraphEngine(minimal_graph)
        lines = engine.process(self._make_items(), self._make_styles())
        # Syl 0: 1000-2000, Syl 1: 2000-3000
        assert "0:00:01.00" in lines[0]
        assert "0:00:02.00" in lines[0]
        assert "0:00:02.00" in lines[1]
        assert "0:00:03.00" in lines[1]

    def test_auto_inherit_text(self, minimal_graph):
        """Si el puerto texto no esta conectado, hereda text_stripped."""
        engine = GraphEngine(minimal_graph)
        lines = engine.process(self._make_items(), self._make_styles())
        assert "hola" in lines[0]
        assert "mundo" in lines[1]

    def test_style_name_propagated(self, minimal_graph):
        engine = GraphEngine(minimal_graph)
        lines = engine.process(self._make_items(), self._make_styles())
        for l in lines:
            parts = l.strip().split(',')
            assert parts[3] == "Default"


# ============================================================
# test_nodes_library.py
# ============================================================

from nodes_library import *
from decorators import NODE_REGISTRY, PYXIS_DB


class TestNodeRegistry:
    """Tests para verificar que los nodos se registran correctamente."""

    def test_math_nodes_registered(self):
        assert "Math/Suma" in NODE_REGISTRY
        assert "Math/Resta" in NODE_REGISTRY
        assert "Math/Multiplicar" in NODE_REGISTRY
        assert "Math/Dividir" in NODE_REGISTRY

    def test_tag_nodes_registered(self):
        assert "Tags/pos" in NODE_REGISTRY
        assert "Tags/fad" in NODE_REGISTRY
        assert "Tags/blur" in NODE_REGISTRY
        assert "Tags/c (Color)" in NODE_REGISTRY

    def test_meta_nodes_registered(self):
        assert "Meta/meta.res_x" in NODE_REGISTRY
        assert "Meta/meta.res_y" in NODE_REGISTRY
        assert "Meta/meta.frame_dur" in NODE_REGISTRY

    def test_var_nodes_registered(self):
        for domain in ["line", "syl", "word", "char"]:
            cat = f"Vars_{domain.capitalize()}"
            assert f"{cat}/{domain}.text" in NODE_REGISTRY
            assert f"{cat}/{domain}.duration" in NODE_REGISTRY
            assert f"{cat}/{domain}.start_time" in NODE_REGISTRY
            assert f"{cat}/{domain}.end_time" in NODE_REGISTRY

    def test_line_specific_vars(self):
        assert "Vars_Line/line.layer" in NODE_REGISTRY
        assert "Vars_Line/line.actor" in NODE_REGISTRY
        assert "Vars_Line/line.effect" in NODE_REGISTRY
        assert "Vars_Line/line.margin_l" in NODE_REGISTRY
        assert "Vars_Line/line.margin_r" in NODE_REGISTRY
        assert "Vars_Line/line.margin_v" in NODE_REGISTRY

    def test_syl_specific_vars(self):
        assert "Vars_Syl/syl.x" in NODE_REGISTRY
        assert "Vars_Syl/syl.y" in NODE_REGISTRY

    def test_pyxis_db_populated(self):
        assert "Math" in PYXIS_DB
        assert "Tags" in PYXIS_DB
        assert "Meta" in PYXIS_DB

    def test_pyxis_db_inputs(self):
        assert PYXIS_DB["Math"]["Suma"] == ["A", "B"]
        assert PYXIS_DB["Tags"]["blur"] == ["Fuerza"]


class TestNodeFunctions:
    """Tests funcionales directos para los nodos."""

    def _ctx(self, **kwargs):
        """Crea un contexto mock minimo."""
        class MockProc:
            res_x = 1280
            res_y = 720
            frame_dur = 41.708

        ctx = {'processor': MockProc()}
        ctx.update(kwargs)
        return ctx

    def test_math_add(self):
        func = NODE_REGISTRY["Math/Suma"]
        assert func(self._ctx(), "5", "3") == 8.0

    def test_math_add_invalid(self):
        func = NODE_REGISTRY["Math/Suma"]
        assert func(self._ctx(), "abc", "def") == 0.0

    def test_math_sub(self):
        func = NODE_REGISTRY["Math/Resta"]
        assert func(self._ctx(), "10", "4") == 6.0

    def test_math_mul(self):
        func = NODE_REGISTRY["Math/Multiplicar"]
        assert func(self._ctx(), "3", "7") == 21.0

    def test_math_div(self):
        func = NODE_REGISTRY["Math/Dividir"]
        assert func(self._ctx(), "10", "3") == round(10.0/3.0, 3)

    def test_math_div_zero(self):
        func = NODE_REGISTRY["Math/Dividir"]
        assert func(self._ctx(), "10", "0") == 0.0

    def test_time_offset(self):
        func = NODE_REGISTRY["Time/Offset (Sumar ms)"]
        assert func(self._ctx(), "1000", "500") == 1500

    def test_tag_pos(self):
        func = NODE_REGISTRY["Tags/pos"]
        result = func(self._ctx(), "640", "360")
        assert "\\pos(" in result
        assert "640" in result
        assert "360" in result

    def test_tag_fad(self):
        func = NODE_REGISTRY["Tags/fad"]
        result = func(self._ctx(), "200", "300")
        assert result == "\\fad(200,300)"

    def test_tag_blur(self):
        func = NODE_REGISTRY["Tags/blur"]
        result = func(self._ctx(), "3.5")
        assert result == "\\blur3.5"

    def test_tag_color(self):
        func = NODE_REGISTRY["Tags/c (Color)"]
        result = func(self._ctx(), "FF0000")
        assert "\\c&HFF0000&" == result

    def test_tag_color_with_hash(self):
        func = NODE_REGISTRY["Tags/c (Color)"]
        result = func(self._ctx(), "#FF0000")
        assert "\\c&HFF0000&" == result

    def test_meta_res_x(self):
        func = NODE_REGISTRY["Meta/meta.res_x"]
        assert func(self._ctx()) == 1280

    def test_var_syl_text(self):
        func = NODE_REGISTRY["Vars_Syl/syl.text"]
        syl = PyxisUnit()
        syl.text_stripped = "ka"
        ctx = self._ctx(syl=syl)
        assert func(ctx) == "ka"

    def test_var_syl_duration(self):
        func = NODE_REGISTRY["Vars_Syl/syl.duration"]
        syl = PyxisUnit()
        syl.duration = 1000
        ctx = self._ctx(syl=syl)
        assert func(ctx) == 1000

    def test_var_syl_missing_returns_default(self):
        func = NODE_REGISTRY["Vars_Syl/syl.text"]
        ctx = self._ctx()  # no syl in context
        assert func(ctx) == ""

    def test_var_line_layer(self):
        func = NODE_REGISTRY["Vars_Line/line.layer"]
        line = PyxisLine()
        line.layer = 5
        ctx = self._ctx(line=line)
        assert func(ctx) == 5

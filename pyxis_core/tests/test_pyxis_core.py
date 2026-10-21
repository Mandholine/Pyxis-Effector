# -*- coding: utf-8 -*-
# Pyxis Effector — Core Tests
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

import pytest
import pyxis_core
from pyxis_core import (
    PyxisCore,
    SubtitleScript,
    DialogueLine,
    SubtitleStyle,
    NodeGraph,
    Timecode,
    Resolution,
)
from pyxis_core.application.dtos import (
    ValidateGraphRequestDTO,
    ProcessGraphRequestDTO,
)
from pyxis_core.cli import main as cli_main


def test_package_version():
    assert pyxis_core.__version__ == "0.1.0"


def test_facade_initialization():
    core = PyxisCore()
    assert core.subtitle_repo is not None
    assert core.template_repo is not None
    assert core.process_graph_use_case is not None
    assert core.validate_graph_use_case is not None
    assert core.templates_use_case is not None


def test_timecode_value_object():
    tc = Timecode.from_ass("0:01:23.45")
    assert tc.milliseconds == (1 * 60 + 23) * 1000 + 450
    assert tc.to_ass() == "0:01:23.45"

    tc2 = Timecode(1000)
    assert tc2.to_ass() == "0:00:01.00"

    added = tc + tc2
    assert added.milliseconds == tc.milliseconds + 1000


def test_resolution_value_object():
    res = Resolution(play_res_x=1920, play_res_y=1080)
    assert res.aspect_ratio == pytest.approx(16 / 9)
    assert res.fps == pytest.approx(23.976, rel=1e-2)


def test_domain_subtitle_entities():
    script = SubtitleScript(
        title="Test Script",
        resolution=Resolution(play_res_x=1920, play_res_y=1080),
        styles={"Default": SubtitleStyle(name="Default", fontname="Arial", fontsize=48.0)},
        dialogues=[
            DialogueLine(
                layer=0,
                start_time=Timecode.from_ass("0:00:01.00"),
                end_time=Timecode.from_ass("0:00:05.00"),
                style="Default",
                actor="",
                margin_l=0,
                margin_r=0,
                margin_v=0,
                effect="",
                text="Hello Pyxis",
            )
        ],
    )
    assert len(script.dialogues) == 1
    assert script.dialogues[0].text == "Hello Pyxis"
    assert script.styles["Default"].fontsize == 48.0


def test_validate_graph():
    core = PyxisCore()
    valid_graph = {
        "nodes": [
            {"id": "node_1", "type": "TextSplitter", "properties": {"mode": "words"}},
            {"id": "node_2", "type": "PositionEffect", "properties": {"x": 100, "y": 200}},
        ],
        "connections": [
            {"from": "node_1", "output": "output", "to": "node_2", "input": "input"}
        ]
    }
    result = core.validate(valid_graph)
    assert result.valid is True
    assert isinstance(result.errors, list)
    assert isinstance(result.warnings, list)


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli_main(["--version"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "pyxis-core 0.1.0" in captured.out or "pyxis-core 0.1.0" in captured.err


def test_cli_info(capsys):
    code = cli_main(["info"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Pyxis Core — Version 0.1.0" in captured.out
    assert "Clean Architecture Layers:" in captured.out

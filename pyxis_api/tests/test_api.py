# -*- coding: utf-8 -*-
import json
import os

import pytest
from fastapi.testclient import TestClient

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "Example_Simple_Effect.json")
ASS = """[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,0:00:05.00,0:00:10.00,Default,,0,0,0,,{\\k43}Ma{\\k65}ry {\\k44}te{\\k87}nia
"""


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PYXIS_WORKSPACE", str(tmp_path))
    (tmp_path / "effect_base.py").write_text('NAME = "@NAME@"\nSTYLE = @STYLE@  # @STYLE_TXT@\n', encoding="utf-8")
    from pyxis_api.main import app
    return TestClient(app)


@pytest.fixture()
def ass(tmp_path):
    p = tmp_path / "in.ass"
    p.write_text(ASS, encoding="utf-8")
    return str(p)


def graph():
    with open(TEMPLATE, encoding="utf-8") as fh:
        return json.load(fh)["graph"]


def test_health(client):
    r = client.get("/api/v1/health").json()
    assert r["status"] == "ok" and r["pyxis_core"]


def test_node_manifest(client):
    m = client.get("/api/v1/nodes/manifest").json()
    assert "Output" in m["system_nodes"]["System"] and m["data_nodes"]
    cats = client.get("/api/v1/nodes/categories").json()
    assert "Loops" in cats and "Main Loop" in cats["Loops"]


def test_validate_and_process(client, ass, tmp_path):
    v = client.post("/api/v1/graph/validate", json={"graph": graph()}).json()
    assert v["valid"] is True
    out = str(tmp_path / "out.ass")
    r = client.post("/api/v1/graph/process", json={"graph": graph(), "ass_path": ass, "output_path": out, "include_lines": True}).json()
    assert r["success"] and r["lines_count"] > 0 and r["lines"][0].startswith("Dialogue:")
    # regresion: el grafo debe llegar al motor CON sus enlaces; sin ellos salian lineas sin tags
    assert any("\\bord" in l and "\\t(" in l for l in r["lines"]), r["lines"][:3]
    # el Queue ID de los Output (aqui "Leadin", "Highlight"...) es solo agrupacion interna: Actor siempre en blanco
    assert {l.split(",", 9)[4] for l in r["lines"]} == {""}
    assert os.path.exists(out)
    assert client.post("/api/v1/graph/process", json={"graph": graph()}).status_code == 422


def test_process_progress_websocket(client, ass):
    with client.websocket_connect("/api/v1/graph/ws/progress") as ws:
        ws.send_json({"action": "start", "graph": graph(), "ass_path": ass})
        last = None
        while True:
            ev = ws.receive_json()
            last = ev
            if ev.get("phase") == "Done" and "success" in ev:
                break
        assert last["success"] and last["lines_count"] > 0


def test_templates_roundtrip(client):
    created = client.post("/api/v1/templates", json={"name": "api_test_tpl", "graph": graph()}).json()["id"]
    try:
        assert any(t["id"] == created for t in client.get("/api/v1/templates").json())
        got = client.get("/api/v1/templates/" + created).json()
        assert got["graph"]["nodes"]
    finally:
        assert client.delete("/api/v1/templates/" + created).status_code == 200
    assert client.get("/api/v1/templates/" + created).status_code == 404


def test_fx_library(client):
    kinds = {k["kind"]: k["count"] for k in client.get("/api/v1/fx/kinds").json()}
    assert kinds["LIfx"] > 1000
    page = client.get("/api/v1/fx", params={"kind": "HLfx", "limit": 5, "status": True}).json()
    assert page["total"] > 400 and len(page["items"]) == 5 and "supported" in page["items"][0]
    ok = client.get("/api/v1/fx", params={"kind": "HLfx", "only_supported": True, "limit": 3}).json()
    assert ok["total"] > 100 and all(i["supported"] for i in ok["items"])
    item = ok["items"][0]
    src = client.get("/api/v1/fx/%s/%s/source" % (item["kind"], item["name"]), params={"style": "Romaji"}).json()
    assert "def run(line, out):" in src["code"]
    assert client.get("/api/v1/fx/LIfx/no_existe/source").status_code == 404


def test_effect_scripts(client):
    assert client.post("/api/v1/effects", json={"name": "mi_fx", "style": "Romaji"}).status_code == 201
    code = client.get("/api/v1/effects/mi_fx").json()["code"]
    assert 'NAME = "mi_fx"' in code and 'STYLE = "Romaji"' in code
    assert client.post("/api/v1/effects", json={"name": "mi_fx"}).status_code == 409
    client.put("/api/v1/effects/mi_fx", json={"code": "x = 1\n"})
    assert client.get("/api/v1/effects/mi_fx").json()["code"] == "x = 1\n"
    assert [e["name"] for e in client.get("/api/v1/effects").json()] == ["mi_fx"]
    assert client.post("/api/v1/effects", json={"name": "../mal"}).status_code == 422
    assert client.delete("/api/v1/effects/mi_fx").status_code == 200
    r = client.post("/api/v1/effects", json={"name": "de_lib", "library_name": "ABC_Create_New_fx", "library_kind": "HLfx"})
    assert r.status_code == 201 and "def run(line, out):" in client.get("/api/v1/effects/de_lib").json()["code"]


def test_session(client, ass):
    assert client.get("/api/v1/session/info").status_code == 404
    s = client.post("/api/v1/session/open", json={"ass_path": ass}).json()
    assert s["lines_count"] == 1 and s["styles"][0]["name"] == "Default" and s["resolution"]["play_res_x"] == 1280
    assert client.get("/api/v1/session/info").json()["ass_path"] == ass


def test_graph_cache_per_key(client, ass):
    assert client.get("/api/v1/cache/graph", params={"key": "Romaji"}).status_code == 404
    assert client.put("/api/v1/cache/graph", json={"key": "Romaji", "graph": graph()}).json() == {"saved": "Romaji"}
    got = client.get("/api/v1/cache/graph", params={"key": "Romaji"}).json()
    assert got["graph"]["nodes"] and got["saved_at"]
    assert client.get("/api/v1/cache/graph", params={"key": "Otro"}).status_code == 404    # otra clave: separada
    s = client.post("/api/v1/session/open", json={"ass_path": ass, "style": "Romaji"}).json()
    assert s["style"] == "Romaji"
    client.delete("/api/v1/cache/graph", params={"key": "Romaji"})
    assert client.get("/api/v1/cache/graph", params={"key": "Romaji"}).status_code == 404


def test_builtin_template_char_fade_jump(client, ass):
    """Plantilla de sistema equivalente al efecto Python base: 3 capas por caracter."""
    ids = {t["id"]: t for t in client.get("/api/v1/templates").json()}
    tid = "20261120_char_fade_jump"
    assert tid in ids and ids[tid]["node_count"] == 13 and ids[tid]["category"] == "Karaoke"
    g = client.get("/api/v1/templates/" + tid).json()["graph"]
    assert client.post("/api/v1/graph/validate", json={"graph": g}).json()["valid"] is True
    r = client.post("/api/v1/graph/process", json={"graph": g, "ass_path": ass, "include_lines": True}).json()
    assert r["success"], r.get("error")
    rows = [l.strip().split(",", 9) for l in r["lines"]]
    assert {f[4] for f in rows} == {""}, "el campo Actor debe quedar vacio"
    # sin nombres de cola, las capas se distinguen por su contenido: \fad(500,0) / \fad(0,400) / \move
    kind = lambda f: "in" if "\\fad(500,0)" in f[9] else "out" if "\\fad(0,400)" in f[9] else "jump"
    by_queue = {}
    for f in rows:
        by_queue.setdefault(kind(f), []).append(f)
    assert sorted(by_queue) == ["in", "jump", "out"]
    assert {len(v) for v in by_queue.values()} == {9}                      # una linea por caracter y capa
    assert {f[0] for f in by_queue["jump"]} == {"Dialogue: 3"} and {f[0] for f in by_queue["in"]} == {"Dialogue: 2"}
    text = "\n".join(r["lines"])
    assert "R(" not in text and "fx." not in text                          # aleatorios y expresiones ya evaluados
    assert "\\move(" in by_queue["jump"][0][9]
    # tiempos: la entrada termina donde empieza la silaba, la salida empieza donde acaba y el salto dura la silaba
    assert by_queue["in"][0][1] < by_queue["in"][0][2] == "0:00:05.00"
    assert by_queue["out"][0][1] == "0:00:05.43"
    assert (by_queue["jump"][0][1], by_queue["jump"][0][2]) == ("0:00:05.00", "0:00:05.43")


TWO_STYLES = ASS.replace("Style: Default,Arial", "Style: Otro,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\nStyle: Default,Arial") + \
    "Dialogue: 1,0:00:20.00,0:00:25.00,Otro,,0,0,0,,{\\k43}ab{\\k65}cd\n"


def test_process_filters_by_style_and_remaps_used_indices(client, tmp_path):
    src = tmp_path / "two.ass"
    src.write_text(TWO_STYLES, encoding="utf-8")
    out = str(tmp_path / "out.ass")
    r = client.post("/api/v1/graph/process", json={"graph": graph(), "ass_path": str(src), "output_path": out,
                                                    "style": "Otro", "include_lines": True}).json()
    assert r["success"], r.get("error")
    # solo se procesa la linea del estilo "Otro": mismo resultado que procesar un archivo que contenga SOLO esa linea
    only = tmp_path / "only.ass"
    only.write_text(TWO_STYLES.replace("Dialogue: 1,0:00:05.00,0:00:10.00,Default", "Comment: 1,0:00:05.00,0:00:10.00,Default"), encoding="utf-8")
    ref = client.post("/api/v1/graph/process", json={"graph": graph(), "ass_path": str(only)}).json()
    assert r["lines_count"] == ref["lines_count"] > 0
    assert r["used_indices"] == [2]                                             # indice de la linea ORIGINAL
    text = open(out, encoding="utf-8").read()
    assert text.startswith("#PYXIS_USED_IDX: 2"), text[:60]
    assert "Otro" in text and "Mary" not in text
    both = client.post("/api/v1/graph/process", json={"graph": graph(), "ass_path": str(src)}).json()
    assert both["lines_count"] > r["lines_count"]                                    # sin estilo: todas


def test_session_choice(client, ass):
    client.post("/api/v1/session/open", json={"ass_path": ass})
    assert client.get("/api/v1/session/choice").json() == {"mode": None, "style": None}
    assert client.post("/api/v1/session/choice", json={"mode": "script", "style": "Default"}).json() == {"mode": "script", "style": "Default"}
    assert client.get("/api/v1/session/choice").json()["mode"] == "script"
    assert client.get("/api/v1/session/info").json()["style"] == "Default"
    assert client.post("/api/v1/session/choice", json={"mode": "otra"}).status_code == 422

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

# tests/test_shape_slicer_all_modes_preview.py
"""Suite de pruebas unitarias exhaustivas para Shape Slicer.
Verifica:
1. Precision matematica y paridad de centros Bounding Box (cx, cy) en todos los modos de corte.
2. Cobertura de area y reconstruccion booleana de las piezas cortadas.
3. Evaluacion dinamica en GraphEngine para todos los tipos de anclaje (piezas, rel, abs, pos, org) y modos de salida (Shape, Clip, iClip).
4. Simulacion completa de previsualizacion (generate_preview_ass / Preview Node).
"""

import os
import shutil
import tempfile
import unittest
import pyclipper

from clipper_engine import ClipperEngine
from node_engine import GraphEngine
from main import PyxisAPI


class TestShapeSlicerAllModesPreview(unittest.TestCase):

    def setUp(self):
        self.sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        self.temp_dir = tempfile.mkdtemp()
        self.appdata_mock = os.path.join(self.temp_dir, "appdata")
        os.makedirs(self.appdata_mock, exist_ok=True)
        self.original_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = self.appdata_mock

        self.pyxis_dir = os.path.join(self.appdata_mock, "PyxisNodes")
        os.makedirs(self.pyxis_dir, exist_ok=True)
        self.user_base_path = os.path.join(self.pyxis_dir, "preview_base.ass")

        base_ass = (
            "[Script Info]\n"
            "Title: Preview Slicer Test\n"
            "PlayResX: 1920\n"
            "PlayResY: 1080\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,5,10,10,10,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:02.00,0:00:06.00,Default,,0,0,0,,{\\k100}Test Line\n"
        )
        with open(self.user_base_path, "w", encoding="utf-8") as f:
            f.write(base_ass)

        self.api = PyxisAPI(
            temp_ass=os.path.join(self.temp_dir, "temp.ass"),
            result_file=os.path.join(self.temp_dir, "res.txt"),
            session_file=os.path.join(self.temp_dir, "sess.json")
        )

    def tearDown(self):
        if self.original_appdata is not None:
            os.environ["APPDATA"] = self.original_appdata
        elif "APPDATA" in os.environ:
            del os.environ["APPDATA"]
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except OSError:
            pass

    def test_piece_centers_match_bounding_box_in_all_modes(self):
        """Verifica que cx y cy coincidan exactamente con el centro del Bounding Box de cada pieza."""
        modes = [
            ("Rejilla 1D/2D", {"cols": 3, "rows": 3}),
            ("hex", {"size_x": 30}),
            ("tri", {"size_x": 30}),
            ("dia", {"size_x": 30}),
            ("ring", {"size_x": 20}),
            ("ray", {"size_x": 45}),
        ]
        for mode_name, kwargs in modes:
            pieces = ClipperEngine.slice_grid(self.sq, engine_mode=mode_name, **kwargs)
            self.assertGreater(len(pieces), 0, f"Modo {mode_name} no genero piezas")
            for i, p in enumerate(pieces):
                cnts = ClipperEngine.parse_assdraw(p["code"])
                _, _, _, _, pcx, pcy, _, _ = ClipperEngine.get_bbox(cnts)
                self.assertAlmostEqual(
                    p["cx"], round(pcx, 2), delta=0.02,
                    msg=f"Modo {mode_name} pieza {i}: cx={p['cx']} != bbox_cx={round(pcx, 2)}"
                )
                self.assertAlmostEqual(
                    p["cy"], round(pcy, 2), delta=0.02,
                    msg=f"Modo {mode_name} pieza {i}: cy={p['cy']} != bbox_cy={round(pcy, 2)}"
                )

    def test_area_coverage_of_reconstructed_pieces(self):
        """Verifica que la union booleana de todas las piezas reconstruya la figura base."""
        scale = 10000.0

        def assdraw_to_poly(ass_str):
            cnts = ClipperEngine.parse_assdraw(ass_str)
            paths = []
            for c in cnts:
                if len(c) >= 3:
                    paths.append([[int(round(pt[0] * scale)), int(round(pt[1] * scale))] for pt in c])
            return paths

        orig_poly = assdraw_to_poly(self.sq)
        orig_area = sum(abs(pyclipper.Area(p)) for p in orig_poly) / (scale * scale)

        modes = [
            ("Rejilla 1D/2D", {"cols": 2, "rows": 2}),
            ("hex", {"size_x": 30}),
            ("tri", {"size_x": 30}),
            ("dia", {"size_x": 30}),
            ("ray", {"size_x": 45}),
        ]
        for mode_name, kwargs in modes:
            pieces = ClipperEngine.slice_grid(self.sq, engine_mode=mode_name, **kwargs)
            pc_union = pyclipper.Pyclipper()
            for p in pieces:
                p_paths = assdraw_to_poly(p["code"])
                for path in p_paths:
                    pc_union.AddPath(path, pyclipper.PT_SUBJECT, True)
            union_res = pc_union.Execute(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
            union_area = sum(abs(pyclipper.Area(p)) for p in union_res) / (scale * scale)
            coverage = (union_area / orig_area) * 100.0
            self.assertAlmostEqual(coverage, 100.0, delta=0.5, msg=f"Cobertura deficiente en {mode_name}: {coverage:.2f}%")

    def test_preview_node_simulation_all_modes_and_anchors(self):
        """Simula la previsualizacion completa en PyxisAPI con todos los modos y anclajes."""
        modes_to_test = [
            ("Rejilla 1D/2D", {"cols": "2", "rows": "2"}),
            ("hex", {"size_x": "30"}),
            ("tri", {"size_x": "30"}),
            ("dia", {"size_x": "30"}),
            ("ring", {"size_x": "20"}),
            ("ray", {"size_x": "45"}),
        ]
        anchors = ["piezas", "rel", "abs", "pos", "org"]
        output_types = ["Shape", "Clip", "iClip"]

        for mode_name, extra_props in modes_to_test:
            for anchor in anchors:
                for out_type in output_types:
                    graph_props = {
                        "shape": self.sq,
                        "anchor": anchor,
                        "out_mode": out_type,
                        "modo": mode_name,
                    }
                    graph_props.update(extra_props)
                    graph = {
                        "nodes": [
                            {
                                "id": 1,
                                "type": "Shape/Shape Slicer",
                                "properties": graph_props,
                                "inputs": [],
                                "outputs": [
                                    {"name": "Piece", "type": "string", "links": [101]},
                                    {"name": "X", "type": "number", "links": []},
                                    {"name": "Y", "type": "number", "links": []},
                                    {"name": "Col", "type": "number", "links": []},
                                    {"name": "Row", "type": "number", "links": []},
                                ]
                            },
                            {
                                "id": 2,
                                "type": "System/Output",
                                "properties": {"apply_to": "All Lines", "queue_id": "slicer_test"},
                                "inputs": [
                                    {"name": "Loop / Domain", "type": "loop", "link": None},
                                    {"name": "Layer", "type": "number", "link": None},
                                    {"name": "Start Time", "type": "number", "link": None},
                                    {"name": "End Time", "type": "number", "link": None},
                                    {"name": "Tags", "type": "string", "link": None},
                                    {"name": "Return", "type": "string", "link": 101}
                                ],
                                "outputs": [{"name": "Preview", "type": "preview", "links": []}]
                            }
                        ],
                        "links": [[101, 1, 0, 2, 5, "string"]]
                    }
                    res = self.api.generate_preview_ass(payload=graph, target_output_id=["slicer_test"])
                    self.assertTrue(res.get("success"), f"Fallo al generar preview en {mode_name}/{anchor}/{out_type}: {res.get('error')}")
                    dialogue_lines = [l for l in res.get("content", "").splitlines() if l.startswith("Dialogue:")]
                    self.assertGreater(len(dialogue_lines), 0, f"No se generaron lineas para {mode_name}/{anchor}/{out_type}")

                    first_line = dialogue_lines[0]
                    if out_type == "Clip":
                        self.assertIn("\\clip(", first_line)
                    elif out_type == "iClip":
                        self.assertIn("\\iclip(", first_line)
                    else:
                        self.assertTrue("{\\p1}" in first_line or "m " in first_line)


if __name__ == '__main__':
    unittest.main()

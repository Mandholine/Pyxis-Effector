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

# test_user_preview_base.py
"""Suite de pruebas unitarias para la fuente de verdad preview_base.ass del usuario.

Verifica:
1. Preservación del preview_base.ass del usuario en %APPDATA%/PyxisNodes/preview_base.ass.
2. Escaneo una sola vez al arrancar (cached).
3. Regla del previsualizador: 2s antes y 2s después.
4. Detección de video/audio "dummy" para usar fallback seguro.
"""

import os
import shutil
import tempfile
import unittest
from main import PyxisAPI


class TestUserPreviewBase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.appdata_mock = os.path.join(self.temp_dir, "appdata")
        os.makedirs(self.appdata_mock, exist_ok=True)
        self.original_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = self.appdata_mock

        self.pyxis_dir = os.path.join(self.appdata_mock, "PyxisNodes")
        os.makedirs(self.pyxis_dir, exist_ok=True)
        self.user_base_path = os.path.join(self.pyxis_dir, "preview_base.ass")

    def tearDown(self):
        if self.original_appdata is not None:
            os.environ["APPDATA"] = self.original_appdata
        elif "APPDATA" in os.environ:
            del os.environ["APPDATA"]
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except OSError:
            pass

    def test_preserve_user_preview_base(self):
        # Crear un preview_base.ass personalizado en AppData
        custom_content = (
            "[Script Info]\n"
            "Title: Custom Test Base\n"
            "PlayResX: 1920\n"
            "PlayResY: 1080\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: CustomStyle,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:05.00,0:00:10.00,CustomStyle,,0,0,0,,{\\k50}Ma{\\k50}ry\n"
        )
        with open(self.user_base_path, "w", encoding="utf-8") as f:
            f.write(custom_content)

        api = PyxisAPI(
            temp_ass=os.path.join(self.temp_dir, "temp.ass"),
            result_file=os.path.join(self.temp_dir, "res.txt"),
            session_file=os.path.join(self.temp_dir, "sess.json")
        )

        # Verificar que NO se sobrescribió y leyó 1920x1080
        info = api._cached_preview_base_info
        self.assertEqual(info["res_x"], 1920)
        self.assertEqual(info["res_y"], 1080)

        with open(self.user_base_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertIn("Title: Custom Test Base", read_content)

    def test_2s_before_and_2s_after_padding(self):
        # Diálogo de 5.0s (5000ms) a 10.0s (10000ms)
        custom_content = (
            "[Script Info]\n"
            "PlayResX: 1280\n"
            "PlayResY: 720\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:05.00,0:00:10.00,Default,,0,0,0,,{\\k50}Test\n"
        )
        with open(self.user_base_path, "w", encoding="utf-8") as f:
            f.write(custom_content)

        api = PyxisAPI(
            temp_ass=os.path.join(self.temp_dir, "temp.ass"),
            result_file=os.path.join(self.temp_dir, "res.txt"),
            session_file=os.path.join(self.temp_dir, "sess.json")
        )

        info = api._cached_preview_base_info
        # 5s - 2s = 3s de inicio (-ss 3.0)
        self.assertAlmostEqual(info["render_start_sec"], 3.0, places=2)
        # 10s + 2s = 12s fin. Duración = 12s - 3s = 9s (-t 9.0)
        self.assertAlmostEqual(info["render_duration_sec"], 9.0, places=2)

    def test_dummy_video_audio_detection(self):
        # Archivos dummy escritos por Aegisub
        custom_content = (
            "[Script Info]\n"
            "PlayResX: 1280\n"
            "PlayResY: 720\n"
            "Audio File: dummy-audio:silence?sr=44100&bd=16&ch=1&ln=396900000\n"
            "Video File: ?dummy:23.976000:361:1000:260:150:150:150:c\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{\\k50}Dummy Test\n"
        )
        with open(self.user_base_path, "w", encoding="utf-8") as f:
            f.write(custom_content)

        api = PyxisAPI(
            temp_ass=os.path.join(self.temp_dir, "temp.ass"),
            result_file=os.path.join(self.temp_dir, "res.txt"),
            session_file=os.path.join(self.temp_dir, "sess.json")
        )

        info = api._cached_preview_base_info
        # Deben filtrarse como None para forzar el fallback seguro
        self.assertIsNone(info["video_file"])
        self.assertIsNone(info["audio_file"])


    def test_aegisub_project_garbage_and_dummy_parsing(self):
        from ass_parser import ASSParser
        dummy_ass = os.path.join(self.temp_dir, "test_dummy.ass")
        content = (
            "[Script Info]\n"
            "PlayResX: 1001\n"
            "PlayResY: 259\n\n"
            "[Aegisub Project Garbage]\n"
            "Last Style Storage: Default\n"
            "Audio File: dummy-audio:silence?sr=44100&bd=16&ch=1&ln=396900000\n"
            "Video File: ?dummy:23.976000:361:1000:260:150:150:150:c\n"
            "Video AR Value: 3.846154\n"
            "Video Position: 120\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,65,&H00FFFFFF,&H000000FF,&H007A3419,&H007A1C42,0,0,0,0,100,100,0,0,1,2,2,2,10,10,100,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:05.00,0:00:10.00,Default,,0,0,0,,{\\k50}Test\n"
        )
        with open(dummy_ass, "w", encoding="utf-8") as f:
            f.write(content)

        parsed = ASSParser.read_file(dummy_ass)

        # 1. Comprobar normalización a número par
        self.assertEqual(parsed.res_x, 1000)  # 1001 -> 1000
        self.assertEqual(parsed.res_y, 258)   # 259 -> 258

        # 2. Comprobar metadatos de garbage
        self.assertEqual(parsed.video_pos, 120)
        self.assertAlmostEqual(parsed.video_ar, 3.846154, places=4)
        self.assertTrue(parsed.is_dummy_video)
        self.assertTrue(parsed.is_dummy_audio)

        # 3. Comprobar decodificación de vídeo dummy
        self.assertEqual(parsed.dummy_info["fps"], 23.976)
        self.assertEqual(parsed.dummy_info["frames"], 361)
        self.assertEqual(parsed.dummy_info["width"], 1000)
        self.assertEqual(parsed.dummy_info["height"], 260)
        self.assertEqual(parsed.dummy_info["r"], 150)
        self.assertEqual(parsed.dummy_info["g"], 150)
        self.assertEqual(parsed.dummy_info["b"], 150)
        self.assertEqual(parsed.dummy_info["color_hex"], "969696")
        self.assertEqual(parsed.dummy_info["pattern"], "c")

        # 4. Comprobar cálculo de frame_dur a partir de FPS dummy
        self.assertAlmostEqual(parsed.frame_dur, 1000.0 / 23.976, places=3)

    def test_aegisub_project_garbage_real_media(self):
        from ass_parser import ASSParser
        real_media_ass = os.path.join(self.temp_dir, "test_real.ass")
        content = (
            "[Script Info]\n"
            "PlayResX: 1920\n"
            "PlayResY: 1080\n\n"
            "[Aegisub Project Garbage]\n"
            "Audio File: C:/Videos/episode_01.mkv\n"
            "Video File: C:/Videos/episode_01.mkv\n"
            "Video AR Value: 1.777778\n"
            "Video Position: 5400\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,65,&H00FFFFFF,&H000000FF,&H007A3419,&H007A1C42,0,0,0,0,100,100,0,0,1,2,2,2,10,10,100,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:05.00,0:00:10.00,Default,,0,0,0,,{\\k50}Test\n"
        )
        with open(real_media_ass, "w", encoding="utf-8") as f:
            f.write(content)

        parsed = ASSParser.read_file(real_media_ass)

        self.assertEqual(parsed.res_x, 1920)
        self.assertEqual(parsed.res_y, 1080)
        self.assertEqual(parsed.audio_file, "C:/Videos/episode_01.mkv")
        self.assertEqual(parsed.video_file, "C:/Videos/episode_01.mkv")
        self.assertFalse(parsed.is_dummy_video)
        self.assertFalse(parsed.is_dummy_audio)
        self.assertEqual(parsed.video_pos, 5400)
        self.assertAlmostEqual(parsed.video_ar, 1.777778, places=4)


    def test_2s_clip_timing_and_time_shift_helpers(self):
        # 1. Comprobar desplazamiento de timestamp individual
        shifted = PyxisAPI._shift_ass_timestamp("0:00:05.00", 3000)
        self.assertEqual(shifted, "0:00:02.00")

        shifted_clamped = PyxisAPI._shift_ass_timestamp("0:00:01.00", 3000)
        self.assertEqual(shifted_clamped, "0:00:00.00")

        # 2. Comprobar desplazamiento de línea de diálogo
        raw_dlg = "Dialogue: 0,0:00:05.00,0:00:10.00,Default,,0,0,0,,{\\k50}Mary\n"
        shifted_dlg = PyxisAPI._shift_ass_line(raw_dlg, 3000)
        self.assertIn("0:00:02.00,0:00:07.00", shifted_dlg)
        self.assertTrue(shifted_dlg.startswith("Dialogue: "))

        # 3. Comprobar desplazamiento de línea de comentario
        raw_com = "Comment: 1,0:00:05.00,0:00:10.00,Default,,0,0,0,,{\\k50}Mary"
        shifted_com = PyxisAPI._shift_ass_line(raw_com, 3000)
        self.assertIn("0:00:02.00,0:00:07.00", shifted_com)
        self.assertTrue(shifted_com.startswith("Comment: "))

    def test_get_preview_info_and_smart_media_cache(self):
        # Diálogo de 5.0s a 12.0s en 1920x1080
        custom_content = (
            "[Script Info]\n"
            "PlayResX: 1920\n"
            "PlayResY: 1080\n\n"
            "[Aegisub Project Garbage]\n"
            "Video File: ?dummy:24.000000:720:1920:1080:40:40:40:c\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,65,&H00FFFFFF,&H000000FF,&H007A3419,&H007A1C42,0,0,0,0,100,100,0,0,1,2,2,2,10,10,100,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:05.00,0:00:12.00,Default,,0,0,0,,{\\k50}Test Clip\n"
        )
        with open(self.user_base_path, "w", encoding="utf-8") as f:
            f.write(custom_content)

        api = PyxisAPI(
            temp_ass=os.path.join(self.temp_dir, "temp.ass"),
            result_file=os.path.join(self.temp_dir, "res.txt"),
            session_file=os.path.join(self.temp_dir, "sess.json")
        )

        # 1. Comprobar metadata de get_preview_info
        info = api.get_preview_info()
        self.assertEqual(info["res_x"], 1920)
        self.assertEqual(info["res_y"], 1080)
        self.assertAlmostEqual(info["aspect_ratio"], 1920 / 1080, places=4)
        self.assertEqual(info["fps"], 24.0)
        # clip_start: 5.0 - 2.0 = 3.0s
        self.assertAlmostEqual(info["clip_start_sec"], 3.0, places=2)
        # clip_end: 12.0 + 2.0 = 14.0s
        self.assertAlmostEqual(info["clip_end_sec"], 14.0, places=2)
        # clip_duration: 14.0 - 3.0 = 11.0s
        self.assertAlmostEqual(info["clip_duration_sec"], 11.0, places=2)

        # 2. Comprobar que get_initial_base_ass devuelve la línea desplazada (inicia en 2.0s)
        initial_ass = api.get_initial_base_ass()
        self.assertIn("0:00:02.00,0:00:09.00", initial_ass)

        # 3. Comprobar que _ensure_preview_media_clip generó un archivo MP4 válido
        cached_clip = api._cached_preview_base_info.get("clip_path")
        self.assertTrue(cached_clip and "preview_bg_dummy_" in cached_clip.replace("\\", "/") and "1920x1080" in cached_clip)

        # 4. Probar que una segunda llamada es un Cache Hit instantáneo
        recheck_clip = api._ensure_preview_media_clip(api._cached_preview_base_info)
        self.assertEqual(cached_clip, recheck_clip)


    def test_dynamic_font_lookup(self):
        # Crear un preview_base.ass con fuente Arial
        custom_content = (
            "[Script Info]\n"
            "PlayResX: 1280\n"
            "PlayResY: 720\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,65,&H00FFFFFF,&H000000FF,&H007A3419,&H007A1C42,0,0,0,0,100,100,0,0,1,2,2,2,10,10,100,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,{\\k50}Font Test\n"
        )
        with open(self.user_base_path, "w", encoding="utf-8") as f:
            f.write(custom_content)

        api = PyxisAPI(
            temp_ass=os.path.join(self.temp_dir, "temp.ass"),
            result_file=os.path.join(self.temp_dir, "res.txt"),
            session_file=os.path.join(self.temp_dir, "sess.json")
        )

        font_url = api.get_preview_font_data_url()
        self.assertTrue(font_url.startswith("data:font/ttf;base64,") or font_url.startswith("data:font/otf;base64,"))
        self.assertGreater(len(font_url), 100)

    def test_render_preview_hardsub_on_cut_clip(self):
        custom_content = (
            "[Script Info]\n"
            "PlayResX: 640\n"
            "PlayResY: 360\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,30,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k50}Hardsub Test\n"
        )
        with open(self.user_base_path, "w", encoding="utf-8") as f:
            f.write(custom_content)

        api = PyxisAPI(
            temp_ass=os.path.join(self.temp_dir, "temp.ass"),
            result_file=os.path.join(self.temp_dir, "res.txt"),
            session_file=os.path.join(self.temp_dir, "sess.json")
        )

        target_out_mp4 = os.path.join(self.temp_dir, "output_hardsub.mp4")
        api._select_save_video_path = lambda default_filename=None: target_out_mp4

        res = api.render_preview_hardsub(payload={}, target_output_id=None)
        if res.get("error") and "subtitles" in str(res.get("error")).lower():
            self.assertIn("FFmpeg", res["error"])
        else:
            self.assertTrue(res.get("success"), f"Fallo al renderizar hardsub: {res}")
            self.assertEqual(res.get("saved_path"), target_out_mp4)
            self.assertTrue(os.path.exists(target_out_mp4))
            self.assertGreater(os.path.getsize(target_out_mp4), 500)

    def test_generate_preview_ass_with_fx_graph(self):
        custom_content = (
            "[Script Info]\n"
            "PlayResX: 1280\n"
            "PlayResY: 720\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            "Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            "Dialogue: 0,0:00:04.00,0:00:08.00,Default,,0,0,0,,{\\k40}Hello {\\k40}World\n"
        )
        with open(self.user_base_path, "w", encoding="utf-8") as f:
            f.write(custom_content)

        api = PyxisAPI(
            temp_ass=os.path.join(self.temp_dir, "temp.ass"),
            result_file=os.path.join(self.temp_dir, "res.txt"),
            session_file=os.path.join(self.temp_dir, "sess.json")
        )

        # Grafo con nodo Salida y bucle sílaba
        graph = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Bucles/Sílabas",
                    "properties": {},
                    "outputs": [{"name": "Loop", "type": "loop", "links": [101]}]
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {
                        "apply_to": "Sel. Lines",
                        "queue_id": "glow_layer"
                    },
                    "inputs": [
                        {"name": "Loop / Domain", "type": "loop", "link": 101},
                        {"name": "Layer", "type": "number", "link": None},
                        {"name": "Start Time", "type": "number", "link": None},
                        {"name": "End Time", "type": "number", "link": None},
                        {"name": "Tags", "type": "string", "link": None},
                        {"name": "Return", "type": "string", "link": None}
                    ],
                    "outputs": [{"name": "Preview", "type": "preview", "links": []}]
                }
            ],
            "links": [
                [101, 1, 0, 2, 0, "loop"]
            ]
        }

        # 1. Petición con target_output_id = ['glow_layer']
        res = api.generate_preview_ass(payload=graph, target_output_id=["glow_layer"])
        self.assertTrue(res.get("success"))
        ass_content = res.get("content")
        self.assertIn("Comment: 0,0:00:02.00,0:00:06.00,Default", ass_content)  # Diálogo base original comentado y shifted
        self.assertIn("Dialogue: 0,0:00:02.00,", ass_content)  # Línea generada desplazada
        self.assertIn("Hello", ass_content)

        # 2. Petición con target_output_id = ['all']
        res_all = api.generate_preview_ass(payload=graph, target_output_id=["all"])
        self.assertTrue(res_all.get("success"))
        self.assertIn("Dialogue: 0,0:00:02.00,", res_all.get("content"))

    def test_has_aegisub_session_flag(self):
        # 1. Cuando temp_ass no existe
        api_no_aegi = PyxisAPI(
            temp_ass=os.path.join(self.temp_dir, "non_existent.ass"),
            result_file=os.path.join(self.temp_dir, "res.txt"),
            session_file=os.path.join(self.temp_dir, "sess.json")
        )
        info_no = api_no_aegi.get_preview_info(source="base")
        self.assertFalse(info_no.get("has_aegisub"))

        # 2. Cuando temp_ass existe con diálogos
        temp_aegi = os.path.join(self.temp_dir, "active_aegisub.ass")
        with open(temp_aegi, "w", encoding="utf-8") as f:
            f.write(
                "[Script Info]\nPlayResX: 1920\nPlayResY: 1080\n\n"
                "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                "Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n"
                "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
                "Dialogue: 0,0:00:05.00,0:00:08.00,Default,,0,0,0,,{\\k30}Aegisub {\\k30}Line\n"
            )
        api_aegi = PyxisAPI(
            temp_ass=temp_aegi,
            result_file=os.path.join(self.temp_dir, "res.txt"),
            session_file=os.path.join(self.temp_dir, "sess.json")
        )
        info_yes = api_aegi.get_preview_info(source="base")
        self.assertTrue(info_yes.get("has_aegisub"))

        # Consulta directa a source="aegisub"
        info_aegi_src = api_aegi.get_preview_info(source="aegisub")
        self.assertTrue(info_aegi_src.get("has_aegisub"))
        self.assertEqual(info_aegi_src.get("source"), "aegisub")
        self.assertEqual(info_aegi_src.get("res_x"), 1920)
        self.assertEqual(info_aegi_src.get("res_y"), 1080)

    def test_mayor_extension_all_lines_vs_selected_lines(self):
        # Archivo con 3 líneas:
        # Línea 1: 0:00:01.00 a 0:00:03.00 (1000ms a 3000ms) - No seleccionada
        # Línea 2: 0:00:06.00 a 0:00:08.00 (6000ms a 8000ms) - Seleccionada
        # Línea 3: 0:00:12.00 a 0:00:14.00 (12000ms a 14000ms) - No seleccionada
        temp_aegi = os.path.join(self.temp_dir, "multi_line_aegi.ass")
        with open(temp_aegi, "w", encoding="utf-8") as f:
            f.write(
                "[Script Info]\nPlayResX: 1920\nPlayResY: 1080\n\n"
                "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                "Style: Default,Arial,60,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n"
                "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
                "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k200}Line 1\n"
                "Dialogue: 0,0:00:06.00,0:00:08.00,Default,,0,0,0,,{\\k200}Line 2\n"
                "Dialogue: 0,0:00:12.00,0:00:14.00,Default,,0,0,0,,{\\k200}Line 3\n"
            )

        api = PyxisAPI(
            temp_ass=temp_aegi,
            result_file=os.path.join(self.temp_dir, "res.txt"),
            session_file=os.path.join(self.temp_dir, "sess.json")
        )
        # Parsear e inyectar selección en la Línea 2
        from ass_parser import ASSParser
        parsed = ASSParser.read_file(temp_aegi)
        if isinstance(parsed.dialogues[0], dict):
            parsed.dialogues[0]['is_selected'] = False
            parsed.dialogues[1]['is_selected'] = True
            parsed.dialogues[2]['is_selected'] = False
        else:
            parsed.dialogues[0].is_selected = False
            parsed.dialogues[1].is_selected = True
            parsed.dialogues[2].is_selected = False
        api._cached_aegisub_info = None

        # Grafo 1: Salida A con "Selected Lines"
        graph_selected_only = {
            "nodes": [
                {
                    "id": 1,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines", "output_id": "out_sel"}
                }
            ]
        }
        # Rango con Selected Lines: Línea 2 (6s-8s) -> 2s antes (4s) a 2s después (10s)
        min_st, max_et, clip_st, clip_et, clip_dur, shift_ms = api._calculate_effective_dialogue_range(
            parsed.dialogues, payload=graph_selected_only, target_output_id=["out_sel"]
        )
        self.assertEqual(min_st, 6000)
        self.assertEqual(max_et, 8000)
        self.assertEqual(clip_st, 4.0)
        self.assertEqual(clip_et, 10.0)
        self.assertEqual(clip_dur, 6.0)
        self.assertEqual(shift_ms, 4000)

        # Grafo 2: Salida B con "All Lines"
        graph_all_lines = {
            "nodes": [
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines", "output_id": "out_all"}
                }
            ]
        }
        # Rango con All Lines: Línea 1 a 3 (1s-14s) -> 2s antes (0s) a 2s después (16s)
        min_st_all, max_et_all, clip_st_all, clip_et_all, clip_dur_all, shift_ms_all = api._calculate_effective_dialogue_range(
            parsed.dialogues, payload=graph_all_lines, target_output_id=["out_all"]
        )
        self.assertEqual(min_st_all, 1000)
        self.assertEqual(max_et_all, 14000)
        self.assertEqual(clip_st_all, 0.0)
        self.assertEqual(clip_et_all, 16.0)
        self.assertEqual(clip_dur_all, 16.0)
        self.assertEqual(shift_ms_all, 0)

        # Grafo 3: Salida 1 (Selected) + Salida 2 (All Lines) -> Prima la MAYOR EXTENSIÓN (All Lines)
        graph_multi_outputs = {
            "nodes": [
                {
                    "id": 1,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines", "output_id": "out_sel"}
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {"apply_to": "All Lines", "output_id": "out_all"}
                }
            ]
        }
        min_st_multi, max_et_multi, clip_st_multi, clip_et_multi, clip_dur_multi, shift_ms_multi = api._calculate_effective_dialogue_range(
            parsed.dialogues, payload=graph_multi_outputs, target_output_id=["out_sel", "out_all"]
        )
        self.assertEqual(min_st_multi, 1000)
        self.assertEqual(max_et_multi, 14000)
        self.assertEqual(clip_st_multi, 0.0)
        self.assertEqual(clip_et_multi, 16.0)
        self.assertEqual(clip_dur_multi, 16.0)

    def test_single_output_selected_lines_only(self):
        """Verifica que con 1 sola Salida en modo 'Sel. Lines', solo se generen efectos para las líneas seleccionadas (MP y SP)."""
        from node_engine import GraphEngine
        graph_single_sel = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Output",
                    "title": "Output",
                    "properties": {"apply_to": "Sel. Lines", "queue_id": "out"},
                    "inputs": [{"name": "In", "link": 10}]
                },
                {
                    "id": 2,
                    "type": "Text",
                    "title": "Text",
                    "properties": {"text": "FX {!\\\\pos($x,$y)!}"},
                    "outputs": [{"name": "Out", "links": [10]}]
                }
            ],
            "links": [
                [10, 2, 0, 1, 0, "string"]
            ]
        }

        # 4 líneas: Solo la línea 2 (índice 1) está seleccionada
        dialogues = [
            {"raw": "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Línea 1 No Sel", "metrics": None},
            {"raw": "Dialogue: 0,0:00:04.00,0:00:06.00,Default,,0,0,0,,Línea2_SELECCIONADA", "metrics": {"sel": 1, "h": 30}},
            {"raw": "Dialogue: 0,0:00:07.00,0:00:09.00,Default,,0,0,0,,Línea 3 No Sel", "metrics": None},
            {"raw": "Dialogue: 0,0:00:10.00,0:00:12.00,Default,,0,0,0,,Línea 4 No Sel", "metrics": None},
        ]
        styles = {"Default": {}}

        # Multiprocessing
        engine_mp = GraphEngine(graph_single_sel, 1280, 720, 41.7)
        engine_mp.target_output_id = [1]
        lines_mp = engine_mp.process(dialogues, styles, use_multiprocessing=True)
        self.assertEqual(len(lines_mp), 1, f"Se esperaba 1 sola línea generada en MP pero se obtuvieron {len(lines_mp)}")
        self.assertIn("Línea2_SELECCIONADA", lines_mp[0])

        # Single-process
        engine_sp = GraphEngine(graph_single_sel, 1280, 720, 41.7)
        engine_sp.target_output_id = [1]
        lines_sp = engine_sp.process(dialogues, styles, use_multiprocessing=False)
        self.assertEqual(len(lines_sp), 1, f"Se esperaba 1 sola línea generada en SP pero se obtuvieron {len(lines_sp)}")
        self.assertIn("Línea2_SELECCIONADA", lines_sp[0])

    def test_switch_apply_to_selected_and_all_lines_dynamic_range(self):
        """Verifica que get_preview_info recalcule dinámicamente el rango al cambiar apply_to de Selected Lines a All Lines."""
        import tempfile
        from main import PyxisAPI

        ass_content = """[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,50,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Comment: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,PyxisMetrics,sel=1
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k20}Lí{\\k30}nea 1 Sel
Dialogue: 0,0:00:05.00,0:00:08.00,Default,,0,0,0,,{\\k20}Lí{\\k30}nea 2 NoSel
Dialogue: 0,0:00:10.00,0:00:14.00,Default,,0,0,0,,{\\k20}Lí{\\k30}nea 3 NoSel
"""
        with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8") as f:
            f.write(ass_content)
            temp_path = f.name

        try:
            api = PyxisAPI(temp_path, "res.ass", "session.json")

            # Paso 1: Salida en modo Selected Lines
            graph_sel = {
                "nodes": [
                    {
                        "id": 1,
                        "type": "Output",
                        "title": "Output",
                        "properties": {"apply_to": "Selected Lines", "output_id": "out"},
                        "inputs": [{"name": "In", "link": 10}]
                    },
                    {
                        "id": 2,
                        "type": "Text",
                        "title": "Text",
                        "properties": {"text": "FX {!\\\\pos($x,$y)!}"},
                        "outputs": [{"name": "Out", "links": [10]}]
                    }
                ],
                "links": [[10, 2, 0, 1, 0, "string"]]
            }
            info_sel = api.get_preview_info(source="aegisub", target_output_id=["out"], payload=graph_sel)
            self.assertEqual(info_sel["clip_duration_sec"], 5.0)
            self.assertEqual(info_sel["clip_start_ms"], 0)

            res_sel = api.generate_preview_ass(graph_sel, target_output_id=["out"], source="aegisub")
            c_sel = res_sel.get("content", "")
            # Línea 1 comentada, Líneas 2 y 3 intactas como Dialogue
            self.assertIn("Comment:  0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k20}Lí{\\k30}nea 1 Sel", c_sel)
            self.assertIn("Dialogue: 0,0:00:05.00,0:00:08.00,Default,,0,0,0,,{\\k20}Lí{\\k30}nea 2 NoSel", c_sel)
            self.assertIn("Dialogue: 0,0:00:10.00,0:00:14.00,Default,,0,0,0,,{\\k20}Lí{\\k30}nea 3 NoSel", c_sel)

            # Paso 2: Usuario cambia apply_to a All Lines y presiona Refresh
            graph_all = {
                "nodes": [
                    {
                        "id": 1,
                        "type": "Output",
                        "title": "Output",
                        "properties": {"apply_to": "All Lines", "output_id": "out"},
                        "inputs": [{"name": "In", "link": 10}]
                    },
                    {
                        "id": 2,
                        "type": "Text",
                        "title": "Text",
                        "properties": {"text": "FX {!\\\\pos($x,$y)!}"},
                        "outputs": [{"name": "Out", "links": [10]}]
                    }
                ],
                "links": [[10, 2, 0, 1, 0, "string"]]
            }
            info_all = api.get_preview_info(source="aegisub", target_output_id=["out"], payload=graph_all)
            self.assertEqual(info_all["clip_duration_sec"], 16.0)
            self.assertEqual(info_all["clip_start_ms"], 0)

            res_all = api.generate_preview_ass(graph_all, target_output_id=["out"], source="aegisub")
            c_all = res_all.get("content", "")
            # Todas las líneas originales (1, 2 y 3) deben estar comentadas
            self.assertIn("Comment:  0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k20}Lí{\\k30}nea 1 Sel", c_all)
            self.assertIn("Comment:  0,0:00:05.00,0:00:08.00,Default,,0,0,0,,{\\k20}Lí{\\k30}nea 2 NoSel", c_all)
            self.assertIn("Comment:  0,0:00:10.00,0:00:14.00,Default,,0,0,0,,{\\k20}Lí{\\k30}nea 3 NoSel", c_all)
            # Y no debe haber ningún Dialogue con el texto original sin pyxis_fx
            for line in c_all.splitlines():
                if line.startswith("Dialogue:"):
                    self.assertIn("pyxis_fx", line)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_preview_base_repeated_modifications_and_restorations(self):
        """Verifica que cualquier modificación, edición directa o restpyxisción de preview_base.ass sea detectada de inmediato."""
        import tempfile
        from main import PyxisAPI

        api = PyxisAPI("dummy.ass", "dummy_res.ass", "dummy_session.json")
        user_base_path = api.ensure_preview_base_ass()
        self.assertTrue(user_base_path and os.path.exists(user_base_path))

        # Backup del archivo original de AppData
        with open(user_base_path, "rb") as f:
            original_content = f.read()

        try:
            # 1. Estado original
            info_1 = api._load_and_cache_preview_base()
            hash_1 = api._preview_base_hash
            self.assertIsNotNone(hash_1)

            # 2. Modificación del usuario (ej. cambiar a 2 líneas y 1920x1080)
            custom_ass = """[Script Info]
PlayResX: 1920
PlayResY: 1080
[Events]
Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,{\\k20}Línea custom 1
Dialogue: 0,0:00:05.00,0:00:09.00,Default,,0,0,0,,{\\k20}Línea custom 2
"""
            with open(user_base_path, "w", encoding="utf-8") as f:
                f.write(custom_ass)

            info_2 = api._load_and_cache_preview_base()
            hash_2 = api._preview_base_hash
            self.assertNotEqual(hash_1, hash_2)
            self.assertEqual(info_2["res_x"], 1920)
            self.assertEqual(info_2["res_y"], 1080)
            self.assertEqual(len(info_2["dialogues"]), 2)

            # 3. Restpyxisción por copiar/pegar del archivo por defecto con timestamp arbitrario
            with open(user_base_path, "wb") as f:
                f.write(original_content)
            # Forzar un timestamp pasado para simular copiar/pegar preservando mtime antiguo
            os.utime(user_base_path, (1000000, 1000000))

            info_3 = api._load_and_cache_preview_base()
            hash_3 = api._preview_base_hash
            self.assertEqual(hash_3, hash_1)
            self.assertEqual(len(info_3["dialogues"]), len(info_1["dialogues"]))
            self.assertEqual(info_3["res_x"], info_1["res_x"])

        finally:
            # Restpyxisr contenido
            with open(user_base_path, "wb") as f:
                f.write(original_content)

    def test_switch_apply_to_style_lines_dynamic_range_and_commenting(self):
        """Verifica que en modo Style Lines el clip abarque todas las líneas del estilo seleccionado y se comenten todas ellas."""
        import tempfile
        from main import PyxisAPI

        ass_content = """[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Romaji,Arial,50,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1
Style: Translation,Arial,40,&H00FFFF00,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Comment: 0,0:00:01.00,0:00:03.00,Romaji,,0,0,0,PyxisMetrics,sel=1
Dialogue: 0,0:00:01.00,0:00:03.00,Romaji,,0,0,0,,{\\k20}Lí{\\k30}nea 1 Romaji Sel
Dialogue: 0,0:00:05.00,0:00:08.00,Romaji,,0,0,0,,{\\k20}Lí{\\k30}nea 2 Romaji NoSel
Dialogue: 0,0:00:01.00,0:00:08.00,Translation,,0,0,0,,Traducción de fondo
"""
        with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8") as f:
            f.write(ass_content)
            temp_path = f.name

        try:
            api = PyxisAPI(temp_path, "res.ass", "session.json")
            graph_style = {
                "nodes": [
                    {
                        "id": 1,
                        "type": "Output",
                        "title": "Output",
                        "properties": {"apply_to": "Style Lines", "output_id": "out"},
                        "inputs": [{"name": "In", "link": 10}]
                    },
                    {
                        "id": 2,
                        "type": "Text",
                        "title": "Text",
                        "properties": {"text": "FX {!\\pos($x,$y)!}"},
                        "outputs": [{"name": "Out", "links": [10]}]
                    }
                ],
                "links": [[10, 2, 0, 1, 0, "string"]]
            }
            info_style = api.get_preview_info(source="aegisub", target_output_id=["out"], payload=graph_style)
            self.assertEqual(info_style["clip_duration_sec"], 10.0)
            self.assertEqual(info_style["clip_start_ms"], 0)

            res_style = api.generate_preview_ass(graph_style, target_output_id=["out"], source="aegisub")
            c = res_style.get("content", "")
            # Las 2 líneas de estilo Romaji deben estar comentadas
            self.assertIn("Comment:  0,0:00:01.00,0:00:03.00,Romaji,,0,0,0,,{\\k20}Lí{\\k30}nea 1 Romaji Sel", c)
            self.assertIn("Comment:  0,0:00:05.00,0:00:08.00,Romaji,,0,0,0,,{\\k20}Lí{\\k30}nea 2 Romaji NoSel", c)
            # La línea de estilo Translation debe permanecer como Dialogue
            self.assertIn("Dialogue: 0,0:00:01.00,0:00:08.00,Translation,,0,0,0,,Traducción de fondo", c)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_preview_fonts_map_and_font_discovery(self):
        """Verifica que _find_font_file resuelva fuentes del sistema y get_preview_fonts_map entregue URLs base64 válidas."""
        import tempfile
        from main import PyxisAPI

        ass_content = """[Script Info]
PlayResX: 1280
PlayResY: 720

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,50,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1
Style: CustomStyle,Comic Sans MS,45,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,CustomStyle,,0,0,0,,Texto con fuente Comic Sans
"""
        with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8") as f:
            f.write(ass_content)
            temp_path = f.name

        try:
            api = PyxisAPI(temp_path, "res.ass", "session.json")
            info = api.get_preview_info(source="aegisub")
            self.assertEqual(info["font_name"], "Comic Sans MS")

            font_path = api._find_font_file("Comic Sans MS")
            self.assertTrue(font_path and os.path.exists(font_path))

            font_url = api.get_preview_font_data_url(source="aegisub")
            self.assertTrue(font_url.startswith("data:font/"))

            fonts_map = api.get_preview_fonts_map(source="aegisub")
            self.assertIn("comic sans ms", fonts_map)
            self.assertIn("arial", fonts_map)
            self.assertTrue(fonts_map["comic sans ms"]["data"].startswith("data:font/"))
            self.assertTrue(fonts_map["comic sans ms"]["http_url"].startswith("http://127.0.0.1:28723/media_file"))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_audio_nodes_in_preview(self):
        """Verifica que generate_preview_ass provea default_audio_source al GraphEngine para nodos de audio."""
        wav_path = os.path.join(self.temp_dir, "test_audio.wav")
        import wave, math, struct
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            frames = bytearray()
            for i in range(44100 * 3):
                t = float(i) / 44100.0
                val = int(0.5 * 32767.0 * math.sin(2.0 * math.pi * 220.0 * t))
                frames.extend(struct.pack("<h", val))
            wf.writeframes(frames)

        custom_content = f"""[Script Info]
PlayResX: 1280
PlayResY: 720

[Aegisub Project Garbage]
Audio File: ?audio:{wav_path}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,50,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:02.50,Default,,0,0,0,,{{\\k100}}Audio{{\\k100}}Test
"""
        with open(self.user_base_path, "w", encoding="utf-8") as f:
            f.write(custom_content)

        api = PyxisAPI("dummy.ass", "res.ass", "session.json")
        info = api.get_preview_info(source="base")
        self.assertEqual(info["real_audio_file"], os.path.abspath(wav_path))

        # Crear grafo con nodo Audio Waveform conectado a Salida
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Audio/Audio Waveform",
                    "properties": {"samples": "10", "modo": "Relleno"},
                    "inputs": [{"name": "Audio Path", "link": None}],
                    "outputs": [{"name": "Shape", "links": [101]}]
                },
                {
                    "id": 2,
                    "type": "System/Output",
                    "properties": {"salida_id": "out1", "apply_to": "All Lines"},
                    "inputs": [
                        {"name": "Loop", "link": None},
                        {"name": "Capa", "link": None},
                        {"name": "Start", "link": None},
                        {"name": "End", "link": None},
                        {"name": "Tags", "link": None},
                        {"name": "Texto/Forma", "link": 101}
                    ],
                    "outputs": []
                }
            ],
            "links": [
                [101, 1, 0, 2, 5, "string"]
            ]
        }

        res = api.generate_preview_ass(graph_data, target_output_id="out1", source="base")
        self.assertTrue(res.get("success"))
        self.assertIn("Dialogue:", res.get("content", ""))
        self.assertIn("m ", res.get("content", ""))


if __name__ == "__main__":
    unittest.main()





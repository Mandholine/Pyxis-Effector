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

# PyxisNodes/tests/test_audio_modulator.py
"""Tests unitarios para el nodo Audio / Audio Modulador y funciones globales de audio."""

import math
import os
import shutil
import struct
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from audio_engine import AudioEngine
from nodes.audio_nodes import (
    audio_modulator_master,
    audio_rms,
    audio_peak,
    audio_band,
    audio_fft,
    resolve_audio_data
)
from node_engine import GraphEngine, _eval_num_expr
from nodes.code_nodes import execute_python_script


def create_test_wav(
    file_path: str,
    duration_s: float = 1.0,
    sample_rate: int = 44100,
    freq: float = 440.0,
    amplitude: float = 0.8
) -> str:
    """Crea un WAV sintético para pruebas unitarias."""
    num_frames = int(duration_s * sample_rate)
    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_frames):
            t = float(i) / sample_rate
            val = int(amplitude * 32767.0 * math.sin(2.0 * math.pi * freq * t))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return file_path


def create_rich_test_wav(file_path: str, duration_s: float = 1.0, sample_rate: int = 44100) -> str:
    """Crea un WAV sintético con bajos (100Hz), medios (1000Hz) y agudos (8000Hz)."""
    num_frames = int(duration_s * sample_rate)
    with wave.open(file_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_frames):
            t = float(i) / sample_rate
            s = 0.28 * math.sin(2.0 * math.pi * 100.0 * t) + \
                0.28 * math.sin(2.0 * math.pi * 1000.0 * t) + \
                0.28 * math.sin(2.0 * math.pi * 8000.0 * t)
            val = int(s * 32767.0)
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)
    return file_path


class TestAudioModulator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="pyxis_test_mod_")
        self.wav_path = os.path.join(self.temp_dir, "test_track.wav")
        create_test_wav(self.wav_path, duration_s=1.0, freq=440.0, amplitude=0.8)
        self.rich_wav_path = os.path.join(self.temp_dir, "test_rich.wav")
        create_rich_test_wav(self.rich_wav_path, duration_s=1.0)
        AudioEngine.clear_cache()

        self.context = {
            "start_time": 0,
            "end_time": 1000,
            "st": 0,
            "et": 1000,
            "default_audio_source": self.wav_path,
            "active_unit": type("Syl", (), {
                "i": 1,
                "n": 1,
                "start_time": 0,
                "end_time": 1000,
                "duration": 1000,
                "dur": 1000,
                "text_stripped": "Test",
                "center": 100.0,
                "middle": 200.0
            })()
        }

    def tearDown(self):
        AudioEngine.clear_cache()
        if os.path.isdir(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # 1. PRUEBAS DE GENERACIÓN DE CADENAS DE TAGS \t
    # -------------------------------------------------------------------------
    def test_audio_modulator_tag_chain_fscy(self):
        """Verifica la generación de la cadena continua \\fscy...\\t(...) en base al audio."""
        tag_chain = audio_modulator_master(
            context=self.context,
            audio_path=self.wav_path,
            tag_name="fscy",
            min_val="100",
            max_val="160",
            step_ms="100",
            smoothing="0.0",
            modo="RMS (Volumen)",
            output_slot_index=0
        )
        self.assertIsInstance(tag_chain, str)
        self.assertTrue(tag_chain.startswith(r"\fscy"))
        self.assertIn(r"\t(", tag_chain)
        self.assertIn(r"\fscy", tag_chain)

    def test_audio_modulator_gain_scaling(self):
        """Verifica que el parámetro Ganancia escale la intensidad de modulación proporcionalmente."""
        val_gain_1 = audio_modulator_master(
            context=self.context,
            audio_path=self.wav_path,
            min_val="100",
            max_val="200",
            ganancia="1.0",
            output_slot_index=1
        )
        val_gain_2 = audio_modulator_master(
            context=self.context,
            audio_path=self.wav_path,
            min_val="100",
            max_val="200",
            ganancia="1.5",
            output_slot_index=1
        )
        self.assertGreater(float(val_gain_2), float(val_gain_1))

    def test_audio_modulator_gain_in_all_modes(self):
        """Verifica que la ganancia escale la salida en todos los 6 modos de Audio Modulador."""
        modes = [
            "RMS (Volumen)",
            "Picos (Peak)",
            "Bajos (20-250Hz)",
            "Medios (250-4kHz)",
            "Agudos (4-16kHz)",
            "Banda Custom"
        ]
        for m in modes:
            rms_1 = audio_modulator_master(
                context=self.context,
                audio_path=self.rich_wav_path,
                modo=m,
                min_hz="200",
                max_hz="1000",
                ganancia="0.5",
                output_slot_index=3
            )
            rms_2 = audio_modulator_master(
                context=self.context,
                audio_path=self.rich_wav_path,
                modo=m,
                min_hz="200",
                max_hz="1000",
                ganancia="1.5",
                output_slot_index=3
            )
            self.assertGreater(rms_2, rms_1, f"El modo '{m}' debe escalar proporcionalmente con la ganancia")

    def test_audio_modulator_custom_tags(self):
        """Verifica la compatibilidad con diferentes tags ASS (blur, frz, bord, fscx)."""
        tags_to_test = ["blur", "frz", "bord", "fscx"]
        for tag in tags_to_test:
            chain = audio_modulator_master(
                context=self.context,
                audio_path=self.wav_path,
                tag_name=tag,
                min_val="0",
                max_val="10",
                step_ms="200",
                output_slot_index=0
            )
            self.assertTrue(chain.startswith(f"\\{tag}"), f"Debe comenzar con \\{tag}")
            self.assertIn(f"\\t(", chain)

    def test_audio_modulator_alpha_hex_conversion(self):
        """Verifica la conversión de hex (&H00& a &HFF&) y formateo de tags alpha (1a, 2a, 3a, 4a, alpha)."""
        alpha_tags = ["1a", "2a", "3a", "4a", "alpha"]
        for tag in alpha_tags:
            chain = audio_modulator_master(
                context=self.context,
                audio_path=self.wav_path,
                tag_name=tag,
                min_val="&H00&",
                max_val="&HFF&",
                step_ms="100",
                output_slot_index=0
            )
            self.assertTrue(chain.startswith(f"\\{tag}&H"), f"Tag {tag} debe comenzar con \\{tag}&H")
            self.assertIn("&", chain)
            self.assertIn(f"\\t(", chain)

            # Slot 1: Valor actual en formato &HAA&
            act_val = audio_modulator_master(
                context=self.context,
                audio_path=self.wav_path,
                tag_name=tag,
                min_val="&H00&",
                max_val="&HFF&",
                output_slot_index=1
            )
            self.assertTrue(str(act_val).startswith("&H") and str(act_val).endswith("&"))

            # Slot 2: Array de valores en formato &HAA&
            arr_vals = audio_modulator_master(
                context=self.context,
                audio_path=self.wav_path,
                tag_name=tag,
                min_val="0",
                max_val="255",
                step_ms="200",
                output_slot_index=2
            )
            self.assertIsInstance(arr_vals, list)
            self.assertTrue(all(isinstance(v, str) and v.startswith("&H") and v.endswith("&") for v in arr_vals))

    # -------------------------------------------------------------------------
    # 2. PRUEBAS DE SALIDAS MULTI-SLOT
    # -------------------------------------------------------------------------
    def test_audio_modulator_multi_slot_outputs(self):
        """Verifica los 4 slots de salida: Tags Out, Valor Actual, Array Valores, RMS Promedio."""
        # Slot 0: Cadena de tags
        out_tags = audio_modulator_master(
            context=self.context,
            audio_path=self.wav_path,
            min_val=100, max_val=200, step_ms=100,
            output_slot_index=0
        )
        self.assertIsInstance(out_tags, str)
        self.assertTrue(out_tags.startswith(r"\fscy"))

        # Slot 1: Valor actual instantáneo (escalar)
        out_val = audio_modulator_master(
            context=self.context,
            audio_path=self.wav_path,
            min_val=100, max_val=200, step_ms=100,
            output_slot_index=1
        )
        self.assertIsInstance(out_val, float)
        self.assertTrue(100.0 <= out_val <= 200.0)

        # Slot 2: Array de valores
        out_arr = audio_modulator_master(
            context=self.context,
            audio_path=self.wav_path,
            min_val=100, max_val=200, step_ms=100,
            output_slot_index=2
        )
        self.assertIsInstance(out_arr, list)
        self.assertGreater(len(out_arr), 1)
        for v in out_arr:
            self.assertTrue(100.0 <= v <= 200.0)

        # Slot 3: RMS Promedio (0.0 a 1.0)
        out_rms = audio_modulator_master(
            context=self.context,
            audio_path=self.wav_path,
            output_slot_index=3
        )
        self.assertIsInstance(out_rms, float)
        self.assertTrue(0.0 <= out_rms <= 1.0)

    # -------------------------------------------------------------------------
    # 3. PRUEBAS DE MODOS EN BADGE DE TÍTULO
    # -------------------------------------------------------------------------
    def test_audio_modulator_modes(self):
        """Verifica la ejecución de los 6 modos acústicos."""
        modes = [
            "RMS (Volumen)",
            "Picos (Peak)",
            "Bajos (20-250Hz)",
            "Medios (250-4kHz)",
            "Agudos (4-16kHz)",
            "Banda Custom"
        ]
        for mode in modes:
            res = audio_modulator_master(
                context=self.context,
                audio_path=self.wav_path,
                modo=mode,
                min_hz=400,
                max_hz=500,
                step_ms=100,
                output_slot_index=3  # Promedio
            )
            self.assertIsInstance(res, float)
            self.assertTrue(0.0 <= res <= 1.0)

    # -------------------------------------------------------------------------
    # 4. PRUEBAS DE FUNCIONES AUXILIARES GLOBALES (audio_rms, audio_peak, etc.)
    # -------------------------------------------------------------------------
    def test_global_audio_functions(self):
        """Verifica audio_rms, audio_peak, audio_band y audio_fft con contexto inyectado."""
        rms = audio_rms(0, 1000, context=self.context)
        self.assertAlmostEqual(rms, 0.565, delta=0.08)

        peak = audio_peak(0, 1000, context=self.context)
        self.assertAlmostEqual(peak, 0.8, delta=0.08)

        band_440 = audio_band(0, 1000, min_hz=400, max_hz=500, context=self.context)
        band_high = audio_band(0, 1000, min_hz=6000, max_hz=10000, context=self.context)
        self.assertGreater(band_440, band_high)

        fft_bands = audio_fft(0, 1000, num_bands=8, context=self.context)
        self.assertEqual(len(fft_bands), 8)

    # -------------------------------------------------------------------------
    # 5. INTEGRACIÓN CON EVALUADOR DE EXPRESIONES (_eval_num_expr)
    # -------------------------------------------------------------------------
    def test_eval_num_expr_with_audio_functions(self):
        """Verifica que las casillas de texto resuelvan fórmulas con audio_rms() y audio_peak()."""
        expr1 = "100 + audio_rms() * 50"
        val1 = _eval_num_expr(expr1, self.context, default=0.0)
        self.assertTrue(120.0 <= val1 <= 140.0)

        expr2 = "syl.center + audio_peak() * 20"
        val2 = _eval_num_expr(expr2, self.context, default=0.0)
        self.assertAlmostEqual(val2, 100.0 + 0.8 * 20.0, delta=1.5)

    # -------------------------------------------------------------------------
    # 6. INTEGRACIÓN CON NODO DE CÓDIGO (Python Script)
    # -------------------------------------------------------------------------
    def test_code_node_integration(self):
        """Verifica que un script en Python en el Nodo de Código acceda a audio_rms() y audio_fft()."""
        script = (
            "vol = audio_rms()\n"
            "result = f'\\\\blur{round(vol * 10, 1)}'\n"
        )
        res = execute_python_script(self.context, script, {})
        self.assertTrue(res.startswith(r"\blur"))

    # -------------------------------------------------------------------------
    # 7. INTEGRACIÓN CON EL MOTOR DE GRAFO (GraphEngine & Salida)
    # -------------------------------------------------------------------------
    def test_graph_engine_with_audio_modulator(self):
        """Verifica el flujo completo de un grafo conectando Audio Modulador a Salida."""
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl"},
                    "outputs": [{"name": "Loop", "links": [101]}]
                },
                {
                    "id": 2,
                    "type": "Audio/Audio Modulator",
                    "properties": {
                        "audio_path": self.wav_path,
                        "tag_name": "fscy",
                        "min_val": "100",
                        "max_val": "180",
                        "step_ms": "100",
                        "modo": "RMS (Volumen)"
                    },
                    "outputs": [{"name": "Tags Out", "links": [102]}]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 101},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": 102},
                        {"name": "Return", "link": None}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 3, 0, "Loop"],
                [102, 2, 0, 3, 4, "String"]
            ]
        }

        engine = GraphEngine(graph_data, 1280, 720, 41.708, default_audio_source=self.wav_path)
        dialogues = [{
            "raw": "Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{\\k100}Test",
            "metrics": {
                "h": 35, "d": 0, "e": 0, "sel": True, "rw": 100, "l": 50, "c": 100, "r": 150, "t": 100, "m": 120, "b": 140,
                "syl_lefts": [50], "syl_centers": [100], "syl_rights": [150], "syl_widths": [100],
                "syl_starts": [0], "syl_ends": [1000], "w": [100]
            }
        }]
        styles = {"Default": {}}

        lines = engine.process(dialogues, styles)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("Dialogue:"))
        self.assertIn(r"\fscy", lines[0])
        self.assertIn(r"\t(", lines[0])

    def test_circuit_3_vars_multitag_concatenar(self):
        """Verifica la ejecución exacta del Circuito 3:
        Main Loop (SYL) -> Definir Vars (audio_band, jump_y, rot_z) -> MultiTag (pos, frz) -> Concatenar -> Salida.
        """
        graph_data = {
            "nodes": [
                {
                    "id": 1,
                    "type": "Loops/Main Loop",
                    "properties": {"iterador": "syl", "noblank": "No Blank"},
                    "outputs": [{"name": "Loop", "links": [101]}]
                },
                {
                    "id": 2,
                    "type": "Variables/Define Vars",
                    "properties": {
                        "variables": "bass = audio_band(st, et, 20, 200);\njump_y = syl.middle - bass * 35; rot_z = (bass - 0.5) * 20;"
                    },
                    "inputs": [{"name": "In", "link": 101}],
                    "outputs": [{"name": "Out", "links": [102]}]
                },
                {
                    "id": 3,
                    "type": "MultiTag",
                    "properties": {"tag_type": "pos", "x": "syl.center", "y": "jump_y"},
                    "inputs": [
                        {"name": "X (px)", "link": None, "value": "syl.center"},
                        {"name": "Y (px)", "link": None, "value": "jump_y"}
                    ],
                    "outputs": [{"name": "String", "links": [103]}]
                },
                {
                    "id": 4,
                    "type": "MultiTag",
                    "properties": {"tag_type": "frz", "valor": "rot_z"},
                    "inputs": [
                        {"name": "Value", "link": None, "value": "rot_z"}
                    ],
                    "outputs": [{"name": "String", "links": [104]}]
                },
                {
                    "id": 5,
                    "type": "Concatenate",
                    "properties": {"separador": "nil"},
                    "inputs": [
                        {"name": "In1", "link": 103},
                        {"name": "In2", "link": 104}
                    ],
                    "outputs": [{"name": "String", "links": [105]}]
                },
                {
                    "id": 6,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 102},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": 105},
                        {"name": "Return", "link": None}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 2, 0, "Loop"],
                [102, 2, 0, 6, 0, "Loop"],
                [103, 3, 0, 5, 0, "String"],
                [104, 4, 0, 5, 1, "String"],
                [105, 5, 0, 6, 4, "String"]
            ]
        }

        engine = GraphEngine(graph_data, 1280, 720, 41.708, default_audio_source=self.wav_path)
        dialogues = [{
            "raw": "Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{\\k100}Test",
            "metrics": {
                "h": 35, "d": 0, "e": 0, "sel": True, "rw": 100, "l": 50, "c": 100, "r": 150, "t": 50, "m": 65, "b": 80,
                "syl_lefts": [50], "syl_centers": [100], "syl_rights": [150], "syl_widths": [100],
                "syl_starts": [0], "syl_ends": [1000], "w": [100]
            }
        }]
        styles = {"Default": {}}

        lines = engine.process(dialogues, styles)
        self.assertEqual(len(lines), 1)
        line_text = lines[0]
        self.assertTrue(line_text.startswith("Dialogue:"))
        # Verifica que pos se genera con syl.center (640) y jump_y dinámico, y frz con rot_z dinámico
        self.assertIn(r"\pos(640,", line_text)
        self.assertIn(r"\frz-", line_text)
        self.assertNotIn(r"\pos(0,0)", line_text)
        self.assertNotIn(r"\frz0.0", line_text)

    def test_audio_modulator_color_interpolation_2_colors(self):
        """Verifica la modulación de color en tag 1c con 2 colores en min_val y max_val."""
        tag_chain = audio_modulator_master(
            context=self.context,
            audio_path=self.wav_path,
            tag_name="1c",
            min_val="&HFFFFFF&",
            max_val="&H0000FF&",
            step_ms="100",
            smoothing="0.0",
            modo="RMS (Volumen)",
            output_slot_index=0
        )
        self.assertIsInstance(tag_chain, str)
        self.assertTrue(tag_chain.startswith(r"\1c&H"))
        self.assertIn(r"\t(", tag_chain)
        self.assertIn(r"\1c&H", tag_chain)

    def test_audio_modulator_color_interpolation_multi_stop_palette(self):
        """Verifica la modulación de color multi-stop con 3 colores en lista (Azul -> Verde -> Rojo)."""
        tag_chain = audio_modulator_master(
            context=self.context,
            audio_path=self.wav_path,
            tag_name="c",
            min_val="&HFF0000&, &H00FF00&, &H0000FF&",
            max_val="",
            step_ms="100",
            smoothing="0.0",
            modo="Bajos (20-250Hz)",
            output_slot_index=0
        )
        self.assertIsInstance(tag_chain, str)
        self.assertTrue(tag_chain.startswith(r"\c&H"))
        self.assertIn(r"\t(", tag_chain)
        self.assertIn(r"\c&H", tag_chain)

    def test_circuit_4_audio_reactive_color_modulation(self):
        """Verifica el circuito 4 completo en 1 sola línea continua usando Audio Modulador de color."""
        graph_data = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {"iterador": "line", "noblank": "No Blank"}, "outputs": [{"name": "Loop", "links": [101]}]},
                {
                    "id": 2,
                    "type": "Audio/Audio Modulator",
                    "properties": {
                        "tag_name": "1c",
                        "min_val": "&HFFFFFF&",
                        "max_val": "&H0000FF&",
                        "ganancia": "2.0",
                        "modo": "Bajos (20-250Hz)",
                        "step_ms": "41.7"
                    },
                    "outputs": [{"name": "Tags Out", "links": [102]}]
                },
                {
                    "id": 3,
                    "type": "System/Output",
                    "properties": {"apply_to": "Selected Lines"},
                    "inputs": [
                        {"name": "Loop / Domain", "link": 101},
                        {"name": "Layer", "link": None},
                        {"name": "Start Time", "link": None},
                        {"name": "End Time", "link": None},
                        {"name": "Tags", "link": 102},
                        {"name": "Return", "link": None}
                    ]
                }
            ],
            "links": [
                [101, 1, 0, 3, 0, "Loop"],
                [102, 2, 0, 3, 4, "String"]
            ]
        }

        engine = GraphEngine(graph_data, 1280, 720, 41.708, default_audio_source=self.wav_path)
        dialogues = [{
            "raw": "Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{\\k100}Test Line",
            "metrics": {
                "h": 35, "d": 0, "e": 0, "sel": True, "rw": 100, "l": 50, "c": 100, "r": 150, "t": 50, "m": 65, "b": 80,
                "syl_lefts": [50], "syl_centers": [100], "syl_rights": [150], "syl_widths": [100],
                "syl_starts": [0], "syl_ends": [1000], "w": [100]
            }
        }]
        styles = {"Default": {}}

        lines = engine.process(dialogues, styles)
        self.assertEqual(len(lines), 1)
        line_text = lines[0]
        self.assertTrue(line_text.startswith("Dialogue:"))
        self.assertIn(r"\1c&H", line_text)
        self.assertIn(r"\t(", line_text)


if __name__ == "__main__":
    unittest.main()

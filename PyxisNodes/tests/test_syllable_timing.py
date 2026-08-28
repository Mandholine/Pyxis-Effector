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

# test_syllable_timing.py
"""Pruebas de verificación de tiempos por sílaba, carácter y palabra en PyxisNodes."""

import unittest
from ass_parser import KaraokeProcessor


class TestSyllableTiming(unittest.TestCase):
    def test_syllable_and_char_times(self):
        kp = KaraokeProcessor(res_x=1280, res_y=720)
        raw_dialogue = "Dialogue: 0,0:00:05.00,0:00:10.00,Default,,0,0,0,,{\\k43}Ma{\\k65}ry {\\k44}te"
        style = {"Fontname": "Arial", "Fontsize": 40}

        line = kp.process_line(raw_dialogue, style)

        self.assertEqual(line.start_time, 5000)
        self.assertEqual(line.end_time, 10000)
        self.assertEqual(line.duration, 5000)

        real_syls = [s for s in line.syls if s.text_spacestripped]
        self.assertEqual(len(real_syls), 3)

        # Verificar tiempos absolutos y relativos de la sílaba 'Ma'
        syl_ma = real_syls[0]
        self.assertEqual(syl_ma.text_spacestripped, "Ma")
        self.assertEqual(syl_ma.start_time, 5000)
        self.assertEqual(syl_ma.end_time, 5430)
        self.assertEqual(syl_ma.duration, 430)
        self.assertEqual(syl_ma.syl_start, 0)
        self.assertEqual(syl_ma.syl_end, 430)
        self.assertEqual(syl_ma.start, 0)
        self.assertEqual(syl_ma.end, 430)
        self.assertEqual(syl_ma.st, 5000)
        self.assertEqual(syl_ma.et, 5430)

        # Verificar tiempos absolutos y relativos de la sílaba 'ry ' (incluye espacio final)
        syl_ry = real_syls[1]
        self.assertEqual(syl_ry.text_spacestripped, "ry")
        self.assertEqual(syl_ry.start_time, 5430)
        self.assertEqual(syl_ry.end_time, 6080)
        self.assertEqual(syl_ry.duration, 650)
        self.assertEqual(syl_ry.syl_start, 430)
        self.assertEqual(syl_ry.syl_end, 1080)

        # Verificar tiempos de la palabra 'Mary' (caracteres visibles 'M', 'a', 'r', 'y')
        self.assertGreaterEqual(len(line.words), 2)
        word1 = line.words[0]
        self.assertEqual(word1.text_stripped, "Mary")
        self.assertEqual(word1.start_time, 5000)
        self.assertEqual(word1.end_time, 5819)  # Los caracteres de 'Mary' terminan a 5819ms; el espacio final dura de 5819ms a 6080ms
        self.assertEqual(word1.word_start, 0)
        self.assertEqual(word1.word_end, 819)

    def test_multi_tag_brackets_timing(self):
        kp = KaraokeProcessor(res_x=1280, res_y=720)
        raw_dialogue = "Dialogue: 0,0:00:02.00,0:00:08.00,Default,,0,0,0,,{\\pos(100,100)\\k50}A{\\k100}B"
        style = {"Fontname": "Arial", "Fontsize": 40}

        line = kp.process_line(raw_dialogue, style)
        self.assertEqual(line.start_time, 2000)

        real_syls = [s for s in line.syls if s.text_spacestripped]
        self.assertEqual(len(real_syls), 2)

        syl_a = real_syls[0]
        self.assertEqual(syl_a.text_spacestripped, "A")
        self.assertEqual(syl_a.start_time, 2000)
        self.assertEqual(syl_a.end_time, 2500)
        self.assertEqual(syl_a.duration, 500)

        syl_b = real_syls[1]
        self.assertEqual(syl_b.text_spacestripped, "B")
        self.assertEqual(syl_b.start_time, 2500)
        self.assertEqual(syl_b.end_time, 3500)
        self.assertEqual(syl_b.duration, 1000)

    def test_non_karaoke_line_estimated_words_as_syls(self):
        """Verifica que una línea sin tags de karaoke (ej. traducción) divida la duración en palabras como sílabas estimadas."""
        kp = KaraokeProcessor(res_x=1280, res_y=720)
        raw_dialogue = "Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,Esta es una traducción de prueba"
        style = {"Fontname": "Arial", "Fontsize": 40}

        line = kp.process_line(raw_dialogue, style)
        self.assertEqual(line.duration, 3000)

        # 6 palabras -> 6 sílabas estimadas de 500ms cada una
        self.assertEqual(len(line.syls), 6)
        self.assertEqual(len(line.words), 6)

        expected_words = ["Esta", "es", "una", "traducción", "de", "prueba"]
        for i, s in enumerate(line.syls):
            self.assertEqual(s.i, i + 1)
            self.assertEqual(s.n, 6)
            self.assertEqual(s.text_stripped, expected_words[i])
            self.assertEqual(s.start_time, 1000 + i * 500)
            self.assertEqual(s.end_time, 1000 + (i + 1) * 500)
            self.assertEqual(s.duration, 500)
            self.assertEqual(s.kdur, 50.0)
            self.assertGreater(s.width, 0)
            self.assertGreater(s.center, 0)


if __name__ == "__main__":
    unittest.main()

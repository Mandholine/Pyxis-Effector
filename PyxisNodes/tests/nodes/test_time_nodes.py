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

"""Pruebas unitarias para nodos de calculo y sincronizacion de tiempo (Time Nodes)."""

import unittest
from ass_parser import KaraokeProcessor
from models import PyxisLine, PyxisUnit
from nodes.time_nodes import (
    time_lead_in, time_lead_out, time_middle_1, time_middle_2,
    time_loop_1, time_loop_2, time_ipol, time_offset, time_duration,
    time_parse_ass, time_format_ass, time_synchronized_extra_node
)


def _make_test_unit(i, n, start_time, end_time, dur, text="A"):
    u = PyxisUnit()
    u.i, u.n = i, n
    u.start_time, u.end_time, u.dur = start_time, end_time, dur
    u.text, u.text_stripped = text, text
    return u


def _make_line(text="Hello", start=1000, end=2000, left=100, right=200, width=100):
    line = PyxisLine()
    line.text = text
    line.text_stripped = text
    line.start_time = start
    line.end_time = end
    line.duration = end - start
    line.left = left
    line.right = right
    line.width = width
    line.x = (left + right) / 2.0
    line.y = 700.0
    line.style_name = "Default"
    line.is_selected = True
    return line


class TestTimeNodesCore(unittest.TestCase):
    """Pruebas de funciones de tiempo de Effector 2 (ke.time)."""

    def setUp(self):
        self.unit1 = _make_test_unit(i=1, n=4, start_time=1000, end_time=2000, dur=1000, text="A")
        self.unit2 = _make_test_unit(i=2, n=4, start_time=1200, end_time=2200, dur=1000, text="B")
        self.unit4 = _make_test_unit(i=4, n=4, start_time=1600, end_time=2600, dur=1000, text="D")

        self.ctx1 = {'active_unit': self.unit1, 'fx_i': 1, 'fx_n': 3, 'J': 1, 'maxJ': 2}
        self.ctx2 = {'active_unit': self.unit2, 'fx_i': 2, 'fx_n': 3, 'J': 2, 'maxJ': 2}
        self.ctx4 = {'active_unit': self.unit4, 'fx_i': 3, 'fx_n': 3, 'J': 2, 'maxJ': 2}

    def test_lead_in(self):
        self.assertEqual(time_lead_in(self.ctx1, delay=40), -200.0)
        self.assertEqual(time_lead_in(self.ctx2, delay=40), -160.0)
        self.assertEqual(time_lead_in(self.ctx4, delay=40), -80.0)

    def test_lead_out(self):
        self.assertEqual(time_lead_out(self.ctx1, delay=40), 40.0)
        self.assertEqual(time_lead_out(self.ctx4, delay=40), 160.0)

    def test_middle_1(self):
        self.assertEqual(time_middle_1(self.ctx1, delay=30), -200.0)
        self.assertEqual(time_middle_1(self.ctx2, delay=30), -170.0)
        self.assertEqual(time_middle_1(self.ctx4, delay=30), -185.0)

    def test_middle_2(self):
        self.assertEqual(time_middle_2(self.ctx1, delay=30), -215.0)
        self.assertEqual(time_middle_2(self.ctx4, delay=30), -230.0)

    def test_loop_1(self):
        self.assertEqual(time_loop_1(self.ctx1, delay=30, mode="leadin"), -200.0)
        self.assertEqual(time_loop_1(self.ctx2, delay=30, mode="leadin"), -170.0)
        self.assertEqual(time_loop_1(self.ctx4, delay=30, mode="leadout"), 170.0)

    def test_loop_2(self):
        self.assertEqual(time_loop_2(self.ctx1, delay=30, mode="leadin"), -200.0)
        self.assertEqual(time_loop_2(self.ctx2, delay=30, mode="leadin"), -170.0)

    def test_ipol(self):
        res = time_ipol(self.ctx1, dur=1000, points="0, 50, 100", accel=1.0)
        self.assertIn("[0.0, 500.0]", res)
        self.assertIn("[500.0, 1000.0]", res)

    def test_expression_evaluation(self):
        ctx = dict(self.ctx1)
        res = time_lead_in(ctx, delay="20 * 2")
        self.assertEqual(res, -200.0)

    def test_offset_and_duration(self):
        self.assertEqual(time_offset(None, base=1000, offset=250), 1250.0)
        self.assertEqual(time_duration(None, st=1000, et=3500), 2500.0)

    def test_parse_and_format_ass_time(self):
        ms = time_parse_ass(None, ass_str="0:01:23.45")
        self.assertEqual(ms, 83450.0)
        formatted = time_format_ass(None, ms=83450)
        self.assertEqual(formatted, "0:01:23.45")


class TestTimeSynchronized(unittest.TestCase):
    """Pruebas del algoritmo de calculo de tiempo sincronizado entre lineas sucesivas."""

    def test_single_line_isolated(self):
        line = _make_line(text="ABCDE", start=1000, end=2000)
        ctx = {'line': line, 'active_line': line}
        res = time_synchronized_extra_node(ctx, progression_const=20, delay=250, max_added_time=2000)
        self.assertEqual(res, 330.0)

    def test_single_line_cap_max(self):
        line = _make_line(text="A" * 100, start=1000, end=2000)
        ctx = {'line': line, 'active_line': line}
        res = time_synchronized_extra_node(ctx, progression_const=50, delay=250, max_added_time=500)
        self.assertEqual(res, 500.0)


class TestSyllableTiming(unittest.TestCase):
    """Pruebas de tiempos metricos por silaba, caracter y palabra."""

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

        syl_ma = real_syls[0]
        self.assertEqual(syl_ma.text_spacestripped, "Ma")
        self.assertEqual(syl_ma.start_time, 5000)
        self.assertEqual(syl_ma.end_time, 5430)
        self.assertEqual(syl_ma.duration, 430)


if __name__ == "__main__":
    unittest.main()

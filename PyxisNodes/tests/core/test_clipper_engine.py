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

"""Pruebas unitarias para el motor poligonal ClipperEngine (operaciones booleanas y trazado ASS)."""

import unittest
from clipper_engine import ClipperEngine


class TestClipperEngine(unittest.TestCase):
    """Pruebas de operaciones booleanas de interseccion, diferencia y union de trazados."""

    def setUp(self):
        self.shape_a = "m 0 0 l 100 0 l 100 100 l 0 100"
        self.shape_b = "m 50 0 l 150 0 l 150 100 l 50 100"

    def test_parse_assdraw(self):
        polys = ClipperEngine.parse_assdraw(self.shape_a)
        self.assertEqual(len(polys), 1)
        self.assertEqual(len(polys[0]), 4)

    def test_boolean_intersection(self):
        res = ClipperEngine.boolean_intersection(self.shape_a, self.shape_b)
        self.assertTrue(isinstance(res, str) and res.startswith("m "))
        polys = ClipperEngine.parse_assdraw(res)
        self.assertGreaterEqual(len(polys), 1)

    def test_boolean_difference(self):
        res = ClipperEngine.boolean_difference(self.shape_a, self.shape_b)
        self.assertTrue(isinstance(res, str) and res.startswith("m "))

    def test_boolean_union(self):
        res = ClipperEngine.boolean_union(self.shape_a, self.shape_b)
        self.assertTrue(isinstance(res, str) and res.startswith("m "))


if __name__ == "__main__":
    unittest.main()

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

import os
import sys
import time
import unittest
import numpy as np

# Ensure PyxisNodes package root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from particle_nodes import sort_particles, _point_in_contour


class TestVectorizedMath(unittest.TestCase):
    def setUp(self):
        # Generate 5,000 particle points
        self.items = [(float(x), float(y), 255, 255, 255, 255) for x in range(50) for y in range(100)]

    def test_numpad_sorting_accuracy(self):
        orders = ["79", "13", "97", "31", "5", "-5", "71", "17", "rand"]
        for order in orders:
            sorted_items = sort_particles(self.items, order_code=order)
            self.assertEqual(len(sorted_items), len(self.items), f"Sorting length mismatch for order {order}")
            self.assertTrue(isinstance(sorted_items, list), f"Expected list output for order {order}")

    def test_vectorized_sorting_speed(self):
        # Benchmark sorting 10,000 items
        large_items = [(float(x), float(y)) for x in range(100) for y in range(100)]
        start = time.time()
        res = sort_particles(large_items, order_code="79")
        elapsed = time.time() - start
        self.assertEqual(len(res), 10000)
        self.assertLess(elapsed, 0.1, f"Vectorized sorting took too long ({elapsed:.4f}s)")
        print(f"\n[Test Vectorized Math] Sorted 10,000 particles in {elapsed*1000:.2f}ms using NumPy C-Sorting.")

    def test_point_in_contour(self):
        poly = [(0, 0), (100, 0), (100, 100), (0, 100)]
        self.assertTrue(_point_in_contour(50, 50, poly))
        self.assertFalse(_point_in_contour(150, 50, poly))


if __name__ == "__main__":
    unittest.main()

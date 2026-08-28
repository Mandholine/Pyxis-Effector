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
import unittest
import numpy as np

# Ensure PyxisNodes package root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gpu_engine import GpuEngineManager, get_gpu_manager


class TestGpuEngine(unittest.TestCase):
    def test_gpu_manager_singleton_and_health(self):
        gpu_mgr = get_gpu_manager()
        self.assertIsNotNone(gpu_mgr)
        self.assertTrue(gpu_mgr.is_healthy, "GPU Manager health-check should return True (healthy backend active)")
        print(f"\n[Test GPU Engine] Active Backend: '{gpu_mgr.backend}' - Device: '{gpu_mgr.device_name}'")

    def test_live_probe_exception_safety(self):
        # Instantiate a fresh GpuEngineManager to verify probe exception safety
        fresh_mgr = GpuEngineManager()
        self.assertIn(fresh_mgr.backend, ["CUDA (CuPy)", "CUDA (Numba)", "OpenCL (PyOpenCL)", "OpenCL (Ctypes Native Runtime)", "CPU"])

    def test_particle_transform_parity(self):
        gpu_mgr = get_gpu_manager()
        coords = np.array([
            [10.0, 20.0, 1.0],
            [30.0, 40.0, 1.0],
            [50.0, 60.0, 1.0]
        ], dtype=np.float64)

        transformed = gpu_mgr.transform_particles_gpu(
            coords, scale_x=2.0, scale_y=2.0, angle_deg=90.0, offset_x=5.0, offset_y=10.0
        )

        self.assertEqual(transformed.shape, coords.shape)
        # Verify 90 degree rotation math parity
        # For point (10, 20) with scale 2 (20, 40): rot90 -> (-40 + 5, 20 + 10) = (-35, 30)
        self.assertAlmostEqual(transformed[0, 0], -35.0, places=4)
        self.assertAlmostEqual(transformed[0, 1], 30.0, places=4)


if __name__ == "__main__":
    unittest.main()

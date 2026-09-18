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

"""Pruebas unitarias para el motor de aceleracion por GPU / CPU Fallback (GpuEngine)."""

import unittest 
import numpy as np 
from gpu_engine import GpuEngineManager ,get_gpu_manager 


class TestGpuEngine (unittest .TestCase ):
    """Pruebas de inicializacion y transformacion de particulas por GPU/CPU."""

    def test_gpu_manager_singleton_and_health (self ):
        gpu_mgr =get_gpu_manager ()
        self .assertIsNotNone (gpu_mgr )
        self .assertTrue (gpu_mgr .is_healthy )

    def test_live_probe_exception_safety (self ):
        fresh_mgr =GpuEngineManager ()
        self .assertIn (fresh_mgr .backend ,[
        "CUDA (CuPy)","CUDA (Numba)","OpenCL (PyOpenCL)",
        "OpenCL (Ctypes Native Runtime)","CPU"
        ])

    def test_particle_transform_parity (self ):
        gpu_mgr =get_gpu_manager ()
        coords =np .array ([
        [10.0 ,20.0 ,1.0 ],
        [30.0 ,40.0 ,1.0 ],
        [50.0 ,60.0 ,1.0 ]
        ],dtype =np .float64 )

        transformed =gpu_mgr .transform_particles_gpu (
        coords ,scale_x =2.0 ,scale_y =2.0 ,angle_deg =90.0 ,offset_x =5.0 ,offset_y =10.0 
        )

        self .assertEqual (transformed .shape ,coords .shape )
        self .assertAlmostEqual (transformed [0 ,0 ],-35.0 ,places =4 )
        self .assertAlmostEqual (transformed [0 ,1 ],30.0 ,places =4 )


if __name__ =="__main__":
    unittest .main ()

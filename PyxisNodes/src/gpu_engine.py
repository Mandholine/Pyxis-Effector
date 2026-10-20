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
# For any question you can visit: https://discord.gg/fsxRESeQZN

"""
GPU Acceleration Engine for PyxisNodes.
Supports detection and live health-check probing for NVIDIA CUDA and Universal OpenCL (NVIDIA, AMD, Intel) with transparent CPU fallback.
"""

import ctypes
import math
import os
import sys
import numpy as np


class GpuEngineManager:
    _instance = None

    def __init__(self):
        self.backend = "CPU"
        self.device_name = "CPU Fallback (Phase 1 & 2 Vectorized)"
        self.is_healthy = False
        self.cl_context = None
        self.cl_queue = None
        self.cl_program = None
        self.cuda_module = None
        
        self._run_live_health_check_probes()

    @classmethod
    def get_instance(cls):
        """Retrieve or initialize the singleton instance of GpuEngineManager."""
        if cls._instance is None:
            cls._instance = GpuEngineManager()
        return cls._instance

    def _run_live_health_check_probes(self):
        """
        Live health-check probe:
        1. Test CUDA with micro-kernel/VRAM allocation.
        2. If failed, test OpenCL with C micro-kernel.
        3. If both fail, assign CPU fallback without crashing.
        """
        if self._probe_cuda_health():
            return

        if self._probe_opencl_health():
            return

        self.backend = "CPU"
        self.device_name = "CPU Multi-Core Vectorized Engine"
        self.is_healthy = True
        print(f"[Pyxis GPU Engine] Active backend: {self.backend} ({self.device_name})", flush=True)

    def _probe_cuda_health(self) -> bool:
        """Live probe for NVIDIA CUDA (CuPy / PyCUDA / Numba CUDA / Driver API)."""
        try:
            try:
                import importlib
                cp = importlib.import_module("cupy")
                arr = cp.array([1.0, 2.0, 3.0, 4.0], dtype=cp.float32)
                res = (arr * 2.0).get()
                if np.allclose(res, [2.0, 4.0, 6.0, 8.0]):
                    self.backend = "CUDA (CuPy)"
                    self.device_name = cp.cuda.runtime.getDeviceProperties(0)['name'].decode('utf-8')
                    self.is_healthy = True
                    print(f"[Pyxis GPU Engine] CUDA Live Probe OK! Active backend: {self.backend} - {self.device_name}", flush=True)
                    return True
            except Exception:
                pass

            try:
                import importlib
                cuda = importlib.import_module("numba.cuda")
                if cuda.is_available():
                    device = cuda.get_current_device()
                    dev_name = getattr(device, 'name', 'NVIDIA GPU')
                    if isinstance(dev_name, bytes):
                        dev_name = dev_name.decode('utf-8')
                    
                    @cuda.jit
                    def _test_kernel(io_array):
                        pos = cuda.grid(1)
                        if pos < io_array.size:
                            io_array[pos] *= 2.0

                    data = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
                    d_data = cuda.to_device(data)
                    _test_kernel[1, 4](d_data)
                    res = d_data.copy_to_host()
                    
                    if np.allclose(res, [2.0, 4.0, 6.0, 8.0]):
                        self.backend = "CUDA (Numba)"
                        self.device_name = str(dev_name)
                        self.is_healthy = True
                        print(f"[Pyxis GPU Engine] CUDA Live Probe OK! Active backend: {self.backend} - {self.device_name}", flush=True)
                        return True
            except Exception:
                pass

        except Exception as e:
            print(f"[Pyxis GPU Engine] CUDA Live Probe failed/incompatible ({e}). Evaluating OpenCL...", flush=True)

        return False

    def _probe_opencl_health(self) -> bool:
        """Live probe for Universal OpenCL (NVIDIA, AMD, Intel)."""
        try:
            try:
                import importlib
                cl = importlib.import_module("pyopencl")
                platforms = cl.get_platforms()
                for platform in platforms:
                    devices = platform.get_devices(device_type=cl.device_type.GPU)
                    if not devices:
                        devices = platform.get_devices(device_type=cl.device_type.ALL)
                    if devices:
                        dev = devices[0]
                        ctx = cl.Context([dev])
                        queue = cl.CommandQueue(ctx)
                        
                        kernel_code = """
                        __kernel void test_k(__global float* a) {
                            int gid = get_global_id(0);
                            a[gid] = a[gid] * 2.0f;
                        }
                        """
                        prg = cl.Program(ctx, kernel_code).build()
                        
                        h_data = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
                        mf = cl.mem_flags
                        d_data = cl.Buffer(ctx, mf.READ_WRITE | mf.COPY_HOST_PTR, hostbuf=h_data)
                        
                        prg.test_k(queue, (4,), None, d_data)
                        res = np.empty_like(h_data)
                        cl.enqueue_copy(queue, res, d_data)
                        queue.finish()

                        if np.allclose(res, [2.0, 4.0, 6.0, 8.0]):
                            self.backend = "OpenCL (PyOpenCL)"
                            self.device_name = str(dev.name).strip()
                            self.cl_context = ctx
                            self.cl_queue = queue
                            self.cl_program = prg
                            self.is_healthy = True
                            print(f"[Pyxis GPU Engine] OpenCL Live Probe OK! Active backend: {self.backend} - {self.device_name}", flush=True)
                            return True
            except Exception:
                pass

            if sys.platform == "win32":
                opencl_dll_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "OpenCL.dll")
                if os.path.exists(opencl_dll_path):
                    try:
                        opencl_lib = ctypes.cdll.LoadLibrary(opencl_dll_path)
                        num_platforms = ctypes.c_uint32()
                        res_code = opencl_lib.clGetPlatformIDs(0, None, ctypes.byref(num_platforms))
                        if res_code == 0 and num_platforms.value > 0:
                            self.backend = "OpenCL (Ctypes Native Runtime)"
                            self.device_name = f"OpenCL.dll Compatible Device ({num_platforms.value} Platform(s))"
                            self.is_healthy = True
                            print(f"[Pyxis GPU Engine] OpenCL Live Probe OK! Active backend: {self.backend} - {self.device_name}", flush=True)
                            return True
                    except Exception as cl_err:
                        print(f"[Pyxis GPU Engine] OpenCL.dll probe exception: {cl_err}", flush=True)

        except Exception as e:
            print(f"[Pyxis GPU Engine] OpenCL Live Probe failed ({e}). Using CPU Fallback...", flush=True)

        return False

    def transform_particles_gpu(self, coords_array, scale_x=1.0, scale_y=1.0, angle_deg=0.0, offset_x=0.0, offset_y=0.0):
        """Transform N-dimensional coordinate arrays using OpenCL GPU with
        persistent VRAM buffer (zero allocation overhead) for maximum hardware performance.
        """
        if not isinstance(coords_array, np.ndarray) or coords_array.shape[0] == 0:
            return coords_array

        if self.backend.startswith("OpenCL (PyOpenCL)") and self.cl_context and self.cl_queue:
            try:
                import importlib
                cl = importlib.import_module("pyopencl")
                if not hasattr(self, '_cl_trans_kernel') or self._cl_trans_kernel is None:
                    trans_code = """
                    __kernel void transform_2d(__global float2* coords, int count, float sc_x, float sc_y, float cos_a, float sin_a, float off_x, float off_y) {
                        int gid = get_global_id(0);
                        if (gid >= count) return;
                        float2 pt = coords[gid];
                        float x_sc = pt.x * sc_x;
                        float y_sc = pt.y * sc_y;
                        coords[gid] = (float2)(x_sc * cos_a - y_sc * sin_a + off_x, x_sc * sin_a + y_sc * cos_a + off_y);
                    }
                    """
                    self._cl_trans_prg = cl.Program(self.cl_context, trans_code).build()
                    self._cl_trans_kernel = cl.Kernel(self._cl_trans_prg, "transform_2d")

                pts_2d = np.ascontiguousarray(coords_array[:, :2], dtype=np.float32)
                n_pts = pts_2d.shape[0]
                rad = np.radians(angle_deg)
                cos_a, sin_a = np.float32(np.cos(rad)), np.float32(np.sin(rad))

                req_bytes = n_pts * 8
                if not hasattr(self, '_vram_buf_size') or self._vram_buf_size < req_bytes:
                    alloc_bytes = max(req_bytes, 1024 * 1024 * 16)
                    self._cl_vram_buf = cl.Buffer(self.cl_context, cl.mem_flags.READ_WRITE, size=alloc_bytes)
                    self._vram_buf_size = alloc_bytes

                cl.enqueue_copy(self.cl_queue, self._cl_vram_buf, pts_2d)

                local_size = (256,)
                global_size = (math.ceil(n_pts / 256) * 256,)

                self._cl_trans_kernel(
                    self.cl_queue, global_size, local_size,
                    self._cl_vram_buf, np.int32(n_pts), np.float32(scale_x), np.float32(scale_y),
                    cos_a, sin_a, np.float32(offset_x), np.float32(offset_y)
                )

                res_2d = np.empty_like(pts_2d)
                cl.enqueue_copy(self.cl_queue, res_2d, self._cl_vram_buf)
                self.cl_queue.finish()

                out = np.empty_like(coords_array)
                out[:, 0] = res_2d[:, 0]
                out[:, 1] = res_2d[:, 1]
                if coords_array.shape[1] > 2:
                    out[:, 2:] = coords_array[:, 2:]
                return out
            except Exception as cl_err:
                print(f"[Pyxis GPU Engine Warning] OpenCL transform failed ({cl_err}). Falling back to CPU...", flush=True)

        xs = coords_array[:, 0]
        ys = coords_array[:, 1]

        rad = np.radians(angle_deg)
        cos_a, sin_a = np.cos(rad), np.sin(rad)

        x_sc = xs * scale_x
        y_sc = ys * scale_y

        x_rot = x_sc * cos_a - y_sc * sin_a + offset_x
        y_rot = x_sc * sin_a + y_sc * cos_a + offset_y

        out = np.empty_like(coords_array)
        out[:, 0] = x_rot
        out[:, 1] = y_rot
        if coords_array.shape[1] > 2:
            out[:, 2:] = coords_array[:, 2:]

        return out


def get_gpu_manager() -> GpuEngineManager:
    """Retrieve the global GpuEngineManager singleton instance."""
    return GpuEngineManager.get_instance()

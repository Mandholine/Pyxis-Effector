# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Adapters (Telemetry Adapter)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

import os
import shutil
import subprocess
import sys
from typing import Any, Dict, Optional, Tuple

from ..engine.telemetry import GLOBAL_TELEMETRY_MANAGER, ASSTelemetryManager
from ..engine.system import BIN_DIR, get_bin_path


class TelemetryAdapter:
    """Adapter for running frame-by-frame ASS telemetry and profiling.

    Supports native execution on Windows, Linux, and macOS via libass_profiler.
    """

    @staticmethod
    def get_manager() -> ASSTelemetryManager:
        return GLOBAL_TELEMETRY_MANAGER

    @staticmethod
    def get_runner_info() -> Dict[str, Any]:
        """Returns details about the profiler binary and execution mode."""
        mgr = GLOBAL_TELEMETRY_MANAGER
        runner = mgr._resolve_runner()
        exe = mgr.profiler_exe
        return {
            "profiler_path": exe,
            "exists": bool(exe and os.path.isfile(exe)),
            "is_native": runner.get("kind") == "native",
            "runner_kind": runner.get("kind"),
            "error": runner.get("error"),
        }

    @staticmethod
    def analyze_content(
        ass_content: str,
        fps: float = 23.976,
        clip_start_ms: Optional[int] = None,
        clip_end_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Runs telemetry profiling on ASS text content."""
        return GLOBAL_TELEMETRY_MANAGER.run_telemetry(
            ass_content=ass_content,
            fps=fps,
            clip_start_ms=clip_start_ms,
            clip_end_ms=clip_end_ms,
        )

    @staticmethod
    def analyze_file(
        ass_file_path: str,
        fps: float = 23.976,
        clip_start_ms: Optional[int] = None,
        clip_end_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Reads an ASS file and runs telemetry profiling."""
        if not os.path.isfile(ass_file_path):
            raise FileNotFoundError(f"ASS file not found: {ass_file_path}")
        with open(ass_file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return TelemetryAdapter.analyze_content(
            ass_content=content,
            fps=fps,
            clip_start_ms=clip_start_ms,
            clip_end_ms=clip_end_ms,
        )

    @classmethod
    def compile_native_profiler(cls) -> Tuple[bool, str]:
        """Attempts to compile the native C profiler on the local machine.

        Supports Linux, macOS (clang/gcc), and Windows (MSYS2/MinGW gcc).
        Places the compiled binary in `bin/` so it is immediately picked up.
        """
        source_c = os.path.join(BIN_DIR, "libass_profiler_native", "libass_profiler.c")
        if not os.path.isfile(source_c):
            # Fallback to check relative paths
            alt = os.path.join(os.path.dirname(BIN_DIR), "bin", "libass_profiler_native", "libass_profiler.c")
            if os.path.isfile(alt):
                source_c = alt
            else:
                return False, f"Source file libass_profiler.c not found at {source_c}"

        target_name = "libass_profiler.exe" if os.name == "nt" else "libass_profiler"
        target_bin = os.path.join(BIN_DIR, target_name)
        os.makedirs(BIN_DIR, exist_ok=True)

        # Detect compiler
        compiler = "clang" if sys.platform == "darwin" and shutil.which("clang") else ("gcc" if shutil.which("gcc") else None)
        if not compiler:
            return False, "Neither 'clang' nor 'gcc' compiler was found on the system PATH."

        cmd = [compiler, "-O3", "-Wall", "-Wextra", "-std=c99", source_c, "-o", target_bin]

        # Add include/lib flags for Homebrew on macOS
        if sys.platform == "darwin":
            for brew_prefix in ("/opt/homebrew", "/usr/local"):
                if os.path.isdir(brew_prefix):
                    cmd.extend([f"-I{brew_prefix}/include", f"-L{brew_prefix}/lib"])

        cmd.extend(["-lass", "-lm"])

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0 and os.path.isfile(target_bin):
                # Ensure executable permissions on POSIX
                if os.name != "nt":
                    os.chmod(target_bin, 0o755)
                # Update manager's executable pointer
                GLOBAL_TELEMETRY_MANAGER.profiler_exe = target_bin
                return True, f"Successfully compiled native profiler to {target_bin}"
            else:
                return False, f"Compilation failed (code {res.returncode}):\n{res.stderr}\n\nHint: Install libass (e.g. 'brew install libass' on macOS, 'sudo apt install libass-dev' on Ubuntu)."
        except Exception as e:
            return False, f"Error executing compiler: {str(e)}"

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
Module: process_utils.py
Architectural Role: Process lifecycle management and orphan process watchdog.

Upstream Dependencies:
    - os, sys, threading, time: Standard library process and thread management.

Downstream Callers:
    - main.py: Starts parent watchdog on POSIX platforms to ensure cleanup when Aegisub exits.
    - pyxis_daemon.py: Supervises daemon lifetime against parent Aegisub process.

Side Effects and State:
    - Spawns a background daemon thread that periodically inspects os.getppid() on POSIX.
    - If parent process changes (adopted by init or subreaper after Aegisub terminates),
      terminates the current process immediately with os._exit(1).
    - On Windows, no-op (returns None) as lifecycle is bound to Windows Job Objects.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from typing import Optional


def start_parent_watchdog(interval: float = 1.0) -> Optional[threading.Thread]:
    """
    Starts a background daemon thread monitoring parent PID on POSIX systems.

    On non-Windows systems (Linux/macOS), if Aegisub crashes or closes forcefully,
    the child process is adopted by PID 1 (init/systemd) or a session manager subreaper.
    This watchdog detects when os.getppid() differs from the original parent PID
    and calls os._exit(1) to avoid leaving orphan daemon or GUI processes running.

    On Windows (os.name == 'nt'), lifecycle termination is handled natively via
    Windows Job Objects (_setup_windows_job_object), so this function returns None.

    Args:
        interval (float, optional): Inspection interval in seconds. Defaults to 1.0.

    Returns:
        Optional[threading.Thread]: Watchdog thread instance on POSIX, or None on Windows.
    """
    if os.name == "nt":
        return None

    try:
        orig_ppid = os.getppid()
    except Exception:
        return None

    # If already orphaned or top-level process, do not monitor
    if orig_ppid <= 1:
        return None

    def _watchdog_loop() -> None:
        while True:
            time.sleep(interval)
            try:
                current_ppid = os.getppid()
                if current_ppid != orig_ppid:
                    # Parent Aegisub process terminated; exit immediately
                    os._exit(1)
            except Exception:
                break

    watchdog_thread = threading.Thread(
        target=_watchdog_loop,
        name="PyxisParentWatchdog",
        daemon=True,
    )
    watchdog_thread.start()
    return watchdog_thread


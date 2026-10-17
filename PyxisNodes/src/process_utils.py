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

"""Utilidades de ciclo de vida de procesos independientes de la plataforma."""

import os
import threading
import time


def start_parent_watchdog(interval: float = 1.0):
    """Hace que un proceso hijo termine si su padre muere (Linux/macOS).

    Windows ya lo resuelve con un Job Object (KILL_ON_JOB_CLOSE) y Linux además usa
    PR_SET_PDEATHSIG, pero ninguno cubre macOS ni los workers creados con
    spawn/forkserver. Si el padre desaparece, el proceso queda adoptado por otro
    (cambia ``os.getppid()``) y el watchdog lo termina.
    """
    if os.name == "nt":
        return None

    parent_pid = os.getppid()

    def _watch():
        while True:
            time.sleep(interval)
            if os.getppid() != parent_pid:
                os._exit(1)

    thread = threading.Thread(target=_watch, name="pyxis-parent-watchdog", daemon=True)
    thread.start()
    return thread

# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 Pyxis Effector contributors
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

"""Utilidades compartidas por los scripts de tools/ (solo biblioteca estándar)."""

import hashlib
import http.client
import os
import platform
import shutil
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
NODES_DIR = REPO_ROOT / "PyxisNodes"

PLATFORMS = ("win64", "linux64", "linux-arm64", "macos-arm64", "macos-x64")


def log(msg: str) -> None:
    print(f"==> {msg}", flush=True)


def warn(msg: str) -> None:
    print(f"[!!] {msg}", file=sys.stderr, flush=True)


def host_platform() -> str:
    machine = platform.machine().lower()
    arm = machine in ("arm64", "aarch64")
    system = platform.system()
    if system == "Windows":
        if arm:
            raise SystemExit("Windows ARM64 no está soportado todavía.")
        return "win64"
    if system == "Darwin":
        return "macos-arm64" if arm else "macos-x64"
    if system == "Linux":
        return "linux-arm64" if arm else "linux64"
    raise SystemExit(f"Sistema no soportado: {system}")


def http_get(url: str, dest: Optional[Path] = None):
    """Descarga ``url`` (con reintentos). Devuelve los bytes, o None si se guarda en ``dest``."""
    headers = {"User-Agent": "pyxis-tools"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    attempts = 4
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                if dest is None:
                    return response.read()
                with open(dest, "wb") as out:
                    shutil.copyfileobj(response, out)
            return None
        except (OSError, http.client.HTTPException) as exc:
            if attempt == attempts:
                raise
            warn(f"Descarga fallida ({exc}); reintento {attempt}/{attempts - 1}")
            time.sleep(2 * attempt)


def resolve_redirects(url: str) -> str:
    """URL final tras seguir las redirecciones (solo se lee el primer byte del cuerpo)."""
    request = urllib.request.Request(url, headers={"User-Agent": "pyxis-tools", "Range": "bytes=0-0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.geturl()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fp:
        for block in iter(lambda: fp.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()

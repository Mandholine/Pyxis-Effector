#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""Shared utilities for the tools/ release and build scripts (standard library only)."""

import argparse
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
    """Print an informational step message to stdout."""
    print(f"==> {msg}", flush=True)


def warn(msg: str) -> None:
    """Print a warning message to stderr."""
    print(f"[!!] {msg}", file=sys.stderr, flush=True)


def host_platform() -> str:
    """Detect the canonical Pyxis target platform identifier for the current machine."""
    machine = platform.machine().lower()
    arm = machine in ("arm64", "aarch64")
    system = platform.system()
    if system == "Windows":
        if arm:
            raise SystemExit("Windows ARM64 is not supported yet.")
        return "win64"
    if system == "Darwin":
        return "macos-arm64" if arm else "macos-x64"
    if system == "Linux":
        return "linux-arm64" if arm else "linux64"
    raise SystemExit(f"Unsupported operating system: {system}")


def http_get(url: str, dest: Optional[Path] = None):
    """Download ``url`` with automatic retries. Returns raw bytes, or None if saved to ``dest``."""
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
            warn(f"Download failed ({exc}); retry {attempt}/{attempts - 1}")
            time.sleep(2 * attempt)


def resolve_redirects(url: str) -> str:
    """Return the final URL after following HTTP redirects (reads only the first response byte)."""
    request = urllib.request.Request(url, headers={"User-Agent": "pyxis-tools", "Range": "bytes=0-0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.geturl()


def sha256_file(path: Path) -> str:
    """Compute the lowercase hexadecimal SHA-256 digest of ``path``."""
    digest = hashlib.sha256()
    with open(path, "rb") as fp:
        for block in iter(lambda: fp.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    """CLI entry point to inspect the detected host platform and repository paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-platform", action="store_true", help="print the detected host platform and exit")
    args = parser.parse_args()
    plat = host_platform()
    if args.print_platform:
        print(plat)
    else:
        log(f"Host platform : {plat}")
        log(f"Repo root     : {REPO_ROOT}")
        log(f"PyxisNodes dir: {NODES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


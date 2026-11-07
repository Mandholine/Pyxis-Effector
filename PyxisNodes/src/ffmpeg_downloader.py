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

"""On-demand FFmpeg native binary downloader and verification manager.

Provides background downloading, SHA-256 checksum verification, and atomic
installation of verified native static FFmpeg binaries for Windows, Linux,
and macOS without requiring external dependencies (standard library only).
"""

from __future__ import annotations

import hashlib
import http.client
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from paths import BIN_DIR, get_bin_path, get_user_data_dir

BTBN_BASE = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
BTBN_BRANCH = "8.0"
BTBN_TARGETS = {
    "win64": ("win64", "zip"),
    "linux64": ("linux64", "tar.xz"),
    "linux-arm64": ("linuxarm64", "tar.xz"),
}
MARTIN_RIEDL = "https://ffmpeg.martin-riedl.de/redirect/latest/macos/{arch}/release/ffmpeg.zip"
MARTIN_RIEDL_ARCH = {"macos-arm64": "arm64", "macos-x64": "amd64"}

_LOCK = threading.Lock()
_STATE: Dict[str, Any] = {
    "status": "idle",
    "progress": 0,
    "detail": "",
    "error": "",
    "target_path": "",
}
_ACTIVE_THREAD: Optional[threading.Thread] = None


def detect_target_platform() -> str:
    """Detect canonical platform identifier matching release artifacts."""
    machine = platform.machine().lower()
    arm = machine in ("arm64", "aarch64")
    system = platform.system()
    if system == "Windows":
        return "win64"
    if system == "Darwin":
        return "macos-arm64" if arm else "macos-x64"
    if system == "Linux":
        return "linux-arm64" if arm else "linux64"
    raise RuntimeError(f"Unsupported operating system: {system}")


def get_download_state() -> Dict[str, Any]:
    """Retrieve a snapshot of the current download and verification state."""
    with _LOCK:
        return dict(_STATE)


def _set_state(status: str, progress: int = 0, detail: str = "", error: str = "", target_path: str = "") -> None:
    with _LOCK:
        _STATE["status"] = status
        _STATE["progress"] = progress
        _STATE["detail"] = detail
        _STATE["error"] = error
        if target_path:
            _STATE["target_path"] = target_path


def _http_get(url: str, dest: Optional[Path] = None, progress_cb=None) -> bytes:
    headers = {"User-Agent": "PyxisEffector-FFmpegDownloader"}
    request = urllib.request.Request(url, headers=headers)
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                total_len = response.headers.get("Content-Length")
                total_bytes = int(total_len) if total_len and total_len.isdigit() else 0
                if dest is None:
                    return response.read()

                downloaded = 0
                chunk_size = 64 * 1024
                with open(dest, "wb") as out:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        out.write(chunk)
                        downloaded += len(chunk)
                        if progress_cb and total_bytes > 0:
                            progress_cb(downloaded, total_bytes)
                return b""
        except (OSError, http.client.HTTPException) as exc:
            if attempt == attempts:
                raise
            time.sleep(2 * attempt)
    return b""


def _resolve_redirects(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "PyxisEffector-FFmpegDownloader", "Range": "bytes=0-0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.geturl()


def _first_hash(text: str, filename: Optional[str] = None) -> Optional[str]:
    for line in text.splitlines():
        parts = line.split()
        if (
            parts
            and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0])
            and (filename is None or len(parts) == 1 or parts[-1].lstrip("*") == filename)
        ):
            return parts[0].lower()
    return None


def _resolve_source_info(plat: str) -> Dict[str, str]:
    if plat in BTBN_TARGETS:
        key, ext = BTBN_TARGETS[plat]
        raw_checksums = _http_get(BTBN_BASE + "checksums.sha256").decode("utf-8", "replace")

        # 1. Prefer permanent master-latest asset which is always kept current in BtbN releases
        preferred_fn = f"ffmpeg-master-latest-{key}-gpl.{ext}"
        digest = _first_hash(raw_checksums, preferred_fn)
        filename = preferred_fn

        # 2. Dynamic fallback: scan checksums.sha256 for release branch assets if master is unavailable
        if not digest:
            for line in raw_checksums.splitlines():
                parts = line.split()
                if len(parts) >= 2 and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
                    candidate = parts[-1].lstrip("*")
                    if (
                        f"-{key}-gpl" in candidate
                        and candidate.endswith(f".{ext}")
                        and "shared" not in candidate
                    ):
                        filename = candidate
                        digest = parts[0].lower()
                        break

        if not digest:
            raise RuntimeError(f"Could not locate SHA-256 for {key} in BtbN checksums.sha256")
        return {
            "provider": "BtbN/FFmpeg-Builds",
            "url": BTBN_BASE + filename,
            "filename": filename,
            "sha256": digest,
        }

    if plat in MARTIN_RIEDL_ARCH:
        final_url = _resolve_redirects(MARTIN_RIEDL.format(arch=MARTIN_RIEDL_ARCH[plat]))
        raw_checksums = _http_get(final_url + ".sha256").decode("utf-8", "replace")
        digest = _first_hash(raw_checksums)
        if not digest:
            raise RuntimeError(f"Could not read SHA-256 checksum from {final_url}.sha256")
        return {
            "provider": "ffmpeg.martin-riedl.de",
            "url": final_url,
            "filename": final_url.rsplit("/", 1)[-1],
            "sha256": digest,
        }

    raise RuntimeError(f"Unsupported platform for automated FFmpeg download: {plat}")


def _extract_binary(archive: Path, exe_name: str, dest_path: Path) -> bool:
    lowered = archive.name.lower()
    if lowered.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            for member in zf.namelist():
                if Path(member).name == exe_name and not member.endswith("/"):
                    with zf.open(member) as src, open(dest_path, "wb") as out:
                        shutil.copyfileobj(src, out)
                    return True
        return False

    if lowered.endswith((".tar.xz", ".tar.gz", ".tgz", ".tar.bz2", ".tar")):
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                if member.isfile() and Path(member.name).name == exe_name:
                    extracted = tar.extractfile(member)
                    if extracted is not None:
                        with open(dest_path, "wb") as out:
                            shutil.copyfileobj(extracted, out)
                        return True
        return False

    return False


def _choose_install_dir() -> Path:
    """Select destination directory: preference for PyxisNodes/bin, fallback to user data dir if read-only."""
    pkg_bin = Path(BIN_DIR)
    try:
        pkg_bin.mkdir(parents=True, exist_ok=True)
        test_file = pkg_bin / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        return pkg_bin
    except OSError:
        pass

    user_bin = Path(get_user_data_dir()) / "bin"
    user_bin.mkdir(parents=True, exist_ok=True)
    return user_bin


def _run_download_workflow() -> None:
    work_dir = None
    try:
        _set_state("resolving", 5, "Resolving official release...")
        plat = detect_target_platform()
        source = _resolve_source_info(plat)

        exe_target_name = "ffmpeg.exe" if plat == "win64" else "ffmpeg"
        work_dir = Path(tempfile.mkdtemp(prefix="pyxis_ff_dl_"))
        archive_path = work_dir / source["filename"]

        def _progress_cb(downloaded: int, total: int):
            pct = min(90, int(10 + (downloaded / total) * 75))
            mb_down = downloaded / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            _set_state(
                "downloading",
                pct,
                f"Downloading {mb_down:.1f} MB / {mb_tot:.1f} MB ({int(downloaded/total*100)}%)...",
            )

        _set_state("downloading", 10, "Connecting to release server...")
        _http_get(source["url"], archive_path, progress_cb=_progress_cb)

        _set_state("verifying", 88, "Verifying SHA-256 checksum...")
        hasher = hashlib.sha256()
        with open(archive_path, "rb") as fp:
            for chunk in iter(lambda: fp.read(1 << 20), b""):
                hasher.update(chunk)
        actual_hash = hasher.hexdigest().lower()
        if source.get("sha256") and actual_hash != source["sha256"].lower():
            raise RuntimeError(
                f"Checksum mismatch for FFmpeg archive.\nExpected: {source['sha256']}\nActual: {actual_hash}"
            )

        _set_state("extracting", 92, "Extracting native binary...")
        dest_dir = _choose_install_dir()
        dest_file = dest_dir / exe_target_name
        if not _extract_binary(archive_path, exe_target_name, dest_file):
            raise RuntimeError(f"Could not find {exe_target_name} inside {archive_path.name}")

        try:
            dest_file.chmod(dest_file.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            pass

        # Write notice
        notice_path = dest_dir / "FFMPEG-NOTICE.txt"
        notice_path.write_text(
            f"FFmpeg binary for Pyxis Effector ({plat})\n"
            f"Provider : {source['provider']}\n"
            f"URL      : {source['url']}\n"
            f"SHA-256  : {actual_hash}\n"
            "This FFmpeg binary is distributed under GPL with libx264, libass, and libwebp enabled.\n",
            encoding="utf-8",
        )

        _set_state("ready", 100, f"FFmpeg installed successfully at {dest_file}", target_path=str(dest_file))
    except Exception as exc:
        _set_state("error", 0, "", error=str(exc))
    finally:
        if work_dir and work_dir.is_dir():
            shutil.rmtree(work_dir, ignore_errors=True)


def start_download() -> bool:
    """Launches the background download and verification thread if not already running."""
    global _ACTIVE_THREAD
    with _LOCK:
        if _STATE["status"] in ("resolving", "downloading", "verifying", "extracting"):
            return True
        _STATE["status"] = "resolving"
        _STATE["progress"] = 0
        _STATE["detail"] = "Starting download..."
        _STATE["error"] = ""
        _STATE["target_path"] = ""

    _ACTIVE_THREAD = threading.Thread(
        target=_run_download_workflow,
        name="PyxisFFmpegDownloader",
        daemon=True,
    )
    _ACTIVE_THREAD.start()
    return True


def check_ffmpeg_availability() -> Dict[str, Any]:
    """Inspects whether a valid, runnable FFmpeg binary is available on the system."""
    ff_path = get_bin_path("ffmpeg")
    if os.path.isfile(ff_path):
        return {"available": True, "path": ff_path, "bundled": True}

    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg and os.path.isfile(sys_ffmpeg):
        return {"available": True, "path": sys_ffmpeg, "bundled": False}

    return {"available": False, "path": "", "bundled": False}


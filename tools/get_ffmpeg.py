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

"""Provision the native FFmpeg binary required by Pyxis: download a verified static build or compile from source.

FFmpeg officially distributes source code (https://ffmpeg.org/download.html), while prebuilt binaries
linked from their download page are provided by third-party builders. By default, this script downloads
and verifies SHA-256 checksums from:

    win64, linux64, linux-arm64   BtbN/FFmpeg-Builds (release branch n8.0, GPL variant)
    macos-arm64, macos-x64        ffmpeg.martin-riedl.de (stable release, native builds)

The build includes libx264, libwebp, and libass (`subtitles` filter), which Pyxis requires for
audio extraction, waveform decoding, and subtitle-burned video export.

    python tools/get_ffmpeg.py                   # download ffmpeg for the host platform into PyxisNodes/bin
    python tools/get_ffmpeg.py --build           # compile from source (see tools/build_ffmpeg.py)
    python tools/get_ffmpeg.py --url <url> --sha256 <hash>   # custom hosted archive
    python tools/get_ffmpeg.py --list-sources

Uses only the Python standard library.
"""

import argparse
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NODES_DIR, PLATFORMS, host_platform, http_get, log, resolve_redirects, sha256_file, warn  # noqa: E402

BTBN_BASE = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
BTBN_BRANCH = "8.0"  # stable release branch (not "master" development snapshot)
BTBN_TARGETS = {
    "win64": ("win64", "zip"),
    "linux64": ("linux64", "tar.xz"),
    "linux-arm64": ("linuxarm64", "tar.xz"),
}
MARTIN_RIEDL = "https://ffmpeg.martin-riedl.de/redirect/latest/macos/{arch}/release/ffmpeg.zip"
MARTIN_RIEDL_ARCH = {"macos-arm64": "arm64", "macos-x64": "amd64"}

SOURCE_TARBALL = "https://ffmpeg.org/releases/ffmpeg-{version}.tar.xz"
SOURCES_PAGE = "https://ffmpeg.org/download.html#get-sources"


def exe_name(plat: str) -> str:
    """Return the platform-specific executable filename for FFmpeg."""
    return "ffmpeg.exe" if plat == "win64" else "ffmpeg"


def _first_hash(text: str, filename: Optional[str] = None) -> Optional[str]:
    """Extract a SHA-256 hex digest from a checksum manifest ('<hash>  <file>' or standalone hash)."""
    for line in text.splitlines():
        parts = line.split()
        if (
            parts
            and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0])
            and (filename is None or len(parts) == 1 or parts[-1].lstrip("*") == filename)
        ):
            return parts[0].lower()
    return None


def default_source(plat: str) -> dict:
    """Resolve the default hosted build metadata (URL and upstream SHA-256 digest) for ``plat``."""
    if plat in BTBN_TARGETS:
        key, ext = BTBN_TARGETS[plat]
        filename = f"ffmpeg-n{BTBN_BRANCH}-latest-{key}-gpl-{BTBN_BRANCH}.{ext}"
        checksums = http_get(BTBN_BASE + "checksums.sha256").decode("utf-8", "replace")
        digest = _first_hash(checksums, filename)
        if not digest:
            raise SystemExit(f"{filename} not found in BtbN checksums.sha256; did the release branch change?")
        return {
            "provider": "BtbN/FFmpeg-Builds",
            "url": BTBN_BASE + filename,
            "filename": filename,
            "sha256": digest,
        }

    if plat in MARTIN_RIEDL_ARCH:
        final_url = resolve_redirects(MARTIN_RIEDL.format(arch=MARTIN_RIEDL_ARCH[plat]))
        digest = _first_hash(http_get(final_url + ".sha256").decode("utf-8", "replace"))
        if not digest:
            raise SystemExit(f"Could not read SHA-256 checksum from {final_url}.sha256")
        return {
            "provider": "ffmpeg.martin-riedl.de",
            "url": final_url,
            "filename": final_url.rsplit("/", 1)[-1],
            "sha256": digest,
        }

    raise SystemExit(f"Unknown target platform: {plat}")


def extract_binary(archive: Path, name: str, dest: Path) -> bool:
    """Extract the executable named ``name`` from a zip or tar archive regardless of inner folder depth."""
    lowered = archive.name.lower()
    if lowered.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            for member in zf.namelist():
                if Path(member).name == name and not member.endswith("/"):
                    with zf.open(member) as src, open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)
                    return True
        return False
    if lowered.endswith((".tar.xz", ".tar.gz", ".tgz", ".tar.bz2", ".tar")):
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                if member.isfile() and Path(member.name).name == name:
                    extracted = tar.extractfile(member)
                    if extracted is not None:
                        with open(dest, "wb") as out:
                            shutil.copyfileobj(extracted, out)
                        return True
        return False
    return False


def describe_binary(binary: Path) -> dict:
    """Query the version and build configuration if the binary can run on the current host."""
    try:
        text = subprocess.run([str(binary), "-version"], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    info = {}
    first = text.splitlines()[0] if text else ""
    match = re.match(r"ffmpeg version (\S+)", first)
    if match:
        info["version_string"] = match.group(1)
    config = re.search(r"^configuration:\s*(.+)$", text, re.M)
    if config:
        info["configuration"] = config.group(1).strip()
    return info


def write_notice(dest_dir: Path, plat: str, info: dict) -> None:
    """Write ``FFMPEG-NOTICE.txt`` alongside the binary documenting provenance and GPL source availability."""
    version_match = re.match(r"n?(\d+\.\d+(?:\.\d+)?)", info.get("version_string", ""))
    source = SOURCE_TARBALL.format(version=version_match.group(1)) if version_match else SOURCES_PAGE
    lines = [
        "FFmpeg Bundled Notice",
        "=====================",
        "",
        f"Platform : {plat}",
        f"Provider : {info.get('provider', 'unknown')}",
        f"Download : {info.get('url', '-')}",
        f"SHA-256  : {info.get('sha256', '-')}",
        f"Version  : {info.get('version_string', 'see `ffmpeg -version`')}",
        "",
        "This FFmpeg binary is a GPL build (including libx264, libass, libwebp, etc.).",
        "FFmpeg is free software; its source code and library sources are available at:",
        f"  {source}",
        "Run `ffmpeg -buildconf` to inspect the exact build configuration.",
        "",
        "To compile FFmpeg from source yourself: python tools/get_ffmpeg.py --build",
        "",
    ]
    (dest_dir / "FFMPEG-NOTICE.txt").write_text("\n".join(lines), encoding="utf-8")


def install(
    plat: str,
    dest_dir: Path,
    *,
    url: Optional[str] = None,
    sha256: Optional[str] = None,
    path: Optional[str] = None,
    build: bool = False,
    build_options: Optional[dict] = None,
    work: Optional[Path] = None,
) -> dict:
    """Install ``ffmpeg`` into ``dest_dir`` and return provenance metadata."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = exe_name(plat)
    dest = dest_dir / name
    own_work = work is None
    work = Path(tempfile.mkdtemp(prefix="pyxis_ffmpeg_")) if own_work else work

    try:
        if build:
            if plat != host_platform():
                raise SystemExit(f"To compile ffmpeg for {plat}, run this script on a {plat} host.")
            import build_ffmpeg
            built = build_ffmpeg.build(out_dir=dest_dir, **(build_options or {}))
            info = {
                "provider": "compiled from official source (ffmpeg.org)",
                "url": built["source_url"],
                "sha256": sha256_file(dest),
                "build": built,
            }
        else:
            if path:
                archive = Path(path)
                if not archive.is_file():
                    raise SystemExit(f"Specified ffmpeg file does not exist: {archive}")
                info = {"provider": "local file", "url": str(archive), "sha256": sha256_file(archive)}
            else:
                source = (
                    {
                        "provider": "custom URL",
                        "url": url,
                        "filename": url.split("?", 1)[0].rsplit("/", 1)[-1],
                        "sha256": sha256,
                    }
                    if url
                    else default_source(plat)
                )
                archive = work / source["filename"]
                log(f"Downloading ffmpeg ({source['provider']})")
                http_get(source["url"], archive)
                actual = sha256_file(archive)
                if source.get("sha256"):
                    if actual != source["sha256"].lower():
                        raise SystemExit(
                            f"FFmpeg SHA-256 mismatch.\n  expected: {source['sha256']}\n  actual  : {actual}"
                        )
                    log("SHA-256 verified")
                else:
                    warn(f"No reference SHA-256 provided; downloaded archive digest is {actual}")
                info = {"provider": source["provider"], "url": source["url"], "sha256": actual}

            if archive.name == name:
                shutil.copy2(archive, dest)
            elif not extract_binary(archive, name, dest):
                raise SystemExit(f"Could not find {name} inside {archive.name}")

        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        if plat == host_platform():
            info.update(describe_binary(dest))
        write_notice(dest_dir, plat, info)
        log(f"ffmpeg installed: {dest} {info.get('version_string', '')}".rstrip())
        return info
    finally:
        if own_work:
            shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platform", choices=PLATFORMS, help="target platform (default: current host)")
    parser.add_argument("--out", default=str(NODES_DIR / "bin"), help="destination directory (default: PyxisNodes/bin)")
    parser.add_argument("--url", help="download this archive (zip/tar) instead of the default provider build")
    parser.add_argument("--sha256", help="expected SHA-256 hex digest for --url")
    parser.add_argument("--path", help="use a local ffmpeg binary or archive containing it")
    parser.add_argument("--build", action="store_true", help="compile from source instead of downloading")
    parser.add_argument("--ffmpeg-version", help="with --build: ffmpeg version to compile")
    parser.add_argument("--jobs", type=int, help="with --build: parallel make jobs")
    parser.add_argument("--list-sources", action="store_true", help="display default upstream source per platform and exit")
    args = parser.parse_args()

    if args.list_sources:
        for plat in PLATFORMS:
            src = default_source(plat)
            print(f"{plat:12} {src['provider']:24} {src['url']}\n{'':12} sha256 {src['sha256']}")
        return 0

    plat = args.platform or host_platform()
    options = {k: v for k, v in (("version", args.ffmpeg_version), ("jobs", args.jobs)) if v}
    install(
        plat,
        Path(args.out),
        url=args.url,
        sha256=args.sha256,
        path=args.path,
        build=args.build,
        build_options=options,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())


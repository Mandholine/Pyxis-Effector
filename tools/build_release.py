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

"""Build a standalone multi-platform PyxisNodes release archive with embedded CPython and native binaries.

Generates ``dist/PyxisEffector-v<version>-<platform>.zip`` containing the self-contained
``PyxisNodes/`` directory ready for ``automation/autoload`` (the archive automatically
fetched by the Aegisub Lua bridge ``Pyxis_engine.lua``).

Each package bundles:
  - A standalone CPython interpreter from ``astral-sh/python-build-standalone``
  - Preinstalled dependencies from ``requirements.txt``, ``requirements-optional.txt``,
    and (on Linux) ``requirements-qt.txt``
  - 100% native platform binaries in ``PyxisNodes/bin/``:
    ``ffmpeg``, ``potrace``, ``img2ass``, and ``libass_profiler`` (zero Wine or emulation)

Usage:
    python tools/build_release.py                       # build for current host platform
    python tools/build_release.py --ffmpeg-build        # compile ffmpeg from source
    python tools/build_release.py --no-ffmpeg           # skip bundling ffmpeg

Uses only the Python standard library.
"""

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import get_ffmpeg  # noqa: E402
from common import NODES_DIR, PLATFORMS, REPO_ROOT, host_platform, http_get, log, sha256_file, warn  # noqa: E402

LUA_FILE = REPO_ROOT / "Pyxis_engine.lua"
VERSION_FILE = NODES_DIR / "src" / "version.py"

PBS_REPO = "astral-sh/python-build-standalone"

# Target platform -> python-build-standalone target triple
TARGETS = {
    "win64": "x86_64-pc-windows-msvc",
    "linux64": "x86_64-unknown-linux-gnu",
    "linux-arm64": "aarch64-unknown-linux-gnu",
    "macos-arm64": "aarch64-apple-darwin",
    "macos-x64": "x86_64-apple-darwin",
}


def read_version() -> str:
    """Read the canonical PYXIS_VERSION from ``PyxisNodes/src/version.py``."""
    if not VERSION_FILE.is_file():
        raise SystemExit(f"Canonical version file not found: {VERSION_FILE}")
    match = re.search(r'^PYXIS_VERSION\s*=\s*"([^"]+)"', VERSION_FILE.read_text(encoding="utf-8"), re.M)
    if not match:
        raise SystemExit(f"Could not find PYXIS_VERSION in {VERSION_FILE}")
    return match.group(1)


def resolve_python_url(version: str, triple: str, tag: Optional[str]) -> str:
    """Resolve the download URL for the latest matching CPython build from python-build-standalone."""
    api = f"https://api.github.com/repos/{PBS_REPO}/releases/" + (f"tags/{tag}" if tag else "latest")
    release = json.loads(http_get(api))
    pattern = re.compile(
        rf"^cpython-({re.escape(version)}\.\d+)\+\d+-{re.escape(triple)}-install_only_stripped\.tar\.gz$"
    )
    best = None
    for asset in release.get("assets", []):
        match = pattern.match(asset["name"])
        if match:
            patch = int(match.group(1).rsplit(".", 1)[1])
            if best is None or patch > best[0]:
                best = (patch, asset["browser_download_url"])
    if not best:
        raise SystemExit(f"python-build-standalone {release.get('tag_name')} has no CPython {version} asset for {triple}")
    log(f"Python: {best[1].rsplit('/', 1)[1]}")
    return best[1]


def extract_tar(archive: Path, dest: Path) -> None:
    """Extract a tar archive safely into ``dest``."""
    with tarfile.open(archive) as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(dest, filter="data")
        else:
            tar.extractall(dest)


def python_exe(python_dir: Path, plat: str) -> Path:
    """Return the path to the Python interpreter inside ``python_dir`` for ``plat``."""
    return python_dir / "python.exe" if plat == "win64" else python_dir / "bin" / "python3"


def install_python(stage_python: Path, plat: str, version: str, url: Optional[str], tag: Optional[str], work: Path) -> None:
    """Download and unpack standalone CPython into ``stage_python``."""
    triple = TARGETS[plat]
    url = url or resolve_python_url(version, triple, tag)
    archive = work / "python.tar.gz"
    log("Downloading standalone Python runtime")
    http_get(url, archive)
    unpack = work / "python_unpack"
    extract_tar(archive, unpack)
    inner = unpack / "python"
    if not inner.is_dir():
        raise SystemExit("Downloaded Python archive does not contain the expected 'python/' directory")
    shutil.move(str(inner), str(stage_python))


# Pure-Python packages published only as sdist on PyPI (pywebview -> proxy_tools).
SDIST_OK = "proxy_tools"


def pip_install(py: Path, args: list, check: bool = True) -> int:
    """Run pip install restricting to prebuilt binary wheels except for ``SDIST_OK``."""
    cmd = [
        str(py), "-m", "pip", "install",
        "--no-warn-script-location", "--disable-pip-version-check",
        "--only-binary=:all:", f"--no-binary={SDIST_OK}",
        *args,
    ]
    return subprocess.run(cmd, check=check).returncode


def read_requirements(path: Path) -> list:
    """Parse non-empty requirement specifications from ``path``."""
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            lines.append(line)
    return lines


def install_dependencies(py: Path, plat: str, with_qt: bool) -> None:
    """Install core, optional, and (on Linux) Qt WebEngine Python dependencies."""
    log("Installing required Python dependencies")
    pip_install(py, ["-r", str(NODES_DIR / "requirements.txt")])

    opt_file = NODES_DIR / "requirements-optional.txt"
    if opt_file.is_file():
        for spec in read_requirements(opt_file):
            log(f"Installing optional dependency: {spec}")
            if pip_install(py, [spec], check=False) != 0:
                warn(f"Could not install optional package {spec}; continuing without it")

    qt_file = NODES_DIR / "requirements-qt.txt"
    if with_qt and plat.startswith("linux") and qt_file.is_file():
        log("Installing Qt WebEngine (self-contained GUI backend for Linux)")
        pip_install(py, ["-r", str(qt_file)])


def build_native_tools(bin_src: Path, bin_dst: Path, plat: str, work: Path) -> None:
    """Provision native binaries (potrace, img2ass, libass_profiler) into ``bin_dst``."""
    bin_dst.mkdir(parents=True, exist_ok=True)
    if plat == "win64":
        for name in ("potrace.exe", "libass_profiler.exe", "img2ass.exe"):
            if (bin_src / name).is_file():
                shutil.copy2(bin_src / name, bin_dst / name)
        # If img2ass.exe is not prebuilt in bin/, compile it from potrace_native/src if a C compiler is available
        if not (bin_dst / "img2ass.exe").is_file():
            potrace_src = bin_src / "potrace_native" / "src"
            cc = shutil.which("gcc") or shutil.which("clang")
            if potrace_src.is_dir() and cc:
                log(f"Compiling native img2ass.exe on Windows using {cc}")
                cmd = [
                    cc, "-O3", "-DHAVE_CONFIG_H", f"-I{potrace_src}", f"-I{potrace_src.parent}",
                    str(potrace_src / "img2ass.c"),
                    str(potrace_src / "curve.c"),
                    str(potrace_src / "trace.c"),
                    str(potrace_src / "decompose.c"),
                    str(potrace_src / "potracelib.c"),
                    "-o", str(bin_dst / "img2ass.exe"), "-lm",
                ]
                subprocess.run(cmd, check=True)
        return

    # POSIX platforms (Linux & macOS): compile native potrace, img2ass, and libass_profiler from C source
    potrace_native_src = bin_src / "potrace_native"
    if potrace_native_src.is_dir():
        log("Compiling native potrace and img2ass from C99 source")
        potrace_work = work / "potrace_build" / "potrace_native"
        shutil.copytree(potrace_native_src, potrace_work)
        subprocess.run(["bash", str(potrace_work / "build.sh")], cwd=str(potrace_work), check=True)
        for tool_name in ("potrace", "img2ass"):
            built_bin = potrace_work.parent / tool_name
            if not built_bin.is_file():
                raise SystemExit(f"Native {tool_name} binary was not produced by potrace_native/build.sh")
            shutil.copy2(built_bin, bin_dst / tool_name)
            (bin_dst / tool_name).chmod(0o755)
    else:
        for tool_name in ("potrace", "img2ass"):
            if (bin_src / tool_name).is_file():
                shutil.copy2(bin_src / tool_name, bin_dst / tool_name)
                (bin_dst / tool_name).chmod(0o755)

    profiler_native_src = bin_src / "libass_profiler_native"
    if profiler_native_src.is_dir():
        log("Compiling native libass_profiler from C99 source")
        profiler_work = work / "profiler_build" / "libass_profiler_native"
        shutil.copytree(profiler_native_src, profiler_work)
        subprocess.run(["bash", str(profiler_work / "build.sh")], cwd=str(profiler_work), check=True)
        built_prof = profiler_work / "libass_profiler"
        if not built_prof.is_file():
            raise SystemExit("Native libass_profiler binary was not produced by libass_profiler_native/build.sh")
        shutil.copy2(built_prof, bin_dst / "libass_profiler")
        (bin_dst / "libass_profiler").chmod(0o755)
    elif (bin_src / "libass_profiler").is_file():
        shutil.copy2(bin_src / "libass_profiler", bin_dst / "libass_profiler")
        (bin_dst / "libass_profiler").chmod(0o755)
    else:
        raise SystemExit("Could not locate or compile native libass_profiler for POSIX target.")


def copy_nodes_tree(stage_nodes: Path, plat: str, work: Path) -> None:
    """Copy the PyxisNodes runtime tree to ``stage_nodes`` and build/copy native binaries."""
    skip_top = {"python", ".venv", "bin"}

    def ignore(directory, names):
        ignored = [n for n in names if n == "__pycache__" or n.endswith((".pyc", ".pyo"))]
        if Path(directory) == NODES_DIR:
            ignored += [n for n in names if n in skip_top]
        return ignored

    shutil.copytree(NODES_DIR, stage_nodes, ignore=ignore)
    build_native_tools(NODES_DIR / "bin", stage_nodes / "bin", plat, work)


def install_ffmpeg(stage_bin: Path, plat: str, args, work: Path) -> Optional[dict]:
    """Provision native ``ffmpeg`` into ``stage_bin``."""
    if args.no_ffmpeg:
        warn("ffmpeg omitted from package: users will need ffmpeg installed on their system PATH")
        return None
    return get_ffmpeg.install(
        plat,
        stage_bin,
        url=args.ffmpeg_url,
        sha256=args.ffmpeg_sha256,
        path=args.ffmpeg_path,
        build=args.ffmpeg_build,
        work=work,
    )


def precompile(py: Path, stage_python: Path, stage_nodes: Path) -> None:
    """Precompile Python bytecode (.pyc) so startup with ``-B`` is instantaneous."""
    log("Precompiling Python bytecode")
    result = subprocess.run(
        [str(py), "-m", "compileall", "-q", "-j", "0", str(stage_python), str(stage_nodes / "src")],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        warn("compileall reported non-fatal errors in third-party test modules; ignoring")


def write_zip(stage_nodes: Path, zip_path: Path) -> None:
    """Package ``stage_nodes`` into ``zip_path`` preserving POSIX permissions and symlinks."""
    log(f"Creating {zip_path.name}")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    root = stage_nodes.parent
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for current, dirs, files in os.walk(stage_nodes):
            dirs.sort()
            for name in sorted(dirs + files):
                full = Path(current) / name
                arcname = full.relative_to(root).as_posix()
                if full.is_symlink():
                    info = zipfile.ZipInfo(arcname)
                    info.create_system = 3
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    zf.writestr(info, os.readlink(full))
                elif full.is_file():
                    info = zipfile.ZipInfo.from_file(full, arcname)
                    info.create_system = 3
                    info.compress_type = zipfile.ZIP_DEFLATED
                    with open(full, "rb") as src:
                        zf.writestr(info, src.read(), compresslevel=6)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platform", choices=PLATFORMS, default=None, help="target platform (default: current host)")
    parser.add_argument("--python", default="3.12", help="CPython minor version to bundle (default: 3.12)")
    parser.add_argument("--python-url", help="explicit python-build-standalone archive URL (install_only*.tar.gz)")
    parser.add_argument("--pbs-tag", help="pinned python-build-standalone release tag (default: latest)")
    ff = parser.add_argument_group("ffmpeg (downloads and verifies upstream build via tools/get_ffmpeg.py by default)")
    ff.add_argument("--ffmpeg-url", help="download this archive (zip/tar) instead of the default build")
    ff.add_argument("--ffmpeg-sha256", help="expected SHA-256 hex digest for --ffmpeg-url")
    ff.add_argument("--ffmpeg-path", help="use a local ffmpeg binary or archive")
    ff.add_argument("--ffmpeg-build", action="store_true", help="compile ffmpeg from source (Linux/macOS; see tools/build_ffmpeg.py)")
    ff.add_argument("--no-ffmpeg", action="store_true", help="do not bundle ffmpeg")
    parser.add_argument("--no-qt", action="store_true", help="on Linux, omit Qt WebEngine (use system WebKitGTK instead)")
    parser.add_argument("--out", default=str(REPO_ROOT / "dist"), help="output directory (default: dist/)")
    parser.add_argument("--keep-stage", action="store_true", help="preserve the temporary staging directory")
    args = parser.parse_args()

    host = host_platform()
    plat = args.platform or host
    if plat != host:
        raise SystemExit(
            f"Target {plat} must be built on a {plat} host (current host is {host}): "
            "native binaries and wheels are compiled/executed during staging."
        )

    version = read_version()
    out_dir = Path(args.out)
    zip_path = out_dir / f"PyxisEffector-v{version}-{plat}.zip"
    log(f"Pyxis Effector v{version} - {plat}")

    work = Path(tempfile.mkdtemp(prefix="pyxis_build_"))
    stage_nodes = work / "stage" / "PyxisNodes"
    try:
        (work / "stage").mkdir()
        copy_nodes_tree(stage_nodes, plat, work)

        stage_python = stage_nodes / "python"
        install_python(stage_python, plat, args.python, args.python_url, args.pbs_tag, work)
        py = python_exe(stage_python, plat)
        if not py.is_file():
            raise SystemExit(f"Bundled Python interpreter not found at {py}")

        install_dependencies(py, plat, with_qt=not args.no_qt)
        ffmpeg_info = install_ffmpeg(stage_nodes / "bin", plat, args, work)
        precompile(py, stage_python, stage_nodes)

        info = {
            "version": version,
            "platform": plat,
            "python": subprocess.run(
                [str(py), "-c", "import platform;print(platform.python_version())"],
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "ffmpeg": (
                {k: ffmpeg_info.get(k) for k in ("provider", "url", "sha256", "version_string")}
                if ffmpeg_info
                else None
            ),
        }
        (stage_nodes / "BUILD_INFO.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")

        write_zip(stage_nodes, zip_path)
        digest = sha256_file(zip_path)
        (zip_path.parent / (zip_path.name + ".sha256")).write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
        log(f"Build complete: {zip_path} ({zip_path.stat().st_size / 1_048_576:.1f} MB)")
        log(f"SHA-256: {digest}")
    finally:
        if args.keep_stage:
            log(f"Staging directory preserved at {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())


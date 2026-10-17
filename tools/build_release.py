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

"""Construye el paquete de release de PyxisNodes con su propio Python incluido.

Genera ``dist/PyxisEffector-v<versión>-<plataforma>.zip`` con la carpeta ``PyxisNodes/``
lista para copiar en ``automation/autoload`` (es el archivo que descarga la macro Lua).

Cada paquete contiene un intérprete de Python independiente (python-build-standalone)
con las dependencias de ``requirements.txt`` ya instaladas. Hay que construirlo en una
máquina de la misma plataforma y arquitectura que el destino, porque las dependencias
son binarias y se ejecutan durante la construcción:

    python tools/build_release.py                       # plataforma actual
    python tools/build_release.py --ffmpeg-build        # compilando ffmpeg desde el código fuente
    python tools/build_release.py --no-ffmpeg           # sin ffmpeg

Por defecto incluye un ffmpeg descargado y verificado (ver tools/get_ffmpeg.py).
Solo usa la biblioteca estándar.
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

LUA_FILE = REPO_ROOT / "pyxis.NodeEngine.lua"

PBS_REPO = "astral-sh/python-build-standalone"

# plataforma -> triple de python-build-standalone
TARGETS = {
    "win64": "x86_64-pc-windows-msvc",
    "linux64": "x86_64-unknown-linux-gnu",
    "linux-arm64": "aarch64-unknown-linux-gnu",
    "macos-arm64": "aarch64-apple-darwin",
    "macos-x64": "x86_64-apple-darwin",
}


def read_version() -> str:
    match = re.search(r'^script_version\s*=\s*"([^"]+)"', LUA_FILE.read_text(encoding="utf-8"), re.M)
    if not match:
        raise SystemExit(f"No se encontró script_version en {LUA_FILE}")
    return match.group(1)


def resolve_python_url(version: str, triple: str, tag: Optional[str]) -> str:
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
        raise SystemExit(f"python-build-standalone {release.get('tag_name')} no tiene CPython {version} para {triple}")
    log(f"Python: {best[1].rsplit('/', 1)[1]}")
    return best[1]


def extract_tar(archive: Path, dest: Path) -> None:
    with tarfile.open(archive) as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(dest, filter="data")
        else:
            tar.extractall(dest)


def python_exe(python_dir: Path, plat: str) -> Path:
    return python_dir / "python.exe" if plat == "win64" else python_dir / "bin" / "python3"


def install_python(stage_python: Path, plat: str, version: str, url: Optional[str], tag: Optional[str], work: Path) -> None:
    triple = TARGETS[plat]
    url = url or resolve_python_url(version, triple, tag)
    archive = work / "python.tar.gz"
    log("Descargando Python independiente")
    http_get(url, archive)
    unpack = work / "python_unpack"
    extract_tar(archive, unpack)
    inner = unpack / "python"
    if not inner.is_dir():
        raise SystemExit("El archivo de Python no contiene la carpeta 'python/' esperada")
    shutil.move(str(inner), str(stage_python))


# Dependencias de Python puro que solo se publican como sdist (pywebview -> proxy_tools).
SDIST_OK = "proxy_tools"


def pip_install(py: Path, args: list, check: bool = True) -> int:
    # Solo ruedas precompiladas (nada se compila en la máquina de CI), salvo SDIST_OK.
    cmd = [str(py), "-m", "pip", "install", "--no-warn-script-location", "--disable-pip-version-check",
           "--only-binary=:all:", f"--no-binary={SDIST_OK}", *args]
    return subprocess.run(cmd, check=check).returncode


def read_requirements(path: Path) -> list:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            lines.append(line)
    return lines


def install_dependencies(py: Path, plat: str, with_qt: bool) -> None:
    log("Instalando dependencias obligatorias")
    pip_install(py, ["-r", str(NODES_DIR / "requirements.txt")])

    for spec in read_requirements(NODES_DIR / "requirements-optional.txt"):
        log(f"Instalando dependencia opcional: {spec}")
        if pip_install(py, [spec], check=False) != 0:
            warn(f"No se pudo instalar {spec}; el paquete funcionará sin él")

    if with_qt and plat.startswith("linux"):
        # WebKitGTK no se puede empaquetar (depende de las bibliotecas del sistema), pero
        # Qt WebEngine sí viene en ruedas de pip y hace el runtime autosuficiente.
        log("Instalando Qt WebEngine (backend gráfico autosuficiente en Linux)")
        pip_install(py, ["-r", str(NODES_DIR / "requirements-qt.txt")])


def copy_nodes_tree(stage_nodes: Path, plat: str) -> None:
    skip_top = {"python", ".venv", "bin"}

    def ignore(directory, names):
        ignored = [n for n in names if n == "__pycache__" or n.endswith((".pyc", ".pyo"))]
        if Path(directory) == NODES_DIR:
            ignored += [n for n in names if n in skip_top]
        return ignored

    shutil.copytree(NODES_DIR, stage_nodes, ignore=ignore)

    bin_src = NODES_DIR / "bin"
    bin_dst = stage_nodes / "bin"
    bin_dst.mkdir(exist_ok=True)
    if plat == "win64":
        wanted = ["potrace.exe", "libass_profiler.exe"]
    else:
        # Un libass_profiler nativo (cuando exista el port) tiene prioridad; el .exe de Windows
        # se incluye como alternativa porque ass_telemetry_engine lo ejecuta mediante Wine.
        wanted = ["libass_profiler", "libass_profiler.exe"]
    for name in wanted:
        if (bin_src / name).is_file():
            shutil.copy2(bin_src / name, bin_dst / name)
    if plat != "win64" and not (bin_src / "libass_profiler").is_file():
        warn("no hay libass_profiler nativo: en este paquete la telemetría de render requerirá Wine en el sistema del usuario")


def install_ffmpeg(stage_bin: Path, plat: str, args, work: Path) -> Optional[dict]:
    """Deja ffmpeg en el paquete: build alojado verificado (por defecto), local, o compilado."""
    if args.no_ffmpeg:
        warn("ffmpeg no incluido en el paquete: los usuarios necesitarán ffmpeg en el PATH")
        return None
    return get_ffmpeg.install(
        plat, stage_bin, url=args.ffmpeg_url, sha256=args.ffmpeg_sha256, path=args.ffmpeg_path,
        build=args.ffmpeg_build, work=work,
    )


def precompile(py: Path, stage_python: Path, stage_nodes: Path) -> None:
    # La macro lanza Python con -B (no escribe .pyc); sin bytecode precompilado cada
    # arranque recompilaría numpy, Pillow, etc.
    log("Precompilando bytecode")
    result = subprocess.run([str(py), "-m", "compileall", "-q", "-j", "0", str(stage_python), str(stage_nodes / "src")],
                            capture_output=True, text=True)
    if result.returncode != 0:
        warn("compileall devolvió errores (suele ser código de pruebas de terceros); se ignoran")


def write_zip(stage_nodes: Path, zip_path: Path) -> None:
    log(f"Creando {zip_path.name}")
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
    parser.add_argument("--platform", choices=PLATFORMS, default=None, help="plataforma destino (por defecto, la actual)")
    parser.add_argument("--python", default="3.12", help="versión menor de CPython a incluir (por defecto 3.12)")
    parser.add_argument("--python-url", help="URL de un python-build-standalone concreto (install_only*.tar.gz)")
    parser.add_argument("--pbs-tag", help="release fijo de python-build-standalone (por defecto, el último)")
    ff = parser.add_argument_group("ffmpeg (por defecto se descarga y verifica el build de tools/get_ffmpeg.py)")
    ff.add_argument("--ffmpeg-url", help="descargar este archivo (zip/tar) en lugar del build por defecto")
    ff.add_argument("--ffmpeg-sha256", help="SHA-256 esperado de --ffmpeg-url")
    ff.add_argument("--ffmpeg-path", help="usar un ffmpeg local (binario o archivo que lo contenga)")
    ff.add_argument("--ffmpeg-build", action="store_true", help="compilar ffmpeg desde el código fuente (Linux/macOS; ver tools/build_ffmpeg.py)")
    ff.add_argument("--no-ffmpeg", action="store_true", help="no incluir ffmpeg")
    parser.add_argument("--no-qt", action="store_true", help="en Linux, no incluir Qt WebEngine (se usará WebKitGTK del sistema)")
    parser.add_argument("--out", default=str(REPO_ROOT / "dist"), help="carpeta de salida (por defecto dist/)")
    parser.add_argument("--keep-stage", action="store_true", help="conserva la carpeta temporal de construcción")
    args = parser.parse_args()

    host = host_platform()
    plat = args.platform or host
    if plat != host:
        raise SystemExit(f"Hay que construir {plat} en una máquina {plat} (esta es {host}): "
                         "las dependencias son binarias y se ejecutan durante la construcción.")

    version = read_version()
    out_dir = Path(args.out)
    zip_path = out_dir / f"PyxisEffector-v{version}-{plat}.zip"
    log(f"Pyxis Effector v{version} — {plat}")

    work = Path(tempfile.mkdtemp(prefix="pyxis_build_"))
    stage_nodes = work / "stage" / "PyxisNodes"
    try:
        (work / "stage").mkdir()
        copy_nodes_tree(stage_nodes, plat)

        stage_python = stage_nodes / "python"
        install_python(stage_python, plat, args.python, args.python_url, args.pbs_tag, work)
        py = python_exe(stage_python, plat)
        if not py.is_file():
            raise SystemExit(f"No se encontró el intérprete en {py}")

        install_dependencies(py, plat, with_qt=not args.no_qt)
        ffmpeg_info = install_ffmpeg(stage_nodes / "bin", plat, args, work)
        precompile(py, stage_python, stage_nodes)

        info = {
            "version": version,
            "platform": plat,
            "python": subprocess.run([str(py), "-c", "import platform;print(platform.python_version())"],
                                     capture_output=True, text=True).stdout.strip(),
            "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "ffmpeg": ({k: ffmpeg_info.get(k) for k in ("provider", "url", "sha256", "version_string")}
                       if ffmpeg_info else None),
        }
        (stage_nodes / "BUILD_INFO.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")

        write_zip(stage_nodes, zip_path)
        digest = sha256_file(zip_path)
        (zip_path.parent / (zip_path.name + ".sha256")).write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
        log(f"Listo: {zip_path} ({zip_path.stat().st_size / 1_048_576:.0f} MB)")
        log(f"SHA-256: {digest}")
    finally:
        if args.keep_stage:
            log(f"Carpeta de construcción conservada en {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

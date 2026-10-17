#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

"""Construye el paquete de release de PyxisNodes con su propio Python incluido.

Genera ``dist/PyxisEffector-v<versión>-<plataforma>.zip`` con la carpeta ``PyxisNodes/``
lista para copiar en ``automation/autoload`` (es el archivo que descarga la macro Lua).

Cada paquete contiene un intérprete de Python independiente (python-build-standalone)
con las dependencias de ``requirements.txt`` ya instaladas. Hay que construirlo en una
máquina de la misma plataforma y arquitectura que el destino, porque las dependencias
son binarias y se ejecutan durante la construcción:

    python tools/build_release.py                       # plataforma actual
    python tools/build_release.py --platform macos-arm64 --ffmpeg-url <url>

Solo usa la biblioteca estándar.
"""

import argparse
import hashlib
import http.client
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
NODES_DIR = REPO_ROOT / "PyxisNodes"
LUA_FILE = REPO_ROOT / "pyxis.NodeEngine.lua"

PBS_REPO = "astral-sh/python-build-standalone"

# plataforma -> (triple de python-build-standalone, ejecutable de ffmpeg)
TARGETS = {
    "win64": ("x86_64-pc-windows-msvc", "ffmpeg.exe"),
    "linux64": ("x86_64-unknown-linux-gnu", "ffmpeg"),
    "linux-arm64": ("aarch64-unknown-linux-gnu", "ffmpeg"),
    "macos-arm64": ("aarch64-apple-darwin", "ffmpeg"),
    "macos-x64": ("x86_64-apple-darwin", "ffmpeg"),
}

# Fuentes de ffmpeg estáticos que usa el workflow de CI (se pasan con --ffmpeg-url).
FFMPEG_NOTE = (
    "win64/linux64/linux-arm64: https://github.com/BtbN/FFmpeg-Builds (GPL); "
    "macOS: https://ffmpeg.martin-riedl.de"
)


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


def read_version() -> str:
    match = re.search(r'^script_version\s*=\s*"([^"]+)"', LUA_FILE.read_text(encoding="utf-8"), re.M)
    if not match:
        raise SystemExit(f"No se encontró script_version en {LUA_FILE}")
    return match.group(1)


def http_get(url: str, dest: Optional[Path] = None):
    headers = {"User-Agent": "pyxis-build-release"}
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
    triple = TARGETS[plat][0]
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


def find_in_archive_and_extract(archive: Path, exe_name: str, dest: Path) -> bool:
    name = archive.name.lower()
    if name.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            for member in zf.namelist():
                if Path(member).name == exe_name and not member.endswith("/"):
                    with zf.open(member) as src, open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)
                    return True
        return False
    if name.endswith((".tar.xz", ".tar.gz", ".tgz", ".tar.bz2", ".tar")):
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                if member.isfile() and Path(member.name).name == exe_name:
                    src = tar.extractfile(member)
                    with open(dest, "wb") as out:
                        shutil.copyfileobj(src, out)
                    return True
        return False
    if name.endswith(".rar"):
        with tempfile.TemporaryDirectory() as tmp:
            for cmd in (["7z", "x", "-y", f"-o{tmp}", str(archive)],
                        ["7zz", "x", "-y", f"-o{tmp}", str(archive)],
                        ["bsdtar", "-xf", str(archive), "-C", tmp],
                        ["unrar", "x", "-y", str(archive), tmp + os.sep]):
                if shutil.which(cmd[0]) and subprocess.run(cmd, capture_output=True).returncode == 0:
                    for found in Path(tmp).rglob(exe_name):
                        shutil.copy2(found, dest)
                        return True
        warn("No se pudo extraer el .rar (se necesita 7z, bsdtar o unrar)")
        return False
    return False


def install_ffmpeg(stage_bin: Path, plat: str, source: Optional[str], work: Path) -> None:
    exe_name = TARGETS[plat][1]
    dest = stage_bin / exe_name

    if not source and plat == "win64" and (NODES_DIR / "bin" / "ffmpeg.rar").is_file():
        source = str(NODES_DIR / "bin" / "ffmpeg.rar")

    if not source:
        warn(f"ffmpeg no incluido en el paquete: los usuarios necesitarán ffmpeg en el PATH ({FFMPEG_NOTE})")
        return

    if source.startswith(("http://", "https://")):
        log("Descargando ffmpeg")
        archive = work / source.split("?", 1)[0].rsplit("/", 1)[-1]
        http_get(source, archive)
    else:
        archive = Path(source)
        if not archive.is_file():
            raise SystemExit(f"No existe el archivo de ffmpeg: {archive}")

    if archive.name == exe_name:
        shutil.copy2(archive, dest)
    elif not find_in_archive_and_extract(archive, exe_name, dest):
        raise SystemExit(f"No se encontró {exe_name} dentro de {archive.name}")
    dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    log(f"ffmpeg incluido: {dest.name}")


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
    parser.add_argument("--platform", choices=sorted(TARGETS), default=None, help="plataforma destino (por defecto, la actual)")
    parser.add_argument("--python", default="3.12", help="versión menor de CPython a incluir (por defecto 3.12)")
    parser.add_argument("--python-url", help="URL de un python-build-standalone concreto (install_only*.tar.gz)")
    parser.add_argument("--pbs-tag", help="release fijo de python-build-standalone (por defecto, el último)")
    parser.add_argument("--ffmpeg-url", help="URL de un archivo (zip/tar) que contenga ffmpeg")
    parser.add_argument("--ffmpeg-path", help="ruta a un ffmpeg, o a un archivo que lo contenga")
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
        install_ffmpeg(stage_nodes / "bin", plat, args.ffmpeg_path or args.ffmpeg_url, work)
        precompile(py, stage_python, stage_nodes)

        info = {
            "version": version,
            "platform": plat,
            "python": subprocess.run([str(py), "-c", "import platform;print(platform.python_version())"],
                                     capture_output=True, text=True).stdout.strip(),
            "built": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        (stage_nodes / "BUILD_INFO.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")

        write_zip(stage_nodes, zip_path)
        digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
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

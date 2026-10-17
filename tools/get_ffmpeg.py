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

"""Obtiene el ffmpeg que necesita Pyxis: lo descarga ya compilado o lo compila desde el código fuente.

FFmpeg solo distribuye código fuente (https://ffmpeg.org/download.html); los binarios que
enlaza su web los compilan terceros. Por defecto se descarga de estos y se verifica su SHA-256:

    win64, linux64, linux-arm64   BtbN/FFmpeg-Builds (rama de release n9.0, variante GPL)
    macos-arm64, macos-x64        ffmpeg.martin-riedl.de (release estable, compilaciones nativas)

El build debe incluir libx264, libwebp y libass (filtro `subtitles`), que Pyxis usa para
exportar vídeo con subtítulos incrustados.

    python tools/get_ffmpeg.py                   # descarga el ffmpeg de esta plataforma en PyxisNodes/bin
    python tools/get_ffmpeg.py --build           # lo compila desde el código fuente (tools/build_ffmpeg.py)
    python tools/get_ffmpeg.py --url <url> --sha256 <hash>   # otro build alojado (p. ej. evermeet.cx)
    python tools/get_ffmpeg.py --list-sources

Solo usa la biblioteca estándar.
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
BTBN_BRANCH = "9.0"  # rama de release (no "master", que es una instantánea de desarrollo)
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
    return "ffmpeg.exe" if plat == "win64" else "ffmpeg"


def _first_hash(text: str, filename: Optional[str] = None) -> Optional[str]:
    """Extrae un SHA-256 de un archivo de sumas ("<hash>  <archivo>" o solo el hash)."""
    for line in text.splitlines():
        parts = line.split()
        if parts and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]) and (filename is None or len(parts) == 1 or parts[-1].lstrip("*") == filename):
            return parts[0].lower()
    return None


def default_source(plat: str) -> dict:
    """Resuelve (con red) el build alojado por defecto: URL y SHA-256 publicado por el proveedor."""
    if plat in BTBN_TARGETS:
        key, ext = BTBN_TARGETS[plat]
        filename = f"ffmpeg-n{BTBN_BRANCH}-latest-{key}-gpl-{BTBN_BRANCH}.{ext}"
        checksums = http_get(BTBN_BASE + "checksums.sha256").decode("utf-8", "replace")
        digest = _first_hash(checksums, filename)
        if not digest:
            raise SystemExit(f"{filename} no figura en checksums.sha256 de BtbN; ¿cambió el nombre de la rama?")
        return {"provider": "BtbN/FFmpeg-Builds", "url": BTBN_BASE + filename, "filename": filename, "sha256": digest}

    if plat in MARTIN_RIEDL_ARCH:
        final_url = resolve_redirects(MARTIN_RIEDL.format(arch=MARTIN_RIEDL_ARCH[plat]))
        digest = _first_hash(http_get(final_url + ".sha256").decode("utf-8", "replace"))
        if not digest:
            raise SystemExit(f"No se pudo leer el SHA-256 de {final_url}")
        return {"provider": "ffmpeg.martin-riedl.de", "url": final_url, "filename": final_url.rsplit("/", 1)[-1], "sha256": digest}

    raise SystemExit(f"Plataforma desconocida: {plat}")


def extract_binary(archive: Path, name: str, dest: Path) -> bool:
    """Extrae del archivo (zip o tar) el ejecutable llamado ``name``, esté en la carpeta que esté."""
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
                    with open(dest, "wb") as out:
                        shutil.copyfileobj(tar.extractfile(member), out)
                    return True
        return False
    return False


def describe_binary(binary: Path) -> dict:
    """Versión y configuración de compilación, si el binario se puede ejecutar aquí."""
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
    """Deja junto al binario de qué fuente procede (ffmpeg se distribuye bajo la GPL)."""
    version_match = re.match(r"n?(\d+\.\d+(?:\.\d+)?)", info.get("version_string", ""))
    source = SOURCE_TARBALL.format(version=version_match.group(1)) if version_match else SOURCES_PAGE
    lines = [
        "FFmpeg incluido en este paquete",
        "===============================",
        "",
        f"Plataforma : {plat}",
        f"Origen     : {info.get('provider', 'desconocido')}",
        f"Descarga   : {info.get('url', '-')}",
        f"SHA-256    : {info.get('sha256', '-')}",
        f"Versión    : {info.get('version_string', 'ver `ffmpeg -version`')}",
        "",
        "Este ffmpeg es una compilación GPL (con libx264, libass, libwebp, ...). FFmpeg es software libre;",
        "su código fuente y el de sus bibliotecas está disponible en:",
        f"  {source}",
        "La línea de configuración exacta del binario se obtiene con `ffmpeg -buildconf`.",
        "",
        "Para compilarlo tú mismo: python tools/get_ffmpeg.py --build",
        "",
    ]
    (dest_dir / "FFMPEG-NOTICE.txt").write_text("\n".join(lines), encoding="utf-8")


def install(plat: str, dest_dir: Path, *, url: Optional[str] = None, sha256: Optional[str] = None,
            path: Optional[str] = None, build: bool = False, build_options: Optional[dict] = None,
            work: Optional[Path] = None) -> dict:
    """Deja ffmpeg en ``dest_dir`` y devuelve un dict con su procedencia."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = exe_name(plat)
    dest = dest_dir / name
    own_work = work is None
    work = Path(tempfile.mkdtemp(prefix="pyxis_ffmpeg_")) if own_work else work

    try:
        if build:
            if plat != host_platform():
                raise SystemExit(f"Para compilar ffmpeg para {plat} hay que estar en una máquina {plat}.")
            import build_ffmpeg
            built = build_ffmpeg.build(out_dir=dest_dir, **(build_options or {}))
            info = {"provider": "compilado desde el código fuente (ffmpeg.org)", "url": built["source_url"],
                    "sha256": sha256_file(dest), "build": built}
        else:
            if path:
                archive = Path(path)
                if not archive.is_file():
                    raise SystemExit(f"No existe el archivo de ffmpeg: {archive}")
                info = {"provider": "archivo local", "url": str(archive), "sha256": sha256_file(archive)}
            else:
                source = ({"provider": "personalizado", "url": url, "filename": url.split("?", 1)[0].rsplit("/", 1)[-1],
                           "sha256": sha256} if url else default_source(plat))
                archive = work / source["filename"]
                log(f"Descargando ffmpeg ({source['provider']})")
                http_get(source["url"], archive)
                actual = sha256_file(archive)
                if source.get("sha256"):
                    if actual != source["sha256"].lower():
                        raise SystemExit(f"SHA-256 de ffmpeg incorrecto.\n  esperado: {source['sha256']}\n  obtenido: {actual}")
                    log("SHA-256 verificado")
                else:
                    warn(f"Sin SHA-256 con el que comparar; el archivo descargado tiene {actual}")
                info = {"provider": source["provider"], "url": source["url"], "sha256": actual}

            if archive.name == name:
                shutil.copy2(archive, dest)
            elif not extract_binary(archive, name, dest):
                raise SystemExit(f"No se encontró {name} dentro de {archive.name}")

        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        if plat == host_platform():
            info.update(describe_binary(dest))
        write_notice(dest_dir, plat, info)
        log(f"ffmpeg instalado: {dest} {info.get('version_string', '')}".rstrip())
        return info
    finally:
        if own_work:
            shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platform", choices=PLATFORMS, help="plataforma destino (por defecto, la actual)")
    parser.add_argument("--out", default=str(NODES_DIR / "bin"), help="carpeta de destino (por defecto PyxisNodes/bin)")
    parser.add_argument("--url", help="descargar este archivo (zip/tar) en lugar del build por defecto")
    parser.add_argument("--sha256", help="SHA-256 esperado de --url")
    parser.add_argument("--path", help="usar un ffmpeg local (binario o archivo que lo contenga)")
    parser.add_argument("--build", action="store_true", help="compilarlo desde el código fuente en lugar de descargarlo")
    parser.add_argument("--ffmpeg-version", help="con --build: versión de ffmpeg a compilar")
    parser.add_argument("--jobs", type=int, help="con --build: trabajos de make en paralelo")
    parser.add_argument("--list-sources", action="store_true", help="muestra el origen por defecto de cada plataforma y sale")
    args = parser.parse_args()

    if args.list_sources:
        for plat in PLATFORMS:
            src = default_source(plat)
            print(f"{plat:12} {src['provider']:24} {src['url']}\n{'':12} sha256 {src['sha256']}")
        return 0

    plat = args.platform or host_platform()
    options = {k: v for k, v in (("version", args.ffmpeg_version), ("jobs", args.jobs)) if v}
    install(plat, Path(args.out), url=args.url, sha256=args.sha256, path=args.path, build=args.build, build_options=options)
    return 0


if __name__ == "__main__":
    sys.exit(main())

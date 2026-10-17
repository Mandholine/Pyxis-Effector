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

"""Compila ffmpeg desde el código fuente con lo que necesita Pyxis (Linux y macOS).

Descarga de ffmpeg.org el tarball de la versión pedida y comprueba su firma PGP contra la
huella publicada en https://ffmpeg.org/download.html; compila libx264 (git de VideoLAN) y
libwebp (tarball de Google, con SHA-256 fijado) como bibliotecas estáticas, y enlaza todo en
un ``ffmpeg`` con libx264, libwebp, libass (filtro `subtitles`), AAC y, en macOS, VideoToolbox.
Al terminar ejecuta codificaciones de prueba reales y falla si falta algo.

    python tools/build_ffmpeg.py --out PyxisNodes/bin

Requisitos previos (el script los comprueba y dice qué instalar):
    Debian/Ubuntu  sudo apt install build-essential nasm pkg-config git libass-dev zlib1g-dev gnupg
    Arch           sudo pacman -S base-devel nasm pkgconf git libass zlib gnupg
    macOS          xcode-select --install && brew install nasm pkg-config libass gnupg

libass (y sus dependencias: freetype, fribidi, harfbuzz, fontconfig) se toman del sistema, así que
el binario resultante es para este equipo; para repartir uno portable usa los builds alojados
(tools/get_ffmpeg.py). En Windows no está soportado: usa también los builds alojados.

Solo usa la biblioteca estándar.
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NODES_DIR, host_platform, http_get, log, sha256_file, warn  # noqa: E402

FFMPEG_VERSION = "9.0.2"
FFMPEG_URL = "https://ffmpeg.org/releases/ffmpeg-{version}.tar.xz"
FFMPEG_KEY_URL = "https://ffmpeg.org/ffmpeg-devel.asc"
# Huella de la clave de firma de las releases, publicada en https://ffmpeg.org/download.html
FFMPEG_KEY_FPR = "FCF986EA15E6E293A5644F10B4322F04D67658D8"

X264_REPO = "https://code.videolan.org/videolan/x264.git"
X264_REF = "stable"

WEBP_VERSION = "1.6.0"
WEBP_URL = "https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-{version}.tar.gz"
# SHA-256 anotado al descargar el tarball de Google (no hay una suma publicada aparte).
WEBP_SHA256 = {"1.6.0": "e4ab7009bf0629fd11982d4c2aa83964cf244cffba7347ecd39019a9e38c4564"}

REQUIRED_ENCODERS = ("libx264", "libwebp", "aac")
REQUIRED_FILTERS = ("subtitles", "scale", "pad", "negate")


class BuildError(SystemExit):
    pass


def run(cmd, *, cwd: Path, env: dict, log_file: Path, what: str) -> None:
    """Ejecuta un comando guardando su salida; si falla, muestra el final del registro."""
    log(what)
    with open(log_file, "ab") as fp:
        fp.write(f"\n$ {' '.join(map(str, cmd))}\n".encode())
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=fp, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        tail = log_file.read_text(errors="replace").splitlines()[-25:]
        raise BuildError(f"Falló: {what}\n" + "\n".join(tail) + f"\n(registro completo: {log_file})")


def preflight() -> None:
    system = platform.system()
    if system == "Windows":
        raise BuildError("Compilar ffmpeg no está soportado en Windows; usa los builds alojados (tools/get_ffmpeg.py).")
    if system not in ("Linux", "Darwin"):
        raise BuildError(f"Sistema no soportado: {system}")

    missing = []
    for tool in ("make", "git", "tar", "pkg-config"):
        if not shutil.which(tool):
            missing.append(tool)
    if not (shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")):
        missing.append("compilador de C (gcc/clang)")
    if platform.machine().lower() in ("x86_64", "amd64", "i686") and not shutil.which("nasm"):
        missing.append("nasm")

    for pkg in ("libass", "zlib"):
        if shutil.which("pkg-config") and subprocess.run(["pkg-config", "--exists", pkg], capture_output=True).returncode != 0:
            missing.append(f"{pkg} (paquete de desarrollo)")

    if missing:
        hint = ("brew install nasm pkg-config libass" if system == "Darwin" else
                "Debian/Ubuntu: sudo apt install build-essential nasm pkg-config git libass-dev zlib1g-dev\n"
                "         Arch: sudo pacman -S base-devel nasm pkgconf git libass zlib")
        raise BuildError("Faltan requisitos para compilar ffmpeg: " + ", ".join(missing) + f"\n  Instala: {hint}")


def verify_pgp(tarball: Path, signature: Path) -> bool:
    """Comprueba la firma PGP de la release. Devuelve False (con aviso) si no hay gpg."""
    gpg = shutil.which("gpg") or shutil.which("gpg2")
    if not gpg:
        warn("gpg no está instalado: no se verificó la firma de ffmpeg (instálalo para comprobarla)")
        return False
    home = Path(tempfile.mkdtemp(prefix="pgp_"))  # ruta corta: el socket del agente tiene un límite de longitud
    home.chmod(0o700)
    env = dict(os.environ, GNUPGHOME=str(home))
    try:
        key = home / "ffmpeg-devel.asc"
        http_get(FFMPEG_KEY_URL, key)
        subprocess.run([gpg, "--batch", "--quiet", "--import", str(key)], env=env, check=True, capture_output=True)
        listing = subprocess.run([gpg, "--batch", "--with-colons", "--fingerprint"], env=env, capture_output=True, text=True).stdout
        if FFMPEG_KEY_FPR not in listing:
            raise BuildError(f"La clave descargada de ffmpeg.org no tiene la huella esperada {FFMPEG_KEY_FPR}")
        result = subprocess.run([gpg, "--batch", "--status-fd", "1", "--verify", str(signature), str(tarball)],
                                env=env, capture_output=True, text=True)
        valid = [line for line in result.stdout.splitlines() if " VALIDSIG " in line]
        if result.returncode != 0 or not valid or not valid[0].split()[-1].upper() == FFMPEG_KEY_FPR:
            raise BuildError("La firma PGP del tarball de ffmpeg NO es válida; se aborta.\n" + result.stderr.strip())
        return True
    finally:
        subprocess.run(["gpgconf", "--kill", "gpg-agent"], env=env, capture_output=True)
        shutil.rmtree(home, ignore_errors=True)


def fetch(url: str, dest: Path) -> Path:
    if not dest.is_file():
        http_get(url, dest)
    return dest


def extract(tarball: Path, dest: Path) -> Path:
    with tarfile.open(tarball) as tar:
        top = tar.getnames()[0].split("/")[0]
        tar.extractall(dest, filter="data") if hasattr(tarfile, "data_filter") else tar.extractall(dest)
    return dest / top


def verify_binary(ffmpeg: Path, work: Path, env: dict) -> None:
    """Falla si al binario le falta algo que Pyxis usa, probándolo de verdad (no solo mirando -encoders)."""
    def ff(*args) -> subprocess.CompletedProcess:
        return subprocess.run([str(ffmpeg), "-hide_banner", "-v", "error", *args], cwd=work, capture_output=True, text=True)

    encoders = subprocess.run([str(ffmpeg), "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    filters = subprocess.run([str(ffmpeg), "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    missing = [e for e in REQUIRED_ENCODERS if not re.search(rf"\s{e}\s", encoders)]
    missing += [f for f in REQUIRED_FILTERS if not re.search(rf"\s{f}\s", filters)]
    if sys.platform == "darwin" and "h264_videotoolbox" not in encoders:
        missing.append("h264_videotoolbox")
    if missing:
        raise BuildError("El ffmpeg compilado no incluye: " + ", ".join(missing))

    (work / "probe.ass").write_text(
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 320\nPlayResY: 240\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Arial,30,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:00.00,0:00:01.00,Default,,0,0,0,,{\\k20}Pyxis\n", encoding="utf-8")
    checks = {
        "libx264 + yuv420p": ["-f", "lavfi", "-i", "color=c=black:s=320x240:d=0.2:r=24", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-f", "null", "-"],
        "aac": ["-f", "lavfi", "-i", "sine=d=0.2", "-c:a", "aac", "-f", "null", "-"],
        "libwebp": ["-y", "-f", "lavfi", "-i", "color=c=red:s=64x64:d=0.1", "-frames:v", "1", "-c:v", "libwebp", "probe.webp"],
        "filtro subtitles (libass)": ["-f", "lavfi", "-i", "color=c=black:s=320x240:d=0.5:r=24", "-vf", "subtitles=probe.ass",
                                      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-f", "null", "-"],
        "scale+pad": ["-f", "lavfi", "-i", "color=s=321x241:d=0.1", "-vf",
                      "scale=w='min(1920,trunc(iw/2)*2)':h='min(1080,trunc(ih/2)*2)':force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2",
                      "-f", "null", "-"],
    }
    for label, args in checks.items():
        result = ff(*args)
        if result.returncode != 0:
            raise BuildError(f"Prueba de ffmpeg fallida ({label}):\n{result.stderr.strip()}")
        log(f"  [OK] {label}")


def build(out_dir: Path, version: str = FFMPEG_VERSION, jobs: Optional[int] = None, work_dir: Optional[Path] = None,
          keep_work: bool = False, x264_ref: str = X264_REF, webp_version: str = WEBP_VERSION,
          verify_signature: bool = True) -> dict:
    """Compila ffmpeg y deja el binario en ``out_dir``. Devuelve los datos de la compilación."""
    preflight()
    jobs = jobs or os.cpu_count() or 2
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    work = Path(work_dir).resolve() if work_dir else Path(tempfile.mkdtemp(prefix="pyxis_ffmpeg_build_"))
    work.mkdir(parents=True, exist_ok=True)
    prefix = work / "prefix"
    stage = work / "stage"
    build_log = work / "build.log"
    env = dict(os.environ)
    env["PKG_CONFIG_PATH"] = os.pathsep.join(p for p in (str(prefix / "lib" / "pkgconfig"), env.get("PKG_CONFIG_PATH", "")) if p)
    make = ["make", f"-j{jobs}"]
    log(f"Compilando ffmpeg {version} (registro: {build_log})")

    try:
        # 1. ffmpeg.org: tarball + firma
        tarball = fetch(FFMPEG_URL.format(version=version), work / f"ffmpeg-{version}.tar.xz")
        signature = fetch(FFMPEG_URL.format(version=version) + ".asc", work / f"ffmpeg-{version}.tar.xz.asc")
        signed = verify_pgp(tarball, signature) if verify_signature else False
        if signed:
            log("Firma PGP de ffmpeg verificada")
        ffmpeg_src = extract(tarball, work / "src")

        # 2. libx264
        x264_src = work / "src" / "x264"
        if not x264_src.is_dir():
            run(["git", "clone", "--depth", "1", "--branch", x264_ref, X264_REPO, str(x264_src)],
                cwd=work, env=env, log_file=build_log, what=f"Descargando x264 ({x264_ref})")
        x264_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=x264_src, capture_output=True, text=True).stdout.strip()
        run(["./configure", f"--prefix={prefix}", f"--libdir={prefix / 'lib'}", "--enable-static", "--enable-pic", "--disable-cli"],
            cwd=x264_src, env=env, log_file=build_log, what="Configurando x264")
        run(make, cwd=x264_src, env=env, log_file=build_log, what="Compilando x264")
        run(["make", "install"], cwd=x264_src, env=env, log_file=build_log, what="Instalando x264")

        # 3. libwebp
        webp_tar = fetch(WEBP_URL.format(version=webp_version), work / f"libwebp-{webp_version}.tar.gz")
        expected = WEBP_SHA256.get(webp_version)
        if expected and sha256_file(webp_tar) != expected:
            raise BuildError(f"SHA-256 de libwebp-{webp_version} incorrecto (esperado {expected})")
        if not expected:
            warn(f"libwebp {webp_version}: sin SHA-256 fijado en el script; descargado {sha256_file(webp_tar)}")
        webp_src = extract(webp_tar, work / "src")
        run(["./configure", f"--prefix={prefix}", f"--libdir={prefix / 'lib'}", "--disable-shared", "--enable-static",
             "--disable-gl", "--disable-sdl", "--disable-png", "--disable-jpeg", "--disable-tiff", "--disable-gif",
             "--disable-wic"], cwd=webp_src, env=env, log_file=build_log, what="Configurando libwebp")
        run(make, cwd=webp_src, env=env, log_file=build_log, what="Compilando libwebp")
        run(["make", "install"], cwd=webp_src, env=env, log_file=build_log, what="Instalando libwebp")

        # 4. ffmpeg (sin autodetección: solo lo que se pide, para que el binario sea reproducible)
        configure = [
            "./configure", f"--prefix={stage}", "--disable-autodetect", "--disable-doc", "--disable-debug",
            "--disable-ffplay", "--disable-ffprobe", "--enable-gpl", "--enable-pthreads", "--enable-zlib",
            "--enable-libx264", "--enable-libwebp", "--enable-libass", "--pkg-config-flags=--static",
            f"--extra-cflags=-I{prefix / 'include'}", f"--extra-ldflags=-L{prefix / 'lib'}",
        ]
        if sys.platform == "darwin":
            configure += ["--enable-videotoolbox", "--enable-audiotoolbox"]
        run(configure, cwd=ffmpeg_src, env=env, log_file=build_log, what="Configurando ffmpeg")
        run(make, cwd=ffmpeg_src, env=env, log_file=build_log, what="Compilando ffmpeg (tarda unos minutos)")
        run(["make", "install"], cwd=ffmpeg_src, env=env, log_file=build_log, what="Instalando ffmpeg")

        # 5. Pruebas reales y entrega
        binary = stage / "bin" / "ffmpeg"
        log("Verificando el binario")
        verify_binary(binary, work, env)
        shutil.copy2(binary, out_dir / "ffmpeg")
        (out_dir / "ffmpeg").chmod(0o755)

        info = {
            "ffmpeg_version": version,
            "source_url": FFMPEG_URL.format(version=version),
            "pgp_verified": signed,
            "x264_ref": x264_ref,
            "x264_commit": x264_commit,
            "libwebp_version": webp_version,
            "platform": host_platform(),
            "built_with": platform.platform(),
        }
        (out_dir / "ffmpeg-build-info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
        log(f"ffmpeg compilado: {out_dir / 'ffmpeg'}")
        return info
    finally:
        if work_dir or keep_work:
            log(f"Directorio de trabajo conservado: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(NODES_DIR / "bin"), help="carpeta donde dejar ffmpeg (por defecto PyxisNodes/bin)")
    parser.add_argument("--version", default=FFMPEG_VERSION, help=f"versión de ffmpeg (por defecto {FFMPEG_VERSION})")
    parser.add_argument("--jobs", type=int, help="trabajos de make en paralelo (por defecto, los núcleos)")
    parser.add_argument("--work", help="directorio de trabajo reutilizable (conserva las descargas entre ejecuciones)")
    parser.add_argument("--keep-work", action="store_true", help="no borrar el directorio de trabajo")
    parser.add_argument("--x264-ref", default=X264_REF, help=f"rama o etiqueta de x264 (por defecto {X264_REF})")
    parser.add_argument("--webp-version", default=WEBP_VERSION, help=f"versión de libwebp (por defecto {WEBP_VERSION})")
    parser.add_argument("--no-verify-signature", action="store_true", help="no comprobar la firma PGP del tarball")
    args = parser.parse_args()
    build(Path(args.out), version=args.version, jobs=args.jobs, work_dir=Path(args.work) if args.work else None,
          keep_work=args.keep_work, x264_ref=args.x264_ref, webp_version=args.webp_version,
          verify_signature=not args.no_verify_signature)
    return 0


if __name__ == "__main__":
    sys.exit(main())

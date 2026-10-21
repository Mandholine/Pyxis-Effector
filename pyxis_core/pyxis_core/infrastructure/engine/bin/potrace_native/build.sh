#!/usr/bin/env bash
# Pyxis Effector — Potrace Native Compiler
# Compiles Potrace 1.16 cleanly on macOS and Linux without autotools

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_BIN="$SCRIPT_DIR/../potrace"

COMPILER="${CC:-clang}"
if ! command -v "$COMPILER" &>/dev/null; then
    COMPILER="gcc"
fi

if ! command -v "$COMPILER" &>/dev/null; then
    echo "Error: Neither 'clang' nor 'gcc' compiler found." >&2
    exit 1
fi

echo "[Potrace Build] Compiling native binary with $COMPILER..."

cd "$SCRIPT_DIR/src"
$COMPILER -O3 -Wall -Wextra -DHAVE_CONFIG_H -I. -I.. \
    main.c bitmap_io.c backend_eps.c flate.c greymap.c render.c \
    backend_pgm.c backend_svg.c backend_xfig.c backend_dxf.c \
    backend_pdf.c backend_geojson.c backend_ass.c lzw.c progress_bar.c bbox.c \
    trans.c curve.c trace.c decompose.c potracelib.c \
    -o "$TARGET_BIN" -lm -lz

chmod +x "$TARGET_BIN"
echo "[Potrace Build] Done! Native binary created at: $TARGET_BIN"
"$TARGET_BIN" --version

TARGET_IMG2ASS="$SCRIPT_DIR/../img2ass"
echo "[img2ass Build] Compiling native direct image-to-Aegisub converter..."
$COMPILER -O3 -Wall -Wextra -DHAVE_CONFIG_H -I. -I.. \
    img2ass.c curve.c trace.c decompose.c potracelib.c \
    -o "$TARGET_IMG2ASS" -lm
chmod +x "$TARGET_IMG2ASS"
echo "[img2ass Build] Done! Native binary created at: $TARGET_IMG2ASS"


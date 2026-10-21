#!/usr/bin/env bash
# Quick build script for libass_profiler on Linux and macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Building libass_profiler Native ==="

# Check for pkg-config
if ! command -v pkg-config >/dev/null 2>&1; then
    echo "Warning: pkg-config not found. Attempting direct build with -lass..."
    LIBASS_FLAGS="-lass -lm"
else
    if ! pkg-config --exists libass; then
        echo "Error: libass development headers not found!"
        echo "Please install them:"
        echo "  Ubuntu/Debian:  sudo apt install libass-dev"
        echo "  Arch Linux:     sudo pacman -S libass"
        echo "  Fedora:         sudo dnf install libass-devel"
        echo "  macOS (brew):   brew install libass pkg-config"
        exit 1
    fi
    LIBASS_FLAGS="$(pkg-config --cflags --libs libass) -lm"
fi

CC="${CC:-gcc}"
if [ "$(uname)" = "Darwin" ] && command -v clang >/dev/null 2>&1; then
    CC="clang"
fi

echo "Compiler: $CC"
echo "Flags: $LIBASS_FLAGS"

$CC -O3 -Wall -Wextra -std=c99 libass_profiler.c -o libass_profiler $LIBASS_FLAGS

chmod +x libass_profiler

echo "Build successful: $SCRIPT_DIR/libass_profiler"
./libass_profiler || true

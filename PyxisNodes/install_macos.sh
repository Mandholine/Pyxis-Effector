#!/usr/bin/env bash
# Pyxis Effector - Developer Environment Installer for macOS
# Creates a virtual environment in PyxisNodes/.venv, installs Python dependencies,
# compiles native C99 tools (potrace, img2ass, libass_profiler), and checks
# system dependencies.
# Note: Prebuilt release archives (PyxisEffector-v*-macos-*.zip) already include
# a self-contained Python runtime and native binaries and do NOT require this script.
#
# Usage:  ./install_macos.sh

set -euo pipefail

PYXIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PYXIS_DIR/.venv"

echo "==> Pyxis Effector - macOS Developer Installer"

# Ensure Homebrew paths are visible
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Install it with:  brew install python" >&2
    exit 1
fi

PYVER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
echo "    Detected Python $PYVER ($(command -v python3))"

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "ERROR: Python 3.10 or newer is required. Install it with:  brew install python" >&2
    exit 1
fi

if [ ! -x "$VENV_DIR/bin/python3" ]; then
    echo "==> Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

echo "==> Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$PYXIS_DIR/requirements.txt"
echo "    Core Python dependencies installed"

if [ -f "$PYXIS_DIR/requirements-optional.txt" ]; then
    while IFS= read -r line; do
        spec="${line%%#*}"
        spec="$(echo "$spec" | xargs)"
        [ -z "$spec" ] && continue
        if "$VENV_DIR/bin/pip" install --quiet "$spec" >/dev/null 2>&1; then
            echo "    [OK] optional: $spec"
        else
            echo "    [..] optional skipped: $spec"
        fi
    done < "$PYXIS_DIR/requirements-optional.txt"
fi

echo "==> Building native C99 tools (potrace, img2ass, libass_profiler)"
if [ -f "$PYXIS_DIR/bin/potrace_native/build.sh" ]; then
    if bash "$PYXIS_DIR/bin/potrace_native/build.sh" >/dev/null 2>&1; then
        echo "    [OK] Native potrace and img2ass compiled in bin/"
    else
        echo "    [..] Could not compile potrace_native (ensure Xcode Command Line Tools are installed)"
    fi
fi

if [ -f "$PYXIS_DIR/bin/libass_profiler_native/build.sh" ]; then
    if bash "$PYXIS_DIR/bin/libass_profiler_native/build.sh" >/dev/null 2>&1; then
        echo "    [OK] Native libass_profiler compiled in bin/"
    else
        echo "    [..] Could not compile libass_profiler (install headers with: brew install libass pkg-config)"
    fi
fi

echo "==> Checking system dependencies"
WARN=0

if [ -x "$PYXIS_DIR/bin/ffmpeg" ] || command -v ffmpeg >/dev/null 2>&1; then
    echo "    [OK] ffmpeg available"
else
    echo "    [!!] ffmpeg NOT found (required for audio/video processing)"
    echo "         Run: python3 ../tools/get_ffmpeg.py  OR  brew install ffmpeg"
    WARN=1
fi

if "$VENV_DIR/bin/python" -c 'import AppKit, WebKit' >/dev/null 2>&1; then
    echo "    [OK] GUI backend: Cocoa (WebKit)"
else
    echo "    [!!] Cocoa bindings (pyobjc) missing; reinstall with:"
    echo "         $VENV_DIR/bin/pip install --force-reinstall pywebview"
    WARN=1
fi

echo ""
if [ "$WARN" -eq 0 ]; then
    echo "==> Installation completed with no warnings."
else
    echo "==> Installation completed with warnings (review the messages above)."
fi
echo ""
echo "To launch Pyxis Effector:"
echo "  - From Aegisub: copy PyxisNodes/ and Pyxis_engine.lua into"
echo "    ~/Library/Application Support/Aegisub/automation/autoload/ and run the macro."
echo "  - Standalone: $VENV_DIR/bin/python $PYXIS_DIR/main.py"


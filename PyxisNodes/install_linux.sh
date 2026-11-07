#!/usr/bin/env bash
# Pyxis Effector - Developer Environment Installer for Linux
# Creates a virtual environment in PyxisNodes/.venv, installs Python dependencies,
# compiles native C99 tools (potrace, img2ass, libass_profiler), and verifies
# system dependencies (ffmpeg, fontconfig, GUI backend).
#
# Usage:  ./install_linux.sh

set -euo pipefail

PYXIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PYXIS_DIR/.venv"

echo "==> Pyxis Effector - Linux Developer Installer"

# 1. Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Please install it via your distribution package manager." >&2
    exit 1
fi

PYVER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
echo "    Detected Python $PYVER"

if ! python3 -c 'import venv' >/dev/null 2>&1; then
    echo "ERROR: Python 'venv' module is not available." >&2
    echo "       Debian/Ubuntu: sudo apt install python3-venv" >&2
    exit 1
fi

# 2. Virtual environment (with --system-site-packages for system GTK/Qt bindings)
if [ ! -x "$VENV_DIR/bin/python3" ]; then
    echo "==> Creating virtual environment at $VENV_DIR"
    python3 -m venv --system-site-packages "$VENV_DIR"
fi

# 3. Python dependencies
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

# 4. Native C99 tools (potrace, img2ass, libass_profiler)
echo "==> Building native C99 tools (potrace, img2ass, libass_profiler)"
if [ -f "$PYXIS_DIR/bin/potrace_native/build.sh" ]; then
    if bash "$PYXIS_DIR/bin/potrace_native/build.sh" >/dev/null 2>&1; then
        echo "    [OK] Native potrace and img2ass compiled in bin/"
    else
        echo "    [..] Could not compile potrace_native (ensure gcc/clang and zlib1g-dev are installed)"
    fi
fi

if [ -f "$PYXIS_DIR/bin/libass_profiler_native/build.sh" ]; then
    if bash "$PYXIS_DIR/bin/libass_profiler_native/build.sh" >/dev/null 2>&1; then
        echo "    [OK] Native libass_profiler compiled in bin/"
    else
        echo "    [..] Could not compile libass_profiler (ensure libass-dev and pkg-config are installed)"
    fi
fi

# 5. System dependency checks
echo "==> Checking system dependencies"
WARN=0

if [ -x "$PYXIS_DIR/bin/ffmpeg" ] || command -v ffmpeg >/dev/null 2>&1; then
    echo "    [OK] ffmpeg available"
else
    echo "    [!!] ffmpeg NOT found (required for audio/video processing)"
    echo "         Run: python3 ../tools/get_ffmpeg.py  OR  sudo apt install ffmpeg"
    WARN=1
fi

if command -v fc-match >/dev/null 2>&1; then
    echo "    [OK] fontconfig: $(command -v fc-match)"
else
    echo "    [!!] fontconfig NOT found (font metrics resolution will be degraded)"
    echo "         Debian/Ubuntu: sudo apt install fontconfig | Arch: sudo pacman -S fontconfig"
    WARN=1
fi

if "$VENV_DIR/bin/python" - "$PYXIS_DIR" <<'PYEOF'
import sys
sys.path.insert(0, sys.argv[1] + "/src")
from dependency_checker import _check_posix_gui_backend
ok, backend, detail = _check_posix_gui_backend()
if ok:
    print(f"    [OK] GUI backend: {backend} ({detail})")
    sys.exit(0)
print("    [!!] GUI backend NOT available")
print("         GTK (recommended): sudo apt install python3-gi gir1.2-webkit2-4.1"
      " | Arch: sudo pacman -S python-gobject webkit2gtk-4.1")
sys.exit(1)
PYEOF
then
    :
else
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
echo "  - From Aegisub: copy PyxisNodes/ and Pyxis_engine.lua into your"
echo "    automation/autoload directory and run the 'Pyxis Effector' macro."
echo "  - Standalone: $VENV_DIR/bin/python $PYXIS_DIR/main.py"


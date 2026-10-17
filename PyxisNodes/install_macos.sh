#!/usr/bin/env bash
# Pyxis Effector - Instalador para macOS (instalación desde el código fuente)
# Crea un entorno virtual en PyxisNodes/.venv e instala las dependencias de Python.
# Si descargaste el paquete de release (PyxisEffector-v*-macos-*.zip) NO necesitas
# este script: ya incluye su propio Python.
#
# Uso:  ./install_macos.sh

set -euo pipefail

PYXIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PYXIS_DIR/.venv"

echo "==> Pyxis Effector — instalador para macOS"

# Homebrew no está en el PATH de algunos shells/entornos
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: no se encontró python3. Instálalo con:  brew install python" >&2
    exit 1
fi

PYVER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
echo "    Python $PYVER detectado ($(command -v python3))"

# /usr/bin/python3 (Xcode Command Line Tools) es demasiado antiguo para pywebview
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "ERROR: se necesita Python 3.10 o superior. Instálalo con:  brew install python" >&2
    exit 1
fi

if [ ! -x "$VENV_DIR/bin/python3" ]; then
    echo "==> Creando entorno virtual en $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

echo "==> Instalando dependencias de Python (puede tardar un momento)"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$PYXIS_DIR/requirements.txt"
echo "    Dependencias de Python instaladas correctamente"

while IFS= read -r line; do
    spec="${line%%#*}"
    spec="$(echo "$spec" | xargs)"
    [ -z "$spec" ] && continue
    if "$VENV_DIR/bin/pip" install --quiet "$spec" >/dev/null 2>&1; then
        echo "    [OK] opcional: $spec"
    else
        echo "    [··] opcional no instalado: $spec"
    fi
done < "$PYXIS_DIR/requirements-optional.txt"

echo "==> Comprobando dependencias del sistema"
WARN=0

if command -v ffmpeg >/dev/null 2>&1; then
    echo "    [OK] ffmpeg: $(command -v ffmpeg)"
else
    echo "    [!!] ffmpeg NO encontrado (obligatorio para audio/vídeo)"
    echo "         brew install ffmpeg"
    WARN=1
fi

if command -v potrace >/dev/null 2>&1; then
    echo "    [OK] potrace: $(command -v potrace)"
else
    echo "    [··] potrace no encontrado (opcional: vectorización rápida de imágenes)"
    echo "         brew install potrace"
fi

if command -v wine >/dev/null 2>&1 || command -v wine64 >/dev/null 2>&1 || [ -d "/Applications/Wine Stable.app" ]; then
    echo "    [OK] wine encontrado (telemetría de renderizado; sin probar en macOS)"
else
    echo "    [··] wine no encontrado (opcional: libass_profiler, la telemetría de renderizado, es un binario de Windows)"
    echo "         brew install --cask wine-stable"
fi

if "$VENV_DIR/bin/python" -c 'import AppKit, WebKit' >/dev/null 2>&1; then
    echo "    [OK] Backend gráfico: Cocoa (WebKit)"
else
    echo "    [!!] Faltan los bindings de Cocoa (pyobjc); reinstala con:"
    echo "         $VENV_DIR/bin/pip install --force-reinstall pywebview"
    WARN=1
fi

echo ""
if [ "$WARN" -eq 0 ]; then
    echo "==> Instalación completada sin avisos."
else
    echo "==> Instalación completada con avisos (revisa los mensajes anteriores)."
fi
echo ""
echo "Para lanzar Pyxis Effector:"
echo "  • Desde Aegisub: copia PyxisNodes/ y pyxis.NodeEngine.lua en"
echo "    ~/Library/Application Support/Aegisub/automation/autoload/ y ejecuta la macro."
echo "  • De forma independiente: $VENV_DIR/bin/python $PYXIS_DIR/main.py"
echo ""
echo "Consulta README.macos.md para más detalles."

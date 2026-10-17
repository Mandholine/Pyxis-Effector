#!/usr/bin/env bash
# Pyxis Effector - Instalador para Linux
# Crea un entorno virtual en PyxisNodes/.venv, instala las dependencias de Python
# y comprueba las dependencias del sistema (ffmpeg, fontconfig, backend gráfico).
#
# Uso:  ./install_linux.sh

set -euo pipefail

PYXIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PYXIS_DIR/.venv"

echo "==> Pyxis Effector — instalador para Linux"

# 1. Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: no se encontró python3. Instálalo con el gestor de paquetes de tu distribución." >&2
    exit 1
fi

PYVER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
echo "    Python $PYVER detectado"

if ! python3 -c 'import venv' >/dev/null 2>&1; then
    echo "ERROR: el módulo 'venv' no está disponible." >&2
    echo "       Debian/Ubuntu: sudo apt install python3-venv" >&2
    exit 1
fi

# 2. Entorno virtual (con acceso a los paquetes del sistema: python-gobject/gi,
#    PyQt6 y demás bindings GTK/Qt los gestiona el gestor de paquetes de la distro)
if [ ! -x "$VENV_DIR/bin/python3" ]; then
    echo "==> Creando entorno virtual en $VENV_DIR"
    python3 -m venv --system-site-packages "$VENV_DIR"
fi

# 3. Dependencias de Python
echo "==> Instalando dependencias de Python (puede tardar un momento)"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$PYXIS_DIR/requirements.txt"
echo "    Dependencias de Python instaladas correctamente"

# Dependencias opcionales (una a una: si alguna falla, Pyxis sigue funcionando)
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

# 4. Comprobaciones del sistema
echo "==> Comprobando dependencias del sistema"
WARN=0

if command -v ffmpeg >/dev/null 2>&1; then
    echo "    [OK] ffmpeg: $(command -v ffmpeg)"
else
    echo "    [!!] ffmpeg NO encontrado (obligatorio para audio/vídeo)"
    echo "         Debian/Ubuntu: sudo apt install ffmpeg | Arch: sudo pacman -S ffmpeg"
    WARN=1
fi

if command -v fc-match >/dev/null 2>&1; then
    echo "    [OK] fontconfig: $(command -v fc-match)"
else
    echo "    [!!] fontconfig NO encontrado (métricas tipográficas degradadas)"
    echo "         Debian/Ubuntu: sudo apt install fontconfig | Arch: sudo pacman -S fontconfig"
    WARN=1
fi

if command -v potrace >/dev/null 2>&1; then
    echo "    [OK] potrace: $(command -v potrace)"
else
    echo "    [··] potrace no encontrado (opcional: vectorización rápida de imágenes)"
    echo "         Debian/Ubuntu: sudo apt install potrace | Arch: sudo pacman -S potrace"
fi

if command -v wine >/dev/null 2>&1 || command -v wine64 >/dev/null 2>&1; then
    echo "    [OK] wine: $(command -v wine || command -v wine64) (telemetría de renderizado)"
else
    echo "    [··] wine no encontrado (opcional: libass_profiler, la telemetría de renderizado, es un binario de Windows)"
    echo "         Debian/Ubuntu: sudo apt install wine | Arch: sudo pacman -S wine"
fi

# Backend gráfico para la GUI (WebKitGTK o Qt WebEngine)
if "$VENV_DIR/bin/python" - "$PYXIS_DIR" <<'PYEOF'
import sys
sys.path.insert(0, sys.argv[1] + "/src")
from dependency_checker import _check_posix_gui_backend
ok, backend, detail = _check_posix_gui_backend()
if ok:
    print(f"    [OK] Backend gráfico: {backend} ({detail})")
    sys.exit(0)
print("    [!!] Backend gráfico NO disponible")
print("         GTK (recomendado): sudo apt install python3-gi gir1.2-webkit2-4.1"
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
    echo "==> Instalación completada sin avisos."
else
    echo "==> Instalación completada con avisos (revisa los mensajes anteriores)."
fi
echo ""
echo "Para lanzar Pyxis Effector:"
echo "  • Desde Aegisub: copia PyxisNodes/ y los archivos .lua en tu carpeta de"
echo "    automation/autoload y ejecuta la macro 'Pyxis Node Engine'."
echo "  • De forma independiente: $VENV_DIR/bin/python $PYXIS_DIR/main.py"
echo ""
echo "Consulta README.linux.md para más detalles."

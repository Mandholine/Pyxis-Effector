# Pyxis Effector — Guía para Linux

Puerto completo de Pyxis Effector para Linux: motor de nodos visual, previsualizador
WebAssembly y la integración con Aegisub (macro de Automation 4).

---

## Paquete de release (recomendado)

Descarga `PyxisEffector-v<versión>-linux64.zip` (o `linux-arm64`) desde
[Releases](https://github.com/Mandholine/Pyxis-Effector/releases) y descomprímelo en
`~/.config/aegisub/automation/autoload/`; crea `PyxisNodes/` con su propio Python 3.12,
las dependencias y Qt WebEngine para la interfaz. La macro también ofrece descargarlo
sola la primera vez. Solo hace falta lo que el paquete no puede llevar:

* `ffmpeg` incluido en el paquete; si se compiló sin él, instálalo con tu gestor de paquetes.
* Las bibliotecas de sistema que exige Qt WebEngine (en un escritorio normal ya están
  instaladas: `libnss3`, `libxkbcommon`, `libxcb-*`…).

El resto de este documento describe la **instalación desde el código fuente**.

---

## Requisitos del sistema (instalación desde el código fuente)

| Componente | Obligatorio | Propósito | Debian / Ubuntu | Arch |
|---|---|---|---|---|
| Python ≥ 3.10 | Sí | Motor de ejecución | `python3 python3-venv` | `python` |
| ffmpeg | Sí | Audio y vídeo | `ffmpeg` | `ffmpeg` |
| WebKitGTK 4.1 | Sí* | GUI (backend `gtk`) | `python3-gi gir1.2-webkit2-4.1` | `python-gobject webkit2gtk-4.1` |
| Qt WebEngine | Alternativa* | GUI (backend `qt`) | `python3-pyqt6.qtwebengine` | `python-pyqt6-webengine` |
| fontconfig | Recomendado | Resolución de fuentes | `fontconfig` | `fontconfig` |
| potrace | Opcional | Vectorización rápida de imágenes | `potrace` | `potrace` |
| tkinter | Opcional | Diálogos de archivo de respaldo | `python3-tk` | `tk` |
| wmctrl / xdotool | Opcional | Elevar el foco de la ventana | `wmctrl` / `xdotool` | igual |

\* Se necesita **uno** de los dos backends gráficos. GTK (WebKitGTK) es el recomendado.

Aegisub está disponible en la mayoría de distribuciones (`aegisub` o `aegisub-git`).

---

## Instalación

```bash
git clone https://github.com/Mandholine/Pyxis-Effector.git
cd Pyxis-Effector/PyxisNodes
./install_linux.sh
```

El instalador crea un entorno virtual en `PyxisNodes/.venv`, instala las dependencias
de Python (`requirements.txt`) y comprueba las dependencias del sistema.

Instalación manual equivalente:

```bash
cd PyxisNodes
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt
```

> `--system-site-packages` es necesario para que el entorno virtual vea los bindings
> GTK/Qt (`python-gobject` / PyQt) instalados por el gestor de paquetes de la distro.

---

## Uso con Aegisub

1. Copia a tu carpeta de automation de Aegisub (`~/.config/aegisub/automation/autoload/`
   o `?user/automation/autoload` dentro de Aegisub):
   * `PyxisNodes/` (carpeta completa, con `.venv` incluido)
   * `pyxis.NodeEngine.lua`
2. En Aegisub: **Automatización → Pyxis Node Engine**.
3. La macro exporta las líneas seleccionadas, abre el editor visual y, al generar,
   inyecta las capas de efectos (`Pyxis_fx`) en la subtítulo.

Flujo en Linux (idéntico a Windows):

* La macro resuelve el intérprete en este orden: `PyxisNodes/.venv/bin/python3` →
  `python3` del sistema → `python`.
* El proceso se lanza desacoplado (`nohup … &`); el daemon HTTP local
  (`127.0.0.1:28723`) permite reaperturas instantáneas sin relanzar Python.
* Si el daemon detecta que Aegisub ha cerrado (PID), se apaga automáticamente.

## Uso independiente (sin Aegisub)

```bash
cd PyxisNodes
.venv/bin/python main.py
```

---

## Ubicación de datos (XDG)

En Linux los datos de usuario viven en `$XDG_DATA_HOME/PyxisNodes`
(por defecto `~/.local/share/PyxisNodes`):

| Ruta | Contenido |
|---|---|
| `~/.local/share/PyxisNodes/user_config.json` | Configuración, geometría de ventana |
| `~/.local/share/PyxisNodes/temp_cache/` | Puente temporal con Aegisub |
| `~/.local/share/PyxisNodes/temp/` | Temporales internos, caché de audio |
| `~/.local/share/PyxisNodes/templates/` | Plantillas de usuario |
| `~/.local/share/PyxisNodes/themes/` | Temas personalizados |

En Windows se mantiene el comportamiento histórico (`%APPDATA%\PyxisNodes`).

---

## Paridad de funciones

| Función | Windows | Linux |
|---|---|---|
| Editor de nodos, preview, partículas | ✔ | ✔ |
| Métricas y contornos tipográficos | Win32 GDI | **FreeType + fontconfig** (`freetype-py`) |
| Texto a forma vectorial (`text_to_shape`) | Contornos GDI | Contornos FreeType reales |
| Audio / vídeo | ffmpeg empaquetado | ffmpeg del sistema |
| Vectorización de imágenes | potrace.exe | potrace del sistema (fallback Python) |
| GPU OpenCL / CUDA | ✔ | ✔ (pyopencl / CPU fallback) |
| Telemetría libass (`libass_profiler`) | ✔ | ✔ mediante **Wine** (ver abajo); sin Wine, error controlado |
| Limpieza de procesos hijos | Job Object | `PR_SET_PDEATHSIG` |
| Descarga automática del motor desde la macro | ✔ (zip win64) | ✔ (zip linux64) o instalación manual |

Notas:

* La macro busca el intérprete en este orden: `PyxisNodes/python/bin/python3` (paquete
  de release) → `PyxisNodes/.venv/bin/python3` → `python3` del sistema.
* Si clonaste el repositorio, `PyxisNodes/python/` puede contener el runtime de Windows
  (`python.exe`); no se usa en Linux. Los paquetes de Linux se generan con
  `python tools/build_release.py` y no comparten ese directorio.
* `bin/*.exe` y `bin/ffmpeg.rar` tampoco se usan en Linux.
* **Telemetría de renderizado:** `libass_profiler` solo existe como binario de Windows
  (`bin/libass_profiler.exe`). Si hay `wine` instalado, Pyxis lo ejecuta con él de forma
  automática (es una herramienta de consola, no necesita pantalla). Es una solución
  provisional hasta que exista un port nativo:
  * La primera vez crea un prefijo de Wine propio en `~/.local/share/PyxisNodes/wine`
    (unos 10 s); las siguientes ejecuciones tardan fracciones de segundo.
  * Los tiempos de render son orientativos: miden libass dentro de Wine, con su
    resolución de fuentes (DirectWrite sobre fontconfig) y sin los mismos cachés que Windows.
  * Si colocas un `libass_profiler` nativo en `PyxisNodes/bin/` (o en el `PATH`), tiene
    prioridad y Wine deja de usarse.
  * Variables de entorno: `PYXIS_DISABLE_WINE=1` (nunca usar Wine), `PYXIS_WINE=<ruta>`
    (otro ejecutable de wine), `PYXIS_WINEPREFIX=<dir>` (otro prefijo).
  * Instalación de Wine: `sudo apt install wine` / `sudo pacman -S wine`.

---

## Solución de problemas

* **«Backend gráfico NO disponible»** → instala `python3-gi gir1.2-webkit2-4.1`
  (GTK) o el paquete Qt WebEngine de tu distro, y vuelve a crear el venv con
  `--system-site-packages`.
* **La macro no encuentra Python** → ejecuta `install_linux.sh` para crear
  `PyxisNodes/.venv`, o instala `python3` en el PATH.
* **Tipografías con métricas imprecisas** → instala `fontconfig` y verifica que la
  familia existe (`fc-match "Nombre De La Fuente"`). Pyxis resuelve las fuentes
  igual que Aegisub: si una familia no existe, se usa la sustitución de fontconfig.
* **No se abre la ventana** → revisa `~/.local/share/PyxisNodes/temp/*_debug.log`
  (el arranque escribe ahí el traceback completo).
* **El audio no se procesa** → `ffmpeg` es obligatorio; comprueba con `ffmpeg -version`.

---

## Licencia

GPL-3.0 — consulta `LICENSE`. El código conserva compatibilidad completa con Windows.

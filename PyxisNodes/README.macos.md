# Pyxis Effector — Guía para macOS

Pyxis Effector funciona en macOS (Apple Silicon e Intel) con la interfaz nativa de
Cocoa/WebKit y la macro de Automation 4 de Aegisub.

> **Estado:** el soporte de macOS está implementado pero todavía no se ha probado en
> hardware Mac. Si encuentras un problema, abre una incidencia con el contenido de
> `~/.local/share/PyxisNodes/temp/` (registros de arranque).

---

## Instalación (paquete de release, recomendado)

1. Descarga desde [Releases](https://github.com/Mandholine/Pyxis-Effector/releases):
   * `PyxisEffector-v<versión>-macos-arm64.zip` — Macs con Apple Silicon (M1 o posterior).
   * `PyxisEffector-v<versión>-macos-x64.zip` — Macs con Intel.
2. Descomprime en la carpeta de automatización de Aegisub (se crea `PyxisNodes/`):
   `~/Library/Application Support/Aegisub/automation/autoload/`
3. Copia ahí también `pyxis.NodeEngine.lua`.
4. En Aegisub: **Automatización → Pyxis Node Engine**. Si falta el motor, la macro ofrece
   descargarlo sola.

El paquete incluye su propio Python 3.12 y todas las dependencias: no necesitas Homebrew
ni instalar Python.

### Gatekeeper

Los paquetes no están firmados con un certificado de Apple. Si los descargas con el
navegador, macOS los pone en cuarentena y bloqueará el Python incluido. Quita la marca
una vez:

```bash
xattr -dr com.apple.quarantine ~/Library/Application\ Support/Aegisub/automation/autoload/PyxisNodes
```

Si la macro descarga el motor por sí misma, ejecuta ese comando automáticamente.

### ffmpeg

El paquete incluye un ffmpeg nativo para tu arquitectura (de [ffmpeg.martin-riedl.de](https://ffmpeg.martin-riedl.de),
con libx264, libass, libwebp y VideoToolbox, verificado por SHA-256). Si se construyó con `--no-ffmpeg`,
instálalo con Homebrew (`brew install ffmpeg`); Pyxis busca también en `/opt/homebrew/bin` y `/usr/local/bin`,
aunque Aegisub se abra desde el Finder con un `PATH` mínimo. `potrace` es opcional (`brew install potrace`).

Para compilar tu propio ffmpeg desde el código fuente: [tools/README.md](../tools/README.md).

---

## Instalación desde el código fuente

```bash
brew install python ffmpeg        # Python ≥ 3.10; /usr/bin/python3 es demasiado antiguo
cd PyxisNodes && ./install_macos.sh
```

Después copia `PyxisNodes/` y `pyxis.NodeEngine.lua` a la carpeta `autoload` de Aegisub.
La macro usa `PyxisNodes/.venv/bin/python3` si no hay un runtime en `PyxisNodes/python/`.

Uso independiente: `PyxisNodes/.venv/bin/python PyxisNodes/main.py`.

---

## Ubicación de datos

Igual que en Linux: `~/.local/share/PyxisNodes` (o `$XDG_DATA_HOME/PyxisNodes`).

---

## Diferencias respecto a Windows

| Función | macOS |
|---|---|
| Interfaz | Cocoa/WebKit (pywebview) |
| Métricas y contornos tipográficos | FreeType; las fuentes se localizan en `/System/Library/Fonts`, `/Library/Fonts` y `~/Library/Fonts` |
| Codificación de vídeo | `h264_videotoolbox` si ffmpeg lo incluye; si no, x264 |
| GPU OpenCL | Opcional (Apple lo considera obsoleto); si falla, se usa la CPU |
| Telemetría libass (`libass_profiler`) | Solo mediante Wine (ver abajo); sin Wine, error controlado |
| Limpieza de procesos hijos | Vigilancia del proceso padre en cada worker |

### Telemetría de renderizado (Wine, provisional)

`libass_profiler` solo existe como binario de Windows. Pyxis intenta ejecutarlo con Wine si
lo encuentra (`brew install --cask wine-stable`, Wine Stable/Staging/Devel o CrossOver en
`/Applications`). **Esta vía no se ha probado en macOS** (en Linux sí): Wine en macOS solo
existe para Intel, así que en Apple Silicon necesita Rosetta 2. Si no funciona, la
telemetría se desactiva con un mensaje de error y el resto de Pyxis no se ve afectado.
Los detalles (prefijo propio, variables `PYXIS_WINE`, `PYXIS_DISABLE_WINE`, precisión de los
tiempos) son los mismos que en [README.linux.md](README.linux.md). Un `libass_profiler`
nativo en `PyxisNodes/bin/` tendrá prioridad cuando exista.

---

## Solución de problemas

* **«Faltan los bindings de Cocoa»** → reinstala con `pip install --force-reinstall pywebview`.
* **La macro no encuentra Python** → reinstala el paquete de release o ejecuta `install_macos.sh`.
* **«"python3" no puede abrirse porque no se puede verificar el desarrollador»** → ver *Gatekeeper*.
* **No se abre la ventana** → revisa `~/.local/share/PyxisNodes/temp/*_debug.log` y
  `preflight_debug.log`.
* **El audio no se procesa** → comprueba `ffmpeg -version` desde una Terminal.

---

## Licencia

GPL-3.0 — consulta `LICENSE`.

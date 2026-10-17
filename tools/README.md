# Herramientas de construcción

Scripts para generar los paquetes de release de Pyxis Effector. Solo necesitan Python 3.9+ y
la biblioteca estándar.

| Script | Para qué sirve |
|---|---|
| `build_release.py` | Construye `dist/PyxisEffector-v<versión>-<plataforma>.zip` con Python, dependencias y ffmpeg incluidos. |
| `get_ffmpeg.py` | Obtiene un ffmpeg listo para Pyxis (descargado y verificado, o compilado) y lo deja en `PyxisNodes/bin/`. |
| `build_ffmpeg.py` | Compila ffmpeg desde el código fuente (Linux y macOS). |

```bash
python tools/build_release.py              # paquete de la plataforma actual
python tools/get_ffmpeg.py                 # solo ffmpeg, para trabajar desde el repositorio
```

Las plataformas son `win64`, `linux64`, `linux-arm64`, `macos-arm64` y `macos-x64`. Cada paquete
hay que construirlo en una máquina de esa plataforma; el workflow
[`.github/workflows/release.yml`](../.github/workflows/release.yml) lo hace en CI al subir una
etiqueta `v*`.

## ffmpeg

Pyxis necesita un ffmpeg con **libx264**, **libwebp** y **libass** (el filtro `subtitles` que
incrusta los subtítulos en el vídeo), además de AAC. Los scripts comprueban esto con
codificaciones de prueba reales y rechazan un binario al que le falte algo.

FFmpeg solo publica código fuente: los binarios que enlaza [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
los compilan terceros. Por eso hay dos vías.

### 1. Descargar un build (por defecto)

| Plataforma | Proveedor | Verificación |
|---|---|---|
| `win64`, `linux64`, `linux-arm64` | [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds) — rama de release `n9.0`, variante GPL | SHA-256 de su `checksums.sha256` |
| `macos-arm64`, `macos-x64` | [ffmpeg.martin-riedl.de](https://ffmpeg.martin-riedl.de) — release estable | SHA-256 publicado junto al archivo |

`python tools/get_ffmpeg.py --list-sources` muestra las URL y los hashes que se usarían ahora.
Si el hash no coincide, el script aborta sin instalar nada.

Otros builds que enlaza ffmpeg.org se pueden usar con `--url` (y `--sha256` si lo publican):

```bash
python tools/get_ffmpeg.py --platform win64 --url https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip \
                           --sha256 "$(curl -sL https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip.sha256)"
python tools/get_ffmpeg.py --platform macos-x64 --url https://evermeet.cx/ffmpeg/ffmpeg-9.0.2.zip   # solo Intel, sin hash publicado
```

> Los hashes protegen contra descargas corruptas, no contra un proveedor comprometido, porque se
> sirven desde el mismo sitio que el archivo. Si eso te importa, compila (opción 2).

### 2. Compilar desde el código fuente

```bash
python tools/get_ffmpeg.py --build                 # lo deja en PyxisNodes/bin/
python tools/build_release.py --ffmpeg-build       # o directamente dentro del paquete
python tools/build_ffmpeg.py --out /ruta --jobs 8  # el script de compilación por sí solo
```

Qué hace `build_ffmpeg.py`:

1. Descarga `ffmpeg-<versión>.tar.xz` **de ffmpeg.org** y comprueba su firma PGP contra la huella
   `FCF986EA15E6E293A5644F10B4322F04D67658D8` publicada en su página de descargas (necesita `gpg`;
   si falta, avisa y sigue). Un tarball alterado se rechaza.
2. Compila **libx264** (rama `stable` de VideoLAN) y **libwebp** (tarball de Google con SHA-256
   fijado) como bibliotecas estáticas.
3. Configura ffmpeg con `--disable-autodetect` (solo lo pedido: GPL, libx264, libwebp, libass,
   zlib; en macOS también VideoToolbox/AudioToolbox) y lo compila.
4. Ejecuta pruebas reales: libx264, AAC, libwebp, el filtro `subtitles` y `scale`+`pad`.

Requisitos previos (el script los comprueba y dice qué falta):

| Sistema | Instalación |
|---|---|
| Debian/Ubuntu | `sudo apt install build-essential nasm pkg-config git libass-dev zlib1g-dev gnupg` |
| Arch | `sudo pacman -S base-devel nasm pkgconf git libass zlib gnupg` |
| macOS | `xcode-select --install && brew install nasm pkg-config libass gnupg` |

Limitaciones:

* **libass y sus dependencias** (freetype, fribidi, harfbuzz, fontconfig) **se enlazan dinámicamente
  desde el sistema**. El binario funciona en el equipo que lo compiló; no es portable. Para repartir
  un ffmpeg portable usa los builds alojados.
* **Windows no está soportado** (compilar con MSYS2 queda fuera); usa los builds alojados.
* Tarda unos 10 minutos en un equipo de 16 núcleos (la mayor parte es ffmpeg).
* No incluye codificadores de hardware de NVIDIA/AMD/Intel; Pyxis recurre a x264 por software.

Versiones por defecto: ffmpeg 9.0.2, libwebp 1.6.0, x264 `stable`. Se cambian con `--version`,
`--webp-version` y `--x264-ref`. Junto al binario se escribe `ffmpeg-build-info.json` con las
versiones y el commit exacto de x264.

## Publicar una release

La macro de Aegisub descarga `PyxisEffector-v<versión>-<plataforma>.zip` de la release cuya etiqueta es
**`v<versión>`**, donde `<versión>` es el `script_version` de `pyxis.NodeEngine.lua`. El workflow
`release.yml` publica con esa etiqueta, así que para sacar una release basta con:

```bash
git tag v1.1.4 && git push origin v1.1.4
```

* Si la etiqueta `v<versión>` no existe, la macro prueba también `PyxisEffector-v<versión>-<plataforma>`, la
  etiqueta que usó la primera release (subida a mano, solo Windows).
* **Forks:** la macro descarga de `Mandholine/Pyxis-Effector`. Para probar las releases de un fork sin tocar
  el código, abre Aegisub con `PYXIS_RELEASE_REPO=usuario/repositorio` en el entorno. Para que un fork las use
  siempre, cambia la constante `RELEASE_REPO` de `pyxis.NodeEngine.lua` y las URL de `DependencyControl.json`
  (y actualiza su `sha1`: `sha1sum pyxis.NodeEngine.lua`). `Pyxis_engine.lua` es una copia idéntica que debe
  mantenerse sincronizada.

## Licencia

Los builds que se incluyen y los que se compilan con estas opciones son **GPL** (libx264). El código
de Pyxis también es GPL-3.0. El paquete lleva `bin/FFMPEG-NOTICE.txt` con el origen del binario, el
SHA-256 y dónde obtener su código fuente (`ffmpeg -buildconf` da la configuración exacta).

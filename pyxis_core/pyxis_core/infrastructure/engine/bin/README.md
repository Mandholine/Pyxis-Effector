# Motores Nativos y Binarios de Alto Rendimiento

Esta carpeta contiene las herramientas nativas en C99 de alto rendimiento integradas con **Pyxis Effector**:
1. **`img2ass`**: Vectorizador nativo directo de imágenes (PNG/JPG/WebP/BMP) a subtítulos Aegisub ASSDraw (`{\p1}m ... b ...{\p0}`) conforme a la especificación técnica de Pyxis (Sección 12: *Shape/IMG to Shape*).
2. **`libass_profiler`**: Medidor de rendimiento fotograma a fotograma y generador de telemetría ASS.
3. **`potrace`**: Binario oficial de Potrace 1.16 con soporte nativo para ASS y SVG.

---

## 🎨 Prueba Rápida de `img2ass` (Vectorización de Imagen a Shape ASS)

Para probar la conversión directa de una imagen PNG (con transparencia) a un archivo de subtítulo listo para abrir en **Aegisub**:

```bash
# 1. Navegar a la carpeta de binarios
cd pyxis_core/pyxis_core/infrastructure/engine/bin

# 2. Ejecutar la prueba con la imagen de muestra (payasito.png)
./img2ass images/payasito.png payasito.ass
```

> [!TIP]
> **Abre `payasito.ass` directamente en Aegisub.** Verás el dibujo vectorial centrado en el medio de la pantalla (1920x1080) sin ningún recuadro blanco ni distorsión, renderizado con la etiqueta estándar `{\p1\pos(960,540)\1c&HFFFFFF&\bord0}`.

### Modos y Opciones de Prueba de `img2ass`
```bash
# Prueba 1: Modo silueta (extrae el cuerpo completo según canal alfa)
./img2ass images/payasito.png payasito_silueta.ass --bin_mode silhouette

# Prueba 2: Ajustar umbral y suavizado de esquinas
./img2ass images/payasito.png payasito.ass --threshold 140 --tolerance 1.5 --alphamax 1.0

# Prueba 3: Cambiar posición cartesiana o escala
./img2ass images/payasito.png payasito.ass --pos 1280 720 --scale 1.5

# Prueba 4: Obtener únicamente la cadena ASSDraw pura por consola
./img2ass images/payasito.png --raw
```

---

## ⏱️ `libass_profiler` — Generador de Telemetría y Rendimiento ASS

**`libass_profiler`** es una herramienta nativa de alto rendimiento escrita en C99 que utiliza la biblioteca `libass` para renderizar subtítulos ASS cuadro a cuadro (*frame by frame*) y medir métricas precisas de consumo de tiempo y memoria.

Genera un archivo `.csv` que identifica caídas de fotogramas (*dropped frames*), picos de lag y consumo de memoria del renderizador.

---

## 🚀 Compilación Multiplataforma

### 1. Compilar `img2ass` y `potrace`
```bash
cd pyxis_core/pyxis_core/infrastructure/engine/bin/potrace_native
./build.sh
```

### 2. Compilar `libass_profiler`
#### 🍎 En macOS (Apple Silicon e Intel)
```bash
brew install libass pkg-config
cd pyxis_core/pyxis_core/infrastructure/engine/bin/libass_profiler_native
clang -O3 -Wall -Wextra -std=c99 libass_profiler.c -o ../libass_profiler -I/opt/homebrew/include -L/opt/homebrew/lib -lass -lm
chmod +x ../libass_profiler
```

#### 🐧 En Linux (Ubuntu / Debian / Arch)
```bash
# Ubuntu / Debian
sudo apt install libass-dev build-essential pkg-config
cd pyxis_core/pyxis_core/infrastructure/engine/bin/libass_profiler_native
gcc -O3 -Wall -Wextra -std=c99 libass_profiler.c -o ../libass_profiler $(pkg-config --cflags --libs libass) -lm
chmod +x ../libass_profiler
```

---

## 📋 Ejemplos de Telemetría con `libass_profiler`

```bash
cd pyxis_core/pyxis_core/infrastructure/engine/bin

# Generar reporte de telemetría CSV de un archivo ASS:
./libass_profiler "ass/test.ass" "reporte.csv"

# Inspeccionar resultados
head -n 20 reporte.csv
```

---

## 🐍 Uso Automático desde Python (`pyxis_core`)

```python
# 1. Vectorización de imágenes a Shapes ASS
from pyxis_core.infrastructure.adapters import ImageTracerAdapter

resultado = ImageTracerAdapter.trace("images/payasito.png", mode="Potrace", anchor="Center")
print("ASSDraw shape:", resultado["shape"][:50], "...")

# 2. Análisis de Telemetría y Rendimiento
from pyxis_core.infrastructure.adapters import TelemetryAdapter

telemetria = TelemetryAdapter.analyze_file("ass/test.ass", fps=23.976)
print("Frames totales:", telemetria["summary"]["total_frames"])
```


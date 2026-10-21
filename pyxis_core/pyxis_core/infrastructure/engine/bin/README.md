# libass_profiler — Generador de Telemetría y Rendimiento ASS

**`libass_profiler`** es una herramienta nativa de alto rendimiento escrita en C99 que utiliza la biblioteca `libass` para renderizar subtítulos ASS cuadro a cuadro (*frame by frame*) y medir métricas precisas de consumo de tiempo y memoria.

Genera un archivo `.csv` que identifica caídas de fotogramas (*dropped frames*), picos de lag y consumo de memoria del renderizador.

---

## 🚀 Compilación Multiplataforma

### 🍎 En macOS (Apple Silicon M1-M4 e Intel)
```bash
# 1. Instalar dependencias con Homebrew
brew install libass pkg-config

# 2. Compilar binario nativo
cd pyxis_core/pyxis_core/infrastructure/engine/bin/libass_profiler_native
clang -O3 -Wall -Wextra -std=c99 libass_profiler.c -o ../libass_profiler -I/opt/homebrew/include -L/opt/homebrew/lib -lass -lm
chmod +x ../libass_profiler
```

### 🐧 En Linux (Ubuntu / Debian / Arch)
```bash
# Ubuntu / Debian
sudo apt install libass-dev build-essential pkg-config
# Arch Linux
sudo pacman -S libass base-devel pkgconf

# Compilar
cd pyxis_core/pyxis_core/infrastructure/engine/bin/libass_profiler_native
gcc -O3 -Wall -Wextra -std=c99 libass_profiler.c -o ../libass_profiler $(pkg-config --cflags --libs libass) -lm
chmod +x ../libass_profiler
```

### 🪟 En Windows
- El binario precompilado `libass_profiler.exe` ya se encuentra en esta carpeta.
- Para recompilarlo usando MSYS2 / MinGW-w64:
  ```cmd
  cd pyxis_core\pyxis_core\infrastructure\engine\bin\libass_profiler_native
  gcc -O3 libass_profiler.c -o ..\libass_profiler.exe -lass -lfreetype -lm
  ```

---

## 📋 Ejemplos de Uso

### 1. En Windows (Modo Gráfico / Drag & Drop)
- Arrastra directamente cualquier archivo `.ass` sobre `libass_profiler.exe`.
- Se generará automáticamente un archivo llamado `output.csv` en el mismo directorio.

---

### 2. En macOS / Linux (Terminal)

#### A. Generar `output.csv` por defecto
```bash
# Desde la raíz del proyecto:
./pyxis_core/pyxis_core/infrastructure/engine/bin/libass_profiler "ruta/a/subtitulo.ass"
```

#### B. Generar un CSV con nombre y ruta personalizados
```bash
# Guardar como reporte.csv
./pyxis_core/pyxis_core/infrastructure/engine/bin/libass_profiler "ruta/a/subtitulo.ass" "reporte.csv"

# Ejemplo dentro de la carpeta bin:
cd pyxis_core/pyxis_core/infrastructure/engine/bin
./libass_profiler "ass/test.ass" "ass/reporte.csv"
```

#### C. Especificar una tasa de cuadros (FPS) personalizada
Por defecto analiza a `23.976 fps` (~41.7 ms por frame). Si tu vídeo es a 60 fps:
```bash
./libass_profiler "ass/test.ass" "reporte_60fps.csv" --fps 60.0
```

#### D. Inspeccionar los resultados generados
```bash
# Ver las primeras 20 líneas del CSV
head -n 20 reporte.csv

# Ver cuántos frames se analizaron en total
wc -l reporte.csv
```

---

## 📊 Estructura del CSV Generado

El archivo `.csv` tiene el siguiente formato estándar:

```csv
../ass/test.ass
time,total_image_size,largest_image_size,image_count,time_benchmark
0:00:00.000,0,0,0,0.000020
0:00:00.042,45120,12800,4,0.003150
0:00:00.083,45120,12800,4,0.003120
...
```

| Columna | Descripción |
| :--- | :--- |
| **`time`** | Marca de tiempo del frame en formato ASS (`H:MM:SS.mmm`). |
| **`total_image_size`** | Memoria acumulada en bytes de todos los bitmaps de glifos/formas en el frame. |
| **`largest_image_size`** | Tamaño en bytes del bitmap individual más grande en ese frame. |
| **`image_count`** | Cantidad de objetos/imágenes que libass dibuja simultáneamente en pantalla. |
| **`time_benchmark`** | Tiempo en segundos que tardó la CPU en rasterizar ese frame (ej: `0.003150` = 3.15 ms). |

---

## 🐍 Uso Automático desde Python (`pyxis_core`)

En lugar de invocar el binario manualmente por consola, `pyxis_core` lo hace de forma automática y analiza los puntos calientes (*hotspots*):

```python
from pyxis_core.infrastructure.adapters import TelemetryAdapter

# Analiza el subtítulo y obtiene el resumen de rendimiento
resultado = TelemetryAdapter.analyze_file("ass/test.ass", fps=23.976)

resumen = resultado["summary"]
print(f"Fotogramas totales: {resumen['total_frames']}")
print(f"Tiempo promedio: {resumen['avg_render_ms']} ms")
print(f"Pico máximo: {resumen['peak_render_ms']} ms")
print(f"Frames con lag (dropped): {resumen['dropped_frames_count']}")

# Lista de momentos críticos de lag en el vídeo:
for spot in resultado["hotspots"]:
    print(f"Lag en {spot['abs_display_time']} - Render: {spot['render_ms']}ms ({spot['budget_pct']}% del presupuesto)")
```

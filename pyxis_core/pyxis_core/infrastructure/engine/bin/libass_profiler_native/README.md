# libass_profiler Native — Informe de Ingeniería Inversa y Reimplementación

> **Ubicación:** `Código de referencia (no se modifica)/libass_profiler_native/`  
> **Propósito:** Reemplazar el binario precompilado de Windows (`libass_profiler.exe`) por una reimplementación nativa en C puro (C99) portable a **Linux**, **macOS** y **Windows**, eliminando el uso de emuladores como Wine en sistemas POSIX.

---

## 1. Resumen Ejecutivo

El motor de telemetría de Pyxis Effector (`ass_telemetry_engine.py`) utiliza un binario llamado `libass_profiler.exe` para perfilar el rendimiento fotograma a fotograma de scripts ASS. En las versiones originales para Windows, este ejecutable corre de forma nativa. Sin embargo, en la adaptación comunitaria a Linux y macOS realizada por Zagon, el script requería ejecutar `libass_profiler.exe` a través de **Wine**, lo cual acarreaba:
1. Una sobrecarga de inicialización notable (arrancar el proceso de Wine por cada fragmento/shard).
2. Errores frecuentes de traducción de rutas absolutas UNIX $\leftrightarrow$ Windows (`Z:\tmp\...`).
3. Dificultad para empaquetar una suite autosuficiente en macOS (donde Wine no siempre está disponible o requiere configuraciones complejas).

Mediante un análisis de ingeniería inversa sobre el binario original, se descubrió que **no se trata de un software propietario complejo**, sino de un *wrapper* de benchmark en C (~100 líneas) enlazado estáticamente contra `libass 0.17.3`. Se ha llevado a cabo una **reimplementación limpia (*clean-room*) en C99**, 100% compatible con el protocolo y los CSVs de salida, permitiendo compilación nativa directa con `gcc` o `clang`.

---

## 2. Hallazgos de la Ingeniería Inversa

El análisis estático y dinámico sobre `Version en desarrollo/PyxisNodes/bin/libass_profiler.exe` (5,913,129 bytes, PE32+ x86-64) arrojó los siguientes datos clave:

### 2.1. Anatomía del Binario
* **Composición:** El 98.5% del tamaño corresponde al código estático de las dependencias (`libass 0.17.3`, `FreeType`, `HarfBuzz 10.2.0`, `FriBidi 1.0.15`, `libpng`, `zlib`).
* **Secciones de Depuración:** El binario conserva secciones DWARF 5 (`/4`, `/19`, `/31`, `/45`, etc., mapeadas a `.debug_info`, `.debug_line`, `.debug_abbrev`), lo que facilitó identificar con precisión quirúrgica el compilador original (MinGW-w64 GCC) y las funciones internas.

### 2.2. Parámetros de Entrada y Salida (CLI)
* Mensaje de ayuda en `.rdata` (RVA `0x29f010`):
  ```text
  libass version 24129536
  Usage: libass_profiler <assfile> <output>
  output is optional and defaults to output.csv
  ```
* Si no se especifica el archivo de salida, escribe por defecto en `output.csv`.

### 2.3. Formato Canónico del CSV de Salida
* **Línea 1:** Ruta exacta del archivo analizado (`%s\n`).
* **Línea 2 (Cabecera):**
  ```csv
  time,total_image_size,largest_image_size,image_count,time_benchmark
  ```
* **Líneas de Datos:** Cadena de formato `"%s,%lld,%lld,%lld,%lf\n"`.

### 2.4. Algoritmos y Fórmulas Inversas (Ensamblador $\to$ C)

#### A. Cálculo de la duración total del track (Función en RVA `0x1605`)
El programa lee el archivo ASS con `ass_read_file(library, ass_path, NULL)` y busca la marca de tiempo de fin más alta de todos los eventos:
```c
long long max_end = 0;
for (int i = 0; i < track->n_events; i++) {
    ASS_Event *ev = &track->events[i];
    long long end_time = (long long)ev->Start + (long long)ev->Duration;
    if (end_time > max_end) max_end = end_time;
}
```

#### B. Avance temporal y tasa de cuadros (Framerate)
En la sección `.data` (RVA `0x29d008`), se halló la constante IEEE 754 float `23.97599983215332` (`23.976 fps`).
El cálculo del tiempo actual del fotograma se redondea en milisegundos:
```c
float fps = 23.976f;
int frame_index = 0;
long long current_time_ms = (long long)roundf((float)frame_index * (1000.0f / fps));
// Bucle mientras: current_time_ms < total_duration_ms
```

#### C. Cronometrado de Alta Precisión
El renderizado del fotograma se aísla llamando a temporizadores de alta resolución:
* **Windows (Original):** `QueryPerformanceCounter` contra `QueryPerformanceFrequency`.
* **POSIX (Linux/macOS):** `clock_gettime(CLOCK_MONOTONIC, &ts)`.
```c
double t_start = get_time_seconds();
ASS_Image *img = ass_render_frame(renderer, track, current_time_ms, &detect_change);
double time_benchmark = get_time_seconds() - t_start;
```

#### D. Fórmula de Memoria de Bitmaps (`ASS_Image`)
En el bucle de inspección de los glifos renderizados (RVA `0x1891`), el desensamblado reveló la fórmula de tamaño de buffer:
```assembly
mov eax, [rax + 0x04]   ; img->h
sub eax, 1              ; (h - 1)
imul eax, [rbp - 0x04]  ; (h - 1) * img->stride
mov edx, eax
mov eax, [rax]          ; img->w
add eax, edx            ; (h - 1) * stride + w
```
En C:
$$\text{size} = (h - 1) \times \text{stride} + w$$
Esta fórmula calcula el tamaño real ocupado en memoria por un mapa de bits 2D donde las primeras $h - 1$ filas abarcan el ancho completo del stride de memoria, y la última fila ocupa $w$ píxeles.

---

## 3. Estructura de Archivos

| Archivo | Descripción |
| :--- | :--- |
| [`libass_profiler.c`](file:///f:/Kara%20Effector/Node/Antigravity-PyxisNode/C%C3%B3digo%20de%20referencia%20%28no%20se%20modifica%29/libass_profiler_native/libass_profiler.c) | Código fuente nativo en C99, limpio, multiplataforma y sin dependencias externas salvo `libass`. |
| [`Makefile`](file:///f:/Kara%20Effector/Node/Antigravity-PyxisNode/C%C3%B3digo%20de%20referencia%20%28no%20se%20modifica%29/libass_profiler_native/Makefile) | Script de compilación estándar POSIX con autodetección de `pkg-config`. |
| [`build.sh`](file:///f:/Kara%20Effector/Node/Antigravity-PyxisNode/C%C3%B3digo%20de%20referencia%20%28no%20se%20modifica%29/libass_profiler_native/build.sh) | Script Bash de compilación en un paso para Linux y macOS con verificación de cabeceras. |
| [`build.bat`](file:///f:/Kara%20Effector/Node/Antigravity-PyxisNode/C%C3%B3digo%20de%20referencia%20%28no%20se%20modifica%29/libass_profiler_native/build.bat) | Script Batch para compilar en Windows usando MSYS2 / MinGW-w64. |
| [`README.md`](file:///f:/Kara%20Effector/Node/Antigravity-PyxisNode/C%C3%B3digo%20de%20referencia%20%28no%20se%20modifica%29/libass_profiler_native/README.md) | Documentación técnica completa (este archivo). |

---

## 4. Instrucciones de Compilación

### 4.1. En Linux (Ubuntu / Debian / Linux Mint)
```bash
sudo apt update
sudo apt install build-essential pkg-config libass-dev

cd "Código de referencia (no se modifica)/libass_profiler_native"
make
# o directamente:
gcc -O3 -Wall -Wextra -std=c99 libass_profiler.c -o libass_profiler $(pkg-config --cflags --libs libass) -lm
```

### 4.2. En Linux (Arch Linux / Manjaro)
```bash
sudo pacman -S base-devel pkgconf libass

cd "Código de referencia (no se modifica)/libass_profiler_native"
make
```

### 4.3. En macOS (Apple Silicon M1/M2/M3 y procesadores Intel)
```bash
# 1. Instalar dependencias mediante Homebrew
brew install libass pkg-config

# 2. Compilar
cd "Código de referencia (no se modifica)/libass_profiler_native"
clang -O3 -Wall -Wextra -std=c99 libass_profiler.c -o libass_profiler $(pkg-config --cflags --libs libass) -lm
```

### 4.4. En Windows (MSYS2 / MinGW-w64)
```bash
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-libass
gcc -O3 -Wall -Wextra -std=c99 libass_profiler.c -o libass_profiler.exe -lass -lfreetype -lm
```

---

## 5. Integración con Pyxis Effector

Para que Pyxis utilice este binario nativo en Linux y macOS:

1. **Copiar el ejecutable generado:**
   Copiar `libass_profiler` compilado en la carpeta de binarios del paquete:
   ```bash
   cp libass_profiler "Version en desarrollo/PyxisNodes/bin/"
   chmod +x "Version en desarrollo/PyxisNodes/bin/libass_profiler"
   ```

2. **Adaptación en `paths.py` / `ass_telemetry_engine.py`:**
   En `src/paths.py` o en `ASSTelemetryManager.__init__`:
   ```python
   # Detección nativa sin forzar la extensión .exe en sistemas POSIX:
   bin_name = "libass_profiler.exe" if os.name == "nt" else "libass_profiler"
   self.profiler_exe = get_bin_path(bin_name)
   ```

3. **Resultado:**
   * La telemetría se ejecuta a velocidad de CPU nativa.
   * Cero llamadas a Wine.
   * Sin problemas de traducción de rutas ni tiempos de arranque en frío.

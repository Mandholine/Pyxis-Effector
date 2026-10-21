# Guía de Línea de Comandos (CLI)

`pyxis-core` incluye la utilidad de terminal `pyxis-core`, instalada automáticamente en tu entorno al ejecutar `pip install pyxis-core`.

---

## 🚀 Uso General

```bash
pyxis-core [-h] [-v] {process,validate,telemetry,info} ...
```

Opciones globales:
- `-h, --help`: Muestra la ayuda de la terminal y las opciones disponibles.
- `-v, --version`: Imprime la versión actual de la librería instalada.

---

## 🛠️ Comandos Disponibles

### 1. `pyxis-core process`

Aplica un grafo de efectos sobre un archivo de subtítulos ASS y genera un nuevo archivo resultante.

```bash
pyxis-core process -g <grafo.json> -a <entrada.ass> [-o <salida.ass>] [--audio <pista.wav>]
```

**Parámetros:**
- `-g, --graph`: *(Requerido)* Ruta al archivo JSON con la definición del grafo de nodos.
- `-a, --ass`: *(Requerido)* Ruta al archivo `.ass` original.
- `-o, --output`: *(Opcional)* Ruta donde se guardará el nuevo archivo `.ass` con los efectos aplicados.
- `--audio`: *(Opcional)* Archivo de audio para sincronización con ondas sonoras o detección de beats.

**Ejemplo:**
```bash
pyxis-core process \
  --graph templates/karaoke_glow.json \
  --ass opening.ass \
  --output opening_con_efectos.ass
```

---

### 2. `pyxis-core validate`

Comprueba la validez sintáctica y estructural de un grafo JSON antes de procesarlo en lotes o entornos de producción.

```bash
pyxis-core validate -g <grafo.json>
```

**Ejemplo de salida válida:**
```text
Graph 'templates/karaoke_glow.json' is VALID (Nodes: 8, Warnings: 0)
```

**Ejemplo con errores:**
```text
Graph 'corrupted_graph.json' is INVALID with 2 errors:
  - Node 'pos_1' references unknown port 'invalid_in'
  - Cycle detected between 'loop_1' and 'time_delay'
```

---

### 3. `pyxis-core telemetry`

Analiza la eficiencia de renderizado de un archivo ASS utilizando el motor nativo `libass_profiler` e informa sobre fotogramas con caídas de framerate (*dropped frames*).

```bash
pyxis-core telemetry -a <subtitulos.ass> [--fps <float>] [-o <reporte.json>]
```

**Parámetros:**
- `-a, --ass`: *(Requerido)* Archivo `.ass` a perfilar.
- `--fps`: *(Opcional, default: 23.976)* Tasa de fotogramas objetivo para evaluar si hay caídas de fotogramas.
- `-o, --output`: *(Opcional)* Guarda el informe detallado fotograma a fotograma en formato JSON.

**Ejemplo:**
```bash
pyxis-core telemetry -a opening_con_efectos.ass --fps 24.0 -o reporte.json
```

**Salida en consola:**
```text
Analyzing ASS rendering telemetry at 24.0 FPS: opening_con_efectos.ass
--------------------------------------------------
Total Frames:          2160
Dropped Frames:        0
Max Render Time:       12.43 ms
Avg Render Time:       3.12 ms
Total Duration:        90.00 s
--------------------------------------------------
Telemetry report written to: reporte.json
```

---

### 4. `pyxis-core info`

Muestra información del entorno de ejecución, versión, rutas de recursos y el estado de resolución de herramientas nativas (`img2ass`, `potrace`, `libass_profiler`, `ffmpeg`).

```bash
pyxis-core info
```

# Guía de Inicio Rápido (Getting Started)

En esta guía aprenderás a instalar `pyxis-core` en tu entorno Python y a ejecutar tu primer procesamiento de subtítulos ASS mediante la fachada `PyxisCore` y mediante la terminal.

---

## 1. Requisitos Previos

- **Python:** 3.9 o superior (3.9, 3.10, 3.11, 3.12).
- **Sistemas Operativos:** macOS (Apple Silicon y x86_64), Linux (x86_64, aarch64), Windows (x64).
- **Herramientas opcionales:** `ffmpeg` para extracción y procesamiento de audio avanzado.

---

## 2. Instalación

### Desde PyPI (Recomendado cuando esté publicado)

```bash
pip install pyxis-core
```

### Instalación en Modo Desarrollo / Local

Si clonas el repositorio o estás desarrollando extensiones para `pyxis-core`:

```bash
cd pyxis_core
pip install -e .
```

### Con Soporte para Aceleración por GPU (CuPy)

Para acelerar operaciones matriciales y de partículas masivas en GPUs NVIDIA compatibles con CUDA:

```bash
pip install "pyxis-core[gpu]"
```

### Con Herramientas de Desarrollo y Testing

Para ejecutar la suite de pruebas unitarias y herramientas de empaquetado:

```bash
pip install "pyxis-core[dev]"
```

---

## 3. Verificación de la Instalación

Comprueba que la librería y el comando CLI estén disponibles en tu entorno:

```bash
python -c "import pyxis_core; print(pyxis_core.__version__)"
# Salida esperada: 0.1.0

pyxis-core --version
# Salida esperada: pyxis-core 0.1.0

pyxis-core info
```

---

## 4. Tu Primer Script con Python

A continuación se muestra un ejemplo básico para cargar un archivo de subtítulos `.ass`, aplicar una plantilla de grafo de nodos y guardar el resultado modificado:

```python
from pyxis_core import PyxisCore

# 1. Instanciar la fachada central
core = PyxisCore()

# 2. Definir un grafo simple de nodos (o cargar desde un archivo JSON)
graph = {
    "nodes": [
        {
            "id": "node_split",
            "type": "TextSplitter",
            "properties": {"mode": "words"}
        },
        {
            "id": "node_pos",
            "type": "PositionEffect",
            "properties": {"x": 100, "y": 200}
        }
    ],
    "connections": [
        {
            "from": "node_split",
            "output": "output",
            "to": "node_pos",
            "input": "input"
        }
    ]
}

# 3. Validar el grafo antes de procesar
validation = core.validate(graph)
if not validation.valid:
    print("Errores en el grafo:", validation.errors)
    exit(1)

print(f"Grafo válido. Contiene {validation.node_count if hasattr(validation, 'node_count') else len(graph['nodes'])} nodos.")

# 4. Procesar el archivo ASS con callback de progreso
def on_progress(event):
    print(f"[{event.percent}%] {event.phase}")

response = core.process(
    graph=graph,
    ass_path="input.ass",
    output_path="output_effects.ass",
    progress_callback=on_progress
)

if response.success:
    print(f"Procesamiento finalizado con éxito en {response.duration_seconds:.2f} segundos!")
    print(f"Líneas generadas: {response.lines_count}")
    print(f"Archivo de salida: {response.output_path}")
else:
    print(f"Error durante el procesamiento: {response.error}")
```

---

## 5. Procesamiento Directo en Memoria (Ideal para APIs)

Si estás construyendo un microservicio con **FastAPI** o **Flask**, no necesitas escribir archivos temporales a disco; puedes pasar y recibir texto directamente en memoria:

```python
from pyxis_core import PyxisCore

core = PyxisCore()

ass_content_raw = """[Script Info]
Title: Script en Memoria
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,50,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:05.00,Default,,0,0,0,,¡Hola Mundo desde Pyxis!
"""

response = core.process(
    graph="mi_efecto.json",
    ass_content=ass_content_raw,
    output_path=None  # No genera archivo físico en disco
)

if response.success:
    # Contenido resultante en memoria como texto ASS completo
    print("Contenido ASS generado:")
    print(response.output_content)
```

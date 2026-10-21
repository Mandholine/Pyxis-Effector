# pyxis-core

**pyxis-core** es el motor y biblioteca modular de efectos por nodos para subtítulos ASS (*Advanced SubStation Alpha*).

Forma parte del ecosistema **Pyxis Effector** y ha sido desacoplado para funcionar independientemente de interfaces de usuario (como `pywebview` o Qt), permitiendo su uso directo en:
- Servidores y microservicios backend (**FastAPI**, Flask, gRPC).
- Scripts CLI y herramientas de renderizado en lote (*batch processing* / headless).
- Extensiones y plugins (Aegisub, etc.).

---

## Características

- **Motor de Grafos (`GraphEngine`):** Evaluación dirigida de nodos (animación, tiempo, matemáticas, transformaciones de texto, máscaras de clips, bucles y variables).
- **Pipeline Orquestador (`PyxisPipeline`):** API simplificada para procesar subtítulos y grafos de nodos con soporte de callbacks de progreso (`progress_callback`) y cancelación (`cancel_checker`).
- **Parseador ASS (`ASSParser` & `KaraokeProcessor`):** Análisis completo de cabeceras, estilos, tiempos y etiquetas de karaoke `\k`, `\kf`, `\ko`.
- **Motores Multimedia Especializados:**
  - `FontEngine` / `FontVectorEngine`: Vectorización de glifos y contornos con FreeType.
  - `AudioEngine` / `AudioPreprocessor`: Extracción de ondas y telemetría de audio.
  - `ClipperEngine`: Operaciones booleanas de trazados y polígonos.
  - `ASSTelemetryEngine`: Análisis de métricas en tiempo real.

---

## Instalación

### Modo desarrollo / local
```bash
pip install -e ./pyxis_core
```

### Requisitos
- Python >= 3.9
- `numpy`, `Pillow`, `pyclipper`, `freetype-py`, `psutil`, `lupa`

---

## Uso Rápido

### Con `PyxisPipeline` (Recomendado)

```python
from pyxis_core import PyxisPipeline

pipeline = PyxisPipeline()

# Ejecutar un grafo sobre un archivo ASS
result = pipeline.process(
    ass_input="subtitulos.ass",
    graph_data="efecto.json",
    progress_callback=lambda p: print(f"Progreso: {p['percent']}% - {p['phase']}"),
    output_path="resultado.ass"
)

if result.success:
    print(f"Líneas generadas: {result.lines_count} en {result.duration_seconds:.2f}s")
else:
    print(f"Error: {result.error}")
```

### Uso Directo de Componentes

```python
from pyxis_core import ASSParser, GraphEngine

# 1. Parsear archivo ASS
styles, dialogues, res_x, res_y, frame_duration = ASSParser.read_file("dialogo.ass")

# 2. Inicializar motor con grafo
engine = GraphEngine(graph_dict, res_x, res_y, frame_duration)

# 3. Procesar líneas
output_lines = engine.process(dialogues, styles)
```

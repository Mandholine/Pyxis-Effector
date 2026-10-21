# Plan de Arquitectura y APIs: Reemplazo de Webview por Flutter Desktop

> **Documento de Diseño Técnico (RFC / Plan de Migración)**  
> **Proyecto:** Pyxis Effector — Reemplazo del Frontend `pywebview` por aplicación nativa de escritorio en **Flutter Desktop** (macOS, Windows, Linux) consumiendo la librería **`pyxis-core`**.

---

## 📑 Tabla de Contenidos

1. [Motivación y Objetivos](#1-motivación-y-objetivos)
2. [Arquitectura del Sistema (IPC / Cliente-Servidor Local)](#2-arquitectura-del-sistema-ipc--cliente-servidor-local)
3. [Catálogo Completo de APIs Requeridas](#3-catálogo-completo-de-apis-requeridas)
   - [A. Módulo de Sesión y Aegisub (`/session`)](#a-módulo-de-sesión-y-aegisub-session)
   - [B. Módulo de Procesamiento de Grafos (`/graph`)](#b-módulo-de-procesamiento-de-grafos-graph)
   - [C. Módulo de Vista Previa y Fotogramas (`/preview`)](#c-módulo-de-vista-previa-y-fotogramas-preview)
   - [D. Módulo de Plantillas de Efectos (`/templates`)](#d-módulo-de-plantillas-de-efectos-templates)
   - [E. Módulo de Vectorización y Geometría (`/geometry`)](#e-módulo-de-vectorización-y-geometría-geometry)
   - [F. Módulo de Fuentes y Métricas Tipográficas (`/fonts`)](#f-módulo-de-fuentes-y-métricas-tipográficas-fonts)
   - [G. Módulo de Audio y Espectrograma (`/audio`)](#g-módulo-de-audio-y-espectrograma-audio)
   - [H. Módulo de Telemetría y Rendimiento (`/telemetry`)](#h-módulo-de-telemetría-y-rendimiento-telemetry)
4. [Implementación de Referencia del Daemon FastAPI](#4-implementación-de-referencia-del-daemon-fastapi)
5. [Integración en Flutter Desktop (Dart Service & WebSocket)](#5-integración-en-flutter-desktop-dart-service--websocket)
6. [Estrategia de Lanzamiento y Ciclo de Vida del Proceso](#6-estrategia-de-lanzamiento-y-ciclo-de-vida-del-proceso)
7. [Fases de Migración Recomendadas](#7-fases-de-migración-recomendadas)

---

## 1. Motivación y Objetivos

El sistema histórico de **PyxisNodes** utilizaba `pywebview` para embeber un navegador web (Chromium/WebKit) que renderizaba la interfaz HTML/JS. Sin embargo:
- **Consumo elevado de memoria:** Embeber un motor de navegador completo consume entre 300 MB y 800 MB de RAM.
- **Latencia de renderizado en grafos masivos:** El DOM y Canvas web sufren caídas de framerate con cientos de partículas y curvas Bézier simultáneas.
- **Falta de integración con el SO:** Limitaciones en atajos de teclado, barras de menú nativas y sincronización de ventanas con Aegisub.

### Objetivos con Flutter Desktop:
- **Renderizado Nativo por GPU:** 60/120 FPS fluidos utilizando el motor gráfico Skia/Impeller (Metal en macOS, DirectX en Windows, Vulkan en Linux).
- **Desacoplamiento Absoluto:** El frontend de Flutter se comunica mediante contratos de API REST/WebSocket estandarizados con el backend `pyxis-core`.
- **Portabilidad:** Una única base de código Flutter para macOS, Windows y Linux.

---

## 2. Arquitectura del Sistema (IPC / Cliente-Servidor Local)

```text
+--------------------------------------------------------------------------+
|                  FLUTTER DESKTOP APP (Frontend UI)                      |
|  - Graph Canvas (Lienzo interactivo de nodos y conexiones Bézier)        |
|  - Inspector de Propiedades de Nodos                                     |
|  - Timeline de Audio y Subtítulos con zoom y magnetismo                  |
|  - Reproductor de Vista Previa de Video / ASS con Metal/DirectX/OpenGL   |
+--------------------------------------------------------------------------+
                                    ▲
                                    │ HTTP REST (Acciones / Datos síncronos)
                                    │ WebSocket (Streaming de Progreso / Logs)
                                    ▼
+--------------------------------------------------------------------------+
|                 PYXIS DAEMON / FASTAPI (http://127.0.0.1:28723)          |
|  - Endpoints REST para validación, plantillas, tipografías y geometría   |
|  - WebSockets para eventos de progreso en tiempo real y cancelación      |
|  - Servidor de medios con soporte HTTP 206 Partial Content (Streaming)  |
+--------------------------------------------------------------------------+
                                    ▲
                                    │ Invocación interna directa
                                    ▼
+--------------------------------------------------------------------------+
|                  PYXIS-CORE (Clean Architecture Library)                 |
|  - PyxisCore Facade (Orquestador)                                        |
|  - Application Use Cases (ProcessGraphUseCase, ValidateGraphUseCase)     |
|  - Domain Entities (SubtitleScript, DialogueLine, NodeGraph, Timecode)   |
|  - Infrastructure Engines (ClipperEngine, Potrace/img2ass, FreeType)     |
+--------------------------------------------------------------------------+
                                    ▲
                                    │ Lectura / Escritura de archivos
                                    ▼
                 [ Aegisub / Archivo .ass / Media ]
```

---

## 3. Catálogo Completo de APIs Requeridas

---

### A. Módulo de Sesión y Aegisub (`/session`)

Permite a Flutter conocer el contexto de la sesión lanzada desde Aegisub y sincronizar el guardado de subtítulos.

#### 1. `GET /api/v1/session/info`
Obtiene los metadatos de la sesión activa iniciada desde Aegisub.
- **Request:** Ninguno.
- **Response (`200 OK`):**
```json
{
  "aegisub_pid": 48210,
  "aegisub_version": "3.3.3",
  "ass_path": "/Users/usuario/Desktop/karaoke.ass",
  "styles": [
    {
      "name": "Default",
      "fontname": "Arial",
      "fontsize": 48.0,
      "primary_color": "&H00FFFFFF",
      "outline_color": "&H00000000"
    }
  ],
  "lines_count": 145,
  "selected_lines": [0, 1, 2, 3],
  "resolution": { "play_res_x": 1920, "play_res_y": 1080 },
  "fps": 23.976
}
```

#### 2. `POST /api/v1/session/reopen`
Notificación cuando Aegisub actualiza el archivo en disco mientras Pyxis está abierto.
- **Request (`application/json`):**
```json
{
  "ass_path": "/Users/usuario/Desktop/karaoke.ass",
  "temp_ass": "/tmp/pyxis_temp.ass"
}
```
- **Response:** `{"status": "reopened", "lines_count": 145}`

#### 3. `POST /api/v1/session/apply`
Aplica el resultado procesado en el archivo `.ass` oficial y notifica a Aegisub para que recargue el proyecto.
- **Request:**
```json
{
  "output_path": "/Users/usuario/Desktop/karaoke.ass"
}
```
- **Response:** `{"success": true, "lines_written": 280}`

#### 4. `POST /api/v1/session/shutdown`
Finaliza limpiamente el daemon cuando Flutter o Aegisub se cierran.

---

### B. Módulo de Procesamiento de Grafos (`/graph`)

El motor central de cálculo de efectos.

#### 1. `POST /api/v1/graph/validate`
Valida la integridad del grafo de nodos antes de ejecutarlo.
- **Request:**
```json
{
  "graph": {
    "nodes": [
      { "id": "node_1", "type": "TextSplitter", "properties": { "mode": "words" } },
      { "id": "node_2", "type": "PositionEffect", "properties": { "x": 100, "y": 200 } }
    ],
    "connections": [
      { "from": "node_1", "output": "output", "to": "node_2", "input": "input" }
    ]
  }
}
```
- **Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": ["Node 'node_2' using default ease-in curve"]
}
```

#### 2. `POST /api/v1/graph/process`
Ejecuta el procesamiento del efecto completo.
- **Request:**
```json
{
  "graph": { ... },
  "ass_path": "/path/input.ass",
  "output_path": "/path/output.ass",
  "default_audio_source": "/path/audio.wav"
}
```
- **Response:**
```json
{
  "success": true,
  "lines_count": 520,
  "duration_seconds": 0.45,
  "output_path": "/path/output.ass",
  "error": null
}
```

#### 3. `POST /api/v1/graph/abort`
Cancela de forma inmediata la tarea en ejecución.
- **Response:** `{"status": "abort_requested"}`

#### 4. `WS /api/v1/graph/ws/progress` *(WebSocket)*
Canal bidireccional en tiempo real para progreso y cancelación interactiva.
- **Flutter envía:**
```json
{ "action": "start", "graph": { ... }, "ass_path": "input.ass" }
```
- **Daemon emite continuamente:**
```json
{ "percent": 45, "phase": "Calculating particle trajectories...", "current_line": 65 }
```
- **Evento final:**
```json
{ "percent": 100, "phase": "Done", "success": true, "duration_seconds": 0.42 }
```

---

### C. Módulo de Vista Previa y Fotogramas (`/preview`)

Permite al reproductor de Flutter mostrar el resultado visual exacto.

#### 1. `POST /api/v1/preview/frame`
Renderiza un único fotograma con `libass` para el visor interactivo.
- **Request:**
```json
{
  "graph": { ... },
  "time_ms": 14500,
  "line_index": 5
}
```
- **Response (`image/png` o `application/json`):**
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "render_time_ms": 4.2,
  "width": 1920,
  "height": 1080
}
```

#### 2. `GET /api/v1/preview/media-stream`
Servidor HTTP de video con soporte de cabeceras de rango (`206 Partial Content`) para que el reproductor nativo de Flutter (`video_player` o `media_kit`) haga scrub fluido de videos MP4/MKV de fondo.
- **Query:** `?path=/ruta/al/video.mp4`

---

### D. Módulo de Plantillas de Efectos (`/templates`)

#### 1. `GET /api/v1/templates`
Lista el catálogo de efectos empaquetados.
- **Response:**
```json
[
  {
    "id": "karaoke_glow_fade",
    "name": "Karaoke Glow & Fade",
    "category": "Karaoke",
    "author": "Pyxis",
    "node_count": 6,
    "description": "Efecto de resplandor dinámico por sílaba con desvanecimiento."
  }
]
```

#### 2. `GET /api/v1/templates/{id}`
Devuelve el grafo JSON completo para inyectarlo en el editor de Flutter.

#### 3. `POST /api/v1/templates`
Guarda el grafo actual del usuario como una nueva plantilla reutilizable.

#### 4. `DELETE /api/v1/templates/{id}`
Elimina una plantilla personalizada de la biblioteca del usuario.

---

### E. Módulo de Vectorización y Geometría (`/geometry`)

#### 1. `POST /api/v1/geometry/trace-image`
Convierte mapas de bits en formas vectoriales ASSDraw (`{\p1}...{\p0}`) mediante `ImageTracerAdapter` / `img2ass` / Potrace.
- **Request:**
```json
{
  "image_path": "/Users/usuario/icon.png",
  "mode": "Potrace",
  "anchor": "Center",
  "turdsize": 2,
  "alphamax": 1.0
}
```
- **Response:**
```json
{
  "shape": "m 0 0 b 12 4 18 10 24 16 l 30 20...",
  "width": 128,
  "height": 128,
  "points": 340
}
```

#### 2. `POST /api/v1/geometry/clipper-boolean`
Ejecuta operaciones booleanas (unión, diferencia, intersección) entre siluetas ASS con el motor `clipper_engine`.

---

### F. Módulo de Fuentes y Métricas Tipográficas (`/fonts`)

#### 1. `GET /api/v1/fonts`
Retorna todas las familias tipográficas del sistema operativo para que el selector de fuentes de Flutter muestre las fuentes disponibles.
- **Response:**
```json
[
  { "family": "Arial", "styles": ["Regular", "Bold", "Italic"] },
  { "family": "Roboto", "styles": ["Light", "Regular", "Bold", "Black"] }
]
```

#### 2. `POST /api/v1/fonts/metrics`
Calcula las métricas de un texto con FreeType para colocar cajas de fondo y alinear formas.
- **Request:** `{"text": "Hola", "font_name": "Arial", "font_size": 48.0}`
- **Response:** `{"width": 98.4, "height": 55.2, "ascent": 42.0, "descent": 13.2}`

---

### G. Módulo de Audio y Espectrograma (`/audio`)

#### 1. `GET /api/v1/audio/waveform`
Genera los picos de amplitud para dibujar la onda de audio en el timeline de Flutter.
- **Query:** `?path=cancion.wav&resolution=100`
- **Response:**
```json
{
  "sample_rate": 44100,
  "duration_ms": 95000,
  "peaks": [0.05, 0.12, 0.45, 0.82, 0.65, 0.30, 0.10]
}
```

#### 2. `GET /api/v1/audio/beats`
Devuelve la lista de marcas de tiempo en ms donde se detectaron beats para habilitar magnetismo al compás de la música.

---

### H. Módulo de Telemetría y Rendimiento (`/telemetry`)

#### 1. `POST /api/v1/telemetry/analyze`
Ejecuta `libass_profiler` sobre el archivo ASS procesado.
- **Request:** `{"ass_path": "karaoke_efectos.ass", "fps": 23.976}`
- **Response:**
```json
{
  "total_frames": 2160,
  "dropped_frames": 0,
  "max_render_time_ms": 14.2,
  "avg_render_time_ms": 3.8,
  "duration_seconds": 90.08
}
```

---

## 4. Implementación de Referencia del Daemon FastAPI

Estructura del servidor local en Python:

```python
# pyxis_api_server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import uvicorn
import asyncio
import os

from pyxis_core import PyxisCore
from pyxis_core.infrastructure.adapters import ImageTracerAdapter, TelemetryAdapter, FontAdapter

app = FastAPI(title="Pyxis Engine API", version="0.1.0")

# Permitir comunicación local desde Flutter Desktop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

core = PyxisCore()

# --- Modelos Pydantic ---
class ValidateGraphRequest(BaseModel):
    graph: Dict[str, Any]

class ProcessGraphRequest(BaseModel):
    graph: Dict[str, Any]
    ass_path: Optional[str] = None
    output_path: Optional[str] = None
    default_audio_source: Optional[str] = None

class TraceImageRequest(BaseModel):
    image_path: str
    mode: str = "Potrace"
    anchor: str = "Center"
    turdsize: int = 2

# --- Endpoints ---
@app.get("/api/v1/session/info")
def get_session_info():
    return {
        "status": "online",
        "version": "0.1.0",
        "pid": os.getpid()
    }

@app.post("/api/v1/graph/validate")
def validate_graph(req: ValidateGraphRequest):
    res = core.validate(req.graph)
    return {"valid": res.valid, "errors": res.errors, "warnings": res.warnings}

@app.post("/api/v1/graph/process")
def process_graph(req: ProcessGraphRequest):
    res = core.process(
        graph=req.graph,
        ass_path=req.ass_path,
        output_path=req.output_path,
        default_audio_source=req.default_audio_source,
    )
    if not res.success:
        raise HTTPException(status_code=400, detail=res.error)
    return {
        "success": True,
        "lines_count": res.lines_count,
        "duration_seconds": res.duration_seconds,
        "output_path": res.output_path
    }

@app.post("/api/v1/geometry/trace-image")
def trace_image(req: TraceImageRequest):
    if not os.path.isfile(req.image_path):
        raise HTTPException(status_code=404, detail="Image file not found")
    result = ImageTracerAdapter.trace(
        image_path=req.image_path,
        mode=req.mode,
        anchor=req.anchor,
        turdsize=req.turdsize
    )
    return result

@app.post("/api/v1/telemetry/analyze")
def analyze_telemetry(ass_path: str, fps: float = 23.976):
    if not os.path.isfile(ass_path):
        raise HTTPException(status_code=404, detail="ASS file not found")
    return TelemetryAdapter.analyze_file(ass_path, fps=fps)

# --- WebSocket de Streaming de Progreso ---
@app.websocket("/api/v1/graph/ws/progress")
async def ws_progress(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            graph = data.get("graph")
            ass_path = data.get("ass_path")
            output_path = data.get("output_path")

            def on_progress(p):
                asyncio.run(websocket.send_json({"percent": p.percent, "phase": p.phase}))

            resp = core.process(graph=graph, ass_path=ass_path, output_path=output_path, progress_callback=on_progress)
            await websocket.send_json({"percent": 100, "phase": "Complete", "success": resp.success, "lines": resp.lines_count})
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=28723)
```

---

## 5. Integración en Flutter Desktop (Dart Service & WebSocket)

En tu aplicación Flutter (`pubspec.yaml` con `dio` y `web_socket_channel`):

```dart
// lib/services/pyxis_api_service.dart
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class PyxisApiService {
  static const String baseUrl = 'http://127.0.0.1:28723/api/v1';
  static const String wsUrl = 'ws://127.0.0.1:28723/api/v1';

  final Dio _dio = Dio(BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 30),
  ));

  // 1. Obtener metadatos de sesión
  Future<Map<String, dynamic>> getSessionInfo() async {
    final response = await _dio.get('/session/info');
    return response.data as Map<String, dynamic>;
  }

  // 2. Validar grafo en el canvas
  Future<ValidationResult> validateGraph(Map<String, dynamic> graph) async {
    final response = await _dio.post('/graph/validate', data: {'graph': graph});
    final data = response.data;
    return ValidationResult(
      valid: data['valid'] ?? false,
      errors: List<String>.from(data['errors'] ?? []),
      warnings: List<String>.from(data['warnings'] ?? []),
    );
  }

  // 3. Procesar grafo con WebSocket interactivo
  Stream<ProgressEvent> processGraphStream({
    required Map<String, dynamic> graph,
    required String assPath,
    String? outputPath,
  }) {
    final channel = WebSocketChannel.connect(
      Uri.parse('$wsUrl/graph/ws/progress'),
    );

    channel.sink.add(jsonEncode({
      'graph': graph,
      'ass_path': assPath,
      'output_path': outputPath,
    }));

    return channel.stream.map((event) {
      final data = jsonDecode(event as String);
      return ProgressEvent(
        percent: data['percent'] ?? 0,
        phase: data['phase'] ?? '',
        isComplete: data['percent'] == 100,
      );
    });
  }

  // 4. Vectorizar imagen a dibujo ASS
  Future<String> traceImage(String imagePath) async {
    final response = await _dio.post('/geometry/trace-image', data: {
      'image_path': imagePath,
      'mode': 'Potrace',
      'anchor': 'Center',
    });
    return response.data['shape'] as String;
  }
}

class ValidationResult {
  final bool valid;
  final List<String> errors;
  final List<String> warnings;
  ValidationResult({required this.valid, required this.errors, required this.warnings});
}

class ProgressEvent {
  final int percent;
  final String phase;
  final bool isComplete;
  ProgressEvent({required this.percent, required this.phase, required this.isComplete});
}
```

---

## 6. Estrategia de Lanzamiento y Ciclo de Vida del Proceso

¿Cómo se comunican Aegisub, el daemon de Python y la app de Flutter?

```
[ Aegisub ] 
     │ (Lua: io.popen / Process)
     ▼
[ Pyxis Python Daemon ] ── (Inicia en segundo plano en http://127.0.0.1:28723)
     │
     ▼ (Lanza la ventana de Flutter)
[ Pyxis Flutter Desktop App ]
```

1. **Cuando el usuario abre Pyxis desde Aegisub:**  
   El script Lua de Aegisub ejecuta `python -m pyxis_server --aegisub-pid <PID>`.
2. **El Daemon arranca FastAPI:**  
   El servidor se vincula al puerto `28723` y verifica si la ventana de Flutter está abierta. Si no lo está, lanza el binario de Flutter (`open PyxisNodes.app` en macOS o `PyxisNodes.exe` en Windows).
3. **Flutter se conecta inmediatamente al Daemon:**  
   Flutter realiza un `GET /api/v1/session/info` y carga el estado de Aegisub en el lienzo.
4. **Cierre sin procesos huérfanos:**  
   El Daemon monitorea el PID de Aegisub. Si Aegisub se cierra, el daemon y Flutter se cierran automáticamente.

---

## 7. Fases de Migración Recomendadas

1. **Fase 1: Capa de Servidor Backend (FastAPI)**
   - Crear el módulo `pyxis_server` que exponga los endpoints descritos consumiendo `pyxis_core`.
   - Probar los endpoints con Postman o Swagger UI (`http://127.0.0.1:28723/docs`).
2. **Fase 2: Estructura del Proyecto Flutter Desktop**
   - Inicializar el proyecto Flutter con soporte para Desktop: `flutter create --platforms=macos,windows,linux pyxis_flutter`.
   - Implementar el lienzo de nodos (usando `flutter_flow_chart` o un `CustomPainter` propio).
3. **Fase 3: Conexión y Timeline**
   - Integrar `PyxisApiService` con Riverpod o Bloc para el estado reactivo.
   - Conectar la barra de progreso vía WebSocket.
4. **Fase 4: Empaquetado y Distribución**
   - Congelar el servidor Python con PyInstaller o distribuirlo en el paquete de la aplicación Flutter.
   - Retirar completamente las dependencias de `pywebview` del repositorio principal.

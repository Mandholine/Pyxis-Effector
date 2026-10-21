# pyxis-core (Clean Architecture)

**pyxis-core** es el motor modular de efectos de subtítulos ASS organizado bajo los principios de **Clean Architecture** (Arquitectura Limpia).

Diseñado para ser consumido limpiamente por:
- **FastAPI / Microservicios:** Controladores que reciben DTOs y llaman a Casos de Uso.
- **Flutter / Web Apps:** Contrato desacoplado con DTOs y Mappers que se corresponden 1:1 con esquemas de API.
- **Scripts CLI / Headless:** Ejecución directa y procesamiento en lote.

---

## 🏛️ Estructura de Capas

```text
pyxis_core/
├── pyproject.toml
├── requirements.txt
└── pyxis_core/
    ├── __init__.py                     # Facade PyxisCore y exportaciones
    │
    ├── domain/                         # Capa de Dominio (Reglas puras)
    │   ├── entities/                   # SubtitleScript, DialogueLine, SubtitleStyle, NodeGraph, EffectTemplate
    │   ├── value_objects/              # Timecode (conversión ms/ASS), Resolution (aspect ratio, fps)
    │   └── repositories/               # Interfaces: ISubtitleRepository, ITemplateRepository
    │
    ├── application/                    # Capa de Aplicación
    │   ├── dtos/                       # Serializers: ProcessGraphRequestDTO, ProcessGraphResponseDTO, ProgressEventDTO
    │   ├── mappers/                    # SubtitleMapper, GraphMapper
    │   └── use_cases/                  # ProcessGraphUseCase, ValidateGraphUseCase, ManageTemplatesUseCase
    │
    └── infrastructure/                 # Capa de Infraestructura
        ├── repositories/               # FileSubtitleRepository (ASSParser), FileTemplateRepository (JSON)
        ├── adapters/                   # AudioAdapter, FontAdapter, TelemetryAdapter
        └── engine/                     # Motores pesados (GraphEngine, Clipper, Nodes)
```

---

## 🚀 Uso Rápido

### 1. Vía Fachada `PyxisCore` (Recomendado)

```python
from pyxis_core import PyxisCore

core = PyxisCore()

# Procesar subtítulos con un grafo de nodos
response = core.process(
    graph="efecto.json",                  # Ruta o dict
    ass_path="dialogo.ass",               # Archivo ASS
    output_path="resultado.ass",          # Salida opcional
    progress_callback=lambda p: print(f"[{p.percent}%] {p.phase}")
)

if response.success:
    print(f"Generadas {response.lines_count} líneas en {response.duration_seconds}s")
else:
    print(f"Error: {response.error}")
```

### 2. Uso con Inyección de Dependencias (Casos de Uso directos)

Ideal para FastAPI con contenedores de dependencias:

```python
from pyxis_core.application.use_cases import ProcessGraphUseCase
from pyxis_core.application.dtos import ProcessGraphRequestDTO
from pyxis_core.infrastructure.repositories import FileSubtitleRepository

# Inyección del repositorio
repo = FileSubtitleRepository()
use_case = ProcessGraphUseCase(subtitle_repo=repo)

# Ejecución con DTO tipado
request = ProcessGraphRequestDTO(
    graph={"nodes": [...], "connections": [...]},
    ass_content="[Script Info]...",
)
response = use_case.execute(request)
```

### 3. Validación de Grafos

```python
from pyxis_core import PyxisCore

core = PyxisCore()
result = core.validate(graph_dict)
if not result.valid:
    print("Errores de validación:", result.errors)
```

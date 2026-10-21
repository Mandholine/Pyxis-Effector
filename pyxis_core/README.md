# pyxis-core (Clean Architecture)

[![PyPI Version](https://img.shields.io/badge/pypi-0.1.0-blue.svg)](https://pypi.org/project/pyxis-core/)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://pypi.org/project/pyxis-core/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()

**pyxis-core** es el motor modular de efectos de subtítulos ASS organizado bajo los principios de **Clean Architecture** (Arquitectura Limpia).

Diseñado para ser consumido limpiamente por:
- **FastAPI / Microservicios:** Controladores que reciben DTOs y llaman a Casos de Uso.
- **Flutter / Web Apps:** Contrato desacoplado con DTOs y Mappers que se corresponden 1:1 con esquemas de API.
- **Herramienta de Línea de Comandos (CLI):** Comando `pyxis-core` disponible en el sistema.
- **Scripts Headless:** Ejecución directa y procesamiento por lotes.

---

## 📚 Documentación Completa

Toda la documentación detallada se encuentra en la carpeta [`docs/`](docs/):

- 🚀 **[Guía de Inicio Rápido](docs/getting_started.md)**: Instalación, primeros pasos y ejemplos.
- 🏛️ **[Arquitectura Limpia](docs/architecture.md)**: Modelo de capas (Domain, Application, Infrastructure).
- 📖 **[Referencia de API](docs/api_reference.md)**: Métodos, clases, DTOs y la fachada `PyxisCore`.
- 🔄 **[Motor de Nodos y Efectos](docs/node_engine.md)**: Catálogo de nodos y cómo crear nodos personalizados.
- ⚙️ **[Adaptadores y Binarios Nativos](docs/adapters_and_binaries.md)**: Potrace (`img2ass`), `libass_profiler`, FreeType.
- 💻 **[Guía de Línea de Comandos (CLI)](docs/cli.md)**: Uso del comando `pyxis-core`.
- 📦 **[Guía de Publicación en PyPI](docs/publishing.md)**: Instrucciones para compilar y subir a PyPI.

---

## 📦 Instalación

```bash
# Instalación desde PyPI
pip install pyxis-core

# O con soporte para aceleración por GPU (CUDA / CuPy)
pip install "pyxis-core[gpu]"

# O en modo desarrollo editable
git clone https://github.com/Pyxis-Effector/Pyxis-Effector.git
cd Pyxis-Effector/pyxis_core
pip install -e ".[dev]"
```

---

## 🏛️ Estructura del Paquete

```text
pyxis_core/
├── pyproject.toml                     # Configuración PEP 517/621 para PyPI
├── MANIFEST.in                        # Reglas de empaquetado de assets y docs
├── LICENSE                            # Licencia GPL-3.0-or-later
├── requirements.txt                   # Dependencias de producción
├── docs/                              # Documentación técnica completa
├── tests/                             # Tests unitarios automatizados (pytest)
└── pyxis_core/                        # Código fuente del paquete
    ├── __init__.py                    # Facade PyxisCore y exportaciones
    ├── cli.py                         # CLI ejecutable `pyxis-core`
    ├── domain/                        # Entidades, Value Objects e Interfaces
    ├── application/                   # Casos de Uso, DTOs y Mappers
    └── infrastructure/                # Repositorios, Adaptadores y Motores de cálculo
```

---

## 💻 Uso desde la Línea de Comandos (CLI)

```bash
# Información del sistema y herramientas nativas
pyxis-core info

# Validar la sintaxis de un grafo de nodos
pyxis-core validate --graph efecto.json

# Procesar subtítulos con un grafo
pyxis-core process --graph efecto.json --ass dialogo.ass --output resultado.ass

# Analizar telemetría de rendimiento y dropped frames
pyxis-core telemetry --ass resultado.ass --fps 23.976 -o reporte.json
```

---

## 🚀 Uso Rápido desde Python

### 1. Vía Fachada `PyxisCore` (Recomendado)

```python
from pyxis_core import PyxisCore

core = PyxisCore()

# Procesar subtítulos con un grafo de nodos
response = core.process(
    graph="efecto.json",                  # Ruta a JSON o dict
    ass_path="dialogo.ass",               # Archivo ASS
    output_path="resultado.ass",          # Salida opcional
    progress_callback=lambda p: print(f"[{p.percent}%] {p.phase}")
)

if response.success:
    print(f"Generadas {response.lines_count} líneas en {response.duration_seconds:.2f}s")
else:
    print(f"Error: {response.error}")
```

### 2. Uso con Inyección de Dependencias (Microservicios / FastAPI)

```python
from pyxis_core.application.use_cases import ProcessGraphUseCase
from pyxis_core.application.dtos import ProcessGraphRequestDTO
from pyxis_core.infrastructure.repositories import FileSubtitleRepository

# Inyección desacoplada
repo = FileSubtitleRepository()
use_case = ProcessGraphUseCase(subtitle_repo=repo)

# Ejecución en memoria sin archivos temporales
request = ProcessGraphRequestDTO(
    graph={"nodes": [...], "connections": [...]},
    ass_content="[Script Info]...",
)
response = use_case.execute(request)
```

---

## 🧪 Pruebas Automatizadas

```bash
python3 -m pytest tests/
```

## 📄 Licencia

Este proyecto está bajo la licencia **GNU General Public License v3 (GPL-3.0-or-later)**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

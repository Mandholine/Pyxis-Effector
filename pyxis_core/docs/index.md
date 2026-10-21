# Pyxis Core — Documentación Oficial

> **Motor modular de efectos y renderizado de subtítulos ASS basado en Clean Architecture y Grafos de Nodos.**

[![PyPI Version](https://img.shields.io/badge/pypi-0.1.0-blue.svg)](https://pypi.org/project/pyxis-core/)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://pypi.org/project/pyxis-core/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](LICENSE)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20Architecture-brightgreen.svg)]()

---

## 📖 Índice General de la Documentación

1. **[Guía de Inicio Rápido (`getting_started.md`)](getting_started.md)**  
   Instalación mediante `pip`, requisitos del sistema, configuración inicial y tu primer efecto procesado en menos de 5 minutos.

2. **[Arquitectura Limpia (`architecture.md`)](architecture.md)**  
   Principios de diseño, desacoplamiento en capas (*Domain*, *Application*, *Infrastructure*), inversión de dependencias y flujo de datos.

3. **[Referencia de API (`api_reference.md`)](api_reference.md)**  
   Catálogo completo de clases, métodos, DTOs, entidades de dominio y la fachada `PyxisCore`.

4. **[Motor de Nodos y Efectos (`node_engine.md`)](node_engine.md)**  
   Estructura de un grafo de efectos, tipos de nodos disponibles (Audio, Texto, Formas, Partículas, Lógica), pipelines y cómo crear nodos personalizados.

5. **[Adaptadores, Herramientas Nativas y Binarios (`adapters_and_binaries.md`)](adapters_and_binaries.md)**  
   Vectorización de imágenes a ASSDraw con `img2ass` / `potrace`, perfiles de rendimiento y telemetría de fotogramas con `libass_profiler`, motores de audio y fuentes tipográficas.

6. **[Guía de Línea de Comandos CLI (`cli.md`)](cli.md)**  
   Uso de la herramienta de terminal `pyxis-core` para procesar archivos ASS, validar esquemas de nodos y generar reportes de telemetría sin escribir código Python.

7. **[Guía de Publicación en PyPI (`publishing.md`)](publishing.md)**  
   Paso a paso para compilar la distribución (`wheel` y `sdist`), verificar con `twine` y publicar la librería en TestPyPI y PyPI oficial.

---

## 🎯 ¿Qué es Pyxis Core?

`pyxis-core` es el núcleo de cálculo y procesamiento de efectos visuales para subtítulos en formato **Advanced SubStation Alpha (`.ass`)**. Proporciona una canalización matemática y vectorial de alto rendimiento capaz de:

- Evaluar y componer **grafos nodales** de efectos complejos (animaciones, transformaciones 2D/3D, gradientes, partículas).
- Vectorizar mapas de bits PNG/JPG a trazados Bézier de dibujo ASS (`{\p1}m ...{\p0}`).
- Sincronizar efectos con ondas sonoras y espectrogramas de audio (*karaoke*, *beat detection*).
- Analizar telemetría de rendimiento y fotogramas caídos (*dropped frames*) usando renderizado nativo headless con `libass`.
- Integrarse de forma nativa en microservicios backend (**FastAPI**, Django, Flask) o herramientas de escritorio mediante contratos desacoplados (**DTOs**).

---

## 🧩 Visión General de la Estructura

```text
pyxis_core/
├── pyproject.toml                     # Configuración estándar PEP 517/621 para PyPI
├── MANIFEST.in                        # Reglas de empaquetado para la distribución fuente
├── LICENSE                            # Licencia GNU General Public License v3
├── requirements.txt                   # Dependencias principales de Python
├── docs/                              # Documentación completa y guías
├── tests/                             # Pruebas unitarias automatizadas con pytest
└── pyxis_core/                        # Paquete Python distribuible
    ├── __init__.py                    # Fachada PyxisCore y exportaciones de capas
    ├── cli.py                         # Herramienta de línea de comandos (pyxis-core)
    ├── domain/                        # Entidades, Value Objects e Interfaces de repositorio
    ├── application/                   # Casos de uso, DTOs y Mappers
    └── infrastructure/                # Repositorios en disco, adaptadores y motor de cálculo
```
